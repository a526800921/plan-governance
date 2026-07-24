# ModelPad 架构图谱阶段 2 GitNexus 回放

> 回放日期：2026-07-24
> 适用计划：[架构图谱治理与三层图谱衔接](plans/architecture-graph-governance.md)

## 只读范围

本次只检查 ModelPad 当前 GitNexus 索引状态和 UID 查询，不运行 `gitnexus analyze`，不修改 GitNexus 索引，不修改 ModelPad 架构 YAML。

## 回放结果

| 样本 | 命令 | 结果 |
|---|---|---|
| 索引新鲜度 | `gitnexus status` | 索引 commit 为 `d63eb71`，当前提交为 `0dde74d`，状态为 stale |
| 精确 UID 命中 | `gitnexus context -r modelpad --uid 'Function:Sources/ModelPadCore/API/APIServer.swift:APIHandler.handleStart#1'` | `status: found`，返回 `APIServer.swift`、`handleStart`、行范围和调用/访问关系 |
| UID 失配 | `gitnexus context -r modelpad --uid 'Function:Sources/ModelPadCore/API/APIServer.swift:APIHandler.handleStart#999'` | 返回 Symbol not found；应转为失配候选，不删除稳定代码锚点 |
| 无 UID 稳定锚点 | `test -f Sources/ModelPadCore/Process/ModelProcessManager.swift && rg -n 'class ModelProcessManager' Sources/ModelPadCore/Process/ModelProcessManager.swift` | 文件存在且唯一定位到 `ModelProcessManager`；可以保存为 `file + symbol + kind` 锚点 |

## 设计结论

- stale 只表示索引与当前提交不同，不直接等价于 UID 全部失效。
- UID 适合精确查询，不适合作为架构图谱的长期主键。
- 阶段 2 应优先保存文件路径、全限定符号名和符号类型；UID 只作为可选索引。
- `analyze` 不由 hook、CLI 或 YAML 校验自动触发；刷新索引后仍需重新执行命中/失配检查。
- LLM 能唯一确认时更新架构层映射；多候选、证据冲突或无法确认时才请求用户。
- 当前尚未验证多候选重绑定 fixture，因此阶段 2 仍保持设计中。
