#!/usr/bin/env python3
import argparse
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path


VALID_STATUSES = {
    "候选",
    "设计中",
    "待实施",
    "实施中",
    "已完成",
    "已替代",
    "已合并",
    "已废弃",
}

CLAUDE_SECTION_BEGIN = "<!-- plan-governance:start -->"
CLAUDE_SECTION_END = "<!-- plan-governance:end -->"
AGENTS_SECTION_BEGIN = "<!-- plan-governance:start -->"
AGENTS_SECTION_END = "<!-- plan-governance:end -->"


def slugify(value):
    value = value.strip().lower()
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"[^a-z0-9\u4e00-\u9fff._-]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-._")
    if not value:
        raise ValueError("计划名称不能为空")
    return value


def write_file(path, content, force):
    if path.exists() and not force:
        raise FileExistsError(f"{path} 已存在；如需覆盖请加 --force")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def init_git(root):
    if (root / ".git").exists():
        return None

    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=root, check=True)
    return root / ".git"


def agent_rules_body():
    return """## 计划治理

本项目使用轻量计划治理。处理跨阶段、架构、公共 API、Schema、迁移、兼容性或长期任务时，必须遵循以下规则。

实施前必须读取：

- `docs/PLAN_MAP.md`
- 当前相关的 `docs/plans/*.md`
- 相关 `docs/adr/*.md`
- 相关 `docs/migrations/*.md`

需求探索与 grilling：

- 对可能进入治理的任务，若 `grill-me` 可用，遇到高影响事项且目标/边界/验收/取舍未明确，或同时存在至少两项需求不确定性信号时，先执行 grilling。
- grilling 每次只问一个问题；可由仓库、环境或工具确认的事实先自行查证，产品取舍和不可逆选择由用户确认。
- 在用户确认结构化总结前不得实施或把暂定内容写成规范事实。确认后，只把已确认事实、暂定假设、范围/非目标、候选方案、未决问题和探索结论写入专项计划的 `需求探索` 章节。
- grilling 不替代 Step 0、样本矩阵、验证、失败/回滚边界或独立准入复核；`grill-me` 不可用时说明依赖不可用并保持在澄清/设计边界，不得伪造已完成 grilling。

事实源规则：

- 专项计划是实施细节事实源，记录字段方案、Schema、枚举、Step 0 证据、验证方式和完成条件。
- `docs/PLAN_MAP.md` 是状态、当前阶段、最后更新、依赖、替代/合并/废弃关系、推荐顺序、阻塞项和证据链接的事实源。
- 总路线图、优先级计划和索引只记录顺序、状态摘要和专项计划链接，不复制字段级方案、枚举、Step 0 细节或完成定义。
- 如果同一事实在多个文档中重复，保留一个事实源，其他文档改为链接引用。

阶段转换规则：

- 阶段 N 完成只关闭阶段 N，不自动改变阶段 N+1 的准入状态。
- 阶段 N+1 默认保持 `设计中`，直到完成该阶段自己的 Step 0、验证方式、完成条件和独立准入复核。
- 只有最新的独立准入复核明确写出“达到 `待实施` 标准”，阶段才可标记为 `待实施`。
- 不得以阶段 N 的完成证据、全量测试通过、治理脚本通过或实施者声明替代阶段 N+1 的 Step 0。
- `PLAN_MAP.md` 的 `状态` 是计划级生命周期，`当前阶段` 是阶段身份指针；专项计划只承载该阶段的实施细节和准入证据。

阶段准入最低条件：

- 当前阶段目标、范围和非目标明确。
- Step 0 记录明确基线类型；样本/fixture 矩阵包含输入或基线、可执行命令、预期结果、失败判定和输出位置。
- 验证方式、完成条件、失败策略和回滚或安全边界明确。
- 没有未解决的当前阶段阻塞项，且 `PLAN_MAP.md` 已同步。
- 最新独立准入复核明确为“通过”。
- 机器识别的结构化章节标题固定为 `阶段路线图`、`当前阶段`、`阶段准入摘要`、`最新独立准入复核`、`独立复核记录`；不要写成 `阶段 1 准入摘要` 等带编号变体，阶段编号以 `PLAN_MAP.md` 的当前阶段为准。

专项计划应保留追加式独立复核记录，并显式维护最新结论的日期、阶段、结论、证据和复核者。历史记录不得覆盖；`PLAN_MAP.md` 只链接最新有效结论。

阶段准入严格检查命令为 `--strict-readiness`。默认治理检查保持兼容，准入缺陷先以 `WARNING` 提示，严格模式才提升为 `ERROR`；该检查只判断结构化准入条件，不替代业务验收。

草案和历史文档规则：

- 启用治理后，已有草案、历史设计、归档计划、临时分析文档等默认只作为背景材料，不再作为规范事实源。
- 除非用户明确点名要求更新这些文档，否则不要继续修改它们来承载新规范。
- 新发生的目标、范围、非目标、公共契约、字段、Schema、状态语义、阶段、验证方式、完成条件、风险和回滚，应写入 `docs/plans/*.md`、ADR、migration 或正式 spec。
- 计划状态、当前阶段、最后更新、依赖、替代/合并/废弃关系、推荐顺序、阻塞项和证据链接，应写入或同步 `docs/PLAN_MAP.md`。
- 当用户说“补充一下”“记录一下”“把刚才的结论写进去”时，如果治理已启用，默认写入治理文档；不要写入草案、README 或历史设计文档，除非用户明确点名该文件。

实施规则：

1. 只实施当前计划文档中明确的当前阶段。
2. 当前阶段必须具备 Step 0 证据、验证方式、完成条件，且没有未解决阻塞项。
3. 如果缺少 Step 0 证据，不要直接改实现；先补充复现、基线、样本、契约测试，或记录替代基线。
4. 如果实现过程中发现假设变化、计划顺序变化、公共契约变化、兼容策略变化、完成条件变化，或专项计划的状态、当前阶段、最后更新、字段方案、完成条件、验证结果变化，先更新治理文档，再继续实现。
5. 当专项计划变化时，必须同步 `docs/PLAN_MAP.md` 和所有引用该计划的路线图、优先级计划或索引。
6. 验收治理文档时，必须用 `rg` 搜索同名计划、P 编号、状态名、关键字段，以及 `草案为准|以草案为事实源|详见草案|draft is source|source of truth.*draft|以.*draft.*为准`，检查是否存在重复定义、漂移或旧草案重新成为事实源。
7. 完成后必须更新计划状态、验证证据、测试覆盖证据。
8. 完成后运行：

   ```bash
   plan-governance-cli check .
   ```

9. 如需检查活跃计划停滞，运行 `plan-governance-cli check . --stale-days`；默认阈值为 10 天。
10. 旧项目如果 `PLAN_MAP.md` 仍是五列表，先运行 `plan-governance-cli init --root . --migrate-plan-map-last-updated` 显式迁移。
11. 普通小范围 bugfix 或一次性修改不需要强制新建治理文档，除非已有计划覆盖它。

验收独立性：

- 实施者可以更新计划状态、填写验证证据和同步治理文档，但这些内容只代表实施声明，不是验收结论。
- 验收者不得仅依据计划状态、完成证据文字或文档格式判定完成；必须基于当前仓库内容、可复现验证命令和反向引用检查独立确认。
- 验收时应逐条核对计划的完成条件、实际代码或文档变更、测试或 CI 输出、覆盖率证据，以及是否存在计划外行为变化。
- 如果实现偏离计划，必须更新相关计划、ADR、migration 或 spec 后再判定完成。
"""


