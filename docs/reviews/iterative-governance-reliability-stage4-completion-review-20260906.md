# 持续迭代治理优化：阶段 4 与全计划独立完成复核

## 第一轮未通过

2026-09-06，结论：**阶段 4 及全计划完成验收未通过。** 阶段 4 保持实施中，D02/D03 阻塞保留；修复后由新的独立复核者重审。本节为追加式历史，不随修复改写。

- 复核者：`/root/iterative_stage4_acceptance`，新上下文独立只读，未参与设计、实现或测试编写；主任务根据返回结果落档。
- 范围：阶段 4 A01—A16 及全计划完成条件；前序保持性另由只读子复核者 `/root/iterative_stage4_acceptance/prior_contract_review` 核查。
- Revision：`336b728d7dacc335a35f2cf97ab39356e3a82ba0` 加混合工作树；未修改生产文件，只运行已授权验证与临时项目实验。

| 阻塞 | 独立实盘证据 | 影响 |
|---|---|---|
| D02 不可读取的快照目录被当作空目录 | `2e2fc9`：有效绑定后 chmod 000，os.listdir 确认 PermissionError，但 strict 退出 0、无快照/I/O 诊断。`bcf83b`：目录 0300 不可读但可写/执行，第二个同计划/purpose 绑定仍创建成功，快照 1→2，恢复权限后才报多个 current | Path.glob 静默吞目录权限错误；违反契约 5、7 和 A11/A14。旧位置 checker 964、1117 |
| D03 混合替代链旧分支仍读取外部 symlink | `2866bb`：legacy→binding 有效替代后，计划改为外部 symlink；strict 退出 1，但 Path.open 确认外部被 rb 读取一次。主任务同案 `80d8a1` 经独立复现 | main 的提前拒绝未覆盖旧快照 hash 分支；违反契约 5。旧位置 checker 1200、1220 |

实验均恢复临时权限并清理临时项目，仓库原有快照未变。主任务最初一次混合路径 spy 未对比较双方 resolve（`5e9121`），不作为有效通过证据；`80d8a1` 才是修正后的真实失败。

### 其余验证与局限

- 独立 `PYTHONDONTWRITEBYTECODE=1 npm run verify` 通过：Python 334 passed、93.16%，Node 99/99、0 skipped，退出 0；`52d6e8`、`3b441a`。现有套件未覆盖上述两个反例，不能替代独立完成结论。
- 其他现有样本及源码支持默认兼容、实际工作树 hash、完整投影/闭包、无关变更保持和替代生命周期；A11/A14 因上述阻塞未满足。
- 前序阶段子复核重放阶段 0 和 D01，核查核心 hash、受管规则、统一验证/发布/CI、按需契约与分发保护，未发现回退。
- 普通/严格/stale 退出 0；workset schema 1，宿主阶段 2 与后续计划阶段 0 均 blocked/resolve_blocker，四旧快照 needs_review 未回填；`d82bcd`。drift 只保留混合地图归属 WARNING；`54007f`。
- skill 与 diff 检查通过 `d7c42a`；反向引用/事实源 `ba7c26`；六份当前文档 98 个本地链接/锚点通过 `7ba830`。
- fixture 列出的 29 个文件均匹配（5 当前核心、24 保持输入），最终 `7b8cb3`。本结论不解除宿主/后续计划阻塞，不证明发布、远端 CI 或业务生产验收完成。

### 第一轮被审查身份

| 文件 | SHA-256 |
|---|---|
| scripts/check_plan_governance.py | `f6b94927608618ab4d8386a31dee81c3a014fd299e60548c1883b5fac579d0d9` |
| tests/test_attestation_binding.py | `4b61525fbf2e01db64abdb4d7a4d93c5232b1551aa91a1884031ea01c800c19f` |
| tests/npm_cli.test.mjs | `e792ef2da8489c66dc033aebeb96443ff1ecb6770280b7cb97005efa68e5ad4d` |
| 专项计划 | `4e786877c30553f6fd3ea373ecde0802374b71a0b428e8c5371b3114abf5069e` |
| 阶段 4 fixture | `f01df97e6cf332cde13b0a49b75660033ed43ab0a19cc616b7c28131028315e1` |
| PLAN_MAP | `ec9d58da27b8c313cc72ac39d8ceaf39b1324a659c5f0dc74105e6958d1ac6df` |

## 第二轮修复复核

2026-09-06，独立只读复核者 `/root/iterative_stage4_recheck` 确认：**D02/D03 可解除，尚非全计划完成；新增 D04 阻塞最终验收。** 未参与实现或测试编写，主任务据此同步状态。

