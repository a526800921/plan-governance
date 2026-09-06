# CLI 操作

只读规则入口：`plan-governance-cli guide [overview|planning|verification|cli]`。缺省 overview；`guide --help` 列用法。四主题从同一包根读取本入口及三参考，任意 cwd 可用且无需 Python。正文中的相对文档链接在 CLI 环境通过对应 guide 主题读取，不相对当前项目查找。

成功退出 0；未知主题、多余参数、缺失/不可读/空资源退出 1 并报错。不下载、安装、修改项目或回退别的版本。skill 环境按实际发现的安装目录读取同源资源，避免硬编码用户路径；存在 skill 与 CLI 多版本时选择一个规范来源并核对所需能力，版本号相同不证明资源一致。

已安装 skill 不等于 CLI 存在；既无 skill 也无 CLI 时说明治理前提缺失，仅阻塞依赖治理规则的工作，不自动安装。CLI 不支持新策略或 guide 时明确能力缺失，按授权更新。仅需阅读规则不调用 init/setup。

## 当前工作集

`plan-governance-cli workset . --json` 派生当前计划、阶段、阻塞、下一动作、并行提示和最近证据；加 `--strict-readiness` 对活跃计划的机械缺陷返回非零。它不写计划、不自动执行动作、不替代授权或业务验收，也不自动核对快照和环境漂移。恢复先读工作集与相关当前记录，必要时再展开原计划。

1.0.1 起，恢复阅读可显式用 `workset . --json --evidence-limit 3`，按原追加顺序显示每个计划末尾三条记录。N 必须为正整数且仅适用于 workset JSON；默认仍返回完整记录。限量模式的 `recent_evidence_window` 提供 `total`、`omitted` 和原文 `source`（实际 `path`/`section`；无法确认时为 null），不改变完整数据派生的阻塞、动作、诊断或退出码。没有记录章节时 section 为 null。

限量窗口不等于完整验收证据；有阻塞、缺关键上下文或需要复核结论时，按 source 回查，或去掉 `--evidence-limit` 读取完整记录。`--include-history` 仍只控制是否纳入历史计划。普通文本不显示记录表，不需要此参数；旧 CLI（包括 1.0.0）不支持限量时，继续用完整输出，按已获授权更新版本。

## 分发与资源

SKILL、三个 references、agents 元数据与 assets 由同一 npm 包的 manifest 分发。`plan-governance-cli setup --target codex|claude|all --dry-run` 查看同步差异；实际覆盖需既有用户授权并按 setup 冲突提示处理，不自动清理用户目录残留。项目升级不迁移旧计划，受管块外内容必须保持。

## 初始化、模板和检查脚本

- `../assets/PLAN_MAP.template.md`：治理入口模板。
- `../assets/plan.template.md`：计划文档模板。
- `../assets/adr.template.md`：可选 ADR 模板。
- `../assets/migration.template.md`：可选迁移模板。
- `scripts/init_plan_governance.py`：初始化 Git 仓库、`docs/PLAN_MAP.md` 和首个 `docs/plans/<plan>.md`；也可升级已有项目的代理规则和检查脚本。
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

如果目标目录还不是 Git 仓库，初始化流程会先执行 `git init`；已有 `.git/` 时跳过。

只更新已有项目的代理规则，不修改 `docs/`：

```bash
plan-governance-cli init \
  --root . \
  --update-agent-rules-only
```

升级已有项目的辅助文件，刷新 `scripts/check_plan_governance.py`、`CLAUDE.md` 和 `AGENTS.md`，但不覆盖 `docs/`：

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
- `--attest <plan-name>`：为已登记计划创建或覆盖 `docs/attestations/<plan-name>.json` 完成快照。
- `--attest-purpose <purpose>`：与 `--attest` 一起创建带 `purpose`、`snapshot_id`、`supersedes` 和 `review_status` 的关系快照；支持 `phase_completion`、`release_gate`、`compliance`。不传时保持旧 JSON 路径和格式。
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
plan-governance-cli hook --event pre-write --paths scripts/check_plan_governance.py
plan-governance-cli hook --event post-write --paths docs/PLAN_MAP.md
plan-governance-cli hook --event stop
```

该脚本不自动安装 `.codex/hooks.json` 或修改全局配置。`stop` 事件只做非阻塞提示，不实现强制 gate。