def managed_section(begin, end):
    return f"{begin}\n{agent_rules_body()}{end}\n"


def claude_md_section():
    return managed_section(CLAUDE_SECTION_BEGIN, CLAUDE_SECTION_END)


def agents_md_section():
    return managed_section(AGENTS_SECTION_BEGIN, AGENTS_SECTION_END)


def update_managed_file(root, filename, section, begin, end):
    target = root / filename
    if not target.exists():
        write_file(target, section, force=False)
        return target

    current = target.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"{re.escape(begin)}.*?{re.escape(end)}",
        re.DOTALL,
    )
    if pattern.search(current):
        updated = pattern.sub(section.rstrip(), current)
    else:
        separator = "\n\n" if current.rstrip() else ""
        updated = f"{current.rstrip()}{separator}{section}"
    target.write_text(updated, encoding="utf-8")
    return target


def update_claude_md(root):
    return update_managed_file(
        root,
        "CLAUDE.md",
        claude_md_section(),
        CLAUDE_SECTION_BEGIN,
        CLAUDE_SECTION_END,
    )


def update_agents_md(root):
    return update_managed_file(
        root,
        "AGENTS.md",
        agents_md_section(),
        AGENTS_SECTION_BEGIN,
        AGENTS_SECTION_END,
    )


def update_agent_rules(root):
    return [update_claude_md(root), update_agents_md(root)]


