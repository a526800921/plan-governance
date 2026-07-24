#!/usr/bin/env node

import { existsSync, readFileSync } from "node:fs";
import { isAbsolute, resolve } from "node:path";
import { spawnSync } from "node:child_process";
import { parse as parseYaml } from "yaml";

const RELATION_TYPES = new Set([
  "contains",
  "orchestrates",
  "exposes",
  "implements",
  "consumes",
  "depends_on",
]);
const ARCHITECTURE_RELATION_TYPES = new Set([
  "contains",
  "exposes",
  "crosses",
  "anchors_to",
  "realized_by",
]);
const NODE_TYPES = new Set([
  "business",
  "function",
  "process",
  "api",
  "external_workflow",
]);
const ARCHITECTURE_NODE_TYPES = new Set([
  "system",
  "module",
  "component",
  "service",
  "interface",
  "data_boundary",
  "trust_boundary",
]);
const EVIDENCE_KINDS = new Set(["document", "code", "test", "api", "gitnexus"]);
const FORWARD_RELATIONS = new Set(["exposes", "implements"]);
const REVERSE_RELATIONS = new Set(["contains", "orchestrates", "consumes", "depends_on"]);

function usage() {
  console.log(`用法：
  plan-governance-cli graph validate [--layer functional|architecture] [root]
  plan-governance-cli graph impact --from <graph-node-id> [--depth 2] [--format text|json] [root]
  plan-governance-cli graph code candidates [--file <relative-path>] --symbol <symbol> --kind class|function [--format text|json] [root]
  plan-governance-cli graph code impact --repo <gitnexus-repo> --file <relative-path> --symbol <symbol> --kind <kind> [--depth 3] [--format text|json] [root]

功能图谱文件：<root>/docs/graph/functional.yaml
架构图谱入口：<root>/docs/graph/architecture/index.yaml`);
}

function error(message) {
  console.error(`graph: ERROR: ${message}`);
  return 1;
}

function graphPath(root) {
  return resolve(root, "docs", "graph", "functional.yaml");
}

function architectureIndexPath(root) {
  return resolve(root, "docs", "graph", "architecture", "index.yaml");
}

function readYamlFile(path, label) {
  if (!existsSync(path)) throw new Error(`缺少${label}：${path}`);
  try {
    return parseYaml(readFileSync(path, "utf8"));
  } catch (cause) {
    throw new Error(`${label} YAML 解析失败：${cause.message}`);
  }
}

function loadGraph(root) {
  const path = graphPath(root);
  const graph = readYamlFile(path, "图谱文件");
  return { graph, path };
}

function asPathList(value, label, issues) {
  if (!Array.isArray(value) || value.length === 0) {
    issues.push(`${label} 必须是非空数组`);
    return [];
  }
  return value.map((entry, index) => {
    if (typeof entry === "string" && entry.length > 0) return entry;
    if (entry && typeof entry.path === "string" && entry.path.length > 0) return entry.path;
    issues.push(`${label}[${index}] 必须是路径字符串或包含 path 的对象`);
    return null;
  }).filter(Boolean);
}

function mergeGraphDocuments(documents) {
  return documents.reduce((merged, document) => ({
    nodes: [...merged.nodes, ...asArray(document.nodes)],
    relations: [...merged.relations, ...asArray(document.relations)],
    codeMappings: [...merged.codeMappings, ...asArray(document.code_mappings)],
  }), { nodes: [], relations: [], codeMappings: [] });
}

function loadReferencedNodeIds(path, label) {
  const document = readYamlFile(path, label);
  const ids = new Set(asArray(document.nodes)
    .map((node) => node?.id)
    .filter((id) => typeof id === "string"));
  if (document.files !== undefined) {
    const issues = [];
    const files = asPathList(document.files, `${label} files`, issues);
    if (issues.length > 0) throw new Error(issues.join("；"));
    files.forEach((relativePath) => {
      const childPath = resolve(path, "..", relativePath);
      loadReferencedNodeIds(childPath, `${label}领域文件`).forEach((id) => ids.add(id));
    });
  }
  return ids;
}

