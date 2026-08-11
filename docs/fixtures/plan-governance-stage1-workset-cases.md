# 计划治理阶段 1 工作集设计案例

本文件只属于 `plan-governance-operability-optimization` 计划，用于阶段 1 的 Step 0 和后续实现回归。它不是事实源；工作集字段、派生规则和完成定义以专项计划为准。

## 案例 W1：活跃工作集和历史过滤

### 输入

最小 `PLAN_MAP.md` 包含：

- `alpha`：`设计中`，当前阶段字段齐全，但尚无当前阶段通过的独立复核。
- `beta`：`待实施`，当前阶段通过独立复核。
- `gamma`：`实施中`，当前阶段有结构化的 `下一动作=验证`。
- `old`：`已完成`，有完成证据。

### 预期

- `workset` 默认只返回 `alpha`、`beta`、`gamma`。
- `--include-history` 才追加 `old`。
- `beta` 的 `readiness=ready`、`next_action.kind=implement`。
- `gamma` 的 `readiness=in_progress`、`next_action.kind=verify`。

### 失败判定

默认把 `old` 当作待办；把计划正文的普通自然语言句子猜成 `verify`；或为了生成工作集改写地图/计划。

## 案例 W2：阻塞优先和未知动作

### 输入

- `blocked-plan`：当前阶段存在非占位阻塞项，同时有一条看似可执行的实施步骤。
- `unknown-plan`：状态为 `设计中`，四项阶段准入字段齐全，但没有结构化下一动作和当前阶段通过复核。

### 预期

- `blocked-plan` 返回 `readiness=blocked`、`next_action.kind=resolve_blocker`，不得返回 `implement`。
- `unknown-plan` 返回 `next_action.state=unknown`，不得从自由文本猜测动作。

### 失败判定

阻塞计划仍输出 `implement`；或者把“准备后续工作”“继续推进”等自由文本映射成确定动作。

## 案例 W3：Step 0 和独立复核分层

### 输入

- `step0-plan`：当前阶段的 Step 0、样本矩阵、验证方式或失败/回滚边界有缺失/占位值。
- `review-plan`：上述四项齐全，但最新独立复核不是当前阶段通过结论。

### 预期

- `step0-plan` 返回 `next_action.kind=complete_step0`。
- `review-plan` 返回 `next_action.kind=independent_review`。
- 任一输出都不能直接把计划状态改成 `待实施`。

### 失败判定

把全量测试通过当成准入复核；或者因为有历史通过记录就忽略当前阶段缺失的 Step 0。

## 案例 W4：未知并行关系和历史实施记录

### 输入

- 计划索引中有两个活跃计划，但没有可解析的阶段关系表。
- 其中一个计划有最近实施/验证记录，另一个只有最新独立复核。

### 预期

- 两个计划均可出现在工作集，但 `parallel.state=unknown`，原因明确为缺少阶段关系证据。
- `recent_evidence` 只引用专项计划中可定位的记录，不复制字段级方案。

### 失败判定

根据计划索引排列顺序推断并行；或把历史复核记录当成最近实施进展。

## 案例 W5：旧计划兼容

### 输入

只有旧六列表 `PLAN_MAP.md` 和没有结构化准入摘要的历史计划。

### 预期

- 基础 `check` 和 `--strict-readiness` 的既有结果不变。
- 工作集明确返回结构化信息不足/未知，不要求历史计划补填新字段。

### 失败判定

因为工作集功能启用而阻断旧计划，或伪造 `complete_step0`、`implement` 等确定动作。

## 案例 W6：只读和结构错误

### 输入

- 一个存在重复计划 ID、非法状态或无法读取计划文件的 fixture。
- 一份合法 fixture，记录运行 `workset --json` 前后的文件 hash。

### 预期

- 默认模式输出明确 WARNING/结构错误；严格模式提升为 ERROR；结构错误时不输出确定工作集动作。
- 合法查询前后 `PLAN_MAP.md`、专项计划、Git 索引和外部系统均不变。

### 失败判定

查询写回状态、修复文档、改变 Git 索引，或在结构错误时继续输出可执行动作。

## 阶段 1 Step 0 回放记录

| 日期 | 案例 | 结果 | 证据 | 复核者 |
|---|---|---|---|---|
| 2026-08-10 | W1—W6 设计检查 | 待独立复核 | 本文件与上游计划阶段 1 技术收敛稿 | - |
| 2026-08-10 | W1—W6 行为回归 | 通过，已独立复核 | `tests/npm_cli.test.mjs`、`tests/test_check_plan_governance.py`；npm 39/39；Python 97 passed；覆盖率 91.39%；第三轮独立复核通过 | Codex（实施者） |
