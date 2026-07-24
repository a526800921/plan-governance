import test from "node:test";
import assert from "node:assert/strict";
import { cpSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { spawnSync } from "node:child_process";

const root = resolve(import.meta.dirname, "..");
const cli = join(root, "bin", "plan-governance-cli.mjs");
const validFixture = join(root, "tests", "fixtures", "architecture-graph", "valid");

function fixture(mutator) {
  const target = mkdtempSync(join(tmpdir(), "plan-architecture-graph-"));
  cpSync(validFixture, target, { recursive: true });
  mutator?.(target);
  return target;
}

function boundariesPath(target) {
  return join(target, "docs", "graph", "architecture", "modelpad-boundaries.yaml");
}

function mappingsPath(target) {
  return join(target, "docs", "graph", "architecture", "mappings.yaml");
}

function codeMappingsPath(target) {
  return join(target, "docs", "graph", "architecture", "code-mappings.yaml");
}

function validate(target) {
  return spawnSync(process.execPath, [cli, "graph", "validate", "--layer", "architecture", target], { encoding: "utf8" });
}

test("architecture graph validate accepts indexed domain files and cross-layer mappings", () => {
  const result = validate(fixture());
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /架构图谱校验通过/);
  assert.match(result.stdout, /节点 6 个，关系 6 条/);
  assert.match(result.stdout, /代码锚点 3 个/);
});

test("architecture graph validate rejects dangling local relations", () => {
  const target = fixture((rootPath) => {
    const path = boundariesPath(rootPath);
    const content = readFileSync(path, "utf8").replace(
      "to: architecture.modelpad.external-model-service",
      "to: architecture.modelpad.missing-service",
    );
    writeFileSync(path, content);
  });
  const result = validate(target);
  assert.equal(result.status, 1);
  assert.match(result.stderr, /悬空节点/);
});

test("architecture graph validate rejects a realized_by mapping to a functional node", () => {
  const target = fixture((rootPath) => {
    const path = mappingsPath(rootPath);
    const content = readFileSync(path, "utf8").replace(
      "to: architecture.modelpad.config-persistence",
      "to: feature.model-lifecycle",
    );
    writeFileSync(path, content);
  });
  const result = validate(target);
  assert.equal(result.status, 1);
  assert.match(result.stderr, /realized_by\.to 必须指向架构层节点/);
});

test("architecture graph validate rejects unsupported node types", () => {
  const target = fixture((rootPath) => {
    const path = boundariesPath(rootPath);
    const content = readFileSync(path, "utf8").replace("type: data_boundary", "type: function");
    writeFileSync(path, content);
  });
  const result = validate(target);
  assert.equal(result.status, 1);
  assert.match(result.stderr, /type 不受支持/);
});

test("architecture graph validate rejects self-loops", () => {
  const target = fixture((rootPath) => {
    const path = boundariesPath(rootPath);
    const content = readFileSync(path, "utf8").replace(
      "to: architecture.modelpad.local-http-api",
      "to: architecture.modelpad.app-state-orchestration",
    );
    writeFileSync(path, content);
  });
  const result = validate(target);
  assert.equal(result.status, 1);
  assert.match(result.stderr, /不允许自环/);
});

test("architecture graph validate rejects duplicate relations", () => {
  const target = fixture((rootPath) => {
    const path = boundariesPath(rootPath);
    const content = readFileSync(path, "utf8").replace(
      "  - type: exposes\n    from: architecture.modelpad.local-http-api\n    to: architecture.modelpad.openapi-contract",
      "  - type: contains\n    from: architecture.modelpad.app-state-orchestration\n    to: architecture.modelpad.local-http-api",
    );
    writeFileSync(path, content);
  });
  const result = validate(target);
  assert.equal(result.status, 1);
  assert.match(result.stderr, /关系重复/);
});

test("architecture graph validate rejects missing evidence", () => {
  const target = fixture((rootPath) => {
    const path = boundariesPath(rootPath);
    const content = readFileSync(path, "utf8").replace(
      "    evidence:\n      - kind: code\n        ref: README.md\n        locator: local HTTP API",
      "    evidence: []",
    );
    writeFileSync(path, content);
  });
  const result = validate(target);
  assert.equal(result.status, 1);
  assert.match(result.stderr, /缺少 evidence/);
});

test("architecture graph validate rejects a code anchor outside architecture nodes", () => {
  const target = fixture((rootPath) => {
    const path = codeMappingsPath(rootPath);
    const content = readFileSync(path, "utf8").replace(
      "architecture_id: architecture.modelpad.local-http-api",
      "architecture_id: architecture.modelpad.missing",
    );
    writeFileSync(path, content);
  });
  const result = validate(target);
  assert.equal(result.status, 1);
  assert.match(result.stderr, /指向悬空架构节点/);
});

test("architecture graph validate rejects a missing code anchor file", () => {
  const target = fixture((rootPath) => {
    const path = codeMappingsPath(rootPath);
    const content = readFileSync(path, "utf8").replace("file: README.md", "file: Sources/Missing.swift");
    writeFileSync(path, content);
  });
  const result = validate(target);
  assert.equal(result.status, 1);
  assert.match(result.stderr, /code_anchor\.file 不存在/);
});

test("architecture graph validate rejects duplicate code anchors", () => {
  const target = fixture((rootPath) => {
    const path = codeMappingsPath(rootPath);
    const content = readFileSync(path, "utf8").replace(
      "architecture_id: architecture.modelpad.config-persistence\n    code_anchor:\n      file: README.md\n      symbol: ConfigStore\n      kind: class",
      "architecture_id: architecture.modelpad.local-http-api\n    code_anchor:\n      file: README.md\n      symbol: APIHandler\n      kind: class",
    );
    writeFileSync(path, content);
  });
  const result = validate(target);
  assert.equal(result.status, 1);
  assert.match(result.stderr, /代码锚点重复/);
});

test("architecture graph validate accepts a missing optional UID", () => {
  const target = fixture();
  const result = validate(target);
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /代码锚点 3 个/);
});

test("functional graph validate remains the default path", () => {
  const target = fixture();
  const result = spawnSync(process.execPath, [cli, "graph", "validate", target], { encoding: "utf8" });
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /图谱校验通过/);
  assert.doesNotMatch(result.stdout, /架构图谱校验通过/);
});
