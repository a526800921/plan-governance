#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import date, datetime, timezone
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

PLACEHOLDER_VALUES = {"-", "待补充", "待补充。", "待确认", "无", "N/A"}

COMPLETED = {"已完成"}
ACTIVE = {"待实施", "实施中"}
WARNING_ACTIVE = {"候选", "设计中", "待实施", "实施中"}
IMPLEMENTING = {"实施中"}
INACTIVE = {"已替代", "已合并", "已废弃"}


def fail(errors, message):
    errors.append(message)


def warn(warnings, message):
    warnings.append(message)


def read_utf8(path, errors):
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        fail(errors, f"{path}: not valid UTF-8")
    except FileNotFoundError:
        fail(errors, f"{path}: file not found")
    return ""


def table_rows(text, heading):
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return []
    tail = text[match.end():]
    next_heading = re.search(r"^##\s+", tail, re.MULTILINE)
    section = tail[: next_heading.start()] if next_heading else tail
    rows = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or "---" in stripped:
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if cells and cells[0] not in {"计划", "问题"}:
            rows.append(cells)
    return rows


def mask_fenced_code(text):
    """用等长空格屏蔽 fenced code 中的伪 Markdown 标题，保留偏移量。"""
    masked = []
    in_fence = False
    for line in text.splitlines(keepends=True):
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            masked.append("".join("\n" if char == "\n" else "\r" if char == "\r" else " " for char in line))
            continue
        if in_fence:
            masked.append("".join("\n" if char == "\n" else "\r" if char == "\r" else " " for char in line))
        else:
            masked.append(line)
    return "".join(masked)


def markdown_section(text, heading_names):
    if not text:
        return None
    heading_pattern = "|".join(re.escape(name) for name in heading_names)
    pattern = re.compile(rf"^#+\s+({heading_pattern})\b.*$", re.MULTILINE)
    match = pattern.search(mask_fenced_code(text))
    if not match:
        return None
    tail = text[match.end():]
    next_heading = re.search(r"^#+\s+", tail, re.MULTILINE)
    return tail[: next_heading.start()] if next_heading else tail


def markdown_table_rows(section):
    if section is None:
        return []
    rows = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or "---" in stripped:
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if cells:
            rows.append(cells)
    return rows


def key_value_table(section):
    values = {}
    for row in markdown_table_rows(section):
        if len(row) < 2 or row[0] in {"字段", "问题"}:
            continue
        values[row[0]] = row[1]
    return values


def numbered_structural_heading(plan_text, heading_names):
    """查找误把阶段编号写入结构化章节标题的常见形式。"""
    phase_number = r"[0-9一二三四五六七八九十百]+"
    variants = []
    for name in heading_names:
        variants.append(rf"阶段\s*{phase_number}\s+{re.escape(name)}")
        if name.startswith("阶段"):
            variants.append(rf"阶段\s*{phase_number}\s*{re.escape(name[2:])}")
    pattern = re.compile(
        rf"^#+\s+((?:{'|'.join(variants)}))\s*$",
        re.MULTILINE,
    )
    match = pattern.search(mask_fenced_code(plan_text))
    return match.group(1) if match else None


def structural_heading_hint(plan_text, heading_name):
    numbered_heading = numbered_structural_heading(plan_text, [heading_name])
    if not numbered_heading:
        return ""
    return (
        f"；检测到标题 `{numbered_heading}`，请改为固定标题 "
        f"`{heading_name}`，阶段编号以 `PLAN_MAP.md` 的当前阶段为准"
    )


def phase_roadmap_rows(plan_text):
    section = markdown_section(plan_text, ["阶段路线图"])
    return [row for row in markdown_table_rows(section) if row and row[0] != "阶段"]


def review_history_rows(plan_text):
    section = markdown_section(plan_text, ["独立复核记录"])
    return [row for row in markdown_table_rows(section) if row and row[0] != "日期"]


def is_placeholder(value, allow_empty=False):
    normalized = re.sub(r"\s+", "", value or "")
    if not normalized:
        return allow_empty
    return normalized in {re.sub(r"\s+", "", item) for item in PLACEHOLDER_VALUES}


READINESS_FIELDS = {
    "准入状态",
    "Step 0",
    "样本矩阵",
    "验证方式",
    "失败/回滚边界",
    "当前阻塞项",
    "最新独立准入复核",
}


def readiness_issue(warnings, errors, strict, message):
    if strict:
        fail(errors, message)
    else:
        warn(warnings, message)


