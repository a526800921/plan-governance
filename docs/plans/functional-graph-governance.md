# 计划：功能图谱治理与影响分析 CLI

## 背景

现有 `plan-governance-cli` 的 `--drift` 与 `--pre-commit` 只能按计划中声明的文件或目录判断覆盖范围，不能回答一次功能变更会影响哪些业务能力、流程、API、外部 workflow 与代码对象。

GitNexus 已提供函数、调用链和依赖等下层代码图谱；本计划补充项目内、可版本管理的业务语义图谱，并让计划治理在实施前使用 CLI 查询影响范围。首个试点项目为 `ModelPad`。

## 目标

- 在 `plan-governance-cli` 中提供通用、只读的功能图谱校验与影响分析入口。
- 让 LLM 依据仓库证据自动维护项目内 YAML 图谱；仅在证据不足或业务语义存在取舍时上升给用户确认。
- 让已覆盖图谱节点的计划在实施前获得可复现的直接/间接影响范围，而不自动回写计划状态或正文。

## 非目标

- 不将功能图谱做成任一被治理项目的对外 HTTP API。
- 不在 YAML 中复制 GitNexus 的函数、调用链或代码依赖事实。
- 不在首期构建图形化浏览器、图数据库服务或任意项目的完整架构图谱。
- 不让 CLI 根据猜测改写 YAML、计划或代码。

## 需求探索

### 已确认事实

- `--drift` 与 `--pre-commit` 当前只基于 `影响模块或文件` 的路径匹配，不表达业务、功能或流程关系。
- GitNexus 是下层函数级代码图谱；`ModelPad` 尚未建立本地 GitNexus 索引。
- `ModelPad` 已有模型生命周期、本地 HTTP API、配置刷新和 `mineru-pdf-workflow` 复用服务等可复现事实，可作为首个试点。
- 用户确认图谱与项目同仓库、同版本管理，并将其作为计划治理的一部分。

### 暂定假设与验证方式

- 项目内 YAML 只记录业务语义节点及其对 GitNexus/API/文件的引用，避免重复定义代码事实；通过 `graph validate` 与 GitNexus 查询 fixture 验证。
- LLM 可在存在代码、API、测试、文档或 GitNexus 证据时自动更新 YAML；通过证据字段、校验器和反向 fixture 验证，证据不足时必须报告而非猜测。
- 默认两跳影响展开足以提供有用且不过度嘈杂的试点结果；通过 ModelPad 三个真实场景评估。

### 范围与非目标

- 范围：通用 YAML Schema、核心关系及传播策略、CLI 校验/影响分析、计划 `graph_scope` 前置分析，以及 ModelPad 试点交接。
- 非目标：自动改写计划、自动推进计划状态、替代独立验收，或创建通用图形化图谱平台。

### 候选方案与取舍

- 采用“项目内 YAML + 通用 CLI + GitNexus 外部引用”的分层方案。YAML 可审阅、可提交；CLI 不需要外部服务；GitNexus 继续保持代码事实源。
- 不采用仅靠 GitNexus 社区/流程推断业务语义的方案，因为业务、功能和外部流程的正式关系需要显式事实源。
- 不采用 LLM 只生成建议、由人手工维护 YAML 的方案，因为目标是 LLM 默认自动维护，人只处理无法证实的语义决策。

### 未决问题

无当前阶段阻塞项。未来项目的架构、事件和部署关系按版本增加扩展关系，不在首期预建。

### 用户确认的探索结论

- YAML 在计划设计、实施前和实施后读取；LLM 在实施前按确认计划更新图谱、实施后按实际改动对账修正。
- `graph validate` 与 `graph impact` 是 CLI 能力；CLI 只读，结果是计划治理前置分析参考，不自动回写计划。
- 已覆盖图谱节点的计划若校验、查询或代码映射失败，保持在设计边界；未覆盖节点可明确标记后继续。
- 影响结果区分直接与间接影响，默认两跳并展示传播路径。
- 计划以稳定的 `graph_scope` 节点 ID 作为影响分析入口。
- 2026-07-22 决策：阶段 0 冻结的契约是功能图谱的唯一事实源。工作区既有图谱 CLI 原型不改变契约；阶段 1 必须先按本计划修正其节点类型、证据字段、GitNexus 回退映射、环策略和影响传播方向，再作为实现候选验收。