function loadArchitectureGraph(root) {
  const indexPath = architectureIndexPath(root);
  const index = readYamlFile(indexPath, "架构图谱入口");
  const indexIssues = [];
  if (!index || typeof index !== "object" || Array.isArray(index)) {
    throw new Error("架构图谱入口必须是 YAML 对象");
  }
  if (index.schema_version !== 1) indexIssues.push(`架构图谱 schema_version 必须为 1，实际为 ${index.schema_version ?? "<missing>"}`);
  if (index.layer !== "architecture") indexIssues.push(`架构图谱 layer 必须为 architecture，实际为 ${index.layer ?? "<missing>"}`);
  const files = asPathList(index.files, "架构图谱 files", indexIssues);
  const documents = files.map((relativePath) => readYamlFile(resolve(indexPath, "..", relativePath), "架构图谱领域文件"));
  const graph = mergeGraphDocuments(documents);
  const externalIds = new Set();
  const functionalReference = index.references?.functional;
  if (functionalReference !== undefined) {
    const referencePath = typeof functionalReference === "string"
      ? functionalReference
      : functionalReference?.path;
    if (typeof referencePath !== "string" || referencePath.length === 0) {
      indexIssues.push("架构图谱 references.functional 必须包含 path");
    } else {
      loadReferencedNodeIds(resolve(indexPath, "..", referencePath), "功能图谱引用")
        .forEach((id) => externalIds.add(id));
    }
  }
  if (indexIssues.length > 0) throw new Error(indexIssues.join("；"));
  return {
    graph: {
      schema_version: 1,
      nodes: graph.nodes,
      relations: graph.relations,
      code_mappings: graph.codeMappings,
    },
    path: indexPath,
    externalIds,
  };
}

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function validateEvidence(evidence, label, root, issues) {
  if (!Array.isArray(evidence) || evidence.length === 0) {
    issues.push(`${label} 缺少 evidence`);
    return;
  }
  evidence.forEach((item, index) => {
    const prefix = `${label}.evidence[${index}]`;
    if (!item || typeof item !== "object") {
      issues.push(`${prefix} 必须是对象`);
      return;
    }
    if (!EVIDENCE_KINDS.has(item.kind)) issues.push(`${prefix}.kind 不受支持：${item.kind ?? "<missing>"}`);
    if (typeof item.ref !== "string" || item.ref.length === 0) issues.push(`${prefix}.ref 缺失`);
    if (typeof item.locator !== "string" || item.locator.length === 0) issues.push(`${prefix}.locator 缺失`);
    if (typeof item.ref === "string" && item.ref.length > 0 && item.kind !== "gitnexus") {
      const target = isAbsolute(item.ref) ? item.ref : resolve(root, item.ref);
      if (!existsSync(target)) issues.push(`${prefix}.ref 不存在：${item.ref}`);
    }
  });
}

function detectCycles(nodes, relations) {
  const edges = new Map(nodes.map((node) => [node.id, []]));
  relations.forEach((relation) => edges.get(relation.from)?.push(relation.to));
  const visiting = new Set();
  const visited = new Set();
  const cycles = [];

  function visit(node, path) {
    if (visiting.has(node)) {
      const start = path.indexOf(node);
      cycles.push([...path.slice(start), node].join(" -> "));
      return;
    }
    if (visited.has(node)) return;
    visiting.add(node);
    for (const next of edges.get(node) ?? []) visit(next, [...path, node]);
    visiting.delete(node);
    visited.add(node);
  }

  for (const node of edges.keys()) visit(node, []);
  return cycles;
}

