# ModelPad 架构图谱阶段 0 只读盘点

> 盘点日期：2026-07-24
> 适用计划：[架构图谱治理与三层图谱衔接](plans/architecture-graph-governance.md)
> 状态：五组边界和最小跨层关系已由用户确认；字段和 Schema 仍未冻结为 ModelPad 正式图谱。

## 盘点范围

本次只读检查覆盖 ModelPad 的 README、现有功能图谱、计划、Swift 源码和测试。未修改 ModelPad 文件、未迁移 `functional.yaml`、未创建架构 YAML、未运行新的 GitNexus 索引。

主要命令：

```bash
rg --files Sources App Tests
rg -n 'URLRequest|URLSession|HTTP|API|endpoint|route|reload|config|model|PDF|mineru|auth|permission|database|SQLite|CoreData|UserDefaults|FileManager' \
  Sources App Tests docs/graph docs/plans README.md
```

## 功能层现状

现有功能图谱可作为功能层入口，但其中的 `api.*`、`code.*` 节点属于后续三层切换时的迁移候选，不代表新的功能层模型：

| 功能入口 | 当前证据 | 后续归属判断 |
|---|---|---|
| `feature.model-lifecycle` | README、`modelpad-v1`、API/进程测试 | 保留功能层；流程和 API 映射下沉 |
| `feature.config-refresh` | README、`modelpad-config-refresh`、配置/API/UI 测试 | 保留功能层；配置边界和接口映射下沉 |
| `feature.pdf-workflow-reuse` | README、`modelpad-workflow-compat`、PDF workflow 计划 | 保留功能层；外部服务消费边界单独映射 |

## 最小架构候选

以下候选按架构职责和维护边界合并，不按类或函数枚举：

| 候选架构边界 | 主要仓库证据 | 承载事实 | 非目标 |
|---|---|---|---|
| 本地 HTTP API 接口边界 | `Sources/ModelPadCore/API/APIServer.swift`、`APIDTOs.swift`、README OpenAPI 章节、`APIContractTests` | loopback 监听、路由、请求/响应、OpenAPI 契约、错误码 | 不拆成每个 endpoint 节点，不复制函数调用 |
| 配置持久化边界 | `Sources/ModelPadCore/Persistence/ConfigStore.swift`、`AppConfig`/`ModelConfig`、配置测试 | `config.json` 路径、JSON 读写、损坏备份、原子写入、配置数据边界 | 不把每个配置字段做成架构节点 |
| 模型进程管理边界 | `Sources/ModelPadCore/Process/ModelProcessManager.swift`、`TCPHealthChecker.swift`、进程测试 | 启停/重启、状态机、环境变量合并、健康检查、失败处理 | 不复制 GitNexus 调用链，不拆每个状态方法 |
| App 状态编排边界 | `App/Sources/AppViewModel.swift`、`AppDelegate.swift`、App 测试 | 配置刷新、选中状态、UI 状态、API 回调与核心对象装配 | 不把 SwiftUI View 逐个建模 |
| 外部模型服务边界 | README 模型端口/健康检查约定、`ModelConfig.port`、PDF workflow 兼容计划 | ModelPad 托管进程与本机端口之间的服务边界、外部 workflow 消费约定 | 不把每个 Python 服务脚本纳入架构图谱 |

暂不单独建立“安全功能”节点。当前可观察的是本地 loopback API 和模型进程环境/端口边界；只有出现真实鉴权、权限或外部数据交换需求时，才增加对应架构边界。

## 轻量与升级样本

这些样本用于验证查询是否按风险下钻，不是要求每次都执行三层查询。

