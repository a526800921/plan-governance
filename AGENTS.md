## npm 包发布流程

- 项目发布统一使用 `npm run release:npm -- <version-spec>`，不要手动组合 `nrm use npm`、`npm version` 和 `npm publish`。
- `<version-spec>` 支持 `patch`、`minor`、`major` 或明确的 SemVer 版本号；工作区版本以 `package.json` 为准，下一次修复发布使用 `patch` 自动生成下一个补丁版本。
- 本仓库按用户要求不运行 GitHub Actions CI；本地及发布前检查使用 `npm run verify`，检查集合、失败中断及恢复边界沿用[阶段 2 验证契约](docs/plans/iterative-governance-reliability.md#阶段-2-行为契约)。验证全部通过后，发布脚本才读取原 registry、切换官方源、升级版本和发布；切源尝试后始终尝试恢复，恢复失败保持非零退出。
- 实际发布前先运行 `npm run release:npm -- --dry-run patch`；dry-run 读取 registry 并展示流程，不运行验证、不切换源、不修改版本、不发布。
- 发布完成后核对官方 registry 的版本和 dist-tag，并将发布证据追加到 [plan-governance-distribution-setup](docs/plans/plan-governance-distribution-setup.md)；不得重复发布已经存在的版本。
- 发布流程的实现位于 [`scripts/release_npm.mjs`](scripts/release_npm.mjs)，分发维护记录是该流程的详细事实源。

<!-- plan-governance:start -->
## 计划治理

本项目使用轻量计划治理。处理治理任务前，先读取当前环境发现的已安装 `plan-governance` skill 的 SKILL.md，并按任务读取其同源 references；不要假定用户安装目录。

只有 CLI 可用时，运行 `plan-governance-cli guide` 读取入口，再按需运行 `guide planning`、`guide verification` 或 `guide cli`。两者均不可用或所需能力缺失时说明前提，不自动安装，也不猜测/拼接不同版本的规则。

最小执行边界：

- 普通无计划覆盖的小改不强制治理；普通改动自验，高风险或高影响同范围独立复核一次，修复后自验；记录与旧策略迁移按共享 verification 规范处理。
- 只实施已授权、已准入的当前阶段。每个阶段有自身 Step 0、验证/完成和失败边界；未解决问题不能记为完成，不可用或超时不能冒充已检查。已有授权不重复索取，新增高影响外部动作按实际授权处理。
- 首次读取 `docs/PLAN_MAP.md`、当前相关 `docs/plans/*.md` 及适用契约/ADR/migration；恢复先核对当前工作集、最近证据和实际 diff，缺失或冲突再展开。
- 地图维护状态、阶段、关系、阻塞与证据入口；计划记录本次差异及验证，现行契约优先复用 Schema/OpenAPI。新事实不写回历史草案，变化同步地图及相关引用。
- 完成时按共享规范记录实际验证与适用用户验收，运行 `plan-governance-cli check .`；准入/CI/发布显式使用 `--strict-readiness`，机械通过不等于业务验收。
<!-- plan-governance:end -->
