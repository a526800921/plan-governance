import importlib.util
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest


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


def git_commit(root):
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-m", "baseline"], cwd=root, check=True, capture_output=True)


def phase_evidence_plan_text(evidence="docs/evidence.md"):
    return f"""# 计划：demo

## 影响模块或文件

- `src/`

## 当前阶段

### 阶段证据

- `{evidence}`

## Step 0 证据

现状基线见 `tests/fixtures/demo.md`。

## 验证方式

运行 `python3 -m pytest`。
"""


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


def test_completion_review_record_does_not_replace_latest_readiness_review(tmp_path, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 实施中 | 阶段 1 | 2026-08-11 | - | - |"),
    )
    plan = readiness_plan_text(status="实施中")
    plan = plan.replace(
        "## Step 0 证据",
        "| 2026-08-11 | 阶段完成验收 | 阶段 1 | 未通过：治理同步尚未完成 | `docs/review.md` | Reviewer |\n\n## Step 0 证据",
    )
    write(tmp_path / "docs" / "plans" / "demo.md", plan)
    assert check_plan_governance.main([str(tmp_path), "--strict-readiness"]) == 0
    assert "历史记录最后一条结论冲突" not in capsys.readouterr().out


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


def test_drift_covers_plan_map_row_plan_file_and_phase_evidence(tmp_path, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 待实施 | 阶段 1 | 2026-08-11 | - | - |"),
    )
    write(tmp_path / "docs" / "plans" / "demo.md", phase_evidence_plan_text())
    write(tmp_path / "docs" / "evidence.md", "baseline\n")
    git_commit(tmp_path)

    plan = tmp_path / "docs" / "plans" / "demo.md"
    plan.write_text(plan.read_text(encoding="utf-8") + "\n实施记录。\n", encoding="utf-8")
    plan_map_path = tmp_path / "docs" / "PLAN_MAP.md"
    plan_map_path.write_text(
        plan_map_path.read_text(encoding="utf-8").replace("阶段 1", "阶段 2"),
        encoding="utf-8",
    )
    evidence = tmp_path / "docs" / "evidence.md"
    evidence.write_text(evidence.read_text(encoding="utf-8") + "updated\n", encoding="utf-8")
    write(tmp_path / "unrelated.txt", "should warn\n")

    assert check_plan_governance.main([str(tmp_path), "--drift"]) == 0
    output = capsys.readouterr().out
    assert "PLAN_MAP.md 变更无法唯一归属" not in output
    assert "docs/plans/demo.md" not in output
    assert "docs/evidence.md" not in output
    assert "unrelated.txt" in output


def test_drift_completed_plan_closing_window_is_narrow(tmp_path, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 已完成 | 阶段 1 | 2026-08-11 | - | - |"),
    )
    write(
        tmp_path / "docs" / "plans" / "demo.md",
        phase_evidence_plan_text() + "\n## 测试覆盖率\n\npytest 通过，覆盖率 98%。\n",
    )
    write(tmp_path / "docs" / "evidence.md", "baseline\n")
    git_commit(tmp_path)

    plan = tmp_path / "docs" / "plans" / "demo.md"
    plan.write_text(plan.read_text(encoding="utf-8") + "\n完成记录。\n", encoding="utf-8")
    plan_map_path = tmp_path / "docs" / "PLAN_MAP.md"
    plan_map_path.write_text(
        plan_map_path.read_text(encoding="utf-8").replace("阶段 1", "阶段 2"),
        encoding="utf-8",
    )
    evidence = tmp_path / "docs" / "evidence.md"
    evidence.write_text(evidence.read_text(encoding="utf-8") + "updated\n", encoding="utf-8")
    write(tmp_path / "src" / "new.py", "new work\n")

    assert check_plan_governance.main([str(tmp_path), "--drift"]) == 0
    output = capsys.readouterr().out
    assert "PLAN_MAP.md 变更无法唯一归属" not in output
    assert "docs/plans/demo.md" not in output
    assert "docs/evidence.md" not in output
    assert "src/new.py" in output


def test_drift_helpers_handle_empty_files_and_no_plan_targets():
    warnings = []
    check_plan_governance.warn_uncovered_changes(warnings, "--drift", set(), {})
    assert warnings == []

    check_plan_governance.warn_uncovered_changes(
        warnings,
        "--drift",
        {"src/uncovered.py"},
        {},
    )
    assert "没有活跃计划声明影响范围" in warnings[0]


