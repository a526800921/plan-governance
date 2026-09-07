import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import test from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";
import vm from "node:vm";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const verifyPath = join(root, "scripts/verify.mjs");
const releasePath = join(root, "scripts/release_npm.mjs");
const originalRegistry = "https://registry.fixture.invalid/";
const officialRegistry = "https://registry.npmjs.org/";
const strictArgs = ["scripts/check_plan_governance.py", ".", "--strict-readiness"];
const pytestArgs = ["-m", "pytest"];
const successResult = { status: 0, signal: null };
const plain = (value) => JSON.parse(JSON.stringify(value));

// Never import either entry point: release has top-level external side effects.
function scriptBody(path, source = readFileSync(path, "utf8")) {
  const imports = [...source.matchAll(/^import .* from "([^"]+)";\n/gm)];
  assert.ok(imports.length >= 3, "entry point imports must be explicitly intercepted");
  for (const [, module] of imports) {
    assert.ok(["node:child_process", "node:fs", "node:path", "node:url"].includes(module), module);
  }
  const body = source.replace(/^import .* from "[^"]+";\n/gm, "")
    .replaceAll("import.meta.url", JSON.stringify(pathToFileURL(path).href));
  assert.doesNotMatch(body, /\bimport\s*(?:\(|\{|["'])/, "unhandled import in VM fixture");
  return body;
}

function vmHarness(path, options = {}) {
  const violations = [];
  const logs = [];
  const errors = [];
  const processStub = {
    argv: ["fixture-node", path, ...(options.args ?? [])],
    platform: options.platform ?? "linux",
    env: { ...(options.env ?? {}) },
    exitCode: undefined,
  };
  // The scripts catch child-process errors. Keep assertion failures outside that
  // catch boundary, so an unknown command cannot masquerade as an expected error.
  function check(callback) {
    try {
      return callback();
    } catch (error) {
      violations.push(error.message);
      throw error;
    }
  }
  function run(bindings) {
    let thrown;
    try {
      vm.runInNewContext(scriptBody(path, options.source), {
        dirname, resolve, fileURLToPath,
        process: processStub,
        console: {
          log: (...args) => logs.push(args.join(" ")),
          error: (...args) => errors.push(args.join(" ")),
        },
        ...bindings,
      }, { timeout: 1000 });
    } catch (error) {
      thrown = error;
    }
    assert.deepEqual(violations, [], "VM child-process/file contract violation");
    if (thrown) throw thrown;
    return { exit: processStub.exitCode, logs, errors };
  }
  return { check, run };
}

function checkRunOptions(options, capture = false) {
  const actual = plain(options);
  assert.equal(actual.cwd, root);
  assert.ok(actual.shell === undefined || actual.shell === false, "must use direct argv without a shell");
  if (capture) {
    assert.equal(actual.encoding, "utf8");
    assert.ok(actual.stdio === undefined || actual.stdio === "pipe");
  } else {
    assert.equal(actual.stdio, "inherit");
  }
}

function failureResult(mode, code = "EACCES") {
  if (mode === "nonzero") return { status: 7, signal: null };
  if (mode === "signal") return { status: null, signal: "SIGTERM" };
  if (mode === "error") return { status: null, error: Object.assign(new Error(`fixture ${code}`), { code }) };
  if (mode === "throw") throw new Error("fixture thrown spawn failure");
  throw new Error(`unknown failure mode ${mode}`);
}

function runVerify(options = {}) {
  const harness = vmHarness(verifyPath, options);
  const trace = [];
  const npmCommand = options.platform === "win32" ? "npm.cmd" : "npm";
  const interpreters = options.env?.PYTHON ? [options.env.PYTHON] : ["python3", "python"];
  const result = harness.run({
    spawnSync(command, args, runOptions) {
      const action = harness.check(() => {
        checkRunOptions(runOptions);
        const argv = plain(args);
        if (command === npmCommand) {
          assert.deepEqual(argv, ["test"]);
          return "node";
        }
        assert.ok(interpreters.includes(command), `unexpected executable ${command}`);
        if (JSON.stringify(argv) === JSON.stringify(strictArgs)) return "strict";
        assert.deepEqual(argv, pytestArgs);
        return "pytest";
      });
      const call = { action, command, args: plain(args) };
      trace.push(call);
      return options.respond ? options.respond(call, trace) : successResult;
    },
  });
  return { ...result, trace, actions: trace.map((call) => call.action) };
}

function runRelease(options = {}) {
  const harness = vmHarness(releasePath, options);
  const trace = [];
  const state = { registry: "original", version: "original", publication: "absent" };
  const npmCommand = options.platform === "win32" ? "npm.cmd" : "npm";
  const nrmCommand = options.platform === "win32" ? "nrm.cmd" : "nrm";
  const versionInput = (options.args ?? []).find((arg) => arg !== "--dry-run") ?? "patch";
  let reads = 0;
  const commands = new Map([
    [JSON.stringify([npmCommand, ["run", "verify"]]), "verify"],
    [JSON.stringify([npmCommand, ["config", "get", "registry"]]), "get"],
    [JSON.stringify([nrmCommand, ["use", "npm"]]), "switch"],
    [JSON.stringify([npmCommand, ["version", versionInput, "--no-git-tag-version"]]), "version"],
    [JSON.stringify([npmCommand, ["publish", "--access", "public", "--registry", officialRegistry]]), "publish"],
    [JSON.stringify([npmCommand, ["config", "set", "registry", originalRegistry]]), "restore"],
  ]);
  const result = harness.run({
    readFileSync(path, encoding) {
      harness.check(() => {
        assert.equal(path, join(root, "package.json"));
        assert.equal(encoding, "utf8");
      });
      reads += 1;
      if (options.readFailure === reads) throw new Error("fixture package read failure");
      return JSON.stringify({ version: state.version === "original" ? "0.3.5" : "0.3.6" });
    },
    execFileSync(command, args, runOptions) {
      const action = harness.check(() => {
        const found = commands.get(JSON.stringify([command, plain(args)]));
        assert.ok(found, `unexpected executable/argv: ${command} ${JSON.stringify(args)}`);
        checkRunOptions(runOptions, found === "get");
        return found;
      });
      trace.push(action);
      const failure = options.failures?.[action];
      if (failure === "before") throw new Error(`fixture ${action} before failure`);
      if (action === "verify" && options.verify) {
        const verified = options.verify();
        if (verified.exit !== 0) throw new Error("fixture verify failed");
      }
      if (action === "get") return options.registryReturn ?? `${originalRegistry}\n`;
      if (action === "switch") state.registry = "official";
      if (action === "version") state.version = "changed";
      if (action === "publish") state.publication = "accepted";
      if (action === "restore") state.registry = "original";
      if (failure === "after") throw new Error(`fixture ${action} after failure`);
      return "";
    },
  });
  return { ...result, trace, state, reads };
}

test("verify runs strict governance, coverage pytest and Node in order", () => {
  const result = runVerify();
  assert.equal(result.exit, 0);
  assert.deepEqual(result.actions, ["strict", "pytest", "node"]);
  assert.deepEqual(result.trace.map((call) => call.command), ["python3", "python3", "npm"]);
  assert.deepEqual(result.errors, []);
});

for (const stage of ["strict", "pytest", "node"]) {
  for (const mode of ["nonzero", "error", "signal", "throw"]) {
    test(`verify stops on ${stage} ${mode}; nested release performs no registry action`, () => {
      let verified;
      const released = runRelease({ verify() {
        verified = runVerify({ respond: ({ action }) => action === stage ? failureResult(mode) : successResult });
        return verified;
      } });
      assert.equal(verified.exit, 1);
      assert.deepEqual(verified.actions, ["strict", "pytest", "node"].slice(0, ["strict", "pytest", "node"].indexOf(stage) + 1));
      assert.ok(verified.errors.length > 0);
      assert.equal(released.exit, 1);
      assert.deepEqual(released.trace, ["verify"]);
      assert.equal(released.reads, 0);
      assert.deepEqual(released.state, { registry: "original", version: "original", publication: "absent" });
    });
  }
}

test("verify falls back only for a missing default interpreter and reuses its selection", () => {
  const result = runVerify({ respond: ({ command }) => command === "python3" ? failureResult("error", "ENOENT") : successResult });
  assert.equal(result.exit, 0);
  assert.deepEqual(result.trace.map(({ action, command }) => [action, command]), [
    ["strict", "python3"], ["strict", "python"], ["pytest", "python"], ["node", "npm"],
  ]);
});

test("verify reports all default interpreters missing", () => {
  const result = runVerify({ respond: () => failureResult("error", "ENOENT") });
  assert.equal(result.exit, 1);
  assert.deepEqual(result.trace.map((call) => call.command), ["python3", "python"]);
  assert.match(result.errors.join("\n"), /Python/);
});

for (const code of ["ENOENT", "EACCES"]) {
  test(`verify does not replace explicit PYTHON on ${code}`, () => {
    const python = "/fixture folder/python executable";
    const result = runVerify({ env: { PYTHON: python }, respond: () => failureResult("error", code) });
    assert.equal(result.exit, 1);
    assert.deepEqual(result.trace.map((call) => call.command), [python]);
  });
}

test("verify preserves explicit Python executable paths with spaces", () => {
  const python = "/fixture folder/python executable";
  const result = runVerify({ env: { PYTHON: python } });
  assert.equal(result.exit, 0);
  assert.deepEqual(result.trace.map((call) => call.command), [python, python, "npm"]);
});

test("verify never discovers another interpreter after pytest cannot start", () => {
  const result = runVerify({ respond: ({ action }) => action === "pytest" ? failureResult("error", "ENOENT") : successResult });
  assert.equal(result.exit, 1);
  assert.deepEqual(result.trace.map((call) => call.command), ["python3", "python3"]);
});

for (const args of [["--skip-tests"], ["unexpected"], ["--help"]]) {
  test(`verify rejects extra arguments ${JSON.stringify(args)} before commands`, () => {
    const result = runVerify({ args });
    assert.equal(result.exit, 2);
    assert.deepEqual(result.trace, []);
  });
}

test("verify selects npm.cmd on win32 without enabling a shell", () => {
  const result = runVerify({ platform: "win32" });
  assert.equal(result.exit, 0);
  assert.equal(result.trace.at(-1).command, "npm.cmd");
});

for (const platform of ["linux", "win32"]) {
  test(`release verifies before registry access and restores on ${platform}`, () => {
    const result = runRelease({ platform });
    assert.equal(result.exit, 0);
    assert.deepEqual(result.trace, ["verify", "get", "switch", "version", "publish", "restore"]);
    assert.deepEqual(result.state, { registry: "original", version: "changed", publication: "accepted" });
    assert.equal(result.reads, 2);
    assert.deepEqual(result.errors, []);
  });
}

for (const version of ["patch", "minor", "major", "1.2.3", "1.2.3-rc.1+fixture"]) {
  test(`release preserves supported version argument ${version}`, () => {
    const result = runRelease({ args: [version] });
    assert.equal(result.exit, 0);
    assert.deepEqual(result.trace, ["verify", "get", "switch", "version", "publish", "restore"]);
  });
}

for (const action of ["switch", "version", "publish", "restore"]) {
  for (const when of ["before", "after"]) {
    test(`release handles ${action} failure ${when} its simulated side effect`, () => {
      const result = runRelease({ failures: { [action]: when } });
      const until = { switch: ["switch"], version: ["switch", "version"], publish: ["switch", "version", "publish"], restore: ["switch", "version", "publish"] };
      assert.equal(result.exit, 1);
      assert.deepEqual(result.trace, ["verify", "get", ...until[action], "restore"]);
      assert.equal(result.state.registry, action === "restore" && when === "before" ? "official" : "original");
      assert.equal(result.state.version, action === "switch" || (action === "version" && when === "before") ? "original" : "changed");
      assert.equal(result.state.publication, action === "restore" || (action === "publish" && when === "after") ? "accepted" : "absent");
      assert.match(result.errors.join("\n"), new RegExp(`fixture ${action} ${when} failure`));
    });
  }
}

test("release retains primary and restore errors without retries", () => {
  const result = runRelease({ failures: { publish: "after", restore: "before" } });
  assert.equal(result.exit, 1);
  assert.deepEqual(result.trace, ["verify", "get", "switch", "version", "publish", "restore"]);
  assert.match(result.errors.join("\n"), /fixture publish after failure/);
  assert.match(result.errors.join("\n"), /fixture restore before failure/);
  assert.equal(result.state.version, "changed");
  assert.equal(result.state.publication, "accepted");
});

for (const options of [{ failures: { get: "before" } }, { registryReturn: "" }, { registryReturn: "  \n" }, { registryReturn: "undefined\n" }]) {
  test(`release rejects unreadable registry ${JSON.stringify(options)}`, () => {
    const result = runRelease(options);
    assert.equal(result.exit, 1);
    assert.deepEqual(result.trace, ["verify", "get"]);
    assert.equal(result.reads, 0);
  });
}

test("release stops before switching when package version cannot be read", () => {
  const result = runRelease({ readFailure: 1 });
  assert.equal(result.exit, 1);
  assert.deepEqual(result.trace, ["verify", "get"]);
  assert.equal(result.reads, 1);
});

test("release still restores if post-publication package version read fails", () => {
  const result = runRelease({ readFailure: 2 });
  assert.equal(result.exit, 1);
  assert.deepEqual(result.trace, ["verify", "get", "switch", "version", "publish", "restore"]);
  assert.equal(result.state.publication, "accepted");
});

for (const args of [["--unknown"], ["banana"], ["patch", "minor"], ["--dry-run", "bad"]]) {
  test(`release rejects invalid arguments ${JSON.stringify(args)} before verification`, () => {
    const result = runRelease({ args });
    assert.equal(result.exit, 2);
    assert.deepEqual(result.trace, []);
    assert.equal(result.reads, 0);
  });
}

test("release dry-run only reads registry and displays the full intended order", () => {
  const result = runRelease({ args: ["--dry-run", "minor"] });
  assert.equal(result.exit, 0);
  assert.deepEqual(result.trace, ["get"]);
  assert.equal(result.reads, 0);
  const preview = result.logs.filter((line) => line.includes("dry-run:"));
  assert.equal(preview.length, 6);
  for (const [index, expected] of ["npm run verify", "npm config get registry", "nrm use npm", "npm version minor --no-git-tag-version", "npm publish --access public --registry", "恢复 registry"].entries()) {
    assert.ok(preview[index].includes(expected), preview[index]);
  }
});

test("release dry-run reports registry failure without executing verification", () => {
  const result = runRelease({ args: ["--dry-run"], failures: { get: "before" } });
  assert.equal(result.exit, 1);
  assert.deepEqual(result.trace, ["get"]);
});

function replaceOnce(source, before, after) {
  assert.equal(source.split(before).length, 2, "mutation anchor must occur exactly once");
  return source.replace(before, after);
}

test("release assertions reject the old verification-after-switch control flow", () => {
  let source = readFileSync(releasePath, "utf8");
  source = replaceOnce(source, '    if (!options.dryRun) run(npmCommand, ["run", "verify"]);\n', "");
  source = replaceOnce(source, '      run(nrmCommand, ["use", npmRegistry]);', '      run(nrmCommand, ["use", npmRegistry]);\n      run(npmCommand, ["run", "verify"]);');
  const result = runRelease({ source, failures: { verify: "before" } });
  assert.equal(result.exit, 1);
  assert.deepEqual(result.trace, ["get", "switch", "verify", "restore"]);
  assert.throws(() => assert.deepEqual(result.trace, ["verify"]), assert.AssertionError);
});

test("release assertions reject the old restore flag set after switching", () => {
  const source = replaceOnce(readFileSync(releasePath, "utf8"),
    '      restoreRequired = true;\n      run(nrmCommand, ["use", npmRegistry]);',
    '      run(nrmCommand, ["use", npmRegistry]);\n      restoreRequired = true;');
  const result = runRelease({ source, failures: { switch: "after" } });
  assert.equal(result.exit, 1);
  assert.deepEqual(result.trace, ["verify", "get", "switch"]);
  assert.equal(result.state.registry, "official");
  assert.throws(() => assert.deepEqual(result.trace, ["verify", "get", "switch", "restore"]), assert.AssertionError);
});

test("VM harness rejects unknown child commands even if entry point catches them", () => {
  const verifySource = replaceOnce(readFileSync(verifyPath, "utf8"), 'run(npmCommand, ["test"])', 'run(npmCommand, ["publish"])');
  assert.throws(() => runVerify({ source: verifySource }), /VM child-process\/file contract violation/);
  const releaseSource = replaceOnce(readFileSync(releasePath, "utf8"), '["run", "verify"]', '["run", "unexpected"]');
  assert.throws(() => runRelease({ source: releaseSource }), /VM child-process\/file contract violation/);
});

test("VM harness rejects shell execution even if entry point catches it", () => {
  const source = replaceOnce(readFileSync(verifyPath, "utf8"), 'stdio: "inherit"', 'stdio: "inherit", shell: true');
  assert.throws(() => runVerify({ source }), /VM child-process\/file contract violation/);
});

test("package keeps local verification and release commands without npm test recursion", () => {
  const manifest = JSON.parse(readFileSync(join(root, "package.json"), "utf8"));
  assert.equal(manifest.scripts.verify, "node scripts/verify.mjs");
  assert.equal(manifest.scripts["release:npm"], "node scripts/release_npm.mjs");
  assert.match(manifest.scripts.test, /^node --test /);
  assert.ok(manifest.scripts.test.split(/\s+/).includes("tests/verification_release.test.mjs"));
  assert.doesNotMatch(manifest.scripts.test, /scripts\/(?:verify|release_npm)\.mjs|npm\s+(?:run\s+verify|test)/);
  for (const hook of ["pretest", "posttest", "preverify", "postverify"]) {
    assert.equal(manifest.scripts[hook], undefined, `${hook} must not bypass the isolated verification composition`);
  }
});

test("real Node verification entry only executes temporary recording Python and npm fixtures", { skip: process.platform === "win32" }, () => {
  const fixtureRoot = mkdtempSync(join(tmpdir(), "plan-governance-verify-entry-"));
  const bin = join(fixtureRoot, "bin");
  const logPath = join(fixtureRoot, "calls.jsonl");
  const program = join(fixtureRoot, "record-command.mjs");
  const fakePython = join(bin, "python fixture");
  const quote = (value) => `'${value.replaceAll("'", "'\\''")}'`;
  try {
    mkdirSync(bin);
    writeFileSync(program, `import { appendFileSync } from "node:fs";
const [kind, ...args] = process.argv.slice(2);
const action = kind === "npm" ? "node" : args[0] === "-m" ? "pytest" : "strict";
const expected = action === "strict" ? ${JSON.stringify(strictArgs)} : action === "pytest" ? ${JSON.stringify(pytestArgs)} : ["test"];
const exit = JSON.stringify(args) !== JSON.stringify(expected) ? 91 : action === process.env.FIXTURE_FAIL ? 7 : 0;
appendFileSync(process.env.FIXTURE_LOG, JSON.stringify({ action, args, cwd: process.cwd(), exit }) + "\\n");
process.exitCode = exit;
`);
    for (const [path, kind] of [[fakePython, "python"], [join(bin, "npm"), "npm"]]) {
      writeFileSync(path, `#!/bin/sh\nexec ${quote(process.execPath)} ${quote(program)} ${quote(kind)} "$@"\n`, { mode: 0o700 });
    }
    for (const failingStage of ["", "strict", "pytest", "node"]) {
      writeFileSync(logPath, "");
      const result = spawnSync(process.execPath, [verifyPath], {
        cwd: fixtureRoot,
        encoding: "utf8",
        timeout: 15000,
        env: { PATH: bin, PYTHON: fakePython, FIXTURE_LOG: logPath, FIXTURE_FAIL: failingStage },
      });
      assert.equal(result.error, undefined, result.error?.message);
      assert.equal(result.signal, null, result.stderr);
      assert.equal(result.status, failingStage ? 1 : 0, result.stderr);
      const calls = readFileSync(logPath, "utf8").trim().split("\n").filter(Boolean).map((line) => JSON.parse(line));
      const stages = ["strict", "pytest", "node"];
      assert.deepEqual(calls.map((call) => call.action), failingStage ? stages.slice(0, stages.indexOf(failingStage) + 1) : stages);
      for (const call of calls) {
        assert.equal(call.cwd, root, "entry point must ignore caller cwd");
        assert.deepEqual(call.args, call.action === "strict" ? strictArgs : call.action === "pytest" ? pytestArgs : ["test"]);
        assert.equal(call.exit, call.action === failingStage ? 7 : 0);
      }
    }
  } finally {
    rmSync(fixtureRoot, { recursive: true, force: true });
  }
});
