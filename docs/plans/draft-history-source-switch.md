# 计划：draft-history-source-switch

## 背景

`marker-pdf-workflow` 的使用报告指出：启用 `plan-governance` 后，助手仍继续修改早期草案 `marker_pdf_workflow_draft.md`，把后续规范写回草案。这违背了治理文档作为事实源的预期。

## 目标

补强 `plan-governance` 规则：一旦启用治理，旧草案、历史设计、归档计划和临时分析文档默认只作为背景材料，不再承载新的规范事实。

## 非目标

- 不重写检查脚本做完整语义漂移检测。
- 不改变现有治理目录结构。
- 不要求所有旧草案都迁移或删除。

## 不变量

- 同一事实只定义一次。
- `docs/plans/*.md` 承载专项计划实施细节事实。
- `docs/PLAN_MAP.md` 承载状态、依赖、阻塞项和证据链接事实。
- 旧草案可以被引用为背景，但不再默认同步更新。

## 影响模块或文件

- `/Users/jafish/.codex/skills/plan-governance/SKILL.md`
- `README.md`
- `plan-governance-design.md`
- `scripts/init_plan_governance.py`
- `tests/test_init_plan_governance.py`
- `docs/PLAN_MAP.md`

## 公共契约变化

治理规则新增草案和历史文档处理约定：

- 启用治理后，旧草案、历史设计、归档计划、临时分析文档默认只作为背景材料。
- 新发生的目标、范围、公共契约、字段、Schema、状态语义、阶段、验证方式、完成条件、风险和回滚，默认进入 `docs/plans/*.md`、ADR、migration 或正式 spec。
- 状态、依赖、替代/合并/废弃关系、推荐顺序、阻塞项和证据链接进入 `docs/PLAN_MAP.md`。
- 除非用户明确点名旧草案，否则不要为了保持一致而修改草案。

## 阶段路线图

| 阶段 | 目标 | 进入条件 | 验证方向 | 状态 |
|---|---|---|---|---|
| 阶段 1 | 将草案事实源切换规则写入 skill 和说明文档 | 使用报告已明确 | 反向引用搜索和治理检查通过 | 已完成 |

## 当前阶段

### 范围

把“启用治理后旧草案停止承载新规范”的规则写入已安装 skill、README、设计文档、本仓库治理入口、生成器和测试断言。

### 实施步骤

1. 更新已安装的 `plan-governance` skill 规则。
2. 更新 README 和设计文档。
3. 更新本仓库 `docs/PLAN_MAP.md`。
4. 更新 `scripts/init_plan_governance.py` 生成的 `CLAUDE.md` 规则和 `PLAN_MAP.md` 模板。
5. 增加测试断言，防止生成规则回退。
6. 搜索反模式表达，确认没有把草案设为事实源。
7. 运行测试和治理检查。

### Step 0 证据

使用报告 `/Users/jafish/Documents/work/marker-pdf-workflow/plan_governance_usage_report.md` 记录了真实失败案例：治理启用后，早期草案仍被错误修改并承载了 `manifest.json`、`data/`、`review_only`、`rerunnable`、页面类型、决策枚举和报告示例等规范内容。

### 验证方式

- 用 `rg` 搜索 `草案和历史文档|事实源切换|草案为准|以草案为事实源|详见草案|draft is source|source of truth.*draft|以.*draft.*为准`。
- 运行 `python3 -m pytest`。
- 运行 `python3 scripts/check_plan_governance.py .`。

验证结果：

- 反向引用搜索确认规则已进入已安装 skill、README、设计文档、本计划和生成器。
- `python3 -m pytest` 通过，34 个测试通过，覆盖率 98.54%。
- `python3 scripts/check_plan_governance.py .` 输出：`计划治理检查通过。`

### 测试覆盖率

`python3 -m pytest` 通过，pytest-cov 报告总覆盖率 98.54%，高于 85% 门禁。

### 完成条件

- skill 规则包含草案和历史文档处理章节。
- README 和设计文档同步说明旧草案不再承载新规范。
- 生成到项目的 `CLAUDE.md` 和 `PLAN_MAP.md` 模板包含草案事实源切换规则。
- `docs/PLAN_MAP.md` 记录该规则变化。
- 测试和治理检查通过。

## 未决问题

| 问题 | 推荐方案 | 是否阻塞当前阶段 | 状态 |
|---|---|---|---|
| 是否把反模式搜索自动化进 `check_plan_governance.py`？ | 先保留为人工验收规则，积累更多真实案例后再做自动化。 | 否 | 已延后 |

## 风险和回滚

风险：规则过宽，导致用户明确希望维护草案时助手也不更新草案。

控制：保留“除非用户明确点名该文件”的例外。

回滚：恢复 skill、README、设计文档和 `PLAN_MAP.md` 中新增的草案处理规则，并删除本计划记录。

## 关联 ADR、迁移、spec 或 issue

- `/Users/jafish/Documents/work/marker-pdf-workflow/plan_governance_usage_report.md`