def plan_map_content(plan_slug, title, status, phase):
    today = date.today().isoformat()
    row = f"| [{title}](plans/{plan_slug}.md) | {status} | {phase} | {today} | - | - |"
    unfinished_row = row if status in {"候选", "设计中", "待实施", "实施中"} else ""
    completed_row = row if status == "已完成" else ""
    deprecated_row = row if status in {"已废弃", "已替代", "已合并"} else ""
    return f"""# PLAN_MAP

## 治理范围

本文件只跟踪跨阶段、影响公共契约、依赖真实反馈，或会与其他计划发生关系的计划。普通一次性任务不要加入这里。

## 文档权责

- `docs/PLAN_MAP.md` 是状态、依赖、替代/合并/废弃关系、推荐顺序、阻塞项和证据链接的事实源。
- `docs/plans/*.md` 是专项计划的实施细节事实源，记录字段方案、Schema、枚举、Step 0 证据、验证方式和完成条件。
- 总路线图、优先级计划和索引只记录顺序、状态摘要和专项计划链接，不复制字段级方案、枚举、Step 0 细节或完成定义。
- 当专项计划变化时，必须同步所有引用该计划的路线图、优先级计划或索引。
- 如果同一事实在多个文档中重复，保留一个事实源，其他文档改为链接引用。
- `PLAN_MAP.md` 的 `状态` 是计划级生命周期，`当前阶段` 是阶段身份指针；阶段 N 完成后，阶段 N+1 默认保持 `设计中`。
- 阶段准入摘要、样本矩阵和独立复核记录只写入专项计划，不复制到本索引。
- 启用治理后，已有草案、历史设计、归档计划和临时分析文档默认只作为背景材料，不再作为规范事实源；后续新规范默认进入 `docs/plans/*.md`、ADR、migration、正式 spec 或 `docs/PLAN_MAP.md`。
- 计划索引固定分为 `未完成`、`已完成`、`已废弃` 三张表；`已替代`、`已合并`等不再推进的终态归入 `已废弃` 表，但保留真实状态值。

## 计划索引

### 未完成

| 计划 | 状态 | 当前阶段 | 最后更新 | 依赖 | 证据 |
|---|---|---|---|---|---|
{unfinished_row}

### 已完成

| 计划 | 状态 | 当前阶段 | 最后更新 | 依赖 | 证据 |
|---|---|---|---|---|---|
{completed_row}

### 已废弃

| 计划 | 状态 | 当前阶段 | 最后更新 | 依赖 | 证据 |
|---|---|---|---|---|---|
{deprecated_row}

允许状态：`候选`、`设计中`、`待实施`、`实施中`、`已完成`、`已替代`、`已合并`、`已废弃`。

## 推荐顺序

1. `{plan_slug}`

## 依赖关系

| 计划 | 依赖 | 原因 |
|---|---|---|
| {plan_slug} | - | - |

## 替代、合并和废弃

| 计划 | 关系 | 目标 | 原因 |
|---|---|---|---|
| - | - | - | - |

## 当前阻塞项

| 问题 | 推荐方案 | 影响范围 | 是否阻塞当前阶段 | 状态 |
|---|---|---|---|---|
| - | - | - | 否 | 已延后 |

## 完成证据

| 计划 | 阶段 | 证据 |
|---|---|---|
| - | - | - |
"""


