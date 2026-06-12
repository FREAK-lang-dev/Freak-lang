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

The future worker should accept `schemas/academy-worker-protocol.schema.json` request envelopes and return versioned response envelopes with deterministic evaluation results.

Until the browser/WASM backend exists, use the local V3-backed worker host to exercise the protocol:

```bash
echo '{"protocolVersion":1,"requestId":"req-1","method":"package.info","params":{}}' \
  | python tools/academy/worker_host.py
```

The local host is not the final browser implementation. It is the executable contract that the WASM worker must match.

Protocol methods currently exercised by the local host:

- `package.info`
- `check`
- `run`
- `evaluateExercise`
- `cancel`
