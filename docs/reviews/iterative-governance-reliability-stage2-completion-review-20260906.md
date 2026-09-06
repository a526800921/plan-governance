# 持续迭代治理优化：阶段 2 独立完成复核

结论：**通过，阶段 2 完成验收通过。** 当前阻塞项：无。可关闭阶段 2，阶段 3 仍需自己的准入。

- 日期：2026-09-06；计划：[iterative-governance-reliability](../plans/iterative-governance-reliability.md)，阶段 2。
- 复核者：`/root/iterative_stage2_acceptance`，新上下文独立只读 subagent，未参与设计、实施或测试编写；主任务按返回结果落档。
- Revision：`336b728d7dacc335a35f2cf97ab39356e3a82ba0` 加派发时混合工作树。
- 范围：verify、release、package scripts、CI、57 项新增回归、AGENTS 发布段、分发维护引用与本阶段治理证据。

## 被审查身份

| 文件 | SHA-256 |
|---|---|
| scripts/verify.mjs | `fbca04629959f57372afb41bc0776ff623d94b566c44e785243e811d374f34ca` |
| scripts/release_npm.mjs | `d746fb669f4aa9148ab515e4489db94732932d66403beb3189c1aefc83444f78` |
| tests/verification_release.test.mjs | `4c6a845d90f12307bb0587aadbc76be5eb331850d6810b83649c54f4fc0b5bb8` |
| .github/workflows/ci.yml | `cf0c5b117591958bcb0adcab2cce200e48ef1a0c7c7e77a6c88c98aec69a5b0b` |
| package.json | `d6d18829d96b010533a4b579d94b77fc9ee26c591c63551898a36d7808f544ad` |
| 专项计划 | `9726baef1ee8abc6c08f9cf8285e74a3d7119dac05e489f32376441c378707ff` |
| 阶段 2 baseline | `4c18a535f1e5eb79414a8074a9e7b79bfbf1e7f2a640011ee55dd85716ff3201` |
| PLAN_MAP | `ccabab6a97d436e2f8b66702e57757aaa7ee50b5fcf1965ad02a2628867e9783` |

派发内容均匹配，复核前后工作区路径列表一致。阶段 1 五份源码/测试 hash 与其第二轮独立完成报告相同；版本仍为 0.3.5，锁文件没有本阶段新差异。

## 完成条件逐项判断

| 条件 | 独立判断 |
|---|---|
| CI 与发布共用三节点 | 通过；严格治理 → 同一 Python 执行 pytest → Node；直接 argv、固定 cwd，CI 和发布均消费 npm run verify |
| 失败矩阵与旧缺陷识别 | 通过；12 个节点×故障组合阻断 registry 操作，解释器、参数、读取及各副作用前后/恢复失败符合契约；两项内存变异暴露旧先切源和漏恢复 |
| 完整验证与兼容 | 通过；Python 203 passed/93.22%，Node 98/98、0 skipped，含 57 项新增；既有版本及阶段 1 差异保留 |
| 文档与阶段边界 | 通过；发布规则和契约一致，四个关键治理链接/锚点可定位，无旧草案重新成为事实源，阶段 3 未准入 |

## 实际命令和证据

| 命令 | 结果与工具输出 |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 npm run verify` | 退出 0；`2c043a`、`1e1faf` |
| `PYTHONDONTWRITEBYTECODE=1 node bin/plan-governance-cli.mjs check . --drift` | 退出 0；`892f2a` |
| `PYTHONDONTWRITEBYTECODE=1 plan-governance-cli check .` | 退出 0；`e9b54e`，全局旧 CLI 只作入口兼容证据 |
| `git diff --check`、源码/差异读取、计划名与事实源 rg、SHA-256、内存链接检查 | 通过；`9582ae`、`e188e2`、`bdb28a` |

工具输出标识属于复核会话，不是仓库路径。完整验证在 macOS 执行；Windows 只验证 VM 命令选择，GitHub CI 未运行。发布路径全部被测试替身拦截，未执行真实发布/切源/版本升级/全局安装。完整 verify 包含已授权的覆盖产物和临时打包/安装测试。宿主计划原有阻塞及共享文件 WARNING 保留，本结论不放行宿主阶段。
