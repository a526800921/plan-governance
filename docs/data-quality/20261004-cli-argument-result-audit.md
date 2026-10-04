# CLI 入参与返回值核查（2026-10-04）

## 范围与证据边界

基线为仓库 `1f85f45`、`package.json` 版本 `2.0.2`，接手工作树干净。覆盖 npm CLI 的全部公开入口及其直接调用边界：`check`、`workset`、`guide`、`setup`、`init`、四类 hook、图谱校验/影响分析、代码候选/影响查询、`plan impact`；附带检查发布脚本的参数与退出码。不宣称遍历全部私有解析函数，也不重新评价治理规则的全部业务正确性。

采用源码核查和只读进程回放。命令入口为 `node bin/plan-governance-cli.mjs`；Python 设置 `PYTHONDONTWRITEBYTECODE=1`。`setup` 全部使用 `--dry-run`；`init` 只调用 `parse_args()`，未调用 `main()`。没有安装、初始化、生成构建产物、资金请求、GitNexus 索引刷新或发布操作。

拟议契约唯一来源为[功能设计](../plans/20261004/cli-check-and-interface-contracts.md#拟议功能契约)。本文件记录现状，不把拟议行为写成已经实现。

## 动态回放结果

下表参数都接在上述 CLI 入口之后。不存在目录固定使用 `/nonexistent/plan-governance-audit`。

| 编号 | 输入 | 实际退出码及输出 | 判断 |
|---|---|---|---|
| A01 | `chekc` | 0；提示未找到地图、未初始化 | 未知命令被当作 root，拼写错误可被误判成功 |
| A02 | `check /nonexistent/plan-governance-audit` | 0；提示未初始化 | root 不存在与合法未初始化目录混淆 |
| A03 | `check --root /nonexistent/plan-governance-audit` | 0；实际检查当前仓库并输出其告警 | 参数被接受但忽略，检查目标错误 |
| A04 | `check --json` | 0；stdout 是 WARNING 与通过提示文本 | 参数被接受但未提供 JSON |
| A05 | `workset --json --drift` | 0；正常 schema 1 JSON，无 drift 检查 | 不属于该命令的参数被静默忽略 |
| A06 | `setup --target codex --dry-run --destination` | 0；预览默认已安装 skill 目录 | 漏值被当作未指定目的地 |
| A07 | `setup --target codex --dry-run --destination ''` | 0；预览默认已安装 skill 目录 | 显式空值被当作未指定目的地 |
| A08 | `setup --target codex --dry-run --destination --force` | 0；预览当前仓库下 `--force/` | 后续开关被吞为目的地 |
| A09 | `graph validate --bogus` | 1；报 `--bogus/docs/graph/functional.yaml` 缺失 | 未知选项被当作 root，错误分类不准确 |
| A10 | `graph impact --from feature.none /nonexistent/first /nonexistent/last` | 1；只报最后目录缺图谱 | 多个 root 静默取最后一个 |
| A11 | `graph code candidates --symbol functionalNodeId --kind function --format text --format json` | 0；输出 JSON | 单值选项重复时最后一个覆盖，缺少明确契约 |
| A12 | `graph code candidates --file nonexistent-audit.mjs --symbol functionalNodeId --kind function --format json` | 0；`unique_candidate`，候选为 `scripts/graph_governance.mjs:720` | 指定文件不存在时扩大搜索，与请求范围不一致 |
| A13 | `guide bogus` | 1；stderr 明确报告主题非法 | 错误诊断正确，参数退出码与 Python 入口不统一 |
| A14 | `check --bogus` | 2；argparse stderr 报未知参数 | 参数错误的 Python 分支行为合理 |
| A15 | `workset /nonexistent/plan-governance-audit --json` | 1；schema 1 JSON，错误在 `warnings` | 与 check 的未初始化行为不一致；退出码需结合命令契约解释 |
| A16 | `init` 解析 `--plan audit --status 已完成` | 接受；没有执行初始化 | 生成器允许终态，但新模板没有完成证据 |
| A17 | `init` 解析 `--plan audit --phase banana` | 接受；没有执行初始化 | 允许生成 checker 不接受的阶段值 |
| A18 | `init` 解析 `--update-agents-md-only --plan audit` | 接受；没有执行初始化 | 更新模式会忽略正常初始化的计划参数 |

## 源码核查结果

| 入口/边界 | 已有合理行为 | 问题与优先级 | 源码入口 |
|---|---|---|---|
| 顶层 CLI | Python/Node 子进程退出码透传；缺 runtime、启动失败与信号终止非零 | P1：A01/A02；P2：顶层帮助只展示 checker，无法枚举全部命令；Node 参数错误通常 1，Python 通常 2 | [启动器](../../bin/plan-governance-cli.mjs) |
| `check` | 结构错误失败；新增准入缺陷默认警告、严格模式失败；保留真实阻塞 | P1：当前未决问题的部分开放状态无条件硬失败，地图/摘要来源却按模式分级；同一事实随存放位置改变退出码。P1：A03/A04；P2：`--include-history` 等 workset 参数可能被忽略。`--attest` 会写快照，不能笼统称整个 check 命令只读 | [检查器](../../scripts/check_plan_governance.py) |
| `workset` | schema 1；阻塞派生为 `blocked/resolve_blocker`，歧义不输出 ready；限量窗口不裁剪门禁 | P1：A05；多会话补查：没有 plan 参数，输出全部活跃计划与全局 warnings，无法提供会话聚焦信息。P2：重复 ID 时可返回空 plans、warnings 和 0；只能说明查询完成，不表示没有问题。缺失文件在不同读取路径的退出码需要统一 | [工作集](../../scripts/check_plan_governance.py) |
| `guide` | 封闭主题、同包资源、缺失/空资源失败；stdout 为 Markdown | P2：A13；`-h` 未与其他命令统一 | [规则读取](../../bin/plan-governance-cli.mjs) |
| `setup` | 仅 codex；目标重复保护；差异默认拒绝覆盖；全部文件预检后写入；dry-run 只读 | P1：A06–A08。P2：destination 重复未拒绝。静态核查发现跨文件写入不是事务；中途失败需报告已完成文件，不能承诺全部成功 | [setup](../../bin/plan-governance-cli.mjs) |
| `init`/升级/迁移 | 默认设计中、日期目录；部分模式互斥；受管块外保留 | P1：A16/A17；P2：A18 与不适用参数组合；初始化按顺序写入，可能先初始化 Git/写地图再遇到冲突，需扩大变更前预检。公开异常范围未覆盖全部 I/O/子进程错误 | [初始化器](../../scripts/init_plan_governance.py) |
| hook | 四事件枚举明确；正常提示非阻塞 0 | P1：stop 调用目标项目 `scripts/check_plan_governance.py`，而其他事件加载包内 checker；无本地脚本时直接跳过，与统一入口文档不符。多会话补查：session-start 展示全部活跃计划，pre-write 虽过滤计划记录但 `print_gate_hints()` 仍输出整个 payload.warnings；没有会话焦点入参。P2：`--paths` 不按事件约束，root/path 规范化不足；stdout/stderr 只择一显示 | [hook runtime](../../scripts/plan_governance_hook.py) |
| `graph validate` | 两层枚举、图谱结构错误非零；GitNexus 不可用明确提示 fallback | P2：A09、单值参数重复；root 只允许一个但未知选项可混入；缺外部 UID 验证不等于 UID 已验证 | [图谱入口](../../scripts/graph_governance.mjs) |
| `graph impact` | depth 1–10、format 枚举；未知节点失败 | P2：A10；未知选项与单值漏值/重复不统一；应拒绝多 root | [图谱影响](../../scripts/graph_governance.mjs) |
| `graph code candidates` | 无候选/多候选返回 0 和明确 resolution，适合查询语义 | P1：A12；P2：A11。kind 校验在搜索阶段才执行，空代码目录可能绕过；指定 file 的范围与路径类型应先校验 | [候选查询](../../scripts/graph_governance.mjs) |
| `graph code impact` | GitNexus 失败、非 JSON 和 error 结果失败；查询参数保留在响应 | P2：`kind` 缺公开枚举契约；只检查响应可解析且无 error，未区分空值、错误顶层类型与正常空影响结果。本机 `gitnexus impact --help` 明示 Function/Class/Method 示例，未实测真实服务 | [代码影响](../../scripts/graph_governance.mjs) |
| `plan impact` | 输入对象及关键枚举/布尔值检查；分层查询和测试映射状态明确；定位不唯一时失败 | P1：继承候选搜索越过指定文件的问题。P2：code_anchor 白空值、kind/file 类型边界与候选查询不一致；输入路径解析为 YAML/JSON 而帮助仅写 JSON；参数漏值/未知/重复问题共用图谱解析 | [计划影响](../../scripts/graph_governance.mjs) |
| `check --attest*` | 显式绑定、用途与替代关系、hash 漂移、严格门禁已有契约 | P1（源码确认，未执行写入）：`create_attestation()` 仅在传 attest_files 时先拒绝已有 errors，无绑定分支可能在最终返回 1 前仍写快照。P2：变更与只读检查共用入口，需要明确模式互斥、输出产物和副作用；不得用普通查询的 0 代替快照创建成功证据 | [快照契约](../plans/20260906/iterative-governance-reliability.md#阶段-4-行为契约) |
| `release:npm` | 参数错 2、流程/恢复失败 1、成功 0；dry-run 不验证/切源/改版本；切源尝试后总尝试恢复 | P2：SemVer 正则允许部分非法版本（如主版本前导零、空 prerelease 标识）；重复 dry-run 需明确；已存在版本不能重复发布的仓库规则尚需流程内明确预检。这里只读核查，未实际发布 | [发布脚本](../../scripts/release_npm.mjs) |

P1 表示可能检查错误范围、误报成功或误导后续动作，应先修；P2 表示接口一致性、错误表达或预检改进，不代表已经发生外部损害。

## 结论

核心查询模型可保留，但入参和成功语义并非全部合适。应先修检查范围、参数静默忽略、安装目标漏值、代码搜索范围与 hook checker 来源，再统一命令语法和退出码。查询成功、检查通过、准入通过、写入成功须分别说明。现有行为有些来自明确兼容契约，应通过新版本与文档同步调整，不能把全部差异当作回归缺陷。


## 实施核对（2026-10-04）

用户后续明确授权实施，以上 A01–A18 保留为实施前基线。仓库已完成 check 目的分层和结构化 JSON、check/workset/hook 会话焦点、参数校验与 0/1/2 返回值、指定代码文件边界、同包 stop、初始化目标预检、失败检查不写任何快照，以及发布 SemVer/已存在版本预检；规则入口同步。

实际验证：`npm run verify` 退出 0，756 项 Python、总覆盖率 89.32%，136 项 Node 均通过。新增 [会话范围回归](../../tests/test_scope_contracts.py) 覆盖双会话并发查询、必要历史阶段、无关局部错误、共享范围、事实版本与参数不变更；[发布回归](../../tests/verification_release.test.mjs) 全部隔离执行。P06/P07 的宿主桥接/文件协调仅核对规范能力边界，没有实际安装 hook、自动绑定聊天、增加文件锁或执行 npm 发布。当前事实和后续发布边界见 [实现计划](../plans/20261004/cli-check-and-interface-contracts.md#实现与验收结果)。
