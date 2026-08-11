# PLAN_MAP

## 计划索引

| 计划 | 状态 | 当前阶段 | 最后更新 | 依赖 | 证据 |
|---|---|---|---|---|---|
| [alpha](plans/alpha.md) | 候选 | 阶段 1 | 2026-08-11 | - | - |
| [beta](plans/beta.md) | 候选 | 阶段 1 | 2026-08-11 | alpha | - |
| [gamma](plans/gamma.md) | 候选 | 阶段 1 | 2026-08-11 | - | - |

## 阶段关系

| 来源计划 | 来源阶段 | 目标计划 | 目标阶段 | 关系类型 | 解除条件 | 证据 |
|---|---|---|---|---|---|---|
| alpha | 阶段 1 | beta | 阶段 1 | hard_gate | alpha 阶段 1 独立复核通过 | [alpha](plans/alpha.md) |
| alpha | 阶段 1 | beta | 阶段 1 | soft_context | - | [alpha](plans/alpha.md) |
| alpha | 阶段 1 | gamma | 阶段 1 | evidence | alpha 阶段 1 验证证据可定位 | [alpha](plans/alpha.md) |

## 并行与共享写入约束

| 范围 | 允许并行 | 串行边界 | 依据 |
|---|---|---|---|
| alpha/beta | 否 | alpha 先于 beta | [关系](#阶段关系) |

### 机器可检查共享写入约束

| 来源计划 | 来源阶段 | 目标计划 | 目标阶段 | 约束类型 | 共享目标 | 串行顺序 | 解除条件 | 证据 |
|---|---|---|---|---|---|---|---|---|
| alpha | 阶段 1 | beta | 阶段 1 | shared_write_risk | `docs/PLAN_MAP.md` | alpha-before-beta | 写入窗口串行 | [关系](#阶段关系) |
