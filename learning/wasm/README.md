# FREAK Academy WASM Track

This directory tracks the browser-safe compiler/interpreter work that follows the terminal MVP.

Current status:

- Worker protocol version: 1.
- Lesson package source: `learning/courses`.
- Website consumer: `C:\Users\razva\Documents\GitHub\freaklang.dev` connector only.
- Execution strategy: WASM or browser-safe interpreter, with no server execution for core lessons.

The first artifact is the exportable Academy package:

```bash
python tools/academy/export_academy_package.py --output dist/academy/freak-academy-package.json
```

The same package can be exported through the terminal learner:

```bash
python -m freakc learn package dist/academy/freak-academy-package.json
```

Build the complete browser connector asset set from this repository:

```bash
python tools/academy/build_browser_assets.py dist/academy
python -m freakc learn web-assets dist/academy
```

This writes:

- `freak-academy-package.json`
- `academy-worker.mjs`
- `academy-assets-manifest.json`

The manifest identifies the current worker as `browser-safe-js-reference` and
keeps `wasmStatus` at `pending-v4-compiler-owned-artifact`. When the real WASM
artifact exists, it should replace the worker behind the same manifest and
worker protocol boundary.

Build the first browser-loadable WASM probe:

```bash
python tools/academy/build_wasm_probe.py build/academy-wasm
python -m freakc learn wasm-status build/academy-wasm
node tools/academy/verify_wasm_probe.mjs build/academy-wasm/academy-wasm-probe.wasm
```

The probe is a freestanding `wasm32` artifact built from
`learning/wasm/academy-wasm-probe.c`. It exports protocol/status functions
only. It does not evaluate lessons yet; that remains the next compiler-owned
WASM milestone.

Build the first lesson-capable WASM evaluator:

```bash
python tools/academy/build_wasm_evaluator.py build/academy-wasm
python -m freakc learn wasm-evaluator build/academy-wasm
node tools/academy/verify_wasm_evaluator.mjs build/academy-wasm/academy-wasm-evaluator.wasm
```

This artifact currently supports `hello-freak` and `variables`. The browser
worker accepts it through the `wasmEvaluator` option and falls back to the
JavaScript reference evaluator for the rest of the basics course.

The future worker should accept `schemas/academy-worker-protocol.schema.json` request envelopes and return versioned response envelopes with deterministic evaluation results.

Until the browser/WASM backend exists, use the local V3-backed worker host to exercise the protocol:

```bash
echo '{"protocolVersion":1,"requestId":"req-1","method":"package.info","params":{}}' \
  | python tools/academy/worker_host.py
```

The local host is not the final browser implementation. It is the executable contract that the WASM worker must match.

The first browser-safe reference worker lives at `learning/wasm/academy-worker.mjs`.
It is not the final WASM compiler. It is a small, dependency-free JavaScript
adapter for the current `v3-mvp` basics-course subset so `freaklang.dev` can
integrate against the worker protocol before the compiler-owned WASM artifact
exists.

Run one request through the browser-safe host:

```bash
node tools/academy/browser_worker_host.mjs learning/wasm/fixtures/run_hello.request.json
```

Protocol methods currently exercised by the local host:

- `package.info`
- `check`
- `run`
- `evaluateExercise`
- `cancel`

Golden fixtures live in `learning/wasm/fixtures`:

```bash
python tools/academy/generate_worker_fixtures.py
python tools/academy/verify_worker_fixtures.py
node tools/academy/verify_browser_worker_fixtures.mjs
python tools/academy/verify_worker_parity.py
python -m freakc learn worker-parity
```

The generator uses the native V3-backed worker host as the source of truth and
currently writes package info plus check/run/evaluate fixtures for every lesson
in `freak-basics`. Future WASM/browser workers must match these fixtures before
the website connector depends on them.
