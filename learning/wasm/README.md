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
