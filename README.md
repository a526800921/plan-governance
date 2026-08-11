# plan-governance

`plan-governance` 是一套面向个人或小团队的轻量计划治理机制。

它不是任务清单，也不是完整项目管理系统。它解决的问题是：当一个任务跨阶段推进、影响公共契约、依赖真实反馈，或会和已有计划发生依赖/替代/冲突时，如何避免计划漂移、旧决策被覆盖、阶段边界失控和完成证据缺失。

## 什么时候使用

适合启用治理的信号：

- 跨阶段、里程碑或多轮会话。
- 涉及架构、公共 API、Schema、兼容性或迁移行为。
- 后续需要真实运行报告、样本或反馈。
- 多个计划之间存在依赖、替代、重叠或冲突。
- 同一模块会被多个后续计划反复修改。

不适合启用治理的场景：

- 一次性 bugfix。
- 小范围本地修改。
- 互不依赖的待办列表。
- 不影响公共契约的普通实现任务。

## 需求探索与 grilling

对可能进入治理、但目标、边界、验收或关键取舍尚未收敛的任务，`plan-governance` 会优先使用可用的 `grill-me` 进行需求探索：高影响事项存在关键不明确内容时触发，或同时存在至少两项需求不确定性信号时触发。每次只推进一个问题；可从仓库和工具查证的事实先查证，决策由用户确认。

结束时应由用户确认结构化总结：目标、范围和非目标、已确认事实、暂定假设、候选方案、未决问题和下一步验证。只有需要治理的任务才把该摘要写入专项计划的 `需求探索` 章节；它不替代 Step 0 或阶段准入，也不会自动生成 ADR。未安装 `grill-me` 时保持在澄清/设计边界，不伪造访谈完成。

## 文档结构

最小结构：

```text
docs/
  PLAN_MAP.md
  plans/
    <plan-name>.md
```

按需增加：

```text
docs/
  adr/
    0001-<decision>.md
  migrations/
    <migration-name>.md
```

文档权责：

| 文档 | 权威内容 |
|---|---|
| `docs/PLAN_MAP.md` | 计划索引、状态、依赖、替代/合并/废弃关系、推荐顺序、阻塞项、证据链接 |
| `docs/plans/*.md` | 单个计划的目标、阶段、当前步骤、字段方案、Schema、枚举、Step 0 证据、验证方式、完成条件 |
| `docs/adr/*.md` | 关键架构决策、备选方案和后果 |
| `docs/migrations/*.md` | 兼容策略、迁移步骤、回滚方式和旧行为保留窗口 |

## 多文档同步

- 专项计划是实施细节事实源，记录字段方案、Schema、枚举、Step 0 证据、验证方式和完成条件。
- `docs/PLAN_MAP.md` 是状态、依赖、替代/合并/废弃关系、推荐顺序、阻塞项和证据链接的事实源。
- 总路线图、优先级计划和索引只记录顺序、状态摘要和专项计划链接，不复制字段级方案、枚举、Step 0 细节或完成定义。
- 当专项计划的状态、字段方案、完成条件或验证结果变化时，必须同步 `docs/PLAN_MAP.md` 和所有引用该计划的路线图、优先级计划或索引。
- 验收治理文档时，必须用 `rg` 搜索同名计划、P 编号、状态名和关键字段，检查是否存在重复定义或漂移。
- 如果同一事实在多个文档中重复，保留一个事实源，其他文档改为链接引用。

## 草案和历史文档

启用治理后，已有草案、历史设计、归档计划、临时分析文档等默认只作为背景材料，不再作为规范事实源。

- 新发生的目标、范围、公共契约、字段、Schema、状态语义、阶段、验证方式、完成条件、风险和回滚，应写入 `docs/plans/*.md`、ADR、migration 或正式 spec。
- 计划状态、依赖、替代/合并/废弃关系、推荐顺序、阻塞项和证据链接，应写入或同步 `docs/PLAN_MAP.md`。
- 不要为了“保持一致”而修改草案或历史文档；除非用户明确点名该文件，否则草案只在治理文档中作为背景材料引用。
- 验收时应搜索并修正“草案为准”“以草案为事实源”“详见草案”等表达。

## 初始化

在目标项目根目录运行：

```bash
plan-governance-cli init \
  --root . \
  --plan api-compat-migration \
  --title "API 兼容性迁移" \
  --goal "分阶段完成 API 兼容性迁移" \
  --update-agent-rules
```

如尚未安装 CLI，先运行 `npm install -g plan-governance-cli`。初始化默认只创建治理文档和代理规则，不复制项目本地检查器。

这会创建：

