# 0.15.0 prerelease notes

This is a draft for the future release. `VERSION` remains 0.14.2 until the
separate release preparation and publication gates complete.

## Breaking changes

- A local value shadows a same-named task. Calling that name reports
  `unknown callable 'f': local value shadows this name`; 0.14.2 allowed both.
  Rename the local or call from a scope where the task is visible.
- Unsupported expression-like interpolation bodies now fail instead of
  silently printing. Escape literal braces as `\{` and `\}`.
- A program with `task main()` rejects executable root statements that older
  versions silently skipped. Put those statements inside `main`, or use a
  script without `main` to execute root statements in source order.
- Integer overflow and invalid division/remainder stop with a controlled
  runtime error on both native backends.

## Prerelease compatibility fixes

Scripts without `main` run again; an empty or declaration-only program still
fails, with its entry diagnostic naming the user file. Standalone `give` and
`back` are identifiers; only the same-line `give back` pair is a return keyword.
`grounded pilot` is a contextual synonym of `fixed pilot`, joined only by spaces
or tabs; line breaks, bare CR and comments do not join the pair. Ordinary `pilot`
bindings are mutable, including under `--strict-borrow`; `pilot mut` remains a
silent synonym. Words support bytewise UTF-8 ordering without locale rules.
Checked integer arithmetic uses inline fast paths while retaining controlled
failure and evaluation order.

Cached `freak run` now revalidates the declared package graph before reuse.
Editing a transitive dependency rebuilds the program, and invalid locked or
frozen inputs fail before cached execution. Source edits detected during a
build abort execution and leave no fresh cache record.

Legacy Hangar commands now refuse schema-v2 graph locks, unknown schemas and
malformed or unreadable existing locks before fetching, editing manifests,
removing installed packages or reporting an audit result. Valid legacy locks
and `hangar install freak` remain supported. Graph-aware public Hangar commands
remain a separate prerelease requirement.

The permanent `examples/v35` projects provide a pure library, diamond package
consumer and bounded HTTP/JSON service. `tests/v3_v35_acceptance.py` checks a
supplied extracted archive through public commands on C and LLVM, including
strict response framing, project-test failures and transitive cache freshness.
These are component gates; provisional producer reuse remains explicitly
labelled, and full bootstrap, syntax, platform and release gates stay separate.

The frozen V4 bootstrap source profile remains separate from current V4
development syntax. Development V4 now supports condition-first bool loops
with `while condition` and `repeat while condition`, including existing
break, continue, cleanup and early-return rules. Only exact lowercase `while`
is reserved; supported names such as `While` and `WHILE` are preserved.
Loop headers now distinguish known constructor payload braces from the body,
with Boolean comparison coverage in frontend/MIR/snapshots and separate
native scalar casing/alias/local controls. Aggregate constructors and global
native values retain their existing lowering limits. Counted-loop parity and
ungrouped multiline condition continuation remain separate work.
Completed V4 `when`/`check route` arms now close detached terminal joins while
following source still receives genuine diagnostics. Live fallthrough, loop
targets and strict snapshot checks remain covered; aggregate native lowering
is unchanged.
Current V4 HIR and MIR snapshots advance to v12 and v10
to retain binding modifiers; older snapshots must be rebuilt. This PR does
not tag or publish a release.