function normalizeGraph(raw, root, options = {}) {
  const issues = [];
  const nodeTypes = options.layer === "architecture" ? ARCHITECTURE_NODE_TYPES : NODE_TYPES;
  const relationTypes = options.layer === "architecture" ? ARCHITECTURE_RELATION_TYPES : RELATION_TYPES;
  const externalIds = options.externalIds ?? new Set();
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
    return { issues: ["根文档必须是 YAML 对象"], nodes: [], relations: [] };
  }
  if (raw.schema_version !== 1) issues.push(`schema_version 必须为 1，实际为 ${raw.schema_version ?? "<missing>"}`);
  if (raw.project !== undefined && (!raw.project || typeof raw.project.id !== "string" || typeof raw.project.name !== "string")) {
    issues.push("project.id 和 project.name 必须同时存在且为字符串");
  }
  const nodes = asArray(raw.nodes);
  const relations = asArray(raw.relations);
  const codeMappings = asArray(raw.code_mappings);
  if (nodes.length === 0) issues.push("nodes 不能为空");
  if (!Array.isArray(raw.nodes)) issues.push("nodes 必须是数组");
  if (!Array.isArray(raw.relations)) issues.push("relations 必须是数组");

  const ids = new Set();
  nodes.forEach((node, index) => {
    const label = `nodes[${index}]`;
    if (!node || typeof node !== "object") {
      issues.push(`${label} 必须是对象`);
      return;
    }
    if (typeof node.id !== "string" || node.id.length === 0) issues.push(`${label}.id 缺失`);
    else if (!/^[a-z0-9][a-z0-9-]*(\.[a-z0-9][a-z0-9-]*)*$/.test(node.id)) issues.push(`${label}.id 必须是由 . 分隔、段内仅含小写字母数字和连字符的标识`);
    else if (ids.has(node.id)) issues.push(`节点 ID 重复：${node.id}`);
    else ids.add(node.id);
    if (!nodeTypes.has(node.type)) issues.push(`${label}.type 不受支持：${node.type ?? "<missing>"}`);
    if (typeof node.name !== "string" || node.name.length === 0) issues.push(`${label}.name 缺失`);
    validateEvidence(node.evidence, label, root, issues);
    asArray(node.code_refs).forEach((ref, refIndex) => {
      const prefix = `${label}.code_refs[${refIndex}]`;
      if (!ref || typeof ref !== "object") issues.push(`${prefix} 必须是对象`);
      else {
        if (ref.kind !== "gitnexus_uid") issues.push(`${prefix}.kind 必须为 gitnexus_uid`);
        if (typeof ref.ref !== "string" || ref.ref.length === 0) issues.push(`${prefix}.ref 缺失`);
        if (typeof ref.fallback !== "string" || ref.fallback.length === 0) issues.push(`${prefix}.fallback 缺失`);
        const fallbackIsRoute = typeof ref.fallback === "string" && ref.fallback.startsWith("/");
        if (typeof ref.fallback === "string" && !fallbackIsRoute && !existsSync(resolve(root, ref.fallback))) {
          issues.push(`${prefix}.fallback 不存在：${ref.fallback}`);
        }
      }
    });
  });

  const seenRelations = new Set();
  relations.forEach((relation, index) => {
    const label = `relations[${index}]`;
    if (!relation || typeof relation !== "object") {
      issues.push(`${label} 必须是对象`);
      return;
    }
    const externalFrom = externalIds.has(relation.from);
    const externalTo = externalIds.has(relation.to);
    const allowsExternalFrom = options.layer === "architecture" && relation.type === "realized_by";
    if (!ids.has(relation.from) && !(allowsExternalFrom && externalFrom)) issues.push(`${label}.from 指向悬空节点：${relation.from ?? "<missing>"}`);
    if (!ids.has(relation.to)) issues.push(`${label}.to 指向悬空节点：${relation.to ?? "<missing>"}`);
    if (!relationTypes.has(relation.type)) issues.push(`${label}.type 不受支持：${relation.type ?? "<missing>"}`);
    if (options.layer === "architecture" && relation.type === "realized_by" && !externalFrom) {
      issues.push(`${label}.realized_by.from 必须指向功能图谱引用中的节点：${relation.from ?? "<missing>"}`);
    }
    if (options.layer === "architecture" && relation.type === "realized_by" && externalTo) {
      issues.push(`${label}.realized_by.to 必须指向架构层节点：${relation.to}`);
    }
    if (relation.from === relation.to) issues.push(`${label} 不允许自环：${relation.from}`);
    const key = `${relation.from}|${relation.type}|${relation.to}`;
    if (seenRelations.has(key)) issues.push(`关系重复：${key}`);
    seenRelations.add(key);
    validateEvidence(relation.evidence, label, root, issues);
  });

  if (options.layer === "architecture") {
    if (raw.code_mappings !== undefined && !Array.isArray(raw.code_mappings)) {
      issues.push("code_mappings 必须是数组");
    }
    const seenCodeAnchors = new Set();
    codeMappings.forEach((mapping, index) => {
      const label = `code_mappings[${index}]`;
      if (!mapping || typeof mapping !== "object") {
        issues.push(`${label} 必须是对象`);
        return;
      }
      if (typeof mapping.architecture_id !== "string" || mapping.architecture_id.length === 0) {
        issues.push(`${label}.architecture_id 缺失`);
      } else if (!ids.has(mapping.architecture_id)) {
        issues.push(`${label}.architecture_id 指向悬空架构节点：${mapping.architecture_id}`);
      }
      const anchor = mapping.code_anchor;
      if (!anchor || typeof anchor !== "object") {
        issues.push(`${label}.code_anchor 必须是对象`);
        return;
      }
      if (typeof anchor.file !== "string" || anchor.file.length === 0) {
        issues.push(`${label}.code_anchor.file 缺失`);
      } else {
        const absoluteFile = isAbsolute(anchor.file) ? anchor.file : resolve(root, anchor.file);
        if (!existsSync(absoluteFile)) issues.push(`${label}.code_anchor.file 不存在：${anchor.file}`);
      }
      if (typeof anchor.symbol !== "string" || anchor.symbol.length === 0) issues.push(`${label}.code_anchor.symbol 缺失`);
      if (typeof anchor.kind !== "string" || anchor.kind.length === 0) issues.push(`${label}.code_anchor.kind 缺失`);
      if (anchor.gitnexus_uid !== undefined && (typeof anchor.gitnexus_uid !== "string" || anchor.gitnexus_uid.length === 0)) {
        issues.push(`${label}.code_anchor.gitnexus_uid 必须是非空字符串`);
      }
      if (typeof mapping.architecture_id === "string" && typeof anchor.file === "string"
        && typeof anchor.symbol === "string" && typeof anchor.kind === "string") {
        const key = `${mapping.architecture_id}|${anchor.file}|${anchor.symbol}|${anchor.kind}`;
        if (seenCodeAnchors.has(key)) issues.push(`代码锚点重复：${key}`);
        seenCodeAnchors.add(key);
      }
    });
  }

  return { issues, nodes, relations, codeMappings, meta: raw };
}

