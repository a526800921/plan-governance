# ModelPad 架构图谱阶段 1 验收记录

> 验收日期：2026-07-24
> 适用计划：[架构图谱治理与三层图谱衔接](plans/architecture-graph-governance.md)

## 验收范围

本次只验证 ModelPad 新增的架构层 YAML、功能→架构映射和既有功能层回归，不修改 Swift 代码，不迁移或删除既有 `docs/graph/functional.yaml`。

新增文件：

- `docs/graph/architecture/index.yaml`
- `docs/graph/architecture/modelpad-boundaries.yaml`
- `docs/graph/architecture/mappings.yaml`

## 可复现命令与结果

| 命令 | 结果 |
|---|---|
| `plan-governance-cli graph validate --layer architecture /Users/jafish/Documents/work/ModelPad` | 通过；架构层 6 个节点、8 条关系、0 个 GitNexus 引用 |
| `plan-governance-cli graph validate /Users/jafish/Documents/work/ModelPad` | 通过；旧功能层 20 个节点、23 条关系、9 个 GitNexus 引用 |
| `scripts/validate_functional_graph_scenarios.sh /Users/jafish/Documents/work/ModelPad` | 配置刷新、模型生命周期、外部 PDF workflow 复用全部通过 |
| `npm test`（计划治理仓库） | 23/23 通过 |
| `plan-governance-cli check . --strict-readiness` | 通过 |

## 三个功能入口的架构映射

| 功能入口 | 架构边界 | 映射证据 |
|---|---|---|
| `feature.config-refresh` | 配置持久化、App 状态编排 | `modelpad-config-refresh.md`、`ConfigStore.swift`、`AppViewModel.swift` |
| `feature.model-lifecycle` | 模型进程管理、本地 HTTP API | `ModelProcessManager.swift`、README 启动 API |
| `feature.pdf-workflow-reuse` | 外部模型服务 | `modelpad-workflow-compat.md`、README 模型端口约定 |

## 重复事实检查

- 新架构文件只声明 `architecture.modelpad.*` 节点；功能层没有新增架构节点或架构技术契约。
- 既有 `functional.yaml` 中的 `api.*`、`code.*`、`test.*` 节点仍存在，但它们属于旧 v1 背景基线，不被新架构 `index.yaml` 加载，也不作为新三层事实源。
- `mappings.yaml` 只保存 `realized_by` 关系和证据，不复制功能名称、API 路由或函数调用关系。
- 当前架构层不包含 GitNexus UID；GitNexus 衔接保留到阶段 2。

## 结论

阶段 1 的 ModelPad 最小架构图谱、功能→架构映射和既有功能层回归均已具备可复现证据。阶段 1 可申请独立完成验收；阶段 2 仍需单独建立 GitNexus 衔接的 Step 0 和准入条件。
