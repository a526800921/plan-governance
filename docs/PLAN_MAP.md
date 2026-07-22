# PLAN_MAP

## 治理范围

本仓库跟踪轻量 `plan-governance` 工作流及其 Codex 集成。影响 skill 工作流、模板、验证规则或文档模型的变更需要进入治理。

## 文档权责

- `docs/PLAN_MAP.md` 是状态、依赖、替代/合并/废弃关系、推荐顺序、阻塞项和证据链接的事实源。
- `docs/plans/*.md` 是专项计划的实施细节事实源，记录字段方案、Schema、枚举、Step 0 证据、验证方式和完成条件。
- 总路线图、优先级计划和索引只记录顺序、状态摘要和专项计划链接，不复制字段级方案、枚举、Step 0 细节或完成定义。
- 当专项计划的状态、字段方案、完成条件或验证结果变化时，必须同步 `docs/PLAN_MAP.md` 和所有引用该计划的路线图、优先级计划或索引。
- 验收治理文档时，必须用 `rg` 搜索同名计划、P 编号、状态名和关键字段，检查是否存在重复定义或漂移。
- 如果同一事实在多个文档中重复，保留一个事实源，其他文档改为链接引用。
- 启用治理后，已有草案、历史设计、归档计划和临时分析文档默认只作为背景材料，不再作为规范事实源；后续新规范默认进入 `docs/plans/*.md`、ADR、migration、正式 spec 或 `docs/PLAN_MAP.md`。

## 计划索引

| 计划 | 状态 | 当前阶段 | 最后更新 | 依赖 | 证据 |
|---|---|---|---|---|---|
| [codex-skill-rollout](plans/codex-skill-rollout.md) | 已完成 | 阶段 2 | 2026-07-05 | - | [验证方式](plans/codex-skill-rollout.md#验证方式) |
| [multi-doc-sync-rules](plans/multi-doc-sync-rules.md) | 已完成 | 阶段 1 | 2026-07-05 | codex-skill-rollout | [验证方式](plans/multi-doc-sync-rules.md#验证方式) |
| [draft-history-source-switch](plans/draft-history-source-switch.md) | 已完成 | 阶段 1 | 2026-07-05 | multi-doc-sync-rules | [验证方式](plans/draft-history-source-switch.md#验证方式) |
| [independent-acceptance-rules](plans/independent-acceptance-rules.md) | 已完成 | 阶段 1 | 2026-07-05 | draft-history-source-switch | [验证方式](plans/independent-acceptance-rules.md#验证方式) |
| [plan-drift-check-enhancements](plans/plan-drift-check-enhancements.md) | 已完成 | 阶段 3 | 2026-07-05 | independent-acceptance-rules | [验证方式](plans/plan-drift-check-enhancements.md#验证方式) |
| [stale-plan-detection](plans/stale-plan-detection.md) | 已完成 | 阶段 2 | 2026-07-05 | plan-drift-check-enhancements | [验证方式](plans/stale-plan-detection.md#验证方式) |
| [agent-runtime-integration](plans/agent-runtime-integration.md) | 已完成 | 阶段 3 | 2026-07-06 | stale-plan-detection, plan-drift-check-enhancements, independent-acceptance-rules | [验证方式](plans/agent-runtime-integration.md#验证方式) |
| [phase-entry-gate-hardening](plans/phase-entry-gate-hardening.md) | 已完成 | 阶段 3 | 2026-07-13 | agent-runtime-integration, independent-acceptance-rules | [验证方式](plans/phase-entry-gate-hardening.md#验证方式) |
| [plan-governance-npm-cli](plans/plan-governance-npm-cli.md) | 已完成 | 阶段 2 | 2026-07-13 | phase-entry-gate-hardening | [阶段 2 完成证据](plans/plan-governance-npm-cli.md#阶段-2-完成证据) |
| [plan-governance-distribution-setup](plans/plan-governance-distribution-setup.md) | 已完成 | 阶段 3 | 2026-07-13 | plan-governance-npm-cli | [完成证据](plans/plan-governance-distribution-setup.md#完成证据) |
| [requirements-grilling-integration](plans/requirements-grilling-integration.md) | 已完成 | 阶段 2 | 2026-07-19 | phase-entry-gate-hardening, plan-governance-distribution-setup | [完成证据](plans/requirements-grilling-integration.md#完成证据) |
| [functional-graph-governance](plans/functional-graph-governance.md) | 已完成 | 阶段 0-3 全部完成 | 2026-07-22 | requirements-grilling-integration, phase-entry-gate-hardening, agent-runtime-integration | [完成证据](plans/functional-graph-governance.md#完成证据) |

允许状态：`候选`、`设计中`、`待实施`、`实施中`、`已完成`、`已替代`、`已合并`、`已废弃`。

## 推荐顺序

1. `codex-skill-rollout`
2. `multi-doc-sync-rules`
3. `draft-history-source-switch`
4. `independent-acceptance-rules`
5. `plan-drift-check-enhancements`
6. `stale-plan-detection`
7. `agent-runtime-integration`
8. `phase-entry-gate-hardening`
9. `plan-governance-npm-cli`
10. `plan-governance-distribution-setup`
11. `requirements-grilling-integration`
12. `functional-graph-governance` ✅（阶段 0-3：契约、CLI、分发和 ModelPad 试点全部完成）

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

## 替代、合并和废弃

| 计划 | 关系 | 目标 | 原因 |
|---|---|---|---|
| - | - | - | - |

## 当前阻塞项

| 问题 | 推荐方案 | 影响范围 | 是否阻塞当前阶段 | 状态 |
|---|---|---|---|---|
| - | - | - | 否 | 已延后 |

## 完成证据

| 计划 | 阶段 | 证据 |
|---|---|---|
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
| requirements-grilling-integration | 阶段 1 | 需求探索规则、唯一计划模板、初始化器、受管代理规则和 README 已同步；27 项针对性 Python 测试、87 项全量测试/91.95% 覆盖率、npm 7 项、严格治理、打包清单和反向引用检查通过 |
| requirements-grilling-integration | 阶段 2 | `plan-governance-cli@0.2.4` 已发布并成为 latest；已安装 tarball 的 `init` 与临时 Codex `setup` 回归通过；dry-run、同步、冲突保护和探索/准入边界均已验证；npm 7 项、Python 87 项/91.95%、严格治理、13 个生产资源、反向引用和格式检查通过 |
| functional-graph-governance | 阶段 0-3 | `npm test` 12/12 通过；`graph validate/impact`、npm 打包清单和 ModelPad 三个场景 fixture 全部通过。详见 [完成证据](plans/functional-graph-governance.md#完成证据)。 |
