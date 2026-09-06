<!-- plan-governance:start -->
## 计划治理

本项目使用轻量计划治理。处理治理任务前，先读取当前环境发现的已安装 `plan-governance` skill 的 SKILL.md，并按任务读取其同源 references；不要假定用户安装目录。

只有 CLI 可用时，运行 `plan-governance-cli guide` 读取入口，再按需运行 `guide planning`、`guide verification` 或 `guide cli`。两者均不可用或所需能力缺失时说明前提，不自动安装，也不猜测/拼接不同版本的规则。

最小执行边界：

- 普通无计划覆盖的小改不强制治理；低风险且范围、后果与验证明确时由当前 AI 自验，高影响及有效独立失败按共享 verification 规范处理。已有计划未显式选择风险策略时保持原独立门禁。
- 只实施已授权、已准入的当前阶段。每个阶段有自身 Step 0、验证/完成和失败边界；失败、不可用或证据冲突不能自批。已有授权不重复索取，新增高影响外部动作按实际授权处理。
- 首次读取 `docs/PLAN_MAP.md`、当前相关 `docs/plans/*.md` 及适用契约/ADR/migration；恢复先核对当前工作集、最近证据和实际 diff，缺失或冲突再展开。
- 地图维护状态、阶段、关系、阻塞与证据入口；计划记录本次差异及验证，现行契约优先复用 Schema/OpenAPI。新事实不写回历史草案，变化同步地图及相关引用。
- 完成时按共享规范记录实际验证与适用用户验收，运行 `plan-governance-cli check .`；准入/CI/发布显式使用 `--strict-readiness`，机械通过不等于业务验收。
<!-- plan-governance:end -->
