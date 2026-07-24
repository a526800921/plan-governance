# 计划：架构图谱治理与三层图谱衔接

## 背景

当前功能图谱试点采用“功能 YAML + GitNexus 代码图谱”的两层衔接。试点已经证明业务语义关系和代码对象可以建立映射，但也暴露出一个边界问题：如果功能图谱节点普遍保存 GitNexus UID，就会把代码索引引用维护责任扩散到业务语义层。

本计划记录后续的三层图谱方向，在功能图谱与 GitNexus 代码图谱之间增加架构图谱，降低功能语义与函数级代码之间的直接耦合。它是 [功能图谱治理与影响分析 CLI](functional-graph-governance.md) 的后续计划，不改写其阶段 0-3 已完成的历史验收结论。

## 目标

- 明确功能图谱、架构图谱和代码图谱的职责边界。
- 让功能图谱主要描述业务、功能、流程和外部能力，不普遍维护代码对象引用。
- 以架构图谱承载系统、模块、组件、服务、接口和数据边界等中间层事实。
- 将 GitNexus UID 从功能图谱节点的普遍字段收缩为少量、可选的架构层到代码层映射。
- 为后续的跨层影响分析和计划前置分析建立可验证的衔接契约。
- 保持需求前置分析轻量：默认只查询功能层，按 API、数据、安全、共享架构或定位代码的风险信号逐层下钻。

## 非目标

- 当前阶段不修改 ModelPad Swift 代码、运行时或对外 API。
- 当前阶段不立即迁移既有 `functional.yaml`，也不删除现有 GitNexus 引用。
- 不在架构图谱中复制 GitNexus 的函数调用、依赖或完整代码关系。
- 当前阶段不把功能图谱扩展为产品线组合模型，不预建 `AND`、`OR`、`XOR`、`Excludes` 等组合约束。
- 不要求每个计划遍历功能、架构和代码三层；测试映射、新鲜度、生命周期和 GitNexus 定位均不是默认前置步骤。
- 不把架构图谱做成图形化浏览器、远程图数据库或自动架构治理平台。
- 不让 Git hook 或 CLI 自动改写 YAML；自动重绑定候选必须经过只读报告和 LLM/人工确认。

## 需求探索

### 已确认事实

- 功能图谱的首要职责是描述功能及其业务、流程和外部能力关系，不应与代码产生过多直接关联。
- 功能图谱、架构图谱、代码图谱构成更合理的三层结构：功能层回答“业务上影响什么”，架构层回答“经过哪些系统边界和模块”，代码层回答“具体哪些文件、类、函数和调用链”。
- 当前 `functional-graph-governance` 阶段 0-3 已完成，但其试点 YAML 中仍有 9 个 GitNexus 引用；这些引用是当前试点的映射验收样本，不应成为所有功能节点的强制模型。
- GitNexus 的索引会随提交更新，UID 可以提供精确、无歧义的代码对象定位，但不应作为功能语义的长期稳定主键。
- GitNexus 是函数级代码图谱；架构图谱应位于功能图谱和 GitNexus 之间。
- API 的路由、协议、请求/响应和版本等技术契约唯一归架构层；功能层只记录用户视角的对外能力，并通过跨层映射关联架构接口，不重复维护 endpoint 或协议事实。

### 暂定假设与验证方式

- 功能图谱优先保留业务、功能、流程和外部 workflow，不重复维护 API 技术契约。
- 架构图谱优先建模系统、模块、组件、服务、接口、数据边界和代码范围，不枚举函数。
- 架构层到代码层的稳定主引用应是仓库内文件、符号名和符号类型等可重绑定定位；GitNexus UID 作为可选的精确索引引用或缓存。
- 通过 ModelPad 的真实场景和最小架构节点矩阵验证三层传播是否比功能层直连代码更容易维护；若架构层只增加重复数据而没有降低耦合，则停留在设计边界。

### 范围与非目标

- 范围：三层职责边界、节点归属、跨层关系、代码映射契约、ModelPad 架构层试点和计划前置分析衔接。
- 非目标：当前直接实施架构图谱运行时、自动迁移全部历史功能图谱或自动刷新 YAML。

### 候选方案与取舍

- 候选方案 A：功能图谱直接连接 GitNexus。实现简单，但业务层承担代码 UID 漂移和映射维护，作为长期模型不采用。
- 候选方案 B：功能图谱、架构图谱、GitNexus 三层衔接。增加一层架构事实，但能把代码映射维护收敛到少量架构边界，作为当前推荐方案。
- 候选方案 C：只保留功能图谱和文件路径证据，不做架构图谱。维护成本最低，但无法表达模块、组件和服务边界，暂不作为完整方案。

### 用户确认的探索结论

