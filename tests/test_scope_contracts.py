"""会话范围、检查分层、失败时不产生快照的公共行为回归。"""
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import sys

import pytest
from test_check_plan_governance import check_plan_governance as checker, plan_map, readiness_plan_text, write
from test_risk_review import risk_plan
from test_plan_governance_hooks import plan_governance_hook as hook

CLI = Path(__file__).resolve().parents[1] / "scripts/check_plan_governance.py"


def project(root, specs=None, relations=""):
    specs = specs or {"alpha": ("待实施", "阶段 1", "-", readiness_plan_text()),
                      "beta": ("待实施", "阶段 1", "-", readiness_plan_text(unresolved_blocker=True))}
    rows = []
    for name, (status, phase, deps, body) in specs.items():
        rows.append(f"| [{name}](plans/{name}.md) | {status} | {phase} | 2026-10-04 | {deps} | proof |")
        write(root / f"docs/plans/{name}.md", body)
    write(root / "docs/PLAN_MAP.md", plan_map("\n".join(rows)) + relations)


def relation(source="beta", phase="阶段 1", target="alpha", kind="hard_gate"):
    return "\n## 阶段关系\n\n| " + " | ".join(checker.RELATION_COLUMNS) + " |\n|---|---|---|---|---|---|---|\n" + f"| {source} | {phase} | {target} | 阶段 1 | {kind} | 来源阶段通过 | [证据](plans/{source}.md) |\n"


def invoke(root, *args):
    result = subprocess.run([sys.executable, str(CLI), str(root), "--json", *args], capture_output=True, text=True)
    return result, json.loads(result.stdout) if result.stdout else None


def test_default_blocker_is_warning_strict_is_error_with_same_facts(tmp_path):
    project(tmp_path)
    ordinary, first = invoke(tmp_path)
    strict, second = invoke(tmp_path, "--strict-readiness")
    assert (ordinary.returncode, strict.returncode) == (0, 1)
    assert first["mode"] == "consistency" and first["status"] == "warning"
    assert second["mode"] == "readiness" and second["status"] == "failed"
    assert not ordinary.stderr and not strict.stderr
    diagnostics = [d for d in first["diagnostics"] if "未解决阻塞项" in d["message"]]
    assert diagnostics[0]["plan"] == "beta"
    assert diagnostics[0]["category"] == "readiness"
    assert diagnostics[0]["sources"][0]["path"] == "docs/plans/beta.md"


def test_simultaneous_conversations_receive_only_their_own_workset(tmp_path):
    project(tmp_path)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda name: invoke(tmp_path, "--workset", "--plan", name, "--strict-readiness"), ["alpha", "beta"]))
    assert [r.returncode for r, _ in results] == [0, 1]
    for name, (_, payload) in zip(["alpha", "beta"], results):
        assert [p["plan"] for p in payload["plans"]] == [name]
        assert payload["scope"]["requested_plans"] == [name]
        assert payload["scope"]["evaluated_plans"] == [name]
    focused, payload = invoke(tmp_path, "--plan", "alpha", "--strict-readiness")
    assert focused.returncode == 0
    assert all(d["plan"] != "beta" for d in payload["diagnostics"])


def test_focus_ignores_unrelated_missing_body_and_cycle(tmp_path):
    project(tmp_path, {"alpha": ("待实施", "阶段 1", "-", readiness_plan_text()),
                      "beta": ("待实施", "阶段 1", "gamma", "invalid"),
                      "gamma": ("待实施", "阶段 1", "beta", "invalid")})
    (tmp_path / "docs/plans/beta.md").unlink()
    assert invoke(tmp_path, "--strict-readiness")[0].returncode == 1
    assert invoke(tmp_path, "--plan", "alpha", "--strict-readiness")[0].returncode == 0