```text
.git/
docs/PLAN_MAP.md
docs/plans/api-compat-migration.md
CLAUDE.md
AGENTS.md
```

其中检查器是 npm 包的内部运行资源；正常使用不需要在目标项目中创建 `scripts/check_plan_governance.py`。

如果目标目录还不是 Git 仓库，初始化流程会先执行 `git init`；已有 `.git/` 时会跳过，不重复初始化。

`--update-agent-rules` 会创建或更新 `CLAUDE.md` 和 `AGENTS.md` 中带标记的计划治理章节，只写稳定执行规则，不写具体计划内容。具体计划仍以 `docs/PLAN_MAP.md` 和 `docs/plans/*.md` 为准。

如果只需要更新单个入口，也可以使用：

```bash
--update-claude-md
--update-agents-md
```

默认不会覆盖已有文件。需要覆盖时显式加：

```bash
--force
```

## 更新已有项目

如果项目已经有 `docs/PLAN_MAP.md` 和 `docs/plans/*.md`，不要重新初始化计划文档。只更新代理执行规则时运行：

```bash
plan-governance-cli init \
  --root . \
  --update-agent-rules-only
```

如果只更新单个入口，可以使用 `--update-claude-md-only` 或 `--update-agents-md-only`。

如果要升级已有项目的辅助文件，刷新检查脚本并更新代理规则，但不覆盖 `docs/`，运行：

```bash
plan-governance-cli init \
  --root . \
  --upgrade-existing
```

`--upgrade-existing` 会：

- 按兼容模式覆盖更新项目中的 `scripts/check_plan_governance.py`
- 创建或更新 `CLAUDE.md` 和 `AGENTS.md` 中带标记的计划治理章节
- 保留已有 `docs/PLAN_MAP.md` 和 `docs/plans/*.md`
- 提示缺失的治理文档

新项目和日常升级不需要使用该兼容模式；优先使用全局 npm CLI。

## 检查

在仓库根目录运行：

```bash
plan-governance-cli check .
```

可选检查：

```bash
plan-governance-cli check . --drift
plan-governance-cli check . --pre-commit
plan-governance-cli check . --stale-days 10
```

`--drift` 会检查工作区变更是否被活跃计划的 `影响模块或文件` 覆盖；`--pre-commit` 会检查 staged 变更，便于用户手动接入 Git hook。两者只输出 `WARNING`，不改变退出码。活跃计划自身文件、`PLAN_MAP.md` 中可唯一归属的变更行和当前阶段 `### 阶段证据` 中声明的合法相对路径会自动覆盖；关闭窗口内，已完成计划自身也在本次变更中时，仅额外覆盖该计划自身和显式阶段证据。跨计划、非法路径或无法归属的变更继续告警。

全局 CLI 是推荐入口：

```bash
npm install -g plan-governance-cli
plan-governance-cli check . --strict-readiness
```

功能图谱校验和影响分析：

```bash
plan-governance-cli graph validate .
plan-governance-cli graph impact --from feature.model-lifecycle --depth 2 --format text .
plan-governance-cli graph impact --from feature.model-lifecycle --depth 2 --format json .
plan-governance-cli plan impact --input docs/graph/fixtures/plan-impact/model-lifecycle-api.json --format json .
plan-governance-cli graph code candidates --symbol APIHandler --kind class --format json .
plan-governance-cli graph code impact --repo modelpad --file Sources/ModelPadCore/API/APIServer.swift --symbol APIHandler --kind class --depth 2 --format json .
```

项目图谱固定放在 `docs/graph/functional.yaml`。CLI 只读，不修改 YAML、计划状态、计划正文或业务代码；图谱节点使用稳定 ID，证据使用 `kind/ref/locator`，代码对象使用带文件回退的 `code_refs`。影响分析默认两跳，按 `contains`、`orchestrates`、`exposes`、`implements`、`consumes`、`depends_on` 的契约方向传播，并输出最短路径、直接/间接分类和证据引用。代码候选命令根据 `file/symbol/kind` 搜索稳定锚点；多候选输出 `resolution: ask_user`，不自动写回。

`plan impact` 是计划治理的前置只读查询：输入文件声明 `graph_scope`、`change_kind`，默认只查询功能层；API 契约、数据、安全、外部边界或明确代码定位才升级到架构层或代码候选。输出查询层级、升级原因、行动分级、测试映射和未查询层级；失败不伪装成“无影响”，也不会触发 `gitnexus analyze`。

也可以不全局安装，直接使用锁定版本：

```bash
npx --yes --package plan-governance-cli@0.3.0 plan-governance-cli check . --strict-readiness
```

