# 计划：计划治理可操作性优化

## 背景

[计划治理体系评审报告](../../plan-governance-system-review-20260810.md) 以 `motorcycle-manual-app` 2026-08-10 的真实工作区为样本，确认现有 `plan-governance` 在 Step 0、独立复核、事实源分层和失败边界方面有效；同时暴露出四类可操作性缺口：

1. 活跃计划、历史计划和完成证据混在同一主视图，无法快速调度当前工作。
2. 依赖只能表达计划级先后，不能表达阶段门、软依赖和可并行边界。
3. 准入结论、实施进展、有效运行证据与 attestation 快照没有清晰区分。
4. `--drift` 会对专项计划自身、`PLAN_MAP.md` 和当前阶段证据等正常治理变更发出未覆盖警告，降低真正遗漏的信号强度。

报告是本计划的背景和 Step 0 证据，不是本计划的事实源。本计划只优化通用 `plan-governance` 工具、模板和文档；`motorcycle-manual-app` 只作为只读验证样本，不在本计划中修改。

2026-08-10，用户已确认一项可立即冻结的执行约定：当用户要求自主推进计划到完成时，执行者无需逐步请求继续，但每项计划步骤、门禁和证据都必须实际执行，不得跳步。该约定不改变阶段准入规则，作为本计划阶段 0 的文档级澄清同步到可分发和当前已安装的 skill。

## 目标

在不把轻量计划治理变成看板或审批系统的前提下，分阶段实现：

- 让使用者能从现有治理事实源获得“当前要推进什么、下一准入动作是什么、哪些可以并行”的紧凑工作集视图。
- 以单一、可兼容的关系模型表达阶段级依赖、依赖类型、解除条件和共享写入风险。
- 并列呈现准入结论、最近实施/验证记录和 attestation 状态，避免把历史快照或实施前复核误读为当前验收。
- 让 `--drift` 精确识别计划自身、地图和已声明阶段证据的正常治理变更，继续提示真正未声明的文件。
- 让用户可用“按计划自主推进至完成，不跳步”这一短指令启用连续执行，同时保留逐项执行、阶段准入和暂停边界。
- 用真实样本和固定 fixture 验证新行为，同时保持现有项目的治理文档和默认检查入口兼容。

## 非目标

- 不创建 Web 看板、审批流、工时估算、强制负责人或强制日期字段。
- 不自动改变计划状态、自动通过准入、自动接受独立复核，或自动修改目标项目的治理文档。
- 不要求一次性移动、改写或删除历史计划、质量报告、ADR、migration 或 attestation。
- 不把 `--check-attestations` 的普通历史漂移一律升级为失败。
- 不为每个计划强制建立图谱/代码映射；计划—功能图谱映射另由后续高风险共享模块计划决定。
- 不以自然语言或通配符猜测影响范围，也不以宽泛排除 `docs/` 的方式消除 drift 警告。

## 需求探索

### 已确认事实

- 用户希望对简单且目标明确的计划使用“推进到完成计划”的短指令；执行者可以连续推进，不需要为例行步骤逐次请求继续，但不得跳过任何步骤、验证、独立复核、状态同步或完成证据。
- 当前工作集采用只读 CLI 派生视图，不在 `PLAN_MAP.md` 增加第二套人工维护的工作集事实。
- 阶段依赖采用 `PLAN_MAP.md` 内唯一的阶段关系边表；现有计划级“依赖”列保留为兼容摘要，不与阶段关系表形成第二个可冲突的事实源。
- 最近实施/验证记录作为专项计划当前阶段中的可选结构化记录；`PLAN_MAP.md` 只保留链接或索引，不覆盖“最新独立准入复核”。
- Drift 覆盖按计划自身文件、可归属到计划 ID 的 `PLAN_MAP.md` 变更和显式声明的阶段证据精确处理；归属不明确时继续 WARNING，不通过全局忽略 `docs/` 消除告警。
- Attestation 只在发布、合规或高风险完成门禁场景启用最小关系信息；普通历史快照漂移仍以 WARNING 和人工复核为主，不要求一次性回填历史计划。
- `motorcycle-manual-app` 仅作为只读验证样本，本计划不修改目标项目。

### 暂定假设与验证方式

- 当前工作集和“下一准入动作”只输出可由结构化事实直接派生的内容；不能从自由文本实施步骤猜测动作，无法判断时输出“未知/需人工确认”。通过最小活跃计划 fixture 验证。
- 阶段关系边表、workset 输出和兼容映射已经形成技术收敛稿；仍需以三计划关系 fixture 验证方向、环检测、兼容投影和输出，并由独立复核者确认后正式冻结。
- `shared_write_risk` 是并行约束或冲突提示，不是普通的硬门禁或证据依赖边；需要通过可并行和共享写入的反例 fixture 验证，避免把所有共享文件错误串行化。
- 最近实施/验证记录默认追加式保留，实施记录不得覆盖历史独立复核；具体字段和是否由检查器校验链接有效性仍待阶段 0 设计。
- Attestation 新增关系字段应保持向后兼容；需要验证旧 JSON 在 `--check-attestations` 下仍保持原有 WARNING 语义，并验证同一计划的替代链不会产生多个未解释的 current 快照。

### 范围与非目标

本次探索覆盖当前工作集、阶段级关系、实施/验证证据、治理 Drift、Attestation 和自主连续执行的策略边界。自主执行的机器可读步骤模型、下一步骤查询和步骤状态仍由独立的 `autonomous-plan-execution` 计划承载；本计划只冻结它所依赖的事实源和安全边界。

不把本次探索扩展为 Web 看板、审批系统、自动代码执行器、全量历史迁移、强制负责人/排期或自动验收。

### 候选方案与取舍

| 能力 | 采用方案 | 放弃或延后的方案 | 取舍 |
|---|---|---|---|
| 当前工作集 | 只读 CLI 派生 | `PLAN_MAP.md` 内人工维护工作集投影 | 减少重复事实；牺牲了人工排序的直接可见性，后续可增加可校验投影 |
| 阶段依赖 | `PLAN_MAP.md` 唯一阶段关系边表 | 独立关系文件或继续只用计划级依赖 | 方便单次检查和引用；需要额外定义旧依赖列的兼容校验 |
| 并行语义 | 阶段关系提供已知的可并行提示；未知时明确输出未知 | 从计划状态或自然语言推测并行关系 | 减少误调度；不能提供没有关系证据的“智能猜测” |
| 进展/证据 | 专项计划当前阶段的可选记录，地图只链接 | 在 `PLAN_MAP.md` 增加完整进展字段 | 保持地图轻量；需要维护记录格式和链接证据 |
| Drift 覆盖 | 计划 ID、显式证据和精确路径归属 | 全局忽略 `docs/` 或宽泛通配符 | 保留未声明变更信号；复杂归属时接受 WARNING |
| Attestation | 最小可选替代关系和人工复核状态 | 强制过期时间或历史计划全量迁移 | 适合发布/合规场景且兼容旧项目；暂不提供自动生命周期管理 |

### 未决问题

