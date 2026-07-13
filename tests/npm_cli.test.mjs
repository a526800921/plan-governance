import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { accessSync, constants, existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join, resolve } from "node:path";
import test from "node:test";
import { tmpdir } from "node:os";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const cli = resolve(root, "bin", "plan-governance-cli.mjs");

function run(...args) {
  return spawnSync(process.execPath, [cli, ...args], {
    cwd: root,
    encoding: "utf8",
  });
}

test("CLI forwards help output from the Python checker", () => {
  const result = run("--help");
  assert.equal(result.status, 0);
  assert.match(result.stdout, /strict-readiness/);
  assert.equal(result.stderr, "");
});

test("CLI forwards a successful strict readiness check", () => {
  const result = run(".", "--strict-readiness");
  assert.equal(result.status, 0);
  assert.match(result.stdout, /计划治理检查通过。/);
});

test("CLI resolves the checker from the package directory", () => {
  const checker = resolve(root, "scripts", "check_plan_governance.py");
  accessSync(checker, constants.R_OK);
  assert.match(cli, /bin[\\/]plan-governance-cli\.mjs$/);
});

test("package manifest contains the distributable skill resources", () => {
  const manifest = JSON.parse(readFileSync(resolve(root, "resources", "manifest.json"), "utf8"));
  for (const resource of manifest.skill.files) {
    accessSync(resolve(root, resource), constants.R_OK);
  }
  assert.doesNotMatch(readFileSync(resolve(root, "resources", "skill", "SKILL.md"), "utf8"), /\/Users\/jafish\//);
  assert.deepEqual(manifest.hooks, []);
});

test("packed package runs from a temporary installation", () => {
  const tempRoot = mkdtempSync(join(tmpdir(), "plan-governance-cli-"));
  const installRoot = join(tempRoot, "install");
  try {
    const packed = spawnSync("npm", ["pack", "--json", "--pack-destination", tempRoot], {
      cwd: root,
      encoding: "utf8",
    });
    assert.equal(packed.status, 0, packed.stderr);
    const tarball = JSON.parse(packed.stdout)[0].filename;
    const tarballPath = resolve(tempRoot, tarball);

    const installed = spawnSync("npm", ["install", "--ignore-scripts", "--prefix", installRoot, tarballPath], {
      cwd: root,
      encoding: "utf8",
    });
    assert.equal(installed.status, 0, installed.stderr);

    const installedCli = resolve(installRoot, "node_modules", "plan-governance-cli", "bin", "plan-governance-cli.mjs");
    const result = spawnSync(process.execPath, [installedCli, "--help"], {
      cwd: root,
      encoding: "utf8",
    });
    assert.equal(result.status, 0, result.stderr);
    assert.match(result.stdout, /strict-readiness/);
  } finally {
    rmSync(tempRoot, { recursive: true, force: true });
  }
});

test("setup supports dry-run, sync, and conflict protection", () => {
  const tempRoot = mkdtempSync(join(tmpdir(), "plan-governance-setup-"));
  const destination = join(tempRoot, "codex", "skills", "plan-governance");
  try {
    const dryRun = spawnSync(process.execPath, [cli, "setup", "--target", "codex", "--destination", destination, "--dry-run"], {
      cwd: root,
      encoding: "utf8",
    });
    assert.equal(dryRun.status, 0, dryRun.stderr);
    assert.match(dryRun.stdout, /setup dry-run 完成/);
    assert.equal(existsSync(destination), false);

    const synced = spawnSync(process.execPath, [cli, "setup", "--target", "codex", "--destination", destination], {
      cwd: root,
      encoding: "utf8",
    });
    assert.equal(synced.status, 0, synced.stderr);
    assert.match(synced.stdout, /已同步/);
    assert.match(readFileSync(join(destination, "SKILL.md"), "utf8"), /plan-governance/);
    assert.equal(existsSync(join(destination, "scripts")), false);

    const skillPath = join(destination, "SKILL.md");
    const original = readFileSync(skillPath, "utf8");
    writeFileSync(skillPath, `${original}\n本地修改\n`, "utf8");
    const conflict = spawnSync(process.execPath, [cli, "setup", "--target", "codex", "--destination", destination], {
      cwd: root,
      encoding: "utf8",
    });
    assert.notEqual(conflict.status, 0);
    assert.match(conflict.stderr, /本地差异/);
    assert.match(readFileSync(skillPath, "utf8"), /本地修改/);
  } finally {
    rmSync(tempRoot, { recursive: true, force: true });
  }
});

test("init uses the package initializer without copying a local checker by default", () => {
  const tempRoot = mkdtempSync(join(tmpdir(), "plan-governance-init-"));
  const projectRoot = join(tempRoot, "project");
  try {
    const result = spawnSync(process.execPath, [
      cli,
      "init",
      "--root",
      projectRoot,
      "--plan",
      "demo-plan",
      "--title",
      "Demo Plan",
      "--goal",
      "验证 npm 初始化入口",
    ], { cwd: root, encoding: "utf8" });
    assert.equal(result.status, 0, result.stderr);
    assert.equal(existsSync(join(projectRoot, "docs", "PLAN_MAP.md")), true);
    assert.equal(existsSync(join(projectRoot, "docs", "plans", "demo-plan.md")), true);
    assert.equal(existsSync(join(projectRoot, "scripts", "check_plan_governance.py")), false);
  } finally {
    rmSync(tempRoot, { recursive: true, force: true });
  }
});