@pytest.mark.parametrize("kind,expected", [("hard_gate", 1), ("evidence", 0), ("soft_context", 0)])
def test_only_hard_predecessors_expand_readiness_scope(tmp_path, kind, expected):
    project(tmp_path, relations=relation(kind=kind))
    result, payload = invoke(tmp_path, "--workset", "--plan", "alpha", "--strict-readiness")
    assert result.returncode == expected, payload
    assert len(payload["scope"]["dependencies"]) == (1 if kind == "hard_gate" else 0)
    assert [p["plan"] for p in payload["plans"]] == ["alpha"]


@pytest.mark.parametrize("body", [readiness_plan_text(), risk_plan()])
def test_passed_source_phase_is_not_gated_by_later_phase_blocker(tmp_path, body):
    # 历史通过只满足显式阶段 1 前置；阶段 2 的业务阻塞不投影进目标。
    later = readiness_plan_text(unresolved_blocker=True).replace("阶段 1", "阶段 2")
    if "阶段复核记录" in body:
        history = body.split("## 阶段复核记录", 1)[1].split("## Step 0 证据", 1)[0]
        later += "\n## 阶段复核记录" + history
    else:
        history = body.split("## 独立复核记录", 1)[1].split("## Step 0 证据", 1)[0]
        later = later.replace("## 独立复核记录", "## 后续阶段记录") + "\n## 独立复核记录" + history
    later = later.replace("| 阶段 2 | 阶段目标", "| 阶段 1 | 已完成 | proof | pytest | 已完成 |\n| 阶段 2 | 阶段目标")
    project(tmp_path, {"alpha": ("待实施", "阶段 1", "beta", readiness_plan_text()),
                      "beta": ("实施中", "阶段 2", "-", later)}, relation())
    result, payload = invoke(tmp_path, "--workset", "--plan", "alpha", "--strict-readiness")
    assert result.returncode == 0, payload
    assert payload["scope"]["dependencies"][0]["phase_passed"]
    assert payload["plans"][0]["readiness"] == "ready"


def test_dependency_failures_are_owned_by_each_requested_plan(tmp_path):
    project(tmp_path, {"alpha": ("待实施", "阶段 1", "beta", readiness_plan_text()),
                      "beta": ("待实施", "阶段 1", "-", readiness_plan_text(unresolved_blocker=True)),
                      "gamma": ("待实施", "阶段 1", "-", readiness_plan_text())})
    _, payload = invoke(tmp_path, "--workset", "--plan", "alpha", "--plan", "gamma")
    assert {p["plan"]: p["readiness"] for p in payload["plans"]} == {"alpha": "blocked", "gamma": "ready"}


def test_shared_writes_include_peer_constraints_without_peer_blockers(tmp_path):
    project(tmp_path, {"alpha": ("待实施", "阶段 1", "-", readiness_plan_text() + "\n## 影响模块或文件\n\n- `src/`\n"),
                      "beta": ("待实施", "阶段 1", "-", readiness_plan_text(unresolved_blocker=True) + "\n## 影响模块或文件\n\n- `src/main.py`\n")})
    result, payload = invoke(tmp_path, "--workset", "--plan", "alpha", "--strict-readiness")
    assert result.returncode == 0
    assert payload["scope"]["shared_writes"][0]["plans"] == ["alpha", "beta"]
    assert "示例问题" not in json.dumps(payload, ensure_ascii=False)


@pytest.mark.parametrize("related", [False, True])
def test_facts_version_ignores_unrelated_map_updates_but_detects_related_edits(tmp_path, monkeypatch, related):
    project(tmp_path)
    original = checker.dependency_diagnostics
    def update(root, scope, text, plans):
        result = original(root, scope, text, plans)
        if related:
            path = root / "docs/plans/alpha.md"
            path.write_text(path.read_text() + "\n新事实\n")
        else:
            path = root / "docs/PLAN_MAP.md"
            path.write_text(path.read_text().replace("| [beta](plans/beta.md) | 待实施", "| [beta](plans/beta.md) | 实施中"))
        return result
    monkeypatch.setattr(checker, "dependency_diagnostics", update)
    payload, status = checker.workset_payload(tmp_path, strict=True, requested=["alpha"])
    assert status == (1 if related else 0)
    assert payload["plans"][0]["readiness"] == ("unknown" if related else "ready")


