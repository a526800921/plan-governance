import importlib.util
from pathlib import Path

import pytest


def load_module(name):
    path = Path(__file__).resolve().parents[1] / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


init_plan_governance = load_module("init_plan_governance")


def test_slugify_keeps_chinese_and_normalizes_symbols():
    assert init_plan_governance.slugify(" API 兼容性 迁移! ") == "api-兼容性-迁移"


def test_slugify_rejects_empty_names():
    with pytest.raises(ValueError, match="计划名称不能为空"):
        init_plan_governance.slugify("!!!")


def test_main_creates_plan_files(tmp_path, capsys):
    result = init_plan_governance.main(
        [
            "--root",
            str(tmp_path),
            "--plan",
            "api migration",
            "--title",
            "API 迁移",
            "--goal",
            "分阶段迁移 API。",
            "--status",
            "待实施",
            "--phase",
            "阶段 1",
        ]
    )

    assert result == 0
    assert (tmp_path / "docs" / "PLAN_MAP.md").exists()
    plan = tmp_path / "docs" / "plans" / "api-migration.md"
    assert plan.exists()
    assert "分阶段迁移 API。" in plan.read_text(encoding="utf-8")
    assert "## 测试覆盖率" in plan.read_text(encoding="utf-8")
    assert "初始化完成" in capsys.readouterr().out


def test_main_refuses_to_overwrite_without_force(tmp_path):
    init_plan_governance.main(["--root", str(tmp_path), "--plan", "demo"])

    with pytest.raises(FileExistsError, match="已存在"):
        init_plan_governance.main(["--root", str(tmp_path), "--plan", "demo"])


def test_main_overwrites_with_force(tmp_path):
    init_plan_governance.main(["--root", str(tmp_path), "--plan", "demo"])
    result = init_plan_governance.main(
        ["--root", str(tmp_path), "--plan", "demo", "--title", "新标题", "--force"]
    )

    assert result == 0
    plan_map = tmp_path / "docs" / "PLAN_MAP.md"
    assert "新标题" in plan_map.read_text(encoding="utf-8")


def test_main_can_copy_checker(tmp_path):
    result = init_plan_governance.main(
        ["--root", str(tmp_path), "--plan", "demo", "--copy-checker"]
    )

    checker = tmp_path / "scripts" / "check_plan_governance.py"
    assert result == 0
    assert checker.exists()
    assert checker.stat().st_mode & 0o111


def test_main_can_create_claude_md(tmp_path):
    result = init_plan_governance.main(
        ["--root", str(tmp_path), "--plan", "demo", "--update-claude-md"]
    )

    claude_md = tmp_path / "CLAUDE.md"
    text = claude_md.read_text(encoding="utf-8")
    assert result == 0
    assert "## 计划治理" in text
    assert "docs/PLAN_MAP.md" in text
    assert "事实源规则" in text
    assert "不复制字段级方案" in text
    assert "草案和历史文档规则" in text
    assert "不再作为规范事实源" in text
    assert "草案为准|以草案为事实源|详见草案" in text
    assert "rg` 搜索同名计划" in text
    assert "python3 scripts/check_plan_governance.py ." in text
    assert init_plan_governance.CLAUDE_SECTION_BEGIN in text
    assert init_plan_governance.CLAUDE_SECTION_END in text


def test_update_claude_md_only_does_not_require_plan_or_touch_docs(tmp_path, capsys):
    result = init_plan_governance.main(
        ["--root", str(tmp_path), "--update-claude-md-only"]
    )

    assert result == 0
    assert (tmp_path / "CLAUDE.md").exists()
    assert not (tmp_path / "docs").exists()
    assert "未修改 docs" in capsys.readouterr().out


def test_generated_plan_map_documents_draft_source_switch(tmp_path):
    result = init_plan_governance.main(["--root", str(tmp_path), "--plan", "demo"])

    plan_map = tmp_path / "docs" / "PLAN_MAP.md"
    text = plan_map.read_text(encoding="utf-8")
    assert result == 0
    assert "不再作为规范事实源" in text
    assert "后续新规范默认进入" in text


def test_upgrade_existing_updates_helpers_without_overwriting_docs(tmp_path, capsys):
    plan_map = tmp_path / "docs" / "PLAN_MAP.md"
    plan = tmp_path / "docs" / "plans" / "demo.md"
    plan.parent.mkdir(parents=True)
    plan_map.write_text("existing map", encoding="utf-8")
    plan.write_text("existing plan", encoding="utf-8")
    checker = tmp_path / "scripts" / "check_plan_governance.py"
    checker.parent.mkdir(parents=True)
    checker.write_text("old checker", encoding="utf-8")

    result = init_plan_governance.main(["--root", str(tmp_path), "--upgrade-existing"])

    assert result == 0
    assert plan_map.read_text(encoding="utf-8") == "existing map"
    assert plan.read_text(encoding="utf-8") == "existing plan"
    assert "old checker" not in checker.read_text(encoding="utf-8")
    assert (tmp_path / "CLAUDE.md").exists()
    output = capsys.readouterr().out
    assert "已有项目升级完成" in output
    assert "WARNING" not in output


def test_upgrade_existing_reports_missing_docs(tmp_path, capsys):
    result = init_plan_governance.main(["--root", str(tmp_path), "--upgrade-existing"])

    output = capsys.readouterr().out
    assert result == 0
    assert "WARNING: 缺少 docs/PLAN_MAP.md" in output
    assert "WARNING: 缺少 docs/plans/*.md" in output


def test_normal_init_still_requires_plan(tmp_path):
    with pytest.raises(SystemExit):
        init_plan_governance.main(["--root", str(tmp_path)])


def test_update_claude_md_appends_to_existing_file(tmp_path):
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text("# 项目规则\n\n已有内容。\n", encoding="utf-8")

    init_plan_governance.update_claude_md(tmp_path)

    text = claude_md.read_text(encoding="utf-8")
    assert text.startswith("# 项目规则\n\n已有内容。")
    assert text.count("## 计划治理") == 1


def test_update_claude_md_replaces_existing_managed_section(tmp_path):
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text(
        "# 项目规则\n\n"
        f"{init_plan_governance.CLAUDE_SECTION_BEGIN}\n"
        "旧规则\n"
        f"{init_plan_governance.CLAUDE_SECTION_END}\n\n"
        "后续内容。\n",
        encoding="utf-8",
    )

    init_plan_governance.update_claude_md(tmp_path)

    text = claude_md.read_text(encoding="utf-8")
    assert "旧规则" not in text
    assert "后续内容。" in text
    assert text.count(init_plan_governance.CLAUDE_SECTION_BEGIN) == 1
    assert text.count("## 计划治理") == 1


def test_copy_checker_refuses_existing_target_without_force(tmp_path):
    checker = tmp_path / "scripts" / "check_plan_governance.py"
    checker.parent.mkdir(parents=True)
    checker.write_text("existing", encoding="utf-8")

    with pytest.raises(FileExistsError, match="已存在"):
        init_plan_governance.copy_checker(tmp_path, force=False)
