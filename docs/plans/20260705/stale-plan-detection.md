# 计划：stale-plan-detection

## 背景

`plan-drift-check-enhancements` 已完成基础证据校验、活跃计划交叉提示、`--drift` 和 `--pre-commit` 可选检查，但计划停滞检测仍只记录了设计边界：不能从文件修改时间推断计划状态，必须先有可靠的 `最后更新` 或等价元数据。

本计划专门处理计划停滞检测，避免继续扩大前一计划的范围。

## 目标

为计划治理增加轻量的停滞检测能力，帮助发现长期停留在 `候选`、`设计中`、`待实施` 或 `实施中` 的计划。

阶段 1 目标：

- 为 `docs/PLAN_MAP.md` 计划索引增加 `最后更新` 列。
- 约定日期格式为 `YYYY-MM-DD`。
- 为检查脚本增加 `--stale-days N` 参数，默认阈值为 10 天。
- 对超过阈值的活跃计划输出 `WARNING`，不改变退出码。
- 不自动改变计划状态。

## 非目标

- 不使用文件 mtime 推断计划更新时间。
- 不自动把计划从 `实施中` 改为 `已废弃`、`已替代` 或其他状态。
- 不引入看板、审批流或工时估算。
- 不要求已完成、已替代、已合并、已废弃计划填写 `最后更新` 后继续参与停滞检测。
- 不在当前阶段处理完成计划 hash、契约关联验证或 hook 安装器。

## 不变量

- `PLAN_MAP.md` 仍是状态、依赖、推荐顺序、阻塞项和证据链接的事实源。
- `docs/plans/*.md` 仍是专项计划实施细节事实源。
- 停滞检测只提示人工复核，不代表计划应自动关闭。
- 日期必须显式写入治理文档，不能由 Git 历史或文件系统时间替代。
- `WARNING` 不改变检查脚本退出码。

## 影响模块或文件

- `docs/PLAN_MAP.md`
- `docs/plans/stale-plan-detection.md`
- `scripts/check_plan_governance.py`
- `tests/test_check_plan_governance.py`
- `scripts/init_plan_governance.py`
- `tests/test_init_plan_governance.py`
- `README.md`
- `plan-governance-design.md`

## 公共契约变化

`docs/PLAN_MAP.md` 的计划索引表新增一列：

```markdown
| 计划 | 状态 | 当前阶段 | 最后更新 | 依赖 | 证据 |
```

检查脚本新增参数：

```bash
python3 scripts/check_plan_governance.py . --stale-days 10
```

兼容策略：

- 阶段 1 实施时必须迁移本仓库 `PLAN_MAP.md` 和初始化模板。
- 如果旧项目仍使用五列表，检查脚本应给出清晰错误或兼容提示，具体策略在实施时用测试固定。

## 阶段路线图

| 阶段 | 目标 | 进入条件 | 验证方向 | 状态 |
|---|---|---|---|---|
| 阶段 1 | 增加 `最后更新` 字段和 `--stale-days` warning 检查 | `plan-drift-check-enhancements` 阶段 3 已完成 | pytest、治理检查、反向引用检查通过 | 已完成 |
| 阶段 2 | 提供旧五列表 `PLAN_MAP.md` 的显式迁移辅助命令 | 阶段 1 已完成，旧五列表会被检查脚本报错 | pytest、迁移样本验证、治理检查通过 | 已完成 |

## 当前阶段

### 范围

阶段 2 只增加显式迁移辅助，不改变检查脚本的五列表报错策略：

1. 在初始化脚本中新增迁移命令，把旧五列表 `PLAN_MAP.md` 转换为六列表。
2. 迁移命令为每条计划索引行填入指定日期；未指定时使用当天日期。
3. 已经是六列表的 `PLAN_MAP.md` 不重复修改。
4. 更新 README 和设计文档说明迁移方式。
5. 补充测试覆盖旧五列表迁移、已迁移文件幂等和缺失 `PLAN_MAP.md` 报错。

### 实施步骤

1. 在 `scripts/init_plan_governance.py` 增加 `migrate_plan_map_last_updated()`。
2. 增加 CLI 参数，例如 `--migrate-plan-map-last-updated` 和可选 `--last-updated-date YYYY-MM-DD`。
3. 让迁移命令作为 only mode 运行，不初始化新计划。
4. 增加测试覆盖旧五列表迁移、六列表幂等和缺失文件错误。
5. 更新 README 和设计文档。
6. 运行验证命令并记录完成证据。

