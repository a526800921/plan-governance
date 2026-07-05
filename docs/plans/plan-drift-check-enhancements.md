# 计划：plan-drift-check-enhancements

## 背景

`docs/plan-governance-optimization-analysis.md` 梳理了当前 `plan-governance` 在防止计划漂移方面的十类优化空间。分析结论显示，现有检查脚本已经能覆盖基础结构、状态合法性、计划链接、依赖环、已完成计划的章节存在性和测试覆盖率证据，但对证据内容质量、孤立计划、计划正文与索引关系、活跃计划影响范围重叠等场景仍主要依赖人工复核。

本计划将该分析文档收敛为正式实施计划。原分析文档仅作为背景材料，不作为规范事实源；本计划记录阶段范围、完成条件和验证方式。

本计划依赖已完成的独立验收规则：[independent-acceptance-rules](independent-acceptance-rules.md)。该计划明确实施者记录的状态和证据不是验收结论，阶段 2 的 warning 级检查也必须保留人工复核边界。

## 目标

分阶段增强 `plan-governance` 的自动化检查能力，在保持轻量治理定位的前提下，优先发现容易导致计划漂移的机械性问题。

阶段 1 已完成低风险、高确定性的检查增强：

- Step 0 证据和验证方式从“只有标题即可”增强为“章节内容必须非空且包含可识别证据”。
- 检测 `docs/plans/*.md` 中未登记到 `docs/PLAN_MAP.md` 的孤立计划文件。
- 扩展当前阶段阻塞项检查，使活跃计划在进入实施前也能暴露未解决阻塞项。
- 明确 `WARNING` 与 `ERROR` 的使用边界，避免把需要人工判断的语义关系误判为硬错误。

## 非目标

- 不引入看板、审批流、自动状态流转或计划工时估算。
- 不引入 AI 自动判定计划是否漂移。
- 不在当前阶段改变计划状态枚举。
- 不在当前阶段改变 `docs/PLAN_MAP.md` 的计划索引 schema，例如新增 `最后更新` 列。
- 不在当前阶段安装或启用 Git hooks。
- 不在当前阶段实现公共契约变化与 spec 文件 diff 的强关联验证。
- 不把 `docs/plan-governance-optimization-analysis.md` 升级为事实源。

## 不变量

- `docs/plans/*.md` 仍是专项计划实施细节事实源。
- `docs/PLAN_MAP.md` 仍是状态、依赖、替代/合并/废弃关系、推荐顺序、阻塞项和证据链接的事实源。
- 检查脚本只自动判断可机械验证的规则；语义冲突、业务完成度和验收结论仍由验收者独立复核。
- 普通小范围 bugfix 或一次性修改不因本计划而强制进入治理。
- 需要人工确认的高误报检查应输出 `WARNING`，不阻断治理检查通过。

## 影响模块或文件

- `scripts/check_plan_governance.py`
- `tests/test_check_plan_governance.py`
- `scripts/init_plan_governance.py`
- `tests/test_init_plan_governance.py`
- `README.md`
- `plan-governance-design.md`
- `docs/PLAN_MAP.md`
- `docs/plans/plan-drift-check-enhancements.md`

## 公共契约变化

当前阶段对检查脚本的命令入口保持兼容：

- `python3 scripts/check_plan_governance.py .` 仍为主要验证命令。
- 已完成计划缺少有效 Step 0 证据或验证方式时，检查结果应为 `ERROR`。
- `docs/plans/*.md` 存在未登记计划时，检查结果应至少输出 `WARNING`；是否阻断由阶段实现时基于测试和现有使用方式确认。
- 当前阶段阻塞项未解决时，活跃计划不得被误判为可安全推进。

后续阶段若新增 `--stale-days`、`--drift`、`--pre-commit` 或 `PLAN_MAP.md` 新列，必须在对应阶段先更新本计划和 `docs/PLAN_MAP.md`。

## 优化项分层

