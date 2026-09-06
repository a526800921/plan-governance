# 持续迭代治理优化：阶段 1 独立完成复核

## 第一轮：未通过

- 日期：2026-09-06；计划：[iterative-governance-reliability](../plans/iterative-governance-reliability.md)，阶段 1。
- 复核者：`/root/iterative_stage1_acceptance`，新上下文独立只读，未参与实施、未修改工作区。
- Revision：`336b728d7dacc335a35f2cf97ab39356e3a82ba0` 加派发时混合工作树。
- 范围：计划、阶段 1 fixture、地图相关行、checker/hook 和三个对应测试文件。
- 结论：**阶段 1 完成验收未通过**，1 项当前阻塞；阶段 2 仍设计中。

### 受审身份

| 文件 | SHA-256 |
|---|---|
| 专项计划 | `66ab59d40018d6166a193599828a9e73e471bdbb0a9e0727b48bb5d188eb6cf3` |
| 阶段 1 fixture | `0c454ac29563ec7ceb33661f7c937e74a09ebfc4e1b0994b81b0bae6528144b2` |
| PLAN_MAP | `5b51f816f7d9965f3d3c0ff75047a4f17675d99619172d9f646340c708fa5e68` |
| scripts/check_plan_governance.py | `6b9199e6a5e856dafdf60368ca5b74643ff3cee34154a946f1dd089ffa4e73d6` |
| scripts/plan_governance_hook.py | `fe33099f3e5c602e454f913e90feccbff9644de363740da37576fdce822fbcce` |
| tests/test_check_plan_governance.py | `1b1bda08427b09846373f4086c34457ea3b5749bbfe1fe2afe64f4bbafc1f68e` |
| tests/test_plan_governance_hooks.py | `8a07a4ff88b4f1111d6d1b34270196db4e44101d778b611c3630e0d1d50854a3` |
| tests/npm_cli.test.mjs | `fdcd2f12eb70e116bf8884c9239e83a1ee1b89d36d272868e692f8b77cdff6af` |

以上八份 hash 与复核前后工作区列表一致。

### 阻塞 D01

P2：`structured_next_action` 正文回退对原始当前阶段正文做正则，代码块里的 `下一动作：实施` 被派生成真实指令。合法实施中计划的普通/严格工作集均输出 `known/implement`，无 warning；即使代码块后声明真实 `下一动作：验证` 也被覆盖。session-start hook 同样提示实施。

