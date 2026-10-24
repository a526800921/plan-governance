## npm 包发布流程

- 项目发布统一使用 `npm run release:npm -- <version-spec>`，不要手动组合 `nrm use npm`、`npm version` 和 `npm publish`。
- `<version-spec>` 支持 `patch`、`minor`、`major` 或明确的 SemVer 版本号；工作区版本以 `package.json` 为准，下一次修复发布使用 `patch` 自动生成下一个补丁版本。
- 本仓库按用户要求不运行 GitHub Actions CI；本地及发布前检查使用 `npm run verify`，检查集合、失败中断及恢复边界沿用[阶段 2 验证契约](docs/plans/20260906/iterative-governance-reliability.md#阶段-2-行为契约)。验证全部通过后，发布脚本才读取原 registry、切换官方源、升级版本和发布；切源尝试后始终尝试恢复，恢复失败保持非零退出。
- 实际发布前先运行 `npm run release:npm -- --dry-run patch`；dry-run 读取 registry 并展示流程，不运行验证、不切换源、不修改版本、不发布。
- 发布完成后核对官方 registry 的版本和 dist-tag，并将发布证据追加到 [plan-governance-distribution-setup](docs/plans/20260713/plan-governance-distribution-setup.md)；不得重复发布已经存在的版本。
- 发布流程的实现位于 [`scripts/release_npm.mjs`](scripts/release_npm.mjs)，分发维护记录是该流程的详细事实源。

<!-- plan-governance:start -->
## 计划治理

处理已有计划或需要持续协调的工作时，读取实际发现的 `plan-governance` skill；开发或审查该 skill 自身时使用仓库源及对应 CLI。规范来源一次选定后复用，按当前动作读取同源 references。

只有 CLI 可用时，以 `plan-governance-cli guide` 为入口，再按需读取 `guide planning`、`guide verification` 或 `guide cli`。所需规则或能力不可用时说明缺口，不自动安装，不拼接不同版本。

- 按用户授权和当前计划范围推进；未解决问题如实保留，流程建议不扩大实施或外部操作授权。阶段准入、复核方式、验证与适用用户验收统一按所选规范的 verification 执行。
- 从 `docs/PLAN_MAP.md` 定位相关计划、当前阶段、依赖和证据，再按索引读取必要文档；恢复先核对当前事实与实际差异。文档职责、记录格式和状态同步统一按 planning 执行。
- 多计划/多会话并行时，在 check/workset/hook 中显式传入本会话的 `--plan ID`；必要前置、共享写入及写入前复核按 cli 执行，不设置全项目可变焦点。
- 完成时运行 `plan-governance-cli check .`；准入/发布使用 `--strict-readiness`。机械检查不替代实际验证和用户验收。
<!-- plan-governance:end -->
