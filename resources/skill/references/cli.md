# CLI 操作

只读规则入口：`plan-governance-cli guide [overview|planning|migration|verification|cli]`。缺省 overview；`guide --help` 列用法。五主题从同一包根读取本入口及参考，任意 cwd 可用且无需 Python。正文中的相对文档链接在 CLI 环境通过对应 guide 主题读取，不相对当前项目查找。

成功退出 0；未知主题、多余参数退出 2；缺失/不可读/空资源退出 1 并报错。不下载、安装、修改项目或回退别的版本。skill/CLI 来源按入口一次选定：开发本 skill 用仓库源与对应 CLI，其他项目用安装资源。出现内容变化或能力缺口时再核对，版本号相同不证明资源一致。

已安装 skill 不等于 CLI 存在；既无 skill 也无 CLI 时说明治理前提缺失，仅阻塞依赖治理规则的工作，不自动安装。CLI 不支持新策略或 guide 时明确能力缺失，按授权更新。仅需阅读规则不调用 init/setup。

## 当前工作集

`plan-governance-cli workset . --json --plan <ID>` 派生会话聚焦计划及必要前置/共享约束；未传 plan 时派生当前计划、阶段、阻塞、下一动作、并行提示和最近证据；加 `--strict-readiness` 对活跃计划的机械缺陷返回非零。它不写计划、不自动执行动作、不替代授权或业务验收，也不自动核对快照和环境漂移。恢复先读工作集与相关当前记录，必要时再展开原计划。

1.0.1 起，恢复阅读可显式用 `workset . --json --evidence-limit 3`，按原追加顺序显示每个计划末尾三条记录。N 必须为正整数且仅适用于 workset JSON；默认仍返回完整记录。限量模式的 `recent_evidence_window` 提供 `total`、`omitted` 和原文 `source`（实际 `path`/`section`；无法确认时为 null），不改变完整数据派生的阻塞、动作、诊断或退出码。没有记录章节时 section 为 null。

限量窗口不等于完整验收证据；有阻塞、缺关键上下文或需要复核结论时，按 source 回查，或去掉 `--evidence-limit` 读取完整记录。`--include-history` 仍只控制是否纳入历史计划。普通文本不显示记录表，不需要此参数；旧 CLI（包括 1.0.0）不支持限量时，继续用完整输出，按已获授权更新版本。

同一项目多会话并行时，各会话根据当前任务明确自己的已登记计划 ID，并在 check/workset/hook 中重复传入同一组 `--plan ID`。焦点不保存为全项目可变状态；未知/重复 ID 返回 2，多个候选不能靠路径匹配自动归属。未设置焦点的 session-start 仅列轻量索引并提示选择，不能据此判断所有计划准入。

聚焦 workset 的 `plans` 只包含请求对象，schema 1 原字段保留，新增 `scope` 列出请求阶段、实际检查范围、必要前置、证据引用、共享写入和 `facts_version`。必要前置按显式依赖和适用阶段 hard_gate 展开；evidence/soft_context 和同文件写入只带入相关约束，其他计划的业务阻塞不会混入当前任务。历史来源阶段只凭有效的该阶段记录判通过，不用上游后续阶段替代。相关事实在本次读取期间改变时返回 unknown，严格模式失败；无关地图行更新不使焦点失效。facts_version 只是读取版本，写入前须重读相关事实并自行安排单一写入者、串行合并或 worktree。

`--plan` 是调用方明确传入的信息范围；工具无法从聊天 ID 自动知道 AI 的任务。宿主没有传入焦点时不能声称已经隔离。必要输入不可读、索引身份不可信等运行/文档错误返回 1；普通工作集的业务阻塞仍是成功查询 0，严格模式为 1。

## 分发与资源

`plan-governance-cli setup --target codex --dry-run` 预览主治理 skill 的同步差异，manifest 包含入口、按需参考、代理元数据和模板。迁移规则位于主 skill 的 `references/migration.md`，可通过 `plan-governance-cli guide migration` 按需读取；不会注册第二个 migration skill。`--destination DIR` 指定主 skill 目标目录。实际覆盖需既有用户授权并按 setup 冲突提示处理，不自动清理目标之外的用户目录。setup 只支持 Codex 单目标同步；项目初始化器只维护 `AGENTS.md`。项目升级不迁移旧计划，受管块外内容必须保持。

