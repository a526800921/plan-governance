# 计划：requirements-grilling-integration

## 背景

在真实需求交流的早期，目标、边界、验收口径和关键取舍常常尚未收敛。如果此时直接把讨论中的暂定方案当作可实施计划，后续发现假设不成立时就会产生不必要的实现回滚。

当前已安装的 `grill-me` 会转交给 `grilling`：后者要求一次只提出一个问题、优先自行查证可从环境获得的事实、将取舍交由用户决定，并在共同理解得到确认前不实施。该组合适合承担轻量的需求探索，但当前 `plan-governance` 的分发源、计划模板和生成的代理规则尚未定义何时自动使用它、何时结束，以及如何将已确认结论交接给专项计划。

本计划把 `grill-me` 纳入 `plan-governance` 的前置探索流程，目标是减少因未收敛需求造成的返工，同时不为普通小任务增加固定文档负担。

本计划依赖已完成的 [phase-entry-gate-hardening](phase-entry-gate-hardening.md)，复用其既有的计划状态、阶段准入和独立复核边界；也依赖 [plan-governance-distribution-setup](plan-governance-distribution-setup.md)，复用其 npm 资源清单、显式 skill 同步和用户目录保护契约。

## 目标

- 为“可能进入计划治理但需求尚不清晰”的任务定义可预测的 grilling 自动触发规则。
- 明确 grilling 的用户决策边界、结束条件和确认方式。
- 只在用户确认共同理解后，将结构化摘要写入专项计划的“需求探索”部分。
- 复用现有 `候选`、`设计中`、`待实施` 状态和阶段准入规则，不新增生命周期状态。
- 将规则、模板、初始化生成内容和 npm 分发资源保持一致，并验证 Codex skill 的显式同步路径。

## 非目标

- 不将 `grill-me` 或 `grilling` 打包、发布或安装为 `plan-governance-cli` 的资源；它们是独立的可选 companion skill。
- 不生成独立的访谈逐字稿、术语表或 ADR；稳定的架构决策仍按既有规则单独创建 ADR。
- 不让检查器用自然语言判断“是否应该 grilling”，也不把未运行 grilling 直接判作业务或阶段准入失败。
- 不为清晰的一次性修改强制访谈，也不让 grilling 取代 Step 0、样本矩阵、独立准入复核或业务验收。
- 不自动覆盖用户目录中的 skill；同步仍使用既有 `setup --dry-run`、冲突保护和显式 `--force` 边界。

## 不变量

- 可由环境、仓库或工具确认的事实必须先查证，不能把它们转化为用户决策问题。
- 产品取舍、外部承诺和不可逆选择由用户明确确认；沉默不等于确认。
- grilling 每次只推进一个问题；已不影响范围、契约、验收或风险的追问不得阻塞结束。
- 共同理解只在最终结构化摘要得到用户确认后成立；确认前不得实施，也不得把暂定内容写成规范事实。
- 需求探索的已确认结论写入 `docs/plans/*.md`；计划状态、当前阶段、最后更新和证据链接只写入 `docs/PLAN_MAP.md`。
- `候选` 表示尚未承诺的想法，`设计中` 包含需求探索和方案收敛；只有既有阶段准入规则满足后才能进入 `待实施`。
- `grill-me` 不可用时，Agent 必须说明依赖不可用并保持在澄清/设计边界，不能伪装为已完成 grilling 或静默实施。

## 影响模块或文件

