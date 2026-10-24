#!/usr/bin/env python3
import argparse
import hashlib
import json
import posixpath
import re
import secrets
import shlex
import stat
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
ATTESTATION_PURPOSES = {"phase_completion", "release_gate", "compliance"}
ATTESTATION_REVIEW_STATUSES = {"current", "superseded", "needs_review"}
ATTESTATION_SNAPSHOT_RE = re.compile(r"^\d{8}T\d{6}Z-[0-9a-f]{8}$")


# 与初始化器共用正文；单文件复制的检查器也能核对同版本入口。
def agent_rules_body():
    return """## 计划治理

处理已有计划或需要持续协调的工作时，读取实际发现的 `plan-governance` skill；开发或审查该 skill 自身时使用仓库源及对应 CLI。规范来源一次选定后复用，按当前动作读取同源 references。

只有 CLI 可用时，以 `plan-governance-cli guide` 为入口，再按需读取 `guide planning`、`guide verification` 或 `guide cli`。所需规则或能力不可用时说明缺口，不自动安装，不拼接不同版本。

- 按用户授权和当前计划范围推进；未解决问题如实保留，流程建议不扩大实施或外部操作授权。阶段准入、复核方式、验证与适用用户验收统一按所选规范的 verification 执行。
- 从 `docs/PLAN_MAP.md` 定位相关计划、当前阶段、依赖和证据，再按索引读取必要文档；恢复先核对当前事实与实际差异。文档职责、记录格式和状态同步统一按 planning 执行。
- 多计划/多会话并行时，在 check/workset/hook 中显式传入本会话的 `--plan ID`；必要前置、共享写入及写入前复核按 cli 执行，不设置全项目可变焦点。
- 完成时运行 `plan-governance-cli check .`；准入/发布使用 `--strict-readiness`。机械检查不替代实际验证和用户验收。
"""


def fail(errors, message):
    errors.append(message)


def warn(warnings, message):
    warnings.append(message)


def agent_rules_markers(text, begin="<!-- plan-governance:start -->", end="<!-- plan-governance:end -->"):
    """读取与更新共用边界；位置保留原换行字节，忽略代码围栏示例。"""
    visible = mask_fenced_code(text)
    starts = list(re.finditer(rf"^{re.escape(begin)}(?=[ \t]*\r?$)", visible, re.MULTILINE))
    ends = list(re.finditer(rf"^{re.escape(end)}(?=[ \t]*\r?$)", visible, re.MULTILINE))
    if not starts and not ends:
        return None
    if len(starts) != 1 or len(ends) != 1 or starts[0].end() >= ends[0].start():
        raise ValueError("AGENTS.md 治理受管标记缺失配对、重复或倒序；请先人工核对")
    return starts[0], ends[0]


def agent_rules_issue(root):
    """仅核对受管入口；返回项目级建议，不推断业务准入或自动覆盖。"""
    path = root / "AGENTS.md"
    try:
        info = path.lstat()
    except FileNotFoundError:
        return None
    except OSError:
        return "AGENT_RULES_UNAVAILABLE", "AGENTS.md 无法读取，未完成治理入口核对"
    if not stat.S_ISREG(info.st_mode):
        return "AGENT_RULES_UNAVAILABLE", "AGENTS.md 不是普通文件（含符号链接），未完成治理入口核对"
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return "AGENT_RULES_UNAVAILABLE", "AGENTS.md 无法读取为 UTF-8，未完成治理入口核对"
    try:
        markers = agent_rules_markers(text)
    except ValueError as exc:
        return "AGENT_RULES_INVALID", f"{exc}，未比较规则内容"
    if not markers:
        return None

    def normalized(value):
        return "\n".join(line.rstrip() for line in value.strip().splitlines())

    start, end = markers
    actual = text[start.end():end.start()]
    if normalized(actual) != normalized(agent_rules_body()):
        command = f"plan-governance-cli init --root {shlex.quote(str(root))} --update-agent-rules-only"
        return "AGENT_RULES_DRIFT", f"AGENTS.md 治理受管块与当前工具不同，可能过期或含定制；核对差异后可执行 `{command}`。不会自动覆盖"
    return None


def read_utf8(path, errors):
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        fail(errors, f"{path}: not valid UTF-8")
    except FileNotFoundError:
        fail(errors, f"{path}: file not found")
    except OSError as exc:
        fail(errors, f"{path}: cannot read file: {exc}")
    return ""


def table_rows(text, heading):
    text = mask_fenced_code(text)
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return []
    tail = text[match.end():]
    next_heading = re.search(r"^##\s+", tail, re.MULTILINE)
    section = tail[: next_heading.start()] if next_heading else tail
    return [cells for cells in markdown_table_rows(section) if cells[0] not in {"计划", "问题"}]


def mask_fenced_code(text):
    """用等长空格屏蔽 fenced code 中的伪 Markdown 标题，保留偏移量。"""
    masked = []
    fence = None
    for line in text.splitlines(keepends=True):
        stripped = line.lstrip()
        marker = re.match(r"(`{3,}|~{3,})", stripped)
        was_in_fence = fence is not None
        if marker:
            value = marker.group(1)
            if fence is None:
                fence = value
            elif value[0] == fence[0] and len(value) >= len(fence) and not stripped[len(value):].strip():
                fence = None
        if was_in_fence or fence is not None:
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
    next_heading = re.search(r"^#+\s+", mask_fenced_code(text)[match.end():], re.MULTILINE)
    return tail[: next_heading.start()] if next_heading else tail


def markdown_table_rows(section):
    if section is None:
        return []
    rows = []
    for line in mask_fenced_code(section).splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if cells and not all(re.fullmatch(r":?-+:?", cell) for cell in cells):
            rows.append(cells)
    return rows


def key_value_table(section):
    values = {}
    for row in markdown_table_rows(section):
        if len(row) < 2 or row[0] in {"字段", "问题"}:
            continue
        values[row[0]] = row[1]
    return values


def fixed_section(text, heading):
    """结构化事实只接受完整的固定标题；正文保留，表格解析另行屏蔽示例。"""
    if not text:
        return None
    masked = mask_fenced_code(text)
    match = re.search(rf"^#+\s+{re.escape(heading)}\s*$", masked, re.MULTILINE)
    if not match:
        return None
    tail = text[match.end():]
    end = re.search(r"^#+\s+", masked[match.end():], re.MULTILINE)
    return tail[:end.start()] if end else tail


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
    section = fixed_section(plan_text, "阶段路线图")
    return [row for row in markdown_table_rows(section) if row and row[0] != "阶段"]


def review_history_rows(plan_text):
    section = fixed_section(plan_text, "独立复核记录")
    return [row for row in markdown_table_rows(section) if row and row[0] != "日期"]


def is_placeholder(value, allow_empty=False):
    normalized = re.sub(r"\s+", "", value or "")
    if not normalized:
        return not allow_empty
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


def review_outcome(conclusion):
    """新策略只识别明确结论；未进行、失败和不确定声明不能混为通过。"""
    conclusion = conclusion.strip()
    choice_separator = r"\s*(?:[/／]|或(?:者)?)\s*"
    if re.match(
        rf"^(?:通过{choice_separator}(?:未通过|不通过)|(?:未通过|不通过){choice_separator}通过)",
        conclusion,
    ):
        # 开头候选始终不是结论，不能因尾标点/说明漏匹配后落入 passed。
        return "unknown"
    if conclusion.startswith(("未通过", "不通过", "失败", "不满足", "拒绝")):
        return "failed"
    if re.match(r"^通过(?:$|[。.!！：:，,；;（(\s])", conclusion):
        return "passed"
    if any(token in conclusion for token in ("不可用", "超时", "证据冲突", "证据失效")):
        return "failed"
    if conclusion in {"未进行", "尚未进行", "待复核", "待自验", "待独立复核", "待验证"}:
        return "pending"
    return "unknown"


def valid_review_date(value):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value or ""):
        return None
    try:
        return parse_plan_date(value)
    except ValueError:
        return None


def legacy_review_method(kind):
    """六列旧记录用类型显式表达自验；其他历史类型仍按独立事实解释。"""
    return "自验" if kind == "复核基线复用" or "自验" in kind else "独立"


def independent_review_requested(summary):
    """只有明确的用户请求证据才将待办派给独立复核。"""
    request = summary.get("独立复核请求", "").strip()
    return bool(request and request != "无" and not is_placeholder(request))


def review_unavailable(conclusion):
    """工具未完成不等于审出了实质问题。"""
    return conclusion.strip().startswith(("超时", "复核工具超时", "复核入口不可用"))


def phase_precedes(plan_text, candidate, current):
    """只允许路线图中更早的阶段；标准数字阶段可在精简路线图中回退比较。"""
    roadmap = [row[0] for row in phase_roadmap_rows(plan_text)]
    if candidate in roadmap and current in roadmap:
        return roadmap.index(candidate) < roadmap.index(current)
    candidate_match = re.fullmatch(r"阶段\s*(\d+)", candidate or "")
    current_match = re.fullmatch(r"阶段\s*(\d+)", current or "")
    return bool(candidate_match and current_match
                and int(candidate_match.group(1)) < int(current_match.group(1)))


def legacy_review_state(plan_text, phase):
    """在不改写六列历史的前提下应用默认自验和真实发现闭环。"""
    result = {"passed": False, "pending_action": None, "issues": [], "blockers": []}
    issues, blockers = result["issues"], result["blockers"]
    rows = review_history_rows(plan_text)
    known_phases = {row[0] for row in phase_roadmap_rows(plan_text)}
    valid_rows = []
    previous_dates = {}
    for row in rows:
        if len(row) != 6:
            kind = row[1] if len(row) > 1 else ""
            row_phase = row[2] if len(row) > 2 else ""
            if ("准入" in kind or "readiness" in kind.lower() or "自验" in kind
                    or kind == "复核基线复用") and (not row_phase or row_phase == phase):
                issues.append("旧独立复核记录必须使用日期、类型、阶段、结论、证据、复核者六列")
            continue
        kind, conclusion = row[1], row[3]
        if not (
            "准入" in kind
            or "readiness" in kind.lower()
            or "自验" in kind
            or kind == "复核基线复用"
            or (("完成验收" in kind or "完成复核" in kind) and review_outcome(conclusion) == "passed")
        ):
            continue
        row_phase = row[2]
        if row_phase != phase and row_phase not in known_phases and not re.fullmatch(r"阶段\s*\d+", row_phase):
            continue
        valid_rows.append(row)
        parsed = valid_review_date(row[0])
        previous = previous_dates.get(row_phase)
        if parsed and previous and parsed < previous:
            issues.append(f"旧独立复核记录 {row_phase} 日期逆序，无法确认最新结果")
        if parsed:
            previous_dates[row_phase] = parsed

    def qualified(row):
        return (len(row) == 6 and not any(is_placeholder(value) for value in row)
                and valid_review_date(row[0]) is not None)

    def completed_independent(row):
        conclusion = row[3].strip()
        return qualified(row) and legacy_review_method(row[1]) == "独立" and (
            review_outcome(conclusion) == "passed" or
            conclusion.startswith(("未通过", "不通过", "失败", "不满足", "拒绝", "证据冲突"))
            and review_outcome(conclusion) == "failed"
        )

    prior_states = {}
    for row in valid_rows:
        if row[2] == phase or not phase_precedes(plan_text, row[2], phase):
            continue
        state = prior_states.setdefault(row[2], {"reviewed": False, "unresolved": False})
        method = legacy_review_method(row[1])
        outcome = review_outcome(row[3])
        if method == "独立":
            state["reviewed"] = completed_independent(row)
            if outcome == "failed" and not review_unavailable(row[3]):
                state["unresolved"] = True
        elif (row[1] == "修复自验" and state["reviewed"] and outcome == "passed"
              and qualified(row)):
            state["unresolved"] = False
    reusable_prior_phases = {
        source_phase for source_phase, state in prior_states.items()
        if state["reviewed"] and not state["unresolved"]
    }

    current = [row for row in valid_rows if row[2] == phase]
    reviewed = False
    unresolved = None
    for row in current:
        method = legacy_review_method(row[1])
        outcome = review_outcome(row[3])
        if outcome == "unknown":
            issues.append("旧独立复核记录结论为空或未知")
        if method == "独立":
            reviewed = completed_independent(row)
            if outcome == "failed" and not review_unavailable(row[3]):
                unresolved = row[3]
        elif row[1] == "复核基线复用":
            referenced = [source for source in reusable_prior_phases if source in row[4]]
            if not referenced:
                issues.append("旧格式复核基线复用须在证据中指向已解决的前阶段独立基线")
            elif outcome == "passed" and qualified(row):
                reviewed = True
        elif row[1] == "修复自验":
            if outcome == "passed" and qualified(row) and reviewed:
                unresolved = None
        if outcome == "passed" and not qualified(row):
            issues.append("旧独立复核记录通过缺少有效日期、类型、证据或身份")

    if unresolved:
        blockers.append("旧独立复核记录存在未修复的独立发现：" + unresolved)
    if current and review_outcome(current[-1][3]) == "failed":
        blockers.append("旧独立复核记录最新结果：" + current[-1][3])

    review = key_value_table(fixed_section(plan_text, "最新独立准入复核"))
    outcome = review_outcome(review.get("结论", ""))
    latest_matches = bool(current) and all(
        review.get(field) == current[-1][index]
        for field, index in [("日期", 0), ("阶段", 2), ("结论", 3), ("证据", 4), ("复核者", 5)]
    )
    summary = key_value_table(fixed_section(top_level_section(plan_text, "当前阶段"), "阶段准入摘要"))
    requested = independent_review_requested(summary)
    awaiting_requested_review = requested and outcome == "passed" and not reviewed
    result["passed"] = outcome == "passed" and latest_matches and not issues and not blockers and not awaiting_requested_review
    if outcome == "pending" and not issues and not blockers:
        result["pending_action"] = "independent_review" if requested else "verify"
    elif awaiting_requested_review and not issues and not blockers:
        result["pending_action"] = "independent_review"
    return result