## 不变量

- `docs/PLAN_MAP.md` 仍是计划状态、当前阶段、依赖和证据链接的事实源。
- 项目 YAML 是功能图谱语义事实源；GitNexus 是代码图谱事实源。
- LLM 自动维护只适用于可由证据确认的图谱文档，不授权其自动修改业务代码或以猜测覆盖既有事实。
- 当前阶段写细，后续阶段写粗。

## 影响模块或文件

- scripts/check_plan_governance.py
- bin/plan-governance-cli.mjs
- resources/skill/
- resources/manifest.json
- package.json
- tests/
- README.md
- docs/plans/functional-graph-governance.md
- docs/PLAN_MAP.md

## 公共契约变化

首期已实现的命令：

```bash
plan-governance-cli graph validate [root]
plan-governance-cli graph impact --from <graph-node-id> [--depth 2] [--format text|json] [root]
```

项目图谱在 `docs/graph/functional.yaml` 中声明 `schema_version`、稳定节点 ID、证据和关系。核心关系固定为 `contains`、`orchestrates`、`exposes`、`implements`、`consumes`、`depends_on`；每种关系的影响传播方向由 Schema/CLI 规则定义。扩展关系必须版本化新增，不能改变既有关系语义。

### 阶段 0 契约草案（唯一事实源）

首期 YAML 的最小文档结构如下；此处是阶段 1 Schema 与 fixture 的设计输入，当前不创建或分发 Schema 文件。

```yaml
schema_version: 1
nodes:
  - id: process.model-lifecycle
    type: process
    name: 模型服务生命周期
    evidence:
      - kind: document
        ref: docs/plans/modelpad-v1.md
        locator: '#模型服务'
    code_refs:
      - kind: gitnexus_uid
        ref: <GitNexus UID>
        fallback: <repo-relative-path-or-route>
relations:
  - type: orchestrates
    from: process.model-lifecycle
    to: function.model-start
    evidence:
      - kind: code
        ref: <repo-relative-path>
        locator: <symbol-or-line-anchor>
```

首期 `schema_version` 只允许整数 `1`；未来版本必须通过版本化契约新增，不能静默改变版本 1 的语义。`nodes[].id` 为项目内稳定、全小写且由 `.` 分隔、段内仅含小写字母数字和连字符的标识；重命名显示名称不得改变 ID。首期 `type` 枚举为 `business`、`function`、`process`、`api`、`external_workflow`。每个节点和关系都至少有一条可定位 `evidence`；证据的 `kind` 为 `document`、`code`、`test`、`api` 或 `gitnexus`，`ref` 指向版本管理的仓库内路径或可复现的 GitNexus 标识，`locator` 用于进一步定位。顶层 `project` 元数据可选；如果存在，`project.id` 和 `project.name` 必须同时为字符串。`code_refs` 不是代码事实副本，只保存到 GitNexus/仓库对象的外部引用；`gitnexus_uid` 引用必须同时给出仓库内回退定位。

关系的 `from` 与 `to` 必须引用已声明节点，禁止重复的 `(type, from, to)` 三元组和自环。首期允许有环的业务语义图，但影响查询必须按已访问节点去重并报告传播路径，不能无限展开。无证据、悬空节点、失配的 GitNexus UID 或回退定位均为校验失败；后两者可以在未索引的项目中标记为“待解析”，但不得被误报为已映射。

### 核心关系与影响传播

`from` 表示关系的语义主语。影响查询从发生变更的节点出发，沿下表 `传播方向` 计算受影响节点；每条命中路径保留关系类型和证据。

