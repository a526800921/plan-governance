# autonomous-plan-execution 阶段 3：模板、skill 与说明文档样本

本文件是阶段 3 的 Step 0 基线与实施验收 fixture。阶段 3 只同步仓库内的模板、分发 skill、代理元数据和 README；不修改全局 CLI/skill、不自动安装 hook、不改变阶段 1/2 的 CLI 契约。

## 公共约束

- 自主模式必须默认关闭；只有计划正文明确声明 `execution_mode: autonomous-continuous` 且提供 `执行清单` 时才启用。
- `plan-governance-cli init` 生成的普通计划不得因为模板新增说明而进入 `not_enabled` 以外的自主步骤解析路径。
- “推进到完成计划”只代表连续推进授权，不代表跳过 Step 0、验证、独立复核、阶段门或完成验收。
- 阶段 3 的回放只使用临时目录或当前仓库；不触碰 `/Users/jafish/.codex`、`/Users/jafish/.claude` 或其他项目。

## Step 0：实现前基线

基线类型为“源资源快照 + 包内初始化器生成计划的兼容回放 + 当前仓库真实计划只读回放”。

### B1：模板和生成器基线

输入或基线：实现前快照中，`resources/skill/assets/plan.template.md` 只有通用治理章节，没有自主模式模板段落；`scripts/init_plan_governance.py` 从该模板生成计划。

可执行命令：

```bash
tmp_root="$(mktemp -d)"
python3 scripts/init_plan_governance.py \
  --root "$tmp_root/project" \
  --plan demo \
  --title "阶段 3 基线计划" \
  --goal "验证模板兼容性"
node bin/plan-governance-cli.mjs plan steps validate demo --json --root "$tmp_root/project"
node bin/plan-governance-cli.mjs plan next demo --json --root "$tmp_root/project"
```

预期结果：生成计划可正常创建；两个自主步骤入口均返回 `not_enabled`，退出码为 0；生成计划不需要迁移或补填步骤表。

失败判定：生成失败；普通模板生成计划被标记为 `invalid`；或未显式启用却产生 `ready_steps`。

输出位置：阶段 3 Step 0 命令输出；临时目录在命令结束后清理。

### B2：当前仓库真实计划基线

输入或基线：实现前快照中，`docs/plans/autonomous-plan-execution.md` 是真实治理计划，但自身未声明自主模式；阶段 2 已完成，阶段 3 尚未准入。

可执行命令：

```bash
node bin/plan-governance-cli.mjs plan steps validate autonomous-plan-execution --json
node bin/plan-governance-cli.mjs plan next autonomous-plan-execution --json
```

预期结果：均返回 `not_enabled`；不产生 ready steps，不修改计划、地图、Git 或外部系统。

失败判定：当前计划被误当成已启用自主计划；查询返回阶段 3 ready step；或查询导致工作区变化。

输出位置：CLI JSON 输出和查询前后 Git 状态/hash 对照。

### B3：skill、README 与分发清单基线

输入或基线：实现前快照中，`resources/skill/SKILL.md` 已有“连续推进且不跳步”的策略层规则；`README.md` 尚未提供完整的模板启用方式和 `plan next` 回放说明；`resources/manifest.json` 已纳入 skill、模板和代理元数据。

可执行命令：

```bash
rg -n '自主连续执行|推进到完成|不跳步|plan next' resources/skill/SKILL.md
rg -n '自主连续执行|推进到完成|不跳步|plan next|execution_mode' README.md
node -e 'const m=require("./resources/manifest.json"); console.log(JSON.stringify(m.skill.files))'
npm pack --dry-run --json
```

预期结果：基线命中 skill 策略层规则；README 的完整自主模式说明尚未存在；manifest 能定位所有需分发的资源；`npm pack --dry-run` 不报错。

失败判定：分发清单遗漏模板或 skill；README/skill 对自动执行、自动验收或跳步作出不安全承诺；包内容无法包含源资源。

输出位置：命令输出；阶段 3 实施前后分别保存资源清单和包内容对照。

### B4：兼容与治理基线

可执行命令：

```bash
python3 -m pytest -q
npm test
node bin/plan-governance-cli.mjs check .
node bin/plan-governance-cli.mjs check . --stale-days 10
git diff --check
```

预期结果：实现前基线为 Python 126 passed、总覆盖率 90.67%、npm 40/40；治理和格式检查通过。阶段 3 实施后的 npm 回归以最终验证记录为准。

失败判定：既有阶段 1/2 行为回归失败，或新增阶段 3 设计文档破坏当前治理检查。

输出位置：pytest-cov、Node TAP、治理检查和 diff 输出。

## 阶段 3 验收样本矩阵

| 样本 | 输入或基线 | 可执行命令 | 预期结果 | 失败判定 | 输出位置 |
|---|---|---|---|---|---|
| T1 默认关闭 | 用更新后的模板初始化普通 `demo` 计划 | `python3 scripts/init_plan_governance.py ...; plan steps validate demo --json; plan next demo --json` | 创建成功；返回 `not_enabled`；不产生 ready steps | 普通计划被强制启用或结构无效 | 临时目录 CLI JSON |
| T2 显式启用 | 临时计划去掉示例代码围栏，保留真实 `execution_mode` 和七列表 | `plan steps validate demo --json; plan next demo --json` | 校验 `valid`；按步骤状态返回 ready/blocked；不执行动作 | 仅复制模板就启用、字段被误解析或跳过前置 | 临时目录 CLI JSON |
| T3 当前真实计划 | 当前 `autonomous-plan-execution` 计划 | `plan next autonomous-plan-execution --json` | 保持 `not_enabled`；阶段 3 不自动进入 ready | 真实计划状态被模板同步意外改变 | 当前仓库输出与 Git 状态 |
| T4 运行时规则 | 更新后的 skill、代理元数据和 README | `rg -n '推进到完成|不跳步|plan next|独立复核|自动执行' resources/skill README.md resources/skill/agents/openai.yaml` | 明确连续推进、不逐步询问、每步执行、异常暂停；不声称自动验收/自动执行 | 说明缺失、互相矛盾或把短指令写成跳过门禁 | 反向引用搜索输出 |
| T5 分发回归 | npm 包资源清单和临时 setup 目标 | `npm pack --dry-run --json; node bin/plan-governance-cli.mjs setup --target codex --dry-run --destination <tmp>` | 模板、skill、代理元数据一致可分发；不触碰全局目录 | 包漏资源、setup 目标写入全局或覆盖本地改动 | npm 输出与临时目标 |
| T6 回滚演练 | 临时复制的模板/skill/README 变更 | `git diff --check; git show HEAD:<path> > <tmp>/before` 或等价临时对照 | 能恢复阶段 3 资源而不影响阶段 1/2 CLI 和旧计划兼容 | 回滚要求全局同步、破坏旧计划或无法定位资源边界 | 临时对照 hash 与 Git 状态 |

## 失败与安全边界

- 普通计划兼容失败时，停止模板/skill/README 实施，保留阶段 1/2 的 CLI 和检查器实现。
- 如果运行时说明导致执行者把 `plan next` 当作自动执行器或把 `complete` 当作独立验收，撤回说明变更并保留只读查询契约。
- 如果包或 setup 回归需要同步全局目录，阶段 3 不执行该动作；改用临时目标验证，并记录为未覆盖的外部分发风险。
- 阶段 3 不修改 `docs/PLAN_MAP.md` 之外的其他项目，不创建 ADR/migration；当前方案保持旧计划兼容，不需要迁移。
