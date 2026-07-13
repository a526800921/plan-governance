# 计划：plan-governance-distribution-setup

## 背景

`plan-governance-cli` 已经可以通过公共 npm 包统一执行版本化的 Python 检查器，但当前 npm 包只包含 CLI 启动器和 `check_plan_governance.py`。Codex 与 Claude Code 仍分别从用户目录加载 skill，初始化脚本、模板和 hook runtime 也没有统一的 npm 分发入口。

本计划不把所有资源复制到每个项目。npm 包作为版本化分发载体：检查和初始化所需的脚本作为包内运行资源，skill 通过显式 `setup` 同步到 Agent 的用户目录，未来 hook 通过明确的安装目标接入；普通 `check` 不自动修改本地文件。

## 目标

- 扩展 `plan-governance-cli`，让 npm 包携带版本化的 skill、初始化脚本、模板和可选 hook 资源。
- 增加显式 `setup` 入口，将包内 skill 同步到 Codex 和 Claude Code 的目标目录。
- 增加 `init` 入口，调用包内初始化逻辑创建或升级项目治理结构，默认不复制项目本地检查器。
- 保持检查脚本集中在 npm 包内部运行；不再因为 `setup` 把 `check_plan_governance.py` 分散复制到项目。
- 为未来 hook 接入保留资源清单和目标适配边界，但不在本计划中自动修改未知的全局 hook 配置。

## 非目标

- 不重写 Python 检查器、初始化器或 hook runtime 为 Node.js。
- 不让 `check`、`setup` 或 npm 安装过程隐式覆盖用户 skill、项目文档或 hook 配置。
- 不自动扫描并修改所有项目；项目治理文档迁移仍由显式 `init` 或独立迁移计划负责。
- 不猜测 Codex、Claude Code 或其他 Agent 的未公开 hook 配置 Schema。
- 不在本计划中实现复杂插件市场、远程更新服务、回滚数据库或多用户权限系统。

## 不变量

- npm 包是资源版本的唯一分发源；安装或更新 npm 包本身不直接修改用户目录。
- 检查脚本和初始化脚本由 CLI 从包内路径调用，不回退到开发机源码路径。
- `setup` 只写入明确支持的目标目录，默认提供 dry-run 或差异预览，并保留失败时的回滚边界。
- skill 同步不会改变治理规则；资源内容必须与包版本一一对应。
- hook 只有在存在明确的目标文件、命令契约和回滚方式时才允许进入实施；没有目标契约时只保留扩展点。

## 影响模块或文件

- `package.json`
- `package-lock.json`
- `bin/plan-governance-cli.mjs`
- `resources/skill/`
- `resources/hooks/`
- `scripts/check_plan_governance.py`
- `scripts/init_plan_governance.py`
- `scripts/plan_governance_hook.py`
- `tests/`
- `README.md`
- `docs/plans/plan-governance-distribution-setup.md`

## 公共契约变化

在现有检查入口之外增加显式子命令：

```bash
plan-governance-cli check [root] [options]
plan-governance-cli setup [--target codex|claude|all] [--dry-run] [--force]
plan-governance-cli init [root] [options]
```

兼容约束：

- 当前的 `plan-governance-cli [root] [options]` 继续等价于 `check [root] [options]`，不强迫现有项目立即改命令。
- `setup` 默认目标为明确列出的 Agent 目录，不根据模糊环境变量推断写入位置。
- `--force` 只在用户显式指定时覆盖目标资源；默认检测目标文件是否发生本地修改并停止或给出差异。
- `init` 默认调用包内 `init_plan_governance.py`，不传 `--copy-checker`；如需本地副本必须显式选择并记录兼容理由。
- `setup` 不自动安装 hook；hook 子命令或选项只有在阶段 0 固定目标契约后才能进入公共 API。

## 阶段路线图

| 阶段 | 目标 | 进入条件 | 验证方向 | 状态 |
|---|---|---|---|---|
| 阶段 0 | 冻结资源清单、目标路径和覆盖契约 | 已确认 npm 包与 Codex/Claude 资源现状 | hash、包内容、目标目录、运行时和回滚基线 | 已完成 |
| 阶段 1 | 将 skill、初始化器和模板纳入 npm 包 | 阶段 0 独立准入通过 | `npm pack`、临时安装、资源清单和脚本回归 | 已完成 |
| 阶段 2 | 实现 `setup` 和 `init` 显式入口 | 阶段 1 包内资源验证通过 | dry-run、目标同步、覆盖保护、初始化和回滚 | 已完成 |
| 阶段 3 | 评估并接入稳定的 hook 目标 | 阶段 2 完成且存在明确 hook Schema | hook fixture、安装/卸载、非阻塞行为和回滚 | 已完成 |

