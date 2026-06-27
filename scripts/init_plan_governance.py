#!/usr/bin/env python3
import argparse
import re
import shutil
import sys
from pathlib import Path


VALID_STATUSES = {
    "候选",
    "设计中",
    "待实施",
    "实施中",
    "已完成",
    "已替代",
    "已合并",
    "已废弃",
}


def slugify(value):
    value = value.strip().lower()
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"[^a-z0-9\u4e00-\u9fff._-]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-._")
    if not value:
        raise ValueError("计划名称不能为空")
    return value


def write_file(path, content, force):
    if path.exists() and not force:
        raise FileExistsError(f"{path} 已存在；如需覆盖请加 --force")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def plan_map_content(plan_slug, title, status, phase):
    return f"""# PLAN_MAP

## 治理范围

本文件只跟踪跨阶段、影响公共契约、依赖真实反馈，或会与其他计划发生关系的计划。普通一次性任务不要加入这里。

## 计划索引

| 计划 | 状态 | 当前阶段 | 依赖 | 证据 |
|---|---|---|---|---|
| [{title}](plans/{plan_slug}.md) | {status} | {phase} | - | - |

允许状态：`候选`、`设计中`、`待实施`、`实施中`、`已完成`、`已替代`、`已合并`、`已废弃`。

## 推荐顺序

1. `{plan_slug}`

## 依赖关系

| 计划 | 依赖 | 原因 |
|---|---|---|
| {plan_slug} | - | - |

## 替代、合并和废弃

| 计划 | 关系 | 目标 | 原因 |
|---|---|---|---|
| - | - | - | - |

## 当前阻塞项

| 问题 | 推荐方案 | 影响范围 | 是否阻塞当前阶段 | 状态 |
|---|---|---|---|---|
| - | - | - | 否 | 已延后 |

## 完成证据

| 计划 | 阶段 | 证据 |
|---|---|---|
| - | - | - |
"""


def plan_content(plan_slug, title, status, phase, goal):
    goal_text = goal or "待补充。"
    return f"""# 计划：{title}

## 背景

待补充。

## 目标

{goal_text}

## 非目标

- 待补充。

## 不变量

- 当前阶段写细，后续阶段写粗。
- 完成时必须记录可验证证据。

## 影响模块或文件

- 待补充。

## 公共契约变化

待确认。若涉及 API、Schema、兼容性或迁移行为，需要在这里明确。

## 阶段路线图

| 阶段 | 目标 | 进入条件 | 验证方向 | 状态 |
|---|---|---|---|---|
| {phase} | 建立当前阶段基线 | 治理文档已初始化 | Step 0 证据存在 | {status} |

## 当前阶段

### 范围

待补充。

### 实施步骤

1. 补充 Step 0 证据。
2. 明确当前阶段完成条件。
3. 实施当前阶段。
4. 运行验证并记录证据。

### Step 0 证据

待补充。实施前需要记录失败测试、最小复现、现状快照、兼容样本、fixture 或关键假设验证。

### 验证方式

待补充。

### 测试覆盖率

待补充。完成后需要记录测试覆盖率报告，例如 pytest-cov 输出、覆盖率百分比、关键模块覆盖情况等。

### 完成条件

- Step 0 证据已记录。
- 当前阶段验证通过。
- `docs/PLAN_MAP.md` 状态和证据已同步。

## 未决问题

| 问题 | 推荐方案 | 是否阻塞当前阶段 | 状态 |
|---|---|---|---|
| 当前阶段 Step 0 证据是什么？ | 在实施前补充最小可观察基线。 | 是 | 待确认 |

## 风险和回滚

待补充。

## 关联 ADR、迁移、spec 或 issue

- 
"""


def copy_checker(root, force):
    source = Path(__file__).with_name("check_plan_governance.py")
    target = root / "scripts" / "check_plan_governance.py"
    if target.exists() and not force:
        raise FileExistsError(f"{target} 已存在；如需覆盖请加 --force")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    target.chmod(0o755)
    return target


def parse_args(argv):
    parser = argparse.ArgumentParser(description="初始化中文 plan-governance 文档。")
    parser.add_argument("--root", default=".", help="目标仓库根目录，默认当前目录。")
    parser.add_argument("--plan", required=True, help="计划文件名或计划标识，例如 api-compat-migration。")
    parser.add_argument("--title", help="计划显示名称，默认使用 --plan。")
    parser.add_argument("--goal", help="计划目标，会写入计划文档。")
    parser.add_argument("--status", default="设计中", choices=sorted(VALID_STATUSES), help="初始状态。")
    parser.add_argument("--phase", default="阶段 0", help="当前阶段名称。")
    parser.add_argument("--copy-checker", action="store_true", help="复制检查脚本到目标仓库 scripts/。")
    parser.add_argument("--force", action="store_true", help="允许覆盖已存在的治理文件。")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    root = Path(args.root).expanduser().resolve()
    plan_slug = slugify(args.plan)
    title = args.title or plan_slug

    docs = root / "docs"
    plan_map = docs / "PLAN_MAP.md"
    plan_file = docs / "plans" / f"{plan_slug}.md"

    created = []
    write_file(plan_map, plan_map_content(plan_slug, title, args.status, args.phase), args.force)
    created.append(plan_map)
    write_file(plan_file, plan_content(plan_slug, title, args.status, args.phase, args.goal), args.force)
    created.append(plan_file)

    if args.copy_checker:
        created.append(copy_checker(root, args.force))

    for path in created:
        print(f"已创建：{path}")
    print("初始化完成。下一步请补充计划文档中的 Step 0 证据、验证方式和完成条件。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileExistsError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
