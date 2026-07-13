# 计划：phase-entry-gate-hardening

## 背景

2026-07-13 的 `plan-governance` skill 评估报告发现：治理原则已经要求 Step 0 和独立验收，但没有把“阶段完成”“下一阶段准入”和“计划整体状态”明确分开。实际风险是阶段 N 完成后，执行者直接把阶段 N+1 标记为 `待实施`，跳过阶段 N+1 自己的基线、样本矩阵和独立准入复核。

评估报告位于相邻项目 `/Users/jafish/Documents/work/mineru-pdf-workflow/docs/reports/plan-governance-skill-review.md`，本计划只把它作为背景输入；本计划自身是新的规范事实源。

本仓库现状核对确认：`SKILL.md` 已有 `待实施` 的宽泛定义、Step 0 存在性要求和独立验收原则，但没有阶段转换硬规则、`待实施` 最低字段清单或历史结论优先级规则。`scripts/check_plan_governance.py` 已能检查部分证据、阻塞项、依赖和完成快照，但还不能检查阶段级准入是否成立。

## 目标

在保留轻量治理定位的前提下，补齐阶段准入闭环：

- 明确计划级状态、阶段级状态和 `PLAN_MAP.md` 当前阶段之间的边界。
- 规定阶段 N 完成后，阶段 N+1 默认进入 `设计中`，不能自动进入 `待实施`。
- 为 `待实施` 定义可复核的最低准入字段、样本/fixture 矩阵和独立准入结论。
- 规定多次独立复核记录的历史保留方式、当前有效结论和 `PLAN_MAP.md` 引用规则。
- 让检查器先以 `WARNING` 发现缺失或矛盾，再提供显式严格模式；不把结构检查冒充业务验收。

## 非目标

- 不新增计划生命周期状态，不自动推进或回退状态，不自动判定业务完成度。
- 不用 LLM、自然语言推断或单次全量测试替代独立验收。
- 不要求为所有历史已完成计划重写验收过程；只在需要复核或修改时补充规范记录。
- 不把外部评估报告、旧分析文档或完成快照作为新的事实源。
- 不引入审批流、看板、工时估算或强制安装 hook。

## 不变量

- `PLAN_MAP.md` 是计划级 `状态`、`当前阶段`、依赖、阻塞项和证据链接的事实源。
- 专项计划是阶段实施细节和准入证据的事实源；计划正文不能另行改变 `PLAN_MAP.md` 的计划级状态。
- 阶段 N 的完成只关闭阶段 N；它不产生阶段 N+1 的准入结论。
- 只有最新的独立准入复核明确写出“达到 `待实施` 标准”，阶段才可进入 `待实施`。
- 历史复核记录追加保留；当前有效结论必须显式标注日期、阶段、结论和证据链接。
- 检查器的 `WARNING` 只提示人工复核；严格模式的失败也只表示治理准入条件不满足，不表示业务验收失败。

## 影响模块或文件

- `/Users/jafish/.codex/skills/plan-governance/SKILL.md`
- `/Users/jafish/.codex/skills/plan-governance/assets/`
- `/Users/jafish/.codex/skills/plan-governance/scripts/check_plan_governance.py`
- `/Users/jafish/.codex/skills/plan-governance/scripts/init_plan_governance.py`
- `scripts/check_plan_governance.py`
- `scripts/init_plan_governance.py`
- `tests/test_check_plan_governance.py`
- `tests/test_init_plan_governance.py`
- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `plan-governance-design.md`
- `docs/PLAN_MAP.md`
- `docs/plans/phase-entry-gate-hardening.md`

## 公共契约变化

### 1. 计划级状态与阶段级准入分离

- `PLAN_MAP.md` 的 `状态` 继续表示计划整体生命周期。
- `PLAN_MAP.md` 的 `当前阶段` 继续表示唯一的阶段身份指针。
- 专项计划的“阶段路线图”记录各阶段进度；`## 当前阶段` 只描述该阶段细节，并增加结构化的准入摘要。
- 阶段准入沿用现有状态语义：`设计中`、`待实施`、`实施中`、`已完成`。不新增状态枚举。

当前阶段的结构化准入摘要只引用 `PLAN_MAP.md` 的阶段身份，不再另定义一个阶段编号：