| 关系 | 语义 | 传播方向 | 示例 |
|---|---|---|---|
| `contains` | 容器包含组成节点 | `to → from` | 功能变更影响其所属流程 |
| `orchestrates` | 流程或功能编排被调用能力 | `to → from` | 被编排步骤变更影响编排流程 |
| `exposes` | 能力通过 API 暴露 | `from → to` | 能力变更影响公开 API |
| `implements` | 上层功能实现某个业务能力 | `from → to` | 实现功能变更影响业务能力 |
| `consumes` | 消费方使用外部 workflow 或 API | `to → from` | 外部 workflow 变更影响消费方 |
| `depends_on` | 依赖方依赖提供方 | `to → from` | 提供方变更影响依赖方 |

首跳命中标为“直接影响”，第二跳及以后标为“间接影响”；默认深度为 2，`--depth` 只能扩大或缩小层数，不能改变关系方向。CLI 输出必须包含入口节点、深度、每个受影响节点的最短传播路径、直接/间接分类、关系序列和每条关系的证据引用；JSON 输出还必须稳定包含这些字段，文本输出也必须展示关系证据。未建模入口或待解析映射不得产生推测性影响结论。

### LLM 自动维护与人工兜底

LLM 在以下时点读取图谱：计划设计时确认 `graph_scope`；实施前按已确认计划补齐有证据的语义关系；实施后按实际变更、测试和 GitNexus 结果对账。只有新增、删除或变更已建模业务、功能、流程、API、外部 workflow、关系或外部代码映射时，才更新 YAML；纯内部重构仍须执行影响查询，但没有语义变化时不改 YAML。

自动写入前必须能为每条变更提供至少一条上述 `evidence`，并保留既有稳定 ID。证据互相矛盾、无法判断关系方向或业务含义、需要合并或拆分节点、需要修改核心关系语义，或 GitNexus 映射失配时，LLM 只报告候选变更并请求用户确认。`graph validate` 和 `graph impact` 永远只读；它们不更新 YAML、计划状态、计划正文或代码。

### 计划前置分析契约

需要图谱保障的专项计划在其当前阶段的实施前置条件中声明：

```yaml
graph_scope:
  - process.model-lifecycle
graph_depth: 2 # 可省略，默认 2
```

计划不复制 CLI 输出。对于已声明的节点，`graph validate`、对应 `graph impact` 或必需的代码映射失败时，计划停留在设计边界；对于当前尚未覆盖的节点，计划必须显式说明“未覆盖”及理由，才可不以图谱结果作为门禁。

## 阶段路线图

| 阶段 | 目标 | 进入条件 | 验证方向 | 状态 |
|---|---|---|---|---|
| 阶段 0 | 冻结通用契约、试点边界与基线 | 用户已确认需求探索结论 | ModelPad 基线、契约草案和反向引用可复核 | 已完成 |
| 阶段 1 | 以阶段 0 契约修正既有原型，并实现 YAML Schema、证据规则与校验器 | 阶段 0 独立准入通过 | 正反例 YAML、循环/悬空/证据 fixture | 已完成 |
| 阶段 2 | 实现影响分析 CLI 与 GitNexus 引用解析 | 阶段 1 完成，传播策略已冻结 | 两跳路径、文本/JSON 输出、代码对象解析 fixture | 已完成 |
| 阶段 3 | 接入计划前置分析并完成 ModelPad 试点验收 | 阶段 2 完成，ModelPad 已建立代码图谱基线 | 三个真实场景、独立复核和分发验证 | 已完成 |

## 当前阶段

### 阶段 0-3 完成记录

### 范围

阶段 0 已固定通用图谱契约、LLM 自动维护边界、ModelPad 试点范围和可观察基线；阶段 1-3 已完成通用校验器、影响分析 CLI、分发和 ModelPad 试点验收。

### 阶段准入摘要