def plan_template_path():
    return Path(__file__).resolve().parents[1] / "resources" / "skill" / "assets" / "plan.template.md"


def plan_content(plan_slug, title, status, phase, goal):
    goal_text = goal or "待补充。"
    template = plan_template_path().read_text(encoding="utf-8")
    return (
        template.replace("{{title}}", title)
        .replace("{{goal}}", goal_text)
        .replace("{{status}}", status)
        .replace("{{phase}}", phase)
    )


def copy_checker(root, force):
    source = Path(__file__).with_name("check_plan_governance.py")
    target = root / "scripts" / "check_plan_governance.py"
    if source.resolve() == target.resolve():
        target.chmod(0o755)
        return target
    if target.exists() and not force:
        raise FileExistsError(f"{target} 已存在；如需覆盖请加 --force")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    target.chmod(0o755)
    return target


def docs_warnings(root):
    warnings = []
    if not (root / "docs" / "PLAN_MAP.md").exists():
        warnings.append("缺少 docs/PLAN_MAP.md")
    plans_dir = root / "docs" / "plans"
    if not plans_dir.exists() or not any(plans_dir.glob("*.md")):
        warnings.append("缺少 docs/plans/*.md")
    return warnings


def migrate_plan_map_last_updated(root, last_updated):
    plan_map = root / "docs" / "PLAN_MAP.md"
    if not plan_map.exists():
        raise FileNotFoundError("缺少 docs/PLAN_MAP.md")

    text = plan_map.read_text(encoding="utf-8")
    lines = text.splitlines()
    migrated = []
    in_plan_index = False
    changed = False

    for line in lines:
        if re.match(r"^##\s+计划索引\s*$", line):
            in_plan_index = True
            migrated.append(line)
            continue
        if in_plan_index and re.match(r"^##\s+", line):
            in_plan_index = False

        if in_plan_index and line.strip().startswith("|"):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if cells == ["计划", "状态", "当前阶段", "依赖", "证据"]:
                migrated.append("| 计划 | 状态 | 当前阶段 | 最后更新 | 依赖 | 证据 |")
                changed = True
                continue
            if len(cells) == 5 and set(cells) == {"---"}:
                migrated.append("|---|---|---|---|---|---|")
                changed = True
                continue
            if len(cells) == 5:
                cells.insert(3, last_updated)
                migrated.append("| " + " | ".join(cells) + " |")
                changed = True
                continue

        migrated.append(line)

    if changed:
        plan_map.write_text("\n".join(migrated) + ("\n" if text.endswith("\n") else ""), encoding="utf-8")
    return plan_map, changed


def upgrade_existing(root):
    written = [
        copy_checker(root, force=True),
        *update_agent_rules(root),
    ]
    return written, docs_warnings(root)


