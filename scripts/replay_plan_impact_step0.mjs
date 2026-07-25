#!/usr/bin/env node

import assert from "node:assert/strict";
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { spawnSync } from "node:child_process";
import { parse as parseYaml } from "yaml";

const governanceRoot = resolve(import.meta.dirname, "..");
const modelpadRoot = resolve(process.argv[2] ?? "/Users/jafish/Documents/work/ModelPad");
const cli = resolve(governanceRoot, "bin", "plan-governance-cli.mjs");
const fixtureRoot = resolve(modelpadRoot, "docs", "graph", "fixtures", "plan-impact");
const functionalPath = resolve(modelpadRoot, "docs", "graph", "functional.yaml");
const mappingsPath = resolve(modelpadRoot, "docs", "graph", "architecture", "mappings.yaml");

function fail(message) {
  console.error(`阶段 3 Step 0 回放失败：${message}`);
  process.exit(1);
}

function readJson(path) {
  try {
    return JSON.parse(readFileSync(path, "utf8"));
  } catch (cause) {
    fail(`${path} 读取失败：${cause.message}`);
  }
}

function readYaml(path) {
  try {
    return parseYaml(readFileSync(path, "utf8"));
  } catch (cause) {
    fail(`${path} 读取失败：${cause.message}`);
  }
}

function run(args) {
  const result = spawnSync(process.execPath, [cli, ...args, "--format", "json", modelpadRoot], {
    encoding: "utf8",
  });
  if (result.status !== 0) fail(`${args.join(" ")}：${result.stderr.trim()}`);
  try {
    return JSON.parse(result.stdout);
  } catch (cause) {
    fail(`${args.join(" ")} 返回非 JSON：${cause.message}`);
  }
}

function validateRequest(request, label) {
  if (!request || typeof request !== "object") throw new Error(`${label} 必须是对象`);
  if (typeof request.graph_scope !== "string" || !request.graph_scope.startsWith("feature.")) {
    throw new Error(`${label}.graph_scope 必须是功能节点`);
  }
  if (!allowedKinds.has(request.change_kind)) throw new Error(`${label}.change_kind 不受支持`);
  if (request.code_locator_requested && (!request.code_anchor || typeof request.code_anchor !== "object")) {
    throw new Error(`${label}.code_locator_requested=true 时必须提供 code_anchor`);
  }
  if (!Array.isArray(request.upgrade_signals)) throw new Error(`${label}.upgrade_signals 必须是数组`);
}

function decideLayers(request) {
  const queriedLayers = ["functional"];
  const upgradeReasons = {};
  const architectureRequired = ["api_contract_change", "data_migration", "security_change"].includes(request.change_kind)
    || request.upgrade_signals.includes("external_boundary");
  if (architectureRequired) {
    queriedLayers.push("architecture");
    upgradeReasons.architecture = request.change_kind === "behavior_change"
      ? "upgrade_signal=external_boundary"
      : `change_kind=${request.change_kind}`;
  }
  if (request.code_locator_requested) {
    queriedLayers.push("code");
    upgradeReasons.code = "code_locator_requested=true";
  }
  const unqueriedLayers = {};
  if (!queriedLayers.includes("architecture")) unqueriedLayers.architecture = "未命中架构升级信号";
  if (!queriedLayers.includes("code")) unqueriedLayers.code = "未要求具体代码定位";
  return { queriedLayers, upgradeReasons, unqueriedLayers };
}

if (!existsSync(fixtureRoot) || !existsSync(functionalPath) || !existsSync(mappingsPath)) {
  fail("缺少 ModelPad 图谱或阶段 3 fixture");
}

const functional = readYaml(functionalPath);
const mappings = readYaml(mappingsPath);
const boundaries = readYaml(resolve(modelpadRoot, "docs", "graph", "architecture", "modelpad-boundaries.yaml"));
const mappingByFeature = new Map();
for (const relation of mappings.relations ?? []) {
  if (relation.type !== "realized_by") continue;
  const nodes = mappingByFeature.get(relation.from) ?? [];
  nodes.push(relation.to);
  mappingByFeature.set(relation.from, nodes);
}
const architectureRelations = boundaries.relations ?? [];
const architectureById = new Map((boundaries.nodes ?? []).map((node) => [node.id, node]));

function expandArchitectureNodes(seedNodes, changeKind) {
  const nodes = new Set(seedNodes);
  if (changeKind === "api_contract_change") {
    for (const relation of architectureRelations) {
      if (relation.type === "exposes" && nodes.has(relation.from)) nodes.add(relation.to);
    }
  }
  return [...nodes].sort();
}

const samples = readdirSync(fixtureRoot)
  .filter((name) => name.endsWith(".json"))
  .sort()
  .map((name) => ({ name, data: readJson(resolve(fixtureRoot, name)) }));
assert.equal(samples.length, 4, "Step 0 应包含四个计划影响样本");

const allowedKinds = new Set([
  "behavior_change",
  "api_contract_change",
  "internal_refactor",
  "data_migration",
  "security_change",
]);
const summaries = [];