- `resources/skill/SKILL.md`
- `resources/skill/assets/plan.template.md`
- `scripts/init_plan_governance.py`
- `tests/test_init_plan_governance.py`
- `tests/npm_cli.test.mjs`
- `README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `package.json`
- `docs/PLAN_MAP.md`
- `docs/plans/requirements-grilling-integration.md`
- 用户目录中由显式 `setup` 同步的 `plan-governance` skill（验证目标，不作为源文件）

## 公共契约变化

### 1. grilling 触发与跳过

`plan-governance` 首先沿用既有启用判定。对可能进入治理的任务，满足下列任一条件时自动调用可用的 `grill-me`：

1. 存在公共 API、Schema、迁移、兼容性或不可逆操作等高影响事项，且目标、边界、验收或关键取舍中至少一项未明确；
2. 下列不确定性信号中至少两项同时存在：目标/验收不清、范围/非目标不清、存在多个有实质取舍的方案、关键事实尚待查证、后续返工成本显著。

以下情况跳过自动 grilling：需求、影响范围和验收方式已明确的小范围任务；当前计划的已确认假设没有变化且当前阶段已通过准入；或用户明确要求直接按既有方案实施。用户仍可随时显式调用 `grill-me`。

### 2. 决策顺序与结束条件

grilling 必须一次只问一个问题，并按下列顺序优先解决：可查证事实、阻塞范围或契约的决策、验收口径、非阻塞风险。每个决策问题应给出推荐答案，但最终选择由用户确认。

会话在以下内容已形成结构化总结并获用户明确确认时结束：

- 目标、范围和非目标；
- 已确认事实与已作出的关键决策；
- 暂定假设及其验证方式；
- 未决问题及其阻塞级别；
- 候选方案的取舍或已选方案；
- 验收口径，以及进入 Step 0 或下一次探索的具体动作。

未决但不阻塞的问题必须保留，不得为了结束会话伪造结论。关键阻塞项未解决时，计划保持 `设计中`。

### 3. 专项计划交接

在用户确认共同理解后，若任务已满足或即将满足治理启用条件，专项计划增加 `## 需求探索`，并使用以下字段：

```markdown
## 需求探索

### 已确认事实

### 暂定假设与验证方式

### 范围与非目标

### 候选方案与取舍

### 未决问题

### 用户确认的探索结论
```

该章节是已确认需求探索结论的事实源，不保存完整访谈逐字稿。只有稳定的架构决定才另建 ADR；grilling 本身不自动创建 ADR。写入探索结论后，仍必须完成当前阶段自己的 Step 0、样本矩阵、验证方式、失败/回滚边界和独立准入复核。

### 4. 依赖可用性与分发

`plan-governance` 将 `grill-me` 视为可选 companion skill，不将它和 `grilling` 收入 npm manifest。运行环境声明这些 skill 可用时才自动调用；不可用时输出简短说明并维持在 `设计中` 或普通澄清流程。npm 包继续只分发 `plan-governance` 自身的规则、模板和运行脚本。

## 阶段路线图

| 阶段 | 目标 | 进入条件 | 验证方向 | 状态 |
|---|---|---|---|---|
| 阶段 0 | 冻结探索门契约、依赖边界和 Step 0 样本矩阵 | 当前 skill、模板、分发与 companion skill 现状已核对 | 反向引用、基线命令和独立准入复核 | 已完成 |
| 阶段 1 | 同步规则源、计划模板和初始化生成内容 | 阶段 0 通过，触发/结束/交接契约无阻塞项 | 生成器 fixture、规则源一致性、回归测试 | 已完成 |
| 阶段 2 | 验证打包、显式同步和真实需求探索交接 | 阶段 1 完成，npm 资源和模板已冻结 | npm 打包、临时 `setup`、治理检查、反向引用和独立验收 | 已完成 |

## 阶段 0 设计与完成记录

### 阶段 0 范围

阶段 0 只固定自动触发条件、共同理解的退出标准、专项计划交接字段、companion skill 缺失时的行为和验证矩阵。当前阶段不修改 skill、模板、初始化器、测试、npm 包或用户目录。

### 阶段 0 准入摘要