function validate(root, layer = "functional") {
  const loaded = layer === "architecture" ? loadArchitectureGraph(root) : loadGraph(root);
  const result = normalizeGraph(loaded.graph, root, { layer, externalIds: loaded.externalIds });
  if (result.issues.length > 0) {
    result.issues.forEach((issue) => console.error(`graph: ERROR: ${issue}`));
    return 1;
  }
  const warnings = [];
  const gitnexusRefs = result.nodes.flatMap((node) => asArray(node.code_refs)
    .filter((ref) => ref.kind === "gitnexus_uid")
    .map((ref) => ({ node, ref })));
  const gitnexusRepo = result.meta.gitnexus?.repo;
  if (gitnexusRefs.length > 0 && existsSync(resolve(root, ".gitnexus")) && gitnexusRepo) {
    for (const { node, ref } of gitnexusRefs) {
      const check = spawnSync("gitnexus", ["context", "-r", gitnexusRepo, "--uid", ref.ref], {
        encoding: "utf8",
        stdio: ["ignore", "pipe", "pipe"],
      });
      if (check.error?.code === "ENOENT") {
        warnings.push("GitNexus CLI 不在 PATH 中，已跳过 UID 实体验证；保留 code_refs.fallback");
        break;
      }
      let contextResult;
      try {
        contextResult = JSON.parse(check.stdout ?? "");
      } catch {
        contextResult = null;
      }
      if (check.status !== 0 || !contextResult || contextResult.status !== "found") {
        const detail = contextResult?.error ?? (check.stderr || `退出码 ${check.status}`);
        result.issues.push(`${node.id}.code_refs GitNexus UID 失配：${ref.ref}；回退：${ref.fallback}`);
        if (detail) result.issues.push(`${node.id}.code_refs GitNexus 响应：${String(detail).trim()}`);
      }
    }
  } else if (gitnexusRefs.length > 0) {
    warnings.push("当前项目没有可用的 .gitnexus 索引，GitNexus UID 标记为待解析；将使用 fallback");
  }
  if (result.issues.length > 0) {
    result.issues.forEach((issue) => console.error(`graph: ERROR: ${issue}`));
    return 1;
  }
  console.log(`${layer === "architecture" ? "架构图谱" : "图谱"}校验通过：${loaded.path}`);
  warnings.forEach((warning) => console.log(`graph: WARNING: ${warning}`));
  const mappingText = layer === "architecture" ? `，代码锚点 ${result.codeMappings.length} 个` : "";
  console.log(`schema_version=1，节点 ${result.nodes.length} 个，关系 ${result.relations.length} 条，GitNexus 引用 ${gitnexusRefs.length} 个${mappingText}`);
  return 0;
}

