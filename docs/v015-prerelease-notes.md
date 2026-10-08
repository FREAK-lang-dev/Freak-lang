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
`grounded pilot` is a contextual synonym of `fixed pilot`. Ordinary `pilot`
bindings are mutable, including under `--strict-borrow`; `pilot mut` remains a
silent synonym. Words support bytewise UTF-8 ordering without locale rules.
Checked integer arithmetic uses inline fast paths while retaining controlled
failure and evaluation order.

The frozen V4 bootstrap source profile remains separate from current V4
development syntax. Current V4 HIR and MIR snapshots advance to v12 and v10
to retain binding modifiers; older snapshots must be rebuilt. This PR does
not tag or publish a release.
