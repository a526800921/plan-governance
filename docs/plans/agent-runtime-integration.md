# 计划：agent-runtime-integration

## 背景

对 `planning-with-files` 的分析表明，它最值得借鉴的不是根目录三文件模板，而是把计划治理重新带回 Agent 生命周期的运行时机制。

但 `plan-governance` 已经有自己的事实源体系：`docs/PLAN_MAP.md` 负责状态、当前阶段、最后更新、依赖和证据链接，`docs/plans/*.md` 负责专项计划细节、Step 0 证据、验证方式和完成条件。因此本计划只保留明确值得做、且能增强现有治理闭环的能力：

1. 最小 Agent hooks runtime：让 Agent 在关键操作前后自动读取和检查治理文档。
2. 完成快照和 hash 认证：检测已完成计划的后续漂移。
3. 作用域匹配增强：让 hooks 和 drift 检查只关注与当前变更相关的活跃计划。

本计划依赖已完成的 [stale-plan-detection](stale-plan-detection.md)、[plan-drift-check-enhancements](plan-drift-check-enhancements.md) 和 [independent-acceptance-rules](independent-acceptance-rules.md)。

## 目标

- 增加项目内 hook 脚本入口，让治理文档在 `session-start`、写入前、写入后和停止前自动参与 Agent 工作流。
- 增加完成快照或 hash 认证机制，使已完成计划被修改时能输出可复核 warning。
- 增强 `影响模块或文件` 的解析和匹配，让 active plan 检查按路径收敛，减少无关计划噪声。

## 非目标

- 不引入 `planning-with-files` 的 `task_plan.md`、`findings.md`、`progress.md`。
- 不实现独立运行账本；当前阶段看不到它比 `PLAN_MAP.md`、计划正文、Git diff 和测试输出带来足够收益。
- 不实现完整会话恢复；Agent 恢复应先通过读取 `PLAN_MAP.md`、相关计划和 Git 状态解决。
- 不自动修改计划状态、当前阶段或 `最后更新`。
- 不默认安装或修改用户全局 hooks 配置。
- 不让 Stop hook 默认阻塞会话；先提示和检查，后续除非有明确收益和安全边界，否则不做 gate。
- 不用自然语言推断业务完成度、契约变更或验收结论。

## 不变量

- `docs/PLAN_MAP.md` 继续作为状态、当前阶段、最后更新、依赖、阻塞项和证据链接事实源。
- `docs/plans/*.md` 继续作为专项计划实施细节事实源。
- Hooks 只能提醒、摘要、运行已有检查或输出 warning；不能静默改写治理事实。
- 完成快照或 hash 告警必须保留人工复核边界，不能把正常文档修正直接视为错误。
- 需要人工判断的场景优先输出 `WARNING`，不改变既有检查脚本的轻量治理定位。

## 影响模块或文件

- `scripts/init_plan_governance.py`
- `scripts/check_plan_governance.py`
- `scripts/plan_governance_hook.py`
- `tests/test_init_plan_governance.py`
- `tests/test_check_plan_governance.py`
- `tests/test_plan_governance_hooks.py`
- `README.md`
- `plan-governance-design.md`
- `docs/PLAN_MAP.md`
- `docs/plans/agent-runtime-integration.md`
- `/Users/jafish/.codex/skills/plan-governance/SKILL.md`

## 公共契约变化

本计划只引入三类公共能力。

### 1. 最小 hooks runtime

新增项目内脚本入口，供 Codex、Claude Code 或其他 Agent hook 配置调用。第一阶段只提供脚本和生成说明，不自动写用户全局配置。

候选入口：

```bash
python3 scripts/plan_governance_hook.py --event session-start
python3 scripts/plan_governance_hook.py --event pre-write --paths scripts/check_plan_governance.py
python3 scripts/plan_governance_hook.py --event post-write --paths docs/PLAN_MAP.md
python3 scripts/plan_governance_hook.py --event stop
```

