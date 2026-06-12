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
```

The generator uses the native V3-backed worker host as the source of truth and
currently writes package info plus check/run/evaluate fixtures for every lesson
in `freak-basics`. Future WASM/browser workers must match these fixtures before
the website connector depends on them.
