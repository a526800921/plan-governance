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
    assert (tmp_path / ".git").exists()
    assert (tmp_path / "docs" / "PLAN_MAP.md").exists()
    plan = tmp_path / "docs" / "plans" / "api-migration.md"
    assert plan.exists()
    assert "分阶段迁移 API。" in plan.read_text(encoding="utf-8")
    assert "## 测试覆盖率" in plan.read_text(encoding="utf-8")
    assert "### 阶段准入摘要" in plan.read_text(encoding="utf-8")
    assert "## 需求探索" in plan.read_text(encoding="utf-8")
    assert "### 用户确认的探索结论" in plan.read_text(encoding="utf-8")
    assert "## 最新独立准入复核" in plan.read_text(encoding="utf-8")
    assert "## 独立复核记录" in plan.read_text(encoding="utf-8")
    docs = tmp_path / "docs"
    assert {path.relative_to(docs).as_posix() for path in docs.rglob("*")} == {
        "PLAN_MAP.md", "plans", "plans/api-migration.md",
    }
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
    assert "最后更新" in text
    assert "不复制字段级方案" in text
    assert "草案和历史文档规则" in text
    assert "不再作为规范事实源" in text
    assert "草案为准|以草案为事实源|详见草案" in text
    assert "rg` 搜索同名计划" in text
    assert "## 计划治理" in text
    assert "验收独立性" in text
    assert "不得仅依据计划状态、完成证据文字或文档格式判定完成" in text
    assert "plan-governance-cli check ." in text
    assert "plan-governance-cli check . --stale-days" in text
    assert "python3 scripts/check_plan_governance.py" not in text
    assert "--migrate-plan-map-last-updated" in text
    assert "阶段 N 完成只关闭阶段 N" in text
    assert "--strict-readiness" in text
    assert "机器识别的结构化章节标题固定为 `阶段路线图`" in text
    assert "追加式独立复核记录" in text
    assert "需求探索与 grilling" in text
    assert "grill-me" in text
    assert "用户确认结构化总结" in text
    assert "阶段内独立复核调度" in text
    assert "不为每个微小动作单独复核" in text
    assert "复核入口不可用" in text
    assert "高影响" in text
    assert init_plan_governance.CLAUDE_SECTION_BEGIN in text
    assert init_plan_governance.CLAUDE_SECTION_END in text


def test_main_can_create_agents_md(tmp_path):
    result = init_plan_governance.main(
        ["--root", str(tmp_path), "--plan", "demo", "--update-agents-md"]
    )

    agents_md = tmp_path / "AGENTS.md"
    text = agents_md.read_text(encoding="utf-8")
    assert result == 0
    assert "## 计划治理" in text
    assert "验收独立性" in text
    assert "不得仅依据计划状态、完成证据文字或文档格式判定完成" in text
    assert "plan-governance-cli check ." in text
    assert "plan-governance-cli check . --stale-days" in text
    assert "python3 scripts/check_plan_governance.py" not in text
    assert "--migrate-plan-map-last-updated" in text
    assert "阶段 N 完成只关闭阶段 N" in text
    assert "--strict-readiness" in text
    assert "机器识别的结构化章节标题固定为 `阶段路线图`" in text
    assert "需求探索与 grilling" in text
    assert "grill-me" in text
    assert "用户确认结构化总结" in text
    assert "阶段内独立复核调度" in text
    assert "不为每个微小动作单独复核" in text
    assert "复核入口不可用" in text
    assert "高影响" in text
    assert init_plan_governance.AGENTS_SECTION_BEGIN in text
    assert init_plan_governance.AGENTS_SECTION_END in text


