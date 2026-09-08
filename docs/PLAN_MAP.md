# PLAN_MAP

## 治理范围

本仓库跟踪轻量 `plan-governance` 工作流及其 Codex 集成。影响 skill 工作流、模板、验证规则或文档模型的变更需要进入治理。

## 文档权责

- `docs/PLAN_MAP.md` 是状态、依赖、替代/合并/废弃关系、推荐顺序、阻塞项和证据链接的事实源。
- 专项计划记录本次行为差异、阶段、Step 0 与验收；现行契约优先引用已有 Schema/OpenAPI，必要时才按需建立 spec，详见[阶段 3 文档职责](plans/iterative-governance-reliability.md#阶段-3-行为契约)。
- 总路线图、优先级计划和索引只记录顺序、状态摘要和专项计划链接，不复制字段级方案、枚举、Step 0 细节或完成定义。
- 当专项计划的状态、字段方案、完成条件或验证结果变化时，必须同步 `docs/PLAN_MAP.md` 和所有引用该计划的路线图、优先级计划或索引。
- 验收治理文档时，必须用 `rg` 搜索同名计划、P 编号、状态名和关键字段，检查是否存在重复定义或漂移。
- 如果同一事实在多个文档中重复，保留一个事实源，其他文档改为链接引用。
- 启用治理后，已有草案、历史设计、归档计划和临时分析文档默认只作为背景材料，不再作为规范事实源；后续新规范默认进入 `docs/plans/*.md`、ADR、migration、正式 spec 或 `docs/PLAN_MAP.md`。
- 计划索引固定分为 `未完成`、`已完成`、`已废弃` 三张表；`已替代`、`已合并`等不再推进的终态归入 `已废弃` 表，但保留真实状态值。

## 计划索引

### 未完成

| 计划 | 状态 | 当前阶段 | 最后更新 | 依赖 | 证据 |
|---|---|---|---|---|---|
| [phase-local-review-dispatch](plans/phase-local-review-dispatch.md) | 设计中 | 阶段 2 | 2026-09-05 | phase-entry-gate-hardening, independent-acceptance-rules, plan-governance-operability-optimization | [阶段准入摘要](plans/phase-local-review-dispatch.md#阶段准入摘要) |
| [plan-governance-workflow-streamlining](plans/plan-governance-workflow-streamlining.md) | 实施中 | 阶段 1 | 2026-09-09 | iterative-governance-reliability | [阶段准入摘要](plans/plan-governance-workflow-streamlining.md#阶段准入摘要)；[原技术验收通过](reviews/plan-governance-workflow-streamlining-completion-review-20260906.md#第三轮通过)；[使用反馈调整、复核及同步完成](plans/plan-governance-workflow-streamlining.md#实际使用反馈与有界调整2026-09-07)；[用户反馈与剩余读取复查](plans/plan-governance-workflow-streamlining.md#使用验收与执行抽查2026-09-08)；[调试复核粒度源规则通过](plans/plan-governance-workflow-streamlining.md#调试复核粒度优化提案2026-09-08)；[单次复核实施与修复自验通过](plans/plan-governance-workflow-streamlining.md#单次复核结论与修复) |

### 已完成

| 计划 | 状态 | 当前阶段 | 最后更新 | 依赖 | 证据 |
|---|---|---|---|---|---|
| [iterative-governance-reliability](plans/iterative-governance-reliability.md) | 已完成 | 阶段 4 | 2026-09-06 | phase-entry-gate-hardening, plan-governance-operability-optimization, plan-governance-distribution-setup, phase-local-review-dispatch | [阶段准入摘要](plans/iterative-governance-reliability.md#阶段准入摘要)；[阶段 4 及全计划完成验收](reviews/iterative-governance-reliability-stage4-completion-review-20260906.md#第二轮通过) |
| [codex-skill-rollout](plans/codex-skill-rollout.md) | 已完成 | 阶段 2 | 2026-07-05 | - | [验证方式](plans/codex-skill-rollout.md#验证方式) |
| [multi-doc-sync-rules](plans/multi-doc-sync-rules.md) | 已完成 | 阶段 1 | 2026-07-05 | codex-skill-rollout | [验证方式](plans/multi-doc-sync-rules.md#验证方式) |
| [draft-history-source-switch](plans/draft-history-source-switch.md) | 已完成 | 阶段 1 | 2026-07-05 | multi-doc-sync-rules | [验证方式](plans/draft-history-source-switch.md#验证方式) |
| [independent-acceptance-rules](plans/independent-acceptance-rules.md) | 已完成 | 阶段 1 | 2026-07-05 | draft-history-source-switch | [验证方式](plans/independent-acceptance-rules.md#验证方式) |
| [plan-drift-check-enhancements](plans/plan-drift-check-enhancements.md) | 已完成 | 阶段 3 | 2026-07-05 | independent-acceptance-rules | [验证方式](plans/plan-drift-check-enhancements.md#验证方式) |
| [stale-plan-detection](plans/stale-plan-detection.md) | 已完成 | 阶段 2 | 2026-07-05 | plan-drift-check-enhancements | [验证方式](plans/stale-plan-detection.md#验证方式) |
| [agent-runtime-integration](plans/agent-runtime-integration.md) | 已完成 | 阶段 3 | 2026-07-06 | stale-plan-detection, plan-drift-check-enhancements, independent-acceptance-rules | [验证方式](plans/agent-runtime-integration.md#验证方式) |
| [phase-entry-gate-hardening](plans/phase-entry-gate-hardening.md) | 已完成 | 阶段 3 | 2026-07-13 | agent-runtime-integration, independent-acceptance-rules | [验证方式](plans/phase-entry-gate-hardening.md#验证方式) |
| [plan-governance-npm-cli](plans/plan-governance-npm-cli.md) | 已完成 | 阶段 2 | 2026-07-13 | phase-entry-gate-hardening | [阶段 2 完成证据](plans/plan-governance-npm-cli.md#阶段-2-完成证据) |
| [plan-governance-distribution-setup](plans/plan-governance-distribution-setup.md) | 已完成 | 阶段 3 | 2026-09-08 | plan-governance-npm-cli | [完成证据](plans/plan-governance-distribution-setup.md#完成证据) / [2026-08-28 发布维护](plans/plan-governance-distribution-setup.md#2026-08-28-发布维护) / [2026-08-30 测试维护](plans/plan-governance-distribution-setup.md#2026-08-30-测试维护) / [2026-08-30 发布流程维护](plans/plan-governance-distribution-setup.md#2026-08-30-发布流程维护) / [2026-08-30 0.3.4 发布维护](plans/plan-governance-distribution-setup.md#2026-08-30-034-发布维护) / [1.0.0 发布维护](plans/plan-governance-distribution-setup.md#2026-09-06-100-发布维护) / [1.0.1 发布维护](plans/plan-governance-distribution-setup.md#2026-09-06-101-发布维护) / [1.0.2 发布维护](plans/plan-governance-distribution-setup.md#2026-09-07-102-发布维护) / [1.0.3 发布与本地更新](plans/plan-governance-distribution-setup.md#2026-09-08-103-发布与本地更新) |
| [requirements-grilling-integration](plans/requirements-grilling-integration.md) | 已完成 | 阶段 2 | 2026-07-19 | phase-entry-gate-hardening, plan-governance-distribution-setup | [完成证据](plans/requirements-grilling-integration.md#完成证据) |
| [functional-graph-governance](plans/functional-graph-governance.md) | 已完成 | 阶段 3 | 2026-07-22 | requirements-grilling-integration, phase-entry-gate-hardening, agent-runtime-integration | [完成证据](plans/functional-graph-governance.md#完成证据) |
| [architecture-graph-governance](plans/architecture-graph-governance.md) | 已完成 | 阶段 3 | 2026-07-25 | functional-graph-governance | [当前阶段](plans/architecture-graph-governance.md#当前阶段) |
| [plan-governance-operability-optimization](plans/plan-governance-operability-optimization.md) | 已完成 | 阶段 3 | 2026-08-11 | plan-drift-check-enhancements, phase-entry-gate-hardening, agent-runtime-integration, architecture-graph-governance | [阶段 3 完成验收复核](reviews/plan-governance-stage3-completion-review-20260811.md)；[阶段 3 可操作性收口样本](fixtures/plan-governance-stage3-operability-cases.md)；[阶段 2 完成验收](plans/plan-governance-operability-optimization.md#阶段-2-完成验收)；[阶段 1 独立复核报告](reviews/plan-governance-stage1-independent-review-20260810.md) |

### 已废弃

| 计划 | 状态 | 当前阶段 | 最后更新 | 依赖 | 证据 |
|---|---|---|---|---|---|
| [autonomous-plan-execution](plans/autonomous-plan-execution.md) | 已废弃 | 阶段 3 | 2026-08-28 | - | [废弃记录](plans/autonomous-plan-execution.md#废弃记录)；历史：[阶段 3 完成验收复核报告](reviews/autonomous-plan-execution-stage3-completion-review-20260812.md)；[阶段 3 完成证据](plans/autonomous-plan-execution.md#阶段-3-完成证据)；[阶段 2 完成验收复核报告](reviews/autonomous-plan-execution-stage2-completion-review-20260811.md)；[阶段 1 完成证据](plans/autonomous-plan-execution.md#完成证据) |

允许状态：`候选`、`设计中`、`待实施`、`实施中`、`已完成`、`已替代`、`已合并`、`已废弃`。

## 推荐顺序

1. `plan-governance-workflow-streamlining`：当前主线，原技术成果与 1.0.0 发布/本地同步已完成，见[发布维护](plans/plan-governance-distribution-setup.md#2026-09-06-100-发布维护)。阶段 1 内的[workset 最近证据限量输出](plans/plan-governance-workflow-streamlining.md#workset-最近证据限量输出)已实现并通过适用自验，已[发布为 1.0.1](plans/plan-governance-distribution-setup.md#2026-09-06-101-发布维护)，[本地 CLI/skill 已同步 1.0.1](plans/plan-governance-distribution-setup.md#101-本地更新)；整体实际使用验收仍保留；下一步为[真实使用反馈调整](plans/plan-governance-workflow-streamlining.md#实际使用反馈与有界调整2026-09-07)，源规则独立复核及本机资源、两个项目入口同步均已完成，随后已[发布 1.0.2](plans/plan-governance-distribution-setup.md#2026-09-07-102-发布维护)并[更新本地 CLI](plans/plan-governance-distribution-setup.md#102-本地更新)，用户反馈和执行抽查见[当前验收结果](plans/plan-governance-workflow-streamlining.md#使用验收与执行抽查2026-09-08)，剩余重复读取问题由 AI 定向复查，[调试复核粒度及已有计划策略接入](plans/plan-governance-workflow-streamlining.md#本次实施进展)已完成源规则实施和独立复核，已[发布并本地更新 1.0.3](plans/plan-governance-distribution-setup.md#2026-09-08-103-发布与本地更新)，[两项目策略接入](plans/plan-governance-workflow-streamlining.md#本次实施进展)已完成可迁移部分，未满足原门禁者保留待接入，真实效果继续观察。内部顺序见[执行顺序](plans/plan-governance-workflow-streamlining.md#执行顺序)。 [单次复核规则及检查器](plans/plan-governance-workflow-streamlining.md#单次复核结论与修复)已完成一次独立检查和两项修复自验，本计划已采用新策略；等待用户验收，尚未安装或发布。
2. `phase-local-review-dispatch` 阶段 2：独立支线，按原计划补齐宿主回放；不作为上述主线的先决条件。涉及共享实现时按下方共享写入边界串行交接。

`iterative-governance-reliability` 及其余已完成计划作为交付基线引用，不重新排队实施；历史阶段和验证入口见已完成索引。

## 依赖关系

| 计划 | 依赖 | 原因 |
|---|---|---|
| codex-skill-rollout | - | - |
| multi-doc-sync-rules | codex-skill-rollout | 依赖已落地的 skill、初始化脚本和治理文档结构 |
| draft-history-source-switch | multi-doc-sync-rules | 依赖既有事实源和多文档同步规则 |
| independent-acceptance-rules | draft-history-source-switch | 依赖既有事实源切换和多文档同步规则 |
| plan-drift-check-enhancements | independent-acceptance-rules | 依赖既有多文档同步、草案事实源切换和独立验收规则 |
| stale-plan-detection | plan-drift-check-enhancements | 依赖已落地的 warning 输出语义、活跃计划影响范围解析和可选检查模式 |
| agent-runtime-integration | stale-plan-detection, plan-drift-check-enhancements, independent-acceptance-rules | 依赖已落地的 `PLAN_MAP.md` 元数据、drift/pre-commit/stale 检查、warning 语义和独立验收边界 |
| phase-entry-gate-hardening | agent-runtime-integration, independent-acceptance-rules | 依赖既有计划状态、阶段索引、独立验收规则、完成快照和 warning 检查能力，补齐阶段准入闭环 |
| plan-governance-npm-cli | phase-entry-gate-hardening | 依赖已冻结的阶段准入、严格检查、完成快照和独立验收边界，将检查器收敛为可安装 CLI |
| plan-governance-distribution-setup | plan-governance-npm-cli | 依赖已发布的 npm 全局入口，将版本化资源、skill 同步和后续 hook 接入收敛到同一分发包 |
| requirements-grilling-integration | phase-entry-gate-hardening, plan-governance-distribution-setup | 复用既有阶段准入状态机，并依赖已冻结的 npm 资源清单、模板分发和显式 skill 同步边界 |
| functional-graph-governance | requirements-grilling-integration, phase-entry-gate-hardening, agent-runtime-integration | 复用已确认需求探索、阶段准入和只读 runtime 边界，已完成通用 CLI、Schema、分发和 ModelPad 试点交接 |
| architecture-graph-governance | functional-graph-governance | 在已完成的功能图谱试点基础上，重新冻结功能层、架构层和代码层边界，并收缩 GitNexus 引用维护范围 |
| plan-governance-operability-optimization | plan-drift-check-enhancements, phase-entry-gate-hardening, agent-runtime-integration, architecture-graph-governance | 复用 drift/pre-commit、严格准入、完成快照、只读 hook 与图谱查询边界；基于真实项目评审补齐当前工作集、阶段关系、证据状态和治理文件覆盖的可操作性缺口 |
| phase-local-review-dispatch | phase-entry-gate-hardening, independent-acceptance-rules, plan-governance-operability-optimization | 复用阶段准入、独立复核、当前工作集和证据状态边界，补齐阶段内复核派发、恢复和高影响停止策略 |
| iterative-governance-reliability | phase-entry-gate-hardening, plan-governance-operability-optimization, plan-governance-distribution-setup, phase-local-review-dispatch | 复用现有准入、工作集和分发契约；与宿主调度计划保持范围和共享写入协调，不承接其阶段 2 回放或解除其阻塞 |
| plan-governance-workflow-streamlining | iterative-governance-reliability | 前置技术成果已提交且本次已获推进授权；自身准入后只实施[成果对照](plans/plan-governance-workflow-streamlining.md#与前置及相关计划的边界)中的剩余差距 |

## 阶段关系

阶段关系的表头、方向和关系类型由上游计划的阶段 0 技术收敛稿定义；本表是唯一关系事实源。已废弃计划不再参与当前阶段关系或实施排序。

| 来源计划 | 来源阶段 | 目标计划 | 目标阶段 | 关系类型 | 解除条件 | 证据 |
|---|---|---|---|---|---|---|
| phase-local-review-dispatch | 阶段 2 | iterative-governance-reliability | 阶段 0 | soft_context | 仅作真实失败样本和分工对照，不作为立项或只读设计的硬门禁 | [计划分工](plans/iterative-governance-reliability.md#与既有计划的边界) |
| iterative-governance-reliability | 阶段 4 | plan-governance-workflow-streamlining | 阶段 0 | hard_gate | 上游已提交技术成果、独立完成证据及本次推进授权可定位，核对最终工作树及差距；新阶段仍须自身准入，不追溯补写产品接受 | [前置边界](plans/plan-governance-workflow-streamlining.md#与前置及相关计划的边界)；[未决问题](plans/plan-governance-workflow-streamlining.md#未决问题) |
| phase-local-review-dispatch | 阶段 1 | plan-governance-workflow-streamlining | 阶段 0 | soft_context | 仅复用既有复核契约并协调共享规则，不等待宿主阶段 2 回放完成，也不解除其阻塞 | [相关计划边界](plans/plan-governance-workflow-streamlining.md#与前置及相关计划的边界) |

## 并行与共享写入约束

| 范围 | 允许并行 | 串行边界 | 依据 |
|---|---|---|---|
| `shared_write_risk` 关系 | 可提示冲突和写入所有权 | 不自动转换为硬门禁依赖；实际写入按单一写入者或串行队列执行 | 共享风险是并行约束，不是业务先后关系 |
| phase-local-review-dispatch / iterative-governance-reliability | 宿主回放仍由原计划负责 | 优化阶段 0—4 已独立验收完成；当前交付保留为后续对照基线，后续计划按自身授权与准入再单一写入；宿主回放规则及旧计划不改 | [范围与安全边界](plans/iterative-governance-reliability.md#与既有计划的边界) |
| plan-governance-workflow-streamlining / 既有活跃计划 | 已完成设计，阶段 1 实施 | 交接及自身准入已通过，按已列范围单一写入；宿主回放及旧完成记录不改 | [共享写入边界](plans/plan-governance-workflow-streamlining.md#与前置及相关计划的边界) |

## 替代、合并和废弃

| 计划 | 关系 | 目标 | 原因 |
|---|---|---|---|
| autonomous-plan-execution | 已废弃 | Codex `goal` | 原生 goal 已覆盖跨轮持续推进，移除 skill 内重复的自主连续执行能力 |

## 当前阻塞项

| 问题 | 推荐方案 | 影响范围 | 是否阻塞当前阶段 | 状态 |
|---|---|---|---|---|
| D02 快照目录不可读导致错误放行 | [第二轮独立确认修复](reviews/iterative-governance-reliability-stage4-completion-review-20260906.md#第二轮修复复核) | iterative-governance-reliability | 否 | 已解决 |
| D03 混合快照仍读取外部 symlink | [第二轮独立确认修复](reviews/iterative-governance-reliability-stage4-completion-review-20260906.md#第二轮修复复核) | iterative-governance-reliability | 否 | 已解决 |
| D04 混合旧快照普通文件不可读时异常退出 | [独立确认修复](reviews/iterative-governance-reliability-stage4-completion-review-20260906.md#d04-独立修复确认) | iterative-governance-reliability | 否 | 已解决 |
| 后续减负计划 B01 前置交接基线 | 已提交技术基线与本次推进授权已核对，不补写历史产品接受，见[未决问题](plans/plan-governance-workflow-streamlining.md#未决问题) | plan-governance-workflow-streamlining | 否 | 已解决 |
| 减负计划 B04 模板式结论误放行 | [第三轮独立确认修复](reviews/plan-governance-workflow-streamlining-completion-review-20260906.md#第三轮通过) | plan-governance-workflow-streamlining | 否 | 已解决 |
| 减负计划 B03 明确通过句号兼容 | [第二轮独立确认修复](reviews/plan-governance-workflow-streamlining-completion-review-20260906.md#第二轮b03-通过b04-未通过) | plan-governance-workflow-streamlining | 否 | 已解决 |
| 后续减负计划 B02 通用规则兼容与执行样本 | [独立设计和阶段 1 自身准入通过](reviews/plan-governance-workflow-streamlining-design-review-20260906.md) | plan-governance-workflow-streamlining | 否 | 已解决 |
| 优化计划阶段 1 真实文件系统基线和扩展反例 | [C01](plans/iterative-governance-reliability.md#未决问题) 已收敛；22 类实盘回放完成，本阶段独立准入通过 | iterative-governance-reliability | 否 | 已收敛 |
| 下一动作示例误读修复 | [D01](plans/iterative-governance-reliability.md#未决问题)：独立完成重审通过，阶段 1 关闭，失败历史保留 | iterative-governance-reliability | 否 | 已解决 |
| 自主连续执行能力已废弃；当前没有需要继续推进的该计划阶段 | 使用 Codex `goal` 管理跨轮持续工作；保留历史设计与验收记录供追溯 | autonomous-plan-execution | 否 | 已解决 |

## 完成证据

| 计划 | 阶段 | 证据 |
|---|---|---|
| plan-governance-distribution-setup | 1.0.1 发布维护（2026-09-06） | [1.0.1 官方发布已确认](plans/plan-governance-distribution-setup.md#2026-09-06-101-发布维护)：完整验证、版本/latest、包完整性与 registry 恢复通过；[本地 1.0.1 更新验证通过](plans/plan-governance-distribution-setup.md#101-本地更新) |
| plan-governance-distribution-setup | 发布维护（2026-09-06） | [1.0.0 发布与本地同步完成](plans/plan-governance-distribution-setup.md#2026-09-06-100-发布维护)：官方 latest/包校验值、全局 CLI、Codex/Claude 20 份资源及安装后验证通过；真实使用验收仍归减负计划 |
| codex-skill-rollout | 阶段 2 | skill 校验、仓库治理检查和临时目录初始化验证通过 |
| multi-doc-sync-rules | 阶段 1 | `python3 -m pytest` 通过，覆盖率 98.54%；反向引用搜索通过；治理检查通过 |
| draft-history-source-switch | 阶段 1 | 反向引用搜索通过；`python3 -m pytest` 通过，覆盖率 98.54%；`python3 scripts/check_plan_governance.py .` 输出 `计划治理检查通过。` |
| independent-acceptance-rules | 阶段 1 | `python3 -m pytest` 通过，覆盖率 98.75%；反向引用搜索通过；`python3 scripts/check_plan_governance.py .` 输出 `计划治理检查通过。` |
| plan-drift-check-enhancements | 阶段 1 | `python3 -m pytest` 通过，覆盖率 98.23%；反向引用搜索通过；`python3 scripts/check_plan_governance.py .` 输出 `计划治理检查通过。` |
| plan-drift-check-enhancements | 阶段 2 | `python3 -m pytest` 通过，覆盖率 97.07%；反向引用搜索通过；`python3 scripts/check_plan_governance.py .` 输出 `计划治理检查通过。` |
| plan-drift-check-enhancements | 阶段 3 | `python3 -m pytest` 通过，覆盖率 96.22%；`--drift` 和 `--pre-commit` 小样本验证通过；治理检查通过；反向引用搜索通过 |
| stale-plan-detection | 阶段 1 | `python3 -m pytest` 通过，覆盖率 96.29%；`--stale-days 10` 和默认阈值验证通过；治理检查通过；反向引用搜索通过 |
| stale-plan-detection | 阶段 2 | `python3 -m pytest` 通过，覆盖率 96.64%；旧五列表迁移辅助测试通过；治理检查和 `--stale-days 10` 通过；反向引用搜索通过 |
| agent-runtime-integration | 阶段 1 | `python3 -m pytest` 通过，覆盖率 92.95%；治理检查和 `--stale-days 10` 通过；反向引用搜索通过 |
| agent-runtime-integration | 阶段 2 | `python3 -m pytest` 通过，覆盖率 92.46%；`--attest` 和 `--check-attestations` 小样本验证通过；治理检查通过；反向引用搜索通过 |
| agent-runtime-integration | 阶段 3 | `python3 -m pytest` 通过，覆盖率 92.39%；测试 fixture 覆盖 `--drift` 和 `pre-write` 作用域匹配；治理检查通过；反向引用搜索通过 |
| phase-entry-gate-hardening | 阶段 0 | 六类阶段准入 fixture 已定义；`python3 -m pytest` 80 项通过、总覆盖率 92.39%；治理检查和 `--stale-days 10` 通过；阶段设计独立复核通过 |
| phase-entry-gate-hardening | 阶段 1 | skill、模板、生成器、代理规则和说明文档同步；`python3 -m pytest` 80 项通过、总覆盖率 92.39%；临时升级 hash 与 docs 保持不变；阶段准入独立复核通过 |
| phase-entry-gate-hardening | 阶段 2 | `--strict-readiness` 已实现；53 项检查器测试、87 项全量测试通过；总覆盖率 91.93%；源/安装检查器一致；默认、严格、停滞和基础治理检查通过；阶段独立验收通过 |
| phase-entry-gate-hardening | 阶段 3 | 阶段路线图和计划状态已完成；最终独立验收、全量测试、严格治理、停滞、drift/pre-commit、反向引用和事实源扫描通过；按最终验收顺序创建完成快照并执行 `--check-attestations` |
| plan-governance-npm-cli | 阶段 1 | npm 包、Node 启动器、参数透传、Python 87 项基线、npm 3 项测试和临时安装 smoke test 通过 |
| plan-governance-npm-cli | 阶段 2 | `plan-governance-cli@0.1.1` 已发布；全局安装和 npx 通过；MinerU、Motorcycle 已切换全局入口并删除本地检查器；项目原有治理基线已记录 |
| plan-governance-distribution-setup | 阶段 1 | 13 个 npm 资源、临时安装、npm 5 项测试、Python 87 项测试和严格治理通过 |
| plan-governance-distribution-setup | 阶段 2 | `plan-governance-cli@0.2.3` 已发布；统一 CLI 入口已同步到 README、代理规则和 init 模板；全局 setup/init/check/hook、npx、Codex/Claude skill 同步和二次 dry-run 通过 |
| plan-governance-distribution-setup | 阶段 3 | hook runtime 可分发和手动调用；无稳定目标 Schema，未自动写入 hook 配置；最终验收和事实源扫描通过 |
| plan-governance-distribution-setup | 发布维护 | `plan-governance-cli@0.3.0` 已发布并成为 `latest`；skill/README 已同步图谱 CLI 与 `plan impact`；37/37 npm 测试、严格治理、公共包 ModelPad 图谱校验/影响分析和 Codex setup 二次 dry-run 通过 |
| plan-governance-distribution-setup | 发布维护 | `plan-governance-cli@0.3.1` 已发布并成为 `latest`；41/41 npm 测试、14 项生产资源打包、全局 registry 安装、npx smoke test 和 Codex setup 二次 dry-run 通过 |
| plan-governance-distribution-setup | 发布维护（2026-08-28） | `plan-governance-cli@0.3.3` 已发布并成为 `latest`；14 项生产资源打包、npm registry 版本查询、Codex skill setup 二次 dry-run、Python 回归、定向 Node CLI 测试和严格治理检查通过；临时安装 smoke test 未形成通过证据 |
| plan-governance-distribution-setup | 发布维护（2026-08-30） | 修复临时 npm 安装测试的独立 cache、audit/fund 和超时边界，统一已移除命令断言；Tencent registry 下 `npm test` 39/39 通过，临时包安装及安装后 CLI/init/workset/setup 回归通过 |
| plan-governance-distribution-setup | 发布流程维护（2026-08-30） | 新增 `npm run release:npm` 统一执行测试、版本升级、官方 npm 发布和 registry 恢复；支持 `--dry-run`，脚本语法及 dry-run 验证通过；尚未执行版本升级或发布 |
| plan-governance-distribution-setup | 发布维护（2026-08-30） | `plan-governance-cli@0.3.4` 已发布并成为 `latest`；发布脚本运行 `npm test` 39/39 通过，官方 registry 查询返回 `version: 0.3.4`、`latest: 0.3.4`，发布后 registry 已恢复为 Tencent |
| requirements-grilling-integration | 阶段 1 | 需求探索规则、唯一计划模板、初始化器、受管代理规则和 README 已同步；27 项针对性 Python 测试、87 项全量测试/91.95% 覆盖率、npm 7 项、严格治理、打包清单和反向引用检查通过 |
| requirements-grilling-integration | 阶段 2 | `plan-governance-cli@0.2.4` 已发布并成为 latest；已安装 tarball 的 `init` 与临时 Codex `setup` 回归通过；dry-run、同步、冲突保护和探索/准入边界均已验证；npm 7 项、Python 87 项/91.95%、严格治理、13 个生产资源、反向引用和格式检查通过 |
| functional-graph-governance | 阶段 0-3 | `npm test` 15/15 通过；通用 `graph validate/impact`、npm 打包清单、正反例 fixture、ModelPad 图谱校验和三个场景 fixture 全部通过。 |
| architecture-graph-governance | 阶段 3 | `npm test` 37/37 通过；五个 ModelPad 真实 `plan impact` 样本、Step 0 失败契约、治理/严格治理、反向引用和 GitNexus 变更检测通过；未刷新 GitNexus 索引。 |
| plan-governance-operability-optimization | 阶段 1 | `workset` 文本/JSON、活跃/历史过滤、阻塞/未知动作、直接关系透传、结构错误、旧计划兼容、阶段状态与计划状态分离和无写入行为通过；npm 39/39、Python 97 passed、覆盖率 91.39%、打包安装 smoke test、严格治理、反向引用和第三轮独立复核通过；曾将当前 `0.3.0` tarball 安装并同步到本机，随后按用户要求恢复同步前状态。 |
| plan-governance-operability-optimization | 阶段 2 | 阶段关系七列表、共享写入九列表兼容校验、R1—R7、npm 39/39、Python 106 passed/90.66%、严格治理、停滞检查、反向引用、只读 hash 和独立阶段完成验收通过；阶段 3 不自动放行。 |
| plan-governance-operability-optimization | 阶段 3 | S1—S6 真实 drift/pre-commit、完成计划关闭窗口、attestation 生命周期、模板/旧计划兼容、覆盖率补强、Python 122 passed/91.36%、npm 39/39、严格治理、停滞、反向引用、只读 hash 和独立完成验收通过；未同步全局环境或其他项目。 |
| autonomous-plan-execution | 阶段 1 | `plan steps validate` 合法/未启用/结构错误、不适用分支、空表、默认/严格退出码、旧计划兼容、阶段状态与计划状态分离和无写入行为通过；npm 39/39、Python 97 passed、覆盖率 91.39%、打包安装 smoke test、严格治理、反向引用和第三轮独立复核通过；曾将当前 `0.3.0` tarball 安装并同步到本机，随后按用户要求恢复同步前状态。 |
| autonomous-plan-execution | 阶段 2 | 阶段 2 Step 0、N1—N8、`next` 冻结契约、执行约束、缺证据分支、退出码、hook/安装包/无写入边界、全量回归和独立完成验收通过；阶段 2 已完成，阶段 3 随后完成。 |
| autonomous-plan-execution | 阶段 3（历史） | 模板默认关闭与显式启用、skill/代理元数据/README 运行时说明、T1—T6、当前真实计划兼容、临时 setup、npm 打包、无写入、回滚对照、Python 126 passed/90.67%、npm 41/41、严格治理和独立完成验收通过；2026-08-28 起计划已废弃。 |
| iterative-governance-reliability | 阶段 1 | [独立完成重审通过](reviews/iterative-governance-reliability-stage1-completion-review-20260906.md#第二轮通过)：203 项 Python/93.22%、41 项 Node、22 类实盘基线及 D01 四类回归；阶段 2 仍设计中 |
| iterative-governance-reliability | 阶段 2 | [独立完成验收通过](reviews/iterative-governance-reliability-stage2-completion-review-20260906.md)：统一 verify，Python 203/93.22%、Node 98/98（含 57 新回归）；阶段 3 设计中 |
| iterative-governance-reliability | 阶段 3 | [独立完成验收通过](reviews/iterative-governance-reliability-stage3-completion-review-20260906.md)：Python 208/93.15%、Node 98/98；规则/模板分发、非受管字节保护和五场景走读验证；阶段 4 设计中 |
| iterative-governance-reliability | 阶段 4 及全计划 | [独立完成验收通过](reviews/iterative-governance-reliability-stage4-completion-review-20260906.md#第二轮通过)：Python 348/92.97%、Node 99/99；140 项绑定回归及真实临时迭代；D02—D04 已解决，其他计划阻塞保留 |
