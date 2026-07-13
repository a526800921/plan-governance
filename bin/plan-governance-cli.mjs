#!/usr/bin/env node

import { accessSync, constants } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { spawnSync } from "node:child_process";

const packageRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const checker = resolve(packageRoot, "scripts", "check_plan_governance.py");

try {
  accessSync(checker, constants.R_OK);
} catch (error) {
  console.error(`plan-governance-cli: 找不到包内检查器：${checker}`);
  process.exit(1);
}

const args = [checker, ...process.argv.slice(2)];
const candidates = process.env.PYTHON ? [process.env.PYTHON] : ["python3", "python"];

let result;
for (const command of candidates) {
  result = spawnSync(command, args, { stdio: "inherit" });
  if (!result.error || result.error.code !== "ENOENT") {
    break;
  }
}

if (result?.error) {
  console.error(`plan-governance-cli: 无法启动 Python 检查器：${result.error.message}`);
  process.exit(1);
}

if (result?.signal) {
  console.error(`plan-governance-cli: 检查器被信号 ${result.signal} 终止`);
  process.exit(1);
}

process.exit(result?.status ?? 1);
