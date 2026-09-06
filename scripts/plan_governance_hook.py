#!/usr/bin/env python3
import argparse
import importlib.util
import re
import subprocess
import sys
from pathlib import Path


# 从随包分发的同目录模块读取，避免误用目标仓库或全局安装的检查器。
_checker_spec = importlib.util.spec_from_file_location(
    "plan_governance_checker", Path(__file__).with_name("check_plan_governance.py")
)
checker = importlib.util.module_from_spec(_checker_spec)
_checker_spec.loader.exec_module(checker)


ACTIVE_STATUSES = {"候选", "设计中", "待实施", "实施中"}
PLACEHOLDER_VALUES = {"-", "待补充", "待补充。", "待确认", "无", "N/A"}


def read_text(path):
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


table_rows = checker.table_rows


extract_plan_link = checker.extract_plan_link


def extract_plan_name(cell, link):
    if link:
        return Path(link).stem
    label = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cell)
    return label.strip("` ")


markdown_section = checker.markdown_section


def markdown_list_items(section):
    if section is None:
        return []
    items = []
    for line in section.splitlines():
        match = re.match(r"\s*[-*]\s+(.+?)\s*$", line)
        if not match:
            continue
        item = match.group(1).strip().strip("` ")
        if item and item not in PLACEHOLDER_VALUES:
            items.append(item)
    return items


def normalize_scope_path(value):
    normalized = value.strip().strip("`").strip()
    normalized = re.sub(r"/+", "/", normalized)
    while normalized.startswith("./"):
        normalized = normalized[2:]
    normalized = normalized.strip("/")
    return normalized


def extract_scope_token(item):
    backtick = re.search(r"`([^`]+)`", item)
    if backtick:
        return normalize_scope_path(backtick.group(1))
    token = item.strip().split(None, 1)[0] if item.strip() else ""
    return normalize_scope_path(token.rstrip(":："))


def load_plans(root):
    plan_map_path = root / "docs" / "PLAN_MAP.md"
    text = read_text(plan_map_path)
    plans = []
    for row in table_rows(text, "计划索引"):
        if len(row) < 6:
            continue
        link = extract_plan_link(row[0])
        name = extract_plan_name(row[0], link)
        plan_path = root / "docs" / link if link else None
        plans.append(
            {
                "name": name,
                "path": plan_path,
                "status": row[1].strip("` "),
                "phase": row[2].strip("` "),
                "last_updated": row[3].strip("` "),
                "evidence": row[5].strip(),
                "targets": [],
            }
        )
    for plan in plans:
        if plan["path"] is None:
            continue
        plan_text = read_text(plan["path"])
        section = markdown_section(plan_text, ["影响模块或文件"])
        plan["targets"] = [
            target
            for item in markdown_list_items(section)
            if (target := extract_scope_token(item))
            and target not in PLACEHOLDER_VALUES
        ]
    return plans, table_rows(text, "当前阻塞项")


def active_plans(root):
    plans, blockers = load_plans(root)
    return [plan for plan in plans if plan["status"] in ACTIVE_STATUSES], blockers


def target_matches_path(target, path):
    normalized_target = normalize_scope_path(target)
    normalized_path = normalize_scope_path(path)
    if not normalized_target or not normalized_path:
        return False
    if normalized_target == normalized_path:
        return True
    return normalized_path.startswith(f"{normalized_target.rstrip('/')}/")


def matching_plans(root, paths):
    active, _ = active_plans(root)
    matches = []
    for plan in active:
        if any(
            target_matches_path(target, path)
            for target in plan["targets"]
            for path in paths
        ):
            matches.append(plan)
    return matches


def print_session_start(root):
    active, _ = active_plans(root)
    if not active:
        print("[plan-governance] 未发现活跃计划。")
        return 0

    print("[plan-governance] 活跃计划摘要：")
    for plan in active:
        print(
            f"- {plan['name']}: {plan['status']}，{plan['phase']}，"
            f"最后更新 {plan['last_updated']}，证据 {plan['evidence']}"
        )
    print_gate_hints(root, {plan["name"] for plan in active})
    return 0


def print_gate_hints(root, names):
    payload, _ = checker.workset_payload(root)
    has_blockers = False
    for plan in payload["plans"]:
        if plan["plan"] not in names:
            continue
        print(f"  {plan['plan']}: {plan['readiness']}，下一动作 {plan['next_action']['kind']}")
        for blocker in plan["blockers"]:
            has_blockers = True
            print(f"  当前阻塞项：{blocker}")
    for warning in payload["warnings"]:
        print(f"  WARNING: {warning}")
    if not has_blockers:
        print("[plan-governance] 当前阻塞项：无法确认，请核对诊断。" if payload["warnings"]
              else "[plan-governance] 当前阻塞项：无。")


def print_pre_write(root, paths):
    matches = matching_plans(root, paths)
    if not matches:
        print("[plan-governance] 未匹配到相关活跃计划。")
        return 0

    print("[plan-governance] 写入前检查：")
    for plan in matches:
        print(f"- {plan['name']}: {plan['status']}，{plan['phase']}")
        print("  当前阶段门禁：确认 Step 0 证据、验证方式、完成条件和公共契约约束。")
    print_gate_hints(root, {plan["name"] for plan in matches})
    return 0


def is_plan_map(path):
    return normalize_scope_path(path) == "docs/PLAN_MAP.md"


def is_plan_doc(path):
    normalized = normalize_scope_path(path)
    return normalized.startswith("docs/plans/") and normalized.endswith(".md")


def print_post_write(paths):
    if any(is_plan_map(path) for path in paths):
        print(
            "[plan-governance] 已写入 PLAN_MAP.md：请同步状态、当前阶段、"
            "最后更新、证据和反向引用检查。"
        )
    if any(is_plan_doc(path) for path in paths):
        print(
            "[plan-governance] 已写入计划文档：请同步 PLAN_MAP.md、验证证据、"
            "测试覆盖率和反向引用检查。"
        )
    if not any(is_plan_map(path) or is_plan_doc(path) for path in paths):
        print("[plan-governance] 写入完成：如影响计划事实，请同步治理文档。")
    return 0


def print_stop(root):
    checker = root / "scripts" / "check_plan_governance.py"
    if not checker.exists():
        print("[plan-governance] 未找到 scripts/check_plan_governance.py，跳过停止前检查。")
        return 0

    result = subprocess.run(
        [sys.executable, str(checker), "."],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    output = (result.stdout or result.stderr).strip()
    if output:
        print(output)
    print("[plan-governance] Stop 检查为非阻塞提示；请人工复核 WARNING/ERROR。")
    return 0


def parse_args(argv):
    parser = argparse.ArgumentParser(description="计划治理 hook runtime。")
    parser.add_argument("--root", default=".", help="仓库根目录，默认当前目录。")
    parser.add_argument(
        "--event",
        required=True,
        choices=["session-start", "pre-write", "post-write", "stop"],
        help="hook 事件类型。",
    )
    parser.add_argument("--paths", nargs="*", default=[], help="事件相关路径。")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    root = Path(args.root)

    if args.event == "session-start":
        return print_session_start(root)
    if args.event == "pre-write":
        return print_pre_write(root, args.paths)
    if args.event == "post-write":
        return print_post_write(args.paths)
    if args.event == "stop":
        return print_stop(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