npm 包内部仍使用版本化的 Python 检查器，但用户不需要直接调用或复制该脚本。旧项目已有本地脚本时仍可保留作为兼容或回滚路径。

作用域匹配规则同样用于 `plan-governance-cli hook --event pre-write`：

- 优先提取列表项中的第一个反引号路径，例如 ``- `./scripts/`: 检查脚本``。
- 没有反引号时提取列表项的第一个纯文本 token，例如 `- README.md`。
- 匹配前会归一化前导 `./`、尾随 `/` 和重复斜杠。
- 支持文件精确匹配和目录前缀匹配。
- 不支持 glob、正则、否定规则或自然语言推断。

`--stale-days` 会检查活跃计划的 `最后更新` 日期是否超过阈值；省略数值时默认 10 天。停滞检测只输出 `WARNING`，不自动改变计划状态。

安装后的资源管理：

```bash
plan-governance-cli setup --target codex --dry-run
plan-governance-cli setup --target claude --dry-run
plan-governance-cli setup --target all
```

`setup` 只同步 npm 包 manifest 指定的 skill、代理元数据和模板文件；默认先用 `--dry-run` 查看差异，目标文件有本地修改时不会静默覆盖。检查器、初始化器和 hook runtime 由 npm 包内部调用，不复制到项目或 skill 目录。当前版本不自动安装 hook 配置。

初始化项目时使用包内初始化器：

```bash
plan-governance-cli init --root . --plan api-compat-migration --title "API 兼容性迁移" --goal "分阶段完成 API 兼容性迁移"
```

`init` 默认不复制项目本地 `scripts/check_plan_governance.py`；如确有兼容需要，才显式传递底层 `--copy-checker` 参数。

## Hook runtime

本仓库提供只读 hook runtime，供 Codex、Claude Code 或其他 Agent 的项目级 hooks 手动接入。脚本只输出短提示和检查结果，不修改治理文档，不更新 `最后更新`，不安装或修改全局配置。

```bash
plan-governance-cli hook --event session-start
plan-governance-cli hook --event pre-write --paths scripts/check_plan_governance.py
plan-governance-cli hook --event post-write --paths docs/PLAN_MAP.md
plan-governance-cli hook --event stop
```

事件语义：

- `session-start`：摘要活跃计划、当前阶段、最后更新、阻塞项和证据链接。
- `pre-write`：按活跃计划的 `影响模块或文件` 匹配路径，提示当前阶段门禁。
- `post-write`：写入 `PLAN_MAP.md` 或计划文档后，提示同步状态、证据、覆盖率和反向引用检查。
- `stop`：运行 `plan-governance-cli check .` 并转发结果；该事件是非阻塞提示，不实现强制 gate。

旧项目如果仍使用五列 `PLAN_MAP.md`，先显式迁移：

```bash
plan-governance-cli init --root . --migrate-plan-map-last-updated --last-updated-date 2026-07-05
```

不传 `--last-updated-date` 时使用当天日期。该迁移只修改 `docs/PLAN_MAP.md` 的计划索引表，不会自动改变计划状态。

当前检查项包括：

- `PLAN_MAP.md` 引用的计划文件是否存在。
- `docs/plans/*.md` 是否存在未登记到 `PLAN_MAP.md` 的孤立计划；孤立计划以 `WARNING` 提示，不阻断检查。
- 计划状态是否合法。
- 计划依赖是否存在环。
- 活跃计划正文中的计划引用是否与 `PLAN_MAP.md` 依赖列一致；不一致以 `WARNING` 提示。
- 多个活跃计划是否声明了相同的影响模块或文件；重叠以 `WARNING` 提示。
- 已完成计划是否有有效 Step 0 证据和验证方式；空章节或纯占位符不视为有效证据。
- 实施中计划是否依赖已替代、已合并或已废弃计划。
- 待实施或实施中计划是否仍有未解决的当前阶段阻塞项。
- 已完成计划是否有测试覆盖率证据。
- 计划索引是否包含合法的 `最后更新` 日期。
- `ERROR` 会导致检查失败；`WARNING` 用于提示需要人工复核但不改变退出码的风险。

计划停滞检测使用计划索引中的 `最后更新`，不推断文件修改时间。

已完成计划修改检测需要完成快照或 hash 等独立元数据；当前版本不锁定已完成计划文件，避免修正文档错误时产生误报。公共契约变化关联验证需要计划文档提供结构化目标文件声明；当前版本不做 spec diff 强校验。

## 完成快照

已完成计划可以显式创建完成快照，用于后续发现未复核修改。快照文件写入 `docs/attestations/<plan-name>.json`，包含计划文件和 `docs/PLAN_MAP.md` 的 SHA-256。