复核者用三反引号、四波浪线分别验证“只有示例”和“示例后有真实验证动作”，四种输入全部复现。真实 Node→Python 共 20 次调用，输入不变且临时目录清理；证据为复核工具输出 `cdedfe`。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B - <<'PY'
import runpy
ns = runpy.run_path('tests/test_check_plan_governance.py')
plan = ns['readiness_plan_text'](status='实施中').replace(
    '## 当前阶段',
    '## 当前阶段\n\n下一动作格式示例：\n\n'
    '```text\n下一动作：实施\n```\n\n下一动作：验证'
)
print(ns['check_plan_governance'].structured_next_action(plan))
PY
```

第一轮实际 `kind=implement`，预期 `verify`；去掉真实动作后预期 `unknown`。修复应屏蔽正文回退中的 fenced code，补四类回归，不改变普通检查和 hook 退出码。

### 已执行验证

| 命令或检查 | 结果/工具证据 |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider -q --no-cov` | 199 passed，`f5f58e` |
| `PYTHONDONTWRITEBYTECODE=1 npm test` | 40/40，含临时安装 smoke，`ef301a` |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m coverage report --precision=2` | 读取既有覆盖数据 93.13%，未重写，`b87313` |
| 原始阶段 1 fixture bash 重放并对照修复后结果表 | 22/22、88 调用，无 stderr、输入不变、临时目录清理，`20d867` |
| AST 比对四个输入 helper 与 HEAD；Node 普通/严格/stale/drift/workset | helper 一致，治理均退出 0，已知告警保留，`0968b0` |
| `git diff --check`、反向引用/草案事实源 rg；最终 hash/状态 | 通过，`e0591e`、`1fbae0`、`dc981b`、`561208` |

真实宿主计划仍为阶段 2 设计中，保留 blocked、两问题与一条最近记录。现有套件全通过不能替代 D01 修复；补回归后必须重新独立完成复核。以上工具标识是此次复核会话输出，不是仓库文件路径。

## 第二轮：通过

2026-09-06，`/root/iterative_stage1_recheck` 使用新上下文执行独立只读完成重审，未参与实施、未修改工作区。Revision 仍为 `336b728d7dacc335a35f2cf97ab39356e3a82ba0` 加派发时混合工作树。

**通过：D01 可解除，阶段 1 完成验收通过。** 阶段 1 无剩余验收阻塞；本结论只关闭阶段 1，阶段 2 仍须自己的 Step 0 与独立准入。

### 第二轮受审身份

| 文件 | SHA-256 |
|---|---|
| 专项计划 | `0f28e6c0b40311146f09a3be66c6bd8ce722593d75c8fb4ced036bc279adfd28` |
| 阶段 1 fixture | `aaf4070dcfc06fc1cb483de6b90566d2f14f79d70c456ff62ed29916b81e6d8a` |
| PLAN_MAP | `cd90aa310a879eb8776622cd6cef54a8fcad960d8b5916207130937bd6b34bc5` |
| scripts/check_plan_governance.py | `157623731026d33e0993ad8908d708bdff5599cc1810383f0f4349790b1eb8df` |
| scripts/plan_governance_hook.py | `fe33099f3e5c602e454f913e90feccbff9644de363740da37576fdce822fbcce` |
| tests/test_check_plan_governance.py | `dc73e21dd707a631b8a596d1b31cdef9a1b509148310ddf3f308cf163dbb7e46` |
| tests/test_plan_governance_hooks.py | `8a07a4ff88b4f1111d6d1b34270196db4e44101d778b611c3630e0d1d50854a3` |
| tests/npm_cli.test.mjs | `91f5c241816d85232ab597bbde188db40fb9e7a93fa9bddf425ac49cb2e91c0d` |

八份受审 hash 与派发值一致。复核前后 129 份文件 hash 及工作区列表均未变化；后续关闭状态与落档会改变文档，以上保留受审历史身份。

### 第二轮实际验证

| 实际命令或检查 | 结果 | 工具证据 |
|---|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider -q --no-cov` | 203 passed | `d26a9f` |
| `PYTHONDONTWRITEBYTECODE=1 npm test` | 41/41，含临时安装 smoke | `073632` |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m coverage report --precision=2` | 读取既有数据 93.22%，未重生成 | `5104b5` |
| 原始阶段 1 fixture 首个 bash 与修复后表逐行比较 | 22/22、88 次调用，输入不变、临时目录清理 | `8dcbf8` |
| D01 四输入实盘及内存逆转 | 20 次真实 CLI/hook，当前 unknown/verify；逆转唯一修复行后四类均恢复错误 implement，且 hash 精确等于第一轮 checker | `b287b3` |
| 本地 Node 普通/严格/stale/drift、普通/严格 workset、hook | 符合受审时保留 D01 的阻塞状态 | `7ffad2` |
| 四个输入 helper 与 HEAD 的 AST 源段比较、反向引用/草案事实源扫描 | helper 未变，无新增漂移 | `40b7fb` |
| `git diff --check`；最终内容/状态核对 | 通过且只读 | `3b68e3`、`bf0a64` |

D01 四输入的普通/严格 check、普通/严格 workset 与 session-start hook 全部退出 0，无 stderr，hook 不提示 implement。CLI 成功透传改用合法临时样本，保留真实入口与成功断言；真实仓库门禁独立执行，受审时因尚未关闭 D01 的正确阻塞表现为 check 退出 1、工作集普通/严格 0/1。

阶段 1 三项完成条件均满足：目标反例与兼容契约一致；完整回归及覆盖证据齐全；实际修复属于本阶段并取得独立完成通过结论。宿主计划仍阶段 2 设计中，保留两项问题、一条最近记录，未解除其失败复核。

主执行者可以据本次独立结论关闭 D01 与阶段 1，再运行治理检查。第一轮失败历史继续保留。

## 落档后复查

2026-09-06，主执行者根据第二轮独立结论关闭 D01 和阶段 1，地图当前指针转为阶段 2 设计中，并登记阶段 2 的源码/内存替代基线。随后从本仓库 Node 入口执行普通、严格、stale、drift 检查，均退出 0；严格 workset 中本计划为 `design/complete_step0`，宿主计划仍为 `blocked/resolve_blocker`。宿主旧标题/阻塞同步/失败复核、共享检查器及地图 drift 归属告警保留。此段为主执行者的落档验证，不扩展独立验收范围或放行阶段 2。
