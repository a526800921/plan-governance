# 持续迭代治理优化：阶段 2 独立准入复核

结论：**通过，达到阶段 2 待实施标准。** 当前准入阻塞：无。仅准入本阶段实现，不代表实现或发布验收通过。

- 日期：2026-09-06；计划：[iterative-governance-reliability](../plans/iterative-governance-reliability.md)，阶段 2。
- 复核者：`/root/iterative_stage2_gate`，新上下文独立只读 subagent，未实施、未修改工作区；主任务按返回结果落档。
- Revision：`336b728d7dacc335a35f2cf97ab39356e3a82ba0` 加派发时混合工作树。
- 范围：统一三节点验证集合、解释器发现、退出分层、发布/恢复控制流、完整目标矩阵、隔离和回滚边界、完成条件及引用。

## 被审查内容

| 文件 | SHA-256 |
|---|---|
| 专项计划 | `454ed032a56e60293c00d3f2b1a6913ea687965ed6421b77584d0cb7b1f86c7f` |
| 阶段 2 baseline | `c9c2cc91434e075eb604bd2bb3308d5012575963e830d1c7b9bea17ffdc451b5` |
| PLAN_MAP | `8522d8a6a777a4e2ef25a7d30f54538ee137b2b7a0ef70f5dcbe8a0df3e9ab62` |
| scripts/release_npm.mjs | `d7c4cbb7e5e6dc13204d6c4e0d41797dadfdf99be17da9f519596dd32eec7111` |
| .github/workflows/ci.yml | `a4da255642dd994d5bce78076907d33a3054b308203a945eca15da8e0ac3b0eb` |

复核前后上述 hash 和工作树列表一致。落档及实施后的内容变化不改写本次受审身份。

## 实际命令和证据

- Python 从 [baseline](../fixtures/iterative-governance-reliability-stage2-verification-baseline.md) 用 `re.findall(r'```bash\n(.*?)\n```', text, re.S)` 提取第二个 bash 块，以 `subprocess.run(['bash'], input=blocks[1], text=True)` 执行。20 场景全部符合记录，真实发布子进程为 0。
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_plan_governance.py . --strict-readiness` 退出 0，保留宿主计划及共享检查器的既有告警。
- `git diff --check` 通过；`git status --short`、`git rev-parse HEAD`、`shasum -a 256` 核实当前内容身份。
- 读取源码、AGENTS、skill、分发维护记录，执行计划名、C02、verify 契约及草案事实源表达的 `rg` 反向引用搜索。仓库没有 docs/adr、docs/migrations，也无本阶段关联新增 ADR/迁移。

工具输出证据：基线 `1b5820`，严格治理 `489827`，反向引用/差异 `44ad5e`，最终身份 `2532e0`。这些是复核会话输出标识，不是仓库路径。

## 判断和边界

源码与基线一致：CI 缺 Node/严格检查，发布先切源后测试，部分切源失败不恢复。当前目标矩阵已明确输入、命令、预期、失败判定、输出位置；三个验证失败必须阻止后续发布，切源尝试起承担恢复责任，已发生的版本/发布副作用不自动回滚或重试。

阶段 1 已有独立完成重审，阶段 2 有自己的替代基线和准入材料。共享写入、工作树保护与宿主回放边界明确。本结论允许落档后把候选文件纳入实施范围；新入口和目标回归尚未实现，必须经完整验证和独立完成验收。未运行 npm/nrm/version/publish、安装、构建或全量测试；不授权实际发布。阶段 3 保持设计中。
