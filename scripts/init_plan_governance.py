#!/usr/bin/env python3
import argparse
import html
import importlib.util
import re
import shutil
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path


_checker_spec = importlib.util.spec_from_file_location("initializer_checker", Path(__file__).with_name("check_plan_governance.py"))
checker = importlib.util.module_from_spec(_checker_spec)
_checker_spec.loader.exec_module(checker)


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

AGENTS_SECTION_BEGIN = "<!-- plan-governance:start -->"
AGENTS_SECTION_END = "<!-- plan-governance:end -->"
WRITTEN_FILES = []


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
    WRITTEN_FILES.append(path)


def init_git(root):
    if (root / ".git").exists():
        return None

    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=root, check=True)
    WRITTEN_FILES.append(root / ".git")
    return root / ".git"


def agent_rules_body():
    return checker.agent_rules_body()


def managed_section(begin, end):
    return f"{begin}\n{agent_rules_body()}{end}\n"


def agents_md_section():
    return managed_section(AGENTS_SECTION_BEGIN, AGENTS_SECTION_END)


def update_managed_file(root, filename, section, begin, end):
    target = root / filename
    if not target.exists():
        write_file(target, section, force=False)
        return target

    # Keep line endings and trailing whitespace outside the managed block intact.
    current = target.read_bytes().decode("utf-8")
    markers = checker.agent_rules_markers(current, begin, end)
    if markers:
        start, finish = markers
        updated = current[:start.start()] + section.rstrip() + current[finish.end():]
    else:
        newline = "\r\n" if "\r\n" in current else "\n"
        if not current or current.endswith(newline * 2):
            separator = ""
        else:
            separator = newline if current.endswith(("\n", "\r")) else newline * 2
        updated = f"{current}{separator}{section}"
    target.write_bytes(updated.encode("utf-8"))
    WRITTEN_FILES.append(target)
    return target


def update_agents_md(root):
    return update_managed_file(
        root,
        "AGENTS.md",
        agents_md_section(),
        AGENTS_SECTION_BEGIN,
        AGENTS_SECTION_END,
    )


def update_agent_rules(root):
    return [update_agents_md(root)]


def plan_map_template_path():
    return Path(__file__).resolve().parents[1] / "resources" / "skill" / "assets" / "PLAN_MAP.template.md"


def plan_map_content(plan_slug, title, status, phase, created_on=None):
    created_on = created_on or date.today()
    template = plan_map_template_path().read_text(encoding="utf-8")
    if not template.startswith("# PLAN_MAP\n") or len(re.findall(r"^# ", template, re.MULTILINE)) != 1:
        raise ValueError("地图模板须以唯一一级标题开始")
    required = {"plan_slug", "unfinished_row", "completed_row", "deprecated_row"}
    tokens = re.findall(r"{{(.*?)}}", template)
    if set(tokens) != required or any(tokens.count(key) != 1 for key in required - {"plan_slug"}):
        raise ValueError("地图模板缺失、重复或包含未知占位符")
    headings = ["## 计划索引", "### 未完成", "### 已完成", "### 已废弃", "## 治理范围"]
    positions = []
    for heading in headings:
        matches = list(re.finditer(rf"^{re.escape(heading)}$", template, re.MULTILINE))
        if len(matches) != 1:
            raise ValueError("地图模板缺少或重复索引分类章节")
        positions.append(matches[0].start())
    if positions != sorted(positions):
        raise ValueError("地图模板索引必须位于治理说明前，分类顺序固定")

    # 标签不能注入新表格列、换行或 Markdown 链接。
    label = html.escape(" ".join(title.splitlines()), quote=False)
    for char, entity in [("\\", "&#92;"), ("|", "&#124;"), ("[", "&#91;"), ("]", "&#93;")]:
        label = label.replace(char, entity)
    plan_relative = f"plans/{created_on:%Y%m%d}/{plan_slug}.md"
    row = f"| [{label}]({plan_relative}) | {status} | {phase} | {created_on.isoformat()} | - | - |"
    groups = {"unfinished_row": {"候选", "设计中", "待实施", "实施中"},
              "completed_row": {"已完成"}, "deprecated_row": {"已替代", "已合并", "已废弃"}}
    if status not in VALID_STATUSES:
        raise ValueError(f"计划状态不合法：{status}")
    values = {key: row if status in states else "" for key, states in groups.items()}
    values["plan_slug"] = plan_slug
    rendered = re.sub(r"{{(.*?)}}", lambda match: values[match.group(1)], template)
    header = ["计划", "状态", "当前阶段", "最后更新", "依赖", "证据"]
    for heading, key in zip(headings[1:4], groups):
        section = rendered.split(heading + "\n", 1)[1].split("\n#", 1)[0]
        rows = checker.markdown_table_rows(section)
        expected = 2 if status in groups[key] else 1
        lines = section.strip().splitlines()
        valid_separator = len(lines) >= 2 and re.fullmatch(r"\|(?:\s*:?-{3,}:?\s*\|){6}", lines[1])
        valid_data_row = expected == 1 or (len(lines) >= 3 and lines[2] == row)
        if (not valid_separator or not valid_data_row or len(rows) != expected
                or rows[0] != header or any(len(item) != 6 for item in rows)):
            raise ValueError("地图模板分类表必须保持六列且每个计划仅出现一次")
    return rendered


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
        return target
    if target.exists() and not force:
        raise FileExistsError(f"{target} 已存在；如需覆盖请加 --force")
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target.write_bytes(source.read_bytes())
    else:
        shutil.copy2(source, target)
    WRITTEN_FILES.append(target)
    return target