```bash
plan-governance-cli check . --attest agent-runtime-integration
plan-governance-cli check . --check-attestations
```

`--attest <plan-name>` 只接受已登记到 `docs/PLAN_MAP.md` 的计划。`--attest-purpose <purpose>` 可与它一起创建带 `purpose`、`snapshot_id`、`supersedes` 和 `review_status` 的关系快照，支持 `phase_completion`、`release_gate`、`compliance`；不传时保持旧 `docs/attestations/<plan-name>.json` 格式。`--supersedes <path>` 和 `--review-status <status>` 可声明替代目标和初始复核状态。`--check-attestations` 会检查 hash 漂移并派生 `current`、`superseded` 或 `needs_review`；旧 JSON 缺少 `purpose` 时按 `phase_completion` 兼容读取。漂移、缺失或 JSON 损坏默认输出 `WARNING`，严格模式才将新增结构错误提升为 `ERROR`。人工确认文档修正合理后，可以重新创建旧快照或用 `--attest-purpose` 创建带替代关系的新快照。

## 测试覆盖率

本项目使用 `pytest` 和 `pytest-cov` 作为测试与覆盖率门禁。首次运行前安装开发依赖：

```bash
python3 -m pip install -r requirements-dev.txt
```

运行测试：

```bash
python3 -m pytest
```

覆盖率规则定义在 `pyproject.toml`：

- 统计 `scripts/` 下的 Python 代码。
- 开启分支覆盖率。
- 总覆盖率低于 85% 时测试失败。
- CI 会同时运行测试覆盖率检查和计划治理检查。

## 状态

统一使用中文状态：

| 状态 | 含义 |
|---|---|
| `候选` | 记录了想法，但尚未承诺实施 |
| `设计中` | 正在明确范围、契约和门禁 |
| `待实施` | 当前阶段门禁已通过，但尚未开始 |
| `实施中` | 当前阶段正在修改代码或文档 |
| `已完成` | 实现、测试、证据和文档已同步 |
| `已替代` | 被另一个计划取代 |
| `已合并` | 并入另一个计划 |
| `已废弃` | 明确不再推进 |

### 阶段准入

计划级 `状态` 和 `当前阶段` 由 `docs/PLAN_MAP.md` 维护；专项计划维护当前阶段的准入摘要和独立复核证据。阶段 N 完成后，阶段 N+1 默认保持 `设计中`，不能直接标记为 `待实施`。

进入 `待实施` 前，当前阶段必须有明确目标/范围、Step 0 基线、样本或替代基线矩阵、可执行验证方式、失败与回滚边界、无未解决阻塞项，以及最新独立准入复核“通过”。复核记录追加保留，`PLAN_MAP.md` 只链接最新有效结论。

机器识别的结构化章节标题固定为 `阶段路线图`、`当前阶段`、`阶段准入摘要`、`最新独立准入复核`、`独立复核记录`，不要在这些标题中插入或添加 `阶段 1` 等编号；阶段编号由 `PLAN_MAP.md` 的当前阶段提供。严格检查发现常见编号变体时，会在输出中给出直接修正提示。

阶段准入严格检查命令为 `--strict-readiness`。默认检查先以 `WARNING` 提示历史文档中的机械缺陷；严格模式才返回非零退出码。该检查只判断结构化准入条件，不替代业务验收。

## Codex 使用方式

如果已经安装本地 Codex skill，可以在对话中触发：

```text
$plan-governance 为这个项目初始化计划治理，计划名是 api-compat-migration，标题是 API 兼容性迁移。
```

或继续推进已有计划：

```text
$plan-governance 继续推进 docs/plans/api-compat-migration.md 的当前阶段，完成后记录验证证据。
```

skill 只负责让 Codex 按流程工作；真实计划状态仍然保存在项目仓库的 `docs/` 中。

## 核心规则

- 普通任务直接做，不引入治理。
- 当前阶段写细，后续阶段写粗。
- 实施前先固定 Step 0 证据。
- 决策、计划、契约和证据各有权威位置，不重复定义同一事实。
- 路线图和优先级计划只保留排序、状态摘要和链接，不复制专项计划细节。
- 验收治理文档时必须做反向引用检查。
- 验收者不得仅依据计划状态、完成证据文字或文档格式判定完成；必须基于当前仓库内容、可复现验证命令和反向引用检查独立确认。
- 启用治理后，旧草案停止承载新规范；后续需求默认进入治理文档。
- 如果新信息改变计划顺序、公共契约、兼容承诺或完成条件，先更新治理文档，再继续实施。

完整设计见 [plan-governance-design.md](plan-governance-design.md)。