- 采用功能图谱、架构图谱、代码图谱三层结构作为后续设计方向。
- 功能图谱不应普遍包含代码相关字段；GitNexus 引用从“节点普遍字段”进一步收缩为“少量可选映射”。
- API 技术契约归架构层；功能层只保留用户视角的对外能力，并通过跨层关系关联架构接口。
- 当前阶段不引入 `AND`、`OR`、`XOR`、`Excludes` 等功能组合约束；仅在 ModelPad 出现功能开关、套餐、互斥模式或可选组合等真实需求时，才以版本化扩展和 fixture 纳入。
- 功能层核心关系收敛为 `contains`、`depends_on`、`orchestrates`、`consumes`；`implements`、`exposes` 迁入架构层或功能到架构的跨层关系。具体 YAML 字段形态仍由后续 Schema 实施阶段承载，跨层关系方向已按本计划冻结。
- 后续跨层影响分析输出行动分级：`必须评估`、`必须测试`、`建议检查`。分级表达待执行的治理动作，不根据单条关系断言“代码必须修改”。
- 后续引入分层测试映射：功能层关联验收/场景测试，架构层关联集成/契约测试，代码层关联单元测试；影响分析应能输出受影响范围及建议执行的测试，当前阶段不实施。
- 声明 `graph_scope` 的计划必须提供一个主 `change_kind`：`behavior_change`、`api_contract_change`、`internal_refactor`、`data_migration` 或 `security_change`。它是计划输入，不写入功能节点；同时含多个高风险类型时拆分为可复核的变更项。
- 图谱新鲜度遵循“只读发现候选 → LLM 依据证据更新 → 证据不足时人工兜底”：提交或实施前可比对代码锚点、测试和文档变化生成待复核候选，但 hook 与 CLI 均不得自动写回 YAML。
- 后续 Schema 支持最小节点生命周期：`active`、`deprecated`、`retired`。下线、合并或替换功能时保留稳定 ID 和可选替代线索，不直接删除历史节点；当前阶段不迁移 ModelPad 现有节点。
- 跨层映射允许多对多，但影响查询只沿与 `change_kind` 匹配的方向保守展开；共享架构或代码对象关联的其他功能进入“必须评估”，不自动升级为“必须测试”。
- 跨层关系最小集合已冻结为：`realized_by`（功能 → 架构，功能由哪个架构边界承载）、`contains`（架构 → 架构，边界或组件包含下属边界）、`exposes`（架构 → 接口，架构边界提供接口契约）、`crosses`（架构 → 数据/信任边界，变更或调用跨越边界）和 `anchors_to`（架构 → 代码，架构边界对应代码范围）。这些关系不复制函数调用、类层级或业务关系。
- 三层 Schema 采用干净切换，不承担现有功能图谱 v1 的兼容或迁移成本。旧 `functional.yaml` 只保留为背景，不再作为新 CLI 或新计划的输入事实源；当前阶段不删除文件。
- 架构层仅为真实存在的鉴权/权限边界、持久化数据边界和外部数据交换边界建模，不创建泛泛的“安全功能”节点；`security_change` 与 `data_migration` 据此定位影响路径、测试和回滚检查。
- 功能层和架构层是两类独立事实源，但物理文件支持按领域拆分为多个 YAML，并各自通过 `index.yaml` 提供 Schema 版本、加载清单和跨文件入口；不固定为两份单文件。
- 代码锚点以仓库内文件路径、全限定符号名和符号类型为长期主引用；GitNexus UID 只作为可选精确索引，行号不得作为主键。
- 需求前置分析默认只执行功能层 `graph_scope` 与 `change_kind` 查询；仅出现 API 契约、数据迁移、安全变更、共享架构影响或需要定位代码对象时，才升级查询架构层和 GitNexus。
- 用户已确认 ModelPad 的最小架构边界为本地 HTTP API、配置持久化、模型进程管理、App 状态编排和外部模型服务五组；默认需求前置只查功能层，命中 API、数据、安全、共享架构或代码定位信号时才逐层升级。
- 性能优化暂归 `internal_refactor`，通过性能基线和专项测试表达非功能风险；当前不增加 `performance_change` 枚举，除非后续真实样本证明其行动路径不同。
- 人工确认不是常规审批：LLM 能依据证据确认时直接更新 YAML 并运行后置校验；只有 LLM 无法确认、证据冲突或语义存在多个合理解释时，才生成候选并找用户确认。
- 当前记录进入本专项计划；具体 Schema、节点枚举、关系方向和迁移方式必须在阶段 0 重新冻结后才能实施。

## 不变量

- 功能图谱仍是业务语义事实源，架构图谱是系统边界事实源，GitNexus 是代码事实源。
- 同一事实只在一个层级维护，其他层级通过显式关系或可定位引用连接。
- GitNexus UID 缺失或失配不能静默伪装为稳定映射；应报告待解析、候选或失配状态。
- `graph validate`、影响分析和重绑定候选查询保持只读，不自动更新 YAML、计划状态或代码。
- LLM 是图谱的默认维护者：能依据证据确认时直接更新 YAML；CLI、hook 和 GitNexus 只读地产生候选，只有 LLM 无法确认、证据冲突或存在多个合理解释时才上升人工确认。
- 当前阶段写细，后续阶段只记录目标和准入条件，不提前冻结未确认的字段方案。

## 影响模块或文件

- `docs/plans/architecture-graph-governance.md`
- `docs/PLAN_MAP.md`
- `docs/plans/functional-graph-governance.md`：仅增加后续计划链接和边界说明
- `docs/modelpad-architecture-stage0-inventory-2026-07-24.md`：ModelPad 阶段 0 只读候选与轻量/升级样本
- `docs/modelpad-architecture-stage0-llm-replay-2026-07-24.md`：LLM 自动维护与人工兜底的只读设计回放
- `docs/modelpad-architecture-stage1-validation-2026-07-24.md`：ModelPad 阶段 1 架构 YAML、映射和回归验收记录
- `docs/modelpad-architecture-stage2-gitnexus-replay-2026-07-24.md`：ModelPad 阶段 2 GitNexus 新鲜度、命中和失配回放
- ModelPad 的 `docs/graph/functional.yaml`：后续阶段候选迁移范围，当前不修改
- 后续候选架构图谱文件：路径和 Schema 待阶段 0 冻结
- `scripts/graph_governance.mjs` 与测试：仅在阶段 1 明确需要修改时纳入

## 公共契约变化

阶段 0 需要冻结以下契约，当前不将候选字段视为已实施事实：

```text
功能图谱 → 架构节点 → 代码锚点 → 可选 GitNexus UID
```

其中 API 路由、协议、请求/响应和版本属于架构节点；功能节点不得复制这些技术契约，只能通过跨层关系表达其对外能力由哪个架构接口承载。

功能层的内部关系仅表达功能组成、业务依赖、流程编排和外部业务能力使用（`contains`、`depends_on`、`orchestrates`、`consumes`）；`implements`、`exposes` 等实现与接口暴露事实属于架构层或跨层关系，不再作为功能层内部关系。跨层关系使用以下固定方向，具体 YAML 字段形态仍由后续 Schema 实施阶段承载：

| 关系 | 方向 | 影响分析用途 |
|---|---|---|
| `realized_by` | 功能 → 架构 | 默认把功能影响升级到承载它的架构边界 |
| `contains` | 架构 → 架构 | 传播共享边界和下属组件的评估范围 |
| `exposes` | 架构 → 接口 | `api_contract_change` 定位接口契约及其消费者 |
| `crosses` | 架构 → 数据/信任边界 | `data_migration`、`security_change` 定位跨边界影响 |
| `anchors_to` | 架构 → 代码 | 仅在需要代码定位时连接文件、符号和可选 GitNexus UID |

默认查询先沿 `realized_by` 展开；API 契约变更追加 `exposes`，数据迁移或安全变更追加 `crosses`，需要具体实现定位时再使用 `anchors_to` 或 GitNexus。共享架构的反向关联默认标记为“必须评估”，不因存在关系就自动变为“必须测试”。