def test_safe_relative_path_rejects_absolute_drive_and_parent_paths():
    assert check_plan_governance.safe_relative_path("/tmp/snapshot.json") is None
    assert check_plan_governance.safe_relative_path("C:/tmp/snapshot.json") is None
    assert check_plan_governance.safe_relative_path("docs/../snapshot.json") is None


def test_pre_commit_uses_the_same_plan_map_and_phase_evidence_ownership(tmp_path, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 待实施 | 阶段 1 | 2026-08-11 | - | - |"),
    )
    write(tmp_path / "docs" / "plans" / "demo.md", phase_evidence_plan_text())
    write(tmp_path / "docs" / "evidence.md", "baseline\n")
    git_commit(tmp_path)

    plan = tmp_path / "docs" / "plans" / "demo.md"
    plan.write_text(plan.read_text(encoding="utf-8") + "\nstaged implementation\n", encoding="utf-8")
    plan_map_path = tmp_path / "docs" / "PLAN_MAP.md"
    plan_map_path.write_text(
        plan_map_path.read_text(encoding="utf-8").replace("阶段 1", "阶段 2"),
        encoding="utf-8",
    )
    evidence = tmp_path / "docs" / "evidence.md"
    evidence.write_text(evidence.read_text(encoding="utf-8") + "staged evidence\n", encoding="utf-8")
    subprocess.run(["git", "add", "docs/PLAN_MAP.md", "docs/plans/demo.md", "docs/evidence.md"], cwd=tmp_path, check=True)

    assert check_plan_governance.main([str(tmp_path), "--pre-commit"]) == 0
    output = capsys.readouterr().out
    assert "PLAN_MAP.md 变更无法唯一归属" not in output
    assert "docs/evidence.md" not in output


def test_phase_evidence_rejects_absolute_glob_and_parent_paths(tmp_path, capsys):
    text = phase_evidence_plan_text("/tmp/evidence.md")
    text = text.replace("- `/tmp/evidence.md`", "- `/tmp/evidence.md`\n- `docs/*.md`\n- `../outside.md`")
    valid, invalid = check_plan_governance.extract_phase_evidence_targets(text)
    assert valid == []
    assert invalid == ["/tmp/evidence.md", "docs/*.md", "../outside.md"]
    write(tmp_path / "docs" / "PLAN_MAP.md", plan_map("| [demo](plans/demo.md) | 待实施 | 阶段 1 | - | - |"))
    write(tmp_path / "docs" / "plans" / "demo.md", text)

    # 直接验证非法声明不会成为覆盖目标；Git 变更获取由现有临时项目测试覆盖。
    assert check_plan_governance.main([str(tmp_path), "--drift"]) == 0
    output = capsys.readouterr().out
    assert "阶段证据路径非法" in output


def test_plan_map_line_with_two_linked_plans_is_ambiguous():
    line = "| [alpha](plans/alpha.md) | [beta](plans/beta.md) |"
    assert check_plan_governance.plan_map_line_candidates(line, {"alpha", "beta"}) == ["alpha", "beta"]
    assert check_plan_governance.plan_map_change_is_covered([["alpha", "beta"]], {"alpha", "beta"}) is False


def test_attest_purpose_creates_relation_snapshot_and_reports_current(tmp_path, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 已完成 | 阶段 1 | - | - |"),
    )
    write(tmp_path / "docs" / "plans" / "demo.md", plan_text(with_coverage=True))

    assert check_plan_governance.main([str(tmp_path), "--attest", "demo", "--attest-purpose", "release_gate"]) == 0
    capsys.readouterr()
    snapshots = list((tmp_path / "docs" / "attestations").glob("demo--release_gate--*.json"))
    assert len(snapshots) == 1
    data = json.loads(snapshots[0].read_text(encoding="utf-8"))
    assert data["purpose"] == "release_gate"
    assert data["review_status"] == "current"
    assert data["supersedes"] == ""
    assert check_plan_governance.ATTESTATION_SNAPSHOT_RE.fullmatch(data["snapshot_id"])

    assert check_plan_governance.main([str(tmp_path), "--check-attestations"]) == 0
    output = capsys.readouterr().out
    assert "purpose=release_gate" in output
    assert "status=current" in output
    plan = tmp_path / "docs" / "plans" / "demo.md"
    plan.write_text(plan.read_text(encoding="utf-8") + "\n人工复核前的文档修订。\n", encoding="utf-8")
    assert check_plan_governance.main([str(tmp_path), "--check-attestations"]) == 0
    output = capsys.readouterr().out
    assert "计划文件 hash 已变化" in output
    assert "status=needs_review" in output


