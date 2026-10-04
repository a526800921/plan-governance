import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDirectory = dirname(fileURLToPath(import.meta.url));
const projectRoot = resolve(scriptDirectory, "..");
const npmCommand = process.platform === "win32" ? "npm.cmd" : "npm";
const nrmCommand = process.platform === "win32" ? "nrm.cmd" : "nrm";
const npmRegistry = "npm";
const npmRegistryUrl = "https://registry.npmjs.org/";

function fail(message) {
  console.error(`[release:npm] ${message}`);
  process.exitCode = 2;
}

function run(command, args, options = {}) {
  return execFileSync(command, args, {
    cwd: projectRoot,
    stdio: "inherit",
    ...options,
  });
}

function capture(command, args) {
  return execFileSync(command, args, {
    cwd: projectRoot,
    encoding: "utf8",
  }).trim();
}

function parseArguments(argumentsList) {
  if (argumentsList.filter((arg) => arg === "--dry-run").length > 1) {
    fail("--dry-run 只能指定一次");
    return null;
  }
  if (argumentsList.length === 1 && ["--help", "-h"].includes(argumentsList[0])) {
    console.log("用法：npm run release:npm -- [--dry-run] [patch|minor|major|SemVer]");
    return null;
  }
  const dryRun = argumentsList.includes("--dry-run");
  const positional = argumentsList.filter((argument) => argument !== "--dry-run");

  if (positional.length > 1) {
    fail("只接受一个版本类型或版本号，例如 patch、minor、major 或 0.3.4");
    return null;
  }

  const versionInput = positional[0] ?? "patch";
  const isBumpType = /^(patch|minor|major)$/.test(versionInput);
  const isVersion = validVersion(versionInput);

  if (!isBumpType && !isVersion) {
    fail(`不支持的版本参数：${versionInput}`);
    return null;
  }

  return { dryRun, versionInput };
}

function validVersion(value) {
  const numeric = "(?:0|[1-9][0-9]*)";
  const prerelease = "(?:0|[1-9][0-9]*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*)";
  return new RegExp(`^${numeric}\\.${numeric}\\.${numeric}(?:-${prerelease}(?:\\.${prerelease})*)?(?:\\+[0-9A-Za-z-]+(?:\\.[0-9A-Za-z-]+)*)?$`).test(value);
}

function packageMetadata() {
  return JSON.parse(readFileSync(resolve(projectRoot, "package.json"), "utf8"));
}

function targetVersion(current, input) {
  if (!validVersion(current)) throw new Error(`工作区版本无效：${current}`);
  if (!/^(patch|minor|major)$/.test(input)) return input;
  let [major, minor, patch] = current.split(/[+-]/)[0].split(".").map(Number);
  const prerelease = current.split("+")[0].includes("-");
  if (input === "major") { major += !prerelease || minor || patch ? 1 : 0; minor = 0; patch = 0; }
  if (input === "minor") { minor += !prerelease || patch ? 1 : 0; patch = 0; }
  if (input === "patch" && !prerelease) patch += 1;
  return `${major}.${minor}.${patch}`;
}

function assertUnpublished(name, version) {
  if (!name?.trim()) throw new Error("package.json 缺少包名");
  let result;
  try {
    result = capture(npmCommand, ["view", `${name}@${version}`, "version", "--json", "--registry", npmRegistryUrl]);
  } catch (error) {
    let report;
    try { report = JSON.parse(String(error.stdout || "")); } catch { /* 只有 npm 明确报告 E404 才确认未发布。 */ }
    if (report?.error?.code === "E404") return;
    throw new Error(`无法确认目标版本是否存在：${error.message}`);
  }
  if (result) throw new Error(`官方 registry 已有 ${name}@${version}，不得重复发布`);
  throw new Error("官方 registry 返回空结果，无法确认目标版本是否存在");
}

const options = parseArguments(process.argv.slice(2));
if (!options) {
  process.exitCode ??= ["--help", "-h"].includes(process.argv[2]) && process.argv.length === 3 ? 0 : 2;
} else {
  let originalRegistry;
  let restoreRequired = false;
  let exitCode = 0;

  try {
    if (!options.dryRun) run(npmCommand, ["run", "verify"]);
    originalRegistry = capture(npmCommand, ["config", "get", "registry"]);
    if (!originalRegistry || originalRegistry === "undefined") {
      throw new Error("无法读取当前 npm registry");
    }

    if (options.dryRun) {
      console.log(`[release:npm] 当前 registry: ${originalRegistry}`);
      console.log("[release:npm] dry-run: npm run verify");
      console.log("[release:npm] dry-run: npm config get registry（验证后保存原值）");
      console.log("[release:npm] dry-run: npm view <package>@<target-version> version --json --registry 官方源（确认未发布）");
      console.log(`[release:npm] dry-run: nrm use ${npmRegistry}`);
      console.log(`[release:npm] dry-run: npm version ${options.versionInput} --no-git-tag-version`);
      console.log(`[release:npm] dry-run: npm publish --access public --registry ${npmRegistryUrl}`);
      console.log(`[release:npm] dry-run: 恢复 registry ${originalRegistry}`);
    } else {
      const metadata = packageMetadata();
      console.log(`[release:npm] 当前版本: ${metadata.version}`);
      assertUnpublished(metadata.name, targetVersion(metadata.version, options.versionInput));
      // A failed switch may already have changed registry, so restore on any attempt.
      restoreRequired = true;
      run(nrmCommand, ["use", npmRegistry]);

      run(npmCommand, ["version", options.versionInput, "--no-git-tag-version"]);
      run(npmCommand, ["publish", "--access", "public", "--registry", npmRegistryUrl]);
      console.log(`[release:npm] 已发布版本: ${packageMetadata().version}`);
    }
  } catch (error) {
    exitCode = 1;
    console.error(`[release:npm] 发布流程失败：${error.message}`);
  } finally {
    if (restoreRequired) {
      try {
        run(npmCommand, ["config", "set", "registry", originalRegistry]);
        console.log(`[release:npm] 已恢复 registry: ${originalRegistry}`);
      } catch (error) {
        exitCode = 1;
        console.error(`[release:npm] 恢复 registry 失败：${error.message}`);
      }
    }
  }

  process.exitCode = Math.max(process.exitCode ?? 0, exitCode);
}