阶段 3 的跨层影响查询除路径和证据外，还应输出 `必须评估`、`必须测试`、`建议检查` 三类行动建议。它们只说明计划治理的后续动作，不能由单一关系自动推导为“代码必须修改”。

需求前置分析采用默认轻量、按风险升级的路径：所有声明 `graph_scope` 的计划先查询功能层；只有 `api_contract_change`、`data_migration`、`security_change`、共享架构影响或需要定位代码对象时，才查询架构层；需要文件、类、函数或调用链证据时才调用 GitNexus。测试映射、新鲜度检查、生命周期查询和 GitNexus 定位均为条件能力，不是每次计划的固定门禁。

测试映射是阶段 3 之后或与阶段 3 同步评估的后续能力：功能节点关联验收/场景测试，架构节点关联集成/契约测试，代码锚点或代码图谱关联单元测试。未建立映射时，报告必须明确“无可用测试映射”，不得虚构测试覆盖。

声明 `graph_scope` 的计划还必须声明一个主 `change_kind`。初期枚举为 `behavior_change`、`api_contract_change`、`internal_refactor`、`data_migration`、`security_change`；它用于选择跨层查询范围、行动分级和建议测试，不属于功能节点属性。一个计划同时包含多个高风险类型时，必须拆分为可独立验收的变更项。

新鲜度检查只读比对代码锚点、测试和文档的变化，输出待复核候选及其证据。LLM 仅在候选有充分证据时更新图谱；关系语义、节点拆分/合并或映射存在歧义时必须上升确认。Git hook、CLI 和重绑定查询均不得自动写回 YAML。

候选报告至少包含变更类型、受影响节点或关系、证据文件与定位、自动更新或上升确认的结论。仅代码锚点变更可由代码证据确认；新增或修改业务关系、功能节点拆分/合并至少还需要测试、API 契约或产品文档等语义证据。自动写入后必须运行新 Schema 校验并保留影响分析前后差异。

后续 Schema 应支持 `active`、`deprecated`、`retired` 三种最小生命周期。`deprecated` 表示现有能力仍可用但不得新增依赖，`retired` 表示能力已移除且仅保留历史与可选替代线索；影响查询默认以 `active` 节点为主，历史、迁移或回滚查询才显式包含其他状态。

功能到架构、架构到代码的映射可以是多对多，但跨层影响不能无条件反向展开。查询必须结合 `change_kind` 选择允许的跨层方向；由共享架构或代码对象反查到的其他功能默认标为“必须评估”，除非存在直接关系、契约证据或测试映射，才可升级为“必须测试”。

架构层只在有仓库证据时记录鉴权/权限边界、持久化数据边界和外部数据交换边界。`security_change` 应沿信任边界定位接口、消费者和权限测试；`data_migration` 应沿数据边界定位读写方、迁移/回滚要求和相关集成测试。不得为了覆盖枚举而创建泛泛的“安全功能”节点。

三层 Schema 不要求兼容或迁移既有功能图谱 v1。新 Schema 启用后，以新文件和新 CLI 的输入范围为唯一事实源；旧 `functional.yaml` 仅作背景材料，不参与校验、影响分析或计划前置门禁。切换前先建立新 Schema 的独立样本与验证，当前阶段不删除旧文件。

功能层和架构层各自使用目录与 `index.yaml` 组织；`index.yaml` 承载 Schema 版本、加载清单和跨文件入口，领域文件承载节点与关系。拆分策略按业务域或系统边界决定，稳定 ID 必须在同一层全局唯一。

架构到代码的长期主锚点固定为以下信息：

```yaml
file: Sources/...
symbol: Module.Type.method
kind: method
gitnexus_uid: <可选>
```

文件路径、全限定符号名和符号类型用于重绑定；GitNexus UID 仅提供精确索引。行号可以作为诊断定位信息，但不得参与锚点身份或重绑定判定。

## 阶段路线图

| 阶段 | 目标 | 进入条件 | 验证方向 | 状态 |
|---|---|---|---|---|
| 阶段 0 | 冻结三层边界、节点归属、API 归属和可选代码映射契约 | 用户已确认三层方向 | ModelPad 现状矩阵、最小架构样本、维护成本和反向引用检查 | 已完成 |
| 阶段 1 | 建立 ModelPad 最小架构图谱并验证功能到架构的映射 | 阶段 0 独立准入通过 | 架构节点/关系校验、三个真实场景和重复事实检查 | 已完成 |
| 阶段 2 | 衔接架构图谱与 GitNexus 代码图谱 | 阶段 1 完成，代码锚点契约已冻结 | 少量 UID 映射、失配候选、重绑定报告和代码级影响查询 | 待实施 |
| 阶段 3 | 接入计划治理的三层前置影响分析 | 阶段 2 完成 | `graph_scope`、`change_kind` 跨层查询、行动分级、测试映射与新鲜度候选只读报告、独立验收 | 待规划 |

## 当前阶段

当前阶段指针：阶段 2（待实施）。阶段 0 和阶段 1 已完成独立复核；阶段 2 的 Step 0、样本矩阵、验证方式和独立准入复核均已完成。

### 阶段 2 准入状态

| 字段 | 内容 |
|---|---|
| 准入状态 | 待实施 |
| 当前阻塞项 | 无；阶段 2 独立准入复核已达到“待实施”标准 |
| 实施边界 | 首批只实施少量架构→代码映射；不修改 GitNexus 索引，不复制函数调用关系，不改写功能层 YAML |
| 进入条件 | 已满足；后续实施仍须遵循本阶段的失败和回滚边界 |

## 阶段准入摘要