| 问题 | 推荐方案 | 是否阻塞当前阶段 | 状态 |
|---|---|---|---|
| 当前工作集的活跃状态集合、派生优先级和未知表示是什么？ | 仅把 `候选/设计中/待实施/实施中` 纳入活跃集合；阻塞优先，其次 `待实施→implement`，其余缺少结构化下一动作时为 `unknown`。 | 否 | 已收敛，待阶段 1 实施 |
| 阶段关系边表与旧计划级依赖如何兼容？ | 阶段表是新事实源；旧依赖仅在无阶段表时作为 legacy plan-level hard gate，有阶段表时冲突只告警。 | 否 | 已收敛，待阶段 1 实施 |
| 显式阶段证据放在哪里、如何解析？ | 当前阶段增加 `### 阶段证据`，只接受相对路径清单；未声明的证据路径继续 WARNING。 | 否 | 已收敛，待阶段 1 实施 |
| `shared_write_risk` 如何与硬门禁、证据依赖和写入所有权区分？ | 建模为独立并行约束；阶段 0 设计案例按计划拆分所有权，阶段 1 起共享实现文件采用串行写入。 | 否 | 已收敛，待阶段 1 实施 |
| Drift 如何把 `PLAN_MAP.md` 的 diff 行归属到计划 ID？ | 可唯一归属则覆盖对应计划；跨计划或无法归属时保留 WARNING。 | 否 | 已收敛，待阶段 1 实施 |
| Attestation 的快照 ID、文件命名、purpose 共存和有效状态如何校验？ | 保留旧 `<plan>.json`；新 purpose 使用带 purpose/ID 的独立快照文件，hash 漂移派生为 `needs_review`，不改写文件。 | 否 | 已收敛，待阶段 1 实施 |

### 用户确认的探索结论

2026-08-10，用户确认以上已确认事实和范围：采用 CLI 派生工作集、`PLAN_MAP.md` 阶段关系边表、计划内实施/验证记录、精确 Drift 覆盖、最小可选 Attestation 关系，以及连续执行但不跳步的策略边界。

### 独立设计复核结论

2026-08-10 的独立设计复核认为整体方向可行，但发现“唯一下一步骤”与并行执行冲突、`shared_write_risk` 与依赖边语义混淆、阶段 1 提前承诺并行提示、共享实现文件缺少机器可识别写入边界、自由文本动作不可安全推断等问题。上述问题已转入本阶段未决设计项；这次复核不等同于阶段 0 正式准入通过。

## 不变量

- `docs/plans/*.md` 继续是专项实施细节的事实源；`docs/PLAN_MAP.md` 继续是状态、当前阶段、依赖、当前阻塞和证据链接的事实源。
- 当前工作集只能是从既有事实源派生的视图，或由检查器校验的一致投影；不得成为字段方案、完成条件或验收结论的第二事实源。
- 阶段 N 完成不会自动放行阶段 N+1；任何阶段进入 `待实施` 仍须经过自己的 Step 0、样本矩阵和独立准入复核。
- 自主连续执行只减少逐步确认，不减少计划步骤、验证、独立复核或治理文档同步；“不适用”也必须按计划分支留证。
- 默认检查保持兼容；新增语义检查先以明确的 `WARNING` 提示，不将业务验收判断伪装成机械 `ERROR`。
- 所有新命令、模板与解析规则必须有 fixture 和回归测试；读取真实样本的命令必须只读。

## 影响模块或文件

- `scripts/check_plan_governance.py`
- `scripts/init_plan_governance.py`
- `scripts/plan_governance_hook.py`
- `bin/plan-governance-cli.mjs`
- `resources/skill/SKILL.md`
- `resources/skill/assets/PLAN_MAP.template.md`
- `resources/skill/assets/plan.template.md`
- `README.md`
- `plan-governance-design.md`
- `tests/test_check_plan_governance.py`
- `tests/npm_cli.test.mjs`
- `tests/fixtures/plan-governance-stage2-relations/`
- `docs/PLAN_MAP.md`
- `docs/fixtures/plan-governance-stage0-design-cases.md`
- `docs/fixtures/plan-governance-stage1-workset-cases.md`
- `docs/fixtures/plan-governance-stage2-relation-cases.md`
- `docs/reviews/plan-governance-stage2-readiness-review-20260811.md`
- `docs/reviews/plan-governance-stage0-independent-review-20260810.md`
- `docs/plans/plan-governance-operability-optimization.md`

## 公共契约变化

本计划会引入新的可选治理表达和只读查询能力。需求探索已经冻结兼容原则；命令名称、精确 Markdown 表头、JSON 字段和迁移细节已形成阶段 0 技术收敛稿，待 fixture 和正式独立准入复核后冻结。

已确认的 skill 行为契约如下，不属于待选 CLI 或文件 schema：用户说“按计划自主推进至完成”“推进到完成计划”或“自主执行且不跳步”时，执行者从当前阶段第一项开始连续、逐项执行；不跳过 Step 0、实施、验证、独立复核、状态同步或完成证据。后续阶段只有在自身已独立准入时才可继续；遇到实质偏差、未解决阻塞或需要新授权时暂停并汇总报告。

| 能力 | 候选方案 | 必须满足的兼容边界 |
|---|---|---|
| 当前工作集 | 只读 CLI 派生；不建立人工维护的工作集投影 | 既有计划索引仍是状态和阶段事实源；无法从结构化事实派生的动作或并行关系必须输出未知，不得猜测 |
| 阶段依赖 | `PLAN_MAP.md` 内唯一的阶段关系边表 | 旧计划级“依赖”列继续读取但只作兼容摘要；`shared_write_risk` 是独立并行约束，不直接等同硬门禁边 |
| 进展/证据 | 专项计划当前阶段中的可选结构化最近实施/验证记录，`PLAN_MAP.md` 只链接 | 不覆盖“最新独立准入复核”；记录不能成为自动验收结论 |
| 治理文件 drift 覆盖 | 计划 ID、计划自身路径和显式阶段证据的精确归属 | 不能全局忽略 `docs/`；跨计划或无法归属的变更继续告警 |
| Attestation | 可选 `purpose`、`supersedes`、`review_status` 关系；旧字段和旧 JSON 继续兼容 | 普通历史漂移不自动阻断；发布/合规/高风险场景由人工决定是否接受 |

### 阶段 0 技术收敛稿（待独立准入复核）

以下是当前阶段推荐冻结的最小技术契约。它只约束后续实现和 fixture，不代表这些命令或字段已经存在。

#### 当前工作集只读输出

入口暂定为 `plan-governance-cli workset [--json]`。默认文本输出面向人工调度，`--json` 输出稳定结构；两种输出均只读，不修改计划、地图、Git 或外部系统。

```json
{
  "schema_version": 1,
  "source": "derived",
  "plans": [
    {
      "plan": "<plan-id>",
      "status": "设计中",
      "phase": "阶段 0",
      "readiness": "design|ready|in_progress|blocked|unknown",
      "blockers": [],
      "next_action": {
        "state": "known|unknown",
        "kind": "resolve_blocker|complete_step0|independent_review|implement|verify|sync|none",
        "reason": "<仅引用结构化事实>"
      },
      "parallel": {
        "state": "known|unknown",
        "peers": [],
        "reason": "<关系证据或未知原因>"
      },
      "recent_evidence": []
    }
  ],
  "warnings": []
}
```

`next_action` 不得从自由文本“实施步骤”猜测；缺少结构化事实时必须返回 `unknown`。`parallel.state=unknown` 不等于允许并行，也不等于必须串行，只表示当前没有足够关系证据。