- 被审查 checker `a84096b94ca4adc0818c47e8a46c232fd6144b0fa11f65661b6b3ddfcf355fe0`、Python 测试 `8a1c9071d991ff332d61f41c6bb3cee2f7540c6f90f48170f791fa7b1815a0ea`；其余受审核心与派发一致（`64c2a2`）。地图有后续减负计划的并行文档更新，原优化计划状态与 D02/D03 行未被改变；本次保留这些更新，仅同步自己的复核记录。
- 独立定向 pytest 136 passed、0 skipped（`7b7ac4`、`447f45`）。不调用测试 helper 的真实临时实验：000/0300 均先确认 PermissionError；默认 0+WARNING、strict 1、创建 1，快照仍 1 份且字节不变；legacy/purpose-only × 计划/地图 symlink 四场景，strict 1、binding needs_review、外部 Path.open 读取 0（`2bb262`）。前置 harness 两次失败分别为样本验证说明缺少关键字与诊断文案断言过窄（`4801cc`、`66e771`），不作产品失败。
- 邻近 D04：同一普通计划文件 chmod 000，旧分支 `sha256_file(plan_path)` 未捕获 PermissionError，已识别 binding 状态未输出（`d7a4a6`）。独立 Python 子进程 legacy/purpose-only × 默认/strict 四场景均 exit 1、stderr Traceback、stdout 无 ATTESTATION（`800bc2`）。恢复权限和临时目录清理完成，快照字节未变；违反契约 5、6，修复应保留契约 7 的内容有效性与替代结构区分。默认治理本身可因计划不可读失败，不把默认退出 0 作为本反例目标。
- 独立源入口与临时安装迭代：`PYTHONDONTWRITEBYTECODE=1 node --test --test-name-pattern='binding iteration|packed package' tests/npm_cli.test.mjs`，2/2、0 skipped、exit 0（`96e74c`、`bdc9de`）。不覆盖 D04，不作为解除其阻塞的证据。

D04 回归由主任务接手编写：尝试派发原测试助手及新助手均被宿主 agent thread limit 拒绝；原独立复核者仍只读，不参与实现。最终 verify 与全计划完成判断留待修复及独立确认后执行。

## D04 独立修复确认

2026-09-06，`/root/iterative_stage4_recheck` 独立只读确认：**D04 可解除，尚非全计划完成。**

