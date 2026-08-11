import importlib.util
import hashlib
import json
import shutil
import subprocess
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
    rows = []
    for line in row.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) == 5:
            cells.insert(3, "2026-07-05")
        rows.append("| " + " | ".join(cells) + " |")
    return f"""# PLAN_MAP

## 计划索引

| 计划 | 状态 | 当前阶段 | 最后更新 | 依赖 | 证据 |
|---|---|---|---|---|---|
{chr(10).join(rows)}
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


def plan_text_with_target(target, extra_text=""):
    return f"""# 计划：demo

## 影响模块或文件

- `{target}`

## Step 0 证据

已有基线。

## 验证方式

运行检查脚本。

## 未决问题

| 问题 | 推荐方案 | 是否阻塞当前阶段 | 状态 |
|---|---|---|---|
| - | - | 否 | 已延后 |

{extra_text}
"""


def readiness_plan_text(
    status="待实施",
    summary_status=None,
    phase_status=None,
    roadmap_phase="阶段 1",
    review_phase="阶段 1",
    history_conclusion="通过",
    include_summary=True,
    unresolved_blocker=False,
):
    summary_status = summary_status or status
    blocker_summary = "未解决阻塞" if unresolved_blocker else "无"
    blocker_row = "| 示例问题 | 暂不处理 | 是 | 未解决 |" if unresolved_blocker else "| - | - | 否 | 已延后 |"
    summary = f"""### 阶段准入摘要

