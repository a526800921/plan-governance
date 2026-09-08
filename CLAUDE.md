<!-- plan-governance:start -->
## 计划治理

本项目使用轻量计划治理。处理已有计划或需要持续协调的工作时，读取实际发现的 `plan-governance` skill；开发或审查该 skill 自身时使用仓库源及对应 CLI。规范来源一次选定后复用，按当前动作读取同源 references。

只有 CLI 可用时，运行 `plan-governance-cli guide` 读取入口，再按需运行 `guide planning`、`guide verification` 或 `guide cli`。两者均不可用或所需能力缺失时说明前提，不自动安装，也不猜测/拼接不同版本的规则。

最小执行边界：

- 普通一次性任务直接处理；已有计划先确定当前有效策略，再按共享 verification 验证。单次策略下高风险或高影响同范围独立复核一次，修复后自验。
- 只实施已授权、已准入的当前阶段。每个阶段有自身 Step 0、验证/完成和失败边界；未解决问题不能记为完成，不可用或超时不能冒充已检查。已有授权不重复索取，新增高影响外部动作按实际授权处理。
- 首次读取 `docs/PLAN_MAP.md`、当前相关 `docs/plans/*.md` 及适用契约/ADR/migration；恢复先核对当前工作集、最近证据和实际 diff，缺失或冲突再展开。
- 地图维护状态、阶段、关系、阻塞与证据入口；计划记录本次差异及验证，现行契约优先复用 Schema/OpenAPI。新事实不写回历史草案，变化同步地图及相关引用。
- 完成时按共享规范记录实际验证与适用用户验收，运行 `plan-governance-cli check .`；准入/CI/发布显式使用 `--strict-readiness`，机械通过不等于业务验收。
<!-- plan-governance:end -->
