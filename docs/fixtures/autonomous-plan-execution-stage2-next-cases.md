# autonomous-plan-execution 阶段 2：next 样本

本文件是阶段 2 的 Step 0 与行为 fixture。它描述 `plan-governance-cli plan next <plan> [--json]` 的输入、预期逻辑状态和失败判定；查询只读，不授权自动执行、状态写回或阶段自动准入。

## 公共约束

- 只有显式声明 `execution_mode: autonomous-continuous` 的计划才进入结构化查询；旧计划返回 `not_enabled`。
- 查询只读：不执行动作、命令、Git 操作或外部系统操作，不修改计划、地图、步骤状态和证据。
- `serial` 缺省保持安全兼容；显式 `parallel` 才允许多个互不依赖的 ready steps。
- `shared_write_risk` 只产生约束或建议顺序，不自动改写为前置关系。
- `complete` 不代表独立验收通过；阶段门仍由当前计划和独立复核事实源决定。

## 案例 N1：未启用旧计划

输入基线：

```markdown
# legacy-plan

## 实施步骤

1. 完成旧计划中的动作。
```

没有 `execution_mode`，也没有结构化七列表。

候选预期：

```json
{
  "status": "not_enabled",
  "ready_steps": [],
  "next_action": {"kind": "none", "reason": "plan_not_enabled"}
}
```

失败判定：把旧计划标为结构错误、强制迁移，或返回任何可执行步骤。

## 案例 N2：串行前置未满足

输入基线：

```yaml
execution_mode: autonomous-continuous
execution_policy: serial
steps:
  - id: S1
    depends_on: []
    status: 未开始
    evidence: null
  - id: S2
    depends_on: [S1]
    status: 未开始
    evidence: null
```

候选预期：`S1` 是唯一可候选的下一步骤；`S2` 必须因为 `S1` 未完成而阻塞，不能被跳过。

失败判定：返回 `S2` 为 ready，或把未完成的 `S1` 视为已完成。

## 案例 N3：显式并行 ready 集合

输入基线：

```yaml
execution_mode: autonomous-continuous
execution_policy: parallel
steps:
  - id: S1
    depends_on: []
    status: 已完成
    evidence: tests/s1.log
  - id: S2
    depends_on: [S1]
    status: 未开始
    evidence: null
  - id: S3
    depends_on: [S1]
    status: 未开始
    evidence: null
```

候选预期：`ready_steps` 同时包含 `S2` 和 `S3`，因为两者互不依赖且 `S1` 已完成。

失败判定：漏报其中一个、重复返回，或在没有约束的情况下隐式串行化。

## 案例 N4：共享写入风险

输入基线：

```yaml
execution_mode: autonomous-continuous
execution_policy: parallel
steps:
  - id: S2
    depends_on: []
    status: 未开始
  - id: S3
    depends_on: []
    status: 未开始
```

对应专项计划的正式来源为可选 `## 执行约束` 表，字段为“约束 ID / 类型 / 步骤 / 共享目标 / 建议顺序 / 说明”。候选预期：保留 `S2`、`S3` 的独立性，同时在 `constraints` 中提示共享写入和建议顺序；不能凭空增加 `S2 -> S3` 的前置关系。

```markdown
## 执行约束

| 约束 ID | 类型 | 步骤 | 共享目标 | 建议顺序 | 说明 |
|---|---|---|---|---|---|
| C1 | shared_write_risk | S2,S3 | docs/PLAN_MAP.md | S2 -> S3 | 两个步骤都可能写入同一目标 |
```

失败判定：静默忽略共享风险，或把未声明的依赖写回步骤模型。

## 案例 N5：缺证据或阻塞步骤

输入基线：

```yaml
execution_mode: autonomous-continuous
execution_policy: serial
steps:
  - id: S1
    depends_on: []
    status: 阻塞
    evidence: null
  - id: S2
    depends_on: [S1]
    status: 未开始
    evidence: null
```

候选预期：状态为 `blocked`，指出 `S1` 的阻塞和证据缺失，`S2` 不能成为 ready step。