| 字段 | 内容 |
|---|---|
| 准入状态 | {summary_status} |
{"| 阶段状态 | " + phase_status + " |" if phase_status else ""}
| Step 0 | [Step 0 证据](#step-0-证据) |
| 样本矩阵 | `tests/fixtures/readiness.md` |
| 验证方式 | `python3 -m pytest`，输出见测试报告 |
| 失败/回滚边界 | 失败返回非零并回滚当前阶段文档 |
| 当前阻塞项 | {blocker_summary} |
| 最新独立准入复核 | [最新复核](#最新独立准入复核) |
""" if include_summary else ""
    return f"""# 计划：demo

## 阶段路线图

| 阶段 | 目标 | 进入条件 | 验证方向 | 状态 |
|---|---|---|---|---|
| {roadmap_phase} | 阶段目标 | Step 0 已有 | pytest | {status} |

## 当前阶段

{summary}
### 最新独立准入复核

| 字段 | 内容 |
|---|---|
| 日期 | 2026-07-13 |
| 阶段 | {review_phase} |
| 结论 | 通过 |
| 证据 | `tests/fixtures/readiness.md` |
| 复核者 | 独立复核者 |

## 独立复核记录

| 日期 | 类型 | 阶段 | 结论 | 证据 | 复核者 |
|---|---|---|---|---|---|
| 2026-07-13 | 阶段准入复核 | {review_phase} | {history_conclusion} | `tests/fixtures/readiness.md` | 独立复核者 |

## Step 0 证据

现状基线见 `tests/fixtures/readiness.md`。

## 验证方式

运行 `python3 -m pytest`。

## 未决问题

| 问题 | 推荐方案 | 是否阻塞当前阶段 | 状态 |
|---|---|---|---|
{blocker_row}
"""


def test_design_plan_does_not_trigger_readiness_check(tmp_path, monkeypatch, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 设计中 | 阶段 1 | - | - |"),
    )
    write(tmp_path / "docs" / "plans" / "demo.md", plan_text())

    assert check_plan_governance.main([str(tmp_path)]) == 0
    output = capsys.readouterr().out
    assert "阶段准入摘要" not in output
    assert "检查通过" in output


def test_markdown_section_ignores_fenced_code_headings():
    text = """```markdown
### 最新独立准入复核

| 阶段 | 阶段 0 |
```

### 最新独立准入复核

真实章节内容。
"""

    section = check_plan_governance.markdown_section(text, ["最新独立准入复核"])
    assert "真实章节内容" in section
    assert "阶段 0" not in section


def test_complete_readiness_passes_default_and_strict(tmp_path, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 待实施 | 阶段 1 | - | - |"),
    )
    write(tmp_path / "docs" / "plans" / "demo.md", readiness_plan_text())

    assert check_plan_governance.main([str(tmp_path)]) == 0
    assert "阶段准入" not in capsys.readouterr().out
    assert check_plan_governance.main([str(tmp_path), "--strict-readiness"]) == 0
    assert "检查通过" in capsys.readouterr().out


def test_completed_current_phase_can_coexist_with_active_plan_status(tmp_path, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 实施中 | 阶段 1 | - | - |"),
    )
    write(
        tmp_path / "docs" / "plans" / "demo.md",
        readiness_plan_text(status="已完成", summary_status="实施中", phase_status="已完成"),
    )

    assert check_plan_governance.main([str(tmp_path), "--strict-readiness"]) == 0
    assert "检查通过" in capsys.readouterr().out


def test_missing_readiness_fields_warns_and_strict_fails(tmp_path, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 待实施 | 阶段 1 | - | - |"),
    )
    write(tmp_path / "docs" / "plans" / "demo.md", readiness_plan_text(include_summary=False))

    assert check_plan_governance.main([str(tmp_path)]) == 0
    output = capsys.readouterr().out
    assert "阶段准入摘要缺少字段" in output
    assert "检查通过" in output
    assert check_plan_governance.main([str(tmp_path), "--strict-readiness"]) == 1
    assert "阶段准入摘要缺少字段" in capsys.readouterr().out


def test_numbered_readiness_heading_explains_fixed_title(tmp_path, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 待实施 | 阶段 1 | - | - |"),
    )
    numbered = readiness_plan_text().replace("### 阶段准入摘要", "### 阶段 1 准入摘要")
    write(tmp_path / "docs" / "plans" / "demo.md", numbered)

    assert check_plan_governance.main([str(tmp_path)]) == 0
    output = capsys.readouterr().out
    assert "检测到标题 `阶段 1 准入摘要`" in output
    assert "请改为固定标题 `阶段准入摘要`" in output
    assert check_plan_governance.main([str(tmp_path), "--strict-readiness"]) == 1
    assert "阶段编号以 `PLAN_MAP.md` 的当前阶段为准" in capsys.readouterr().out


def test_numbered_review_headings_explain_fixed_titles(tmp_path, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 待实施 | 阶段 1 | - | - |"),
    )
    numbered = readiness_plan_text()
    numbered = numbered.replace("### 最新独立准入复核", "### 阶段 1 最新独立准入复核")
    numbered = numbered.replace("## 独立复核记录", "## 阶段 1 独立复核记录")
    write(tmp_path / "docs" / "plans" / "demo.md", numbered)

    assert check_plan_governance.main([str(tmp_path)]) == 0
    output = capsys.readouterr().out
    assert "请改为固定标题 `最新独立准入复核`" in output
    assert "请改为固定标题 `独立复核记录`" in output


def test_conflicting_latest_review_warns_and_strict_fails(tmp_path, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 待实施 | 阶段 1 | - | - |"),
    )
    write(
        tmp_path / "docs" / "plans" / "demo.md",
        readiness_plan_text(history_conclusion="未通过"),
    )

    assert check_plan_governance.main([str(tmp_path)]) == 0
    assert "结论冲突" in capsys.readouterr().out
    assert check_plan_governance.main([str(tmp_path), "--strict-readiness"]) == 1
    assert "结论冲突" in capsys.readouterr().out


def test_phase_pointer_mismatch_warns_and_strict_fails(tmp_path, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 待实施 | 阶段 2 | - | - |"),
    )
    write(tmp_path / "docs" / "plans" / "demo.md", readiness_plan_text())

    assert check_plan_governance.main([str(tmp_path)]) == 0
    output = capsys.readouterr().out
    assert "未在计划阶段路线图中找到" in output
    assert "最新独立准入复核阶段" in output
    assert check_plan_governance.main([str(tmp_path), "--strict-readiness"]) == 1
    assert "未在计划阶段路线图中找到" in capsys.readouterr().out


def test_open_blocker_keeps_existing_error_in_readiness_modes(tmp_path, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 待实施 | 阶段 1 | - | - |"),
    )
    write(
        tmp_path / "docs" / "plans" / "demo.md",
        readiness_plan_text(unresolved_blocker=True),
    )

    assert check_plan_governance.main([str(tmp_path)]) == 1
    assert "活跃计划仍有未解决的当前阶段阻塞项" in capsys.readouterr().out
    assert check_plan_governance.main([str(tmp_path), "--strict-readiness"]) == 1
    assert "活跃计划仍有未解决的当前阶段阻塞项" in capsys.readouterr().out


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


def test_legacy_plan_index_without_last_updated_fails(tmp_path, monkeypatch, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        """# PLAN_MAP

## 计划索引

| 计划 | 状态 | 当前阶段 | 依赖 | 证据 |
|---|---|---|---|---|
| [demo](plans/demo.md) | 待实施 | 阶段 1 | - | - |
""",
    )
    write(tmp_path / "docs" / "plans" / "demo.md", plan_text())
    monkeypatch.setattr(check_plan_governance.sys, "argv", ["check", str(tmp_path)])

    assert check_plan_governance.main() == 1
    assert "必须包含 `最后更新` 列" in capsys.readouterr().out


def test_invalid_last_updated_date_fails(tmp_path, monkeypatch, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 待实施 | 阶段 1 | 2026/07/05 | - | - |"),
    )
    write(tmp_path / "docs" / "plans" / "demo.md", plan_text())
    monkeypatch.setattr(check_plan_governance.sys, "argv", ["check", str(tmp_path)])

    assert check_plan_governance.main() == 1
    assert "最后更新日期不合法" in capsys.readouterr().out


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
    assert "活跃计划仍有未解决的当前阶段阻塞项" in capsys.readouterr().out


def test_ready_plan_with_open_blocker_fails(tmp_path, monkeypatch, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 待实施 | 阶段 1 | - | - |"),
    )
    write(tmp_path / "docs" / "plans" / "demo.md", plan_text(unresolved_blocker=True))
    monkeypatch.setattr(check_plan_governance.sys, "argv", ["check", str(tmp_path)])

    assert check_plan_governance.main() == 1
    assert "活跃计划仍有未解决的当前阶段阻塞项" in capsys.readouterr().out


def test_completed_plan_without_evidence_fails(tmp_path, monkeypatch, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 已完成 | 阶段 1 | - | - |"),
    )
    write(tmp_path / "docs" / "plans" / "demo.md", "# 计划：demo\n")
    monkeypatch.setattr(check_plan_governance.sys, "argv", ["check", str(tmp_path)])

    assert check_plan_governance.main() == 1
    assert "缺少有效 Step 0 证据或验证方式" in capsys.readouterr().out


def test_completed_plan_with_placeholder_evidence_fails(tmp_path, monkeypatch, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 已完成 | 阶段 1 | - | - |"),
    )
    write(
        tmp_path / "docs" / "plans" / "demo.md",
        plan_text(with_coverage=True)
        .replace("已有基线。", "待补充。")
        .replace("运行检查脚本。", "TODO"),
    )
    monkeypatch.setattr(check_plan_governance.sys, "argv", ["check", str(tmp_path)])

    assert check_plan_governance.main() == 1
    assert "缺少有效 Step 0 证据或验证方式" in capsys.readouterr().out


def test_completed_plan_without_coverage_fails(tmp_path, monkeypatch, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 已完成 | 阶段 1 | - | - |"),
    )
    write(tmp_path / "docs" / "plans" / "demo.md", plan_text())
    monkeypatch.setattr(check_plan_governance.sys, "argv", ["check", str(tmp_path)])

    assert check_plan_governance.main() == 1
    assert "缺少测试覆盖率证据" in capsys.readouterr().out


def test_completed_plan_with_placeholder_coverage_fails(tmp_path, monkeypatch, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 已完成 | 阶段 1 | - | - |"),
    )
    write(
        tmp_path / "docs" / "plans" / "demo.md",
        plan_text(with_coverage=True).replace(
            "pytest-cov 报告：98.8% 覆盖率。",
            "待补充。",
        ),
    )
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


def test_orphan_plan_warns_without_failing(tmp_path, monkeypatch, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 待实施 | 阶段 1 | - | - |"),
    )
    write(tmp_path / "docs" / "plans" / "demo.md", plan_text())
    write(tmp_path / "docs" / "plans" / "orphan.md", plan_text())
    monkeypatch.setattr(check_plan_governance.sys, "argv", ["check", str(tmp_path)])

    assert check_plan_governance.main() == 0
    output = capsys.readouterr().out
    assert "WARNING" in output
    assert "孤立计划" in output
    assert "检查通过" in output


def test_overlapping_active_plan_targets_warn_without_failing(tmp_path, monkeypatch, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map(
            "| [a](plans/a.md) | 待实施 | 阶段 1 | - | - |\n"
            "| [b](plans/b.md) | 设计中 | 阶段 1 | - | - |"
        ),
    )
    write(tmp_path / "docs" / "plans" / "a.md", plan_text_with_target("src/api.py"))
    write(tmp_path / "docs" / "plans" / "b.md", plan_text_with_target("src/api.py"))
    monkeypatch.setattr(check_plan_governance.sys, "argv", ["check", str(tmp_path)])

    assert check_plan_governance.main() == 0
    output = capsys.readouterr().out
    assert "WARNING" in output
    assert "多个活跃计划声明相同影响目标" in output
    assert "src/api.py" in output
    assert "检查通过" in output


def test_plan_reference_missing_from_declared_dependencies_warns(tmp_path, monkeypatch, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map(
            "| [a](plans/a.md) | 待实施 | 阶段 1 | - | - |\n"
            "| [b](plans/b.md) | 已完成 | 阶段 1 | - | - |"
        ),
    )
    write(
        tmp_path / "docs" / "plans" / "a.md",
        plan_text_with_target("src/a.py", "参考 [b](plans/b.md)。"),
    )
    write(tmp_path / "docs" / "plans" / "b.md", plan_text(with_coverage=True))
    monkeypatch.setattr(check_plan_governance.sys, "argv", ["check", str(tmp_path)])

    assert check_plan_governance.main() == 0
    output = capsys.readouterr().out
    assert "正文引用了计划 b" in output
    assert "依赖列未声明" in output


def test_relative_markdown_plan_reference_matches_declared_dependency(tmp_path, monkeypatch, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map(
            "| [a](plans/a.md) | 待实施 | 阶段 1 | b | - |\n"
            "| [b](plans/b.md) | 已完成 | 阶段 1 | - | - |"
        ),
    )
    write(
        tmp_path / "docs" / "plans" / "a.md",
        plan_text_with_target("src/a.py", "依赖 [b](b.md)。"),
    )
    write(tmp_path / "docs" / "plans" / "b.md", plan_text(with_coverage=True))
    monkeypatch.setattr(check_plan_governance.sys, "argv", ["check", str(tmp_path)])

    assert check_plan_governance.main() == 0
    output = capsys.readouterr().out
    assert "正文引用了计划" not in output
    assert "正文未引用" not in output


def test_declared_dependency_without_plan_reference_warns(tmp_path, monkeypatch, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map(
            "| [a](plans/a.md) | 待实施 | 阶段 1 | b | - |\n"
            "| [b](plans/b.md) | 已完成 | 阶段 1 | - | - |"
        ),
    )
    write(tmp_path / "docs" / "plans" / "a.md", plan_text_with_target("src/a.py"))
    write(tmp_path / "docs" / "plans" / "b.md", plan_text(with_coverage=True))
    monkeypatch.setattr(check_plan_governance.sys, "argv", ["check", str(tmp_path)])

    assert check_plan_governance.main() == 0
    output = capsys.readouterr().out
    assert "声明依赖 b" in output
    assert "正文未引用" in output


def test_self_plan_reference_is_ignored(tmp_path, monkeypatch, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 待实施 | 阶段 1 | - | - |"),
    )
    write(
        tmp_path / "docs" / "plans" / "demo.md",
        plan_text_with_target("src/demo.py", "自引用 [demo](plans/demo.md) 不应视为依赖。"),
    )
    monkeypatch.setattr(check_plan_governance.sys, "argv", ["check", str(tmp_path)])

    assert check_plan_governance.main() == 0
    output = capsys.readouterr().out
    assert "正文引用了计划" not in output
    assert "正文未引用" not in output


def test_target_matches_exact_file_or_directory_prefix():
    assert check_plan_governance.target_matches_path("src/api.py", "src/api.py") is True
    assert check_plan_governance.target_matches_path("src", "src/api.py") is True
    assert check_plan_governance.target_matches_path("./src/", "src/api.py") is True
    assert check_plan_governance.target_matches_path("src//nested/", "./src/nested/file.py") is True
    assert check_plan_governance.target_matches_path("src/api.py", "src/api_extra.py") is False


def test_extract_affected_targets_prefers_backticked_path_and_normalizes_text_path():
    plan_text = """# 计划：demo

## 影响模块或文件

- `./scripts/`: 检查脚本和 hook runtime
- `tests/test_check_plan_governance.py`
- README.md
- 待补充。
"""

    assert check_plan_governance.extract_affected_targets(plan_text) == [
        "scripts",
        "tests/test_check_plan_governance.py",
        "README.md",
    ]


def test_drift_uses_normalized_scope_targets(tmp_path, monkeypatch, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 待实施 | 阶段 1 | - | - |"),
    )
    write(
        tmp_path / "docs" / "plans" / "demo.md",
        plan_text_with_target("./scripts/: 检查脚本"),
    )

    def fake_run(cmd, **kwargs):
        class Result:
            stdout = "scripts/check_plan_governance.py\n"

        return Result()

    monkeypatch.setattr(check_plan_governance.subprocess, "run", fake_run)

    assert check_plan_governance.main([str(tmp_path), "--drift"]) == 0
    output = capsys.readouterr().out
    assert "变更文件未被活跃计划影响范围覆盖" not in output
    assert "检查通过" in output


def test_drift_warns_for_changed_file_outside_active_plan_targets(tmp_path, monkeypatch, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 待实施 | 阶段 1 | - | - |"),
    )
    write(tmp_path / "docs" / "plans" / "demo.md", plan_text_with_target("src/covered.py"))

    def fake_run(cmd, **kwargs):
        class Result:
            stdout = "src/uncovered.py\n" if cmd[1:3] == ["diff", "--name-only"] else ""

        return Result()

    monkeypatch.setattr(check_plan_governance.subprocess, "run", fake_run)

    assert check_plan_governance.main([str(tmp_path), "--drift"]) == 0
    output = capsys.readouterr().out
    assert "WARNING" in output
    assert "--drift" in output
    assert "src/uncovered.py" in output
    assert "检查通过" in output


def test_pre_commit_covered_changed_file_does_not_warn(tmp_path, monkeypatch, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 待实施 | 阶段 1 | - | - |"),
    )
    write(tmp_path / "docs" / "plans" / "demo.md", plan_text_with_target("src"))

    def fake_run(cmd, **kwargs):
        class Result:
            stdout = "src/covered.py\n"

        return Result()

    monkeypatch.setattr(check_plan_governance.subprocess, "run", fake_run)

    assert check_plan_governance.main([str(tmp_path), "--pre-commit"]) == 0
    output = capsys.readouterr().out
    assert "变更文件未被活跃计划影响范围覆盖" not in output
    assert "检查通过" in output


def test_optional_git_change_check_warns_when_git_is_unavailable(tmp_path, monkeypatch, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 待实施 | 阶段 1 | - | - |"),
    )
    write(tmp_path / "docs" / "plans" / "demo.md", plan_text_with_target("src"))

    def fail_run(*args, **kwargs):
        raise subprocess.CalledProcessError(128, args[0])

    monkeypatch.setattr(check_plan_governance.subprocess, "run", fail_run)

    assert check_plan_governance.main([str(tmp_path), "--drift"]) == 0
    output = capsys.readouterr().out
    assert "Git 变更检查不可用" in output
    assert "检查通过" in output


def test_stale_days_warns_for_old_active_plan(tmp_path, monkeypatch, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 待实施 | 阶段 1 | 2000-01-01 | - | - |"),
    )
    write(tmp_path / "docs" / "plans" / "demo.md", plan_text())
    monkeypatch.setattr(check_plan_governance.sys, "argv", ["check", str(tmp_path), "--stale-days", "10"])

    assert check_plan_governance.main() == 0
    output = capsys.readouterr().out
    assert "WARNING" in output
    assert "超过 --stale-days 10 阈值" in output


def test_stale_days_ignores_inactive_plan(tmp_path, monkeypatch, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 已废弃 | 阶段 1 | 2000-01-01 | - | - |"),
    )
    write(tmp_path / "docs" / "plans" / "demo.md", plan_text())
    monkeypatch.setattr(check_plan_governance.sys, "argv", ["check", str(tmp_path), "--stale-days", "10"])

    assert check_plan_governance.main() == 0
    assert "超过 --stale-days" not in capsys.readouterr().out


def test_negative_stale_days_fails(tmp_path, monkeypatch, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 待实施 | 阶段 1 | 2026-07-05 | - | - |"),
    )
    write(tmp_path / "docs" / "plans" / "demo.md", plan_text())
    monkeypatch.setattr(check_plan_governance.sys, "argv", ["check", str(tmp_path), "--stale-days", "-1"])

    assert check_plan_governance.main() == 1
    assert "--stale-days 必须是非负整数" in capsys.readouterr().out


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
    assert check_plan_governance.has_coverage_evidence("### 测试覆盖率\n\npytest-cov 报告：98.8% 覆盖率。") is True


def test_has_coverage_evidence_english():
    assert check_plan_governance.has_coverage_evidence("## Coverage\n\n95% line coverage.") is True


def test_has_coverage_evidence_rejects_placeholder():
    assert check_plan_governance.has_coverage_evidence("### 测试覆盖率\n\n待补充。") is False


def test_has_coverage_evidence_rejects_unrelated():
    assert check_plan_governance.has_coverage_evidence("本计划覆盖 API 迁移范围。") is False


def test_has_completion_evidence_rejects_empty_or_placeholder_sections():
    assert check_plan_governance.has_completion_evidence("### Step 0 证据\n\n### 验证方式\n\n") is False
    assert check_plan_governance.has_completion_evidence("### Step 0 证据\n\n待补充。\n\n### 验证方式\n\nTODO") is False


def test_has_completion_evidence_accepts_commands_paths_and_baselines():
    assert (
        check_plan_governance.has_completion_evidence(
            "### Step 0 证据\n\n现状基线见 `tests/fixtures/demo.json`。\n\n"
            "### 验证方式\n\n运行 `python3 -m pytest`。"
        )
        is True
    )


def test_attest_creates_snapshot_for_indexed_plan(tmp_path, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 已完成 | 阶段 1 | - | - |"),
    )
    write(tmp_path / "docs" / "plans" / "demo.md", plan_text(with_coverage=True))

    assert check_plan_governance.main([str(tmp_path), "--attest", "demo"]) == 0
    output = capsys.readouterr().out
    attestation = tmp_path / "docs" / "attestations" / "demo.json"
    data = json.loads(attestation.read_text(encoding="utf-8"))

    assert "已创建完成快照" in output
    assert data["plan"] == "demo"
    assert data["phase"] == "阶段 1"
    assert data["status"] == "已完成"
    assert len(data["plan_sha256"]) == 64
    assert len(data["plan_map_sha256"]) == 64
    assert data["plan_path"] == "docs/plans/demo.md"
    assert data["plan_map_path"] == "docs/PLAN_MAP.md"
    assert data["reason"] == "阶段完成快照"


def test_attest_unknown_plan_fails(tmp_path, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 已完成 | 阶段 1 | - | - |"),
    )
    write(tmp_path / "docs" / "plans" / "demo.md", plan_text(with_coverage=True))

    assert check_plan_governance.main([str(tmp_path), "--attest", "missing"]) == 1
    assert "未登记计划，无法创建完成快照" in capsys.readouterr().out


def test_check_attestations_passes_when_hashes_match(tmp_path, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 已完成 | 阶段 1 | - | - |"),
    )
    write(tmp_path / "docs" / "plans" / "demo.md", plan_text(with_coverage=True))

    assert check_plan_governance.main([str(tmp_path), "--attest", "demo"]) == 0
    capsys.readouterr()

    assert check_plan_governance.main([str(tmp_path), "--check-attestations"]) == 0
    output = capsys.readouterr().out
    assert "WARNING" not in output
    assert "检查通过" in output


def test_check_attestations_warns_when_plan_hash_changes(tmp_path, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 已完成 | 阶段 1 | - | - |"),
    )
    plan = tmp_path / "docs" / "plans" / "demo.md"
    write(plan, plan_text(with_coverage=True))

    assert check_plan_governance.main([str(tmp_path), "--attest", "demo"]) == 0
    capsys.readouterr()
    plan.write_text(plan.read_text(encoding="utf-8") + "\n补充说明。\n", encoding="utf-8")

    assert check_plan_governance.main([str(tmp_path), "--check-attestations"]) == 0
    output = capsys.readouterr().out
    assert "WARNING" in output
    assert "计划文件 hash 已变化" in output
    assert "检查通过" in output


def test_check_attestations_warns_when_plan_map_hash_changes(tmp_path, capsys):
    plan_map_path = tmp_path / "docs" / "PLAN_MAP.md"
    write(
        plan_map_path,
        plan_map("| [demo](plans/demo.md) | 已完成 | 阶段 1 | - | - |"),
    )
    write(tmp_path / "docs" / "plans" / "demo.md", plan_text(with_coverage=True))

    assert check_plan_governance.main([str(tmp_path), "--attest", "demo"]) == 0
    capsys.readouterr()
    plan_map_path.write_text(plan_map_path.read_text(encoding="utf-8") + "\n<!-- changed -->\n", encoding="utf-8")

    assert check_plan_governance.main([str(tmp_path), "--check-attestations"]) == 0
    output = capsys.readouterr().out
    assert "WARNING" in output
    assert "PLAN_MAP.md hash 已变化" in output
    assert "检查通过" in output


def test_check_attestations_warns_for_bad_json_and_missing_plan(tmp_path, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 已完成 | 阶段 1 | - | - |"),
    )
    write(tmp_path / "docs" / "plans" / "demo.md", plan_text(with_coverage=True))
    write(tmp_path / "docs" / "attestations" / "bad.json", "{")
    write(
        tmp_path / "docs" / "attestations" / "missing.json",
        json.dumps(
            {
                "plan": "missing",
                "phase": "阶段 1",
                "status": "已完成",
                "plan_path": "docs/plans/missing.md",
                "plan_map_path": "docs/PLAN_MAP.md",
                "plan_sha256": "0" * 64,
                "plan_map_sha256": "0" * 64,
            }
        ),
    )

    assert check_plan_governance.main([str(tmp_path), "--check-attestations"]) == 0
    output = capsys.readouterr().out
    assert "WARNING" in output
    assert "attestation JSON 无法解析" in output
    assert "快照引用了未登记计划" in output
    assert "检查通过" in output


def workset_plan_text(status="设计中", review="尚未进行", blocker=False, missing_summary=False, next_action=None):
    summary = "" if missing_summary else f"""### 阶段准入摘要

| 字段 | 内容 |
|---|---|
| 准入状态 | {status} |
| Step 0 | 基线 |
| 样本矩阵 | fixture |
| 验证方式 | pytest |
| 失败/回滚边界 | 失败停止 |
| 当前阻塞项 | {'存在阻塞' if blocker else '无'} |
| 最新独立准入复核 | {review} |
"""
    action = f"\n下一动作: {next_action}\n" if next_action else ""
    blocker_row = "| 阻塞 | 先处理 | 是 | 待处理 |" if blocker else "| - | - | 否 | 已决定 |"
    return f"""# 计划

## 当前阶段
{action}
{summary}
## 最新独立准入复核

| 字段 | 内容 |
|---|---|
| 日期 | 2026-08-10 |
| 阶段 | 阶段 1 |
| 结论 | {'通过' if review == '通过' else '尚未进行'} |
| 证据 | fixture |
| 复核者 | tester |

## 未决问题

| 问题 | 推荐方案 | 是否阻塞当前阶段 | 状态 |
|---|---|---|---|
{blocker_row}
"""


def autonomous_step_plan(rows, policy="serial", enabled=True, include_table=True):
    mode = "execution_mode: autonomous-continuous\n" if enabled else ""
    table = "" if not include_table else f"""### 执行清单

| 步骤 ID | 前置步骤 | 动作 | 证据 | 完成条件 | 状态 | 分支记录 |
|---|---|---|---|---|---|---|
{rows}
"""
    return f"""# 计划

{mode}execution_policy: {policy}

## 当前阶段

{table}
"""


def test_workset_derives_actions_history_and_parallel_state(tmp_path, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map(
            "\n".join(
                [
                    "| [ready](plans/ready.md) | 待实施 | 阶段 1 | - | - |",
                    "| [review](plans/review.md) | 设计中 | 阶段 1 | - | - |",
                    "| [step0](plans/step0.md) | 设计中 | 阶段 1 | - | - |",
                    "| [blocked](plans/blocked.md) | 设计中 | 阶段 1 | - | - |",
                    "| [running](plans/running.md) | 实施中 | 阶段 1 | - | - |",
                    "| [unknown](plans/unknown.md) | 实施中 | 阶段 1 | - | - |",
                    "| [history](plans/history.md) | 已完成 | 阶段 1 | - | - |",
                ]
            )
        )
        + "\n## 阶段关系\n\n| 来源计划 | 来源阶段 | 目标计划 | 目标阶段 | 关系类型 | 解除条件 | 证据 |\n|---|---|---|---|---|---|---|\n| ready | 阶段 1 | review | 阶段 1 | soft_context | - | rel.md |\n",
    )
    write(tmp_path / "docs" / "plans" / "ready.md", workset_plan_text("待实施", "通过"))
    write(tmp_path / "docs" / "plans" / "review.md", workset_plan_text("设计中"))
    write(tmp_path / "docs" / "plans" / "step0.md", workset_plan_text("设计中", missing_summary=True))
    write(tmp_path / "docs" / "plans" / "blocked.md", workset_plan_text("设计中", blocker=True))
    write(tmp_path / "docs" / "plans" / "running.md", workset_plan_text("实施中", next_action="验证"))
    write(tmp_path / "docs" / "plans" / "unknown.md", workset_plan_text("实施中"))
    write(tmp_path / "docs" / "plans" / "history.md", workset_plan_text("已完成", "通过"))

    assert check_plan_governance.main(["--workset", "--json", str(tmp_path)]) == 0
    payload = json.loads(capsys.readouterr().out)
    items = {item["plan"]: item for item in payload["plans"]}
    assert "history" not in items
    assert items["ready"]["next_action"]["kind"] == "implement"
    assert items["review"]["next_action"]["kind"] == "independent_review"
    assert items["step0"]["next_action"]["kind"] == "complete_step0"
    assert items["blocked"]["next_action"]["kind"] == "resolve_blocker"
    assert items["running"]["next_action"]["kind"] == "verify"
    assert items["unknown"]["next_action"]["state"] == "unknown"
    assert items["ready"]["parallel"]["state"] == "known"
    assert items["ready"]["parallel"]["peers"] == ["review"]

    assert check_plan_governance.main(["--workset", "--include-history", str(tmp_path)]) == 0
    assert "history" in capsys.readouterr().out


def test_workset_include_history_keeps_unstructured_legacy_plan_compatible(tmp_path, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [history](plans/history.md) | 已完成 | 阶段 1 | - | - |"),
    )
    write(tmp_path / "docs" / "plans" / "history.md", "# 旧计划\n\n只有自然语言记录。\n")

    assert check_plan_governance.main(["--workset", "--include-history", "--json", str(tmp_path)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["plans"][0]["plan"] == "history"
    assert payload["plans"][0]["readiness"] == "unknown"


def test_workset_reads_only_current_recent_evidence(tmp_path, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [running](plans/running.md) | 实施中 | 阶段 1 | - | - |"),
    )
    plan = workset_plan_text("实施中", next_action="验证")
    plan = plan.replace(
        "## 最新独立准入复核",
        "### 最近实施/验证记录\n\n"
        "| 日期 | 类型 | 动作/结果 | 证据 | 状态 | 记录者 |\n"
        "|---|---|---|---|---|---|\n"
        "| 2026-08-10 | 验证 | 只读回放 | 命令输出 | 通过 | tester |\n\n"
        "## 最新独立准入复核",
    )
    write(tmp_path / "docs" / "plans" / "running.md", plan)

    assert check_plan_governance.main(["--workset", "--json", str(tmp_path)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["plans"][0]["recent_evidence"][0][2] == "只读回放"


def test_workset_handles_missing_map_plan_and_unknown_status(tmp_path, capsys):
    assert check_plan_governance.main(["--workset", "--json", str(tmp_path)]) == 1
    assert "未找到 docs/PLAN_MAP.md" in capsys.readouterr().out

    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map(
            "\n".join(
                [
                    "| [missing](plans/missing.md) | 设计中 | 阶段 1 | - | - |",
                    "| [invalid](plans/invalid.md) | 不合法 | 阶段 1 | - | - |",
                ]
            )
        ),
    )
    write(tmp_path / "docs" / "plans" / "invalid.md", workset_plan_text("不合法"))
    assert check_plan_governance.main(["--workset", "--json", "--include-history", str(tmp_path)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert any("计划文件不存在" in warning for warning in payload["warnings"])
    assert any("状态非法" in warning for warning in payload["warnings"])
    assert payload["plans"] == []
    assert check_plan_governance.main(
        ["--workset", "--strict-readiness", str(tmp_path)]
    ) == 1
    assert "ERROR" in capsys.readouterr().out

    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [missing](plans/missing.md) | 设计中 | 阶段 1 | - | - |"),
    )
    assert check_plan_governance.main(["--workset", "--strict-readiness", str(tmp_path)]) == 1
    assert "ERROR" in capsys.readouterr().out


def test_workset_rejects_duplicate_plan_ids_without_actions(tmp_path, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map(
            "| [demo](plans/demo.md) | 设计中 | 阶段 1 | - | - |\n"
            "| [demo](plans/demo.md) | 待实施 | 阶段 1 | - | - |"
        ),
    )
    write(tmp_path / "docs" / "plans" / "demo.md", workset_plan_text("设计中"))

    assert check_plan_governance.main(["--workset", "--json", str(tmp_path)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert any("重复计划 ID" in warning for warning in payload["warnings"])
    assert payload["plans"] == []


def test_validate_steps_valid_not_enabled_and_invalid_modes(tmp_path, capsys):
    write(tmp_path / "docs" / "PLAN_MAP.md", plan_map("| [demo](plans/demo.md) | 设计中 | 阶段 1 | - | - |"))
    valid_rows = "| S1 | - | 建立基线 | 测试输出 | 基线存在 | 已完成 | - |\n| S2 | S1 | 校验方案 | 测试输出 | 校验通过 | 未开始 | - |\n| S3 | S2 | 记录分支 | 替代输出 | 分支已记录 | 不适用 | 触发条件：不满足；理由：无需执行；替代证据：替代输出 |"
    write(tmp_path / "docs" / "plans" / "demo.md", autonomous_step_plan(valid_rows))

    assert check_plan_governance.main(["--validate-steps", "--json", "demo", "--root", str(tmp_path)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "valid"
    assert payload["execution_policy"] == "serial"
    assert len(payload["steps"]) == 3

    write(tmp_path / "docs" / "plans" / "demo.md", "# 旧计划\n\n## 实施步骤\n\n- 普通步骤\n")
    assert check_plan_governance.main(["--validate-steps", "--json", "demo", "--root", str(tmp_path)]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "not_enabled"

    invalid_rows = "| S1 | Missing | 动作 | 证据 | 完成 | 取消 | - |\n| S1 | S1 | 动作 | 证据 | 完成 | 不适用 | - |"
    write(tmp_path / "docs" / "plans" / "demo.md", autonomous_step_plan(invalid_rows, policy="bad"))
    assert check_plan_governance.main(["--validate-steps", "demo", "--root", str(tmp_path)]) == 0
    output = capsys.readouterr().out
    assert "WARNING" in output
    assert check_plan_governance.main(["--validate-steps", "--strict-readiness", "--json", "demo", "--root", str(tmp_path)]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "invalid"
    assert any("重复" in error for error in payload["errors"])


def test_validate_steps_rejects_missing_table_fields_unknown_dependency_and_cycle(tmp_path, capsys):
    write(tmp_path / "docs" / "PLAN_MAP.md", plan_map("| [demo](plans/demo.md) | 设计中 | 阶段 1 | - | - |"))
    write(tmp_path / "docs" / "plans" / "demo.md", autonomous_step_plan("", include_table=False))
    assert check_plan_governance.main(["--validate-steps", "--json", "demo", "--root", str(tmp_path)]) == 0
    assert "执行清单" in json.loads(capsys.readouterr().out)["errors"][0]

    write(tmp_path / "docs" / "plans" / "demo.md", autonomous_step_plan("", include_table=True))
    assert check_plan_governance.main(["--validate-steps", "--json", "demo", "--root", str(tmp_path)]) == 0
    assert "至少需要一个步骤" in json.loads(capsys.readouterr().out)["errors"][0]

    bad_header = "### 执行清单\n\n| A | B |\n|---|---|\n| x | y |\n"
    write(tmp_path / "docs" / "plans" / "demo.md", "# 计划\n\nexecution_mode: autonomous-continuous\n\n" + bad_header)
    assert check_plan_governance.main(["--validate-steps", "--json", "demo", "--root", str(tmp_path)]) == 0
    assert "固定七列表头" in json.loads(capsys.readouterr().out)["errors"][0]

    cycle_rows = "| S1 | S2 | 动作 | 证据 | 完成 | 未开始 | - |\n| S2 | S1 Missing | 动作 | 证据 | 完成 | 未开始 | - |"
    write(tmp_path / "docs" / "plans" / "demo.md", autonomous_step_plan(cycle_rows, policy="parallel"))
    assert check_plan_governance.main(["--validate-steps", "--json", "demo", "--root", str(tmp_path)]) == 0
    errors = json.loads(capsys.readouterr().out)["errors"]
    assert any("未知前置" in error for error in errors)

    branch_rows = "| S1 | - | 动作 | 证据 | 完成 | 不适用 | 仅记录了理由 |"
    write(tmp_path / "docs" / "plans" / "demo.md", autonomous_step_plan(branch_rows))
    assert check_plan_governance.main(["--validate-steps", "--json", "demo", "--root", str(tmp_path)]) == 0
    errors = json.loads(capsys.readouterr().out)["errors"]
    assert any("触发条件" in error for error in errors)

    empty_branch_rows = "| S1 | - | 动作 | 证据 | 完成 | 不适用 | 触发条件：；理由：；替代证据： |"
    write(tmp_path / "docs" / "plans" / "demo.md", autonomous_step_plan(empty_branch_rows))
    assert check_plan_governance.main(["--validate-steps", "--strict-readiness", "--json", "demo", "--root", str(tmp_path)]) == 1
    errors = json.loads(capsys.readouterr().out)["errors"]
    assert any("有效触发条件" in error for error in errors)

    cycle_rows = "| S1 | S2 | 动作 | 证据 | 完成 | 未开始 | - |\n| S2 | S1 | 动作 | 证据 | 完成 | 未开始 | - |"
    write(tmp_path / "docs" / "plans" / "demo.md", autonomous_step_plan(cycle_rows, policy="parallel"))
    assert check_plan_governance.main(["--validate-steps", "--json", "demo", "--root", str(tmp_path)]) == 0
    assert "环依赖" in "\n".join(json.loads(capsys.readouterr().out)["errors"])


def relation_fixture(name, tmp_path):
    source = Path(__file__).parent / "fixtures" / "plan-governance-stage2-relations" / name
    docs = tmp_path / "docs"
    (docs / "plans").mkdir(parents=True)
    shutil.copy2(source / "docs" / "PLAN_MAP.md", docs / "PLAN_MAP.md")
    for plan in (source / "docs" / "plans").glob("*.md"):
        shutil.copy2(plan, docs / "plans" / plan.name)
    return tmp_path


def test_stage2_relation_fixture_valid_and_legacy_compatible(tmp_path, capsys):
    valid = relation_fixture("valid", tmp_path / "valid")
    assert check_plan_governance.main([str(valid), "--strict-readiness"]) == 0
    output = capsys.readouterr().out
    assert "计划治理检查通过" in output

    legacy = relation_fixture("legacy", tmp_path / "legacy")
    assert check_plan_governance.main([str(legacy)]) == 0
    output = capsys.readouterr().out
    assert "计划治理检查通过" in output
    assert check_plan_governance.main([str(legacy), "--strict-readiness"]) == 0
    output = capsys.readouterr().out
    assert "计划治理检查通过" in output
    assert "阶段关系" not in output
    assert check_plan_governance.main(["--workset", "--json", str(legacy)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert all(item["parallel"]["state"] == "unknown" for item in payload["plans"])


def test_stage2_relation_fixture_accepts_soft_context_and_evidence(tmp_path, capsys):
    valid = relation_fixture("valid", tmp_path / "valid")
    assert check_plan_governance.main([str(valid), "--strict-readiness"]) == 0
    output = capsys.readouterr().out
    assert "计划治理检查通过" in output
    assert "soft_context" in (valid / "docs" / "PLAN_MAP.md").read_text(encoding="utf-8")
    assert "evidence" in (valid / "docs" / "PLAN_MAP.md").read_text(encoding="utf-8")


def test_stage2_relation_fixture_invalid_default_warns_and_strict_fails(tmp_path, capsys):
    invalid = relation_fixture("invalid-reference", tmp_path / "invalid")
    assert check_plan_governance.main([str(invalid)]) == 0
    output = capsys.readouterr().out
    assert "阶段关系第" in output
    assert "计划治理检查通过" in output

    assert check_plan_governance.main([str(invalid), "--strict-readiness"]) == 1
    output = capsys.readouterr().out
    assert "ERROR: PLAN_MAP.md: 阶段关系第" in output
    assert "来源阶段不存在于计划路线图" in output
    assert "目标阶段不存在于计划路线图" in output
    assert "证据链接不存在" in output
    assert "缺少有效解除条件" in output
    assert "缺少有效证据" in output

    assert check_plan_governance.main(["--workset", "--json", str(invalid)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert all(item["parallel"]["state"] == "unknown" for item in payload["plans"])


def test_stage2_relation_fixture_cycle_and_self_edge_are_rejected(tmp_path, capsys):
    cycle = relation_fixture("cycle", tmp_path / "cycle")
    assert check_plan_governance.main([str(cycle)]) == 0
    output = capsys.readouterr().out
    assert "环依赖" in output
    assert "不能引用自身同一阶段" in output

    assert check_plan_governance.main([str(cycle), "--strict-readiness"]) == 1
    assert "ERROR: PLAN_MAP.md: 阶段关系" in capsys.readouterr().out


def test_stage2_shared_write_contract_is_optional_but_invalid_rows_fail_strict(tmp_path, capsys):
    invalid = relation_fixture("shared-write-invalid", tmp_path / "shared-write-invalid")
    assert check_plan_governance.main([str(invalid)]) == 0
    output = capsys.readouterr().out
    assert "共享写入约束第" in output
    assert "约束类型非法" in output

    assert check_plan_governance.main([str(invalid), "--strict-readiness"]) == 1
    assert "共享写入约束第" in capsys.readouterr().out


def test_stage2_legacy_dependency_conflict_warns_without_overriding_old_data(tmp_path, capsys):
    root = relation_fixture("legacy-conflict", tmp_path / "legacy-conflict")
    assert check_plan_governance.main([str(root)]) == 0
    output = capsys.readouterr().out
    assert "hard_gate" in output
    assert "计划索引依赖列未包含 alpha" in output
    assert "gamma" in (root / "docs" / "PLAN_MAP.md").read_text(encoding="utf-8")
    assert check_plan_governance.main([str(root), "--strict-readiness"]) == 0
    capsys.readouterr()
    assert check_plan_governance.main(["--workset", "--json", str(root)]) == 0
    payload = json.loads(capsys.readouterr().out)
    beta = next(item for item in payload["plans"] if item["plan"] == "beta")
    assert beta["parallel"]["state"] == "known"


def test_stage2_legacy_four_column_shared_write_table_remains_compatible(tmp_path, capsys):
    root = relation_fixture("shared-write-legacy", tmp_path / "shared-write-legacy")
    assert check_plan_governance.main([str(root), "--strict-readiness"]) == 0
    assert "计划治理检查通过" in capsys.readouterr().out


def test_stage2_nine_column_shared_write_table_has_priority_over_human_summary(tmp_path, capsys):
    root = relation_fixture("shared-write-conflict", tmp_path / "shared-write-conflict")
    assert check_plan_governance.main([str(root), "--strict-readiness"]) == 0
    output = capsys.readouterr().out
    assert "计划治理检查通过" in output
    assert "beta 先于 alpha" in (root / "docs" / "PLAN_MAP.md").read_text(encoding="utf-8")


def test_stage2_relation_queries_are_read_only(tmp_path, capsys):
    root = relation_fixture("valid", tmp_path / "valid")
    files = [root / "docs" / "PLAN_MAP.md", *sorted((root / "docs" / "plans").glob("*.md"))]
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    assert check_plan_governance.main([str(root), "--strict-readiness"]) == 0
    capsys.readouterr()
    assert check_plan_governance.main(["--workset", "--json", str(root)]) == 0
    capsys.readouterr()
    after = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    assert before == after
