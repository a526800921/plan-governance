# 计划：迁移流程按需引用与文档记录命名

## 背景

`plan-governance-migration` 目前作为独立 skill 注册在 Codex 目录中，但用户希望入口只保留 `plan-governance`，并在需要迁移存量计划时由主 skill 按需读取迁移规则。另一个需要落地的约定是为 `docs/reviews/`、`docs/data-quality/` 等历史记录建议日期前置文件名；当前检查器主要校验计划索引及计划结构，不强制这些目录的命名。

## 目标

- 将存量计划迁移步骤合并到 `plan-governance` 的按需参考中，不再单独分发或注册迁移 skill。
- 保留“只有用户明确要求才迁移”的授权边界，并在迁移规则中维护日期来源、路径引用、attestation、验证及回滚要求。
- 为 `reviews`、`data-quality` 等历史记录推荐日期前置命名；说明该命名属于建议而非 checker 门禁。
- 说明可复用 fixtures 和工具管理的 attestations 使用各自稳定规则，不按历史记录方式加日期前缀。
- 更新 npm CLI 文档与本机 Codex skill；不发布 npm 新版本。

## 非目标

- 不迁移其他项目或本仓库的计划、复核、数据质量记录。
- 不修改计划 checker 去强制校验非计划文档的文件名。
- 不运行测试套件、不发布 npm 包、不更改版本号。

## 需求探索

- 用户确认需要调整 skill，并明确要求迁移能力不要作为独立 Codex skill 注册，而由 `plan-governance` 提及并按需调用。
- 文件名中的日期放在前面。新建议以记录形成日期命名；既有文档仅在用户明确要求批量迁移或重命名时调整。

## 不变量

- 日常计划治理不会自行迁移或改名存量文件；只有用户明确提出时才执行。
- 日期取可核实的首次创建/记录日期；Git 首次添加记录优先，正文明确记载可作回退；不使用 mtime 或最后更新日猜测。
- 搬迁时保持文件内容、身份和证据结论，先列映射，修复受影响链接并检查 attestation；失败按映射回滚。
- 单独迁移规则只作为主 skill 的按需参考，不在 Codex skill 根目录生成第二个注册项。

## 影响模块或文件

- `resources/skill/SKILL.md`
- `resources/skill/references/planning.md`
- `resources/skill/references/migration.md`
- `resources/skill/references/cli.md`
- `resources/manifest.json`
- `resources/migration-skill/`
- `bin/plan-governance-cli.mjs`
- `package.json`
- `README.md`
- `docs/PLAN_MAP.md`
- `tests/npm_cli.test.mjs`（同步已有分发契约断言，不运行测试）
- `/Users/jafish/.agents/skills/plan-governance/`
- `/Users/jafish/.agents/skills/plan-governance-migration/`

## 公共契约变化

- npm 包 manifest 只分发和同步 `plan-governance` 一个 Codex skill；迁移规则作为该 skill 的 `references/migration.md`，CLI 可以通过 `guide migration` 按需读取。
- 命名建议：复核记录使用 `YYYYMMDD-<subject>[-stageN]-<review-type>[-rN].md`；数据质量记录使用 `YYYYMMDD-<subject>-<record-type>[-rN].<ext>`。阶段和修订标记按需增加。
- `docs/fixtures/` 中可复用样本优先按场景/版本命名；`docs/attestations/` 保持 CLI 管理；上述命名建议不作为 checker 的强制规则。

## 阶段路线图

| 阶段 | 目标 | 进入条件 | 验证方向 | 状态 |
|---|---|---|---|---|
| 阶段 1 | 合并按需迁移规则、补充记录文件命名建议，并同步本机 skill | 用户已授权调整 skill 和取消独立注册 | skill validator、CLI guide、治理检查、文档链接与目标目录核对 | 已完成 |

## 当前阶段

### 范围

更新仓库源、CLI guide/分发配置、README 和 PLAN_MAP 当前规则；把本机迁移 skill 目录移出 Codex 注册路径并保留可恢复备份；将更新后的仓库源同步到已安装的主 skill。npm CLI 的实现版本仅更新在仓库，未来发布前由后续发布流程纳入 npm 包。

### 阶段准入摘要