def risk_review_state(plan_text, phase):
    """显式风险策略的共享事实判定；历史策略名不改变默认自验行为。"""
    summary_section = fixed_section(top_level_section(plan_text, "当前阶段"), "阶段准入摘要")
    policies = [row for row in markdown_table_rows(summary_section) if row[0] == "复核策略"]
    result = {"enabled": bool(policies), "passed": False, "pending_action": None,
              "issues": [], "blockers": []}
    if not policies:
        return result
    issues, blockers = result["issues"], result["blockers"]
    if len(policies) != 1 or len(policies[0]) != 2 or policies[0][1] not in {"风险分流", "单次独立复核", "默认自验"}:
        issues.append("复核策略必须唯一且为 默认自验/风险分流/单次独立复核；空值、未知值或重复声明不能准入")
    risks = {"低风险", "高影响", "高风险"}
    summary = key_value_table(summary_section)
    if "最新独立准入复核" in summary:
        issues.append("显式复核策略的阶段准入摘要应以 最新阶段复核 替代 最新独立准入复核")
    if is_placeholder(summary.get("最新阶段复核")):
        issues.append("阶段准入摘要缺少有效的 最新阶段复核 链接")

    review = key_value_table(fixed_section(plan_text, "最新阶段复核"))
    if any(len(row) != 2 for row in markdown_table_rows(fixed_section(plan_text, "最新阶段复核"))):
        issues.append("最新阶段复核必须使用字段/内容两列表格")
    fields = {"日期", "阶段", "方式", "风险", "风险依据", "结论", "证据", "复核者"}
    for field in sorted(fields - set(review)):
        issues.append(f"最新阶段复核缺少字段：{field}")
    outcome = review_outcome(review.get("结论", ""))
    if review.get("阶段") != phase:
        issues.append(f"最新阶段复核阶段与 PLAN_MAP 当前阶段 {phase} 不一致")
    if review.get("方式") not in {"自验", "独立"}:
        issues.append("最新阶段复核方式必须为 自验/独立")
    if review.get("风险") not in risks | {"待判断"}:
        issues.append("最新阶段复核风险必须为 " + "/".join(sorted(risks)) + "/待判断")
    if review.get("风险") == "待判断":
        issues.append("最新阶段复核风险待判断，不能准入")
    if is_placeholder(review.get("风险依据")):
        issues.append("最新阶段复核风险依据为空或占位")
    if outcome == "unknown":
        issues.append("最新阶段复核结论为空或未知")
    if outcome == "failed" and review.get("阶段") == phase:
        blockers.append("最新阶段复核：" + review["结论"])

    valid_date = valid_review_date

    def qualified(row, legacy=False):
        # 独立基线须有完整身份和证据；记录的结论另行判断。
        return (len(row) == (6 if legacy else 8) and not any(is_placeholder(value) for value in row)
                and valid_date(row[0]) is not None
                and (legacy or (row[3] == "独立" and row[4] in risks)))

    def completed(row):
        # 明确的通过/缺陷结论代表已完成检查；不扫描业务发现中的状态词。
        conclusion = row[5].strip()
        return qualified(row) and (
            review_outcome(conclusion) == "passed" or
            conclusion.startswith(("未通过", "不通过", "失败", "不满足", "拒绝", "证据冲突"))
            and review_outcome(conclusion) == "failed"
        )

    known_phases = {row[0] for row in phase_roadmap_rows(plan_text)}

    def known_other_phase(value):
        return value != phase and (value in known_phases or re.fullmatch(r"阶段\s*\d+", value))

    def history_rows(title, width):
        section = fixed_section(plan_text, title)
        rows = markdown_table_rows(section)
        expected = (["日期", "类型", "阶段", "方式", "风险", "结论", "证据", "复核者"]
                    if width == 8 else ["日期", "类型", "阶段", "结论", "证据", "复核者"])
        if rows and rows[0] != expected:
            issues.append(f"{title} 必须使用固定的 {width} 列表头")
        if rows.count(expected) > 1:
            issues.append(f"{title} 存在重复表头，无法确认记录结构")
        valid = []
        previous_dates = {}
        for row in rows:
            if row == expected:
                continue
            if len(row) > 2 and row[2] != phase:
                if not known_other_phase(row[2]):
                    issues.append(f"{title} 记录阶段为空或未知，不能忽略")
                    continue
            if len(row) != width or len(row) < 3 or (row[2] != phase and not known_other_phase(row[2])):
                issues.append(f"{title} 记录字段不足、列数不符或阶段不明")
                continue
            valid.append(row)
            if is_placeholder(row[1]):
                issues.append(f"{title} 类型为空或占位")
            parsed = valid_date(row[0])
            if not is_placeholder(row[0]) and parsed is None:
                issues.append(f"{title} 日期不合法：{row[0]}")
            previous_date = previous_dates.get(row[2])
            if parsed and previous_date and parsed < previous_date:
                issues.append(f"{title} {row[2]} 记录日期逆序，无法确认最新结果")
            if parsed:
                previous_dates[row[2]] = parsed
        return valid

    all_history = history_rows("阶段复核记录", 8)
    history = [row for row in all_history if row[2] == phase]

    prior_states = {}
    for row in all_history:
        if (row[2] == phase or not phase_precedes(plan_text, row[2], phase)
                or row[3] not in {"自验", "独立"}):
            continue
        state = prior_states.setdefault(row[2], {"reviewed_high": False, "unresolved": False})
        if row[3] == "独立":
            if completed(row):
                state["reviewed_high"] = row[4] in {"高风险", "高影响"}
            else:
                state["reviewed_high"] = False
            row_outcome = review_outcome(row[5])
            if row_outcome == "failed" and not review_unavailable(row[5]):
                state["unresolved"] = True
        elif (row[1] == "修复自验" and state["reviewed_high"]
              and review_outcome(row[5]) == "passed"
              and not any(is_placeholder(value) for value in row)
              and valid_date(row[0]) is not None):
            state["unresolved"] = False
    reusable_prior_phases = {
        source_phase for source_phase, state in prior_states.items()
        if state["reviewed_high"] and not state["unresolved"]
    }

    reviewed = False
    reviewed_high = False
    repair_date = None
    unresolved_single = None
    for row in history:
        if row[3] not in {"自验", "独立"} or row[4] not in risks | {"待判断"}:
            issues.append("阶段复核记录方式或风险未知")
        if row[3] == "独立":
            if completed(row):
                reviewed = True
                reviewed_high = row[4] in {"高风险", "高影响"}
            else:
                reviewed = reviewed_high = False
            if review_outcome(row[5]) == "failed" and not review_unavailable(row[5]):
                unresolved_single = row[5]
            elif review_outcome(row[5]) == "passed" and completed(row):
                # 后续独立通过可形成新范围基线，但不能清除既有独立发现。
                pass
        elif row[3] == "自验":
            if row[1] == "复核基线复用":
                referenced = [source for source in reusable_prior_phases if source in row[6]]
                if row[4] not in {"高风险", "高影响"} or not referenced:
                    issues.append("复核基线复用须在证据中指向已解决的前阶段高风险/高影响独立基线")
                elif (review_outcome(row[5]) == "passed"
                      and not any(is_placeholder(value) for value in row)
                      and valid_date(row[0]) is not None):
                    reviewed = reviewed_high = True
            if row[1] == "修复自验":
                if (reviewed and review_outcome(row[5]) == "passed" and row[4] in risks
                      and not any(is_placeholder(value) for value in row)
                      and valid_date(row[0]) is not None):
                    unresolved_single = None
                    repair_date = valid_date(row[0])
        if review_outcome(row[5]) == "unknown":
            issues.append("阶段复核记录结论为空或未知")
        if review_outcome(row[5]) == "passed" and (
            any(is_placeholder(value) for value in row) or valid_date(row[0]) is None or row[4] == "待判断"
        ):
            issues.append("阶段复核记录通过缺少有效日期、类型、风险、证据或身份")
    if history:
        latest = history[-1]
        for field, index in [("日期", 0), ("方式", 3), ("风险", 4), ("结论", 5), ("证据", 6), ("复核者", 7)]:
            if review.get(field) != latest[index]:
                issues.append(f"最新阶段复核与当前阶段历史记录最后一条 {field} 冲突")
        if review_outcome(latest[5]) == "failed":
            blockers.append("阶段复核记录最新结果：" + latest[5])
    elif outcome != "pending":
        issues.append(f"阶段复核记录缺少当前阶段 {phase} 的记录")
    if outcome == "passed":
        for field in sorted(fields & set(review)):
            if is_placeholder(review[field]):
                issues.append(f"最新阶段复核字段 {field} 为空或占位")
    if (outcome == "passed" or not is_placeholder(review.get("日期"))) and valid_date(review.get("日期", "")) is None:
        issues.append("最新阶段复核日期不合法")

    if unresolved_single:
        blockers.append("阶段复核记录存在未修复的独立发现：" + unresolved_single)

    # 旧独立记录仍是独立事实源；完成失败也不能被新自验覆盖。
    legacy_history = [row for row in history_rows("独立复核记录", 6) if row[2] == phase]
    legacy_section = fixed_section(plan_text, "最新独立准入复核")
    legacy = key_value_table(legacy_section)
    legacy_current = legacy.get("阶段") == phase
    if legacy_section is not None and not legacy_current and not known_other_phase(legacy.get("阶段", "")):
        issues.append("旧最新独立准入复核阶段为空或未知，不能降级放行")
    if legacy_history:
        latest = legacy_history[-1]
        if not legacy_current or any(legacy.get(field) != latest[index]
                                    for field, index in [("日期", 0), ("证据", 4), ("复核者", 5)]) or (
            latest[3] != legacy.get("结论") and not (
                review_outcome(latest[3]) == review_outcome(legacy.get("结论", "")) == "passed"
                and latest[3] in legacy.get("结论", "")
            )
        ):
            issues.append("旧最新独立准入复核与当前阶段历史记录冲突，不能降级放行")
    unresolved = None
    for row in legacy_history:
        row_outcome = review_outcome(row[3])
        if not qualified(row, legacy=True):
            issues.append("旧独立复核记录缺少有效日期、类型、证据或身份，迁移不能掩盖")
        if row_outcome == "failed" and not review_unavailable(row[3]):
            unresolved = row[3]
        elif row_outcome == "passed" and qualified(row, legacy=True):
            pass
        elif row_outcome == "passed":
            issues.append("旧独立通过记录缺少有效日期、类型、证据或身份")
        elif row_outcome == "unknown":
            issues.append("旧独立复核记录结论为空或未知")
    # 显式迁移后保留旧结论；新记录中的有效修复自验可解除旧发现。
    legacy_dates = [valid_date(row[0]) for row in legacy_history]
    legacy_repaired = (repair_date is not None and bool(legacy_dates)
                       and all(date is not None and date <= repair_date for date in legacy_dates)
                       and not unresolved_single)
    if unresolved and not legacy_repaired:
        blockers.append("旧独立复核记录存在未解除的失败：" + unresolved)
    if legacy_current:
        if review_outcome(legacy.get("结论", "")) == "failed" and not legacy_repaired:
            blockers.append("最新独立准入复核：" + legacy["结论"])
        elif not legacy_history or any(is_placeholder(legacy.get(field))
                                     for field in ["日期", "阶段", "结论", "证据", "复核者"]) or valid_date(legacy.get("日期", "")) is None:
            issues.append("旧最新独立准入复核缺少有效字段或当前阶段历史，不能降级放行")
    requested = independent_review_requested(summary)
    awaiting_requested_review = requested and outcome == "passed" and not reviewed
    result["passed"] = outcome == "passed" and not issues and not blockers and not awaiting_requested_review
    if outcome == "pending" and not issues and not blockers:
        result["pending_action"] = "independent_review" if requested else "verify"
    elif awaiting_requested_review and not issues and not blockers:
        result["pending_action"] = "independent_review"
    return result


