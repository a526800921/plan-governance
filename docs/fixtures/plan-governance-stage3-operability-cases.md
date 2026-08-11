# 计划治理阶段 3 可操作性收口样本

本文件是阶段 3 的 Step 0 设计样本，不是 `PLAN_MAP.md` 或专项计划的事实源。阶段 3 只收口治理 drift 覆盖、状态/进展/attestation 分层以及模板/文档兼容；不做全量历史迁移，不把普通 attestation 漂移自动升级为失败，也不修改目标业务项目。

## 候选契约

### Drift 精确归属

- `--drift` 与 `--pre-commit` 使用同一套归属语义。
- 活跃计划自身文件、`PLAN_MAP.md` 中可唯一归属到该计划的索引行、当前阶段显式声明的相对证据文件，属于该计划的覆盖范围。
- 跨计划或无法唯一归属的地图变更继续输出 `WARNING`；未被任何活跃计划声明的文件继续输出 `WARNING`。
- 不通过全局忽略 `docs/` 消除告警；计划目标重叠只提示 `WARNING`，不自动制造业务依赖。
- `### 阶段证据` 只接受仓库内相对路径，不接受绝对路径、通配符或越界路径。

### 状态、进展和 Attestation 分层

- `最新独立准入复核` 只回答当前阶段是否达到准入标准。
- `最近实施/验证记录` 采用追加式记录，记录动作、结果和证据，不覆盖独立准入结论，也不自动改变计划状态。
- 旧格式 `docs/attestations/<plan>.json` 缺少 `purpose` 时按 `phase_completion` 兼容读取。
- 新快照使用 `purpose`、`snapshot_id`、`supersedes`、`review_status`；`purpose` 只允许 `phase_completion`、`release_gate`、`compliance`，`review_status` 只允许 `current`、`superseded`、`needs_review`。
- hash 漂移输出 `WARNING`；`release_gate` 和 `compliance` 不因机械检查自动接受。
- 同一计划/purpose 只有一个有效 `current`；缺失替代目标、替代环、重复 current 和非法快照结构属于结构错误。

### 模板和历史兼容

- 新模板包含阶段证据、最近实施/验证记录和最小 attestation 说明，但既有计划不因新增可选字段而被强制迁移。
- 只在临时初始化 fixture 中验证新模板；不覆盖真实用户目录，不移动或删除历史计划、ADR、migration 或 attestation。
- 失败时保留旧命令、旧快照和旧计划解析行为，撤回新增可选字段及对应测试即可。

## 样本矩阵

| 案例 | 输入或基线 | 可执行命令 | 预期退出码/输出 | 失败判定 | 输出位置 |
|---|---|---|---|---|---|
| S1 Drift 精确覆盖 | 阶段证据含合法相对路径；变更包含活跃/已完成计划自身、可唯一归属的地图行、显式证据文件和无关文件 | `python3 -m pytest --no-cov -q tests/test_check_plan_governance.py -k 'drift_completed_plan_closing_window_is_narrow or drift_covers_plan_map_row_plan_file_and_phase_evidence or pre_commit_uses_the_same_plan_map_and_phase_evidence_ownership'` | 0；活跃计划和完成计划关闭窗口的前三类可归属，无关文件和完成计划影响范围外的文件保留 WARNING | 全局忽略 `docs/`、把跨计划地图变更自动覆盖或漏报无关文件 | pytest stdout |
| S2 Drift 非法归属 | 阶段证据含绝对路径、通配符、仓库外路径，或地图变更无法唯一归属 | `python3 -m pytest --no-cov -q tests/test_check_plan_governance.py -k phase_evidence_rejects_absolute_glob_and_parent_paths` | 0；非法证据不被接受，歧义变更保留 WARNING | 把非法路径当作覆盖证据或静默吞掉歧义 | pytest stdout |
| S3 状态与进展分层 | 同一计划含通过的准入复核、追加式实施记录和状态字段变化 | `python3 -m pytest --no-cov -q tests/test_check_plan_governance.py -k recent_evidence_remains_separate_from_independent_review` | 0；三类信息分别输出，实施记录不替代准入结论 | 用最近实施记录覆盖准入复核或自动改变生命周期 | pytest stdout |
| S4 Attestation 生命周期 | 旧 JSON、新 purpose 快照、合法 supersedes、hash 漂移、重复 current、缺失目标和替代环 | `python3 -m pytest --no-cov -q tests/test_check_plan_governance.py -k 'attest_purpose or attestation_supersedes or attestation_missing'` | 0；旧格式兼容，漂移 WARNING，结构错误可定位且不产生有效 current | 把漂移快照继续当 current、自动接受 release_gate 或接受非法替代关系 | pytest stdout |
| S5 模板/旧计划兼容 | 新模板、旧六列计划索引和无新增可选字段的历史计划 | `npm test -- --test-name-pattern 'package manifest|packed package|init uses'` | 0；新模板字段和临时初始化输出可定位，旧计划不强制迁移 | 用样本文档中的文字伪造模板行为，或强制历史计划迁移、覆盖真实用户目录、删除旧快照 | npm stdout |
| S6 只读和回滚 | 合法查询前后文件 hash、目标项目和全局环境状态 | `python3 -m pytest --no-cov -q tests/test_check_plan_governance.py -k check_attestations_is_read_only` | 0；查询不写回，失败可移除新增可选段和测试恢复旧行为 | 生成快照/迁移时无授权写入目标项目或全局环境 | pytest stdout |

