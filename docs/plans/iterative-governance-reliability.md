# 计划：持续迭代治理与规范优化

## 背景

2026-09-05，用户希望评估本项目作为类似 SDD 的 vibe coding 持续迭代规范，在流程、门禁、文档职责和目录结构方面的改进空间。只读评审确认现有阶段准入、Step 0、独立复核和事实源分层值得保留，同时发现严格检查漏检、恢复摘要失真、验证入口分离及长期契约入口不清等问题。用户随后要求创建优化计划，2026-09-06 继续完成立项。

本计划承接这次评审，不重开已完成的优化计划。计划级状态、当前阶段、依赖和阻塞索引以 [PLAN_MAP](../PLAN_MAP.md) 为准；本文件承载优化范围、候选方案、阶段验证和验收条件。

## 目标

- 让严格门禁能够拒绝空值、冲突状态和有效阻塞，避免以声明状态代替准入结果。
- 让新会话从现有 `workset` 得到可信的阻塞、最近证据和下一动作。
- 让本仓库 CI 与发布前验证采用一致的检查集合，并验证失败能够阻止后续发布动作。
- 明确长期行为契约与单次变更计划的职责，以较少文档支持持续迭代。
- 建立小修改、阶段内迭代、高风险跨阶段变更的分流与用户场景验收方式。
- 让需要严格验收的证据关联被审查内容，减少无关文档更新造成的复核噪声。

## 非目标

- 立项本身不授权代码实施。2026-09-06 用户要求推进并确认兼容策略，阶段 0 和阶段 1 独立准入随后通过，阶段 1 已完成，阶段 2 已独立验收完成，阶段 3 已独立验收完成；阶段 4 用户已确认可选范围绑定，本阶段独立准入通过后开始实现。提交、发布、安装同步、部署及外部项目修改不在本轮范围内。
- 不恢复已废弃的整计划自主执行、步骤清单或 `plan next`；跨轮执行继续使用宿主已有能力。
- 不建立通用工作流引擎、审批平台、强制 PRD/design/tasks 文档组合或第二套人工维护状态文件。
- 不批量迁移历史文档，不预建空目录，不追溯改写独立复核记录，不自动更新旧 attestation。
- 不把机械检查、覆盖率百分比或实施声明作为业务验收，也不以自动修复扩大用户授权。

## 需求探索

### 已确认事实