def check_phase_structure(plan_name, data, plan_text, strict, warnings, errors, review_state=None, selected=False):
    """检查待实施/实施中计划的阶段准入结构，不判断业务证据真实性。"""
    if data["status"] not in ACTIVE and not selected:
        return

    current_phase = data["phase"]
    current_section = top_level_section(plan_text, "当前阶段")
    summary_section = fixed_section(current_section, "阶段准入摘要")
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
        if roadmap_status != expected_roadmap_status:
            readiness_issue(
                warnings,
                errors,
                strict,
                f"{plan_name}: 当前阶段 {current_phase} 的路线图状态 {roadmap_status} 与阶段状态 {expected_roadmap_status} 不一致",
            )

    if markdown_section(plan_text, ["当前阶段"]) is None:
        section_hint = structural_heading_hint(plan_text, "当前阶段")
        readiness_issue(warnings, errors, strict, f"{plan_name}: 缺少 `## 当前阶段` 章节{section_hint}")

    review_state = review_state if review_state is not None else risk_review_state(plan_text, current_phase)
    required_fields = READINESS_FIELDS
    if review_state["enabled"]:
        required_fields = (READINESS_FIELDS - {"最新独立准入复核"}) | {"最新阶段复核"}
    missing_fields = sorted(required_fields - set(summary))
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
    for field in sorted(required_fields - {"当前阻塞项"}):
        if field in summary and is_placeholder(summary[field]):
            readiness_issue(
                warnings,
                errors,
                strict,
                f"{plan_name}: 阶段准入摘要字段 {field} 仍是占位内容",
            )
    if "当前阻塞项" in summary and is_placeholder(summary["当前阻塞项"]) and summary["当前阻塞项"].strip() != "无":
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

    if review_state["enabled"]:
        for issue in review_state["issues"] + review_state["blockers"]:
            readiness_issue(warnings, errors, strict, f"{plan_name}: {issue}")
        if review_state["pending_action"]:
            readiness_issue(warnings, errors, strict, f"{plan_name}: 最新阶段复核尚未通过")
        return

    review = key_value_table(fixed_section(plan_text, "最新独立准入复核"))
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
    for field in sorted(review_fields & set(review)):
        if is_placeholder(review[field]):
            readiness_issue(warnings, errors, strict,
                            f"{plan_name}: 最新独立准入复核字段 {field} 仍是占位内容")
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

    history = [
        row
        for row in review_history_rows(plan_text)
        if len(row) == 6
        and row[2] == current_phase
        and (
            "准入" in row[1]
            or "自验" in row[1]
            or row[1] == "复核基线复用"
            or ("完成验收" in row[1] and row[3].startswith("通过"))
            or ("完成复核" in row[1] and row[3].startswith("通过"))
            or "readiness" in row[1].lower()
        )
    ]
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
    legacy_state = legacy_review_state(plan_text, current_phase)
    for issue in legacy_state["issues"] + legacy_state["blockers"]:
        readiness_issue(warnings, errors, strict, f"{plan_name}: {issue}")
    if not legacy_state["passed"] and not legacy_state["issues"] and not legacy_state["blockers"]:
        readiness_issue(
            warnings,
            errors,
            strict,
            f"{plan_name}: 旧格式当前阶段记录未满足自验或已请求复核的准入",
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


def plan_link_issue(link):
    """Validate the canonical YYYYMMDD bucket while preserving legacy/custom paths."""
    parts = Path(link).parts
    if len(parts) < 2 or parts[0] != "plans":
        return f"计划路径必须位于 docs/plans 下：{link}"
    bucket = parts[1]
    if len(parts) == 2 and bucket.endswith(".md"):
        return None
    if not bucket[:1].isdigit():
        return None
    if not re.fullmatch(r"\d{8}", bucket):
        return f"计划日期目录必须为 YYYYMMDD：{link}"
    try:
        datetime.strptime(bucket, "%Y%m%d")
    except ValueError:
        return f"计划日期目录不是有效日期：{link}"
    if len(parts) != 3 or not parts[2].endswith(".md"):
        return f"计划日期目录必须直接包含 Markdown 文件：{link}"
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


def extract_phase_evidence_targets(plan_text):
    """读取当前阶段显式声明的证据路径，并返回合法路径和非法原文。"""
    current = top_level_section(plan_text, "当前阶段")
    section = markdown_section(current, ["阶段证据"])
    valid = []
    invalid = []
    for item in markdown_list_items(section):
        backtick = re.search(r"`([^`]+)`", item)
        token = backtick.group(1).strip() if backtick else (item.strip().split(None, 1)[0] if item.strip() else "")
        if not token or token in PLACEHOLDER_VALUES:
            continue
        raw = token.replace("\\", "/")
        if (
            raw.startswith("/")
            or re.match(r"^[A-Za-z]:/", raw)
            or any(part == ".." for part in raw.split("/"))
            or any(char in raw for char in "*?[]{}")
        ):
            invalid.append(token)
            continue
        normalized = normalize_scope_path(raw)
        if not normalized or normalized == ".":
            invalid.append(token)
            continue
        valid.append(normalized)
    return valid, invalid


def extract_plan_references(plan_text, known_plans, current_name):
    references = set()
    for match in re.finditer(r"\[\[([^\]]+)\]\]", plan_text):
        name = Path(match.group(1).strip()).stem
        if name in known_plans and name != current_name:
            references.add(name)

    for match in re.finditer(
        r"(?:docs/)?plans/(?:\d{8}/)?([A-Za-z0-9\u4e00-\u9fff._-]+)\.md",
        plan_text,
    ):
        name = Path(match.group(1).strip()).stem
        if name in known_plans and name != current_name:
            references.add(name)

    for match in re.finditer(r"\]\(([^)#]+\.md)(?:#[^)]+)?\)", plan_text):
        target = match.group(1).strip()
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", target):
            continue
        name = Path(target).stem
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
    """保留默认 check 对已有开放问题的硬错误，不扩大到新增来源。"""
    for row in table_rows(plan_text, "未决问题"):
        if (len(row) >= 4 and row[2].strip().lower() in {"是", "yes"}
                and row[3].strip().lower() not in CLOSED_BLOCKER_STATES
                and re.search(r"Open|待确认|未解决|待处理|未决定", row[3], re.IGNORECASE)):
            return True
    return False


def find_orphan_plans(docs, plans):
    plans_dir = docs / "plans"
    if not plans_dir.exists():
        return []
    indexed_paths = {data["path"].resolve() for data in plans.values()}
    candidates = set(plans_dir.glob("*.md"))
    for bucket in plans_dir.iterdir():
        if not bucket.is_dir() or not bucket.name[:1].isdigit():
            continue
        # Numeric buckets are reserved for dated plans. Include malformed buckets
        # and deeper files so they cannot disappear from orphan diagnostics.
        candidates.update(bucket.rglob("*.md"))
    return sorted(
        plan_file
        for plan_file in candidates
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


def changed_plan_map_lines(root, staged=False):
    """返回 PLAN_MAP diff 中实际变更的行；无法读取时由调用方按未知归属处理。"""
    args = ["diff"]
    if staged:
        args.append("--cached")
    args.extend(["--unified=0", "--", "docs/PLAN_MAP.md"])
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    lines = []
    for line in result.stdout.splitlines():
        if line.startswith(("+++", "---", "@@")):
            continue
        if line.startswith(("+", "-")):
            content = line[1:].strip()
            if content:
                lines.append(content)
    return lines


def plan_map_line_candidates(line, known_plans):
    linked_plans = sorted(
        {
            name
            for name in re.findall(r"plans/([A-Za-z0-9\u4e00-\u9fff._-]+)\.md", line)
            if name in known_plans
        }
    )
    if linked_plans:
        return linked_plans
    candidates = []
    for name in known_plans:
        if re.search(rf"(?<![A-Za-z0-9_-]){re.escape(name)}(?![A-Za-z0-9_-])", line):
            candidates.append(name)
    return sorted(set(candidates))


def plan_map_change_owners(root, staged, known_plans):
    try:
        lines = changed_plan_map_lines(root, staged=staged)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return [plan_map_line_candidates(line, known_plans) for line in lines]


def plan_map_change_is_covered(plan_map_owners, active_plan_names):
    if plan_map_owners is None or not plan_map_owners:
        return False
    return all(len(candidates) == 1 and candidates[0] in active_plan_names for candidates in plan_map_owners)


def warn_uncovered_changes(
    warnings,
    mode,
    files,
    plan_targets,
    root=None,
    known_plans=None,
    covering_plan_names=None,
):
    if not files:
        return
    if not plan_targets:
        warn(warnings, f"{mode}: 存在变更文件，但没有活跃计划声明影响范围")
        return
    covering_plan_names = set(covering_plan_names or plan_targets)
    map_owners = plan_map_change_owners(root, mode == "--pre-commit", known_plans or set()) if root else None
    uncovered = []
    for changed_file in sorted(files):
        normalized_file = normalize_scope_path(changed_file)
        if normalized_file == "docs/PLAN_MAP.md":
            if plan_map_change_is_covered(map_owners, covering_plan_names):
                continue
            warn(warnings, f"{mode}: PLAN_MAP.md 变更无法唯一归属到活跃计划索引行")
            continue
        if any(target_matches_path(target, normalized_file) for targets in plan_targets.values() for target in targets):
            continue
        uncovered.append(changed_file)
    for changed_file in uncovered:
        warn(warnings, f"{mode}: 变更文件未被活跃计划影响范围覆盖：{changed_file}")


def completed_plan_drift_targets(plans, plan_texts, root, files):
    """关闭窗口内只覆盖已完成计划的自身和显式阶段证据。

    已完成计划不再属于活跃计划，但关闭阶段时通常还要原子地同步计划、地图和
    验收证据。只有当该计划文件本身也在本次变更中时，才开启这个窄窗口；不会
    复用已完成计划的完整影响范围，从而避免历史计划吞掉新的未声明变更。
    """
    changed = {normalize_scope_path(path) for path in files}
    targets = {}
    for name, data in plans.items():
        if data["status"] not in COMPLETED:
            continue
        plan_relative = data["path"].relative_to(root).as_posix()
        if plan_relative not in changed:
            continue
        phase_evidence, _ = extract_phase_evidence_targets(plan_texts.get(name, ""))
        targets[name] = [plan_relative, *phase_evidence]
    return targets


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


def safe_relative_path(value):
    raw = str(value or "").strip().replace("\\", "/")
    if not raw or raw.startswith("/") or re.match(r"^[A-Za-z]:/", raw):
        return None
    parts = [part for part in raw.split("/") if part not in {"", "."}]
    if ".." in parts:
        return None
    normalized = posixpath.normpath("/".join(parts))
    return normalized if normalized not in {"", ".", "/"} else None


def binding_path(value):
    """范围绑定只接受明确文件路径；不改变旧路径解析的兼容行为。"""
    if not isinstance(value, str) or re.search(r"[\x00*?\[\]]", value) or re.match(r"^[A-Za-z]:", value):
        raise ValueError(f"binding 路径非法：{value!r}")
    normalized = safe_relative_path(value)
    if normalized is None:
        raise ValueError(f"binding 路径必须是仓库内相对文件：{value!r}")
    return normalized


def binding_file(root, value, require_file=True):
    relative = binding_path(value)
    path = root
    if path.is_symlink():
        raise ValueError("binding 仓库根目录不能是 symlink")
    parts = relative.split("/")
    for index, part in enumerate(parts):
        path = path / part
        if path.is_symlink():
            raise ValueError(f"binding 路径不能包含 symlink：{relative}")
        if index < len(parts) - 1 and path.exists() and not path.is_dir():
            raise ValueError(f"binding 父路径不是目录：{relative}")
    if require_file and not path.is_file():
        raise ValueError(f"binding 文件不存在或不是普通文件：{relative}")
    return path


def canonical_sha256(value):
    content = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def binding_table(text, heading, columns, repeated_header=False):
    count = len(re.findall(rf"^##\s+{re.escape(heading)}\s*$", mask_fenced_code(text), re.MULTILINE))
    if count > 1:
        raise ValueError(f"binding PLAN_MAP 重复结构章节：{heading}")
    section = top_level_section(text, heading)
    if section is None or not section.strip():
        return []
    rows = markdown_table_rows(section)
    if not rows or rows[0] != columns:
        raise ValueError(f"binding PLAN_MAP {heading} 表头非法")
    result = []
    for row in rows[1:]:
        if row == columns and repeated_header:
            continue
        if len(row) != len(columns) or row == columns:
            raise ValueError(f"binding PLAN_MAP {heading} 列数或重复表头非法")
        if row in result:
            raise ValueError(f"binding PLAN_MAP {heading} 重复行")
        result.append(row)
    return sorted(result)


def binding_plan_id(cell):
    link = extract_plan_link(cell)
    return Path(link).stem if link else clean_relation_value(cell)


def binding_metadata(root, plan_map_relative, plan_name):
    text = binding_file(root, plan_map_relative).read_text(encoding="utf-8")
    index = binding_table(text, "计划索引", ["计划", "状态", "当前阶段", "最后更新", "依赖", "证据"], True)
    dependency = binding_table(text, "依赖关系", ["计划", "依赖", "原因"])
    relations = binding_table(text, "阶段关系", RELATION_COLUMNS)
    shared = binding_table(text, "机器可检查共享写入约束", SHARED_WRITE_COLUMNS)
    blockers = binding_table(text, "当前阻塞项", ["问题", "推荐方案", "影响范围", "是否阻塞当前阶段", "状态"])
    by_name = {}
    dependencies = {}
    for row in index:
        link = extract_plan_link(row[0])
        name = binding_plan_id(row[0])
        if not link or name in by_name:
            raise ValueError(f"binding PLAN_MAP 计划链接非法或重复 ID：{name}")
        binding_path("docs/" + link)
        if clean_relation_value(row[1]) not in VALID_STATUSES or not valid_phase_name(row[2]):
            raise ValueError(f"binding PLAN_MAP 计划状态或阶段非法：{name}")
        parse_plan_date(clean_relation_value(row[3]))
        by_name[name] = row
        deps = extract_declared_dependencies(row[4])
        if len(set(deps)) != len(deps):
            raise ValueError(f"binding PLAN_MAP 重复依赖：{name}")
        dependencies[name] = set(deps)
    if plan_name not in by_name:
        raise ValueError(f"binding 未登记计划：{plan_name}")
    for name, deps in dependencies.items():
        if deps - by_name.keys():
            raise ValueError(f"binding PLAN_MAP 未知依赖：{name}")
    if detect_dependency_cycles(dependencies):
        raise ValueError("binding PLAN_MAP 索引依赖存在环")
    seen = set()
    for row in dependency:
        name = binding_plan_id(row[0])
        if name not in by_name or name in seen:
            raise ValueError(f"binding PLAN_MAP 依赖详情未知或重复计划：{name}")
        deps = extract_declared_dependencies(row[1])
        if len(set(deps)) != len(deps) or set(deps) != dependencies[name]:
            raise ValueError(f"binding PLAN_MAP 依赖详情与索引不一致：{name}")
        seen.add(name)
    for rows, label in [(relations, "阶段关系"), (shared, "共享写入约束")]:
        for row in rows:
            source, source_phase, target, target_phase, kind = map(clean_relation_value, row[:5])
            if source not in by_name or target not in by_name:
                raise ValueError(f"binding PLAN_MAP {label} 未知关系端点")
            kinds = RELATION_TYPES if rows is relations else {"shared_write_risk"}
            if kind not in kinds or not valid_phase_name(source_phase) or not valid_phase_name(target_phase):
                raise ValueError(f"binding PLAN_MAP {label} 类型或阶段非法")
    scopes = []
    for row in blockers:
        if all(cell in {"", "-"} for cell in row[:3]) and row[3].lower() in {"否", "no"}:
            continue
        scope = re.sub(r"\[[^\]]+\]\((?:\./)?plans/([^/)]+)\.md(?:#[^)]*)?\)", r"\1", row[2]).replace("`", "")
        targets = set(filter(None, re.split(r"[,，、/;；\s]+", scope.strip())))
        if not targets or targets - by_name.keys():
            raise ValueError(f"binding PLAN_MAP 阻塞影响范围无法归属：{row[2]}")
        scopes.append((row, targets))
    members = {plan_name}
    while True:
        expanded = members | set().union(*(dependencies[name] for name in members))
        expanded.update(clean_relation_value(row[0]) for row in relations
                        if clean_relation_value(row[2]) in members and clean_relation_value(row[4]) in {"hard_gate", "evidence"})
        if expanded == members:
            break
        members = expanded
    projection = {
        "version": 1,
        "members": sorted(members),
        "index_rows": sorted(by_name[name] for name in members),
        "dependency_rows": [row for row in dependency if binding_plan_id(row[0]) in members],
        "relation_rows": [row for row in relations if clean_relation_value(row[0]) in members or clean_relation_value(row[2]) in members],
        "shared_write_rows": [row for row in shared if clean_relation_value(row[0]) in members or clean_relation_value(row[2]) in members],
        "blocker_rows": [row for row, targets in scopes if targets & members],
    }
    related = []
    for name in sorted(members):
        relative = binding_path("docs/" + extract_plan_link(by_name[name][0]))
        path = binding_file(root, relative)
        related.append({"plan": name, "path": relative, "sha256": sha256_file(path)})
    return projection, related


def make_attestation_binding(root, plan_map_relative, plan_name, files):
    if not files:
        raise ValueError("binding files 不能为空")
    entries = []
    seen = set()
    for value in files:
        relative = binding_path(value)
        if relative in seen:
            raise ValueError(f"binding 文件重复：{relative}")
        seen.add(relative)
        entries.append({"path": relative, "sha256": sha256_file(binding_file(root, relative))})
    projection, related = binding_metadata(root, plan_map_relative, plan_name)
    head = None
    try:
        result = subprocess.run(["git", "rev-parse", "--verify", "HEAD"], cwd=root, capture_output=True, text=True, check=False)
        value = result.stdout.strip()
        if result.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", value):
            head = value
    except OSError:
        pass
    return {"version": 1, "files": sorted(entries, key=lambda entry: entry["path"]),
            "related_plans": related, "plan_map_projection": projection,
            "plan_map_projection_sha256": canonical_sha256(projection),
            "revision": {"source": "working_tree", "head": head}}


def validate_attestation_binding(attestation):
    """验证保存的结构，不访问已可能变化/删除的文件。"""
    binding = attestation["binding"]
    if not isinstance(binding, dict) or type(binding.get("version")) is not int or binding["version"] != 1:
        raise ValueError("binding version 必须为 1")
    projection = binding.get("plan_map_projection")
    columns = {"index_rows": 6, "dependency_rows": 3, "relation_rows": 7, "shared_write_rows": 9, "blocker_rows": 5}
    if not isinstance(projection, dict) or set(projection) != {"version", "members", *columns}:
        raise ValueError("binding plan_map_projection 结构非法")
    if type(projection["version"]) is not int or projection["version"] != 1:
        raise ValueError("binding projection version 必须为 1")
    members = projection["members"]
    if (not isinstance(members, list) or not members or any(not isinstance(name, str) or not name for name in members)
            or members != sorted(set(members)) or attestation.get("plan") not in members):
        raise ValueError("binding projection members 非法")
    for field, width in columns.items():
        rows = projection[field]
        if (not isinstance(rows, list) or any(not isinstance(row, list) or len(row) != width
                or any(not isinstance(cell, str) for cell in row) for row in rows)):
            raise ValueError(f"binding {field} 必须为固定列数的字符串二维数组")
        if rows != sorted(rows) or len({tuple(row) for row in rows}) != len(rows):
            raise ValueError(f"binding {field} 未排序或重复")
    if binding.get("plan_map_projection_sha256") != canonical_sha256(projection):
        raise ValueError("binding projection hash 不匹配")
    for field, key in [("files", "path"), ("related_plans", "plan")]:
        entries = binding.get(field)
        if not isinstance(entries, list) or not entries:
            raise ValueError(f"binding {field} 不能为空")
        keys = []
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get(key), str) or not entry[key]:
                raise ValueError(f"binding {field} 条目非法")
            if binding_path(entry.get("path")) != entry["path"]:
                raise ValueError(f"binding {field} 路径未规范化")
            if not isinstance(entry.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]):
                raise ValueError(f"binding {field} sha256 非法")
            keys.append(entry[key])
        if keys != sorted(set(keys)):
            raise ValueError(f"binding {field} 未排序或重复")
    related = binding["related_plans"]
    if [entry["plan"] for entry in related] != members:
        raise ValueError("binding related_plans 与 members 不一致")
    index_names = [binding_plan_id(row[0]) for row in projection["index_rows"]]
    if sorted(index_names) != members:
        raise ValueError("binding index_rows 与 members 不一致")
    for entry in related:
        row = next(row for row in projection["index_rows"] if binding_plan_id(row[0]) == entry["plan"])
        link = extract_plan_link(row[0])
        if not link or entry["path"] != binding_path("docs/" + link):
            raise ValueError("binding related_plans 与索引路径不一致")
    target = next(entry for entry in related if entry["plan"] == attestation["plan"])
    if target["path"] != attestation.get("plan_path") or target["sha256"] != attestation.get("plan_sha256"):
        raise ValueError("binding 目标计划与原快照字段不一致")
    binding_path(attestation.get("plan_map_path"))
    revision = binding.get("revision")
    if not isinstance(revision, dict) or revision.get("source") != "working_tree" or "head" not in revision:
        raise ValueError("binding revision 非法")
    head = revision["head"]
    if head is not None and (not isinstance(head, str) or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", head)):
        raise ValueError("binding HEAD 非法")
    if "purpose" not in attestation:
        raise ValueError("binding 必须使用 purpose 快照")


def attestation_binding_drift(root, attestation):
    binding = attestation["binding"]
    changed = []
    for entry in binding["files"]:
        if sha256_file(binding_file(root, entry["path"])) != entry["sha256"]:
            changed.append(entry["path"])
    projection, related = binding_metadata(root, attestation["plan_map_path"], attestation["plan"])
    if projection != binding["plan_map_projection"] or related != binding["related_plans"]:
        changed.append("相关计划或 PLAN_MAP 投影")
    return changed


def attestation_paths(root):
    directory = binding_file(root, "docs/attestations", require_file=False)
    try:
        directory.stat()
    except FileNotFoundError:
        return []
    # glob 会把 PermissionError 当作空结果；证据清单必须显式枚举。
    return sorted(path for path in directory.iterdir() if path.name.endswith(".json"))


def has_attestation_binding(root):
    for path in attestation_paths(root):
        if path.is_symlink():
            return True
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            continue
        if isinstance(data, dict) and "binding" in data:
            return True
    return False


def create_attestation(
    root,
    plan_map,
    plans,
    plan_name,
    errors,
    purpose=None,
    supersedes="",
    review_status="current",
    attest_files=None,
):
    binding = None
    if errors:
        return None
    if attest_files is not None:
        if errors:
            return None
        try:
            if purpose not in ATTESTATION_PURPOSES:
                raise ValueError("--attest-file 必须与 --attest 和 --attest-purpose 一起使用")
            binding_file(root, relative_to_root(plan_map, root))
            binding = make_attestation_binding(root, relative_to_root(plan_map, root), plan_name, attest_files)
        except (ValueError, OSError, UnicodeError) as exc:
            fail(errors, f"{plan_name}: 无法创建 binding 快照：{exc}")
            return None
    data = plans.get(plan_name)
    if data is None:
        fail(errors, f"{plan_name}: 未登记计划，无法创建完成快照")
        return None
    if not data["path"].exists():
        fail(errors, f"{plan_name}: 计划文件不存在，无法创建完成快照")
        return None

    try:
        plan_hash = sha256_file(data["path"])
        map_hash = sha256_file(plan_map)
    except OSError as exc:
        if binding is None:
            raise
        fail(errors, f"{plan_name}: binding 快照读取失败：{exc}")
        return None
    attestation = {
        "plan": plan_name,
        "phase": data["phase"],
        "status": data["status"],
        "plan_path": relative_to_root(data["path"], root),
        "plan_map_path": relative_to_root(plan_map, root),
        "plan_sha256": plan_hash,
        "plan_map_sha256": map_hash,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "created_by": "plan-governance",
        "reason": "阶段完成快照",
    }
    if purpose is not None:
        if purpose not in ATTESTATION_PURPOSES:
            fail(errors, f"{plan_name}: attestation purpose 非法：{purpose}")
            return None
        if review_status not in ATTESTATION_REVIEW_STATUSES:
            fail(errors, f"{plan_name}: attestation review_status 非法：{review_status}")
            return None
        normalized_supersedes = ""
        if supersedes:
            normalized_supersedes = safe_relative_path(supersedes)
            if normalized_supersedes is None:
                fail(errors, f"{plan_name}: attestation supersedes 必须是仓库内相对路径：{supersedes}")
                return None
        snapshot_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + f"-{secrets.token_hex(4)}"
        attestation.update(
            {
                "purpose": purpose,
                "snapshot_id": snapshot_id,
                "supersedes": normalized_supersedes,
                "review_status": review_status,
            }
        )
        filename = f"{plan_name}--{purpose}--{snapshot_id}.json"
    else:
        filename = f"{plan_name}.json"
    target = root / "docs" / "attestations" / filename
    if binding is not None:
        attestation["binding"] = binding
        try:
            relative = relative_to_root(target, root)
            binding_file(root, relative, require_file=False)
            if target.exists() or relative in {entry["path"] for entry in binding["files"]}:
                raise ValueError("binding 快照目标已存在或引用自身")
            validate_attestation_binding(attestation)
            preflight_errors = []
            warn_attestation_drift([], root, plans, errors=preflight_errors, strict=True,
                                   pending=(target, attestation), enforce_binding_review=False)
            if preflight_errors:
                errors.extend(preflight_errors)
                return None
        except (ValueError, OSError, UnicodeError) as exc:
            fail(errors, f"{plan_name}: binding 创建预检失败：{exc}")
            return None
        created_directory = False
        created_file = False
        try:
            if not target.parent.exists():
                target.parent.mkdir()
                created_directory = True
            with target.open("x", encoding="utf-8") as stream:
                created_file = True
                stream.write(json.dumps(attestation, ensure_ascii=False, indent=2) + "\n")
        except OSError as exc:
            fail(errors, f"{plan_name}: binding 快照写入失败：{exc}")
            for artifact, created in [(target, created_file), (target.parent, created_directory)]:
                if not created:
                    continue
                try:
                    artifact.unlink() if artifact == target else artifact.rmdir()
                except OSError as cleanup_error:
                    fail(errors, f"binding 清理失败，残留路径 {artifact}：{cleanup_error}")
            return None
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(attestation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def attestation_issue(warnings, errors, strict, message):
    if strict:
        fail(errors, message)
    else:
        warn(warnings, message)


def warn_attestation_drift(warnings, root, plans, errors=None, strict=False, reports=None,
                           pending=None, enforce_binding_review=True, selected=None):
    errors = errors if errors is not None else []
    attestations_dir = root / "docs" / "attestations"
    try:
        paths = attestation_paths(root)
        scoped_checks = pending is not None or has_attestation_binding(root)
    except (ValueError, OSError) as exc:
        attestation_issue(warnings, errors, strict, f"{attestations_dir}: 快照清单无法读取：{exc}")
        return

    records = []
    if pending is not None:
        paths.append(pending[0])
    for path in sorted(paths):
        if path.is_symlink():
            attestation_issue(warnings, errors, strict, f"{path}: 快照不能是 symlink")
            continue
        try:
            attestation = pending[1] if pending is not None and path == pending[0] else json.loads(path.read_text(encoding="utf-8"))
        except OSError as exc:
            attestation_issue(warnings, errors, strict, f"{path}: attestation 无法读取：{exc}")
            continue
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            warn(warnings, f"{path}: attestation JSON 无法解析：{exc}")
            continue
        if not isinstance(attestation, dict):
            warn(warnings, f"{path}: attestation JSON 必须为对象")
            continue

        bound = "binding" in attestation
        invalid_structure = False
        plan_name = str(attestation.get("plan", "")).strip()
        if selected and plan_name in plans and plan_name not in selected:
            continue
        if not plan_name or plan_name not in plans:
            message = f"{path}: 快照引用了未登记计划：{plan_name or '<missing>'}"
            if not bound:
                warn(warnings, message)
                continue
            # 删除计划也是可被后继替代的内容变化，记录不能消失。
            warn(warnings, message)

        legacy = "purpose" not in attestation
        purpose = str(attestation.get("purpose", "phase_completion")).strip()
        if purpose not in ATTESTATION_PURPOSES:
            attestation_issue(warnings, errors, strict, f"{path}: attestation purpose 非法：{purpose or '<missing>'}")
            if not bound:
                continue
            invalid_structure = True
        snapshot_id = str(attestation.get("snapshot_id", "")).strip()
        review_status = str(attestation.get("review_status", "current")).strip()
        supersedes = attestation.get("supersedes", "")
        if not legacy:
            for field in ["snapshot_id", "supersedes", "review_status"]:
                if field not in attestation:
                    attestation_issue(warnings, errors, strict, f"{path}: 新 attestation 缺少字段：{field}")
                    invalid_structure = True
            if not ATTESTATION_SNAPSHOT_RE.fullmatch(snapshot_id):
                attestation_issue(warnings, errors, strict, f"{path}: snapshot_id 格式非法：{snapshot_id or '<missing>'}")
                invalid_structure = True
            expected_name = f"{plan_name}--{purpose}--{snapshot_id}.json"
            if path.name != expected_name:
                attestation_issue(warnings, errors, strict, f"{path}: 文件名应为 {expected_name}")
                invalid_structure = True
        if review_status not in ATTESTATION_REVIEW_STATUSES:
            attestation_issue(warnings, errors, strict, f"{path}: review_status 非法：{review_status or '<missing>'}")
            invalid_structure = True
        if not isinstance(supersedes, str):
            attestation_issue(warnings, errors, strict, f"{path}: supersedes 必须是相对路径字符串")
            supersedes = ""
            invalid_structure = True
        normalized_supersedes = safe_relative_path(supersedes) if supersedes else ""
        if supersedes and normalized_supersedes is None:
            attestation_issue(warnings, errors, strict, f"{path}: supersedes 必须是仓库内相对路径：{supersedes}")
            normalized_supersedes = ""
            invalid_structure = True

        binding_changes = []
        if bound:
            try:
                validate_attestation_binding(attestation)
                if path != (pending[0] if pending is not None else None):
                    binding_file(root, path.relative_to(root).as_posix())
            except (ValueError, OSError, UnicodeError) as exc:
                attestation_issue(warnings, errors, strict, f"{path}: binding 结构非法：{exc}")
                invalid_structure = True
            if not invalid_structure:
                try:
                    binding_changes = attestation_binding_drift(root, attestation)
                except (ValueError, OSError, UnicodeError) as exc:
                    binding_changes = [str(exc)]
            records.append({"path": path, "relative_path": path.relative_to(root).as_posix(),
                            "plan": plan_name, "purpose": purpose, "review_status": review_status,
                            "supersedes": normalized_supersedes, "drifted": bool(binding_changes),
                            "legacy": legacy, "invalid_structure": invalid_structure,
                            "bound": True, "binding_changes": binding_changes})
            continue

        plan_path_value = attestation.get("plan_path", "")
        plan_map_path_value = attestation.get("plan_map_path", "docs/PLAN_MAP.md")
        plan_path_rel = safe_relative_path(plan_path_value)
        plan_map_path_rel = safe_relative_path(plan_map_path_value)
        if plan_path_rel is None:
            warn(warnings, f"{path}: 快照引用的计划路径非法：{plan_path_value}")
            continue
        if plan_map_path_rel is None:
            warn(warnings, f"{path}: 快照引用的 PLAN_MAP 路径非法：{plan_map_path_value}")
            continue
        plan_path = root / plan_path_rel
        plan_map_path = root / plan_map_path_rel
        if scoped_checks:
            try:
                binding_file(root, plan_path_rel, require_file=plan_path.exists())
                binding_file(root, plan_map_path_rel)
            except (ValueError, OSError) as exc:
                attestation_issue(warnings, errors, strict, f"{path}: 混合快照路径读取预检失败：{exc}")
                continue
        if not plan_map_path.exists():
            warn(warnings, f"{path}: 快照引用的 PLAN_MAP.md 不存在：{plan_map_path}")
            continue

        # A moved plan leaves the historical snapshot's recorded path behind.
        # Keep that legacy record in the supersedes graph; an explicit valid
        # successor can retire it, while an unretired record remains needs_review.
        missing_plan = not plan_path.exists()
        drift_reasons = []
        if missing_plan:
            drift_reasons.append(f"快照引用的计划文件不存在：{plan_path}")
        try:
            if not missing_plan and sha256_file(plan_path) != attestation.get("plan_sha256"):
                drift_reasons.append(f"{plan_name} 计划文件 hash 已变化，需要人工复核")
            if sha256_file(plan_map_path) != attestation.get("plan_map_sha256"):
                drift_reasons.append("PLAN_MAP.md hash 已变化，需要人工复核")
        except OSError as exc:
            if not scoped_checks:
                raise
            # 内容不可读不使已存在的替代目标消失，也不阻止后续绑定报告。
            attestation_issue(warnings, errors, strict, f"{path}: 混合快照内容读取失败：{exc}")
            drift_reasons.append(f"快照内容读取失败：{exc}")
        records.append(
            {
                "path": path,
                "relative_path": path.relative_to(root).as_posix(),
                "plan": plan_name,
                "purpose": purpose,
                "review_status": review_status,
                "supersedes": normalized_supersedes,
                "drifted": bool(drift_reasons),
                "legacy": legacy,
                "invalid_structure": invalid_structure,
                "bound": False,
                "plan_path": plan_path,
                "drift_reasons": drift_reasons,
            }
        )

    by_path = {record["relative_path"]: record for record in records}
    incoming = {}
    edges = {}
    for record in records:
        target = record["supersedes"]
        if not target:
            continue
        target_record = by_path.get(target)
        if target_record is None:
            attestation_issue(warnings, errors, strict, f"{record['path']}: supersedes 目标不存在：{target}")
            record["invalid_structure"] = True
            continue
        if target_record["purpose"] != record["purpose"] or target_record["plan"] != record["plan"]:
            attestation_issue(
                warnings,
                errors,
                strict,
                f"{record['path']}: supersedes 目标必须与当前快照属于同一计划和 purpose：{target}",
            )
            record["invalid_structure"] = True
            continue
        if target == record["relative_path"]:
            attestation_issue(warnings, errors, strict, f"{record['path']}: supersedes 不能指向自身")
            record["invalid_structure"] = True
            continue
        if target_record["bound"] and not record["bound"]:
            attestation_issue(warnings, errors, strict, f"{record['path']}: binding 前驱必须由带 binding 的后继替代")
            record["invalid_structure"] = True
            continue
        incoming.setdefault(target, []).append(record["relative_path"])
        edges.setdefault(record["relative_path"], []).append(target)

    cycles = detect_dependency_cycles(edges)
    for cycle in cycles:
        attestation_issue(warnings, errors, strict, f"attestation supersedes 存在环：{cycle}")
        for node in cycle.split(" -> "):
            if node in by_path:
                by_path[node]["invalid_structure"] = True

    # 新范围关系的结构错误向后继传播，不能通过损坏中间节点压掉前驱。
    changed = True
    while changed:
        changed = False
        for record in records:
            target_record = by_path.get(record["supersedes"])
            if (target_record and (record["bound"] or target_record["bound"])
                    and target_record["invalid_structure"] and not record["invalid_structure"]):
                attestation_issue(warnings, errors, strict, f"{record['path']}: supersedes 目标结构无效")
                record["invalid_structure"] = True
                changed = True
    incoming = {target: [source for source in sources
                        if not (by_path[target]["bound"] or by_path[source]["bound"])
                        or not (by_path[target]["invalid_structure"] or by_path[source]["invalid_structure"])]
                for target, sources in incoming.items()}

    current_by_key = {}
    for record in records:
        effective = record["review_status"]
        if record["invalid_structure"]:
            effective = "needs_review"
        elif incoming.get(record["relative_path"]):
            effective = "superseded"
        elif record["drifted"] or record["review_status"] == "needs_review":
            effective = "needs_review"
        if effective == "current":
            key = (record["plan"], record["purpose"])
            current_by_key.setdefault(key, []).append(record["relative_path"])
        record["effective_status"] = effective
        if effective != "superseded":
            for reason in record.get("drift_reasons", []):
                warn(warnings, f"{record['path']}: {reason}")

    for key, paths in current_by_key.items():
        if len(paths) > 1:
            attestation_issue(
                warnings,
                errors,
                strict,
                f"attestation 同一计划/purpose 存在多个 current：{key[0]}/{key[1]}：{', '.join(paths)}",
            )
            for record in records:
                if record["relative_path"] in paths:
                    record["effective_status"] = "needs_review"

    if enforce_binding_review:
        for record in records:
            if not record["bound"]:
                continue
            pending_review = record["drifted"] or record["review_status"] == "needs_review"
            if pending_review:
                details = ", ".join(record["binding_changes"]) or "声明待复核"
                # 有效替代仅免除历史内容漂移，存储结构错误在上面仍阻断。
                retired = bool(incoming.get(record["relative_path"]))
                label = "binding 历史内容已变化，已有有效替代" if retired else "binding 需要复核"
                attestation_issue(warnings, errors, strict and not retired, f"{record['path']}: {label}：{details}")

    if reports is not None:
        for record in records:
            reports.append(
                f"{record['relative_path']} | plan={record['plan']} | purpose={record['purpose']} | status={record['effective_status']}"
            )


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
    if len(re.findall(r"^##\s+计划索引\s*$", mask_fenced_code(plan_map_text), re.MULTILINE)) > 1:
        issues.append("PLAN_MAP 存在重复计划索引章节，无法安全派生工作集")
    seen = set()
    for row_index, row in enumerate(table_rows(plan_map_text, "计划索引"), start=1):
        if len(row) < 6:
            issues.append(f"计划索引第 {row_index} 行字段不足，无法安全派生工作集")
            continue
        link = extract_plan_link(row[0])
        if not link:
            issues.append(f"计划索引第 {row_index} 行缺少计划链接，无法安全派生工作集")
            continue
        path_issue = plan_link_issue(link)
        if path_issue:
            issues.append(f"计划索引第 {row_index} 行路径无效：{path_issue}")
        name = Path(link).stem
        if name in seen:
            issues.append(f"计划索引存在重复计划 ID：{name}")
        seen.add(name)
        status = row[1].strip("` ")
        if status not in VALID_STATUSES:
            issues.append(f"{name}: 计划状态非法：{status}")
        try:
            parse_plan_date(row[3].strip("` "))
        except ValueError:
            issues.append(f"{name}: 最后更新日期不合法：{row[3]}")
    return issues


def unresolved_current_blockers(plan_text):
    return problem_blockers(plan_text)[0]


CLOSED_BLOCKER_STATES = {"已决定", "已收敛", "已完成", "已解决", "已关闭", "无", "resolved", "closed", "done"}
OPEN_BLOCKER_STATES = {"open", "待确认", "未解决", "待处理", "未决定", "待补充"}


def blocker_is_open(impact, state, label, issues):
    impact, state = impact.strip().lower(), state.strip().lower()
    if impact in {"否", "no"} or state in CLOSED_BLOCKER_STATES:
        return False
    if impact not in {"是", "yes"}:
        issues.append(f"{label}: 是否阻塞当前阶段为空或未知：{impact or '(空)'}")
        return False
    if state not in OPEN_BLOCKER_STATES:
        issues.append(f"{label}: 当前阻塞状态为空或未知：{state or '(空)'}")
    return True


def problem_blockers(plan_text):
    blockers, issues = [], []
    for row in table_rows(plan_text, "未决问题"):
        if not any(row):
            continue
        if len(row) < 4:
            issues.append("未决问题表字段不足，无法确认当前阻塞")
            continue
        label = row[0] or "未命名阻塞项"
        if blocker_is_open(row[2], row[3], label, issues):
            blockers.append(label)
    return blockers, issues


def map_blockers(plan_map_text):
    """只按显式 ID/链接归属；无法归属的开放行保留为全局诊断。"""
    names = {
        Path(link).stem for row in table_rows(plan_map_text, "计划索引")
        if row and (link := extract_plan_link(row[0]))
    }
    result, issues = {}, []
    if len(re.findall(r"^##\s+当前阻塞项\s*$", mask_fenced_code(plan_map_text), re.MULTILINE)) > 1:
        issues.append("PLAN_MAP 存在重复当前阻塞项章节，无法确认阻塞来源")
    for row in table_rows(plan_map_text, "当前阻塞项"):
        if not any(row):
            continue
        if len(row) < 5:
            issues.append("PLAN_MAP 当前阻塞项字段不足，无法归属")
            continue
        label = row[0] or "未命名阻塞项"
        if not blocker_is_open(row[3], row[4], f"PLAN_MAP {label}", issues):
            continue
        scope = re.sub(
            r"\[[^\]]+\]\(((?:\./)?plans/[^)#]+\.md)(?:#[^)]*)?\)",
            lambda match: Path(match.group(1)).stem,
            row[2],
        ).replace("`", "")
        targets = set(filter(None, re.split(r"[,，、/;；\s]+", scope.strip())))
        if not targets or targets - names:
            issues.append(f"PLAN_MAP 当前阻塞项 {label} 的影响范围无法归属：{row[2]}")
            continue
        for name in sorted(targets):
            result.setdefault(name, []).append(label)
    return result, issues


def structural_ambiguities(plan_text, phase):
    issues = []
    current = top_level_section(plan_text, "当前阶段") or ""
    sections = [(plan_text, "当前阶段"), (current, "阶段准入摘要"),
                (plan_text, "最新独立准入复核"), (plan_text, "阶段路线图"),
                (plan_text, "独立复核记录"), (plan_text, "未决问题")]
    if "复核策略" in key_value_table(fixed_section(current, "阶段准入摘要")):
        sections.extend([(plan_text, "最新阶段复核"), (plan_text, "阶段复核记录")])
    for text, title in sections:
        level = "##" if title in {"当前阶段", "未决问题"} else "#+"
        if len(re.findall(rf"^{level}\s+{re.escape(title)}\s*$", mask_fenced_code(text), re.MULTILINE)) > 1:
            issues.append(f"重复结构化章节：{title}")
        if title in {"阶段准入摘要", "最新独立准入复核", "最新阶段复核"}:
            seen = set()
            for row in markdown_table_rows(fixed_section(text, title)):
                if len(row) < 2 or row[0] == "字段":
                    continue
                if row[0] in seen:
                    issues.append(f"{title} 存在重复字段：{row[0]}")
                seen.add(row[0])
    if len([r for r in phase_roadmap_rows(plan_text) if r[0] == phase]) > 1:
        issues.append(f"阶段路线图重复当前阶段：{phase}")
    return issues


def phase_gate(plan_map_text, plan_name, data, plan_text, selected=False):
    """共享只读派生；严重级别由 check/workset/hook 的入口契约决定。"""
    issues = structural_ambiguities(plan_text, data["phase"])
    warnings = []
    review_state = risk_review_state(plan_text, data["phase"])
    check_phase_structure(plan_name, data, plan_text, True, warnings, issues, review_state, selected=selected)
    if review_state["enabled"]:
        issues.extend(review_state["issues"] + review_state["blockers"])
    if data["status"] in ACTIVE and is_placeholder(data["phase"]):
        issues.append("PLAN_MAP 当前阶段为空或占位")
    details, detail_issues = problem_blockers(plan_text)
    issues.extend(detail_issues)
    mapped, _ = map_blockers(plan_map_text)
    indexed = mapped.get(plan_name, [])
    summary = current_summary(plan_text)
    value = summary.get("当前阻塞项", "").strip()
    declared = [value] if value and not is_placeholder(value) and not re.match(r"^无(?:[；;，,。]|$)", value) else []
    blockers = list(dict.fromkeys(details + indexed + declared))
    issue_codes = {}
    if blockers:
        message = "当前阶段存在未解决阻塞项：" + "；".join(blockers)
        issues.append(message)
        issue_codes[message] = "CURRENT_PHASE_BLOCKED"
        if ((details or indexed) and value == "无") or ((details or declared) and not indexed):
            issues.append("当前阻塞来源需同步：PLAN_MAP 索引、未决问题或阶段准入摘要缺失/冲突")
    if review_state["enabled"]:
        blockers.extend(review_state["blockers"])
    else:
        legacy_state = legacy_review_state(plan_text, data["phase"])
        history = [r for r in review_history_rows(plan_text) if len(r) == 6 and r[2] == data["phase"]]
        completion_positions = [i for i, r in enumerate(history)
                                if "完成" in r[1] and review_outcome(r[3]) == "passed"
                                and valid_review_date(r[0]) is not None
                                and not any(is_placeholder(v) for v in r)]
        completed_review = (data["status"] in COMPLETED and completion_positions
                            and all(review_outcome(r[3]) == "passed" for r in history[completion_positions[-1]:]))
        if not completed_review:
            blockers.extend(legacy_state["blockers"])
        review = key_value_table(fixed_section(plan_text, "最新独立准入复核"))
        conclusion = review.get("结论", "").strip()
        if review.get("阶段") == data["phase"] and conclusion.startswith(("未通过", "不通过", "失败", "不满足", "拒绝")):
            blockers.append("最新独立准入复核：" + conclusion)
            if data["status"] not in ACTIVE:
                issues.append(blockers[-1])
    _, recent_warnings = current_recent_evidence(plan_text, data["phase"])
    warnings.extend(recent_warnings)
    issues = [message.removeprefix(f"{plan_name}: ") for message in issues]
    return {"blockers": list(dict.fromkeys(blockers)), "issues": list(dict.fromkeys(issues)),
            "warnings": warnings, "review": review_state, "issue_codes": issue_codes}


def check_phase_readiness(plan_map_text, plan_name, data, plan_text, strict, warnings, errors, selected=False):
    if selected and data["status"] in INACTIVE:
        readiness_issue(warnings, errors, strict, f"{plan_name}: 已废弃/替代/合并的计划不能准入")
        return
    if data["status"] not in WARNING_ACTIVE:
        return
    gate = phase_gate(plan_map_text, plan_name, data, plan_text, selected=selected)
    warnings.extend(f"{plan_name}: {message}" for message in gate["warnings"])
    for message in gate["issues"]:
        for target in (errors, warnings):
            if isinstance(target, DiagnosticList):
                sources = target.metadata["sources"]
                target.context(plan_name, data["phase"], category="readiness",
                               code=gate["issue_codes"].get(message, "PHASE_NOT_READY"),
                               path=sources[0]["path"] if sources else data["path"], section="当前阶段")
        # 缺失材料的设计计划仍合法；其显式冲突和阻塞保持可见而不强制准入。
        readiness_issue(warnings, errors, strict and (data["status"] in ACTIVE or selected), f"{plan_name}: {message}")


def top_level_section(text, heading):
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.MULTILINE)
    masked = mask_fenced_code(text)
    match = pattern.search(masked)
    if not match:
        return None
    tail = text[match.end():]
    next_heading = re.search(r"^##\s+", masked[match.end():], re.MULTILINE)
    return tail[: next_heading.start()] if next_heading else tail


def current_summary(plan_text):
    return key_value_table(fixed_section(top_level_section(plan_text, "当前阶段"), "阶段准入摘要"))


def current_review_passes(plan_text, phase):
    return legacy_review_state(plan_text, phase)["passed"]


def structured_next_action(plan_text):
    section = mask_fenced_code(top_level_section(plan_text, "当前阶段") or "")
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
        "等待用户验收": "none",
    }
    if not value:
        return {"state": "unknown", "kind": "unknown", "reason": "缺少结构化下一动作"}
    kind = mapping.get(value.lower(), "unknown")
    if kind == "unknown":
        return {"state": "unknown", "kind": "unknown", "reason": f"下一动作值无法识别：{value}"}
    if value == "等待用户验收":
        return {"state": "known", "kind": "none", "reason": "等待用户验收；技术完成不自动关闭计划"}
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
    first_path = next(iter(plans.values()))["path"]
    plans_dir = next((parent for parent in first_path.parents if parent.name == "plans"), None)
    docs_root = plans_dir.parent if plans_dir else first_path.parent.parent
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