| 样本 | 计划输入 | 默认路径 | 预期升级 | 失败判定 |
|---|---|---|---|---|
| 配置刷新行为保持不变 | `graph_scope: feature.config-refresh`、`change_kind: behavior_change` | 只查功能层，输出配置刷新流程和验收测试 | 无 API 契约或数据格式变化时不查架构/GitNexus | 强制遍历全部三层，或遗漏功能/流程影响 |
| 修改本地 API 请求/响应 | `graph_scope: feature.model-lifecycle`、`change_kind: api_contract_change` | 先查功能层 | 升级到本地 HTTP API、OpenAPI、消费者和契约测试；需要实现定位时再查 GitNexus | 未说明升级原因，或把所有模型功能无差别判为必须测试 |
| 共享进程管理边界重构 | `graph_scope: feature.model-lifecycle`、`change_kind: internal_refactor` | 先查功能层 | 若变更命中模型进程管理边界，再查架构层和按需 GitNexus；功能语义未变时不更新功能 YAML | 把内部重构自动判定为功能变化，或强制维护函数级 YAML |
| 配置格式迁移 | `graph_scope: feature.config-refresh`、`change_kind: data_migration` | 先查功能层 | 升级到配置持久化边界，输出读写方、迁移和回滚测试 | 没有数据边界证据却生成迁移结论 |
| 安全边界变更但当前无鉴权模型 | `graph_scope: feature.model-lifecycle`、`change_kind: security_change` | 先查功能层 | 报告缺少可定位的鉴权/权限边界，要求候选或人工确认，不创建泛化安全节点 | LLM 猜测存在权限模型，或静默当作普通行为变更 |

## 现有影响查询基线

2026-07-24 使用当前 v1 `functional.yaml` 执行三次只读影响查询。三次场景和图谱校验均通过，但现有结果仍将 API、代码对象和测试节点直接作为功能影响结果的一部分：

| 入口 | 直接影响 | 间接影响 | 观察 |
|---|---:|---:|---|
| `feature.config-refresh` | 5 | 1 | 同时出现 API、`AppViewModel`、`ConfigStore` 和测试节点 |
| `feature.model-lifecycle` | 7 | 2 | 同时出现 3 个 API、进程管理器、OpenAPI、代码处理器和测试 |
| `feature.pdf-workflow-reuse` | 3 | 1 | 同时出现外部 workflow、服务消费流程和 `/health` API |

这不是当前试点失败：它固定了旧两层模型的可复现基线，并说明新三层模型应把 API/代码节点移出功能层默认结果。目标不是减少影响证据，而是让功能层结果先回答业务影响，再按风险原因下钻到架构和代码证据。

## 变更类型传播矩阵（候选）

以下矩阵是阶段 0 的设计输入，需结合 ModelPad 样本和独立复核后冻结，不是当前 CLI 契约：

| `change_kind` | 默认入口 | 架构层升级条件 | GitNexus 升级条件 | 主要证据/动作 |
|---|---|---|---|---|
| `behavior_change` | 功能层 | 直接命中接口、数据或共享架构边界 | 需要定位实现或测试范围 | 功能/流程影响、验收测试 |
| `api_contract_change` | 功能层 | 必须升级到本地 HTTP API、OpenAPI 和消费者 | 需要定位 handler、DTO 或调用链 | 契约兼容、集成测试 |
| `internal_refactor` | 功能层只做影响核对，不更新功能语义 | 命中已建模共享架构边界 | 需要确认具体文件、类、函数或调用链 | 代码/单元测试；语义不变时不写功能 YAML |
| `data_migration` | 功能层 | 必须升级到配置持久化或其他真实数据边界 | 需要定位读写方和迁移实现 | 迁移、历史数据、回滚测试 |
| `security_change` | 功能层 | 必须升级到已有信任/权限边界；无证据则报告缺口 | 需要定位接口入口和鉴权实现 | 权限/安全测试；禁止猜测安全节点 |

矩阵的核心约束是：变更类型决定升级理由，不决定自动扩大到全图；没有对应边界证据时输出“缺少边界证据”，不生成推测性影响。

## 跨层关系最小候选

为保持架构图谱轻量，阶段 0 已确认只引入以下跨层/架构关系；它们是计划层冻结的最小契约，尚未写入 ModelPad 正式图谱：

| 关系候选 | 方向 | 语义 | 示例 | 不表达什么 |
|---|---|---|---|---|
| `realized_by` | 功能 → 架构 | 功能由哪些架构边界承载 | `feature.config-refresh` → 配置持久化边界 | 不表达函数调用 |
| `contains` | 架构 → 架构 | 系统/组件包含模块或接口边界 | App 状态编排 → 本地 API | 不枚举类层级 |
| `exposes` | 架构 → 接口 | 架构边界对外提供接口契约 | 本地 HTTP API → OpenAPI 契约 | 不放回功能层 |
| `crosses` | 架构 → 数据/信任边界 | 变更或调用跨越边界 | 本地 API → 模型服务端口 | 不推测不存在的安全边界 |
| `anchors_to` | 架构 → 代码 | 架构节点对应哪些代码范围 | 模型进程管理 → `ModelProcessManager` | 不复制 GitNexus 调用链 |

