# V3 diagnostic codes + optional cast (additive foundation)

Layout decision: this lives under **`src/diagnostics/`** (not `docs/data`)
because the deterministic selector (`selector.py`) is importable code while
every voice line stays in JSON data files with no execution. Tests import the
selector by file path and read the JSON as data.

## Contents

| Path | Kind | Purpose |
|---|---|---|
| `codes.json` | data | Stable codes E0001–E0010 (never renamed/renumbered/repurposed) |
| `packs/*.json` | data | Voice packs: FREAK, YUUKO, MEIYA, HANGAR, COCKPIT, MINISTRY, LLVM, LINKER, PLATFORM (platform voices under `platforms`) |
| `easter_eggs.json` | data | Exact-invalid-source easter eggs (byte-exact match only, post-invalid only) |
| `resources.json` | data | Resource companion lines (E0009, normal mode only) |
| `selector.py` | code | Deterministic selector + presentation modes `off`/`minimal`/`normal` |

## Rules

- Canonical diagnostics are owned by the checker/emitter lanes and are never
  modified here. Mode `off` (the default) returns them byte-identical.
- Easter eggs replace the pack line only in `minimal`/`normal` mode and only
  on byte-exact match of a registered invalid source. Near-misses never fire.
- Packs are data only: JSON with strings/lists/dicts, no code, no templates
  that execute.

## Integration hook (deferred as one wiring task with code emission)

Checker diagnostics do not yet carry stable codes, so a `--diagnostic-cast`
flag today could not select per-code lines — it would be a placebo. The flag
wiring and the code emission at diagnostic sites land together as one
follow-up: emit the code alongside (never inside) the canonical message so
mode `off` stays byte-identical, then pass `(compiler version, code, file,
line, column, source, speaker)` to `selector.render()` as a post-pass
presentation step only. This lane ships no checker edits and no CLI
flag-parsing edits.