def current_recent_evidence(plan_text, phase=None):
    current = top_level_section(plan_text, "当前阶段") or ""
    section = fixed_section(current, "最近实施/验证记录")
    warnings = []
    if section is None and phase:
        for title in [f"{phase} 最近验证记录", f"{phase} 最近实施/验证记录"]:
            section = fixed_section(current, title)
            if section is not None:
                warnings.append(f"兼容记录标题 `{title}`，请使用固定标题 `最近实施/验证记录`")
                break
    rows = markdown_table_rows(section)
    return [row for row in rows if len(row) >= 2 and row[0] not in {"日期", "字段", "类型"}], warnings


def recent_evidence(plan_text, phase=None):
    return current_recent_evidence(plan_text, phase)[0]


class UsageError(ValueError):
    pass


def validate_options(parser, argv, repeatable=()):
    """Argparse handles values/types; reject ambiguous duplicate declarations."""
    seen = set()
    for token in argv:
        if token == "--":
            break
        option = token.split("=", 1)[0]
        action = parser._option_string_actions.get(option)
        if action is None or action.dest in repeatable:
            continue
        if action.dest in seen:
            parser.error(f"{option} 只能指定一次")
        seen.add(action.dest)


def nonempty(value):
    if not value.strip():
        raise argparse.ArgumentTypeError("参数值不能为空")
    return value