def test_main_can_create_all_agent_rules(tmp_path):
    result = init_plan_governance.main(
        ["--root", str(tmp_path), "--plan", "demo", "--update-agent-rules"]
    )

    assert result == 0
    assert (tmp_path / "CLAUDE.md").exists()
    assert (tmp_path / "AGENTS.md").exists()
    assert "验收独立性" in (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert "验收独立性" in (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "需求探索与 grilling" in (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert "需求探索与 grilling" in (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "阶段内独立复核调度" in (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert "阶段内独立复核调度" in (tmp_path / "AGENTS.md").read_text(encoding="utf-8")


def test_update_claude_md_only_does_not_require_plan_or_touch_docs(tmp_path, capsys):
    result = init_plan_governance.main(
        ["--root", str(tmp_path), "--update-claude-md-only"]
    )

    assert result == 0
    assert (tmp_path / "CLAUDE.md").exists()
    assert not (tmp_path / ".git").exists()
    assert not (tmp_path / "docs").exists()
    assert "未修改 docs" in capsys.readouterr().out


def test_update_agents_md_only_does_not_require_plan_or_touch_docs(tmp_path, capsys):
    result = init_plan_governance.main(
        ["--root", str(tmp_path), "--update-agents-md-only"]
    )

    assert result == 0
    assert (tmp_path / "AGENTS.md").exists()
    assert not (tmp_path / ".git").exists()
    assert not (tmp_path / "docs").exists()
    assert "未修改 docs" in capsys.readouterr().out


def test_update_agent_rules_only_does_not_require_plan_or_touch_docs(tmp_path, capsys):
    result = init_plan_governance.main(
        ["--root", str(tmp_path), "--update-agent-rules-only"]
    )

    assert result == 0
    assert (tmp_path / "CLAUDE.md").exists()
    assert (tmp_path / "AGENTS.md").exists()
    assert not (tmp_path / ".git").exists()
    assert not (tmp_path / "docs").exists()
    assert "代理规则已更新" in capsys.readouterr().out


def test_init_git_skips_existing_git_dir(tmp_path, monkeypatch):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    def fail_run(*args, **kwargs):
        raise AssertionError("不应重复执行 git init")

    monkeypatch.setattr(init_plan_governance.subprocess, "run", fail_run)

    assert init_plan_governance.init_git(tmp_path) is None


def test_generated_plan_map_documents_draft_source_switch(tmp_path):
    result = init_plan_governance.main(["--root", str(tmp_path), "--plan", "demo"])

    plan_map = tmp_path / "docs" / "PLAN_MAP.md"
    text = plan_map.read_text(encoding="utf-8")
    assert result == 0
    assert "| 计划 | 状态 | 当前阶段 | 最后更新 | 依赖 | 证据 |" in text
    assert "不再作为规范事实源" in text
    assert "后续新规范默认进入" in text


@pytest.mark.parametrize("option", ["--upgrade-existing", "--update-agent-rules-only"])
def test_upgrade_existing_updates_helpers_without_overwriting_docs(tmp_path, capsys, option):
    preserved_files = {
        "docs/PLAN_MAP.md": b"existing map\r\n  \t",
        "docs/plans/demo.md": b"existing plan\r\n\r\n",
        "docs/specs/capability.md": b"# Existing contract\r\n\r\nBehavior.  \t\r\n",
        "api/openapi.json": b'{"openapi":"3.1.0","info":{"title":"Existing","version":"1"}}\r\n',
        "docs/adr/0001-original.md": b"# Original decision\r\nKeep this choice.\r\n",
        "docs/migrations/existing.md": b"# Existing migration\r\nKeep the old window.\r\n",
        "docs/reviews/historical.md": b"# Historical review\r\nDo not rewrite.  \t\r\n",
    }
    for relative, content in preserved_files.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    docs = tmp_path / "docs"
    original_docs = {path.relative_to(docs).as_posix() for path in docs.rglob("*")}
    begin = b"<!-- plan-governance:start -->"
    end = b"<!-- plan-governance:end -->"
    prefix = b"# Project rules\r\nCustom prefix.  \t\r\n"
    suffix = b"\r\n\r\nCustom suffix.  \t\r\n"
    for filename in ("AGENTS.md", "CLAUDE.md"):
        (tmp_path / filename).write_bytes(prefix + begin + b"\r\nold rules\r\n" + end + suffix)
    checker = tmp_path / "scripts" / "check_plan_governance.py"
    checker.parent.mkdir(parents=True)
    checker.write_text("old checker", encoding="utf-8")

    result = init_plan_governance.main(["--root", str(tmp_path), option])

    assert result == 0
    for relative, content in preserved_files.items():
        assert (tmp_path / relative).read_bytes() == content, relative
    assert {path.relative_to(docs).as_posix() for path in docs.rglob("*")} == original_docs
    generated = init_plan_governance.agent_rules_body().encode("utf-8")
    for filename in ("AGENTS.md", "CLAUDE.md"):
        updated = (tmp_path / filename).read_bytes()
        assert updated.startswith(prefix + begin + b"\n")
        assert updated.endswith(end + suffix)
        assert updated.split(begin, 1)[1].split(end, 1)[0] == b"\n" + generated
    output = capsys.readouterr().out
    if option == "--upgrade-existing":
        assert "old checker" not in checker.read_text(encoding="utf-8")
        assert "已有项目升级完成" in output
        assert "plan-governance-cli check ." in output
    else:
        assert checker.read_bytes() == b"old checker"
        assert "代理规则已更新" in output
    assert "WARNING" not in output


def test_upgrade_existing_reports_missing_docs(tmp_path, capsys):
    result = init_plan_governance.main(["--root", str(tmp_path), "--upgrade-existing"])

    output = capsys.readouterr().out
    assert result == 0
    assert "WARNING: 缺少 docs/PLAN_MAP.md" in output
    assert "WARNING: 缺少 docs/plans/*.md" in output


def test_migrate_plan_map_last_updated_converts_legacy_table(tmp_path, capsys):
    plan_map = tmp_path / "docs" / "PLAN_MAP.md"
    plan_map.parent.mkdir(parents=True)
    plan_map.write_text(
        """# PLAN_MAP

## 计划索引

| 计划 | 状态 | 当前阶段 | 依赖 | 证据 |
|---|---|---|---|---|
| [demo](plans/demo.md) | 待实施 | 阶段 1 | - | - |
""",
        encoding="utf-8",
    )

    result = init_plan_governance.main(
        [
            "--root",
            str(tmp_path),
            "--migrate-plan-map-last-updated",
            "--last-updated-date",
            "2026-07-05",
        ]
    )

    text = plan_map.read_text(encoding="utf-8")
    assert result == 0
    assert "| 计划 | 状态 | 当前阶段 | 最后更新 | 依赖 | 证据 |" in text
    assert "| [demo](plans/demo.md) | 待实施 | 阶段 1 | 2026-07-05 | - | - |" in text
    assert "已迁移" in capsys.readouterr().out


def test_migrate_plan_map_last_updated_is_idempotent(tmp_path, capsys):
    init_plan_governance.main(["--root", str(tmp_path), "--plan", "demo"])
    plan_map = tmp_path / "docs" / "PLAN_MAP.md"
    before = plan_map.read_text(encoding="utf-8")

    result = init_plan_governance.main(
        ["--root", str(tmp_path), "--migrate-plan-map-last-updated"]
    )

    assert result == 0
    assert plan_map.read_text(encoding="utf-8") == before
    assert "无需迁移" in capsys.readouterr().out


def test_migrate_plan_map_last_updated_requires_plan_map(tmp_path):
    with pytest.raises(FileNotFoundError, match="缺少 docs/PLAN_MAP.md"):
        init_plan_governance.main(
            ["--root", str(tmp_path), "--migrate-plan-map-last-updated"]
        )


def test_migrate_plan_map_last_updated_rejects_invalid_date(tmp_path):
    plan_map = tmp_path / "docs" / "PLAN_MAP.md"
    plan_map.parent.mkdir(parents=True)
    plan_map.write_text("# PLAN_MAP\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid isoformat"):
        init_plan_governance.main(
            [
                "--root",
                str(tmp_path),
                "--migrate-plan-map-last-updated",
                "--last-updated-date",
                "2026/07/05",
            ]
        )


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


def test_update_agents_md_appends_to_existing_file(tmp_path):
    agents_md = tmp_path / "AGENTS.md"
    agents_md.write_text("# 项目规则\n\n已有内容。\n", encoding="utf-8")

    init_plan_governance.update_agents_md(tmp_path)

    text = agents_md.read_text(encoding="utf-8")
    assert text.startswith("# 项目规则\n\n已有内容。")
    assert text.count("## 计划治理") == 1
    assert "验收独立性" in text


def test_update_agents_md_replaces_existing_managed_section(tmp_path):
    agents_md = tmp_path / "AGENTS.md"
    agents_md.write_text(
        "# 项目规则\n\n"
        f"{init_plan_governance.AGENTS_SECTION_BEGIN}\n"
        "旧规则\n"
        f"{init_plan_governance.AGENTS_SECTION_END}\n\n"
        "后续内容。\n",
        encoding="utf-8",
    )

    init_plan_governance.update_agents_md(tmp_path)

    text = agents_md.read_text(encoding="utf-8")
    assert "旧规则" not in text
    assert "后续内容。" in text
    assert text.count(init_plan_governance.AGENTS_SECTION_BEGIN) == 1
    assert text.count("## 计划治理") == 1


@pytest.mark.parametrize(
    ("filename", "option"),
    [
        ("AGENTS.md", "--update-agents-md-only"),
        ("CLAUDE.md", "--update-claude-md-only"),
    ],
)
@pytest.mark.parametrize("existing_section", [False, True], ids=["append-trailing", "replace-crlf"])
def test_update_rules_preserves_unmanaged_bytes_and_is_idempotent(tmp_path, filename, option, existing_section):
    target = tmp_path / filename
    begin = b"<!-- plan-governance:start -->"
    end = b"<!-- plan-governance:end -->"
    if existing_section:
        prefix = "# 项目规则\r\n\r\n自定义前文。  \t\r\n".encode("utf-8")
        suffix = "\r\n\r\n自定义后文。  \t\r\n\r\n".encode("utf-8")
        original = prefix + begin + b"\r\nold managed rules\r\n" + end + suffix
    else:
        prefix = "# 项目规则\n\n保留末尾空白。  \t\n\n  \t".encode("utf-8")
        suffix = b""
        original = prefix
    target.write_bytes(original)

    assert init_plan_governance.main(["--root", str(tmp_path), option]) == 0

    updated = target.read_bytes()
    assert updated.startswith(prefix)
    assert updated.endswith(suffix)
    assert updated.count(begin) == 1
    assert updated.count(end) == 1
    assert b"old managed rules" not in updated
    assert not (tmp_path / "docs").exists()
    assert init_plan_governance.main(["--root", str(tmp_path), option]) == 0
    assert target.read_bytes() == updated


def test_copy_checker_refuses_existing_target_without_force(tmp_path):
    checker = tmp_path / "scripts" / "check_plan_governance.py"
    checker.parent.mkdir(parents=True)
    checker.write_text("existing", encoding="utf-8")

    with pytest.raises(FileExistsError, match="已存在"):
        init_plan_governance.copy_checker(tmp_path, force=False)


def test_copy_checker_allows_source_repo_itself(tmp_path, monkeypatch):
    source = tmp_path / "scripts" / "check_plan_governance.py"
    source.parent.mkdir()
    source.write_bytes(b"source checker")
    source.chmod(0o644)
    monkeypatch.setattr(init_plan_governance, "__file__", str(source.with_name("init_plan_governance.py")))
    target = init_plan_governance.copy_checker(tmp_path, force=True)

    assert target == source
    assert target.read_bytes() == b"source checker"
    assert target.stat().st_mode & 0o111