function parseValidateArgs(args) {
  const options = { layer: "functional", root: process.cwd() };
  const positional = [];
  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--layer") options.layer = args[++index];
    else if (arg === "-h" || arg === "--help") return null;
    else positional.push(arg);
  }
  if (!["functional", "architecture"].includes(options.layer)) {
    throw new Error("validate --layer 只能是 functional 或 architecture");
  }
  if (positional.length > 1) throw new Error("validate 只能接收一个 root 路径");
  if (positional.length === 1) options.root = resolve(positional[0]);
  return options;
}

function parseImpactArgs(args) {
  const options = { from: null, depth: 2, format: "text", root: process.cwd() };
  const positional = [];
  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--from") options.from = args[++index];
    else if (arg === "--depth") options.depth = Number(args[++index]);
    else if (arg === "--format") options.format = args[++index];
    else if (arg === "-h" || arg === "--help") return null;
    else positional.push(arg);
  }
  if (positional.length > 0) options.root = resolve(positional.at(-1));
  if (!options.from) throw new Error("impact 必须指定 --from <graph-node-id>");
  if (!Number.isInteger(options.depth) || options.depth < 1 || options.depth > 10) throw new Error("--depth 必须是 1 到 10 的整数");
  if (!["text", "json"].includes(options.format)) throw new Error("--format 只能是 text 或 json");
  return options;
}

const CODE_FILE_GLOBS = [
  "*.c", "*.cc", "*.cpp", "*.cs", "*.go", "*.h", "*.java", "*.js", "*.jsx",
  "*.kt", "*.m", "*.mm", "*.mjs", "*.php", "*.py", "*.rb", "*.rs", "*.swift",
  "*.ts", "*.tsx",
];

function codeCandidatePattern(kind, symbol) {
  const escaped = symbol.replace(/[\\^$.*+?()[\]{}|]/g, "\\$&");
  const modifiers = "(?:(?:public|private|fileprivate|internal|open|final|static|abstract|sealed|override|async)\\s+)*";
  if (kind === "class") return `^\\s*${modifiers}(?:class|struct|enum|actor|protocol)\\s+${escaped}\\b`;
  if (kind === "function") return `^\\s*${modifiers}(?:func|def|function)\\s+${escaped}\\s*\\(`;
  throw new Error("--kind 首期只能是 class 或 function");
}

