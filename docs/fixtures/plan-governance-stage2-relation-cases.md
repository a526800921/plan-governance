# 计划治理阶段 2 关系校验样本

本文件是阶段 2 的 Step 0 设计样本，不是当前 `PLAN_MAP.md` 的关系事实源。阶段 2 计划复用现有 `check` 入口：默认模式报告 WARNING，`--strict-readiness` 将结构错误提升为 ERROR；不会新增独立关系查询命令。

## 候选机器契约

`PLAN_MAP.md` 的 `阶段关系` 表继续作为唯一关系事实源，固定七列：

`来源计划 | 来源阶段 | 目标计划 | 目标阶段 | 关系类型 | 解除条件 | 证据`

关系类型只有：

- `hard_gate`：目标阶段进入实施前必须满足解除条件。
- `evidence`：目标阶段需要来源阶段提供证据，但不自动改变目标阶段生命周期。
- `soft_context`：只提供排序或上下文，不形成阻塞门。

计划级依赖列只作兼容摘要：有阶段关系时，只对同一来源/目标计划对的 `hard_gate` 缺少旧依赖项发出 WARNING；旧依赖中没有对应阶段关系的额外项保留为旧的计划级约束，不被覆盖，也不强制回填阶段关系。没有阶段关系时，旧依赖按 legacy plan-level hard gate 读取。

共享写入约束不放入阶段关系边表，单独使用固定九列表：

`来源计划 | 来源阶段 | 目标计划 | 目标阶段 | 约束类型 | 共享目标 | 串行顺序 | 解除条件 | 证据`

其中 `约束类型` 当前只允许 `shared_write_risk`；该约束只限制写入顺序，不改变业务依赖关系。现有四列表 `并行与共享写入约束` 是人工说明，只有九列表存在时才启用机器校验；只有四列表或两者混用均保持兼容，九列表是机器校验的优先事实源，四列表不反向覆盖九列表。

## 样本矩阵

| 案例 | 输入或基线 | 可执行命令 | 预期退出码/输出 | 失败判定 | 输出位置 |
|---|---|---|---|---|---|
| R1 合法硬门禁 | `tests/fixtures/plan-governance-stage2-relations/valid/docs/PLAN_MAP.md` 的登记计划、`hard_gate`、解除条件和证据 | `python3 -m pytest -q --no-cov tests/test_check_plan_governance.py -k stage2_relation_fixture_valid` | 0；输出 `计划治理检查通过` | 把缺失计划、阶段或解除条件当成合法 | pytest stdout |
| R2 软上下文和证据 | valid fixture 中同时存在 `soft_context`、`evidence` 和 `hard_gate` | `python3 -m pytest -q --no-cov tests/test_check_plan_governance.py -k stage2_relation_fixture_accepts_soft_context` | 0；软关系不形成阻塞，证据关系不改变阶段生命周期 | 将 `soft_context` 或共享风险误当硬门禁 | pytest stdout |
| R3 引用错误 | `invalid-reference/docs/PLAN_MAP.md` 含来源计划缺失、阶段格式错误、阶段 99、未知类型和空字段 | `python3 -m pytest -q --no-cov tests/test_check_plan_governance.py -k stage2_relation_fixture_invalid` | 默认 0 且 WARNING；严格 1 且 ERROR；workset 并行状态为 unknown | 错误关系仍被 `workset` 当成确定并行证据 | pytest stdout/JSON |
| R4 依赖环 | `cycle/docs/PLAN_MAP.md` 含 hard_gate/evidence 多节点环和 soft_context 自环 | `python3 -m pytest -q --no-cov tests/test_check_plan_governance.py -k stage2_relation_fixture_cycle` | 默认 0 且提示环/自环；严格 1 | 允许循环门禁继续通过 | pytest stdout |
| R5 旧依赖兼容 | `legacy/docs/PLAN_MAP.md` 只有旧计划级依赖；`legacy-conflict/docs/PLAN_MAP.md` 的阶段 `hard_gate` 与旧依赖列冲突 | `python3 -m pytest -q --no-cov tests/test_check_plan_governance.py -k 'stage2_legacy'` | 旧地图默认/严格均 0；冲突只 WARNING；workset 不覆盖旧依赖 | 强制历史计划迁移、把额外旧依赖静默删除或把 WARNING 升为 ERROR | pytest stdout/JSON |
| R6 共享写入风险 | `shared-write-invalid/docs/PLAN_MAP.md` 含九列表但约束类型、目标和顺序非法；`shared-write-legacy/docs/PLAN_MAP.md` 只有四列表；`shared-write-conflict/docs/PLAN_MAP.md` 验证九列表优先 | `python3 -m pytest -q --no-cov tests/test_check_plan_governance.py -k 'stage2_shared_write or stage2_legacy_four_column or stage2_nine_column'` | 3 项通过；非法九列表默认 0 且 WARNING、严格 1；只有四列表默认/严格均 0；冲突时九列表严格通过 | 把共享文件重叠自动转换为业务依赖，或允许同时写入 | pytest stdout |
| R7 只读保证 | valid fixture 的地图和计划文件在 check/workset 前后做 SHA-256 | `python3 -m pytest -q --no-cov tests/test_check_plan_governance.py -k stage2_relation_queries_are_read_only` | 0；前后 hash 相同 | 检查过程写回关系、状态或快照 | pytest stdout |

## 可执行基线命令

每个 fixture 本身就是可直接传给 CLI 的项目根，包含 `<root>/docs/PLAN_MAP.md` 和 `<root>/docs/plans/`。直接回放可使用：

```bash
node bin/plan-governance-cli.mjs check \
  tests/fixtures/plan-governance-stage2-relations/valid --strict-readiness
```

```bash
node bin/plan-governance-cli.mjs check .
node bin/plan-governance-cli.mjs check . --strict-readiness
rg -n '阶段关系|hard_gate|evidence|soft_context|shared_write_risk|R[1-7]' \
  docs/PLAN_MAP.md docs/fixtures/plan-governance-stage2-relation-cases.md
git diff --check
```

阶段 2 实现后，追加临时目录正反样本、默认/严格退出码、旧依赖兼容、环检测、共享写入顺序和前后 hash 回归；不修改 `motorcycle-manual-app`。
