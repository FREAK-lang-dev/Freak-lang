# FREAK Academy

This directory holds the shared Academy lesson data that the terminal learner, documentation checks, and the `freaklang.dev` website should consume.

Current phase:

- Compiler target: V3 / v0.13.x.
- Repository phase: main repo first, split-ready later.
- Website target: `C:\Users\razva\Documents\GitHub\freaklang.dev`.

Validate the Academy contracts with:

```bash
python tools/academy/validate_academy.py
```

The validator intentionally uses only Python's standard library so it can run in CI before a dedicated Academy toolchain exists.
