# 持续迭代治理优化：阶段 1 独立准入复核

结论：**通过，达到阶段 1 待实施标准。** 当前无阶段 1 准入阻塞；不代表缺陷已修复，不放行其他阶段。

- 日期：2026-09-06。
- 计划：[iterative-governance-reliability](../plans/iterative-governance-reliability.md)，阶段 1。
- 复核者：`/root/iterative_stage1_gate`，新上下文独立只读 subagent，未参与实施、未修改工作区；主执行者按返回报告落档。
- Revision：`336b728d7dacc335a35f2cf97ab39356e3a82ba0` 加派发时混合未提交工作树。
- 范围：Step 0、22 类预期矩阵、默认/严格退出码、JSON 兼容、阻塞与复核派生、当前记录、hook 一致性、验证及回滚边界。

## 被审查内容

| 文件 | SHA-256 |
|---|---|
| 专项计划 | `3928e624a69c617bb4b64d9d515409bc39ae8621c54aac788b6dfff2be296a5c` |
| 阶段 1 fixture | `0c770adc50c7ca7a785126cfcd33d53a8706913ee5883a4d6e93e4417def3eeb` |
| 阶段 0 fixture | `74aceb549fb5fb41223248803c6b525a56deb798aad8d5d2770e5bec14a930b4` |
| PLAN_MAP | `38ccb3b94508a93a1c7ca9209537bd9be28dacda0146ced5abf1479dae04ecfa` |
| scripts/check_plan_governance.py | `b17bbaf97ebb1c5de3fff9d4b8d2a35d442e2a2e739cfd1453a2081d83f7ea4e` |
| scripts/plan_governance_hook.py | `08e4af00d5fc01ecc6fa6fb9794daeb095344a6164f47a04abf6e31cbbec26a7` |
| bin/plan-governance-cli.mjs | `d71a5c9a556b7349187a36902664eece3495fa85ddfcfb2ca4a8488a5feea029` |
| tests/test_check_plan_governance.py | `52985957dd0364000cfb1d14738c98226ca7b117794ed48318bb2408ec7ca4f7` |
| tests/test_plan_governance_hooks.py | `46e9e6900d4f76708dcaf3ac84e7db685695253d0171405b414edd2853618cb8` |
| tests/npm_cli.test.mjs | `8a922588e9224018ba7c42d57531ad97dcd2b65dc5f39c9459b856809ac2efa5` |

复核前后内容 hash 与工作区列表一致。落档、状态转换和后续实施会改变当前文件，以上保留历史受审身份。

## 实际命令与证据

| 命令或检查 | 结果 |
|---|---|
| Python 提取阶段 1 fixture 原始 bash，经 `subprocess.run(['bash','--noprofile','--norc'], input=block, ...)` 执行并逐行比对结果表 | 退出 0，22/22 行匹配；88 次真实 Node→Python，无 stderr，输入 hash 不变，临时目录清理 |
| `PYTHONDONTWRITEBYTECODE=1 node bin/plan-governance-cli.mjs check .` | 退出 0 |
| 同上加 `--strict-readiness`、`--stale-days 10` | 均退出 0 |
| 同上加 `--drift` | 退出 0，一条已记录的地图归属 WARNING |
| `PYTHONDONTWRITEBYTECODE=1 node bin/plan-governance-cli.mjs workset . --json`，以及加 `--strict-readiness` | 均退出 0、Schema 1；宿主计划仍重现空阻塞/independent_review 的既知缺陷 |
| `git diff --check`；反向引用、关键契约、草案事实源 rg；相关源码读取 | 通过，未见新增事实源漂移 |
| 屏蔽代码块后的本地链接检查 | 计划与阶段 1 fixture 的 46 个链接有效 |

复核工具输出证据：fixture `6d3b08`，普通/严格 `53ff04` / `087bfa`，workset `4a6b53` / `4ea287`，drift `4fad87`，链接/最终 hash `03a1c3`。可重放命令和结果在 [阶段 1 fixture](../fixtures/iterative-governance-reliability-stage1-cli-cases.md)。工具输出标识是此次复核会话证据，不是仓库文件路径。

## 判断与实施约束

本阶段有自己的真实文件基线和修复目标矩阵，覆盖主要正反场景；默认硬错误、新增告警、严格失败和工作集动作分别定义，现有 JSON 字段不变。源码支持既知缺陷及共享派生方案，未证明需要修改 Node 启动器。完成条件要求针对性/完整回归、覆盖证据与独立完成复核；范围、失败策略、精确回滚和混合工作树保护明确。

1. 实施前补全 `阶段 N 最近验证记录` 与 `阶段 N 最近实施/验证记录` 两个精确别名。前者已在输入及预期矩阵固定，属于非阻塞表述补全。
2. 保持动态复用的测试 helper 输入，尤其 `design_unreviewed`；若需变更输入，记录新身份并追加结果，不沿用旧基线。
3. 修改生产文件前同步影响范围、最新复核和地图。完整 pytest/npm、安装 smoke 及修复后的 hook 回归尚未执行。

既有 [phase-local-review-dispatch](../plans/phase-local-review-dispatch.md#最新独立准入复核) 阶段 2 仍设计中，六类宿主输出缺失的失败复核有效。本次未执行实现、全套测试、安装、发布、attest 或外部操作。
