# 计划：stale-plan-detection

## 背景

`plan-drift-check-enhancements` 已完成基础证据校验、活跃计划交叉提示、`--drift` 和 `--pre-commit` 可选检查，但计划停滞检测仍只记录了设计边界：不能从文件修改时间推断计划状态，必须先有可靠的 `最后更新` 或等价元数据。

本计划专门处理计划停滞检测，避免继续扩大前一计划的范围。

## 目标

为计划治理增加轻量的停滞检测能力，帮助发现长期停留在 `候选`、`设计中`、`待实施` 或 `实施中` 的计划。

阶段 1 目标：

- 为 `docs/PLAN_MAP.md` 计划索引增加 `最后更新` 列。
- 约定日期格式为 `YYYY-MM-DD`。
- 为检查脚本增加 `--stale-days N` 参数，默认阈值为 90 天。
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
python3 scripts/check_plan_governance.py . --stale-days 90
```

兼容策略：

- 阶段 1 实施时必须迁移本仓库 `PLAN_MAP.md` 和初始化模板。
- 如果旧项目仍使用五列表，检查脚本应给出清晰错误或兼容提示，具体策略在实施时用测试固定。

## 阶段路线图

| 阶段 | 目标 | 进入条件 | 验证方向 | 状态 |
|---|---|---|---|---|
| 阶段 1 | 增加 `最后更新` 字段和 `--stale-days` warning 检查 | `plan-drift-check-enhancements` 阶段 3 已完成 | pytest、治理检查、反向引用检查通过 | 待实施 |

## 当前阶段

### 范围

1. 迁移 `docs/PLAN_MAP.md` 计划索引，加入 `最后更新` 列。
2. 更新初始化模板，让新项目默认生成 `最后更新`。
3. 检查脚本解析 `最后更新`，校验日期格式。
4. `--stale-days N` 对活跃计划做停滞 warning。
5. 补充测试覆盖新列解析、非法日期、过期 warning、非活跃计划忽略和模板生成。
6. 更新 README 和设计文档说明。

### 实施步骤

1. 先迁移本仓库 `PLAN_MAP.md`，为现有计划填写明确日期。
2. 更新 `scripts/check_plan_governance.py` 的计划索引解析逻辑。
3. 增加日期解析与阈值判断。
4. 更新 `scripts/init_plan_governance.py` 生成的新 `PLAN_MAP.md` 模板。
5. 更新测试和说明文档。
6. 运行验证命令并记录完成证据。

### Step 0 证据

当前基线：

- `docs/PLAN_MAP.md` 计划索引当前为五列：`计划`、`状态`、`当前阶段`、`依赖`、`证据`。
- `scripts/check_plan_governance.py` 当前不解析日期，也没有 `--stale-days` 参数。
- `plan-drift-check-enhancements` 阶段 3 已明确：停滞检测需要 `最后更新` 或等价元数据，不能从文件 mtime 推断。
- README 和 `plan-governance-design.md` 当前只记录“不推断文件修改时间”，尚未定义实际字段和命令。

### 验证方式

- 运行 `python3 -m pytest`。
- 运行 `python3 scripts/check_plan_governance.py .`。
- 运行 `python3 scripts/check_plan_governance.py . --stale-days 90`。
- 用 `rg` 搜索 `stale-plan-detection|最后更新|stale-days|计划停滞|WARNING|ERROR`，确认计划、索引、说明文档、脚本和测试同步。
- 用 `rg` 搜索 `草案为准|以草案为事实源|详见草案|draft is source|source of truth.*draft|以.*draft.*为准`，确认没有旧草案或临时分析文档重新成为事实源。

### 测试覆盖率

阶段 1 完成时必须运行 `python3 -m pytest`，并记录 pytest-cov 总覆盖率。覆盖率不得低于当前项目既有门禁。

### 完成条件

- `PLAN_MAP.md` 计划索引包含 `最后更新` 列。
- 初始化模板会生成包含 `最后更新` 的 `PLAN_MAP.md`。
- 检查脚本能识别非法日期并输出 `ERROR`。
- `--stale-days` 能对超过阈值的活跃计划输出 `WARNING`。
- 非活跃计划不会触发停滞 warning。
- 新增行为有测试覆盖。
- README、设计文档和本仓库治理索引没有事实源漂移。
- `python3 -m pytest`、基础治理检查和 `--stale-days` 检查通过。
- `docs/PLAN_MAP.md` 状态和证据同步。

## 未决问题

| 问题 | 推荐方案 | 是否阻塞当前阶段 | 状态 |
|---|---|---|---|
| 旧五列表 `PLAN_MAP.md` 是报错还是兼容？ | 阶段 1 实施时用测试固定；倾向输出清晰 `ERROR`，避免静默跳过停滞检测。 | 否 | 待确认 |
| `最后更新` 对已完成计划是否必填？ | 本仓库迁移时全部填写；停滞 warning 只作用于活跃状态。 | 否 | 待确认 |
| 默认阈值是否固定 90 天？ | 先采用 90 天；可通过 `--stale-days` 覆盖。 | 否 | 待确认 |

## 风险和回滚

风险：新增列会让旧项目的 `PLAN_MAP.md` 与新检查脚本不兼容。

控制：实施时为错误信息和初始化模板补测试；README 明确迁移方式。

风险：停滞 warning 被误解为计划失败。

控制：明确 warning 只提示人工复核，不自动改变状态。

回滚：恢复五列 `PLAN_MAP.md` 表结构，移除 `--stale-days` 参数和对应测试，将本计划标记为 `已废弃` 或回退到 `候选`。

## 关联 ADR、迁移、spec 或 issue

- 依赖计划：[plan-drift-check-enhancements](plan-drift-check-enhancements.md)
