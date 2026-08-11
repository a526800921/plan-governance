# 计划：自主连续执行

## 背景

`plan-governance` 已加入“按计划自主推进至完成，不跳步”的 skill 行为约定：执行者不必为例行步骤逐次请求继续，但必须逐项执行、留证并遵守阶段准入。

该约定目前是策略层规则，不能机械证明“每一步均已执行”。现有计划模板只有自然语言“实施步骤”，检查器只校验计划级状态、阶段准入、影响范围和完成证据，不能识别下一未完成步骤、步骤证据缺失或被静默跳过的步骤。

本计划将为自愿采用“自主连续执行”的专项计划设计轻量、可检查的步骤模型。它依赖 [plan-governance-operability-optimization](plan-governance-operability-optimization.md) 冻结当前工作集、证据状态和阶段关系的兼容边界；不修改任何业务项目，也不实现通用工作流引擎。

本计划与上游计划都可能涉及检查器、CLI、skill、模板和测试。阶段 0 只编辑本计划、自主执行设计案例和 `PLAN_MAP.md`；阶段 1 起必须等待上游相关契约完成并采用串行写入，不将这些共享文件作为两个活跃计划的并行实现目标。

## 目标

- 为选择自主连续执行的计划提供可机器读取的步骤清单，逐步声明前置条件、动作、必需证据、完成条件和失败/不适用分支。
- 让执行者或只读 CLI 能确定“当前可执行步骤集合”，并在前置步骤或证据缺失时拒绝把后续步骤标为完成。
- 让步骤级执行状态与计划级阶段状态保持清晰分层：步骤进度留在专项计划，阶段与计划生命周期仍以 `PLAN_MAP.md` 为准。
- 保留“短指令触发自主执行、仅在异常时汇报”的体验，同时不允许跨越 Step 0、独立复核或未准入阶段。
- 保持对现有 Markdown 计划的兼容；未选择该模式的计划无需补充步骤表或改变检查结果。

## 非目标

- 不构建自动执行 shell、代码修改、部署或外部操作的工作流引擎；CLI 只读取、校验和提示下一步。
- 不自动批准独立复核，不允许实施者用步骤状态取代独立验收结论。
- 不为所有历史计划回填步骤级日志，也不要求普通小任务进入该模式。
- 不以“自主连续执行”为由跳过失败分支、合并步骤、自动跨越阶段，或放宽现有安全和授权边界。

## 需求探索

### 已确认事实

- 用户希望对简单且目标明确的计划直接发出“推进到完成计划”，执行者连续推进，不需要逐步请求继续；但每一个步骤、证据、验证、独立复核和阶段门禁都必须实际执行。
- 本计划只设计可选的机器可读步骤模型、只读校验和下一步骤查询，不构建自动执行 shell、代码修改、部署或外部操作引擎。
- 上游计划提供只读派生工作集、阶段关系事实源、实施/验证记录和 Drift/Attestation 的兼容边界；本计划不重新定义这些事实源。
- 阶段 0 设计可以并行推进，但阶段 1 起与上游共享的 CLI、检查器、模板、skill、测试和 `PLAN_MAP.md` 写入必须串行；共享写入风险不是自动硬门禁依赖。

### 暂定假设与验证方式

- 结构化步骤只对明确启用自主模式的计划生效；没有执行模式或执行清单的旧计划继续走兼容的人工计划流程，查询入口应明确返回“未启用/不适用”，而不是要求历史计划补填。
- `next` 查询应返回当前可执行步骤集合，而不是永远假设只有一个步骤；只有计划显式声明串行约束时才收敛为单个步骤。通过两条相互独立的 ready steps fixture 验证。
- 步骤状态是实施事实记录，不是独立验收结论；失败步骤默认阻塞后续步骤，除非计划明示进入修复或不适用分支并记录替代证据。
- 证据允许命令输出、测试名称、提交、文档锚点或可定位运行记录，但必须可复现或可核查；是否要求结构化证据类型仍待阶段 0 冻结。

### 范围与非目标

本计划只覆盖可选步骤清单、顺序与依赖、状态、证据、失败/不适用分支、只读下一步骤查询和与阶段门的兼容边界。它不覆盖自动执行外部命令、自动写文件、自动批准、自动接受独立复核或自动跨越未准入阶段。

普通小任务和未启用自主模式的历史计划不纳入步骤级迁移；本计划也不把步骤表变成 `PLAN_MAP.md` 的第二套计划级状态事实源。

### 候选方案与取舍

| 能力 | 采用方向 | 放弃或延后的方案 | 取舍 |
|---|---|---|---|
| 步骤表达 | 优先专项计划内可解析 Markdown 表 | 一开始强制外部 JSON/YAML manifest 或只依赖自然语言 | 迁移成本低；复杂分支表达能力需要 fixture 验证 |
| 下一步骤 | 输出所有当前可执行步骤，按串行约束收敛 | 永远只输出一个“唯一下一步骤” | 支持并行计划/步骤；调用者需要处理集合和冲突约束 |
| 旧计划 | 查询明确“不适用”，默认检查结果不变 | 强制历史计划补填步骤 | 保持兼容；旧计划不能获得机械跳步证明 |
| 执行能力 | 只读解析、校验、提示 | 通用自动执行器 | 保留授权、安全和回滚边界；自动化收益暂不覆盖 |

### 未决问题

| 问题 | 推荐方案 | 是否阻塞当前阶段 | 状态 |
|---|---|---|---|
| 步骤表的精确字段、ID 规则和 Markdown 解析限制是什么？ | 采用 ID、前置步骤、动作、证据、完成条件、状态、分支记录七列；复杂分支先用分支记录表达。 | 否 | 已收敛，待阶段 1 实施 |
| 步骤状态及其允许转换是什么？ | 采用未开始、执行中、已完成、阻塞、不适用；失败默认转阻塞，不静默转完成。 | 否 | 已收敛，待阶段 1 实施 |
| 多个 ready steps 的输出和共享写入约束如何表达？ | 返回 ready steps 集合，并单独输出串行/共享写入约束；不把 `shared_write_risk` 伪装成前置步骤。 | 否 | 已收敛，待阶段 1 实施 |
| 什么证据可完成步骤、谁可以更新步骤状态？ | 实施者可记录事实，证据必须可复现或可核查；独立复核仍不由步骤状态替代。 | 否 | 已收敛，待阶段 1 实施 |
| 如何与上游阶段关系、实施记录和 Drift 契约保持单一事实源？ | 步骤只记录当前阶段执行事实，引用上游契约，不复制地图级字段；上游契约变化先同步计划。 | 否 | 已收敛，待阶段 1 实施 |
| 是否直接实现自动执行器？ | 否；首期仅解析、校验、下一步骤查询和提示。 | 否 | 已决定 |

### 用户确认的探索结论

2026-08-10，用户确认连续推进但不跳步的执行边界，并同意将其作为可复用的 `plan-governance` 行为约定；机器可读步骤模型继续采用独立可选计划，不改变旧计划兼容性。

### 独立设计复核结论

2026-08-10 的独立设计复核认为步骤模型方向可行，但“唯一下一步骤”不适合并行场景；同时需要明确旧计划“不适用”、步骤状态转换、共享写入约束和证据边界。上述问题已纳入本阶段未决设计项，不构成阶段 0 正式准入通过。
- 不在本计划处理当前工作集、阶段依赖、attestation 生命周期或 drift 覆盖的底层 schema 决策；这些由上游优化计划承载。

