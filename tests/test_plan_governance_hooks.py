import importlib.util
from pathlib import Path


def load_module(name):
    path = Path(__file__).resolve().parents[1] / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


plan_governance_hook = load_module("plan_governance_hook")


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def snapshot_files(root):
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def setup_runtime_fixture(root):
    write(
        root / "docs" / "PLAN_MAP.md",
        """# PLAN_MAP

## 计划索引

| 计划 | 状态 | 当前阶段 | 最后更新 | 依赖 | 证据 |
|---|---|---|---|---|---|
| [active-runtime-plan](plans/active-runtime-plan.md) | 实施中 | 阶段 1 | 2026-07-06 | - | [Step 0 证据](plans/active-runtime-plan.md#step-0-证据) |
| [completed-plan](plans/completed-plan.md) | 已完成 | 阶段 1 | 2026-07-05 | - | [验证方式](plans/completed-plan.md#验证方式) |

## 当前阻塞项

| 问题 | 推荐方案 | 影响范围 | 是否阻塞当前阶段 | 状态 |
|---|---|---|---|---|
| - | - | - | 否 | 已延后 |
""",
    )
    write(
        root / "docs" / "plans" / "active-runtime-plan.md",
        """# 计划：active-runtime-plan

## 影响模块或文件

- `scripts/`
- `tests/`

## 公共契约变化

当前阶段不得修改全局 hook 配置。

## 当前阶段

### Step 0 证据

fixture 已记录。

### 验证方式

运行 hook runtime 测试。
""",
    )
    write(
        root / "docs" / "plans" / "completed-plan.md",
        """# 计划：completed-plan

## 影响模块或文件

- `scripts/`

## 当前阶段

### Step 0 证据

历史证据。

### 验证方式

已完成。
""",
    )
    write(
        root / "scripts" / "check_plan_governance.py",
        """#!/usr/bin/env python3
print("WARNING: fixture warning")
print("计划治理检查通过。")
raise SystemExit(0)
""",
    )


def run_hook(tmp_path, *args, capsys):
    before = snapshot_files(tmp_path)
    result = plan_governance_hook.main(["--root", str(tmp_path), *args])
    output = capsys.readouterr().out
    after = snapshot_files(tmp_path)
    assert after == before
    return result, output


def test_session_start_outputs_active_plan_summary_without_full_body(tmp_path, capsys):
    setup_runtime_fixture(tmp_path)

    result, output = run_hook(tmp_path, "--event", "session-start", capsys=capsys)

    assert result == 0
    assert "active-runtime-plan" in output
    assert "阶段 1" in output
    assert "2026-07-06" in output
    assert "completed-plan" not in output
    assert "当前阶段不得修改全局 hook 配置" not in output


def test_pre_write_matches_active_plan_by_directory_target(tmp_path, capsys):
    setup_runtime_fixture(tmp_path)

    result, output = run_hook(
        tmp_path,
        "--event",
        "pre-write",
        "--paths",
        "scripts/foo.py",
        capsys=capsys,
    )

    assert result == 0
    assert "active-runtime-plan" in output
    assert "当前阶段门禁" in output
    assert "Step 0" in output
    assert "completed-plan" not in output


def test_pre_write_reports_no_matching_active_plan(tmp_path, capsys):
    setup_runtime_fixture(tmp_path)

    result, output = run_hook(
        tmp_path,
        "--event",
        "pre-write",
        "--paths",
        "README.md",
        capsys=capsys,
    )

    assert result == 0
    assert "未匹配到相关活跃计划" in output
    assert "active-runtime-plan" not in output


def test_post_write_plan_map_reminds_to_sync_evidence(tmp_path, capsys):
    setup_runtime_fixture(tmp_path)

    result, output = run_hook(
        tmp_path,
        "--event",
        "post-write",
        "--paths",
        "docs/PLAN_MAP.md",
        capsys=capsys,
    )

    assert result == 0
    assert "同步状态" in output
    assert "证据" in output
    assert "反向引用" in output


def test_post_write_plan_doc_reminds_to_sync_plan_map_and_validation(tmp_path, capsys):
    setup_runtime_fixture(tmp_path)

    result, output = run_hook(
        tmp_path,
        "--event",
        "post-write",
        "--paths",
        "docs/plans/active-runtime-plan.md",
        capsys=capsys,
    )

    assert result == 0
    assert "PLAN_MAP.md" in output
    assert "验证证据" in output
    assert "测试覆盖率" in output


def test_stop_runs_governance_check_without_blocking_on_warning(tmp_path, capsys):
    setup_runtime_fixture(tmp_path)

    result, output = run_hook(tmp_path, "--event", "stop", capsys=capsys)

    assert result == 0
    assert "fixture warning" in output
    assert "计划治理检查通过" in output
    assert "非阻塞" in output
