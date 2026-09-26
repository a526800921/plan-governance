# 计划：计划文档日期目录与独立迁移技能

## 背景

`docs/plans/` 当前有 18 个计划文件平铺在根目录。用户希望按日期归档，并已明确现有计划也应按创建日期迁入，例如 `docs/plans/20260926/example.md`。

当前治理契约仍要求计划平铺：`docs/PLAN_MAP.md` 和 README 指向 `docs/plans/*.md`；检查器的孤立计划扫描使用 `plans_dir.glob("*.md")`；初始化器生成 `plans/<slug>.md` 并仅检查根目录是否有 Markdown 文件。只搬动文件会让检查器漏掉计划，因此目录迁移必须与发现逻辑、生成器、文档规则及引用更新一起完成。

已完成的[阶段 3 文档职责决策](../20260906/iterative-governance-reliability.md#阶段-3-行为契约)曾要求平铺且不迁移历史计划。本计划是在用户明确提出新目录规则及迁移存量计划后建立的后续变更；旧记录保留为当时决策的真实历史，不追溯改写。

## 目标

- 新计划使用 `docs/plans/YYYYMMDD/<slug>.md`，日期表示计划首次创建日期，格式固定为八位数字。
- 本仓库当前 18 个平铺计划按可核对的创建日期迁入对应日期目录。
- `PLAN_MAP.md` 继续作为状态索引和计划路径的事实源；检查器、workset、初始化器和文档链接均识别日期目录。
- 保留对外部项目旧式 `docs/plans/<slug>.md` 路径的兼容，避免升级工具时强制迁移使用方。
- 批量迁移现有计划由独立、按需调用的 migration skill 承担，不放进日常计划治理流程自动执行。

## 非目标

- 阶段 1 不搬动已有计划；本仓库的存量迁移在阶段 2 通过独立 migration skill 执行。
- 不改变计划内容、状态、阶段、证据结论或评审事实；迁移只改路径和因路径变化必须调整的链接/路径字段。
- 不自动迁移其他项目的历史计划，也不自动运行全局同步、发布或安装。

## 需求探索

### 已确认决定

- 用户要求采用日期目录，示例格式为 `docs/plans/20260926/xxx.md`。
- 用户明确要求现有计划也按创建日期迁移。
- 用户提出将迁移单独做成 skill；据此将主治理规则的日常日期路径支持与存量批量迁移流程分开。
- 新计划日期按首次创建时的本地日历日期生成；修改计划时不改变目录日期。
- 本仓库存量计划的创建日期优先采用 Git 跟踪到的首次添加日期。以后若遇到没有可追溯提交历史的文件，使用计划正文中明确记录的最早创建日期；仍无法确定时先停下列出文件，不以文件 mtime 或最后更新日猜测。
- 保留根目录旧式计划路径的读取兼容；迁移本仓库不等于给其他项目批量迁移授权。

### 迁移日期基线

以下日期来自 `git log --follow --diff-filter=A --format=%cs -- <path>` 的首次添加记录。相同日期的计划进入同一个 `YYYYMMDD` 目录。

| 创建日期 | 迁移计划 |
|---|---|
| 2026-06-27 | `codex-skill-rollout.md` |
| 2026-06-28 | `multi-doc-sync-rules.md` |
| 2026-06-29 | `draft-history-source-switch.md` |
| 2026-07-04 | `independent-acceptance-rules.md` |
| 2026-07-05 | `plan-drift-check-enhancements.md`、`stale-plan-detection.md` |
| 2026-07-06 | `agent-runtime-integration.md` |
| 2026-07-13 | `phase-entry-gate-hardening.md`、`plan-governance-distribution-setup.md`、`plan-governance-npm-cli.md` |
| 2026-07-19 | `requirements-grilling-integration.md` |
| 2026-07-22 | `architecture-graph-governance.md`、`functional-graph-governance.md` |
| 2026-08-10 | `autonomous-plan-execution.md`、`plan-governance-operability-optimization.md` |
| 2026-09-05 | `phase-local-review-dispatch.md` |
| 2026-09-06 | `iterative-governance-reliability.md`、`plan-governance-workflow-streamlining.md` |

## 不变量

- `docs/PLAN_MAP.md` 的链接指向每份计划的真实路径；每份计划在索引中只出现一次。
- 计划日期目录恰为 `YYYYMMDD` 一层；目录内计划仍以 `.md` 结尾。无效日期或不符合结构的路径不能静默漏检。
- 检查器同时识别受支持的旧式根目录计划和日期目录计划；workset 的计划路径与证据来源返回实际相对路径。
- 历史 attestation 文件不原地改写。迁移后逐个检查其计划路径和 PLAN_MAP hash；确需延续的证据通过 CLI 新建 superseding snapshot，并保留旧快照。
- 只有在日期目录发现、索引、引用和快照检查全部通过后，才移出对应的平铺文件；失败时恢复原路径和原引用。

## 影响模块或文件

- scripts/check_plan_governance.py
- scripts/init_plan_governance.py
- bin/plan-governance-cli.mjs
- package.json
- resources/manifest.json
- resources/skill/
- resources/migration-skill/
- README.md
- AGENTS.md
- tests/
- docs/PLAN_MAP.md
- docs/plans/
- docs/attestations/

## 公共契约变化

本计划是本仓库日期目录行为的当前设计事实源。获准实施后，统一规划规则为：

- 新建计划默认写入 `docs/plans/YYYYMMDD/<slug>.md`，其中日期是新建时本地日期，后续更新不重命名目录。
- `PLAN_MAP.md` 用相对 `docs/` 的路径链接该计划，例如 `plans/20260926/<slug>.md`。
- checker 与 workset 以索引中的路径读取计划，同时检查合法日期目录内的孤立文件；initializer 自动生成当天目录，并将新路径写入地图。
- 已有项目中的平铺计划继续可读，不因安装/升级工具自动搬迁。用户显式迁移时，以其可验证的首次创建日期分类。
- 单独提供 `plan-governance-migration` skill（名称暂定），由用户明确调用后执行存量迁移；它先核对计划路径、Git 创建日期、引用、路径碰撞和 attestation，再按迁移范围更新文件及引用，并验证结果。日常主 skill 不自动调用它。
- 本仓库迁移期间保持文件名及计划身份不变。历史正文、状态和证据不重写；更新地图、Markdown 链接、attestation 路径等路径指针并逐项验证。

## 阶段路线图

| 阶段 | 目标 | 进入条件 | 验证方向 | 状态 |
|---|---|---|---|---|
| 阶段 0 | 收敛新路径、创建日期来源、旧路径兼容及存量迁移规则 | 用户已确认日期目录格式及迁移现有计划 | 本计划/地图自验，迁移清单与影响范围可核对 | 已完成 |
| 阶段 1 | 更新主治理 skill、CLI、检查器和模板，使新日期路径成为默认并兼容旧路径，并分发独立迁移 skill | 阶段 0 完成；用户明确授权开始实现 | `npm run verify`、严格治理检查、新旧路径样本及一次同范围独立复核 | 已完成 |
| 阶段 2 | 用独立 migration skill 迁移本仓库 18 个存量计划及本计划，并更新引用 | 阶段 1 完成；迁移 skill 可调用；用户的现有计划迁移授权仍有效 | 迁移前后清单、链接检查、地图/workset、4 个 attestation 状态及回滚样本 | 已完成 |

## 当前阶段

### 范围

阶段 2 范围为使用独立 migration skill 搬迁本仓库开始时的 18 个计划，并将本计划一并放入其创建日期目录；更新计划索引、受影响链接和可建立后继关系的 attestation。阶段 1 已通过全量验证和独立复核，用户“开始”的授权涵盖本仓库存量迁移。

### 阶段准入摘要

| 字段 | 内容 |
|---|---|
| 准入状态 | 已完成 |
| 复核策略 | 风险分流 |
| Step 0 | [当前目录、工具和存量计划日期基线](#step-0-证据) |
| 样本矩阵 | [阶段 2 验收场景](#用户可观察验收) |
| 验证方式 | [验证方式](#验证方式) |
| 失败/回滚边界 | [风险和回滚](#风险和回滚) |
| 当前阻塞项 | 无 |
| 最新阶段复核 | [当前阶段自验记录](#最新阶段复核) |

### 实施步骤

1. 冻结日期语义、目录结构、旧路径兼容、迁移 skill 职责和存量迁移清单。
2. 更新检查器、workset、initializer、主治理规则及分发器；在临时项目验证新旧路径和双 skill 安装。
3. 阶段 1 完成全量验证并接受一次同范围独立复核；已完成。
4. 按独立 migration skill 的清单，将本仓库 18 个存量计划及本计划迁入对应日期目录，更新地图和相对链接；逐项核对 4 个 attestation 及其替代关系。
5. 阶段 2 完成链接、路径和快照检查，并对最终迁移差异做同范围独立复核；复核后自验。
6. 运行 `npm run verify`、`plan-governance-cli check . --strict-readiness` 和相关反向链接/日期目录检查，全部通过后完成阶段 2。

### Step 0 证据

- 当前 `docs/plans/` 根目录有 18 个 `.md` 计划文件。
- `scripts/check_plan_governance.py:917-925` 的孤立计划扫描只使用 `plans_dir.glob("*.md")`；日期子目录中的计划会被漏掉。
- `scripts/init_plan_governance.py:116-119` 写入 `plans/<slug>.md`；`scripts/init_plan_governance.py:221-228` 也只检查根目录下是否存在 Markdown 文件。
- 当前 `docs/PLAN_MAP.md`、README、skill 规划参考和初始化模板都以平铺路径为契约。
- migration skill 尚不存在；主 skill/CLI 的常规流程不应在无迁移请求时更改现有计划路径。
- `rg` 在 README、docs、resources/skill 中发现约 125 个计划路径链接；`docs/attestations/` 中有 4 个快照直接记录旧计划路径和同一份 PLAN_MAP hash。
- 上表为 18 个文件的 Git 首次添加日期清单，作为本仓库迁移的分类基线。
- 用户于 2026-09-26 明确回复“开始”，授权开始实现本计划所列日期目录契约。
- 阶段 0 本计划和地图结构检查已通过；检查报告的 4 条 workflow-streamlining 依赖告警与本范围无关。

### 阶段证据

- 实施前基线：`docs/plans/` 根目录 18 个计划；日期分组共 12 个创建日；4 个 attestation 需迁移后复核。
- 阶段 1 实施中：checker 支持平铺及日期目录路径、校验日期格式并扫描数字目录孤立计划；initializer 默认创建当天目录；主 skill 和 migration skill 已进入 npm manifest。
- 阶段 1 独立复核发现 `setup --destination` 与迁移 skill 目标目录重名时会相互覆盖；已增加目标目录重叠预检及负例，Node CLI 16 项通过，`node --check`、`git diff --check` 通过。
- 阶段 1 修复后首次 `npm run verify` 通过：严格治理检查、Python 678 项（93.05% 覆盖率）、Node 103 项；migration skill `quick_validate.py` 通过。该次严格检查包含与当时仍活跃的 workflow-streamlining 计划共享文件的 7 条范围告警，以及该计划既有 4 条依赖告警，均为 WARNING。
- 阶段 2 迁移基线包括原有 18 个按 Git 首次添加日期归组的计划和本计划（正文明确日期为 2026-09-26），共 19 个；4 个旧 attestation 字节保持不变。
- 迁移预检确认 19 个平铺源文件与 PLAN_MAP 直接计划链接一一对应，所有目标日期文件均不存在；18 个存量计划均有 Git 首次添加日期，本计划使用明确记录的创建日期。
- 迁移结果：19 个计划已按 13 个创建日期目录归档；更新 38 份 Markdown 文件，重算 374 个本地链接（其中 209 个指向迁移计划）；原平铺路径不再留有计划文件。4 个旧 attestation 原样保留，并由 4 个 CLI 新快照以 `supersedes` 关系承接。
- 迁移前检查在 `iterative-governance-reliability` 中发现 1 个既有不可达相对链接 `../../.github/workflows/ci.yml`；迁移时只重算其相对位置以保持原目标，不把它归因于本次迁移。
- 迁移后严格检查发现关系证据根目录和计划引用提取仍假设平铺结构；检查器现以 `docs/` 为关系证据基准并识别日期目录及带相对路径的计划链接，新增回归测试覆盖两种场景。
- 阶段 2 独立复核发现 3 处跨目录相对链接未增加一级父目录（`plan-governance-operability-optimization` 两处、`autonomous-plan-execution` 一处）；已改为 `../../reviews/...` 和 `../../fixtures/...`。排除 `node_modules` 后，全仓 Markdown 本地链接扫描核对 477 个链接；仅余历史 CI 失效链接及模板/负例样本的预期缺失目标。
- 首次快照复核发现旧 JSON 的 `plan_path` 不存在时会从 `supersedes` 图中跳过。检查器现保留该历史节点；被有效后继替代后报告 `superseded`，未被替代时仍报告 `needs_review`。新增迁移回归覆盖两种状态，并确认原快照字节不变。
- 后续代码审查发现三处遗漏：含绑定型快照的项目仍会跳过迁移后的旧快照、数字开头的平铺计划被误判为日期目录、已完成计划仍列在地图的未完成表。已调整混合快照预检与平铺路径判定，并将本计划移至已完成表。`--check-attestations --strict-readiness` 通过；地图变化后用 CLI 为 4 个计划各建立一份后继快照，最新快照为 `current`，此前快照为 `superseded`。本轮未运行测试套件；新快照只记录修复后的文件状态，不代表新增测试证据。

### 最近实施/验证记录

| 日期 | 类型 | 动作/结果 | 证据 | 状态 | 记录者 |
|---|---|---|---|---|---|
| 2026-09-26 | 需求落档 | 用户确认新建日期目录、存量计划迁移方向及将迁移流程独立为 skill；Git 首次添加日期已盘点 | 本计划 Step 0、`docs/PLAN_MAP.md` | 通过；阶段 1 未准入 | Codex |
| 2026-09-26 | 阶段 2 迁移 | 19 个计划迁入 13 个日期目录；38 份 Markdown 的 374 个本地链接已重算；4 个旧 attestation 未改写 | [迁移日期基线](#迁移日期基线)、本节迁移结果及最终验证记录 | 迁移后检查发现并修复两项日期路径解析问题 | Codex |
| 2026-09-26 | 最终验收 | 严格治理检查、全量 Python/Node 验证、skill 校验、链接核对及快照 supersedes 状态检查 | [完成证据](#阶段证据)、CLI 输出及旧/新 attestation | 通过；4 个旧快照 `superseded`，4 个新快照 `current` | Codex |
| 2026-09-26 | 审查后修复 | 补齐混合快照迁移兼容、数字开头的平铺路径兼容，并修正地图状态分组 | [阶段证据](#阶段证据)；严格治理与快照检查、4 条 CLI 后继快照 | 治理检查通过；本轮未运行测试套件 | Codex |

### 验证方式

阶段 1 运行 `npm run verify`（含 Python、Node 测试及 85% 覆盖率门槛）、skill `quick_validate.py`、npm 打包/临时安装和严格治理检查；迁移前后再按阶段 2 样本验证链接、索引、workset、孤立路径和 attestation。

阶段 1 验证至少覆盖：新建日期目录路径；旧式根目录计划继续被发现；日期目录内计划进入 check/workset 且只计一次；畸形目录给出明确诊断。阶段 2 验证迁移后地图链接和相对 Markdown 链接，4 个旧快照不变且各有一份有效的 CLI 后继快照。

### 用户可观察验收

| 场景 | 输入/前置 | 操作 | 可观察结果 | 验证证据 |
|---|---|---|---|---|
| 新建计划 | 当前日期为 D，计划 slug 可用 | 运行 init 创建计划 | 新文件位于 `docs/plans/D/<slug>.md`，地图链接到该路径 | 临时项目输出及文件列表 |
| 兼容旧路径 | 项目已有 `docs/plans/legacy.md` | 运行 check 和 workset | 旧计划仍被索引，不要求自动迁移 | CLI 输出及旧文件 hash |
| 按需迁移存量计划 | 本仓库 18 个文件和创建日期表 | 用户明确要求后使用独立 migration skill | 主 skill 不触发迁移；18 个历史计划及本计划位于正确日期目录，地图同步 | 本计划迁移记录、文件清单、check/workset 输出 |
| 路径和证据引用 | README、计划、reviews、fixtures、attestations 存在相互引用 | 迁移后进行定向链接扫描和快照核对 | 计划链接可达；旧快照未被覆盖；可信后继报告 `current`，原快照报告 `superseded` | 链接扫描输出和 attestation JSON/CLI 输出 |
| 畸形目录 | 测试项目含无效日期或额外层级的 `.md` 文件 | 运行 check | 输出能定位到具体路径的诊断，不静默忽略文件 | 负例 fixture 和 CLI 输出 |

### 测试覆盖率

阶段 1 的 Python 覆盖率为 93.05%；Python 678 项和 Node 103 项通过。阶段 2 `npm run verify` 通过：Python 682 项、93.05% 覆盖率，Node 103 项；skill 校验及迁移定向检查也通过。

### 完成条件

- 阶段 0 的需求、创建日期来源、旧路径兼容和 18 个存量计划的迁移清单已记录。
- 阶段 1 已完成；18 个存量计划及本计划均位于真实创建日期目录，索引和链接检查通过；4 个旧 attestation 原样保留，4 个 CLI 后继快照均为 `current`，原快照均为 `superseded`。
- 阶段 2 同范围独立复核及其后自验完成；完整 `npm run verify`、严格治理检查和 `plan-governance-cli check .` 通过。
- `docs/PLAN_MAP.md` 状态、阶段、证据与阻塞同步；`plan-governance-cli check .` 通过。

## 最新阶段复核

| 字段 | 内容 |
|---|---|
| 日期 | 2026-09-26 |
| 阶段 | 阶段 2 |
| 方式 | 自验 |
| 风险 | 高影响 |
| 风险依据 | 迁移了 19 个现有计划并调整跨文档路径；阶段 2 已进行同范围独立复核，发现的问题经修复后重新自验。 |
| 结论 | 通过：独立复核发现的 3 条相对链接已修复；链接扫描、完整验证和严格快照检查通过；4 个旧快照保留并由 current 后继快照替代。 |
| 证据 | [阶段证据](#阶段证据)中的迁移统计、独立复核和最终验证记录；[迁移日期基线](#迁移日期基线) |
| 复核者 | Codex |

## 阶段复核记录

| 日期 | 类型 | 阶段 | 方式 | 风险 | 结论 | 证据 | 复核者 |
|---|---|---|---|---|---|---|---|
| 2026-09-26 | 普通自验 | 阶段 0 | 自验 | 低风险 | 通过：阶段 0 需求、日期基线、迁移 skill 边界和验收范围已记录；本计划无结构警告 | `plan-governance-cli check .` 通过；全仓保留 4 条 workflow-streamlining 既有依赖警告；[Step 0 证据](#step-0-证据) | Codex |
| 2026-09-26 | 阶段准入自验 | 阶段 1 | 自验 | 低风险 | 通过：用户已授权阶段 1/2 实施，Step 0 基线和阶段验收范围明确；实现尚在进行 | 用户“开始”的明确授权；[Step 0 证据](#step-0-证据) | Codex |
| 2026-09-26 | 单次独立复核 | 阶段 1 | 独立 | 高影响 | 未通过：自定义 destination 与迁移 skill 目标目录重合时会覆盖主治理 skill | [独立复核发现](#阶段证据) | date_directory_phase1_review（推理强度 medium） |
| 2026-09-26 | 修复自验 | 阶段 1 | 自验 | 高影响 | 通过：setup 在写入前拒绝重叠目标目录，完整验证通过 | `npm run verify`：Python 678 项（93.05% 覆盖率）、Node 103 项；[阶段证据](#阶段证据) | Codex |
| 2026-09-26 | 阶段准入自验 | 阶段 2 | 自验 | 低风险 | 通过：阶段 1 验收通过，19 项迁移清单和日期来源明确；迁移后将独立复核 | [阶段证据](#阶段证据)及[迁移日期基线](#迁移日期基线) | Codex |
| 2026-09-26 | 单次独立复核 | 阶段 2 | 独立 | 高影响 | 未通过：3 个跨目录相对 Markdown 链接因目录加深一级而失效 | [阶段证据](#阶段证据)；独立扫描列出 3 处链接 | date_directory_phase2_review（推理强度 medium） |
| 2026-09-26 | 修复自验 | 阶段 2 | 自验 | 高影响 | 通过：修正 reviews/fixtures 相对路径并补齐旧路径缺失时的 supersedes 处理；477 个本地 Markdown 链接扫描仅余已知历史损坏链接与预期模板/负例目标；4 旧/新快照状态分别为 `superseded`/`current` | [阶段证据](#阶段证据)；`npm run verify`、`quick_validate.py`、`--check-attestations --strict-readiness` | Codex |

## 未决问题

| 问题 | 推荐方案 | 是否阻塞当前阶段 | 状态 |
|---|---|---|---|
| 无 | 已迁移链接、计划索引及旧快照替代关系均由最终验证确认 | 否 | 无 |

## 风险和回滚

- 主要风险是检查器漏检子目录、相对链接因层级变化失效、重复计划身份、旧快照路径/hash 漂移。每类都必须有正反样本和可核对输出。
- migration skill 只处理文档与路径引用；计划格式/CLI 兼容先由阶段 1 提供。skill 不编辑检查器或其他代码，不自动安装、发布或扫描迁移范围之外的项目。
- 先完成工具与兼容样本，再移动文件；任何一步检查失败时停止迁移，恢复已移动文件的原路径及本批路径引用，再复验原目录状态。
- 不覆盖或重写现有 attestation。需要新快照时用 CLI 建立 supersedes 关系；无法形成可信后继的快照保留并标记实际复核状态，不声称全部证据 current。
- 迁移仅覆盖本仓库迁移清单。其他项目继续使用旧路径，除非其用户单独要求迁移。

## 关联 ADR、迁移、spec 或 issue

- 历史设计基线：[iterative-governance-reliability 阶段 3 行为契约](../20260906/iterative-governance-reliability.md#阶段-3-行为契约)
