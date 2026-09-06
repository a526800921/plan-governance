# 持续迭代治理优化：阶段 3 文档与任务样本

日期：2026-09-06；所属计划：[iterative-governance-reliability](../plans/iterative-governance-reliability.md#当前阶段)。本文件记录实施前基线、输入和验证入口，不作为新规范的第二事实源。以下前半保存实施前基线；本阶段实施和后测另见文末记录。

## 基线类型

1. 只读源码与模板定位：`/root/stage3_document_baseline` 核对规则、模板、内嵌生成器和分发清单，不运行生成、测试或修改文件。
2. 独立技能行为走读：`/root/stage3_forward_baseline` 使用旧 skill 和四个模板处理下面三项虚构请求，未读取本优化计划、预期答案或其他代理结论；不实施、不承担准入/完成复核。
3. 内存生成器替代基线：直接调用生成函数得到字符串，没有创建目标目录、Git 或文档。它不证明真实 init/upgrade/setup 的效果，后者在准入后验证。

HEAD 为 `336b728d7dacc335a35f2cf97ab39356e3a82ba0` 加混合工作树。基线身份：

| 文件 | SHA-256 |
|---|---|
| resources/skill/SKILL.md | `a9538a355fb556a3d99f88072967227259120d6f8c95c9b726c3a996cf7a2e97` |
| resources/skill/assets/PLAN_MAP.template.md | `ca08918fb0d6531ff9c18a11513d346b129b0212f26d91921c191911a823453c` |
| resources/skill/assets/plan.template.md | `48af0150688626401b76fec69c02edcfb50b174b6eab4f1cd2c2985b0a842f18` |
| resources/skill/assets/adr.template.md | `d34ec253a3814c851f657fc19d6efd1c5941ed86028d0c2b364cba2c0fbe7879` |
| resources/skill/assets/migration.template.md | `68d947c9d459737a329db45b8f3533d707528153f7fec6429ff5063a0d407616` |
| scripts/init_plan_governance.py | `4bd7cc95e67370511633ee0266e9d0f29c7186ea1f23fde54ecbf14ba91c63cd` |
| resources/manifest.json | `58b019fc1626044afe04edff2f303e7fefff89cd67c8f507df3249b8b43135e5` |
| AGENTS.md | `6a54e4194e8bc55de25a34ab21dd90b3fa5c42b58faf5261cc8b2493c7d6d0f3` |
| CLAUDE.md | `acb71a4e36e534940707010bf70579ec967aeb1102fd50c7ec93adb2091d3501` |
| README.md | `805e48a37d956313783e0a8aae0e6fe4b76ad1160d799c551e666dd5d1044cf9` |
| tests/test_init_plan_governance.py | `af157cde0e9a7823e1ae3ed6b3eae2c45365c6dc809115314c72dfac1eee09b8` |
| tests/npm_cli.test.mjs | `91f5c241816d85232ab597bbde188db40fb9e7a93fa9bddf425ac49cb2e91c0d` |

## 三类原始请求与实际走读

以下输入和结果是旧规则下的实际技能走读，不是新实现已经完成的声明。

| 样本 | 原始输入 | 实际走读结果 | 已有能力与缺口 |
|---|---|---|---|
| S3-01 | 单页保存提示“已保寸”改为“已保存”；无行为变化、无既有治理计划，用户明确要求修正文案 | 不新增/更新治理文档，先定位文本，再在同一路径确认正确提示；无需 grilling/阶段门 | 小任务豁免已经有效，应保持；不得宣称该能力本轮才实现 |
| S3-02 | 已准入输入校验阶段，目标/范围/公共契约/完成条件/授权均未变且无阻塞；空白输入和重复提交尚未满足原验收 | 复用原计划与准入，补复现/验证记录，地图按实际元数据同步；从原场景读取业务预期，不擅自定义去重方式 | 可组合现有规则得到短路径，但没有直接区分原验收未满足与新需求，存在误重开门禁的解释成本 |
| S3-03 | API name 改为 display_name；已有 openapi.yaml，兼容窗口/废弃/回滚未定，有地图但无专项计划 | 先核对契约，再逐项 grilling；确认后最少新建一份计划，引用现有 OpenAPI；ADR/migration 按实际需要 | “计划记录 Schema”和“spec/Schema 是契约”并存，只能靠单一事实源原则消解；无 docs/specs 查找入口，用户可观察结果依赖执行者自行补足 |

走读者对 S3-01/02 置信度高，S3-03 中高。模拟业务没有实际运行，因此这些观察只证明技能解释结果，不证明客户端兼容、业务修复或用户验收通过。后测须给新上下文相同请求与最少原始材料，不提前提供期望文档数量或本表结论。

## 源码观察

- skill 的启用判定/需求探索已覆盖豁免；仓库模型允许 spec，但未给 docs/specs 入口，计划与 Schema/migration 有职责重叠。
- plan 模板有 Step 0、验证、覆盖率和完成条件，没有用户可观察场景表或明确契约来源定位。
- `scripts/init_plan_governance.py` 的 `agent_rules_body` 与 `plan_map_content` 内嵌规则；计划正文读取资源模板。同步应覆盖这两份内嵌投影，无需重构生成器。
- checker 只扫描平铺 `docs/plans/*.md`；已有证据校验不普遍验证 Markdown 锚点。保持平铺和固定机器标题，另做文档链接检查，不声称 strict 已具备任意锚点门禁。
- 当前没有 docs/specs、docs/adr、docs/migrations 的正式文件，不为空目录创建占位文档。`resources/manifest.json` 显式分发 6 项 skill 资源，新增可选模板须纳入该清单。

## 可执行基线命令

在仓库根目录执行；输出在 stdout。该命令在实施前执行的四个布尔结果依次为 false、false、true、true，工具输出 `923d4f`。修改模板后这些观察允许变化，但机器固定标题应保留。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PYCODE'
import importlib.util,json
spec=importlib.util.spec_from_file_location('init_snapshot','scripts/init_plan_governance.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
plan=m.plan_content('fixture','Fixture','设计中','阶段 0','Fixture goal')
rules=m.agent_rules_body(); pm=m.plan_map_content('fixture','Fixture','设计中','阶段 0')
print(json.dumps({
 'plan_has_observable_acceptance':'用户可观察验收' in plan,
 'rules_have_specs_directory':'docs/specs' in rules,
 'map_repeats_schema_owner':'记录字段方案、Schema、枚举' in pm,
 'plan_has_required_titles':all(x in plan for x in ['## 当前阶段','### 阶段准入摘要','## 最新独立准入复核','## 独立复核记录'])
},ensure_ascii=False))
PYCODE
```

人工走读的复现方式：以新上下文只读代理读取上述受审版本的 skill 和模板，仅提供三项原始请求，要求报告最少文档、下一动作、可观察验收及未决问题。实际只读命令为 `cat resources/skill/SKILL.md`、`rg --files resources/skill/assets`、`nl -ba` 各模板、`shasum -a 256` 与规则关键词 `rg`。模型走读具有非确定性，不能用某次措辞或字符串匹配替代行为判断。

## 实施后验证入口

目标契约、预期和失败判定只在[阶段 3 目标矩阵](../plans/iterative-governance-reliability.md#阶段-3-目标矩阵)定义。准入后执行：

- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider tests/test_init_plan_governance.py --no-cov`
- `node --test tests/npm_cli.test.mjs`
- `PYTHONDONTWRITEBYTECODE=1 npm run verify`
- `python3 /Users/jafish/.codex/skills/.system/skill-creator/scripts/quick_validate.py resources/skill`
- 当前新增/修改规则与样本的 Markdown 本地链接和固定锚点检查、`git diff --check`、计划名/关键字段/草案事实源 rg。

新上下文行为后测覆盖三原始请求，另用“最新独立复核未通过”的 S3-02 变体检查分流没有覆盖原停止门禁。init/upgrade/setup 在测试临时目录内运行并清理；Node 分发测试会临时打包/安装且可能读网络，属于本阶段验证边界，未授权全局安装或真实发布。


## 准入复核补充：受管区外字节保护

`/root/iterative_stage3_gate` 只读核对发现，旧 `update_managed_file` 使用 `current.rstrip()` 追加区块，会删除尾部空白；文本读取的通用换行转换会改写 CRLF 的非受管区。主任务保留保护承诺，将该局部兼容修复纳入阶段 3，未缩减为只验证普通 LF 文本。尚未修改实现。

2026-09-06 主任务执行以下内存文件替身，输出 `7dac85`：append-trailing 的 original_prefix_preserved=false；replace-crlf 的 prefix/suffix 均 false。没有真实文件写入。修改后用真实临时文件反例证明原字节保留和二次执行幂等。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PYCODE'
import importlib.util,json
spec=importlib.util.spec_from_file_location('managed_snapshot','scripts/init_plan_governance.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class File:
 def __init__(self,data):self.data=data
 def exists(self):return True
 def read_text(self,encoding):return self.data.decode(encoding).replace('\r\n','\n').replace('\r','\n')
 def read_bytes(self):return self.data
 def write_text(self,text,encoding):self.data=text.encode(encoding)
 def write_bytes(self,data):self.data=data
class Root:
 def __init__(self,target):self.target=target
 def __truediv__(self,name):return self.target
begin=m.AGENTS_SECTION_BEGIN;end=m.AGENTS_SECTION_END
cases=[('append-trailing',b'user \t\n\n \t',None),('replace-crlf',('prefix \t\r\n'+begin+'\r\nold\r\n'+end+'\r\nsuffix \t\r\n').encode(),('prefix \t\r\n'.encode(),'\r\nsuffix \t\r\n'.encode()))]
for name,raw,outside in cases:
 target=File(raw);m.update_managed_file(Root(target),'AGENTS.md',m.agents_md_section(),begin,end)
 print(json.dumps({'case':name,'original_prefix_preserved':target.data.startswith(raw) if outside is None else target.data.startswith(outside[0]),'original_suffix_preserved':None if outside is None else target.data.endswith(outside[1]),'real_writes':0}))
PYCODE
```

这是准入过程的范围补全，尚未形成一次失败完成验收。独立准入的最终结论须审查更新后的目标及此基线，不能把原候选“只改内嵌文案”当作完整实施范围。


## 实施后机械验证

2026-09-06，独立准入通过后实施。以下是实施者验证声明，完成结论仍需独立验收。

| 实际命令/检查 | 结果 |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider tests/test_init_plan_governance.py -k preserves_unmanaged_bytes --no-cov -q`（旧实现） | 4 failed，27 deselected；AGENTS/CLAUDE 的尾空白及 CRLF 均破坏非受管前缀 |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider tests/test_init_plan_governance.py --no-cov -q`（修复后） | 32 passed；包括新保护反例、幂等、最小目录与 upgrade/rules-only |
| `node --test tests/npm_cli.test.mjs` | 11/11 通过；真实临时 pack/install，manifest 和全部 skill/runtime 字节一致，安装 init 与模板一致，Codex/Claude 临时 setup 一致 |
| `PYTHONDONTWRITEBYTECODE=1 npm run verify` | 退出 0：严格治理 → Python 208 passed/93.15% → Node 98/98、0 skipped；工具输出 `4d7122`、`29efb2` |
| `PYTHONDONTWRITEBYTECODE=1 python3 /Users/jafish/.codex/skills/.system/skill-creator/scripts/quick_validate.py resources/skill` | Skill is valid；`848b0c`，只验证元数据与结构 |
| `git diff --check`、现行字段权责/草案事实源 rg、本地链接扫描 | 通过；81 处扫描中 80 处可定位，1 处是既有地图模板的 example-plan 占位链接，实际 init 的真实路径由安装测试验证；`d175db`、`6dee50` |

非受管字节修复只改变更新函数的读写和追加分隔，原 CLI 参数和标记识别保留。现有同源 checker 测试改在临时目录构造，以免 chmod 真实仓库文件。测试仅修改各自临时目标；未全局安装或同步、未发布、未改变 registry/版本/锁文件。

| 受验证文件 | SHA-256 |
|---|---|
| resources/skill/SKILL.md | `12e270717d235315363893881b7b4c75afc65961b02cdb80b46a4124fa194ec0` |
| resources/skill/assets/PLAN_MAP.template.md | `cc216e0f6a8147c64ed625360f8f44602022c531acc2f4639fb06a2dcee7325b` |
| resources/skill/assets/plan.template.md | `af5e5719b8df8c671d3eb0ea6ab5713a24b559464a19fc0c47ff13311dbdf907` |
| resources/skill/assets/spec.template.md | `069c12a70374b135012aec3b50755abe44fdc2380b0eb63e5c3ee4cc7dd4036d` |
| resources/manifest.json | `47a2c566580eec7b3799f30fc47c1b504ab23831630598530b06fa60aa9bf6bd` |
| scripts/init_plan_governance.py | `f7f17ae2a54b7be4d0dc964065306748780c56727804d43a614c00ca6855d5d8` |
| README.md | `b23630b056e7cd82c4545428186ee4ccf637bd46980a921e7c1c6f4aee44b1df` |
| AGENTS.md | `b98b15a235089010645b62a7e2c0316f1ae2bcd1895ff416183a707ae7f90fb0` |
| CLAUDE.md | `3710acaba20dea6d87543eb0a73f4a126e27f2dd9d368f470e45d90f866e850a` |
| tests/test_init_plan_governance.py | `166e19192333182cb4cdca17f788f4a999c956f16c229746e79946c0bed9f255` |
| tests/npm_cli.test.mjs | `213f94bf6648dd6146b4d7a13c554638e0a34e86238be1a5ded96f094dc8f2bd` |

## 独立新上下文行为后测

后测者 `/root/stage3_forward_validation` 未参与设计/实施，仅读取上述 skill 和五模板，没有读取优化计划、fixture、预期文档数量或其他代理结论。输入为 S3-01/02/03 原始请求，加“最新独立阶段门未通过”的 S3-02 变体，以及“已确定的长期 CLI 行为无正式契约源、后续持续变更”的样本。实际只读命令为 cat/rg --files/shasum；受审 skill/template hash 匹配上表，旧 ADR/migration 模板不变。

| 输入 | 实际决定与验证建议 |
|---|---|
| S3-01 | 0 新/改治理文档，直接在原保存操作观察正确提示；不强制 grilling/阶段门 |
| S3-02 | 复用原计划/场景/准入，追加原验收未满足记录与证据；预期从原场景读取，不发明去重方式 |
| S3-03 | 保留 OpenAPI 唯一字段来源，先查事实并逐项澄清窗口/废弃/回滚，确认后新建一份计划；migration/ADR 按需，不创建重复 spec |
| 最新失败复核变体 | 保留失败阻塞及历史通过，停止阶段实施；普通反馈分流、用户“继续”和实施声明不覆盖新失败，需新有效独立通过 |
| 无正式来源的长期 CLI 行为 | 按需建一份有内容的 spec，记录已确认现行输入/输出/失败/兼容与可观察场景；本次计划链接差异，spec 不复制状态和进度 |

五项决定符合当前阶段目标。模型走读具有非确定性，只显示这些输入下的文档选择和停止判断，不证明真实业务、宿主执行、阶段准入或自动化行为保证。本记录由主任务按独立返回结果落档，仍须独立完成复核结合当前源码与可复现机械验证判断。
