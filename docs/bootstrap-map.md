# Bootstrap Map (addendum)

A short pointer, not a new authority. For compiler truth, read the two
owner READMEs:

- V3 (shipping self-hosted compiler): [`src/compiler/v3/README.md`](../src/compiler/v3/README.md)
  — architecture, ordered-source reconstruction, preservation boundary.
- V4 Maverick / 00-Unit: [`src/compiler/v4/README.md`](../src/compiler/v4/README.md)
  — bootstrap completion marker, post-bootstrap sequencing, crate ownership.

If this addendum ever disagrees with either README, the README wins.

## Delivery gates

The [release checklist](../src/compiler/v4/RELEASE_CHECKLIST.md) distinguishes
the tier-1 preview, self-hosting, V3 replacement (tiers 1–4 and 8), and complete
bible conformance (tiers 1–8). V3 replacement requires executable parity with
everything V3 ships, a self-hosting fixed point, preservation tests, and the
release tooling gates on the current tree. It does not imply completion of
concurrency or advanced features that V3 never shipped.

## Full conformance sequence (phases A–F)

These phases describe the broader bible-conformance target and its dependency
order. They remain open independently of V3 parity. Verify applicable gates
with `python src/compiler/v4/check_v4.py` plus
`python -u -m freakc audit-conformance`; record executable coverage for each
promoted feature rather than treating those two commands as blanket evidence:

- **A — Semantic core.** Value shapes, variants/routes, aliases, tuple/array
  forms, and generics each land as full vertical slices
  (`lex → parse → HIR → TY → MIR → editor/snapshot/LSP → smokes`).
- **B — Meiya borrow gate.** Ownership, loans, lifetimes, drops, captures,
  and shared ownership close out; the current partial-contract checkpoint in
  the V4 README promotes to a complete gate.
- **C — FFI and systems boundary.** ABI, layout, raw-pointer, and LLVM
  carriage settle on top of stable TY/MIR contracts.
- **D — Concurrency.** `xm3`, `sortie`, `formation`, `briefing room`, and
  `wingman` land only after ownership semantics are coherent.
- **E — Advanced and anime surface.** `mood`, `prob`, `power`, `causality`,
  narrative strictness, and error voices enforced on the stabilized core.
- **F — Backend depth and conformance sweep.** Production codegen parity and
  the conformance sweep promote V4 rows in `freak-conformance-audit.md`
  without overstating coverage; the V3 preservation tests stay green as the
  compatibility oracle.
