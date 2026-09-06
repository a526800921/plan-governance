import { spawnSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const projectRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const npmCommand = process.platform === "win32" ? "npm.cmd" : "npm";

function run(command, args) {
  console.log(`[verify] ${command} ${args.join(" ")}`);
  return spawnSync(command, args, { cwd: projectRoot, stdio: "inherit" });
}

function requireSuccess(result, label) {
  if (result.error) throw result.error;
  if (result.signal || result.status !== 0) {
    throw new Error(`${label} 失败（${result.signal ?? result.status ?? "未知退出状态"}）`);
  }
}

function verify() {
  const candidates = process.env.PYTHON ? [process.env.PYTHON] : ["python3", "python"];
  let python;
  for (const candidate of candidates) {
    const result = run(candidate, ["scripts/check_plan_governance.py", ".", "--strict-readiness"]);
    // Only a missing default executable permits fallback; failed checks never do.
    if (!process.env.PYTHON && result.error?.code === "ENOENT") continue;
    requireSuccess(result, "严格治理检查");
    python = candidate;
    break;
  }
  if (!python) throw new Error("找不到 Python；请安装 Python 或设置 PYTHON 可执行路径");

  requireSuccess(run(python, ["-m", "pytest"]), "Python 测试与覆盖率检查");
  requireSuccess(run(npmCommand, ["test"]), "Node 测试");
}

if (process.argv.length > 2) {
  console.error("[verify] 不接受参数；请直接运行 npm run verify");
  process.exitCode = 2;
} else {
  try {
    verify();
    process.exitCode = 0;
  } catch (error) {
    console.error(`[verify] 验证失败：${error.message}`);
    process.exitCode = 1;
  }
}