def test_create_attestation_rejects_invalid_relation_arguments(tmp_path):
    plan_map_path = tmp_path / "docs" / "PLAN_MAP.md"
    plan_path = tmp_path / "docs" / "plans" / "demo.md"
    write(plan_map_path, "# PLAN_MAP\n")
    write(plan_path, "# demo\n")
    plans = {
        "demo": {
            "path": plan_path,
            "phase": "阶段 1",
            "status": "已完成",
        }
    }

    errors = []
    assert check_plan_governance.create_attestation(
        tmp_path,
        plan_map_path,
        plans,
        "demo",
        errors,
        purpose="unsupported",
    ) is None
    assert "purpose 非法" in errors[-1]

    errors = []
    assert check_plan_governance.create_attestation(
        tmp_path,
        plan_map_path,
        plans,
        "demo",
        errors,
        purpose="release_gate",
        review_status="unsupported",
    ) is None
    assert "review_status 非法" in errors[-1]

    errors = []
    assert check_plan_governance.create_attestation(
        tmp_path,
        plan_map_path,
        plans,
        "demo",
        errors,
        purpose="release_gate",
        supersedes="../outside.json",
    ) is None
    assert "supersedes 必须是仓库内相对路径" in errors[-1]


def test_attestation_supersedes_old_snapshot_and_duplicate_current_is_strict_error(tmp_path, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 已完成 | 阶段 1 | - | - |"),
    )
    write(tmp_path / "docs" / "plans" / "demo.md", plan_text(with_coverage=True))
    assert check_plan_governance.main([str(tmp_path), "--attest", "demo", "--attest-purpose", "release_gate"]) == 0
    capsys.readouterr()
    first = next((tmp_path / "docs" / "attestations").glob("demo--release_gate--*.json"))
    first_rel = first.relative_to(tmp_path).as_posix()
    assert check_plan_governance.main(
        [str(tmp_path), "--attest", "demo", "--attest-purpose", "release_gate", "--supersedes", first_rel]
    ) == 0
    capsys.readouterr()
    assert check_plan_governance.main([str(tmp_path), "--check-attestations", "--strict-readiness"]) == 0
    capsys.readouterr()

    duplicate = tmp_path / "docs" / "attestations" / "demo--release_gate--20260811T010203Z-deadbeef.json"
    first_data = json.loads(first.read_text(encoding="utf-8"))
    first_data.update(
        {
            "snapshot_id": "20260811T010203Z-deadbeef",
            "supersedes": "",
            "review_status": "current",
        }
    )
    duplicate.write_text(json.dumps(first_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    assert check_plan_governance.main([str(tmp_path), "--check-attestations", "--strict-readiness"]) == 1
    assert "多个 current" in capsys.readouterr().out


def test_attestation_supersedes_cycle_is_warning_by_default_and_error_in_strict_mode(tmp_path, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 已完成 | 阶段 1 | - | - |"),
    )
    plan = tmp_path / "docs" / "plans" / "demo.md"
    write(plan, plan_text(with_coverage=True))
    plan_map_path = tmp_path / "docs" / "PLAN_MAP.md"
    base = {
        "plan": "demo",
        "phase": "阶段 1",
        "status": "已完成",
        "plan_path": "docs/plans/demo.md",
        "plan_map_path": "docs/PLAN_MAP.md",
        "plan_sha256": hashlib.sha256(plan.read_bytes()).hexdigest(),
        "plan_map_sha256": hashlib.sha256(plan_map_path.read_bytes()).hexdigest(),
        "created_at": "2026-08-11T01:02:03Z",
        "created_by": "test",
        "reason": "测试",
        "purpose": "release_gate",
        "review_status": "current",
    }
    a = "docs/attestations/demo--release_gate--20260811T010203Z-aaaaaaaa.json"
    b = "docs/attestations/demo--release_gate--20260811T010204Z-bbbbbbbb.json"
    base_a = {**base, "snapshot_id": "20260811T010203Z-aaaaaaaa", "supersedes": b}
    base_b = {**base, "snapshot_id": "20260811T010204Z-bbbbbbbb", "supersedes": a}
    write(tmp_path / a, json.dumps(base_a, ensure_ascii=False, indent=2) + "\n")
    write(tmp_path / b, json.dumps(base_b, ensure_ascii=False, indent=2) + "\n")

    assert check_plan_governance.main([str(tmp_path), "--check-attestations"]) == 0
    assert "supersedes 存在环" in capsys.readouterr().out
    assert check_plan_governance.main([str(tmp_path), "--check-attestations", "--strict-readiness"]) == 1
    assert "supersedes 存在环" in capsys.readouterr().out


def test_attestation_missing_supersedes_target_is_strict_error(tmp_path, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 已完成 | 阶段 1 | - | - |"),
    )
    plan = tmp_path / "docs" / "plans" / "demo.md"
    write(plan, plan_text(with_coverage=True))
    plan_map_path = tmp_path / "docs" / "PLAN_MAP.md"
    data = {
        "plan": "demo",
        "phase": "阶段 1",
        "status": "已完成",
        "plan_path": "docs/plans/demo.md",
        "plan_map_path": "docs/PLAN_MAP.md",
        "plan_sha256": hashlib.sha256(plan.read_bytes()).hexdigest(),
        "plan_map_sha256": hashlib.sha256(plan_map_path.read_bytes()).hexdigest(),
        "created_at": "2026-08-11T01:02:03Z",
        "created_by": "test",
        "reason": "测试",
        "purpose": "compliance",
        "snapshot_id": "20260811T010203Z-cccccccc",
        "supersedes": "docs/attestations/missing.json",
        "review_status": "current",
    }
    write(
        tmp_path / "docs" / "attestations" / "demo--compliance--20260811T010203Z-cccccccc.json",
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
    )
    assert check_plan_governance.main([str(tmp_path), "--check-attestations"]) == 0
    output = capsys.readouterr().out
    assert "supersedes 目标不存在" in output
    assert "status=needs_review" in output
    assert check_plan_governance.main([str(tmp_path), "--check-attestations", "--strict-readiness"]) == 1
    assert "supersedes 目标不存在" in capsys.readouterr().out


def test_attestation_structure_and_supersedes_boundaries_are_reported(tmp_path):
    plan = tmp_path / "docs" / "plans" / "demo.md"
    plan_map_path = tmp_path / "docs" / "PLAN_MAP.md"
    write(plan_map_path, plan_map("| [demo](plans/demo.md) | 已完成 | 阶段 1 | - | - |"))
    write(plan, plan_text(with_coverage=True))
    plan_sha = hashlib.sha256(plan.read_bytes()).hexdigest()
    plan_map_sha = hashlib.sha256(plan_map_path.read_bytes()).hexdigest()
    base = {
        "plan": "demo",
        "phase": "阶段 1",
        "status": "已完成",
        "plan_path": "docs/plans/demo.md",
        "plan_map_path": "docs/PLAN_MAP.md",
        "plan_sha256": plan_sha,
        "plan_map_sha256": plan_map_sha,
        "created_at": "2026-08-11T01:02:03Z",
        "created_by": "test",
        "reason": "测试",
        "purpose": "release_gate",
        "review_status": "current",
        "supersedes": "",
    }

    def snapshot(relative_path, **updates):
        payload = {**base, **updates}
        write(tmp_path / relative_path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")

    snapshot(
        "docs/attestations/invalid-purpose.json",
        purpose="unsupported",
        snapshot_id="20260811T010203Z-11111111",
    )
    snapshot(
        "docs/attestations/missing-snapshot.json",
        snapshot_id=None,
    )
    missing_snapshot = tmp_path / "docs/attestations/missing-snapshot.json"
    missing_data = json.loads(missing_snapshot.read_text(encoding="utf-8"))
    missing_data.pop("snapshot_id", None)
    missing_snapshot.write_text(json.dumps(missing_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    snapshot(
        "docs/attestations/invalid-review.json",
        snapshot_id="20260811T010204Z-22222222",
        review_status="unsupported",
    )
    snapshot(
        "docs/attestations/non-string-supersedes.json",
        snapshot_id="20260811T010205Z-33333333",
        supersedes=["docs/attestations/other.json"],
    )
    snapshot(
        "docs/attestations/absolute-supersedes.json",
        snapshot_id="20260811T010206Z-44444444",
        supersedes="/tmp/other.json",
    )
    snapshot(
        "docs/attestations/invalid-plan-path.json",
        snapshot_id="20260811T010207Z-55555555",
        plan_path="/tmp/demo.md",
    )
    snapshot(
        "docs/attestations/invalid-map-path.json",
        snapshot_id="20260811T010208Z-66666666",
        plan_map_path="/tmp/PLAN_MAP.md",
    )
    snapshot(
        "docs/attestations/missing-plan.json",
        snapshot_id="20260811T010209Z-77777777",
        plan_path="docs/plans/missing.md",
    )
    snapshot(
        "docs/attestations/missing-map.json",
        snapshot_id="20260811T010210Z-88888888",
        plan_map_path="docs/missing-PLAN_MAP.md",
    )

    mismatch = "docs/attestations/mismatch-target.json"
    snapshot(
        mismatch,
        snapshot_id="20260811T010211Z-99999999",
        supersedes="docs/attestations/other-purpose.json",
    )
    snapshot(
        "docs/attestations/other-purpose.json",
        purpose="compliance",
        snapshot_id="20260811T010212Z-aaaaaaaa",
    )
    self_path = "docs/attestations/self-target.json"
    snapshot(
        self_path,
        snapshot_id="20260811T010213Z-bbbbbbbb",
        supersedes=self_path,
    )

    warnings = []
    errors = []
    reports = []
    check_plan_governance.warn_attestation_drift(
        warnings,
        tmp_path,
        {"demo": {"path": plan, "phase": "阶段 1", "status": "已完成"}},
        errors=errors,
        reports=reports,
    )
    output = "\n".join(warnings)
    assert "purpose 非法" in output
    assert "snapshot_id 格式非法" in output
    assert "review_status 非法" in output
    assert "supersedes 必须是相对路径字符串" in output
    assert "supersedes 必须是仓库内相对路径" in output
    assert "快照引用的计划路径非法" in output
    assert "快照引用的 PLAN_MAP 路径非法" in output
    assert "计划文件不存在" in output
    assert "PLAN_MAP.md 不存在" in output
    assert "supersedes 目标必须与当前快照属于同一计划和 purpose" in output
    assert "supersedes 不能指向自身" in output
    assert errors == []
    assert reports


def test_recent_evidence_remains_separate_from_independent_review():
    text = """# 计划：demo

## 当前阶段

### 最近实施/验证记录

| 日期 | 类型 | 动作/结果 | 证据 | 状态 | 记录者 |
|---|---|---|---|---|---|
| 2026-08-11 | 验证 | 运行回归 | `tests/test_demo.py` | 通过 | Codex |

## 最新独立准入复核

| 字段 | 内容 |
|---|---|
| 日期 | 2026-08-10 |
| 阶段 | 阶段 1 |
| 结论 | 通过 |
| 证据 | `docs/review.md` |
| 复核者 | Reviewer |
"""
    rows = check_plan_governance.recent_evidence(text)
    assert rows == [["2026-08-11", "验证", "运行回归", "`tests/test_demo.py`", "通过", "Codex"]]
    assert "最新独立准入复核" not in "|".join(rows[0])


def test_check_attestations_is_read_only(tmp_path, capsys):
    write(
        tmp_path / "docs" / "PLAN_MAP.md",
        plan_map("| [demo](plans/demo.md) | 已完成 | 阶段 1 | - | - |"),
    )
    write(tmp_path / "docs" / "plans" / "demo.md", plan_text(with_coverage=True))
    before = {
        path.relative_to(tmp_path).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in [tmp_path / "docs" / "PLAN_MAP.md", tmp_path / "docs" / "plans" / "demo.md"]
    }
    assert check_plan_governance.main([str(tmp_path), "--check-attestations"]) == 0
    capsys.readouterr()
    after = {
        path.relative_to(tmp_path).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in [tmp_path / "docs" / "PLAN_MAP.md", tmp_path / "docs" / "plans" / "demo.md"]
    }
    assert after == before


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
    write(tmp_path / "docs" / "plans" / "ready.md", readiness_plan_text())
    write(tmp_path / "docs" / "plans" / "review.md", workset_plan_text("设计中"))
    write(tmp_path / "docs" / "plans" / "step0.md", workset_plan_text("设计中", missing_summary=True))
    write(tmp_path / "docs" / "plans" / "blocked.md", workset_plan_text("设计中", blocker=True))
    write(tmp_path / "docs" / "plans" / "running.md",
          readiness_plan_text(status="实施中").replace("## 当前阶段", "## 当前阶段\n\n下一动作：验证"))
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


def assert_gate_result(root, capsys, plan, *, index=None, check_codes=(0, 1),
                       workset_codes=(0, 1), readiness="unknown", action="unknown"):
    write(root / "docs/PLAN_MAP.md", index or plan_map(
        "| [demo](plans/demo.md) | 待实施 | 阶段 1 | - | - |"))
    write(root / "docs/plans/demo.md", plan)
    before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
    for strict, check_code, workset_code in zip([False, True], check_codes, workset_codes):
        flags = ["--strict-readiness"] if strict else []
        assert check_plan_governance.main([str(root), *flags]) == check_code
        capsys.readouterr()
        payload, code = check_plan_governance.workset_payload(root, strict=strict)
        assert code == workset_code
        assert set(payload) == {"schema_version", "source", "plans", "warnings"}
        assert payload["schema_version"] == 1
        item = payload["plans"][0]
        assert set(item) == {"plan", "status", "phase", "readiness", "blockers",
                             "next_action", "parallel", "recent_evidence"}
        assert (item["readiness"], item["next_action"]["kind"]) == (readiness, action)
    assert {p: p.read_bytes() for p in root.rglob("*") if p.is_file()} == before
    return payload


@pytest.mark.parametrize("field", ["准入状态", "Step 0", "样本矩阵", "验证方式",
    "失败/回滚边界", "当前阻塞项", "最新独立准入复核", "日期", "阶段", "结论", "证据", "复核者"])
def test_gate_rejects_each_empty_required_value(tmp_path, capsys, field):
    import re
    plan = re.sub(r"(?m)^\| " + re.escape(field) + r" \|.*\|$",
                  "| " + field + " | |", readiness_plan_text())
    payload = assert_gate_result(tmp_path, capsys, plan)
    assert any(field in warning for warning in payload["warnings"])


def blocker_map(scope="demo", impact="是", state="待处理"):
    return plan_map("| [demo](plans/demo.md) | 待实施 | 阶段 1 | - | - |") + f"""
## 当前阻塞项

| 问题 | 推荐方案 | 影响范围 | 是否阻塞当前阶段 | 状态 |
|---|---|---|---|---|
| 外部授权待确认 | 先确认 | {scope} | {impact} | {state} |
"""


@pytest.mark.parametrize("source", ["summary", "map", "both", "open", "unknown"])
def test_gate_preserves_blockers_across_sources(tmp_path, capsys, source):
    plan = readiness_plan_text()
    index = None
    if source in {"summary", "both"}:
        plan = plan.replace("| 当前阻塞项 | 无 |", "| 当前阻塞项 | 外部授权待确认 |")
    if source in {"map", "both"}:
        index = blocker_map()
    if source in {"open", "unknown"}:
        plan = readiness_plan_text(unresolved_blocker=True)
        if source == "unknown":
            plan = plan.replace("| 是 | 未解决 |", "| 是 | Pending |")
    payload = assert_gate_result(tmp_path, capsys, plan, index=index,
        check_codes=(1, 1) if source == "open" else (0, 1),
        readiness="blocked", action="resolve_blocker")
    assert payload["plans"][0]["blockers"]
    assert payload["warnings"]


@pytest.mark.parametrize("state", ["已决定", "已收敛", "已完成", "已解决", "已关闭", "无", "RESOLVED", "closed", "done"])
def test_resolved_blockers_do_not_block(tmp_path, capsys, state):
    plan = readiness_plan_text().replace("| - | - | 否 | 已延后 |",
        f"| 已处理问题 | 已补齐 | Yes | {state} |")
    payload = assert_gate_result(tmp_path, capsys, plan, index=blocker_map(state=state),
        check_codes=(0, 0), workset_codes=(0, 0), readiness="ready", action="implement")
    assert payload["plans"][0]["blockers"] == []


@pytest.mark.parametrize("mutation", [
    lambda p: p.replace("| 结论 | 通过 |", "| 结论 | 未通过 |\n| 结论 | 通过 |"),
    lambda p: p.replace("| Step 0 |", "| Step 0 | 空 |\n| Step 0 |"),
    lambda p: p + "\n## 当前阶段\n",
    lambda p: p + "\n## 最新独立准入复核\n",
    lambda p: p.replace("### 最新独立准入复核", "### 阶段准入摘要\n\n### 最新独立准入复核"),
    lambda p: p.replace("| 阶段 1 | 阶段目标 |", "| 阶段 1 | 重复 | Step 0 | pytest | 待实施 |\n| 阶段 1 | 阶段目标 |"),
    lambda p: p.replace("| 阶段 | 阶段 1 |", "| 阶段 | 阶段 2 |"),
    lambda p: p.replace("| 阶段准入复核 | 阶段 1 | 通过 |", "| 阶段准入复核 | 阶段 1 | 未通过 |"),
])
def test_ambiguous_readiness_never_implements(tmp_path, capsys, mutation):
    payload = assert_gate_result(tmp_path, capsys, mutation(readiness_plan_text()))
    assert payload["warnings"]


@pytest.mark.parametrize("status", ["设计中", "待实施", "实施中"])
@pytest.mark.parametrize("conclusion", ["未通过", "不通过", "失败", "不满足标准", "拒绝"])
def test_failed_current_review_is_not_an_unreviewed_design(tmp_path, capsys, status, conclusion):
    plan = readiness_plan_text(status=status).replace("| 结论 | 通过 |", f"| 结论 | {conclusion} |")
    plan = plan.replace("| 阶段 1 | 通过 |", f"| 阶段 1 | {conclusion} |")
    payload = assert_gate_result(tmp_path, capsys, plan,
        index=plan_map(f"| [demo](plans/demo.md) | {status} | 阶段 1 | - | - |"),
        check_codes=(0, 0) if status == "设计中" else (0, 1),
        workset_codes=(0, 0) if status == "设计中" else (0, 1),
        readiness="blocked", action="resolve_blocker")
    assert conclusion in " ".join(payload["plans"][0]["blockers"])


@pytest.mark.parametrize("scope,impact", [("demo", "未知"), ("demo", ""), ("missing", "是"), ("demo, missing", "是")])
def test_uncertain_blocker_index_cannot_allow_implementation(tmp_path, capsys, scope, impact):
    payload = assert_gate_result(tmp_path, capsys, readiness_plan_text(),
        index=blocker_map(scope=scope, impact=impact))
    assert payload["warnings"]


@pytest.mark.parametrize("fence", ["```", "~~~~"])
def test_code_examples_do_not_become_governance_facts(tmp_path, capsys, fence):
    fake = f"{fence}markdown\n## 当前阶段\n### 阶段准入摘要\n| Step 0 | |\n## 最新独立准入复核\n| 结论 | 未通过 |\n{fence}\n"
    plan = fake + readiness_plan_text()
    plan = plan.replace("| 结论 | 通过 |", "| 结论 | 通过 |\n" + fake)
    payload = assert_gate_result(tmp_path, capsys, plan, check_codes=(0, 0),
        workset_codes=(0, 0), readiness="ready", action="implement")
    assert not payload["warnings"]


@pytest.mark.parametrize("title,expected", [("阶段 1 最近验证记录", 1),
    ("阶段 1 最近实施/验证记录", 1), ("阶段 2 最近验证记录", 0)])
def test_legacy_recent_record_alias_is_current_phase_only(tmp_path, capsys, title, expected):
    record = f"### {title}\n\n| 日期 | 结果 |\n|---|---|\n| 2026-09-06 | 真实结果 |\n\n"
    plan = readiness_plan_text().replace("### 最新独立准入复核", record + "### 最新独立准入复核")
    payload = assert_gate_result(tmp_path, capsys, plan, check_codes=(0, 0),
        workset_codes=(0, 0), readiness="ready", action="implement")
    assert len(payload["plans"][0]["recent_evidence"]) == expected
    assert bool(payload["warnings"]) == bool(expected)


def test_exploration_subheading_does_not_duplicate_top_level_problem_table(tmp_path, capsys):
    plan = readiness_plan_text().replace("## 阶段路线图",
        "## 需求探索\n\n### 未决问题\n\n参见下方正式未决表。\n\n## 阶段路线图")
    assert_gate_result(tmp_path, capsys, plan, check_codes=(0, 0), workset_codes=(0, 0),
        readiness="ready", action="implement")


@pytest.mark.parametrize("separator", [",", "，", "、", "/"])
def test_map_blocker_explicit_multiple_targets_and_links(tmp_path, capsys, separator):
    index = blocker_map(scope=f"[demo](plans/demo.md){separator}other")
    index = index.replace("## 当前阻塞项", "| [other](plans/other.md) | 设计中 | 阶段 1 | 2026-09-06 | - | - |\n\n## 当前阻塞项")
    write(tmp_path / "docs/plans/other.md", workset_plan_text())
    payload = assert_gate_result(tmp_path, capsys, readiness_plan_text(), index=index,
        readiness="blocked", action="resolve_blocker")
    assert all("外部授权待确认" in item["blockers"] for item in payload["plans"])


@pytest.mark.parametrize("duplicate_heading", [False, True])
def test_duplicate_index_is_strict_error_in_both_commands(tmp_path, capsys, duplicate_heading):
    row = "| [demo](plans/demo.md) | 待实施 | 阶段 1 | - | - |"
    index = plan_map(row) + plan_map(row) if duplicate_heading else plan_map(row + "\n" + row.replace("待实施", "设计中"))
    write(tmp_path / "docs/PLAN_MAP.md", index)
    write(tmp_path / "docs/plans/demo.md", readiness_plan_text())
    for strict in [False, True]:
        assert check_plan_governance.main([str(tmp_path), *(["--strict-readiness"] if strict else [])]) == int(strict)
        assert "重复计划" in capsys.readouterr().out
        payload, code = check_plan_governance.workset_payload(tmp_path, strict=strict)
        assert code == int(strict)
        assert payload["plans"] == []


def test_design_missing_materials_remain_legal(tmp_path, capsys):
    for label, text, action in [("legacy", plan_text(), "complete_step0"),
                               ("unreviewed", workset_plan_text(), "independent_review")]:
        assert_gate_result(tmp_path / label, capsys, text,
            index=plan_map("| [demo](plans/demo.md) | 设计中 | 阶段 1 | - | - |"),
            check_codes=(0, 0), workset_codes=(0, 0), readiness="design", action=action)


def test_duplicate_map_blocker_sections_cannot_hide_later_blocker(tmp_path, capsys):
    index = blocker_map(state="已解决") + "\n## 当前阻塞项\n" + blocker_map().split("## 当前阻塞项", 1)[1]
    assert_gate_result(tmp_path, capsys, readiness_plan_text(), index=index)


def test_blocker_text_with_dashes_is_not_a_table_separator(tmp_path, capsys):
    plan = readiness_plan_text(unresolved_blocker=True).replace("| 示例问题 |", "| 失败---待修复 |")
    payload = assert_gate_result(tmp_path, capsys, plan, check_codes=(1, 1),
        readiness="blocked", action="resolve_blocker")
    assert "失败---待修复" in payload["plans"][0]["blockers"]


def test_legacy_open_state_with_description_keeps_default_hard_error(tmp_path, capsys):
    plan = readiness_plan_text(unresolved_blocker=True).replace("| 是 | 未解决 |", "| 是 | 待处理：补证据 |")
    assert_gate_result(tmp_path, capsys, plan, check_codes=(1, 1),
        readiness="blocked", action="resolve_blocker")


@pytest.mark.parametrize("fence", ["```", "~~~~"])
@pytest.mark.parametrize("real_action", [False, True])
def test_next_action_ignores_fenced_prose_examples(tmp_path, capsys, fence, real_action):
    sample = f"下一动作格式示例：\n\n{fence}text\n下一动作：实施\n{fence}\n"
    if real_action:
        sample += "\n下一动作：验证\n"
    plan = readiness_plan_text(status="实施中").replace("## 当前阶段", "## 当前阶段\n\n" + sample)
    assert_gate_result(tmp_path, capsys, plan,
        index=plan_map("| [demo](plans/demo.md) | 实施中 | 阶段 1 | - | - |"),
        check_codes=(0, 0), workset_codes=(0, 0), readiness="in_progress",
        action="verify" if real_action else "unknown")