def scoped_table(text, title, keep):
    section = top_level_section(text, title)
    if section is None:
        return text
    rows = markdown_table_rows(section)
    selected = [row for i, row in enumerate(rows) if i == 0 or keep(row)]
    replacement = "\n\n" + "\n".join("| " + " | ".join(row) + " |" for row in selected) + "\n\n"
    start = re.search(rf"^##\s+{re.escape(title)}\s*$", mask_fenced_code(text), re.MULTILINE).end()
    return text[:start] + replacement + text[start + len(section):]


def scoped_map(text, names):
    for title in ("阶段关系", "机器可检查共享写入约束"):
        text = scoped_table(text, title, lambda row: len(row) < 3 or bool({clean_relation_value(row[0]), clean_relation_value(row[2])} & names))
    return text


def historical_phase_review(text, phase):
    """复用历史校验，不使用后续阶段的最新结果替代来源阶段。"""
    for title, width in (("阶段复核记录", 8), ("独立复核记录", 6)):
        rows = markdown_table_rows(fixed_section(text, title))
        expected = (["日期", "类型", "阶段", "方式", "风险", "结论", "证据", "复核者"]
                    if width == 8 else ["日期", "类型", "阶段", "结论", "证据", "复核者"])
        relevant = [r for r in rows[1:] if len(r) < 3 or r[2] == phase or not valid_phase_name(r[2])]
        if relevant and (rows[0] != expected or rows.count(expected) > 1
                         or any(len(r) != width or len(r) < 3 or not valid_phase_name(r[2]) for r in relevant)):
            return {"passed": False, "issues": [f"来源阶段 {phase} 的 {title} 结构无效"], "blockers": []}
    explicit = [r for r in markdown_table_rows(fixed_section(text, "阶段复核记录")) if len(r) == 8 and r[2] == phase]
    legacy = [r for r in review_history_rows(text) if len(r) == 6 and r[2] == phase]
    if explicit:
        row = explicit[-1]
        latest = dict(zip(["日期", "阶段", "方式", "风险", "结论", "证据", "复核者"], [row[0], row[2], *row[3:]]))
        latest["风险依据"] = "来源阶段历史证据"
        synthetic = "## 当前阶段\n\n### 阶段准入摘要\n\n| 字段 | 内容 |\n|---|---|\n| 复核策略 | 默认自验 |\n| 最新阶段复核 | #最新阶段复核 |\n\n## 最新阶段复核\n\n| 字段 | 内容 |\n|---|---|\n"
        synthetic += "\n".join(f"| {key} | {value} |" for key, value in latest.items())
        synthetic += "\n\n## 阶段复核记录\n\n| 日期 | 类型 | 阶段 | 方式 | 风险 | 结论 | 证据 | 复核者 |\n|---|---|---|---|---|---|---|---|\n"
        synthetic += "\n".join("| " + " | ".join(r) + " |" for r in explicit)
        return risk_review_state(synthetic, phase)
    if legacy:
        row = legacy[-1]
        synthetic = "## 最新独立准入复核\n\n| 字段 | 内容 |\n|---|---|\n"
        synthetic += "\n".join(f"| {key} | {value} |" for key, value in zip(["日期", "阶段", "结论", "证据", "复核者"], [row[0], *row[2:]]))
        synthetic += "\n\n## 独立复核记录\n\n| 日期 | 类型 | 阶段 | 结论 | 证据 | 复核者 |\n|---|---|---|---|---|---|\n"
        synthetic += "\n".join("| " + " | ".join(r) + " |" for r in legacy)
        return legacy_review_state(synthetic, phase)
    return {"passed": False, "issues": [f"来源阶段 {phase} 缺少有效复核历史"], "blockers": []}