```markdown
### 阶段准入摘要

| 字段 | 内容 |
|---|---|
| 准入状态 | 设计中 / 待实施 / 实施中 / 已完成 |
| Step 0 | 当前阶段 Step 0 证据的链接或锚点 |
| 样本矩阵 | 样本/fixture 或替代基线的链接或锚点 |
| 验证方式 | 可执行命令和输出位置的链接或锚点 |
| 失败/回滚边界 | 失败判定和安全边界的链接或锚点 |
| 当前阻塞项 | 无，或指向未决问题表中的具体行 |
| 最新独立准入复核 | 指向最新复核结论 |
```

检查器以 `PLAN_MAP.md` 的 `当前阶段` 为阶段身份事实源，并验证该阶段在计划的“阶段路线图”中存在、`## 当前阶段` 和上述摘要存在；最新复核记录中的阶段标识必须与该身份一致。这样既避免双重事实源，也能发现阶段指针漂移。

### 2. 阶段转换规则

```text
阶段 N 已完成
    ↓
阶段 N+1 设计中
    ↓ 当前阶段自己的准入复核通过
阶段 N+1 待实施
    ↓ 开始修改
阶段 N+1 实施中
    ↓ 独立验收通过
阶段 N+1 已完成
```

禁止仅因上一阶段完成、治理脚本通过、全量测试通过或实施者声明完成，就把下一阶段标记为 `待实施`。

### 3. `待实施` 最低准入清单

目标阶段必须同时具备：

1. 当前阶段的目标、范围和非目标。
2. Step 0 证据，且明确基线类型（失败回归、最小复现、现状快照、兼容样本、fixture 或替代基线）。
3. 样本/fixture 矩阵：每个样本的输入或基线、可执行命令、预期结果、失败判定和证据位置。
4. 验证方式、输出位置和完成条件。
5. 失败策略、回滚边界或安全边界。
6. 当前未决问题中没有未解决阻塞项。
7. `PLAN_MAP.md` 的状态、当前阶段、依赖和证据链接已同步。
8. 最新独立准入复核明确为“通过”，而不是实施者自己的完成声明。

若任务类型不适合固定样本，必须在 Step 0 中记录替代基线及其可观察产物，不能只写“已确认”或“测试通过”。

样本/fixture 矩阵至少使用以下字段；允许按任务类型增加列，但不能删除“预期结果”和“失败判定”：

```markdown
| 样本/fixture | 输入或基线 | 可执行命令 | 预期结果 | 失败判定 | 输出位置 |
|---|---|---|---|---|---|
```

### 4. 独立复核记录

专项计划新增 `## 独立复核记录` 和 `### 最新独立准入复核` 约定：

```markdown
### 最新独立准入复核

| 字段 | 内容 |
|---|---|
| 日期 | 2026-07-13 |
| 阶段 | 阶段 N |
| 结论 | 通过 / 未通过 |
| 证据 | 命令、样本或 CI 链接 |
| 复核者 | 姓名或 Agent |

## 独立复核记录

| 日期 | 类型 | 阶段 | 结论 | 证据 | 复核者 |
|---|---|---|---|---|---|
```

历史记录不得删除或覆盖。当前状态只由最新有效的独立结论决定；新的“未通过”覆盖此前的“通过”，修复后的新“通过”必须新增记录。`PLAN_MAP.md` 只链接最新有效结论，不复制历史表格。

### 5. 检查器行为

在不破坏现有命令兼容性的前提下增加阶段准入检查：

- 默认检查对 `待实施` 或 `实施中` 阶段缺少最低准入字段、缺少独立准入结论、存在矛盾结论或当前阶段不一致时输出 `WARNING`。
- 增加显式严格模式（命令名在阶段 0 设计中固定），将上述机械缺陷提升为 `ERROR`，供 CI 或实施前门禁使用。
- 只检查结构化字段、日期、阶段标识、结论和链接等机械事实；不判断样本是否真的代表业务、命令是否真的证明目标达成。
- 完成快照继续只负责检测已完成文档的 hash 漂移，不替代最新独立复核结论。

## 阶段路线图