def docs_warnings(root):
    warnings = []
    if not (root / "docs" / "PLAN_MAP.md").exists():
        warnings.append("缺少 docs/PLAN_MAP.md")
    plans_dir = root / "docs" / "plans"
    dated_plans = False
    if plans_dir.exists():
        for child in plans_dir.iterdir():
            if not (child.is_dir() and re.fullmatch(r"\d{8}", child.name)):
                continue
            try:
                datetime.strptime(child.name, "%Y%m%d")
            except ValueError:
                continue
            if any(child.glob("*.md")):
                dated_plans = True
                break
    if not plans_dir.exists() or (not any(plans_dir.glob("*.md")) and not dated_plans):
        warnings.append("缺少 docs/plans 下的平铺或 YYYYMMDD 日期目录计划")
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
        WRITTEN_FILES.append(plan_map)
    return plan_map, changed


def upgrade_existing(root):
    written = [
        copy_checker(root, force=True),
        *update_agent_rules(root),
    ]
    return written, docs_warnings(root)


def parse_args(argv):
    parser = argparse.ArgumentParser(description="初始化中文 plan-governance 文档。", allow_abbrev=False)
    parser.add_argument("--root", type=checker.nonempty, default=".", help="目标仓库根目录，默认当前目录。")
    parser.add_argument("--plan", type=checker.nonempty, help="计划文件名或计划标识，例如 api-compat-migration。")
    parser.add_argument("--title", type=checker.nonempty, help="计划显示名称，默认使用 --plan。")
    parser.add_argument("--goal", type=checker.nonempty, help="计划目标，会写入计划文档。")
    parser.add_argument("--status", default="设计中", choices=sorted(VALID_STATUSES), help="初始状态。")
    parser.add_argument("--phase", type=checker.nonempty, default="阶段 0", help="当前阶段名称。")
    parser.add_argument("--copy-checker", action="store_true", help="复制检查脚本到目标仓库 scripts/。")
    parser.add_argument("--update-agents-md", action="store_true", help="创建或更新目标仓库 AGENTS.md 中的计划治理规则。")
    parser.add_argument("--update-agent-rules", action="store_true", help="创建或更新目标仓库 AGENTS.md 中的计划治理规则。")
    parser.add_argument("--update-agents-md-only", action="store_true", help="只创建或更新 AGENTS.md，不初始化或覆盖 docs/。")
    parser.add_argument("--update-agent-rules-only", action="store_true", help="只创建或更新 AGENTS.md，不初始化或覆盖 docs/。")
    parser.add_argument("--upgrade-existing", action="store_true", help="升级已有项目的辅助文件：刷新检查脚本和代理规则，不覆盖 docs/。")
    parser.add_argument("--migrate-plan-map-last-updated", action="store_true", help="将旧五列表 PLAN_MAP.md 迁移为包含最后更新的六列表。")
    parser.add_argument("--last-updated-date", default=date.today().isoformat(), help="迁移 PLAN_MAP.md 时填入的最后更新日期，默认今天。")
    parser.add_argument("--force", action="store_true", help="允许覆盖已存在的治理文件。")
    checker.validate_options(parser, argv)
    args = parser.parse_args(argv)
    only_modes = [
        args.update_agents_md_only,
        args.update_agent_rules_only,
        args.upgrade_existing,
        args.migrate_plan_map_last_updated,
    ]
    if sum(bool(mode) for mode in only_modes) > 1:
        parser.error("--update-*-only、--upgrade-existing 和 --migrate-plan-map-last-updated 不能同时使用")
    if not any(only_modes) and not args.plan:
        parser.error("正常初始化必须提供 --plan；已有项目可使用 --update-*-only、--upgrade-existing 或 --migrate-plan-map-last-updated")
    supplied = {token.split("=", 1)[0] for token in argv if token.startswith("--")}
    if any(only_modes):
        allowed = {"--root", "--update-agents-md-only", "--update-agent-rules-only", "--upgrade-existing", "--migrate-plan-map-last-updated"}
        if args.migrate_plan_map_last_updated:
            allowed.add("--last-updated-date")
        if supplied - allowed:
            parser.error("当前模式不接受：" + "、".join(sorted(supplied - allowed)))
    else:
        if "--last-updated-date" in supplied:
            parser.error("--last-updated-date 仅用于迁移")
        if args.status not in {"候选", "设计中"}:
            parser.error("新计划只能以 候选/设计中 初始化；准入后再同步状态")
        if not checker.valid_phase_name(args.phase):
            parser.error("--phase 必须为阶段身份，例如 阶段 0")
        if args.update_agents_md and args.update_agent_rules:
            parser.error("代理规则更新别名不能同时指定")
    if args.migrate_plan_map_last_updated:
        try:
            date.fromisoformat(args.last_updated_date)
        except ValueError:
            parser.error("--last-updated-date 必须是有效 ISO 日期")
    return args