事件语义：

| 事件 | 行为 | 阻塞语义 |
|---|---|---|
| `session-start` | 摘要 `PLAN_MAP.md` 中的活跃计划、当前阶段、阻塞项和证据链接 | 不阻塞 |
| `pre-write` | 写入前提示当前阶段门禁、影响范围、Step 0 和公共契约约束 | 不阻塞 |
| `post-write` | 写入后提示是否需要同步 `PLAN_MAP.md`、完成证据、测试覆盖率和反向引用 | 不阻塞 |
| `stop` | 运行基础治理检查，可选串联 `--drift` 和 `--stale-days` | 不阻塞 |

输出应短、稳定、可测试。不要把完整计划正文反复注入上下文。

### 2. 完成快照和 hash 认证

新增完成快照元数据，用于检测已完成计划在完成后是否被修改。元数据不得写入计划正文自身，以避免自引用 hash。

候选位置：

```text
docs/attestations/<plan-name>.json
```

候选字段：

```json
{
  "plan": "agent-runtime-integration",
  "phase": "阶段 1",
  "status": "已完成",
  "plan_sha256": "<sha256>",
  "plan_map_sha256": "<sha256>",
  "created_at": "2026-07-06T00:00:00Z",
  "created_by": "agent-or-user",
  "reason": "阶段完成快照"
}
```

检查语义：

- 已完成计划存在 attestation 且 hash 变化时输出 `WARNING`。
- 缺少 attestation 不应自动失败；需要先通过计划或命令显式启用该门禁。
- 重新验收并确认文档修正合理后，可以重建 attestation。

### 3. 作用域匹配增强

优先增强 `docs/plans/*.md` 的 `影响模块或文件` 解析，让 hooks 和 `--drift` 能按路径选择相关活跃计划。暂不新增 `PLAN_MAP.md` 列，避免过早扩大 schema。

推荐表达：

```markdown
## 影响模块或文件

- `scripts/`
- `tests/`
- `docs/plans/agent-runtime-integration.md`
```

匹配规则：

- 文件精确匹配。
- 目录前缀匹配。
- 活跃计划没有声明影响范围时输出 warning。
- 多个活跃计划覆盖同一路径时输出 warning，由用户确认推进顺序。

## 阶段路线图

| 阶段 | 目标 | 进入条件 | 验证方向 | 状态 |
|---|---|---|---|---|
| 阶段 0 | 固定运行时集成的最小值得做范围 | `planning-with-files` 分析和本仓库现状已确认 | 计划登记、治理检查和反向引用检查通过 | 已完成 |
| 阶段 1 | 增加最小 hooks runtime 脚本入口 | 阶段 0 完成，确认不自动修改全局配置 | hook 脚本测试、治理检查通过 | 已完成 |
| 阶段 2 | 增加完成快照和 hash 认证 | 阶段 1 完成，完成快照元数据结构确定 | hash 变化 warning 测试、治理检查通过 | 已完成 |
| 阶段 3 | 增强作用域匹配 | 阶段 2 完成，真实 hooks 使用暴露噪声点 | drift/hook 路径匹配测试、文档同步通过 | 候选 |

## 阶段 1 设计补充

阶段 1 只实现最小 hooks runtime。该阶段不安装真实 hooks，不修改全局配置，不自动写治理文档。

### Hook 事件契约

`scripts/plan_governance_hook.py` 只支持以下事件：

```bash
python3 scripts/plan_governance_hook.py --event session-start
python3 scripts/plan_governance_hook.py --event pre-write --paths <path> [<path> ...]
python3 scripts/plan_governance_hook.py --event post-write --paths <path> [<path> ...]
python3 scripts/plan_governance_hook.py --event stop
```

事件行为：

