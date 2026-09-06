import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { accessSync, constants, existsSync, mkdtempSync, mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from "node:fs";
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

function admittedPlan(status = "待实施") {
  return worksetPlan(status, "通过").replace("## 当前阶段",
    `## 阶段路线图\n\n| 阶段 | 目标 | 进入条件 | 验证方向 | 状态 |\n|---|---|---|---|---|\n| 阶段 1 | CLI | 基线 | node | ${status} |\n\n## 当前阶段`) +
    "\n## 独立复核记录\n\n| 日期 | 类型 | 阶段 | 结论 | 证据 | 复核者 |\n|---|---|---|---|---|---|\n| 2026-08-10 | 准入 | 阶段 1 | 通过 | fixture | tester |\n";
}

function exerciseBindingIteration(entry, projectRoot) {
  const invoke = (...args) => spawnSync(process.execPath, [entry, ...args], {
    cwd: root, encoding: "utf8", timeout: 15000,
    env: { ...process.env, PYTHONDONTWRITEBYTECODE: "1" },
  });
  const requireStatus = (result, expected = 0) => {
    assert.equal(result.error, undefined, result.error?.message);
    assert.equal(result.signal, null, result.stderr);
    assert.equal(result.status, expected, result.stdout + result.stderr);
    return result.stdout;
  };
  requireStatus(invoke("init", "--root", projectRoot, "--plan", "demo", "--title", "Binding Fixture", "--goal", "验证临时项目迭代"));
  const mapText = (status) => `# PLAN_MAP\n\n## 计划索引\n\n| 计划 | 状态 | 当前阶段 | 最后更新 | 依赖 | 证据 |\n|---|---|---|---|---|---|\n| [demo](plans/demo.md) | ${status} | 阶段 1 | 2026-09-06 | - | demo evidence |\n| [other](plans/other.md) | 设计中 | 阶段 1 | 2026-09-06 | - | other evidence |\n`;
  writeProjectFile(projectRoot, "docs/PLAN_MAP.md", mapText("待实施"));
  writeProjectFile(projectRoot, "docs/plans/demo.md", admittedPlan());
  writeProjectFile(projectRoot, "docs/plans/other.md", worksetPlan("设计中"));
  const workset = JSON.parse(requireStatus(invoke("workset", projectRoot, "--json", "--strict-readiness")));
  assert.equal(workset.schema_version, 1);
  assert.equal(workset.plans.find((plan) => plan.plan === "demo").next_action.kind, "implement");

  writeProjectFile(projectRoot, "src/demo.py", "print('first reviewed implementation')\n");
  writeProjectFile(projectRoot, "docs/review.md", "Technical fixture review: implementation and checks passed.\n");
  writeProjectFile(projectRoot, "docs/PLAN_MAP.md", mapText("已完成"));
  writeProjectFile(projectRoot, "docs/plans/demo.md", admittedPlan("已完成") +
    "\n## Step 0 证据\n\n已有基线。\n\n## 验证方式\n\n运行检查脚本。\n\n## 测试覆盖率\n\npytest-cov 报告：98.8% 覆盖率。\n");
  requireStatus(invoke("check", projectRoot, "--strict-readiness"));
  const snapshotDirectory = join(projectRoot, "docs/attestations");
  const create = (...extra) => invoke("check", projectRoot, "--attest", "demo", "--attest-purpose", "release_gate",
    "--attest-file", "src/demo.py", "--attest-file", "docs/review.md", ...extra);
  requireStatus(create());
  const firstName = readdirSync(snapshotDirectory).find((name) => name.endsWith(".json"));
  const firstPath = join(snapshotDirectory, firstName);
  const firstBytes = readFileSync(firstPath);
  const first = JSON.parse(firstBytes.toString("utf8"));
  assert.equal(first.binding.version, 1);
  assert.deepEqual(first.binding.files.map((file) => file.path), ["docs/review.md", "src/demo.py"]);
  for (const file of first.binding.files) {
    assert.equal(file.sha256, createHash("sha256").update(readFileSync(join(projectRoot, file.path))).digest("hex"));
  }
  const check = (...extra) => invoke("check", projectRoot, "--check-attestations", ...extra);
  assert.match(requireStatus(check("--strict-readiness")), /status=current/);
  writeProjectFile(projectRoot, "docs/PLAN_MAP.md", mapText("已完成").replace("other evidence", "other changed evidence"));
  assert.match(requireStatus(check("--strict-readiness")), /status=current/);
  writeProjectFile(projectRoot, "src/demo.py", "print('second implementation needing review')\n");
  assert.match(requireStatus(check()), /status=needs_review/);
  assert.match(requireStatus(check("--strict-readiness"), 1), /status=needs_review/);
  writeProjectFile(projectRoot, "docs/review.md", "Technical fixture review: second implementation inspected.\n");
  requireStatus(create("--supersedes", `docs/attestations/${firstName}`));
  const finalOutput = requireStatus(check("--strict-readiness"));
  const rows = finalOutput.split("\n").filter((line) => line.startsWith("ATTESTATION:"));
  assert.equal(rows.filter((line) => line.endsWith("status=current")).length, 1);
  assert.equal(rows.filter((line) => line.endsWith("status=superseded")).length, 1);
  assert.deepEqual(readFileSync(firstPath), firstBytes, "superseding must not rewrite historical evidence");
  assert.equal(readdirSync(snapshotDirectory).filter((name) => name.endsWith(".json")).length, 2);
}

test("binding iteration traverses real Node and Python without touching repository snapshots", () => {
  const tempRoot = mkdtempSync(join(tmpdir(), "plan-governance-binding-"));
  const snapshots = join(root, "docs/attestations");
  const original = new Map(readdirSync(snapshots).map((name) => [name, readFileSync(join(snapshots, name))]));
  try {
    exerciseBindingIteration(cli, join(tempRoot, "project"));
    assert.deepEqual(readdirSync(snapshots).sort(), [...original.keys()].sort());
    for (const [name, bytes] of original) assert.deepEqual(readFileSync(join(snapshots, name)), bytes);
  } finally {
    rmSync(tempRoot, { recursive: true, force: true });
  }
});

test("CLI forwards help output from the Python checker", () => {
  const result = run("--help");
  assert.equal(result.status, 0);
  assert.match(result.stdout, /strict-readiness/);
  assert.equal(result.stderr, "");
});

test("CLI forwards a successful strict readiness check", () => {
  const tempRoot = mkdtempSync(join(tmpdir(), "plan-governance-valid-"));
  try {
    writeProjectFile(tempRoot, "docs/PLAN_MAP.md", "# PLAN_MAP\n\n## 计划索引\n\n| 计划 | 状态 | 当前阶段 | 最后更新 | 依赖 | 证据 |\n|---|---|---|---|---|---|\n| [demo](plans/demo.md) | 待实施 | 阶段 1 | 2026-09-06 | - | fixture |\n");
    writeProjectFile(tempRoot, "docs/plans/demo.md", admittedPlan());
    const result = run(tempRoot, "--strict-readiness");
    assert.equal(result.status, 0, result.stdout);
    assert.equal(result.stderr, "");
    assert.match(result.stdout, /计划治理检查通过。/);
  } finally {
    rmSync(tempRoot, { recursive: true, force: true });
  }
});

test("removed autonomous execution commands point to Codex goals", () => {
  const next = run("plan", "next", "demo");
  assert.equal(next.status, 1);
  assert.match(next.stderr, /goal/);

  const validate = run("plan", "steps", "validate", "demo");
  assert.equal(validate.status, 1);
  assert.match(validate.stderr, /goal/);
});

test("workset derives active plans without writing history", () => {
  const tempRoot = mkdtempSync(join(tmpdir(), "plan-governance-workset-"));
  try {
    writeProjectFile(tempRoot, "docs/PLAN_MAP.md", `# PLAN_MAP\n\n## 计划索引\n\n| 计划 | 状态 | 当前阶段 | 最后更新 | 依赖 | 证据 |\n|---|---|---|---|---|---|\n| [alpha](plans/alpha.md) | 设计中 | 阶段 1 | 2026-08-10 | - | - |\n| [beta](plans/beta.md) | 待实施 | 阶段 1 | 2026-08-10 | - | - |\n| [old](plans/old.md) | 已完成 | 阶段 1 | 2026-08-10 | - | - |\n`);
    writeProjectFile(tempRoot, "docs/plans/alpha.md", worksetPlan("设计中"));
    writeProjectFile(tempRoot, "docs/plans/beta.md", admittedPlan());
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

test("strict check and workset reject the same readiness defects without writing", () => {
  const tempRoot = mkdtempSync(join(tmpdir(), "plan-governance-gates-"));
  const index = "# PLAN_MAP\n\n## 计划索引\n\n| 计划 | 状态 | 当前阶段 | 最后更新 | 依赖 | 证据 |\n|---|---|---|---|---|---|\n| [demo](plans/demo.md) | 待实施 | 阶段 1 | 2026-09-06 | - | fixture |\n";
  try {
    writeProjectFile(tempRoot, "docs/PLAN_MAP.md", index);
    for (const [label, plan, next, strictStatus] of [
      ["valid", admittedPlan(), "implement", 0],
      ["empty", admittedPlan().replace("| Step 0 | 已有基线 |", "| Step 0 | |"), "unknown", 1],
      ["failed", admittedPlan().replace("| 结论 | 通过 |", "| 结论 | 未通过 |"), "resolve_blocker", 1],
      ["blocker", admittedPlan().replace("| 当前阻塞项 | 无 |", "| 当前阻塞项 | 等待授权 |"), "resolve_blocker", 1],
    ]) {
      writeProjectFile(tempRoot, "docs/plans/demo.md", plan);
      for (const strict of [false, true]) {
        const flags = strict ? ["--strict-readiness"] : [];
        const check = run("check", tempRoot, ...flags);
        const workset = run("workset", tempRoot, "--json", ...flags);
        assert.equal(check.status, strict ? strictStatus : 0, `${label}: ${check.stdout}`);
        assert.equal(workset.status, strict ? strictStatus : 0, `${label}: ${workset.stdout}`);
        assert.equal(check.stderr + workset.stderr, "");
        const payload = JSON.parse(workset.stdout);
        assert.equal(payload.schema_version, 1);
        assert.equal(payload.plans[0].next_action.kind, next);
      }
      const hook = run("hook", "--root", tempRoot, "--event", "session-start");
      assert.equal(hook.status, 0, hook.stderr);
      assert.match(hook.stdout, new RegExp(next));
      assert.equal(readFileSync(join(tempRoot, "docs/PLAN_MAP.md"), "utf8"), index);
      assert.equal(readFileSync(join(tempRoot, "docs/plans/demo.md"), "utf8"), plan);
    }
  } finally {
    rmSync(tempRoot, { recursive: true, force: true });
  }
});

test("workset and hook ignore fenced next-action examples", () => {
  const tempRoot = mkdtempSync(join(tmpdir(), "plan-governance-action-"));
  const index = "# PLAN_MAP\n\n## 计划索引\n\n| 计划 | 状态 | 当前阶段 | 最后更新 | 依赖 | 证据 |\n|---|---|---|---|---|---|\n| [demo](plans/demo.md) | 实施中 | 阶段 1 | 2026-09-06 | - | fixture |\n";
  try {
    writeProjectFile(tempRoot, "docs/PLAN_MAP.md", index);
    for (const fence of ["```", "~~~~"]) {
      for (const realAction of [false, true]) {
        const example = `\n\n下一动作格式示例：\n\n${fence}text\n下一动作：实施\n${fence}\n`;
        const plan = admittedPlan("实施中").replace("## 当前阶段", "## 当前阶段" + example + (realAction ? "\n下一动作：验证\n" : ""));
        writeProjectFile(tempRoot, "docs/plans/demo.md", plan);
        for (const flags of [[], ["--strict-readiness"]]) {
          assert.equal(run("check", tempRoot, ...flags).status, 0);
          const result = run("workset", tempRoot, "--json", ...flags);
          assert.equal(result.status, 0, result.stderr);
          assert.equal(JSON.parse(result.stdout).plans[0].next_action.kind, realAction ? "verify" : "unknown");
        }
        const hook = run("hook", "--root", tempRoot, "--event", "session-start");
        assert.equal(hook.status, 0, hook.stderr);
        assert.match(hook.stdout, new RegExp(realAction ? "verify" : "unknown"));
        assert.doesNotMatch(hook.stdout, /implement/);
        assert.equal(readFileSync(join(tempRoot, "docs/PLAN_MAP.md"), "utf8"), index);
        assert.equal(readFileSync(join(tempRoot, "docs/plans/demo.md"), "utf8"), plan);
      }
    }
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
  const agent = readFileSync(resolve(root, "resources", "skill", "agents", "openai.yaml"), "utf8");
  const planTemplate = readFileSync(resolve(root, "resources", "skill", "assets", "plan.template.md"), "utf8");
  const readme = readFileSync(resolve(root, "README.md"), "utf8");
  assert.doesNotMatch(skill, /\/Users\/jafish\//);
  assert.match(skill, /需求探索与 grilling/);
  assert.match(skill, /grill-me/);
  assert.match(skill, /goal/);
  assert.match(skill, /阶段内独立复核调度/);
  assert.match(skill, /自动启动独立只读 subagent/);
  assert.match(skill, /不为每个微小动作单独复核/);
  assert.match(skill, /复核入口不可用/);
  assert.match(agent, /阶段门.*自动启动独立只读 subagent/);
  assert.doesNotMatch(skill, /^## 自主连续执行$/m);
  assert.doesNotMatch(skill, /plan next|execution_mode|execution_policy/);
  assert.doesNotMatch(agent, /推进到完成/);
  assert.match(readme, /^## 持续推进$/m);
  assert.match(readme, /goal/);
  assert.match(readme, /自动启动独立只读 subagent/);
  assert.match(readme, /不为每个微小动作单独复核/);
  assert.match(planTemplate, /^## 需求探索$/m);
  assert.match(planTemplate, /独立复核只绑定阶段准入\/阶段转换和高影响边界/);
  assert.doesNotMatch(planTemplate, /自主连续执行|执行清单|execution_mode|execution_policy/);
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
  const npmOptions = {
    cwd: root,
    encoding: "utf8",
    timeout: 60_000,
    env: {
      ...process.env,
      npm_config_cache: join(tempRoot, "npm-cache"),
      npm_config_audit: "false",
      npm_config_fund: "false",
    },
  };
  try {
    const manifestBytes = readFileSync(resolve(root, "resources", "manifest.json"));
    const manifest = JSON.parse(manifestBytes.toString("utf8"));
    assert.ok(manifest.skill.files.includes("resources/skill/assets/spec.template.md"));
    const sourceResources = new Map(
      [...manifest.skill.files, ...manifest.runtime].map((resource) => [resource, readFileSync(resolve(root, resource))]),
    );
    const packed = spawnSync("npm", ["pack", "--json", "--pack-destination", tempRoot], npmOptions);
    assert.equal(packed.status, 0, packed.error?.message || packed.stderr);
    const tarball = JSON.parse(packed.stdout)[0].filename;
    const tarballPath = resolve(tempRoot, tarball);

    const installed = spawnSync(
      "npm",
      ["install", "--ignore-scripts", "--no-audit", "--no-fund", "--prefix", installRoot, tarballPath],
      npmOptions,
    );
    assert.equal(installed.status, 0, installed.error?.message || installed.stderr);

    const installedPackageRoot = resolve(installRoot, "node_modules", "plan-governance-cli");
    assert.deepEqual(readFileSync(resolve(installedPackageRoot, "resources", "manifest.json")), manifestBytes);
    for (const [resource, sourceBytes] of sourceResources) {
      assert.deepEqual(readFileSync(resolve(installedPackageRoot, resource)), sourceBytes, resource);
    }
    const installedCli = resolve(installedPackageRoot, "bin", "plan-governance-cli.mjs");
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
    const expectedPlan = sourceResources.get("resources/skill/assets/plan.template.md").toString("utf8")
      .replaceAll("{{title}}", "Installed Demo")
      .replaceAll("{{goal}}", "验证安装后的模板资源")
      .replaceAll("{{status}}", "设计中")
      .replaceAll("{{phase}}", "阶段 0");
    assert.equal(plan, expectedPlan);
    for (const directory of ["specs", "adr", "migrations", "reviews", "fixtures", "attestations"]) {
      assert.equal(existsSync(join(projectRoot, "docs", directory)), false, directory);
    }

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
    assert.equal(installedStepValidation.status, 1, installedStepValidation.stderr);
    assert.match(installedStepValidation.stderr, /goal/);

    const installedNext = spawnSync(process.execPath, [
      installedCli,
      "plan",
      "next",
      "installed-demo",
      "--json",
      "--root",
      projectRoot,
    ], { cwd: root, encoding: "utf8" });
    assert.equal(installedNext.status, 1, installedNext.stderr);
    assert.match(installedNext.stderr, /goal/);

    for (const target of ["codex", "claude"]) {
      const destination = join(tempRoot, target, "skills", "plan-governance");
      const setupArgs = [installedCli, "setup", "--target", target, "--destination", destination];
      const dryRun = spawnSync(process.execPath, [...setupArgs, "--dry-run"], { cwd: root, encoding: "utf8" });
      assert.equal(dryRun.status, 0, dryRun.stderr);
      assert.equal(existsSync(destination), false);

      const synced = spawnSync(process.execPath, setupArgs, { cwd: root, encoding: "utf8" });
      assert.equal(synced.status, 0, synced.stderr);
      for (const resource of manifest.skill.files) {
        const relative = resource.slice("resources/skill/".length);
        assert.deepEqual(readFileSync(join(destination, relative)), sourceResources.get(resource), `${target}: ${resource}`);
      }
      assert.equal(existsSync(join(destination, "scripts")), false);
    }
    exerciseBindingIteration(installedCli, join(tempRoot, "binding-project"));
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