工作集派生规则固定为：

1. 仅 `候选`、`设计中`、`待实施`、`实施中` 进入活跃工作集；其他状态只在 `--include-history` 下显示。
2. 当前阶段存在非占位阻塞项时，`readiness=blocked`、`next_action.kind=resolve_blocker`。
3. 无阻塞且状态为 `待实施` 时，`readiness=ready`、`next_action.kind=implement`。
4. 状态为 `实施中` 时，`readiness=in_progress`；只有显式 `下一动作` 结构化字段才能派生 `verify`、`sync` 等动作。
5. 无阻塞且状态为 `候选/设计中` 时，如果当前阶段 `阶段准入摘要` 的 `Step 0`、`样本矩阵`、`验证方式` 或 `失败/回滚边界` 是缺失/占位值，`next_action.kind=complete_step0`。
6. 无阻塞且上述四项齐全，但 `最新独立准入复核` 不是通过当前阶段的结论时，`next_action.kind=independent_review`。
7. 其他缺少结构化下一动作的情况，`next_action.state=unknown`，不得从自然语言猜测；`none` 只用于显式声明当前阶段无需动作的计划。

#### 阶段关系边表

`docs/PLAN_MAP.md` 的阶段关系表是唯一事实源，方向统一为“来源阶段 → 目标阶段”：

| 来源计划 | 来源阶段 | 目标计划 | 目标阶段 | 关系类型 | 解除条件 | 证据 |
|---|---|---|---|---|---|---|
| `<upstream-plan>` | `阶段 N` | `<downstream-plan>` | `阶段 M` | `hard_gate\|evidence\|soft_context` | `<结构化条件>` | `<链接>` |

- `hard_gate`：目标阶段不得进入实施，直到解除条件和独立准入证据满足。
- `evidence`：目标阶段需要来源阶段提供指定证据，但不自动改变目标阶段生命周期。
- `soft_context`：仅提供排序或上下文，不阻塞实施。
- `shared_write_risk` 不作为上述依赖边的关系类型，而在并行/共享写入约束中单独表达；它不自动制造业务先后关系。
- 旧计划级“依赖”列继续兼容读取；若与阶段关系表冲突，以阶段关系表作为新模型事实源，并输出兼容 WARNING。

兼容规则固定为：存在阶段关系表时，旧依赖列只作摘要校验；阶段表中的 `hard_gate`/`evidence` 来源计划可投影到旧依赖列，`soft_context` 和共享写入约束不投影。只有没有阶段关系表的旧地图，旧依赖列才按 legacy plan-level hard gate 读取，并标记兼容来源。

#### 最近实施/验证记录

记录放在专项计划当前阶段，采用追加式最小字段；`PLAN_MAP.md` 只引用最新记录入口：

| 字段 | 约束 |
|---|---|
| 日期 | `YYYY-MM-DD` |
| 类型 | `实施`、`验证`、`阻塞` 或 `同步` |
| 动作/结果 | 简短事实描述，不替代完成定义 |
| 证据 | 命令、测试名、文档锚点、提交或可定位运行记录 |
| 状态 | `通过`、`失败`、`阻塞` 或 `待复核` |
| 记录者 | 实施者或执行 Agent；不代表独立验收 |

实施记录不得覆盖、改写或替代“最新独立准入复核”；独立复核仍使用固定章节和追加式记录。

#### Attestation 最小关系

在现有快照字段上增加可选字段。旧快照继续使用 `docs/attestations/<plan>.json`；缺少 `purpose` 的旧快照按 `phase_completion` 归类。新关系快照使用 `docs/attestations/<plan>--<purpose>--<snapshot-id>.json`，其中 `snapshot-id` 必须匹配 `YYYYMMDDTHHMMSSZ-[0-9a-f]{8}`，在同一计划/purpose 下唯一，并作为 JSON 的 `snapshot_id` 字段保存：

| 字段 | 值/语义 |
|---|---|
| `purpose` | `phase_completion`、`release_gate`、`compliance` |
| `supersedes` | 规范化为同一仓库内的相对文件路径；目标必须存在、purpose 相同且不能形成环；无替代时为空 |
| `review_status` | `current`、`superseded`、`needs_review` |

旧 JSON 缺少这些字段时按旧行为处理；存在 hash 漂移时仍输出 WARNING。有效状态按以下优先级派生：被其他快照 `supersedes` 的快照为 `superseded`；自身 hash 漂移或声明 `needs_review` 时为 `needs_review`；声明 `current` 且 hash 未漂移时才为 `current`。同一计划/purpose 的唯一性按“有效状态为 `current`”计算；多个 current、缺失替代目标或替代环均为结构错误。`release_gate` 和 `compliance` 快照必须人工复核后才能被外部门禁接受；不引入自动过期时间。

#### 显式阶段证据

专项计划当前阶段使用 `### 阶段证据` 声明治理检查应覆盖的相对路径，每行一个反引号路径；路径必须位于仓库根目录，不能使用绝对路径或通配符。没有该章节时不自动扩大 Drift 覆盖范围；无法唯一归属的变更继续 WARNING。

## 阶段路线图

| 阶段 | 目标 | 进入条件 | 验证方向 | 状态 |
|---|---|---|---|---|
| 阶段 0 | 冻结最小兼容契约、样本矩阵和迁移边界，并同步已确认的自主连续执行约定 | 本计划与地图已同步；真实样本基线可只读复现 | 当前工作集、阶段依赖、证据状态、drift 与自主执行语义的设计复核 | 已完成 |
| 阶段 1 | 提供派生的当前工作集与准入/实施/证据状态入口；关系未知时明确标记未知 | 阶段 0 独立准入复核通过 | fixture、CLI 输出、旧地图兼容和反向引用检查 | 已完成 |
| 阶段 2 | 提供阶段级依赖与可并行关系的单一表达 | 阶段 1 完成；关系 schema 与兼容投影已冻结 | 依赖环、阶段门、软依赖、共享写入风险和旧计划级依赖兼容测试 | 已完成 |
| 阶段 3 | 收口 drift 覆盖、attestation 提示和模板/文档迁移 | 阶段 2 完成；治理文件覆盖规则已冻结 | 真实样本回放、warning 信噪比、完成快照语义、安装包和独立验收 | 设计中 |

## 阶段 0 设计记录

### 范围

当前为阶段 0，只做契约和验证设计，不实现 CLI、模板、检查器或目标项目改动：

1. 将评审报告中的 P0/P1 问题映射到最小通用能力，不引入看板或全量历史迁移。
2. 用 `motorcycle-manual-app` 的只读基线验证四类问题确实存在，并将其抽象为不含项目专有路径的 fixture 场景。
3. 选定单一关系事实源和兼容策略，明确哪些字段是可选投影、哪些是计划实施事实。
4. 为阶段 1—3 定义可执行样本、失败判定、回滚边界与独立准入条件。
5. 同步用户已确认的自主连续执行约定到 `resources/skill/SKILL.md` 和当前已安装的 skill；这只澄清执行边界，不改变代码、CLI、模板或阶段状态。
6. 在阶段 0 独立准入复核前，不修改其他生产代码、CLI 命令、模板或分发资源。

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