| 事件 | 输入 | 读取 | 输出 |
|---|---|---|---|
| `session-start` | 无 | `docs/PLAN_MAP.md` | 活跃计划、当前阶段、最后更新、阻塞项和证据链接摘要 |
| `pre-write` | 计划写入的路径列表 | `docs/PLAN_MAP.md`、匹配活跃计划的 `影响模块或文件` | 匹配到的计划、当前阶段门禁、Step 0 和公共契约提醒 |
| `post-write` | 已写入的路径列表 | `docs/PLAN_MAP.md`、相关计划文件 | 是否需要同步状态、证据、测试覆盖率和反向引用检查的提醒 |
| `stop` | 无 | `docs/PLAN_MAP.md`、`docs/plans/*.md` | `python3 scripts/check_plan_governance.py .` 的结果摘要 |

路径匹配第一阶段沿用现有规则：

- 文件精确匹配。
- 目录前缀匹配。
- `pre-write` 只提示匹配到的活跃计划。
- 写入路径没有匹配活跃计划时，输出“未匹配到相关活跃计划”的短提示，不阻塞。

### 只读边界

阶段 1 的 hook 脚本必须满足：

- 不修改任何文件。
- 不更新 `PLAN_MAP.md` 的 `最后更新`。
- 不自动改变计划状态、当前阶段、证据或阻塞项。
- 不注入完整计划正文。
- 不安装或修改 `.codex/hooks.json`、`CLAUDE.md`、`AGENTS.md`、`~/.codex/config.toml` 或其他全局配置。
- 不把 `stop` 事件升级为强阻塞 gate。

### Step 0 fixture

阶段 1 实施前先用测试 fixture 固定最小行为：

```text
tmp/
  docs/
    PLAN_MAP.md
    plans/
      active-runtime-plan.md
      completed-plan.md
  scripts/
    check_plan_governance.py
```

Fixture 内容要求：

- `PLAN_MAP.md` 包含 1 个 `实施中` 计划和 1 个 `已完成` 计划。
- `active-runtime-plan.md` 的 `影响模块或文件` 包含 `scripts/` 和 `tests/`。
- `completed-plan.md` 用于确认已完成计划不会被 `pre-write` 当作活跃计划注入。
- `scripts/check_plan_governance.py` 可以用最小 stub 固定 `stop` 事件的调用和输出。

必须覆盖的测试：

- `session-start` 输出活跃计划摘要，不输出完整计划正文。
- `pre-write --paths scripts/foo.py` 能匹配 `active-runtime-plan`。
- `pre-write --paths README.md` 输出未匹配相关活跃计划。
- `post-write --paths docs/PLAN_MAP.md` 提醒同步状态、证据和反向引用检查。
- `post-write --paths docs/plans/active-runtime-plan.md` 提醒同步 `PLAN_MAP.md` 和验证证据。
- `stop` 调用治理检查并转发摘要，但不把 warning 当作阻塞失败。
- 四类事件执行后 fixture 文件内容保持不变。

### 阶段 1 完成条件

- 新增 `scripts/plan_governance_hook.py`。
- 新增 `tests/test_plan_governance_hooks.py`，覆盖四个事件和只读边界。
- hook 输出保持短摘要，不反复注入完整计划正文。
- `stop` 事件运行治理检查但不实现强阻塞 gate。
- README、已安装 skill 或代理规则只说明手动接入方式，不自动安装 hooks。
- `python3 -m pytest` 通过并记录覆盖率。
- `python3 scripts/check_plan_governance.py .` 通过。

## 当前阶段

### 范围

阶段 2 增加完成快照和 hash 认证，用于检测已完成计划在完成后是否发生未复核修改。

当前阶段只实现显式命令和 warning 级检查。它不自动锁定所有已完成计划，不阻断基础治理检查，不把正常文档修正直接判定为错误。

阶段 2 固定以下契约：