| 阶段 | 目标 | 进入条件 | 验证方向 | 状态 |
|---|---|---|---|---|
| 阶段 0 | 固定阶段准入模型、字段和兼容策略 | 报告与本仓库现状已核对 | 文档反向引用、治理检查和 fixture 设计通过 | 已完成 |
| 阶段 1 | 同步 skill、模板、代理规则和设计文档 | 阶段 0 的契约无阻塞项 | 规则源、生成器和模板一致性测试通过 | 已完成 |
| 阶段 2 | 增加检查器的 warning/严格模式 | 阶段 1 的结构化字段已冻结 | 正反例 fixture、pytest 和命令兼容性通过 | 已完成 |
| 阶段 3 | 补充当前计划的准入记录并完成独立验收 | 阶段 2 的检查器可复现 | 治理检查、反向引用、严格模式和独立复核通过 | 已完成 |

## 阶段 0 完成证据

- 已冻结阶段转换规则、计划级/阶段级状态边界、`待实施` 最低准入清单和独立复核记录格式。
- 已选定严格模式命令为 `--strict-readiness`；无参数检查命令保持兼容，默认 warning 不改变退出码。
- 六类 fixture 已定义输入、预期结果和失败判定：状态机不误推进、准入通过、缺字段、结论冲突、开放阻塞和阶段指针不一致。
- 基线 `python3 -m pytest`：80 项通过，pytest-cov 总覆盖率 92.39%。
- 基线 `python3 scripts/check_plan_governance.py .` 和 `--stale-days 10` 均输出 `计划治理检查通过。`。

## 阶段 1 实施记录

### 范围

阶段 1 同步阶段准入规则的规则源和文档入口，不实现检查器逻辑。范围包括：

- `/Users/jafish/.codex/skills/plan-governance/SKILL.md` 的阶段转换、最低准入、独立复核和严格模式契约。
- skill 的 `PLAN_MAP.template.md`、`plan.template.md` 和 `init_plan_governance.py` 生成的代理规则。
- 本仓库的 `AGENTS.md`、`CLAUDE.md`、`README.md` 和 `plan-governance-design.md`。
- 不改变 `PLAN_MAP.md` 表结构，不实现 `--strict-readiness`，不改变既有检查器退出码。

### 阶段 1 准入摘要

