# V3 negative corpus

These sources are intentionally invalid. They are permanent regression inputs
for the shipping V3 frontend's truthful-failure contract:

- `freak check` reports a counted diagnostic, exits nonzero, and never prints
  `PASSED`;
- C and LLVM transpile/build paths never emit a fresh artifact or binary after
  a lexer, parser, type, or strict-borrow failure;
- a rejected transpile preserves an unrelated older artifact at the requested
  output path.

`manifest.json` is the inventory and diagnostic oracle. Its schema is
`freak-v3-negative-corpus-v1`. Each entry records a unique case name, failure
kind, local `.fk` file, a stable case-insensitive diagnostic fragment, optional
CLI flags, and whether the standalone stage compiler must also reject it.

`tests/v3_codegen_error_gate.py` validates that every `.fk` file is listed,
copies each source to an owned temporary directory, and runs all artifact-
producing commands only against that copy. Do not run transpile or build
directly on files in this directory.

When adding a frontend recovery case, add one focused source and one manifest
entry. Prefer the narrowest diagnostic fragment that proves the intended
recovery boundary without coupling the corpus to colors or surrounding prose.
