# 计划：plan-governance-npm-cli

## 背景

当前计划治理检查器以 Python 脚本形式分散在部分项目中。目标不是重写检查逻辑，而是提供一个统一入口：npm 包携带版本化的 Python 检查器，由 Node.js 只负责定位并启动它。

这样项目可以统一使用：

```bash
npx --yes --package plan-governance-cli@0.1.1 plan-governance-cli . --strict-readiness
```

项目不再维护自己的 `scripts/check_plan_governance.py` 副本，也不依赖 `/Users/jafish/Documents/work/plan-governance` 这类开发机绝对路径。

## 目标

- 创建一个最小 npm CLI 包，暂定包名为 `plan-governance-cli`。
- 支持全局安装后直接调用：`npm install -g plan-governance-cli`。
- 原样转发现有检查器参数、输出和退出码。
- 将当前 Python 检查器作为 npm 包内资源分发，不重写为 Node.js/TypeScript。
- 用 `npm pack` 和临时安装验证包可离线运行、可定位包内脚本、不会依赖开发机路径。
- 提供从项目本地脚本切换到 npm CLI 的最小迁移方式。

## 非目标

- 不重构 Python 检查器。
- 不改变治理规则、Markdown 解析、计划状态或 `PLAN_MAP.md` 语义。
- 不增加配置系统、远程服务、GUI、机器可读协议或复杂发布流水线。
- 不一次性改造所有项目；只在包验证通过后处理实际使用本地检查器的项目。
- 不建设复杂的公共发布流水线；本计划直接完成一次公共 npm 发布和安装验证。

## 不变量

- npm CLI 必须使用包内携带的检查器，不回退到源码仓库或用户目录。
- CLI 参数保持兼容：根目录、`--strict-readiness`、`--stale-days`、`--drift`、`--pre-commit`、`--attest` 和 `--check-attestations`。
- Python 检查器返回的退出码和标准输出由 npm CLI 原样传递。
- npm 包版本是唯一分发版本；项目迁移前记录旧脚本基线，迁移失败时可通过版本控制恢复。

## 影响模块或文件

- `package.json`、`package-lock.json`：npm 包元数据和本地测试依赖。
- `bin/plan-governance-cli.mjs`：最小 Node.js 启动器。
- npm 包资源清单：携带 `scripts/check_plan_governance.py`。
- `tests/`：npm CLI 启动、参数转发、退出码和临时安装测试。
- `README.md`：增加最小调用方式和迁移说明。
- `docs/plans/plan-governance-npm-cli.md`：本计划事实源。

## 公共契约变化

新增一个 npm CLI 入口：

```bash
npx plan-governance-cli [root] [options]
```

全局安装入口：

```bash
npm install -g plan-governance-cli
plan-governance-cli [root] [options]
```

首版只增加包名和入口，不增加新的治理参数；所有已有参数直接传给包内 Python 检查器。Node.js 和 Python 的最低版本要求在阶段 0 风险验证后记录到 `package.json` 和 README。

## 阶段路线图

| 阶段 | 目标 | 进入条件 | 验证方向 | 状态 |
|---|---|---|---|---|
| 阶段 0 | 冻结最小包装契约和基线 | 已确认脚本副本与固定路径问题 | npm 名称、运行时、参数转发和包内资源定位基线 | 已完成 |
| 阶段 1 | 实现 npm 包和本地安装验证 | 阶段 0 独立准入通过 | `npm pack`、临时安装、CLI 对照测试 | 已完成 |
| 阶段 2 | 发布 npm 包并切换实际使用方 | 阶段 1 包验证通过，分发渠道已确认 | 全局安装、`npx`、项目命令、测试和回滚 | 已完成 |

## 阶段 0 设计记录

### 范围

阶段 0 只确认 npm 包名、包内资源布局、Node/Python 运行时边界和参数转发方式，不创建 `package.json`，不修改其他项目。

### 阶段 0 准入摘要

