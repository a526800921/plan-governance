# 计划治理阶段 0 设计案例

本文件是阶段 0 的可复核设计样本，不是新的事实源。字段、枚举和完成定义以对应专项计划为准；本文件只固定输入形态、预期行为和失败判定，供阶段 0 人工回放以及阶段 1—3 转换为自动 fixture。

## 案例 A：当前工作集

### 输入

最小 `PLAN_MAP.md` 包含三个活跃计划：

- `alpha`：当前阶段缺少结构化 Step 0 证据，因此动作可确定为 `complete_step0`。
- `beta`：当前阶段存在明确阻塞项。
- `gamma`：只有自然语言实施步骤，没有可派生的下一动作。

另有两个 `已完成` 或 `已废弃` 计划。

### 预期

- 工作集只包含 `alpha`、`beta`、`gamma`。
- `alpha` 的动作必须表示为 `complete_step0`。
- `beta` 显示 `resolve_blocker`。
- `gamma` 的 `next_action.state=unknown`，不得从自然语言猜测。
- 没有阶段关系证据时，计划的 `parallel.state=unknown`。

### 失败判定

历史计划出现在工作集；`gamma` 被猜测为“实施”；或未知并行关系被输出为允许并行。

## 案例 B：阶段关系与共享写入

### 输入

阶段关系包含：

| 来源计划 | 来源阶段 | 目标计划 | 目标阶段 | 关系类型 | 解除条件 |
|---|---|---|---|---|---|
| `alpha` | 阶段 0 | `beta` | 阶段 0 | `soft_context` | 无，仅提供上下文 |
| `alpha` | 阶段 0 | `beta` | 阶段 1 | `hard_gate` | `alpha` 阶段 0 独立准入通过 |
| `alpha` | 阶段 1 | `beta` | 阶段 1 | `evidence` | 提供指定验证快照 |

旧计划级依赖摘要包含：`beta` 依赖 `alpha`；另有一个对照计划 `gamma` 仅保留相同摘要，但阶段关系中只有 `soft_context`。

另有一条共享写入约束：`alpha` 和 `beta` 的阶段 1 都会修改 `scripts/check_plan_governance.py`，写入策略为串行。

### 预期

- `alpha`/`beta` 阶段 0 可以逻辑并行设计。
- `beta` 阶段 1 不能绕过 `alpha` 阶段 0 的 `hard_gate`。
- `evidence` 不自动改变 `beta` 的计划生命周期。
- `beta` 的旧依赖摘要可由 `hard_gate/evidence` 投影保持一致；`gamma` 的旧摘要与仅有 `soft_context` 的阶段关系冲突并输出 WARNING。
- 共享写入约束提示串行写入，但不变成业务硬门禁边。

### 失败判定

把 `shared_write_risk` 当作 `hard_gate`；或因为阶段 0 存在 `soft_context` 就强制串行。

## 案例 C：状态、进展与 Attestation

### 输入

同一计划包含：

- 最新独立准入复核：阶段 1，结论“通过”。
- 当前阶段最近实施记录：阶段 1 已完成步骤 S1，证据链接到测试输出。
- 一份 `purpose=release_gate` 的 Attestation，`review_status=current`。
- 计划文件 hash 已变化，但尚未有新的 Attestation。
- 另有兼容样本：旧格式 `docs/attestations/legacy.json` 没有 `purpose`。
- 失败样本：`supersedes` 指向不存在文件、两个同 purpose 快照都声明 `current`、以及两个快照互相替代形成环。

### 预期

- 准入结论、最近实施记录和 Attestation 状态分别输出。
- hash 漂移为 WARNING，并提示人工复核。
- 当前实施记录不能覆盖最新独立准入复核。
- release gate 不因机械检查自动接受。
- 旧格式快照按 `phase_completion` 归类；失败样本返回结构错误，不产生有效 `current`。

### 失败判定

把实施记录当成新的独立准入结论；把 hash 漂移的快照继续显示为有效 current；或接受缺失目标、重复 current、替代环。

## 案例 D：治理 Drift 覆盖

### 输入

当前计划的当前阶段包含以下显式声明：

```markdown
### 阶段证据

- `docs/evidence/alpha-stage0.md`
```

一次工作区变更同时包含：

1. `docs/plans/alpha.md` 自身变更。
2. `docs/PLAN_MAP.md` 中可唯一定位到 `alpha` 的计划行变更。
3. `docs/evidence/alpha-stage0.md`，由 `alpha` 当前阶段显式声明。
4. `docs/notes/unrelated.md`，没有任何计划声明。

另有失败输入：阶段证据清单使用绝对路径、通配符或仓库外路径。

### 预期

- 前三类变更按计划归属覆盖。
- `unrelated.md` 保留 Drift WARNING。
- 无法唯一归属的地图跨计划变更保留 WARNING。
- 绝对路径、通配符和越界路径不被接受为显式阶段证据。

### 失败判定

全局忽略 `docs/`；把所有地图变更自动覆盖给所有活跃计划；或接受非法阶段证据路径。

## 人工回放记录

| 日期 | 案例 | 结果 | 证据 | 复核者 |
|---|---|---|---|---|
| 2026-08-10 | A—D 设计检查 | 待独立复核 | 本文件与上游计划技术收敛稿 | - |
