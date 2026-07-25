import test from "node:test";
import assert from "node:assert/strict";
import { cpSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { spawnSync } from "node:child_process";

const root = resolve(import.meta.dirname, "..");
const cli = join(root, "bin", "plan-governance-cli.mjs");
const validFixture = join(root, "tests", "fixtures", "architecture-graph", "valid");

function fixture() {
  const target = mkdtempSync(join(tmpdir(), "plan-impact-"));
  cpSync(validFixture, target, { recursive: true });
  return target;
}

function runPlan(target, request) {
  const input = join(target, "plan-impact.json");
  writeFileSync(input, JSON.stringify(request));
  return spawnSync(process.execPath, [cli, "plan", "impact", "--input", input, "--format", "json", target], { encoding: "utf8" });
}

test("plan impact keeps a normal behavior change on the functional layer", () => {
  const result = runPlan(fixture(), {
    graph_scope: "feature.config-refresh",
    change_kind: "behavior_change",
  });
  assert.equal(result.status, 0, result.stderr);
  const output = JSON.parse(result.stdout);
  assert.deepEqual(output.queried_layers, ["functional"]);
  assert.equal(output.architecture, null);
  assert.equal(output.code, null);
  assert.deepEqual(output.actions, ["必须评估", "建议检查"]);
});

test("plan impact expands an API contract change to the exposed architecture contract", () => {
  const target = fixture();
  const mappings = join(target, "docs", "graph", "architecture", "mappings.yaml");
  writeFileSync(mappings, `${readFileSync(mappings, "utf8")}\n  - type: realized_by\n    from: feature.model-lifecycle\n    to: architecture.modelpad.local-http-api\n    evidence:\n      - kind: document\n        ref: README.md\n        locator: model lifecycle API\n`);
  const result = runPlan(target, {
    graph_scope: "feature.model-lifecycle",
    change_kind: "api_contract_change",
  });
  assert.equal(result.status, 0, result.stderr);
  const output = JSON.parse(result.stdout);
  assert.deepEqual(output.queried_layers, ["functional", "architecture"]);
  assert.deepEqual(output.architecture.nodes.map((item) => item.id), [
    "architecture.modelpad.local-http-api",
    "architecture.modelpad.model-process-management",
    "architecture.modelpad.openapi-contract",
  ]);
  assert.equal(output.code, null);
});

test("plan impact only resolves code when explicitly requested", () => {
  const target = fixture();
  mkdirSync(join(target, "Sources"));
  writeFileSync(join(target, "Sources", "Only.swift"), "final class Only: NSObject {}\n");
  const result = runPlan(target, {
    graph_scope: "feature.model-lifecycle",
    change_kind: "api_contract_change",
    code_locator_requested: true,
    code_anchor: { file: "Sources/Only.swift", symbol: "Only", kind: "class" },
  });
  assert.equal(result.status, 0, result.stderr);
  const output = JSON.parse(result.stdout);
  assert.deepEqual(output.queried_layers, ["functional", "architecture", "code"]);
  assert.equal(output.code.resolution, "unique_candidate");
  assert.equal(output.code.candidates[0].file, "Sources/Only.swift");
});

test("plan impact rejects invalid input and unresolved code anchors", () => {
  const invalid = runPlan(fixture(), { graph_scope: "feature.config-refresh", change_kind: "unknown" });
  assert.notEqual(invalid.status, 0);
  assert.match(invalid.stderr, /change_kind 不受支持/);

  const unresolved = runPlan(fixture(), {
    graph_scope: "feature.model-lifecycle",
    change_kind: "api_contract_change",
    code_locator_requested: true,
    code_anchor: { file: "Sources/Missing.swift", symbol: "MissingBoundary", kind: "class" },
  });
  assert.notEqual(unresolved.status, 0);
  assert.match(unresolved.stderr, /代码定位未唯一确认/);

  const missingArchitecture = fixture();
  const mappings = join(missingArchitecture, "docs", "graph", "architecture", "mappings.yaml");
  writeFileSync(mappings, readFileSync(mappings, "utf8").replace(/  - type: realized_by\n    from: feature\.model-lifecycle[\s\S]*?(?=\n  - type|$)/, ""));
  const missingMapping = runPlan(missingArchitecture, {
    graph_scope: "feature.model-lifecycle",
    change_kind: "api_contract_change",
  });
  assert.notEqual(missingMapping.status, 0);
  assert.match(missingMapping.stderr, /没有可验证的架构映射/);
});