def build_scope(root, requested, text, plans):
    if len(requested) != len(set(requested)):
        raise UsageError("--plan 不接受重复计划 ID")
    unknown = set(requested) - set(plans)
    if unknown:
        raise UsageError("未登记的 --plan：" + "、".join(sorted(unknown)))
    scope = {"requested_plans": requested, "focused_phases": [{"plan": n, "phase": plans[n]["phase"]} for n in requested],
             "evaluated_plans": list(requested), "dependencies": [], "evidence_links": [], "shared_writes": [], "global_diagnostics": []}
    relation_header, relations = relation_rows(text)
    shared_header, shared = shared_write_rows(text)
    relations = [[clean_relation_value(cell) for cell in row] for row in relations]
    shared = [[clean_relation_value(cell) for cell in row] for row in shared]
    if relation_header == [] or shared_header == []:
        scope["global_diagnostics"].append("相关关系表缺少固定表头，无法可信确认作用域")
    queue = [(name, plans[name]["phase"]) for name in requested]
    visited = set()
    edges = {}
    for name, phase in queue:
        if (name, phase) in visited:
            continue
        visited.add((name, phase))
        # 已完成前置由完成证据核验，不重新开启其已经关闭的历史依赖链。
        if plans[name]["status"] in COMPLETED:
            continue
        incoming = [r for r in relations if len(r) == 7 and clean_relation_value(r[2]) == name and clean_relation_value(r[3]) == phase and r[4] == "hard_gate"]
        predecessors = [(clean_relation_value(r[0]), clean_relation_value(r[1]), r[5], r[6]) for r in incoming]
        explicit = {row[0] for row in predecessors}
        for dep in extract_declared_dependencies(plans[name]["depends"]) if phase == plans[name]["phase"] else []:
            if dep not in explicit:
                predecessors.append((dep, plans.get(dep, {}).get("phase", ""), "计划索引依赖", "PLAN_MAP.md"))
        for dep, source_phase, unlock, evidence in predecessors:
            if dep not in plans:
                scope["global_diagnostics"].append(f"{name}: 必要前置不存在：{dep}")
                continue
            edges.setdefault(f"{name}@{phase}", []).append(f"{dep}@{source_phase}")
            record = {"plan": dep, "phase": source_phase, "required_by": name, "reason": unlock, "evidence": evidence}
            if record not in scope["dependencies"]:
                scope["dependencies"].append(record)
            queue.append((dep, source_phase))
    for cycle in detect_dependency_cycles(edges):
        scope["global_diagnostics"].append(f"相关阶段依赖存在环：{cycle}")
    names = {name for name, _ in visited}
    scope["evaluated_plans"] = sorted(names)
    filtered = scoped_map(text, names)
    for row in relations:
        if len(row) == 7 and {row[0], row[2]} & names and row[4] in {"evidence", "soft_context"}:
            scope["evidence_links"].append({"plan": row[0], "phase": row[1], "required_by": row[2], "relation": row[4], "evidence": row[6]})
    for row in shared:
        if len(row) == 9 and {row[0], row[2]} & names:
            scope["shared_writes"].append({"plans": [row[0], row[2]], "targets": row[5], "order": row[6], "reason": row[7], "evidence": row[8]})
    # 同伴仅检查范围声明，不投影其业务状态。
    affected = {}
    for name, data in plans.items():
        if name in names or data["status"] in WARNING_ACTIVE:
            try:
                affected[name] = extract_affected_targets(data["path"].read_text(encoding="utf-8"))
            except (OSError, UnicodeError):
                affected[name] = []
    for name in requested:
        for peer, targets in affected.items():
            if peer in requested:
                continue
            overlap = sorted({a for a in affected.get(name, []) for b in targets if a == b or a.startswith(b.rstrip("/") + "/") or b.startswith(a.rstrip("/") + "/")})
            if overlap:
                scope["shared_writes"].append({"plans": [name, peer], "targets": overlap, "reason": "影响范围重叠；需要单一写入或串行合并"})
    projection = {"index": [r for r in table_rows(text, "计划索引") if r and (link := extract_plan_link(r[0])) and Path(link).stem in names],
                  "relations": [r for r in relations if len(r) < 3 or {r[0], r[2]} & names],
                  "shared": scope["shared_writes"], "headers": [relation_header, shared_header],
                  "scope_issues": scope["global_diagnostics"], "identity_issues": plan_index_issues(text),
                  "blockers": {k: v for k, v in map_blockers(text)[0].items() if k in names}, "blocker_issues": map_blockers(text)[1]}
    contents = {}
    for name in sorted(names):
        try:
            contents[name] = sha256_file(plans[name]["path"])
        except OSError:
            contents[name] = None
    scope["facts_version"] = hashlib.sha256(json.dumps([projection, contents], ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    return scope, filtered


def dependency_diagnostics(root, scope, text, plans):
    errors = list(scope["global_diagnostics"])
    for dep in scope["dependencies"]:
        name, phase = dep["plan"], dep["phase"]
        data = plans[name]
        read_errors = []
        body = read_utf8(data["path"], read_errors)
        reasons = list(read_errors)
        if data["status"] in INACTIVE:
            reasons.append("必要前置已废弃/替代，须确认有效承接")
        elif phase != data["phase"]:
            review = historical_phase_review(body, phase)
            reasons.extend(review["issues"] + review["blockers"])
            if not review["passed"]:
                reasons.append(f"来源阶段 {phase} 未通过")
        elif data["status"] in COMPLETED:
            if not has_completion_evidence(body) or not has_coverage_evidence(body):
                reasons.append("已完成前置缺少完成/验证证据")
            reasons.extend(phase_gate(text, name, data, body)["blockers"])
        else:
            gate = phase_gate(text, name, data, body)
            reasons.extend(gate["issues"])
            review = gate["review"] if gate["review"]["enabled"] else legacy_review_state(body, phase)
            if not review["passed"]:
                reasons.append("必要前置当前阶段尚未通过")
        dep["phase_passed"] = not reasons
        dep["blockers"] = list(dict.fromkeys(reasons))
        errors.extend(f"{name}@{phase}: {reason}" for reason in dep["blockers"])
    return list(dict.fromkeys(errors))


def scope_unchanged(root, scope):
    errors = []
    text, _, plans = load_plan_records(root, errors)
    if errors or plan_index_issues(text):
        return False
    try:
        fresh, _ = build_scope(root, scope["requested_plans"], text, plans)
        return fresh["facts_version"] == scope["facts_version"]
    except (UsageError, OSError, ValueError):
        return False


def workset_payload(root, include_history=False, strict=False, requested=None):
    if not requested:
        return unscoped_workset_payload(root, include_history, strict)
    errors = []
    text, _, plans = load_plan_records(root, errors)
    errors.extend(plan_index_issues(text))
    empty = {"schema_version": 1, "source": "derived", "plans": [], "warnings": errors,
             "scope": {"requested_plans": requested, "evaluated_plans": [], "dependencies": []}}
    if errors:
        return empty, 1
    scope, selected_map = build_scope(root, requested, text, plans)
    output, status = unscoped_workset_payload(root, include_history, strict, focus=requested, supplied=(selected_map, plans))
    dep_errors = dependency_diagnostics(root, scope, selected_map, plans)
    output["warnings"].extend(dep_errors)
    output["scope"] = scope
    blocked = {d["required_by"] for d in scope["dependencies"] if not d["phase_passed"]}
    while True:
        expanded = blocked | {d["required_by"] for d in scope["dependencies"] if d["plan"] in blocked}
        if expanded == blocked:
            break
        blocked = expanded
    for item in output["plans"]:
        if item["plan"] in blocked or scope["global_diagnostics"]:
            item["readiness"] = "blocked"
            item["next_action"] = {"state": "known", "kind": "resolve_blocker", "reason": "必要前置尚未满足，见 scope.dependencies"}
    if not scope_unchanged(root, scope):
        output["warnings"].append("相关事实在读取期间发生变化；请重读聚焦工作集")
        for item in output["plans"]:
            item["readiness"] = "unknown"
            item["next_action"] = {"state": "unknown", "kind": "unknown", "reason": "相关事实已变更"}
        status = 1 if strict else status
    return output, 1 if scope["global_diagnostics"] or (strict and dep_errors) else status


def unscoped_workset_payload(root, include_history=False, strict=False, focus=None, supplied=None):
    errors = []
    strict_failures = []
    document_failures = []
    if supplied:
        plan_map_text, plans = supplied
    else:
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
    _, blocker_index_issues = map_blockers(plan_map_text)
    output["warnings"].extend(blocker_index_issues)
    strict_failures.extend(blocker_index_issues)
    relation_errors, relation_warnings = validate_relation_graph(plan_map_text, plans)
    output["warnings"].extend(relation_warnings)
    if relation_errors:
        output["warnings"].extend(relation_errors)
        strict_failures.extend(relation_errors)

    for name, data in plans.items():
        if focus and name not in focus:
            continue
        if not focus and not include_history and data["status"] not in WARNING_ACTIVE:
            continue
        path = data["path"]
        if not path.exists():
            message = f"{name}: 计划文件不存在：{path}"
            output["warnings"].append(message)
            strict_failures.append(message)
            document_failures.append(message)
            continue
        plan_text = read_utf8(path, errors)
        summary = current_summary(plan_text)
        gate = phase_gate(plan_map_text, name, data, plan_text, selected=bool(focus) and strict and data["status"] in WARNING_ACTIVE)
        blockers = gate["blockers"]
        output["warnings"].extend(f"{name}: {message}" for message in gate["issues"] + gate["warnings"])
        if data["status"] in ACTIVE or focus:
            strict_failures.extend(gate["issues"])
        uncertain = gate["issues"] or blocker_index_issues or relation_errors
        if blockers:
            readiness = "blocked"
            action = {
                "state": "known",
                "kind": "resolve_blocker",
                "reason": "当前阶段存在未解决阻塞项",
            }
        elif uncertain and data["status"] in WARNING_ACTIVE:
            readiness = "unknown"
            action = {"state": "unknown", "kind": "unknown", "reason": "准入信息存在缺失或冲突，见 warnings"}
        elif data["status"] == "待实施":
            readiness = "ready"
            action = {"state": "known", "kind": "implement", "reason": "待实施计划的结构化准入检查通过"}
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
            elif gate["review"]["enabled"]:
                readiness = "design"
                kind = "sync" if gate["review"]["passed"] else gate["review"]["pending_action"]
                action = {
                    "state": "known" if kind else "unknown",
                    "kind": kind or "unknown",
                    "reason": ("当前阶段复核通过，待同步 PLAN_MAP 准入状态" if kind == "sync" else
                               "当前阶段待自验" if kind == "verify" else
                               "当前阶段待独立复核" if kind == "independent_review" else
                               "当前阶段复核声明无法确定"),
                }
            elif not current_review_passes(plan_text, data["phase"]):
                legacy_state = legacy_review_state(plan_text, data["phase"])
                kind = legacy_state["pending_action"] or "verify"
                readiness = "design"
                action = {
                    "state": "known",
                    "kind": kind,
                    "reason": ("当前阶段待自验" if kind == "verify" else
                               "用户已明确要求独立复核"),
                }
            else:
                readiness = "design"
                action = {"state": "unknown", "kind": "unknown", "reason": "缺少结构化下一动作"}
        elif focus and data["status"] in COMPLETED:
            valid = has_completion_evidence(plan_text) and has_coverage_evidence(plan_text) and not blockers
            readiness = "unknown"
            action = {"state": "unknown", "kind": "unknown", "reason": "当前完成声明已检查；终态无下一实施动作" if valid else "完成声明缺少有效证据"}
            if not valid:
                strict_failures.append(f"{name}: 完成声明缺少有效证据")
                document_failures.append(f"{name}: 完成声明缺少有效证据")
        elif focus and data["status"] in INACTIVE:
            readiness = "unknown"
            action = {"state": "unknown", "kind": "unknown", "reason": "终态计划不能准入"}
            strict_failures.append(f"{name}: 终态计划不能准入")
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
                "recent_evidence": recent_evidence(plan_text, data["phase"]),
            }
        )

    if errors:
        output["warnings"].extend(errors)
        strict_failures.extend(errors)
    if index_issues:
        output["plans"] = []
        output["warnings"].extend(index_issues)
        strict_failures.extend(index_issues)
    return output, 1 if errors or index_issues or document_failures or (strict and strict_failures) else 0


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
        level = "ERROR" if strict and "兼容记录标题" not in warning else "WARNING"
        print(f"{level}: {warning}")


