---
name: plan-governance-migration
description: Migrate existing flat docs/plans/*.md files into date directories when the user explicitly requests migration, preserving plan history and repairing references.
---

# 计划日期目录迁移

仅在用户明确要求迁移存量计划时使用。计划目录存在或主治理 skill 已升级，都不构成迁移授权。日常治理只读取索引路径，不主动搬动计划。

迁移前读取项目 `AGENTS.md`、`docs/PLAN_MAP.md`、受影响计划和适用的 plan-governance verification 规则。先检查工作区差异、地图登记、所有平铺计划、目标路径占用、Markdown 引用和 attestation；建立源路径、目标路径、创建日期及引用影响清单，并先报告无法确定的日期或歧义。日期优先取 Git 首次添加记录；仅当正文明确记录创建日期时才可回退使用该日期。不得用修改时间或最后更新日期猜测。路径冲突、未登记文件、无法解析的日期或会丢失的本地修改未解决前，不移动文件。

迁移时保留计划内容、文件名、身份、状态、阶段和历史证据。按核对后的清单移动到 `docs/plans/YYYYMMDD/<slug>.md`，同步 `PLAN_MAP.md`、指向这些计划的文档链接，以及因源文件层级变化而失效的相对 Markdown 链接。保留锚点；计划链接按原目标重新计算相对路径。代码块中的示例路径不视为引用。不要改写旧 attestation；检查其计划路径、地图 hash 和替代关系。若不能用项目 CLI 建立可信后继快照，保留旧快照并报告 `needs_review`，不要手改 JSON 来制造通过状态。

每批迁移都先保存可逆的源/目标映射。完成后确认源路径已清空、目标文件各出现一次、索引路径准确、所有受影响本地链接可达，且 checker、workset 和 attestation 检查符合项目规则。任一检查失败时停止，并依据映射恢复文件和引用；报告实际恢复范围及仍未解决的项目。只处理用户授权的仓库与计划范围，不安装依赖、不发布、不触碰其他项目。
