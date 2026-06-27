import importlib.util
from pathlib import Path


def load_module(name):
    path = Path(__file__).resolve().parents[1] / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


check_plan_governance = load_module("check_plan_governance")


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def plan_map(row):
    return f"""# PLAN_MAP

## 计划索引

| 计划 | 状态 | 当前阶段 | 依赖 | 证据 |
|---|---|---|---|---|
{row}
"""


def plan_text(status="待实施", unresolved_blocker=False, with_coverage=False):
    blocker = "是 | 待确认" if unresolved_blocker else "否 | 已延后"
    coverage = "## 测试覆盖率\n\npytest-cov 报告：98.8% 覆盖率。\n" if with_coverage else ""
    return f"""# 计划：demo

## Step 0 证据

已有基线。

## 验证方式

运行检查脚本。

{coverage}
## 未决问题

| 问题 | 推荐方案 | 是否阻塞当前阶段 | 状态 |
|---|---|---|---|
| 示例问题 | 暂不处理 | {blocker} |

## 当前状态

{status}
"""


def test_missing_plan_map_is_not_an_error(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(check_plan_governance.sys, "argv", ["check", str(tmp_path)])

    assert check_plan_governance.main() == 0
    assert "尚未初始化计划治理" in capsys.readouterr().out


def test_valid_plan_map_passes(tmp_path, monkeypatch, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 已完成 | 阶段 1 | - | - |"),
    )
    write(tmp_path / "docs" / "plans" / "demo.md", plan_text(with_coverage=True))
    monkeypatch.setattr(check_plan_governance.sys, "argv", ["check", str(tmp_path)])

    assert check_plan_governance.main() == 0
    assert "检查通过" in capsys.readouterr().out


def test_invalid_status_and_missing_file_fail(tmp_path, monkeypatch, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 不合法 | 阶段 1 | - | - |"),
    )
    monkeypatch.setattr(check_plan_governance.sys, "argv", ["check", str(tmp_path)])

    assert check_plan_governance.main() == 1
    output = capsys.readouterr().out
    assert "状态不合法" in output
    assert "引用的计划文件不存在" in output


def test_missing_plan_index_fails(tmp_path, monkeypatch, capsys):
    write(tmp_path / "docs" / "PLAN_MAP.md", "# PLAN_MAP\n")
    monkeypatch.setattr(check_plan_governance.sys, "argv", ["check", str(tmp_path)])

    assert check_plan_governance.main() == 1
    assert "缺少计划索引表" in capsys.readouterr().out


def test_plan_row_without_link_fails(tmp_path, monkeypatch, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| demo | 待实施 | 阶段 1 | - | - |"),
    )
    monkeypatch.setattr(check_plan_governance.sys, "argv", ["check", str(tmp_path)])

    assert check_plan_governance.main() == 1
    assert "计划行缺少 docs/plans 链接" in capsys.readouterr().out


def test_plain_plan_link_is_supported(tmp_path, monkeypatch, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| plans/demo.md | 待实施 | 阶段 1 | - | - |"),
    )
    write(tmp_path / "docs" / "plans" / "demo.md", plan_text())
    monkeypatch.setattr(check_plan_governance.sys, "argv", ["check", str(tmp_path)])

    assert check_plan_governance.main() == 0
    assert "检查通过" in capsys.readouterr().out


def test_read_utf8_reports_decode_error(tmp_path):
    bad_file = tmp_path / "bad.md"
    bad_file.write_bytes(b"\xff")
    errors = []

    assert check_plan_governance.read_utf8(bad_file, errors) == ""
    assert "not valid UTF-8" in errors[0]


def test_dependency_cycle_fails(tmp_path, monkeypatch, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map(
            "| [a](plans/a.md) | 待实施 | 阶段 1 | b | - |\n"
            "| [b](plans/b.md) | 待实施 | 阶段 1 | a | - |"
        ),
    )
    write(tmp_path / "docs" / "plans" / "a.md", plan_text())
    write(tmp_path / "docs" / "plans" / "b.md", plan_text())
    monkeypatch.setattr(check_plan_governance.sys, "argv", ["check", str(tmp_path)])

    assert check_plan_governance.main() == 1
    assert "计划依赖存在环" in capsys.readouterr().out


def test_implementing_plan_cannot_depend_on_inactive_plan(tmp_path, monkeypatch, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map(
            "| [active](plans/active.md) | 实施中 | 阶段 1 | inactive | - |\n"
            "| [inactive](plans/inactive.md) | 已废弃 | 阶段 1 | - | - |"
        ),
    )
    write(tmp_path / "docs" / "plans" / "active.md", plan_text())
    write(tmp_path / "docs" / "plans" / "inactive.md", plan_text())
    monkeypatch.setattr(check_plan_governance.sys, "argv", ["check", str(tmp_path)])

    assert check_plan_governance.main() == 1
    assert "依赖了非活跃计划" in capsys.readouterr().out


def test_implementing_plan_with_open_blocker_fails(tmp_path, monkeypatch, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 实施中 | 阶段 1 | - | - |"),
    )
    write(tmp_path / "docs" / "plans" / "demo.md", plan_text(unresolved_blocker=True))
    monkeypatch.setattr(check_plan_governance.sys, "argv", ["check", str(tmp_path)])

    assert check_plan_governance.main() == 1
    assert "仍有未解决的当前阶段阻塞项" in capsys.readouterr().out


def test_completed_plan_without_evidence_fails(tmp_path, monkeypatch, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 已完成 | 阶段 1 | - | - |"),
    )
    write(tmp_path / "docs" / "plans" / "demo.md", "# 计划：demo\n")
    monkeypatch.setattr(check_plan_governance.sys, "argv", ["check", str(tmp_path)])

    assert check_plan_governance.main() == 1
    assert "缺少 Step 0 证据或验证方式章节" in capsys.readouterr().out


def test_completed_plan_without_coverage_fails(tmp_path, monkeypatch, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 已完成 | 阶段 1 | - | - |"),
    )
    write(tmp_path / "docs" / "plans" / "demo.md", plan_text())
    monkeypatch.setattr(check_plan_governance.sys, "argv", ["check", str(tmp_path)])

    assert check_plan_governance.main() == 1
    assert "缺少测试覆盖率证据" in capsys.readouterr().out


def test_completed_plan_with_coverage_passes(tmp_path, monkeypatch, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 已完成 | 阶段 1 | - | - |"),
    )
    write(tmp_path / "docs" / "plans" / "demo.md", plan_text(with_coverage=True))
    monkeypatch.setattr(check_plan_governance.sys, "argv", ["check", str(tmp_path)])

    assert check_plan_governance.main() == 0
    assert "检查通过" in capsys.readouterr().out


def test_non_completed_plan_without_coverage_ok(tmp_path, monkeypatch, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 待实施 | 阶段 1 | - | - |"),
    )
    write(tmp_path / "docs" / "plans" / "demo.md", plan_text())
    monkeypatch.setattr(check_plan_governance.sys, "argv", ["check", str(tmp_path)])

    assert check_plan_governance.main() == 0
    assert "检查通过" in capsys.readouterr().out


def test_has_coverage_evidence_chinese():
    assert check_plan_governance.has_coverage_evidence("### 测试覆盖率\n\n报告见附件。") is True


def test_has_coverage_evidence_english():
    assert check_plan_governance.has_coverage_evidence("## Coverage\n\n95% line coverage.") is True


def test_has_coverage_evidence_rejects_unrelated():
    assert check_plan_governance.has_coverage_evidence("本计划覆盖 API 迁移范围。") is False