def parse_args(argv):
    parser = argparse.ArgumentParser(description="初始化中文 plan-governance 文档。")
    parser.add_argument("--root", default=".", help="目标仓库根目录，默认当前目录。")
    parser.add_argument("--plan", help="计划文件名或计划标识，例如 api-compat-migration。")
    parser.add_argument("--title", help="计划显示名称，默认使用 --plan。")
    parser.add_argument("--goal", help="计划目标，会写入计划文档。")
    parser.add_argument("--status", default="设计中", choices=sorted(VALID_STATUSES), help="初始状态。")
    parser.add_argument("--phase", default="阶段 0", help="当前阶段名称。")
    parser.add_argument("--copy-checker", action="store_true", help="复制检查脚本到目标仓库 scripts/。")
    parser.add_argument("--update-claude-md", action="store_true", help="创建或更新目标仓库 CLAUDE.md 中的计划治理规则。")
    parser.add_argument("--update-agents-md", action="store_true", help="创建或更新目标仓库 AGENTS.md 中的计划治理规则。")
    parser.add_argument("--update-agent-rules", action="store_true", help="同时创建或更新 CLAUDE.md 和 AGENTS.md 中的计划治理规则。")
    parser.add_argument("--update-claude-md-only", action="store_true", help="只创建或更新 CLAUDE.md，不初始化或覆盖 docs/。")
    parser.add_argument("--update-agents-md-only", action="store_true", help="只创建或更新 AGENTS.md，不初始化或覆盖 docs/。")
    parser.add_argument("--update-agent-rules-only", action="store_true", help="只创建或更新 CLAUDE.md 和 AGENTS.md，不初始化或覆盖 docs/。")
    parser.add_argument("--upgrade-existing", action="store_true", help="升级已有项目的辅助文件：刷新检查脚本和代理规则，不覆盖 docs/。")
    parser.add_argument("--migrate-plan-map-last-updated", action="store_true", help="将旧五列表 PLAN_MAP.md 迁移为包含最后更新的六列表。")
    parser.add_argument("--last-updated-date", default=date.today().isoformat(), help="迁移 PLAN_MAP.md 时填入的最后更新日期，默认今天。")
    parser.add_argument("--force", action="store_true", help="允许覆盖已存在的治理文件。")
    args = parser.parse_args(argv)
    only_modes = [
        args.update_claude_md_only,
        args.update_agents_md_only,
        args.update_agent_rules_only,
        args.upgrade_existing,
        args.migrate_plan_map_last_updated,
    ]
    if sum(bool(mode) for mode in only_modes) > 1:
        parser.error("--update-*-only、--upgrade-existing 和 --migrate-plan-map-last-updated 不能同时使用")
    if not any(only_modes) and not args.plan:
        parser.error("正常初始化必须提供 --plan；已有项目可使用 --update-*-only、--upgrade-existing 或 --migrate-plan-map-last-updated")
    return args


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    root = Path(args.root).expanduser().resolve()

    if args.update_claude_md_only:
        target = update_claude_md(root)
        print(f"已写入：{target}")
        print("CLAUDE.md 已更新；未修改 docs/。")
        return 0

    if args.update_agents_md_only:
        target = update_agents_md(root)
        print(f"已写入：{target}")
        print("AGENTS.md 已更新；未修改 docs/。")
        return 0

    if args.update_agent_rules_only:
        for target in update_agent_rules(root):
            print(f"已写入：{target}")
        print("代理规则已更新；未修改 docs/。")
        return 0

    if args.upgrade_existing:
        written, warnings = upgrade_existing(root)
        for path in written:
            print(f"已写入：{path}")
        for warning in warnings:
            print(f"WARNING: {warning}")
        print("已有项目升级完成；未覆盖 docs/。下一步请运行 plan-governance-cli check .")
        return 0

    if args.migrate_plan_map_last_updated:
        parse_date = date.fromisoformat(args.last_updated_date)
        target, changed = migrate_plan_map_last_updated(root, parse_date.isoformat())
        print(f"已检查：{target}")
        if changed:
            print("PLAN_MAP.md 已迁移为包含最后更新的六列表。")
        else:
            print("PLAN_MAP.md 已是六列表；无需迁移。")
        return 0

    plan_slug = slugify(args.plan)
    title = args.title or plan_slug

    docs = root / "docs"
    plan_map = docs / "PLAN_MAP.md"
    plan_file = docs / "plans" / f"{plan_slug}.md"

    created = []
    git_dir = init_git(root)
    if git_dir is not None:
        created.append(git_dir)

    write_file(plan_map, plan_map_content(plan_slug, title, args.status, args.phase), args.force)
    created.append(plan_map)
    write_file(plan_file, plan_content(plan_slug, title, args.status, args.phase, args.goal), args.force)
    created.append(plan_file)

    if args.copy_checker:
        created.append(copy_checker(root, args.force))
    if args.update_agent_rules:
        created.extend(update_agent_rules(root))
    else:
        if args.update_claude_md:
            created.append(update_claude_md(root))
        if args.update_agents_md:
            created.append(update_agents_md(root))

    for path in created:
        print(f"已写入：{path}")
    print("初始化完成。下一步请补充计划文档中的 Step 0 证据、验证方式和完成条件。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileExistsError, FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