1. 记录真实样本基线和现有 CLI/模板能力，建立不含目标项目私有内容的 fixture。
2. 比较当前工作集、阶段依赖、证据状态和治理 drift 覆盖的候选表达，选择最小兼容契约。
3. 将最终字段、命令、兼容策略、迁移/回滚方式和 warning 语义写回“公共契约变化”。
4. 核对可分发和已安装 skill 的自主连续执行约定一致，确保短指令不削弱逐项执行或阶段准入。
5. 为阶段 1—3 补齐 fixture、失败案例、验证命令和完成条件。
6. 由未参与阶段 0 设计的复核者对范围、样本和准入条件独立复核；通过后进入阶段 1 的独立 Step 0 准备，不得直接将阶段 1 标记为 `待实施`。

### 阶段证据

- `docs/fixtures/plan-governance-stage0-design-cases.md`
- `docs/reviews/plan-governance-stage0-independent-review-20260810.md`

### 阶段 0 Step 0 证据

基线类型为“真实仓库只读回放 + 当前工具回归测试”。已确认的基线如下：

- 评审样本项目在 2026-08-10 有 32 个专项计划，其中 3 个活跃；`PLAN_MAP.md` 同时承载索引、推荐顺序、当前阻塞和完成证据，当前工作集难以直接辨识。
- 样本项目的 `data-release-validation` 已有阶段 1 推进记录，但最新独立复核是阶段 1 实施前准入结论，证明“准入”和“实施进展”需要并列而不能覆盖。
- 样本项目的三个活跃计划存在阶段 0 可并行、候选级验证才硬依赖的关系；现有计划级依赖不足以表达该边界。
- 对样本项目运行 `plan-governance-cli check <root> --drift` 以退出码 0 通过，但对 `PLAN_MAP.md`、两个专项计划和两个当前阶段证据文件发出未覆盖 WARNING，证明现有作用域匹配缺少治理文件的精确覆盖规则。
- 本仓库 2026-08-10 执行 `npm test` 通过 37/37 项；现有 `--strict-readiness`、`--drift`、`--check-attestations` 和图谱命令均已有实现与测试入口。
- 用户已确认自主执行的边界是“连续推进但逐项执行、不跳步”，而不是自动跳过阶段门禁或只在最终状态补写证据。

阶段 0 不以这些观察直接冻结设计；每条观察都必须在下列样本矩阵中以可重复输入、预期结果和失败判定固定。

### 阶段 0 样本矩阵

| 样本 | 输入或基线 | 可执行命令 | 预期结果 | 失败判定 | 输出位置 |
|---|---|---|---|---|---|
| 当前工作集 | 3 个活跃、其余为完成/废弃的最小 `PLAN_MAP.md` fixture，包含一个无法结构化推断下一动作的计划 | `test -f docs/fixtures/plan-governance-stage0-design-cases.md && rg -n '案例 A|complete_step0|unknown' docs/fixtures/plan-governance-stage0-design-cases.md`；阶段 1 再转为 `workset --json` 测试 | 只呈现活跃计划及可结构化派生的准入动作、当前阻塞和最近进展入口；未知动作和未知并行关系明确标记 | 历史计划成为默认待办，或从自然语言猜出动作/并行关系 | 设计案例文档；后续 `tests/` fixture 与测试输出 |
| 阶段关系 | “阶段 0 可并行、候选验证才硬门禁、共享写入需串行”的三计划 fixture | `rg -n '案例 B|soft_context|hard_gate|legacy|WARNING' docs/fixtures/plan-governance-stage0-design-cases.md`；阶段 2 再做关系解析/校验测试 | 区分 `hard_gate`、`evidence`、`soft_context` 与独立的 `shared_write_risk` 约束，并说明解除条件 | 把共享写入风险误当硬门禁，或关系与旧依赖摘要冲突 | 设计案例文档；后续 `tests/` fixture 与测试输出 |
| 状态与证据 | 同一计划同时含准入复核、阶段推进记录和已漂移 attestation 的 fixture | 状态/快照检查测试 | 分别输出准入、最近进展/证据和快照有效性；不把 warning 当验收失败 | 实施记录覆盖准入结论，或过期快照仍显示为当前完成 | `tests/` fixture 与测试输出 |
| 治理 drift 覆盖 | 专项计划自身、地图中该计划的变更、显式证据文件及一个无关文件 | `--drift` 与 `--pre-commit` 测试 | 前三类按计划精确覆盖；无关文件保留 WARNING | 通过全局忽略 `docs/` 消除告警，或仍对已声明治理文件告警 | `tests/` fixture 与测试输出 |
| 旧项目兼容 | 仅有六列计划索引和计划级依赖的 fixture | 基础检查、严格准入和迁移/兼容测试 | 不增加必填字段即可保持既有命令和结果 | 新版本要求历史项目补齐新字段才能运行基础检查 | `tests/` fixture 与测试输出 |
| 自主连续执行 | 明确步骤、失败分支和后续阶段准入的专项计划 | skill 文本反向引用检查和人工场景复核 | 短指令触发连续逐项执行；步骤、独立复核和状态同步均不跳过 | 将“推进至完成”解释为自动推进未准入阶段、静默跳过步骤或省略最终证据 | skill 源文件与已安装副本 |

### 阶段 0 完成条件

- 四类能力各有至少一个正常样本和一个失败/边界样本，且样本不依赖目标项目绝对路径或未提交状态。
- 当前工作集、阶段关系、状态/证据和 drift 覆盖各自只有一个明确事实源与派生边界。
- 最终公共契约、兼容策略、warning/ERROR 语义和阶段 1—3 的回滚方式已写入本计划。
- 新旧计划索引、现有 `--strict-readiness`、`--drift`、`--pre-commit` 与 `--check-attestations` 的兼容影响已逐项记录。
- 阶段 1 不在缺少阶段关系证据时输出确定的并行结论；阶段 2 才负责阶段级并行关系和共享写入约束的机器可检查表达。
- 可分发与当前已安装的 skill 均包含相同的自主连续执行约定，且该约定没有降低阶段准入或独立验收要求。
- 当前阶段的阶段 0 设计无未解决阻塞项；独立准入复核明确阶段 0 修订设计通过，但阶段 1 仍须自身 Step 0 和独立准入。

### 阶段 0 历史验证方式

阶段 0 完成前至少执行：

```bash
npm test
plan-governance-cli check .
plan-governance-cli check . --strict-readiness
SAMPLE_ROOT=<只读评审样本仓库根目录>
plan-governance-cli check "$SAMPLE_ROOT" --drift
plan-governance-cli check "$SAMPLE_ROOT" --check-attestations
rg -n 'plan-governance-operability-optimization|当前工作集|阶段依赖|自主连续执行|latest_review|latest_evidence|attestation|--drift' docs README.md resources scripts tests
PLAN_GOVERNANCE_SKILL_PATH=<当前已安装 plan-governance SKILL.md 的路径>
cmp -s resources/skill/SKILL.md "$PLAN_GOVERNANCE_SKILL_PATH"
rg -n '草案为准|以草案为事实源|详见草案|draft is source|source of truth.*draft|以.*draft.*为准' docs README.md resources
```

阶段 1—3 的实现验证必须在阶段 0 冻结后补充：新旧 fixture 回归、CLI 打包安装验证、默认与严格治理检查、warning 精确性测试，以及不修改样本项目的只读回放记录。