| 字段 | 内容 |
|---|---|
| 准入状态 | 已完成 |
| 复核策略 | 风险分流 |
| Step 0 | 本机存在主 skill 与独立迁移 skill；源 manifest 配置了 `additionalSkills`，README 和 CLI 帮助仍描述两个 skill。 |
| 样本矩阵 | 主 skill 入口、migration reference、manifest、setup/guide help、命名建议、备份与安装目录 |
| 验证方式 | `quick_validate.py`、`plan-governance-cli check .`、`git diff --check`、CLI guide/help 及文件/manifest 静态核对；不运行测试套件 |
| 失败/回滚边界 | 源文件调整可用 Git 回退；本机目录操作前备份两个 skill，若同步异常可从备份恢复 |
| 当前阻塞项 | 无 |
| 最新阶段复核 | [当前阶段复核](#最新阶段复核) |

### 实施步骤

1. 将独立迁移操作流程移入主 skill 的按需参考，并在入口和规划参考中链接；添加日期前置记录命名建议。
2. 移除 npm manifest 中第二个 skill 的注册/分发项，更新 CLI 帮助、guide 主题、README 和既有分发测试断言。
3. 备份本机两个 skill 目录，使用仓库源更新主 skill，将迁移 skill 目录移出 Codex skill 根目录。
4. 运行适用的 skill validator、治理检查及静态检查；记录 npm CLI 暂未发布的边界。

### Step 0 证据

- 源仓库初始 Git 工作区干净，当前版本为 1.2.0。
- `resources/manifest.json` 定义一个主 skill 和一个 `additionalSkills` 迁移 skill；`package.json` 将 `resources/migration-skill` 包含在 npm 文件列表内。
- CLI `setup --help`、README 分发说明和 `tests/npm_cli.test.mjs` 仍假设会同步两个 skill；CLI guide 目前有 overview、planning、verification、cli 四个主题。
- 本机 `/Users/jafish/.agents/skills/plan-governance-migration` 仅含 `SKILL.md` 和 `agents/openai.yaml`；主 skill 已安装。
- checker 在 `docs/PLAN_MAP.md` 中校验计划链接、状态、依赖、完成证据，并发现计划目录孤立文件；没有为 `docs/reviews/` 或 `docs/data-quality/` 定义文件命名强制规则。

### 阶段证据

- 迁移操作原文完整移入 `resources/skill/references/migration.md`；`SKILL.md` 和 planning reference 只在用户明确要求时引导读取，日常治理不会迁移文件。`guide migration` 能从包内输出该参考。
- planning reference 和 README 现建议复核、数据质量记录使用 `YYYYMMDD-` 日期前缀，并区分按场景/版本命名的 fixtures 和 CLI 管理的 attestations；明确 checker 不强制 reviews/data-quality 命名。
- manifest 不再声明 `additionalSkills`；`package.json` 不再包含 `resources/migration-skill`，原独立 skill 源文件已移除。setup help 说明只同步主 skill 及其按需参考和模板。
- 本机独立迁移 skill 已移出 `/Users/jafish/.agents/skills/`。主 skill 已由仓库源同步；安装目录的 `setup --dry-run` 全部显示“已是最新”。旧主 skill 和迁移 skill 备份位于 `/Users/jafish/.codex/backups/plan-governance-migration-reference-20260926/`，`SHA256SUMS` 全部通过。
- `quick_validate.py` 对仓库源和本机主 skill 均通过；CLI guide migration 和 setup help 可读取；CLI/现有测试文件语法检查与 `git diff --check` 通过。本阶段未运行测试套件，也未发布 npm。
- 最终 `plan-governance-cli check .` 通过，本计划无结构或准入警告。剩余 4 条 WARNING 是 `plan-governance-workflow-streamlining` 正文引用计划但依赖列未声明；实施期间两计划共同修改 README/manifest/CLI 的协调关系已写入 `PLAN_MAP.md`。

### 最近实施/验证记录

| 日期 | 类型 | 动作/结果 | 证据 | 状态 | 记录者 |
|---|---|---|---|---|---|
| 2026-09-26 | 阶段基线 | 确认独立 skill 分发配置、CLI 文档和本机注册目录现状 | [Step 0 证据](#step-0-证据) | 已记录 | Codex |
| 2026-09-26 | 实施与本机同步 | 迁移规则并入主 skill reference；更新命名建议、manifest、CLI、README 和本机安装；独立 skill 目录移入校验过的备份 | [阶段证据](#阶段证据) | 完成 | Codex |
| 2026-09-26 | 最终自验 | skill validator、CLI guide/setup dry-run、语法、空白、备份校验和 `plan-governance-cli check .` 通过；未运行测试套件或发布 npm | [阶段证据](#阶段证据) | 通过；保留既有跨计划 WARNING | Codex |

### 验证方式

- 使用 `$CODEX_HOME/skills/.system/skill-creator/scripts/quick_validate.py` 对主 skill 目录执行结构校验。
- 运行 `plan-governance-cli check .` 和 `git diff --check`。
- 静态核对 `guide migration` 输出、本机主 skill 文件同步、独立 skill 已不在 `~/.agents/skills/`，且备份存在。
- 按用户和仓库规则不运行测试套件，也不发布 npm。

### 用户可观察验收

| 场景 | 输入/前置 | 操作 | 可观察结果 | 验证证据 |
|---|---|---|---|---|
| 常规注册 | Codex skills 目录 | 检查技能目录 | 只存在 `plan-governance` 主治理入口，不单独出现迁移 skill | 本机目录清单 |
| 按需迁移 | 用户明确要求迁移存量计划 | 使用主 skill 查询迁移参考 | 主 skill 引导读取 migration 规则并遵守显式授权/验证边界 | `SKILL.md` 和 `guide migration` |
| 记录文件命名 | 新建复核或数据质量历史记录 | 按需创建记录 | 推荐格式以 `YYYYMMDD-` 开头；checker 未声明强制要求 | `planning.md`、CLI guide |

### 测试覆盖率

本阶段为 skill、文档和分发入口调整；代码覆盖率不适用。测试套件不运行，已有 npm CLI 测试中的分发断言仅同步为单 skill 契约。

### 完成条件

- 独立迁移规则完整进入主 skill 的按需参考，日常入口不会自动触发迁移。
- npm manifest、README、CLI guide/setup 帮助描述单 skill；本机迁移 skill 不再位于 Codex 注册目录。
- reviews/data-quality 日期前置命名建议、fixtures 与 attestations 的区别已说明，并明确 checker 不强制该命名。
- skill validator、治理检查和静态检查通过；本机备份可恢复；未发布 npm。
- `docs/PLAN_MAP.md` 同步状态和证据。

## 最新阶段复核

| 字段 | 内容 |
|---|---|
| 日期 | 2026-09-26 |
| 阶段 | 阶段 1 |
| 方式 | 自验 |
| 风险 | 低风险 |
| 风险依据 | skill 文档和可恢复的本地 skill 同步，无业务代码行为变化。 |
| 结论 | 通过：迁移内容只在用户明确要求时由主 skill 按需读取；单 skill manifest 与本机注册目录一致，推荐命名和 checker 边界说明清楚。 |
| 证据 | [阶段证据](#阶段证据)；skill validator、guide migration、setup dry-run、治理检查、备份校验 |
| 复核者 | Codex |

## 阶段复核记录

| 日期 | 类型 | 阶段 | 方式 | 风险 | 结论 | 证据 | 复核者 |
|---|---|---|---|---|---|---|---|
| 2026-09-26 | 普通自验 | 阶段 1 | 自验 | 低风险 | 通过：skill 结构及本机同步有效；独立迁移 skill 不再注册；文档和分发配置只保留主 skill 入口 | [阶段证据](#阶段证据) | Codex |

## 未决问题

| 问题 | 推荐方案 | 是否阻塞当前阶段 | 状态 |
|---|---|---|---|
| npm 包何时发布本次单 skill 分发改动？ | 后续用户明确要求发布时按发布计划执行；本次不发布。 | 否 | 已决定 |

## 风险和回滚

- 迁移目录操作前将主 skill 和独立迁移 skill 备份到 `~/.codex/backups/` 并生成校验清单；校验通过后才将原独立 skill 移出注册目录。
- npm registry 上的 1.2.0 仍包含旧 manifest；在新的 npm 版本发布前，已安装的全局 CLI 再次运行 `setup` 仍可能同步独立迁移 skill。本次只同步本机主 skill 并移出旧注册目录，没有更新全局 CLI，也没有发布 npm。

## 关联 ADR、迁移、spec 或 issue

- [原日期目录计划](plan-documentation-date-directories.md)记录此前把迁移流程做成独立 skill 的历史决定，本计划只记录后续用户提出的合并调整。