- checker `669c6c3e7e0690f5e57c98a4a221af7a712a1ff236a6cf550a765384e77c6ebb`、Python 测试 `822efac4a11bb6cc89d9bde4dfe025d908af25efc300ecf8faaeef5491723571`、Node 测试 `e792ef2da8489c66dc033aebeb96443ff1ecb6770280b7cb97005efa68e5ad4d` 身份匹配（`ef8da5`）；115 个 AST 顶层节点仅 `warn_attestation_drift` 改变（`c794a8`、`c984b0`）。无 opt-in 的旧路径保持。
- 独立重写真实临时复现，legacy/purpose-only × plan/map × 默认/strict 共 8 个 Python 子进程全部 exit 1、有可见 Permission denied、无 Traceback，binding needs_review 保留；计划场景前驱仍 superseded。快照字节未变、finally 恢复权限清理（`bff4d3`）。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/test_attestation_binding.py -q --no-cov`：140 passed、0 skipped（`f2a10d`、`10f596`）。

主任务据此解除 D04，保留前述失败历史。阶段 4 继续实施中，最终统一 verify、治理与文档/保持性检查及全计划完成判断尚待独立复核者执行。

## 第二轮通过

2026-09-06，结论：**阶段 4 与全计划完成验收通过，可以关闭本计划。** 当前阶段无未解决阻塞，D02—D04 均经独立确认修复。复核者 `/root/iterative_stage4_recheck` 未参与实现或测试编写，受审 revision 为 `336b728d7dacc335a35f2cf97ab39356e3a82ba0` 加混合工作树；主任务仅据返回结论落档与同步状态。

| 验收项 | 实际命令或检查 | 结果与证据 |
|---|---|---|
| D02—D04 | 真实临时权限、混合 symlink 及独立子进程，详见本报告修复确认 | 000/0300 不误放行、零新增/外部读取；D04 八场景可见失败并保留 binding 状态，权限恢复和字节保持；2bb262、800bc2、bff4d3 |
| A01—A16 | `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/test_attestation_binding.py -q --no-cov` 及契约逐项核对 | 140 passed、0 skipped；f2a10d、10f596 |
| 统一验证 | `PYTHONDONTWRITEBYTECODE=1 npm run verify` | exit 0；Python 348 passed，启用分支统计的总覆盖率 92.97%，超过 85% 门槛；Node 99/99、0 skipped；149047、2ac9c1 |
| 源与安装包迭代 | 源/临时安装的 Node 定向回放，完整命令见第二轮修复复核 | 临时 Node→Python 及打包安装回放 2/2；96e74c、bdc9de |
| 治理 | 源 Node CLI 普通 check、`--strict-readiness`、`--strict-readiness --check-attestations`、`--stale-days 10`、workset JSON | 均 exit 0，schema 1；宿主阶段 2 与后续阶段 0 仍 blocked/resolve_blocker；四份旧快照 needs_review；001a7d |
| 前序保持 | 独立子复核 `/root/iterative_stage4_recheck/prior_contract_recheck`：24 个保持输入、11 类/33 次门禁入口、57 项验证发布回归和受管区域保护 | 阶段 0—3 无功能回退；60b903、2afc61、bc6639 |
| 文档/分发/身份 | skill quick_validate、`git diff --check`、反向引用/事实源搜索、源 check `--drift`、29 文件 hash | 通过；drift 仅余既存混合地图归属 WARNING；d46210、2dce57、465e69 |
| 链接 | 六份文档共 174 个本地链接及锚点 | 无新增失效；两处地图历史锚点在 HEAD 已存在，保留为本轮非阻塞；431355、73b0c0 |

完成前统一 verify 曾因摘要“无；说明……”未满足固定无阻塞值而在严格首节点停止（845110）；已仅将单元格规范为“无”，保留实际独立解除依据，再完整验证通过。drift 指出完成报告未登记在顶部影响列表，补上原已授权的精确路径后复验通过；两项均未修改门禁或源代码，不重复无变化的全量套件。并行后续计划只更新其 B02 方案引用，最终地图中的本计划状态、已解决阻塞、关系和边界均经核对。

### 第二轮被审查身份

以下为验收时身份；通过后仅追加本结论与状态同步，适用文档检查另记。

| 文件 | SHA-256 |
|---|---|
| scripts/check_plan_governance.py | `669c6c3e7e0690f5e57c98a4a221af7a712a1ff236a6cf550a765384e77c6ebb` |
| tests/test_attestation_binding.py | `822efac4a11bb6cc89d9bde4dfe025d908af25efc300ecf8faaeef5491723571` |
| tests/npm_cli.test.mjs | `e792ef2da8489c66dc033aebeb96443ff1ecb6770280b7cb97005efa68e5ad4d` |
| 专项计划 | `412dbeb416a380821d0d3f932b5769596a094df26a6f2aece25c72e09b3e64e5` |
| 阶段 4 fixture | `a648cc1bd5c19fc22e5345e095531d9a6d81b66229c1f6221ac68a755e9b933a` |
| PLAN_MAP | `45c63e1f96fe166ce2a5a2da62b8b86bf1fe7ed30f69acbba580700dbeda15c9` |
| 本报告（追加最终结论前） | `eb6c182c1e4049704ecf08b9f0a7c108f20d3fbf0f777f0addbd9949494f62d6` |

本结论仅关闭本计划，不代表用户已接受后续计划的前置交付，不解除宿主回放或后续减负计划阻塞。四份旧快照未回填；未发布、全局同步或操作真实 registry；虚构临时项目验收不作为生产或业务独立验收证明。工具输出 ID 用于本会话证据追溯，跨会话复验使用本报告命令及 fixture 中的真实测试入口。

### 完成落档后的检查

主任务仅追加本次独立结论并同步地图/计划完成状态后，源 CLI 普通、严格、严格 attestation、stale、workset 和 drift 均退出 0，`git diff --check` 通过（e9501e）。本计划退出活跃工作集，宿主与后续计划仍 blocked，四份旧快照状态不变。已完成计划不参与现有 drift 的活跃影响范围匹配，故仍未提交的本计划文件新增“未被活跃计划影响范围覆盖”提示；这是完成状态与混合未提交工作树的既有规则结果，保留告警，不为隐藏它改门禁、重开计划或自动提交。

四份完成文档 176 个链接中无新增失效，仍仅两处既存地图锚点（a5008f）；反向引用和草案事实源搜索命中仅规则/历史验证说明（87bbca）。源码及测试仍匹配独立验收身份，24 个保护输入仍保持。全局已安装旧 CLI 的普通检查也通过（8874e8），其证明范围仅为兼容检查。未因纯落档重复全量测试。