## 不变量

- 自主连续执行是可选执行模式；未声明该模式的计划维持现有工作流与检查兼容性。
- 每个可执行步骤必须有稳定 ID、明确前置条件、可验证完成条件和证据位置；步骤顺序只允许向前推进。
- `不适用` 不是跳步：只能走计划明示的分支，并记录触发条件、理由和替代证据。
- 阶段完成、阶段状态变更、当前阻塞项和最新有效证据仍由 `PLAN_MAP.md` 承载；步骤表不复制字段方案或阶段准入结论。
- 任何后续阶段都必须单独满足 Step 0、样本矩阵、验证方式、完成条件和独立准入复核。
- 若状态记录与实际变更/验证不一致，以可复现命令和独立复核为准，不能仅凭步骤表判定完成。

## 影响模块或文件

- `scripts/check_plan_governance.py`
- `scripts/init_plan_governance.py`
- `scripts/plan_governance_hook.py`
- `bin/plan-governance-cli.mjs`
- `resources/skill/SKILL.md`
- `resources/skill/assets/plan.template.md`
- `README.md`
- `plan-governance-design.md`
- `tests/test_check_plan_governance.py`
- `tests/npm_cli.test.mjs`
- `tests/test_plan_governance_hooks.py`
- `docs/PLAN_MAP.md`
- `docs/fixtures/autonomous-plan-execution-stage0-design-cases.md`
- `docs/fixtures/autonomous-plan-execution-stage1-validation-cases.md`
- `docs/fixtures/autonomous-plan-execution-stage2-next-cases.md`
- `docs/reviews/autonomous-plan-execution-stage2-independent-review-20260811.md`
- `docs/reviews/autonomous-plan-execution-stage2-completion-review-20260811.md`
- `docs/plans/autonomous-plan-execution.md`

## 公共契约变化

阶段 0 技术收敛稿是历史候选设计；阶段 2 已通过独立准入复核并冻结了当前 `next` 实施契约，以下历史内容仅用于说明演进来源：

| 能力 | 候选方案 | 兼容边界 |
|---|---|---|
| 启用方式 | 专项计划的可选执行模式字段；skill 短指令仅作为运行时授权 | 旧计划不增加必填项；短指令不能绕过计划内未启用的步骤模型 |
| 步骤模型 | `执行清单` 表：`步骤 ID / 前置步骤 / 动作 / 证据 / 完成条件 / 状态 / 分支记录` | 保留现有自然语言“实施步骤”；避免把计划级状态复制到每一行 |
| 读取入口 | 只读 `plan-governance-cli plan next <plan>`；或现有 `check` 的可选模式，输出当前可执行步骤集合 | 不执行命令、不写计划、不自动更改 Git 或外部系统；多个 ready steps 必须作为集合输出 |
| 检查强度 | 自主模式下缺少步骤字段、顺序、证据或分支记录先以 `WARNING` 提示；稳定后再讨论严格模式 | 默认检查和未启用计划保持原行为；业务验收不由机械检查替代 |

### 阶段 0 技术收敛稿（历史候选）

#### 可选执行模式和步骤表

专项计划只有显式声明 `execution_mode: autonomous-continuous` 时才启用步骤级解析；旧计划没有该字段时保持兼容，并由查询入口返回“不适用”。建议的最小步骤表为：

可选的 `execution_policy` 为 `serial` 或 `parallel`，缺省为 `serial` 以保持安全兼容；只有显式 `parallel` 时才允许返回多个 ready steps。`shared_write_risk` 只提示写入冲突，不自动把 `parallel` 改成 `serial`。

| 步骤 ID | 前置步骤 | 动作 | 证据 | 完成条件 | 状态 | 分支记录 |
|---|---|---|---|---|---|---|
| `S1` | `-` | `<动作>` | `<证据定位>` | `<可验证条件>` | `未开始` | `-` |

步骤 ID 在当前计划阶段内唯一；`前置步骤` 只能引用同一阶段中存在的 ID。现有自然语言“实施步骤”保留为面向人的说明，不重复成为第二套状态事实。

#### 状态和分支转换

最小状态为 `未开始`、`执行中`、`已完成`、`阻塞`、`不适用`。允许的基本转换为：

```text
未开始 -> 执行中 -> 已完成
执行中 -> 阻塞 -> 执行中
执行中 -> 不适用（仅当计划声明的分支条件满足）
```

`已完成` 和 `不适用` 必须有证据或替代证据；失败默认进入 `阻塞`，不得静默标记为完成。`不适用` 分支必须记录触发条件、理由和替代证据。步骤状态由实施者记录执行事实，不能替代阶段准入或独立验收。

结构错误在默认检查中输出 WARNING，在 `--strict-readiness` 或自主步骤严格检查中提升为 ERROR；出现结构错误时 `next` 不返回 ready steps。

#### 下一步骤集合和暂停输出

只读查询暂定为 `plan-governance-cli plan next <plan> [--json]`，输出以下逻辑状态之一：

| 状态 | 含义 |
|---|---|
| `ready` | 返回所有前置条件和阶段门满足的步骤集合 |
| `blocked` | 返回失败步骤、缺失证据或未解决前置条件 |
| `phase_gate` | 当前阶段步骤已收口，但下一阶段尚未独立准入 |
| `not_enabled` | 计划没有启用结构化自主模式 |
| `complete` | 当前计划声明的步骤和阶段完成条件均已收口，仍不自动接受独立验收 |

当多个步骤互不依赖且没有共享写入约束时，`ready_steps` 可以包含多个 ID；存在串行或 `shared_write_risk` 约束时，查询单独输出约束和建议写入顺序，不把共享风险伪装成前置步骤。查询不执行命令、不更新状态、不写文件。

#### 步骤证据边界

证据可以是命令输出、测试名称、提交、文档锚点或可定位运行记录。机械检查只校验字段存在、ID/前置关系、状态转换和证据定位的基本结构；它不替代命令执行、业务验收或独立复核。

## 阶段路线图

| 阶段 | 目标 | 进入条件 | 验证方向 | 状态 |
|---|---|---|---|---|
| 阶段 0 | 冻结可选步骤模型、状态语义、失败分支和兼容策略 | 上游计划的相关契约已足以复用；Step 0 样本齐备 | 顺序、分支、证据、阶段门、ready steps 集合和旧计划兼容的设计复核 | 已完成 |
| 阶段 1 | 增加自主模式的步骤解析与只读校验 | 阶段 0 独立准入通过 | 正反 fixture、warning 语义、默认检查兼容和严格检查边界 | 已完成 |
| 阶段 2 | 提供下一步骤只读查询与 hook 提示 | 阶段 1 完成；阶段 2 输出契约已冻结并通过实施后独立验收 | `next` 输出、暂停条件、无写入保证和安装包回归 | 已完成 |
| 阶段 3 | 同步模板、skill、说明文档并以真实样本做独立验收 | 阶段 2 完成；自愿试点计划已独立准入 | 端到端回放、反向引用、独立验收和回滚演练 | 设计中 |

## 阶段 0 设计记录

### 范围

当前为阶段 0，只做设计和准入准备：

