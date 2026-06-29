# PLAN_MAP

## 治理范围

本仓库跟踪轻量 `plan-governance` 工作流及其 Codex 集成。影响 skill 工作流、模板、验证规则或文档模型的变更需要进入治理。

## 文档权责

- `docs/PLAN_MAP.md` 是状态、依赖、替代/合并/废弃关系、推荐顺序、阻塞项和证据链接的事实源。
- `docs/plans/*.md` 是专项计划的实施细节事实源，记录字段方案、Schema、枚举、Step 0 证据、验证方式和完成条件。
- 总路线图、优先级计划和索引只记录顺序、状态摘要和专项计划链接，不复制字段级方案、枚举、Step 0 细节或完成定义。
- 当专项计划的状态、字段方案、完成条件或验证结果变化时，必须同步 `docs/PLAN_MAP.md` 和所有引用该计划的路线图、优先级计划或索引。
- 验收治理文档时，必须用 `rg` 搜索同名计划、P 编号、状态名和关键字段，检查是否存在重复定义或漂移。
- 如果同一事实在多个文档中重复，保留一个事实源，其他文档改为链接引用。
- 启用治理后，已有草案、历史设计、归档计划和临时分析文档默认只作为背景材料，不再作为规范事实源；后续新规范默认进入 `docs/plans/*.md`、ADR、migration、正式 spec 或 `docs/PLAN_MAP.md`。

## 计划索引

| 计划 | 状态 | 当前阶段 | 依赖 | 证据 |
|---|---|---|---|---|
| [codex-skill-rollout](plans/codex-skill-rollout.md) | 已完成 | 阶段 2 | - | [验证方式](plans/codex-skill-rollout.md#验证方式) |
| [multi-doc-sync-rules](plans/multi-doc-sync-rules.md) | 已完成 | 阶段 1 | codex-skill-rollout | [验证方式](plans/multi-doc-sync-rules.md#验证方式) |
| [draft-history-source-switch](plans/draft-history-source-switch.md) | 已完成 | 阶段 1 | multi-doc-sync-rules | [验证方式](plans/draft-history-source-switch.md#验证方式) |

允许状态：`候选`、`设计中`、`待实施`、`实施中`、`已完成`、`已替代`、`已合并`、`已废弃`。

## 推荐顺序

1. `codex-skill-rollout`
2. `multi-doc-sync-rules`
3. `draft-history-source-switch`

## 依赖关系

| 计划 | 依赖 | 原因 |
|---|---|---|
| codex-skill-rollout | - | - |
| multi-doc-sync-rules | codex-skill-rollout | 依赖已落地的 skill、初始化脚本和治理文档结构 |
| draft-history-source-switch | multi-doc-sync-rules | 依赖既有事实源和多文档同步规则 |

## 替代、合并和废弃

| 计划 | 关系 | 目标 | 原因 |
|---|---|---|---|
| - | - | - | - |

## 当前阻塞项

| 问题 | 推荐方案 | 影响范围 | 是否阻塞当前阶段 | 状态 |
|---|---|---|---|---|
| - | - | - | 否 | 已延后 |

## 完成证据

| 计划 | 阶段 | 证据 |
|---|---|---|
| codex-skill-rollout | 阶段 2 | skill 校验、仓库治理检查和临时目录初始化验证通过 |
| multi-doc-sync-rules | 阶段 1 | `python3 -m pytest` 通过，覆盖率 98.54%；反向引用搜索通过；治理检查通过 |
| draft-history-source-switch | 阶段 1 | 反向引用搜索通过；`python3 -m pytest` 通过，覆盖率 98.54%；`python3 scripts/check_plan_governance.py .` 输出 `计划治理检查通过。` |