## 阶段 3 实施后行为证据

S1—S6 已由真实临时目录或测试行为覆盖，命令和输出位置如下；这些证据不替代阶段 3 最终独立完成验收。

| 案例 | 可执行命令 | 结果 |
|---|---|---|
| S1 | `python3 -m pytest --no-cov -q tests/test_check_plan_governance.py -k 'drift_completed_plan_closing_window_is_narrow or drift_covers_plan_map_row_plan_file_and_phase_evidence or pre_commit_uses_the_same_plan_map_and_phase_evidence_ownership'` | 通过；drift/pre-commit 的活跃计划和完成计划关闭窗口的计划自身、唯一归属地图行和阶段证据不告警，无关文件及完成计划影响范围外的文件保留 WARNING |
| S2 | `python3 -m pytest --no-cov -q tests/test_check_plan_governance.py -k phase_evidence_rejects_absolute_glob_and_parent_paths` | 通过；绝对路径、通配符和越界路径不进入覆盖范围 |
| S3 | `python3 -m pytest --no-cov -q tests/test_check_plan_governance.py -k recent_evidence_remains_separate_from_independent_review` | 通过；实施/验证记录与独立准入复核分层保留 |
| S4 | `python3 -m pytest --no-cov -q tests/test_check_plan_governance.py -k 'attest_purpose or attestation_supersedes or attestation_missing'` | 通过；旧 JSON 兼容，新关系、漂移、重复 current、缺失目标和替代环均有证据 |
| S5 | `npm test -- --test-name-pattern 'package manifest|packed package|init uses'` | 通过；新模板和临时初始化可定位，旧计划不强制迁移 |
| S6 | `python3 -m pytest --no-cov -q tests/test_check_plan_governance.py -k check_attestations_is_read_only` | 通过；查询前后治理文件 SHA-256 一致 |

## 阶段 3 实施前基线

当前仓库已确认：

- `python3 -m pytest -q`：106 passed，覆盖率 90.66%。
- `npm test`：39/39。
- `node bin/plan-governance-cli.mjs check . --strict-readiness` 和 `--stale-days 10` 通过。
- `--drift` 退出码 0；`--check-attestations` 对已有历史快照输出 WARNING，原因是后续计划/地图修改造成 hash 漂移，符合当前旧行为但尚未完成 purpose/supersedes 分层。
- Step 0 的干净基线是已提交的 `02d7f85`（`feat: complete plan governance stage 2`）；该提交后新增的阶段 3 计划/fixture 属于当前设计工作区，不冒充干净基线。阶段 3 Step 0 不修改目标项目、不创建完成快照、不同步本机全局环境。

## 证据层级

实施前的设计命令和实施后的行为命令均保留，前者只说明候选边界，后者才构成真实行为证据；不得用 `rg` 命中文档替代行为验证。

阶段 3 实现前已由 Aristotle 独立复核者确认候选契约、S1—S6 命令和失败边界；实施后行为命令已执行。它们仍不替代阶段 3 最终独立完成验收。
