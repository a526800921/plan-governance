import test from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { spawnSync } from "node:child_process";

const root = resolve(import.meta.dirname, "..");
const cli = join(root, "bin", "plan-governance-cli.mjs");

function fixture(content) {
  const target = mkdtempSync(join(tmpdir(), "plan-graph-"));
  mkdirSync(join(target, "docs", "graph"), { recursive: true });
  writeFileSync(join(target, "README.md"), "fixture evidence\n");
  writeFileSync(join(target, "docs", "graph", "functional.yaml"), content);
  return target;
}

const valid = `schema_version: 1
project:
  id: demo
  name: Demo
nodes:
  - id: feature.one
    type: function
    name: Feature One
    evidence:
      - kind: document
        ref: README.md
        locator: fixture evidence
  - id: api.one
    type: api
    name: API One
    evidence:
      - kind: document
        ref: README.md
        locator: fixture evidence
relations:
  - from: feature.one
    type: exposes
    to: api.one
    evidence:
      - kind: document
        ref: README.md
        locator: fixture evidence
`;

test("graph validate accepts a valid YAML graph", () => {
  const target = fixture(valid);
  const result = spawnSync(process.execPath, [cli, "graph", "validate", target], { encoding: "utf8" });
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /图谱校验通过/);
});

test("graph validate rejects dangling relations", () => {
  const target = fixture(valid.replace("to: api.one", "to: api.missing"));
  const result = spawnSync(process.execPath, [cli, "graph", "validate", target], { encoding: "utf8" });
  assert.equal(result.status, 1);
  assert.match(result.stderr, /悬空节点/);
});

test("graph validate rejects self-loops", () => {
  const target = fixture(valid.replace("to: api.one", "to: feature.one"));
  const result = spawnSync(process.execPath, [cli, "graph", "validate", target], { encoding: "utf8" });
  assert.equal(result.status, 1);
  assert.match(result.stderr, /不允许自环/);
});

test("graph validate accepts cycles and impact analysis deduplicates them", () => {
  const target = fixture(`${valid}
  - from: api.one
    type: implements
    to: feature.one
    evidence:
      - kind: document
        ref: README.md
        locator: fixture evidence
`);
  const validateResult = spawnSync(process.execPath, [cli, "graph", "validate", target], { encoding: "utf8" });
  assert.equal(validateResult.status, 0, validateResult.stderr);
  const impactResult = spawnSync(process.execPath, [cli, "graph", "impact", "--from", "feature.one", "--depth", "3", "--format", "json", target], { encoding: "utf8" });
  assert.equal(impactResult.status, 0, impactResult.stderr);
  const output = JSON.parse(impactResult.stdout);
  assert.deepEqual(output.direct.map((item) => item.id), ["api.one"]);
  assert.deepEqual(output.indirect, []);
});

test("graph impact returns direct and indirect results as JSON", () => {
  const target = fixture(`schema_version: 1
project:
  id: demo
  name: Demo
nodes:
  - id: feature.one
    type: function
    name: Feature One
    evidence:
      - kind: document
        ref: README.md
        locator: fixture evidence
  - id: process.one
    type: process
    name: Process One
    evidence:
      - kind: document
        ref: README.md
        locator: fixture evidence
  - id: api.one
    type: api
    name: API One
    evidence:
      - kind: document
        ref: README.md
        locator: fixture evidence
relations:
  - from: feature.one
    type: implements
    to: process.one
    evidence:
      - kind: document
        ref: README.md
        locator: fixture evidence
  - from: process.one
    type: exposes
    to: api.one
    evidence:
      - kind: document
        ref: README.md
        locator: fixture evidence
`);
  const result = spawnSync(process.execPath, [cli, "graph", "impact", "--from", "feature.one", "--depth", "2", "--format", "json", target], { encoding: "utf8" });
  assert.equal(result.status, 0, result.stderr);
  const output = JSON.parse(result.stdout);
  assert.equal(output.direct[0].id, "process.one");
  assert.equal(output.indirect[0].id, "api.one");
});