def main(argv=None):
    WRITTEN_FILES.clear()
    args = parse_args(sys.argv[1:] if argv is None else argv)
    root = Path(args.root).expanduser().resolve()
    if root.exists() and not root.is_dir():
        raise NotADirectoryError(f"root 不是目录：{root}")
    if any((args.update_agents_md_only, args.update_agent_rules_only, args.upgrade_existing,
            args.update_agents_md, args.update_agent_rules)):
        target = root / "AGENTS.md"
        if target.exists():
            checker.agent_rules_markers(target.read_text(encoding="utf-8"))
    if args.upgrade_existing:
        target = root / "scripts/check_plan_governance.py"
        if target.exists() and not target.is_file():
            raise IsADirectoryError(f"checker 目标不是普通文件：{target}")
        if target.parent.exists() and not target.parent.is_dir():
            raise NotADirectoryError(f"checker 父路径不是目录：{target.parent}")

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
    created_on = date.today()
    plan_file = docs / "plans" / created_on.strftime("%Y%m%d") / f"{plan_slug}.md"

    targets = [plan_map, plan_file]
    if args.copy_checker:
        targets.append(root / "scripts/check_plan_governance.py")
    for target in targets:
        if target.exists() and (not args.force or not target.is_file()):
            raise FileExistsError(f"{target} 已存在；未写入任何治理文件")
        for parent in target.parents:
            if parent.exists() and not parent.is_dir():
                raise NotADirectoryError(f"目标父路径不是目录：{parent}")
    # 首次写入前读取全部必要来源。
    map_text = plan_map_content(plan_slug, title, args.status, args.phase, created_on)
    body = plan_content(plan_slug, title, args.status, args.phase, args.goal)
    if args.update_agents_md or args.update_agent_rules:
        target = root / "AGENTS.md"
        if target.exists():
            target.read_text(encoding="utf-8")
    created = []
    git_dir = init_git(root)
    if git_dir is not None:
        created.append(git_dir)

    write_file(plan_map, map_text, args.force)
    created.append(plan_map)
    write_file(plan_file, body, args.force)
    created.append(plan_file)

    if args.copy_checker:
        created.append(copy_checker(root, args.force))
    if args.update_agent_rules:
        created.extend(update_agent_rules(root))
    elif args.update_agents_md:
        created.append(update_agents_md(root))

    for path in created:
        print(f"已写入：{path}")
    print("初始化完成。下一步请补充计划文档中的 Step 0 证据、验证方式和完成条件。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print("初始化未完成；已写入：" + ("、".join(str(p) for p in WRITTEN_FILES) or "无") + "；请核对出错目标后恢复或重试。", file=sys.stderr)
        raise SystemExit(1)