def check_phase_readiness(plan_map_text, plan_name, data, plan_text, strict, warnings, errors):
    """检查待实施/实施中计划的阶段准入结构，不判断业务证据真实性。"""
    if data["status"] not in ACTIVE:
        return

    current_phase = data["phase"]
    current_section = top_level_section(plan_text, "当前阶段")
    summary_section = markdown_section(current_section, ["阶段准入摘要"])
    summary = key_value_table(summary_section)
    roadmap = phase_roadmap_rows(plan_text)
    matching_rows = [row for row in roadmap if row and row[0] == current_phase]
    if not matching_rows:
        roadmap_hint = structural_heading_hint(plan_text, "阶段路线图")
        readiness_issue(
            warnings,
            errors,
            strict,
            f"{plan_name}: PLAN_MAP 当前阶段 {current_phase} 未在计划阶段路线图中找到{roadmap_hint}",
        )
    else:
        roadmap_status = matching_rows[-1][4] if len(matching_rows[-1]) > 4 else ""
        phase_status = summary.get("阶段状态", "").strip()
        expected_roadmap_status = phase_status or data["status"]
        if roadmap_status and roadmap_status != expected_roadmap_status:
            readiness_issue(
                warnings,
                errors,
                strict,
                f"{plan_name}: 当前阶段 {current_phase} 的路线图状态 {roadmap_status} 与阶段状态 {expected_roadmap_status} 不一致",
            )

    if markdown_section(plan_text, ["当前阶段"]) is None:
        section_hint = structural_heading_hint(plan_text, "当前阶段")
        readiness_issue(warnings, errors, strict, f"{plan_name}: 缺少 `## 当前阶段` 章节{section_hint}")

    missing_fields = sorted(READINESS_FIELDS - set(summary))
    if missing_fields:
        title_hint = ""
        if summary_section is None:
            title_hint = structural_heading_hint(plan_text, "阶段准入摘要")
        readiness_issue(
            warnings,
            errors,
            strict,
            f"{plan_name}: 阶段准入摘要缺少字段：{', '.join(missing_fields)}{title_hint}",
        )
    for field in sorted(READINESS_FIELDS - {"当前阻塞项"}):
        if field in summary and is_placeholder(summary[field]):
            readiness_issue(
                warnings,
                errors,
                strict,
                f"{plan_name}: 阶段准入摘要字段 {field} 仍是占位内容",
            )
    if summary.get("当前阻塞项") and is_placeholder(summary["当前阻塞项"]) and summary["当前阻塞项"].strip() != "无":
        readiness_issue(
            warnings,
            errors,
            strict,
            f"{plan_name}: 阶段准入摘要的当前阻塞项不可使用占位内容",
        )
    if summary.get("准入状态") and summary["准入状态"] != data["status"]:
        readiness_issue(
            warnings,
            errors,
            strict,
            f"{plan_name}: 阶段准入摘要状态 {summary['准入状态']} 与 PLAN_MAP 状态 {data['status']} 不一致",
        )

    review = key_value_table(markdown_section(plan_text, ["最新独立准入复核"]))
    review_fields = {"日期", "阶段", "结论", "证据", "复核者"}
    missing_review = sorted(review_fields - set(review))
    if missing_review:
        review_hint = structural_heading_hint(plan_text, "最新独立准入复核")
        readiness_issue(
            warnings,
            errors,
            strict,
            f"{plan_name}: 最新独立准入复核缺少字段：{', '.join(missing_review)}{review_hint}",
        )
    if review.get("日期"):
        try:
            parse_plan_date(review["日期"])
        except ValueError:
            readiness_issue(warnings, errors, strict, f"{plan_name}: 最新独立准入复核日期不合法：{review['日期']}")
    if review.get("阶段") and review["阶段"] != current_phase:
        readiness_issue(
            warnings,
            errors,
            strict,
            f"{plan_name}: 最新独立准入复核阶段 {review['阶段']} 与 PLAN_MAP 当前阶段 {current_phase} 不一致",
        )
    if review.get("结论") and not review["结论"].startswith("通过"):
        readiness_issue(
            warnings,
            errors,
            strict,
            f"{plan_name}: 最新独立准入复核结论不是通过：{review['结论']}",
        )

    history = [row for row in review_history_rows(plan_text) if len(row) >= 4 and row[2] == current_phase]
    if not history:
        history_hint = structural_heading_hint(plan_text, "独立复核记录")
        readiness_issue(
            warnings,
            errors,
            strict,
            f"{plan_name}: 独立复核记录缺少当前阶段 {current_phase} 的记录{history_hint}",
        )
    else:
        latest_history = history[-1]
        if review.get("日期") and latest_history[0] != review["日期"]:
            readiness_issue(
                warnings,
                errors,
                strict,
                f"{plan_name}: 最新独立准入复核日期与历史记录最后一条不一致",
            )
        if review.get("结论") and latest_history[3] not in review["结论"]:
            readiness_issue(
                warnings,
                errors,
                strict,
                f"{plan_name}: 最新独立准入复核与历史记录最后一条结论冲突",
            )


def markdown_list_items(section):
    if section is None:
        return []
    items = []
    for line in section.splitlines():
        match = re.match(r"\s*[-*]\s+(.+?)\s*$", line)
        if not match:
            continue
        item = match.group(1).strip()
        item = item.strip("` ")
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


def extract_plan_link(cell):
    match = re.search(r"\((plans/[^)]+\.md)\)", cell)
    if match:
        return match.group(1)
    if cell.endswith(".md") and cell.startswith("plans/"):
        return cell
    return None


def extract_declared_dependencies(depends_cell):
    return [d.strip("` ") for d in re.split(r",|<br>|、", depends_cell) if d.strip("` -")]


def parse_plan_date(value):
    return datetime.strptime(value.strip(), "%Y-%m-%d").date()


def extract_affected_targets(plan_text):
    section = markdown_section(plan_text, ["影响模块或文件"])
    targets = []
    for item in markdown_list_items(section):
        target = extract_scope_token(item)
        if target and target not in PLACEHOLDER_VALUES:
            targets.append(target)
    return targets


def extract_plan_references(plan_text, known_plans, current_name):
    references = set()
    for match in re.finditer(r"\[\[([^\]]+)\]\]", plan_text):
        name = Path(match.group(1).strip()).stem
        if name in known_plans and name != current_name:
            references.add(name)

    for match in re.finditer(r"(?:docs/)?plans/([A-Za-z0-9\u4e00-\u9fff._-]+)\.md", plan_text):
        name = Path(match.group(1).strip()).stem
        if name in known_plans and name != current_name:
            references.add(name)

    for match in re.finditer(r"\]\(([A-Za-z0-9\u4e00-\u9fff._-]+)\.md(?:#[^)]+)?\)", plan_text):
        name = Path(match.group(1).strip()).stem
        if name in known_plans and name != current_name:
            references.add(name)

    return references


def has_substantive_evidence(content):
    if content is None:
        return False

    stripped = content.strip()
    if not stripped:
        return False
    if re.search(r"^(待补充|TODO|TBD|待确认)[。.\s]*$", stripped, re.IGNORECASE):
        return False

    evidence_patterns = [
        r"```",
        r"\b(python3|python|pytest|bash|sh|rg|npm|make|curl|git)\b",
        r"[\w./-]+/(?:[\w./-]+)",
        r"\b(?:commit|hash)\s+[0-9a-f]{6,40}\b",
        r"\bv?\d+\.\d+(?:\.\d+)?\b",
        r"\d+(?:\.\d+)?%",
        r"(基线|复现|样本|fixture|测试|验证|运行|失败案例|现状|快照|报告|覆盖率|命令|搜索)",
    ]
    if any(re.search(pattern, stripped, re.IGNORECASE) for pattern in evidence_patterns):
        return True

    normalized = re.sub(r"\s+", "", stripped)
    return len(normalized) >= 40


def has_completion_evidence(plan_text):
    evidence = markdown_section(plan_text, ["Step 0 Evidence", "Step 0 证据", "完成证据", "验证证据"])
    validation = markdown_section(plan_text, ["验证方式", "验证"])
    return has_substantive_evidence(evidence) and has_substantive_evidence(validation)