| 字段 | 内容 |
|---|---|
| 准入状态 | 待实施 |
| Step 0 | [阶段 2 Step 0 证据](#阶段-2-step-0-证据) |
| 样本矩阵 | [阶段 2 样本矩阵](#阶段-2-样本矩阵) |
| 验证方式 | GitNexus 状态、UID 命中/失配、稳定代码锚点和只读候选报告回放 |
| 失败/回滚边界 | 阶段 2 只生成只读映射候选；边界未收敛时不修改 ModelPad 架构 YAML 和 GitNexus 索引 |
| 当前阻塞项 | 无 |
| 最新独立准入复核 | 2026-07-24，阶段 2，达到“待实施”标准；详见[最新独立准入复核](#最新独立准入复核) |

### 阶段 2 Step 0 证据

阶段 2 只负责架构层到代码图谱的少量可选映射、UID 新鲜度和失配候选，不把 GitNexus 函数调用关系复制到架构图谱，也不改变阶段 1 已完成的功能→架构映射。

#### 代码锚点候选

架构层维护逻辑上的 `anchors_to` 映射，物理上使用独立的 `code_mappings` 数组保存 `code_anchor` 对象，不创建代码节点。长期主键使用仓库内文件路径、全限定符号名和符号类型；GitNexus UID 只作为可选精确索引。候选结构如下：

```yaml
code_mappings:
  - architecture_id: architecture.modelpad.model-process-management
    code_anchor:
      file: Sources/ModelPadCore/Process/ModelProcessManager.swift
      symbol: ModelProcessManager
      kind: class
      gitnexus_uid: <可选>
```

同一架构边界可以有多个 `code_anchor`，但每个锚点必须有唯一的文件、符号和类型组合；不得把 GitNexus 调用链复制到 YAML。首批只验证以下三类边界，不扩展到每个函数：

| 架构边界 | 稳定代码锚点 | GitNexus UID | 维护目的 |
|---|---|---|---|
| 本地 HTTP API | `Sources/ModelPadCore/API/APIServer.swift` / `APIHandler` / `class` | 可选 | 定位接口处理边界 |
| 配置持久化 | `Sources/ModelPadCore/Persistence/ConfigStore.swift` / `ConfigStore` / `class` | 可选 | 定位配置读写边界 |
| 模型进程管理 | `Sources/ModelPadCore/Process/ModelProcessManager.swift` / `ModelProcessManager` / `class` | 可选 | 定位进程生命周期边界 |

代码锚点不是新的代码事实源；它只说明架构边界对应的代码范围。函数、调用链、依赖和数据流继续由 GitNexus 负责。

#### 新鲜度和 LLM 维护边界

- `gitnexus status` 只读报告索引 commit 与当前 commit 的差异；索引 stale 不等于所有 UID 立即失效。
- GitNexus `context --uid` 命中时记录精确命中；未命中时保留稳定代码锚点并生成失配候选，不静默删除映射。
- GitNexus `analyze` 不由 hook、CLI 或阶段 2 映射校验自动触发；是否重新索引属于独立操作，索引刷新后仍需重新验证候选。
- LLM 能依据文件、符号类型、符号名和 GitNexus 查询证据唯一确认时，可更新架构层映射；证据冲突、多个符号候选或无法确认时才请求用户。
- 任何 UID 重绑定、架构边界拆分/合并和 `anchors_to` 方向变化，都必须保留候选报告和前后差异；不自动写回。

#### 只读候选报告 CLI 契约

为让 LLM 在修改计划前获得可复现的重绑定证据，阶段 2 增加以下只读命令：

```text
plan-governance-cli graph code candidates \
  [--file <relative-path>] \
  --symbol <symbol> \
  --kind <kind> \
  [--format text|json] \
  <root>
```

- `--file` 可省略：省略时在仓库代码文件中搜索同名符号，用于验证多候选边界；提供时优先在指定文件中搜索。
- `--symbol`、`--kind` 是必填定位条件；首期 `kind` 至少支持 `class` 和 `function`，不把行号作为身份。
- 输出只包含查询条件、候选文件、符号、类型、行号和 `resolution`：`unique_candidate`、`ask_user` 或 `no_candidate`；多候选必须为 `ask_user`。
- 命令不解析或写回架构 YAML，不修改 GitNexus 索引，不自动触发 `analyze`；LLM 是否更新 `code_mappings` 仍受唯一证据和人工兜底规则约束。
- 失败边界：搜索工具不可用、输入不完整或根目录非法时返回错误；无候选和多候选均返回成功的只读报告，不伪造映射。

#### 代码级影响查询 CLI 契约

在架构代码锚点已由 LLM 唯一确认后，使用 GitNexus 查询代码级影响范围：

```text
plan-governance-cli graph code impact \
  --repo <gitnexus-repo> \
  --file <relative-path> \
  --symbol <symbol> \
  --kind <kind> \
  [--depth 3] \
  [--format text|json] \
  <root>
```

- `--repo` 必填，禁止根据当前目录猜测 GitNexus 仓库，避免跨项目误查；`file/symbol/kind` 使用已确认的稳定代码锚点。
- 命令只调用 `gitnexus impact`，输出查询条件、GitNexus 返回的风险、直接/间接数量、受影响流程和模块；不把 GitNexus 函数关系复制回 YAML。
- GitNexus 不可用、repo 未注册、索引失配或查询失败时返回错误并保留原始诊断；不自动执行 `analyze`，不把失败降级为“无影响”。
- 该命令是架构层到代码层的查询验证，不改变功能层默认的轻量影响分析路径；只有计划声明需要定位代码对象时才调用。

### 阶段 2 样本矩阵

| 样本 | 输入或基线 | 可执行命令 | 预期结果 | 失败判定 | 当前状态 |
|---|---|---|---|---|---|
| 索引新鲜度 | ModelPad 当前提交 `0dde74d`、GitNexus 索引提交 `d63eb71` | `gitnexus status` | 明确报告 stale 和两者 commit，不直接判定 UID 全部失效 | stale 被静默忽略或自动触发 analyze | 已通过只读回放 |
| UID 精确命中 | `Function:Sources/ModelPadCore/API/APIServer.swift:APIHandler.handleStart#1` | `gitnexus context -r modelpad --uid <uid>` | `status: found`，返回文件、符号和范围 | 命中被当作架构事实，或没有记录证据 | 已通过只读回放 |
| UID 失配 | `Function:Sources/ModelPadCore/API/APIServer.swift:APIHandler.handleStart#999` | 同上 | 生成失配候选，保留文件/符号 fallback | 失配被静默删除或误报为精确命中 | 已通过只读回放 |
| 稳定锚点无 UID | `ModelProcessManager.swift` + `ModelProcessManager` + `class` | `test -f ... && rg -n 'class ModelProcessManager' ...` | 可作为长期映射，不依赖 UID | 把缺少 UID 判为无映射 | 已通过只读基线和架构 fixture |
| 多候选重绑定 | ModelPad 中的 `APIHandler`：`APIServer.swift:89` 与 `mlx_lm_server_fork.py:986` | `plan-governance-cli graph code candidates --symbol APIHandler --kind class --format json /Users/jafish/Documents/work/ModelPad` | 产生两个候选，`resolution: ask_user`；不得自动选择或写回 | 自动选择任意候选并写回 | 已通过 CLI 测试和真实只读回放 |
| 代码级影响查询 | 已确认的 `APIServer.swift` / `APIHandler` / `class` | `plan-governance-cli graph code impact --repo modelpad --file Sources/ModelPadCore/API/APIServer.swift --symbol APIHandler --kind class --depth 2 --format json /Users/jafish/Documents/work/ModelPad` | 返回 GitNexus 风险、影响数量、流程和模块，不触发 analyze | 误查其他 repo、失败被伪装为无影响或自动刷新索引 | 已通过 CLI 测试和 ModelPad 真实回放 |

阶段 2 Step 0 要求的精确命中、失配、无 UID 锚点、多候选和索引 stale 五类样本均已有可复现输出；候选报告 CLI、代码级查询和失败边界测试均已通过，独立准入复核明确达到“待实施”标准。

#### 阶段 2 当前实现候选证据

- 架构层校验器已支持 `code_mappings[].code_anchor`，校验架构节点归属、文件存在性、`file + symbol + kind` 唯一性和可选 UID 格式。
- 通用架构 fixture 已覆盖无 UID 锚点、悬空架构节点、代码文件缺失和重复锚点反例；阶段 2 新增测试与阶段 1 测试合计 12 项架构测试通过。
- 根仓库全量测试当前为 32/32 通过，功能层默认路径保持兼容。
- 候选报告 CLI 已实现并覆盖唯一候选、多候选、无候选三种解析结果；在 ModelPad 真实回放中，同名符号出现在 Swift 与 Python 文件中，输出 `ask_user`，不允许 LLM 在缺少文件约束时猜测。
- 代码级影响 CLI 已实现并覆盖 GitNexus 结果封装、错误边界和不触发 `analyze` 的测试；ModelPad 真实回放返回 `CRITICAL`、34 个受影响符号、30 个直接、4 个间接，涉及 1 个流程和 2 个模块。
- ModelPad 当前只保留阶段 1 的架构边界和功能→架构映射；`code_mappings` 暂不写入 ModelPad，待独立准入复核通过后再决定首批少量映射。

### 阶段 1 完成记录

### 阶段 1 准入状态

| 字段 | 内容 |
|---|---|
| 准入状态 | 已完成 |
| 当前阻塞项 | 无；阶段 1 已关闭，阶段 2 另行执行准入流程 |
| 实施边界 | 已创建 ModelPad 架构 YAML；未迁移或删除现有 `functional.yaml`，未修改 Swift 代码 |
| 进入条件 | 阶段 1 独立完成复核已通过 |

## 阶段 1 准入摘要

| 字段 | 内容 |
|---|---|
| 准入状态 | 实施中 |
| Step 0 | [阶段 1 Step 0 证据](#阶段-1-step-0-证据) |
| 样本矩阵 | [阶段 1 Step 0 样本矩阵](#阶段-1-step-0-样本矩阵候选) |
| 验证方式 | 架构层正反例测试、功能层回归、架构 fixture 校验和治理检查 |
| 失败/回滚边界 | 阶段 1 实施失败时只移除新增架构 YAML，不修改现有功能图谱、Swift 代码、GitNexus 索引或计划历史 |
| 当前阻塞项 | 三层结果、重复事实检查和阶段 1 完成验收尚未完成 |
| 最新独立准入复核 | [2026-07-24 阶段 1 通过](#最新独立准入复核) |

### 阶段 1 Step 0 证据

阶段 1 Step 0 定义最小架构图谱的输入、校验和场景基线。通用校验器和正反例 fixture 已通过独立准入复核，以下内容成为阶段 1 的实施契约；ModelPad 正式 YAML 已按此创建并完成校验。

#### 候选文件布局

功能层和架构层保持独立目录与事实源；功能→架构的 `realized_by` 映射由架构层维护，不回写功能 YAML。ModelPad 的候选布局为：

```text
docs/graph/functional/index.yaml       # 新三层切换后的功能层入口，当前仍不迁移旧文件
docs/graph/architecture/index.yaml     # 架构层入口，已创建
docs/graph/architecture/modelpad-boundaries.yaml
docs/graph/architecture/mappings.yaml  # 架构层维护 realized_by 等跨层映射
```

`architecture/index.yaml` 负责声明架构 Schema 版本、加载领域文件和功能层外部引用；`mappings.yaml` 只维护跨层映射，不复制功能节点的业务描述。上述架构路径已成为 ModelPad 现行路径，功能层仍以旧 `functional.yaml` 作为只读背景输入。

#### 最小 Schema 候选

```yaml
schema_version: 1
layer: architecture
nodes:
  - id: architecture.modelpad.local-http-api
    type: interface
    name: 本地 HTTP API 接口边界
    evidence:
      - kind: code
        ref: Sources/ModelPadCore/API/APIServer.swift
        locator: APIServer
relations:
  - type: contains
    from: architecture.modelpad.app-state-orchestration
    to: architecture.modelpad.local-http-api
    evidence:
      - kind: code
        ref: App/Sources/AppViewModel.swift
        locator: API 回调与核心对象装配
```

阶段 1 首期候选节点类型限制为 `system`、`module`、`component`、`service`、`interface`、`data_boundary`、`trust_boundary`；节点必须有可定位证据。候选关系只允许阶段 0 冻结的 `contains`、`exposes`、`crosses`、`anchors_to`，以及架构层维护的跨层 `realized_by`。关系两端必须存在且不得自环、重复；不得把函数调用、类继承或完整 GitNexus 关系复制进来。`anchors_to` 和 GitNexus UID 在阶段 1 只作为可选字段/关系形态保留，实际代码图谱衔接仍由阶段 2 验证。

#### 阶段 1 Step 0 样本矩阵候选

| 样本 | 输入或基线 | 预期命令 | 预期结果 | 失败判定 | 当前状态 |
|---|---|---|---|---|---|
| 最小合法架构图谱 | 五组 ModelPad 架构边界节点、最小 `contains`/`exposes` 关系 | `plan-governance-cli graph validate --layer architecture <fixture-root>` | 通过并报告节点、关系、Schema 版本 | 节点类型、证据、关系端点或方向非法 | 已实现，架构 fixture 通过 |
| 跨层映射 | `mappings.yaml` 中三条 `realized_by`：配置刷新、模型生命周期、PDF workflow | 同上并加载 `functional/index.yaml` | 通过外部功能节点存在性校验，架构层拥有映射事实 | 功能 ID 悬空、映射放入功能层或重复维护业务描述 | 已实现，架构 fixture 通过 |
| 架构关系反例 | 悬空端点、自环、重复关系、缺证据、非法节点类型 | 同上，分别执行正反例 fixture | 每个反例只报对应错误，不污染其他结果 | 反例通过、错误不稳定或静默忽略 | 已实现，8 项架构测试通过 |
| 配置刷新轻量路径 | `graph_scope: feature.config-refresh`、`change_kind: behavior_change` | `graph impact --from feature.config-refresh --layer functional ...` | 先输出功能影响，不自动遍历全部架构节点 | 无风险信号却强制下钻或遗漏功能影响 | 复用阶段 0 基线，待新入口 |
| API 契约升级路径 | `graph_scope: feature.model-lifecycle`、`change_kind: api_contract_change` | 同上并启用架构层映射 | 沿 `realized_by`、`exposes` 输出 API、消费者和契约证据 | 未说明升级原因或把全部代码判为必须修改 | 复用阶段 0 基线，待新入口 |
| 外部 workflow 跨边界路径 | `graph_scope: feature.pdf-workflow-reuse`、`change_kind: behavior_change` | 同上并按需查询 `crosses` | 输出外部模型服务边界及必要评估动作 | 猜测不存在的安全边界或无条件查询 GitNexus | 复用阶段 0 基线，待新入口 |

阶段 1 的通用校验 Step 0 已具备可执行命令、输入 fixture、预期输出和失败判定；ModelPad 正式图谱和三类新三层场景是阶段 1 进入实施后的完成条件，不再阻塞本次准入。

#### 阶段 1 实施范围候选

只读检查显示现有 `scripts/graph_governance.mjs` 将功能层文件路径、节点类型、关系集合和传播规则写在同一套逻辑中。阶段 1 实施时应增加架构层加载分支，不得静默改变既有功能图谱 v1 的校验和影响结果：

| 位置 | 候选变化 | 明确不做 |
|---|---|---|
| `scripts/graph_governance.mjs` | 增加 `architecture` layer 解析、`index.yaml` 加载、架构节点/关系校验和架构层维护的跨层映射端点校验 | 不删除或改写功能层 v1 的默认路径、关系传播和 GitNexus 行为 |
| `bin/plan-governance-cli.mjs` | 保持现有转发方式，补充 `graph validate --layer architecture` 的帮助和参数约束 | 不让 CLI 自动写入 YAML、计划或代码 |
| `tests/architecture_graph_cli.test.mjs` | 覆盖合法架构图、悬空映射、自环、重复关系、非法类型、缺失证据和 index 加载 | 不把 ModelPad 真实图谱作为唯一测试样本 |
| `tests/fixtures/architecture-graph/` | 增加正例、反例和跨层映射 fixture | 不修改现有 `tests/fixtures/functional-graph/` 契约 |
| ModelPad `docs/graph/architecture/` | 已创建五组边界和映射 YAML，并通过真实仓库证据校验 | 不迁移、不删除既有功能图谱文件，不修改 Swift 代码 |

阶段 1 只交付架构层校验和最小映射完整性验证；不实现跨层 `graph impact`、行动分级、测试映射、新鲜度候选或 GitNexus 查询。上述能力分别留在阶段 3、阶段 2 或其后续准入中，避免把架构 Schema 验证与计划前置分析一次性耦合。

#### 阶段 1 当前实施证据

- `graph validate --layer architecture` 已支持架构 `index.yaml`、领域文件汇总和 `functional/index.yaml` 外部节点 ID 加载。
- 已新增 `tests/fixtures/architecture-graph/`，覆盖五组边界的架构节点、架构关系和三条 `realized_by` 映射。
- 已新增 8 项架构层测试，覆盖合法图谱、跨层映射、悬空关系、错误映射方向、非法节点类型、自环、重复关系、缺失证据，以及功能层默认路径回归。
- 根仓库全量测试当前为 23/23 通过；通用 CLI、测试和 fixture 已完成，ModelPad 只新增架构图谱 YAML，未修改 Swift 文件或既有功能图谱。
- ModelPad 已创建 `docs/graph/architecture/index.yaml`、`modelpad-boundaries.yaml` 和 `mappings.yaml`；架构层校验通过（6 个节点、8 条关系、0 个 GitNexus 引用）。
- ModelPad 既有功能层校验仍通过（20 个节点、23 条关系、9 个 GitNexus 引用），三个现有场景脚本均通过；当前未修改 Swift 代码和既有 `functional.yaml`。

#### 阶段 1 完成条件

- 架构层 Schema、索引加载、节点/关系/证据校验和 `realized_by` 外部功能节点校验通过独立正反例测试。
- ModelPad 创建最小架构图谱，覆盖已确认的五组边界；架构层维护跨层映射，功能层不新增架构引用。
- ModelPad 的配置刷新、模型生命周期、外部 PDF workflow 三个场景均能通过新入口验证，且新三层结果与阶段 0 旧图谱基线的差异可解释。
- 检查功能层、架构层和现有代码/测试之间没有重复维护同一 API、模块或业务事实。
- 阶段 1 失败/回滚边界、输出位置、旧功能图谱保留策略和实施证据完整。
- `plan-governance-cli check .`、全量测试和阶段 1 独立准入复核通过后，阶段 1 才能标记完成；阶段 2 已另行完成独立准入。

#### 阶段 1 失败与回滚边界

- 校验命令不能区分功能层节点、架构层节点和跨层映射时，停止阶段 1，不迁移既有 YAML。
- 映射存在悬空、重复或多种合理归属时，输出候选并交给 LLM；LLM 无法唯一确认时才请求用户，不自动写入。
- 架构节点无法用仓库证据说明边界职责时，不创建节点；保留盘点候选并标记缺失证据。
- 阶段 1 任何失败都只删除尚未纳入 ModelPad 的新增 fixture 或候选文件，不修改现有功能图谱、代码、GitNexus 索引或计划历史。

### 阶段 0 完成记录

### 阶段 0 范围

阶段 0 只冻结设计边界和可验证契约，不修改代码或 ModelPad 现有图谱：

1. 盘点现有功能图谱节点，判断哪些属于功能层、架构层或代码映射；五组最小架构边界已由用户确认，当前继续冻结其字段和关系形式。
2. 已确认 API 技术契约唯一归架构层；功能层只保留用户视角的对外能力和跨层关联。
3. 设计最小架构节点矩阵，限制在系统、模块、组件、服务、接口和数据边界；ModelPad 的五组最小架构边界已完成确认。
4. 已确认功能层核心关系为 `contains`、`depends_on`、`orchestrates`、`consumes`，并将 `implements`、`exposes` 迁入架构层或跨层关系；五个跨层关系的方向、用途和按 `change_kind` 升级的默认路径已冻结，避免复制 GitNexus 调用关系。
5. 设计 GitNexus UID 可选化和代码锚点重绑定边界。
6. 定义 LLM 候选报告、自动写入的证据门槛和新 Schema 校验闭环；记录切换、失败和回滚边界；通过独立复核后，阶段 1 才能进入设计或实施。

### 阶段 0 准入摘要

| 字段 | 内容 |
|---|---|
| 准入状态 | 已完成 |
| Step 0 | [阶段 0 Step 0 证据](#阶段-0-step-0-证据) |
| 样本矩阵 | [阶段 0 样本矩阵](#阶段-0-样本矩阵) |
| 验证方式 | [阶段 0 验证方式](#阶段-0-验证方式) |
| 失败/回滚边界 | 阶段 0 只更新本计划和 PLAN_MAP；边界未收敛则不修改现有 YAML 或 CLI |
| 当前阻塞项 | 无；阶段 1 另行执行自己的准入流程 |
| 最新独立准入复核 | [2026-07-24 阶段 0 通过](#最新独立准入复核) |

### 阶段 0 Step 0 证据

- 已完成的功能图谱试点基线：ModelPad `functional.yaml` 包含 20 个节点、23 条关系和 9 个 GitNexus 引用。
- 已完成 ModelPad 只读架构盘点：候选压缩为本地 HTTP API、配置持久化、模型进程管理、App 状态编排和外部模型服务五组边界；候选证据见 [阶段 0 只读盘点](../modelpad-architecture-stage0-inventory-2026-07-24.md)。
- 已完成三次现有 v1 影响查询基线：配置刷新为 5 个直接/1 个间接，模型生命周期为 7 个直接/2 个间接，PDF workflow 复用为 3 个直接/1 个间接；旧结果会混入 API、代码和测试节点，作为新三层拆分的对照证据。
- 已完成 ModelPad LLM 维护设计回放：API 变更和性能重构具备自动更新证据，缺少鉴权边界和 API 消费者语义的样本必须上升确认；回放证据见 [LLM 设计回放](../modelpad-architecture-stage0-llm-replay-2026-07-24.md)。
- `plan-governance-cli graph validate /Users/jafish/Documents/work/ModelPad` 已通过。
- ModelPad 三个真实场景 fixture 已通过：模型生命周期、配置刷新、外部 PDF workflow 复用。
- 当前功能图谱计划已明确“首期不构建完整架构图谱”；本计划记录该非目标后的后续演进，不把历史试点重新解释为三层架构已完成。

### 阶段 0 样本矩阵

| 样本/基线 | 输入或基线 | 可执行命令 | 预期结果 | 失败判定 | 输出位置 |
|---|---|---|---|---|---|
| 功能层现状 | ModelPad `docs/graph/functional.yaml` | `plan-governance-cli graph validate /Users/jafish/Documents/work/ModelPad` | 记录现有节点、关系和代码引用数量 | 图谱无法校验或数量无法复现 | 命令输出、本计划 Step 0 |
| 三层场景 | 模型生命周期、配置刷新、外部 PDF workflow | `scripts/validate_functional_graph_scenarios.sh /Users/jafish/Documents/work/ModelPad` | 三个场景均可定位功能入口和现有影响路径 | 任一场景失去可定位证据 | ModelPad 场景脚本输出 |
| 架构最小集合 | ModelPad 五组架构边界候选 | 阶段 0 只读盘点与 `rg` 反向引用检查 | 每个候选节点有唯一层级归属和仓库证据 | 节点重复维护或无法说明职责 | [只读盘点](../modelpad-architecture-stage0-inventory-2026-07-24.md) |
| 轻量前置路径 | 一般行为变更的功能 `graph_scope` | 功能层影响查询，不下钻架构层或 GitNexus | 输出功能/流程影响和行动分级，未触发升级 | 无风险信号仍强制遍历全部三层，或遗漏功能层影响 | 阶段 0 场景记录 |
| 风险升级路径 | API、数据、安全、共享架构、代码定位五类信号 | 按 `change_kind` 依次查询功能层、架构层和按需 GitNexus | 仅命中升级信号的层级被查询，输出升级原因和证据 | 无升级依据仍下钻，或有升级信号却未查询相应层级 | 阶段 0 场景记录 |
| UID 映射边界 | 当前 9 个 GitNexus 引用和文件 fallback | `gitnexus status`、`gitnexus context --uid <uid>`、图谱校验 | UID 作为可选精确引用，失配可由代码锚点产生候选 | UID 被当作唯一稳定事实或失配被静默忽略 | 命令输出、阶段 0 评审记录 |

### 阶段 0 验证方式

- 执行 ModelPad 图谱校验和三个场景脚本，固定现状基线。
- 使用 `rg -n 'functional-graph-governance|architecture-graph-governance|GitNexus|code_refs|graph_scope|架构图谱'` 检查计划、索引和试点文档反向引用。
- 检查功能层、架构层和代码层是否存在重复事实源，尤其是 API、模块和代码对象归属。
- 记录至少一个 UID 仍有效、一个 UID 失配或待解析、一个仅有稳定代码锚点的样本。
- 以 ModelPad 样本验证默认功能层查询与风险升级查询的边界，记录未下钻原因、升级原因和行动分级。
- 检查 LLM 候选报告是否包含规定的证据，并以一条可自动更新候选和一条必须上升确认候选验证门槛。
- 使用 `plan-governance-cli check .`；阶段 0 未通过前不修改实现或迁移现有 YAML。

### 阶段 0 完成条件

- 三层职责边界和非目标明确。
- API 的唯一事实归属已决定，或明确记录为当前阻塞项。
- 架构图谱最小节点集合和关系方向已冻结。
- GitNexus UID 已明确为可选映射，稳定代码锚点和失配/重绑定策略已冻结。
- 默认功能层查询、条件升级架构层/GitNexus 查询及其触发信号已由 ModelPad 样本验证。
- LLM 候选报告、自动写入证据门槛、上升确认边界和新 Schema 校验闭环已冻结。
- 新 Schema 的目录入口、CLI 输入路径和旧 v1 图谱退出计划前置门禁的切换条件已明确。
- 样本矩阵、验证方式、失败/回滚边界和维护成本评估完整。
- `PLAN_MAP.md` 已同步状态、当前阶段、依赖和证据链接。
- 阶段 1 最新独立完成复核明确通过；阶段 2 已另行完成自己的 Step 0 和独立准入复核。

## 未决问题

| 问题 | 推荐方案 | 是否阻塞阶段 0 | 状态 |
|---|---|---|---|
| API 的事实归属是功能层还是架构层？ | 架构层负责路由、协议、请求/响应和版本等接口契约；功能层只通过跨层关系引用用户视角的对外能力 | 否 | 已确认（2026-07-24） |
| 架构图谱是否单独使用 YAML 文件？ | 功能层与架构层使用独立目录和各自 `index.yaml`；各层可按领域拆分多个 YAML，避免固定为两份单文件 | 否 | 已确认（2026-07-24） |
| GitNexus UID 是否保留在架构图谱？ | 保留为可选精确索引；长期锚点使用文件路径、全限定符号名和符号类型，行号不作为主键 | 否 | 已确认（2026-07-24） |
| 是否自动执行 UID 重绑定？ | 只生成候选并交给 LLM/人工确认，不自动写回 | 否 | 已确认边界 |
| 性能优化是否需要独立的 `change_kind`？ | 先以 `internal_refactor` 表达，使用性能证据和专项测试区分；若真实样本显示行动路径不同，再版本化增加 `performance_change` | 否 | 已确认（2026-07-24） |
| 跨层关系采用哪些最小关系及方向？ | 使用 `realized_by`、`contains`、`exposes`、`crosses`、`anchors_to`，分别按功能→架构、架构→架构、架构→接口、架构→数据/信任边界、架构→代码连接；查询按 `change_kind` 保守展开 | 否 | 已确认（2026-07-24） |
| `realized_by` 等跨层映射由哪一层维护？ | 由架构层维护，放入架构层的映射文件；功能层只保留业务语义，不反向写入架构引用 | 否 | 已确认（2026-07-24） |

## 最新独立准入复核

| 字段 | 内容 |
|---|---|
| 日期 | 2026-07-24 |
| 阶段 | 阶段 2 |
| 结论 | 通过；达到待实施标准 |
| 证据 | 五类 Step 0 样本可复现；候选 CLI 覆盖唯一、多候选 `ask_user` 和无候选；UID 失配→稳定 fallback→候选 CLI 串联回放通过；代码影响 CLI 正常查询和错误查询均通过；ModelPad 真实回放返回 `CRITICAL`、34 个受影响符号（30 个直接、4 个间接）、1 个流程和 2 个模块；根仓库 32/32 测试、治理检查和严格准入检查通过；复核记录见下方阶段 2 记录 |
| 未满足条件 | 无；ModelPad 首批 `code_mappings` 属于后续实施，不影响本阶段准入 |
| 复核者 | Arendt 独立复核代理（基于当前仓库内容和可复现命令） |

## 独立复核记录

| 日期 | 类型 | 阶段 | 结论 | 证据 | 复核者 |
|---|---|---|---|---|---|
| 2026-07-24 | 阶段准入复核 | 阶段 0 | 不通过 | 只读盘点、图谱校验、三个场景脚本和三次影响查询均通过；但当前阻塞项仍未满足 | Codex 独立复核 |
| 2026-07-24 | 阶段准入复核 | 阶段 0 | 通过 | ModelPad 图谱校验、三个场景脚本、根仓库 15 项测试、治理检查、停滞检查和反向引用检查均通过；五组架构边界、五个跨层关系、轻量/升级路径和 LLM 证据门槛均已记录并确认 | Codex 独立复核 |
| 2026-07-24 | 阶段准入复核 | 阶段 1 | 通过 | 架构层索引/领域文件加载、跨层映射校验、8 项架构正反例测试、23 项全量测试、架构 fixture 校验和严格治理检查均通过；阶段 1 达到待实施标准 | Codex 独立复核 |
| 2026-07-24 | 阶段完成复核 | 阶段 1 | 通过 | ModelPad 架构 YAML、功能层回归、三个场景脚本、映射摘要、重复事实检查、23 项全量测试和严格治理检查均通过 | Codex 独立复核 |
| 2026-07-24 | 阶段准入复核 | 阶段 2 | 通过；达到待实施标准 | 五类 Step 0 样本、候选 CLI、UID 失配串联回放、代码影响 CLI 正常/失败查询、ModelPad 真实回放、32/32 测试、治理检查和严格准入检查均通过；未运行 `gitnexus analyze` | Arendt 独立复核代理 |

## 风险和回滚

风险：新增架构层后，三张图重复表达模块、API 或代码事实。

控制：阶段 0 先冻结唯一事实源和跨层关系；无法减少重复维护时停止架构层实施。

风险：旧功能图谱 v1 与新三层 Schema 并存，造成事实源混淆。

控制：新 Schema 启用时明确 CLI 输入路径和计划前置门禁仅指向新文件；旧文件只标注为背景，不提供兼容读取或迁移承诺。

切换条件：新目录 Schema 校验、最小架构样本、三类 ModelPad 场景和新 CLI 输入路径均通过后，计划前置门禁才切换到新图谱；阶段 0 期间旧图谱仅作为只读基线。

风险：架构图谱规模膨胀为另一份代码目录或函数清单。

控制：只允许系统、模块、组件、服务、接口、数据边界和代码范围等架构粒度，禁止枚举函数调用关系。

风险：UID 失配被自动重绑定到错误函数。

控制：重绑定只输出候选，必须有文件、符号和类型证据；无法唯一确定时上升确认。

回滚：阶段 0/1 只删除新增架构图谱计划或试点文件，不修改现有功能 YAML、Swift 代码、GitNexus 索引或计划状态。

## 关联计划

- 前置计划：[functional-graph-governance](functional-graph-governance.md)。
- ModelPad 试点计划：ModelPad 仓库的 `docs/plans/functional-graph-pilot.md`。
