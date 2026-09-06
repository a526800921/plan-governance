# 独立复核：持续迭代治理优化阶段 0

| 字段 | 内容 |
|---|---|
| 日期 | 2026-09-06 |
| 计划 | iterative-governance-reliability |
| 阶段 | 阶段 0 |
| 复核者 | `/root/iterative_stage0_gate`，新上下文独立只读 subagent，未参与实施 |
| 被审查 revision | `336b728d7dacc335a35f2cf97ab39356e3a82ba0` 加派发时未提交工作树，内容 hash 见下表 |
| 范围 | B01—B03 技术收敛、用户确认的兼容边界、替代集成基线、计划分工及状态/证据同步 |
| 结论 | 通过，达到阶段 0 `待实施` 标准；阶段 0 设计交付完成。阶段 1 尚未准入，必须保持 `设计中` |
| 阻塞项 | 阶段 0 无阻塞项 |
| 记录方式 | 主执行者按独立复核返回结果落档；复核者未编辑工作区 |

## 被审查内容

| 文件 | SHA-256 |
|---|---|
| `docs/plans/iterative-governance-reliability.md` | `1c2a88832e5b179c3a28ef5c7f4addb60c86479505f0255dd90618eec225cd27` |
| `docs/fixtures/iterative-governance-reliability-stage0-cases.md` | `74aceb549fb5fb41223248803c6b525a56deb798aad8d5d2770e5bec14a930b4` |
| `docs/PLAN_MAP.md` | `55f06d9e35cebb72bd57171d622e90ba21c97531cf48cfc8cd89b95a07a2e3f7` |

复核前后上述 hash 一致；六份运行源和测试文件也全部匹配 [阶段 0 fixture](../fixtures/iterative-governance-reliability-stage0-cases.md) 的记录。后续追加本报告和阶段转换记录会改变计划及地图的 hash，不改写本次被审查身份。

## 实际执行与证据

| 命令或检查 | 结果 |
|---|---|
| 提取 fixture bash 原文，经 `subprocess.run(['bash','--noprofile','--norc'], input=block, text=True, capture_output=True)` 执行并核对结果 | 11 类、33 次 Python CLI 调用，11/11 与实际结果表匹配 |
| 计划内最小只读复现 | 退出 0，重现 E01 |
| `PYTHONDONTWRITEBYTECODE=1 node bin/plan-governance-cli.mjs check .` | 退出 0 |
| 上述检查加 `--strict-readiness` 或 `--stale-days 10` | 均退出 0 |
| 上述检查加 `--drift` | 退出 0；一条已记录的地图归属 WARNING |
| 上述检查加 `--check-attestations` | 退出 0；四份旧快照仍为 needs_review |
| `PYTHONDONTWRITEBYTECODE=1 node bin/plan-governance-cli.mjs workset . --json` | 退出 0；真实宿主计划仍重现 E02 |
| `git diff --check`、反向引用及事实源搜索 | 通过 |
| 屏蔽代码块后的本地链接检查 | 本计划及 fixture 新增链接有效 |

命令输出位置为独立复核工具输出；可重放输入和结果表位于 [阶段 0 fixture](../fixtures/iterative-governance-reliability-stage0-cases.md#2026-09-06-实际结果)。未运行 pytest/npm 套件、安装或构建。

## 判断依据与边界

- 用户确认的兼容策略已准确写入：保留默认退出码分层、现有 JSON 字段和 Schema 版本；新增准入问题由严格模式阻断，未接管宿主调度。
- 十一类样本稳定观察到现行漏检及合法对照；没有将错误放行称为修复通过。
- 阶段关系为 soft_context，既有宿主计划阶段 2 的失败复核仍然有效，没有被解除。
- 真实文件系统 Node→Python 全链路、扩大反例和完整测试明确留给阶段 1，自身 Step 0 与准入不可省略。
- 地图另有两处既存历史锚点失效，属于旧引用，不阻塞本次新增阶段包的准入。

本结论关闭阶段 0 设计交付，不证明实现缺陷已修复，也不放行阶段 1。