function listCodeFiles(root) {
  const args = ["--files", "--hidden", "-g", "!.git", "-g", "!node_modules", "-g", "!.build", "-g", "!dist"];
  CODE_FILE_GLOBS.forEach((glob) => args.push("-g", glob));
  const result = spawnSync("rg", args, { cwd: root, encoding: "utf8" });
  if (result.error?.code === "ENOENT") throw new Error("候选报告需要 rg，但当前 PATH 中找不到 rg");
  if (result.status === 1) return [];
  if (result.status !== 0) throw new Error(`候选报告无法列出代码文件：${(result.stderr || `退出码 ${result.status}`).trim()}`);
  return (result.stdout ?? "").split("\n").filter(Boolean);
}

function runCodeCandidateSearch(root, options) {
  let files;
  if (options.file && existsSync(resolve(root, options.file))) {
    files = [options.file];
  } else {
    files = listCodeFiles(root);
  }
  if (files.length === 0) return [];

  const args = ["--with-filename", "--no-heading", "--color", "never", "-n", "-e", codeCandidatePattern(options.kind, options.symbol), "--", ...files];
  const result = spawnSync("rg", args, { cwd: root, encoding: "utf8" });
  if (result.error?.code === "ENOENT") throw new Error("候选报告需要 rg，但当前 PATH 中找不到 rg");
  if (result.status > 1) throw new Error(`候选报告搜索失败：${(result.stderr || `退出码 ${result.status}`).trim()}`);
  return (result.stdout ?? "").split("\n").filter(Boolean).map((line) => {
    const firstColon = line.indexOf(":");
    const secondColon = line.indexOf(":", firstColon + 1);
    return {
      file: line.slice(0, firstColon),
      line: Number(line.slice(firstColon + 1, secondColon)),
      symbol: options.symbol,
      kind: options.kind,
    };
  }).sort((left, right) => left.file.localeCompare(right.file) || left.line - right.line);
}

function parseCodeCandidatesArgs(args) {
  const options = { file: null, symbol: null, kind: null, format: "text", root: process.cwd() };
  const positional = [];
  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--file") options.file = args[++index];
    else if (arg === "--symbol") options.symbol = args[++index];
    else if (arg === "--kind") options.kind = args[++index];
    else if (arg === "--format") options.format = args[++index];
    else if (arg === "-h" || arg === "--help") return null;
    else positional.push(arg);
  }
  if (positional.length > 1) throw new Error("code candidates 只能接收一个 root 路径");
  if (positional.length === 1) options.root = resolve(positional[0]);
  if (!options.symbol) throw new Error("code candidates 必须指定 --symbol <symbol>");
  if (!options.kind) throw new Error("code candidates 必须指定 --kind <kind>");
  if (!options.file && options.file !== null) throw new Error("--file 必须指定路径");
  if (!options.format || !["text", "json"].includes(options.format)) throw new Error("--format 只能是 text 或 json");
  if (!existsSync(options.root)) throw new Error(`root 不存在：${options.root}`);
  return options;
}

function codeCandidates(root, options) {
  const candidates = runCodeCandidateSearch(root, options);
  const resolution = candidates.length === 1
    ? "unique_candidate"
    : candidates.length > 1 ? "ask_user" : "no_candidate";
  return {
    schema_version: 1,
    query: { file: options.file, symbol: options.symbol, kind: options.kind },
    resolution,
    candidates,
  };
}

function printCodeCandidatesText(result) {
  console.log(`代码候选报告：${result.query.symbol}（${result.query.kind}）`);
  console.log(`目标文件：${result.query.file ?? "未限定"}`);
  console.log(`resolution: ${result.resolution}`);
  if (result.candidates.length === 0) {
    console.log("候选：\n- 无");
    return;
  }
  console.log("候选：");
  result.candidates.forEach((candidate) => {
    console.log(`- ${candidate.file}:${candidate.line} ${candidate.symbol}（${candidate.kind}）`);
  });
}