### Step 0 证据

阶段 2 基线：

- 阶段 1 已将本仓库 `PLAN_MAP.md` 迁移为六列表。
- 阶段 1 已让检查脚本对旧五列表输出清晰 `ERROR`。
- `scripts/init_plan_governance.py --upgrade-existing` 当前刷新辅助文件但不迁移 `docs/PLAN_MAP.md`。
- 旧项目需要一个显式迁移命令，避免手动编辑表格时破坏列顺序。

### 验证方式

- 运行 `python3 -m pytest`。
- 运行 `python3 scripts/check_plan_governance.py .`。
- 运行 `python3 scripts/check_plan_governance.py . --stale-days 10`。
- 在测试 fixture 中验证旧五列表迁移命令。
- 用 `rg` 搜索 `stale-plan-detection|最后更新|stale-days|计划停滞|WARNING|ERROR`，确认计划、索引、说明文档、脚本和测试同步。
- 用 `rg` 搜索 `草案为准|以草案为事实源|详见草案|draft is source|source of truth.*draft|以.*draft.*为准`，确认没有旧草案或临时分析文档重新成为事实源。

### 测试覆盖率

`python3 -m pytest` 通过，pytest-cov 总覆盖率 96.64%，高于 85% 门禁。

### 完成条件

- 旧五列表 `PLAN_MAP.md` 可以通过显式迁移命令转换为六列表。
- 迁移命令支持指定填入的 `最后更新` 日期。
- 已经是六列表的 `PLAN_MAP.md` 迁移命令保持幂等。
- 缺失 `docs/PLAN_MAP.md` 时迁移命令输出清晰错误。
- 新增行为有测试覆盖。
- README、设计文档和本仓库治理索引没有事实源漂移。
- `python3 -m pytest`、基础治理检查和 `--stale-days` 检查通过。
- `docs/PLAN_MAP.md` 状态和证据同步。

### 完成证据

- `scripts/init_plan_governance.py` 已新增 `--migrate-plan-map-last-updated` 和 `--last-updated-date YYYY-MM-DD`，可将旧五列表 `PLAN_MAP.md` 显式迁移为包含 `最后更新` 的六列表。
- 迁移命令对已是六列表的 `PLAN_MAP.md` 保持幂等，缺失 `docs/PLAN_MAP.md` 或非法日期时会给出明确错误。
- `tests/test_init_plan_governance.py` 已覆盖旧五列表迁移、六列表幂等、缺失文件和非法日期场景。
- README 和 `plan-governance-design.md` 已同步迁移命令说明。
- 阶段 1 的默认阈值已根据反馈调整为 10 天，测试和文档均已同步。
- `python3 -m pytest` 通过，65 项测试全部通过，pytest-cov 总覆盖率 96.64%。
- `python3 scripts/check_plan_governance.py .` 输出 `计划治理检查通过。`
- `python3 scripts/check_plan_governance.py . --stale-days 10` 输出 `计划治理检查通过。`
- `python3 scripts/check_plan_governance.py . --stale-days` 输出 `计划治理检查通过。`

## 未决问题

| 问题 | 推荐方案 | 是否阻塞当前阶段 | 状态 |
|---|---|---|---|
| 旧五列表 `PLAN_MAP.md` 是报错还是兼容？ | 阶段 1 已实现为清晰 `ERROR`，避免静默跳过停滞检测。 | 否 | 已决定 |
| `最后更新` 对已完成计划是否必填？ | 本仓库迁移时全部填写；停滞 warning 只作用于活跃状态。 | 否 | 已决定 |
| 默认阈值是否固定 10 天？ | 阶段 1 已调整为 `--stale-days` 省略数值时默认 10 天，也可显式传入 N。 | 否 | 已决定 |

## 风险和回滚

风险：新增列会让旧项目的 `PLAN_MAP.md` 与新检查脚本不兼容。

控制：实施时为错误信息和初始化模板补测试；README 明确迁移方式。

风险：停滞 warning 被误解为计划失败。

控制：明确 warning 只提示人工复核，不自动改变状态。

回滚：恢复五列 `PLAN_MAP.md` 表结构，移除 `--stale-days` 参数和对应测试，将本计划标记为 `已废弃` 或回退到 `候选`。

## 关联 ADR、迁移、spec 或 issue

- 依赖计划：[plan-drift-check-enhancements](plan-drift-check-enhancements.md)
