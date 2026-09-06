# 持续迭代治理优化：阶段 4 范围绑定样本

计划：[iterative-governance-reliability](../plans/iterative-governance-reliability.md#当前阶段)。阶段 4 使用源码读取及内存替代基线；新增参数尚不存在。用户已确认可选范围绑定，实施仍需本阶段独立准入。

## Step 0 基线

本节是实施前已执行命令与内容指纹的历史证据；其虚拟文件访问替身针对当时实现。当前正反验证使用下方真实临时文件测试，不把旧命令在新解析器上的输出当作原基线重放。

Revision 为 `336b728d7dacc335a35f2cf97ab39356e3a82ba0` 加未提交工作树；检查器 SHA-256 为 `157623731026d33e0993ad8908d708bdff5599cc1810383f0f4349790b1eb8df`。现有四份 `docs/attestations/*.json` 不写入或回填。

源码确认：旧快照只保存计划全文和地图全文 hash；`plans` 摘要丢失索引日期/证据，`map_blockers` 丢失方案/解除条件等完整单元格，不能直接用作新投影。`safe_relative_path` 是词法处理，接受 glob 且没有 symlink 检查。当前 main 在已有 errors 时仍可调用创建，必须只为新可选模式收紧写入前校验。旧生命周期在全文漂移后仍只警告，strict 不提升旧 hash 漂移。

下面命令调用真实旧检查函数，仅用虚拟文件与 BytesIO 替换文件访问；无真实写入或子进程。计划明确列出源码，地图包含两个计划；只改变另一计划的日期可隔离无关索引变化。它不证明新参数、真实文件系统和 Node 透传；这些须实施后在临时目录验证。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import hashlib, importlib.util, io, json
from pathlib import Path
from unittest.mock import patch
spec = importlib.util.spec_from_file_location('attest_baseline', 'scripts/check_plan_governance.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
root = Path('/virtual-repo')
plan = root / 'docs/plans/demo.md'
plan_map = root / 'docs/PLAN_MAP.md'
snapshot = root / 'docs/attestations/demo.json'
source = root / 'src/demo.py'
base = {
    plan: b'# demo\n\n## Impact\n\n- `src/demo.py`\n',
    plan_map: ('## 计划索引\n\n| 计划 | 状态 | 当前阶段 | 最后更新 | 依赖 | 证据 |\n'
               '|---|---|---|---|---|---|\n'
               '| [demo](plans/demo.md) | 已完成 | 阶段 1 | 2026-09-06 | - | test |\n'
               '| [other](plans/other.md) | 设计中 | 阶段 1 | 2026-09-05 | - | baseline |\n').encode(),
    source: b'print("before")\n',
}
digest = lambda data: hashlib.sha256(data).hexdigest()
record = {'plan': 'demo', 'phase': '阶段 1', 'status': '已完成',
          'plan_path': 'docs/plans/demo.md', 'plan_map_path': 'docs/PLAN_MAP.md',
          'plan_sha256': digest(base[plan]), 'plan_map_sha256': digest(base[plan_map])}
for scenario in ['unchanged', 'related-source', 'other-map-date', 'plan-content']:
    files = dict(base); files[snapshot] = json.dumps(record).encode()
    if scenario == 'related-source': files[source] = b'print("after")\n'
    if scenario == 'other-map-date': files[plan_map] = files[plan_map].replace(b'2026-09-05', b'2026-09-06')
    if scenario == 'plan-content': files[plan] += b'\nChanged scope\n'
    with patch.object(Path, 'exists', lambda p: p in files or p == root / 'docs/attestations'), \
         patch.object(Path, 'glob', lambda p, pattern: [snapshot] if p == root / 'docs/attestations' else []), \
         patch.object(Path, 'open', lambda p, mode: io.BytesIO(files[p])), \
         patch.object(Path, 'read_text', lambda p, encoding=None: files[p].decode(encoding or 'utf-8')):
        warnings = []; errors = []; reports = []
        m.warn_attestation_drift(warnings, root, {'demo': {'path': plan}}, errors=errors, strict=True, reports=reports)
        print(json.dumps({'scenario': scenario, 'warnings': len(warnings), 'errors': len(errors),
                          'reports': reports, 'real_writes': 0}, ensure_ascii=False))
PY
```

## 目标矩阵

行为契约只定义在[阶段 4 行为契约](../plans/iterative-governance-reliability.md#阶段-4-行为契约)，此处给出输入、命令和失败判定。定向 Python 命令为 `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/test_attestation_binding.py`；Node 实盘入口为 `node --test tests/npm_cli.test.mjs`。执行输出为终端 pytest/TAP，汇总和 hash 追加于本文件；完整迭代回放使用临时项目，不生成真实仓库快照。

| ID / 输入 | 预期 | 失败判定 |
|---|---|---|
| A01 legacy 和 purpose 无 file | 旧字段集合/状态输出/退出码保持；旧全文漂移 strict 仍只 WARNING | 自动增字段/回填/新默认阻断 |
| A02 新绑定，两份明确文件、干净或混合工作树、非 Git | 实际内容 hash；非 Git HEAD null，原样 current | 只记录提交、依赖暂存状态、无 Git 失败 |
| A03 文件内容改变/删除/变目录或 symlink | needs_review；默认警告、显式严格失败；仍保留报告记录 | current、记录消失、读取越界目标 |
| A04 无关地图日期/证据/注释、重排行、无关提交 | 新绑定 current，旧全地图快照仍按旧规则漂移 | 误触发新复核或偷偷修改旧字段 |
| A05 目标索引六列、计划全文、相关依赖索引或计划阻塞变化 | needs_review；strict 失败 | 摘要漏字段或忽略上游计划变化 |
| A06 新增/删除硬依赖、evidence、相关阻塞；仅改同名阻塞方案/状态 | 重新计算闭包/完整行后漂移 | 固定老成员、仅比较阻塞名称 |
| A07 soft/shared 关系自身与纯对端变化 | 行自身变化漂移，纯对端无关索引/计划变化不漂移 | 沿软关系扩张全图或忽略关系行 |
| A08 重复索引/结构章节、未知依赖/关系、无法归属的阻塞 | 创建失败零快照写入；检查 needs_review/严格失败 | 歧义被当空投影或 current |
| A09 空值、重复、非字符串（快照）、目录/glob/绝对/越界/symlink（含父级） | 明确拒绝，不读取越界内容；创建不留下文件/目录 | 接受非法清单或已有 errors 后仍写快照 |
| A10 binding 字段类型/version/hash/投影结构损坏，缺少绑定计划或文件；非对象 JSON | 已识别 binding 为 needs_review 且 strict 失败；非对象 JSON 保守 WARNING/跳过，检查只读 | 异常崩溃、静默 continue、自行补数据 |
| A11 有效 supersedes、缺目标/自指/环/不同计划或 purpose/多个 current、跨模式后继 | 有效链单一当前，非法关系可见且创建先拒绝；binding 可替代旧，旧后继不可使 binding 前驱免责 | 无效后继压掉旧证据或错误恢复旧 current |
| A12 前驱内容漂移且有效后继存在、后继随后漂移 | 前驱 superseded 不永久阻断；后继漂移阻断，不恢复前驱 | 历史 hash 永久阻断或后继失败恢复旧通过 |
| A13 新增未列文件、HEAD 变更 | 不声称自动发现未列文件；HEAD 仅定位 | 把 hash 声称为独立验收或完整变更范围 |
| A14 参数组合/未初始化项目/错误治理/目标快照 symlink；mkdir/write/清理 OSError | 参数或预检失败零快照写入；实际 I/O 失败清理本次部分文件/空目录，清理失败报告残留；无开关保持原样 | 新模式静默成功、删除既有内容或掩盖残留 |
| A15 Node → Python 实盘迭代 | 临时 init → 准入/workset → 实现/证据 → opt-in snapshot → 无关变化仍有效 → 源码变化需复核 → 替代快照 | CLI 不透传、退出码不符、原仓库快照被改 |
| A16 全计划回归与引用 | npm run verify、既有阶段矩阵/资源、skill 校验和引用通过；独立完成复核通过 | 覆盖门槛失败、前序契约回退或证据冒充业务验收 |

## 安全与回滚

仅显式快照命令在测试临时项目内写入；真实仓库四份历史快照保持字节。hash 不是签名，不验证复核者身份，也不自动证明显式文件清单完整；源码/证据范围由独立复核判断。测试临时 Git、临时打包/安装及覆盖产物属于本阶段授权验证，不全局同步、发布或改宿主。失败只撤销本阶段精确差异并保留复核历史。

## 实际基线输出

2026-09-06 执行上方命令，退出 0，工具输出 `81c0b9`：unchanged 与 related-source 均 WARNING 0 / ERROR 0 / current；other-map-date 与 plan-content 均 WARNING 1 / ERROR 0 / needs_review；全部 real_writes 0。确认两个旧行为边界，未创建任何真实快照。

准入复核补充旧缺陷：`[]` 等非对象 JSON 会触发 AttributeError（复核输出 `27214c`）；实施后按损坏 JSON 的兼容分层输出 WARNING 并跳过，不据此声称识别了 binding。

## 实施后验证

2026-09-06，在本阶段独立准入通过后执行。实现者为主任务；测试实现助手为 `/root/iterative_stage2_acceptance`（此前只完成阶段 2 独立验收，未参与阶段 4 独立复核）。以下为实施证据，完成结论仍须另一名独立复核者。

| 验证 | 实际结果 | 工具输出 |
|---|---|---|
| 两项真实临时 Python CLI 失败回归 | 旧 checker 不识别新参数，目标退出 0、实际 2；2 failed，未写快照 | `4393b9`；根任务另以真实 Node→Python 临时目录确认同一结果 |
| 全投影/生命周期/路径扩展 | 初版 55 passed；后续读取监测发现 symlink 外部计划被 main 提前读取两次 | 真实失败 `c26986`、`1cb73d`（121 passed、1 failed） |
| 修复读取顺序后的定向 Python | 126 passed；含 10 组创建/检查路径读监测、7 类 I/O 定点故障 | `4f9e60`、`b6f3b9`；`python3 -m pytest tests/test_attestation_binding.py --no-cov -q --tb=short` |
| 源与已安装包完整迭代 | 2 项定向通过；复用原临时安装，不新增全局环境 | `cf48dd`、`211f74`；`node --test --test-name-pattern='binding iteration\|packed package' tests/npm_cli.test.mjs` |
| 完整统一入口 | Python 334 passed、分支覆盖率 93.16%；Node 99/99、0 skipped；严格治理通过 | `f22620`、`79ae3e`；`PYTHONDONTWRITEBYTECODE=1 npm run verify` |
| skill、格式与事实源反查 | 有效、diff 无空白问题；事实源词仅命中禁止规则/检查说明；后续计划依赖警告保留 | `ad2abb` |
| 六份当前文档本地链接 | 排除代码块后 97 个链接/锚点全部有效 | `d4836f` |
| 阶段输入指纹保持 | 检查 29 个既有文件，只有本阶段 README/地图/skill/checker/Node 测试变化；其他 24 个保持 | `0e69d8` |

其中一次扩展测试的 13 项失败来自测试 helper 漏掉原有 `ATTESTATION: ` 前缀，修正 helper 后重跑；未通过改产品输出迁就测试。全量验证在 macOS 执行，未运行远端 CI、发布或同步全局 skill。临时迭代中的准入与复核文字是虚构 fixture，证明 CLI 状态/证据路径及安装透传，不代表真实业务或宿主验收。

### A01—A16 覆盖入口

| 矩阵 | 可复现覆盖 |
|---|---|
| A01/A02/A13 | 精确旧字段/默认漂移、独立计算规范投影 hash、真实临时 Git 的提交/暂存/工作树不同内容及无关 HEAD |
| A03—A07 | `test_bound_content_changes_keep_review_record`、五类表逐列变异、闭包重算、无关行排序/注释和软/共享对端保持 |
| A08—A10/A14 | 歧义图、非法路径、存储损坏、丢计划/地图、组合错误、10 组路径读取监测、实际排他写的定点 I/O/残留报告 |
| A11/A12 | 同计划/purpose 替代、双向跨模式、自指/环/非法后继/重复 current、前驱文件删除后替代及后继漂移不恢复旧 current |
| A15 | `exerciseBindingIteration` 在源入口和已安装包各调用：init→已准入 workset→虚构实现/证据→绑定→无关地图保持→源码变更需复核→新绑定替代，历史字节保持 |
| A16 | 统一 verify 同时执行前序阶段全部回归，skill 资源字节/初始化保护/严格门禁/发布失败中断全部保留；独立完成复核待执行 |

### 被验证源码身份

| 文件 | SHA-256 |
|---|---|
| scripts/check_plan_governance.py | `f6b94927608618ab4d8386a31dee81c3a014fd299e60548c1883b5fac579d0d9` |
| tests/test_attestation_binding.py | `4b61525fbf2e01db64abdb4d7a4d93c5232b1551aa91a1884031ea01c800c19f` |
| tests/npm_cli.test.mjs | `e792ef2da8489c66dc033aebeb96443ff1ecb6770280b7cb97005efa68e5ad4d` |
| README.md | `ed7844e7bbeab8494c10a540246254d9cdd85d6e9508c37789221323bcdf17c8` |
| resources/skill/SKILL.md | `d99df9cd4173416fcbd92c06ae7050a8c08ef0d79e009e1f0435c4ecfa3fd3ae` |

并行新增 `plan-governance-workflow-streamlining` 及其地图行由另一工作流产生，本任务仅将两个计划/地图阻塞状态对从未识别词规范为“未解决”（四个单元格），保留设计中与真实阻塞。该专项计划规范化后的 SHA-256 为 `d34b22c18eb69d9210787964840bd0c1757caa7a5b769410c1b4303fe49e8ba0`，不是本任务创建的实现成果。

### 保持不变的阶段输入

| 文件 | SHA-256 |
|---|---|
| .github/workflows/ci.yml | `cf0c5b117591958bcb0adcab2cce200e48ef1a0c7c7e77a6c88c98aec69a5b0b` |
| AGENTS.md | `b98b15a235089010645b62a7e2c0316f1ae2bcd1895ff416183a707ae7f90fb0` |
| CLAUDE.md | `3710acaba20dea6d87543eb0a73f4a126e27f2dd9d368f470e45d90f866e850a` |
| docs/plans/phase-local-review-dispatch.md | `a21f11cbe54ad85585646a844fa23c1ec205629822eb13d6d7935193cbc0f17b` |
| docs/plans/plan-governance-distribution-setup.md | `1c71f78c37a38daf83dbe54a8d0ba1d31fef2cc1dc384c528e7e04fc4cd9998c` |
| package-lock.json | `e8db48f2d2d2b9596d0a37b3aa1c81d1e6a5edac3f0231847598188f4107bd95` |
| package.json | `d6d18829d96b010533a4b579d94b77fc9ee26c591c63551898a36d7808f544ad` |
| resources/manifest.json | `47a2c566580eec7b3799f30fc47c1b504ab23831630598530b06fa60aa9bf6bd` |
| resources/skill/agents/openai.yaml | `f70e0da9a4aa0b031c6f430b86161a83ec2633c6315ffe9a0af346fb1064d736` |
| resources/skill/assets/PLAN_MAP.template.md | `cc216e0f6a8147c64ed625360f8f44602022c531acc2f4639fb06a2dcee7325b` |
| resources/skill/assets/plan.template.md | `af5e5719b8df8c671d3eb0ea6ab5713a24b559464a19fc0c47ff13311dbdf907` |
| scripts/init_plan_governance.py | `f7f17ae2a54b7be4d0dc964065306748780c56727804d43a614c00ca6855d5d8` |
| scripts/plan_governance_hook.py | `fe33099f3e5c602e454f913e90feccbff9644de363740da37576fdce822fbcce` |
| scripts/release_npm.mjs | `d746fb669f4aa9148ab515e4489db94732932d66403beb3189c1aefc83444f78` |
| tests/test_check_plan_governance.py | `dc73e21dd707a631b8a596d1b31cdef9a1b509148310ddf3f308cf163dbb7e46` |
| tests/test_init_plan_governance.py | `166e19192333182cb4cdca17f788f4a999c956f16c229746e79946c0bed9f255` |
| tests/test_plan_governance_hooks.py | `8a07a4ff88b4f1111d6d1b34270196db4e44101d778b611c3630e0d1d50854a3` |
| scripts/verify.mjs | `fbca04629959f57372afb41bc0776ff623d94b566c44e785243e811d374f34ca` |
| tests/verification_release.test.mjs | `4c6a845d90f12307bb0587aadbc76be5eb331850d6810b83649c54f4fc0b5bb8` |
| resources/skill/assets/spec.template.md | `069c12a70374b135012aec3b50755abe44fdc2380b0eb63e5c3ee4cc7dd4036d` |
| docs/attestations/functional-graph-governance.json | `dad21c0adf77bd31f9ff18021c6d6df46577bbe374f682c174a3598a599e4627` |
| docs/attestations/phase-entry-gate-hardening.json | `427c512919c83f9e0437b6ca2d63b5cefb9e6fce3afc0229262b8d32ff5908ce` |
| docs/attestations/plan-governance-distribution-setup.json | `a11de023a0e96c03fa3fad5a8a89a2fc03ebc9489d22a9b166931a99997761f5` |
| docs/attestations/plan-governance-npm-cli.json | `87722e855c14c3bcc08c23d43ef38455cdd091eee00b5dbbc76efd20dd3c8dfd` |

## D02/D03 修复与重审材料

本节保留送审时历史状态；D02—D04 现已独立确认修复，最新结论见[完成复核报告](../reviews/iterative-governance-reliability-stage4-completion-review-20260906.md#d04-独立修复确认)。

[第一轮独立完成未通过](../reviews/iterative-governance-reliability-stage4-completion-review-20260906.md#第一轮未通过)已追加保留。D02/D03 当前仍为阻塞，以下仅为修复实施声明，须新的独立复核者确认后才能解除；不因单元测试通过改写验收结论。

- D02：目录使用显式 stat/iterdir，清单不可读取会报告 I/O，默认检查 WARNING、strict 检查和新绑定创建预检失败。读取目录失败不等于空清单，无法绕过已有 current 检查。
- D03：涉及 binding 的混合检查，旧快照的计划/地图 hash 分支也先校验路径，不跟随外部 symlink。
- 新增 10 项真实临时回归：000/0300 均先用 os.listdir 确认 PermissionError；默认/strict 检查及创建零写入；legacy/purpose-only 前驱各配计划/地图 symlink，spy 确认外部读取为零。测试在 finally 恢复权限并清理。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/test_attestation_binding.py --no-cov -q --tb=short`：136 passed、0 skipped；新 10 项 10/10。输出 `9e188a`、`519f19`、`0daa10`。首次运行时修复已就绪，旧失败使用独立实盘 `2e2fc9`、`bcf83b`、`2866bb`，不称此次运行取得旧代码失败证据。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest`：344 passed，分支覆盖率 93.19%，退出 0；`8abf00`、`9bee48`。当前真实阻塞仍保留，完整 verify 的严格节点应保持阻断；待独立确认缺陷可解除后，再执行完整 verify 形成最终完成证据。

| 修复后文件 | SHA-256 |
|---|---|
| scripts/check_plan_governance.py | `a84096b94ca4adc0818c47e8a46c232fd6144b0fa11f65661b6b3ddfcf355fe0` |
| tests/test_attestation_binding.py | `8a1c9071d991ff332d61f41c6bb3cee2f7540c6f90f48170f791fa7b1815a0ea` |

Node 测试、README、skill 和前述 24 份保持输入均未因本次修复改变。

## D04 修复与重审材料

本节保留送审时历史状态；D02—D04 现已独立确认修复，最新结论见[完成复核报告](../reviews/iterative-governance-reliability-stage4-completion-review-20260906.md#d04-独立修复确认)。

第二轮独立复核确认 D02/D03 可解除，并发现 D04；实际失败、复核者和审查身份见[第二轮修复复核](../reviews/iterative-governance-reliability-stage4-completion-review-20260906.md#第二轮修复复核)。主任务只在参与 binding 的混合旧快照 hash 读取处捕获 OSError，报告可见原因并保留内容漂移和替代记录；未启用范围绑定时保持旧路径。独立复核者未参与修复或回归编写。

- 新增 4 项真实临时子进程回归：legacy/purpose-only × 普通计划/地图文件 chmod 000，先用 read_bytes 确认 PermissionError；各执行默认及 strict，要求无 Traceback、绑定 needs_review、strict 1；计划不可读时前驱仍 superseded。地图不可读时旧快照沿用未登记跳过，不强制改变旧记录语义。恢复权限后 strict 0、旧 superseded/新 current，目录字节完全保持，finally 恢复权限。
- 修复前命令 `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/test_attestation_binding.py -q -k d04 --no-cov`：4 failed、136 deselected（`87403e`）；计划两例是真实未捕获异常，地图两例是初始测试过度要求旧前驱也留在输出，后者修正测试预期，不作为产品缺陷。
- 修复后命令 `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/test_attestation_binding.py -q --no-cov`：140 passed、0 skipped（`8bd534`、`bdcf5c`）。此为实施验证，D04 仍等待独立确认，尚未执行最终统一 verify。
- checker SHA-256：`669c6c3e7e0690f5e57c98a4a221af7a712a1ff236a6cf550a765384e77c6ebb`；Python 测试：`822efac4a11bb6cc89d9bde4dfe025d908af25efc300ecf8faaeef5491723571`；Node 测试仍 `e792ef2da8489c66dc033aebeb96443ff1ecb6770280b7cb97005efa68e5ad4d`。

后续减负计划在独立复核期间追加执行减负与调度需求，地图的相关描述同步变化；本计划保留该并行内容，不将旧地图全文 hash 不同当作自身代码失效，也不放宽全仓门禁或接管其设计。

## 最终验收

2026-09-06，[第二轮独立完成验收通过](../reviews/iterative-governance-reliability-stage4-completion-review-20260906.md#第二轮通过)：阶段 4 与全计划完成，D02—D04 均已解决。最终源码/测试身份见该报告；本文件早先各轮测试计数和“待重审”文字保留为当时历史。

统一 `PYTHONDONTWRITEBYTECODE=1 npm run verify`：Python 348 passed、分支统计总覆盖率 92.97%，Node 99/99、0 skipped（149047、2ac9c1）；独立绑定回归 140/140。源/安装包完整迭代、前序保持和新增/修改链接通过。虚构项目技术回放的证明范围、旧快照及其他计划阻塞边界不变。
