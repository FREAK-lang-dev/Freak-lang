# V3 negative corpus

These sources are intentionally invalid. They are permanent regression inputs
for the shipping V3 frontend's truthful-failure contract:

- `freak check` reports a counted diagnostic, exits nonzero, and never prints
  `PASSED`;
- C and LLVM transpile/build paths never emit a fresh artifact or binary after
  a lexer, parser, type, or strict-borrow failure;
- a rejected transpile or build removes older `.fk`-derived artifacts so stale
  output cannot be mistaken for the result of the rejected invocation;
- non-`.fk` neighboring files are never treated as compiler-owned cleanup
  targets, and a derived artifact that cannot be removed fails closed;
- standalone-stage type and strict-borrow cases run for both backends, with
  source-aware diagnostic oracles.

The semantic cases cover known and duplicate declaration types, callable and
builtin arity/types, directional `int` to `num` assignment compatibility,
operator domains, exact shape-constructor labels/order, lvalues, return and
entry-point contracts, loop/declaration context, `if`/repeat/training types,
literal-compatible `when` arms, nominal fields/methods, and the word-only V3
array ABI. They also pin same-scope binding uniqueness while preserving nested
lexical shadowing, source-ordered global initialization with fail-closed
forward references and transitive user/impl task dependencies, integer-only
remainder/compound assignment rules, and integer geometry across all raw UI
drawing calls. Shape operator-doctrine
syntax remains fail-closed because V3 does not lower those operators; call the
proven instance method explicitly. Shape constructors remain declaration-order
dependent, and compiler-internal `shape::alloc/get/set` spellings are not
source builtins. V3 `fs::delete(path)` is the public file-only deletion API on
both backends: it returns `true` after a successful unlink or when the file was
already absent, and `false` on an unlink failure. Compiler/CLI derived-artifact
cleanup checks that result and fails closed.

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
Acceptance coverage belongs in the main gate's positive matrices, not in this
directory; those matrices preserve forward calls, associated and instance impl
tasks, exact shape construction, boolean aliases, word concatenation, and
numeric widening, unary-minus numeric `when` literals, prior-global aliases,
and nested lexical shadowing without turning them into negative fixtures.