| 字段 | 内容 |
|---|---|
| 准入状态 | 设计中 |
| Step 0 | [阶段 0 Step 0 证据](#step-0-证据) |
| 样本矩阵 | [阶段 0 样本矩阵](#阶段-0-样本矩阵) |
| 验证方式 | [阶段 0 验证方式](#验证方式) |
| 失败/回滚边界 | 阶段 0 不修改运行时；包装方案无法稳定定位包内 Python 文件时停留在设计中 |
| 当前阻塞项 | 无；npm 包名和最低运行时要求待阶段 0 验证后确认 |
| 最新独立准入复核 | 尚未进行 |

### 阶段 0 样本矩阵

| 样本/fixture | 输入或基线 | 可执行命令 | 预期结果 | 失败判定 | 输出位置 |
|---|---|---|---|---|---|
| 包名 | `plan-governance-cli` 当前 npm registry 查询为未占用 | `npm view plan-governance-cli name version --json` | 可作为候选包名 | 已被占用或查询结果不可用 | 命令输出 |
| 脚本副本 | 主仓库、MinerU、Codex、Claude、Motorcycle 检查器 | `shasum -a 256 <checker paths>` | 记录当前一致副本和漂移副本 | 漏记副本或软链接关系 | 本计划 Step 0 证据 |
| 运行时 | Node `v22.23.0`、npm `10.9.8`、Python 3.11 | `node --version && npm --version && python3 --version` | 确认启动器的实际运行时 | 运行时假设未记录 | 命令输出 |
| 行为基线 | Python 检查器 87 项测试通过、总覆盖率 91.93% | `python3 -m pytest` | 作为 npm CLI 转发对照 | 基线失败或输出未记录 | pytest 输出 |
| 包内路径 | 启动器只能读取 npm 包自身目录 | 阶段 1 临时 `npm pack`/安装测试 | 安装后仍能找到包内 Python 脚本 | 读取开发机绝对路径或当前仓库路径 | 临时目录输出 |

### 实施步骤

1. 确认 `plan-governance-cli` 包名和 Node/Python 最低版本。
2. 固定 npm 包只携带启动器和当前 `check_plan_governance.py`，不引入新治理逻辑。
3. 固定参数透传、退出码透传和 Python 启动失败提示。
4. 独立复核阶段 0 基线和最小契约，达到 `待实施` 标准后进入阶段 1。

### 阶段 0 Step 0 证据

- 主仓库、`mineru-pdf-workflow`、Codex skill 和 Claude Code skill 的检查器 SHA-256 均为 `d4ef2a75fdd414c811e5ed3884c5f140c5050f2203ec34cfa883b0308fb80fe9`。
- `motorcycle-manual-app` 的检查器 SHA-256 为 `12abdf2a53154df436049466f6f59a0a220e2aa083cc74d553d51b104895bf23`；其他盘点项目没有本地检查器。
- 当前仓库没有 `package.json`；运行时为 Node `v22.23.0`、npm `10.9.8`、Python 3.11。
- `npm view plan-governance-cli name version --json` 返回 404，当前可作为候选包名，发布前仍需复核。
- Python 基线为 87 项测试通过、总覆盖率 91.93%；基础、严格和停滞治理检查通过。

### 阶段 0 验证方式

- 阶段 0：复核本计划与 `PLAN_MAP.md` 的状态、当前阶段、依赖和证据链接。
- 阶段 1：运行 `npm pack`，在临时目录安装包，验证 CLI 能找到包内 Python 检查器，并对照 Python 原命令的输出和退出码。
- 阶段 2：在实际使用方运行 npm CLI、项目测试和回滚命令；确认不再依赖固定绝对路径。
- 全程用 `rg` 搜索旧脚本调用、包名和固定路径，确认入口切换完整。

### 阶段 0 测试覆盖率

阶段 0 不增加运行时代码；Python 基线为 87 项测试通过、总覆盖率 91.93%。阶段 1 只需覆盖启动器、参数透传、退出码和临时安装，不要求重写 Python 检查器测试体系。

### 阶段 0 完成条件

- npm 包名、包内脚本布局、Node/Python 运行时和 CLI 透传契约已记录。
- npm 包不依赖开发机绝对路径，不引入新的治理规则。
- `PLAN_MAP.md` 已同步阶段 0 状态、最后更新、依赖和证据链接。
- 阶段 0 独立复核已通过，并已为阶段 1 建立独立准入证据。

## 阶段 0 完成证据

- 已决定 npm 包只做统一入口和版本化分发，携带并启动 Python 检查器，不重写检查逻辑。
- 已确认候选包名 `plan-governance-cli` 当前未在 npm registry 占用；发布前仍需复核。
- 已确认主仓库、MinerU、Codex 和 Claude Code 副本一致，Motorcycle 副本存在漂移；这构成统一入口的真实基线。
- 已确认阶段 1 只实现 `package.json`、Node 启动器、包内脚本资源和最小安装测试，不改变治理语义。

## 阶段 1 实施记录

### 阶段 1 范围

阶段 1 实现最小 npm 包：Node 启动器从自身包目录定位 `check_plan_governance.py`，透传参数、标准输出和退出码。只增加包入口和测试，不迁移其他项目、不发布公共 registry。

### 阶段 1 准入摘要

| 字段 | 内容 |
|---|---|
| 准入状态 | 已完成 |
| Step 0 | [阶段 1 Step 0 证据](#step-0-证据) |
| 样本矩阵 | [阶段 1 样本矩阵](#阶段-1-样本矩阵) |
| 验证方式 | [阶段 1 验证方式](#阶段-1-验证方式) |
| 失败/回滚边界 | 包内脚本定位或 Python 启动失败则阻止进入实施；保留现有 Python 命令作为回滚路径 |
| 当前阻塞项 | 无 |
| 最新独立准入复核 | [阶段 1 独立准入复核](#最新独立准入复核) |

### 阶段 1 样本矩阵

| 样本/fixture | 输入或基线 | 可执行命令 | 预期结果 | 失败判定 | 输出位置 |
|---|---|---|---|---|---|
| 参数转发 | 现有 Python CLI 帮助和治理检查命令 | `node bin/plan-governance-cli.mjs . --strict-readiness` | 参数、输出和退出码与 Python 命令一致 | 参数丢失或退出码改变 | npm CLI 测试 |
| 包内资源 | 临时 `npm pack` 后安装的包 | `npm pack && npm install <tarball>` | 启动器只从包内定位 Python 检查器 | 依赖开发机源码路径 | 临时目录输出 |
| Python 不可用 | 临时 PATH 隔离 Python | `PATH=<without-python> npm exec -- plan-governance-cli .` | 输出明确启动失败并返回非零 | 静默成功或吞掉错误 | CLI 测试 |
| 原有基线 | Python 87 项测试、91.93% 覆盖率 | `python3 -m pytest` | 基线保持通过 | Python 基线回归 | pytest 输出 |

### 阶段 1 实施步骤

1. 创建最小 `package.json` 和 `bin/plan-governance-cli.mjs`。
2. 将当前检查器纳入 npm 包文件清单，并用包目录路径定位，不使用绝对源码路径。
3. 实现参数、stdout/stderr 和退出码透传。
4. 增加 Node 内置测试和 `npm pack` 临时安装 smoke test。
5. 运行 Python 基线和 npm 测试，完成阶段 1 独立验收。

### 阶段 1 Step 0 证据

- 阶段 0 完成证据已冻结最小包装契约和回滚边界。
- 阶段 1 不改变 `scripts/check_plan_governance.py` 内容；目标是验证 npm 包能稳定调用现有脚本。
- 当前仓库 Node `v22.23.0`、npm `10.9.8`、Python 3.11，具备执行最小包装实验的运行时。

### 阶段 1 验证方式

- `npm test`：验证启动器参数、输出和退出码。
- `npm pack` 与临时目录安装：验证包内资源定位。
- `python3 -m pytest`：确认原检查器基线不受包文件影响。
- `python3 scripts/check_plan_governance.py . --strict-readiness`：确认治理文档仍通过。

### 阶段 1 测试覆盖率

阶段 1 不改变 Python 检查器逻辑；保留 Python 总覆盖率 91.93%，新增 Node 启动器行为测试和临时安装 smoke test。

### 阶段 1 完成条件

- npm 包可在临时目录安装并通过统一入口执行检查。
- 包内 Python 脚本定位不依赖开发机绝对路径。
- 参数、输出和退出码与现有 Python 命令保持一致。
- Python 基线、npm 测试和治理检查全部通过。

### 阶段 1 最新独立验收

| 字段 | 内容 |
|---|---|
| 日期 | 2026-07-13 |
| 阶段 | 阶段 1 |
| 结论 | 通过，阶段 1 达到完成标准 |
| 证据 | `npm test` 3 项通过；Python 87 项测试通过、总覆盖率 91.93%；严格治理通过；`npm pack` 后临时安装并执行 CLI 通过 |
| 复核者 | Codex 独立复核 |

## 阶段 1 完成证据

- 已创建 `package.json`、`package-lock.json` 和 `bin/plan-governance-cli.mjs`。
- npm 包只携带启动器和 `scripts/check_plan_governance.py`，启动器从包目录定位脚本并透传参数、输出和退出码。
- `npm test` 3 项通过；Python 全量测试 87 项通过，总覆盖率 91.93%。
- `npm pack` 后在临时目录安装并运行 `--strict-readiness` 通过；未依赖开发机绝对路径。

## 当前阶段

### 范围

阶段 2 处理公共 npm 发布、全局安装验证和实际使用方迁移。npm 包本身已经完成；迁移失败时可通过版本控制恢复迁移前的 Python 命令。

### 阶段准入摘要

| 字段 | 内容 |
|---|---|
| 准入状态 | 已完成 |
| Step 0 | 阶段 1 完成证据；用户已确认公共 npm 发布和全局安装入口 |
| 样本矩阵 | 公共 npm 发布、全局安装、`npx`、项目双跑和旧脚本回滚 |
| 验证方式 | `npm publish`、全局安装、CLI 严格检查和实际项目回归 |
| 失败/回滚边界 | 发布或安装失败则不改项目；迁移失败时可通过版本控制恢复旧 Python 命令 |
| 当前阻塞项 | 无 |
| 最新独立准入复核 | [阶段 2 独立准入复核](#最新独立准入复核) |

### 阶段 2 样本矩阵

| 样本/fixture | 输入或基线 | 可执行命令 | 预期结果 | 失败判定 | 输出位置 |
|---|---|---|---|---|---|
| registry 发布 | `plan-governance-cli@0.1.1` 包 | `npm publish --access public` | registry 可查询该版本 | 发布失败或包内容不完整 | npm 输出 |
| 全局安装 | 公共 registry 版本 | `npm install -g plan-governance-cli@0.1.1` | `plan-governance-cli --help` 可运行 | 命令不可发现或启动失败 | npm/CLI 输出 |
| npx 入口 | 公共 registry 版本 | `npx --yes --package plan-governance-cli@0.1.1 plan-governance-cli . --strict-readiness` | 检查通过 | npx 入口和全局入口语义不一致 | CLI 输出 |
| 项目迁移对照 | MinerU、Motorcycle 迁移前的本地 Python 命令 | 记录旧命令基线并运行全局 CLI | 入口切换不改变治理行为 | 迁移后行为变化 | 项目验证输出 |
| 回滚 | 迁移前规则文件和版本控制记录 | 恢复迁移前规则与脚本 | 旧命令可由版本控制恢复 | 迁移破坏旧路径 | 项目验证输出 |

### 阶段 2 实施步骤

1. 检查 npm 登录状态和包元数据，关闭 `private` 标记并执行发布前 dry-run。
2. 发布 `plan-governance-cli@0.1.1` 到公共 npm registry。
3. 用全局安装和 `npx` 分别执行严格治理检查。
4. 迁移实际存在本地检查器的项目，保留旧命令作为回滚证据。
5. 运行项目回归、反向引用检查和最终独立验收。

### 阶段 2 Step 0 证据

- 用户已明确允许公共 npm 发布，并要求支持全局安装。
- 阶段 1 已通过 npm 测试、Python 全量测试、严格治理和临时 tarball 安装。
- 包名 `plan-governance-cli` 在阶段 0 查询时未被占用，首个公开版本为 `0.1.1`（`0.1.0` 已发布，`0.1.1` 修正 npx 使用说明）。

### 阶段 2 验证方式

- `npm publish --dry-run --access public`。
- `npm install -g plan-governance-cli@0.1.1` 后运行 `plan-governance-cli . --strict-readiness`。
- `npx --yes --package plan-governance-cli@0.1.1 plan-governance-cli . --strict-readiness`。
- MinerU 和 Motorcycle 迁移前后双跑及项目测试。

### 最新独立准入复核

| 字段 | 内容 |
|---|---|
| 日期 | 2026-07-13 |
| 阶段 | 阶段 2 |
| 结论 | 通过，阶段 2 和整个计划达到完成标准 |
| 证据 | `plan-governance-cli@0.1.1` 已发布；全局安装和 `npx` 严格检查通过；两个实际使用项目已切换入口并删除本地检查器；项目原有治理基线保持可观察 |
| 复核者 | Codex 独立复核 |

### 阶段 2 完成条件

- 分发渠道和包版本策略已确认。
- 需要迁移的项目完成 npm CLI 检查，并记录迁移前旧命令基线。
- 旧脚本删除范围、迁移前基线和版本控制回滚方式已有明确记录。

## 阶段 2 完成证据

- `plan-governance-cli@0.1.0` 和修正 npx 文档后的 `plan-governance-cli@0.1.1` 已发布到公共 npm registry。
- `npm install -g plan-governance-cli@0.1.1` 后，全局入口执行严格治理检查通过；`npx --yes --package plan-governance-cli@0.1.1 plan-governance-cli ...` 也通过。
- `mineru-pdf-workflow` 和 `motorcycle-manual-app` 的项目规则已改为调用全局 CLI，项目本地 `scripts/check_plan_governance.py` 已删除。
- MinerU 迁移前后的治理命令保持相同的既有完成计划证据错误；Motorcycle 迁移后通过并保留既有准入 warning；迁移没有改变业务代码。
- 本计划的 npm 测试、Python 全量测试、严格治理、registry 查询、全局安装和 npx 验证均已完成。

## 整个计划完成条件

- npm 包提供统一全局入口，携带版本化 Python 检查器，不依赖开发机绝对路径。
- npm 包不改变现有治理规则、参数、输出和退出码语义。
- 实际存在本地检查器的两个项目已完成入口迁移，并保留可追溯的旧命令基线。
- 发布、安装、npx、项目命令和回滚边界已有验证证据。

## Step 0 证据

- 阶段 0 已记录检查器副本、运行时、包名和 Python 测试基线；阶段 1 已验证包内资源定位和参数透传；阶段 2 已确认公共 npm 发布、全局安装、npx 和两个实际项目迁移范围。
- 迁移前后均以可执行命令和项目现状作为基线：MinerU 保持既有错误，Motorcycle 保持既有 warning，未修改业务代码。

## 验证方式

- `npm test`、`python3 -m pytest`、`python3 scripts/check_plan_governance.py .`、`--strict-readiness` 和 `--stale-days 10`。
- `npm view plan-governance-cli version dist.tarball --json`、全局安装、npx 严格检查、两个项目的全局 CLI 检查，以及 `rg` 反向引用和事实源反模式扫描。

## 测试覆盖率

Python 检查器全量测试 87 项通过，总覆盖率 91.93%；npm CLI 内置测试 3 项通过。npm 包、全局安装、npx 和项目迁移 smoke test 均已执行。

## 独立复核记录

| 日期 | 类型 | 阶段 | 结论 | 证据 | 复核者 |
|---|---|---|---|---|---|
| 2026-07-13 | 阶段设计复核 | 阶段 0 | 通过 | npm 包统一入口范围、Python 包装方案、包名查询、运行时基线和回滚边界核对 | Codex 独立复核 |
| 2026-07-13 | 阶段准入复核 | 阶段 1 | 通过 | 阶段 1 最小包装范围、参数透传、包内资源定位、临时安装和 Python 回滚边界已核对 | Codex 独立复核 |
| 2026-07-13 | 阶段验收复核 | 阶段 1 | 通过 | npm 测试、Python 全量测试、严格治理和临时打包安装 smoke test 通过 | Codex 独立复核 |
| 2026-07-13 | 阶段准入复核 | 阶段 2 | 通过 | 用户确认公共 npm 发布和全局安装入口；阶段 1 包验证、Python 基线和严格治理均通过 | Codex 独立复核 |
| 2026-07-13 | 阶段验收复核 | 阶段 2 | 通过 | npm registry、全局安装、npx、两个项目入口迁移、Python/npm 测试和治理检查通过 | Codex 独立复核 |
| - | - | - | - | - | - |

## 未决问题

| 问题 | 推荐方案 | 是否阻塞当前阶段 | 状态 |
|---|---|---|---|
| npm 包名是否继续使用 `plan-governance-cli`？ | 保持候选名，发布前再次检查 registry | 否 | 已决定 |
| Node/Python 最低版本？ | 阶段 1 先使用当前 Node `v22.23.0`、Python 3.11，兼容范围在包验证后补充 | 否 | 已决定 |
| 是否需要发布到公共 npm registry？ | 发布 `plan-governance-cli@0.1.1`，并支持全局安装和 `npx` | 否 | 已决定 |

## 风险和回滚

- 目标机器没有 Python 运行时：CLI 明确报错；迁移期间可回退到项目原有脚本或安装 Python。
- npm 包资源路径处理错误：用临时安装测试阻断发布，不能回退到开发机绝对路径。
- npm 包版本与项目不一致：项目锁定版本；旧脚本在迁移验证完成前不删除。

## 关联 ADR、迁移、spec 或 issue

- 依赖：[phase-entry-gate-hardening](phase-entry-gate-hardening.md)，提供阶段准入和独立验收规则。
- 不新增 ADR；本计划只做最小分发入口，不改变治理架构。
