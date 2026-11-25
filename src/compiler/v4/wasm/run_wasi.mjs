// Run a FREAK wasm32-unknown-wasip1 module under Node's WASI preview 1.
//   node --no-warnings run_wasi.mjs program.wasm [args...]
// The module's exit status becomes this process's. A trap (abort, an
// unreachable, an out-of-bounds access) exits with 134, the status a native
// SIGABRT gives through a shell; set FREAK_WASI_TRACE=1 to print the trap.
import { readFile } from 'node:fs/promises';
import { WASI } from 'node:wasi';
import { argv, env, exit, stderr } from 'node:process';

const [path, ...args] = argv.slice(2);
if (!path) {
  stderr.write('usage: run_wasi.mjs program.wasm [args...]\n');
  exit(2);
}
const wasi = new WASI({ version: 'preview1', args: [path, ...args], env: {}, returnOnExit: true });
const module = await WebAssembly.compile(await readFile(path));
const instance = await WebAssembly.instantiate(module, wasi.getImportObject());
let code;
try {
  code = wasi.start(instance);
} catch (error) {
  if (env.FREAK_WASI_TRACE) stderr.write(`wasm trap: ${error.message}\n`);
  code = 134;
}
exit(code);
