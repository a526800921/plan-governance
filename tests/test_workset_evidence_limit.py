"""Optional JSON evidence windows preserve the complete workset decision."""

import copy
import json
from pathlib import Path

import pytest

from test_check_plan_governance import (
    check_plan_governance as checker,
    plan_map,
    readiness_plan_text,
    write,
)
from test_risk_review import record, risk_plan


RECENT_TITLE = "最近实施/验证记录"


def evidence_rows(count):
    return [
        ["2026-09-06", "验证", f"记录 {number}", f"输出 {number}", "通过", "tester"]
        for number in range(count)
    ]


def with_recent(text, rows, title=RECENT_TITLE):
    table = (
        f"### {title}\n\n"
        "| 日期 | 类型 | 动作/结果 | 证据 | 状态 | 记录者 |\n"
        "|---|---|---|---|---|---|\n"
        + "\n".join("| " + " | ".join(row) + " |" for row in rows)
        + "\n\n"
    )
    marker = "### 最新阶段复核" if "### 最新阶段复核" in text else "### 最新独立准入复核"
    return text.replace(marker, table + marker, 1)


def project(root, rows, *, text=None, title=RECENT_TITLE,
            path="docs/plans/demo.md"):
    write(root / "docs/PLAN_MAP.md", plan_map(
        f"| [demo]({Path(path).relative_to('docs').as_posix()}) | 待实施 | 阶段 1 | - | - |"))
    write(root / path, with_recent(text or readiness_plan_text(), rows, title))


def snapshot(root):
    return {
        path.relative_to(root).as_posix(): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in root.rglob("*") if path.is_file()
    }


def run_json(root, capsys, *, limit=None, strict=False, history=False):
    args = ["--workset", "--json", str(root)]
    if strict:
        args.append("--strict-readiness")
    if history:
        args.append("--include-history")
    if limit is not None:
        args.extend(["--evidence-limit", str(limit)])
    status = checker.main(args)
    output = capsys.readouterr()
    return json.loads(output.out), status, output.err


def assert_only_evidence_changed(full, limited, limit):
    """Compare every decision, diagnostic and existing field, not a selected subset."""
    restored = copy.deepcopy(limited)
    assert len(restored["plans"]) == len(full["plans"])
    for original, item in zip(full["plans"], restored["plans"]):
        assert "recent_evidence_window" not in original
        metadata = item.pop("recent_evidence_window")
        assert set(metadata) == {"total", "omitted", "source"}
        assert metadata["total"] == len(original["recent_evidence"])
        assert metadata["omitted"] == max(len(original["recent_evidence"]) - limit, 0)
        assert item["recent_evidence"] == original["recent_evidence"][-limit:]
        item["recent_evidence"] = original["recent_evidence"]
    assert restored == full


def test_default_json_and_shared_payload_remain_complete(tmp_path, capsys):
    rows = evidence_rows(18)
    project(tmp_path, rows)
    before = snapshot(tmp_path)
    for strict in (False, True):
        payload, status = checker.workset_payload(tmp_path, strict=strict)
        assert set(payload) == {"schema_version", "source", "plans", "warnings"}
        assert payload["schema_version"] == 1
        assert set(payload["plans"][0]) == {
            "plan", "status", "phase", "readiness", "blockers", "next_action",
            "parallel", "recent_evidence",
        }
        assert payload["plans"][0]["recent_evidence"] == rows
        args = ["--workset", "--json", str(tmp_path)]
        if strict:
            args.append("--strict-readiness")
        assert checker.main(args) == status == 0
        output = capsys.readouterr()
        assert output.out == json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        assert output.err == ""
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize("count,limit", [(18, 3), (0, 3), (2, 5)])
def test_explicit_window_has_counts_even_when_nothing_is_omitted(tmp_path, capsys, count, limit):
    project(tmp_path, evidence_rows(count))
    before = snapshot(tmp_path)
    full, full_status, full_err = run_json(tmp_path, capsys)
    limited, status, err = run_json(tmp_path, capsys, limit=limit)
    assert_only_evidence_changed(full, limited, limit)
    assert status == full_status == 0
    assert err == full_err
    assert limited["plans"][0]["recent_evidence_window"]["source"] == {
        "path": "docs/plans/demo.md", "section": RECENT_TITLE,
    }
    # A later unrestricted query must still return all rows without metadata.
    assert run_json(tmp_path, capsys) == (full, full_status, full_err)
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize("dates", [
    ["2026-09-06"] * 4,
    ["2026-09-10", "2026-09-08", "2026-09-09", "2026-09-01"],
])
def test_window_uses_append_order_without_sorting_or_deduplicating_dates(tmp_path, capsys, dates):
    rows = evidence_rows(4)
    for row, date in zip(rows, dates):
        row[0] = date
    project(tmp_path, rows)
    full, full_status, full_err = run_json(tmp_path, capsys)
    limited, status, err = run_json(tmp_path, capsys, limit=2)
    assert_only_evidence_changed(full, limited, 2)
    assert limited["plans"][0]["recent_evidence"] == [rows[2], rows[3]]
    assert (status, err) == (full_status, full_err)