## 阶段 0 设计记录

### 范围

阶段 0 只盘点现有资源和目标路径，冻结最小分发契约，不修改 skill、npm 包、用户目录或项目文件。

### 阶段 0 历史准入摘要

| 字段 | 内容 |
|---|---|
| 准入状态 | 已完成 |
| Step 0 | [阶段 0 Step 0 证据](#阶段-0-step-0-证据) |
| 样本矩阵 | [阶段 0 样本矩阵](#阶段-0-样本矩阵) |
| 验证方式 | [阶段 0 验证方式](#阶段-0-验证方式) |
| 失败/回滚边界 | 阶段 0 不写入运行时资源；无法确认目标路径、资源 hash 或覆盖边界时停留在设计中 |
| 当前阻塞项 | hook 目标配置 Schema 尚未确认；不阻塞 skill 与 init 的前两阶段，但阻塞 hook 实施 |
| 最新独立准入复核 | [阶段 0 最新独立验收](#阶段-0-最新独立验收) |

### 阶段 0 样本矩阵

| 样本/fixture | 输入或基线 | 可执行命令 | 预期结果 | 失败判定 | 输出位置 |
|---|---|---|---|---|---|
| Codex skill | `~/.codex/skills/plan-governance` 当前资源清单和 hash | `rg --files ~/.codex/skills/plan-governance`、`shasum -a 256 ...` | 记录可分发文件和稳定目标目录 | 漏记资源、路径不可写或 hash 不可复现 | 本计划 Step 0 证据 |
| Claude skill | `~/.claude/skills/plan-governance` 当前资源清单和 hash | `rg --files ~/.claude/skills/plan-governance`、`shasum -a 256 ...` | 确认与 Codex 的共用资源和差异 | 目标结构不一致或存在未解释漂移 | 本计划 Step 0 证据 |
| 当前 npm 包 | `plan-governance-cli@0.1.1` 仅包含 CLI、README 和检查器 | `npm pack --dry-run --json` | 明确新增资源清单和包体边界 | 误把测试、attestation 或项目文档打入生产包 | npm 输出 |
| 初始化资源 | 源仓库 `scripts/init_plan_governance.py`、`assets/` 和模板 | `python3 -m pytest tests/test_init_plan_governance.py` | 确认初始化器的相对路径和资源依赖 | 包内运行依赖开发机路径或测试回归 | pytest 输出 |
| hook 现状 | 源仓库 `scripts/plan_governance_hook.py`，当前无 plan-governance 专属目标配置 | `rg -n "plan_governance_hook|hooks\.json|hooks" . ~/.codex ~/.claude` | 记录已有调用方式和缺失的目标契约 | 把未知配置误当成可直接安装契约 | 本计划 Step 0 证据 |

### 阶段 0 实施步骤

1. 盘点 Codex、Claude Code 和源仓库的资源清单、hash、权限与相对路径依赖。
2. 确认 npm 包内资源布局，区分“包内执行资源”和“需要同步的用户资源”。
3. 确认 `setup` 的目标选择、dry-run、覆盖保护和回滚边界。
4. 确认 `init` 的参数透传和默认不复制本地检查器的行为。
5. 对 hook 只记录现状和阻塞条件，不在目标契约未冻结前实现安装。
6. 完成独立准入复核，明确阶段 1 是否达到 `待实施` 标准。

### 阶段 0 Step 0 证据

- Codex 与 Claude 的 `SKILL.md` SHA-256 均为 `d8f928ff386435aec7b10da64e0e27be739f0fee44679a9d1c3cc28fb7ab6e05`，当前内容一致。
- 两个 skill 目录均包含 `SKILL.md`、`agents/openai.yaml`、四个模板资源和 `scripts/check_plan_governance.py`、`scripts/init_plan_governance.py`；当前没有随 skill 目录分发的 `plan_governance_hook.py`。
- 源仓库另有 `scripts/plan_governance_hook.py`，SHA-256 为 `30316621935095cc3f8d079b3b4817db5179ac46c54c01f03784f667ae0435d9`，但尚未绑定到 Codex 或 Claude 的 plan-governance 安装目标。
- 当前 `plan-governance-cli@0.1.1` tarball 只有 `README.md`、启动器、`package.json` 和 `scripts/check_plan_governance.py`，没有 skill、初始化器、模板或 hook 资源。
- 当前 npm 包已公开发布并支持全局安装；阶段 0 的新增工作是资源分发和显式 setup/init，不改变既有检查语义。

### 阶段 0 验证方式

- 运行资源清单和 hash 命令，确认 Codex/Claude 共用资源、差异资源和源仓库资源均有记录。
- 运行 `npm pack --dry-run --json`，确认生产包文件清单只包含计划内资源。
- 运行 `npm test`、`python3 -m pytest` 和 `python3 scripts/check_plan_governance.py . --strict-readiness`，确认基线没有回归。
- 使用 `rg` 搜索旧本地检查器调用、skill 目标路径、hook 目标和计划名，确认事实源未漂移。

### 阶段 0 测试覆盖率

阶段 0 不增加运行时代码；沿用 Python 全量测试 87 项、总覆盖率 91.93% 和 npm CLI 3 项测试作为替代基线。阶段 1 起新增资源打包和初始化入口测试。

### 阶段 0 完成条件

- skill、脚本、模板和 hook 的包内/同步边界已记录。
- Codex、Claude Code 的目标路径和覆盖保护规则已冻结。
- `init` 的默认行为不复制项目本地检查器，且回滚方式已记录。
- hook 未知契约被明确记录为阶段 3 阻塞项，没有提前实现隐式安装。
- `PLAN_MAP.md` 已同步计划状态、当前阶段、依赖、推荐顺序和证据链接。
- 阶段 0 独立准入复核通过，或明确记录阻塞项并保持阶段为 `设计中`。

### 阶段 0 最新独立验收

| 字段 | 内容 |
|---|---|
| 日期 | 2026-07-13 |
| 阶段 | 阶段 0 |
| 结论 | 通过，阶段 0 完成，并达到阶段 1 `待实施` 标准 |
| 证据 | Codex/Claude skill 资源清单与 hash 已核对；npm tarball 当前仅含 CLI 和检查器；初始化器相对路径与 hook 现状已核对；npm、Python 和严格治理基线通过 |
| 复核者 | Codex 独立复核 |

## 阶段 1 实施记录

### 范围

阶段 1 只把 skill、初始化器、模板和必要的包内资源纳入 npm tarball，不实现 `setup`、`init` 或 hook 安装行为，不修改用户目录。

### 阶段 1 历史准入摘要

| 字段 | 内容 |
|---|---|
| 准入状态 | 已完成 |
| Step 0 | [阶段 1 Step 0 证据](#阶段-1-step-0-证据) |
| 样本矩阵 | [阶段 1 样本矩阵](#阶段-1-样本矩阵) |
| 验证方式 | [阶段 1 验证方式](#阶段-1-验证方式) |
| 失败/回滚边界 | 包清单或相对路径验证失败时不发布；保留 `0.1.1` 作为 npm 回滚版本 |
| 当前阻塞项 | 无；hook 目标契约只阻塞阶段 3，不进入本阶段 |
| 最新独立准入复核 | [阶段 1 最新独立验收](#阶段-1-最新独立验收) |

### 阶段 1 样本矩阵

| 样本/fixture | 输入或基线 | 可执行命令 | 预期结果 | 失败判定 | 输出位置 |
|---|---|---|---|---|---|
| skill 资源包 | Codex/Claude 当前一致的 skill 目录 | `npm pack --dry-run --json` | tarball 含 manifest 指定资源，不含测试和 attestation | 资源缺失、重复或包外路径泄漏 | npm 输出 |
| 初始化器 | 源仓库 `scripts/init_plan_governance.py` 和 `assets/` | 临时安装后运行 `plan-governance-cli --help` 与初始化 fixture | 包内初始化器能定位模板，不依赖开发机路径 | 初始化器回退到源码仓库或失败 | 临时目录输出 |
| 检查器回归 | 当前 `plan-governance-cli@0.1.1` 行为 | `npm test`、`python3 -m pytest` | 原有 CLI 和 Python 测试保持通过 | 检查参数、输出或退出码变化 | 测试输出 |
| hook 边界 | 当前无 plan-governance 目标配置 | 包内容与资源 manifest 检查 | 本阶段不打包可自动安装 hook 配置 | 误把未知 hook 配置纳入生产资源 | 资源清单输出 |

### 阶段 1 实施步骤

1. 设计稳定的包内资源目录和 manifest，区分运行资源与待同步 skill 资源。
2. 将 Codex/Claude 共用 skill、初始化器和模板纳入包文件清单。
3. 修正包内初始化器的相对路径依赖，确保临时安装可运行。
4. 增加资源清单、临时打包安装和原有行为回归测试。
5. 完成本阶段独立验收后，才进入阶段 2 的 `setup`/`init` 实现。

### 阶段 1 Step 0 证据

- 阶段 0 已通过独立验收，并明确阶段 1 只处理 npm 资源打包，不修改用户目录。
- 当前 `npm pack --dry-run --json` 显示生产包只有 README、启动器、package 元数据和检查器，构成可对照的包内容基线。
- Codex 与 Claude skill 目录清单一致，`SKILL.md` hash 一致；初始化器依赖自身相邻脚本和源仓库 `assets/`，需要在阶段 1 用临时安装验证。

### 阶段 1 验证方式

- `npm pack --dry-run --json`：核对生产包资源清单。
- `npm pack` 后在临时目录安装：验证 skill、模板和初始化器只从包内路径读取。
- `npm test`、`python3 -m pytest` 和全局 CLI 严格检查：确认现有检查行为不变。
- `git diff --check` 和 `rg` 反向引用扫描：确认包文件、README、计划和路线图同步。

### 阶段 1 测试覆盖率

阶段 1 不改变 Python 治理逻辑；保留 Python 总覆盖率 91.93%，并新增 npm 资源清单、临时安装和初始化 fixture 测试。

### 阶段 1 完成条件

- npm tarball 包含 manifest 指定的 skill、初始化器和模板资源，不包含未授权的项目文档或 hook 配置。
- 临时安装后的资源定位不依赖开发机绝对路径。
- 原有 npm/Python 测试、参数透传、输出和退出码语义保持通过。
- 阶段 1 独立验收通过，并为阶段 2 建立 `setup`/`init` 的 Step 0 基线。

### 阶段 1 最新独立验收

| 字段 | 内容 |
|---|---|
| 日期 | 2026-07-13 |
| 阶段 | 阶段 1 |
| 结论 | 通过，阶段 1 达到完成标准 |
| 证据 | npm 包清单已包含 13 个计划内资源；npm 5 项测试、Python 87 项测试和严格治理通过；临时打包安装后的 CLI 运行通过 |
| 复核者 | Codex 独立复核 |

## 阶段 1 完成证据

- npm 包已加入 `resources/manifest.json`、Codex/Claude 共用 skill、四个模板、初始化器和 hook runtime；生产 tarball 共 13 个计划内文件。
- npm CLI 资源清单测试、临时打包安装测试和原有 CLI 测试共 5 项通过；Python 全量测试 87 项通过，总覆盖率 91.93%。
- 包内 skill 的初始化和检查命令已切换为 npm CLI 入口文本；本阶段没有修改 Codex/Claude 用户目录，也没有安装 hook。
- `python3 scripts/check_plan_governance.py . --strict-readiness`、`npm pack --dry-run --json` 和 `git diff --check` 通过。

## 阶段 2 实施记录

### 范围

阶段 2 实现 `setup` 和 `init` 两个显式入口：`setup` 同步 manifest 指定的 skill 文件，`init` 调用包内初始化器。检查脚本、初始化器和 hook runtime 继续留在 npm 包内，不复制到项目或用户 skill 目录。

### 阶段 2 历史准入摘要

| 字段 | 内容 |
|---|---|
| 准入状态 | 已完成 |
| Step 0 | [阶段 2 Step 0 证据](#阶段-2-step-0-证据) |
| 样本矩阵 | [阶段 2 样本矩阵](#阶段-2-样本矩阵) |
| 验证方式 | [阶段 2 验证方式](#阶段-2-验证方式) |
| 失败/回滚边界 | 默认 dry-run；目标文件有本地差异时不覆盖；初始化失败时不删除目标文件；保留 `0.1.1` 作为回滚版本，当前发布版本为 `0.2.2` |
| 当前阻塞项 | 无；hook 目标契约只阻塞阶段 3 |
| 最新独立准入复核 | [阶段 2 最新独立验收](#阶段-2-最新独立验收) |

### 阶段 2 样本矩阵

| 样本/fixture | 输入或基线 | 可执行命令 | 预期结果 | 失败判定 | 输出位置 |
|---|---|---|---|---|---|
| Codex 临时目标 | 空目录或已有相同 skill 文件 | `plan-governance-cli setup --target codex --destination <tmp> --dry-run` | 只报告待写入文件，不修改目标 | dry-run 写入或路径越界 | npm 测试输出 |
| Claude 临时目标 | 空目录或已有不同 skill 文件 | `plan-governance-cli setup --target claude --destination <tmp>` | 写入 manifest 文件，保护非 manifest 文件 | 覆盖未知文件或漏写资源 | npm 测试输出 |
| 覆盖保护 | 目标 `SKILL.md` 已被本地修改 | `plan-governance-cli setup --target codex --destination <tmp>` | 报告冲突并返回非零，不覆盖 | 静默覆盖本地修改 | npm 测试输出 |
| 初始化 fixture | 空 Git 项目目录 | `plan-governance-cli init --root <tmp> --plan demo` | 创建 docs 治理结构，不复制 `scripts/check_plan_governance.py` | 缺少文档或意外复制检查器 | npm 测试输出 |
| 回滚 | setup/init 中途失败的临时目标 | 失败 fixture 和目标文件快照对照 | 原有目标文件保持不变或可恢复 | 失败后留下半套资源 | npm 测试输出 |

### 阶段 2 实施步骤

1. 在 Node CLI 中增加子命令解析和包内资源 manifest 读取。
2. 实现 `setup` 的 target/destination、dry-run、冲突检测和原子写入。
3. 实现 `init` 对包内 `init_plan_governance.py` 的参数透传，默认不传 `--copy-checker`。
4. 增加临时目标、冲突保护、初始化和失败回滚测试。
5. 完成阶段 2 独立验收后，再评估阶段 3 hook 目标契约。

### 阶段 2 Step 0 证据

- 阶段 1 已完成并确认 npm tarball 能在临时目录运行，包内资源路径可被稳定定位。
- manifest 已冻结 Codex/Claude 默认目标目录及同步文件；运行资源和 hook 列表为空/不安装边界已记录。
- 当前两个真实 skill 目录均存在可写目标，但本阶段先使用临时 destination fixture，避免未经验证覆盖真实用户目录。

### 阶段 2 验证方式

- `npm test`：覆盖 `setup` 的 dry-run、目标同步、冲突保护和 `init` 参数透传。
- 临时目录执行 `npm pack`、安装和 CLI 子命令，确认不依赖源码仓库绝对路径。
- `python3 -m pytest`、严格治理检查、`npm pack --dry-run --json` 和反向引用扫描。

### 阶段 2 测试覆盖率

保留 Python 总覆盖率 91.93%；新增 Node CLI 子命令和文件同步行为测试，覆盖成功、dry-run、冲突和失败回滚路径。

### 阶段 2 完成条件

- `setup` 能按 manifest 将 skill 同步到 Codex/Claude 目标，默认 dry-run 并保护本地修改。
- `init` 能调用包内初始化器，默认不复制项目本地检查器。
- 临时安装、初始化、冲突保护和失败回滚测试通过，原有检查命令语义不变。
- 阶段 2 独立验收通过，并对阶段 3 hook 是否具备稳定目标契约作出结论。

### 阶段 2 最新独立验收

| 字段 | 内容 |
|---|---|
| 日期 | 2026-07-13 |
| 阶段 | 阶段 2 |
| 结论 | 通过，阶段 2 达到完成标准 |
| 证据 | `plan-governance-cli@0.2.2` 已发布；全局安装、setup 实际同步、二次 dry-run、全局 init、显式 check、npx 和 hook runtime 均通过；npm/Python 测试和严格治理通过 |
| 复核者 | Codex 独立复核 |

## 阶段 2 完成证据

- npm 包已升级并发布为 `plan-governance-cli@0.2.2`，registry 可查询版本和 tarball。
- `setup --target all --force` 已实际同步 Codex 与 Claude skill；随后 `setup --target all --dry-run` 对全部 manifest 文件报告为最新。
- `init --root ... --plan ...` 的全局 fixture 通过，创建治理文档且默认未复制项目本地检查器。
- `plan-governance-cli check`、旧的无子命令兼容入口、`npx --package plan-governance-cli@0.2.2` 和 `plan-governance-cli hook --event session-start` 均通过。
- 默认冲突保护、dry-run、临时安装、npm 7 项测试、Python 87 项测试和严格治理检查均通过。

## 阶段 3 评估记录

### 范围

阶段 3 只评估 hook runtime 是否具备可安全自动安装的目标契约，不猜测或修改 Codex/Claude 的全局 hook 配置。

### 评估结论

- `scripts/plan_governance_hook.py` 已作为 npm 包内 runtime 分发，并可通过 `plan-governance-cli hook` 显式调用。
- 现有 hook 配置属于其他工具或用户自定义配置；当前没有可由本包安全声明和维护的 plan-governance 专属安装 Schema。
- `resources/manifest.json` 的 `hooks` 保持空列表；`setup` 不修改 `~/.claude/settings.json`、未知 `.codex` 配置或其他全局文件。
- 因此本计划完成“可分发、可手动调用、不可隐式安装”的 hook 边界；未来若出现稳定 Schema，再另立专项计划实现安装/卸载。

### 阶段 3 完成条件

- hook runtime 可从 npm 包临时安装和全局安装后调用。
- 未知 hook 配置不会被自动写入或覆盖。
- hook 目标契约的缺失、影响和后续入口已记录。

## 后续阶段摘要

### 阶段 1：资源打包

将 `SKILL.md`、`agents/openai.yaml`、模板、初始化器及其必要资源纳入 npm 包。检查器、初始化器和 hook runtime 作为包内执行资源，不复制到项目；skill 资源以明确 manifest 管理。验证临时安装后不依赖开发机绝对路径。

### 阶段 2：setup 与 init

增加 `setup --target codex|claude|all [--dry-run] [--force]` 和 `init [root]`。`setup` 默认只同步 skill，先显示差异并保护本地修改；`init` 调用包内初始化器，默认不加 `--copy-checker`。两个入口都必须有临时目录 fixture 和失败回滚验证。

### 阶段 3：hook 评估

只有在实际目标工具提供稳定、可验证的 hook 配置契约后，才决定是否增加 `setup --hooks` 或独立 hook 子命令。hook 应调用全局 CLI 或包内入口，不重新分发 Python 副本；安装、卸载和失败行为必须保持显式、可回滚、非破坏性。

## 整个计划完成条件

- npm 包携带版本化 skill、初始化器、模板和 hook runtime，并能从包内路径运行。
- `setup` 能显式同步 Codex/Claude skill，默认 dry-run 并保护本地修改；`init` 默认不复制项目检查器。
- 检查脚本、初始化器和 hook runtime 不再作为新的项目或 skill 副本同步；hook 不自动修改未知全局配置。
- 公共 npm 发布、全局安装、临时安装、实际 skill 同步、初始化、检查、npx 和回滚边界均有可复现证据。

## Step 0 证据

- 阶段 0 记录了 Codex/Claude skill 资源清单与 hash、npm `0.1.1` 包内容、初始化器路径依赖和 hook 配置现状。
- 阶段 1 记录了 13 个 npm 资源的 tarball 清单；阶段 2 记录了全局安装、setup/init fixture、实际同步和 hook runtime 验证。

## 验证方式

- `npm test`、`python3 -m pytest`、`python3 scripts/check_plan_governance.py . --strict-readiness`、`npm pack --dry-run --json` 和 `git diff --check`。
- `npm view plan-governance-cli version dist.tarball --json`、全局 `setup`/`init`/`check`/`hook`、npx 严格检查和 Codex/Claude 二次 dry-run。
- `rg` 反向引用、绝对路径和草案事实源扫描，确认新资源不依赖开发机路径且路线图同步。

## 测试覆盖率

Python 全量测试 87 项通过，总覆盖率 91.93%；npm CLI 测试 7 项通过，覆盖资源清单、临时安装、setup dry-run、同步、冲突保护、init 和 hook 边界。

## 完成证据

- `plan-governance-cli@0.2.3` 已发布到公共 npm registry，并完成全局安装；该版本同步修正了 README、代理规则和 `init` 模板中的统一 CLI 入口。
- Codex/Claude skill 已通过 `setup --target all --force` 同步；二次 `--dry-run` 显示全部资源最新，且 skill 不再包含开发机绝对路径。
- `init` 默认创建治理文档但不复制 `scripts/check_plan_governance.py`；`hook` runtime 可显式运行，未安装未知 hook 配置。
- 计划、路线图、测试、发布版本、实际目标同步和独立验收记录已完成同步。

## 完成后的维护修正

2026-07-13 发现 `0.2.2` 的初始化器模板仍会在 `AGENTS.md` 和 `CLAUDE.md` 中写入旧的 Python 检查命令，形成 skill 与代理规则入口不一致。已将 README、当前代理规则和初始化器模板统一为 `plan-governance-cli check/init`，保留包内 Python 脚本作为运行资源和显式兼容模式，并发布 `0.2.3`。

## 独立复核记录

| 日期 | 类型 | 阶段 | 结论 | 证据 | 复核者 |
|---|---|---|---|---|---|
| 2026-07-13 | 阶段验收复核 | 阶段 0 | 通过 | Codex/Claude skill 清单与 hash、npm 包现状、初始化器路径、hook 现状以及 npm/Python/严格治理基线已核对 | Codex 独立复核 |
| 2026-07-13 | 阶段准入复核 | 阶段 1 | 通过，达到 `待实施` 标准 | 阶段 0 完成；阶段 1 资源清单、临时安装、初始化器和回滚边界已具备可执行验证方式 | Codex 独立复核 |
| 2026-07-13 | 阶段验收复核 | 阶段 1 | 通过 | 13 个 npm 资源、npm 5 项测试、Python 87 项测试、临时安装和严格治理通过 | Codex 独立复核 |
| 2026-07-13 | 阶段准入复核 | 阶段 2 | 通过，达到 `待实施` 标准 | setup/init 的目标、dry-run、冲突保护、初始化 fixture、失败回滚和 hook 边界已核对 | Codex 独立复核 |
| 2026-07-13 | 阶段验收复核 | 阶段 2 | 通过 | `plan-governance-cli@0.2.2` 发布、全局 setup/init/check/hook、npx、Codex/Claude 同步和全量测试通过 | Codex 独立复核 |
| 2026-07-13 | 阶段验收复核 | 阶段 3 | 通过 | hook runtime 可分发和手动调用；无稳定目标 Schema，因此 manifest 不安装 hook 配置 | Codex 独立复核 |
| 2026-07-13 | 最终验收复核 | 整个计划 | 通过 | npm 资源分发、skill 同步、init、检查、hook 边界、测试、registry 和反向引用检查通过 | Codex 独立复核 |
| 2026-07-13 | 完成后维护复核 | 整个计划 | 通过 | `0.2.3` 已发布；初始化器生成的代理规则、README 和当前项目入口均改用 npm CLI；生成器测试和治理检查通过 | Codex 独立复核 |
| - | - | - | - | - | - |

## 未决问题

| 问题 | 推荐方案 | 是否阻塞当前阶段 | 状态 |
|---|---|---|---|
| skill 是否需要按 Codex/Claude 分别维护资源？ | 共享同一份 skill manifest，只有实际差异才拆分目标覆盖层 | 否 | 已决定 |
| setup 默认是否覆盖用户已有 skill？ | 默认 dry-run/差异提示；仅 `--force` 覆盖 | 否 | 已决定 |
| hook 是否纳入首个 setup 版本？ | 不纳入首个 setup；等待明确目标 Schema 后进入阶段 3 | 是（仅阻塞阶段 3） | 已决定 |
| init 是否继续支持 `--copy-checker`？ | 保留底层 Python 参数兼容，但 npm `init` 默认关闭并要求显式选择 | 否 | 已决定 |

## 风险和回滚

- 用户目录存在本地修改：默认 dry-run 和差异检测，覆盖前保留可恢复边界；失败时不删除原目录。
- Codex/Claude 资源结构发生差异：使用共享 manifest 加目标覆盖层，无法匹配时停止，不静默写入相邻目录。
- npm 包内 Python 相对路径失效：用临时 tarball 安装和初始化 fixture 阻断发布。
- 初始化行为意外复制本地检查器：默认不传 `--copy-checker`，并用文件清单断言阻止项目出现副本。
- hook 配置契约不稳定：不自动安装，阶段 3 保持阻塞，不以猜测替代验证。

## 关联 ADR、迁移、spec 或 issue

- 依赖：[plan-governance-npm-cli](plan-governance-npm-cli.md)，提供公共 npm 包和全局 CLI 入口。
- 当前不新增 ADR 或 migration；阶段 2 如果涉及用户目录覆盖窗口或跨工具差异，再单独创建 migration 文档。