仅更新计划格式不等于更新项目入口。已有项目在任务交接、没有进行中的实施或复核时更新受管入口；升级不批量回写历史，旧策略名和六列格式按 verification 解释为默认自验，保留真实历史发现。安装副本与仓库开发规则有差异时说明本次选用来源，不能因版本号相同就混读正文。

项目受管入口只保留规范发现、授权、计划定位和必要CLI约束；复核策略、阶段门及记录细节引用同源 verification/planning/cli，不在入口重复维护。

升级分三层：npm 安装更新 CLI 与包内资源，`setup` 更新用户目录 skill，项目的 `AGENTS.md` 则由 `init --update-agent-rules-only` 单独刷新。前两步不会自动更新各项目。已有地图的 `check`（含聚焦/严格模式）会只读对比 AGENTS 受管块与所用工具自带规则：`AGENT_RULES_DRIFT` 表示内容不同，可能过期或含定制，核对后可执行诊断给出的刷新命令；仅忽略换行方式和行尾空白，受管块外自定义内容不参与比较。无文件/无受管标记时跳过，代码围栏中的示例标记不算入口。

受管标记缺失配对、重复或倒序报告 `AGENT_RULES_INVALID`，先人工核对；显式入口刷新也在写入前拒绝这些损坏标记，并保留围栏中的示例及受管块外原文。读取失败、非 UTF-8、非普通文件或符号链接报告 `AGENT_RULES_UNAVAILABLE`，明确未完成核对。三类诊断均为项目级 advisory/WARNING，严格模式也不提升为业务错误，不改变 workset 的阶段判断或自动覆盖文件；原有业务错误照常失败。复制到项目的单文件 checker 只能比较其自身版本规则，不能发现线上最新版本。

## 初始化、模板和检查脚本

- `../assets/PLAN_MAP.template.md`：治理入口模板。
- `../assets/plan.template.md`：计划文档模板。
- `../assets/adr.template.md`：可选 ADR 模板。
- `../assets/migration.template.md`：可选迁移模板。
- `scripts/init_plan_governance.py`：初始化 Git 仓库、`docs/PLAN_MAP.md` 和首个 `docs/plans/YYYYMMDD/<plan>.md`；检查器仍读取旧式根目录计划。也可升级已有项目的代理规则和检查脚本。
- `scripts/check_plan_governance.py`：检查状态、最后更新、计划链接、依赖、阻塞项、完成证据、测试覆盖率证据，并提供可选漂移、pre-commit、停滞和 attestation 生命周期检查。
- `scripts/plan_governance_hook.py`：只读 hook runtime，可由项目级 Agent hooks 手动调用；只输出短提示和检查结果，不修改治理文档、不更新状态、不安装 hooks。

初始化一个项目：

```bash
plan-governance-cli init \
  --root . \
  --plan api-compat-migration \
  --title "API 兼容性迁移" \
  --goal "分阶段完成 API 兼容性迁移" \
  --copy-checker \
  --update-agent-rules
```

新计划仅允许 候选/设计中，phase 必须是阶段身份。初始化先预检全部可预测目标冲突和模式参数，再执行 `git init` 和写入；已有 `.git/` 时跳过。升级/入口-only/迁移模式拒绝无关参数。

地图正文只维护在同包 `assets/PLAN_MAP.template.md`，初始化器渲染日期路径、计划行和分类占位符；模板缺失、空、占位符错误或基本索引结构损坏时，在任何项目写入前失败，不回退内嵌旧模板。该能力不重排已有地图，入口-only/升级模式也不依赖地图模板。

只更新已有项目的代理规则，不修改 `docs/`：

```bash
plan-governance-cli init \
  --root . \
  --update-agent-rules-only
```

升级已有项目的辅助文件，刷新 `scripts/check_plan_governance.py` 和 `AGENTS.md`，但不覆盖 `docs/` 或其他代理入口：

