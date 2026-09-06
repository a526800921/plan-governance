"""M02–M04: risk review declarations, shared consumers and failure recovery."""

import re
from pathlib import Path

import pytest

from test_check_plan_governance import (
    assert_gate_result,
    load_module,
    plan_map,
    readiness_plan_text,
)


hook = load_module("plan_governance_hook")
EVIDENCE = "`tests/fixtures/readiness.md`"
REVIEWER = "当前 AI"


def record(conclusion="通过", *, method="自验", risk="低风险", phase="阶段 1",
           date="2026-07-13", kind="阶段准入复核", evidence=EVIDENCE, reviewer=REVIEWER):
    return f"| {date} | {kind} | {phase} | {method} | {risk} | {conclusion} | {evidence} | {reviewer} |"


def risk_plan(*, status="待实施", method="自验", risk="低风险", conclusion="通过", history=None):
    text = readiness_plan_text(status=status).replace("最新独立准入复核", "最新阶段复核").replace(
        "独立复核记录", "阶段复核记录")
    text = text.replace("| 准入状态 |", "| 复核策略 | 风险分流 |\n| 准入状态 |")
    text = text.replace("| 结论 | 通过 |", f"| 方式 | {method} |\n| 风险 | {risk} |\n"
                        "| 风险依据 | 仅本地提示文案，范围明确、可撤销，已运行适用回归 |\n"
                        f"| 结论 | {conclusion} |")
    text = text.replace("| 复核者 | 独立复核者 |", f"| 复核者 | {REVIEWER} |")
    history_text = record(conclusion, method=method, risk=risk) if history is None else history
    start, tail = text.split("## 阶段复核记录", 1)
    _, suffix = tail.split("## Step 0 证据", 1)
    return start + "## 阶段复核记录\n\n" + (
        "| 日期 | 类型 | 阶段 | 方式 | 风险 | 结论 | 证据 | 复核者 |\n"
        "|---|---|---|---|---|---|---|---|\n" + history_text + "\n\n## Step 0 证据" + suffix
    )


def latest_field(text, field, value):
    return re.sub(r"(?m)^\| " + re.escape(field) + r" \|[^|\n]*\|$", f"| {field} | {value} |", text)


def with_legacy(text, conclusion="未通过", *, history=None, phase="阶段 1", kind="阶段准入复核"):
    legacy = readiness_plan_text(review_phase=phase, history_conclusion=conclusion)
    latest = legacy.split("### 最新独立准入复核", 1)[1].split("## 独立复核记录", 1)[0]
    latest = latest_field(latest, "结论", conclusion)
    history_section = legacy.split("## 独立复核记录", 1)[1].split("## Step 0 证据", 1)[0]
    if history is not None:
        history_section = "\n\n| 日期 | 类型 | 阶段 | 结论 | 证据 | 复核者 |\n|---|---|---|---|---|---|\n" + history + "\n"
    history_section = history_section.replace("阶段准入复核", kind)
    return text + "\n## 最新独立准入复核" + latest + "## 独立复核记录" + history_section


def legacy_record(conclusion="通过", *, phase="阶段 1", date="2026-07-13", kind="阶段准入复核"):
    return f"| {date} | {kind} | {phase} | {conclusion} | {EVIDENCE} | 独立复核者 |"