@pytest.mark.parametrize("title", [
    RECENT_TITLE, "阶段 1 最近验证记录", "阶段 1 最近实施/验证记录",
])
def test_source_follows_map_path_and_actual_compatible_heading(tmp_path, capsys, title):
    actual_path = "docs/plans/roadmaps/recovery-notes.md"
    project(tmp_path, evidence_rows(4), title=title, path=actual_path)
    # This plausible conventional path is deliberately a different document.
    write(tmp_path / "docs/plans/recovery-notes.md", with_recent(readiness_plan_text(), evidence_rows(1)))
    full, full_status, full_err = run_json(tmp_path, capsys, strict=True)
    limited, status, err = run_json(tmp_path, capsys, limit=2, strict=True)
    assert_only_evidence_changed(full, limited, 2)
    assert limited["plans"][0]["recent_evidence_window"]["source"] == {
        "path": actual_path, "section": title,
    }
    assert (status, err) == (full_status, full_err)
    if title != RECENT_TITLE:
        assert any("兼容记录标题" in warning for warning in limited["warnings"])


@pytest.mark.parametrize("title", [None, "阶段 2 最近验证记录"])
def test_missing_current_record_heading_has_no_fabricated_section(tmp_path, capsys, title):
    project(tmp_path, evidence_rows(3), title=title or RECENT_TITLE)
    if title is None:
        write(tmp_path / "docs/plans/demo.md", readiness_plan_text())
    full, full_status, full_err = run_json(tmp_path, capsys)
    limited, status, err = run_json(tmp_path, capsys, limit=1)
    assert full["plans"][0]["recent_evidence"] == []
    assert_only_evidence_changed(full, limited, 1)
    assert limited["plans"][0]["recent_evidence_window"]["source"] == {
        "path": "docs/plans/demo.md", "section": None,
    }
    assert (status, err) == (full_status, full_err)


def test_history_filter_is_independent_of_each_plans_window(tmp_path, capsys):
    write(tmp_path / "docs/PLAN_MAP.md", plan_map("\n".join([
        "| [active](plans/active.md) | 待实施 | 阶段 1 | - | - |",
        "| [running](plans/running.md) | 实施中 | 阶段 1 | - | - |",
        "| [history](plans/history.md) | 已完成 | 阶段 1 | - | - |",
        "| [legacy](plans/legacy.md) | 已废弃 | 阶段 1 | - | - |",
    ])))
    for name, state, count in [
        ("active", "待实施", 4), ("running", "实施中", 3), ("history", "已完成", 5),
    ]:
        write(tmp_path / f"docs/plans/{name}.md",
              with_recent(readiness_plan_text(status=state), evidence_rows(count)))
    write(tmp_path / "docs/plans/legacy.md", "# 旧计划\n\n只有自然语言历史记录。\n")
    before = snapshot(tmp_path)
    for history in (False, True):
        full, full_status, full_err = run_json(tmp_path, capsys, history=history)
        limited, status, err = run_json(tmp_path, capsys, limit=2, history=history)
        assert_only_evidence_changed(full, limited, 2)
        expected = ["active", "running", "history", "legacy"] if history else ["active", "running"]
        assert [item["plan"] for item in limited["plans"]] == expected
        assert (status, err) == (full_status, full_err)
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize("strict", [False, True])
def test_hidden_independent_failure_still_blocks_after_later_self_check(tmp_path, capsys, strict):
    text = risk_plan(history=record("未通过", method="独立") + "\n" + record())
    rows = evidence_rows(2)
    rows[0][2:5] = ["独立复核未通过，等待独立重审", "独立失败证据", "未通过"]
    rows[1][2] = "后续自验通过"
    project(tmp_path, rows, text=text)
    before = snapshot(tmp_path)
    full, full_status, full_err = run_json(tmp_path, capsys, strict=strict)
    limited, status, err = run_json(tmp_path, capsys, limit=1, strict=strict)
    assert_only_evidence_changed(full, limited, 1)
    item = limited["plans"][0]
    assert item["recent_evidence"] == [rows[1]]
    assert item["readiness"] == "blocked"
    assert item["next_action"]["kind"] == "resolve_blocker"
    assert any("未通过" in blocker for blocker in item["blockers"])
    assert item["blockers"] and limited["warnings"]
    assert status == full_status == int(strict)
    assert err == full_err
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize("strict", [False, True])
def test_single_review_repair_is_preserved_in_limited_workset(tmp_path, capsys, strict):
    text = risk_plan(history=record("未通过", method="独立") + "\n" + record(kind="修复自验"))
    text = text.replace("| 复核策略 | 风险分流 |", "| 复核策略 | 单次独立复核 |")
    rows = evidence_rows(2)
    rows[0][2:5] = ["独立发现", "原问题证据", "未通过"]
    rows[1][2] = "修复自验通过"
    project(tmp_path, rows, text=text)
    before = snapshot(tmp_path)
    full, full_status, full_err = run_json(tmp_path, capsys, strict=strict)
    limited, status, err = run_json(tmp_path, capsys, limit=1, strict=strict)
    assert_only_evidence_changed(full, limited, 1)
    assert limited["plans"][0]["readiness"] == "ready"
    assert limited["plans"][0]["next_action"]["kind"] == "implement"
    assert status == full_status == 0
    assert err == full_err
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize("problem", ["unresolved_blocker", "missing_step0"])
def test_gate_diagnostics_and_exit_codes_do_not_depend_on_window(tmp_path, capsys, problem):
    if problem == "unresolved_blocker":
        text = readiness_plan_text(unresolved_blocker=True)
    else:
        text = readiness_plan_text().replace(
            "| Step 0 | [Step 0 证据](#step-0-证据) |", "| Step 0 | |")
    project(tmp_path, evidence_rows(4), text=text)
    for strict in (False, True):
        full, full_status, full_err = run_json(tmp_path, capsys, strict=strict)
        limited, status, err = run_json(tmp_path, capsys, limit=1, strict=strict)
        assert_only_evidence_changed(full, limited, 1)
        assert limited["warnings"]
        assert limited["plans"][0]["next_action"]["kind"] != "implement"
        assert status == full_status == int(strict)
        assert err == full_err