- attestation 文件位置：`docs/attestations/<plan-name>.json`。
- hash 覆盖范围：对应 `docs/plans/<plan-name>.md` 和 `docs/PLAN_MAP.md`。
- 创建命令：`python3 scripts/check_plan_governance.py . --attest <plan-name>`。
- 检查命令：`python3 scripts/check_plan_governance.py . --check-attestations`。
- `--check-attestations` 对 hash 变化、引用缺失或 JSON 损坏输出 `WARNING`，不改变退出码。
- `--attest` 只对已登记到 `PLAN_MAP.md` 的计划创建或覆盖快照；未登记计划返回 `ERROR`。
- 重新验收并确认文档修正合理后，可以再次运行 `--attest <plan-name>` 重建快照。

### 实施步骤

1. 在 `tests/test_check_plan_governance.py` 增加 attestation fixture。
2. 增加 SHA-256 计算函数，使用文件字节内容计算 hash。
3. 在 `scripts/check_plan_governance.py` 增加 `--attest <plan-name>`。
4. `--attest` 读取 `PLAN_MAP.md` 中登记的计划路径，创建 `docs/attestations/<plan-name>.json`。
5. 在 `scripts/check_plan_governance.py` 增加 `--check-attestations`。
6. `--check-attestations` 读取 `docs/attestations/*.json`，对比当前文件 hash。
7. 更新 README、已安装 skill 和本计划完成证据。
8. 运行测试、治理检查、attestation 小样本验证和反向引用搜索。

### Step 0 证据

阶段 2 的 Step 0 fixture：

```text
tmp/
  docs/
    PLAN_MAP.md
    plans/
      completed-plan.md
    attestations/
      completed-plan.json
```

Fixture 内容要求：

- `PLAN_MAP.md` 登记 `completed-plan`，状态为 `已完成`。
- `completed-plan.md` 包含有效 Step 0 证据、验证方式和测试覆盖率证据。
- `--attest completed-plan` 生成 `docs/attestations/completed-plan.json`。
- 修改 `completed-plan.md` 后，`--check-attestations` 输出 hash 变化 `WARNING`，但返回码仍为 0。
- 修改 `docs/PLAN_MAP.md` 后，`--check-attestations` 输出 `PLAN_MAP.md` hash 变化 `WARNING`，但返回码仍为 0。
- JSON 损坏、计划文件缺失、attestation 指向未登记计划时，`--check-attestations` 输出 `WARNING`，不改变基础检查退出码。

这些 fixture 固定了阶段 2 的核心边界：快照用于提示复核，不用于自动阻断或自动判定文档修正非法。

### 验证方式

阶段 2 验证命令：

```bash
python3 -m pytest
python3 scripts/check_plan_governance.py .
python3 scripts/check_plan_governance.py . --check-attestations
rg -n "agent-runtime-integration|attestation|attest|check-attestations|完成快照|hash|sha256" docs README.md plan-governance-design.md scripts tests
rg -n "草案为准|以草案为事实源|详见草案|draft is source|source of truth.*draft|以.*draft.*为准" .
```

预期结果：

- pytest 通过且覆盖率高于 85%。
- 治理检查通过。
- attestation 相关事实同步到计划、README、脚本、测试和已安装 skill。
- `--check-attestations` 无快照时可安静通过；存在快照漂移时输出 `WARNING` 且返回码为 0。
- 未发现旧草案或临时分析文档重新成为事实源。

### 测试覆盖率

`python3 -m pytest` 通过，77 项测试全部通过，pytest-cov 总覆盖率 92.46%，高于 85% 门禁。

### 完成条件

- `scripts/check_plan_governance.py` 支持 `--attest <plan-name>`。
- `scripts/check_plan_governance.py` 支持 `--check-attestations`。
- `docs/attestations/<plan-name>.json` 的字段结构稳定并有测试覆盖。
- hash 覆盖对应计划文件和 `docs/PLAN_MAP.md`。
- hash 变化、文件缺失、JSON 损坏和未登记计划均输出 `WARNING`，不改变检查退出码。
- 未登记计划执行 `--attest` 返回 `ERROR`。
- README 和已安装 skill 记录命令和 warning 语义。
- `python3 -m pytest` 通过并记录覆盖率。
- `python3 scripts/check_plan_governance.py .` 通过。
- `python3 scripts/check_plan_governance.py . --check-attestations` 通过。
- 反向引用和草案事实源搜索通过。

