# 计划：independent-acceptance-rules

## 背景

当前 `plan-governance` 已能通过 `CLAUDE.md` 约束 Claude Code 的实施行为，并通过检查脚本校验基础治理结构。但实际协作模式通常是 Codex 负责规划和验收，Claude Code 负责实施。如果实施者把治理文档写得很规范，验收者可能误把“文档声明已完成”当作事实完成，从而降低验收独立性。

## 目标

补强计划治理规则，明确实施者填写的状态、证据文字和规范文档不能作为完成结论本身；验收者必须基于当前仓库内容、可复现验证命令和反向引用检查独立确认。

同时把治理规则入口从仅支持 `CLAUDE.md` 扩展到 `AGENTS.md`，使 Codex 也能读取同一套稳定执行规则。

## 非目标

- 不引入完整审批流或多人签名机制。
- 不强制所有普通小任务进入治理。
- 不实现复杂的语义级代码完成度判定。
- 不自动判断某个实现是否完全满足业务需求；当前阶段只固定验收规则和可检查文档结构。

## 不变量

- 计划状态不是验收结论。
- 文档格式规范不是完成证据。
- 完成证据必须能被当前仓库状态、命令输出或 CI 结果复核。
- 生成到项目的代理规则必须和本仓库 README、检查脚本测试保持一致。

## 影响模块或文件

- `scripts/init_plan_governance.py`
- `tests/test_init_plan_governance.py`
- `README.md`
- `plan-governance-design.md`
- `docs/PLAN_MAP.md`
- `docs/plans/independent-acceptance-rules.md`
- `/Users/jafish/.codex/skills/plan-governance/SKILL.md`

## 公共契约变化

初始化脚本新增或强化以下约定：

- `CLAUDE.md` 中的计划治理规则必须包含独立验收规则。
- 新增 `AGENTS.md` 生成/更新能力，供 Codex 等代理读取同一套规则。
- 已完成计划的证据应能支持验收者复核，而不是只描述实施者主观结论。

## 阶段路线图

| 阶段 | 目标 | 进入条件 | 验证方向 | 状态 |
|---|---|---|---|---|
| 阶段 1 | 将独立验收规则写入代理规则生成器、README 和测试 | 用户确认采用“实施者记录、验收者独立复核”的协作模型 | pytest、治理检查和反向引用检查通过 | 已完成 |

## 当前阶段

### 范围

实现当前阶段的最小闭环：

1. 在生成的代理规则中加入“验收独立性”章节。
2. 支持生成/更新 `AGENTS.md`。
3. 更新 README 和设计文档中的初始化、升级和验收独立性说明。
4. 用测试固定 `CLAUDE.md` 与 `AGENTS.md` 的输出内容。
5. 运行测试、覆盖率门禁、治理检查和反向引用检查。

### 实施步骤

1. 更新初始化脚本，抽出通用代理规则正文。
2. 为 `CLAUDE.md` 和 `AGENTS.md` 提供各自的受管标记与更新函数。
3. 增加 CLI 参数支持 `AGENTS.md` 更新，并让升级路径刷新两个入口文件。
4. 更新 README 和设计文档的使用说明。
5. 补充测试断言独立验收规则和 `AGENTS.md` 生成行为。
6. 运行验证并记录完成证据。

### Step 0 证据

现状基线：

- `scripts/init_plan_governance.py` 只有 `CLAUDE_SECTION_BEGIN` / `CLAUDE_SECTION_END` 和 `update_claude_md`。
- CLI 只有 `--update-claude-md`、`--update-claude-md-only` 和 `--upgrade-existing`。
- `--upgrade-existing` 只刷新 `scripts/check_plan_governance.py` 和 `CLAUDE.md`。
- `tests/test_init_plan_governance.py` 只断言 `CLAUDE.md` 生成内容，没有 `AGENTS.md` 测试。

### 验证方式

- 运行 `python3 -m pytest`。
- 运行 `python3 scripts/check_plan_governance.py .`。
- 用 `rg` 搜索 `验收独立性|不得仅依据|AGENTS.md|update-agents-md|independent-acceptance-rules`，确认脚本、测试、README 和治理索引同步。

### 测试覆盖率

`python3 -m pytest` 通过，pytest-cov 总覆盖率 98.75%，高于 85% 门禁。

### 完成条件

- 生成的 `CLAUDE.md` 包含验收独立性规则。
- 初始化脚本可以生成和更新 `AGENTS.md`。
- `--upgrade-existing` 同时刷新检查脚本、`CLAUDE.md` 和 `AGENTS.md`。
- README 说明新的代理规则入口。
- 测试、覆盖率门禁、治理检查和反向引用检查通过。
- `docs/PLAN_MAP.md` 状态和证据同步。

### 完成证据

- `python3 -m pytest` 通过，41 项测试全部通过，pytest-cov 总覆盖率 98.75%。
- `python3 scripts/check_plan_governance.py .` 输出 `计划治理检查通过。`
- `rg -n "验收独立性|不得仅依据|AGENTS.md|update-agents-md|independent-acceptance-rules" .` 已确认脚本、测试、README、设计文档和治理索引同步。
- `rg -n "草案为准|以草案为事实源|详见草案|draft is source|source of truth.*draft|以.*draft.*为准" .` 未发现旧草案重新成为事实源；命中均为规则文本、测试断言或历史完成计划中的检查表达。
- 已同步已安装 skill 说明 `/Users/jafish/.codex/skills/plan-governance/SKILL.md`，使 Codex 后续触发该 skill 时也遵循独立验收和 `AGENTS.md` 入口规则。

## 未决问题

| 问题 | 推荐方案 | 是否阻塞当前阶段 | 状态 |
|---|---|---|---|
| 是否支持 Cursor、Gemini 等更多入口？ | 当前阶段先落地 `AGENTS.md`，后续根据实际工具链再扩展。 | 否 | 已延后 |
| 是否自动检查“完成证据是否可复现”？ | 当前阶段先强化文档和测试；复杂复现性判断后续单独设计。 | 否 | 已延后 |

## 风险和回滚

风险：代理规则变长，导致普通任务也被误认为必须进入治理。

控制：保留“普通小范围 bugfix 或一次性修改不需要强制新建治理文档”的规则。

回滚：恢复初始化脚本中的代理规则生成逻辑，删除 `AGENTS.md` 相关 CLI 和测试，并将本计划从 `PLAN_MAP.md` 移除或标为已废弃。

## 关联 ADR、迁移、spec 或 issue

- 无。