function parseCodeImpactArgs(args) {
  const options = { repo: null, file: null, symbol: null, kind: null, depth: 3, format: "text", root: process.cwd() };
  const positional = [];
  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--repo") options.repo = args[++index];
    else if (arg === "--file") options.file = args[++index];
    else if (arg === "--symbol") options.symbol = args[++index];
    else if (arg === "--kind") options.kind = args[++index];
    else if (arg === "--depth") options.depth = Number(args[++index]);
    else if (arg === "--format") options.format = args[++index];
    else if (arg === "-h" || arg === "--help") return null;
    else positional.push(arg);
  }
  if (positional.length > 1) throw new Error("code impact 只能接收一个 root 路径");
  if (positional.length === 1) options.root = resolve(positional[0]);
  ["repo", "file", "symbol", "kind"].forEach((field) => {
    if (!options[field]) throw new Error(`code impact 必须指定 --${field} <value>`);
  });
  if (!Number.isInteger(options.depth) || options.depth < 1 || options.depth > 10) throw new Error("--depth 必须是 1 到 10 的整数");
  if (!options.format || !["text", "json"].includes(options.format)) throw new Error("--format 只能是 text 或 json");
  if (!existsSync(options.root)) throw new Error(`root 不存在：${options.root}`);
  return options;
}

function gitnexusKind(kind) {
  return kind.length > 0 ? `${kind[0].toUpperCase()}${kind.slice(1)}` : kind;
}

function codeImpact(root, options) {
  const args = [
    "impact",
    "--repo", options.repo,
    "--file", options.file,
    "--kind", gitnexusKind(options.kind),
    "--depth", String(options.depth),
    options.symbol,
  ];
  const result = spawnSync("gitnexus", args, { cwd: root, encoding: "utf8" });
  if (result.error?.code === "ENOENT") throw new Error("代码级影响查询需要 GitNexus CLI，但当前 PATH 中找不到 gitnexus");
  if (result.status !== 0) {
    const detail = (result.stderr || result.stdout || `退出码 ${result.status}`).trim();
    throw new Error(`GitNexus 代码级影响查询失败：${detail}`);
  }
  let gitnexusResult;
  try {
    gitnexusResult = JSON.parse(result.stdout ?? "");
  } catch (cause) {
    throw new Error(`GitNexus 代码级影响查询返回了无法解析的结果：${cause.message}`);
  }
  if (gitnexusResult?.error) {
    throw new Error(`GitNexus 代码级影响查询失败：${String(gitnexusResult.error)}`);
  }
  return {
    schema_version: 1,
    query: {
      repo: options.repo,
      file: options.file,
      symbol: options.symbol,
      kind: options.kind,
      depth: options.depth,
    },
    source: "gitnexus",
    result: gitnexusResult,
  };
}

function printCodeImpactText(report) {
  const result = report.result;
  console.log(`代码影响分析：${report.query.file} / ${report.query.symbol}（${report.query.kind}）`);
  console.log(`GitNexus repo：${report.query.repo}，最大 ${report.query.depth} 跳`);
  console.log(`风险：${result.risk ?? "未知"}；影响符号：${result.impactedCount ?? "未知"}`);
  if (result.summary) {
    console.log(`直接：${result.summary.direct ?? 0}；间接：${result.summary.indirect ?? 0}；流程：${result.summary.processes_affected ?? 0}；模块：${result.summary.modules_affected ?? 0}`);
  }
  const processes = (result.affected_processes ?? []).map((item) => item.name).join("、") || "无";
  const modules = (result.affected_modules ?? []).map((item) => item.name).join("、") || "无";
  console.log(`受影响流程：${processes}`);
  console.log(`受影响模块：${modules}`);
}