默认查询只沿 `realized_by` 找架构候选；`api_contract_change` 才沿 `exposes`，`data_migration/security_change` 才沿 `crosses`，需要具体实现时才沿 `anchors_to` 查询 GitNexus。共享架构节点的反向关联默认只标为“必须评估”。

## 现有计划与变更类型映射

| ModelPad 既有计划 | 当前可映射类型 | 观察 |
|---|---|---|
| `modelpad-config-refresh` | `behavior_change` | 有真实功能、流程、API 和测试证据，可作为默认轻量路径样本 |
| `modelpad-api-start-env-overrides` | `api_contract_change` | 有真实请求体、兼容性、敏感字段和契约测试证据，可作为架构/API 升级样本 |
| `modelpad-model-desc-field`、`modelpad-api-openapi-spec` | `api_contract_change` 或行为变化 | 需要按“是否改变消费者契约”区分，不能只看是否新增字段 |
| `modelpad-logbuffer-performance` | `internal_refactor` | 行为保持兼容，验收重点是热路径性能和边界测试；用性能证据表达非功能风险，不新增枚举 |
| 数据格式迁移 | 暂无真实 ModelPad 实施样本 | 可用配置 Schema 变更作为风险样本，但不能伪造已发生的数据迁移 |
| 安全/鉴权变更 | 暂无真实 ModelPad 实施样本 | 现有计划明确不做 API 鉴权；阶段 0 应验证“缺少安全边界证据”时如何上升确认 |

已确认不增加 `performance_change`。性能优化继续归入 `internal_refactor`，通过性能基线和专项测试表达非功能风险；只有未来行动路径明显不同，才重新提出版本化扩展。

## 阶段 0 结论

- ModelPad 的最小架构边界已确认控制在五组，不需要把现有 20 个功能图谱节点逐一转换为架构节点。
- 默认需求前置可以停留在功能层；API、数据、安全、共享边界和代码定位才触发升级。
- 当前 v1 影响查询会混入 API、代码和测试节点；这作为三层拆分前的基线，不作为新功能层输出契约。
- `api.*`、`code.*`、`test.*` 等现有功能图谱节点是迁移/映射候选，不能直接作为新三层 Schema 的正式架构节点。
- 五类 `change_kind` 样本已完成轻量/升级路径和 LLM 证据门槛回放；本文件只固定当前仓库事实和计划层候选边界，不代表 ModelPad 已完成正式图谱迁移。
- 现有计划显示性能风险可以由 `internal_refactor` 加专项证据表达，当前不扩充五类枚举。

## LLM 维护证据门槛样本（候选）

以下是基于既有 ModelPad 计划的回放样本，用于验证“LLM 默认维护、歧义才人工兜底”，尚未作为自动写回测试执行：

| 样本 | 证据组合 | 预期结论 |
|---|---|---|
| 启动接口环境变量覆盖 | `modelpad-api-start-env-overrides.md` 的 API 契约 + `APIServer.swift`/`APIDTOs.swift` 实现 + API/进程测试 + 敏感字段非范围 | `auto_update`：可更新 API 架构边界映射；更新后运行 Schema 校验和影响查询 |
| LogBuffer 环形缓冲优化 | 性能计划 + `LogBuffer.swift`/`ModelProcessManager.swift` 代码证据 + 专项边界测试 + 全量测试 | `auto_update`：按 `internal_refactor` 更新代码锚点/性能证据；不改功能语义 |
| 新增安全/鉴权能力但仓库无权限边界 | 只有需求文字，没有现有鉴权实现、契约或安全测试 | `ask_user`：报告缺少信任边界证据，不创建“安全功能”节点 |
| 模型描述字段 | 数据模型、API DTO、UI 计划和测试均有证据，但需判断是否改变外部消费者契约 | `ask_user` 或补充契约证据：不能只根据新增字段自动判断传播范围 |

候选报告最小结构：

```yaml
decision: auto_update # auto_update | ask_user
change_kind: api_contract_change
changes: []
evidence: []
reason: ""
post_checks:
  - validate
  - impact
```

自动更新的最低条件是：变更类型明确、受影响节点/关系唯一、证据可定位且没有互相矛盾。只有 LLM 无法据此作出唯一判断时才使用 `ask_user`；节点拆分/合并、关系方向不唯一或证据冲突属于典型升级场景，不代表所有自动更新都需要人工审批。