- 用户先要求创建计划，2026-09-06 要求推进，并确认采用“兼容优先 + CI/发布显式严格检查”：保留默认检查现有退出码分层及 JSON 字段，新准入问题在严格模式阻断；本阶段不迁移旧文档、不改宿主调度。
- 当前项目已有治理、独立准入和小任务豁免；优化应在现有机制上进行。
- 2026-09-06 对 `HEAD 336b728` 加当前未提交工作树进行只读复查，观察结果见 [Step 0 证据](#step-0-证据)。该描述不是不可变内容指纹。

### 暂定假设与验证方式

- 共享解析模型可以改善 `check`、`workset` 和 hook 的一致性；须用旧计划、空值、阻塞及冲突反例验证，不能只统一内部函数就宣称语义一致。
- 现有 Markdown 可继续作为主要编辑格式；先收窄机器字段并校验链接，再决定是否需要版本化元数据。
- 跨多次迭代的能力适合独立 spec，普通变更通常一份计划足够；以三类任务样本验证文档成本和可查找性。
- 范围化证据可以减少无关失效；须同时证明相关代码变化能够触发复核、无关索引变化不会错误地恢复或撤销结论。

### 范围与非目标

范围覆盖门禁解析、恢复摘要、仓库验证入口、文档和流程规范、可选证据关联。具体宿主调度和六类宿主回放仍由既有计划负责，见 [与既有计划的边界](#与既有计划的边界)。

### 候选方案与取舍

| 事项 | 推荐候选 | 需要保留的边界 |
|---|---|---|
| 门禁与恢复 | 共享解析与校验结果，区分声明状态和验证结果 | 已确认保留现有 JSON 字段和退出码分层；阶段 1 不增加 Schema 字段或命令开关 |
| 规范格式 | 保留 Markdown 固定骨架，正文自由组织，增加链接校验 | 不同时人工维护 Markdown 与 YAML 两套状态 |
| 中等迭代 | 复用已准入阶段，记录行为差异、验收和证据 | 契约、范围或完成条件变化时仍重新评估阶段准入 |
| 失败复核 | 已授权范围内补证据或修复后，再由独立复核者判断 | 候选改进，不覆盖当前“保留阻塞并报告”规则；越过阶段门仍须通过复核 |
| 证据关联 | 对确有门禁需求的场景采用 revision、范围和证据清单 | 不把全量历史回填或每次修改生成快照作为默认要求 |

### 未决问题

未决设计项统一记录在本计划的 [未决问题表](#未决问题)，不在此重复定义。

### 用户确认的探索结论

2026-09-06，使用 `grill-me` 对兼容策略进行单项需求探索。用户先询问两种策略的区别，在了解旧项目升级、默认/严格退出码及 JSON 兼容影响后，确认采用“兼容优先 + CI/发布显式严格检查”。本阶段目标为修复已证实的漏检和摘要失真；范围是诊断与现有派生字段，保留默认错误分层，不迁移旧文档、不改宿主调度；验收以本计划的正反样本和旧文档对照为准。后续 spec、复核修复循环和证据扩展仍是候选，不因本次确认自动冻结。

2026-09-06 阶段 3 需求探索补充：用户确认采用“按需独立契约”。确认范围为跨迭代现行行为优先引用已有 Schema/OpenAPI，没有合适来源才建立 `docs/specs`；计划记录本次差异、阶段和验收，不重复维护字段。小修改不增加文档，已有文档不迁移。具体模板、场景证明和生成/分发一致性仍须本阶段 Step 0 与独立准入；本次不新增逐次用户签收门禁，原有高影响取舍和授权边界保持有效。

2026-09-06 阶段 4 需求探索补充：用户确认采用“可选范围绑定”。只对显式选择的新快照记录被审查文件及相关计划信息，相关变化要求复核，无关地图更新不触发；旧快照、默认命令和既有输出保持兼容，不自动回填。具体文件边界、失效条件和混合工作树证明须本阶段 Step 0 与独立准入。

## 不变量

- 阶段 N 完成不会自动放行阶段 N+1，每阶段须有自己的 Step 0、验证、完成条件和独立准入。
- 普通检查与严格门禁的兼容差异必须明确；不直接把所有历史 warning 升级为 error。
- 同一事实只定义一次，摘要和索引引用或派生；未知、无法解析和冲突不得伪装成无阻塞或通过。
- 文档立项检查不等于独立准入复核；复核不能要求“本次复核已经通过”作为开展本次判断的前提。
- 保留未提交工作树中的既有修改；共享文件采用单一写入者，阶段切换前重新核对差异。

## 与既有计划的边界

| 既有计划 | 本计划的关系 |
|---|---|
| [phase-entry-gate-hardening](phase-entry-gate-hardening.md) | 沿用阶段准入和默认/严格模式边界，新增可复现漏检修复，不改写历史验收 |
| [plan-governance-operability-optimization](plan-governance-operability-optimization.md) | 沿用工作集、阶段关系及证据生命周期，后续变更其公共输出必须先明确兼容契约 |
| [plan-governance-distribution-setup](plan-governance-distribution-setup.md) | 本计划负责验证入口一致性；实际 npm 发布和安装同步仍遵循既有分发流程及授权 |
| [phase-local-review-dispatch](phase-local-review-dispatch.md) | 其阶段 2 继续负责宿主创建/等待/结果消费及六类回放；本计划读取其失败样本，不接管或解除其阻塞。涉及复核修复循环的规范变更，先协调该计划，再审查共同规则 |

阶段 0 的只读分析可以与宿主回放并行。未来修改共同的检查器、skill、模板、生成器、代理入口、测试或地图前，先在地图明确写入次序；不因共享文件就把整个计划变成宿主回放的硬依赖。

## 影响模块或文件

- `docs/plans/iterative-governance-reliability.md`
- `docs/fixtures/iterative-governance-reliability-stage0-cases.md`
- `docs/fixtures/iterative-governance-reliability-stage1-cli-cases.md`
- `docs/fixtures/iterative-governance-reliability-stage2-verification-baseline.md`
- `docs/reviews/iterative-governance-reliability-stage0-readiness-review-20260906.md`
- `docs/reviews/iterative-governance-reliability-stage1-readiness-review-20260906.md`
- `docs/reviews/iterative-governance-reliability-stage1-completion-review-20260906.md`
- `scripts/check_plan_governance.py`
- `scripts/plan_governance_hook.py`
- `tests/test_check_plan_governance.py`
- `tests/test_plan_governance_hooks.py`
- `tests/npm_cli.test.mjs`

- `package.json`
- `.github/workflows/ci.yml`
- `scripts/verify.mjs`
- `scripts/release_npm.mjs`
- `tests/verification_release.test.mjs`
- `AGENTS.md`
- `docs/plans/plan-governance-distribution-setup.md`
- `docs/reviews/iterative-governance-reliability-stage2-readiness-review-20260906.md`
- `docs/reviews/iterative-governance-reliability-stage2-completion-review-20260906.md`
- `docs/fixtures/iterative-governance-reliability-stage3-document-cases.md`

阶段 1—2 交付保留。阶段 2 独立准入后，上述新增文件由当前任务单写；隔离回归文件由 `/root/stage2_failure_baseline` 单写，不兼任独立复核。AGENTS 仅同步发布段，分发计划仅追加维护引用；其余旧修改、锁文件和版本保持原样。

- `resources/skill/SKILL.md`
- `resources/skill/assets/plan.template.md`
- `resources/skill/assets/PLAN_MAP.template.md`
- `resources/skill/assets/spec.template.md`
- `resources/manifest.json`
- `scripts/init_plan_governance.py`
- `tests/test_init_plan_governance.py`
- `README.md`
- `CLAUDE.md`
- `docs/reviews/iterative-governance-reliability-stage3-readiness-review-20260906.md`

阶段 3 由主任务单写规则、模板、manifest、生成器和文档；`/root/stage3_document_baseline` 单写两个初始化/分发测试文件，不兼任独立验收。既有宿主计划、代理元数据及阶段 1—2 非本阶段测试的核心源保持原样。

- `tests/test_attestation_binding.py`
- `docs/fixtures/iterative-governance-reliability-stage4-attestation-cases.md`
- `docs/reviews/iterative-governance-reliability-stage3-completion-review-20260906.md`
- `docs/reviews/iterative-governance-reliability-stage4-readiness-review-20260906.md`
- `docs/reviews/iterative-governance-reliability-stage4-completion-review-20260906.md`

阶段 4 本阶段独立准入已通过，写入所有权见[实施文件范围](#实施文件范围)，保留阶段 1—3 非本阶段文件。

## 后续实施候选范围

| 阶段 | 候选范围 |
|---|---|
| 阶段 1 | `scripts/check_plan_governance.py`、`scripts/plan_governance_hook.py`、`bin/plan-governance-cli.mjs`、检查器/hook/CLI 回归及相关 fixture |
| 阶段 2 | `package.json`、`.github/workflows/ci.yml`、`scripts/verify.mjs`、`scripts/release_npm.mjs`、`tests/verification_release.test.mjs`；仅同步 `AGENTS.md` 发布段及分发计划维护记录，不扩展阶段 3 规范 |
| 阶段 3 | `resources/skill/`、`resources/manifest.json`、`scripts/init_plan_governance.py`（内嵌规则与受管区外字节保护）、`README.md`、`AGENTS.md`、`CLAUDE.md`、文档模板及初始化回归；按需建立正式 spec |
| 阶段 4 | 检查器证据关联、复核/attestation 模型、样本及端到端验收记录 |

## 公共契约变化

阶段 1 门禁与工作集按下述约束实现，修复结果见[阶段 1 完成证据](#阶段-1-完成证据)。CI/发布检查集合在阶段 2 固定，固定 Markdown/长期 spec 职责在阶段 3 固定，范围化证据在阶段 4 固定，不以本次兼容策略确认替代后续阶段自己的验证。

## 阶段 0 技术收敛

### B01 阻塞事实源与保守投影

- 沿用地图负责计划/阶段的阻塞索引、专项计划负责问题细节的权责；不增加第二套人工维护状态文件。`check`、`workset`、hook 应消费同一解析结果，再按入口决定严重级别和展示方式。
- 读取地图当前阻塞表中可明确归属该计划的记录、专项计划 `未决问题` 表及当前阶段准入摘要。任一来源明确声明当前阻塞时，不得因为另一来源缺失或写“无”而将其清空；同时输出来源缺失或冲突诊断，要求同步现有文档。
- 地图影响范围只按明确计划 ID/链接归属；无法归属时输出诊断，不用自然语言猜测影响哪个计划。
- 已有已解决状态不继续阻塞；未知状态不能默认当作已解决。必填空值、占位值、重复字段/计划 ID 和无法确定的当前阶段是结构诊断；历史未启用准入结构与“声明待实施但结构不全”分开处理。
- 摘要中的原始阻塞文字可以作为已声明问题展示，不从描述中生成实施步骤。只有明确“无”或可定位且一致的已解决记录才表示无阻塞；链接、未识别文本或相互矛盾的结论不能证明准入通过。

### B02 输出及退出码兼容

- 保留 `schema_version: 1` 和既有 JSON 字段；阶段 1 不新增 `gate_status`、生命周期枚举、命令开关或自动写回。
- `status`/`phase` 保持地图声明；`readiness` 和 `next_action` 使用现有枚举表达经过检查的可操作性。明确阻塞或当前失败复核对应 `blocked/resolve_blocker`；结构冲突、重复 ID 或无法证明准入时不得输出确定的 `ready/implement`，应使用现有 `unknown` 和 `warnings` 解释原因。
- `候选/设计中` 允许缺少尚未产出的准入证据；缺基线时仍提示 `complete_step0`，材料齐全但尚未复核才提示 `independent_review`。失败复核与尚未复核必须区分，不能循环要求同一份失败材料再次申请复核。
- 对 `待实施/实施中`，严格 `check` 与严格 `workset` 对同一准入缺陷均失败。默认模式中已有硬错误仍失败；新增准入/一致性诊断以 WARNING 表达，不因修复默认升级成全量严格检查。默认 `workset` 的诊断退出码兼容现行行为，但即使退出 0 也不能给出错误的实施建议。
- hook 仍为只读、非阻塞提示，返回码不承担硬门禁；更新提示以呈现相同的已知阻塞和诊断。实际 CI/发布的严格检查接入属于阶段 2。
- 当前阶段的编号记录标题可作为已知历史别名读取并告警；生成模板仍使用固定标题。仅读取当前阶段内的最近记录，不把历史章节当作新进展。

### B03 阶段 0 替代集成基线

完整复现从单函数扩展到 Python CLI 的参数解析、`main`、默认/严格退出码及工作集 JSON，使用虚拟文件系统，不替换业务校验函数。十一类样本和执行命令见 [阶段 0 样本](../fixtures/iterative-governance-reliability-stage0-cases.md)。当前仓库另用真实 Node 入口执行治理和工作集查询。

这是阶段 0 的替代集成基线：避免在契约收敛前创建或安装测试产物。它覆盖 Python 命令入口，不等价于真实临时目录中的 Node→Python 全链路、完整 pytest 或 npm 套件。阶段 1 实施前须用实际文件样本再确认 CLI 参数透传、返回码及无写入边界；不得把本次十一项回放称为完整端到端通过。

| 样本 | 阶段 1 目标行为 | 默认/严格边界 |
|---|---|---|
| 合法准入、当前固定记录、旧设计文档 | 合法准入仍可派生 ready；当前记录被读取；旧设计保持 design | 保留成功返回，不误伤尚未准入的设计计划 |
| 空值、重复 ID、无法判定的状态 | 有明确诊断，不派生实施建议 | 新诊断默认告警；影响待实施/实施中准入或全局索引完整性时严格失败 |
| 仅摘要或仅地图阻塞 | 显示有效阻塞，提示来源需同步 | 新增来源诊断默认告警，严格准入失败；原有开放问题硬错误不降级 |
| 未决问题开放或未知状态 | 保留问题；未知不得当已解决 | 已有错误分层保持；严格入口不能对同一准入问题一过一拒 |
| 当前复核失败 | 保留失败原因并引导补证据/解决阻塞 | 设计阶段保留设计自由；声明待实施/实施中时严格失败 |
| 当前记录使用阶段编号标题 | 兼容读取已知别名且给出固定标题提示 | 不读取历史阶段，不通过自动改写文件掩盖漂移 |

## 文档与目录

阶段 3 已验证下列按需布局；职责以[阶段 3 行为契约](#阶段-3-行为契约)为准，不要求目标项目迁移历史文档：

```text
docs/
  PLAN_MAP.md              # 状态、当前阶段、依赖和证据入口
  plans/<change>.md        # 本次行为差异、实施和验收，保持平铺
  specs/<capability>.md    # 按需：跨迭代的现行行为契约
  adr/<decision>.md        # 按需：重要决策、备选项和后果
  migrations/<name>.md     # 按需：真实迁移与兼容窗口
  reviews/<report>.md      # 独立复核结果
  fixtures/<case>.md       # 人工样本设计或宿主回放说明
  attestations/*.json      # 按需：实际使用的验收快照
tests/fixtures/            # 可执行测试输入，避免与文档样本重复维护
```

- 已有 OpenAPI/Schema 可直接作为契约，不强制另写重复 spec；普通变更通常一份计划即可。
- 固定机器字段与自由正文分开；现行标题、目录扫描和历史锚点的兼容方案先验证，再决定是否迁移。
- 索引保留现有三表，历史详情通过链接查找；不为了整齐搬动旧计划或改写历史事实。
- 模板用少量“输入、操作、可观察结果、验证链接”串联用户验收；反馈区分原验收未满足、原范围内改进和新需求，再决定是否调整阶段或新建计划。

## 阶段路线图

| 阶段 | 目标 | 进入条件 | 验证方向 | 状态 |
|---|---|---|---|---|
| 阶段 0 | 固定问题基线、候选方案、兼容边界和计划分工 | 用户已要求创建优化计划；现有仓库可只读检查 | 真实样本、最小反例、未决取舍和独立设计准入 | 已完成 |
| 阶段 1 | 修复门禁漏检和恢复摘要失真 | 阶段 0 收敛；本阶段反例、兼容契约、实施授权及独立准入齐全 | 空值/重复/阻塞/冲突反例，check/workset/hook 一致性及旧文档兼容 | 已完成 |
| 阶段 2 | 统一 CI 与发布前验证入口 | 阶段 1 验收；本阶段失败注入基线与独立准入齐全 | Python/Node/治理检查完整覆盖，任一失败中断后续发布动作 | 已完成 |
| 阶段 3 | 完善文档职责、目录、任务分流和用户验收 | 本阶段三类任务样本及独立准入齐全，共同规则分工明确 | spec/plan 可查找性、固定结构/锚点、模板分发一致及复核修复边界 | 已完成 |
| 阶段 4 | 增强证据关联并完成端到端验收 | 前序成果可复现；本阶段证据失效与旧快照兼容样本通过独立准入 | 相关/无关变化、混合工作树、完整迭代回放及独立完成验收 | 已完成 |

路线图中的目标和验证方向不能单独作为准入依据；各阶段的实施授权与复核证据以对应章节为准。

## 阶段 0 完成证据

2026-09-06 独立复核确认：达到阶段 0 `待实施` 标准，阶段 0 设计交付完成；[报告与被审查内容指纹](../reviews/iterative-governance-reliability-stage0-readiness-review-20260906.md)。下列记录保留为阶段 0 过程，阶段 1 的当前准入见 [当前阶段](#当前阶段)。

### 范围

阶段 0 负责立项、只读复现和契约设计。当前交付是一份可继续收敛的专项计划及同步索引，保留后续实现授权和阶段准入边界。

### 阶段 0 历史准入摘要

| 字段 | 内容 |
|---|---|
| 准入状态 | 设计中 |
| Step 0 | [只读基线](#step-0-证据)；尚未形成全部反例的固定回归集 |
| 样本矩阵 | [阶段 0 样本矩阵](#样本矩阵) |
| 验证方式 | [文档和基线验证](#验证方式) |
| 失败/回滚边界 | [风险和回滚](#风险和回滚) |
| 当前阻塞项 | 无 |
| 最新独立准入复核 | 尚未进行；本轮创建计划不构成准入复核 |

### 实施步骤

1. 登记评审发现、范围、非目标和候选阶段，同步地图。
2. 只读复查当前仓库及最小反例，区分漏检与既有兼容设计。
3. 按用户确认的兼容组合收敛 B01—B03，记录默认/严格差异和未覆盖的证据边界。
4. 以文档中的可执行命令固定正反样本、输入、结果和安全边界；真实文件系统 CLI 回归在阶段 1 自己的 Step 0 中补齐。
5. 在范围和证据齐全时自动发起独立只读准入复核，输入计划、阶段、被审查内容指纹、范围、实际命令和安全边界；追加结论，不自我批准。

### Step 0 证据

基线类型：当前仓库只读快照、纯内存函数回放和既有真实计划样本。2026-09-06 重新检查时，普通结构基线所对应的 `HEAD` 为 `336b728`，另有用户既有未提交修改；不能只凭 HEAD 复原这份工作树。

| 编号 | 当前观察 | 证据入口 |
|---|---|---|
| E01 | 合法准入样本与必填值全部清空的样本均未得到严格校验错误；仅摘要声明阻塞时 `has_current_blocker` 为 false | [最小只读复现](#最小只读复现)、[检查器](../../scripts/check_plan_governance.py) |
| E02 | `phase-local-review-dispatch` 阶段 2 正文已有回放缺口与失败复核，工作集仍输出空阻塞、空最近证据及 `independent_review` | [真实计划](phase-local-review-dispatch.md#阶段准入摘要)、[最新复核](phase-local-review-dispatch.md#最新独立准入复核)、[验证方式](#验证方式) |
| E03 | CI 运行 Python 测试和普通治理检查；发布前运行 npm 测试，集合不同 | [CI](../../.github/workflows/ci.yml)、[发布脚本](../../scripts/release_npm.mjs)、[package.json](../../package.json) |
| E04 | 文档权责允许 spec/Schema，但目录和模板的默认入口主要围绕计划；长期契约与变更记录的迁移规则待设计 | [skill](../../resources/skill/SKILL.md)、[计划模板](../../resources/skill/assets/plan.template.md) |
| E05 | attestation 记录整份计划和地图 hash，未直接绑定实现范围；2026-09-05 评审观察到四份旧快照为 needs_review | [快照实现](../../scripts/check_plan_governance.py)、`docs/attestations/`；后续验收须重查 |

#### 最小只读复现

从仓库根目录执行。复用现有测试样本函数，在内存检查，不执行测试套件、不创建 fixture 或缓存文件：

```bash
python3 -B - <<'PY'
import re
import runpy
ns = runpy.run_path('tests/test_check_plan_governance.py')
checker = ns['check_plan_governance']
valid = ns['readiness_plan_text']()
fields = ['Step 0', '样本矩阵', '验证方式', '失败/回滚边界', '最新独立准入复核', '日期', '阶段', '结论', '证据', '复核者']
empty = re.sub(r'(?m)^\| (' + '|'.join(map(re.escape, fields)) + r') \|.*\|$', r'| \1 | |', valid)
for name, content in [('valid', valid), ('empty_values', empty)]:
    warnings, errors = [], []
    checker.check_phase_readiness('', 'demo', {'status': '待实施', 'phase': '阶段 1'}, content, True, warnings, errors)
    print(name, {'errors': errors, 'warnings': warnings})
blocked = valid.replace('| 当前阻塞项 | 无 |', '| 当前阻塞项 | 外部授权待确认 |')
print('summary_only_blocker', checker.has_current_blocker(blocked))
PY
```

2026-09-06 实际输出：`valid {'errors': [], 'warnings': []}`、`empty_values {'errors': [], 'warnings': []}`、`summary_only_blocker False`。这是当前缺陷基线，不是修复通过证据；函数级回放不替代后续完整 CLI 正反测试。

### 样本矩阵

| 样本 | 输入或基线 | 可执行命令 | 当前预期结果 | 失败判定 | 输出位置 |
|---|---|---|---|---|---|
| S01 空值及摘要阻塞 | E01 的现有 helper 和内存字符串 | 执行上方 Python 命令块 | 重现 E01 的无错误/未识别结果 | 无法加载 helper，或输出变化却仍沿用旧结论 | 标准输出；摘要记录在 E01 下方 |
| S02 恢复摘要 | E02 真实计划、固定标题与最新复核 | `PYTHONDONTWRITEBYTECODE=1 node bin/plan-governance-cli.mjs workset . --json`；按计划 ID 检查 | 立项基线仍存在空阻塞、空最近证据 | 只看字段为空就宣称没有阻塞，或把当前样本变化忽略 | 标准输出；E02 |
| S03 验证集合 | E03 当前源码 | `rg -n 'pytest|npm|strict-readiness|run\(' .github/workflows/ci.yml package.json scripts/release_npm.mjs` | 可确认两入口覆盖集合不同 | 无法定位实际入口或把说明文字当执行证据 | 标准输出；E03 |
| S04 文档结构 | 当前模板、README 与规则源 | `rg -n 'spec|Schema|阶段准入摘要|完成条件|测试覆盖率' README.md resources/skill/SKILL.md resources/skill/assets/plan.template.md` | 找到既有职责与固定结构，列出待设计差异 | 以新候选规范评价旧文档违规，或重复建事实源 | 标准输出；E04 |
| S05 证据生命周期 | 当前四份旧快照 | `PYTHONDONTWRITEBYTECODE=1 node bin/plan-governance-cli.mjs check . --check-attestations` | 记录实际漂移与有效状态，普通历史漂移不构成实现失败 | 覆盖旧快照、把 warning 清空当验收，或未经复核宣称 current | 标准输出；E05 |

扩充的十一类 Python 命令入口样本已经固定于 [阶段 0 样本](../fixtures/iterative-governance-reliability-stage0-cases.md)，包含合法对照、空值、两种单一来源阻塞、开放/未知状态、重复 ID、失败复核、两种当前记录标题和旧设计计划。阶段 1 准入前还须补齐真实文件系统 CLI、跨来源冲突、已解决状态、复核历史/当前阶段冲突和重复字段反例。

### 阶段证据

- `docs/plans/iterative-governance-reliability.md`
- `docs/fixtures/iterative-governance-reliability-stage0-cases.md`

### 最近实施/验证记录

| 日期 | 类型 | 动作/结果 | 证据 | 状态 | 记录者 |
|---|---|---|---|---|---|
| 2026-09-06 | 只读基线 | 严格治理检查返回 0；工作集仍重现 E02；纯内存回放重现 E01 | [Step 0](#step-0-证据)、[最小复现](#最小只读复现) | 观察完成，缺陷未修复 | Codex |
| 2026-09-06 | 立项文档验证 | 普通/严格/停滞检查及 git diff --check 通过；本计划本地链接和锚点有效；workset 正确列出本计划 B01—B03。drift 返回 0，保留一条跨计划地图行无法唯一归属的 WARNING | [验证方式](#验证方式)；命令标准输出 | 立项验证通过，阶段准入未完成 | Codex |
| 2026-09-06 | 需求探索与基线扩充 | 用户确认兼容优先及 CI/发布显式严格检查；十一类 Python CLI 入口样本重现漏检与合法对照，记录内容 hash 和替代基线限制 | [技术收敛](#阶段-0-技术收敛)、[样本](../fixtures/iterative-governance-reliability-stage0-cases.md) | 待独立准入复核 | Codex |

### 验证方式

立项文档的验证命令如下；完整测试套件在实施阶段另行运行，不能把文档检查当作测试通过证据：

```bash
PYTHONDONTWRITEBYTECODE=1 node bin/plan-governance-cli.mjs check .
PYTHONDONTWRITEBYTECODE=1 node bin/plan-governance-cli.mjs check . --strict-readiness
PYTHONDONTWRITEBYTECODE=1 node bin/plan-governance-cli.mjs check . --stale-days 10
PYTHONDONTWRITEBYTECODE=1 node bin/plan-governance-cli.mjs check . --drift
PYTHONDONTWRITEBYTECODE=1 node bin/plan-governance-cli.mjs workset . --json
git diff --check
rg -n 'iterative-governance-reliability|持续迭代治理与规范优化|B01|B02|B03' docs README.md resources/skill
rg -n '草案为准|以草案为事实源|详见草案|draft is source|source of truth.*draft|以.*draft.*为准' docs README.md resources/skill
```

核对索引、依赖、阻塞链接、当前阶段与反向引用；同一事实只在专项计划定义，地图保留摘要入口。检查通过只代表当前结构兼容；处于 `设计中` 的计划不会因此获得实施准入。

本次 drift 的具体提示是 `PLAN_MAP.md 变更无法唯一归属到活跃计划索引行`：新增的阶段关系和共享写入行同时引用两个活跃计划，已逐项核对为本轮分工登记。保留该提示，不用扩大影响范围或忽略整个地图来消除它。

### 测试覆盖率

本轮是文档立项和只读函数回放，没有新增测试或重跑完整套件，不引用旧覆盖率作为本计划验收结果。后续按行为场景记录覆盖；实施检查器时运行现有 Python 分支覆盖门禁及 Node 回归，统一验证入口阶段验证任一检查失败均能中断。

### 完成条件

- 立项交付：七项评审方向均有阶段归属，目标、范围、非目标、样本和未决项可查，地图同步，文档检查通过。
- 阶段 0 完成：B01—B03 已收敛并记录用户确认；十一类 Python 命令入口替代基线与真实仓库 Node 查询可复现；未覆盖的真实文件集成明确交给阶段 1 Step 0；独立设计准入复核明确通过。
- 阶段 1 在其自己的样本矩阵、实施授权和独立准入齐全前保持设计状态；阶段 0 完成不代替阶段 1 准入。

## 阶段 1 完成证据

2026-09-06 [独立完成重审通过](../reviews/iterative-governance-reliability-stage1-completion-review-20260906.md#第二轮通过)，D01 解除，阶段 1 关闭。以下保留阶段 1 实施与验证过程；阶段 2 不自动准入。

### 范围

阶段 1 修复检查器/工作集的空值、重复标识、阻塞来源、失败复核和当前证据读取问题，使默认诊断与严格门禁符合已确认兼容契约；hook 只同步已知阻塞提示。不修改 CI、发布流程、宿主调度、Schema 字段或历史项目。

### 阶段 1 历史准入摘要

| 字段 | 内容 |
|---|---|
| 准入状态 | 已完成 |
| Step 0 | [真实 CLI 基线](../fixtures/iterative-governance-reliability-stage1-cli-cases.md#实际结果)：22 样本、88 调用，修复前输入 hash 不变且临时目录清理 |
| 样本矩阵 | [阶段 1 行为契约](#阶段-1-行为契约)及真实文件样本 |
| 验证方式 | [阶段 1 验证方式](#阶段-1-验证方式) |
| 失败/回滚边界 | [风险和回滚](#风险和回滚)，基线只使用本次创建的临时目录 |
| 当前阻塞项 | 无；D01 经独立重审解除 |
| 最新独立准入复核 | [阶段 1 独立准入：通过](../reviews/iterative-governance-reliability-stage1-readiness-review-20260906.md) |

下一动作：验证

### 实施步骤

1. 在临时目录用真实 Node CLI 回放阶段 0 样本并补齐跨来源冲突、已解决状态、重复字段和跨阶段复核反例。
2. 固定字段解析优先级、已知状态、退出码和旧样本兼容断言，完成独立准入。
3. 通过准入后先补失败回归，再在已声明共享文件边界内实施解析与诊断修复。
4. 运行针对性及完整回归；核对默认/严格入口、旧 JSON 字段和只读边界；独立完成验收后再判断阶段 2 准入。

### 阶段 1 行为契约

- 必填值为空或占位均诊断；结构化摘要、最新复核的重复字段，以及重复当前阶段/摘要/最新复核章节不得采用最后一个值放行。阶段路线图中当前阶段须唯一；重复地图索引/阻塞章节也不能静默覆盖。固定二级未决问题表与需求探索内同名三级标题区分。示例代码块中的标题和表格不能参与事实解析；正文包含连字符不等于表格分隔行。
- 未决问题和地图阻塞表：`是/Yes` 为当前影响，`否/No` 为非当前影响；大小写不敏感。已解决集合为 `已决定、已收敛、已完成、已解决、已关闭、无、resolved、closed、done`；开放集合为 `Open、待确认、未解决、待处理、未决定、待补充`。当前影响行遇到其他状态保留阻塞并给出未知状态诊断；空值或未知影响标志不能证明无阻塞。非当前影响、已解决记录不继续阻塞。
- 地图影响列按明确计划 ID 或计划 Markdown 链接识别；支持逗号、中文逗号、顿号、斜杠分隔的多个 ID。开放且无法归属的地图记录作为全局诊断，严格模式失败。摘要只接受明确 `无` 作为无阻塞；非空非占位文本保留为阻塞。来源有阻塞而摘要为无，或仅摘要有阻塞且无地图索引时提示同步；来源缺失不能清除已知问题。不从自然语言链接推测阻塞已解决。
- 最新复核阶段必须匹配当前阶段；同一阶段明确 `未通过/不通过/失败/不满足/拒绝` 视为失败并保留原因。日期/阶段/结论/证据/复核者必填；与最后一条有效准入历史冲突不得放行。尚未进行或未知结论不能当作失败，也不能当作通过。
- 所有入口复用同一准入诊断和阻塞投影。严格 check/workset 在待实施/实施中因任何准入缺陷失败；候选/设计中缺材料和失败复核保留默认成功退出，以阻塞或设计动作表达实际情况。全局索引重复、无法归属的地图阻塞是严格错误，与生命周期无关。
- 工作集优先顺序：已知阻塞/当前失败复核 → `blocked/resolve_blocker`；其他准入结构不确定 → `unknown/unknown`；有效待实施 → `ready/implement`；有效实施中 → `in_progress` 并读取原有下一动作。设计阶段缺基线 → `design/complete_step0`，材料齐全未复核 → `design/independent_review`。保留原有顶层及计划条目 JSON 字段、`schema_version: 1`、历史筛选行为。
- 最近记录仅取固定 `## 当前阶段` 内的 `最近实施/验证记录`；兼容与索引当前阶段一致的 `阶段 N 最近验证记录` 或 `阶段 N 最近实施/验证记录` 并告警。不同阶段、历史章节和代码块记录不得进入当前摘要。hook 的 session-start/pre-write 使用相同诊断，只提示并返回 0。
- 共享写入由本任务串行负责检查器、hook 和对应测试；复核者只读。CLI 启动器仅验证透传，没有证据说明必须修改。既有宿主调度阶段 2 工作树不被覆盖，共同规范资源留在后续阶段。

下表为修复后预期；退出码按普通/严格顺序。`告警` 指新增诊断保留兼容退出；既有未决表开放阻塞和缺文件默认硬错误不降级。

| 样本 | check | workset | 预期派生/判定 |
|---|---|---|---|
| valid、current_recent、resolved_table、resolved_map、historical_recent | 0/0 | 0/0 | ready/implement；只有 current_recent 有一条当前证据，已解决阻塞不出现 |
| empty_fields、duplicate_field、wrong_review_phase、history_conflict | 0/1 | 0/1 | 告警；unknown/unknown，不实施 |
| summary_only、map_only、both_sources、unknown_state | 0/1 | 0/1 | 告警；blocked/resolve_blocker |
| open_table | 1/1 | 0/1 | 保留默认 check 硬错误；blocked/resolve_blocker |
| duplicate | 0/1 | 0/1 | 重复 ID 诊断，工作集不输出有歧义的计划列表 |
| failed_review | 0/1 | 0/1 | 当前失败原因；blocked/resolve_blocker |
| numbered_recent | 0/0 | 0/0 | ready/implement，一条当前证据与兼容标题告警 |
| legacy_design | 0/0 | 0/0 | design/complete_step0 |
| design_unreviewed | 0/0 | 0/0 | design/independent_review |
| design_failed_review | 0/0 | 0/0 | blocked/resolve_blocker，保留设计阶段自由 |
| no_map | 0/0 | 1/1 | 保留未启用治理的旧入口行为 |
| missing_plan | 1/1 | 0/1 | 缺文件诊断，无实施建议 |

### 阶段 1 验证方式

- 实盘基线：执行 [真实 CLI 样本](../fixtures/iterative-governance-reliability-stage1-cli-cases.md#可执行命令) 中命令块，对照上述修复后矩阵；输入无写入且临时目录清理。
- 针对性回归：`PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider tests/test_check_plan_governance.py tests/test_plan_governance_hooks.py --no-cov`，覆盖空值、重复、跨来源、已解决/未知状态、失败/错位复核、当前/历史记录，以及 hook 一致性。
- 全量验证：`PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider`（保留仓库 85% 分支覆盖门禁）和 `npm test`（含临时包安装 smoke，允许只在本次测试临时目录安装并清理，不同步全局）。测试产生的本地覆盖率文件按原测试配置管理，不提交。
- 治理及差异：本地 Node 入口普通/严格/stale/drift/workset、`git diff --check`、反向引用和草案事实源扫描；区分原有混合工作树告警与本次新增缺陷。不运行写入型 attest、发布或安装同步。
- 额外反例在回归中覆盖：摘要/复核重复章节、代码块假字段、地图多计划/未知归属、未知影响标志、全空阻塞字段、设计失败与缺证据、已完成阶段兼容，以及任一 check 严格缺陷不能继续派生实施动作。若此验证推翻契约，先改本计划并补独立复核。
- D01 复核补充：`下一动作` 的表格和正文回退均屏蔽代码块，示例后的真实动作必须被正确读取。Node 的成功透传测试使用临时合法准入样本；真实仓库普通/严格治理单独执行并保留等待复核时的阻塞结果，避免测试要求本次复核已经通过。该测试隔离不解除阶段门或改变 CLI 行为。

### 阶段证据

- `docs/plans/iterative-governance-reliability.md`
- `docs/fixtures/iterative-governance-reliability-stage1-cli-cases.md`
- `docs/reviews/iterative-governance-reliability-stage0-readiness-review-20260906.md`

### 最近实施/验证记录

| 日期 | 类型 | 动作/结果 | 证据 | 状态 | 记录者 |
|---|---|---|---|---|---|
| 2026-09-06 | 阶段转换 | 阶段 0 独立准入和设计交付通过，当前进入阶段 1 设计；实现尚未开始 | [阶段 0 复核](../reviews/iterative-governance-reliability-stage0-readiness-review-20260906.md) | 待本阶段 Step 0 | Codex |
| 2026-09-06 | Step 0 实盘基线 | 22 类输入、88 次真实 Node→Python 调用完成，输入 hash 不变且临时目录清理；固定预期矩阵及状态语义 | [真实结果](../fixtures/iterative-governance-reliability-stage1-cli-cases.md#实际结果)、[行为契约](#阶段-1-行为契约) | 待独立准入 | Codex |
| 2026-09-06 | 独立准入与实施 | 阶段 1 准入通过后新增失败回归，修复必填/重复结构、阻塞与复核派生；hook 复用检查器，CLI 启动器保持原样 | [准入报告](../reviews/iterative-governance-reliability-stage1-readiness-review-20260906.md)、本阶段源码及测试差异 | 实施声明，待独立完成复核 | Codex |
| 2026-09-06 | 完整回归 | Python 199 passed，覆盖率 93.13%；npm 40/40，含临时安装 smoke；相同 22 类实盘输入符合修复后矩阵，输入不变且临时目录清理 | [修复后结果](../fixtures/iterative-governance-reliability-stage1-cli-cases.md#修复后回归结果)、[阶段 1 验证方式](#阶段-1-验证方式) | 验证通过，待独立完成复核 | Codex |
| 2026-09-06 | D01 失败修复 | 第一轮独立完成复核发现示例动作误读；四类回归先全部失败，修复后 Python 203 passed/93.22%，npm 41/41 含新增 20 次真实 CLI/hook 回放；成功透传测试使用合法临时样本，真实仓库严格检查仍因待复核 D01 返回 1 | [第一轮报告](../reviews/iterative-governance-reliability-stage1-completion-review-20260906.md#第一轮未通过)、新增 D01 回归 | 修复验证通过，阻塞保留至独立重审 | Codex |

### 阶段 1 覆盖与剩余边界

- 首批 58 个针对性反例在原实现上 53 失败、5 个合法/旧行为对照通过；之后扩充多计划归属、重复地图章节、探索同名标题、正文连字符和 D01 示例动作。当前全量 Python 203 项通过，分支覆盖配置开启，总覆盖率 93.22%，满足仓库 85% 门禁。Node 41 项包含默认/严格 CLI 同缺陷拒绝、hook 非阻断、临时安装及 D01 回归。
- CLI 基线输入 helper 保持原样；只对原有工作集测试中本应可实施的调用补齐合法路线图和复核历史，不通过放松断言隐藏缺陷。
- 当前真实 `phase-local-review-dispatch` 派生 `blocked/resolve_blocker`、两项问题和一条最近回放记录，修复了原空摘要；仍设计中，失败复核和宿主证据缺口没有解除。普通/严格治理只作 WARNING 诊断该设计计划。
- 保留已知诊断：宿主旧记录标题、阻塞索引/摘要未同步、其失败复核，以及两活跃计划共享检查器。共享修改由本任务单写，不以改旧计划或扩大 drift 覆盖消除告警。
- 未执行 npm 发布、全局安装同步、宿主调度、旧文档迁移或新 attestation。CI/发布统一验证仍属阶段 2；阶段 1 已经独立完成验收通过，阶段 2 尚未准入。

### 完成条件

- 目标反例得到预期诊断和动作建议，合法旧计划与现有 JSON 字段兼容；严格入口对同一准入缺陷一致失败。
- Python/Node 相关回归和现有完整验证通过，记录场景及覆盖证据；不以少量 fixture 代替完整验收。
- 实施差异与规则源/计划一致，独立完成复核明确通过；阶段 2 不自动准入。

## 阶段 2 完成证据

2026-09-06，[独立完成验收通过](../reviews/iterative-governance-reliability-stage2-completion-review-20260906.md)。以下保存本阶段行为契约与证据；当前推进位置见 [当前阶段](#当前阶段)。

### 范围

阶段 2 统一本仓库 CI 与发布前验证集合，确保 Python、Node 和严格治理检查中任一失败均中断后续版本/发布动作。沿用用户确认的“兼容优先 + CI/发布显式严格检查”，不修改默认 check 契约，不执行实际发布、全局安装同步或外部 registry 写入。

### 阶段 2 历史准入摘要

| 字段 | 内容 |
|---|---|
| 准入状态 | 已完成 |
| Step 0 | [源码与内存替代基线](../fixtures/iterative-governance-reliability-stage2-verification-baseline.md)：已确认集合不一致、验证前切源以及部分切源失败漏恢复；新增入口不存在，采用当前控制流反例作为替代基线 |
| 样本矩阵 | [阶段 2 目标验证矩阵](#阶段-2-目标验证矩阵)，包含三个验证节点、解释器发现、参数、发布失败和恢复边界 |
| 验证方式 | 实施后执行 `node --test tests/verification_release.test.mjs`、`npm run verify`、普通/严格治理及反向引用检查；实际发布路径仅用全部子进程替身回放 |
| 失败/回滚边界 | 任一验证失败停止后续节点，切源尝试起保证 finally 恢复；恢复失败退出非零。失败不重试发布、不自动回滚版本文件。测试隔离与局限见行为契约；撤销仅限本阶段差异 |
| 当前阻塞项 | 无 |
| 最新独立准入复核 | [通过，达到阶段 2 待实施标准](../reviews/iterative-governance-reliability-stage2-readiness-review-20260906.md) |

### 实施步骤

1. 本阶段独立准入通过后，将候选文件纳入影响范围、登记共享文件写入人并实施统一入口和隔离回归。
2. CI 配置 Node/Python 与依赖，只消费统一验证入口；发布在任何 registry 读取/切换、版本或发布命令前调用相同入口。
3. 执行目标矩阵及真实统一验证，核对版本、锁文件和其他既有工作树修改不变，独立完成复核后才关闭本阶段。

### 阶段 2 行为契约

- `npm run verify` 是开发仓库的统一入口，固定顺序为：同一选定 Python 解释器运行 `scripts/check_plan_governance.py . --strict-readiness` → `-m pytest`（沿用分支覆盖和 85% 门槛）→ `npm test`。使用直接 argv 和仓库根目录，不依赖调用者 cwd；任一非零、信号或启动错误退出 1 并停止后续步骤。
- Python 发现沿用 CLI 习惯：设置 `PYTHON` 时只使用该可执行路径；否则依次尝试 `python3`、`python`，仅 ENOENT 可以回退。Python 测试/治理失败不得换解释器重试；选定解释器用于两个 Python 节点。`verify` 不接受位置参数或跳过门禁选项，多余参数退出 2。
- `npm test` 继续是 Node 套件，新增编排回归但不调用真实 verify，避免递归。CI 安装 Python 测试依赖和 `npm ci`，通过 Node 22 与 Python 3.11 执行 `npm run verify`，不再复制另一份检查命令。
- 发布保留现有版本参数、默认 patch、`--dry-run` 和 0/1/2 退出分层。非 dry-run 顺序是 verify → 读取并校验原 registry → 读取版本 → 切官方源 → version → publish → finally 恢复 registry。在调用切源前记录恢复责任，切源部分生效后抛错也尝试恢复；恢复失败必须报告且退出 1。
- dry-run 仅读 registry 并打印完整顺序，不运行验证、切源、version、publish 或恢复命令；参数非法在全部子进程前退出 2，registry 无法读取或值为空/undefined 退出 1。
- 已完成的版本变更不会自动回滚；发布报错可能已被远端接受，退出非零不证明未发布。流程不自动重试，真实发布仍需用户授权并通过分发流程核对 registry。当前任务不执行真实发布、切源、全局安装、安装同步或版本变更。
- 控制流测试读取实际脚本正文，用 VM 拦截全部子进程、文件读取和日志，命令白名单拒绝未知动作；三个验证节点还需嵌套组合回放证明失败无法到达切源。一个临时目录的真实 Node 入口使用虚构 Python/npm 可执行程序验证 argv、cwd、退出码和顺序，不触及真实 registry。
- `npm run verify` 的真实执行会产生现有 pytest 覆盖产物，以及原有 Node 打包/临时安装测试的临时文件和可能的网络读取。它们属于已授权验证范围，不能称整个 verify 为零写入/零网络；零真实发布子进程的声明仅适用于隔离控制流测试。

### 阶段 2 目标验证矩阵

统一编排和发布控制流场景以 `node --test tests/verification_release.test.mjs` 为实施后命令，输出 TAP 到标准输出；实际完整验证以 `npm run verify` 输出及阶段证据记录为准。

| 输入或基线 | 预期结果 | 失败判定 |
|---|---|---|
| 严格治理、pytest、Node 三节点全部成功 | 严格 → pytest → Node；退出 0；CI 和发布均调用 verify | 集合、顺序、cwd 不同，或 npm test 递归 |
| 分别在三个节点注入非零/启动异常/信号 | verify 退出 1，后续节点不运行；组合发布回放没有 registry 读取、切源、version、publish、restore | 错误被放行、换解释器重试测试或继续发布 |
| python3 不存在、全部不存在、显式 PYTHON 不存在、路径包含空格 | 仅默认 ENOENT 回退；显式路径作为完整 executable；失败可见 | 错误回退、shell 拆分或继续 Node |
| 无效 verify 参数、无效 release 参数 | 退出 2，零子进程 | 忽略参数或开始流程 |
| 发布成功及 win32 命令名 | verify → get → switch → version → publish → restore，退出 0 | 未复用统一入口、平台命令错误或顺序不符 |
| registry 抛错/空值/undefined；版本读取失败 | 退出 1，没有切源、version 或 publish | 继续修改外部状态 |
| 切源变更前/部分变更后失败 | 退出 1，均尝试恢复；无 version/publish | 缺少恢复责任或自动继续 |
| version 或 publish 在副作用前/后失败 | 退出 1，均尝试恢复；version 失败不 publish；无自动版本回滚/发布重试 | 隐藏失败、越过节点或重复不可逆动作 |
| 恢复前/后失败，或主动作失败且恢复失败 | 退出 1，主错误和恢复错误都保留 | 恢复失败后成功退出或吞主错误 |
| dry-run 正常和 registry 读取失败 | 仅 get；分别退出 0/1，成功日志按完整顺序展示 | 执行真实验证或任意写动作 |
| 临时目录真实 Node + 虚构命令入口 | 正确 argv/cwd、顺序及失败中断，临时目录 finally 清理 | 虚构命令执行真实业务、递归或残留测试目录 |
| 真实 npm run verify、反向引用与差异检查 | Python 全量/覆盖率、Node 全量、严格治理通过；引用可定位；既有版本和无关差异保留 | 检查失败、覆盖下降至门槛下、越界修改或未处理独立复核问题 |

### 阶段证据

- `docs/fixtures/iterative-governance-reliability-stage2-verification-baseline.md`

### 最近实施/验证记录

| 日期 | 类型 | 动作/结果 | 证据 | 状态 | 记录者 |
|---|---|---|---|---|---|
| 2026-09-06 | 阶段转换 | 阶段 1 独立完成重审通过，D01 解除；阶段 2 保持设计中 | [第二轮完成复核](../reviews/iterative-governance-reliability-stage1-completion-review-20260906.md#第二轮通过) | 阶段 1 已完成 | Codex |
| 2026-09-06 | 只读替代基线 | CI 与发布验证集合不同；发布控制流三场景在内存回放，未执行真实子进程或修改 registry | [阶段 2 基线](../fixtures/iterative-governance-reliability-stage2-verification-baseline.md) | 待固定完整矩阵 | Codex |
| 2026-09-06 | 落档复查 | 关闭阶段 1 后，普通/严格/stale/drift 均退出 0；严格 workset 派生本阶段 design/complete_step0，宿主计划仍 blocked | [完成复核落档检查](../reviews/iterative-governance-reliability-stage1-completion-review-20260906.md#落档后复查) | 结构兼容，阶段 2 未准入 | Codex |
| 2026-09-06 | 独立准入 | 本阶段 Step 0、失败矩阵和边界通过；纳入候选文件后开始实现 | [阶段 2 准入](../reviews/iterative-governance-reliability-stage2-readiness-review-20260906.md) | 实施中 | /root/iterative_stage2_gate |
| 2026-09-06 | 实施及完整验证 | verify/CI/release 采用同一三节点；切源尝试后保证恢复；57 项隔离回归通过，真实统一入口 Python 203/93.22%、Node 98/98 | [实施后证据](../fixtures/iterative-governance-reliability-stage2-verification-baseline.md#实施后验证) | 实施声明，待独立完成复核 | Codex、/root/stage2_failure_baseline |
| 2026-09-06 | 独立完成验收 | 实际复跑完整 verify、核对矩阵/差异/引用，阶段 2 完成验收通过 | [阶段 2 完成报告](../reviews/iterative-governance-reliability-stage2-completion-review-20260906.md) | 已完成 | /root/iterative_stage2_acceptance |

### 完成条件

- CI 与发布消费 `npm run verify`，三节点使用上述固定集合与顺序，默认 CLI/JSON 和 Node-only 的 npm test 契约不变。
- 目标矩阵全部得到预期输出；新控制流回归能在旧发布行为上暴露先切源/漏恢复，并证明三个验证失败均阻止发布。
- 真实统一验证通过，记录 Python 数量/覆盖率、Node 数量、隔离控制流的证明边界；版本、锁文件和无关既有修改保持原样。
- 发布规则段和分发维护记录与当前实现一致；独立完成复核基于当前文件、实际命令及反向引用明确通过；阶段 3 保持设计中。

## 阶段 3 完成证据

2026-09-06 [独立完成验收通过](../reviews/iterative-governance-reliability-stage3-completion-review-20260906.md)，阶段 3 关闭，不自动放行阶段 4。

### 范围

阶段 3 完善文档职责、按需目录、任务分流和用户可观察验收。用户已确认长期行为优先引用现有 Schema/OpenAPI，无合适来源才按需建立 docs/specs；计划记录本次差异和验收。小修改不增治理文档，历史文档不迁移，已有准入/授权不被文档分流替代。

### 阶段 3 历史准入摘要

| 字段 | 内容 |
|---|---|
| 准入状态 | 已完成 |
| Step 0 | [源码、三类旧技能独立走读和内存生成器基线](../fixtures/iterative-governance-reliability-stage3-document-cases.md)，补充受管区外尾部空白/CRLF 被改写的内存反例；不等价于生成/分发端到端 |
| 样本矩阵 | [阶段 3 目标矩阵](#阶段-3-目标矩阵)，含三个主场景、失败复核变体与文档保持边界 |
| 验证方式 | 当前样本文件的 pytest/npm/verify/skill 校验命令，独立新上下文行为后测和本地链接复查 |
| 失败/回滚边界 | 仅变更本阶段规则/模板与分发回归；临时 init/upgrade/setup/pack/install 明确授权验证，不迁移旧 docs、不改 CLI/Schema/宿主调度、不全局安装或发布；失败保留阻塞，只撤销本阶段精确差异 |
| 当前阻塞项 | 无 |
| 最新独立准入复核 | [通过，达到阶段 3 待实施标准](../reviews/iterative-governance-reliability-stage3-readiness-review-20260906.md) |

### 阶段 3 行为契约

- 三类任务分流：无既有计划的小修改遵循现有豁免；仍满足当前准入且范围、契约、完成条件和授权未变的阶段内反馈复用原计划；公共契约/迁移或实质范围变化先澄清、更新相应计划并重新评估准入。分流不覆盖独立复核失败的停止规则，不自动允许跨阶段或高影响动作。
- 现行契约优先使用已有 Schema/OpenAPI 等正式来源；需要长期文字行为契约而无合适来源时才按需建 `docs/specs/<capability>.md`。计划记录本次差异、阶段、Step 0、验证和完成条件并链接契约；无独立来源时允许计划明确承载位置，不要求追溯提取旧内容。ADR 记录取舍与后果，migration 记录真实迁移、兼容窗口和回滚；一旦使用独立文档，其他地方链接，不并行维护同一事实。
- `docs/plans/*.md` 保持平铺和五个固定机器标题；spec/ADR/migration/reviews/fixtures/attestations 按实际内容使用，tests/fixtures 承载可执行输入。init 不自动创建 spec 或额外目录，不强制 PRD/design/tasks 组合，不迁移历史计划或旧复核记录。
- 计划模板增加小型 `用户可观察验收` 表：场景、输入/前置、操作、可观察结果、验证证据。技术任务可用 CLI 输出、文件差异或调用方行为，无界面要求；不适用时简述替代观察。反馈区分原验收未满足、原范围改进、新需求；沿用现有记录区。场景不是逐次用户签收的新门禁，也不能以治理/覆盖率通过代替结果。
- 新增可选 `assets/spec.template.md`，只提示范围、已有契约引用、现行行为/失败语义、兼容和可观察场景及关联计划；不复制计划状态/阶段/Step 0。skill 链接该模板，manifest 纳入分发；只作为按需起点，不自动创建目标项目 spec。
- `update_managed_file` 纳入局部兼容修复：用不转换换行的 UTF-8 读写保留原字节；替换仅覆盖受管标记之间的内容，追加只增加必要分隔与新块，不 rstrip 用户原文；重复执行保持幂等。原有文件新建、标记识别和命令接口不变。测试包含尾部空白、CRLF 前后文和原有 LF 文本。
- 同步 skill、计划/地图模板、生成器内嵌代理规则/地图、README、仓库 AGENTS/CLAUDE 受管区及本地图权责摘要；代理元数据、checker/JSON/默认严格契约和阶段 2 verify/release 不变。已有业务历史文档不扫描回写。保留已发布分发记录，不运行全局同步。

### 阶段 3 目标矩阵

所有命令和输出位置见[本阶段样本入口](../fixtures/iterative-governance-reliability-stage3-document-cases.md#实施后验证入口)。行为样本通过新上下文走读，机械一致性通过临时 init/upgrade/setup 和分发测试；二者分别记录。

| 输入/基线 | 预期 | 失败判定 |
|---|---|---|
| S3-01 文案小修改 | 沿用豁免，0 新治理文档，按实际提示验证 | 强制新建计划/spec/ADR或初始化 |
| S3-02 原阶段反馈 | 复用原计划、原契约和准入；读取原验收预期，记录实际差异和证据 | 自动新开计划/重做所有阶段门；自行发明业务预期 |
| S3-02 最新独立复核失败变体 | 保留失败阻塞，不因历史已准入或新分流自行放行 | 以实施声明或旧通过越过失败门禁 |
| S3-03 字段迁移且已有 OpenAPI | 契约继续单一定义在 OpenAPI；先确认窗口/失败/回滚，再建立本次计划，其他文档按需 | 擅定兼容窗口、重复定义字段、无准入直接实施 |
| 无既有契约且确需跨迭代文字规范 | 可选 spec 能定位现行行为及验证，计划链接本次差异 | 把 spec 变成第二地图或强制所有任务使用 |
| 临时 init 新项目 | 模板含场景和契约入口，机器标题兼容；仅生成现有最小结构 | 自动新建 spec/历史迁移、固定结构失效 |
| 临时 upgrade/rules-only | 已有计划、spec、Schema、历史报告和非受管区内容字节不变，受管规则与生成器一致 | 覆盖既有文档或丢失用户自定义内容 |
| 无受管标记尾部空白、CRLF 前后文，重复更新 | 原文作为字节前缀/后缀保留，第二次无额外变化；用真实临时文件对比 | 文本规范化、空白裁剪、追加重复块或幂等失败 |
| 源资源 → 打包 → 临时 setup | manifest 列出可选模板，实际安装资源与源内容一致，init 使用相同计划模板 | 缺文件/旧模板、全局目标被写入 |
| 全量 verify/skill 校验/链接与反向引用 | 完整验证通过，规则语义一致、引用可定位、阶段 1—2 核心文件保持 | 旧事实源规则并存冲突、资源漏同步或独立复核未通过 |

### 实施步骤

1. 独立准入通过后纳入本阶段资源/生成器/测试范围，登记单一写入人。
2. 按上述契约更新规则和模板，补充必要的文档保护与资源分发验证。
3. 运行机械验证及独立新上下文行为后测，补齐证据；独立完成验收后再关闭阶段 3。

### 阶段证据

- `docs/fixtures/iterative-governance-reliability-stage3-document-cases.md`

- `docs/reviews/iterative-governance-reliability-stage2-completion-review-20260906.md`

### 最近实施/验证记录

| 日期 | 类型 | 动作/结果 | 证据 | 状态 | 记录者 |
|---|---|---|---|---|---|
| 2026-09-06 | 阶段转换 | 阶段 2 独立完成通过；阶段 3 保持设计中，收敛自身材料 | [阶段 2 完成复核](../reviews/iterative-governance-reliability-stage2-completion-review-20260906.md) | 待自身 Step 0 | Codex |
| 2026-09-06 | 用户确认 | 用户选择按需独立契约，保留现有来源、小修改豁免和不迁移旧文档 | [需求探索](#需求探索) | 已确认职责取舍 | 用户 |
| 2026-09-06 | 独立准入 | 文档职责/分流/分发矩阵通过；审查中补齐非受管区字节保护范围与基线 | [阶段 3 准入](../reviews/iterative-governance-reliability-stage3-readiness-review-20260906.md) | 实施中 | /root/iterative_stage3_gate |
| 2026-09-06 | 实施与机械验证 | 规则/模板/manifest/受管规则同步；4 项旧失败修复；初始化 32、Node 单文件 11、完整 Python 208/93.15% 与 Node 98 通过 | [机械验证](../fixtures/iterative-governance-reliability-stage3-document-cases.md#实施后机械验证) | 实施声明，待独立完成验收 | Codex、/root/stage3_document_baseline |
| 2026-09-06 | 独立行为后测 | 新上下文仅使用 skill/模板处理三个原始请求、失败复核变体与长期契约新样本，文档选择/停止判断符合目标 | [后测记录](../fixtures/iterative-governance-reliability-stage3-document-cases.md#独立新上下文行为后测) | 行为走读通过，非业务验收 | /root/stage3_forward_validation |
| 2026-09-06 | 独立完成验收 | 复跑 verify、资源/受管字节/旧反例和引用检查，阶段 3 完成验收通过 | [阶段 3 完成报告](../reviews/iterative-governance-reliability-stage3-completion-review-20260906.md) | 已完成 | /root/iterative_stage3_acceptance |

### 完成条件

- 三类任务及失败复核变体在新上下文中正确选择最少文档、准入动作和可观察验证，既有 Schema 被复用，长期 spec 可按需找到。
- 规则源、生成规则、模板及临时分发一致；用户已有文档和非受管内容保持不变，不建立多余目标目录。
- 模板保持固定结构，阶段 1—2 核心契约无回归；本阶段完整 verify、skill 校验、链接/反向引用和针对性验证通过，证据如实区分模型走读与真实业务。
- 最新独立完成复核基于当前文件和实际命令通过；不以本阶段完成自动放行阶段 4。

## 当前阶段

阶段 4 已于 2026-09-06 经[独立完成验收](../reviews/iterative-governance-reliability-stage4-completion-review-20260906.md#第二轮通过)关闭；阶段 0—4 均完成，当前阶段指针保留为阶段 4。以下契约和过程证据保留。

### 范围

阶段 4 按用户确认增加可选的文件范围绑定，并用真实临时项目回放完整迭代。沿用现有 attestation purpose/替代关系和状态输出；不改默认快照、不自动回填、不修改宿主调度、不创建真实仓库完成快照。主任务单写检查器与说明，`/root/iterative_stage2_acceptance` 作为本阶段测试实施助手单写新 Python 回归和 Node CLI 回放（只参与过阶段 2 独立验收，不兼任阶段 4 复核）；独立准入和完成复核者不参与实现。D04 修复时助手派发因宿主线程上限不可用，由主任务接手该项 Python 回归，原助手不再写文件。

### 阶段准入摘要

| 字段 | 内容 |
|---|---|
| 准入状态 | 已完成 |
| Step 0 | [阶段 4 源码与内存替代基线](../fixtures/iterative-governance-reliability-stage4-attestation-cases.md#step-0-基线)：相关源码漏检和无关地图失效均复现；新 CLI 尚不存在 |
| 样本矩阵 | [A01—A16](../fixtures/iterative-governance-reliability-stage4-attestation-cases.md#目标矩阵)，含实际内容/依赖闭包/非法范围/生命周期/兼容与完整迭代 |
| 验证方式 | 定向 Python/Node 回归、真实临时 CLI 回放、npm run verify、skill/链接/反向引用及既有快照 hash 保持；输出与指纹追加到样本和复核报告 |
| 失败/回滚边界 | 新模式创建前失败不写快照；只读检查不修复快照；严格检查新模式失效时阻断。仅临时项目/Git/安装和现有覆盖产物；不发布、全局同步或改旧快照；撤销限本阶段精确差异 |
| 当前阻塞项 | 无 |
| 最新独立准入复核 | [通过，达到阶段 4 待实施标准](../reviews/iterative-governance-reliability-stage4-readiness-review-20260906.md) |

### 阶段 4 行为契约

1. 可重复 `--attest-file PATH` 显式启用绑定，必须同时提供 `--attest PLAN` 和已有 `--attest-purpose PURPOSE`；无该参数时 legacy `<plan>.json` 与 purpose-only 快照字段/创建/默认输出保持原样。新参数与 workset 不兼容；无值为 argparse 退出 2，组合或预检问题退出 1；未初始化项目使用新参数也不得静默成功。Node check 继续原样透传；不改 workset schema_version 1。
2. 新快照保留全部旧字段，只添加 `binding` 对象：`version: 1`；`files` 为非空 `{path, sha256}` 数组；`related_plans` 为 `{plan, path, sha256}` 数组；`plan_map_projection` 为下述 version 1 投影；`plan_map_projection_sha256` 为投影规范 JSON 的 SHA-256；`revision: {source: "working_tree", head: <40/64 位 hex 或 null>}`。hash 为小写 64 位 hex；数组排序、重复拒绝。完整投影与 hash 同时记录以便复核，hash 不是签名。
3. 投影成员 S 从目标计划开始，反复加入成员索引依赖列的上游，以及 `hard_gate/evidence` 中目标属于 S 的来源，至固定点；不沿下游扩张，soft_context/shared_write 不扩张 S。投影含 `version`、排序 `members`、S 的完整 `index_rows`、属于 S 的完整 `dependency_rows`、任一端点属于 S 的完整 `relation_rows` 与 `shared_write_rows`、影响范围与 S 相交的全部 `blocker_rows`（含已关闭行）。`shared_write_rows` 只读取已有固定九列 `机器可检查共享写入约束`，四列人读 `并行与共享写入约束` 不在自动投影内；需要审查其中说明时显式绑定地图全文。各 `*_rows` 为字符串数组的数组，保留固定表头列序，不包含表头/分隔行；仅去单元格首尾空白、按整行字典序稳定排序；固定 JSON 使用 ensure_ascii=False、sort_keys=True、separators=(逗号,冒号) 后 UTF-8 hash，保留各列正文。空可选章节允许；仅问题/方案/范围全部为 `-` 或空且明确标记“否”的模板阻塞占位行可忽略。有实际问题/方案、影响为是或未知的行不可忽略。依赖详情章节可缺省；存在时每个实际计划行依赖集合须等于索引声明（允许无依赖的 `-` 行），禁止重复行和未知 ID。重复结构章节、非法表头/列数、重复 ID/行、未知依赖/关系端点或无法归属的阻塞使投影失败，不当成空集合。依赖详情必须与索引声明可解释且不遗漏未知 ID。
4. S 中全部专项计划自动记录路径及全文 hash，以包含其自身未决问题、阶段摘要和复核变化。每次检查从当前整图重新计算 S/投影/计划 hash，不只重读老成员。纯 soft/shared 对端索引或全文变化不触发，关系行自身变化触发。目标计划全文仍绑定；`plan_map_sha256` 保留为拍摄时定位，有 binding 时不用于漂移判定。地图无关行、注释、表行顺序不触发新模式漂移。
5. 显式路径为仓库内普通文件，不接受空值、重复（含归一化后重复）、目录、glob、绝对/驱动器/越界路径、文件或父目录 symlink；快照中的路径/类型/version/hash 同样严格验证。自动绑定的计划/地图、快照目录及输出目标也不可经 symlink 越界。新创建或检查已识别 binding 时，在常规治理读取计划前先校验其输入路径，避免先读取外部目标再拒绝；无 opt-in 的既有读取流程保持。拒绝把待创建快照自身作为范围；不自动绑定报告链接，所需报告须先定稿并显式列入。读写 OSError 以可见诊断处理；目录不可枚举不能视为空集合，含已有旧快照的混合检查也先校验路径再读 hash。所有参数、范围、投影、既有治理错误及替代关系在 mkdir/write 前校验；新模式参数/预检失败不留下新快照或目录，不覆盖既有快照。实际创建使用排他文件写入；mkdir/write 的 OSError 可见，尝试删除仅本次新建的部分文件和空目录，不删除既有内容。清理本身失败也须报告残留路径，不声称操作系统故障下绝对零残留。
6. 文件、计划、相关元数据变化/删除/非法或 binding 结构损坏，保留状态记录为 `needs_review`。普通 `--check-attestations` 警告；配合 `--strict-readiness` 时未被有效后继替代的新 binding 漂移/待复核状态阻断，binding 存储结构非法在显式 strict 中始终阻断，默认仍 WARNING。仅手写 `superseded` 不掩盖仍未被有效替代的漂移。无 binding 的旧全文漂移在 strict 中仍只警告；旧字段、状态行格式及默认命令不变。
7. 沿用同计划/purpose、目标存在、无自指/无环和单一 current 规则。新模式创建前校验这些关系；非法后继不能使前驱通过或抑制问题。有效后继指替代边及其存储结构合法，内容漂移不撤销已成立的替代关系。针对带 binding 的前驱，后继也必须带合法 binding；purpose-only/legacy 后继不能解除其范围复核责任，此跨模式边为无效替代（默认 WARNING、strict ERROR），不影响没有 binding 参与的旧关系。新 binding 可以显式替代同计划/purpose 的旧快照。有效后继存在时，历史内容漂移的前驱可保持 superseded，不使严格检查永久失败；后继随后漂移不自动恢复前驱 current。新 binding 缺文件/损坏也留在报告和替代链中，不静默消失。无法解析的 JSON 无法判断是否带 binding，保留旧 WARNING/跳过语义；非对象 JSON 的旧实现会 AttributeError，本阶段补充保守 WARNING/跳过处理，沿用损坏 JSON 的分层，不承诺为其生成绑定状态；若后继显式引用这种记录，目标不可解析仍是关系错误，不能成立替代边。结构和内容有效性分开判断，当前证据不得以未通过独立复核的 hash 冒充验收。
8. hash 来自调用时的实际工作树字节，不读取暂存/提交版本；HEAD 只作定位，非 Git 为 null，无关 HEAD/暂存变化本身不失效。不承诺自动发现未列出的新文件、证明清单完整、验证复核者或抵抗恶意篡改/并发写入；范围完整性和行为正确性仍由独立复核判断。本阶段不新增宿主调度、签名系统或强制 CI 快照开关，CI/release 仍按阶段 2 契约；严格证据检查须显式调用。

### 实施文件范围

- `scripts/check_plan_governance.py`：局部新增绑定解析/校验/快照检查与 CLI 参数，保留独立模块/打包结构。
- `tests/test_attestation_binding.py`：新的正反回归；`tests/npm_cli.test.mjs`：Node 实盘完整迭代及安装透传。
- `README.md`、`resources/skill/SKILL.md`：只说明可选参数、失效边界及独立性，链接本阶段契约，不重复字段定义。
- 本计划、地图、阶段 4 fixture、阶段 3 完成报告、阶段 4 准入/完成报告。

本阶段不修改 init/模板/manifest、hook、verify/release、CI、package/lock、代理元数据、宿主计划或已有 attestation。并行新增的 `plan-governance-workflow-streamlining` 两个阻塞状态使用检查器未识别词，作为文档兼容收口，只将其专项计划和地图对应四个状态单元格规范为“未解决”，保留阻塞事实、阶段与授权边界；其余新增内容保持。新 Python 文件由 pytest 自动发现，不增加依赖。

### 用户可观察验收

| 场景 | 输入/前置 | 操作 | 可观察结果 | 验证证据 |
|---|---|---|---|---|
| 迭代后定位复核对象 | 临时治理项目、明确源码和已准入阶段 | 查询 workset，记录结果后创建可选快照 | 实际文件及相关计划信息可查 | A02/A15 |
| 无关任务继续开发 | 已有有效绑定 | 更新另一计划日期/证据 | 本快照保持 current | A04/A15 |
| 已审查源码再次变化 | 已有有效绑定 | 修改/删除源码，再显式严格检查 | 非零并显示 needs_review；补证据与替代后恢复有效当前记录 | A03/A12/A15 |

### 实施步骤与完成条件

1. 自身独立准入通过后纳入拟议范围，先将源码漏检/无关失效转成真实临时回归，再实现可选绑定。
2. A01—A16 全部获得预期；旧 JSON/退出码、相关闭包和失败零写入经正反样本确认。完整迭代为虚构项目的技术行为验收，不作为宿主或业务生产证明。
3. 完整 verify、skill 校验、反向引用及链接通过，记录真实计数和覆盖率、既有快照/非本阶段核心指纹；阶段 1—3 已审查功能无回退。
4. 独立完成复核基于当前文件、实际命令和全部完成条件明确通过，才关闭阶段 4 和本计划；宿主阶段 2 原有阻塞保持。

### 最近实施/验证记录

| 日期 | 类型 | 动作/结果 | 证据 | 状态 | 记录者 |
|---|---|---|---|---|---|
| 2026-09-06 | 阶段转换 | 阶段 3 独立完成验收通过，关闭；阶段 4 用户确认可选范围绑定 | [阶段 3 完成报告](../reviews/iterative-governance-reliability-stage3-completion-review-20260906.md)、需求探索 | 设计中 | Codex、用户 |
| 2026-09-06 | Step 0 | 真实函数四场景内存回放，源码变化 current、他计划日期变化 needs_review，strict 均无 error；实际写入 0 | [阶段 4 基线](../fixtures/iterative-governance-reliability-stage4-attestation-cases.md#step-0-基线)，工具输出 81c0b9 | 替代基线，非新 CLI 验收 | Codex |
| 2026-09-06 | 独立准入 | 本阶段完整契约/矩阵通过，明确存储结构与漂移、跨模式替代及失败清理边界 | [阶段 4 准入](../reviews/iterative-governance-reliability-stage4-readiness-review-20260906.md) | 实施中 | /root/iterative_stage4_gate |
| 2026-09-06 | 真实失败回归 | 两项临时CLI目标回归在旧checker因不支持新参数失败；旧实际2、目标0，未写快照 | 新测试原始输出 4393b9；A02/A03/A04 | 基线已固定 | /root/iterative_stage2_acceptance |
| 2026-09-06 | 并行文档兼容 | 新出现后续减负计划，原状态词导致严格全仓检查失败；仅四个状态单元格改为规范“未解决” | check 输出 b3703f；后续计划/地图 B01、B02 | 阻塞事实保留，未放行后续计划 | Codex |
| 2026-09-06 | 实施与完整验证 | 可选绑定/完整投影/生命周期及I/O边界落实；126项新增Python，源/安装包完整迭代；全量334/93.16%、Node99/99 | [阶段 4 实施后验证](../fixtures/iterative-governance-reliability-stage4-attestation-cases.md#实施后验证) | 实施声明，待独立完成验收 | Codex、/root/iterative_stage2_acceptance |
| 2026-09-06 | 独立完成验收 | 未通过：独立实盘发现 D02 目录不可读误放行及 D03 混合旧快照路径读取 | [第一轮未通过](../reviews/iterative-governance-reliability-stage4-completion-review-20260906.md#第一轮未通过) | D02/D03 阻塞，未关闭阶段 | /root/iterative_stage4_acceptance |
| 2026-09-06 | 阻塞修复验证 | 显式枚举传播目录错误，混合旧分支先验路径；10 项新回归与全量 Python 344/93.19% 通过 | [D02/D03 重审材料](../fixtures/iterative-governance-reliability-stage4-attestation-cases.md#d02d03-修复与重审材料) | 修复声明，D02/D03 仍待独立确认解除 | Codex、/root/iterative_stage2_acceptance |
| 2026-09-06 | 独立修复重审 | D02/D03 可解除；新增 D04：普通计划文件不可读令混合旧分支异常退出 | [第二轮修复复核](../reviews/iterative-governance-reliability-stage4-completion-review-20260906.md#第二轮修复复核) | D04 阻塞，尚非全计划完成 | /root/iterative_stage4_recheck |
| 2026-09-06 | D04 修复验证 | 混合旧分支 hash 读取错误转诊断并保留替代记录；4 项真实权限正反回归，全绑定测试 140/140 | [D04 重审材料](../fixtures/iterative-governance-reliability-stage4-attestation-cases.md#d04-修复与重审材料) | 修复声明，仍待独立解除 D04 | Codex |


## 全计划完成证据

2026-09-06，独立复核者 `/root/iterative_stage4_recheck` 基于当前工作树和可复现命令确认阶段 4 及全计划完成验收通过，[最终报告](../reviews/iterative-governance-reliability-stage4-completion-review-20260906.md#第二轮通过)。阶段 1 的门禁/恢复摘要、阶段 2 的统一 CI/发布验证、阶段 3 的按需契约与任务分流、阶段 4 的可选范围绑定均已完成；D01—D04 的失败历史及修复独立结论保留。

最终 `npm run verify`：Python 348 passed，分支统计总覆盖率 92.97%；Node 99/99、0 skipped。绑定回归 140 项、源/安装完整迭代、前序保持和新增/修改文档链接通过。旧快照、宿主和后续计划阻塞保持；提交、发布、全局同步及业务生产验收不包含在本次完成结论内。

## 全计划验收方向

最终验收需要证明：门禁拒绝错误输入且兼容合法旧计划；恢复摘要保留真实阻塞与失败原因；CI/发布采用同一检查集合；三类任务都能找到最少必要文档和用户可观察验收场景；相关实现变化触发证据复核，无关索引更新不误判；规则源、生成模板和文档一致。具体完成条件在各阶段实施前固定，并以独立验收记录关闭，不能仅凭地图状态或全量检查通过结束计划。

## 最新独立准入复核

| 字段 | 内容 |
|---|---|
| 日期 | 2026-09-06 |
| 阶段 | 阶段 4 |
| 结论 | 通过，达到阶段 4 待实施标准 |
| 证据 | [阶段 4 独立准入](../reviews/iterative-governance-reliability-stage4-readiness-review-20260906.md) |
| 复核者 | /root/iterative_stage4_gate |

## 独立复核记录

| 日期 | 类型 | 阶段 | 结论 | 证据 | 复核者 |
|---|---|---|---|---|---|
| 2026-09-06 | 独立设计准入与交付复核 | 阶段 0 | 通过，达到阶段 0 待实施标准，阶段 0 设计交付完成；阶段 1 尚未准入 | [独立复核报告](../reviews/iterative-governance-reliability-stage0-readiness-review-20260906.md) | /root/iterative_stage0_gate |
| 2026-09-06 | 独立准入复核 | 阶段 1 | 通过，达到阶段 1 待实施标准 | [准入报告](../reviews/iterative-governance-reliability-stage1-readiness-review-20260906.md) | /root/iterative_stage1_gate |
| 2026-09-06 | 独立完成验收 | 阶段 1 | 未通过：D01 代码块中的下一动作被当成真实指令 | [第一轮完成复核](../reviews/iterative-governance-reliability-stage1-completion-review-20260906.md#第一轮未通过) | /root/iterative_stage1_acceptance |
| 2026-09-06 | 独立完成验收 | 阶段 1 | 通过：D01 可解除，阶段 1 完成验收通过；阶段 2 仍需自身 Step 0 与独立准入 | [第二轮完成复核](../reviews/iterative-governance-reliability-stage1-completion-review-20260906.md#第二轮通过) | /root/iterative_stage1_recheck |
| 2026-09-06 | 独立准入复核 | 阶段 2 | 通过，达到阶段 2 待实施标准 | [阶段 2 准入](../reviews/iterative-governance-reliability-stage2-readiness-review-20260906.md) | /root/iterative_stage2_gate |
| 2026-09-06 | 独立完成验收 | 阶段 2 | 通过，阶段 2 完成验收通过 | [阶段 2 完成报告](../reviews/iterative-governance-reliability-stage2-completion-review-20260906.md) | /root/iterative_stage2_acceptance |
| 2026-09-06 | 独立准入复核 | 阶段 3 | 通过，达到阶段 3 待实施标准 | [阶段 3 准入报告](../reviews/iterative-governance-reliability-stage3-readiness-review-20260906.md) | /root/iterative_stage3_gate |
| 2026-09-06 | 独立完成验收 | 阶段 3 | 通过，阶段 3 完成验收通过 | [阶段 3 完成报告](../reviews/iterative-governance-reliability-stage3-completion-review-20260906.md) | /root/iterative_stage3_acceptance |
| 2026-09-06 | 独立准入复核 | 阶段 4 | 通过，达到阶段 4 待实施标准 | [阶段 4 准入报告](../reviews/iterative-governance-reliability-stage4-readiness-review-20260906.md) | /root/iterative_stage4_gate |
| 2026-09-06 | 独立完成验收 | 阶段 4 | 未通过：D02/D03 实际阻塞 | [第一轮未通过](../reviews/iterative-governance-reliability-stage4-completion-review-20260906.md#第一轮未通过) | /root/iterative_stage4_acceptance |
| 2026-09-06 | 独立修复重审 | 阶段 4 | D02/D03 已解决，D04 阻塞最终验收 | [第二轮修复复核](../reviews/iterative-governance-reliability-stage4-completion-review-20260906.md#第二轮修复复核) | /root/iterative_stage4_recheck |
| 2026-09-06 | 独立修复确认 | 阶段 4 | D04 已解决，仍待最终完成验收 | [D04 独立确认](../reviews/iterative-governance-reliability-stage4-completion-review-20260906.md#d04-独立修复确认) | /root/iterative_stage4_recheck |
| 2026-09-06 | 独立完成验收 | 阶段 4 及全计划 | 通过，可关闭；348 项 Python/92.97%、99 项 Node，D02—D04 独立修复确认 | [第二轮通过](../reviews/iterative-governance-reliability-stage4-completion-review-20260906.md#第二轮通过) | /root/iterative_stage4_recheck |

## 未决问题

| 问题 | 推荐方案 | 是否阻塞当前阶段 | 状态 |
|---|---|---|---|
| B01 阻塞事实源、冲突及历史缺失如何统一？ | 沿用地图索引/计划细节权责，任何明确阻塞不因投影缺失被清空，冲突可见；见技术收敛 | 否 | 已收敛 |
| B02 workset 输出与默认/严格退出码如何兼容？ | 用户已确认兼容组合；保留现有字段，用既有枚举表达诊断，严格禁止误放行；见技术收敛 | 否 | 已收敛 |
| B03 关键漏检是否已形成可执行命令入口基线？ | 十一类 Python CLI 入口回放为阶段 0 替代基线，真实文件系统及 Node 全链路为阶段 1 Step 0；见样本文件 | 否 | 已收敛 |
| C01 阶段 1 真实文件系统基线和扩展反例是否齐全？ | 已完成 22 类实盘基线及修复后预期矩阵，见阶段 1 行为契约；独立准入已通过 | 否 | 已收敛 |
| D01 代码块中的下一动作示例误读 | 四类回归及独立完成重审通过，见第二轮完成复核；失败历史保留 | 否 | 已解决 |
| C02 阶段 2 统一验证集合与完整失败矩阵如何固定？ | 已固定严格治理 → pytest → Node 的统一入口、完整矩阵和恢复责任；见阶段 2 行为契约，独立准入已通过 | 否 | 已收敛 |
| C03 阶段 3 文档职责和三类任务如何验收？ | 用户已确认按需独立契约；源码/独立走读/内存基线与完整矩阵已齐全，本阶段独立准入已通过 | 否 | 已收敛 |
| C04 可选范围绑定如何减少噪声并避免漏检？ | 用户已确认 opt-in；完整行投影、必要上游全文、显式文件及生命周期边界见阶段 4 行为契约；独立准入通过 | 否 | 已收敛 |
| D02 不可读取快照目录被当作空集合 | 显式枚举及真实 000/0300 检查、创建零写入经第二轮独立确认 | 否 | 已解决 |
| D03 混合旧/新替代链读取外部 symlink | legacy/purpose-only × 计划/地图四场景读取 spy 为零，经第二轮独立确认 | 否 | 已解决 |
| D04 混合旧快照普通文件不可读时异常退出 | 独立 8 子进程确认可见诊断、绑定报告及替代记录保持；140 项定向回归通过 | 否 | 已解决 |

## 风险和回滚

- 解析规则收紧可能误伤历史文档：保留旧样本对照，先明确 warning/error 分层，再修改实现；兼容失败时停止该阶段。
- 工作集动作或迭代分流可能被误当实施授权：所有动作建议都受实际准入与已有授权约束，复核失败时不能自行放行。
- 不同计划修改同一规则源可能产生漂移：在实际写入前划分所有权和次序，先同步计划再实施，不全局扩大 drift 覆盖。
- 本轮按已准入阶段推进；撤销时只逆向移除本阶段精确变更，保留其他未提交内容。实现按阶段差异回滚，保留失败证据和独立复核历史。
- 若独立复核不可用、超时或失败，保留阶段阻塞；不得以本轮文档校验或范围核对充当准入通过。

## 关联 ADR、迁移、spec 或 issue

当前没有为本计划新建 ADR、迁移或 spec；只有阶段设计形成持久决策、真实迁移或跨迭代契约时才按需创建。既有计划关联统一见 [与既有计划的边界](#与既有计划的边界)。

## 提交范围

2026-09-06，用户最终明确要求提交工作区全部改动，包括本轮优化与简单改动自验约定、宿主调度及回放记录、既有 0.3.5 版本/发布维护记录、后续减负计划和审计文档。本次只进行本地 Git 提交；提交既有版本记录不代表再次发布，也不改变各计划当前状态或独立复核结论。

项目复核约定在 AGENTS 中自包含，CLAUDE 引用它。最终暂存按完整工作区取值，前面用于尝试分片提交的隔离快照不作为此次提交内容；验证以完整工作树既有独立结果及提交前身份、差异和治理检查为准。