另一种缺证据输入是步骤声明为 `已完成` 但证据列为 `-`；`plan next` 必须返回 `blocked`，原因码为 `missing_evidence`，而不是把它作为可推进完成或无定位的结构错误吞掉。

失败判定：自动补证据、自动改状态、把 `S2` 返回为 ready，或只返回无定位原因的笼统提示。

## 案例 N6：阶段门未开放

输入基线：

```markdown
<!-- PLAN_MAP.md 的相关行：当前阶段仍为阶段 1，计划级状态仍为实施中 -->
| [gate-demo](plans/gate-demo.md) | 实施中 | 阶段 1 | 2026-08-11 | - | fixture |

<!-- gate-demo.md 的结构化步骤已全部收口；阶段 2 没有自己的 Step 0 和独立准入复核 -->
execution_mode: autonomous-continuous
execution_policy: serial

## 当前阶段

当前阶段：阶段 1

### 执行清单

| 步骤 ID | 前置步骤 | 动作 | 证据 | 完成条件 | 状态 | 分支记录 |
|---|---|---|---|---|---|---|
| S1 | - | 收口阶段 1 | tests/s1.log | 阶段 1 收口 | 已完成 | - |
```

候选预期：

```json
{
  "status": "phase_gate",
  "ready_steps": [],
  "blocked_steps": [],
  "next_action": {"kind": "await_phase_gate", "reason": "next_phase_not_admitted"}
}
```

查询不得修改 `PLAN_MAP.md`，不得把阶段完成自动解释为下一阶段可实施。

失败判定：自动切换当前阶段、返回下一阶段 ready steps，或省略缺失的独立准入原因。

## 案例 N7：完成但不替代验收

输入基线：

```markdown
<!-- 临时计划 terminal-demo：这是一个没有后继阶段的终态计划，不改动当前 PLAN_MAP.md -->
execution_mode: autonomous-continuous
execution_policy: serial

## 当前阶段

当前阶段：阶段 2

### 执行清单

| 步骤 ID | 前置步骤 | 动作 | 证据 | 完成条件 | 状态 | 分支记录 |
|---|---|---|---|---|---|---|
| S1 | - | 完成终态动作 | tests/s1.log | 阶段完成条件满足 | 已完成 | - |

阶段完成条件证据：tests/stage-complete.log
独立验收：尚未进行
```

候选预期：

```json
{
  "status": "complete",
  "ready_steps": [],
  "blocked_steps": [],
  "next_action": {"kind": "await_independent_acceptance", "reason": "implementation_complete_acceptance_pending"}
}
```

不得把 `complete` 当作独立验收通过，或继续生成无依据步骤。

失败判定：把 `complete` 当作独立验收通过，或因为缺少下一步骤而自动修改计划状态。

## 案例 N8：查询无写入

输入基线：复制一个包含上述步骤表的临时计划目录，记录 `docs/PLAN_MAP.md`、专项计划、fixture 和 Git 状态的 hash。

可执行验证：

```bash
test_plan="autonomous-plan-execution"
before_hash="$(shasum docs/PLAN_MAP.md docs/plans/autonomous-plan-execution.md docs/fixtures/autonomous-plan-execution-stage2-next-cases.md)"
before_status="$(git status --short)"
node bin/plan-governance-cli.mjs plan next "$test_plan" --json >/tmp/autonomous-plan-next.out 2>&1
after_hash="$(shasum docs/PLAN_MAP.md docs/plans/autonomous-plan-execution.md docs/fixtures/autonomous-plan-execution-stage2-next-cases.md)"
after_status="$(git status --short)"
test "$before_hash" = "$after_hash"
test "$before_status" = "$after_status"
```

当前专项计划本身没有声明 `execution_mode`，因此实际预期是返回结构化 `not_enabled`、退出码为 0；N1—N8 的启用计划行为由真实临时目录测试覆盖。查询退出码、JSON 输出和 hash 均可复现；查询前后文件与 Git 状态一致。

失败判定：修改任何计划治理文件、步骤状态、Git 索引或外部系统，或因输出不稳定导致无法复现。
