# 持续迭代治理优化：阶段 0 命令入口基线

所属计划：[iterative-governance-reliability](../plans/iterative-governance-reliability.md#阶段-0-技术收敛)。本文只承载输入、命令、当前观察和复现边界；目标行为由专项计划定义，不在本文件复制新的规范。

## 基线身份与限制

- 日期：2026-09-06。
- Git HEAD：`336b728d7dacc335a35f2cf97ab39356e3a82ba0`，另有未提交工作树；以下内容 hash 才是本次相关源文件身份。
- 基线类型：Python CLI 参数解析和 `main` 的虚拟文件系统回放。只替换 `Path.exists/read_text/glob` 的存储读取，使用当前真实校验逻辑，不写文件、不安装依赖、不运行完整测试。
- 不覆盖：Node→Python 的真实进程/临时目录全链路、Git drift 实盘样本、完整 pytest/npm 回归、宿主调度或业务验收。真实 Node 入口在本仓库的查询命令另由专项计划记录。

| 文件 | SHA-256 |
|---|---|
| `scripts/check_plan_governance.py` | `b17bbaf97ebb1c5de3fff9d4b8d2a35d442e2a2e739cfd1453a2081d83f7ea4e` |
| `scripts/plan_governance_hook.py` | `08e4af00d5fc01ecc6fa6fb9794daeb095344a6164f47a04abf6e31cbbec26a7` |
| `bin/plan-governance-cli.mjs` | `d71a5c9a556b7349187a36902664eece3495fa85ddfcfb2ca4a8488a5feea029` |
| `tests/test_check_plan_governance.py` | `52985957dd0364000cfb1d14738c98226ca7b117794ed48318bb2408ec7ca4f7` |
| `tests/test_plan_governance_hooks.py` | `46e9e6900d4f76708dcaf3ac84e7db685695253d0171405b414edd2853618cb8` |
| `tests/npm_cli.test.mjs` | `8a922588e9224018ba7c42d57531ad97dcd2b65dc5f39c9459b856809ac2efa5` |

## 可执行命令

从仓库根目录运行以下代码块。每个样本执行普通 check、严格 check 和严格 workset，打印 JSON 摘要；退出码和业务输出都由当前入口实际产生。

```bash
python3 -B - <<'PY'
from contextlib import ExitStack, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch
import json, re, runpy
ns = runpy.run_path('tests/test_check_plan_governance.py')
m = ns['check_plan_governance']
root = Path('/__plan_governance_stage0_memory__')
valid = ns['readiness_plan_text']()
row = '| [demo](plans/demo.md) | 待实施 | 阶段 1 | 2026-09-06 | - | evidence |'
index = ns['plan_map'](row)
fields = ['Step 0','样本矩阵','验证方式','失败/回滚边界','最新独立准入复核','日期','阶段','结论','证据','复核者']
empty = re.sub(r'(?m)^\| ('+'|'.join(map(re.escape,fields))+r') \|.*\|$',r'| \1 | |',valid)
summary_blocker = valid.replace('| 当前阻塞项 | 无 |','| 当前阻塞项 | 外部授权待确认 |')
map_blocker = index + '\n## 当前阻塞项\n\n| 问题 | 推荐方案 | 影响范围 | 是否阻塞当前阶段 | 状态 |\n|---|---|---|---|---|\n| 外部授权待确认 | 先确认 | demo | 是 | 待处理 |\n'
failed = valid.replace('| 结论 | 通过 |','| 结论 | 未通过 |').replace('| 阶段准入复核 | 阶段 1 | 通过 |','| 阶段准入复核 | 阶段 1 | 未通过 |')
recent = '\n### 最近实施/验证记录\n\n| 日期 | 类型 | 动作/结果 | 证据 | 状态 | 记录者 |\n|---|---|---|---|---|---|\n| 2026-09-06 | 验证 | 部分失败 | report.md | 失败 | tester |\n'
with_recent = valid.replace('### 最新独立准入复核',recent+'\n### 最新独立准入复核')
cases = [
 ('valid',index,valid),('empty_fields',index,empty),('summary_only',index,summary_blocker),('map_only',map_blocker,valid),
 ('open_table',index,ns['readiness_plan_text'](unresolved_blocker=True)),
 ('unknown_state',index,ns['readiness_plan_text'](unresolved_blocker=True).replace('| 是 | 未解决 |','| 是 | Pending |')),
 ('duplicate',ns['plan_map'](row+'\n'+row.replace('待实施','设计中')),valid),
 ('failed_review',index,failed),('current_recent',index,with_recent),
 ('numbered_recent',index,with_recent.replace('### 最近实施/验证记录','### 阶段 1 最近验证记录')),
 ('legacy_design',ns['plan_map'](row.replace('待实施','设计中')),ns['plan_text'](status='设计中')),
]
for name,map_text,plan_text in cases:
    files={root/'docs/PLAN_MAP.md':map_text,root/'docs/plans/demo.md':plan_text}
    dirs={root,root/'docs',root/'docs/plans'}
    outputs={}
    with ExitStack() as stack:
        stack.enter_context(patch.object(Path,'exists',lambda p:p in files or p in dirs))
        stack.enter_context(patch.object(Path,'read_text',lambda p,*a,**k:files[p]))
        stack.enter_context(patch.object(Path,'glob',lambda p,pattern:iter([root/'docs/plans/demo.md'] if p==root/'docs/plans' else [])))
        for label,args in [('check',[]),('strict',['--strict-readiness']),('workset',['--workset','--json','--strict-readiness'])]:
            out=StringIO()
            with redirect_stdout(out):
                code=m.main([str(root),*args])
            value=out.getvalue()
            if label=='workset':
                data=json.loads(value)
                items=data['plans']
                outputs[label]={'exit':code,'plans':len(items),'readiness':items[0]['readiness'] if items else None,'next':items[0]['next_action']['kind'] if items else None,'blockers':len(items[0]['blockers']) if items else None,'recent':len(items[0]['recent_evidence']) if items else None,'warnings':len(data['warnings'])}
            else:
                outputs[label]={'exit':code,'warnings':value.count('WARNING:'),'errors':value.count('ERROR:')}
    print(json.dumps({'case':name,**outputs},ensure_ascii=False))
PY
```

## 2026-09-06 实际结果

所有行均来自上述命令实际输出。`workset` 一列为严格模式；“回放成功”只表示稳定观察到现行行为，错误放行仍是待修复缺陷。

| 样本 | 输入差异 | 普通 check 退出码 | 严格 check 退出码 | 严格 workset 退出码 | workset 当前结果 |
|---|---|---|---|---|---|
| valid | 原有合法样本 | 0 | 0 | 0 | ready / implement |
| empty_fields | 保留必填字段名，清空准入与复核值 | 0 | 0 | 0 | ready / implement；无诊断 |
| summary_only | 只在摘要声明外部授权待确认 | 0 | 0 | 0 | ready / implement；阻塞 0 |
| map_only | 只在地图声明 demo 的开放阻塞 | 0 | 0 | 0 | ready / implement；阻塞 0 |
| open_table | 专项计划未决问题为开放阻塞 | 1 | 1 | 0 | blocked / resolve_blocker；阻塞 1 |
| unknown_state | 将开放状态文字改为 Pending | 0 | 0 | 0 | blocked / resolve_blocker；阻塞 1 |
| duplicate | 同一计划登记两次，后一行设计中 | 0 | 0 | 1 | plans 为空，诊断 1 |
| failed_review | 当前复核和历史最后一条均未通过 | 0（告警 1） | 1 | 0 | ready / implement；无诊断 |
| current_recent | 当前固定标题下一条验证记录 | 0 | 0 | 0 | recent_evidence 长度 1 |
| numbered_recent | 当前记录标题改为阶段编号变体 | 0 | 0 | 0 | recent_evidence 长度 0 |
| legacy_design | 未启用准入结构的旧设计计划 | 0 | 0 | 0 | design / complete_step0 |

## 验证与失败判定

- 输出位置：命令标准输出与本文件实际结果表；不生成仓库外日志或覆盖旧证据。
- 执行失败、缺少任一样本、输出与表格不同，均要求重新核对源文件 hash 和基线，不得假定仍复现。
- 修复后的输出理应改变；届时保留本次历史观察，在阶段 1 验证记录中追加新结果，不把旧表改写成“原来就正确”。
- 此基线只证明这些输入下的现行行为。未知状态、跨来源冲突、已解决记录、多个阶段以及真实文件系统均须进一步扩大样本，不能用十一项回放替代全部完成条件。
