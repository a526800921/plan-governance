# 持续迭代治理优化：阶段 1 真实 CLI 基线

所属计划：[iterative-governance-reliability](../plans/iterative-governance-reliability.md#阶段-1-完成证据)。本文件承载真实文件输入、命令、当前输出和安全边界；目标行为以专项计划技术契约为准。

## 范围和安全边界

- 日期：2026-09-06；基线实现保持阶段 0 fixture 所记录的六份源码/测试 hash。
- 复用 [阶段 0 输入](iterative-governance-reliability-stage0-cases.md) 的十一类 Markdown 样本，扩充至二十二类。
- 仅在 `TemporaryDirectory(prefix='plan-governance-stage1-')` 创建本次拥有的文件；退出时自动清理，不写当前项目代码、Git、安装目录或外部项目。
- 使用真实 Node 启动器和 Python 子进程，分别调用普通/严格 check 与普通/严格 workset；继承环境但不输出环境变量，禁止 Python 字节码缓存。
- 每个样本前后核对输入文件 hash，命令设 20 秒超时；此处不调用 init、setup、attest、release、Git hooks、网络服务或完整测试套件。

## 可执行命令

从仓库根目录执行。阶段 0 文档只提取输入构造部分，不执行其虚拟文件系统回放；本文件没有 mock 文件系统或业务校验逻辑。

```bash
python3 -B - <<'PY'
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib, json, os, re, subprocess
repo = Path.cwd()
document = (repo/'docs/fixtures/iterative-governance-reliability-stage0-cases.md').read_text()
block = re.search(r'```bash\n(.*?)\n```', document, re.S).group(1)
script = block.split('\n', 1)[1].rsplit('\nPY', 1)[0]
context = {}
exec(script.split('for name,map_text,plan_text in cases:')[0], context)
cases = list(context['cases'])
valid, index, row, ns = (context[key] for key in ['valid', 'index', 'row', 'ns'])
resolved = valid.replace('| - | - | 否 | 已延后 |', '| 已处理问题 | 已补齐 | 是 | 已解决 |')
cases += [
 ('resolved_table', index, resolved),
 ('resolved_map', context['map_blocker'].replace('| demo | 是 | 待处理 |', '| demo | 是 | 已解决 |'), valid),
 ('duplicate_field', index, valid.replace('| 结论 | 通过 |', '| 结论 | 未通过 |\n| 结论 | 通过 |')),
 ('wrong_review_phase', index, ns['readiness_plan_text'](review_phase='阶段 2')),
 ('history_conflict', index, ns['readiness_plan_text'](history_conclusion='未通过')),
 ('design_unreviewed', ns['plan_map'](row.replace('待实施','设计中')), ns['workset_plan_text']()),
 ('design_failed_review', ns['plan_map'](row.replace('待实施','设计中')), ns['readiness_plan_text'](status='设计中').replace('| 结论 | 通过 |','| 结论 | 未通过 |').replace('| 阶段准入复核 | 阶段 1 | 通过 |','| 阶段准入复核 | 阶段 1 | 未通过 |')),
 ('historical_recent', index, valid.replace('## 当前阶段', '## 历史阶段\n'+context['recent']+'\n## 当前阶段')),
 ('both_sources', context['map_blocker'], context['summary_blocker']),
 ('no_map', None, None),
 ('missing_plan', index, None),
]
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
cli = str(repo/'bin/plan-governance-cli.mjs')
def hashes(directory):
    return {str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.rglob('*') if p.is_file()}
with TemporaryDirectory(prefix='plan-governance-stage1-') as temp:
    for name,map_text,plan_text in cases:
        root = Path(temp)/name
        root.mkdir()
        for rel,content in [('docs/PLAN_MAP.md', map_text), ('docs/plans/demo.md', plan_text)]:
            if content is None: continue
            target = root/rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        before = hashes(root)
        result = {'case': name}
        for label,command,extra in [('check','check',[]),('strict','check',['--strict-readiness']),('workset','workset',['--json']),('workset_strict','workset',['--json','--strict-readiness'])]:
            completed = subprocess.run(['node',cli,command,str(root),*extra],cwd=repo,env=env,text=True,capture_output=True,timeout=20)
            output = {'exit': completed.returncode}
            if command == 'workset':
                payload = json.loads(completed.stdout)
                items = payload['plans']
                output.update({'plans':len(items),'readiness':items[0]['readiness'] if items else None,'next':items[0]['next_action']['kind'] if items else None,'blockers':len(items[0]['blockers']) if items else None,'recent':len(items[0]['recent_evidence']) if items else None,'warnings':len(payload['warnings'])})
            else:
                output.update({'warnings':completed.stdout.count('WARNING:'),'errors':completed.stdout.count('ERROR:')})
            assert not completed.stderr, (name, label, completed.stderr)
            result[label] = output
            assert hashes(root) == before, (name,label,'input files changed')
        print(json.dumps(result,ensure_ascii=False))
print(json.dumps({'samples':len(cases),'input_hashes_unchanged':True,'temporary_directory_removed':not Path(temp).exists()}))
PY
```

## 实际结果

2026-09-06 已实际执行：22 类样本、88 次真实 Node→Python 调用，全部完成。每次输入 hash 均未改变，专用临时目录已清理，没有 stderr。下表为修复前观察，不能作为修复通过证据。退出码按普通/严格顺序；最后一列为阻塞条数/最近记录条数。

| 样本 | check 退出码 | workset 退出码 | 工作集状态/下一动作 | 阻塞/记录 |
|---|---|---|---|---|
| valid | 0/0 | 0/0 | ready/implement | 0/0 |
| empty_fields | 0/0 | 0/0 | ready/implement | 0/0 |
| summary_only | 0/0 | 0/0 | ready/implement | 0/0 |
| map_only | 0/0 | 0/0 | ready/implement | 0/0 |
| open_table | 1/1 | 0/0 | blocked/resolve_blocker | 1/0 |
| unknown_state | 0/0 | 0/0 | blocked/resolve_blocker | 1/0 |
| duplicate | 0/0 | 0/1 | 无条目/无动作 | —/— |
| failed_review | 0/1 | 0/0 | ready/implement | 0/0 |
| current_recent | 0/0 | 0/0 | ready/implement | 0/1 |
| numbered_recent | 0/0 | 0/0 | ready/implement | 0/0 |
| legacy_design | 0/0 | 0/0 | design/complete_step0 | 0/0 |
| resolved_table | 0/0 | 0/0 | blocked/resolve_blocker | 1/0 |
| resolved_map | 0/0 | 0/0 | ready/implement | 0/0 |
| duplicate_field | 0/0 | 0/0 | ready/implement | 0/0 |
| wrong_review_phase | 0/1 | 0/0 | ready/implement | 0/0 |
| history_conflict | 0/1 | 0/0 | ready/implement | 0/0 |
| design_unreviewed | 0/0 | 0/0 | design/independent_review | 0/0 |
| design_failed_review | 0/0 | 0/0 | design/independent_review | 0/0 |
| historical_recent | 0/0 | 0/0 | ready/implement | 0/0 |
| both_sources | 0/0 | 0/0 | ready/implement | 0/0 |
| no_map | 0/0 | 1/1 | 无条目/无动作 | —/— |
| missing_plan | 1/1 | 0/1 | 无条目/无动作 | —/— |

新增实盘发现：`已解决` 仍被工作集算作阻塞；重复结论字段被最后一个值覆盖；设计阶段失败复核被当成尚未复核；索引重复、复核阶段错位及复核历史冲突在严格 check 与工作集之间不一致。

## 修复后回归结果

2026-09-06 对修复实现重放相同 22 类输入、88 次 CLI 调用，结果符合计划矩阵；输入 hash 不变、临时目录清理、stderr 为空。通过 AST 提取对比确认 `plan_map`、`readiness_plan_text`、`workset_plan_text`、`plan_text` 四个输入 helper 与修复前 HEAD 的源码完全一致；修改只新增测试和补齐特定旧测试调用的合法输入，没有重定义基线 helper。

| 样本 | check 退出码 | workset 退出码 | 工作集状态/下一动作 | 阻塞/记录 |
|---|---|---|---|---|
| valid | 0/0 | 0/0 | ready/implement | 0/0 |
| empty_fields | 0/1 | 0/1 | unknown/unknown | 0/0 |
| summary_only | 0/1 | 0/1 | blocked/resolve_blocker | 1/0 |
| map_only | 0/1 | 0/1 | blocked/resolve_blocker | 1/0 |
| open_table | 1/1 | 0/1 | blocked/resolve_blocker | 2/0 |
| unknown_state | 0/1 | 0/1 | blocked/resolve_blocker | 2/0 |
| duplicate | 0/1 | 0/1 | 无条目/无动作 | —/— |
| failed_review | 0/1 | 0/1 | blocked/resolve_blocker | 1/0 |
| current_recent | 0/0 | 0/0 | ready/implement | 0/1 |
| numbered_recent | 0/0 | 0/0 | ready/implement | 0/1 |
| legacy_design | 0/0 | 0/0 | design/complete_step0 | 0/0 |
| resolved_table | 0/0 | 0/0 | ready/implement | 0/0 |
| resolved_map | 0/0 | 0/0 | ready/implement | 0/0 |
| duplicate_field | 0/1 | 0/1 | unknown/unknown | 0/0 |
| wrong_review_phase | 0/1 | 0/1 | unknown/unknown | 0/0 |
| history_conflict | 0/1 | 0/1 | unknown/unknown | 0/0 |
| design_unreviewed | 0/0 | 0/0 | design/independent_review | 0/0 |
| design_failed_review | 0/0 | 0/0 | blocked/resolve_blocker | 1/0 |
| historical_recent | 0/0 | 0/0 | ready/implement | 0/0 |
| both_sources | 0/1 | 0/1 | blocked/resolve_blocker | 1/0 |
| no_map | 0/0 | 1/1 | 无条目/无动作 | —/— |
| missing_plan | 1/1 | 0/1 | 无条目/无动作 | —/— |

修复后普通模式保留既有开放问题/缺文件硬错误，新诊断为 WARNING；严格模式阻断目标准入缺陷。设计失败复核显示原因且仍保留设计阶段的成功退出码，编号记录标题只告警。输入/命令不覆盖历史观察表；完整回归和独立验收结论在专项计划记录。

## D01 补充回归

第一轮完成复核额外发现 fenced prose 的下一动作误读，见 [失败报告](../reviews/iterative-governance-reliability-stage1-completion-review-20260906.md#阻塞-d01)。三反引号/四波浪线分别覆盖仅示例与示例后真实验证动作四类输入，预期依次为 unknown/verify；普通与严格 check/workset 及 hook 均保持 0，hook 不显示 implement，输入不变且临时目录清理。

固定回归位于 `tests/test_check_plan_governance.py::test_next_action_ignores_fenced_prose_examples` 与 `tests/npm_cli.test.mjs` 的 `workset and hook ignore fenced next-action examples`，不重定义原 22 类基线输入。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider tests/test_check_plan_governance.py -k next_action_ignores_fenced --no-cov
PYTHONDONTWRITEBYTECODE=1 node --test --test-name-pattern='fenced next-action' tests/npm_cli.test.mjs
```

2026-09-06 实际结果：修复前 Python 四类全部失败，修复后全部通过；完整 npm 41/41 包含四输入共 20 次真实 CLI/hook 回放。当前完整 Python 为 203 passed、覆盖率 93.22%。随后独立完成重审通过，D01 解除；原失败报告继续保留，见第二轮完成复核。

## 失败判定与输出位置

- 输出位置：命令标准输出与本文件追加的实际结果。每行保留样本 ID、真实退出码、诊断数量和工作集摘要。
- 运行异常、超时、stderr、JSON 不可解析、输入 hash 改变或临时目录未清理，均不能形成通过基线。
- 这里记录的是修复前行为；错误放行、未识别阻塞和合法对照需分别记录。修复后的回归结果另行追加，不能覆盖本次基线。
- 本命令覆盖真实 Node→Python 和真实文件读取，但不代替 pytest/npm 全量回归、Git 实盘 drift、发布失败注入或独立准入。
