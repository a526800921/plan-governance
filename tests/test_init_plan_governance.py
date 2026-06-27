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


def test_copy_checker_refuses_existing_target_without_force(tmp_path):
    checker = tmp_path / "scripts" / "check_plan_governance.py"
    checker.parent.mkdir(parents=True)
    checker.write_text("existing", encoding="utf-8")

    with pytest.raises(FileExistsError, match="已存在"):
        init_plan_governance.copy_checker(tmp_path, force=False)
