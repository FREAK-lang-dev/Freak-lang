# freakc_v4 Bootstrap Workspace

This directory is the implementation home for Project 00-Unit, the V4 compiler architecture described in `freakc-v4-00-unit-architecture.md`.

The first landing is intentionally small and isolated from the V3 compiler:

```text
crates/
  freak_span/      source ids, spans, line/column helpers
  freak_diag/      diagnostic encoding and severity helpers
  freak_arena/     append-only word arenas for early compiler storage
  freak_intern/    string interning table
  freak_session/   source database and revision tracking
  freak_lex/       lossless token streams with trivia and diagnostics
  freak_parse/     resilient top-level syntax tree and recovery nodes
  freak_hir/       top-level item lowering and stable def ids
  freak_resolve/   file-local semantic index and duplicate diagnostics
  freak_ty/        item-level signature scaffold
  freak_mir/       empty MIR body/basic-block scaffold for task signatures
  freak_borrowck/  Meiya borrow-check result scaffold
  freak_query/     memoized query cache prototype
  freak_driver/    early driver facade over the V4 services
```

Current FREAK compilation still works best with concatenated source files, so these crates use globally unique `v4_` names and a dependency order that can be flattened by a later bootstrap script:

```text
freak_span -> freak_diag -> freak_arena -> freak_intern -> freak_session -> freak_lex -> freak_parse -> freak_hir -> freak_resolve -> freak_ty -> freak_mir -> freak_borrowck -> freak_query -> freak_driver
```

The boundary shape follows the architecture manifesto even though the initial code uses simple arrays and encoded words. That is deliberate: the first goal is to make the 00-Unit data model executable before replacing the internals with richer shapes, arenas, and persistent caches.

## Checks

Run the V4 bootstrap checks from the repository root:

```powershell
python src/compiler/v4/check_v4.py
```

The harness verifies crate existence/order, ASCII source, individual parser acceptance, flattened-crate type checking, and transpilation of every `src/compiler/v4/tests/*.fk` smoke fixture.