def assert_risk(tmp_path, capsys, text, *, status="待实施", readiness="unknown", action="unknown"):
    valid = readiness in {"ready", "design", "in_progress"}
    codes = (0, 0) if valid or status == "设计中" else (0, 1)
    payload = assert_gate_result(tmp_path, capsys, text,
        index=plan_map(f"| [demo](plans/demo.md) | {status} | 阶段 1 | - | - |"),
        check_codes=codes, workset_codes=codes, readiness=readiness, action=action)
    before = {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    assert hook.main(["--root", str(tmp_path), "--event", "session-start"]) == 0
    output = capsys.readouterr().out
    assert f"demo: {readiness}，下一动作 {action}" in output
    if readiness in {"unknown", "blocked"}:
        assert "WARNING:" in output
    assert {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()} == before
    return payload


@pytest.mark.parametrize("method,risk", [("自验", "低风险"), ("独立", "低风险"), ("独立", "高影响")])
def test_review_passes_without_fabricating_legacy_records(tmp_path, capsys, method, risk):
    text = risk_plan(method=method, risk=risk)
    assert "独立复核记录" not in text
    payload = assert_risk(tmp_path, capsys, text, readiness="ready", action="implement")
    assert not payload["warnings"]


@pytest.mark.parametrize("strategy", ["legacy", "risk", "risk_with_legacy"])
@pytest.mark.parametrize("conclusion", ["通过。", "通过.", "通过！", "通过!", "通过。已修复证据冲突"])
def test_explicit_pass_punctuation_preserves_legacy_compatibility(tmp_path, capsys, strategy, conclusion):
    if strategy == "legacy":
        text = latest_field(readiness_plan_text(history_conclusion=conclusion), "结论", conclusion)
    elif strategy == "risk_with_legacy":
        text = with_legacy(risk_plan(), conclusion)
    else:
        text = risk_plan(conclusion=conclusion)
    assert_risk(tmp_path, capsys, text, readiness="ready", action="implement")


@pytest.mark.parametrize("legacy", [True, False])
def test_punctuation_pass_recovers_independent_failure(tmp_path, capsys, legacy):
    if legacy:
        history = legacy_record("未通过") + "\n" + legacy_record("通过。")
        text = with_legacy(risk_plan(), "通过。", history=history)
    else:
        history = record("未通过", method="独立") + "\n" + record("通过。", method="独立") + "\n" + record()
        text = risk_plan(history=history)
    assert_risk(tmp_path, capsys, text, readiness="ready", action="implement")


@pytest.mark.parametrize("conclusion", ["通过不了", "通过不了。", "可能通过", "可能通过。", "通过？", "通过?"])
def test_similar_or_questioned_wording_is_not_explicit_pass(tmp_path, capsys, conclusion):
    assert_risk(tmp_path, capsys, risk_plan(conclusion=conclusion))


@pytest.mark.parametrize("legacy", [True, False])
@pytest.mark.parametrize("conclusion", [
    "通过 / 未通过", "通过/未通过", "通过 ／ 未通过", "通过／未通过",
    "通过 或 未通过", "通过或未通过", "通过 或者 未通过",
    "通过 / 未通过（待选）", "未通过 / 通过",
    "通过 / 未通过？", "通过 / 未通过?", "通过 / 未通过待选", "通过 / 未通过”",
])
def test_unselected_review_candidates_are_unknown(tmp_path, capsys, legacy, conclusion):
    text = with_legacy(risk_plan(), conclusion) if legacy else risk_plan(conclusion=conclusion)
    assert_risk(tmp_path, capsys, text)


@pytest.mark.parametrize("legacy", [True, False])
@pytest.mark.parametrize("conclusion", [
    "通过：已修复未通过问题", "通过。已修复未通过问题",
    "通过：已修复通过 / 未通过模板", "通过：已修复超时或证据冲突",
])
def test_actual_pass_explanation_is_not_an_unselected_candidate(tmp_path, capsys, legacy, conclusion):
    text = with_legacy(risk_plan(), conclusion) if legacy else risk_plan(conclusion=conclusion)
    assert_risk(tmp_path, capsys, text, readiness="ready", action="implement")


@pytest.mark.parametrize("legacy", [True, False])
@pytest.mark.parametrize("conclusion", [
    "通过 / 未通过", "通过 / 未通过？", "通过 / 未通过?", "通过 / 未通过待选", "通过 / 未通过”",
])
def test_unselected_candidate_cannot_clear_independent_failure(tmp_path, capsys, legacy, conclusion):
    if legacy:
        history = legacy_record("未通过") + "\n" + legacy_record(conclusion)
        text = with_legacy(risk_plan(), conclusion, history=history)
    else:
        history = record("未通过", method="独立") + "\n" + record(conclusion, method="独立") + "\n" + record()
        text = risk_plan(history=history)
    assert_risk(tmp_path, capsys, text, readiness="blocked", action="resolve_blocker")


@pytest.mark.parametrize("conclusion", ["未进行", "尚未进行", "待复核", "待自验", "待验证"])
@pytest.mark.parametrize("history", [None, ""])
def test_low_risk_pending_self_review_is_verify(tmp_path, capsys, conclusion, history):
    text = risk_plan(status="设计中", conclusion=conclusion, history=history)
    assert_risk(tmp_path, capsys, text, status="设计中", readiness="design", action="verify")


def test_pending_review_can_have_placeholder_result_evidence(tmp_path, capsys):
    text = risk_plan(status="设计中", conclusion="未进行", history="")
    for field in ["日期", "证据", "复核者"]:
        text = latest_field(text, field, "待补充")
    assert_risk(tmp_path, capsys, text, status="设计中", readiness="design", action="verify")


def test_high_impact_pending_is_independent_review(tmp_path, capsys):
    text = risk_plan(status="设计中", method="独立", risk="高影响", conclusion="待独立复核")
    assert_risk(tmp_path, capsys, text, status="设计中", readiness="design", action="independent_review")


def test_passed_design_requires_map_sync(tmp_path, capsys):
    assert_risk(tmp_path, capsys, risk_plan(status="设计中"), status="设计中", readiness="design", action="sync")


def test_pending_review_cannot_enter_active_status(tmp_path, capsys):
    assert_risk(tmp_path, capsys, risk_plan(conclusion="未进行"))


@pytest.mark.parametrize("risk_strategy", [True, False])
def test_waiting_for_user_acceptance_uses_existing_none_action(tmp_path, capsys, risk_strategy):
    text = risk_plan(status="实施中") if risk_strategy else readiness_plan_text(status="实施中")
    text = text.replace("## 当前阶段", "## 当前阶段\n\n下一动作：等待用户验收")
    payload = assert_risk(tmp_path, capsys, text, status="实施中", readiness="in_progress", action="none")
    item = payload["plans"][0]
    assert item["status"] == "实施中"
    assert "等待用户验收" in item["next_action"]["reason"]
    assert "不自动关闭" in item["next_action"]["reason"]


@pytest.mark.parametrize("value", ["", "-", "默认", "低风险", "risk", "风险分流 | 额外值"])
def test_invalid_policy_never_defaults_to_self_review(tmp_path, capsys, value):
    payload = assert_risk(tmp_path, capsys, latest_field(risk_plan(), "复核策略", value))
    assert "复核策略" in " ".join(payload["warnings"])


@pytest.mark.parametrize("field", ["复核策略", "最新阶段复核", "日期", "阶段", "方式", "风险", "风险依据", "结论", "证据", "复核者"])
def test_duplicate_risk_fields_are_ambiguous(tmp_path, capsys, field):
    text = risk_plan().replace(f"| {field} |", f"| {field} | 待补充 |\n| {field} |")
    assert_risk(tmp_path, capsys, text)


@pytest.mark.parametrize("field", ["最新阶段复核", "日期", "阶段", "方式", "风险", "风险依据", "结论", "证据", "复核者"])
@pytest.mark.parametrize("replacement", ["", "待补充"])
def test_pass_requires_nonplaceholder_fields(tmp_path, capsys, field, replacement):
    assert_risk(tmp_path, capsys, latest_field(risk_plan(), field, replacement))


@pytest.mark.parametrize("field", ["日期", "阶段", "方式", "风险", "风险依据", "结论", "证据", "复核者"])
def test_pass_requires_all_review_fields(tmp_path, capsys, field):
    text = re.sub(r"(?m)^\| " + re.escape(field) + r" \|[^\n]*\n", "", risk_plan())
    assert_risk(tmp_path, capsys, text)


@pytest.mark.parametrize("date", ["2026-02-30", "2026-13-01", "2026-7-13", "tomorrow"])
def test_invalid_date_never_passes(tmp_path, capsys, date):
    assert_risk(tmp_path, capsys, risk_plan().replace("2026-07-13", date))


@pytest.mark.parametrize("method,risk,conclusion", [
    ("自验", "高影响", "通过"), ("独立", "待判断", "通过"),
    ("自验", "待判断", "未进行"), ("自验", "中风险", "通过"),
    ("无需复核", "低风险", "通过"), ("自验", "低风险", "可能通过"),
])
def test_unknown_or_high_impact_self_review_cannot_pass(tmp_path, capsys, method, risk, conclusion):
    assert_risk(tmp_path, capsys, risk_plan(method=method, risk=risk, conclusion=conclusion))


@pytest.mark.parametrize("title", ["最新阶段复核", "阶段复核记录", "阶段准入摘要", "当前阶段"])
def test_duplicate_headings_are_ambiguous(tmp_path, capsys, title):
    text = risk_plan()
    if title == "阶段准入摘要":
        text = text.replace("### 最新阶段复核", "### 阶段准入摘要\n\n### 最新阶段复核")
    else:
        text += f"\n## {title}\n"
    assert_risk(tmp_path, capsys, text)


@pytest.mark.parametrize("field,value", [("日期", "2026-07-14"), ("方式", "独立"), ("风险", "高影响"),
    ("结论", "通过：补充说明"), ("证据", "other.md"), ("复核者", "其他 AI"), ("阶段", "阶段 2")])
def test_latest_and_history_must_agree(tmp_path, capsys, field, value):
    assert_risk(tmp_path, capsys, latest_field(risk_plan(), field, value))


def test_cross_phase_history_does_not_authorize_current_phase(tmp_path, capsys):
    assert_risk(tmp_path, capsys, risk_plan(history=record(phase="阶段 2")))


@pytest.mark.parametrize("fence", ["```", "~~~~"])
def test_fenced_fake_review_does_not_authorize_plan(tmp_path, capsys, fence):
    text = risk_plan()
    prefix, review = text.split("### 最新阶段复核", 1)
    evidence, suffix = review.split("## Step 0 证据", 1)
    text = prefix + f"{fence}markdown\n### 最新阶段复核" + evidence + f"{fence}\n## Step 0 证据" + suffix
    assert_risk(tmp_path, capsys, text)


@pytest.mark.parametrize("fence", ["```", "~~~~"])
def test_fenced_failed_examples_do_not_block_real_review(tmp_path, capsys, fence):
    fake = f"{fence}markdown\n" + risk_plan(conclusion="未通过") + f"\n{fence}\n"
    assert_risk(tmp_path, capsys, fake + risk_plan(), readiness="ready", action="implement")


def test_mixed_summary_contract_is_ambiguous(tmp_path, capsys):
    text = risk_plan().replace("| 最新阶段复核 |", "| 最新独立准入复核 | [旧复核](#最新独立准入复核) |\n| 最新阶段复核 |")
    assert_risk(tmp_path, capsys, text)


@pytest.mark.parametrize("source", ["latest", "history", "legacy"])
@pytest.mark.parametrize("failure", ["未通过", "失败", "不通过", "不满足标准", "拒绝", "复核入口不可用", "超时", "证据冲突", "证据失效"])
def test_failures_stay_blocked_across_consumers(tmp_path, capsys, source, failure):
    text = risk_plan()
    if source == "latest":
        text = latest_field(text, "结论", failure)
    elif source == "history":
        text = risk_plan(history=record(failure, method="独立") + "\n" + record())
    else:
        text = with_legacy(text, failure)
    payload = assert_risk(tmp_path, capsys, text, readiness="blocked", action="resolve_blocker")
    assert failure in " ".join(payload["plans"][0]["blockers"])


@pytest.mark.parametrize("kind", ["阶段准入复核", "阶段完成复核", "阶段完成验收", "其他独立复核"])
@pytest.mark.parametrize("legacy", [True, False])
def test_self_review_cannot_erase_any_independent_failure(tmp_path, capsys, kind, legacy):
    if legacy:
        text = with_legacy(risk_plan(), kind=kind)
    else:
        text = risk_plan(history=record("未通过", method="独立", kind=kind) + "\n" + record())
    assert_risk(tmp_path, capsys, text, readiness="blocked", action="resolve_blocker")


@pytest.mark.parametrize("legacy", [True, False])
def test_independent_recovery_unblocks_without_deleting_history(tmp_path, capsys, legacy):
    if legacy:
        history = legacy_record("未通过") + "\n" + legacy_record(kind="阶段完成复核")
        text = with_legacy(risk_plan(), "通过", history=history)
    else:
        history = record("未通过", method="独立") + "\n" + record(method="独立", kind="阶段完成复核") + "\n" + record()
        text = risk_plan(history=history)
    assert "未通过" in text
    assert_risk(tmp_path, capsys, text, readiness="ready", action="implement")


def test_self_review_failure_can_be_repaired_by_self_review(tmp_path, capsys):
    text = risk_plan(history=record("未通过") + "\n" + record())
    assert_risk(tmp_path, capsys, text, readiness="ready", action="implement")


@pytest.mark.parametrize("legacy", [True, False])
@pytest.mark.parametrize("problem", ["证据冲突", "超时", "复核入口不可用", "证据失效"])
def test_explicit_independent_pass_can_describe_repaired_failure(tmp_path, capsys, legacy, problem):
    conclusion = f"通过：已修复{problem}"
    if legacy:
        history = legacy_record(problem) + "\n" + legacy_record(conclusion)
        text = with_legacy(risk_plan(), conclusion, history=history)
    else:
        history = record(problem, method="独立") + "\n" + record(conclusion, method="独立") + "\n" + record()
        text = risk_plan(history=history)
    assert_risk(tmp_path, capsys, text, readiness="ready", action="implement")


@pytest.mark.parametrize("conclusion", ["未通过：重试后通过，但仍超时", "已修复证据冲突，待复核", "复核后超时"])
def test_failure_text_without_explicit_pass_remains_blocked(tmp_path, capsys, conclusion):
    assert_risk(tmp_path, capsys, risk_plan(conclusion=conclusion), readiness="blocked", action="resolve_blocker")


def test_legacy_recovery_requires_updating_latest_result(tmp_path, capsys):
    history = legacy_record("未通过") + "\n" + legacy_record()
    text = with_legacy(risk_plan(), "未通过", history=history)
    assert_risk(tmp_path, capsys, text, readiness="blocked", action="resolve_blocker")


@pytest.mark.parametrize("legacy", [True, False])
@pytest.mark.parametrize("field,value", [("date", "-"), ("date", "2026-02-30"), ("evidence", "待补充"), ("reviewer", "-")])
def test_incomplete_independent_pass_cannot_clear_failure(tmp_path, capsys, legacy, field, value):
    if legacy:
        passed = legacy_record()
        target = {"date": "2026-07-13", "evidence": EVIDENCE, "reviewer": "独立复核者"}[field]
        history = legacy_record("未通过") + "\n" + passed.replace(target, value)
        text = with_legacy(risk_plan(), "通过", history=history)
    else:
        history = record("未通过", method="独立") + "\n" + record(method="独立", **{field: value}) + "\n" + record()
        text = risk_plan(history=history)
    assert_risk(tmp_path, capsys, text, readiness="blocked", action="resolve_blocker")


@pytest.mark.parametrize("legacy", [True, False])
def test_previous_phase_failures_do_not_block_current_phase(tmp_path, capsys, legacy):
    if legacy:
        text = with_legacy(risk_plan(), phase="阶段 0")
    else:
        text = risk_plan(history=record("未通过", method="独立", phase="阶段 0") + "\n" + record())
    assert_risk(tmp_path, capsys, text, readiness="ready", action="implement")


@pytest.mark.parametrize("history", [
    "| 2026-07-13 | 阶段准入复核 | 阶段 1 | 自验 | 低风险 | 通过 | evidence |",
    "| 2026-07-13 | 阶段准入复核 | | 自验 | 低风险 | 通过 | evidence | AI |",
    record(date="2026-07-14") + "\n" + record(),
    record(method="未知") + "\n" + record(),
    record("可能通过", method="独立") + "\n" + record(),
])
def test_malformed_or_conflicting_history_is_unknown(tmp_path, capsys, history):
    assert_risk(tmp_path, capsys, risk_plan(history=history))


def test_legacy_latest_and_history_conflict_is_not_self_approved(tmp_path, capsys):
    text = with_legacy(risk_plan(), "通过", history=legacy_record(date="2026-07-12"))
    assert_risk(tmp_path, capsys, text)


def test_waiting_for_user_does_not_bypass_failed_review(tmp_path, capsys):
    text = risk_plan(status="实施中", conclusion="未通过").replace(
        "## 当前阶段", "## 当前阶段\n\n下一动作：等待用户验收")
    assert_risk(tmp_path, capsys, text, status="实施中", readiness="blocked", action="resolve_blocker")


@pytest.mark.parametrize("field,value", [("phase", "未知"), ("phase", "待补充"), ("phase", ""),
    ("kind", ""), ("kind", "待补充"), ("method", "")])
def test_invalid_tail_record_cannot_fall_back_to_previous_pass(tmp_path, capsys, field, value):
    text = risk_plan(history=record() + "\n" + record("未进行", **{field: value}))
    assert_risk(tmp_path, capsys, text)


@pytest.mark.parametrize("legacy", [False, True])
def test_fake_date_header_cannot_hide_failed_history(tmp_path, capsys, legacy):
    if legacy:
        text = with_legacy(risk_plan(), "通过", history=legacy_record() + "\n" + legacy_record("失败", date="日期"))
    else:
        text = risk_plan(history=record() + "\n" + record("失败", method="独立", date="日期"))
    assert_risk(tmp_path, capsys, text, readiness="blocked", action="resolve_blocker")


@pytest.mark.parametrize("value", ["", "未知", "待补充"])
def test_unscoped_legacy_failure_cannot_disappear(tmp_path, capsys, value):
    text = with_legacy(risk_plan(), phase=value)
    assert_risk(tmp_path, capsys, text)


@pytest.mark.parametrize("legacy", [False, True])
def test_invalid_current_history_table_header_is_not_accepted(tmp_path, capsys, legacy):
    text = with_legacy(risk_plan(), "通过") if legacy else risk_plan()
    text = text.replace("| 日期 | 类型 | 阶段 |", "| 日期 | 未知列 | 阶段 |")
    assert_risk(tmp_path, capsys, text)


def test_new_titles_remain_background_when_policy_is_absent(tmp_path, capsys):
    background = "\n## 最新阶段复核\n| 方式 | 背景说明 |\n| 方式 | 不是当前契约 |\n## 阶段复核记录\n"
    text = readiness_plan_text() + background + background
    assert_risk(tmp_path, capsys, text, readiness="ready", action="implement")


def test_current_template_starts_without_review_approval(tmp_path, capsys):
    text = (Path(__file__).resolve().parents[1] / "resources/skill/assets/plan.template.md").read_text(encoding="utf-8")
    text = text.replace("{{phase}}", "阶段 1").replace("{{status}}", "设计中")
    payload = assert_risk(tmp_path, capsys, text, status="设计中", readiness="blocked", action="resolve_blocker")
    assert "风险待判断" in " ".join(payload["warnings"])