```bash
plan-governance-cli init \
  --root . \
  --upgrade-existing
```

旧项目如果 `docs/PLAN_MAP.md` 仍是五列表，显式迁移为包含 `最后更新` 的六列表：

```bash
plan-governance-cli init \
  --root . \
  --migrate-plan-map-last-updated \
  --last-updated-date 2026-07-05
```

不传 `--last-updated-date` 时使用当天日期。该迁移只修改 `docs/PLAN_MAP.md` 的计划索引表，不自动改变计划状态。

在仓库根目录运行：

```bash
plan-governance-cli check .
```

普通 `check` 检查文档一致性：未完成阶段的真实业务阻塞、失败或准入材料缺口返回 WARNING/0，不表示可实施。`--strict-readiness` 对待实施/实施中计划实施门禁；显式 `--plan ID` 时也评估候选/设计中的当前阶段。已完成声明缺少证据或仍有当前阻塞/失败、身份/路径/日期/依赖环损坏、必要输入读取失败为 ERROR/1。合法未初始化目录普通 check 为 not_applicable/0，严格为 1；不存在或非目录 root 为 1。

```bash
plan-governance-cli check . --plan api-compat-migration --json
plan-governance-cli check --root . --plan api-compat-migration --strict-readiness
```

check JSON 的 `schema_version=1`，含 command、mode（consistency/readiness）、status（passed/warning/failed/not_applicable）、exit_code、scope、summary（errors/warnings）及 diagnostics；每条诊断提供 code、category、severity、plan、phase、message 和 sources。JSON stdout 只有结果对象；文本 ERROR 在 stderr，告警在 stdout。0 表示本次操作成功，1 为领域/运行失败，2 为语法、未知参数、漏值、重复单值或互斥组合错误；help 为 0。单个 root 可用位置参数或 `--root`，不能同时传。旧直接检查 root 入口输出弃用提示；未知裸命令不再猜成目录。

可选检查：

```bash
plan-governance-cli check . --drift
plan-governance-cli check . --pre-commit
plan-governance-cli check . --stale-days
plan-governance-cli check . --stale-days 10
```

- `--drift`：检查工作区变更是否被活跃计划的 `影响模块或文件` 覆盖；关闭窗口内，若已完成计划自身也在本次变更中，则额外覆盖该计划自身和 `阶段证据` 中的显式路径。
- `--pre-commit`：检查 staged 变更是否被活跃计划的 `影响模块或文件` 覆盖，可由用户手动接入 Git hook。
- drift 会自动覆盖活跃计划自身文件、`PLAN_MAP.md` 中可唯一归属的变更行和当前阶段 `### 阶段证据` 中声明的合法相对路径；关闭窗口内，已完成计划自身也在本次变更中时，仅额外覆盖该计划自身和显式阶段证据。跨计划、非法路径或无法归属的变更继续输出 `WARNING`。
- `--stale-days`：检查活跃计划是否超过阈值未更新；默认 10 天。
- 这些可选检查输出 `WARNING`，不改变退出码。
- `--attest <plan-name>`：检查失败时不写入任何快照；完成/发布目的还需目标当前阶段符合准入/完成事实，不因普通检查降级告警而放行。为已登记计划创建或覆盖 `docs/attestations/<plan-name>.json` 完成快照。
- `--attest-purpose <purpose>`：与 `--attest` 一起创建带 `purpose`、`snapshot_id`、`supersedes` 和 `review_status` 的关系快照；支持 `phase_completion`、`release_gate`、`compliance`。不传时保持旧 JSON 路径和格式。快照写入拒绝与 workset/plan/drift/pre-commit 混用；supersedes/review-status 须与 attest-purpose 一起使用。
- `--supersedes <path>`、`--review-status <status>`：创建关系快照时声明替代目标和初始复核状态。
- `--check-attestations`：检查完成快照中的计划文件和 `PLAN_MAP.md` hash 是否漂移，并派生 `current`、`superseded` 或 `needs_review`；旧 JSON 缺少 `purpose` 时按 `phase_completion` 兼容读取。漂移、缺失或 JSON 损坏默认只输出 `WARNING`，严格模式才将新增结构错误提升为 `ERROR`。
- `--attest-file <path>`：可重复，仅与 `--attest`、`--attest-purpose` 组合启用范围绑定；记录显式文件、目标及必要上游计划的实际内容和相关地图行。文件须为仓库内普通文件，不接受重复、目录、glob、越界或 symlink。无关地图更新不失效；相关内容改变/删除或绑定无效会要求复核，`--check-attestations --strict-readiness` 显式阻断。旧快照不回填、旧默认行为保持，CI/发布不自动开启此检查。
- 范围绑定取工作树字节，HEAD 只定位；未列新文件不自动发现，hash 不证明清单完整或独立验收。相关证据先定稿，再显式创建；复核后使用带绑定的新快照与 `--supersedes` 替代。无 binding 后继不能解除 binding 前驱的范围复核责任，后继漂移也不恢复前驱 current。

