#!/usr/bin/env node

import {
  accessSync,
  constants,
  existsSync,
  mkdirSync,
  readFileSync,
  renameSync,
  writeFileSync,
} from "node:fs";
import { homedir, tmpdir } from "node:os";
import { dirname, join, relative, resolve } from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const packageRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const checker = resolve(packageRoot, "scripts", "check_plan_governance.py");
const initializer = resolve(packageRoot, "scripts", "init_plan_governance.py");
const hookRuntime = resolve(packageRoot, "scripts", "plan_governance_hook.py");
const graphRuntime = resolve(packageRoot, "scripts", "graph_governance.mjs");
const manifestPath = resolve(packageRoot, "resources", "manifest.json");

function fail(message) {
  console.error(`plan-governance-cli: ${message}`);
  return 1;
}

function runPython(script, args) {
  try {
    accessSync(script, constants.R_OK);
  } catch {
    return fail(`找不到包内脚本：${script}`);
  }

  const candidates = process.env.PYTHON ? [process.env.PYTHON] : ["python3", "python"];
  let result;
  for (const command of candidates) {
    result = spawnSync(command, [script, ...args], { stdio: "inherit" });
    if (!result.error || result.error.code !== "ENOENT") {
      break;
    }
  }

  if (result?.error) {
    return fail(`无法启动 Python 脚本：${result.error.message}`);
  }
  if (result?.signal) {
    console.error(`plan-governance-cli: 脚本被信号 ${result.signal} 终止`);
    return 1;
  }
  return result?.status ?? 1;
}

function runNode(script, args) {
  try {
    accessSync(script, constants.R_OK);
  } catch {
    return fail(`找不到包内脚本：${script}`);
  }

  const result = spawnSync(process.execPath, [script, ...args], { stdio: "inherit" });
  if (result.error) {
    return fail(`无法启动 Node.js 脚本：${result.error.message}`);
  }
  if (result.signal) {
    console.error(`plan-governance-cli: 脚本被信号 ${result.signal} 终止`);
    return 1;
  }
  return result.status ?? 1;
}

function loadManifest() {
  try {
    return JSON.parse(readFileSync(manifestPath, "utf8"));
  } catch (error) {
    throw new Error(`无法读取包内资源清单：${error.message}`);
  }
}

function parseSetupArgs(args) {
  const options = { target: null, destination: null, dryRun: false, force: false };
  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--target") {
      options.target = args[++index];
    } else if (arg === "--destination") {
      options.destination = args[++index];
    } else if (arg === "--dry-run") {
      options.dryRun = true;
    } else if (arg === "--force") {
      options.force = true;
    } else if (arg === "-h" || arg === "--help") {
      console.log("用法：plan-governance-cli setup --target codex|claude|all [--destination DIR] [--dry-run] [--force]");
      return null;
    } else {
      throw new Error(`setup 不支持参数：${arg}`);
    }
  }

  if (!options.target || !["codex", "claude", "all"].includes(options.target)) {
    throw new Error("setup 必须指定 --target codex、claude 或 all");
  }
  if (options.destination && options.target === "all") {
    throw new Error("--destination 只能与单个 setup target 一起使用");
  }
  return options;
}

function expandTarget(target) {
  const home = process.env.HOME || homedir();
  return target.replace(/^~(?=\/|$)/, home);
}

function targetRoots(manifest, options) {
  const names = options.target === "all" ? ["codex", "claude"] : [options.target];
  return names.map((name) => ({
    name,
    root: resolve(options.destination ? options.destination : expandTarget(manifest.skill.targets[name])),
  }));
}

function resourceFiles(manifest) {
  const skillPrefix = "resources/skill/";
  return manifest.skill.files.map((source) => {
    if (!source.startsWith(skillPrefix)) {
      throw new Error(`skill 资源不在受支持的目录中：${source}`);
    }
    return {
      source: resolve(packageRoot, source),
      relative: source.slice(skillPrefix.length),
    };
  });
}

function setup(args) {
  const options = parseSetupArgs(args);
  if (options === null) return 0;

  let manifest;
  let files;
  try {
    manifest = loadManifest();
    files = resourceFiles(manifest);
  } catch (error) {
    return fail(error.message);
  }

  const plans = [];
  try {
    for (const target of targetRoots(manifest, options)) {
      for (const file of files) {
        accessSync(file.source, constants.R_OK);
        const destination = resolve(target.root, file.relative);
        const existing = existsSync(destination) ? readFileSync(destination, "utf8") : null;
        const sourceContent = readFileSync(file.source, "utf8");
        if (existing !== null && existing !== sourceContent && !options.force) {
          throw new Error(`目标文件存在本地差异，未覆盖：${destination}（如确认覆盖请加 --force）`);
        }
        plans.push({ target: target.name, destination, existing, sourceContent });
      }
    }
  } catch (error) {
    return fail(error.message);
  }

  for (const plan of plans) {
    if (plan.existing === plan.sourceContent) {
      console.log(`已是最新：${plan.destination}`);
    } else if (options.dryRun) {
      console.log(`将写入：${plan.destination}`);
    } else {
      mkdirSync(dirname(plan.destination), { recursive: true });
      const temporary = join(tmpdir(), `plan-governance-${process.pid}-${Date.now()}-${Math.random().toString(16).slice(2)}`);
      writeFileSync(temporary, plan.sourceContent, "utf8");
      renameSync(temporary, plan.destination);
      console.log(`已同步：${plan.destination}`);
    }
  }
  if (options.dryRun) console.log("setup dry-run 完成，未修改目标目录。");
  return 0;
}

function main() {
  const args = process.argv.slice(2);
  const command = args[0];
  if (command === "setup") return setup(args.slice(1));
  if (command === "workset") return runPython(checker, ["--workset", ...args.slice(1)]);
  if (command === "init") return runPython(initializer, args.slice(1));
  if (command === "hook") return runPython(hookRuntime, args.slice(1));
  if (command === "graph") return runNode(graphRuntime, args.slice(1));
  if (command === "plan" && args[1] === "next") {
    return fail("plan next 已移除；在 Codex 中请使用 goal 管理跨轮持续推进。");
  }
  if (command === "plan" && args[1] === "steps" && args[2] === "validate") {
    return fail("自主执行步骤校验已移除；在 Codex 中请使用 goal 管理跨轮持续推进。");
  }
  if (command === "plan") return runNode(graphRuntime, args);
  if (command === "check") return runPython(checker, args.slice(1));
  return runPython(checker, args);
}

try {
  process.exitCode = main();
} catch (error) {
  process.exitCode = fail(error.message);
}
