"""Stage 4 contracts exercised against real temporary repositories."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import copy
from datetime import datetime, timezone

import pytest


CHECKER = Path(__file__).resolve().parents[1] / "scripts/check_plan_governance.py"
spec = importlib.util.spec_from_file_location("binding_checker", CHECKER)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)

INDEX = ["计划", "状态", "当前阶段", "最后更新", "依赖", "证据"]
DEPENDENCIES = ["计划", "依赖", "原因"]
RELATIONS = ["来源计划", "来源阶段", "目标计划", "目标阶段", "关系类型", "解除条件", "证据"]
SHARED = ["来源计划", "来源阶段", "目标计划", "目标阶段", "约束类型", "共享目标", "串行顺序", "解除条件", "证据"]
BLOCKERS = ["问题", "推荐方案", "影响范围", "是否阻塞当前阶段", "状态"]


def write(root, path, content):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


def table(title, columns, rows):
    return "\n## " + title + "\n\n" + "\n".join(
        "| " + " | ".join(row) + " |"
        for row in [columns, ["---"] * len(columns), *rows]
    ) + "\n"


def plan_text(name):
    return f"""# 计划：{name}

## 阶段路线图

| 阶段 | 目标 | 进入条件 | 验证方向 | 状态 |
|---|---|---|---|---|
| 阶段 1 | fixture | 已有基线 | pytest | 已完成 |
| 阶段 2 | fixture next | 自身基线 | pytest | 设计中 |

## 影响模块或文件

- `src/{name}.py`

## Step 0 证据

已有基线。

## 验证方式

运行检查脚本。

## 测试覆盖率

pytest-cov 报告：98.8% 覆盖率。

## 未决问题