## 图谱与计划前置影响分析

当项目声明了功能图谱或架构图谱时，使用 npm CLI 的只读命令查询影响范围：

```bash
plan-governance-cli graph validate .
plan-governance-cli graph impact --from feature.model-lifecycle --depth 2 --format json .
plan-governance-cli graph code candidates --symbol APIHandler --kind class --format json .
plan-governance-cli graph code impact \
  --repo modelpad \
  --file Sources/ModelPadCore/API/APIServer.swift \
  --symbol APIHandler \
  --kind class \
  --format json .
```

计划前置分析使用计划输入文件：

```bash
plan-governance-cli plan impact \
  --input docs/graph/fixtures/plan-impact/model-lifecycle-api.json \
  --format json .
```

`plan impact` 默认只查询功能层；API 契约、数据迁移、安全、外部边界或明确要求代码定位时，才升级到架构层或代码层。输出包含查询层级、升级原因、影响节点、行动分级、测试映射和未查询层级。`graph validate`、`graph impact`、代码查询和 `plan impact` 全部只读，不修改 YAML、计划、代码或 GitNexus 索引；失败也不能被解释为“无影响”。

graph 命令拒绝未知/重复/漏值参数，depth 为 1–10 整数、format 为 text/json。候选 kind 为 class/function；指定 file 必须是 root 内存在的普通文件，缺失不会扩大到全仓库。外部 impact kind 支持 class/function/method，错误/空/非法响应返回 1；无候选和多候选仍为有效查询 0。

GitNexus 只在需要代码定位时使用。CLI 不自动执行 `gitnexus analyze`，也不自动写回 UID 或 YAML；候选映射由 LLM 依据文件、符号、类型和测试等证据确认，证据不足或存在多个合理候选时再请求用户确认。

`影响模块或文件` 的作用域匹配规则：

- `--drift`、`--pre-commit` 和 `plan_governance_hook.py --event pre-write` 使用同一语义；已完成计划的关闭窗口只适用于 drift/pre-commit，不扩大 pre-write 的活跃计划门禁。
- 优先提取列表项中的第一个反引号路径，例如 ``- `./scripts/`: 检查脚本``。
- 没有反引号时提取第一个纯文本 token，例如 `- README.md`。
- 匹配前归一化前导 `./`、尾随 `/` 和重复斜杠。
- 支持文件精确匹配和目录前缀匹配。
- 不支持 glob、正则、否定规则或自然语言推断。

只读 hook runtime 可手动接入项目级 Agent hooks：

```bash
plan-governance-cli hook --event session-start
plan-governance-cli hook --event pre-write --plan api-compat-migration --paths src/api.py
plan-governance-cli hook --event post-write --paths docs/PLAN_MAP.md
plan-governance-cli hook --event stop --plan api-compat-migration
```

该脚本不自动安装 `.codex/hooks.json` 或修改全局配置。`--paths` 仅适用于 pre-write/post-write，须在 root 内；路径匹配仅给候选，不授权接管。聚焦 pre-write 展示自己及相关共享约束。`stop` 使用同包检查器，领域告警/错误均为非阻塞提示 0，执行故障返回 1 并说明未完成检查；不依赖目标仓库的旧脚本。