def has_coverage_evidence(plan_text):
    """已完成计划是否包含非占位的测试覆盖率证据章节。"""
    section = markdown_section(plan_text, ["测试覆盖率", "测试覆盖", "覆盖率报告", "Coverage", "Test Coverage"])
    if section is None:
        return False
    content = section.strip()
    if not content or re.search(r"^(待补充|TODO|TBD)[。.\s]*$", content, re.IGNORECASE):
        return False

    return bool(re.search(r"(\d+(?:\.\d+)?%|pytest|coverage|覆盖率|测试通过|passed)", content, re.IGNORECASE))


def has_current_blocker(plan_text):
    for row in table_rows(plan_text, "未决问题"):
        joined = "|".join(row)
        if re.search(r"\b(Yes|是)\b", joined) and re.search(r"(Open|待确认|未解决|待处理|未决定)", joined, re.IGNORECASE):
            return True
    return False


def find_orphan_plans(docs, plans):
    plans_dir = docs / "plans"
    if not plans_dir.exists():
        return []
    indexed_paths = {data["path"].resolve() for data in plans.values()}
    return sorted(
        plan_file
        for plan_file in plans_dir.glob("*.md")
        if plan_file.resolve() not in indexed_paths
    )


def detect_overlapping_targets(active_plan_targets):
    target_to_plans = {}
    for plan_name, targets in active_plan_targets.items():
        for target in targets:
            target_to_plans.setdefault(target, []).append(plan_name)
    return {
        target: sorted(plan_names)
        for target, plan_names in target_to_plans.items()
        if len(plan_names) > 1
    }


def target_matches_path(target, changed_file):
    normalized_target = normalize_scope_path(target)
    normalized_file = normalize_scope_path(changed_file)
    if not normalized_target or not normalized_file:
        return False
    if normalized_target == normalized_file:
        return True
    return normalized_file.startswith(f"{normalized_target}/")


def uncovered_changed_files(changed_files, active_plan_targets):
    targets = [
        target
        for targets_for_plan in active_plan_targets.values()
        for target in targets_for_plan
    ]
    return sorted(
        changed_file
        for changed_file in changed_files
        if not any(target_matches_path(target, changed_file) for target in targets)
    )