| 层级 | 优化项 | 本计划处理方式 |
|---|---|---|
| P0 | 证据有效性检查增强 | 阶段 1 实施 |
| P0 | 计划停滞检测 | 阶段 2 设计，因涉及 `PLAN_MAP.md` schema |
| P1 | 依赖声明与正文交叉验证 | 阶段 2 实施为 `WARNING` |
| P1 | 同模块多计划冲突标记 | 阶段 2 实施为 `WARNING` |
| P2 | 孤立计划文件检测 | 阶段 1 实施 |
| P2 | 阶段阻塞项自动化 | 阶段 1 实施 |
| P2 | 已完成计划被修改检测 | 阶段 3 设计，避免 hash 方案误伤文档修正 |
| P3 | pre-commit 钩子 | 阶段 3 候选 |
| P3 | 漂移检查半自动化 | 阶段 3 候选 |
| P3 | 契约变化关联验证 | 阶段 3 候选 |

## 阶段路线图

| 阶段 | 目标 | 进入条件 | 验证方向 | 状态 |
|---|---|---|---|---|
| 阶段 1 | 增强检查脚本的低风险机械校验 | 本计划登记到 `PLAN_MAP.md`，且 Step 0 基线已记录 | pytest、治理检查、反向引用检查通过 | 已完成 |
| 阶段 2 | 增加活跃计划之间的交叉提示和停滞检测设计 | 阶段 1 完成，确认 `WARNING` 输出格式稳定 | 新增测试覆盖 warning 场景，治理检查通过 | 已完成 |
| 阶段 3 | 增加可选 drift/pre-commit 检查，并记录完成计划修改检测和契约关联验证的设计边界 | 阶段 2 已完成，warning 输出格式稳定 | 新增测试覆盖可选命令场景，治理检查通过 | 已完成 |

## 当前阶段

### 范围

阶段 3 增加可选命令模式，并记录暂不落地的高误报检查边界：

1. 新增 `--drift` 模式，对工作区已变更文件与活跃计划声明的影响范围做 warning 级比对。
2. 新增 `--pre-commit` 模式，对 staged 文件与活跃计划声明的影响范围做 warning 级比对，供用户手动接入 pre-commit hook。
3. `--drift` 和 `--pre-commit` 只提示风险，不因没有匹配计划而阻断检查。
4. 不自动安装 Git hook；只提供可复制命令。
5. 不实现已完成计划 hash 锁定；阶段 3 只记录该方案需独立元数据和人工复核边界。
6. 不实现公共契约变化与 spec diff 的强关联验证；阶段 3 只记录未来需要结构化目标文件声明。

### 实施步骤

1. 将脚本入口切换为 `argparse`，保持 `python3 scripts/check_plan_governance.py .` 兼容。
2. 增加 Git 变更文件读取函数：`--drift` 使用工作区变更，`--pre-commit` 使用 staged 变更。
3. 增加影响目标匹配函数，支持文件精确匹配和目录前缀匹配。
4. 对没有任何活跃计划覆盖的变更文件输出 `WARNING`。
5. 增加测试覆盖无 Git 仓库、无变更、有匹配计划、无匹配计划和 staged 文件场景。
6. 更新 README 和设计文档。
7. 运行验证命令，并记录完成证据。

### Step 0 证据

阶段 3 基线：

- 阶段 2 已确认活跃计划 warning 不改变退出码。
- `scripts/check_plan_governance.py` 仍使用 `sys.argv` 手动解析根目录参数，没有命令模式。
- 当前仓库存在未提交变更，适合作为 `--drift` 的真实样本，但测试应通过 mock/subprocess fixture 固定行为，避免依赖本地 Git 状态。
- 阶段 2 已能解析活跃计划的 `影响模块或文件`，可复用为 drift/pre-commit 的匹配依据。
- 完成计划 hash 锁定会误伤文档修正，需要单独的完成快照元数据，不纳入阶段 3 实现。
- 契约变化关联验证需要计划文档提供结构化目标文件表，不纳入阶段 3 实现。

### 验证方式

- 运行 `python3 -m pytest`。
- 运行 `python3 scripts/check_plan_governance.py .`。
- 用 `rg` 搜索 `plan-drift-check-enhancements|--drift|--pre-commit|完成计划|契约关联|WARNING|ERROR`，确认计划、README、设计文档、脚本、测试和 `PLAN_MAP.md` 同步。
- 用 `rg` 搜索 `草案为准|以草案为事实源|详见草案|draft is source|source of truth.*draft|以.*draft.*为准`，确认没有旧草案或临时分析文档重新成为事实源。

### 测试覆盖率

`python3 -m pytest` 通过，pytest-cov 总覆盖率 96.22%，高于 85% 门禁。

### 完成条件

