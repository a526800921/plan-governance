# 计划：codex-skill-rollout

## 背景

`plan-governance-design.md` 定义了轻量治理模型，包括分阶段计划、Step 0 证据、ADR、迁移说明和一致性检查。下一步是让它可以被 Codex 实际使用，而不是只停留在设计文档中。

## 目标

创建一个本地 Codex skill，让 Codex 知道何时、如何应用计划治理，并提供可复用模板和基础检查脚本。

## 非目标

- 不把治理流程强加给一次性任务。
- 不在每个项目里预建空的 ADR 或 migration 目录。
- 不替代 issue tracker、CI、release 管理或项目管理工具。

## 不变量

- 真实项目状态保存在仓库的 `docs/` 文件中，不保存在 skill 内。
- skill 只定义工作流和启用启发式规则。
- 机械一致性检查交给脚本。
- 当前阶段写细，后续阶段写粗。

## 影响模块或文件

- `/Users/jafish/.codex/skills/plan-governance/SKILL.md`
- `/Users/jafish/.codex/skills/plan-governance/assets/`
- `/Users/jafish/.codex/skills/plan-governance/scripts/check_plan_governance.py`
- `docs/PLAN_MAP.md`
- `docs/plans/codex-skill-rollout.md`
- `scripts/check_plan_governance.py`

## 公共契约变化

Codex skill 名称是 `plan-governance`。用户可以用 `$plan-governance` 显式触发，也可以自然描述“管理分阶段计划、ADR、迁移、Step 0 证据或 PLAN_MAP.md”来触发。

## 阶段路线图

| 阶段 | 目标 | 进入条件 | 验证方向 | 状态 |
|---|---|---|---|---|
| 阶段 0 | 将设计转成 Codex 工作流 | 设计文档已存在 | skill 文件有效 | 已完成 |
| 阶段 1 | 添加项目级示例和检查脚本 | skill 已存在 | 检查脚本在本仓库通过 | 已完成 |
| 阶段 2 | 添加确定性初始化脚本 | 用户要求可通过 skill 触发初始化 | 临时目录初始化和检查通过 | 已完成 |
| 阶段 3 | 根据真实使用继续改进 | 真实任务暴露摩擦点 | 带证据更新 skill 或脚本 | 候选 |

## 当前阶段

### 范围

阶段 2 添加确定性初始化脚本，让 Codex 触发 `$plan-governance` 时可以直接调用脚本初始化项目；用户也可以手动运行脚本。

### 实施步骤

1. 添加 `scripts/init_plan_governance.py`。
2. 支持 `--root`、`--plan`、`--title`、`--goal`、`--status`、`--phase`、`--copy-checker` 和 `--force`。
3. 默认创建 `docs/PLAN_MAP.md` 和 `docs/plans/<plan>.md`。
4. 默认不覆盖已有文件。
5. 更新 skill 使用说明。
6. 在临时目录验证初始化结果可通过检查脚本。

### Step 0 证据

基线是已有设计文档 `plan-governance-design.md` 和已落地的中文模板。它们已经定义目标文档模型、状态生命周期、Step 0 证据规则、漂移检查和最低自动化检查项。

### 验证方式

运行：

```bash
python3 /Users/jafish/.codex/skills/.system/skill-creator/scripts/quick_validate.py /Users/jafish/.codex/skills/plan-governance
python3 scripts/check_plan_governance.py .
tmp_dir="$(mktemp -d)"
python3 scripts/init_plan_governance.py --root "$tmp_dir" --plan api-compat-migration --title "API 兼容性迁移" --goal "分阶段完成 API 兼容性迁移" --copy-checker
python3 "$tmp_dir/scripts/check_plan_governance.py" "$tmp_dir"
```

预期结果：

- skill 校验通过
- 仓库计划治理检查通过
- 临时目录初始化成功
- 初始化后的临时目录治理检查通过

### 测试覆盖率

2026-06-27 运行 `python3 -m pytest`，结果为 26 个测试通过，总覆盖率 98.88%，超过 85% 覆盖率门禁。

### 完成条件

- 本地 Codex skill 已存在。
- skill 包含模板和检查脚本。
- skill 包含初始化脚本。
- 本仓库有 `docs/PLAN_MAP.md` 和一个具体 rollout 计划。
- 验证命令通过。

## 未决问题

| 问题 | 推荐方案 | 是否阻塞当前阶段 | 状态 |
|---|---|---|---|
| 是否后续做成可分发 plugin？ | 等本地 skill 在真实项目中使用后再决定。 | 否 | 已延后 |

## 风险和回滚

风险：这个流程对小任务可能过重。

回滚：对不需要治理的项目，删除或忽略 `docs/PLAN_MAP.md`；skill 的启用规则已经要求跳过普通一次性任务。

## 关联 ADR、迁移、spec 或 issue

- `plan-governance-design.md`
