"""项目入口差异是只读告警，不改变业务准入结论。"""
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest
from test_scope_contracts import project, invoke
from test_check_plan_governance import check_plan_governance as checker, readiness_plan_text
from test_init_plan_governance import init_plan_governance as initializer


def setup_project(root):
    project(root, {"alpha": ("待实施", "阶段 1", "-", readiness_plan_text())})


def snapshot(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}


@pytest.mark.parametrize("args", [[], ["--strict-readiness"], ["--plan", "alpha", "--strict-readiness"]])
def test_stale_rules_warn_without_changing_exit_or_files(tmp_path, args):
    setup_project(tmp_path)
    target = tmp_path / "AGENTS.md"
    target.write_text("<!-- plan-governance:start -->\n旧独立门禁\n<!-- plan-governance:end -->\n")
    before = snapshot(tmp_path)
    result, payload = invoke(tmp_path, *args)
    assert result.returncode == 0
    assert snapshot(tmp_path) == before
    diagnostic = next(d for d in payload["diagnostics"] if d["code"] == "AGENT_RULES_DRIFT")
    assert diagnostic["severity"] == "warning" and diagnostic["category"] == "advisory"
    assert diagnostic["plan"] is None and diagnostic["phase"] is None
    assert diagnostic["sources"] == [{"path": "AGENTS.md", "section": "计划治理"}]
    assert "--update-agent-rules-only" in diagnostic["message"]
    assert str(tmp_path) in diagnostic["message"]


@pytest.mark.parametrize("variant", ["current", "crlf", "missing", "unmanaged", "fenced"])
def test_current_or_unmanaged_rules_do_not_warn(tmp_path, variant):
    setup_project(tmp_path)
    block = initializer.agents_md_section()
    if variant == "crlf":
        block = "\r\n".join(line + "  \t" for line in block.splitlines()) + "\r\n"
    elif variant == "unmanaged":
        block = "# 项目自定义说明\n"
    elif variant == "fenced":
        block = "```markdown\n" + block + "```\n"
    if variant != "missing":
        (tmp_path / "AGENTS.md").write_bytes(("自定义前文\n" + block + "\n自定义后文\n").encode())
    result, payload = invoke(tmp_path, "--strict-readiness")
    assert result.returncode == 0
    assert not any(d["code"].startswith("AGENT_RULES_") for d in payload["diagnostics"])


@pytest.mark.parametrize("content", [
    "<!-- plan-governance:start -->\n残缺",
    "<!-- plan-governance:end -->\n<!-- plan-governance:start -->",
    "<!-- plan-governance:start -->\n<!-- plan-governance:end -->\n" * 2,
])
def test_malformed_blocks_are_unknown_not_stale(tmp_path, content):
    setup_project(tmp_path)
    (tmp_path / "AGENTS.md").write_text(content)
    result, payload = invoke(tmp_path, "--strict-readiness")
    assert result.returncode == 0
    assert [d["code"] for d in payload["diagnostics"]] == ["AGENT_RULES_INVALID"]
    assert "--update-agent-rules-only" not in payload["diagnostics"][0]["message"]


@pytest.mark.parametrize("kind", ["invalid_utf8", "directory", "symlink", "unreadable"])
def test_unavailable_rules_are_explicit_advisories(tmp_path, kind, monkeypatch, capsys):
    setup_project(tmp_path)
    target = tmp_path / "AGENTS.md"
    if kind == "directory":
        target.mkdir()
    elif kind == "symlink":
        target.symlink_to(tmp_path / "missing-target")
    elif kind == "invalid_utf8":
        target.write_bytes(b"\xff")
    else:
        target.write_text(initializer.agents_md_section())
        original = Path.read_text

        def denied(path, *args, **kwargs):
            if path == target:
                raise PermissionError("fixture")
            return original(path, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", denied)
    assert checker.main([str(tmp_path), "--json", "--strict-readiness"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert [d["code"] for d in payload["diagnostics"]] == ["AGENT_RULES_UNAVAILABLE"]


def test_entry_update_resolves_warning_and_copied_checker_can_verify_it(tmp_path):
    setup_project(tmp_path)
    (tmp_path / "AGENTS.md").write_text("用户说明\n<!-- plan-governance:start -->\n旧规则\n<!-- plan-governance:end -->\n后记\n")
    docs_before = snapshot(tmp_path / "docs")
    initializer.main(["--root", str(tmp_path), "--update-agent-rules-only"])
    assert snapshot(tmp_path / "docs") == docs_before
    checker_path = tmp_path / "standalone.py"
    shutil.copyfile(Path(checker.__file__), checker_path)
    result = subprocess.run([sys.executable, str(checker_path), str(tmp_path), "--json", "--strict-readiness"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert not json.loads(result.stdout)["diagnostics"]


def test_drift_warning_does_not_hide_a_business_failure(tmp_path):
    project(tmp_path)
    (tmp_path / "AGENTS.md").write_text("<!-- plan-governance:start -->\n旧规则\n<!-- plan-governance:end -->")
    result, payload = invoke(tmp_path, "--strict-readiness")
    assert result.returncode == 1
    assert any(d["severity"] == "error" for d in payload["diagnostics"])
    assert any(d["code"] == "AGENT_RULES_DRIFT" for d in payload["diagnostics"])


def test_update_preserves_fenced_example_and_custom_crlf_bytes(tmp_path):
    setup_project(tmp_path)
    sample = b"```markdown\r\n<!-- plan-governance:start -->\r\nexample\r\n<!-- plan-governance:end -->\r\n```\r\n"
    suffix = b"\r\ncustom  \t\r\n"
    target = tmp_path / "AGENTS.md"
    target.write_bytes(sample + b"<!-- plan-governance:start -->\r\nold\r\n<!-- plan-governance:end -->" + suffix)
    assert invoke(tmp_path)[1]["diagnostics"][0]["code"] == "AGENT_RULES_DRIFT"
    initializer.main(["--root", str(tmp_path), "--update-agent-rules-only"])
    assert target.read_bytes() == sample + initializer.agents_md_section().rstrip().encode() + suffix
    assert not invoke(tmp_path)[1]["diagnostics"]


@pytest.mark.parametrize("args", [["--update-agent-rules-only"], ["--upgrade-existing"], ["--plan", "demo", "--update-agent-rules"]])
def test_explicit_update_refuses_malformed_block_without_writes(tmp_path, args):
    (tmp_path / "AGENTS.md").write_text("<!-- plan-governance:start -->\n保留残缺原文")
    before = snapshot(tmp_path)
    with pytest.raises(ValueError, match="人工核对"):
        initializer.main(["--root", str(tmp_path), *args])
    assert snapshot(tmp_path) == before