| 问题 | 推荐方案 | 是否阻塞当前阶段 | 状态 |
|---|---|---|---|
| - | - | 否 | 已解决 |
"""


def project(root, names=("demo", "other")):
    rows = [[f"[{name}](plans/{name}.md)", "已完成", "阶段 1", "2026-09-06", "-", f"{name} evidence"] for name in names]
    write(root, "docs/PLAN_MAP.md", "# PLAN_MAP\n" + table("计划索引", INDEX, rows))
    for name in names:
        write(root, f"docs/plans/{name}.md", plan_text(name))
        write(root, f"src/{name}.py", f"print('{name} baseline')\n")
    write(root, "docs/report.md", "Fixture review output: 1 passed.\n")
    return rows


def cli(root, *args):
    return subprocess.run([sys.executable, str(CHECKER), str(root), *args], text=True, capture_output=True,
                          env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, timeout=15)


def create_args(*files, purpose="release_gate", plan="demo", supersedes=None):
    args = ["--attest", plan, "--attest-purpose", purpose]
    for path in files or ("src/demo.py", "docs/report.md"):
        args.extend(["--attest-file", path])
    if supersedes is not None:
        args.extend(["--supersedes", supersedes])
    return args


def test_real_cli_bound_source_change_requires_review(tmp_path):
    project(tmp_path)
    created = cli(tmp_path, *create_args())
    assert created.returncode == 0, created.stdout + created.stderr
    write(tmp_path, "src/demo.py", "print('changed working tree')\n")
    checked = cli(tmp_path, "--check-attestations", "--strict-readiness")
    assert checked.returncode == 1, checked.stdout + checked.stderr
    assert "needs_review" in checked.stdout


def test_real_cli_unrelated_index_change_keeps_binding_current(tmp_path):
    project(tmp_path)
    created = cli(tmp_path, *create_args())
    assert created.returncode == 0, created.stdout + created.stderr
    path = tmp_path / "docs/PLAN_MAP.md"
    path.write_text(path.read_text().replace("other evidence", "other new evidence"), encoding="utf-8")
    checked = cli(tmp_path, "--check-attestations", "--strict-readiness")
    assert checked.returncode == 0, checked.stdout + checked.stderr
    assert "current" in checked.stdout
    assert "needs_review" not in checked.stdout


def invoke(root, capsys, *args):
    try:
        result = checker.main([str(root), *args])
    except SystemExit as exc:
        result = exc.code
    output = capsys.readouterr()
    return result, output.out + output.err


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree(root):
    """Record bytes, directories and links without following symlink targets."""
    return {p.relative_to(root).as_posix(): ("link", os.readlink(p)) if p.is_symlink()
            else ("dir",) if p.is_dir() else ("file", p.read_bytes())
            for p in root.rglob("*") if ".git" not in p.relative_to(root).parts}


def make_snapshot(root, capsys, *files, **kwargs):
    before = set((root / "docs/attestations").glob("*.json"))
    status, output = invoke(root, capsys, *create_args(*files, **kwargs))
    assert status == 0, output
    added = set((root / "docs/attestations").glob("*.json")) - before
    assert len(added) == 1, output
    path = added.pop()
    return path, json.loads(path.read_text())


def assert_checked(root, capsys, expected="current", strict_code=0, default_code=0):
    before = tree(root)
    for flags, code in [((), default_code), (("--strict-readiness",), strict_code)]:
        actual, output = invoke(root, capsys, "--check-attestations", *flags)
        if code is not None:
            assert actual == code, output
        assert f"status={expected}" in output, output
    assert tree(root) == before, "checking must not rewrite snapshots or source files"


def update_snapshot(path, mutate):
    data = json.loads(path.read_text())
    mutate(data)
    path.write_text(json.dumps(data, ensure_ascii=False) + "\n", encoding="utf-8")


def graph_project(root):
    names = ("demo", "dep", "deep", "hard", "proof", "soft", "shared", "downstream", "other")
    rows = project(root, names)
    rows[0][4] = "dep"
    rows[1][4] = "deep"
    graph = {
        "index_rows": rows,
        "dependency_rows": [[name, "dep" if name == "demo" else "deep" if name == "dep" else "-", f"{name} reason"] for name in names],
        "relation_rows": [
            ["hard", "阶段 1", "demo", "阶段 1", "hard_gate", "hard admitted", "hard evidence"],
            ["proof", "阶段 1", "hard", "阶段 1", "evidence", "proof inspected", "proof evidence"],
            ["soft", "阶段 1", "demo", "阶段 1", "soft_context", "context only", "soft evidence"],
            ["demo", "阶段 1", "downstream", "阶段 1", "evidence", "outgoing only", "down evidence"],
        ],
        "shared_write_rows": [["shared", "阶段 1", "demo", "阶段 1", "shared_write_risk", "src/demo.py", "shared-before-demo", "serial only", "shared evidence"]],
        "blocker_rows": [["closed issue", "closed resolution", "demo, dep", "否", "已解决"],
                         ["unrelated issue", "unrelated resolution", "other", "否", "已解决"]],
    }
    render_graph(root, graph)
    return graph


def render_graph(root, graph):
    mapping = [("计划索引", INDEX, "index_rows"), ("依赖关系", DEPENDENCIES, "dependency_rows"),
               ("阶段关系", RELATIONS, "relation_rows"), ("机器可检查共享写入约束", SHARED, "shared_write_rows"),
               ("当前阻塞项", BLOCKERS, "blocker_rows")]
    write(root, "docs/PLAN_MAP.md", "# PLAN_MAP\n" + "".join(table(title, columns, graph[key]) for title, columns, key in mapping))


def test_binding_records_complete_sorted_projection_and_actual_bytes(tmp_path, capsys):
    graph = graph_project(tmp_path)
    path, data = make_snapshot(tmp_path, capsys, "src/demo.py", "docs/report.md")
    binding = data["binding"]
    assert set(binding) == {"version", "files", "related_plans", "plan_map_projection", "plan_map_projection_sha256", "revision"}
    assert binding["version"] == 1
    assert binding["files"] == [{"path": name, "sha256": digest(tmp_path / name)} for name in ["docs/report.md", "src/demo.py"]]
    members = ["deep", "demo", "dep", "hard", "proof"]
    assert binding["related_plans"] == [{"plan": name, "path": f"docs/plans/{name}.md", "sha256": digest(tmp_path / f"docs/plans/{name}.md")} for name in members]
    expected = {"version": 1, "members": members,
                "index_rows": sorted(graph["index_rows"][:5]),
                "dependency_rows": sorted(graph["dependency_rows"][:5]),
                "relation_rows": sorted(graph["relation_rows"]),
                "shared_write_rows": graph["shared_write_rows"],
                "blocker_rows": graph["blocker_rows"][:1]}
    assert binding["plan_map_projection"] == expected
    canonical = json.dumps(expected, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    assert binding["plan_map_projection_sha256"] == hashlib.sha256(canonical).hexdigest()
    assert binding["revision"] == {"source": "working_tree", "head": None}
    assert data["plan_map_sha256"] == digest(tmp_path / "docs/PLAN_MAP.md")
    assert_checked(tmp_path, capsys)


@pytest.mark.parametrize("purpose", [None, "release_gate"])
def test_unbound_snapshot_preserves_exact_fields_and_strict_legacy_drift(tmp_path, capsys, purpose):
    project(tmp_path)
    args = ["--attest", "demo"] + (["--attest-purpose", purpose] if purpose else [])
    code, output = invoke(tmp_path, capsys, *args)
    assert code == 0, output
    path = next((tmp_path / "docs/attestations").glob("*.json"))
    data = json.loads(path.read_text())
    expected = {"plan", "phase", "status", "plan_path", "plan_map_path", "plan_sha256", "plan_map_sha256", "created_at", "created_by", "reason"}
    if purpose:
        expected |= {"purpose", "snapshot_id", "supersedes", "review_status"}
    assert set(data) == expected
    write(tmp_path, "src/demo.py", "unbound source change\n")
    assert_checked(tmp_path, capsys)
    with (tmp_path / "docs/PLAN_MAP.md").open("a") as stream:
        stream.write("\n<!-- unrelated old whole-map drift -->\n")
    assert_checked(tmp_path, capsys, "needs_review", 0)


@pytest.mark.parametrize("mutation", ["change", "delete", "directory", "symlink", "parent_symlink", "plan", "upstream_plan"])
def test_bound_content_changes_keep_review_record(tmp_path, capsys, mutation):
    graph_project(tmp_path)
    make_snapshot(tmp_path, capsys)
    target = tmp_path / "src/demo.py"
    outside = tmp_path.parent / (tmp_path.name + "-external")
    outside.mkdir()
    sentinel = write(outside, "demo.py", "external must not be used\n")
    if mutation == "change":
        target.write_text("changed\n")
    elif mutation == "delete":
        target.unlink()
    elif mutation == "directory":
        target.unlink()
        target.mkdir()
    elif mutation == "symlink":
        target.unlink()
        target.symlink_to(sentinel)
    elif mutation == "parent_symlink":
        (tmp_path / "src").rename(tmp_path / "saved-src")
        (tmp_path / "src").symlink_to(outside, target_is_directory=True)
    else:
        plan = "demo" if mutation == "plan" else "proof"
        with (tmp_path / f"docs/plans/{plan}.md").open("a") as stream:
            stream.write("\nUpdated review evidence.\n")
    assert_checked(tmp_path, capsys, "needs_review", 1)
    assert sentinel.read_text() == "external must not be used\n"


@pytest.mark.parametrize("key,count", [("index_rows", 6), ("dependency_rows", 3), ("relation_rows", 7), ("shared_write_rows", 9), ("blocker_rows", 5)])
def test_every_projection_column_participates_in_drift(tmp_path, capsys, key, count):
    graph = graph_project(tmp_path)
    make_snapshot(tmp_path, capsys)
    for column in range(count):
        altered = copy.deepcopy(graph)
        # A changed identity/enum can invalidate the projection; it must still
        # retain the snapshot's needs_review row instead of silently dropping it.
        altered[key][0][column] += " changed"
        render_graph(tmp_path, altered)
        assert_checked(tmp_path, capsys, "needs_review", 1, None)
    render_graph(tmp_path, graph)
    assert_checked(tmp_path, capsys)


@pytest.mark.parametrize("change", ["add_dependency", "remove_dependency", "add_evidence", "remove_evidence", "add_blocker", "remove_blocker"])
def test_recomputes_members_and_related_rows_from_current_graph(tmp_path, capsys, change):
    graph = graph_project(tmp_path)
    make_snapshot(tmp_path, capsys)
    if change == "add_dependency":
        graph["index_rows"][0][4] = "dep, other"
        graph["dependency_rows"][0][1] = "dep, other"
    elif change == "remove_dependency":
        graph["index_rows"][0][4] = "-"
        graph["dependency_rows"][0][1] = "-"
    elif change == "add_evidence":
        graph["relation_rows"].append(["other", "阶段 1", "proof", "阶段 1", "evidence", "new upstream", "new proof"])
    elif change == "remove_evidence":
        graph["relation_rows"].pop(1)
    elif change == "add_blocker":
        graph["blocker_rows"].append(["another closed issue", "new resolution", "demo", "否", "已解决"])
    else:
        graph["blocker_rows"].pop(0)
    render_graph(tmp_path, graph)
    assert_checked(tmp_path, capsys, "needs_review", 1)


def test_unrelated_rows_order_comments_and_soft_shared_peer_content_do_not_drift(tmp_path, capsys):
    graph = graph_project(tmp_path)
    make_snapshot(tmp_path, capsys)
    for name in ["soft", "shared", "downstream", "other"]:
        row = next(row for row in graph["index_rows"] if row[0].startswith(f"[{name}]"))
        row[3], row[5] = "2026-09-07", "new unrelated evidence"
        write(tmp_path, f"docs/plans/{name}.md", plan_text(name) + "\nUnrelated plan content.\n")
    for key in graph:
        graph[key].reverse()
    render_graph(tmp_path, graph)
    with (tmp_path / "docs/PLAN_MAP.md").open("a") as stream:
        stream.write("\n<!-- irrelevant comment -->\n" + table("并行与共享写入约束", ["范围", "允许并行", "串行边界", "依据"], [["demo", "human notes", "human ordering", "human review"]]))
    write(tmp_path, "src/unlisted.py", "new file outside declared binding\n")
    assert_checked(tmp_path, capsys)


@pytest.mark.parametrize("kind", ["duplicate_index", "duplicate_section", "duplicate_relation", "unknown_dependency", "unknown_relation", "dependency_mismatch", "duplicate_dependency", "unattributable_blocker", "bad_header", "extra_column"])
def test_ambiguous_graph_rejects_creation_without_any_snapshot_write(tmp_path, capsys, kind):
    graph = graph_project(tmp_path)
    if kind == "duplicate_index":
        graph["index_rows"].append(graph["index_rows"][0][:])
    elif kind == "duplicate_relation":
        graph["relation_rows"].append(graph["relation_rows"][0][:])
    elif kind == "unknown_dependency":
        graph["index_rows"][0][4] = "missing"
        graph["dependency_rows"][0][1] = "missing"
    elif kind == "unknown_relation":
        graph["relation_rows"][0][0] = "missing"
    elif kind == "dependency_mismatch":
        graph["dependency_rows"][0][1] = "-"
    elif kind == "duplicate_dependency":
        graph["dependency_rows"].append(graph["dependency_rows"][0][:])
    elif kind == "unattributable_blocker":
        graph["blocker_rows"].append(["real problem", "needs decision", "unknown scope", "否", "已解决"])
    elif kind == "extra_column":
        graph["index_rows"][0].append("extra")
    render_graph(tmp_path, graph)
    path = tmp_path / "docs/PLAN_MAP.md"
    if kind == "duplicate_section":
        path.write_text(path.read_text() + table("阶段关系", RELATIONS, []))
    elif kind == "bad_header":
        path.write_text(path.read_text().replace("来源阶段", "unknown heading"))
    before = tree(tmp_path)
    code, output = invoke(tmp_path, capsys, *create_args())
    assert code == 1, output
    assert tree(tmp_path) == before


def test_empty_optional_sections_and_nonblocking_template_placeholder_are_allowed(tmp_path, capsys):
    project(tmp_path)
    with (tmp_path / "docs/PLAN_MAP.md").open("a") as stream:
        stream.write(table("阶段关系", RELATIONS, []) + table("机器可检查共享写入约束", SHARED, []) + table("当前阻塞项", BLOCKERS, [["-", "-", "-", "否", "已解决"]]))
    _, data = make_snapshot(tmp_path, capsys)
    projection = data["binding"]["plan_map_projection"]
    assert projection["dependency_rows"] == []
    assert projection["blocker_rows"] == []
    assert_checked(tmp_path, capsys)


@pytest.mark.parametrize("paths", [[""], ["src/demo.py", "./src/demo.py"], ["src"], ["src/*.py"], ["/tmp/external"], ["C:\\outside\\file.py"], ["../outside.py"], ["src/../../outside.py"]])
def test_invalid_explicit_paths_do_not_create_directories(tmp_path, capsys, paths):
    project(tmp_path)
    before = tree(tmp_path)
    code, output = invoke(tmp_path, capsys, *create_args(*paths))
    assert code == 1, output
    assert tree(tmp_path) == before


@pytest.mark.parametrize("target", ["file", "file_parent", "plan", "plan_parent", "map", "snapshots"])
def test_symlinks_in_all_automatic_and_explicit_paths_are_rejected(tmp_path, capsys, monkeypatch, target):
    project(tmp_path)
    outside = tmp_path.parent / (tmp_path.name + "-outside")
    outside.mkdir()
    if target in {"file", "plan", "map"}:
        relative = {"file": "src/demo.py", "plan": "docs/plans/demo.md", "map": "docs/PLAN_MAP.md"}[target]
        path = tmp_path / relative
        copy_path = write(outside, "outside.txt", path.read_text())
        path.unlink()
        path.symlink_to(copy_path)
    elif target == "snapshots":
        (tmp_path / "docs/attestations").symlink_to(outside, target_is_directory=True)
    else:
        path = tmp_path / ("src" if target == "file_parent" else "docs/plans")
        saved = tmp_path / "saved-folder"
        path.rename(saved)
        path.symlink_to(saved, target_is_directory=True)
    before, external_before = tree(tmp_path), tree(outside)
    original_open = Path.open
    outside_reads = []

    def recording_open(path, mode="r", *args, **kwargs):
        if mode in {"r", "rb"} and path.resolve().is_relative_to(outside.resolve()):
            outside_reads.append(str(path))
        return original_open(path, mode, *args, **kwargs)

    with monkeypatch.context() as patcher:
        patcher.setattr(Path, "open", recording_open)
        code, output = invoke(tmp_path, capsys, *create_args())
    assert code == 1, output
    assert outside_reads == [], "preflight must reject paths before reading an external symlink target"
    assert tree(tmp_path) == before
    assert tree(outside) == external_before


@pytest.mark.parametrize("args,expected", [(["--attest-file"], 2), (["--attest-file", "src/demo.py"], 1),
    (["--attest", "demo", "--attest-file", "src/demo.py"], 1),
    (["--workset", "--attest", "demo", "--attest-purpose", "release_gate", "--attest-file", "src/demo.py"], 1)])
def test_binding_argument_errors_are_visible_and_never_write(tmp_path, capsys, args, expected):
    project(tmp_path)
    before = tree(tmp_path)
    code, output = invoke(tmp_path, capsys, *args)
    assert code == expected, output
    assert tree(tmp_path) == before


def test_new_binding_cannot_silently_succeed_without_governance(tmp_path, capsys):
    write(tmp_path, "src/demo.py", "fixture\n")
    before = tree(tmp_path)
    code, output = invoke(tmp_path, capsys, *create_args("src/demo.py"))
    assert code == 1, output
    assert tree(tmp_path) == before
    assert invoke(tmp_path, capsys)[0] == 0, "uninitialized default mode remains compatible"


def test_existing_governance_errors_prevent_binding_write(tmp_path, capsys):
    project(tmp_path)
    write(tmp_path, "docs/plans/other.md", "# Missing completed-plan evidence\n")
    before = tree(tmp_path)
    code, output = invoke(tmp_path, capsys, *create_args())
    assert code == 1, output
    assert tree(tmp_path) == before


STORAGE_MUTATIONS = [
    ("binding-type", lambda d: d.update(binding=[])),
    ("binding-version", lambda d: d["binding"].update(version=2)),
    ("binding-bool-version", lambda d: d["binding"].update(version=True)),
    ("files-type", lambda d: d["binding"].update(files="src/demo.py")),
    ("files-empty", lambda d: d["binding"].update(files=[])),
    ("files-duplicate", lambda d: d["binding"]["files"].append(d["binding"]["files"][0].copy())),
    ("files-unsorted", lambda d: d["binding"]["files"].reverse()),
    ("file-path-type", lambda d: d["binding"]["files"][0].update(path=17)),
    ("file-path-escape", lambda d: d["binding"]["files"][0].update(path="../outside")),
    ("file-hash", lambda d: d["binding"]["files"][0].update(sha256="BAD")),
    ("related-empty", lambda d: d["binding"].update(related_plans=[])),
    ("related-duplicate", lambda d: d["binding"]["related_plans"].append(d["binding"]["related_plans"][0].copy())),
    ("related-path", lambda d: d["binding"]["related_plans"][0].update(path="../outside.md")),
    ("projection-type", lambda d: d["binding"].update(plan_map_projection=[])),
    ("projection-version", lambda d: d["binding"]["plan_map_projection"].update(version=2)),
    ("projection-members", lambda d: d["binding"]["plan_map_projection"].update(members=[])),
    ("projection-row-type", lambda d: d["binding"]["plan_map_projection"].update(index_rows=[{}])),
    ("projection-cell-type", lambda d: d["binding"]["plan_map_projection"]["index_rows"][0].__setitem__(1, 3)),
    ("projection-hash", lambda d: d["binding"].update(plan_map_projection_sha256="0" * 64)),
    ("revision-type", lambda d: d["binding"].update(revision=[])),
    ("revision-source", lambda d: d["binding"]["revision"].update(source="index")),
    ("revision-head", lambda d: d["binding"]["revision"].update(head="not-a-head")),
]


@pytest.mark.parametrize("label,mutation", STORAGE_MUTATIONS, ids=[entry[0] for entry in STORAGE_MUTATIONS])
def test_malformed_binding_is_retained_and_strictly_rejected(tmp_path, capsys, label, mutation):
    project(tmp_path)
    path, _ = make_snapshot(tmp_path, capsys)
    update_snapshot(path, mutation)
    assert_checked(tmp_path, capsys, "needs_review", 1)


@pytest.mark.parametrize("kind", ["index_missing", "plan_missing", "related_plan_missing", "plan_directory", "map_missing"])
def test_missing_bound_plan_cannot_disappear_from_reports(tmp_path, capsys, kind):
    graph = graph_project(tmp_path)
    snapshot, _ = make_snapshot(tmp_path, capsys)
    if kind == "index_missing":
        graph["index_rows"].pop(0)
        render_graph(tmp_path, graph)
    elif kind == "map_missing":
        (tmp_path / "docs/PLAN_MAP.md").unlink()
    else:
        (tmp_path / f"docs/plans/{'demo' if kind == 'plan_missing' else 'proof'}.md").unlink()
        if kind == "plan_directory":
            (tmp_path / "docs/plans/proof.md").mkdir()
    code, output = invoke(tmp_path, capsys, "--check-attestations", "--strict-readiness")
    assert code == 1, output
    assert f"{snapshot.relative_to(tmp_path).as_posix()} |" in output, output
    assert "status=needs_review" in output
    if kind == "map_missing":
        code, output = invoke(tmp_path, capsys, "--check-attestations")
        assert code == 0, output
        assert "status=needs_review" in output


@pytest.mark.parametrize("value", [None, [], True, "invalid record", "{"])
def test_unparseable_or_nonobject_legacy_json_remains_warning(tmp_path, capsys, value):
    project(tmp_path)
    write(tmp_path, "docs/attestations/bad.json", "{" if value == "{" else json.dumps(value))
    before = tree(tmp_path)
    for flags in [[], ["--strict-readiness"]]:
        code, output = invoke(tmp_path, capsys, "--check-attestations", *flags)
        assert code == 0, output
        assert "WARNING" in output
    assert tree(tmp_path) == before


def clone_snapshot(root, source, *, token="bbbbbbbb", **changes):
    data = json.loads(source.read_text())
    data.update(snapshot_id="20260906T010203Z-" + token, **changes)
    path = root / f"docs/attestations/{data['plan']}--{data['purpose']}--{data['snapshot_id']}.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


def status_for(output, path, root):
    prefix = "ATTESTATION: " + path.relative_to(root).as_posix() + " |"
    rows = [line for line in output.splitlines() if line.startswith(prefix)]
    assert len(rows) == 1, output
    return rows[0].rsplit("status=", 1)[-1]


def test_valid_successor_retires_drifted_predecessor_and_later_drift_does_not_revive_it(tmp_path, capsys):
    project(tmp_path)
    first, _ = make_snapshot(tmp_path, capsys)
    first_bytes = first.read_bytes()
    write(tmp_path, "src/demo.py", "second reviewed version\n")
    second, _ = make_snapshot(tmp_path, capsys, supersedes=first.relative_to(tmp_path).as_posix())
    code, output = invoke(tmp_path, capsys, "--check-attestations", "--strict-readiness")
    assert code == 0, output
    assert status_for(output, first, tmp_path) == "superseded"
    assert status_for(output, second, tmp_path) == "current"
    assert first.read_bytes() == first_bytes
    write(tmp_path, "src/demo.py", "third unreviewed version\n")
    code, output = invoke(tmp_path, capsys, "--check-attestations", "--strict-readiness")
    assert code == 1, output
    assert status_for(output, first, tmp_path) == "superseded"
    assert status_for(output, second, tmp_path) == "needs_review"


@pytest.mark.parametrize("legacy", [True, False])
def test_binding_can_replace_old_same_purpose_snapshot(tmp_path, capsys, legacy):
    project(tmp_path)
    args = ["--attest", "demo"] + ([] if legacy else ["--attest-purpose", "phase_completion"])
    assert invoke(tmp_path, capsys, *args)[0] == 0
    first = next((tmp_path / "docs/attestations").glob("*.json"))
    second, _ = make_snapshot(tmp_path, capsys, purpose="phase_completion", supersedes=first.relative_to(tmp_path).as_posix())
    code, output = invoke(tmp_path, capsys, "--check-attestations", "--strict-readiness")
    assert code == 0, output
    assert status_for(output, first, tmp_path) == "superseded"
    assert status_for(output, second, tmp_path) == "current"


@pytest.mark.parametrize("bad_successor", ["purpose_only", "legacy", "malformed_binding", "missing_target", "different_plan", "different_purpose", "cycle", "self"])
def test_invalid_successor_never_suppresses_bound_predecessor(tmp_path, capsys, bad_successor):
    project(tmp_path)
    first, _ = make_snapshot(tmp_path, capsys, purpose="phase_completion")
    relative = first.relative_to(tmp_path).as_posix()
    second = clone_snapshot(tmp_path, first, supersedes=relative)
    if bad_successor in {"purpose_only", "legacy"}:
        update_snapshot(second, lambda d: d.pop("binding"))
        if bad_successor == "legacy":
            update_snapshot(second, lambda d: [d.pop(key) for key in ["purpose", "snapshot_id"]])
            second.rename(tmp_path / "docs/attestations/demo.json")
            second = tmp_path / "docs/attestations/demo.json"
    elif bad_successor == "malformed_binding":
        update_snapshot(second, lambda d: d["binding"].update(version=999))
    elif bad_successor == "missing_target":
        update_snapshot(second, lambda d: d.update(supersedes="docs/attestations/missing.json"))
    elif bad_successor in {"different_plan", "different_purpose"}:
        changes = {"plan": "other"} if bad_successor == "different_plan" else {"purpose": "compliance"}
        update_snapshot(second, lambda d: d.update(changes))
        data = json.loads(second.read_text())
        renamed = second.with_name(f"{data['plan']}--{data['purpose']}--{data['snapshot_id']}.json")
        second.rename(renamed)
        second = renamed
    elif bad_successor == "cycle":
        update_snapshot(first, lambda d: d.update(supersedes=second.relative_to(tmp_path).as_posix()))
    else:
        update_snapshot(second, lambda d: d.update(supersedes=second.relative_to(tmp_path).as_posix()))
    write(tmp_path, "src/demo.py", "drift that an invalid edge must not hide\n")
    before = tree(tmp_path)
    for flags, expected_code in [([], 0), (["--strict-readiness"], 1)]:
        code, output = invoke(tmp_path, capsys, "--check-attestations", *flags)
        assert code == expected_code, output
        assert status_for(output, first, tmp_path) == "needs_review", output
    assert tree(tmp_path) == before


def test_structurally_invalid_predecessor_blocks_even_with_a_successor(tmp_path, capsys):
    project(tmp_path)
    first, _ = make_snapshot(tmp_path, capsys)
    second, _ = make_snapshot(tmp_path, capsys, supersedes=first.relative_to(tmp_path).as_posix())
    update_snapshot(first, lambda d: d["binding"].update(version=999))
    code, output = invoke(tmp_path, capsys, "--check-attestations", "--strict-readiness")
    assert code == 1, output
    assert status_for(output, first, tmp_path) == "needs_review"
    assert second.exists()


@pytest.mark.parametrize("review_status", ["superseded", "needs_review"])
def test_manual_status_cannot_remove_pending_binding_review(tmp_path, capsys, review_status):
    project(tmp_path)
    path, _ = make_snapshot(tmp_path, capsys)
    update_snapshot(path, lambda d: d.update(review_status=review_status))
    if review_status == "superseded":
        write(tmp_path, "src/demo.py", "changed\n")
    assert_checked(tmp_path, capsys, "needs_review", 1)


@pytest.mark.parametrize("kind", ["missing", "different_plan", "different_purpose", "duplicate_current", "unparseable"])
def test_new_snapshot_relation_preflight_never_creates_invalid_successor(tmp_path, capsys, kind):
    project(tmp_path)
    first, _ = make_snapshot(tmp_path, capsys)
    kwargs = {}
    if kind == "missing":
        kwargs["supersedes"] = "docs/attestations/missing.json"
    elif kind == "different_plan":
        other, _ = make_snapshot(tmp_path, capsys, "src/other.py", plan="other")
        kwargs["supersedes"] = other.relative_to(tmp_path).as_posix()
    elif kind == "different_purpose":
        other, _ = make_snapshot(tmp_path, capsys, purpose="compliance")
        kwargs["supersedes"] = other.relative_to(tmp_path).as_posix()
    elif kind == "unparseable":
        target = write(tmp_path, "docs/attestations/unparseable.json", "{")
        kwargs["supersedes"] = target.relative_to(tmp_path).as_posix()
    before = tree(tmp_path)
    code, output = invoke(tmp_path, capsys, *create_args(**kwargs))
    assert code == 1, output
    assert tree(tmp_path) == before


def test_duplicate_current_snapshots_are_retained_as_needing_review(tmp_path, capsys):
    project(tmp_path)
    first, _ = make_snapshot(tmp_path, capsys)
    second = clone_snapshot(tmp_path, first)
    code, output = invoke(tmp_path, capsys, "--check-attestations", "--strict-readiness")
    assert code == 1, output
    assert "多个 current" in output
    assert status_for(output, first, tmp_path) == status_for(output, second, tmp_path) == "needs_review"


def fixed_snapshot_name(monkeypatch):
    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 9, 6, 1, 2, 3, tzinfo=timezone.utc)
    monkeypatch.setattr(checker, "datetime", FixedDateTime)
    monkeypatch.setattr(checker.secrets, "token_hex", lambda count: "aaaaaaaa")
    return "docs/attestations/demo--release_gate--20260906T010203Z-aaaaaaaa.json"


@pytest.mark.parametrize("kind", ["self_supersedes", "self_file", "existing_file", "target_symlink"])
def test_output_identity_preflight_prevents_self_reference_or_overwrite(tmp_path, capsys, monkeypatch, kind):
    project(tmp_path)
    relative = fixed_snapshot_name(monkeypatch)
    args = create_args()
    if kind == "self_supersedes":
        args.extend(["--supersedes", relative])
    elif kind == "self_file":
        args.extend(["--attest-file", relative])
    elif kind == "existing_file":
        write(tmp_path, relative, "existing contents must remain\n")
    else:
        external = write(tmp_path, "external-sentinel.json", "external contents must remain\n")
        (tmp_path / relative).parent.mkdir()
        (tmp_path / relative).symlink_to(external)
    before = tree(tmp_path)
    code, output = invoke(tmp_path, capsys, *args)
    assert code == 1, output
    assert tree(tmp_path) == before


def test_working_tree_bytes_are_distinct_from_head_and_index(tmp_path, capsys):
    project(tmp_path)
    def git(*args):
        return subprocess.run(["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", *args],
                              cwd=tmp_path, text=True, capture_output=True, check=True).stdout.strip()
    git("init", "-q")
    git("add", ".")
    git("commit", "-qm", "fixture baseline")
    first_head = git("rev-parse", "HEAD")
    source = tmp_path / "src/demo.py"
    source.write_text("staged bytes\n")
    git("add", "src/demo.py")
    source.write_text("working tree bytes\n")
    path, data = make_snapshot(tmp_path, capsys)
    recorded = next(item for item in data["binding"]["files"] if item["path"] == "src/demo.py")
    assert recorded["sha256"] == digest(source)
    for prior in [git("show", "HEAD:src/demo.py"), git("show", ":src/demo.py")]:
        assert recorded["sha256"] != hashlib.sha256((prior + "\n").encode()).hexdigest()
    assert data["binding"]["revision"] == {"source": "working_tree", "head": first_head}
    write(tmp_path, "unrelated.txt", "unrelated commit\n")
    git("add", "unrelated.txt")
    git("commit", "-qm", "only unrelated file", "--only", "unrelated.txt")
    assert git("rev-parse", "HEAD") != first_head
    assert_checked(tmp_path, capsys)
    assert data == json.loads(path.read_text())


@pytest.mark.parametrize("failure", ["read", "mkdir", "open", "write", "write_existing_directory", "unlink", "rmdir"])
def test_binding_io_failures_clean_only_new_artifacts_and_report_cleanup_failure(tmp_path, capsys, monkeypatch, failure):
    project(tmp_path)
    relative = fixed_snapshot_name(monkeypatch)
    target = tmp_path / relative
    if failure == "write_existing_directory":
        write(tmp_path, "docs/attestations/keep.txt", "existing directory contents\n")
    before = tree(tmp_path)
    original_open, original_mkdir = Path.open, Path.mkdir
    original_unlink, original_rmdir = Path.unlink, Path.rmdir
    injected = []

    class PartialWrite:
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.stream.close()

        def write(self, content):
            self.stream.write(content[:10])
            self.stream.flush()
            injected.append("write")
            raise OSError("fixture partial write failure")

    def failing_open(path, mode="r", *args, **kwargs):
        if failure == "read" and path == tmp_path / "src/demo.py" and mode == "rb":
            injected.append("read")
            raise OSError("fixture source read failure")
        if path == target and mode == "x":
            if failure == "open":
                injected.append("open")
                raise OSError("fixture exclusive open failure")
            stream = original_open(path, mode, *args, **kwargs)
            return PartialWrite(stream)
        return original_open(path, mode, *args, **kwargs)

    def failing_mkdir(path, *args, **kwargs):
        if failure == "mkdir" and path == target.parent:
            injected.append("mkdir")
            raise OSError("fixture mkdir failure")
        return original_mkdir(path, *args, **kwargs)

    def failing_unlink(path, *args, **kwargs):
        if failure == "unlink" and path == target:
            injected.append("unlink")
            raise OSError("fixture unlink failure")
        return original_unlink(path, *args, **kwargs)

    def failing_rmdir(path, *args, **kwargs):
        if failure == "rmdir" and path == target.parent:
            injected.append("rmdir")
            raise OSError("fixture rmdir failure")
        return original_rmdir(path, *args, **kwargs)

    with monkeypatch.context() as patcher:
        patcher.setattr(Path, "open", failing_open)
        patcher.setattr(Path, "mkdir", failing_mkdir)
        patcher.setattr(Path, "unlink", failing_unlink)
        patcher.setattr(Path, "rmdir", failing_rmdir)
        code, output = invoke(tmp_path, capsys, *create_args())
    assert code == 1, output
    assert injected, "fault injection must actually execute"
    assert "fixture" in output
    if failure in {"unlink", "rmdir"}:
        assert "残留路径" in output
        assert str(target if failure == "unlink" else target.parent) in output
        assert target.exists() == (failure == "unlink")
        assert target.parent.is_dir()
        for name, value in before.items():
            assert tree(tmp_path)[name] == value, name
    else:
        assert tree(tmp_path) == before


def test_explicit_whole_map_binding_includes_human_shared_write_notes(tmp_path, capsys):
    project(tmp_path)
    make_snapshot(tmp_path, capsys, "src/demo.py", "docs/PLAN_MAP.md")
    with (tmp_path / "docs/PLAN_MAP.md").open("a") as stream:
        stream.write(table("并行与共享写入约束", ["范围", "允许并行", "串行边界", "依据"], [["demo", "new human notes", "human ordering", "human evidence"]]))
    assert_checked(tmp_path, capsys, "needs_review", 1)


def test_removed_predecessor_file_can_be_replaced_by_reviewed_new_file(tmp_path, capsys):
    project(tmp_path)
    first, _ = make_snapshot(tmp_path, capsys)
    (tmp_path / "src/demo.py").unlink()
    write(tmp_path, "src/replacement.py", "replacement reviewed implementation\n")
    second, _ = make_snapshot(tmp_path, capsys, "src/replacement.py", "docs/report.md", supersedes=first.relative_to(tmp_path).as_posix())
    code, output = invoke(tmp_path, capsys, "--check-attestations", "--strict-readiness")
    assert code == 0, output
    assert status_for(output, first, tmp_path) == "superseded"
    assert status_for(output, second, tmp_path) == "current"


def test_pending_successor_cycle_is_rejected_before_write(tmp_path, capsys, monkeypatch):
    project(tmp_path)
    first, _ = make_snapshot(tmp_path, capsys)
    pending_relative = fixed_snapshot_name(monkeypatch)
    update_snapshot(first, lambda d: d.update(supersedes=pending_relative))
    before = tree(tmp_path)
    code, output = invoke(tmp_path, capsys, *create_args(supersedes=first.relative_to(tmp_path).as_posix()))
    assert code == 1, output
    assert tree(tmp_path) == before


@pytest.mark.parametrize("kind", ["plan", "map", "snapshot", "snapshot_directory"])
def test_checking_existing_bindings_never_reads_external_symlink_targets(tmp_path, capsys, monkeypatch, kind):
    project(tmp_path)
    snapshot, _ = make_snapshot(tmp_path, capsys)
    outside = tmp_path.parent / (tmp_path.name + "-external")
    outside.mkdir()
    if kind == "snapshot_directory":
        source = tmp_path / "docs/attestations"
        moved = outside / "records"
        source.rename(moved)
        source.symlink_to(moved, target_is_directory=True)
    else:
        source = {"plan": tmp_path / "docs/plans/demo.md", "map": tmp_path / "docs/PLAN_MAP.md", "snapshot": snapshot}[kind]
        moved = outside / "content"
        source.rename(moved)
        source.symlink_to(moved)
    before, outside_before = tree(tmp_path), tree(outside)
    opened = []
    original_open = Path.open

    def recording_open(path, mode="r", *args, **kwargs):
        if mode in {"r", "rb"} and path.resolve().is_relative_to(outside.resolve()):
            opened.append(str(path))
        return original_open(path, mode, *args, **kwargs)

    with monkeypatch.context() as patcher:
        patcher.setattr(Path, "open", recording_open)
        code, output = invoke(tmp_path, capsys, "--check-attestations", "--strict-readiness")
    assert opened == [], "checking must reject external links before reading their contents"
    assert code == 1, output
    if kind in {"plan", "map"}:
        assert status_for(output, snapshot, tmp_path) == "needs_review"
    assert tree(tmp_path) == before
    assert tree(outside) == outside_before


@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0, reason="root bypasses POSIX file read permissions")
@pytest.mark.parametrize("legacy", [True, False], ids=["legacy", "purpose_only"])
@pytest.mark.parametrize("kind", ["plan", "map"])
def test_d04_unreadable_mixed_content_preserves_reports_and_recovers(tmp_path, capsys, legacy, kind):
    project(tmp_path)
    old_args = ["--attest", "demo"] + ([] if legacy else ["--attest-purpose", "phase_completion"])
    code, output = invoke(tmp_path, capsys, *old_args)
    assert code == 0, output
    first = next((tmp_path / "docs/attestations").iterdir())
    second, _ = make_snapshot(tmp_path, capsys, purpose="phase_completion", supersedes=first.relative_to(tmp_path).as_posix())
    source = tmp_path / ("docs/plans/demo.md" if kind == "plan" else "docs/PLAN_MAP.md")
    permissions = source.stat().st_mode & 0o777
    before = tree(tmp_path)
    try:
        source.chmod(0o000)
        with pytest.raises(PermissionError):
            source.read_bytes()
        for flags in [(), ("--strict-readiness",)]:
            result = cli(tmp_path, "--check-attestations", *flags)
            output = result.stdout + result.stderr
            assert "Traceback" not in output, output
            assert "Permission denied" in output, output
            if kind == "plan":
                assert status_for(output, first, tmp_path) == "superseded", output
            assert status_for(output, second, tmp_path) == "needs_review", output
            if flags:
                assert result.returncode == 1, output
    finally:
        source.chmod(permissions)
    assert tree(tmp_path) == before
    recovered = cli(tmp_path, "--check-attestations", "--strict-readiness")
    output = recovered.stdout + recovered.stderr
    assert recovered.returncode == 0, output
    assert status_for(output, first, tmp_path) == "superseded", output
    assert status_for(output, second, tmp_path) == "current", output
    assert tree(tmp_path) == before


@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0, reason="root bypasses POSIX directory read permissions")
@pytest.mark.parametrize("permissions", [0o000, 0o300], ids=["000", "0300"])
@pytest.mark.parametrize("strict", [False, True], ids=["default", "strict"])
def test_d02_unreadable_snapshot_directory_is_not_an_empty_success(tmp_path, capsys, permissions, strict):
    project(tmp_path)
    make_snapshot(tmp_path, capsys)
    directory = tmp_path / "docs/attestations"
    original_permissions = directory.stat().st_mode & 0o777
    before = tree(tmp_path)
    try:
        directory.chmod(permissions)
        with pytest.raises(PermissionError):
            os.listdir(directory)
        flags = ["--strict-readiness"] if strict else []
        code, output = invoke(tmp_path, capsys, "--check-attestations", *flags)
    finally:
        directory.chmod(original_permissions)
    assert code == (1 if strict else 0), output
    assert ("ERROR:" if strict else "WARNING:") in output, output
    assert "attestations" in output, "directory enumeration failure needs a visible path diagnostic"
    assert tree(tmp_path) == before


@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0, reason="root bypasses POSIX directory read permissions")
@pytest.mark.parametrize("permissions", [0o000, 0o300], ids=["000", "0300"])
def test_d02_unreadable_directory_cannot_create_a_second_current(tmp_path, capsys, monkeypatch, permissions):
    project(tmp_path)
    first, _ = make_snapshot(tmp_path, capsys)
    directory = first.parent
    original_permissions = directory.stat().st_mode & 0o777
    before = tree(tmp_path)
    original_open = Path.open
    attempted_writes = []

    def record_exclusive_open(path, mode="r", *args, **kwargs):
        if path.parent == directory and mode == "x":
            attempted_writes.append(path.name)
        return original_open(path, mode, *args, **kwargs)

    try:
        directory.chmod(permissions)
        with pytest.raises(PermissionError):
            os.listdir(directory)
        with monkeypatch.context() as patcher:
            patcher.setattr(Path, "open", record_exclusive_open)
            code, output = invoke(tmp_path, capsys, *create_args())
    finally:
        directory.chmod(original_permissions)
    assert code == 1, output
    assert attempted_writes == [], "unreadable inventory must fail preflight before any new snapshot write"
    assert "ERROR:" in output, output
    assert tree(tmp_path) == before
    assert len(list(directory.iterdir())) == 1


@pytest.mark.parametrize("legacy", [True, False], ids=["legacy", "purpose_only"])
@pytest.mark.parametrize("kind", ["plan", "map"])
def test_d03_mixed_old_and_bound_chain_does_not_read_external_targets(tmp_path, capsys, monkeypatch, legacy, kind):
    project(tmp_path)
    old_args = ["--attest", "demo"] + ([] if legacy else ["--attest-purpose", "phase_completion"])
    code, output = invoke(tmp_path, capsys, *old_args)
    assert code == 0, output
    first = next((tmp_path / "docs/attestations").iterdir())
    second, _ = make_snapshot(tmp_path, capsys, purpose="phase_completion", supersedes=first.relative_to(tmp_path).as_posix())
    code, output = invoke(tmp_path, capsys, "--check-attestations", "--strict-readiness")
    assert code == 0, output
    assert status_for(output, first, tmp_path) == "superseded"
    assert status_for(output, second, tmp_path) == "current"

    outside = tmp_path.parent / (tmp_path.name + "-external")
    outside.mkdir()
    source = tmp_path / ("docs/plans/demo.md" if kind == "plan" else "docs/PLAN_MAP.md")
    external_file = outside / "original-content.md"
    source.rename(external_file)
    source.symlink_to(external_file)
    before, outside_before = tree(tmp_path), tree(outside)
    original_open = Path.open
    opened = []

    def recording_open(path, mode="r", *args, **kwargs):
        if mode in {"r", "rb"} and path.resolve().is_relative_to(outside.resolve()):
            opened.append((str(path), mode))
        return original_open(path, mode, *args, **kwargs)

    with monkeypatch.context() as patcher:
        patcher.setattr(Path, "open", recording_open)
        code, output = invoke(tmp_path, capsys, "--check-attestations", "--strict-readiness")
    assert opened == [], "legacy hash branches must obey the bound chain's path checks"
    assert code == 1, output
    assert status_for(output, second, tmp_path) == "needs_review"
    assert tree(tmp_path) == before
    assert tree(outside) == outside_before