| 字段 | 内容 |
|---|---|
| 准入状态 | 已完成 |
| Step 0 | [阶段 0 Step 0 证据](#阶段-0-step-0-证据) |
| 样本矩阵 | [阶段 0 样本矩阵](#阶段-0-样本矩阵) |
| 验证方式 | [阶段 0 验证方式](#阶段-0-验证方式) |
| 失败/回滚边界 | [风险和回滚](#风险和回滚) |
| 当前阻塞项 | 无 |
| 最新独立准入复核 | [阶段 0 独立复核](#独立复核记录) |

### 阶段 0 实施步骤

1. 用本计划的公共契约核对 `grill-me`、`grilling`、当前 `plan-governance` 规则源和 npm 分发边界。
2. 完成阶段 0 样本矩阵的基线记录，并确认不新增生命周期状态、不将 companion skill 纳入 manifest。
3. 对阶段 0 进行独立准入复核；只有结论明确为“通过，达到 `待实施` 标准”后，阶段 1 才可开始。
4. 阶段 1 先更新 `resources/skill/` 与生成器，再用临时项目 fixture 验证新计划模板和代理规则。
5. 阶段 2 只在源资源和测试通过后验证 npm 打包、临时目标 `setup` 与文档反向引用；发布或覆盖真实用户目录需要另行显式授权。

### 阶段 0 Step 0 证据

基线类型为“现状快照与契约样本”。2026-07-19 已确认：

- `/Users/jafish/.codex/skills/grill-me/SKILL.md` 不再含 `disable-model-invocation`，且转交 `/grilling` 会话。
- `/Users/jafish/.codex/skills/grilling/SKILL.md` 要求一次只问一个问题、先查证可观察事实、由用户确认决策，并在共同理解前不行动。
- `resources/skill/SKILL.md`、计划模板、初始化器和 README 尚未包含 `grill-me`、`grilling`、`需求探索`、共同理解或暂定假设的交接规则。
- `resources/manifest.json` 只分发 `plan-governance` 自身资源；不包含 companion skill。
- `plan-governance-cli check . --strict-readiness` 输出 `计划治理检查通过。`；`npm test` 为 7 项通过；`python3 -m pytest` 为 87 项通过、总覆盖率 91.93%。

### 阶段 0 样本矩阵

| 样本/fixture | 输入或基线 | 可执行命令 | 预期结果 | 失败判定 | 输出位置 |
|---|---|---|---|---|---|
| 规则源缺口 | 当前 `resources/skill/`、生成器、README 与计划文档 | `rg -n 'grill-me|grilling|需求探索|共同理解|暂定假设' resources/skill scripts README.md docs/PLAN_MAP.md docs/plans` | 阶段 0 前仅本计划记录新契约，既有分发源尚无重复规则 | 分发源已存在未登记的冲突规则，或探索契约被复制到多个事实源 | 命令输出 |
| companion skill 行为 | 已安装的 `grill-me` 与 `grilling` | `sed -n '1,120p' /Users/jafish/.codex/skills/grill-me/SKILL.md`；`sed -n '1,220p' /Users/jafish/.codex/skills/grilling/SKILL.md` | 无自动调用禁用项；单问题、查证事实、用户决策和确认前不实施的边界存在 | companion skill 不可用、仍禁止模型调用，或关键行为与本计划冲突 | 命令输出 |
| 清晰小任务 | 目标、范围、验收均明确的局部修改 | 阶段 1 规则审阅 fixture | 不自动 grilling，不新增探索章节 | 对每个小任务强制访谈或生成计划 | 审阅记录/测试输出 |
| 模糊高影响任务 | API/Schema/迁移且边界或取舍未明确 | 阶段 1 规则审阅 fixture | 自动进入 grilling，保持 `设计中` 至用户确认摘要 | 未质询即实施，或把用户未确认建议写成事实 | 审阅记录/测试输出 |
| 环境可查证事实 | 仓库中已有接口、调用点或兼容样本 | 阶段 1 规则审阅 fixture | 先用工具查证，而非询问用户 | 将可验证事实误当产品决策问题 | 审阅记录/测试输出 |
| 交接与准入 | 已确认的探索摘要、仍缺 Step 0 的计划 | 临时项目 `init` fixture 与严格治理检查 | 摘要进入专项计划；计划仍保持 `设计中`，直至完成既有准入条件 | 探索确认被误当成 `待实施` 准入或自动创建 ADR | pytest/治理检查输出 |

### 阶段 0 验证方式

```bash
rg -n 'grill-me|grilling|需求探索|共同理解|暂定假设' \
  resources/skill scripts README.md docs/PLAN_MAP.md docs/plans
sed -n '1,120p' /Users/jafish/.codex/skills/grill-me/SKILL.md
sed -n '1,220p' /Users/jafish/.codex/skills/grilling/SKILL.md
plan-governance-cli check . --strict-readiness
npm test
python3 -m pytest
```

阶段 1 和阶段 2 的验证必须补充：生成/升级临时项目 fixture、规则源与安装目标关键词核对、`npm pack --dry-run --json`、临时 `setup --dry-run`、反向引用扫描和独立验收。

### 阶段 0 测试覆盖率

阶段 0 基线为 2026-07-19 的 `python3 -m pytest`：87 项通过，总覆盖率 91.93%，高于 85% 门禁。阶段 1 若修改初始化生成逻辑，必须新增或更新对应 fixture；阶段 2 的全量验收不得降低 85% 覆盖率门禁。

### 阶段 0 完成条件

- 自动触发、跳过、结束、用户确认、交接和 companion skill 缺失行为已在本计划中冻结。
- 没有新增状态枚举、独立逐字稿事实源、自动 ADR 或自动阶段推进。
- 当前基线命令、六类样本和失败判定可复现。
- 阶段 0 独立准入复核明确为“通过，达到 `待实施` 标准”。

## 阶段 0 完成证据

- 已从实际安装的 `grill-me` 与 `grilling` 读取规则：前者不再禁止模型调用；后者已具备单问题、先查证事实、用户决策及确认前不实施的边界。
- `rg -n 'grill-me|grilling|需求探索|共同理解|暂定假设' resources/skill scripts README.md` 无匹配，确认分发规则源尚未包含未登记的同类契约；`resources/manifest.json` 与 `package.json` 也未分发 companion skill，符合本计划的可选依赖边界。
- `plan-governance-cli check . --strict-readiness` 通过；`npm test` 7 项通过；`python3 -m pytest` 87 项通过，覆盖率 91.93%。
- 已独立核对公共契约、六类样本矩阵、失败判定和非目标；阶段 0 无未解决阻塞项。

## 阶段 1 实施与完成记录

### 阶段 1 范围

阶段 1 只同步阶段 0 已冻结的规则和模板入口：更新 npm 分发源 `resources/skill/SKILL.md`、按需保留的计划模板章节、初始化器生成的 `AGENTS.md`/`CLAUDE.md` 受管规则及相关说明和测试。实施发现初始化器内嵌另一份计划模板，因此本阶段将把初始化器改为读取同一份 `resources/skill/assets/plan.template.md` 并渲染运行时字段，消除双重模板事实源。该阶段同时将计划模板的独立复核表改为检查器可直接解析的顶级章节，避免新计划在严格准入时因标题层级而失效。阶段 1 不修改检查器准入语义、不分发 companion skill、不发布 npm 包，也不覆盖真实用户目录中的 skill。

### 阶段 1 准入摘要

| 字段 | 内容 |
|---|---|
| 准入状态 | 已完成 |
| Step 0 | [阶段 1 Step 0 证据](#阶段-1-step-0-证据) |
| 样本矩阵 | [阶段 1 样本矩阵](#阶段-1-样本矩阵) |
| 验证方式 | [阶段 1 验证方式](#阶段-1-验证方式) |
| 失败/回滚边界 | [风险和回滚](#风险和回滚) |
| 当前阻塞项 | 无 |
| 最新独立准入复核 | [阶段 1 独立准入复核](#最新独立准入复核) |

### 阶段 1 实施步骤

1. 在 `resources/skill/SKILL.md` 增加需求探索门：触发/跳过阈值、可用性检查、一次一问、用户确认、结束摘要和不替代既有准入的边界。
2. 在 `resources/skill/assets/plan.template.md` 增加标有“仅在触发 grilling 后保留”的 `需求探索` 可选章节；未触发时不要求创建或保留空章节。同时把“最新独立准入复核”和“独立复核记录”改为检查器可直接解析的顶级章节。
3. 让 `scripts/init_plan_governance.py` 从该资源模板渲染计划标题、目标、状态和当前阶段，移除内嵌的重复模板；在受管代理规则中同步同一执行边界，并更新 `README.md` 的简短使用说明。
4. 更新初始化器和资源包测试，覆盖新计划模板、生成的两类代理规则、已有项目升级不改 `docs/`、以及分发资源完整性。
5. 在临时项目验证初始化/升级输出，运行相关测试、全量测试、严格治理和反向引用检查；独立准入复核通过后，阶段 2 才可开始。

### 阶段 1 Step 0 证据

基线类型为“规则源快照与生成器 fixture”。2026-07-19 的现状为：

- `resources/skill/SKILL.md` 已定义治理启用和阶段准入，但不含 `grill-me`、`grilling`、`需求探索`、共同理解或暂定假设规则。
- `resources/skill/assets/plan.template.md` 没有探索章节，且以 `## 独立复核记录` 下嵌 `### 最新独立准入复核` 的标题层级组织复核表；严格检查器的 `markdown_section()` 会在下一个标题停止，因此不能读取该嵌套历史表。
- 初始化器的 `plan_content()` 另行内嵌计划正文，不读取上述资源模板；针对性测试已复现“资源模板已更新但 `init` 输出仍旧”的失败，必须收敛为单一模板事实源。
- `scripts/init_plan_governance.py` 的 `agent_rules_body()` 也不含上述探索契约。
- 现有 `tests/test_init_plan_governance.py` 已覆盖新计划模板的基础章节、`--update-agent-rules`、`--update-agent-rules-only`、`--upgrade-existing` 不覆盖 `docs/` 等稳定边界。
- 阶段 0 基线测试仍为 npm 7 项、Python 87 项通过，Python 覆盖率 91.93%。

### 阶段 1 样本矩阵

| 样本/fixture | 输入或基线 | 可执行命令 | 预期结果 | 失败判定 | 输出位置 |
|---|---|---|---|---|---|
| 规则源契约 | 更新后的 `resources/skill/SKILL.md` | `rg -n 'grill-me|需求探索|共同理解|一次只问一个问题|不替代.*Step 0' resources/skill/SKILL.md` | 触发、结束、交接和准入边界均存在且无开发机绝对路径 | 缺少任一边界、与本计划公共契约冲突或错误宣称必然可用 | 命令输出 |
| 新计划模板 | 临时 `plan-governance-cli init --root <tmp> --plan demo` | `rg -n '需求探索|已确认事实|暂定假设与验证方式|用户确认的探索结论|^## 最新独立准入复核$|^## 独立复核记录$' <tmp>/docs/plans/demo.md` | 初始化器渲染唯一资源模板，提供按需保留的探索字段和可被严格检查器直接解析的复核章节，不自动将探索当作准入完成 | 资源与 `init` 输出漂移、缺少字段、字段成为必填、复核标题仍嵌套，或生成独立逐字稿/ADR | pytest/临时目录输出 |
| 代理规则 | 临时 `--update-agent-rules-only` 输出的 `AGENTS.md` 与 `CLAUDE.md` | `rg -n 'grill-me|需求探索|共同理解' <tmp>/AGENTS.md <tmp>/CLAUDE.md` | 两个受管章节包含同一执行摘要，且不写具体计划事实 | 两个入口漂移、改写 `docs/` 或包含字段级重复定义 | pytest/临时目录 diff |
| 既有项目升级 | 含既有 `docs/PLAN_MAP.md` 和计划文件的临时目录 | `plan-governance-cli init --root <tmp> --upgrade-existing` | 更新辅助规则但保持 `docs/` 内容和 hash 不变 | 覆盖 `docs/`、丢失用户内容或改变计划状态 | pytest/临时目录 diff |
| 小任务边界 | 更新后的 skill 文本与规则审阅 fixture | 规则审阅与关键词反向引用 | 明确清晰小任务跳过 grilling，显式调用仍可用 | 把 grilling 变成每个任务的强制步骤 | 审阅记录 |

### 阶段 1 验证方式

```bash
python3 -m pytest tests/test_init_plan_governance.py --no-cov
npm test
python3 -m pytest
plan-governance-cli check . --strict-readiness
npm pack --dry-run --json
rg -n 'requirements-grilling-integration|grill-me|grilling|需求探索|共同理解|暂定假设' \
  resources/skill scripts README.md AGENTS.md CLAUDE.md docs/PLAN_MAP.md docs/plans
rg -n '草案为准|以草案为事实源|详见草案|draft is source|source of truth.*draft|以.*draft.*为准' \
  resources/skill scripts README.md AGENTS.md CLAUDE.md docs
```

临时项目 fixture 必须在阶段 1 实施前由测试固定；阶段 2 再验证实际包安装和 `setup --dry-run`。

### 阶段 1 测试覆盖率

阶段 1 涉及初始化器和测试，应保持 Python 全量覆盖率不低于 85%。新建或更新的断言应覆盖模板字段、两类代理规则和不覆盖 `docs/` 的边界；npm 资源测试必须继续覆盖 manifest 中的 skill 文件可读。

### 阶段 1 完成条件

- 规则源、计划模板、初始化生成规则和 README 使用同一触发、确认和交接契约。
- 模板的探索章节明确按需保留，未触发 grilling 的计划不被要求保留空内容；新计划的复核章节与严格检查器的顶级章节解析规则兼容。
- 初始化器与 npm 分发源使用同一计划模板资源，不再维护内嵌副本。
- companion skill 保持可选依赖；检查器和状态枚举未扩张，未自动创建 ADR 或推进阶段。
- 临时初始化/升级、相关测试、全量测试、严格治理、npm 打包清单和反向引用检查通过。
- 阶段 1 独立准入复核明确为“通过，达到 `待实施` 标准”。

## 阶段 1 完成证据

- `resources/skill/SKILL.md`、`README.md`、初始化器生成的 `AGENTS.md`/`CLAUDE.md` 已同步需求探索触发、单问题访谈、用户确认、专项计划交接和 companion skill 缺失边界。
- `resources/skill/assets/plan.template.md` 已增加按需保留的 `需求探索` 字段，并将 `最新独立准入复核` 与 `独立复核记录` 改为严格检查器可直接解析的顶级章节。
- 初始化器已从内嵌正文改为读取上述资源模板并替换标题、目标、状态与阶段字段；针对性测试曾稳定复现资源模板不进入 `init` 输出，修复后 27 项针对性 Python 测试通过。
- `node bin/plan-governance-cli.mjs init --root . --update-agent-rules-only` 已更新本仓库受管代理章节且未修改 `docs/`。
- 全量 `python3 -m pytest` 87 项通过，覆盖率 91.95%；`npm test` 7 项通过；严格治理检查、`npm pack --dry-run --json`（13 个生产资源）和 `git diff --check` 通过。

## 当前阶段

### 范围

阶段 2 验证阶段 1 资源在 npm tarball、临时安装和临时 Codex skill 目标中的可用性；同时验证从包内初始化器生成的计划仍使用唯一模板资源。当前阶段不发布 npm 包、不执行真实用户目录的 `setup --force`、不修改 companion skill，也不把模拟用例伪装为真实用户需求探索。

### 阶段准入摘要

| 字段 | 内容 |
|---|---|
| 准入状态 | 已完成 |
| Step 0 | [Step 0 证据](#step-0-证据) |
| 样本矩阵 | [阶段 2 样本矩阵](#阶段-2-样本矩阵) |
| 验证方式 | [验证方式](#验证方式) |
| 失败/回滚边界 | [风险和回滚](#风险和回滚) |
| 当前阻塞项 | 无 |
| 最新独立准入复核 | 通过，达到 `待实施` 标准（2026-07-19） |

### 实施步骤

1. 为临时 tarball 安装补充回归测试：调用安装后的 `init`，确认生成计划含需求探索字段和顶级复核章节，且不依赖开发机绝对路径。
2. 在临时 Codex destination 执行 `setup --dry-run` 与实际同步，确认清单资源一致、skill 包含需求探索规则且不复制 runtime 脚本；保留现有冲突保护测试。
3. 核对临时生成计划的探索字段只提供记录位置，不会把探索确认误当作 Step 0 或 `待实施` 准入。
4. 运行完整 npm/Python 测试、严格治理、打包清单、临时安装与反向引用检查；独立验收通过后关闭阶段 2。

### Step 0 证据

基线类型为“tarball 与临时目标快照”。阶段 1 已确认 `npm pack --dry-run --json` 包含 13 个生产资源，且 manifest 已列出 skill 模板；现有 npm 测试验证 tarball 可运行 `--help`、源仓库 `init` 可创建文档、临时 `setup` 可同步 skill，但尚未验证“安装后的 `init` 使用资源模板并生成需求探索字段”。

### 阶段 2 样本矩阵

| 样本/fixture | 输入或基线 | 可执行命令 | 预期结果 | 失败判定 | 输出位置 |
|---|---|---|---|---|---|
| 临时 tarball 初始化 | `npm pack` 产物安装到临时 prefix | 安装后运行 `plan-governance-cli init --root <tmp> --plan demo` | 生成计划含 `需求探索`、顶级复核章节和传入目标，且不含开发机绝对路径 | 安装后无法定位资源、输出仍为旧模板或泄漏开发机路径 | npm 测试输出/临时计划 |
| 临时 Codex 同步 | 空 destination | `setup --target codex --destination <tmp> --dry-run` 后实际同步 | dry-run 不写入；同步后 skill 含 grilling 规则且不含 `scripts/` | dry-run 写入、资源遗漏、旧规则或 runtime 副本出现 | npm 测试输出/临时目录 |
| 冲突保护 | 已修改的临时 `SKILL.md` | 再次 `setup`，不加 `--force` | 返回冲突且不覆盖本地修改 | 静默覆盖 | npm 测试输出 |
| 探索/准入边界 | 临时生成计划的探索字段 | `rg` 与严格治理 fixture | 只提供摘要字段；不自动产生 Step 0、ADR 或 `待实施` 结论 | 模板将探索内容误声明为阶段准入 | pytest/严格检查输出 |

### 验证方式

```bash
npm test
python3 -m pytest
node bin/plan-governance-cli.mjs check . --strict-readiness
npm pack --dry-run --json
rg -n 'requirements-grilling-integration|grill-me|grilling|需求探索|共同理解|暂定假设' \
  resources/skill scripts README.md AGENTS.md CLAUDE.md docs/PLAN_MAP.md docs/plans
rg -n '草案为准|以草案为事实源|详见草案|draft is source|source of truth.*draft|以.*draft.*为准' \
  resources/skill scripts README.md AGENTS.md CLAUDE.md docs
```

### 测试覆盖率

阶段 2 的新增 npm 测试必须覆盖安装后初始化和临时同步的实际资源路径。Python 全量覆盖率继续不得低于 85%；npm 测试必须保持全部通过。

### 阶段 2 完成条件

- 生产 tarball 的初始化器从包内资源生成含需求探索字段和顶级复核章节的计划，不依赖开发机绝对路径。
- 临时 `setup` 的 dry-run、同步和冲突保护均通过，且只同步 manifest 声明的 skill 资源。
- 探索字段不改变 Step 0、ADR、阶段状态或严格检查语义。
- 完整测试、严格治理、打包清单、反向引用和独立验收通过。

## 完成证据

- 已安装的临时 npm tarball 可执行 `init`，生成计划包含 `需求探索`、顶级 `最新独立准入复核` 章节和传入目标，且不含开发机绝对路径。
- 已安装 tarball 在临时 Codex destination 的 `setup --dry-run` 不写入，实际同步后包含 grilling 规则且不复制 `scripts/`；既有回归继续覆盖本地修改时的冲突保护。
- `npm test` 7 项通过；`python3 -m pytest` 87 项通过，覆盖率 91.95%；`node bin/plan-governance-cli.mjs check . --strict-readiness`、`npm pack --dry-run --json`（13 个生产资源）和 `git diff --check` 通过。
- 反向引用检查确认需求探索仅提供用户确认摘要的记录位置，不会自动创建 Step 0、ADR 或 `待实施` 结论。
- 用户明确要求发布后，已将当前资源发布为 `plan-governance-cli@0.2.4`；`npm view` 确认该版本存在且为 `latest`，`npm exec --yes --package plan-governance-cli@0.2.4 -- plan-governance-cli --help` 验证公共入口可运行。

## 最新独立准入复核

| 字段 | 内容 |
|---|---|
| 日期 | 2026-07-19 |
| 阶段 | 阶段 2 |
| 结论 | 通过，达到 `待实施` 标准 |
| 证据 | 阶段 2 Step 0、四类样本矩阵、验证方式、风险边界和零阻塞项已核对；现有 tarball 清单、npm/Python 基线和严格治理检查通过。安装后 `init` 资源路径的缺口已明确纳入本阶段首项回归测试。 |
| 复核者 | Codex 独立复核 |

## 独立复核记录

| 日期 | 类型 | 阶段 | 结论 | 证据 | 复核者 |
|---|---|---|---|---|---|
| 2026-07-19 | 阶段验收复核 | 阶段 0 | 通过 | 实际 companion skill、规则源/manifest 缺口、公共契约与六类样本矩阵核对；严格治理、npm 7 项、Python 87 项和 91.93% 覆盖率通过 | Codex 独立复核 |
| 2026-07-19 | 阶段准入复核 | 阶段 1 | 通过，达到 `待实施` 标准 | 阶段 1 目标、范围、非目标、Step 0、五类样本矩阵、验证方式、回滚边界和零阻塞项均已核对；严格治理和完整测试基线通过 | Codex 独立复核 |
| 2026-07-19 | 阶段设计更新复核 | 阶段 1 | 未通过 | 实施前发现计划模板的复核标题层级与严格检查器解析方式不兼容；已纳入阶段 1 范围和样本矩阵，需基于更新后范围重新独立准入复核 | Codex 独立复核 |
| 2026-07-19 | 阶段准入复核 | 阶段 1 | 通过，达到 `待实施` 标准 | 更新后的范围已包含模板复核章节兼容性；目标、范围、非目标、Step 0、五类样本矩阵、验证方式、回滚边界和零阻塞项完整，严格治理和完整测试基线通过 | Codex 独立复核 |
| 2026-07-19 | 阶段验收复核 | 阶段 1 | 通过 | 资源规则、唯一模板渲染、代理章节、README、27 项针对性测试、87 项全量测试/91.95% 覆盖率、npm 7 项、严格治理、打包清单和反向引用检查通过 | Codex 独立复核 |
| 2026-07-19 | 阶段准入复核 | 阶段 2 | 通过，达到 `待实施` 标准 | 阶段 2 的范围、非目标、tarball 与临时目标 Step 0、四类样本、验证命令、回滚边界和零阻塞项完整；安装后 `init` 资源路径缺口已被明确纳入首项回归测试，现有 tarball 清单、npm/Python 基线和严格治理检查通过 | Codex 独立复核 |
| 2026-07-19 | 阶段验收复核 | 阶段 2 | 通过 | 已安装 tarball 的 `init` 和临时 Codex `setup` 回归通过；dry-run 不写入，实际同步不复制 runtime 脚本，冲突保护保留；npm 7 项、Python 87 项/91.95%、严格治理、13 个生产资源、反向引用和格式检查通过 | Codex 独立复核 |
| 2026-07-19 | 发布后验收复核 | 整个计划 | 通过 | `plan-governance-cli@0.2.4` 已发布到公共 npm registry 并成为 `latest`；指定版本查询和 npx 入口运行通过 | Codex 独立复核 |
| - | - | - | - | - | - |

## 未决问题

| 问题 | 推荐方案 | 是否阻塞当前阶段 | 状态 |
|---|---|---|---|
| companion skill 不可用时是否实现内置等价访谈？ | 不实现；明确报告不可用并保持在澄清/设计边界，避免复制另一套 skill | 否 | 已决定 |
| 是否新增 `探索中` 生命周期状态？ | 不新增；用 `候选` 表达未承诺想法，用 `设计中` 承载 grilling 与方案收敛 | 否 | 已决定 |
| 是否自动创建 ADR 或保存逐字稿？ | 不自动创建；只将用户确认的结构化摘要写入专项计划，稳定架构决定再建 ADR | 否 | 已决定 |
| npm 包是否分发 companion skill？ | 不分发；继续通过 manifest 仅管理 `plan-governance` 自身资源 | 否 | 已决定 |
| 是否需要为缺少 grilling 记录增加严格检查器错误？ | 不需要；触发判断依赖语义和运行时可用性，不适合机械强制 | 否 | 已决定 |

## 风险和回滚

- 自动触发过于频繁会增加交流摩擦：通过高影响加不确定性、或至少两个不确定性信号的阈值收敛；清晰小任务显式跳过。
- grilling 可能无限延长：以结构化总结与用户确认作为结束条件，非阻塞问题记录后不再阻塞。
- 暂定内容可能被误固化：确认前不实施、不写入规范事实；确认后也明确区分事实、假设和未决问题。
- companion skill 在其他环境缺失：不伪造调用结果，不自动实施；保留普通澄清和 `设计中` 边界。
- 分发或同步失败：阶段 2 先在临时目标 dry-run 和冲突保护下验证；真实用户目录不在本计划中自动覆盖，失败时保留原资源。

回滚只撤销新增的规则、模板字段和生成内容；不改变既有计划状态、严格检查语义、已完成计划的完成快照或用户目录中的未授权文件。

## 关联 ADR、迁移、spec 或 issue

- 无。当前是工作流与文档模型升级，不涉及需要持久化的独立架构决策或兼容迁移。
