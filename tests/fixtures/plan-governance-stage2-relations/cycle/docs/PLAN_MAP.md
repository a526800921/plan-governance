# PLAN_MAP

## 计划索引

| 计划 | 状态 | 当前阶段 | 最后更新 | 依赖 | 证据 |
|---|---|---|---|---|---|
| [alpha](plans/alpha.md) | 候选 | 阶段 1 | 2026-08-11 | - | - |
| [beta](plans/beta.md) | 候选 | 阶段 1 | 2026-08-11 | - | - |

## 阶段关系

| 来源计划 | 来源阶段 | 目标计划 | 目标阶段 | 关系类型 | 解除条件 | 证据 |
|---|---|---|---|---|---|---|
| alpha | 阶段 1 | beta | 阶段 1 | hard_gate | alpha 完成 | [alpha](plans/alpha.md) |
| beta | 阶段 1 | alpha | 阶段 1 | evidence | beta 完成 | [beta](plans/beta.md) |
| alpha | 阶段 1 | alpha | 阶段 1 | soft_context | 仅上下文 | [alpha](plans/alpha.md) |
