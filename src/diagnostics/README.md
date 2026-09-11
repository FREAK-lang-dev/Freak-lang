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

## Integration hook (deferred, lead-owned)

The lead wires an opt-in `--diagnostic-cast=<off|minimal|normal>` CLI flag
(default `off`) at the CLI dispatch boundary at integration time. The
checker/parser/emitters keep emitting canonical diagnostics unchanged and
pass `(compiler version, code, file, line, column, source, speaker)` to
`selector.render()` as a post-pass presentation step only. This lane ships no
checker edits and no CLI flag-parsing edits.
