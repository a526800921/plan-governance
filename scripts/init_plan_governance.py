#!/usr/bin/env python3
import argparse
import re
import shutil
import subprocess
import sys
from datetime import date
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

CLAUDE_SECTION_BEGIN = "<!-- plan-governance:start -->"
CLAUDE_SECTION_END = "<!-- plan-governance:end -->"
AGENTS_SECTION_BEGIN = "<!-- plan-governance:start -->"
AGENTS_SECTION_END = "<!-- plan-governance:end -->"


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


def init_git(root):
    if (root / ".git").exists():
        return None

    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=root, check=True)
    return root / ".git"


def agent_rules_body():
    return """## 计划治理

本项目使用轻量计划治理。处理治理任务前，先读取当前环境发现的已安装 `plan-governance` skill 的 SKILL.md，并按任务读取其同源 references；不要假定用户安装目录。

只有 CLI 可用时，运行 `plan-governance-cli guide` 读取入口，再按需运行 `guide planning`、`guide verification` 或 `guide cli`。两者均不可用或所需能力缺失时说明前提，不自动安装，也不猜测/拼接不同版本的规则。

最小执行边界：

- 普通无计划覆盖的小改不强制治理；普通改动自验，高风险或高影响同范围独立复核一次，修复后自验；记录与旧策略迁移按共享 verification 规范处理。
- 只实施已授权、已准入的当前阶段。每个阶段有自身 Step 0、验证/完成和失败边界；未解决问题不能记为完成，不可用或超时不能冒充已检查。已有授权不重复索取，新增高影响外部动作按实际授权处理。
- 首次读取 `docs/PLAN_MAP.md`、当前相关 `docs/plans/*.md` 及适用契约/ADR/migration；恢复先核对当前工作集、最近证据和实际 diff，缺失或冲突再展开。
- 地图维护状态、阶段、关系、阻塞与证据入口；计划记录本次差异及验证，现行契约优先复用 Schema/OpenAPI。新事实不写回历史草案，变化同步地图及相关引用。
- 完成时按共享规范记录实际验证与适用用户验收，运行 `plan-governance-cli check .`；准入/CI/发布显式使用 `--strict-readiness`，机械通过不等于业务验收。
"""


def managed_section(begin, end):
    return f"{begin}\n{agent_rules_body()}{end}\n"


def claude_md_section():
    return managed_section(CLAUDE_SECTION_BEGIN, CLAUDE_SECTION_END)


def agents_md_section():
    return managed_section(AGENTS_SECTION_BEGIN, AGENTS_SECTION_END)


def update_managed_file(root, filename, section, begin, end):
    target = root / filename
    if not target.exists():
        write_file(target, section, force=False)
        return target

    # Keep line endings and trailing whitespace outside the managed block intact.
    current = target.read_bytes().decode("utf-8")
    pattern = re.compile(
        rf"{re.escape(begin)}.*?{re.escape(end)}",
        re.DOTALL,
    )
    if pattern.search(current):
        updated = pattern.sub(lambda match: section.rstrip(), current)
    else:
        newline = "\r\n" if "\r\n" in current else "\n"
        if not current or current.endswith(newline * 2):
            separator = ""
        else:
            separator = newline if current.endswith(("\n", "\r")) else newline * 2
        updated = f"{current}{separator}{section}"
    target.write_bytes(updated.encode("utf-8"))
    return target


def update_claude_md(root):
    return update_managed_file(
        root,
        "CLAUDE.md",
        claude_md_section(),
        CLAUDE_SECTION_BEGIN,
        CLAUDE_SECTION_END,
    )


def update_agents_md(root):
    return update_managed_file(
        root,
        "AGENTS.md",
        agents_md_section(),
        AGENTS_SECTION_BEGIN,
        AGENTS_SECTION_END,
    )


def update_agent_rules(root):
    return [update_claude_md(root), update_agents_md(root)]