def limit_workset_evidence(root, payload, limit):
    """裁剪 JSON 阅读窗口；完整 payload 和门禁结果保持不变。"""
    result = {**payload, "plans": []}
    if not payload["plans"]:
        return result
    source_errors = []
    _, _, records = load_plan_records(root, source_errors)
    if source_errors:
        records = {}
    for item in payload["plans"]:
        rows = item["recent_evidence"]
        source = None
        record = records.get(item["plan"])
        if record and record["phase"] == item["phase"]:
            errors = []
            text = read_utf8(record["path"], errors)
            # 来源只辅助回查；再次读取失败或内容变化不能伪造定位。
            if not errors and recent_evidence(text, item["phase"]) == rows:
                current = top_level_section(text, "当前阶段") or ""
                titles = ["最近实施/验证记录"]
                if item["phase"]:
                    titles.extend([f"{item['phase']} 最近验证记录", f"{item['phase']} 最近实施/验证记录"])
                section = next((title for title in titles if fixed_section(current, title) is not None), None)
                try:
                    path = record["path"].relative_to(root).as_posix()
                except ValueError:
                    path = record["path"].as_posix()
                source = {"path": path, "section": section}
        shown = rows[-limit:]
        result["plans"].append({
            **item,
            "recent_evidence": shown,
            "recent_evidence_window": {
                "total": len(rows), "omitted": len(rows) - len(shown), "source": source,
            },
        })
    return result


def run_workset(root, as_json=False, include_history=False, strict=False, evidence_limit=None, requested=None):
    payload, status = workset_payload(root, include_history=include_history, strict=strict, requested=requested)
    if as_json:
        if evidence_limit is not None:
            payload = limit_workset_evidence(root, payload, evidence_limit)
            scope = payload.get("scope")
            if scope and scope.get("facts_version") and not scope_unchanged(root, scope):
                payload["warnings"].append("证据窗口读取期间相关事实发生变化；请重读聚焦工作集")
                for item in payload["plans"]:
                    item["readiness"] = "unknown"
                    item["next_action"] = {"state": "unknown", "kind": "unknown", "reason": "相关事实已变更"}
                status = 1 if strict else status
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_workset_text(payload, strict=strict)
    return status


class DiagnosticList(list):
    def __init__(self, records, severity):
        super().__init__()
        self.records = records
        self.severity = severity
        self.context()

    def context(self, plan=None, phase=None, category="document", code=None, path=None, section=None):
        self.metadata = {"plan": plan, "phase": phase, "category": category,
                         "code": code or ("DOCUMENT_ERROR" if category == "document" else "PHASE_NOT_READY"),
                         "sources": [{"path": str(path), "section": section}] if path else []}

    def append(self, value):
        super().append(value)
        self.records.append({**self.metadata, "severity": self.severity, "message": value})

    def extend(self, values):
        for value in values:
            self.append(value)


def finish_check(args, records, scope=None, reports=None, attested_path=None, not_applicable=False):
    unique = {}
    for item in records:
        key = (item["plan"], item["phase"], item["code"], item["message"])
        if key not in unique or item["severity"] == "error":
            unique[key] = item
    diagnostics = list(unique.values())
    counts = {level + "s": sum(item["severity"] == level for item in diagnostics) for level in ("error", "warning")}
    status = "failed" if counts["errors"] else "not_applicable" if not_applicable else "warning" if counts["warnings"] else "passed"
    code = 1 if counts["errors"] else 0
    result = {"schema_version": 1, "command": "check", "mode": "readiness" if args.strict_readiness else "consistency",
              "status": status, "exit_code": code, "scope": scope or {"requested_plans": [], "evaluated_plans": getattr(args, "evaluated_plans", []), "dependencies": []},
              "summary": counts, "diagnostics": diagnostics}
    if reports:
        result["attestations"] = reports
    if attested_path:
        result["created_attestation"] = str(attested_path)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for item in diagnostics:
            print(f"{item['severity'].upper()}: {item['message']}", file=sys.stderr if item["severity"] == "error" else sys.stdout)
        for report in reports or []:
            print(f"ATTESTATION: {report}")
        if attested_path:
            print(f"已创建完成快照：{attested_path}")
        if not code:
            if not_applicable:
                print("未执行：当前目录未启用计划治理。")
            elif counts["warnings"]:
                print(f"{'准入' if args.strict_readiness else '文档'}检查完成，有 {counts['warnings']} 项告警。")
            else:
                print("准入检查通过。" if args.strict_readiness else "计划治理检查通过（文档一致性）。")
    return code


