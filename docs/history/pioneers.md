# Pioneers

A short history of the FREAK compiler generations — the pioneers, in the
structural sense: each generation made the next one possible. No personal
attribution is attempted here; the commit history is the authorship record
(see `AUTHORS.md`). AI-assisted contributions are part of this project's
story and are disclosed there, not mythologized here.

## Generation 0 — Python bootstrap ("FREAK Lite")

The Python compiler under `freakc/` proved the language could exist: lexer,
parser, type checker, C emitter, and the audit suite. It remains the
development bootstrap and the source-checkout audit runner
(`python -m freakc audit-conformance`). It accepts a smaller language subset
than V3 — that divergence is documented in `freak-conformance-audit.md`, not
hidden.

## Generation 1 — V3 self-hosted compiler

FREAK learned to compile itself. The eight-file concatenated-source compiler
under `src/compiler/v3/` emits LLVM IR (default) and C (portability target)
and links native binaries via Clang. V3 is the **shipping** compiler:
actively hardened, **not stable** (see `README.md` project status). Its
architecture, reconstruction procedure, and preservation boundary are owned by
`src/compiler/v3/README.md`.

## Generation 2 — V4 Maverick / 00-Unit (in progress)

The modular, query-backed rewrite under `src/compiler/v4/`: resilient
parsing, HIR/TY/MIR layers, the Meiya borrow checker, editor/snapshot/LSP
protocols. The executable 00-Unit bootstrap slice is complete, but V4 is not
yet a V3 replacement. Its architecture and sequencing are owned by
`src/compiler/v4/README.md`; the self-host exit checklist (phases A–F) is
summarized in `docs/bootstrap-map.md`.

## What "pioneer" means here

Each generation is preserved, not erased: V3 stays in-tree as implementation,
compatibility oracle, and historical record while V4 develops. The rule for
future pioneers is the same — land the replacement before retiring the road
that carried you.