def plan_map_content(plan_slug, title, status, phase):
    today = date.today().isoformat()
    row = f"| [{title}](plans/{plan_slug}.md) | {status} | {phase} | {today} | - | - |"
    unfinished_row = row if status in {"候选", "设计中", "待实施", "实施中"} else ""
    completed_row = row if status == "已完成" else ""
    deprecated_row = row if status in {"已废弃", "已替代", "已合并"} else ""
    return f"""# PLAN_MAP

## 治理范围

本文件只跟踪跨阶段、影响公共契约、依赖真实反馈，或会与其他计划发生关系的计划。普通一次性任务不要加入这里。

## 文档权责

- `docs/PLAN_MAP.md` 是状态、依赖、替代/合并/废弃关系、推荐顺序、阻塞项和证据链接的事实源。
- `docs/plans/*.md` 记录本次行为差异、阶段、Step 0 和验收；现行契约优先引用已有 Schema/OpenAPI，无合适来源且需长期维护时才按需建立 `docs/specs/*.md`。同一事实不重复维护。
- 总路线图、优先级计划和索引只记录顺序、状态摘要和专项计划链接，不复制字段级方案、枚举、Step 0 细节或完成定义。
- 当专项计划变化时，必须同步所有引用该计划的路线图、优先级计划或索引。
- 如果同一事实在多个文档中重复，保留一个事实源，其他文档改为链接引用。
- `PLAN_MAP.md` 的 `状态` 是计划级生命周期，`当前阶段` 是阶段身份指针；阶段 N 完成后，阶段 N+1 默认保持 `设计中`。
- 阶段准入摘要、样本矩阵和独立复核记录只写入专项计划，不复制到本索引。
- 启用治理后，已有草案、历史设计、归档计划和临时分析文档默认只作为背景材料，不再作为规范事实源；后续新规范默认进入 `docs/plans/*.md`、ADR、migration、正式 spec 或 `docs/PLAN_MAP.md`。
- 计划索引固定分为 `未完成`、`已完成`、`已废弃` 三张表；`已替代`、`已合并`等不再推进的终态归入 `已废弃` 表，但保留真实状态值。

## 计划索引

### 未完成

| 计划 | 状态 | 当前阶段 | 最后更新 | 依赖 | 证据 |
|---|---|---|---|---|---|
{unfinished_row}

### 已完成

| 计划 | 状态 | 当前阶段 | 最后更新 | 依赖 | 证据 |
|---|---|---|---|---|---|
{completed_row}

### 已废弃

| 计划 | 状态 | 当前阶段 | 最后更新 | 依赖 | 证据 |
|---|---|---|---|---|---|
{deprecated_row}

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


def plan_template_path():
    return Path(__file__).resolve().parents[1] / "resources" / "skill" / "assets" / "plan.template.md"


def plan_content(plan_slug, title, status, phase, goal):
    goal_text = goal or "待补充。"
    template = plan_template_path().read_text(encoding="utf-8")
    return (
        template.replace("{{title}}", title)
        .replace("{{goal}}", goal_text)
        .replace("{{status}}", status)
        .replace("{{phase}}", phase)
    )


def copy_checker(root, force):
    source = Path(__file__).with_name("check_plan_governance.py")
    target = root / "scripts" / "check_plan_governance.py"
    if source.resolve() == target.resolve():
        target.chmod(0o755)
        return target
    if target.exists() and not force:
        raise FileExistsError(f"{target} 已存在；如需覆盖请加 --force")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    target.chmod(0o755)
    return target


def docs_warnings(root):
    warnings = []
    if not (root / "docs" / "PLAN_MAP.md").exists():
        warnings.append("缺少 docs/PLAN_MAP.md")
    plans_dir = root / "docs" / "plans"
    if not plans_dir.exists() or not any(plans_dir.glob("*.md")):
        warnings.append("缺少 docs/plans/*.md")
    return warnings


def migrate_plan_map_last_updated(root, last_updated):
    plan_map = root / "docs" / "PLAN_MAP.md"
    if not plan_map.exists():
        raise FileNotFoundError("缺少 docs/PLAN_MAP.md")

    text = plan_map.read_text(encoding="utf-8")
    lines = text.splitlines()
    migrated = []
    in_plan_index = False
    changed = False

    for line in lines:
        if re.match(r"^##\s+计划索引\s*$", line):
            in_plan_index = True
            migrated.append(line)
            continue
        if in_plan_index and re.match(r"^##\s+", line):
            in_plan_index = False

        if in_plan_index and line.strip().startswith("|"):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if cells == ["计划", "状态", "当前阶段", "依赖", "证据"]:
                migrated.append("| 计划 | 状态 | 当前阶段 | 最后更新 | 依赖 | 证据 |")
                changed = True
                continue
            if len(cells) == 5 and set(cells) == {"---"}:
                migrated.append("|---|---|---|---|---|---|")
                changed = True
                continue
            if len(cells) == 5:
                cells.insert(3, last_updated)
                migrated.append("| " + " | ".join(cells) + " |")
                changed = True
                continue

        migrated.append(line)

    if changed:
        plan_map.write_text("\n".join(migrated) + ("\n" if text.endswith("\n") else ""), encoding="utf-8")
    return plan_map, changed


def upgrade_existing(root):
    written = [
        copy_checker(root, force=True),
        *update_agent_rules(root),
    ]
    return written, docs_warnings(root)


def parse_args(argv):
    parser = argparse.ArgumentParser(description="初始化中文 plan-governance 文档。")
    parser.add_argument("--root", default=".", help="目标仓库根目录，默认当前目录。")
    parser.add_argument("--plan", help="计划文件名或计划标识，例如 api-compat-migration。")
    parser.add_argument("--title", help="计划显示名称，默认使用 --plan。")
    parser.add_argument("--goal", help="计划目标，会写入计划文档。")
    parser.add_argument("--status", default="设计中", choices=sorted(VALID_STATUSES), help="初始状态。")
    parser.add_argument("--phase", default="阶段 0", help="当前阶段名称。")
    parser.add_argument("--copy-checker", action="store_true", help="复制检查脚本到目标仓库 scripts/。")
    parser.add_argument("--update-claude-md", action="store_true", help="创建或更新目标仓库 CLAUDE.md 中的计划治理规则。")
    parser.add_argument("--update-agents-md", action="store_true", help="创建或更新目标仓库 AGENTS.md 中的计划治理规则。")
    parser.add_argument("--update-agent-rules", action="store_true", help="同时创建或更新 CLAUDE.md 和 AGENTS.md 中的计划治理规则。")
    parser.add_argument("--update-claude-md-only", action="store_true", help="只创建或更新 CLAUDE.md，不初始化或覆盖 docs/。")
    parser.add_argument("--update-agents-md-only", action="store_true", help="只创建或更新 AGENTS.md，不初始化或覆盖 docs/。")
    parser.add_argument("--update-agent-rules-only", action="store_true", help="只创建或更新 CLAUDE.md 和 AGENTS.md，不初始化或覆盖 docs/。")
    parser.add_argument("--upgrade-existing", action="store_true", help="升级已有项目的辅助文件：刷新检查脚本和代理规则，不覆盖 docs/。")
    parser.add_argument("--migrate-plan-map-last-updated", action="store_true", help="将旧五列表 PLAN_MAP.md 迁移为包含最后更新的六列表。")
    parser.add_argument("--last-updated-date", default=date.today().isoformat(), help="迁移 PLAN_MAP.md 时填入的最后更新日期，默认今天。")
    parser.add_argument("--force", action="store_true", help="允许覆盖已存在的治理文件。")
    args = parser.parse_args(argv)
    only_modes = [
        args.update_claude_md_only,
        args.update_agents_md_only,
        args.update_agent_rules_only,
        args.upgrade_existing,
        args.migrate_plan_map_last_updated,
    ]
    if sum(bool(mode) for mode in only_modes) > 1:
        parser.error("--update-*-only、--upgrade-existing 和 --migrate-plan-map-last-updated 不能同时使用")
    if not any(only_modes) and not args.plan:
        parser.error("正常初始化必须提供 --plan；已有项目可使用 --update-*-only、--upgrade-existing 或 --migrate-plan-map-last-updated")
    return args


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    root = Path(args.root).expanduser().resolve()

    if args.update_claude_md_only:
        target = update_claude_md(root)
        print(f"已写入：{target}")
        print("CLAUDE.md 已更新；未修改 docs/。")
        return 0

    if args.update_agents_md_only:
        target = update_agents_md(root)
        print(f"已写入：{target}")
        print("AGENTS.md 已更新；未修改 docs/。")
        return 0

    if args.update_agent_rules_only:
        for target in update_agent_rules(root):
            print(f"已写入：{target}")
        print("代理规则已更新；未修改 docs/。")
        return 0

    if args.upgrade_existing:
        written, warnings = upgrade_existing(root)
        for path in written:
            print(f"已写入：{path}")
        for warning in warnings:
            print(f"WARNING: {warning}")
        print("已有项目升级完成；未覆盖 docs/。下一步请运行 plan-governance-cli check .")
        return 0

    if args.migrate_plan_map_last_updated:
        parse_date = date.fromisoformat(args.last_updated_date)
        target, changed = migrate_plan_map_last_updated(root, parse_date.isoformat())
        print(f"已检查：{target}")
        if changed:
            print("PLAN_MAP.md 已迁移为包含最后更新的六列表。")
        else:
            print("PLAN_MAP.md 已是六列表；无需迁移。")
        return 0

    plan_slug = slugify(args.plan)
    title = args.title or plan_slug

    docs = root / "docs"
    plan_map = docs / "PLAN_MAP.md"
    plan_file = docs / "plans" / f"{plan_slug}.md"

    created = []
    git_dir = init_git(root)
    if git_dir is not None:
        created.append(git_dir)

    write_file(plan_map, plan_map_content(plan_slug, title, args.status, args.phase), args.force)
    created.append(plan_map)
    write_file(plan_file, plan_content(plan_slug, title, args.status, args.phase, args.goal), args.force)
    created.append(plan_file)

    if args.copy_checker:
        created.append(copy_checker(root, args.force))
    if args.update_agent_rules:
        created.extend(update_agent_rules(root))
    else:
        if args.update_claude_md:
            created.append(update_claude_md(root))
        if args.update_agents_md:
            created.append(update_agents_md(root))

    for path in created:
        print(f"已写入：{path}")
    print("初始化完成。下一步请补充计划文档中的 Step 0 证据、验证方式和完成条件。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileExistsError, FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
