# plan-governance

`plan-governance` 是一套面向个人或小团队的轻量计划治理机制。

它不是任务清单，也不是完整项目管理系统。它解决的问题是：当一个任务跨阶段推进、影响公共契约、依赖真实反馈，或会和已有计划发生依赖/替代/冲突时，如何避免计划漂移、旧决策被覆盖、阶段边界失控和完成证据缺失。

## 什么时候使用

适合启用治理的信号：

- 跨阶段、里程碑或多轮会话。
- 涉及架构、公共 API、Schema、兼容性或迁移行为。
- 后续需要真实运行报告、样本或反馈。
- 多个计划之间存在依赖、替代、重叠或冲突。
- 同一模块会被多个后续计划反复修改。

不适合启用治理的场景：

- 一次性 bugfix。
- 小范围本地修改。
- 互不依赖的待办列表。
- 不影响公共契约的普通实现任务。

## 文档结构

最小结构：

```text
docs/
  PLAN_MAP.md
  plans/
    <plan-name>.md
```

按需增加：

```text
docs/
  adr/
    0001-<decision>.md
  migrations/
    <migration-name>.md
```

文档权责：

| 文档 | 权威内容 |
|---|---|
| `docs/PLAN_MAP.md` | 计划索引、状态、依赖、替代/合并/废弃关系、推荐顺序、阻塞项、证据链接 |
| `docs/plans/*.md` | 单个计划的目标、阶段、当前步骤、字段方案、Schema、枚举、Step 0 证据、验证方式、完成条件 |
| `docs/adr/*.md` | 关键架构决策、备选方案和后果 |
| `docs/migrations/*.md` | 兼容策略、迁移步骤、回滚方式和旧行为保留窗口 |

## 多文档同步

- 专项计划是实施细节事实源，记录字段方案、Schema、枚举、Step 0 证据、验证方式和完成条件。
- `docs/PLAN_MAP.md` 是状态、依赖、替代/合并/废弃关系、推荐顺序、阻塞项和证据链接的事实源。
- 总路线图、优先级计划和索引只记录顺序、状态摘要和专项计划链接，不复制字段级方案、枚举、Step 0 细节或完成定义。
- 当专项计划的状态、字段方案、完成条件或验证结果变化时，必须同步 `docs/PLAN_MAP.md` 和所有引用该计划的路线图、优先级计划或索引。
- 验收治理文档时，必须用 `rg` 搜索同名计划、P 编号、状态名和关键字段，检查是否存在重复定义或漂移。
- 如果同一事实在多个文档中重复，保留一个事实源，其他文档改为链接引用。

## 初始化

在目标项目根目录运行：

```bash
python3 scripts/init_plan_governance.py \
  --root . \
  --plan api-compat-migration \
  --title "API 兼容性迁移" \
  --goal "分阶段完成 API 兼容性迁移" \
  --copy-checker \
  --update-claude-md
```

这会创建：

```text
docs/PLAN_MAP.md
docs/plans/api-compat-migration.md
scripts/check_plan_governance.py
CLAUDE.md
```

`--update-claude-md` 会创建或更新 `CLAUDE.md` 中带标记的计划治理章节，只写稳定执行规则，不写具体计划内容。具体计划仍以 `docs/PLAN_MAP.md` 和 `docs/plans/*.md` 为准。

默认不会覆盖已有文件。需要覆盖时显式加：

```bash
--force
```

## 更新已有项目

如果项目已经有 `docs/PLAN_MAP.md` 和 `docs/plans/*.md`，不要重新初始化计划文档。只让 Claude Code 遵循最新执行规则时运行：

```bash
python3 scripts/init_plan_governance.py \
  --root . \
  --update-claude-md-only
```

如果要升级已有项目的辅助文件，刷新检查脚本并更新 `CLAUDE.md`，但不覆盖 `docs/`，运行：

```bash
python3 scripts/init_plan_governance.py \
  --root . \
  --upgrade-existing
```

`--upgrade-existing` 会：

- 覆盖更新 `scripts/check_plan_governance.py`
- 创建或更新 `CLAUDE.md` 中带标记的计划治理章节
- 保留已有 `docs/PLAN_MAP.md` 和 `docs/plans/*.md`
- 提示缺失的治理文档

## 检查

在仓库根目录运行：

```bash
python3 scripts/check_plan_governance.py .
```

当前检查项包括：

- `PLAN_MAP.md` 引用的计划文件是否存在。
- 计划状态是否合法。
- 计划依赖是否存在环。
- 已完成计划是否有 Step 0 证据和验证方式。
- 实施中计划是否依赖已替代、已合并或已废弃计划。
- 实施中计划是否仍有未解决的当前阶段阻塞项。
- 已完成计划是否有测试覆盖率证据。

## 测试覆盖率

本项目使用 `pytest` 和 `pytest-cov` 作为测试与覆盖率门禁。首次运行前安装开发依赖：

```bash
python3 -m pip install -r requirements-dev.txt
```

运行测试：

```bash
python3 -m pytest
```

覆盖率规则定义在 `pyproject.toml`：

- 统计 `scripts/` 下的 Python 代码。
- 开启分支覆盖率。
- 总覆盖率低于 85% 时测试失败。
- CI 会同时运行测试覆盖率检查和计划治理检查。

## 状态

统一使用中文状态：

| 状态 | 含义 |
|---|---|
| `候选` | 记录了想法，但尚未承诺实施 |
| `设计中` | 正在明确范围、契约和门禁 |
| `待实施` | 当前阶段门禁已通过，但尚未开始 |
| `实施中` | 当前阶段正在修改代码或文档 |
| `已完成` | 实现、测试、证据和文档已同步 |
| `已替代` | 被另一个计划取代 |
| `已合并` | 并入另一个计划 |
| `已废弃` | 明确不再推进 |

## Codex 使用方式

如果已经安装本地 Codex skill，可以在对话中触发：

```text
$plan-governance 为这个项目初始化计划治理，计划名是 api-compat-migration，标题是 API 兼容性迁移。
```

或继续推进已有计划：

```text
$plan-governance 继续推进 docs/plans/api-compat-migration.md 的当前阶段，完成后记录验证证据。
```

skill 只负责让 Codex 按流程工作；真实计划状态仍然保存在项目仓库的 `docs/` 中。

## 核心规则

- 普通任务直接做，不引入治理。
- 当前阶段写细，后续阶段写粗。
- 实施前先固定 Step 0 证据。
- 决策、计划、契约和证据各有权威位置，不重复定义同一事实。
- 路线图和优先级计划只保留排序、状态摘要和链接，不复制专项计划细节。
- 验收治理文档时必须做反向引用检查。
- 如果新信息改变计划顺序、公共契约、兼容承诺或完成条件，先更新治理文档，再继续实施。

完整设计见 [plan-governance-design.md](plan-governance-design.md)。
