# FREAK Academy

This directory temporarily stages the shared Academy lesson data that the terminal learner, WASM/browser adapter, documentation checks, and the `freaklang.dev` website connector should consume.

Current phase:

- Compiler target: V3 / v0.13.x.
- Repository phase: staged in this repo now, future dedicated FREAK Academy repo later.
- Website target: connector only in `C:\Users\razva\Documents\GitHub\freaklang.dev`.
- Priority after terminal MVP: WASM or browser-safe compiler/interpreter.

Validate the Academy contracts with:

```bash
python tools/academy/validate_academy.py
```

Run the compiler-backed Academy example checks with:

```bash
python tools/academy/check_academy_examples.py
python -m freakc learn check-examples
```

Try the terminal learner with the native CLI:

```bash
build\freak.exe learn list
build\freak.exe learn start hello-freak
build\freak.exe learn status
```

The native CLI currently delegates Learning Mode to the V3-first Python Academy
implementation. The FREAK-native Academy rewrite is planned after the V4 query
surface is ready.

The validator intentionally uses only Python's standard library so it can run in CI before a dedicated Academy toolchain exists.
