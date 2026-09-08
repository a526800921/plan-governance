"""Single independent review: repairs close through explicit, evidenced self-checks."""

import pytest

from test_risk_review import assert_risk, latest_field, legacy_record, record, risk_plan, with_legacy


def single_plan(*, history=None, method="自验", risk="高影响", conclusion="通过", **kwargs):
    if history is None:
        history = record("未通过：拒绝路径缺少回归", method="独立", risk=risk)
        history += "\n" + record(conclusion, method=method, risk=risk, kind="修复自验")
    return risk_plan(history=history, method=method, risk=risk, conclusion=conclusion, **kwargs).replace(
        "| 复核策略 | 风险分流 |", "| 复核策略 | 单次独立复核 |")


@pytest.mark.parametrize("risk", ["低风险", "高影响", "高风险"])
@pytest.mark.parametrize("finding", ["未通过：两个缺陷", "证据冲突：运行样本与报告不同", "通过"])
def test_one_independent_result_then_repair_self_check(tmp_path, capsys, risk, finding):
    history = record(finding, method="独立", risk=risk) + "\n" + record(risk=risk, kind="修复自验")
    text = single_plan(history=history, risk=risk)
    payload = assert_risk(tmp_path, capsys, text, readiness="ready", action="implement")
    assert not payload["warnings"]
    assert text.count("| 独立 |") == 1
    assert finding in text


def test_ordinary_change_needs_no_independent_record(tmp_path, capsys):
    text = single_plan(risk="低风险", history=record())
    assert_risk(tmp_path, capsys, text, readiness="ready", action="implement")


@pytest.mark.parametrize("risk", ["高影响", "高风险"])
def test_implementation_self_check_reuses_design_review(tmp_path, capsys, risk):
    history = record(method="独立", risk=risk) + "\n" + record(risk=risk)
    assert_risk(tmp_path, capsys, single_plan(history=history, risk=risk), readiness="ready", action="implement")


@pytest.mark.parametrize("finding", ["超时", "复核入口不可用", "证据失效", "复核工具超时"])
def test_unfinished_independent_check_cannot_be_repaired_as_completed(tmp_path, capsys, finding):
    history = record(finding, method="独立", risk="高影响") + "\n" + record(risk="高影响", kind="修复自验")
    assert_risk(tmp_path, capsys, single_plan(history=history), readiness="blocked", action="resolve_blocker")


@pytest.mark.parametrize("finding", [
    "未通过：业务请求超时后重试错误，独立检查已完成",
    "未通过：上游不可用时没有回退",
    "未通过：证据失效处理路径错误",
])
def test_business_findings_do_not_invalidate_completed_review(tmp_path, capsys, finding):
    history = record(finding, method="独立", risk="高影响") + "\n" + record(risk="高影响", kind="修复自验")
    assert_risk(tmp_path, capsys, single_plan(history=history), readiness="ready", action="implement")


@pytest.mark.parametrize("field,value", [("date", "2026-02-30"), ("evidence", "待补充"), ("reviewer", "-")])
def test_incomplete_independent_baseline_cannot_authorize_repair(tmp_path, capsys, field, value):
    history = record("未通过", method="独立", risk="高影响", **{field: value})
    history += "\n" + record(risk="高影响", kind="修复自验")
    assert_risk(tmp_path, capsys, single_plan(history=history), readiness="blocked", action="resolve_blocker")


@pytest.mark.parametrize("field,value", [("date", "2026-02-30"), ("evidence", "待补充"), ("reviewer", "-")])
def test_incomplete_repair_does_not_clear_finding(tmp_path, capsys, field, value):
    history = record("未通过", method="独立", risk="高影响")
    history += "\n" + record(risk="高影响", kind="修复自验", **{field: value})
    assert_risk(tmp_path, capsys, single_plan(history=history), readiness="blocked", action="resolve_blocker")


@pytest.mark.parametrize("kind", ["修复自验", "阶段完成复核"])
def test_high_impact_self_check_needs_independent_baseline(tmp_path, capsys, kind):
    text = single_plan(history=record(risk="高影响", kind=kind))
    assert_risk(tmp_path, capsys, text)


def test_low_risk_baseline_does_not_authorize_high_impact_self_check(tmp_path, capsys):
    history = record(method="独立", risk="低风险") + "\n" + record(risk="高影响", kind="修复自验")
    assert_risk(tmp_path, capsys, single_plan(history=history))


def test_previous_phase_review_is_not_current_baseline(tmp_path, capsys):
    history = record(method="独立", risk="高影响", phase="阶段 0") + "\n" + record(risk="高影响", kind="修复自验")
    assert_risk(tmp_path, capsys, single_plan(history=history))


def test_generic_self_pass_does_not_hide_unresolved_findings(tmp_path, capsys):
    history = record("未通过", method="独立", risk="高影响") + "\n" + record(risk="高影响")
    assert_risk(tmp_path, capsys, single_plan(history=history), readiness="blocked", action="resolve_blocker")


def test_failed_repair_stays_blocked_then_self_recovers(tmp_path, capsys):
    text = single_plan(conclusion="未通过：回归仍失败")
    assert_risk(tmp_path, capsys, text, readiness="blocked", action="resolve_blocker")
    history = record("未通过", method="独立", risk="高影响")
    history += "\n" + record("未通过：回归仍失败", risk="高影响", kind="修复自验")
    history += "\n" + record(risk="高影响", kind="修复自验")
    assert_risk(tmp_path, capsys, single_plan(history=history), readiness="ready", action="implement")


def test_structured_blocker_still_blocks_after_repair(tmp_path, capsys):
    text = latest_field(single_plan(), "当前阻塞项", "生产数据差异仍未解决")
    assert_risk(tmp_path, capsys, text, readiness="blocked", action="resolve_blocker")


def test_migration_preserves_old_failure_but_allows_evidenced_repair(tmp_path, capsys):
    text = with_legacy(single_plan())
    assert "## 独立复核记录" in text and "未通过" in text
    assert_risk(tmp_path, capsys, text, readiness="ready", action="implement")


@pytest.mark.parametrize("missing", ["`tests/fixtures/readiness.md`", "独立复核者", "阶段准入复核"])
def test_migration_retains_older_incomplete_failure_as_issue(tmp_path, capsys, missing):
    history = legacy_record("未通过").replace(missing, "-") + "\n" + legacy_record("未通过")
    text = with_legacy(single_plan(), history=history)
    assert_risk(tmp_path, capsys, text)


def test_switching_policy_alone_cannot_clear_legacy_failure(tmp_path, capsys):
    text = with_legacy(single_plan(risk="低风险", history=record()))
    assert_risk(tmp_path, capsys, text, readiness="blocked", action="resolve_blocker")


def test_newer_legacy_failure_is_not_cleared_by_older_repair(tmp_path, capsys):
    text = with_legacy(single_plan())
    prefix, legacy = text.split("## 最新独立准入复核", 1)
    text = prefix + "## 最新独立准入复核" + legacy.replace("2026-07-13", "2026-07-14")
    assert_risk(tmp_path, capsys, text, readiness="blocked", action="resolve_blocker")


def test_pending_single_review_dispatches_once(tmp_path, capsys):
    text = single_plan(history="", status="设计中", method="独立", conclusion="尚未进行")
    assert_risk(tmp_path, capsys, text, status="设计中", readiness="design", action="independent_review")