@pytest.mark.parametrize("arguments", [
    ["--workset", "--json", "--evidence-limit", "0"],
    ["--workset", "--json", "--evidence-limit", "-1"],
    ["--workset", "--json", "--evidence-limit", "1.5"],
    ["--workset", "--json", "--evidence-limit", "abc"],
    ["--workset", "--json", "--evidence-limit"],
    ["--workset", "--evidence-limit", "2"],
    ["--json", "--evidence-limit", "2"],
    ["--evidence-limit", "2"],
])
def test_invalid_limit_or_output_mode_is_an_argparse_error(tmp_path, capsys, arguments):
    project(tmp_path, evidence_rows(2))
    before = snapshot(tmp_path)
    with pytest.raises(SystemExit) as error:
        checker.main([str(tmp_path), *arguments])
    assert error.value.code == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert "--evidence-limit" in output.err
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize("failure", ["missing_map", "missing_plan", "unreadable_plan"])
def test_unresolvable_source_is_null_without_changing_complete_decision(tmp_path, monkeypatch, failure):
    project(tmp_path, evidence_rows(4))
    payload, status = checker.workset_payload(tmp_path, strict=True)
    original = copy.deepcopy(payload)
    plan_path = tmp_path / "docs/plans/demo.md"
    if failure == "missing_map":
        (tmp_path / "docs/PLAN_MAP.md").unlink()
    elif failure == "missing_plan":
        plan_path.unlink()
    else:
        original_read = Path.read_text

        def read_text(path, *args, **kwargs):
            if path == plan_path:
                raise PermissionError("fixture: plan source unavailable after gate")
            return original_read(path, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", read_text)
    before = snapshot(tmp_path)
    limited = checker.limit_workset_evidence(tmp_path, payload, 2)
    assert status == 0
    assert_only_evidence_changed(original, limited, 2)
    assert limited["plans"][0]["recent_evidence_window"]["source"] is None
    assert payload == original
    assert snapshot(tmp_path) == before


def test_window_helper_leaves_shared_payload_unchanged(tmp_path):
    project(tmp_path, evidence_rows(4))
    payload, _ = checker.workset_payload(tmp_path)
    original = copy.deepcopy(payload)
    limited = checker.limit_workset_evidence(tmp_path, payload, 2)
    assert limited is not payload
    assert_only_evidence_changed(original, limited, 2)
    assert payload == original
    assert checker.workset_payload(tmp_path)[0] == original
