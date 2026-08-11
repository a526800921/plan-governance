import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { accessSync, constants, existsSync, mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
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

function writeProjectFile(projectRoot, relativePath, content) {
  const path = resolve(projectRoot, relativePath);
  const directory = dirname(path);
  mkdirSync(directory, { recursive: true });
  writeFileSync(path, content, "utf8");
}

function worksetPlan(status, review = "尚未进行") {
  return `# 计划\n\n## 当前阶段\n\n### 阶段准入摘要\n\n| 字段 | 内容 |\n|---|---|\n| 准入状态 | ${status} |\n| Step 0 | 已有基线 |\n| 样本矩阵 | fixture |\n| 验证方式 | npm test |\n| 失败/回滚边界 | 失败停止 |\n| 当前阻塞项 | 无 |\n| 最新独立准入复核 | ${review} |\n\n## 最新独立准入复核\n\n| 字段 | 内容 |\n|---|---|\n| 日期 | 2026-08-10 |\n| 阶段 | 阶段 1 |\n| 结论 | ${review === "通过" ? "通过" : "尚未进行"} |\n| 证据 | fixture |\n| 复核者 | tester |\n\n## 未决问题\n\n| 问题 | 推荐方案 | 是否阻塞当前阶段 | 状态 |\n|---|---|---|---|\n| - | - | 否 | 已决定 |\n`;
}

function stepPlan(statusRows) {
  return `# 计划\n\nexecution_mode: autonomous-continuous\nexecution_policy: serial\n\n## 当前阶段\n\n### 执行清单\n\n| 步骤 ID | 前置步骤 | 动作 | 证据 | 完成条件 | 状态 | 分支记录 |\n|---|---|---|---|---|---|---|\n${statusRows}\n`;
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

test("workset derives active plans without writing history", () => {
  const tempRoot = mkdtempSync(join(tmpdir(), "plan-governance-workset-"));
  try {
    writeProjectFile(tempRoot, "docs/PLAN_MAP.md", `# PLAN_MAP\n\n## 计划索引\n\n| 计划 | 状态 | 当前阶段 | 最后更新 | 依赖 | 证据 |\n|---|---|---|---|---|---|\n| [alpha](plans/alpha.md) | 设计中 | 阶段 1 | 2026-08-10 | - | - |\n| [beta](plans/beta.md) | 待实施 | 阶段 1 | 2026-08-10 | - | - |\n| [old](plans/old.md) | 已完成 | 阶段 1 | 2026-08-10 | - | - |\n`);
    writeProjectFile(tempRoot, "docs/plans/alpha.md", worksetPlan("设计中"));
    writeProjectFile(tempRoot, "docs/plans/beta.md", worksetPlan("待实施", "通过"));
    writeProjectFile(tempRoot, "docs/plans/old.md", worksetPlan("已完成", "通过"));

    const mapBefore = readFileSync(resolve(tempRoot, "docs/PLAN_MAP.md"), "utf8");
    const alphaBefore = readFileSync(resolve(tempRoot, "docs/plans/alpha.md"), "utf8");
    const result = run("workset", "--json", "--root", tempRoot);
    assert.equal(result.status, 0, result.stderr);
    const payload = JSON.parse(result.stdout);
    assert.deepEqual(payload.plans.map((item) => item.plan), ["alpha", "beta"]);
    assert.equal(payload.plans[0].next_action.kind, "independent_review");
    assert.equal(payload.plans[1].next_action.kind, "implement");
    assert.equal(payload.plans[0].parallel.state, "unknown");
    assert.equal(readFileSync(resolve(tempRoot, "docs/PLAN_MAP.md"), "utf8"), mapBefore);
    assert.equal(readFileSync(resolve(tempRoot, "docs/plans/alpha.md"), "utf8"), alphaBefore);

    const history = run("workset", "--json", "--include-history", "--root", tempRoot);
    assert.equal(history.status, 0, history.stderr);
    assert.deepEqual(JSON.parse(history.stdout).plans.map((item) => item.plan), ["alpha", "beta", "old"]);
  } finally {
    rmSync(tempRoot, { recursive: true, force: true });
  }
});

test("plan steps validate checks valid and invalid autonomous plans", () => {
  const tempRoot = mkdtempSync(join(tmpdir(), "plan-governance-steps-"));
  try {
    writeProjectFile(tempRoot, "docs/PLAN_MAP.md", `# PLAN_MAP\n\n## 计划索引\n\n| 计划 | 状态 | 当前阶段 | 最后更新 | 依赖 | 证据 |\n|---|---|---|---|---|---|\n| [demo](plans/demo.md) | 设计中 | 阶段 1 | 2026-08-10 | - | - |\n`);
    writeProjectFile(tempRoot, "docs/plans/demo.md", stepPlan("| `S1` | - | 建立基线 | 测试输出 | 基线存在 | 已完成 | - |\n| `S2` | S1 | 校验方案 | 测试输出 | 校验通过 | 未开始 | - |"));

    const planBefore = readFileSync(resolve(tempRoot, "docs/plans/demo.md"), "utf8");
    const valid = run("plan", "steps", "validate", "demo", "--json", "--root", tempRoot);
    assert.equal(valid.status, 0, valid.stderr);
    const validPayload = JSON.parse(valid.stdout);
    assert.equal(validPayload.status, "valid");
    assert.equal(validPayload.steps.length, 2);
    assert.equal(readFileSync(resolve(tempRoot, "docs/plans/demo.md"), "utf8"), planBefore);

    writeProjectFile(tempRoot, "docs/plans/demo.md", stepPlan("| `S1` | - | 建立基线 | 测试输出 | 基线存在 | 取消 | - |\n| `S1` | - | 重复步骤 | 测试输出 | 条件满足 | 未开始 | - |"));
    const invalid = run("plan", "steps", "validate", "demo", "--json", "--strict-readiness", "--root", tempRoot);
    assert.equal(invalid.status, 1);
    const invalidPayload = JSON.parse(invalid.stdout);
    assert.equal(invalidPayload.status, "invalid");
    assert.match(invalidPayload.errors.join("\n"), /重复|状态非法/);
  } finally {
    rmSync(tempRoot, { recursive: true, force: true });
  }
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
  const skill = readFileSync(resolve(root, "resources", "skill", "SKILL.md"), "utf8");
  const planTemplate = readFileSync(resolve(root, "resources", "skill", "assets", "plan.template.md"), "utf8");
  assert.doesNotMatch(skill, /\/Users\/jafish\//);
  assert.match(skill, /需求探索与 grilling/);
  assert.match(skill, /grill-me/);
  assert.match(planTemplate, /^## 需求探索$/m);
  assert.match(planTemplate, /^### 阶段证据$/m);
  assert.match(planTemplate, /^### 最近实施\/验证记录$/m);
  assert.match(planTemplate, /purpose.*snapshot_id.*supersedes.*review_status/);
  assert.match(planTemplate, /^## 最新独立准入复核$/m);
  assert.match(planTemplate, /^## 独立复核记录$/m);
  assert.doesNotMatch(planTemplate, /^### 最新独立准入复核$/m);
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

    const projectRoot = join(tempRoot, "project");
    const initialized = spawnSync(process.execPath, [
      installedCli,
      "init",
      "--root",
      projectRoot,
      "--plan",
      "installed-demo",
      "--title",
      "Installed Demo",
      "--goal",
      "验证安装后的模板资源",
    ], {
      cwd: root,
      encoding: "utf8",
    });
    assert.equal(initialized.status, 0, initialized.stderr);
    const plan = readFileSync(join(projectRoot, "docs", "plans", "installed-demo.md"), "utf8");
    assert.match(plan, /^## 需求探索$/m);
    assert.match(plan, /^### 阶段证据$/m);
    assert.match(plan, /^### 最近实施\/验证记录$/m);
    assert.match(plan, /purpose.*snapshot_id.*supersedes.*review_status/);
    assert.match(plan, /^## 最新独立准入复核$/m);
    assert.match(plan, /验证安装后的模板资源/);
    assert.doesNotMatch(plan, /\/Users\/jafish\/Documents\/work\/plan-governance/);

    const installedWorkset = spawnSync(process.execPath, [
      installedCli,
      "workset",
      "--json",
      "--root",
      projectRoot,
    ], { cwd: root, encoding: "utf8" });
    assert.equal(installedWorkset.status, 0, installedWorkset.stderr);
    const worksetPayload = JSON.parse(installedWorkset.stdout);
    assert.equal(worksetPayload.schema_version, 1);
    assert.equal(worksetPayload.plans.length, 1);
    assert.equal(worksetPayload.plans[0].plan, "installed-demo");

    const installedStepValidation = spawnSync(process.execPath, [
      installedCli,
      "plan",
      "steps",
      "validate",
      "installed-demo",
      "--json",
      "--root",
      projectRoot,
    ], { cwd: root, encoding: "utf8" });
    assert.equal(installedStepValidation.status, 0, installedStepValidation.stderr);
    assert.equal(JSON.parse(installedStepValidation.stdout).status, "not_enabled");

    const destination = join(tempRoot, "codex", "skills", "plan-governance");
    const dryRun = spawnSync(process.execPath, [
      installedCli,
      "setup",
      "--target",
      "codex",
      "--destination",
      destination,
      "--dry-run",
    ], { cwd: root, encoding: "utf8" });
    assert.equal(dryRun.status, 0, dryRun.stderr);
    assert.equal(existsSync(destination), false);

    const synced = spawnSync(process.execPath, [
      installedCli,
      "setup",
      "--target",
      "codex",
      "--destination",
      destination,
    ], { cwd: root, encoding: "utf8" });
    assert.equal(synced.status, 0, synced.stderr);
    assert.match(readFileSync(join(destination, "SKILL.md"), "utf8"), /需求探索与 grilling/);
    assert.equal(existsSync(join(destination, "scripts")), false);
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
    assert.match(readFileSync(join(destination, "SKILL.md"), "utf8"), /需求探索与 grilling/);
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
