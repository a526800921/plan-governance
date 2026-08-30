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
  const dryRun = argumentsList.includes("--dry-run");
  const positional = argumentsList.filter((argument) => argument !== "--dry-run");

  if (positional.length > 1) {
    fail("只接受一个版本类型或版本号，例如 patch、minor、major 或 0.3.4");
    return null;
  }

  const versionInput = positional[0] ?? "patch";
  const isBumpType = /^(patch|minor|major)$/.test(versionInput);
  const isVersion = /^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$/.test(versionInput);

  if (!isBumpType && !isVersion) {
    fail(`不支持的版本参数：${versionInput}`);
    return null;
  }

  return { dryRun, versionInput };
}

function currentPackageVersion() {
  const packageJson = JSON.parse(readFileSync(resolve(projectRoot, "package.json"), "utf8"));
  return packageJson.version;
}

const options = parseArguments(process.argv.slice(2));
if (!options) {
  process.exitCode ??= 2;
} else {
  let originalRegistry;
  let switchedToNpm = false;
  let exitCode = 0;

  try {
    originalRegistry = capture(npmCommand, ["config", "get", "registry"]);
    if (!originalRegistry || originalRegistry === "undefined") {
      throw new Error("无法读取当前 npm registry");
    }

    if (options.dryRun) {
      console.log(`[release:npm] 当前 registry: ${originalRegistry}`);
      console.log(`[release:npm] dry-run: nrm use ${npmRegistry}`);
      console.log("[release:npm] dry-run: npm test");
      console.log(`[release:npm] dry-run: npm version ${options.versionInput} --no-git-tag-version`);
      console.log(`[release:npm] dry-run: npm publish --access public --registry ${npmRegistryUrl}`);
      console.log(`[release:npm] dry-run: 恢复 registry ${originalRegistry}`);
    } else {
      console.log(`[release:npm] 当前版本: ${currentPackageVersion()}`);
      run(nrmCommand, ["use", npmRegistry]);
      switchedToNpm = true;

      run(npmCommand, ["test"]);
      run(npmCommand, ["version", options.versionInput, "--no-git-tag-version"]);
      run(npmCommand, ["publish", "--access", "public", "--registry", npmRegistryUrl]);
      console.log(`[release:npm] 已发布版本: ${currentPackageVersion()}`);
    }
  } catch (error) {
    exitCode = 1;
    console.error(`[release:npm] 发布流程失败：${error.message}`);
  } finally {
    if (switchedToNpm) {
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