def git_name_only(root, git_args):
    result = subprocess.run(
        ["git", *git_args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return {
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip()
    }


def changed_files(root, staged=False):
    if staged:
        return git_name_only(root, ["diff", "--cached", "--name-only", "--diff-filter=ACMR"])

    files = set()
    files.update(git_name_only(root, ["diff", "--name-only", "--diff-filter=ACMR"]))
    files.update(git_name_only(root, ["diff", "--cached", "--name-only", "--diff-filter=ACMR"]))
    files.update(git_name_only(root, ["ls-files", "--others", "--exclude-standard"]))
    return files


def warn_uncovered_changes(warnings, mode, files, active_plan_targets):
    if not files:
        return
    if not active_plan_targets:
        warn(warnings, f"{mode}: 存在变更文件，但没有活跃计划声明影响范围")
        return
    for changed_file in uncovered_changed_files(files, active_plan_targets):
        warn(warnings, f"{mode}: 变更文件未被活跃计划影响范围覆盖：{changed_file}")


def warn_stale_plans(warnings, plans, stale_days, today=None):
    today = today or date.today()
    for name, data in plans.items():
        if data["status"] not in WARNING_ACTIVE:
            continue
        age = (today - data["last_updated_date"]).days
        if age > stale_days:
            warn(
                warnings,
                f"{name}: 活跃计划已 {age} 天未更新，超过 --stale-days {stale_days} 阈值",
            )


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative_to_root(path, root):
    return path.relative_to(root).as_posix()


def create_attestation(root, plan_map, plans, plan_name, errors):
    data = plans.get(plan_name)
    if data is None:
        fail(errors, f"{plan_name}: 未登记计划，无法创建完成快照")
        return None
    if not data["path"].exists():
        fail(errors, f"{plan_name}: 计划文件不存在，无法创建完成快照")
        return None

    attestation = {
        "plan": plan_name,
        "phase": data["phase"],
        "status": data["status"],
        "plan_path": relative_to_root(data["path"], root),
        "plan_map_path": relative_to_root(plan_map, root),
        "plan_sha256": sha256_file(data["path"]),
        "plan_map_sha256": sha256_file(plan_map),
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "created_by": "plan-governance",
        "reason": "阶段完成快照",
    }
    target = root / "docs" / "attestations" / f"{plan_name}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(attestation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def warn_attestation_drift(warnings, root, plans):
    attestations_dir = root / "docs" / "attestations"
    if not attestations_dir.exists():
        return

    for path in sorted(attestations_dir.glob("*.json")):
        try:
            attestation = json.loads(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            warn(warnings, f"{path}: attestation JSON 无法解析：{exc}")
            continue

        plan_name = str(attestation.get("plan", "")).strip()
        if not plan_name or plan_name not in plans:
            warn(warnings, f"{path}: 快照引用了未登记计划：{plan_name or '<missing>'}")
            continue

        plan_path = root / str(attestation.get("plan_path", ""))
        plan_map_path = root / str(attestation.get("plan_map_path", "docs/PLAN_MAP.md"))
        if not plan_path.exists():
            warn(warnings, f"{path}: 快照引用的计划文件不存在：{plan_path}")
            continue
        if not plan_map_path.exists():
            warn(warnings, f"{path}: 快照引用的 PLAN_MAP.md 不存在：{plan_map_path}")
            continue

        if sha256_file(plan_path) != attestation.get("plan_sha256"):
            warn(warnings, f"{path}: {plan_name} 计划文件 hash 已变化，需要人工复核")
        if sha256_file(plan_map_path) != attestation.get("plan_map_sha256"):
            warn(warnings, f"{path}: PLAN_MAP.md hash 已变化，需要人工复核")


def detect_dependency_cycles(edges):
    visited = set()
    stack = set()
    cycles = []

    def visit(node, path):
        if node in stack:
            cycles.append(" -> ".join(path + [node]))
            return
        if node in visited:
            return
        visited.add(node)
        stack.add(node)
        for dep in edges.get(node, []):
            visit(dep, path + [node])
        stack.remove(node)

    for node in edges:
        visit(node, [])
    return cycles


def load_plan_records(root, errors):
    """读取计划索引，供只读工作集和步骤校验入口复用。"""
    docs = root / "docs"
    plan_map = docs / "PLAN_MAP.md"
    if not plan_map.exists():
        fail(errors, "未找到 docs/PLAN_MAP.md；当前仓库尚未初始化计划治理")
        return "", plan_map, {}

    plan_map_text = read_utf8(plan_map, errors)
    plans = {}
    for row in table_rows(plan_map_text, "计划索引"):
        if len(row) < 6:
            continue
        link = extract_plan_link(row[0])
        if not link:
            continue
        name = Path(link).stem
        plans[name] = {
            "path": docs / link,
            "status": row[1].strip("` "),
            "phase": row[2].strip("` "),
            "depends": row[4],
        }
    if not plans:
        fail(errors, "docs/PLAN_MAP.md: 缺少可读取的计划索引")
    return plan_map_text, plan_map, plans


def plan_index_issues(plan_map_text):
    """检查工作集入口依赖的计划索引结构，不改变既有基础检查语义。"""
    issues = []
    seen = set()
    for row_index, row in enumerate(table_rows(plan_map_text, "计划索引"), start=1):
        if len(row) < 6:
            issues.append(f"计划索引第 {row_index} 行字段不足，无法安全派生工作集")
            continue
        link = extract_plan_link(row[0])
        if not link:
            issues.append(f"计划索引第 {row_index} 行缺少计划链接，无法安全派生工作集")
            continue
        name = Path(link).stem
        if name in seen:
            issues.append(f"计划索引存在重复计划 ID：{name}")
        seen.add(name)
        status = row[1].strip("` ")
        if status not in VALID_STATUSES:
            issues.append(f"{name}: 计划状态非法：{status}")
    return issues


def unresolved_current_blockers(plan_text):
    blockers = []
    for row in table_rows(plan_text, "未决问题"):
        if len(row) < 4 or not re.search(r"\b(Yes|是)\b", row[2]):
            continue
        state = row[3].strip()
        if state in {"已决定", "已收敛", "已完成", "无"}:
            continue
        blockers.append(row[0].strip() or "未命名阻塞项")
    return blockers


def top_level_section(text, heading):
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return None
    tail = text[match.end():]
    next_heading = re.search(r"^##\s+", tail, re.MULTILINE)
    return tail[: next_heading.start()] if next_heading else tail


def current_summary(plan_text):
    return key_value_table(markdown_section(top_level_section(plan_text, "当前阶段"), ["阶段准入摘要"]))


def current_review_passes(plan_text, phase):
    review = key_value_table(markdown_section(plan_text, ["最新独立准入复核"]))
    return review.get("阶段") == phase and review.get("结论", "").startswith("通过")


def structured_next_action(plan_text):
    section = top_level_section(plan_text, "当前阶段") or ""
    values = key_value_table(section)
    value = values.get("下一动作", "").strip()
    if not value:
        match = re.search(r"(?:^|\n)\s*下一动作\s*[：:]\s*([^\n]+)", section)
        value = match.group(1).strip() if match else ""
    mapping = {
        "验证": "verify",
        "verify": "verify",
        "同步": "sync",
        "sync": "sync",
        "实施": "implement",
        "implement": "implement",
        "无": "none",
        "none": "none",
    }
    if not value:
        return {"state": "unknown", "kind": "unknown", "reason": "缺少结构化下一动作"}
    kind = mapping.get(value.lower(), "unknown")
    if kind == "unknown":
        return {"state": "unknown", "kind": "unknown", "reason": f"下一动作值无法识别：{value}"}
    return {"state": "known", "kind": kind, "reason": "来自当前阶段结构化下一动作"}


def parallel_summary(plan_map_text, plan_name, relation_valid=True):
    if not relation_valid:
        return {
            "state": "unknown",
            "peers": [],
            "reason": "阶段关系存在结构错误，不能派生确定并行关系",
        }
    rows = table_rows(plan_map_text, "阶段关系")
    peers = []
    evidence = []
    for row in rows:
        if len(row) < 7 or row[0] == "来源计划":
            continue
        source, target = row[0].strip("` "), row[2].strip("` ")
        if plan_name not in {source, target}:
            continue
        peer = target if source == plan_name else source
        if peer and peer != plan_name and peer not in peers:
            peers.append(peer)
        if row[6] and row[6] not in evidence:
            evidence.append(row[6])
    if not rows or not peers:
        return {"state": "unknown", "peers": [], "reason": "缺少当前计划的直接阶段关系证据"}
    return {
        "state": "known",
        "peers": peers,
        "reason": "只读透传阶段关系表中的直接关系；完整关系校验由后续阶段负责",
        "evidence": evidence,
    }


RELATION_COLUMNS = ["来源计划", "来源阶段", "目标计划", "目标阶段", "关系类型", "解除条件", "证据"]
RELATION_TYPES = {"hard_gate", "evidence", "soft_context"}
SHARED_WRITE_COLUMNS = [
    "来源计划",
    "来源阶段",
    "目标计划",
    "目标阶段",
    "约束类型",
    "共享目标",
    "串行顺序",
    "解除条件",
    "证据",
]


def relation_rows(plan_map_text):
    section = markdown_section(plan_map_text, ["阶段关系"])
    if section is None:
        return None, []
    rows = markdown_table_rows(section)
    header_index = next((index for index, row in enumerate(rows) if row[: len(RELATION_COLUMNS)] == RELATION_COLUMNS), None)
    if header_index is None:
        return [], []
    return RELATION_COLUMNS, rows[header_index + 1 :]


def shared_write_rows(plan_map_text):
    section = markdown_section(plan_map_text, ["机器可检查共享写入约束"])
    if section is None:
        return None, []
    rows = markdown_table_rows(section)
    header_index = next(
        (index for index, row in enumerate(rows) if row[: len(SHARED_WRITE_COLUMNS)] == SHARED_WRITE_COLUMNS),
        None,
    )
    if header_index is None:
        return [], []
    return SHARED_WRITE_COLUMNS, rows[header_index + 1 :]


def clean_relation_value(value):
    return (value or "").strip().strip("`").strip()


def valid_phase_name(value):
    return bool(re.fullmatch(r"阶段\s*[0-9][0-9]*", clean_relation_value(value)))


def declared_plan_phases(plan_data):
    path = plan_data.get("path") if plan_data else None
    if not path or not path.exists():
        return set()
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return set()
    return {
        clean_relation_value(row[0])
        for row in phase_roadmap_rows(text)
        if row and clean_relation_value(row[0])
    }


def validate_relation_evidence(evidence, plans, row_label):
    """仅校验 Markdown 链接形式的相对证据路径；纯文本运行记录保持兼容。"""
    if not evidence or not plans:
        return []
    docs_root = next(iter(plans.values()))["path"].parent.parent
    errors = []
    for match in re.finditer(r"\]\(([^)#]+)(?:#[^)]+)?\)", evidence):
        target = match.group(1).strip()
        if not target or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", target):
            continue
        candidate = (docs_root / target).resolve()
        if not candidate.exists():
            errors.append(f"PLAN_MAP.md: {row_label} 证据链接不存在：{target}")
    return errors


def validate_relation_graph(plan_map_text, plans):
    """校验阶段关系和可选机器共享写入约束；不校验业务完成结论。"""
    errors = []
    warnings = []
    headers, rows = relation_rows(plan_map_text)
    if headers is None:
        relation_defined = False
    elif not headers:
        errors.append("PLAN_MAP.md: `阶段关系` 缺少固定七列表头")
        relation_defined = True
    else:
        relation_defined = True

    gate_pairs = set()
    relation_graph = {}
    phase_cache = {name: declared_plan_phases(data) for name, data in plans.items()}
    if headers:
        for row_index, row in enumerate(rows, start=1):
            if not any(clean_relation_value(cell) for cell in row):
                continue
            if len(row) != len(RELATION_COLUMNS):
                errors.append(f"PLAN_MAP.md: 阶段关系第 {row_index} 行字段数应为 {len(RELATION_COLUMNS)}")
                continue
            values = [clean_relation_value(cell) for cell in row]
            source, source_phase, target, target_phase, relation_type, unlock, evidence = values
            for label, value in [
                ("来源计划", source),
                ("来源阶段", source_phase),
                ("目标计划", target),
                ("目标阶段", target_phase),
                ("关系类型", relation_type),
                ("证据", evidence),
            ]:
                if not value or is_placeholder(value):
                    errors.append(f"PLAN_MAP.md: 阶段关系第 {row_index} 行缺少有效{label}")
            if source not in plans:
                errors.append(f"PLAN_MAP.md: 阶段关系第 {row_index} 行来源计划不存在：{source}")
            if target not in plans:
                errors.append(f"PLAN_MAP.md: 阶段关系第 {row_index} 行目标计划不存在：{target}")
            if not valid_phase_name(source_phase):
                errors.append(f"PLAN_MAP.md: 阶段关系第 {row_index} 行来源阶段格式非法：{source_phase}")
            if not valid_phase_name(target_phase):
                errors.append(f"PLAN_MAP.md: 阶段关系第 {row_index} 行目标阶段格式非法：{target_phase}")
            if source in plans and valid_phase_name(source_phase):
                declared = phase_cache.get(source, set())
                if declared and source_phase not in declared:
                    errors.append(f"PLAN_MAP.md: 阶段关系第 {row_index} 行来源阶段不存在于计划路线图：{source_phase}")
            if target in plans and valid_phase_name(target_phase):
                declared = phase_cache.get(target, set())
                if declared and target_phase not in declared:
                    errors.append(f"PLAN_MAP.md: 阶段关系第 {row_index} 行目标阶段不存在于计划路线图：{target_phase}")
            if relation_type not in RELATION_TYPES:
                errors.append(f"PLAN_MAP.md: 阶段关系第 {row_index} 行关系类型非法：{relation_type}")
            elif relation_type != "soft_context" and (not unlock or is_placeholder(unlock)):
                errors.append(f"PLAN_MAP.md: 阶段关系第 {row_index} 行缺少有效解除条件")
            errors.extend(validate_relation_evidence(evidence, plans, f"阶段关系第 {row_index} 行"))
            if source == target and source_phase == target_phase:
                errors.append(f"PLAN_MAP.md: 阶段关系第 {row_index} 行不能引用自身同一阶段：{source}")
            if source not in plans or target not in plans or relation_type not in RELATION_TYPES:
                continue
            source_node = f"{source}@{source_phase}"
            target_node = f"{target}@{target_phase}"
            relation_graph.setdefault(source_node, [])
            relation_graph.setdefault(target_node, [])
            if relation_type in {"hard_gate", "evidence"}:
                relation_graph[source_node].append(target_node)
            if relation_type == "hard_gate":
                gate_pairs.add((source, target))

        for cycle in detect_dependency_cycles(relation_graph):
            errors.append(f"PLAN_MAP.md: 阶段关系存在 hard_gate/evidence 环依赖：{cycle}")

        for source, target in sorted(gate_pairs):
            declared = extract_declared_dependencies(plans[target].get("depends", ""))
            if source not in declared:
                warnings.append(
                    f"PLAN_MAP.md: 阶段关系 {source} -> {target} 为 hard_gate，但计划索引依赖列未包含 {source}；以阶段关系为准"
                )

    shared_headers, shared_rows = shared_write_rows(plan_map_text)
    if shared_headers == []:
        errors.append("PLAN_MAP.md: `机器可检查共享写入约束` 缺少固定九列表头")
    elif shared_headers:
        for row_index, row in enumerate(shared_rows, start=1):
            if not any(clean_relation_value(cell) for cell in row):
                continue
            if len(row) != len(SHARED_WRITE_COLUMNS):
                errors.append(f"PLAN_MAP.md: 共享写入约束第 {row_index} 行字段数应为 {len(SHARED_WRITE_COLUMNS)}")
                continue
            values = [clean_relation_value(cell) for cell in row]
            source, source_phase, target, target_phase, constraint, target_paths, order, unlock, evidence = values
            for label, value in [
                ("来源计划", source),
                ("来源阶段", source_phase),
                ("目标计划", target),
                ("目标阶段", target_phase),
                ("约束类型", constraint),
                ("共享目标", target_paths),
                ("串行顺序", order),
                ("解除条件", unlock),
                ("证据", evidence),
            ]:
                if not value or is_placeholder(value):
                    errors.append(f"PLAN_MAP.md: 共享写入约束第 {row_index} 行缺少有效{label}")
            if source not in plans:
                errors.append(f"PLAN_MAP.md: 共享写入约束第 {row_index} 行来源计划不存在：{source}")
            if target not in plans:
                errors.append(f"PLAN_MAP.md: 共享写入约束第 {row_index} 行目标计划不存在：{target}")
            if not valid_phase_name(source_phase):
                errors.append(f"PLAN_MAP.md: 共享写入约束第 {row_index} 行来源阶段格式非法：{source_phase}")
            if not valid_phase_name(target_phase):
                errors.append(f"PLAN_MAP.md: 共享写入约束第 {row_index} 行目标阶段格式非法：{target_phase}")
            if constraint != "shared_write_risk":
                errors.append(f"PLAN_MAP.md: 共享写入约束第 {row_index} 行约束类型非法：{constraint}")
            errors.extend(validate_relation_evidence(evidence, plans, f"共享写入约束第 {row_index} 行"))
            expected_order = f"{source}-before-{target}"
            if source and target and order != expected_order:
                errors.append(
                    f"PLAN_MAP.md: 共享写入约束第 {row_index} 行串行顺序应为 {expected_order}：{order}"
                )

    return errors, warnings


def recent_evidence(plan_text):
    current = top_level_section(plan_text, "当前阶段") or ""
    section = markdown_section(current, ["最近实施/验证记录"])
    rows = markdown_table_rows(section)
    return [row for row in rows if len(row) >= 2 and row[0] not in {"日期", "字段", "类型"}]


def workset_payload(root, include_history=False, strict=False):
    errors = []
    strict_failures = []
    plan_map_text, _, plans = load_plan_records(root, errors)
    output = {
        "schema_version": 1,
        "source": "derived",
        "plans": [],
        "warnings": [],
    }
    if errors:
        output["warnings"] = errors
        return output, 1

    index_issues = plan_index_issues(plan_map_text)
    relation_errors, relation_warnings = validate_relation_graph(plan_map_text, plans)
    output["warnings"].extend(relation_warnings)
    if relation_errors:
        output["warnings"].extend(relation_errors)
        strict_failures.extend(relation_errors)

    for name, data in plans.items():
        if not include_history and data["status"] not in WARNING_ACTIVE:
            continue
        path = data["path"]
        if not path.exists():
            message = f"{name}: 计划文件不存在：{path}"
            output["warnings"].append(message)
            strict_failures.append(message)
            continue
        plan_text = read_utf8(path, errors)
        summary = current_summary(plan_text)
        blockers = unresolved_current_blockers(plan_text)
        if blockers:
            readiness = "blocked"
            action = {
                "state": "known",
                "kind": "resolve_blocker",
                "reason": "当前阶段存在未解决阻塞项",
            }
        elif data["status"] == "待实施":
            readiness = "ready"
            action = {"state": "known", "kind": "implement", "reason": "计划状态为待实施"}
        elif data["status"] == "实施中":
            readiness = "in_progress"
            action = structured_next_action(plan_text)
        elif data["status"] in {"候选", "设计中"}:
            missing = [
                field for field in ["Step 0", "样本矩阵", "验证方式", "失败/回滚边界"]
                if not summary.get(field) or is_placeholder(summary.get(field))
            ]
            if missing:
                readiness = "design"
                action = {
                    "state": "known",
                    "kind": "complete_step0",
                    "reason": f"阶段准入摘要缺少或占位字段：{', '.join(missing)}",
                }
            elif not current_review_passes(plan_text, data["phase"]):
                readiness = "design"
                action = {
                    "state": "known",
                    "kind": "independent_review",
                    "reason": "当前阶段尚无通过的最新独立准入复核",
                }
            else:
                readiness = "design"
                action = {"state": "unknown", "kind": "unknown", "reason": "缺少结构化下一动作"}
        else:
            readiness = "unknown"
            action = {"state": "unknown", "kind": "unknown", "reason": "计划状态不在工作集派生范围"}

        output["plans"].append(
            {
                "plan": name,
                "status": data["status"],
                "phase": data["phase"],
                "readiness": readiness,
                "blockers": blockers,
                "next_action": action,
                "parallel": parallel_summary(plan_map_text, name, relation_valid=not relation_errors),
                "recent_evidence": recent_evidence(plan_text),
            }
        )

    if errors:
        output["warnings"].extend(errors)
        strict_failures.extend(errors)
    if index_issues:
        output["plans"] = []
        output["warnings"].extend(index_issues)
        strict_failures.extend(index_issues)
    return output, 1 if strict and strict_failures else 0


def print_workset_text(payload, strict=False):
    print("工作集（只读派生）")
    for item in payload["plans"]:
        action = item["next_action"]
        parallel = item["parallel"]
        print(
            f"- {item['plan']} | {item['status']} | {item['phase']} | "
            f"{item['readiness']} | next={action['kind']} | "
            f"parallel={parallel['state']}"
        )
        if item["blockers"]:
            print(f"  blockers: {'；'.join(item['blockers'])}")
    for warning in payload["warnings"]:
        print(f"{'ERROR' if strict else 'WARNING'}: {warning}")


STEP_COLUMNS = ["步骤 ID", "前置步骤", "动作", "证据", "完成条件", "状态", "分支记录"]
STEP_STATES = {"未开始", "执行中", "已完成", "阻塞", "不适用"}


def split_prerequisites(value):
    if not value or value.strip("` -") == "":
        return []
    return [item for item in re.split(r"[,，、\s]+", value.strip("` ")) if item and item != "-"]


def branch_record_has_value(branch_record, marker):
    match = re.search(rf"{re.escape(marker)}\s*[：:]\s*([^；;,，\n]+)", branch_record)
    return bool(match and not is_placeholder(match.group(1).strip()))


def find_execution_rows(plan_text):
    section = markdown_section(plan_text, ["执行清单"])
    if section is None:
        return None, []
    rows = markdown_table_rows(section)
    header_index = next((index for index, row in enumerate(rows) if row[: len(STEP_COLUMNS)] == STEP_COLUMNS), None)
    if header_index is None:
        return [], []
    return STEP_COLUMNS, rows[header_index + 1 :]


def validate_step_plan(root, plan_name, strict=False):
    errors = []
    _, _, plans = load_plan_records(root, errors)
    if errors:
        payload = {
            "schema_version": 1,
            "plan": plan_name,
            "phase": "",
            "enabled": False,
            "status": "invalid",
            "steps": [],
            "errors": errors,
            "warnings": [],
        }
        return payload, 1

    data = plans.get(plan_name)
    if data is None or not data["path"].exists():
        payload = {
            "schema_version": 1,
            "plan": plan_name,
            "phase": data["phase"] if data else "",
            "enabled": False,
            "status": "invalid",
            "steps": [],
            "errors": [f"{plan_name}: 未登记计划或计划文件不存在"],
            "warnings": [],
        }
        return payload, 1

    plan_errors = []
    plan_text = read_utf8(data["path"], plan_errors)
    if plan_errors:
        return {
            "schema_version": 1,
            "plan": plan_name,
            "phase": data["phase"],
            "enabled": False,
            "status": "invalid",
            "steps": [],
            "errors": plan_errors,
            "warnings": [],
        }, 1
    parse_text = mask_fenced_code(plan_text)
    if not re.search(r"^\s*execution_mode\s*:\s*autonomous-continuous\s*$", parse_text, re.MULTILINE):
        return {
            "schema_version": 1,
            "plan": plan_name,
            "phase": data["phase"],
            "enabled": False,
            "status": "not_enabled",
            "steps": [],
            "errors": [],
            "warnings": [],
        }, 0

    errors = []
    policy_match = re.search(r"^\s*execution_policy\s*:\s*(\S+)\s*$", parse_text, re.MULTILINE)
    policy = policy_match.group(1).strip("`") if policy_match else "serial"
    if policy not in {"serial", "parallel"}:
        errors.append(f"{plan_name}: 字段 execution_policy 值非法：{policy}")

    headers, rows = find_execution_rows(plan_text)
    if headers is None:
        errors.append(f"{plan_name}: 缺少 `### 执行清单` 章节")
        rows = []
    elif not headers:
        errors.append(f"{plan_name}: 执行清单缺少固定七列表头")
    elif not rows:
        errors.append(f"{plan_name}: 执行清单至少需要一个步骤")

    steps = []
    ids = set()
    dependencies = {}
    for row_index, row in enumerate(rows, start=1):
        if len(row) < len(STEP_COLUMNS):
            errors.append(f"{plan_name}: 执行清单第 {row_index} 行字段不足")
            continue
        step = dict(zip(STEP_COLUMNS, row[: len(STEP_COLUMNS)]))
        step_id = step["步骤 ID"].strip("` ")
        if not step_id:
            errors.append(f"{plan_name}: 执行清单第 {row_index} 行缺少步骤 ID")
            continue
        if step_id in ids:
            errors.append(f"{plan_name}: 步骤 {step_id} 重复")
        ids.add(step_id)
        dependencies[step_id] = split_prerequisites(step["前置步骤"])
        for field in ["动作", "证据", "完成条件"]:
            if not step[field].strip("` ") or is_placeholder(step[field]):
                errors.append(f"{plan_name}: 步骤 {step_id} 缺少字段 {field}")
        state = step["状态"].strip("` ")
        if state not in STEP_STATES:
            errors.append(f"{plan_name}: 步骤 {step_id} 状态非法：{state}")
        if state == "不适用":
            branch_record = step["分支记录"].strip("` ")
            if is_placeholder(branch_record):
                errors.append(f"{plan_name}: 步骤 {step_id} 为不适用但缺少分支记录")
            else:
                for marker in ["触发条件", "理由", "替代证据"]:
                    if not branch_record_has_value(branch_record, marker):
                        errors.append(f"{plan_name}: 步骤 {step_id} 的不适用分支记录缺少有效{marker}")
        if state in {"已完成", "不适用"} and is_placeholder(step["证据"]):
            errors.append(f"{plan_name}: 步骤 {step_id} 为 {state} 但缺少证据")
        steps.append(
            {
                "id": step_id,
                "preconditions": dependencies[step_id],
                "action": step["动作"],
                "evidence": step["证据"],
                "completion": step["完成条件"],
                "state": state,
                "branch_record": step["分支记录"],
            }
        )

    for step_id, prerequisites in dependencies.items():
        for prerequisite in prerequisites:
            if prerequisite not in ids:
                errors.append(f"{plan_name}: 步骤 {step_id} 引用了未知前置步骤 {prerequisite}")

    graph = {step_id: [item for item in prerequisites if item in ids] for step_id, prerequisites in dependencies.items()}
    errors.extend(f"{plan_name}: 执行清单存在环依赖：{cycle}" for cycle in detect_dependency_cycles(graph))
    status = "invalid" if errors else "valid"
    warnings = list(errors) if errors and not strict else []
    return {
        "schema_version": 1,
        "plan": plan_name,
        "phase": data["phase"],
        "enabled": True,
        "status": status,
        "execution_policy": policy,
        "steps": steps if not errors else [],
        "errors": errors,
        "warnings": warnings,
    }, 1 if errors and strict else 0


def run_workset(root, as_json=False, include_history=False, strict=False):
    payload, status = workset_payload(root, include_history=include_history, strict=strict)
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_workset_text(payload, strict=strict)
    return status


def run_validate_steps(root, plan_name, as_json=False, strict=False):
    payload, status = validate_step_plan(root, plan_name, strict=strict)
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"步骤校验：{payload['plan']} | {payload['phase']} | {payload['status']}")
        for error in payload["errors"]:
            print(f"{'ERROR' if strict else 'WARNING'}: {error}")
        for warning in payload["warnings"]:
            if warning not in payload["errors"]:
                print(f"WARNING: {warning}")
    return status


def parse_args(argv):
    parser = argparse.ArgumentParser(description="检查计划治理文档的一致性。")
    parser.add_argument("root", nargs="?", default=".", help="仓库根目录，默认当前目录。")
    parser.add_argument("--workset", action="store_true", help="输出只读当前工作集。")
    parser.add_argument("--validate-steps", action="store_true", help="只读校验指定计划的自主执行步骤表。")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出工作集或步骤校验结果。")
    parser.add_argument("--include-history", action="store_true", help="工作集包含历史计划。")
    parser.add_argument("--root", dest="mode_root", help="工作集/步骤校验的仓库根目录。")
    parser.add_argument("--drift", action="store_true", help="检查工作区变更是否被活跃计划影响范围覆盖。")
    parser.add_argument("--pre-commit", action="store_true", help="检查 staged 变更是否被活跃计划影响范围覆盖。")
    parser.add_argument(
        "--strict-readiness",
        action="store_true",
        help="将待实施/实施中计划的阶段准入结构缺陷从 WARNING 提升为 ERROR。",
    )
    parser.add_argument("--attest", metavar="PLAN", help="为已登记计划创建或覆盖完成快照。")
    parser.add_argument("--check-attestations", action="store_true", help="检查完成快照 hash 是否漂移。")
    parser.add_argument(
        "--stale-days",
        nargs="?",
        const=10,
        type=int,
        default=None,
        help="检查活跃计划是否超过 N 天未更新；省略 N 时默认 10 天。",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.workset:
        return run_workset(
            Path(args.mode_root or args.root),
            as_json=args.json,
            include_history=args.include_history,
            strict=args.strict_readiness,
        )
    if args.validate_steps:
        return run_validate_steps(
            Path(args.mode_root or "."),
            args.root,
            as_json=args.json,
            strict=args.strict_readiness,
        )
    root = Path(args.root)
    docs = root / "docs"
    plan_map = docs / "PLAN_MAP.md"
    errors = []
    warnings = []

    if not plan_map.exists():
        print("未找到 docs/PLAN_MAP.md；当前仓库尚未初始化计划治理。")
        return 0

    text = read_utf8(plan_map, errors)
    plan_rows = table_rows(text, "计划索引")
    if not plan_rows:
        fail(errors, "docs/PLAN_MAP.md: 缺少计划索引表")

    plans = {}
    for row in plan_rows:
        if len(row) < 2:
            continue
        if len(row) < 6:
            fail(errors, "docs/PLAN_MAP.md: 计划索引表必须包含 `最后更新` 列")
            continue
        link = extract_plan_link(row[0])
        name = Path(link).stem if link else row[0].strip("` ")
        status = row[1].strip("` ")
        last_updated = row[3].strip("` ")
        if status not in VALID_STATUSES:
            fail(errors, f"docs/PLAN_MAP.md: {name} 的状态不合法：{status}")
        try:
            last_updated_date = parse_plan_date(last_updated)
        except ValueError:
            fail(errors, f"docs/PLAN_MAP.md: {name} 的最后更新日期不合法：{last_updated}")
            last_updated_date = date.min
        if link:
            path = docs / link
            if not path.exists():
                fail(errors, f"docs/PLAN_MAP.md: 引用的计划文件不存在：{link}")
            plans[name] = {
                "path": path,
                "status": status,
                "phase": row[2].strip("` "),
                "last_updated_date": last_updated_date,
                "depends": row[4],
            }
        else:
            fail(errors, f"docs/PLAN_MAP.md: 计划行缺少 docs/plans 链接：{row[0]}")

    relation_errors, relation_warnings = validate_relation_graph(text, plans)
    warnings.extend(relation_warnings)
    if args.strict_readiness:
        errors.extend(relation_errors)
    else:
        warnings.extend(relation_errors)

    edges = {}
    inactive = {name for name, data in plans.items() if data["status"] in INACTIVE}
    for name, data in plans.items():
        deps = extract_declared_dependencies(data["depends"])
        edges[name] = [dep for dep in deps if dep in plans]
        if data["status"] in IMPLEMENTING:
            for dep in edges[name]:
                if dep in inactive:
                    fail(errors, f"{name}: 实施中计划依赖了非活跃计划 {dep}")

    for cycle in detect_dependency_cycles(edges):
        fail(errors, f"计划依赖存在环：{cycle}")

    for orphan in find_orphan_plans(docs, plans):
        warn(warnings, f"{orphan}: docs/plans 中存在未登记到 PLAN_MAP.md 的孤立计划")

    active_plan_targets = {}
    plan_texts = {}
    for name, data in plans.items():
        plan_text = read_utf8(data["path"], errors)
        plan_texts[name] = plan_text
        if data["status"] in COMPLETED and not has_completion_evidence(plan_text):
            fail(errors, f"{data['path']}: 已完成计划缺少有效 Step 0 证据或验证方式")
        if data["status"] in COMPLETED and not has_coverage_evidence(plan_text):
            fail(errors, f"{data['path']}: 已完成计划缺少测试覆盖率证据")
        if data["status"] in ACTIVE and has_current_blocker(plan_text):
            fail(errors, f"{data['path']}: 活跃计划仍有未解决的当前阶段阻塞项")
        if data["status"] in WARNING_ACTIVE:
            active_plan_targets[name] = extract_affected_targets(plan_text)

        check_phase_readiness(
            text,
            name,
            data,
            plan_text,
            args.strict_readiness,
            warnings,
            errors,
        )

    for target, plan_names in detect_overlapping_targets(active_plan_targets).items():
        warn(warnings, f"{target}: 多个活跃计划声明相同影响目标：{', '.join(plan_names)}")

    known_plans = set(plans)
    for name, data in plans.items():
        if data["status"] not in WARNING_ACTIVE:
            continue
        declared = set(edges.get(name, []))
        referenced = extract_plan_references(plan_texts.get(name, ""), known_plans, name)
        for missing in sorted(referenced - declared):
            warn(warnings, f"{name}: 正文引用了计划 {missing}，但 PLAN_MAP.md 依赖列未声明")
        for unreferenced in sorted(declared - referenced):
            warn(warnings, f"{name}: PLAN_MAP.md 声明依赖 {unreferenced}，但计划正文未引用")

    try:
        if args.drift:
            warn_uncovered_changes(warnings, "--drift", changed_files(root), active_plan_targets)
        if args.pre_commit:
            warn_uncovered_changes(warnings, "--pre-commit", changed_files(root, staged=True), active_plan_targets)
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        warn(warnings, f"Git 变更检查不可用：{exc}")

    if args.stale_days is not None:
        if args.stale_days < 0:
            fail(errors, f"--stale-days 必须是非负整数：{args.stale_days}")
        else:
            warn_stale_plans(warnings, plans, args.stale_days)

    if args.check_attestations:
        warn_attestation_drift(warnings, root, plans)

    attested_path = None
    if args.attest:
        attested_path = create_attestation(root, plan_map, plans, args.attest, errors)

    for warning in warnings:
        print(f"WARNING: {warning}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    if attested_path is not None:
        print(f"已创建完成快照：{attested_path}")

    print("计划治理检查通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