function impact(root, options) {
  const loaded = loadGraph(root);
  const graph = normalizeGraph(loaded.graph, root);
  if (graph.issues.length > 0) throw new Error(`图谱校验失败，无法分析：${graph.issues.join("；")}`);
  const byId = new Map(graph.nodes.map((node) => [node.id, node]));
  if (!byId.has(options.from)) throw new Error(`未知图谱节点：${options.from}`);
  const edges = new Map(graph.nodes.map((node) => [node.id, []]));
  for (const relation of graph.relations) {
    if (FORWARD_RELATIONS.has(relation.type)) edges.get(relation.from)?.push({ relation, target: relation.to });
    if (REVERSE_RELATIONS.has(relation.type)) edges.get(relation.to)?.push({ relation, target: relation.from });
  }

  const queue = [{ id: options.from, depth: 0, path: [] }];
  const bestDepth = new Map([[options.from, 0]]);
  const results = [];
  while (queue.length) {
    const current = queue.shift();
    if (current.depth >= options.depth) continue;
    for (const edge of edges.get(current.id) ?? []) {
      const nextDepth = current.depth + 1;
      const nextPath = [...current.path, {
        from: current.id,
        type: edge.relation.type,
        to: edge.target,
        evidence: edge.relation.evidence,
      }];
      if (bestDepth.has(edge.target) && bestDepth.get(edge.target) <= nextDepth) continue;
      bestDepth.set(edge.target, nextDepth);
      queue.push({ id: edge.target, depth: nextDepth, path: nextPath });
      results.push({ id: edge.target, depth: nextDepth, node: byId.get(edge.target), evidence: byId.get(edge.target).evidence, path: nextPath });
    }
  }

  return {
    schema_version: 1,
    source: { id: options.from, node: byId.get(options.from) },
    depth: options.depth,
    direct: results.filter((item) => item.depth === 1),
    indirect: results.filter((item) => item.depth > 1),
  };
}

function printText(result) {
  console.log(`影响分析：${result.source.id}（最大 ${result.depth} 跳）`);
  const printGroup = (title, items) => {
    console.log(`${title}：`);
    if (items.length === 0) console.log("- 无");
    for (const item of items) {
      const path = item.path.map((edge) => `${edge.from} -[${edge.type}]-> ${edge.to}`).join("；");
      const pathEvidence = item.path
        .flatMap((edge) => edge.evidence ?? [])
        .map((entry) => `${entry.ref}#${entry.locator}`)
        .join("；");
      console.log(`- ${item.id}（${item.node.type}）：${item.node.name}`);
      console.log(`  路径：${path}`);
      console.log(`  关系证据：${pathEvidence || "-"}`);
      console.log(`  证据：${item.evidence.map((entry) => `${entry.ref}#${entry.locator}`).join("；")}`);
    }
  };
  printGroup("直接影响", result.direct);
  printGroup("间接影响", result.indirect);
}

function main(args) {
  const command = args[0];
  if (!command || command === "--help" || command === "-h") {
    usage();
    return command ? 0 : 1;
  }
  try {
    if (command === "validate") {
      const options = parseValidateArgs(args.slice(1));
      if (options === null) {
        usage();
        return 0;
      }
      return validate(options.root, options.layer);
    }
    if (command === "impact") {
      const options = parseImpactArgs(args.slice(1));
      if (options === null) {
        usage();
        return 0;
      }
      const result = impact(options.root, options);
      if (options.format === "json") console.log(JSON.stringify(result, null, 2));
      else printText(result);
      return 0;
    }
    if (command === "code") {
      if (args[1] === "candidates") {
        const options = parseCodeCandidatesArgs(args.slice(2));
        if (options === null) {
          usage();
          return 0;
        }
        const result = codeCandidates(options.root, options);
        if (options.format === "json") console.log(JSON.stringify(result, null, 2));
        else printCodeCandidatesText(result);
        return 0;
      }
      if (args[1] === "impact") {
        const options = parseCodeImpactArgs(args.slice(2));
        if (options === null) {
          usage();
          return 0;
        }
        const result = codeImpact(options.root, options);
        if (options.format === "json") console.log(JSON.stringify(result, null, 2));
        else printCodeImpactText(result);
        return 0;
      }
      return error(`code 不支持子命令：${args[1] ?? "<missing>"}`);
    }
    return error(`不支持子命令：${command}`);
  } catch (cause) {
    return error(cause.message);
  }
}

process.exitCode = main(process.argv.slice(2));