1. 将“自主但不跳步”拆成可验证的步骤顺序、证据、分支和暂停条件，不把它误解为自动代码执行。
2. 比较 Markdown 表、独立 JSON/YAML manifest 与仅依赖自然语言清单三种表达，优先选择零迁移或最小迁移方案。
3. 定义步骤状态与计划/阶段状态的边界，避免步骤表成为第二个计划地图。
4. 设计只读下一步骤查询、hook 提示和严格检查的渐进启用方式。
5. 为阶段 1—3 建立固定 fixture、失败判定、迁移/回滚边界和独立准入条件；不修改生产 CLI、模板或检查器。

### 阶段 0 历史准入摘要

| 字段 | 内容 |
|---|---|
| 准入状态 | 设计中 |
| Step 0 | [阶段 0 Step 0 证据](#阶段-0-step-0-证据) |
| 样本矩阵 | [阶段 0 样本矩阵](#阶段-0-样本矩阵) |
| 验证方式 | [验证方式](#验证方式) |
| 失败/回滚边界 | [风险和回滚](#风险和回滚) |
| 当前阻塞项 | 阶段 0 修订设计已通过独立复核；阶段 1 尚未完成自身 Step 0、样本矩阵、验证方式、完成条件和独立准入 |
| 最新独立准入复核 | [2026-08-10 独立复核：通过（阶段 1 仍需自身准入）](../reviews/plan-governance-stage0-independent-review-20260810.md) |

### 实施步骤

1. 固定当前 skill 行为、计划模板和检查器能力的基线。
2. 用样本矩阵比较三种步骤表达，选择单一事实源和最小兼容方案。
3. 冻结步骤状态、证据和失败/不适用分支语义，以及与 `PLAN_MAP.md` 的同步边界。
4. 定义只读查询与检查器的错误/WARNING 语义，确认不产生写入或自动批准。
5. 补齐阶段 1—3 的 fixture、验证命令、完成条件和回滚方式。
6. 由未参与设计的复核者独立核对契约、样本和安全边界；通过后进入阶段 1 的独立 Step 0 准备，不得直接将阶段 1 标记为 `待实施`。

### 阶段证据

- `docs/fixtures/autonomous-plan-execution-stage0-design-cases.md`
- `docs/reviews/plan-governance-stage0-independent-review-20260810.md`

### 阶段 0 Step 0 证据

基线类型为“现有 skill/检查器能力快照 + 最小步骤计划样本”。

- 当前 skill 已将“按计划自主推进至完成”“推进到完成计划”和“不跳步”解释为连续、逐项执行；它同时要求阶段 N+1 自己完成准入，并在异常时暂停汇报。
- `resources/skill/assets/plan.template.md` 只有自然语言实施步骤，未定义稳定步骤 ID、步骤状态、前置步骤或步骤证据字段。
- `scripts/check_plan_governance.py` 已能检查计划状态、阶段准入、计划级依赖、影响范围、停滞和 attestation，但不解析实施步骤，也不检查步骤顺序或步骤级证据。
- 2026-08-10 本仓库 `npm test` 通过 37/37 项，`plan-governance-cli check . --strict-readiness` 通过；这是新增能力的兼容基线。
- 本条是阶段 0 记录当时的状态快照；当前 `plan-governance-operability-optimization` 已完成阶段 0 独立复核并进入阶段 1。本计划仍不能把上游阶段 1 的设计稿当作已实施能力。

### 阶段 0 样本矩阵

| 样本 | 输入或基线 | 可执行命令 | 预期结果 | 失败判定 | 输出位置 |
|---|---|---|---|---|---|
| 顺序执行 | 含 S1→S2→S3 的自主模式最小计划 | `test -f docs/fixtures/autonomous-plan-execution-stage0-design-cases.md && rg -n '案例 E1|execution_policy: parallel|S4' docs/fixtures/autonomous-plan-execution-stage0-design-cases.md` | 仅无前置且条件满足的步骤可执行；完成并留证后才允许后置步骤 | 后置步骤在前置步骤缺证时被标记完成 | 设计案例；后续 `tests/` fixture |
| 不适用分支 | S2 明确有“不适用”条件和替代证据 | `rg -n '案例 E2|不适用|替代证据|阻塞' docs/fixtures/autonomous-plan-execution-stage0-design-cases.md` | 记录触发条件、理由和替代证据后按分支进入下一步 | 使用“不适用”跳过 S2 或没有证据仍前进 | 设计案例；后续 `tests/` fixture |
| 验证失败 | S2 的验证命令失败，且计划规定修复/暂停分支 | `rg -n '案例 E2|验证命令失败|修复分支|后置步骤' docs/fixtures/autonomous-plan-execution-stage0-design-cases.md` | 后续步骤保持不可执行，输出阻塞原因和修复分支 | 将失败步骤视作已完成或继续后置步骤 | 设计案例；后续 `tests/` fixture |
| 结构错误 | 重复 ID、环依赖、缺失证据和非法状态转换 | `rg -n '案例 E3|重复 ID|环依赖|非法状态|WARNING|ERROR' docs/fixtures/autonomous-plan-execution-stage0-design-cases.md` | 返回明确 WARNING/ERROR，且不产生 ready steps | 接受结构错误并继续执行 | 设计案例；后续 `tests/` fixture |
| 阶段门 | 阶段 1 完成、阶段 2 仍为设计中的多阶段计划 | `rg -n '案例 E4|phase_gate|not_enabled|未准入' docs/fixtures/autonomous-plan-execution-stage0-design-cases.md` | 阶段 1 收口后返回 `phase_gate` 并停止 | 自动进入阶段 2 或把测试通过当作阶段 2 准入 | 设计案例；后续 `tests/` fixture |
| 旧计划兼容 | 没有执行模式或步骤清单的现有六列地图计划 | `rg -n '案例 E4|旧计划|not_enabled|不要求历史计划' docs/fixtures/autonomous-plan-execution-stage0-design-cases.md` | 既有检查结果不变，查询返回 `not_enabled` | 要求历史计划补填步骤或误判已完成 | 设计案例；后续 `tests/` fixture |
| 无写入 | 合法自主模式计划和 `next` 查询 | `test -f docs/fixtures/autonomous-plan-execution-stage0-design-cases.md && rg -n '案例 E5|hash 一致|不修改计划' docs/fixtures/autonomous-plan-execution-stage0-design-cases.md` | 只输出 ready steps/暂停原因，不修改计划、地图、Git 或外部系统 | 查询导致文件、状态或 Git 索引改变 | 设计案例；后续临时目录 hash |

### 阶段 0 完成条件

- 已选择步骤模型和唯一事实源，并明确其与现有“实施步骤”、`PLAN_MAP.md` 和独立复核记录的边界。
- 每种步骤状态、前置条件、完成证据、失败与不适用分支都有正常和失败样本。
- 已定义“下一步骤”“暂停”“阶段完成”与“计划完成”的可观察输出，且没有任何输出被解释为自动验收或自动授权。
- 旧计划、未启用自主模式的计划和现有默认/严格检查的兼容策略已通过 fixture 证明。
- 阶段 1—3 的实现范围、验证命令、回滚边界和独立准入条件已经固定。
- 当前阶段的阶段 0 设计无未解决阻塞项；独立准入复核明确阶段 0 修订设计通过，但阶段 1 仍须自身 Step 0 和独立准入。

### 阶段 0 历史验证方式

阶段 0 完成前至少执行：

```bash
npm test
plan-governance-cli check .
plan-governance-cli check . --strict-readiness
rg -n '自主连续执行|自主推进至完成|不跳步|实施步骤|执行清单|步骤 ID|下一步骤' resources docs README.md scripts tests
rg -n 'autonomous-plan-execution|自主连续执行|步骤状态|不适用|下一步骤' docs README.md resources scripts tests
rg -n '草案为准|以草案为事实源|详见草案|draft is source|source of truth.*draft|以.*draft.*为准' docs README.md resources
```

阶段 1—3 必须额外运行新旧 fixture 回归、候选 CLI 的无写入 hash 检查、安装包 smoke test、反向引用检查和独立验收。若上游计划尚未冻结所需契约，只能完成不依赖其字段的样本设计，不得以推测代替输入。

### 阶段 0 历史测试覆盖率

阶段 0 基线为 2026-08-10 的 `npm test`：37/37 项通过。后续以覆盖顺序、分支、失败、阶段门、旧计划兼容和无写入六类 fixture 作为新增行为的最低覆盖证据；当前项目不输出 Node 百分比覆盖率，不得伪造百分比。

### 阶段 0 历史独立准入复核

| 字段 | 内容 |
|---|---|
| 日期 | 2026-08-10 |
| 阶段 | 阶段 0 |
| 结论 | 通过：修订后的阶段 0 设计达到阶段 1 `待实施` 准入要求；阶段 1 仍须自身 Step 0 和独立准入 |
| 证据 | [独立复核报告](../reviews/plan-governance-stage0-independent-review-20260810.md)；`plan-governance-cli check . --strict-readiness`；`npm test` 37/37 |
| 复核者 | Dalton（独立只读复核 subagent） |

### 阶段 0 历史独立复核记录

| 日期 | 类型 | 阶段 | 结论 | 证据 | 复核者 |
|---|---|---|---|---|---|
| 2026-08-10 | 阶段 0 准入复核 | 阶段 0 | 未通过：方向通过但尚未达到阶段 1 `待实施` 标准 | [独立复核报告](../reviews/plan-governance-stage0-independent-review-20260810.md) | Dalton（独立只读复核 subagent） |
| 2026-08-10 | 阶段 0 修订后准入复核 | 阶段 0 | 通过：修订后的阶段 0 设计达到阶段 1 `待实施` 准入要求；阶段 1 仍须自身 Step 0 和独立准入 | [独立复核报告](../reviews/plan-governance-stage0-independent-review-20260810.md) | Dalton（独立只读复核 subagent） |

### 阶段 0 历史未决问题

本阶段的详细未决项以[需求探索—未决问题](#需求探索)为事实源。这里仅保留阶段准入状态，避免与需求探索重复定义步骤契约。

| 问题 | 推荐方案 | 是否阻塞当前阶段 | 状态 |
|---|---|---|---|
| 步骤模型、状态转换、ready steps 输出和上游兼容契约是否已冻结？ | 技术收敛稿、E1—E5 设计案例和修订后的独立复核已完成；进入阶段 1 前仍须建立其自身准入材料。 | 否 | 已收敛，待阶段 1 实施 |
| 当前阶段是否达到阶段 1 `待实施` 标准？ | 阶段 0 修订设计已通过；阶段 1 仍需自己的 Step 0、样本矩阵、验证命令、完成条件和独立准入，因此当前不标记为 `待实施`。 | 是 | 待阶段 1 Step 0 |

### 阶段 0 历史风险和回滚

风险：把每一个细小动作都固化为步骤，导致简单计划的维护成本高于收益。

控制：步骤模型只对显式启用自主连续执行的计划生效；普通小任务继续使用现有计划或非治理流程。

风险：步骤状态与 `PLAN_MAP.md`、独立复核或实际代码状态相互矛盾。

控制：步骤只记录当前阶段执行事实；阶段与计划生命周期仍以地图为准；独立验收只由复核证据决定。

风险：下一步骤查询被误解为允许自动执行风险操作。

控制：命令只读；具体工具调用仍遵守项目权限、外部授权和已有 approval 机制；输出明确不代表批准。

风险：上游优化计划的契约未定导致重复定义。

控制：阶段 1 前必须独立复核上游关系；若其方案改变，先更新本计划的依赖、字段和样本，再继续。

回滚：若步骤模型造成兼容性问题或不足以可靠发现跳步，移除自主模式解析、候选 CLI 和模板段落；保留当前 skill 的策略层约定、现有计划文档、计划地图和严格准入规则，不迁移或破坏旧计划。

## 关联 ADR、迁移、spec 或 issue

- 上游计划：[plan-governance-operability-optimization](plan-governance-operability-optimization.md)
- 相关已完成计划：[phase-entry-gate-hardening](phase-entry-gate-hardening.md)、[agent-runtime-integration](agent-runtime-integration.md)、[plan-governance-npm-cli](plan-governance-npm-cli.md)
- 当前不创建 ADR 或 migration。阶段 0 若确定步骤模型需要不可兼容的外部 manifest 或状态迁移，再单独创建相应文档。

## 当前阶段

### 范围

当前为阶段 2；阶段 2 已完成实施和独立验收，阶段 3 仍保持设计中：

1. 提供只读 `plan-governance-cli plan next <plan> [--json]`，返回当前可推进步骤集合或明确暂停原因。
2. 复用阶段 1 的步骤解析和校验结果，不重新定义步骤字段、状态和证据边界。
3. 支持串行/显式并行 ready 集合、专项计划 `执行约束` 表中的 `shared_write_risk` 提示、阶段门和完成边界。
4. 接入只读 hook 提示；不执行动作、不更新状态、不写计划/地图/Git/外部系统，不替代独立验收。

### 阶段准入摘要

| 字段 | 内容 |
|---|---|
| 准入状态 | 实施中 |
| 阶段状态 | 已完成 |
| Step 0 | [阶段 2 Step 0 证据](#阶段2-step-0-证据) |
| 样本矩阵 | [阶段 2 next 样本](../fixtures/autonomous-plan-execution-stage2-next-cases.md)；[阶段 2 样本矩阵](#阶段2样本矩阵) |
| 验证方式 | [阶段2验证方式、完成条件和失败边界](#阶段2验证方式完成条件和失败边界) |
| 失败/回滚边界 | [阶段2验证方式、完成条件和失败边界](#阶段2验证方式完成条件和失败边界) |
| 当前阻塞项 | 无；阶段 2 已完成，阶段 3 仍需自身 Step 0、验证方式、完成条件和独立准入复核 |
| 最新独立准入复核 | [2026-08-11 阶段 2 完成验收：通过](../reviews/autonomous-plan-execution-stage2-completion-review-20260811.md) |

### 实施步骤

1. 冻结已通过复核的 `next` 输入/输出、状态优先级、退出码、执行约束和 hook 只读边界。
2. 实现 `plan next` 的只读解析与查询；结构错误、缺证据和未满足前置条件不得返回 ready steps。
3. 为 N1—N8 增加真实正反行为测试、无写入 hash 测试、hook 提示测试和安装包入口回归。
4. 运行阶段 1 `plan steps validate` 兼容回归、npm/Python 全量测试、严格治理、停滞、drift、pre-commit、反向引用和事实源扫描。
5. 由未参与阶段 2 实施的复核者独立验收；阶段 2 已关闭，阶段 3 不自动放行。

### 阶段 2 实施授权记录

2026-08-11，阶段 2 Step 0 独立复核明确达到 `待实施` 标准，本记录授权开始阶段 2 的 `plan next`、hook 提示、对应测试和安装包回归实现。授权范围不包括自动执行器、状态写回、阶段 3 模板/skill 同步、全局 CLI/skill 同步或其他项目改动。

### 阶段证据

- `docs/fixtures/autonomous-plan-execution-stage2-next-cases.md`
- `docs/reviews/autonomous-plan-execution-stage2-independent-review-20260811.md`
- `docs/reviews/autonomous-plan-execution-stage2-completion-review-20260811.md`

### 阶段1历史实施记录

#### 阶段1历史范围

历史快照对应阶段 1；阶段 1 已完成自主模式步骤表解析与只读校验的实现、验证和独立复核。当前阶段指针以文档前面的“当前阶段”和 `PLAN_MAP.md` 为准，阶段 2 已完成，阶段 3 仍保持设计中：

1. 解析显式声明 `execution_mode: autonomous-continuous` 的专项计划步骤表，校验字段、ID、前置关系、状态、证据和分支记录。
2. 提供只读校验入口 `plan-governance-cli plan steps validate <plan> [--json]`；本阶段不提供 `next`，下一步骤集合由阶段 2 承载。
3. 默认模式输出 WARNING，严格模式输出 ERROR；结构错误时不得给出可供后续执行的 ready steps 依据。
4. 旧计划和未启用自主模式的计划返回 `not_enabled`，不要求迁移，不执行动作，不写回状态、计划、地图、Git 或外部系统。

#### 阶段1历史准入摘要

| 字段 | 内容 |
|---|---|
| 准入状态 | 实施中 |
| 阶段状态 | 已完成 |
| Step 0 | [阶段 1 Step 0 证据](#阶段-1-step-0-证据) |
| 样本矩阵 | [阶段 1 样本矩阵](#阶段-1-样本矩阵) |
| 验证方式 | [验证方式](#验证方式) |
| 失败/回滚边界 | [风险和回滚](#风险和回滚) |
| 当前阻塞项 | 无；阶段 1 已完成，阶段 2 仍需自身 Step 0、验证方式、完成条件和独立准入复核 |
| 最新独立准入复核 | [2026-08-10 独立复核：通过，达到阶段 1 `待实施` 标准](../reviews/plan-governance-stage1-independent-review-20260810.md) |

#### 阶段1历史实施步骤

1. 固定现有模板和检查器没有步骤表解析能力的基线，确认阶段 0 设计契约可直接复用。
2. 用 V1—V5 fixture 固定合法串行/并行声明、旧计划、不适用分支、结构错误、严格模式和无写入边界。
3. 冻结 `plan steps validate` 的文本/JSON 输出、状态码、错误定位和兼容语义；不把 `next` 提前纳入本阶段。
4. 实现后运行步骤校验 fixture、默认/严格治理、npm 回归、打包安装和无写入 hash 检查。
5. 由未参与阶段 1 设计的复核者独立复核；通过后关闭阶段 1，计划级状态仍保持 `实施中`，不自动进入阶段 2。

#### 阶段 1 实施授权记录

2026-08-10，用户在阶段 1 独立复核未通过后明确要求“继续”，本记录将其解释为允许开始阶段 1 的步骤表解析、只读校验和测试实现，用于补齐复核指出的真实行为证据。授权范围仅包括 `plan steps validate` 入口及其校验测试；不包括阶段 2 的 `next`、自动执行器、状态写回或外部系统改动。阶段 1 完成后仍须重新独立准入复核，不能用本授权替代准入结论。

#### 阶段1历史阶段证据

- `docs/fixtures/autonomous-plan-execution-stage1-validation-cases.md`
- `docs/reviews/plan-governance-stage1-independent-review-20260810.md`

#### 阶段 1 Step 0 证据

本节保留实现前基线，类型为“现有模板/检查器只读回放 + 阶段 0 设计样本 + 既有测试回归”。实现前已确认：

- `resources/skill/assets/plan.template.md` 当前只有自然语言实施步骤，不包含稳定步骤 ID、前置步骤、证据、状态或分支字段。
- `scripts/check_plan_governance.py` 当前不解析自主执行步骤表，也不提供步骤校验结果。
- 当前 CLI 没有 `plan steps validate` 路由；现有 `plan` 路由属于图谱命令，阶段 1 需要新增明确子命令并保持图谱入口兼容。
- 2026-08-10 的 `npm test` 为 37/37，严格治理检查通过；这是步骤校验实现前基线。
- 阶段 0 已冻结 `execution_mode`、`execution_policy`、七列表、状态转换、分支记录和 WARNING/ERROR 边界；阶段 1 只实现解析/校验，不重新定义业务验收或独立复核。

#### 阶段1最近实施/验证记录

| 日期 | 类型 | 动作/结果 | 证据 | 状态 | 记录者 |
|---|---|---|---|---|---|
| 2026-08-10 | 实施 | 增加 `plan steps validate` 路由、execution mode/policy、七列表、ID/前置关系、状态/分支/证据校验和 JSON 输出 | `bin/plan-governance-cli.mjs`、`scripts/check_plan_governance.py`、npm CLI 行为测试 | 通过 | Codex |
| 2026-08-10 | 验证 | npm 39/39、Python 97 passed、覆盖率 91.39%、严格治理和 diff 检查通过；打包安装后的 `workset` 与 `plan steps validate` 冒烟通过 | `npm test`；`python3 -m pytest -q`；`node bin/plan-governance-cli.mjs check . --strict-readiness`；`git diff --check`；临时打包安装 smoke test | 通过 | Codex |
| 2026-08-11 | 同步 | 当前仓库 `plan-governance-cli@0.3.0` 已安装到本机全局 CLI；`plan steps validate` 全局入口回归返回预期 `not_enabled`，Codex/Claude skill 清单资源已同步 | `npm pack`；`npm install -g plan-governance-cli-0.3.0.tgz`；`plan-governance-cli plan steps validate autonomous-plan-execution --json --root /Users/jafish/Documents/work/plan-governance`；`plan-governance-cli setup --target all --force`；清单资源 hash 对比 | 通过 | Codex |
| 2026-08-11 | 回滚 | 按用户要求将全局 CLI、Codex skill 和 Claude skill 恢复到同步前状态；当前仓库计划和代码未回退 | `/tmp/plan-governance-sync.aow9Lt` 中的同步前备份；恢复后旧全局检查器与备份 hash 一致；旧入口拒绝 `plan steps validate` 新路由参数 | 通过 | Codex |
| 2026-08-11 | 治理同步 | 按新计划规范补齐阶段 1 完成证据入口，区分阶段准入状态与计划级实施中状态；阶段 2/3 保持设计中 | [阶段 1 完成证据](#完成证据)；`docs/PLAN_MAP.md` 计划索引 | 通过 | Codex |

#### 阶段 1 样本矩阵

| 样本 | 输入或基线 | 可执行命令 | 预期结果 | 失败判定 | 输出位置 |
|---|---|---|---|---|---|
| 合法串行 | V1：`execution_policy: serial`，S1→S2→S3 | `test -f docs/fixtures/autonomous-plan-execution-stage1-validation-cases.md && rg -n '案例 V1|execution_policy: serial|valid' docs/fixtures/autonomous-plan-execution-stage1-validation-cases.md` | 校验 valid；不执行动作、不计算 ready steps | 把自然语言当步骤事实或写回计划 | fixture；后续 `tests/` 输出 |
| 合法并行 | V2：并行策略和独立 shared write 提示 | `rg -n '案例 V2|execution_policy: parallel|shared_write_risk|阶段 2' docs/fixtures/autonomous-plan-execution-stage1-validation-cases.md` | 校验表达合法；不提前输出 next 集合 | 将共享风险改成前置步骤或提前执行 | fixture；后续 `tests/` 输出 |
| 旧计划兼容 | V3：无 execution mode/步骤表的旧计划 | `rg -n '案例 V3|not_enabled|旧计划' docs/fixtures/autonomous-plan-execution-stage1-validation-cases.md` | 返回 not_enabled，既有治理结果不变 | 把未启用计划标为 invalid 或强制迁移 | fixture；后续兼容测试 |
| 结构错误 | V4：重复 ID、环依赖、缺证据、非法状态值/分支记录 | `rg -n '案例 V4|重复 ID|未知前置|环|WARNING|ERROR' docs/fixtures/autonomous-plan-execution-stage1-validation-cases.md` | 默认 WARNING、严格 ERROR；不得作为 next 输入 | 接受错误结构或继续给出执行依据 | fixture；后续 `tests/` 输出 |
| 分支和无写入 | V5：不适用分支证据与合法/非法 hash 对比 | `rg -n '案例 V5|不适用|替代证据|hash|只读' docs/fixtures/autonomous-plan-execution-stage1-validation-cases.md` | 分支证据完整才通过；查询前后无写入 | 自动补证据、推进状态或改变文件 | fixture；后续临时目录 hash |

#### 阶段 1 技术收敛稿

阶段 1 的校验结果固定为：

```json
{
  "schema_version": 1,
  "plan": "<plan-id>",
  "phase": "阶段 1",
  "enabled": true,
  "status": "valid|invalid|not_enabled",
  "steps": [],
  "errors": [],
  "warnings": []
}
```

`steps` 只返回经过解析的结构化步骤，不返回 ready steps；`errors` 和 `warnings` 必须包含可定位的步骤 ID/字段信息。`not_enabled` 不视为错误，结构错误才进入 `invalid`。校验命令只读，不能自动更新步骤状态。

#### 阶段 1 完成条件

- `plan steps validate <plan>` 支持文本和稳定 JSON 输出，合法结构、未启用计划和结构错误三类结果可区分。
- 七列表、execution mode/policy、ID/前置关系、允许状态值、证据和不适用分支均有正反 fixture；历史状态转换不在阶段 1 的单快照输入范围内。
- 默认 WARNING、严格 ERROR、错误定位和退出码有可复现测试；结构错误不会产生 ready steps 依据。
- 旧计划和未启用自主模式的计划保持既有基础/严格治理结果，不要求历史迁移。
- 校验过程不修改计划、地图、步骤状态、Git 索引或外部系统；npm、打包安装和反向引用检查通过。
- 步骤校验的合法/未启用/结构错误、默认/严格 WARNING/ERROR、退出码、旧计划兼容、阶段状态与计划状态分离和无写入行为已有测试；Python 覆盖率达到 91.39%。
- npm 39/39、Python 97 passed、CLI 打包清单、反向引用检查和无写入 hash 已通过；最新独立复核已通过，阶段 2 仍须自身准入，不自动放行。

## 验证方式

阶段 1 实施和独立复核前至少执行：

```bash
node bin/plan-governance-cli.mjs plan steps validate autonomous-plan-execution --json
node bin/plan-governance-cli.mjs check .
node bin/plan-governance-cli.mjs check . --strict-readiness
npm test
python3 -m pytest -q
test -f docs/fixtures/autonomous-plan-execution-stage1-validation-cases.md
rg -n 'plan steps validate|not_enabled|shared_write_risk|invalid|WARNING|ERROR' docs/fixtures/autonomous-plan-execution-stage1-validation-cases.md docs/plans/autonomous-plan-execution.md
git diff --check
```

实现后追加：正反 fixture 回归、CLI 打包安装 smoke test、校验前后 hash 对比和重新独立准入复核。当前仓库用 `node bin/plan-governance-cli.mjs plan steps validate ...` 验证本地实现，安装包再用 `plan-governance-cli plan steps validate ...` 回归。

## 测试覆盖率

阶段 1 的可复现基线仍为 `npm test` 37/37；当前 Node 测试不输出百分比覆盖率。实现后以 V1—V5 的正反 fixture、文本/JSON 输出和默认/严格模式作为最低覆盖证据，不伪造覆盖率百分比。

## 完成证据

阶段 1 已完成：`plan steps validate` 的合法、未启用和结构错误结果，默认 WARNING/严格 ERROR、退出码、旧计划兼容、阶段状态与计划状态分离和无写入边界均有 V1—V5 测试证据；npm 39/39、Python 97 passed、覆盖率 91.39%、打包安装 smoke test、严格治理、反向引用和独立复核均通过。阶段 2/3 未因阶段 1 完成自动放行，仍需各自 Step 0、验证方式、完成条件和独立准入复核。

## 阶段2设计与实施契约

本节保留阶段 2 的 Step 0、冻结契约、样本、实施结果和边界。阶段 2 已于 2026-08-11 通过未参与实施的独立完成验收并关闭；阶段 3 仍为设计中，不因阶段 2 完成自动放行。

### 目标、范围和非目标

阶段 2 的目标是提供一个只读的“下一步骤集合”查询和 hook 提示，让执行者能在不跳步的前提下识别当前可以推进的步骤、阻塞原因和阶段门状态。

范围：

1. 实现候选入口 `plan-governance-cli plan next <plan> [--json]`。
2. 基于阶段 1 已验证的步骤表解析结果，计算前置步骤、步骤状态、证据、分支和当前阶段准入条件。
3. 输出 `ready`、`blocked`、`phase_gate`、`not_enabled`、`complete` 五类逻辑状态，以及可定位的约束和建议顺序。
4. 为 hook 提供只读提示所需的稳定结果；hook 不负责执行步骤或替换独立验收。

非目标：

- 不执行步骤动作、命令、Git 操作或外部系统操作。
- 不更新步骤状态、计划文档、`PLAN_MAP.md`、证据或完成声明。
- 不自动批准阶段、不替代独立准入复核、不把“完成”解释成独立验收通过。
- 不在本阶段引入自动执行器、并行调度器、外部 manifest 或状态迁移。

### 阶段2 Step 0 证据

基线类型为“阶段 0 技术收敛稿中的候选 `next` 契约 + 阶段 1 已实现的真实 `plan steps validate` 兼容基线 + 只读边界回放”。已确认：

- 阶段 1 已能稳定识别启用/未启用计划、步骤 ID、前置关系、状态、证据和不适用分支；阶段 2 不重新定义这些字段。
- 阶段 0 提出的 `ready`、`blocked`、`phase_gate`、`not_enabled`、`complete` 五类逻辑状态已在阶段 2 独立准入复核后冻结；本节以下结构是当前实施事实源。
- N6 的临时计划样本仍需证明查询不会把前一阶段收口或阶段状态变化误判为下一阶段已准入；这与当前 `PLAN_MAP.md` 的阶段 2 指针无关。
- 当前仓库已实现只读 `plan next` 和 hook 提示；阶段 2 的真实行为测试仍以临时启用计划验证，当前专项计划本身没有启用自主步骤模式，因此入口返回 `not_enabled`。

阶段 2 冻结输出契约如下：

```json
{
  "schema_version": 1,
  "plan": "<plan-id>",
  "phase": "<current-phase>",
  "execution_mode": "autonomous-continuous",
  "execution_policy": "serial|parallel",
  "status": "ready|blocked|phase_gate|not_enabled|complete",
  "ready_steps": [],
  "blocked_steps": [],
  "constraints": [],
  "next_action": {"kind": "run_ready_steps|resolve_blocked|review_shared_write_order|await_phase_gate|await_independent_acceptance|none", "reason": "<稳定原因码>"}
}
```

`ready_steps` 必须是当前所有满足前置关系和阶段门的步骤集合；当 `execution_policy` 为 `serial` 时最多返回当前序列中的下一项，显式 `parallel` 时返回所有互不依赖的候选步骤。存在共享写入约束时仍可返回独立候选，但必须同时输出约束和建议顺序，不能把 `shared_write_risk` 隐式改写为前置步骤。`not_enabled` 必须保持旧计划兼容；`complete` 只表示声明的步骤和阶段完成条件已收口，不代表独立验收通过。

阶段 2 不扩展阶段 1 的七列表步骤表。步骤级共享写入约束的唯一候选来源是专项计划中可选的 `## 执行约束` 表，表头固定为：

| 约束 ID | 类型 | 步骤 | 共享目标 | 建议顺序 | 说明 |
|---|---|---|---|---|---|
| `C1` | `shared_write_risk` | `S2,S3` | `docs/PLAN_MAP.md` | `S2 -> S3` | 两个步骤都可能写入同一目标 |

`类型` 当前只允许 `shared_write_risk`；`步骤` 必须引用当前阶段已声明的步骤 ID；`共享目标` 必须是可定位的相对路径或明确外部目标；`建议顺序` 只提供执行提示，不创建步骤前置关系。没有 `执行约束` 表时，约束集合为空。`PLAN_MAP.md` 中已有的计划级关系仍由地图事实源承载，不能被 `plan next` 静默推断为步骤级前置关系；如需让某个步骤消费该约束，必须在专项计划的 `执行约束` 表中显式声明。

阶段 2 冻结字段结构和状态优先级如下：

```json
{
  "ready_steps": [
    {"id": "S2", "reason": {"kind": "dependencies_satisfied"}}
  ],
  "blocked_steps": [
    {"id": "S3", "reasons": [{"kind": "missing_evidence", "step_id": "S2"}]}
  ],
  "constraints": [
    {
      "id": "C1",
      "kind": "shared_write_risk",
      "step_ids": ["S2", "S3"],
      "targets": ["docs/PLAN_MAP.md"],
      "recommended_order": ["S2", "S3"],
      "description": "两个步骤都可能写入同一目标"
    }
  ],
  "next_action": {"kind": "run_ready_steps|resolve_blocked|review_shared_write_order|await_phase_gate|await_independent_acceptance|none", "reason": "<稳定原因码>"}
}
```

`phase` 表示 `PLAN_MAP.md` 当前阶段指针，不表示查询目标阶段；`blocked` 包含结构无效、缺失前置、缺证据和步骤失败等安全停止原因，具体原因必须在 `blocked_steps[].reasons[].kind` 中区分，原因枚举至少包括 `invalid_structure`、`missing_predecessor`、`missing_evidence` 和 `failed_step`。状态优先级为 `not_enabled`（未启用）→ `blocked`（无法安全计算）→ `phase_gate`（当前阶段收口但后继阶段未准入）→ `complete`（计划终态且无需后继阶段门）→ `ready`。所有逻辑状态的查询成功退出码为 `0`；参数/计划不存在为 `2`；计划结构无法安全解析为 `1`，且不得返回 ready steps。`not_enabled` 不视为错误。

hook 只消费上述稳定结果并输出 `next_action.kind`、原因和 ready/blocked 步骤 ID；多计划按 `PLAN_MAP.md` 顺序逐个提示，不执行任何步骤、不改状态、不写文件。hook 的逻辑状态不改变查询退出码；解析失败仍返回对应错误码。

### 阶段2样本矩阵

完整输入片段、预期 JSON 字段和失败判定记录在 [阶段 2 next 样本](../fixtures/autonomous-plan-execution-stage2-next-cases.md)。N1—N8 已有真实 Python/Node 行为测试；以下命令保留为 fixture 覆盖检查和实施回归入口：

| 样本 | 输入或基线 | 可执行命令 | 预期结果 | 失败判定 | 输出位置 |
|---|---|---|---|---|---|
| N1 未启用 | V1：旧计划无 `execution_mode` 和结构化步骤表 | `rg -n '案例 N1|not_enabled|无 execution_mode' docs/fixtures/autonomous-plan-execution-stage2-next-cases.md` | 设计为 `not_enabled`；不要求迁移 | 旧计划被标为 invalid、被强制迁移或产生 ready steps | fixture；阶段 2 CLI 测试输出 |
| N2 串行前置 | V2：S1 未完成，S2 前置为 S1 | `rg -n '案例 N2|serial|S1|S2|blocked' docs/fixtures/autonomous-plan-execution-stage2-next-cases.md` | 只允许返回满足前置条件的步骤；S2 必须阻塞 | 跳过 S1 返回 S2，或把失败静默当完成 | fixture；`--json` 输出 |
| N3 并行集合 | V3：显式 `parallel`，S2/S3 无互相前置 | `rg -n '案例 N3|parallel|ready_steps|S2.*S3' docs/fixtures/autonomous-plan-execution-stage2-next-cases.md` | 返回多个独立 ready steps | 隐藏串行化、漏报 ready step 或重复返回 | fixture；`--json` 输出 |
| N4 共享写入风险 | V4：`执行约束` 表显式声明 `shared_write_risk` | `rg -n '案例 N4|执行约束|shared_write_risk|constraints|顺序' docs/fixtures/autonomous-plan-execution-stage2-next-cases.md` | 保留多个候选并输出约束/建议顺序，不伪造前置步骤 | 共享风险被静默忽略或变成未声明的前置步骤 | fixture；约束输出 |
| N5 缺证据/失败 | V5：步骤缺少证据或处于 `阻塞` | `rg -n '案例 N5|缺证据|阻塞|blocked_steps' docs/fixtures/autonomous-plan-execution-stage2-next-cases.md` | 输出 `blocked` 及可定位原因 | 返回 ready、自动补证据或推进状态 | fixture；错误/阻塞输出 |
| N6 阶段门 | V6：当前阶段步骤收口，但下一阶段没有独立准入 | `rg -n '案例 N6|phase_gate|独立准入|下一阶段' docs/fixtures/autonomous-plan-execution-stage2-next-cases.md` | 输出 `phase_gate`，不自动进入下一阶段 | 将阶段收口当成下一阶段准入或自动改地图 | fixture；阶段门输出 |
| N7 完成边界 | V7：声明步骤和阶段完成条件均收口 | `rg -n '案例 N7|complete|独立验收|不自动' docs/fixtures/autonomous-plan-execution-stage2-next-cases.md` | 输出 `complete`，明确仍需独立验收 | 以查询结果替代验收或继续生成无依据步骤 | fixture；完成输出 |
| N8 无写入 | V8：查询前后仓库和计划文件 hash 一致 | `rg -n '案例 N8|hash|只读|不修改' docs/fixtures/autonomous-plan-execution-stage2-next-cases.md` | 查询前后 hash 一致，退出码和输出可复现 | 修改计划、地图、步骤状态、Git 或外部系统 | fixture；阶段 2 临时目录 hash 输出 |

### 阶段2验证方式、完成条件和失败边界

Step 0 阶段先执行：

```bash
test -f docs/fixtures/autonomous-plan-execution-stage2-next-cases.md
rg -n '案例 N[1-8]|not_enabled|ready_steps|blocked|phase_gate|complete|shared_write_risk|hash' docs/fixtures/autonomous-plan-execution-stage2-next-cases.md
node bin/plan-governance-cli.mjs check . --strict-readiness
node bin/plan-governance-cli.mjs check . --drift
git diff --check
```

阶段 2 实施后追加真实行为验证：

```bash
node bin/plan-governance-cli.mjs plan next autonomous-plan-execution --json
node bin/plan-governance-cli.mjs hook --event session-start --root .
npm pack --dry-run
npm test -- --test-name-pattern='next.*read-only|next.*hash|next.*JSON'
python3 -m pytest -q tests/test_plan_governance_hooks.py -k 'autonomous_next or next_read_only'
npm test
python3 -m pytest -q
node bin/plan-governance-cli.mjs check . --strict-readiness
node bin/plan-governance-cli.mjs check . --drift
node bin/plan-governance-cli.mjs check . --pre-commit
```

当前阶段 2 实施快照：npm 40/40；Python 126 passed，总覆盖率 90.67%；阶段 2 定向 `plan next`、hook、JSON、串行/并行、执行约束、缺证据/阻塞、阶段门、完成边界、未知计划和无写入测试均通过。当前专项计划本身按兼容规则返回 `not_enabled`，启用计划的行为由临时目录测试覆盖。

### 最近实施/验证记录

| 日期 | 类型 | 动作/结果 | 证据 | 状态 | 记录者 |
|---|---|---|---|---|---|
| 2026-08-11 | 实施 | 增加 `plan next` 只读查询、执行约束解析、五类状态/退出码和 session-start hook 提示；不执行动作、不写回状态 | `scripts/check_plan_governance.py`；`bin/plan-governance-cli.mjs`；`scripts/plan_governance_hook.py` | 通过 | Codex |
| 2026-08-11 | 验证 | 临时启用计划的 N1—N8 行为、CLI JSON/文本、hook、无写入 hash、打包安装兼容通过；npm 40/40、Python 126 passed、覆盖率 90.67% | `tests/test_check_plan_governance.py`；`tests/npm_cli.test.mjs`；`tests/test_plan_governance_hooks.py`；`npm test`；`python3 -m pytest -q` | 通过 | Codex |

### 阶段2完成证据

阶段 2 已完成：N1—N8 真实行为、缺证据 `missing_evidence`、串行/并行 ready 集合、执行约束、阶段门、完成边界、旧计划兼容、hook、退出码、无写入 hash、安装包回归和治理检查均通过；npm 40/40、Python 126 passed、覆盖率 90.67%；最新独立完成验收已通过。计划级状态仍为 `实施中`，阶段 3 不自动放行。

阶段 2 的完成条件为：五类逻辑状态、稳定 JSON 字段结构和退出码、串行/并行 ready 集合、专项计划 `执行约束` 表中的共享写入约束、失败/缺证据阻塞、阶段门、完成边界和无写入行为均有真实正反测试；旧计划和阶段 1 的 `plan steps validate` 回归通过；hook 只提示不执行；安装包入口和反向引用检查通过；独立复核明确阶段 2 已达到完成标准。阶段 3 不因阶段 2 完成自动放行。

失败或回滚边界：若 `next` 不能可靠阻止跳步、把共享风险误判为依赖、发生写入，或旧计划兼容性受损，则撤回 `plan next` 和 hook 提示实现及其测试，保留阶段 1 的只读校验能力；不得通过降级输出或手工改状态掩盖失败。若仅是候选输出字段需要调整，先更新本节候选契约、fixture 和独立复核记录，再继续实现。

## 最新独立准入复核

| 字段 | 内容 |
|---|---|
| 日期 | 2026-08-11 |
| 阶段 | 阶段 2 |
| 结论 | 通过：阶段 2 完成验收通过；阶段 2 已关闭，阶段 3 不自动放行 |
| 证据 | [阶段 2 完成验收复核报告](../reviews/autonomous-plan-execution-stage2-completion-review-20260811.md)；[阶段 2 完成证据](#阶段2完成证据)；[阶段 2 样本矩阵](#阶段2样本矩阵) |
| 复核者 | Schrodinger（独立只读复核 subagent） |

## 独立复核记录

| 日期 | 类型 | 阶段 | 结论 | 证据 | 复核者 |
|---|---|---|---|---|---|
| - | - | 阶段 1 | 尚未进行；阶段 1 Step 0 尚未完成 | 本阶段 Step 0 和样本矩阵 | - |
| 2026-08-10 | 阶段 1 Step 0 独立准入复核 | 阶段 1 | 未通过：只有实现前基线和设计案例，尚无新入口行为测试，未达到 `待实施` 标准 | [阶段 1 独立复核报告](../reviews/plan-governance-stage1-independent-review-20260810.md) | Kepler（独立只读复核 subagent） |
| 2026-08-10 | 阶段 1 实现后独立准入复核 | 阶段 1 | 通过 | [阶段 1 独立复核报告](../reviews/plan-governance-stage1-independent-review-20260810.md) | Locke（独立只读复核 subagent） |
| 2026-08-11 | 阶段 2 Step 0 独立准入复核 | 阶段 2 | 通过：达到阶段 2 `待实施` 标准；允许切换当前阶段并开始阶段 2 实施，阶段 3 不自动放行 | [阶段 2 独立准入复核报告](../reviews/autonomous-plan-execution-stage2-independent-review-20260811.md) | Aristotle（独立只读复核 subagent） |
| 2026-08-11 | 阶段 2 实施后完成验收 | 阶段 2 | 通过：阶段 2 完成验收通过；阶段 2 已关闭，阶段 3 不自动放行 | [阶段 2 完成验收复核报告](../reviews/autonomous-plan-execution-stage2-completion-review-20260811.md) | Schrodinger（独立只读复核 subagent） |

## 未决问题

| 问题 | 推荐方案 | 是否阻塞当前阶段 | 状态 |
|---|---|---|---|
| `plan steps validate` 的路由、输出和错误定位是否已冻结？ | 已完成最小实现、V1—V5 行为测试和独立复核。 | 否 | 已完成 |
| 是否允许校验器自动修复步骤、证据或状态？ | 不允许；只读返回错误，修复和状态变更仍由执行者按计划执行。 | 否 | 已决定 |

## 风险和回滚

风险：步骤校验器被误解为自动执行器或自动验收器。

控制：命令只读，不执行动作、不补证据、不改状态；输出明确区分结构校验和业务验收。

风险：新增步骤表让旧计划无法通过治理检查。

控制：只有显式 `execution_mode` 才启用解析；旧计划返回 `not_enabled`，既有检查结果保持不变。

回滚：若解析兼容性、错误定位或无写入边界未达到 V1—V5，移除步骤校验入口和对应测试，保留阶段 0 约定、短指令策略和旧计划行为，不进入阶段 2。