| 字段 | 内容 |
|---|---|
| 准入状态 | 待实施 |
| Step 0 | 本阶段 Step 0 证据 |
| 样本矩阵 | 阶段 1 文档/生成器同步 fixture |
| 验证方式 | 生成器测试、pytest、治理检查和反向引用搜索 |
| 失败/回滚边界 | 只回滚阶段 1 文档同步，不触碰阶段 0 已冻结契约 |
| 当前阻塞项 | 无 |
| 最新独立准入复核 | [阶段 1 独立准入复核](#阶段-1-最新独立准入复核) |

阶段 1 Step 0 fixture 矩阵：

| 样本/fixture | 输入或基线 | 可执行命令 | 预期结果 | 失败判定 | 输出位置 |
|---|---|---|---|---|---|
| 规则源关键词 | 当前 skill、模板、生成器和代理章节 | `rg -n "阶段 N|strict-readiness|阶段准入摘要|独立复核记录" ...` | 记录当前缺失项，作为同步前后对照 | 同一规则源出现未计划的分叉或漏改 | 命令输出 |
| 临时项目升级 | 临时目录含旧 `AGENTS.md`、`CLAUDE.md`、`docs/` | `python3 scripts/init_plan_governance.py --root <tmp> --upgrade-existing` | 受管章节同步，`docs/` 内容保持不变 | 覆盖 docs 或遗漏任一入口 | 临时目录 diff |
| 代理章节一致性 | 生成后的 `AGENTS.md`、`CLAUDE.md` 与 `agent_rules_body()` | `rg -n "阶段 N|strict-readiness|阶段准入摘要" <files>` | 两个入口包含同一稳定规则 | 两入口内容不一致或出现独立计划细节 | 测试断言 |
| 说明文档同步 | README、设计文档和 skill 规则 | `rg -n "阶段转换|待实施|strict-readiness|独立复核" ...` | 只出现规则摘要和链接，不复制索引事实 | 说明与 skill 契约冲突或把旧文档当事实源 | 反向引用扫描 |

### 实施步骤

1. 把阶段 0 已冻结的规则同步到已安装 skill 的 `SKILL.md` 和模板。
2. 更新初始化脚本中的代理规则正文，并重新生成本仓库 `AGENTS.md` 与 `CLAUDE.md` 的受管章节。
3. 更新 README 和设计文档的状态、阶段门禁及检查器说明，但不复制阶段级字段细节到索引文档。
4. 运行初始化脚本测试、全文反向引用检查和治理检查。
5. 由独立复核确认规则源、模板、代理入口和说明文档一致后，才进入阶段 2。

### Step 0 证据

阶段 1 实施前的现状基线：

- `SKILL.md`、skill 模板、`scripts/init_plan_governance.py` 的 `agent_rules_body()`、`AGENTS.md` 和 `CLAUDE.md` 均尚未包含阶段转换硬规则、`--strict-readiness`、阶段准入摘要或独立复核记录格式。
- 本仓库完整基线测试为 80 项通过，总覆盖率 92.39%；治理检查和停滞检查通过。针对性测试若单独运行必须关闭全局覆盖率门禁，否则会因未加载其他脚本而产生误报。
- 阶段 0 已冻结的六类准入 fixture 可作为文档同步后的关键词和契约回归样本；阶段 1 不改变其预期行为。

可复核命令：

```bash
rg -n "阶段 N|strict-readiness|阶段准入摘要|独立复核记录" \
  /Users/jafish/.codex/skills/plan-governance \
  scripts/init_plan_governance.py AGENTS.md CLAUDE.md README.md plan-governance-design.md
python3 -m pytest tests/test_init_plan_governance.py
```

### 验证方式

- `python3 -m pytest tests/test_init_plan_governance.py tests/test_plan_governance_hooks.py --no-cov`（只验证相关测试行为）。
- `python3 -m pytest`（完成阶段验收时验证全局 85% 覆盖率门禁）。
- 在临时目录运行 `init_plan_governance.py --upgrade-existing`，确认生成的代理规则包含阶段准入契约且不覆盖 `docs/`。
- 用 `rg` 检查 `SKILL.md`、两个模板、初始化脚本、`AGENTS.md`、`CLAUDE.md`、README 和设计文档的关键规则一致。
- `python3 scripts/check_plan_governance.py .` 和 `python3 scripts/check_plan_governance.py . --stale-days 10`。

### 测试覆盖率

阶段 1 只增加文档生成断言和 fixture，不改变 Python 运行逻辑；完整 `python3 -m pytest` 验收记录总覆盖率 92.39%，高于 85% 门禁。

### 完成条件

- 阶段 0 的契约在 skill、模板、初始化生成器和代理受管章节中一致。
- README 和设计文档说明阶段转换与严格模式边界，且不把本计划细节复制到 `PLAN_MAP.md`。
- 初始化/升级测试覆盖生成内容和不覆盖 `docs/` 的边界。
- `python3 -m pytest`、治理检查、停滞检查和反向引用检查通过。
- 阶段 1 独立复核通过后，才进入阶段 2 的检查器实现。

### 阶段 1 最新独立准入复核

| 字段 | 内容 |
|---|---|
| 日期 | 2026-07-13 |
| 阶段 | 阶段 1 |
| 结论 | 通过，达到 `待实施` 标准 |
| 证据 | 规则关键词基线核对；临时项目升级保持 `PLAN_MAP.md` 与计划 hash 不变；34 项针对性测试通过；治理检查和停滞检查通过 |
| 复核者 | Codex 独立复核 |

## 独立复核记录

| 日期 | 类型 | 阶段 | 结论 | 证据 | 复核者 |
|---|---|---|---|---|---|
| 2026-07-13 | 阶段设计复核 | 阶段 0 | 通过 | 六类 fixture 结构核对；pytest 80 passed / 92.39%；治理检查和停滞检查通过 | Codex 独立复核 |
| 2026-07-13 | 阶段准入复核 | 阶段 1 | 通过 | 规则关键词基线、临时升级 hash、34 项针对性测试、治理检查和停滞检查 | Codex 独立复核 |
| 2026-07-13 | 阶段验收复核 | 阶段 2 | 通过 | 53 项检查器测试、87 项全量测试、严格模式、治理检查和源/安装副本核对 | Codex 独立复核 |
| 2026-07-13 | 阶段准入复核 | 阶段 2 | 通过 | 完整 pytest、治理检查、停滞检查和检查器基线核对 | Codex 独立复核 |
| 2026-07-13 | 阶段准入复核 | 阶段 3 | 通过 | 87 项全量测试、严格治理、脚本副本和 drift/pre-commit 基线核对 | Codex 独立复核 |
| 2026-07-13 | 阶段验收复核 | 阶段 3 | 通过 | 最终全量测试、严格治理、停滞、drift/pre-commit、反向引用和事实源扫描 | Codex 独立复核 |

## 阶段 1 完成证据

- 已同步 `/Users/jafish/.codex/skills/plan-governance/SKILL.md`、两个 skill 模板、仓库源生成器和已安装生成器。
- 已通过生成器刷新 `AGENTS.md` 与 `CLAUDE.md`，并保留 `docs/` 内容不变。
- `tests/test_init_plan_governance.py` 已覆盖阶段准入摘要、独立复核记录、阶段转换和严格模式契约文本。
- 源仓库与已安装 `init_plan_governance.py` 内容一致；临时项目生成和升级 fixture 通过。
- `python3 -m pytest`：80 项通过，pytest-cov 总覆盖率 92.39%。
- `python3 scripts/check_plan_governance.py .` 和 `--stale-days 10` 通过；阶段 1 独立准入复核通过。

## 阶段 2 实施记录

### 范围

阶段 2 实现阶段准入检查器的机械校验和 `--strict-readiness` 严格模式。只检查结构化字段、阶段指针、复核结论和阻塞项，不判断样本是否代表业务，也不自动改变计划状态。

### 阶段 2 准入摘要

| 字段 | 内容 |
|---|---|
| 准入状态 | 已完成 |
| Step 0 | 阶段 2 检查器 fixture 基线 |
| 样本矩阵 | 六类阶段准入检查 fixture |
| 验证方式 | pytest、默认 warning、严格模式退出码、治理检查 |
| 失败/回滚边界 | 只影响准入检查输出；保留既有无参数命令和基础治理规则 |
| 当前阻塞项 | 无 |
| 最新独立准入复核 | [阶段 2 独立准入复核](#阶段-2-最新独立准入复核) |

阶段 2 Step 0 fixture 矩阵：

| 样本/fixture | 输入或基线 | 可执行命令 | 预期结果 | 失败判定 | 输出位置 |
|---|---|---|---|---|---|
| 设计中不误报 | 当前阶段=`设计中`，缺少准入摘要 | `python3 scripts/check_plan_governance.py <fixture>` | 基础检查不因尚未准入而 warning | 把设计中直接判为准入失败 | pytest 输出 |
| 准入完整 | 当前阶段=`待实施`，摘要字段和最新复核齐全 | 基础命令及 `--strict-readiness` | 默认无 warning，严格模式退出 0 | 任一模式误报或失败 | pytest 输出 |
| 准入字段缺失 | 缺样本矩阵或失败/回滚边界 | 基础命令及严格模式 | 默认 warning，严格模式退出 1 | 未发现或严格模式通过 | pytest 输出 |
| 复核结论冲突 | 摘要为“通过”，历史最新记录为“未通过” | 基础命令及严格模式 | 输出冲突 warning，严格模式退出 1 | 采信旧结论 | pytest 输出 |
| 阶段指针不一致 | `PLAN_MAP` 当前阶段与路线图/最新复核阶段不同 | 基础命令及严格模式 | 输出指针 warning，严格模式退出 1 | 静默通过 | pytest 输出 |
| 当前阶段开放阻塞 | `待实施` 且未决问题存在未解决阻塞 | 基础命令及严格模式 | 保留既有错误，严格模式非零 | 准入摘要掩盖阻塞或改变既有语义 | pytest 输出 |

### 实施步骤

1. 增加阶段路线图、当前阶段准入摘要和独立复核记录的机械解析 helper。
2. 增加 `--strict-readiness` 参数；默认模式只输出 warning，严格模式将准入结构缺陷转为 error。
3. 校验 `PLAN_MAP.md` 当前阶段在计划路线图中存在，且最新复核阶段与其一致。
4. 校验 `待实施`/`实施中` 计划的准入摘要字段、非占位值、最新独立复核和历史结论一致性。
5. 保持现有基础检查、warning 退出码和 `--drift`、`--pre-commit`、`--stale-days`、attestation 命令兼容。
6. 增加六类 fixture 测试，运行完整测试、治理检查和反向引用检查。

### Step 0 证据

阶段 2 实施前基线：

- `scripts/check_plan_governance.py` 当前使用 `argparse`，没有 `--strict-readiness` 参数，也没有阶段准入摘要或独立复核记录解析器。
- 当前基础治理检查对已完成计划、活跃阻塞项、依赖、影响范围、停滞和 attestation 有既有行为，必须保持兼容。
- 完整 `python3 -m pytest` 基线为 80 项通过、总覆盖率 92.39%。
- 阶段 0 已定义六类准入场景，阶段 1 已把结构契约写入规则源和模板。

可复核命令：

```bash
rg -n "strict-readiness|阶段准入摘要|独立复核记录|def parse_args|def markdown_section" \
  scripts/check_plan_governance.py tests/test_check_plan_governance.py
python3 -m pytest
python3 scripts/check_plan_governance.py .
```

### 验证方式

- `python3 -m pytest`，记录总覆盖率。
- 对六类 fixture 验证默认 warning、严格模式退出码和既有阻塞错误。
- 验证无参数基础命令、`--drift`、`--pre-commit`、`--stale-days 10`、`--attest` 和 `--check-attestations` 不回归。
- `python3 scripts/check_plan_governance.py .` 和 `python3 scripts/check_plan_governance.py . --stale-days 10`。
- 用 `rg` 搜索本计划名称、`strict-readiness`、阶段准入字段和历史结论，检查脚本、测试、README、设计文档、skill 和计划同步。

### 阶段 2 最新独立准入复核

| 字段 | 内容 |
|---|---|
| 日期 | 2026-07-13 |
| 阶段 | 阶段 2 |
| 结论 | 通过，达到 `待实施` 标准 |
| 证据 | 完整 pytest 80 passed / 92.39%；治理检查和停滞检查通过；检查器基线确认无 `--strict-readiness` 与阶段准入解析 |
| 复核者 | Codex 独立复核 |

### 测试覆盖率

完成阶段 2 时必须记录完整 pytest 的实际覆盖率，保持总覆盖率不低于 85%；不能用单独子集覆盖率替代全量门禁。

### 完成条件

- `--strict-readiness` 已实现，默认模式只 warning，严格模式对机械准入缺陷返回非零退出码。
- 六类 fixture 均有测试，且设计中计划不会被误报为已进入准入失败。
- 当前阶段指针、阶段路线图、准入摘要、最新复核和历史结论冲突可被发现。
- 既有无参数治理检查和可选命令行为保持兼容。
- 完整 pytest、治理检查、停滞检查和反向引用检查通过。
- 阶段 2 独立复核通过后，才进入阶段 3。

## 阶段 2 完成证据

- `scripts/check_plan_governance.py` 已新增 `--strict-readiness`，默认模式对准入结构缺陷输出 `WARNING`，严格模式返回非零退出码。
- 检查器已校验当前阶段路线图、阶段准入摘要、最新独立复核、历史结论一致性和 fenced code 标题误读边界。
- `tests/test_check_plan_governance.py` 已覆盖设计中不误报、准入完整、字段缺失、结论冲突、阶段指针不一致、开放阻塞和 fenced code 场景。
- 53 项检查器测试通过；完整 `python3 -m pytest` 为 87 项通过，总覆盖率 91.93%。
- 源仓库与已安装 skill 的 `check_plan_governance.py` 内容一致；默认、严格、停滞、基础治理、drift 和 pre-commit 检查通过。
- 阶段 2 独立验收通过；drift 仅提示既有 `.DS_Store`，以及本次受管入口文件在计划影响范围外的历史登记问题已补入计划。

## 当前阶段

### 范围

阶段 3 完成最终治理文档收口和独立验收，不再增加新的检查器行为。范围包括：

- 将阶段 2 的实现、测试、覆盖率和兼容性证据写入本计划和 `PLAN_MAP.md`。
- 补充当前计划的阶段 3 准入摘要、最新独立复核和追加历史记录。
- 运行最终测试、基础/严格治理检查、停滞、drift、pre-commit 和反向引用检查。
- 在所有文档最终稳定后创建本计划完成快照；不在快照创建后继续修改计划或 `PLAN_MAP.md`。

### 阶段准入摘要

| 字段 | 内容 |
|---|---|
| 准入状态 | 已完成 |
| Step 0 | 阶段 2 完成证据和最终验收基线 |
| 样本矩阵 | 文档收口、完整测试、严格检查、引用扫描和完成快照 |
| 验证方式 | `python3 -m pytest`、治理命令和反向引用检查 |
| 失败/回滚边界 | 只回滚阶段 3 文档状态/快照，不回滚已验证的规则实现 |
| 当前阻塞项 | 无 |
| 最新独立准入复核 | [阶段 3 独立准入复核](#最新独立准入复核) |

阶段 3 Step 0 fixture 矩阵：

| 样本/fixture | 输入或基线 | 可执行命令 | 预期结果 | 失败判定 | 输出位置 |
|---|---|---|---|---|---|
| 文档状态收口 | 阶段 0/1/2 完成证据已存在，当前阶段为阶段 3 | `rg -n "阶段 0 完成证据|阶段 1 完成证据|阶段 2 完成证据" ...` | 三个历史阶段均有独立证据 | 缺任一阶段证据或 PLAN_MAP 漂移 | rg 输出 |
| 运行验证 | 87 项测试、91.93% 覆盖率基线 | `python3 -m pytest` | 全量通过且覆盖率不低于 85% | 测试失败或覆盖率不足 | pytest 输出 |
| 严格治理 | 当前计划具备阶段 3 结构化摘要 | `python3 scripts/check_plan_governance.py . --strict-readiness` | 返回 0 | 返回非零或静默忽略状态冲突 | 命令输出 |
| 反向引用 | skill、脚本、测试、README、设计文档和计划已同步 | `rg -n "phase-entry-gate-hardening|strict-readiness|阶段准入" ...` | 无未登记引用和事实源漂移 | 发现旧事实源或引用缺失 | rg 输出 |
| 完成快照 | 最终计划和 PLAN_MAP 已稳定 | `python3 scripts/check_plan_governance.py . --attest phase-entry-gate-hardening` | 创建 hash 快照 | 快照创建后仍需修改计划或 map | attestation JSON |

### 实施步骤

1. 由本阶段 Step 0 证据确认阶段 2 已完成，补齐阶段 3 的准入摘要和样本矩阵。
2. 独立复核阶段 3 的目标、验证命令、完成快照顺序和无阻塞项，达到 `待实施` 标准。
3. 将阶段 3 状态改为 `实施中`，完成计划/`PLAN_MAP.md` 的最终证据和状态同步。
4. 运行完整验证和反向引用检查；如发现漂移，先修正治理文档再继续。
5. 独立验收通过后将阶段 3 和整个计划标记为 `已完成`，同步 `PLAN_MAP.md`。
6. 最后创建完成快照并运行 `--check-attestations`；快照之后不再修改计划或 `PLAN_MAP.md`。

### Step 0 证据

阶段 3 实施前基线：

- 阶段 0、1、2 的完成证据已写入本计划，`PLAN_MAP.md` 当前阶段为阶段 3，计划仍为 `设计中`。
- 阶段 2 验证基线为 87 项测试通过、总覆盖率 91.93%；`--strict-readiness`、基础治理和停滞检查通过。
- source/installed checker 和 init 脚本一致，规则源关键词扫描通过；当前 drift 仅有既有 `.DS_Store` 无关 warning。

可复核命令：

```bash
python3 -m pytest
python3 scripts/check_plan_governance.py . --strict-readiness
cmp scripts/check_plan_governance.py /Users/jafish/.codex/skills/plan-governance/scripts/check_plan_governance.py
```

### 验证方式

- `python3 -m pytest`，记录总覆盖率。
- `python3 scripts/check_plan_governance.py .`、`--strict-readiness`、`--stale-days 10`、`--drift` 和 `--pre-commit`。
- 用 `rg` 搜索本计划名称、阶段状态、严格模式、关键字段和历史复核，确认所有引用同步。
- 用事实源反模式搜索确认外部报告和旧分析只作为背景。
- 最终创建 `docs/attestations/phase-entry-gate-hardening.json` 后运行 `--check-attestations`。

### 最新独立准入复核

| 字段 | 内容 |
|---|---|
| 日期 | 2026-07-13 |
| 阶段 | 阶段 3 |
| 结论 | 通过，阶段 3 和整个计划达到完成标准 |
| 证据 | 87 项全量测试、91.93% 覆盖率；基础/严格/停滞检查通过；source/installed 脚本一致；drift/pre-commit 通过（仅有既有 `.DS_Store` warning）；反向引用与事实源扫描通过 |
| 复核者 | Codex 独立复核 |

### 测试覆盖率

阶段 3 不增加 Python 逻辑；最终证据沿用阶段 2 的 87 项测试和 91.93% 总覆盖率，并重新运行完整测试确认没有文档收口回归。

### 完成条件

- 阶段 0、1、2 的完成证据、阶段 3 的最终复核和 `PLAN_MAP.md` 状态一致。
- 阶段 3 的完整验证命令和反向引用检查通过。
- 计划整体状态为 `已完成`，阶段路线图四个阶段均为 `已完成`。
- 完成快照创建后 `--check-attestations` 通过且没有 hash 漂移。

## 阶段 3 完成证据

- 阶段路线图四个阶段均已标记 `已完成`，计划级状态已同步为 `已完成`。
- 最新独立验收结论明确为阶段 3 和整个计划通过；历史复核记录保持追加、不覆盖。
- `PLAN_MAP.md` 已同步阶段 3 完成证据和最终状态。
- 完成快照顺序已固定：先稳定本节及 `PLAN_MAP.md`，再创建快照并执行 `--check-attestations`；创建后不再修改两份治理事实源。

## 整个计划完成条件

- skill、初始化生成器、模板、设计文档和 README 对上述规则保持一致。
- 检查器能发现阶段准入的机械缺陷，并支持显式严格模式。
- 现有无参数检查命令保持兼容，既有已完成计划不因新增历史规则被误判。
- 新增行为有测试和覆盖率证据；`PLAN_MAP.md`、计划状态和最新独立复核结论已同步。
- 独立验收者基于仓库内容和可复现命令确认完成，不只依据本计划的完成声明。

整个计划完成条件：

- skill、初始化生成器、模板、设计文档和 README 对上述规则保持一致。
- 检查器能发现阶段准入的机械缺陷，并支持显式严格模式。
- 现有无参数检查命令保持兼容，既有已完成计划不因新增历史规则被误判。
- 新增行为有测试和覆盖率证据；`PLAN_MAP.md`、计划状态和最新独立复核结论已同步。
- 独立验收者基于仓库内容和可复现命令确认完成，不只依据本计划的完成声明。

## 未决问题

| 问题 | 推荐方案 | 是否阻塞当前阶段 | 状态 |
|---|---|---|---|
| 严格模式命令名采用 `--readiness` 还是 `--strict-readiness`？ | 采用更明确的 `--strict-readiness`，并保留无参数调用兼容。 | 否 | 已决定 |
| `待实施` 的缺字段检查默认是否阻断基础治理检查？ | 默认只 `WARNING`，显式严格模式才 `ERROR`，避免历史计划一次性失败。 | 否 | 已决定 |
| 历史复核的“最新”是否只按日期判断？ | 不仅按日期；要求显式维护“最新独立准入复核”，日期用于排序和审计。 | 否 | 已决定 |
| 是否给每个已完成历史计划补阶段准入记录？ | 不追溯改写；只有恢复、修改或重新实施时补充。 | 否 | 已决定 |

## 风险和回滚

风险：阶段级字段与现有自由格式计划不兼容，产生大量 warning。

控制：先以 warning 兼容历史文档，提供模板和正反例；严格模式只在计划主动接入后启用。

风险：把“最新结论”机械化后，实施者可能伪造复核记录。

控制：检查器只验证记录结构；独立验收仍必须核对仓库、命令输出和证据来源。

风险：计划级状态与阶段级状态重复导致事实源漂移。

控制：`PLAN_MAP.md` 继续是计划级状态/当前阶段事实源，计划正文只承载当前阶段细节和准入证据；任何同步冲突先更新治理文档。

回滚：保留已完成的规则文档和历史复核记录；若检查器误报，先关闭严格模式并回退新增 warning 入口，不删除已确认的阶段转换和事实源规则。

## 关联 ADR、迁移、spec 或 issue

- 背景评估报告：`/Users/jafish/Documents/work/mineru-pdf-workflow/docs/reports/plan-governance-skill-review.md`
- 既有独立验收规则：[independent-acceptance-rules](independent-acceptance-rules.md)
- 既有运行时集成：[agent-runtime-integration](agent-runtime-integration.md)