### 阶段 0 历史测试覆盖率

阶段 0 基线为 2026-08-10 的 `npm test`：37/37 项通过。当前仓库的 Node 测试不输出百分比覆盖率，因此以完整测试清单、新增正常/失败 fixture 和关键 CLI 路径回归作为覆盖证据；若后续引入覆盖率工具，必须记录实际命令和结果，不得伪造百分比。

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

本阶段的详细未决项以[需求探索—未决问题](#需求探索)为事实源。这里仅保留准入视图，避免重复定义已经确认的产品取舍。

| 问题 | 推荐方案 | 是否阻塞当前阶段 | 状态 |
|---|---|---|---|
| 阶段 0 最小兼容契约、fixture 和回滚边界是否已冻结？ | 技术收敛稿、设计案例和修订后的独立复核已完成；进入阶段 1 前仍须建立其自身准入材料。 | 否 | 已收敛，待阶段 1 实施 |
| 当前阶段是否达到阶段 1 `待实施` 标准？ | 阶段 0 修订设计已通过；阶段 1 仍需自己的 Step 0、样本矩阵、验证命令、完成条件和独立准入，因此当前不标记为 `待实施`。 | 是 | 待阶段 1 Step 0 |

### 阶段 0 历史风险和回滚

风险：新增主视图或阶段关系造成事实重复、历史项目解析失败，或把轻量治理变成需要长期维护的看板。

控制：优先采用只读派生视图和可选结构；保留既有六列索引、计划级依赖和默认命令；所有新解析先经过旧项目 fixture 回归。

风险：治理文件被自动视为覆盖，会掩盖没有关联到任何活跃计划的真实文档变更。

控制：只自动覆盖专项计划自身和可归属到计划 ID 的地图行；阶段证据仅接受显式声明；归属不明确时继续 WARNING。

风险：将 attestation 漂移升级为自动阻断，导致普通说明修订妨碍开发。

控制：保持普通快照为 WARNING；仅在发布、合规或明确完成门禁引用快照时，由人决定是否阻断。

回滚：任何阶段若兼容性、warning 信噪比或事实源边界未达到样本矩阵要求，停止该阶段，不迁移目标项目；移除新命令/可选段落和对应测试，保留既有 `PLAN_MAP.md`、计划级依赖、drift 和 attestation 行为。

## 关联 ADR、迁移、spec 或 issue

- 背景评审：[计划治理体系评审报告](../../plan-governance-system-review-20260810.md)
- 相关已完成计划：[plan-drift-check-enhancements](plan-drift-check-enhancements.md)、[phase-entry-gate-hardening](phase-entry-gate-hardening.md)、[agent-runtime-integration](agent-runtime-integration.md)、[architecture-graph-governance](architecture-graph-governance.md)
- 当前不创建 ADR 或 migration；阶段 0 若确定需要不可兼容的文件 schema 迁移，再单独新建对应文档。

## 阶段 1 历史实施记录

### 范围

当前为阶段 1，已完成“当前工作集与准入/实施/证据状态入口”的实现、验证和独立复核：

1. 只读解析 `PLAN_MAP.md` 计划索引，以及专项计划当前阶段的结构化准入摘要、最新复核和最近实施/验证记录。
2. 冻结 `workset [--json] [--include-history]` 的稳定输出和工作集派生规则，不建立第二套人工状态事实。
3. 阶段 1 不新增关系 schema、不做关系图计算；如果 `PLAN_MAP.md` 已有可直接读取的当前计划关系，可只读透传对应 peers 和证据，否则必须输出 `parallel.state=unknown`。阶段 2 再实现关系校验、环检测和共享写入约束的机器可检查表达。
4. 不实现自主步骤表解析、`next` 查询、attestation 生命周期或 drift 覆盖改造；这些由对应阶段和专项计划承载。

### 阶段准入摘要

| 字段 | 内容 |
|---|---|
| 准入状态 | 实施中 |
| 阶段状态 | 已完成 |
| Step 0 | [阶段 1 Step 0 证据](#阶段-1-step-0-证据) |
| 样本矩阵 | [阶段 1 样本矩阵](#阶段-1-样本矩阵) |
| 验证方式 | [验证方式](#验证方式) |
| 失败/回滚边界 | [风险和回滚](#风险和回滚) |
| 当前阻塞项 | 无；阶段 2 仍需自身 Step 0、验证方式、完成条件和独立准入复核 |
| 最新独立准入复核 | [2026-08-10 独立复核：通过，达到阶段 1 `待实施` 标准](../reviews/plan-governance-stage1-independent-review-20260810.md) |

### 实施步骤

1. 记录当前 CLI 没有 `workset` 入口的可复现基线，并冻结不影响既有命令的兼容边界。
2. 用 W1—W6 fixture 固定活跃/历史过滤、阻塞优先、未知动作、复核分层、旧计划兼容和只读约束。
3. 将 `workset` 文本/JSON 字段、退出码、WARNING/ERROR 语义和不猜测规则写入实现契约。
4. 实现后运行默认/严格治理、npm 回归、fixture、打包安装和无写入 hash 检查。
5. 由未参与阶段 1 设计的复核者独立复核；通过后关闭阶段 1，计划级状态仍保持 `实施中`，不自动进入阶段 2。

### 阶段 1 实施授权记录

2026-08-10，用户在阶段 1 独立复核未通过后明确要求“继续”，本记录将其解释为允许开始阶段 1 的 CLI、检查器和测试实现，用于补齐复核指出的真实行为证据。授权范围仅包括 `workset` 入口、工作集派生和相关测试；不包括阶段 2 的关系校验/`next`、自动执行器、目标业务项目或外部系统改动。阶段 1 完成后仍须重新独立准入复核，不能用本授权替代准入结论。

### 阶段证据

- `docs/fixtures/plan-governance-stage1-workset-cases.md`
- `docs/reviews/plan-governance-stage1-independent-review-20260810.md`

### 阶段 1 Step 0 证据

本节保留实现前基线，类型为“现有 CLI 只读回放 + 设计 fixture + 既有测试回归”。实现前已确认：

- 当前 CLI 只支持 `check`、`init`、`setup`、`hook`、`graph` 和既有 `plan` 路由，没有 `workset` 命令。
- 运行 `plan-governance-cli workset --json` 当前退出码为 2，Python 检查器报告不支持 `--json`；这证明新入口尚未实现，不能把设计文档误当成现有能力。
- `scripts/check_plan_governance.py` 已有计划索引、状态、阶段准入、依赖、drift、停滞和 attestation 检查，但没有工作集派生入口。
- 2026-08-10 的 `npm test` 为 37/37，通过严格治理检查；这是阶段 1 实现前的兼容基线。
- 阶段 0 已冻结 `readiness`、`next_action`、`parallel` 和 `recent_evidence` 的最小字段；阶段 1 只实现当前工作集入口，不重新定义这些字段。

### 最近实施/验证记录

| 日期 | 类型 | 动作/结果 | 证据 | 状态 | 记录者 |
|---|---|---|---|---|---|
| 2026-08-10 | 实施 | 增加 `workset` 入口、活跃/历史过滤、准入动作派生、直接关系透传和文本/JSON 输出 | `bin/plan-governance-cli.mjs`、`scripts/check_plan_governance.py`、npm CLI 行为测试 | 通过 | Codex |
| 2026-08-10 | 验证 | npm 39/39、Python 97 passed、覆盖率 91.39%、严格治理和 diff 检查通过；打包安装后的 `workset` 与 `plan steps validate` 冒烟通过 | `npm test`；`python3 -m pytest -q`；`node bin/plan-governance-cli.mjs check . --strict-readiness`；`git diff --check`；临时打包安装 smoke test | 通过 | Codex |
| 2026-08-11 | 同步 | 当前仓库 `plan-governance-cli@0.3.0` 已安装到本机全局 CLI；`workset` 全局入口回归通过，Codex/Claude skill 清单资源已同步 | `npm pack`；`npm install -g plan-governance-cli-0.3.0.tgz`；`plan-governance-cli workset --json --root /Users/jafish/Documents/work/plan-governance`；`plan-governance-cli setup --target all --force`；清单资源 hash 对比 | 通过 | Codex |
| 2026-08-11 | 回滚 | 按用户要求将全局 CLI、Codex skill 和 Claude skill 恢复到同步前状态；当前仓库计划和代码未回退 | `/tmp/plan-governance-sync.aow9Lt` 中的同步前备份；恢复后旧全局检查器与备份 hash 一致；旧入口拒绝 `workset --json --root` 新参数 | 通过 | Codex |

### 阶段 1 样本矩阵

| 样本 | 输入或基线 | 可执行命令 | 预期结果 | 失败判定 | 输出位置 |
|---|---|---|---|---|---|
| 活跃/历史过滤 | W1：三个活跃计划和一个已完成历史计划 | `test -f docs/fixtures/plan-governance-stage1-workset-cases.md && rg -n '案例 W1|include-history|old' docs/fixtures/plan-governance-stage1-workset-cases.md` | 默认只返回活跃计划；显式参数才包含历史计划 | 历史计划成为默认待办或工作集写回地图 | fixture；后续 `tests/` 输出 |
| 阻塞和未知 | W2：阻塞计划与无结构化动作计划 | `rg -n '案例 W2|resolve_blocker|unknown' docs/fixtures/plan-governance-stage1-workset-cases.md` | 阻塞优先；无法派生时明确 unknown | 从自由文本猜测 implement/verify | fixture；后续 `tests/` 输出 |
| Step 0/复核分层 | W3：缺 Step 0 与缺当前阶段复核的计划 | `rg -n '案例 W3|complete_step0|independent_review' docs/fixtures/plan-governance-stage1-workset-cases.md` | 分别返回 complete_step0 与 independent_review | 用测试通过替代独立准入 | fixture；后续 `tests/` 输出 |
| 并行未知和证据 | W4：无阶段关系表但有最近记录的两个计划 | `rg -n '案例 W4|parallel.state=unknown|recent_evidence' docs/fixtures/plan-governance-stage1-workset-cases.md` | 并行关系 unknown；最近证据可定位 | 从索引顺序猜并行或复制字段方案 | fixture；后续 `tests/` 输出 |
| 旧计划兼容 | W5：旧六列表地图和无结构化摘要的计划 | `rg -n '案例 W5|旧计划|not_enabled' docs/fixtures/plan-governance-stage1-workset-cases.md` | 既有 check 结果不变，工作集不伪造动作 | 要求历史计划迁移或阻断基础检查 | fixture；后续兼容测试 |
| 错误和无写入 | W6：重复 ID/非法状态及合法查询 hash | `rg -n '案例 W6|WARNING|ERROR|hash' docs/fixtures/plan-governance-stage1-workset-cases.md` | 默认 WARNING、严格 ERROR；合法查询无写入 | 错误时输出确定动作或改写文件 | fixture；后续临时目录 hash |

### 阶段 1 完成条件

- `workset` 支持文本和稳定 JSON 输出，默认只返回活跃计划，`--include-history` 的边界可验证。
- `next_action` 严格按阶段 0 冻结规则派生；阻塞、Step 0、独立复核和未知动作不互相混淆。
- 阶段 1 只透传已冻结阶段关系表中的直接证据；没有关系证据时 `parallel.state=unknown`，不从自然语言、索引顺序或计划状态猜测并行，完整关系校验留到阶段 2。
- 旧计划和未启用结构化字段的计划不因工作集入口而被要求迁移；既有基础/严格检查结果保持兼容。
- 结构错误的默认/严格输出、退出码、fixture 和无写入 hash 均有测试证据。
- `workset` 的文本/JSON、活跃/历史过滤、阻塞/未知/准入动作、直接关系透传、结构错误、历史计划兼容、阶段状态与计划状态分离、退出码和无写入行为已有测试；Python 覆盖率达到 91.39%。
- 默认/严格治理、npm 39/39、Python 97 passed、CLI 打包清单、反向引用检查和无写入 hash 已通过；最新独立复核已通过，阶段 2 仍须自身准入，不自动放行。

## 验证方式

阶段 1 实施和独立复核前至少执行：

```bash
node bin/plan-governance-cli.mjs workset --json
node bin/plan-governance-cli.mjs workset --json --strict-readiness
node bin/plan-governance-cli.mjs check .
node bin/plan-governance-cli.mjs check . --strict-readiness
npm test
python3 -m pytest -q
test -f docs/fixtures/plan-governance-stage1-workset-cases.md
rg -n 'workset|include-history|resolve_blocker|complete_step0|independent_review|parallel.state=unknown' docs/fixtures/plan-governance-stage1-workset-cases.md docs/plans/plan-governance-operability-optimization.md
git diff --check
```

实现后追加：新旧 fixture 回归、CLI 打包安装 smoke test、合法查询前后 hash 对比、目标项目只读回放和重新独立准入复核。当前仓库用 `node bin/plan-governance-cli.mjs workset --json` 验证本地实现，安装包再用 `plan-governance-cli workset --json` 回归。

## 测试覆盖率

阶段 1 的可复现基线仍为 `npm test` 37/37；当前 Node 测试不输出百分比覆盖率。实现后以 W1—W6 的正反 fixture、文本/JSON 两种输出和默认/严格模式作为最低覆盖证据，不伪造覆盖率百分比。

## 最新独立准入复核

| 字段 | 内容 |
|---|---|
| 日期 | 2026-08-11 |
| 阶段 | 阶段 2 |
| 结论 | 通过：阶段 2 已完成；R1—R7、完成条件、实施回归和独立验收均通过，阶段 3 未放行 |
| 证据 | [阶段 2 完成验收复核报告](../reviews/plan-governance-stage2-readiness-review-20260811.md)；[阶段 2 完成验收](#阶段-2-完成验收)；[阶段 2 关系校验样本](../fixtures/plan-governance-stage2-relation-cases.md) |
| 复核者 | Banach（独立只读复核 subagent） |

## 独立复核记录

| 日期 | 类型 | 阶段 | 结论 | 证据 | 复核者 |
|---|---|---|---|---|---|
| - | - | 阶段 1 | 尚未进行；阶段 1 Step 0 尚未完成 | 本阶段 Step 0 和样本矩阵 | - |
| 2026-08-10 | 阶段 1 Step 0 独立准入复核 | 阶段 1 | 未通过：只有实现前基线和设计案例，尚无新入口行为测试，未达到 `待实施` 标准 | [阶段 1 独立复核报告](../reviews/plan-governance-stage1-independent-review-20260810.md) | Kepler（独立只读复核 subagent） |
| 2026-08-10 | 阶段 1 实现后独立准入复核 | 阶段 1 | 通过 | [阶段 1 独立复核报告](../reviews/plan-governance-stage1-independent-review-20260810.md) | Locke（独立只读复核 subagent） |
| 2026-08-11 | 阶段 2 Step 0 独立准入复核 | 阶段 2 | 未通过：R1—R7 尚未提供可执行输入/输出/退出码，shared_write_risk 兼容规则和关系校验语义仍未冻结 | [阶段 2 准入复核报告](../reviews/plan-governance-stage2-readiness-review-20260811.md) | Hume（独立只读复核 subagent） |
| 2026-08-11 | 阶段 2 修订后独立准入复核 | 阶段 2 | 未通过：候选实现和主要测试已通过，但 R2/R5、真实阶段引用、四列/九列兼容和证据分层仍有缺口 | [阶段 2 准入复核报告](../reviews/plan-governance-stage2-readiness-review-20260811.md) | Wegener（独立只读复核 subagent） |
| 2026-08-11 | 阶段 2 第三轮独立准入复核 | 阶段 2 | 未通过：主要实现和回归已通过，但合法关系差异、旧依赖保留、目标阶段错误、证据路径和四列/九列冲突反例仍需补强 | [阶段 2 准入复核报告](../reviews/plan-governance-stage2-readiness-review-20260811.md) | Volta（独立只读复核 subagent） |
| 2026-08-11 | 阶段 2 第四轮独立准入复核 | 阶段 2 | 未通过：仅剩阶段 2 完成条件章节和 R6 命令覆盖范围两个文档准入缺口 | [阶段 2 准入复核报告](../reviews/plan-governance-stage2-readiness-review-20260811.md) | Boyle（独立只读复核 subagent） |
| 2026-08-11 | 阶段 2 修订后最终独立准入复核 | 阶段 2 | 通过：阶段 2 达到 `待实施` 标准；R1—R7、完成条件和 R6 命令覆盖均已确认 | [阶段 2 准入复核报告](../reviews/plan-governance-stage2-readiness-review-20260811.md) | Boyle（独立只读复核 subagent） |
| 2026-08-11 | 阶段 2 首次完成验收 | 阶段 2 | 未通过：技术项已通过，但完成后的阶段状态、PLAN_MAP 完成证据和独立验收记录尚未同步 | [阶段 2 完成验收复核报告](../reviews/plan-governance-stage2-readiness-review-20260811.md) | Banach（独立只读复核 subagent） |
| 2026-08-11 | 阶段 2 完成验收复核 | 阶段 2 | 通过：阶段 2 已完成；R1—R7、完成条件、实施回归和独立验收均通过，阶段 3 未放行 | [阶段 2 完成验收复核报告](../reviews/plan-governance-stage2-readiness-review-20260811.md) | Banach（独立只读复核 subagent） |

## 未决问题

| 问题 | 推荐方案 | 是否阻塞当前阶段 | 状态 |
|---|---|---|---|
| `workset` 的文本/JSON 输出、退出码和未知动作语义是否已冻结？ | 已完成最小实现、W1—W6 行为测试和独立复核。 | 否 | 已完成 |
| 工作集是否提前实现完整阶段关系和并行约束？ | 不实现完整校验；仅透传已有关系表中的直接证据，缺少或无法唯一归属时输出 unknown，阶段 2 再实现关系解析。 | 否 | 已决定 |

## 风险和回滚

风险：工作集入口与 `PLAN_MAP.md` 或专项计划产生第二套状态事实。

控制：只读派生，所有字段回指现有事实源；无法判断时输出 unknown，不写入投影。

风险：旧计划因为缺少新字段而被误判或阻断。

控制：旧计划返回结构化信息不足/unknown；默认和严格治理保持原兼容边界。

回滚：若输出契约、兼容性或 warning 信噪比未达到 W1—W6，移除 `workset` 入口和对应测试，保留阶段 0 文档契约、现有检查器和旧计划行为，不修改目标项目。

## 阶段 2 设计与准入记录

阶段 1 已关闭；阶段 2 已完成自身 Step 0、验证条件和独立准入复核，达到 `待实施` 标准。当前 `PLAN_MAP.md` 已将阶段指针切换到阶段 2；本节承载阶段 2 的关系契约、样本、完成条件和准入记录。

### 目标与非目标

- 目标：让现有 `check` 入口只读校验 `PLAN_MAP.md` 的阶段关系边表、旧计划级依赖兼容关系、依赖环和独立的共享写入约束。
- 目标：默认检查保留 WARNING 兼容语义，`--strict-readiness` 对结构错误返回 ERROR；`workset` 继续只读取已确认的关系，不产生第二套事实。
- 非目标：不新增独立关系查询命令，不自动修改阶段状态，不把共享写入风险转换为业务硬门禁，不修改目标业务项目。

### 阶段 2 Step 0 证据

基线类型为“当前关系表只读回放 + 旧依赖兼容快照 + 关系样本矩阵”。已确认：

- Step 0 基线时，当前 `PLAN_MAP.md` 已有阶段关系表，但检查器只在 `workset` 中透传直接关系，尚未校验关系类型、计划/阶段引用、解除条件、证据、环依赖或共享写入约束；随后形成的候选校验实现尚未纳入正式阶段完成证据。
- 当前检查器已有计划级依赖环检测；阶段关系环不能直接复用计划级依赖结果，否则会丢失阶段身份和关系类型。
- 当前 `PLAN_MAP.md` 的共享写入表是人工说明，尚未具备固定的机器字段，不能被解释为已完成的结构化约束。
- 当前仓库运行 `node bin/plan-governance-cli.mjs check . --strict-readiness` 通过，仅有两个活跃计划共享影响目标的预期 WARNING；这是阶段 2 实现前基线。
- 候选关系样本已拆分为 R1—R7，见 [`plan-governance-stage2-relation-cases.md`](../fixtures/plan-governance-stage2-relation-cases.md)；阶段 2 实现前必须由独立复核者确认契约和失败边界。

### 候选契约和兼容边界

阶段 2 候选方案复用现有 `check`，不新增 CLI 入口。`阶段关系` 继续是唯一关系事实源，`hard_gate`、`evidence`、`soft_context` 三种关系语义保持阶段 0 技术收敛稿；`hard_gate`/`evidence` 参与阶段级环检测，`soft_context` 不参与环检测；计划和阶段引用必须存在于索引/阶段路线图（旧计划没有阶段路线图时保持兼容），关系结构错误默认 WARNING，严格模式 ERROR。旧计划没有阶段关系表时保持旧依赖行为；有阶段关系时仅对同一计划对的 `hard_gate` 缺少旧依赖项告警，额外旧依赖保留，不被阶段表静默覆盖。

现有四列表 `并行与共享写入约束` 继续作为人工说明；可选九列表 `机器可检查共享写入约束` 才进入机器校验。只有四列表保持旧兼容；两者同时存在时九列表是机器校验事实源，四列表不覆盖九列表；九列表缺失或结构错误只影响机器校验，不把人工说明误判为已通过的机器约束。

该候选方案的详细七列/九列表头、R1—R7 输入、预期结果和失败判定以[阶段 2 关系校验样本](../fixtures/plan-governance-stage2-relation-cases.md)为准；在独立准入复核通过前，不将其视为已冻结公共契约。

### 阶段 2 验证和回滚边界

- 验证必须覆盖合法关系、未知引用、非法关系类型、缺失解除条件/证据、硬门禁/证据环、旧依赖冲突、共享写入风险和只读 hash。
- 默认检查不能因为历史计划没有新表而失败；严格检查只对当前存在的结构错误提升为 ERROR。
- 如果关系表解析、兼容投影或 warning 信噪比不满足 R1—R7，回滚新增关系解析和测试，保留阶段 1 `workset` 只读透传及旧计划级依赖行为。
- 如果四列表/九列表混用规则、阶段路线图引用、旧依赖告警或非法关系对 `workset` 的降级语义不满足 R1—R7，回滚新增关系解析和测试，保留阶段 1 `workset` 只读透传及旧计划级依赖行为。

### 阶段 2 完成条件

阶段 2 关闭前必须同时满足：

- `阶段关系` 七列表和可选的机器共享写入九列表按候选契约通过 R1—R7；默认检查保持兼容，严格检查对结构错误返回 ERROR，非法关系下 `workset.parallel.state=unknown`。
- 旧计划无阶段关系表时默认和严格检查均保持兼容；旧依赖额外项不被阶段关系静默覆盖；四列表/九列表混用时九列表优先且有反例测试。
- 全量 Python 测试通过且总覆盖率不低于 85%，npm 测试全部通过；严格治理、停滞检查、Node/Python 语法检查、`git diff --check` 和本地链接检查通过。
- 反向引用扫描未发现草案重新成为事实源；检查、workset 和查询 fixture 前后 hash 一致；未修改目标业务项目或本机全局安装状态。
- 阶段 2 实施细节、验证证据、完成条件和独立验收结论已写入本计划，`PLAN_MAP.md` 已同步计划状态、当前阶段、阻塞项和证据链接；阶段 3 不因阶段 2 完成自动放行。

### 阶段 2 实施结果

2026-08-11，阶段 2 最终独立准入复核通过后，正式纳入先前形成的候选关系校验实现。实现范围严格限定为本计划明确的现有 `check` 入口、关系解析/校验、`workset` 非法关系降级、测试 fixture 和治理文档；不新增独立关系命令，不修改 `motorcycle-manual-app`，不同步本机全局 CLI/skill。

- `scripts/check_plan_governance.py`：校验阶段关系七列表、阶段真实引用、解除条件、证据路径、hard_gate/evidence 环和 soft_context 语义；校验可选共享写入九列表，并保持四列表兼容。
- `tests/fixtures/plan-governance-stage2-relations/`、`tests/test_check_plan_governance.py`：固定 R1—R7 合法/非法/legacy/环/共享写入/只读样本和行为断言。
- `docs/fixtures/plan-governance-stage2-relation-cases.md`、本计划和 `docs/PLAN_MAP.md`：记录正式实施契约、验证方式、完成条件、状态和证据链接。

本次正式实施回归已执行阶段 2 定向测试、全量 Python/npm 测试、严格治理、停滞检查、语法/格式检查和直接 fixture 回放；下一步是独立阶段完成验收，阶段 3 仍不自动放行。

### 阶段 2 完成验收

阶段 2 技术验收已完成：R1—R7、全量 Python/npm 测试、覆盖率、严格治理、停滞检查、语法/格式、反向引用、事实源扫描、直接 fixture 回放和只读 hash 均通过。独立验收者确认没有计划外行为变化，指出的唯一收口项是将阶段完成状态、完成证据和独立验收记录同步到本计划及 `PLAN_MAP.md`；本次已完成该同步，最终独立确认记录见[阶段 2 验收复核报告](../reviews/plan-governance-stage2-readiness-review-20260811.md)。

## 当前阶段

### 范围

当前为阶段 2，已完成正式实施和独立验收：

1. 固化 `阶段关系` 七列表、旧计划级依赖兼容投影和可选机器共享写入九列表。
2. 通过现有 `check` 入口执行默认 WARNING、严格 ERROR、环检测、阶段真实引用、证据路径和共享写入约束校验。
3. 保持 `workset` 只读；关系结构错误时并行状态为 `unknown`，不自动修改计划状态或关系事实源。
4. 阶段 2 已完成独立验收并同步状态；阶段 3 不自动进入实施。

### 阶段准入摘要

| 字段 | 内容 |
|---|---|
| 准入状态 | 实施中 |
| 阶段状态 | 已完成 |
| Step 0 | [阶段 2 Step 0 证据](#阶段-2-step-0-证据) |
| 样本矩阵 | [阶段 2 关系校验样本](../fixtures/plan-governance-stage2-relation-cases.md) |
| 验证方式 | [阶段 2 验证方式](#阶段-2-验证方式) |
| 失败/回滚边界 | [阶段 2 验证和回滚边界](#阶段-2-验证和回滚边界) |
| 当前阻塞项 | 无；阶段 2 已完成，阶段 3 保持设计中并需自身准入 |
| 最新独立准入复核 | [2026-08-11 阶段 2 完成验收：通过](../reviews/plan-governance-stage2-readiness-review-20260811.md) |

### 阶段 2 验证方式

```bash
python3 -m pytest -q --no-cov tests/test_check_plan_governance.py -k 'stage2_relation or stage2_legacy or stage2_shared_write or stage2_nine_column'
python3 -m pytest -q
npm test
node bin/plan-governance-cli.mjs check .
node bin/plan-governance-cli.mjs check . --strict-readiness
node bin/plan-governance-cli.mjs check . --stale-days 10
node --check bin/plan-governance-cli.mjs
python3 -m py_compile scripts/check_plan_governance.py
git diff --check
```

阶段 2 实施和验收还必须回放 `tests/fixtures/plan-governance-stage2-relations/` 下的合法、非法、环、legacy 和共享写入样本，运行反向引用/事实源扫描，并对 check/workset 前后文件执行 SHA-256 对比。

### 阶段 2 准入动作

1. 由未参与阶段 1 实现的复核者独立检查 R1—R7、候选契约、Step 0 命令和回滚边界。
2. 复核通过后，更新 `PLAN_MAP.md` 当前阶段为阶段 2，并补齐正式 `当前阶段` 准入摘要；当前已存在的候选实现不计为阶段完成证据，需在复核结论中正式纳入或按回滚边界撤回。
3. 阶段 2 实现只写入共享 CLI、检查器、测试和地图的串行窗口；阶段 2 完成后再做独立验收，不自动放行阶段 3。

### 阶段 2 实施偏差记录

2026-08-11，第一轮阶段 2 准入复核未通过后，为把 R1—R7 从设计描述补齐为可执行行为证据，先行加入了候选关系校验、fixture 和测试。这属于“实现先行”的流程偏差；候选实现不自动改变阶段指针、准入状态或完成证据，必须由后续独立复核确认，若复核仍未通过则按本节回滚边界撤回。

当前候选实现的验证快照：`python3 -m pytest -q` 为 106 passed、覆盖率 90.66%；`npm test` 为 39/39；`node bin/plan-governance-cli.mjs check . --strict-readiness` 通过；这些是候选实现证据，不是阶段 2 完成结论。
