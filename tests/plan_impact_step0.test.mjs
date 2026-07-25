import test from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const replay = resolve(root, "scripts", "replay_plan_impact_step0.mjs");
const modelpad = "/Users/jafish/Documents/work/ModelPad";

test("阶段 3 Step 0 原型拒绝缺失和非法计划输入", () => {
  const result = spawnSync(process.execPath, [replay, modelpad, "--check-failures"], { encoding: "utf8" });
  assert.equal(result.status, 0, result.stderr);
  const output = JSON.parse(result.stdout);
  assert.equal(output.failure_contracts.length, 4);
  assert.ok(output.failure_contracts.every((item) => item.result === "nonzero_expected"));
  assert.equal(output.writes, false);
  assert.equal(output.analyze_triggered, false);
});