def parse_args(argv):
    parser = argparse.ArgumentParser(description="检查计划治理文档的一致性；--strict-readiness 用于准入。", allow_abbrev=False)
    parser.add_argument("root", nargs="?", type=nonempty, default=None, help="仓库根目录，默认当前目录。")
    parser.add_argument("--workset", action="store_true", help="输出只读当前工作集。")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出工作集。")
    parser.add_argument("--include-history", action="store_true", help="工作集包含历史计划。")
    parser.add_argument("--evidence-limit", type=int, metavar="N",
                        help="仅工作集 JSON：每个计划显示末尾 N 条记录（正整数），省略时返回全部。")
    parser.add_argument("--root", dest="mode_root", type=nonempty, help="仓库根目录，与 positional root 二选一。")
    parser.add_argument("--plan", action="append", type=nonempty, default=[], help="可重复：聚焦已登记计划 ID，各会话独立传入。")
    parser.add_argument("--drift", action="store_true", help="检查工作区变更是否被活跃计划影响范围覆盖。")
    parser.add_argument("--pre-commit", action="store_true", help="检查 staged 变更是否被活跃计划影响范围覆盖。")
    parser.add_argument(
        "--strict-readiness",
        action="store_true",
        help="将待实施/实施中计划的阶段准入结构缺陷从 WARNING 提升为 ERROR。",
    )
    parser.add_argument("--attest", type=nonempty, metavar="PLAN", help="为已登记计划创建或覆盖完成快照。")
    parser.add_argument("--attest-file", type=nonempty, action="append", metavar="PATH",
                        help="可重复：与 --attest/--attest-purpose 显式绑定被审查的普通文件。")
    parser.add_argument(
        "--attest-purpose",
        choices=sorted(ATTESTATION_PURPOSES),
        help="创建带 purpose/snapshot_id 关系的完成快照；不传时保持旧 <plan>.json 格式。",
    )
    parser.add_argument("--supersedes", type=nonempty, help="新 attestation 要替代的仓库内相对快照路径。")
    parser.add_argument(
        "--review-status",
        choices=sorted(ATTESTATION_REVIEW_STATUSES),
        default="current",
        help="新 attestation 的初始复核状态，默认 current。",
    )
    parser.add_argument("--check-attestations", action="store_true", help="检查完成快照 hash 是否漂移。")
    parser.add_argument(
        "--stale-days",
        nargs="?",
        const=10,
        type=int,
        default=None,
        help="检查活跃计划是否超过 N 天未更新；省略 N 时默认 10 天。",
    )
    validate_options(parser, argv, {"plan", "attest_file"})
    args = parser.parse_args(argv)
    if args.mode_root is not None and args.root is not None:
        parser.error("root 与 --root 不能同时使用")
    args.root = args.mode_root or args.root or "."
    if len(args.plan) != len(set(args.plan)):
        parser.error("--plan 不接受重复 ID")
    if args.workset:
        if any((args.drift, args.pre_commit, args.stale_days is not None, args.attest, args.attest_file is not None, args.attest_purpose, args.supersedes, args.check_attestations)):
            parser.error("workset 不接受 check 的检查/快照参数")
    elif args.include_history:
        parser.error("--include-history 仅适用于 workset")
    if args.attest and any((args.plan, args.drift, args.pre_commit, args.workset)):
        parser.error("--attest 不能与 workset/plan/drift/pre-commit 混用")
    if args.attest_file is not None and (not args.attest or not args.attest_purpose):
        parser.error("--attest-file 必须与 --attest/--attest-purpose 一起使用")
    if (args.attest_purpose or args.supersedes) and not args.attest:
        parser.error("--attest-purpose/--supersedes 必须与 --attest 一起使用")
    if any(token.split("=", 1)[0] == "--review-status" for token in argv) and not args.attest_purpose:
        parser.error("--review-status 必须与 --attest/--attest-purpose 一起使用")
    if args.supersedes and not args.attest_purpose:
        parser.error("--supersedes 必须与 --attest-purpose 一起使用")
    if args.stale_days is not None and args.stale_days < 0:
        parser.error("--stale-days 必须是非负整数")
    if args.evidence_limit is not None:
        if args.evidence_limit <= 0:
            parser.error("--evidence-limit 必须为正整数")
        if not args.workset or not args.json:
            parser.error("--evidence-limit 只能与 --workset 和 --json 一起使用")
    return args


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.attest_file is not None and (not args.attest or not args.attest_purpose or args.workset):
        print("ERROR: --attest-file 必须与 --attest/--attest-purpose 一起使用，不能用于 workset")
        return 1
    root = Path(args.root).expanduser().resolve()
    if args.workset:
        if not root.is_dir():
            payload = {"schema_version": 1, "source": "derived", "plans": [], "warnings": [f"root 不存在或不是目录：{root}"]}
            print(json.dumps(payload, ensure_ascii=False) if args.json else payload["warnings"][0])
            return 1
        return run_workset(
            root,
            as_json=args.json,
            include_history=args.include_history,
            strict=args.strict_readiness,
            evidence_limit=args.evidence_limit,
            requested=args.plan,
        )
    docs = root / "docs"
    plan_map = docs / "PLAN_MAP.md"
    records = []
    errors = DiagnosticList(records, "error")
    warnings = DiagnosticList(records, "warning")
    scope = None
    if not root.is_dir():
        errors.context(category="runtime", code="INVALID_ROOT")
        errors.append(f"root 不存在或不是目录：{root}")
        return finish_check(args, records)

    try:
        bound_input = args.attest_file is not None or (args.check_attestations and has_attestation_binding(root))
    except (ValueError, OSError) as exc:
        attestation_issue(warnings, errors, args.strict_readiness, f"快照清单无法读取：{exc}")
        return finish_check(args, records)
    unsafe_map = False
    if bound_input:
        try:
            binding_file(root, "docs/PLAN_MAP.md")
        except (ValueError, OSError) as exc:
            if args.attest_file is not None:
                errors.append(f"binding 创建预检失败：{exc}")
                return finish_check(args, records)
            unsafe_map = True
    if unsafe_map:
        reports = []
        warn_attestation_drift(warnings, root, {}, errors=errors, strict=args.strict_readiness, reports=reports)
        return finish_check(args, records, reports=reports)
    if not plan_map.exists():
        reports = []
        if args.check_attestations:
            warn_attestation_drift(warnings, root, {}, errors=errors, strict=args.strict_readiness, reports=reports)
        readiness_issue(warnings, errors, args.strict_readiness or bool(args.plan), "未找到 docs/PLAN_MAP.md；当前仓库尚未初始化计划治理")
        return finish_check(args, records, reports=reports, not_applicable=not errors)

    issue = agent_rules_issue(root)
    if issue:
        code, message = issue
        warnings.context(category="advisory", code=code, path="AGENTS.md", section="计划治理")
        warnings.append(message)
        warnings.context()
    text = read_utf8(plan_map, errors)
    _, blocker_index_issues = map_blockers(text)
    for issue in plan_index_issues(text):
        fail(errors, issue)
    for issue in blocker_index_issues:
        readiness_issue(warnings, errors, args.strict_readiness, issue)
    plan_rows = table_rows(text, "计划索引")
    if not plan_rows:
        fail(errors, "docs/PLAN_MAP.md: 缺少计划索引表")

    plans = {}
    unsafe_plans = set()
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
            if bound_input:
                try:
                    binding_file(root, "docs/" + link)
                except (ValueError, OSError) as exc:
                    attestation_issue(warnings, errors, args.attest_file is not None or args.strict_readiness,
                                      f"{name}: binding 计划读取预检失败：{exc}")
                    unsafe_plans.add(name)
            if not path.exists() and (not args.plan or name in args.plan):
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

    if args.plan and not errors:
        scope, text = build_scope(root, args.plan, text, plans)
    elif args.plan:
        return finish_check(args, records)

    args.evaluated_plans = list(plans)
    readable_plans = {name: data for name, data in plans.items() if name not in unsafe_plans}
    relation_errors, relation_warnings = validate_relation_graph(text, readable_plans)
    warnings.extend(relation_warnings)
    if args.strict_readiness:
        errors.extend(relation_errors)
    else:
        warnings.extend(relation_errors)

    edges = {}
    inactive = {name for name, data in plans.items() if data["status"] in INACTIVE}
    for name, data in plans.items():
        deps = extract_declared_dependencies(data["depends"])
        if not scope:
            for missing in set(deps) - set(plans):
                errors.append(f"{name}: 声明依赖的计划不存在：{missing}")
        edges[name] = [dep for dep in deps if dep in plans]
        if data["status"] in IMPLEMENTING and (not scope or name in scope["evaluated_plans"]):
            for dep in edges[name]:
                if dep in inactive:
                    fail(errors, f"{name}: 实施中计划依赖了非活跃计划 {dep}")

    for cycle in detect_dependency_cycles(edges):
        if not scope:
            fail(errors, f"计划依赖存在环：{cycle}")

    if not scope:
        for orphan in find_orphan_plans(docs, plans):
            warn(warnings, f"{orphan}: docs/plans 中存在未登记到 PLAN_MAP.md 的孤立计划")

    active_plan_targets = {}
    plan_texts = {}
    for name, data in plans.items():
        if name in unsafe_plans or (scope and name not in args.plan):
            continue
        for target in (errors, warnings):
            target.context(name, data["phase"], path=data["path"].relative_to(root))
        plan_text = read_utf8(data["path"], errors)
        plan_texts[name] = plan_text
        if data["status"] in COMPLETED and not has_completion_evidence(plan_text):
            fail(errors, f"{data['path']}: 已完成计划缺少有效 Step 0 证据或验证方式")
        if data["status"] in COMPLETED and not has_coverage_evidence(plan_text):
            fail(errors, f"{data['path']}: 已完成计划缺少测试覆盖率证据")
        if data["status"] in COMPLETED and phase_gate(text, name, data, plan_text)["blockers"]:
            fail(errors, f"{data['path']}: 已完成计划仍有当前阶段阻塞/失败")
        if data["status"] in WARNING_ACTIVE:
            targets = extract_affected_targets(plan_text)
            plan_relative = data["path"].relative_to(root).as_posix()
            if plan_relative not in targets:
                targets.append(plan_relative)
            phase_evidence, invalid_evidence = extract_phase_evidence_targets(plan_text)
            for evidence in phase_evidence:
                if evidence not in targets:
                    targets.append(evidence)
            for invalid in invalid_evidence:
                warn(
                    warnings,
                    f"{data['path']}: 阶段证据路径非法，未纳入 drift 覆盖：{invalid}",
                )
            active_plan_targets[name] = targets

        for target in (errors, warnings):
            target.context(name, data["phase"], category="readiness", path=data["path"].relative_to(root), section="当前阶段")
        check_phase_readiness(
            text,
            name,
            data,
            plan_text,
            args.strict_readiness,
            warnings,
            errors,
            selected=bool(scope),
        )

    for target in (errors, warnings):
        target.context(category="advisory", code="SHARED_WRITE_RISK")
    for target, plan_names in detect_overlapping_targets(active_plan_targets).items():
        warn(warnings, f"{target}: 多个活跃计划声明相同影响目标：{', '.join(plan_names)}")

    known_plans = set(plans)
    for name, data in plans.items():
        if data["status"] not in WARNING_ACTIVE or (scope and name not in args.plan):
            continue
        warnings.context(name, data["phase"], category="advisory", code="DEPENDENCY_REFERENCE", path=data["path"].relative_to(root))
        declared = set(edges.get(name, []))
        referenced = extract_plan_references(plan_texts.get(name, ""), known_plans, name)
        for missing in sorted(referenced - declared):
            warn(warnings, f"{name}: 正文引用了计划 {missing}，但 PLAN_MAP.md 依赖列未声明")
        for unreferenced in sorted(declared - referenced):
            warn(warnings, f"{name}: PLAN_MAP.md 声明依赖 {unreferenced}，但计划正文未引用")

    for target in (errors, warnings):
        target.context(category="advisory", code="OPTIONAL_CHECK")
    try:
        drift_files = changed_files(root) if args.drift else set()
        pre_commit_files = changed_files(root, staged=True) if args.pre_commit else set()
        if scope:
            peer_targets = {}
            for peer, data in plans.items():
                if peer not in args.plan and data["path"].is_file():
                    body = data["path"].read_text(encoding="utf-8")
                    peer_targets[peer] = extract_affected_targets(body) + [data["path"].relative_to(root).as_posix()]
            def relevant_changes(files, staged):
                selected = set()
                for file in files:
                    own = any(target_matches_path(t, file) for targets in active_plan_targets.values() for t in targets)
                    peers = any(target_matches_path(t, file) for targets in peer_targets.values() for t in targets)
                    if file == "docs/PLAN_MAP.md":
                        owners = plan_map_change_owners(root, staged, set(plans))
                        if owners and all(owner and not set(owner) & set(args.plan) for owner in owners):
                            continue
                    if own or not peers:
                        selected.add(file)
                return selected
            drift_files = relevant_changes(drift_files, False)
            pre_commit_files = relevant_changes(pre_commit_files, True)
        completion_window_targets = completed_plan_drift_targets(
            plans,
            plan_texts,
            root,
            drift_files | pre_commit_files,
        )
        drift_plan_targets = dict(active_plan_targets)
        drift_plan_targets.update(completion_window_targets)
        drift_covering_plan_names = set(active_plan_targets) | set(completion_window_targets)
        if args.drift:
            warn_uncovered_changes(
                warnings,
                "--drift",
                drift_files,
                drift_plan_targets,
                root=root,
                known_plans=set(plans),
                covering_plan_names=drift_covering_plan_names,
            )
        if args.pre_commit:
            warn_uncovered_changes(
                warnings,
                "--pre-commit",
                pre_commit_files,
                drift_plan_targets,
                root=root,
                known_plans=set(plans),
                covering_plan_names=drift_covering_plan_names,
            )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        warn(warnings, f"Git 变更检查不可用：{exc}")

    if args.stale_days is not None:
        if args.stale_days < 0:
            fail(errors, f"--stale-days 必须是非负整数：{args.stale_days}")
        else:
            warn_stale_plans(warnings, {n: d for n, d in plans.items() if not scope or n in args.plan}, args.stale_days)

    if scope:
        errors.context(category="document", code="SCOPE_STRUCTURE_INVALID")
        errors.extend(scope["global_diagnostics"])
        warnings.context(category="readiness", code="DEPENDENCY_BLOCKED")
        errors.context(category="readiness", code="DEPENDENCY_BLOCKED")
        for message in dependency_diagnostics(root, scope, text, plans):
            if message not in scope["global_diagnostics"]:
                readiness_issue(warnings, errors, args.strict_readiness, message)
    if args.check_attestations:
        attestation_reports = []
        warn_attestation_drift(
            warnings,
            root,
            plans,
            errors=errors,
            strict=args.strict_readiness,
            reports=attestation_reports,
            selected=scope["evaluated_plans"] if scope else None,
        )
    else:
        attestation_reports = []

    attested_path = None
    if (args.attest_purpose or args.supersedes) and not args.attest:
        fail(errors, "--attest-purpose/--supersedes 必须与 --attest 一起使用")
    if args.attest:
        target = plans.get(args.attest)
        if target and not errors and args.attest_purpose != "compliance":
            body = read_utf8(target["path"], errors)
            if target["status"] in INACTIVE:
                errors.append("终态目标不能创建完成/发布门快照")
            elif target["status"] not in COMPLETED:
                gate = phase_gate(text, args.attest, target, body, selected=True)
                errors.extend(gate["issues"])
            elif phase_gate(text, args.attest, target, body)["blockers"]:
                fail(errors, "完成快照目标仍有未解决阻塞")
        attested_path = create_attestation(
            root,
            plan_map,
            plans,
            args.attest,
            errors,
            purpose=args.attest_purpose,
            supersedes=args.supersedes or "",
            review_status=args.review_status,
            attest_files=args.attest_file,
        )

    if scope and not scope_unchanged(root, scope):
        errors.context(category="readiness", code="FACTS_CHANGED")
        warnings.context(category="readiness", code="FACTS_CHANGED")
        readiness_issue(warnings, errors, args.strict_readiness, "相关事实在读取期间发生变化；请重新检查")
    return finish_check(args, records, scope=scope, reports=attestation_reports, attested_path=attested_path)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except UsageError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