### 完成证据

- `scripts/check_plan_governance.py` 已支持 `--attest <plan-name>`，为已登记计划创建或覆盖 `docs/attestations/<plan-name>.json`。
- `scripts/check_plan_governance.py` 已支持 `--check-attestations`，检查计划文件和 `docs/PLAN_MAP.md` 的 hash 漂移。
- `tests/test_check_plan_governance.py` 已覆盖快照创建、未登记计划 attest 失败、hash 匹配、计划文件 hash 变化、`PLAN_MAP.md` hash 变化、坏 JSON 和未登记快照 warning。
- README 已记录完成快照命令和 warning 语义。
- 已安装 skill `/Users/jafish/.codex/skills/plan-governance/SKILL.md` 已同步 attestation 命令说明。
- 真实仓库小样本验证：`python3 scripts/check_plan_governance.py . --attest agent-runtime-integration` 创建快照后，`python3 scripts/check_plan_governance.py . --check-attestations` 通过；临时快照已删除，避免提交验收产物。
- `python3 -m pytest` 通过，77 项测试全部通过，pytest-cov 总覆盖率 92.46%。
- `python3 scripts/check_plan_governance.py .` 输出 `计划治理检查通过。`
- `python3 scripts/check_plan_governance.py . --check-attestations` 输出 `计划治理检查通过。`
- `rg -n "agent-runtime-integration|attestation|attest|check-attestations|完成快照|hash|sha256" docs README.md plan-governance-design.md scripts tests` 已确认计划、README、脚本、测试和 `PLAN_MAP.md` 同步。
- `rg -n "草案为准|以草案为事实源|详见草案|draft is source|source of truth.*draft|以.*draft.*为准" .` 未发现旧草案重新成为事实源；命中均为规则文本、历史计划或本计划验证命令。

## 未决问题

| 问题 | 推荐方案 | 是否阻塞当前阶段 | 状态 |
|---|---|---|---|
| 第一阶段是否生成真实 `.codex/hooks.json`？ | 阶段 1 先生成项目内脚本和文档说明；真实 hook 配置作为可选输出，避免误改用户全局配置。 | 否 | 待决定 |
| Stop hook 是否应阻塞？ | 当前不做；除非后续有明确 gate 收益和防循环边界。 | 否 | 待决定 |
| attestation 元数据是否进入 `docs/attestations/`？ | 阶段 2 已决定使用 `docs/attestations/<plan-name>.json`，且不写入计划正文自身。 | 否 | 已决定 |

## 风险和回滚

风险：hooks 过度注入计划内容，导致普通任务也被治理流程接管。

控制：第一阶段只输出短摘要和检查提示，不注入完整计划正文；继续保留普通小任务跳过治理的规则。

风险：hash 认证误伤合理文档修正。

控制：hash 变化先输出 `WARNING`，并要求人工复核后重建完成快照。

风险：作用域匹配过严导致真实相关计划未被提示。

控制：缺少影响范围时提示 warning，不阻塞；路径匹配先保持简单透明。

回滚：删除本计划在 `docs/PLAN_MAP.md` 的登记，将 `docs/plans/agent-runtime-integration.md` 标记为 `已废弃` 或移除；后续阶段若已实现脚本，则按对应阶段回滚脚本、测试和文档。

## 关联 ADR、迁移、spec 或 issue

- 外部参考：`planning-with-files` hooks 和 attestation 设计。
- 依赖计划：[stale-plan-detection](stale-plan-detection.md)
- 依赖计划：[plan-drift-check-enhancements](plan-drift-check-enhancements.md)
- 依赖计划：[independent-acceptance-rules](independent-acceptance-rules.md)
