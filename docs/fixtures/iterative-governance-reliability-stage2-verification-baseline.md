# 持续迭代治理优化：阶段 2 验证入口基线

所属计划：[iterative-governance-reliability](../plans/iterative-governance-reliability.md#当前阶段)。日期：2026-09-06。当前只记录设计基线，尚未获得阶段 2 实施准入。

## 基线类型和限制

- CI 源码基线：`.github/workflows/ci.yml` 只有 Python pytest 与普通治理，没有 Node 回归与显式严格治理。
- 发布源码基线：`scripts/release_npm.mjs` 先切 registry，再执行 npm test；没有 Python 或严格治理检查。
- 替代执行基线：在内存 VM 中执行原发布脚本正文，替换模块导入和全部子进程调用；package 版本与 registry 使用虚构输入。没有真实子进程、registry 修改、版本变更、打包或发布。
- 该回放证明当前控制流，不证明真实发布环境、registry 恢复可靠性或未来统一验证入口已实现。Python/npm/严格治理分别失败的完整矩阵与 CI 对齐验证仍需补齐。

源码身份：`scripts/release_npm.mjs` SHA-256 为 `d7c4cbb7e5e6dc13204d6c4e0d41797dadfdf99be17da9f519596dd32eec7111`；`.github/workflows/ci.yml` 为 `a4da255642dd994d5bce78076907d33a3054b308203a945eca15da8e0ac3b0eb`。后续源码变化须追加新基线，不沿用这份控制流观察。

## 可执行命令

从仓库根目录执行，所有命令均被内存替身拦截，仅打印调用轨迹：

```bash
node --input-type=module <<'JS'
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';
import vm from 'node:vm';
const scriptPath = resolve('scripts/release_npm.mjs');
const source = readFileSync(scriptPath, 'utf8').replace(/^import .*;\n/gm, '').replaceAll('import.meta.url', JSON.stringify(pathToFileURL(scriptPath).href));
for (const scenario of ['success', 'npm-test-fails', 'dry-run']) {
  const trace = [];
  const processStub = { platform: process.platform, argv: ['node', scriptPath, ...(scenario === 'dry-run' ? ['--dry-run'] : []), 'patch'], exitCode: undefined };
  vm.runInNewContext(source, {
    dirname, resolve, fileURLToPath, process: processStub,
    readFileSync: () => '{"version":"0.3.5"}',
    console: { log() {}, error() {} },
    execFileSync(command, args) {
      trace.push([command, ...args]);
      if (command === 'npm' && args.join(' ') === 'config get registry') return 'https://registry.example.invalid/\n';
      if (!['npm', 'nrm'].includes(command)) throw new Error('unexpected command');
      if (scenario === 'npm-test-fails' && command === 'npm' && args[0] === 'test') throw new Error('fixture test failure');
      return '';
    },
  }, { timeout: 1000 });
  console.log(JSON.stringify({scenario, exit: processStub.exitCode, intercepted_commands: trace, real_child_processes: 0}));
}
JS
```

## 实际结果和样本矩阵

2026-09-06 实际执行完成，命令退出 0，三个场景的真实子进程数均为 0。输出在标准输出；结果如下，均为**内存替代基线**：

| 输入 | 当前预期与实际调用顺序 | 流程退出码 | 失败判定 |
|---|---|---|---|
| success：所有替身成功 | 读 registry → 切 npm registry → npm test → version → publish → 恢复 registry | 0 | 顺序不符，或误认为已真实发布 |
| npm-test-fails：npm test 抛出 fixture 错误 | 读 registry → 切 npm registry → npm test 失败 → 恢复 registry；无 version/publish | 1 | 失败后继续版本或发布动作 |
| dry-run | 仅读 registry，不调用切源、测试、version 或 publish | 0 | 出现其他子进程动作 |

后续须在专项计划固定统一验证集合、执行顺序和失败中断矩阵，再由独立复核决定阶段 2 准入。本文件不授权实际发布或修改用户 registry。


## 扩展失败基线与目标矩阵

2026-09-06，独立技术分析者 `/root/stage2_failure_baseline`（不承担本阶段准入/完成复核）完成 20 场景 VM 回放。原源码身份不变，真实子进程、文件写入和网络调用为 0。发现切源部分生效后抛错时，仅发生 get → switch，缺少 restore；version 已变化或远端已接受的模拟失败不会回滚副作用。这些注入说明控制流边界，不说明真实 npm 必然如此。

以下精简命令复现关键扩展场景；使用本文件记录的**实施前源码**，源码改变后应执行实施回归而非把历史轨迹断言用于新行为。输出位置为 stdout，各场景 trace/exit 与下表相反即基线不符。

```bash
node --input-type=module <<'JS'
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';
import vm from 'node:vm';
const scriptPath = resolve('scripts/release_npm.mjs');
const source = readFileSync(scriptPath, 'utf8').replace(/^import .*;\n/gm, '').replaceAll('import.meta.url', JSON.stringify(pathToFileURL(scriptPath).href));
const cases = [
  ['success', {}], ['test', {test:'before'}],
  ['switch-before', {switch:'before'}], ['switch-after', {switch:'after'}],
  ['version-before', {version:'before'}], ['version-after', {version:'after'}],
  ['publish-before', {publish:'before'}], ['publish-after', {publish:'after'}],
  ['restore-before', {restore:'before'}], ['restore-after', {restore:'after'}],
  ['test-restore', {test:'before',restore:'before'}],
  ['get-error', {get:'before'}], ['get-empty', {value:''}], ['get-undefined', {value:'undefined'}],
  ['invalid-flag', {argv:['--oops']}], ['invalid-version', {argv:['next']}],
  ['two-args', {argv:['patch','minor']}], ['dry-run', {argv:['--dry-run','patch']}],
  ['dry-get-error', {argv:['--dry-run','patch'],get:'before'}], ['win32', {platform:'win32'}],
];
for (const [scenario, config] of cases) {
  const trace=[], errors=[];
  const state={registry:'original',version:'original',publication:'absent'};
  const processStub={platform:config.platform??'darwin',argv:['node',scriptPath,...(config.argv??['patch'])]};
  const allowed=new Map([
    ['npm config get registry','get'], ['nrm use npm','switch'], ['npm test','test'],
    ['npm version patch --no-git-tag-version','version'],
    ['npm publish --access public --registry https://registry.npmjs.org/','publish'],
    ['npm config set registry https://registry.fixture.invalid/','restore'],
  ]);
  vm.runInNewContext(source, {
    dirname,resolve,fileURLToPath,process:processStub,
    readFileSync:()=>'{"version":"0.3.5"}', console:{log(){},error(message){errors.push(message)}},
    execFileSync(command,args) {
      const key=[command.replace(/\.cmd$/,''),...args].join(' ');
      const action=allowed.get(key);
      if(!action) throw new Error('unexpected command '+key);
      trace.push(action);
      if(config[action]==='before') throw new Error('fixture '+action+' before');
      if(action==='switch') state.registry='official';
      if(action==='version') state.version='changed';
      if(action==='publish') state.publication='accepted';
      if(action==='restore') state.registry='original';
      if(config[action]==='after') throw new Error('fixture '+action+' after');
      return action==='get' ? (config.value??'https://registry.fixture.invalid/')+'\n' : '';
    },
  },{timeout:1000});
  console.log(JSON.stringify({scenario,exit:processStub.exitCode,trace,state,errors:errors.length,real_child_processes:0}));
}
JS
```

| 场景（合计 20） | 实际轨迹 | 退出码与副作用边界 |
|---|---|---|
| success / win32 | get switch test version publish restore | 0；registry 恢复 |
| test | get switch test restore | 1；无 version/publish，但测试前已经切源 |
| switch-before / switch-after | get switch | 1；均未恢复，after 的模拟 registry 留在 official |
| version-before / version-after | get switch test version restore | 1；无 publish，after 的模拟版本保持 changed |
| publish-before / publish-after | get switch test version publish restore | 1；after 的模拟 publication 保持 accepted |
| restore-before / restore-after | get switch test version publish restore | 1；前者未恢复，后者已恢复但仍报告失败 |
| test-restore | get switch test restore | 1；两条错误均保留 |
| get-error / get-empty / get-undefined | get | 1；无其他命令 |
| invalid-flag / invalid-version / two-args | 空 | 2；参数校验先于子进程 |
| dry-run / dry-get-error | get | 0 / 1；无验证或写动作 |

阶段 2 的新增入口当前不存在，不能声称新三节点失败矩阵已经通过；其可执行命令、预期、失败判定和输出位置冻结于[当前阶段目标矩阵](../plans/iterative-governance-reliability.md#阶段-2-目标验证矩阵)，独立准入后通过新回归兑现。新回归不得直接执行或 import 发布入口，必须替换全部子进程；整个真实 verify 则仍包含既有 npm 打包/临时安装及 pytest 产物，二者的证明边界不同。


## 实施后验证

2026-09-06，阶段 2 独立准入通过后实现，以下为实施者验证声明，尚待独立完成复核。前两节及扩展命令保留实施前观察，新实现不再符合旧缺陷轨迹，复现新行为请运行下面的回归命令。

| 受验证文件 | SHA-256 |
|---|---|
| scripts/verify.mjs | `fbca04629959f57372afb41bc0776ff623d94b566c44e785243e811d374f34ca` |
| scripts/release_npm.mjs | `d746fb669f4aa9148ab515e4489db94732932d66403beb3189c1aefc83444f78` |
| tests/verification_release.test.mjs | `4c6a845d90f12307bb0587aadbc76be5eb331850d6810b83649c54f4fc0b5bb8` |
| .github/workflows/ci.yml | `cf0c5b117591958bcb0adcab2cce200e48ef1a0c7c7e77a6c88c98aec69a5b0b` |
| package.json | `d6d18829d96b010533a4b579d94b77fc9ee26c591c63551898a36d7808f544ad` |

| 实际命令 | 实际结果 | 证据和限制 |
|---|---|---|
| `node --test tests/verification_release.test.mjs` | 57/57 通过，0 skipped | 实施代理工具输出 `0b24e6`；全部发布子进程 VM 拦截 |
| `PYTHONDONTWRITEBYTECODE=1 npm run verify` | 退出 0：严格治理 → Python 203 passed/93.22% → Node 98/98 | 主任务工具输出 `aeb9e0`、`d4e237`；Node 包含前述 57 项及既有临时打包/安装测试 |
| `node --check scripts/verify.mjs`、`node --check scripts/release_npm.mjs` | 退出 0 | 语法验证，不证明运行结果 |
| `PYTHONDONTWRITEBYTECODE=1 node bin/plan-governance-cli.mjs check . --drift` | 退出 0 | 已知宿主阻塞、共享文件和地图归属 WARNING 保留，未扩大覆盖掩盖它们 |
| `PYTHONDONTWRITEBYTECODE=1 plan-governance-cli check .`、`git diff --check` | 退出 0 | 全局 CLI 为已安装旧版本，仅作入口兼容检查；源内严格检查由 verify 实际执行 |

57 项新回归覆盖：12 个三节点 × 非零/error/signal/throw 嵌套失败；缺失解释器及路径有空格；参数拒绝；发布顺序、读取失败、副作用前后失败、主失败与恢复失败；dry-run；两个旧缺陷的内存反向变异；白名单错误不被主流程 catch 吞掉；YAML 解析后的 CI 集合一致性。一项真实 Node 入口测试内含成功及三个失败路径，PATH 仅含临时虚构 npm，PYTHON 是临时虚构可执行路径，检查 argv/cwd/退出码并 finally 清理。没有真实 npm/nrm 发布或 registry 变更；Windows 仅验证 VM 命令选择，未做 Windows 实机验证。

独立完成复核须核对当前内容身份与可执行回归，不能仅依据本表。CI 工作流尚未在 GitHub 运行，也未运行真实发布脚本；本地完整 verify 通过不证明外部发布环境或远端行为。版本保持 0.3.5，锁文件和阶段 1 源码/测试 hash 与阶段 2 进入基线一致。