@pytest.mark.parametrize("args", [["--plan", "missing"], ["--plan", "alpha", "--plan", "alpha"],
    ["--root", "."], ["--workset", "--drift"], ["--include-history"], ["--json", "--json"],
    ["--plan", ""], ["--review-status", "current"], ["--stale-days", "-1"]])
def test_argument_errors_never_mutate_or_succeed(tmp_path, args):
    project(tmp_path)
    before = {str(p): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    result, _ = invoke(tmp_path, *args)
    assert result.returncode == 2, result.stdout + result.stderr
    assert result.stderr
    assert {str(p): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before


@pytest.mark.parametrize("strict,expected", [(False, 0), (True, 1)])
def test_uninitialized_is_explicitly_not_checked(tmp_path, strict, expected):
    result, payload = invoke(tmp_path, *(["--strict-readiness"] if strict else []))
    assert result.returncode == expected
    assert payload["status"] == ("failed" if strict else "not_applicable")


def test_bad_root_is_runtime_failure_not_not_applicable(tmp_path):
    result, payload = invoke(tmp_path / "missing")
    assert result.returncode == 1 and payload["status"] == "failed"
    assert payload["diagnostics"][0]["category"] == "runtime"


@pytest.mark.parametrize("purpose", [None, "release_gate", "phase_completion"])
def test_failed_check_and_blocked_target_never_write_attestation(tmp_path, purpose):
    project(tmp_path)
    flags = ["--attest", "beta"] + (["--attest-purpose", purpose] if purpose else [])
    result, _ = invoke(tmp_path, *flags)
    assert result.returncode == 1
    assert not (tmp_path / "docs/attestations").exists()


def test_hook_focus_and_unset_focus_have_different_information(tmp_path, capsys):
    project(tmp_path)
    assert hook.main(["--root", str(tmp_path), "--event", "session-start"]) == 0
    output = capsys.readouterr().out
    assert "尚未设置会话焦点" in output and "示例问题" not in output
    assert hook.main(["--root", str(tmp_path), "--event", "session-start", "--plan", "alpha"]) == 0
    output = capsys.readouterr().out
    assert "beta" not in output and "ready" in output

@pytest.mark.parametrize("status", ["候选", "设计中", "已废弃", "已替代", "已合并"])
def test_explicit_non_admitted_targets_cannot_bypass_strict_gate(tmp_path, status):
    project(tmp_path, {"alpha": (status, "阶段 1", "-", "# 未产出准入材料\n")})
    assert invoke(tmp_path, "--plan", "alpha")[0].returncode == 0
    assert invoke(tmp_path, "--plan", "alpha", "--strict-readiness")[0].returncode == 1
    assert invoke(tmp_path, "--workset", "--plan", "alpha", "--strict-readiness")[0].returncode == 1


@pytest.mark.parametrize("status", ["已完成", "已废弃"])
def test_upstream_evidence_or_lifecycle_is_checked(tmp_path, status):
    project(tmp_path, {"alpha": ("待实施", "阶段 1", "beta", readiness_plan_text()),
                      "beta": (status, "阶段 1", "-", "# 缺少证据\n")})
    result, payload = invoke(tmp_path, "--plan", "alpha", "--strict-readiness")
    assert result.returncode == 1
    assert not payload["scope"]["dependencies"][0]["phase_passed"]


def test_related_cycle_is_document_failure_in_both_modes(tmp_path):
    project(tmp_path, {"alpha": ("待实施", "阶段 1", "beta", readiness_plan_text()),
                      "beta": ("待实施", "阶段 1", "alpha", readiness_plan_text())})
    for flags in [[], ["--strict-readiness"], ["--workset"], ["--workset", "--strict-readiness"]]:
        result, _ = invoke(tmp_path, "--plan", "alpha", *flags)
        assert result.returncode == 1


def test_missing_and_malformed_source_phase_evidence_never_pass(tmp_path):
    for body in ["# 无历史证据", readiness_plan_text().replace("| `tests/fixtures/readiness.md` | 独立复核者 |", "|")]:
        project(tmp_path, {"alpha": ("待实施", "阶段 1", "beta", readiness_plan_text()),
                          "beta": ("实施中", "阶段 2", "-", body)}, relation())
        result, payload = invoke(tmp_path, "--workset", "--plan", "alpha", "--strict-readiness")
        assert result.returncode == 1, payload


def test_invalid_identity_or_related_input_is_never_hidden(tmp_path):
    project(tmp_path)
    path = tmp_path / "docs/PLAN_MAP.md"
    path.write_text(path.read_text().replace("2026-10-04", "2026-02-30"))
    assert invoke(tmp_path, "--plan", "alpha")[0].returncode == 1
    assert invoke(tmp_path, "--workset", "--plan", "alpha")[0].returncode == 1
    project(tmp_path)
    (tmp_path / "docs/plans/alpha.md").unlink()
    assert invoke(tmp_path, "--plan", "alpha")[0].returncode == 1
    assert invoke(tmp_path, "--workset", "--plan", "alpha")[0].returncode == 1


def test_hook_reports_shared_writes_and_paths_outside_focus(tmp_path, capsys):
    project(tmp_path, {"alpha": ("待实施", "阶段 1", "-", readiness_plan_text() + "\n## 影响模块或文件\n\n- `src/`\n"),
                      "beta": ("待实施", "阶段 1", "-", readiness_plan_text(unresolved_blocker=True) + "\n## 影响模块或文件\n\n- `src/`\n")})
    assert hook.main(["--root", str(tmp_path), "--event", "pre-write", "--plan", "alpha", "--paths", "src/a.py", "other.py"]) == 0
    output = capsys.readouterr().out
    assert "共享写入约束" in output and "超出聚焦计划声明范围：other.py" in output
    assert "示例问题" not in output


@pytest.mark.parametrize("args,expected", [(["--event", "session-start", "--paths", "a"], 2),
    (["--event", "stop", "--plan", "missing"], 2), (["--event", "pre-write", "--paths", "../escape"], 2),
    (["--event", "pre-write", "--paths", ""], 2), (["--event", "stop", "--root", "missing"], 1)])
def test_hook_parameter_and_root_failures_are_visible(tmp_path, capsys, args, expected):
    project(tmp_path)
    try:
        code = hook.main(["--root", str(tmp_path), *args])
    except SystemExit as exc:
        code = exc.code
    # 重复 root 是参数错误，不能静默覆盖到另一个目录。
    assert code == (2 if "--root" in args else expected)
    assert capsys.readouterr().err


def test_scoped_optional_drift_and_staleness_do_not_dump_peer_changes(tmp_path, monkeypatch, capsys):
    project(tmp_path, {"alpha": ("待实施", "阶段 1", "-", readiness_plan_text() + "\n## 影响模块或文件\n\n- `src/alpha/`\n"),
                      "beta": ("待实施", "阶段 1", "-", readiness_plan_text() + "\n## 影响模块或文件\n\n- `src/beta/`\n")})
    monkeypatch.setattr(checker, "changed_files", lambda root, staged=False: {"src/beta/app.py", "docs/PLAN_MAP.md"})
    monkeypatch.setattr(checker, "plan_map_change_owners", lambda root, staged, names: [["beta"]])
    assert checker.main([str(tmp_path), "--plan", "alpha", "--json", "--drift", "--pre-commit", "--stale-days", "0"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert "src/beta" not in json.dumps(payload, ensure_ascii=False)
    assert all("beta: 超过" not in d["message"] for d in payload["diagnostics"])


def test_backticked_hard_gate_cannot_disappear_from_scope(tmp_path):
    project(tmp_path, relations=relation().replace("| beta |", "| `beta` |").replace("| hard_gate |", "| `hard_gate` |"))
    result, payload = invoke(tmp_path, "--workset", "--plan", "alpha", "--strict-readiness")
    assert result.returncode == 1
    assert payload["scope"]["dependencies"][0]["plan"] == "beta"


def test_empty_relation_header_corruption_is_global_scope_failure(tmp_path):
    project(tmp_path, relations="\n## 阶段关系\n\n| 未知 | 表头 |\n|---|---|\n")
    assert invoke(tmp_path, "--plan", "alpha")[0].returncode == 1
    assert invoke(tmp_path, "--workset", "--plan", "alpha")[0].returncode == 1


def test_completed_target_retains_existing_workset_enums(tmp_path):
    from test_check_plan_governance import plan_text
    project(tmp_path, {"alpha": ("已完成", "阶段 1", "-", plan_text(with_coverage=True))})
    assert invoke(tmp_path, "--plan", "alpha", "--strict-readiness")[0].returncode == 0
    result, payload = invoke(tmp_path, "--workset", "--plan", "alpha", "--strict-readiness")
    assert result.returncode == 0
    assert payload["plans"][0]["status"] == "已完成"
    assert payload["plans"][0]["readiness"] == "unknown"
    assert payload["plans"][0]["next_action"]["kind"] == "unknown"


def test_related_facts_change_in_check_and_evidence_window_are_detected(tmp_path, monkeypatch, capsys):
    project(tmp_path)
    original = checker.dependency_diagnostics
    def changed(root, scope, text, plans):
        output = original(root, scope, text, plans)
        path = root / "docs/plans/alpha.md"
        path.write_text(path.read_text() + "\n新证据\n")
        return output
    monkeypatch.setattr(checker, "dependency_diagnostics", changed)
    assert checker.main([str(tmp_path), "--plan", "alpha", "--strict-readiness", "--json"]) == 1
    assert any(d["code"] == "FACTS_CHANGED" for d in json.loads(capsys.readouterr().out)["diagnostics"])
    monkeypatch.setattr(checker, "dependency_diagnostics", original)
    window = checker.limit_workset_evidence
    def changed_window(root, payload, limit):
        output = window(root, payload, limit)
        path = root / "docs/plans/alpha.md"
        path.write_text(path.read_text() + "\n证据窗口新事实\n")
        return output
    monkeypatch.setattr(checker, "limit_workset_evidence", changed_window)
    assert checker.run_workset(tmp_path, as_json=True, strict=True, requested=["alpha"], evidence_limit=1) == 1
    assert json.loads(capsys.readouterr().out)["plans"][0]["readiness"] == "unknown"


def test_completed_predecessor_does_not_reopen_closed_historical_dependencies(tmp_path):
    from test_check_plan_governance import plan_text
    project(tmp_path, {"alpha": ("待实施", "阶段 1", "beta", readiness_plan_text()),
                      "beta": ("已完成", "阶段 1", "old", plan_text(with_coverage=True)),
                      "old": ("已替代", "阶段 1", "-", "# 已由后续完成成果承接\n")})
    result, payload = invoke(tmp_path, "--workset", "--plan", "alpha", "--strict-readiness")
    assert result.returncode == 0, payload
    assert payload["scope"]["evaluated_plans"] == ["alpha", "beta"]
    assert payload["scope"]["dependencies"][0]["phase_passed"]
    assert payload["plans"][0]["readiness"] == "ready"
    assert invoke(tmp_path, "--plan", "alpha", "--strict-readiness")[0].returncode == 0
    # 当前直接依赖已替代目标仍失败，不因其祖先链的兼容规则放行。
    path = tmp_path / "docs/PLAN_MAP.md"
    path.write_text(path.read_text().replace("| [alpha](plans/alpha.md) | 待实施 | 阶段 1 | 2026-10-04 | beta |", "| [alpha](plans/alpha.md) | 待实施 | 阶段 1 | 2026-10-04 | old |"))
    assert invoke(tmp_path, "--plan", "alpha", "--strict-readiness")[0].returncode == 1
