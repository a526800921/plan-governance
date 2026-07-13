import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { accessSync, constants } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import test from "node:test";

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