- `python3 scripts/check_plan_governance.py . --drift` 可检查工作区变更是否被活跃计划影响范围覆盖。
- `python3 scripts/check_plan_governance.py . --pre-commit` 可检查 staged 变更是否被活跃计划影响范围覆盖。
- drift/pre-commit 风险以 `WARNING` 输出，不改变退出码。
- 无 Git 仓库或 Git 命令不可用时，可选模式以 `WARNING` 提示并继续基础治理检查。
- 已完成计划修改检测和契约关联验证已有设计结论，且阶段 3 不引入 hash 存储或契约目标文件强校验。
- 新增行为有测试覆盖。
- README、设计文档和本仓库治理索引没有事实源漂移。
- `python3 -m pytest` 和 `python3 scripts/check_plan_governance.py .` 通过。
- `docs/PLAN_MAP.md` 状态和证据同步。

### 完成证据

- `scripts/check_plan_governance.py` 已切换为 `argparse`，保持 `python3 scripts/check_plan_governance.py .` 兼容，并新增 `--drift` 与 `--pre-commit`。
- `--drift` 会检查工作区变更是否被活跃计划 `影响模块或文件` 覆盖；`--pre-commit` 会检查 staged 变更，两个模式都只输出 `WARNING`，不改变退出码。
- 已完成计划修改检测设计结论：当前不引入 hash 锁定；未来若需要，必须先提供完成快照或等价元数据，并保留人工复核边界。
- 契约关联验证设计结论：当前不根据自然语言推断 spec diff；未来若需要，必须先在计划文档结构化声明目标 spec 或 Schema 文件。
- `tests/test_check_plan_governance.py` 已覆盖路径匹配、drift 未覆盖变更 warning、pre-commit 已覆盖变更无 warning、Git 不可用 warning。
- README 和 `plan-governance-design.md` 已同步 `--drift`、`--pre-commit`、完成计划修改检测和契约关联验证边界说明。
- `python3 -m pytest` 通过，56 项测试全部通过，pytest-cov 总覆盖率 96.22%。
- `python3 scripts/check_plan_governance.py .` 输出 `计划治理检查通过。`
- `python3 scripts/check_plan_governance.py . --drift` 输出 1 条预期 `WARNING`：当前没有活跃计划声明影响范围；检查仍通过。
- `python3 scripts/check_plan_governance.py . --pre-commit` 输出 `计划治理检查通过。`
- `rg -n "plan-drift-check-enhancements|--drift|--pre-commit|完成计划|契约关联|WARNING|ERROR" docs README.md plan-governance-design.md scripts tests` 已确认计划、索引、说明文档、脚本和测试同步。
- `rg -n "草案为准|以草案为事实源|详见草案|draft is source|source of truth.*draft|以.*draft.*为准" .` 未发现旧草案或临时分析文档重新成为事实源；命中均为规则文本、检查说明或历史完成计划中的验证表达。

## 未决问题

| 问题 | 推荐方案 | 是否阻塞当前阶段 | 状态 |
|---|---|---|---|
| 孤立计划检测应输出 `WARNING` 还是 `ERROR`？ | 阶段 1 已实现为 `WARNING`，不改变退出码，因为历史遗留计划可能需要人工归档。 | 否 | 已决定 |
| 证据有效性的最小文本长度是多少？ | 阶段 1 采用关键词/命令/路径/版本/基线识别，辅以较低长度兜底，避免单纯长度判断。 | 否 | 已决定 |
| `待实施` 计划是否应因未解决阻塞项直接失败？ | 阶段 1 已实现为 `ERROR`，因为待实施代表当前阶段门禁应已通过。 | 否 | 已决定 |

## 风险和回滚

风险：证据有效性规则过严，导致历史已完成计划因表述方式不同而失败。

控制：优先识别多种证据模式，并用现有四个已完成计划作为兼容样本。

风险：`WARNING` 输出进入现有 CI 后被误认为失败或被忽略。

控制：阶段 1 明确检查脚本返回码语义，并在 README 或设计文档中说明 `WARNING` 与 `ERROR` 区别。

回滚：恢复 `scripts/check_plan_governance.py` 中新增检查逻辑和对应测试，将本计划在 `docs/PLAN_MAP.md` 中标记为 `已废弃` 或移除未实施阶段说明。

## 关联 ADR、迁移、spec 或 issue

- 背景分析：[docs/plan-governance-optimization-analysis.md](../plan-governance-optimization-analysis.md)