| 字段 | 内容 |
|---|---|
| 准入状态 | 已完成 |
| Step 0 | [阶段 0 Step 0 证据](#阶段-0-step-0-证据) |
| 样本矩阵 | [阶段 0 样本矩阵](#阶段-0-样本矩阵) |
| 验证方式 | [阶段 0 验证方式](#阶段-0-验证方式) |
| 失败/回滚边界 | 阶段 0 只更新计划文档；契约未收敛则不进入实现 |
| 当前阻塞项 | 无 |
| 最新独立准入复核 | [2026-07-22 阶段 3 通过](#独立复核记录) |

### 阶段 0 Step 0 证据

- Step 0 基线确认当前 CLI 只有路径级 `--drift` / `--pre-commit`，没有 `graph` 子命令或 YAML 图谱 Schema；该基线已由本计划实现闭环。
- 当前本仓库已完成 `requirements-grilling-integration`，可记录用户确认的需求探索结论，但不会把探索本身误作阶段准入。
- ModelPad 已迁移为含“最后更新”的六列表并建立图谱试点计划；历史已完成计划的 Step 0、验证和覆盖率证据已补齐，严格治理检查现已通过。

### 阶段 0 样本矩阵

| 样本/fixture | 输入或基线 | 可执行命令 | 预期结果 | 失败判定 | 输出位置 |
|---|---|---|---|---|---|
| 当前 CLI 基线 | 阶段 0 记录的路径级 CLI | `plan-governance-cli --help` | 基线已记录；当前帮助中出现已登记的 `graph` 子命令 | 命令契约未登记或与计划不一致 | 命令输出 |
| 路径级漂移基线 | 活跃计划的 `影响模块或文件` 语义 | `plan-governance-cli check . --drift` | 仅做路径覆盖判断 | 已能回答业务/流程影响却未记录新契约 | 命令输出 |
| ModelPad 治理基线 | 已迁移的六列表与历史完成计划 | `plan-governance-cli check /Users/jafish/Documents/work/ModelPad --strict-readiness` | 治理检查通过，不修改项目文件 | 静默通过、改写项目文件或仍报告已解决的历史缺口 | 命令输出 |
| 真实影响场景清单 | 模型生命周期、配置刷新、外部 PDF workflow 复用 | `rg -n 'start|reload|mineru-pdf-workflow' <ModelPad 文档与源码>` | 三个场景均有可引用事实 | 任一场景无法定位证据 | rg 输出 |
| 合法最小图谱 | 一个有证据的节点和关系 | 阶段 1 fixture：`graph validate <fixture-root>` | 接受最小版本 1 文档并保留证据 | 缺少必填字段仍通过 | `tests/fixtures/functional-graph/valid-minimal/` |
| 结构反例 | 重复 ID、悬空端点、自环、重复关系 | 阶段 1 fixture：`graph validate <fixture-root>` | 分别指出精确字段与失败原因 | 静默接受或笼统报错 | `tests/fixtures/functional-graph/invalid-structure/` |
| 证据与映射反例 | 无证据、失配 UID、缺少回退定位 | 阶段 1 fixture：`graph validate <fixture-root>` | 拒绝无证据；待解析映射与失配分开报告 | 将待解析当作已映射 | `tests/fixtures/functional-graph/invalid-evidence/` |
| 传播 fixture | 六种核心关系、分支与环 | 阶段 2 fixture：`graph impact --from <id> --depth 2 --format json <fixture-root>` | 输出最短路径、关系证据、直接/间接分类、去重节点 | 方向错误、缺少关系证据、重复节点或无限循环 | `tests/fixtures/functional-graph/impact/` |

### 实施步骤

1. 已将 YAML 节点、关系、证据、传播、计划前置与自动维护边界固定为本计划中的契约草案。
2. 已为正反例、传播和三类 ModelPad 场景定义 fixture 矩阵，不实现运行时命令。
3. 已定义 GitNexus 外部引用的稳定性、缺失和降级策略。
4. 阶段 0 通过后依次完成阶段 1-3，并在每阶段追加独立复核记录。

### 阶段 0 验证方式

```bash
plan-governance-cli check . --strict-readiness
plan-governance-cli check /Users/jafish/Documents/work/ModelPad
rg -n 'functional-graph-governance|graph_scope|graph validate|graph impact|自动维护' \
  docs README.md resources scripts tests
rg -n '草案为准|以草案为事实源|详见草案|draft is source|source of truth.*draft|以.*draft.*为准' \
  docs README.md resources scripts tests
```

### 完成条件

- Schema 的节点、核心关系、证据字段和影响传播边界已在本计划中唯一确定。
- ModelPad 试点范围、三组真实场景和旧治理基线均有可复核证据。
- LLM 自动维护与用户兜底的触发条件明确，且不与计划状态自动化混淆。
- 阶段 1 的正反例 fixture、验证命令、失败边界和回滚策略已实现并通过测试。
- 阶段 0-3 的独立复核记录均已追加，最新复核达到完成标准。

## 最新独立准入复核

| 字段 | 内容 |
|---|---|
| 日期 | 2026-07-22 |
| 阶段 | 阶段 3 |
| 结论 | 通过；阶段 0-3 全部达到完成标准 |
| 证据 | 阶段 0-2 专属图谱测试 8/8、根仓库全量测试、ModelPad `graph validate`、三个场景 fixture、GitNexus `context --uid` 和分发检查均通过 |
| 复核者 | 独立复核 |

## 独立复核记录

| 日期 | 类型 | 阶段 | 结论 | 证据 | 复核者 |
|---|---|---|---|---|---|
| 2026-07-22 | 阶段准入复核 | 阶段 0 | 不通过 | 文档契约、Step 0、fixture 矩阵、LLM 边界、依赖计划和 ModelPad 基线均已核对；工作区原型与冻结契约存在漂移。 | 独立复核 |
| 2026-07-22 | 用户裁决 | 阶段 0 | 契约为准 | 用户确认阶段 0 冻结契约为唯一事实源；既有原型收编为阶段 1 的待修正输入，不改写阶段 0 契约。 | 用户 |
| 2026-07-22 | 阶段准入复核 | 阶段 0 | 通过 | 契约、Step 0、ModelPad 基线和反向引用已复核；阶段 0 达到完成标准。 | Codex 独立复核 |
| 2026-07-22 | 阶段准入复核 | 阶段 1 | 通过 | `graph_governance.mjs`、正反例测试、节点类型/证据字段/回退映射校验已通过。 | Codex 独立复核 |
| 2026-07-22 | 阶段准入复核 | 阶段 2 | 通过 | 两跳传播、文本/JSON 输出、环去重和路径证据输出已通过测试。 | Codex 独立复核 |
| 2026-07-22 | 阶段验收 | 阶段 3 | 通过 | ModelPad 三个场景 fixture、GitNexus 索引、npm 包清单和全量治理检查已通过。 | Codex 独立复核 |
| 2026-07-22 | 阶段验收复核 | 阶段 3 | 不通过 | 通用 CLI 的 12 个 Node 测试和治理检查通过；但真实 ModelPad `graph validate` 对 9 个 GitNexus UID 报失配，底层 `gitnexus context --uid` 报 Binder 错误，不能确认代码映射已验收。 | 独立复核 |
| 2026-07-22 | 阶段 0-2 复核 | 阶段 0 | 通过 | 契约细节已与实现对齐：`project` 可选且存在时校验、版本 1 明确、ID 规则收紧；阶段 0 达到完成标准。 | 独立复核 |
| 2026-07-22 | 阶段 0-2 复核 | 阶段 1 | 通过 | `node --test tests/graph_cli.test.mjs` 8/8；正反例、project、证据、fallback、待解析和 UID 失配校验均通过。 | 独立复核 |
| 2026-07-22 | 阶段 0-2 复核 | 阶段 2 | 通过 | 六种关系、分支、环、两跳、直接/间接结果、关系级 evidence、文本/JSON 输出和分发清单均通过。 | 独立复核 |
| 2026-07-22 | 阶段 3 当前状态复核 | 阶段 3 | 不通过 | 阶段 0-2 已通过；ModelPad 真实 GitNexus UID 仍有 9 个失配，阶段 3 保持阻塞。 | 独立复核 |
| 2026-07-22 | 阶段 3 最终验收 | 阶段 3 | 通过 | 完整 `gitnexus analyze --force` 后索引为 1,866 nodes、4,140 edges；ModelPad `graph validate` 通过，三个场景 fixture 全部通过，影响分析输出关系级证据。 | 独立复核 |

## 未决问题

| 问题 | 推荐方案 | 是否阻塞当前阶段 | 状态 |
|---|---|---|---|
| 阶段 1 需使既有原型符合阶段 0 契约 | 已按冻结契约修正节点类型、证据字段、GitNexus 回退映射、环策略、`contains` 与 `orchestrates` 传播方向，并由 fixture 验证 | 否 | 已完成 |
| GitNexus 符号 ID 在重命名或重载变化后的稳定引用策略 | 已记录 UID、文件/路由回退和失配报告规则，并在 ModelPad 完整重建索引后验证 `context --uid` | 否 | 已完成 |
| 扩展关系的审批方式 | 只在真实项目需要时按 Schema 版本新增，并补充传播 fixture | 否 | 已决定 |

## 风险和回滚

- LLM 将推断写成事实：要求每条自动确认关系保留可定位证据；证据不足即升级给用户。
- 影响范围过宽：默认两跳，按关系类型定义传播方向，并在输出中分开直接/间接影响。
- YAML 与代码图谱漂移：在实施前和实施后均运行校验；失配阻止已覆盖节点进入实施。
- 试点约束反向绑定所有项目：ModelPad 专属节点只存在于 ModelPad YAML，通用 CLI 不硬编码项目语义。
- 回滚：移除新增 `graph` 命令与资源即可恢复现有路径级检查；项目 YAML 保留为历史文档，不自动影响代码。

## Step 0 证据

阶段 0 基线已通过 `plan-governance-cli --help`、路径级 `check --drift`、ModelPad 治理检查和三类真实场景 `rg` 命令固定；该基线结果已写入本计划的阶段 0 样本矩阵。

## 验证方式

```bash
npm test
npm pack --dry-run --json
plan-governance-cli graph validate /Users/jafish/Documents/work/ModelPad
plan-governance-cli graph impact --from feature.model-lifecycle --depth 2 --format json /Users/jafish/Documents/work/ModelPad
```

预期结果：15 个 Node.js 测试通过，分发清单包含图谱脚本和 YAML 依赖，ModelPad 图谱校验及 JSON 影响分析通过。

## 完成证据

- `npm test` 通过，15/15 测试通过，覆盖 CLI 转发、YAML 正反例、GitNexus 待解析/失配、两跳影响分析、关系级 evidence、JSON 输出、打包运行和 setup/init 回归。
- `npm pack --dry-run --json` 确认 `scripts/graph_governance.mjs` 和 `yaml` 依赖进入分发包。
- `graph validate` 已按冻结契约校验 `schema_version`、节点类型、证据 `ref`、`code_refs.fallback`、悬空关系、自环和重复关系。
- `graph impact` 已按六种关系的冻结传播方向输出最短路径、直接/间接结果和证据；环只做访问去重，不无限展开。
- ModelPad 完整 `gitnexus analyze --force` 后 `graph validate` 通过：20 个节点、23 条关系、9 个 GitNexus 引用；三个真实场景 fixture 全部通过。

## 测试覆盖率

覆盖率证据：2026-07-22 执行 `npm test`，15 个 Node.js 测试全部通过；阶段 0-2 专属图谱测试为 8/8，ModelPad 图谱校验与三个场景 fixture 全部通过。Node.js 内置测试未配置行覆盖率统计，本条以测试通过数、fixture 覆盖矩阵和分发 smoke test 作为覆盖证据。

## 关联 ADR、迁移、spec 或 issue

- 依赖计划：[requirements-grilling-integration](requirements-grilling-integration.md)。
- 依赖计划：[phase-entry-gate-hardening](phase-entry-gate-hardening.md)。
- 依赖计划：[agent-runtime-integration](agent-runtime-integration.md)。
- 外部试点计划：ModelPad 仓库的 `functional-graph-pilot`。

## 后续演进

阶段 0-3 的完成范围仍是功能图谱 YAML、通用 CLI、分发和 ModelPad 两层试点验收。后续三层结构、架构图谱以及 GitNexus 引用收缩由独立计划 [architecture-graph-governance](architecture-graph-governance.md) 承载：功能图谱保持业务语义边界，架构图谱承载系统/模块/组件/接口边界，GitNexus UID 收缩为架构层到代码层的少量可选映射。该后续计划未完成阶段 0 设计前，不改变本计划已验收的历史契约或 ModelPad 现有 YAML。