for (const sample of samples) {
  const request = sample.data;
  validateRequest(request, sample.name);
  assert(Array.isArray(request.expected_layers) && request.expected_layers.length > 0, `${sample.name} 缺少 expected_layers`);
  assert(request.expected_upgrade_reasons && typeof request.expected_upgrade_reasons === "object", `${sample.name} 缺少 expected_upgrade_reasons`);
  assert(Array.isArray(request.expected_functional_nodes), `${sample.name} 缺少 expected_functional_nodes`);
  assert(Array.isArray(request.expected_actions) && request.expected_actions.length > 0, `${sample.name} 缺少 expected_actions`);

  const functionalImpact = run(["graph", "impact", "--from", request.graph_scope, "--depth", "2"]);
  assert.equal(functionalImpact.source.id, request.graph_scope, `${sample.name} 功能层 source 不匹配`);
  const impactedIds = [
    ...(functionalImpact.direct ?? []).map((item) => item.id),
    ...(functionalImpact.indirect ?? []).map((item) => item.id),
  ];
  assert(impactedIds.length > 0, `${sample.name} 功能层没有可观察影响`);
  const decision = decideLayers(request);
  assert.deepEqual(decision.queriedLayers, request.expected_layers, `${sample.name} queried_layers 不匹配`);
  assert.deepEqual(decision.upgradeReasons, request.expected_upgrade_reasons, `${sample.name} upgrade_reasons 不匹配`);
  assert.deepEqual(decision.unqueriedLayers, request.expected_unqueried, `${sample.name} unqueried_layers 不匹配`);

  const functionalTypes = new Set(["business", "function", "process", "external_workflow"]);
  const legacyNonFunctionalPrefixes = ["api.", "code.", "test.", "document."];
  const functionalIds = [...new Set([
    ...(functionalImpact.direct ?? []),
    ...(functionalImpact.indirect ?? []),
  ].filter((item) => functionalTypes.has(item.node?.type)
    && !legacyNonFunctionalPrefixes.some((prefix) => item.id.startsWith(prefix))).map((item) => item.id))].sort();
  assert.deepEqual(functionalIds, [...request.expected_functional_nodes].sort(), `${sample.name} functional 影响节点不匹配`);

  const architectureNodes = expandArchitectureNodes(mappingByFeature.get(request.graph_scope) ?? [], request.change_kind);
  if (decision.queriedLayers.includes("architecture")) {
    assert(architectureNodes.length > 0, `${sample.name} 需要架构层但没有 realized_by 映射`);
    for (const node of request.expected_architecture_nodes ?? []) {
      assert(architectureNodes.includes(node), `${sample.name} 缺少架构映射：${node}`);
    }
  }

  let codeResolution = "skipped";
  if (decision.queriedLayers.includes("code")) {
    assert(request.code_anchor, `${sample.name} 要求代码定位但缺少 code_anchor`);
    const candidates = run([
      "graph", "code", "candidates",
      "--file", request.code_anchor.file,
      "--symbol", request.code_anchor.symbol,
      "--kind", request.code_anchor.kind,
    ]);
    assert.equal(candidates.resolution, "unique_candidate", `${sample.name} 代码锚点未唯一确认`);
    codeResolution = candidates.resolution;
  }

  const hasTestEvidence = [...(functionalImpact.direct ?? []), ...(functionalImpact.indirect ?? [])]
    .some((item) => (item.node?.evidence ?? []).some((evidence) => evidence.kind === "test"));
  if (request.expected_test_mapping.length > 0) {
    assert(hasTestEvidence, `${sample.name} 期望测试映射但基线没有测试证据`);
    const evidenceText = JSON.stringify([
      functionalImpact,
      ...(request.expected_architecture_nodes ?? []).map((id) => architectureById.get(id)),
    ]);
    for (const testPath of request.expected_test_mapping) assert(evidenceText.includes(testPath), `${sample.name} 缺少测试证据：${testPath}`);
  } else assert(!hasTestEvidence, `${sample.name} 应明确输出无可用测试映射`);

  const actualActions = ["必须评估", hasTestEvidence ? "必须测试" : "建议检查"];
  assert.deepEqual(actualActions, request.expected_actions, `${sample.name} actions 不匹配`);

  summaries.push({
    sample: sample.name,
    graph_scope: request.graph_scope,
    change_kind: request.change_kind,
    queried_layers: decision.queriedLayers,
    upgrade_reasons: decision.upgradeReasons,
    unqueried_layers: decision.unqueriedLayers,
    functional_nodes: functionalIds,
    legacy_impact_count: impactedIds.length,
    architecture_nodes: decision.queriedLayers.includes("architecture") ? architectureNodes : [],
    code_resolution: codeResolution,
    test_mapping: hasTestEvidence ? "available" : "无可用测试映射",
    actions: request.expected_actions,
  });
}

let failureContracts = [];
if (process.argv.includes("--check-failures")) {
  const invalidRequests = [
    ["missing graph_scope", { change_kind: "behavior_change", upgrade_signals: [] }],
    ["invalid change_kind", { graph_scope: "feature.config-refresh", change_kind: "unknown", upgrade_signals: [] }],
    ["missing code anchor", { graph_scope: "feature.model-lifecycle", change_kind: "api_contract_change", code_locator_requested: true, upgrade_signals: [] }],
    ["invalid upgrade signals", { graph_scope: "feature.pdf-workflow-reuse", change_kind: "behavior_change", upgrade_signals: "external_boundary" }],
  ];
  for (const [label, request] of invalidRequests) {
    assert.throws(() => validateRequest(request, label), `${label} 应被拒绝`);
  }
  failureContracts = invalidRequests.map(([label]) => ({ label, result: "nonzero_expected" }));
}

console.log(JSON.stringify({
  baseline: "ModelPad 真实仓库只读回放",
  samples: summaries,
  writes: false,
  analyze_triggered: false,
  failure_contracts: failureContracts,
}, null, 2));
