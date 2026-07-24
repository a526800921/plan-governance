# ModelPad 阶段 0 LLM 维护设计回放

> 回放日期：2026-07-24
> 性质：只读设计验证，不执行 YAML 自动写回。

## 目的

用 ModelPad 已完成计划回放 LLM 在图谱维护中的两类结论：

- 证据一致时自动更新候选；
- 证据缺失或语义不唯一时请求确认。

回放不把历史实现结果反写为新 Schema，只验证证据门槛和后置校验是否可解释。

## 回放命令

```bash
rg -n 'StartModelRequest|envOverrides|POST /api/models/:id/start|不持久化|敏感字段|APIContractTests' \
  docs/plans/modelpad-api-start-env-overrides.md Sources/ModelPadCore/API \
  Sources/ModelPadCore/Process Tests/ModelPadCoreTests/APITests README.md

rg -n 'LogBuffer|removeFirst|环形缓冲|O\(1\)|性能|高输出|append|满缓冲' \
  docs/plans/modelpad-logbuffer-performance.md Sources/ModelPadCore/Logging \
  Sources/ModelPadCore/Process Tests/ModelPadCoreTests/LoggingTests

rg -n '鉴权|认证|权限|不做 API 鉴权|不新增.*鉴权|远程访问|局域网监听' \
  docs/plans README.md Sources App Tests

rg -n 'desc|ModelSummary|decodeIfPresent|ModelRow|145 个测试|API 对外' \
  docs/plans/modelpad-model-desc-field.md Sources App Tests
```

## 回放结果

| 样本 | 可定位事实 | LLM 结论 | 后置校验 | 结果 |
|---|---|---|---|---|
| 启动接口环境变量覆盖 | API 计划契约、`StartModelRequest`、`APIServer` 请求体解析、`envOverrides` 合并、11 个契约测试、不持久化/不泄露边界 | `auto_update`；属于 `api_contract_change`，升级本地 HTTP API 架构边界 | 新 Schema `validate`、影响查询、契约测试 | 证据充分，允许自动更新候选 |
| LogBuffer 环形缓冲 | 性能计划、`LogBuffer` O(1) 实现、`ModelProcessManager.captureOutput`、17 个专项测试和全量测试 | `auto_update`；属于 `internal_refactor`，保留性能证据，不改功能语义 | 新 Schema `validate`、性能/边界测试 | 证据充分，允许自动更新代码锚点候选 |
| 新增 API 鉴权但当前仓库无鉴权 | 多份计划明确“不做 API 鉴权”、只监听 `127.0.0.1`；没有鉴权实现或测试证据 | `ask_user`；不能创建“安全功能”或伪造信任边界 | 输出缺失边界证据，不执行自动写回 | 必须人工确认 |
| 新增 `desc` 字段 | `ModelConfig`、`ModelSummary`、UI、兼容解码和测试均有证据；但是否影响外部消费者取决于 API 契约意图 | `ask_user` 或补充 API 消费者证据；不能只依据字段存在推导全量传播 | `validate`、API 契约和兼容测试 | 语义边界暂不唯一 |

## 候选报告示例

```yaml
decision: auto_update
change_kind: api_contract_change
changes:
  - type: architecture_mapping
    node: architecture.local-http-api
    reason: "新增 POST /api/models/:id/start 请求体契约"
evidence:
  - ref: docs/plans/modelpad-api-start-env-overrides.md
    locator: "公共 API 契约 / 阶段 1 完成证据"
  - ref: Sources/ModelPadCore/API/APIServer.swift
    locator: "handleStart、StartModelRequest"
  - ref: Tests/ModelPadCoreTests/APITests/APIContractTests.swift
    locator: "请求体校验、不持久化、不泄露"
reason: "变更类型明确，架构边界唯一，证据无冲突"
post_checks:
  - validate
  - impact
```

人工兜底示例只需要改变 `decision: ask_user`，并明确写出缺失的信任边界或消费者契约证据；不得由 LLM 自动补造节点。

## 结论

- LLM 自动维护可以建立在“变更类型明确、节点/关系唯一、证据可定位、证据无冲突”四个条件上。
- 代码锚点变化的证据门槛低于业务关系变化；业务关系、节点拆分/合并和安全边界需要语义证据或人工确认。
- 后置 `validate` 和 `impact` 是自动写回后的固定检查；人工不是常规审批，只有 LLM 无法依据证据确认时才介入。
- 现有样本足以验证 LLM 维护策略的方向，但尚未实现新三层 Schema 的自动写回测试；阶段 0 仍不能标记完成。
