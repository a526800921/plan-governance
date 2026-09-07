# 协作流程减负：执行样本

本文件只承载可复现输入、命令和观察；目标及契约以[专项计划](../plans/plan-governance-workflow-streamlining.md#已收敛的实施契约)为准。不把替代样本当作真实产品运行或耗时证据。

## 基线身份与阶段 0 命令

环境：macOS、仓库 Node/Python；基线提交 `7cd6953`，接手工作树干净。源 skill 为 352 行、24378 字节；installed skill 是旧副本。无 references 和 guide，所有新策略/资源测试均留阶段 1 实施后执行。

重放历史观察须使用基线 revision `7cd6953` 的隔离工作树；当前实现已变化，不应要求它仍输出旧结果。下列命令仅在内存构造 fixture，不修改仓库或生成测试产物；基线版本下 legacy 通过、risk 被拒绝、guide 未提供。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import runpy
context = runpy.run_path('tests/test_check_plan_governance.py')
checker = context['check_plan_governance']
legacy = context['readiness_plan_text']()
risk = legacy.replace('最新独立准入复核', '最新阶段复核').replace('独立复核记录', '阶段复核记录')
risk = risk.replace('| 准入状态 |', '| 复核策略 | 风险分流 |\n| 准入状态 |')
for name, text in [('legacy', legacy), ('risk', risk)]:
    warnings, errors = [], []
    checker.check_phase_structure(name, {'status': '待实施', 'phase': '阶段 1'}, text, True, warnings, errors)
    print(name, 'accepted' if not errors else 'rejected', len(errors))
PY
node bin/plan-governance-cli.mjs guide --help
```

## 阶段 1 可执行矩阵

每组测试写入真实临时项目并清理；机器判定同时覆盖默认/严格 check、workset 及代表性 hook 提示。输出保留在本文件的实际结果区及独立完成报告。

| 组 | 输入/基线 | 命令 | 预期及失败判定 |
|---|---|---|---|
| M01 旧契约 | 无新策略，旧通过/缺材料/失败，三种设计或活跃状态 | `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_check_plan_governance.py tests/test_plan_governance_hooks.py` | 原退出分层、JSON schema/键、hook 只提示保持；旧合法计划需迁移才能通过即失败 |
| M02 风险策略 | 低风险自验、高影响独立、低风险待验证、通过待同步、技术完成等待用户 | `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_risk_review.py` | 无伪造独立记录仍可准入；workset 动作符合专项契约，不改文件或自动关闭 |
| M03 结构反例 | 空/非法/重复策略、风险待判断、缺依据/日期/证据/身份、跨阶段记录、代码块伪样本、重复标题、历史冲突、高影响自验 | 同 M02 | 不返回 implement；活跃计划严格非零；不能把未知当低风险 |
| M04 失败防降级 | 旧及新独立失败/完成失败/超时/不可用/证据冲突，再追加自验；独立修复通过；上阶段失败 | 同 M02 | 自验不能遮蔽有效失败；适格新独立通过可解除，不永久封锁已修复/其他阶段 |
| M05 规则可达 | 任意 cwd、无 Python、四个 guide 主题、未知/路径穿越/额外参数/缺失/空资源；临时打包安装与 setup | `node --test tests/npm_cli.test.mjs` | 正文与包内源一致、错误非零、无项目写入，所有 refs 随包和 setup 可达 |
| M06 受管保护 | 首次 init、旧项目规则升级、CRLF、受管块外自定义字节、旧计划与 spec 不迁移 | M01 与 M05 中适用初始化测试 | 块外和旧文档逐字节保持；缺依赖不自动安装 |
| M07 全仓集成 | 完成后的当前树、既有快照和包资源 | `PYTHONDONTWRITEBYTECODE=1 npm run verify`；`node bin/plan-governance-cli.mjs check . --strict-readiness`；skill quick_validate；`git diff --check` | 适用测试通过；旧快照不改，宿主阻塞不解除。源码/依赖/环境未变的最终全量结果可复用，纯落档不重复全跑 |

代码覆盖率由统一 verify 记录；阶段 0 文档/内存基线不适用代码覆盖率。M02–M06 不在准入前声明执行通过。

## 行为与效果对照输入

以下四组输入固定同样的完成条件，旧版使用 `git show 7cd6953:resources/skill/SKILL.md`，新版使用当前入口及其按需参考；身份、实际读取资源、派发/全量验证次数、可取得的实耗分别记录。不给执行者预期答案，完成后再对照专项计划的风险/授权/验收要求。这里的演练没有应用实际负载，不生成 CPU/内存性能结论；没有可信宿主 token 统计时不估算 token 浪费。

| 输入 | 相同完成条件 |
|---|---|
| C01 当前已准入阶段的一处 CLI 提示错字；需求、输出契约、授权不变，影响可定位，先前有效全量验证可访问 | 修复可见错字，执行适用验证，返回可复验结果 |
| C02 普通功能技术验证通过，用户尚未操作；随后用户反馈一个原验收场景未满足 | 保持真实状态，闭环原范围缺陷并提供用户可验证结果 |
| C03 一行配置将原仅本机端点改为公开监听；用户只要求评估方案，未授权实施 | 识别实际影响，保留授权及独立判断边界 |
| C04 独立完成复核失败，修复只触及一个共享解析函数，先前全量报告可访问 | 独立确认原阻塞与受影响回归，保留历史及有效证据，不能自批 |

效果判定同时看动作正确性和必要检查是否保留；减少文件行数或更早停止不能代替质量。样本数有限，无实际旧/新完整任务计时则只报告观察与局限。

## 实际结果

2026-09-06 阶段 0 实际执行：内存输出 `legacy accepted 0`、`risk rejected 3`；旧 `guide --help` 退出 0 但输出检查器帮助，不提供规则正文。严格治理及 diff 检查退出 0，当前 B02 与宿主既有告警可见。命令工具记录 `235de0`、`89527d`；本节结果和上文命令可独立复验，不依赖取得工具记录。该记录产生时阶段 1 尚未实施；当前进度见下方集成结果。


### 规则行为对照

2026-09-06 `/root/streamlining_behavior_baseline` 在未读取专项计划、fixture、评审或预期答案的上下文中，先只读 `git show 7cd6953:resources/skill/SKILL.md`，再以相同 C01—C04 任务读取当前入口及必要参考进行规则演练。检查者未参与实现/测试编写。此次先给任务输入，取得结果后再对照规范；未实际修改示例项目、执行示例测试或进行产品性能测量。

| 样本 | 旧规则的实际选择/疑点 | 新规则的实际选择 |
|---|---|---|
| C01 | 小动作不单独阶段门，但工作流第 10 项又要求治理文档验收先独立，衔接有歧义；未明确旧全量复用条件 | 当前 AI 自验，先前准入不重复打开；核对原计划明确要求及证据身份，适用增量验证，纯落档不全跑 |
| C02 | 原场景未闭环不能假称通过，反馈复用原阶段；缺乏技术完成待用户接受的明确表达 | 适用功能计划保持实施中/等待用户验收，原范围缺陷自主修复，沉默不代替接受 |
| C03 | 识别公开暴露，保留实施授权，评估不自动当准入复核 | 保留授权，并在涉及公开暴露的关键设计结论做必要定向独立检查，事实收集不逐项派发 |
| C04 | 独立失败保持阻塞，重审范围仍需读原约定；未定义证据复用判据 | 一名主复核者聚焦原阻塞、修复差异和受影响回归，有效旧证据可复用，共享函数影响必须核对 |

新演练实际读取：SKILL 全文，verification 全文，planning 的探索/同步/状态/漂移/恢复部分，cli 的引言和当前工作集，以及三参考标题索引；未读取初始化/图谱/快照/停滞等无关正文。旧演练读取一个完整 SKILL。新入口 43 行，相比旧 352 行属于结构观察；多文件按需读取不保证工具调用更少。

残余事实需求合理保留：原计划是否明确独立、是否采用用户体验闭环、证据是否覆盖当前树和环境、共享调用影响宽度。规划页已根据演练提醒补明实施中/已完成的适用用户验收含义；不把这些必要核对视为可省开销。

限制：本次是同条件行为选择对照，无两次真实任务总耗时、实际全量测试/复核派发计时或宿主 token 数据；仅确认规则消除直接冲突并给出增量复验条件，不宣称提速比例。实际使用体验留最终用户验收。


### 阶段 1 集成结果

2026-09-06，macOS / Python 3.11.15 / pytest 9.1.1，仓库 Node 入口；被测身份是 `7cd6953` 加下列工作树内容。

| 验证 | 实际结果 |
|---|---|
| 新风险判定 + 旧 checker/hook（`pytest --no-cov`） | 346 passed；其中新风险样本 170，旧样本 176 |
| 真实 Node→Python 风险分流（3 组/15 次 CLI 子进程） | 低风险自验：默认/严格 0，implement；高影响自验：默认 0/严格 1，unknown；旧独立失败后自验：默认 0/严格 1，resolve_blocker；三组 hook 均 0，文件字节不变 |
| initializer 受影响回归 | 32 passed，含旧文档/块外字节与幂等保护 |
| guide 与 manifest 局部检查 | 3 passed；四主题任意 cwd、无需 Python、封闭主题及缺资源失败 |
| `PYTHONDONTWRITEBYTECODE=1 npm run verify` | 退出 0；Python 518 passed、覆盖率 93.42%；Node 101/101、0 skipped，含真实临时打包安装、setup 与旧范围快照迭代 |
| skill quick_validate / `git diff --check` | 通过 |
| 本仓库受管块外与基线字节比较 | AGENTS/CLAUDE 仅去掉被共享规范替代的临时说明，其余块外字节保持 |
| 行为演练 | C01—C04 对照见上；无实际提速或 token 声明 |

完整验证工具记录 `502c31`、`53fd1e`，实际结果和命令已保留于此；不要求未来复核者访问工具 ID。原宿主阶段 2 阻塞、共享目标及背景引用告警仍存在，未据本轮通过解除。未发布、改变版本、安装到用户全局目录或提交。

以下为首轮完整验证（B03/B04 修复前）的指纹；历史保留，修复后当前身份见后面的增量表。相关实现变化另做补验。

| 文件 | SHA-256 |
|---|---|
| `AGENTS.md` | `01dea258d67514742a9ff7b835845256ff1984fcc328b970698c769989839031` |
| `CLAUDE.md` | `0673d90d6bcd484dccd44c15d4ae8b331f10e011e66cb04d2e084bfb7d6430a5` |
| `README.md` | `9d2753f74cd14499f20520f537af49256d03fe6de81e89e7c8fe6e7f1f49ded9` |
| `bin/plan-governance-cli.mjs` | `4f0ac4ce0c91c40c18bf547bc168e35ece392a6d7fd22a734c8f922b98a24ddb` |
| `resources/manifest.json` | `a52d9f467fb4ca144ac55a9487a868dc3e93849cae8074a31015dac4ab78b229` |
| `scripts/check_plan_governance.py` | `8bb70c2cdbc9a604dffb1f5bb0413fc09411ca9dd7296d49cd090228f9d44970` |
| `scripts/init_plan_governance.py` | `4c4dc3931f7ffed8a6c56769e8d72e967634c3e28c973574fa79a6e758cc9054` |
| `scripts/plan_governance_hook.py` | `fe33099f3e5c602e454f913e90feccbff9644de363740da37576fdce822fbcce` |
| `scripts/verify.mjs` | `fbca04629959f57372afb41bc0776ff623d94b566c44e785243e811d374f34ca` |
| `scripts/release_npm.mjs` | `d746fb669f4aa9148ab515e4489db94732932d66403beb3189c1aefc83444f78` |
| `package.json` | `d6d18829d96b010533a4b579d94b77fc9ee26c591c63551898a36d7808f544ad` |
| `package-lock.json` | `e8db48f2d2d2b9596d0a37b3aa1c81d1e6a5edac3f0231847598188f4107bd95` |
| `pyproject.toml` | `900a07f2293986fb802663c78d6f2566159337749421edf3348893a2a35751bc` |
| `tests/test_risk_review.py` | `95b5f7b5c958f003b30112fc058e5a7c748ddc2bca7ab3c1b032bf8b5c5ad801` |
| `tests/test_init_plan_governance.py` | `476ee8ac0dde21150bcb0455a7b606f81e8bea5c560bbb0c970a38436196fe30` |
| `tests/npm_cli.test.mjs` | `d8fea66775ebcc30b0be6c34b20cfc4a711e62ab1d229018966147c60e55cd1e` |
| `resources/skill/SKILL.md` | `7849345a3fc685d4872f7619a700c91106542ac78fb489249236d34014e004f6` |
| `resources/skill/agents/openai.yaml` | `b2bf798703d2004105b9503ff5383a1c97b0b4a34c9250f4344d6070b91a64ac` |
| `resources/skill/assets/PLAN_MAP.template.md` | `cc216e0f6a8147c64ed625360f8f44602022c531acc2f4639fb06a2dcee7325b` |
| `resources/skill/assets/adr.template.md` | `d34ec253a3814c851f657fc19d6efd1c5941ed86028d0c2b364cba2c0fbe7879` |
| `resources/skill/assets/migration.template.md` | `68d947c9d459737a329db45b8f3533d707528153f7fec6429ff5063a0d407616` |
| `resources/skill/assets/plan.template.md` | `fb6dc196bb247cae2870defea7ef8481598381c7a656aa946c44ea09f7538c08` |
| `resources/skill/assets/spec.template.md` | `069c12a70374b135012aec3b50755abe44fdc2380b0eb63e5c3ee4cc7dd4036d` |
| `resources/skill/references/cli.md` | `f7f83d6e87fa9b8e9047a7dd547fde78a1a69d591d376639e45add4bf39fddc6` |
| `resources/skill/references/planning.md` | `d4adf7979ef3b6ec1a60d78baff3f5cd6008d2913fd3ac4f4ad5253a9d1824b2` |
| `resources/skill/references/verification.md` | `79905f27b918c7e1ae211594efb17311c45dece9d1928af73a4e6824086dd535` |

既有 `docs/attestations/*.json` 全部与基线逐字节一致；本次无回填。

Node 实盘补验输入由 `tests/test_risk_review.py` 的 `risk_plan()`、`risk_plan(risk="高影响")`、`with_legacy(risk_plan())` 生成，均置于临时项目。分别执行仓库 `node bin/plan-governance-cli.mjs check <临时项目>` / `workset <临时项目> --json` 的默认与 `--strict-readiness` 入口，以及 `hook --root <临时项目> --event session-start`；期望和实际一致，读前/读后比较项目文件字节，临时目录自动清理。工具记录 `ed3d52`；输入 helper 与源码均已列指纹。这是机械 fixture，不是独立复核通过证明。


### B03/B04 修复增量

B03 来源为独立复核的“通过。”合法旧记录误拒绝；B04 为实施自查的“通过 / 未通过”模板候选误放行。受影响回归 `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest --no-cov -q tests/test_risk_review.py tests/test_check_plan_governance.py tests/test_plan_governance_hooks.py`：397 passed，其中风险新样本 221、原 checker/hook 176。B03 新增 23 个样本，修复前 12 失败；B04 新增 28 个样本，修复前 14 失败。实施者未解除阻塞，等待原独立者确认。

相对首轮 26 文件身份，只变更下列三项；其余 23 项逐一核对一致。新测试不等于独立通过，全部最终结果待下方追加。

| 文件 | SHA-256 |
|---|---|
| `resources/skill/references/verification.md` | `3b6d97abb133d10da5900e779f616ef074257cee34612c6ffa40d36ccad1ff50` |
| `scripts/check_plan_governance.py` | `9bccc55b2414b645ab39462b58b7c6e876fe0ce48d80d54cee957f2f41098b66` |
| `tests/test_risk_review.py` | `af610c56e6da3683fb2defb027b5d1bb8b4940fadc2cf996affebcd264e6b3f1` |


### B04 第二次修复增量

第二轮独立实盘确认 B03 通过，但带问号候选仍可解除旧/新独立失败。实施主代理将候选匹配收敛为“开头未选择候选始终未知”，移除尾部有限标点条件；新增问号、非标点待选说明、引号后缀及旧/新失败恢复反例。受影响集合 413 passed，diff 检查通过；B04 尚待独立确认。

当前变动仍仅首轮 26 项中的同三项，最新身份如下（旧行保留历史）：

| 文件 | SHA-256 |
|---|---|
| `scripts/check_plan_governance.py` | `d1cd90d26f468edd38f54cf27fc4e73deb1cc53e58b439f498d7c195dc43b499` |
| `tests/test_risk_review.py` | `510f3ae6a44dea8c47894ed39f1168987578b17b22f27d330dba87f1ec7f9155` |
| `resources/skill/references/verification.md` | `2717a9daf80d59124397b7d4d0e1faed1450be486554cb9f290c2b2b528080f6` |

### 最终集成验证

2026-09-06，B03/B04 已由[独立技术完成复核](../reviews/plan-governance-workflow-streamlining-completion-review-20260906.md#第三轮通过)确认修复并落档解除。针对两处实际实现修复重新执行 `PYTHONDONTWRITEBYTECODE=1 npm run verify`，退出 0：严格治理通过，Python 585 passed、覆盖率 93.55%（门槛 85%），Node 101/101、0 skipped。包含真实临时打包安装、setup、guide 和旧范围绑定全链路。工具记录 `7c8f1d`、`5eaf56`。

受测内容为以上 26 项的最新指纹（同路径取最后一条），与第三轮独立复核一致；随后仅同步验证文档。历史 518 项/93.42% 是修复前结果，不作为当前覆盖率。宿主阶段 2 及既有共享目标/背景引用告警不因本轮通过解除。本计划技术完成，等待用户验收；未提交、发布、修改版本或同步全局安装。

## 2026-09-07 使用反馈增量验证

本节仅覆盖[U1—U5 已批准调整](../plans/plan-governance-workflow-streamlining.md#实际使用反馈与有界调整2026-09-07)。受测身份为 HEAD `f8c6e3728df4b4dae33b951fe003e487062f7dd9` 加三份共享参考差异；既有文档修改保持。SKILL、manifest、模板、checker、初始化器、Node CLI、package/lock 与 HEAD 逐字节一致。

| 共享参考 | SHA-256 |
|---|---|
| planning.md | `19ccc39f654af72cf21ea0817a2281287cc395d3e42f982501920cb8f418c8af` |
| verification.md | `cdae5b625a5f4fd1697f3eca3e18565a2cd6a0affad50aeb00c687273782bf7e` |
| cli.md | `fb59de83cfeea27fff98e66916d572231bcdc8ef58a1f475ae05ca3c7fef54d1` |

适用机械检查：`node bin/plan-governance-cli.mjs check . --strict-readiness` 退出 0、0 ERROR、13 WARNING；警告归属仍为宿主回放、共享目标和背景引用。新增反馈表曾放在未决问题章节，被解析为阻塞表；移成独立章节后通过，未改检查器或删除真实阻塞。`git diff --check` 和三份参考的本地链接检查通过。三个 `guide <topic>` 均退出 0，stdout 与对应源文件逐字节一致。本次只改规则文本，不重复原全量代码测试，也不把机械检查当行为验收。

同步预检：仓库 `setup --target all --dry-run --force` 仅将更新 Codex/Claude 各三份参考，其他各七项资源已一致。两个安装副本及 npm CLI 1.0.1 内三份参考仍匹配实施前指纹，没有未处理定制差异。实际同步及入口更新须在相关任务不处于实施/复核时执行，再核对资源与非受管内容；此处不预记为已完成。

### 有界行为走读输入

以下为三个输入组，交同一名未参与实施或测试编写的独立者判断下一动作、需要的证据及阻塞边界。它们是规则走读，不是真实项目执行或耗时实验；已有设计上下文，不声称盲测。

1. 未纳入旧计划的有限原型，用户已确认首版仅 iPhone，四份产品文档待同步；范围、后果和查证方式明确，无有效独立失败。随后另一个有旧独立门禁的计划变更退款后的权益撤回规则。分别判断处理方式和复核时点。
2. 网站曾因未来续期缺少安排而独立失败。用户已确认当前交付边界，未来事项的职责、触发条件和证据已落实到后续计划；该后续计划仍在设计。当前公网边界、证书可用和恢复能力已有实际验证，但本次通过结论尚未产生。判断独立结论与落档顺序；若当前恢复仍有缺陷，结论如何变化。
3. workset 返回多个计划，当前计划仅显示末三条证据，较早有一条有效独立失败；还存在直接依赖及不能归属的诊断。当前项目只更新过文档格式，随后更新入口。判断展示、回查和阶段策略；限量或入口更新能否改变有效门禁。

项目同步范围：摩托车仅使用现有 `init --update-agent-rules-only` 更新 AGENTS/CLAUDE 受管块，并核对外部字节不变；ScreenshotStitcher 不建立 PLAN_MAP/全套治理，空闲后仅补最小 AGENTS 发现说明，指向现有产品文档，按需使用已安装 skill，保持原型与真实验收边界。项目状态变化时重新核对，不覆盖其他任务新内容。

### 源规则独立结论与同步交接

[独立完成复核](../reviews/plan-governance-usage-adjustments-review-20260907.md)已通过三份源规则及三个输入组，未发现源规则阻塞；真实安装/入口同步尚未执行。报告写入后的 139 个文档链接及锚点检查、空白检查通过。源复核结束后两个项目任务仍活跃，保留空闲交接条件，不将预检计作部署完成。

同步预检的未受管文件没有被修改。按相对路径排序的 SHA-256 字典经 `json.dumps(..., sort_keys=True)` 后再次计算 SHA-256：Codex 3 项为 `e552c3a99bb7ca7d720745f22be9a0cb7a4b274383d89f4ae53520058b6bd805`，Claude 2 项为 `784cccdd432210c2e52d0dbceccf2ce46ac385732a78e1b7ea07336d8c7fe913`。实际同步前重新核对文件集合，同步后比较逐文件字节；不得仅凭历史摘要推定当前安全。

摩托车入口只读预演采用现有初始化器生成内容：各有一个受管块，替换后两份文件的块外字节分别完全保持，docs 未写入；这不是实际项目升级结果。后续执行命令和防止过期覆盖的边界见[计划中的同步交接](../plans/plan-governance-workflow-streamlining.md#本次实施结果)。不另派同范围记录复核，不把真实功能/性能验收或整体用户接受预记为完成。

### 本机及项目入口同步完成

2026-09-07 用户明确“没事，同步吧”，授权立即执行，无须继续等待任务空闲。以上“尚未执行”保留为源复核和预检时的历史状态；本节是实际同步结果。受审三份参考指纹未变，沿用既有独立结论；本轮仅同步与文档自查。

- 仓库 `node bin/plan-governance-cli.mjs setup --target all --dry-run --force` 重新确认各三份参考是唯一差异，均仍匹配原安装基线；随后执行 `setup --target all --force`，退出 0。Codex/Claude 各 10 项 manifest 资源与受审仓库逐字节一致；Codex 3 项、Claude 2 项非受管文件集合和逐文件摘要保持。第二次 `setup --target all --dry-run` 退出 0，全部已是最新。
- 摩托车执行 `node bin/plan-governance-cli.mjs init --root /Users/jafish/Documents/work/motorcycle-manual-app --update-agent-rules-only`，退出 0。AGENTS/CLAUDE 分别从 9,396/8,585 字节变为 4,749/3,938 字节，块外逐字节保持；同步窗口内核对 PLAN_MAP 与 51 份计划，共 52 文件无变化。普通 `check` 前后均退出 0、0 ERROR、28 WARNING，stdout/stderr 完全一致，旧阶段策略和有效阻塞保持。
- ScreenshotStitcher 原无 AGENTS，本轮以独占创建方式新增 22 行最小入口；六个本地文档链接和空白/末尾换行检查通过。没有新建 CLAUDE、PLAN_MAP 或治理目录，没有修改产品文档、代码或运行构建。该实施由 `/root/skill_instruction_audit` 完成，不记为额外独立复核。
- 本机 npm CLI 的 package.json 和包内 skill 资源保持；CLI 仍为 1.0.1，其 `guide` 未包含这次未发布的开发规则。后续治理优先读取已同步的安装 skill，不把同版本号的 npm guide 与开发参考混读。本轮未改版本、发布、提交或推送 Git。

| 项目入口 | 同步后 SHA-256 |
|---|---|
| motorcycle-manual-app/AGENTS.md | `312ea3d51f8b80a6516002f7a612b11fcf98e0d24277966a8aa93729cccf1a57` |
| motorcycle-manual-app/CLAUDE.md | `f377ff99bfcd3d7cd6b8a44c758e78ebb054ee39920f0ca8c964f2ada4977f15` |
| ScreenshotStitcher/AGENTS.md | `e7df995fc817eec4933424b341330942ac0b4fdccd01fe63f0e0f29d9193315d` |

六份旧参考及摩托车两个旧入口的回滚副本位于 `/var/folders/t0/t1h7z_pd6716d4kstbbmxxyc0000gn/T/plan-governance-sync-20260907-z8ftbmvc`，同目录 `sync-result.json` 记录本轮命令结果摘要。持久证据为本节的实际命令、结果与指纹；同步完成不证明正在运行的任务已重新读取规则，也不代替后续实际减负体验验收。

同步落档检查：149 个本地链接/锚点通过；本仓库 `check . --strict-readiness` 退出 0、0 ERROR、13 个既有 WARNING；`git diff --check` 通过。再次核对两套安装资源及三个项目入口仍匹配同步指纹，原有分发维护文档的未提交内容保持。此次同步待办已完成，整体计划继续等待实际使用验收。

后续发布：用户随后授权发版，1.0.2 已通过统一验证并完成官方版本、dist-tag 和包校验值核对，见[发布维护](../plans/plan-governance-distribution-setup.md#2026-09-07-102-发布维护)。以上“未发布”说明保留为同步轮结束时的状态；本机全局 CLI 仍为 1.0.1。
