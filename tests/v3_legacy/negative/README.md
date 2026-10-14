# V3 negative corpus

These sources record rejection regressions for the registered shipping V3
frontend paths. The forward-constructor case is rejected only by the direct
stage compiler, as documented below. Registered rejection paths verify:

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
proven instance method explicitly. The direct stage compiler's shape constructor
parser remains declaration-order dependent. The public CLI package binder
discovers shape headers before parsing bodies, matching the resolution phases
in Bible §17.4, and accepts forward-declared shape constructors. The unchanged
`forward_shape_constructor.fk` fixture retains its direct C/LLVM parse-error
oracle and artifact-cleanup checks. Its explicit `public_cli: false` metadata
records this front-door distinction; the public gate instead checks acceptance,
both emitters, and native C/LLVM execution of the same forward constructor with
a field-value oracle of `1`. The harness permits no other public CLI exception.
Compiler-internal `shape::alloc/get/set` spellings are not
source builtins. V3 `fs::delete(path)` is the public file-only deletion API on
both backends: it returns `true` after a successful unlink or when the file was
already absent, and `false` on an unlink failure. Compiler/CLI derived-artifact
cleanup checks that result and fails closed.

`manifest.json` is the inventory and diagnostic oracle. Its schema is
`freak-v3-negative-corpus-v1`. Each entry records a unique case name, failure
kind, local `.fk` file, a stable case-insensitive diagnostic fragment, optional
CLI flags, and whether the standalone stage compiler must also reject it. The
optional boolean `public_cli` defaults to `true` and selects public rejection
coverage; its sole documented exception above retains direct-stage coverage.

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
