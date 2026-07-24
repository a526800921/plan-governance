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
| 多候选重绑定 | `rg -n -g 'APIServer.swift' -g 'mlx_lm_server_fork.py' 'class APIHandler' Sources/ModelPadCore/API/APIServer.swift App/Resources/Scripts/mlx_lm_server_fork.py` | 发现两个 `APIHandler`：Swift `APIServer.swift:89` 和 Python `mlx_lm_server_fork.py:986`；仅凭符号名无法唯一重绑定，结论应为 `ask_user` |
| 候选报告 CLI | `plan-governance-cli graph code candidates --symbol APIHandler --kind class --format json /Users/jafish/Documents/work/ModelPad` | 返回两个候选和 `resolution: ask_user`；限定 `--file Sources/ModelPadCore/API/APIServer.swift` 时返回唯一候选 |
| 代码级影响查询 | `plan-governance-cli graph code impact --repo modelpad --file Sources/ModelPadCore/API/APIServer.swift --symbol APIHandler --kind class --depth 2 --format json /Users/jafish/Documents/work/ModelPad` | GitNexus 返回 `CRITICAL`、34 个受影响符号（30 个直接、4 个间接）、1 个流程和 2 个模块；未触发 `analyze` |

## 设计结论

- stale 只表示索引与当前提交不同，不直接等价于 UID 全部失效。
- UID 适合精确查询，不适合作为架构图谱的长期主键。
- 阶段 2 应优先保存文件路径、全限定符号名和符号类型；UID 只作为可选索引。
- `analyze` 不由 hook、CLI 或 YAML 校验自动触发；刷新索引后仍需重新执行命中/失配检查。
- LLM 能唯一确认时更新架构层映射；多候选、证据冲突或无法确认时才请求用户。
- ModelPad 已提供真实多候选回放：同名 `APIHandler` 分属不同文件和语言；如果失配后的 fallback 缺少文件约束，LLM 必须输出 `ask_user`，不得自动写回。
- 候选报告 CLI 和代码级影响 CLI 已将重绑定与影响范围边界固化为可执行的只读输出；阶段 2 仍保持设计中，下一步是独立准入复核。
