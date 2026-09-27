# 计划：npm 2.0.0 破坏性发布

## 背景

本计划开始时工作区为 `plan-governance-cli@1.2.0`。用户确认本次 skill 分发和文档治理调整按破坏性改动处理，要求发布 `2.0.0` 并撤回 npm 上的 `1.1.3`、`1.2.0`。完成 2.0.0 发布后，用户决定不再处理这两个旧版本；它们按当前 registry 状态保留，不再尝试 unpublish 或 deprecate。

## 目标

- 用仓库统一脚本发布 `plan-governance-cli@2.0.0` 并核实官方 registry 的版本、dist-tag 与包完整性。
- 根据用户最新决定，保留 npm 上的 `1.1.3`、`1.2.0`，不再撤回或弃用。
- 将发布结果、用户调整范围的决定和 registry 版本状态追加到分发维护记录。

## 非目标

- 不撤回、删除或 deprecate `1.1.3`、`1.2.0` 或其他版本；用户已取消对两个旧版本的处理。
- 本计划最初只包含 npm 发布与旧版本处理；用户之后另行要求更新本机 CLI，完成情况记录于[分发维护日志](../20260713/plan-governance-distribution-setup.md#2026-09-26-2-0-0-本机安装更新)。
- 不提交或推送 Git。

## 需求探索

- 用户明确要求撤回 `1.2.0` 和 `1.1.3`，并将当前改动作为破坏性改动发布为 `2.0.0`。
- 2026-09-26 发布 `2.0.0` 后，用户明确决定不再处理 `1.1.3`、`1.2.0`；该决定替代先前的撤回要求，旧版本保持原样。
- 本计划将“撤回”解释为对两个精确版本执行 unpublish。deprecate 仍允许安装，不等于用户要求的撤回；若 registry 不允许物理移除，先记录拒绝原因并向用户报告，不自动执行其他 registry 写操作。
- npm 官方文档指出 unpublish 会移除 registry tarball/版本记录，版本名不能再复用；是否允许撤回还受发布时间、依赖情况和账号安全限制影响。[npm unpublish policy](https://docs.npmjs.com/policies/unpublish/)；[recovery code 安全限制](https://docs.npmjs.com/recovering-your-2fa-enabled-account/)

## 不变量

- 发布只能运行 `npm run release:npm -- <version-spec>`；版本固定为 `2.0.0`，不手动组合 `nrm`、`npm version` 与 `npm publish`。
- 发布前先 dry-run 并完成单次独立复核；实际发布脚本必须先通过 `npm run verify`，失败时不切源、不 bump、不 publish。
- 不重复发布已存在版本；不把发布响应或短暂 E404 当成最终 registry 状态，必须只读核对最终版本和 dist-tag。
- 2.0.0 发布并核实后，按用户最新指示停止旧版本 unpublish/deprecate；先前 1.1.3 的 E403 失败只作为执行记录保留。
- 不将身份凭证、OTP、恢复码写入计划、日志或命令历史。

## 影响模块或文件

- `package.json`
- `package-lock.json`
- `docs/plans/20260713/plan-governance-distribution-setup.md`
- `docs/plans/20260926/npm-major-release-2.0.0.md`
- `docs/PLAN_MAP.md`

## 公共契约变化

在 npm 安装与文档中将当前 breaking-change 资源作为 `2.0.0` 主版本提供。用户已取消撤回旧版本的要求，因此 `1.1.3`、`1.2.0` 继续留在 npm registry。

## 阶段路线图

| 阶段 | 目标 | 进入条件 | 验证方向 | 状态 |
|---|---|---|---|---|
| 阶段 1 | 发布 2.0.0 并确认 latest 与包完整性 | 用户明确授权；官方 registry 未有 2.0.0；用户确认近 72 小时未使用 recovery code 登录；独立复核通过 | release dry-run、`npm run verify`、发布 tarball/registry 元数据、dist-tag、registry 恢复 | 已完成 |
| 阶段 2 | 撤回旧版本的原提议 | 阶段 1 完成；等待用户决定 | 按用户最新决定保留 1.1.3、1.2.0，不执行 unpublish 或 deprecate | 已废弃 |

## 当前阶段

### 范围

本计划现已完成：阶段 1 发布并核实 `2.0.0`；阶段 2 的旧版撤回提议由用户取消。`1.1.3`、`1.2.0` 均保持可见，不执行 unpublish 或 deprecate。

### 阶段准入摘要

| 字段 | 内容 |
|---|---|
| 准入状态 | 已完成 |
| 阶段状态 | 已完成 |
| 复核策略 | 单次独立复核 |
| Step 0 | [registry、账号和工作区基线](#step-0-证据) |
| 样本矩阵 | 2.0.0 发布及 package metadata；1.1.3、1.2.0 保持现有状态 |
| 验证方式 | release 输出、官方 npm registry 的版本/dist-tags/完整性、registry 源状态 |
| 失败/回滚边界 | 发布结果不明时只读查询 registry，不重复发布；旧版本操作已由用户取消 |
| 当前阻塞项 | 无；用户决定不再撤回旧版本 |
| 最新阶段复核 | [当前阶段复核](#最新阶段复核) |

### 实施与收口步骤

1. 复用阶段 1 独立复核，并按仓库发布契约完成 dry-run、验证与 2.0.0 发布。
2. 通过官方 registry 核对 `2.0.0`、`latest`、repository 元数据与包完整性。
3. 按用户最新决定，停止先前提出的 1.1.3/1.2.0 撤回操作，将两个版本保留为现状。
4. 将发布证据与用户范围调整记录到分发日志、计划索引，并运行治理检查与 diff 格式检查。

### Step 0 证据

- 源仓库初始工作区包含上一请求批准的 skill 合并及命名规则变更，当前 `package.json` 版本 `1.2.0`；这些源文件尚未提交/推送。
- 官方 registry 只读查询显示当前版本包含 `1.1.3`、`1.2.0`，`latest` 为 `1.2.0`；发布时间分别为 `2026-09-26T09:06:05.510Z`、`2026-09-26T09:20:39.312Z`，查询时当前时间为 `2026-09-26 10:00 UTC`。
- `npm whoami --registry=https://registry.npmjs.org/` 返回 `jafish`；未读取或记录 token、OTP。
- `npm run release:npm -- --dry-run patch` 与 `npm run release:npm -- --dry-run 2.0.0` 均退出 0；`npm pack --dry-run --json` 成功，当前发布清单为 19 个生产文件，包含合并后的 migration reference，不包含独立 migration skill 资源；未生成 tarball。
- npm 官方 recovery 文档说明，使用 recovery code 登录后 72 小时不能 publish/unpublish；`npm whoami` 成功不证明安全 hold 不存在。用户已确认近 72 小时未使用恢复码登录，排除该安全 hold。
- npm 官方 unpublish policy 要求版本在 72 小时内且没有公共 registry dependents；目标版本发布时间均在 72 小时内。官方 npm 页面 Dependents 标签显示 `Dependents (0)`，账号 recovery-code hold 已由用户确认排除。
- 账号必须启用可交互 2FA 才能通过当前 npm 的写操作认证。浏览器 CLI 登录完成后，`npm profile get --json` 仍返回 `tfa: false`；账户设置完成前不得重试 unpublish。
- npm unpublish 会使该 `name@version` 永远不能复用。若 npm policy 仍拒绝某个版本，停止该版本操作并报告；不自动 deprecate，因为 deprecate 仍可安装。
- 2.0.0 的 package metadata repository 指向 `git+https://github.com/a526800921/plan-governance.git`；实际发布核验见阶段证据。

### 阶段证据

- 2026-09-26 10:10 UTC：`npm run release:npm -- 2.0.0` 退出 0。内置严格治理检查保留四条既有 WARNING 后通过；682 项 Python 测试通过、总覆盖率 93.06%；103 项 Node 测试通过、0 skipped。
- npm publish 输出确认 `plan-governance-cli@2.0.0`、19 个文件、shasum `ab64ac7decf53fefd57ad4b96e5e466720f65936`；脚本结束时 registry 已恢复至执行前的官方源 `https://registry.npmjs.org/`。
- 首次发布后读查询遇到 npm 处理延迟，没有重复发布。10:14 UTC 后，官方 registry 新鲜 packument 与 `npm view` 确认版本可见、`latest: 2.0.0`、repository `git+https://github.com/a526800921/plan-governance.git`、19 个文件；shasum `ab64ac7decf53fefd57ad4b96e5e466720f65936`、integrity `sha512-tSN6hStiGOavOpHwqVPdur8EAO2SJzD3gBjgrjvnVBJxRoO36lXf6d79Y+PjBDZRdVgm/Fles7QGJmME8h9bBA==` 与发布输出一致。官方 npm 页面显示 package version 2.0.0、Dependents (0)、299 weekly downloads、一个 collaborator。
- 1.1.3、1.2.0 的发布时间分别为 `2026-09-26T09:06:05.510Z`、`2026-09-26T09:20:39.312Z`；当前时间 10:16 UTC，两者均在 72 小时内。用户确认近 72 小时未使用 recovery code 登录，阶段 2 准入条件满足。
- 10:23 UTC 首次 `npm unpublish plan-governance-cli@1.1.3 --registry=https://registry.npmjs.org/` 因 granular token bypass-2FA 限制返回 E403，registry 未改变。用户完成 `npm login --auth-type=web` 的浏览器验证，`npm whoami` 返回 `jafish`；登录后重试仍于 10:23 UTC 返回 E403（要求 2FA 或 bypass-2FA token）。只读 `npm profile get --json` 显示 `tfa: false`，确认登录态不等同于启用账号 2FA。随后官方 registry 仍列出 `1.1.3`、`1.2.0`、`2.0.0`，`latest: 2.0.0`；尚未成功撤回任何旧版本，未尝试 `1.2.0`，未执行 deprecate。需用户启用账号 2FA 后再继续。
- 2026-09-26 10:34 UTC：用户决定不再处理 `1.1.3`、`1.2.0`。官方 registry 最新查询确认 `version: 2.0.0`、`latest: 2.0.0`、repository 指向此 Git 仓库；后续不再尝试撤回或弃用旧版本。

### 最近实施/验证记录

| 日期 | 类型 | 动作/结果 | 证据 | 状态 | 记录者 |
|---|---|---|---|---|---|
| 2026-09-26 | registry 基线 | 官方 registry 核对版本列表、发布时间、latest 和 npm 账号 | [Step 0 证据](#step-0-证据) | 已记录；未发布或撤回 | Codex |
| 2026-09-26 | 阶段 1 发布 | 统一脚本发布 2.0.0 成功；官方元数据、latest、repository 和完整性已核实 | [阶段证据](#阶段证据) | 已完成 | Codex |
| 2026-09-26 | 阶段 2 撤回提议 | `1.1.3` unpublish 因账号 `tfa: false` 被 E403 拒绝；用户随后决定不再处理两个旧版本 | [阶段证据](#阶段证据) | 已取消；两个旧版本保留现状，计划按修订范围完成 | Codex |

### 验证方式

- 依仓库发布契约先运行 `npm run release:npm -- --dry-run patch`，再对明确 SemVer 运行 dry-run `2.0.0`。
- 实际 release script 会执行 `npm run verify`；用户要求发布，按项目契约此次运行完整本地验证，不运行 GitHub Actions。
- 发布后使用官方 registry 查询 `version`、`dist.shasum`、`dist.integrity`、repository 和 `dist-tags`；不重复发布。
- 旧版本撤回后分别检查 404/版本列表；若 npm 拒绝撤回则停止并报告，不自动 deprecate；最后重新确认 `latest: 2.0.0`。

### 用户可观察验收

| 场景 | 输入/前置 | 操作 | 可观察结果 | 验证证据 |
|---|---|---|---|---|
| Major 发布 | 官方 registry 不存在 `2.0.0`，工作区验证通过 | 运行统一发布脚本 | 官方 `2.0.0` 可见、latest 为 `2.0.0`，tarball 校验与发布结果一致 | `npm view` 及 release 输出 |
| 旧版处理 | 用户决定不再撤回 1.1.3、1.2.0 | 保持 registry 现状 | 两个版本仍可见；不执行 unpublish 或 deprecate | 官方 registry 版本列表 |
| registry 恢复 | 发布脚本结束 | 查询 npm 当前 registry | 与执行前一致 | `npm config get registry` |

### 测试覆盖率

发布时由统一脚本运行 `npm run verify`：682 项 Python 测试通过，总覆盖率 93.06%；103 项 Node 测试通过，0 skipped。GitHub Actions 不运行。

### 完成条件

- 2.0.0 通过统一脚本发布，官方元数据和 tarball 完整性已核对，`latest` 为 2.0.0。
- 用户决定不再处理 1.1.3 和 1.2.0；记录其仍可见，并停止撤回/deprecate 操作。
- registry 已恢复；发布维护记录和 `docs/PLAN_MAP.md` 已同步。

## 最新阶段复核

| 字段 | 内容 |
|---|---|
| 日期 | 2026-09-26 |
| 阶段 | 阶段 1 |
| 方式 | 独立 |
| 风险 | 高影响 |
| 风险依据 | npm public registry 发布及旧版本 unpublish 有广泛或不可逆影响；受审范围为此次 2.0.0 tarball 与两个精确旧版本操作。 |
| 结论 | 通过 |
| 证据 | 阶段 1 的发布范围、breaking SemVer、release dry-run 与完整验证已独立复核；官方 npm registry 已核对 2.0.0/latest 与包完整性。用户随后取消旧版本撤回，该阶段不再执行 registry 写操作。CLI guide migration 主题测试覆盖缺口评为非阻塞。 |
| 复核者 | 独立复核代理 `/root/npm_2_0_release_review` |

## 阶段复核记录

| 日期 | 类型 | 阶段 | 方式 | 风险 | 结论 | 证据 | 复核者 |
|---|---|---|---|---|---|---|---|
| 2026-09-26 | 发布范围与旧版本撤回审查 | 阶段 1 | 独立 | 高影响 | 通过 | 独立只读复核通过源改动范围、breaking SemVer 和“先发 2.0.0、核对 latest、再逐版本撤回”的顺序；发布前确认 recovery-code hold 已排除，阶段 2 撤回前仍须核实依赖状态。CLI guide migration 主题测试覆盖缺口评为非阻塞。 | 独立复核代理 `/root/npm_2_0_release_review` |
| 2026-09-26 | 阶段 2 撤回范围取消 | 阶段 2 | 自验 | 低影响 | 已决定 | 用户明确决定不再处理 1.1.3、1.2.0；其 registry 状态保持不变，本计划按已完成的 2.0.0 发布范围收口。 | Codex |

## 未决问题

| 问题 | 推荐方案 | 是否阻塞当前阶段 | 状态 |
|---|---|---|---|
| 近 72 小时是否使用 recovery code 登录？ | 用户已确认未使用；发布和撤回的 72 小时 hold 均已排除。 | 否 | 已解决 |
| 官方 registry 是否已收录 2.0.0 并将其设为 latest？ | 已通过官方 registry 核验版本、dist-tags、tarball 校验值和 repository。 | 否 | 已解决 |
| npm registry 的依赖状态是否符合 unpublish policy？ | npm 官方页面显示 `Dependents (0)`，两个目标版本仍在 72 小时内，recovery-code hold 已排除；如果 unpublish 返回拒绝，停止并记录，不自动 deprecate。 | 否 | 已核实；以 npm 命令实际响应为最终结果 |
| npm policy 是否允许分别 unpublish 指定版本？ | 用户决定不再处理两个旧版本，不进行新的 unpublish 尝试。 | 否 | 已决定 |
| npm 账号 2FA 是否已启用？ | 当前撤回要求已取消，无需为此启用账号 2FA。 | 否 | 已决定 |

## 风险和回滚

- 旧版本撤回已由用户取消，故不再承担 unpublish 的不可逆影响，也不执行 deprecate。
- 历史记录保留账号 2FA 状态与 E403 拒绝原因；不记录或传递 token、OTP、恢复码。
- 如果 2.0.0 的发布命令返回不明确，停止所有旧版本撤回，仅只读核查 2.0.0。
- release script 负责恢复 registry；恢复失败会保持非零退出并记录，修复前不进行其他发布步骤。

## 关联 ADR、迁移、spec 或 issue

- [分发与发布维护事实源](../20260713/plan-governance-distribution-setup.md)
- [本次单 skill 与 migration reference 变更](migration-reference-and-record-naming.md)
- [npm 官方 unpublish policy](https://docs.npmjs.com/policies/unpublish/)
