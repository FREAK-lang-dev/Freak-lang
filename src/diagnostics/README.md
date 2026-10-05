# V3 diagnostic codes and native cast selector

Layout decision: this lives under **`src/diagnostics/`** (not `docs/data`)
because the Python parity oracle (`selector.py`) and generated native data
belong beside the stable code table. Voice lines remain JSON data. Normal
native builds consume the generated FREAK source without Python, JSON parsing,
network access, or dynamic pack loading.

## Contents

| Path | Kind | Purpose |
|---|---|---|
| `codes.json` | data | Stable codes E0001–E0010 (never renamed/renumbered/repurposed) |
| `packs/*.json` | data | Voice packs: FREAK, YUUKO, MEIYA, HANGAR, COCKPIT, MINISTRY, LLVM, LINKER, PLATFORM (platform voices under `platforms`) |
| `easter_eggs.json` | data | Exact-invalid-source easter eggs (byte-exact match only, post-invalid only) |
| `resources.json` | data | Resource companion lines (E0009, normal mode only) |
| `selector.py` | code | Deterministic selector + presentation modes `off`/`minimal`/`normal` |
| `embedded_cast.fk` | generated code | Nine packs, 103 top-level lines, 20 platform lines, exact eggs, resource lines, stable code metadata and pinned Unicode uppercase data |
| `../cli/diagnostic_cast.fk` | native code | SHA-256 selection and append-only presentation |
| `../../tools/embed_diagnostic_cast.py` | build tool | Deterministic embedding; `--check` rejects stale generated source |

## Rules

- Canonical diagnostics are owned by the checker/emitter lanes and are never
  modified here. Explicit mode `off` returns them byte-identical, including
  sized raw source words containing NUL. It performs no selection-key hashing
  or presentation-data lookup.
- The CLI integration contract defaults to `normal` for interactive stdout
  and `off` for redirected stdout and `--json`. An explicit `off` overrides
  the terminal default. Cast text is never added to JSON output.
- Easter eggs replace the pack line only in `minimal`/`normal` mode and only
  on byte-exact match of a registered invalid source. Near-misses never fire.
- Packs are data only: JSON with strings/lists/dicts, no code, no templates
  that execute.

## Native boundary

`cli_diagnostic_cast_suffix(mode, version, code, source_file, line_n,
column_n, source, speaker, platform) -> word` returns only the appended suffix.
`cli_diagnostic_cast_render(canonical, ...) -> word` returns canonical bytes
followed by that suffix. All ordinary `word` parameters transfer ownership;
callers that retain a word pass an explicit owned clone such as `source + ""`.
`cli_diagnostic_cast_mode_valid(mode)` validates the three modes, and
`cli_diagnostic_cast_default_mode(is_json, is_terminal)` implements the terminal
default without probing a terminal itself. Mode names accept ASCII case
variants. Invalid modes must be rejected by the CLI before rendering.

Selection hashes the UTF-8 bytes of seven fields, separated by exactly six
NUL bytes: compiler version, uppercase diagnostic code, source filename,
decimal line, decimal column, full original source, uppercase speaker. It
uses `fs::sha256_bytes` and reduces all 64 hexadecimal digits modulo the
selected line count. Each field participates; this is not a checksum or a
truncated digest. Unicode key uppercase uses a pinned Unicode 15.0.0 full
mapping, including one-to-many expansions, independently of the host C locale.
The generator embeds that checked-in mapping and checks its SHA-256, so
regeneration does not depend on the running Python Unicode version.

Unknown and empty speakers use FREAK's top-level pack. Their original
uppercase key remains in the digest and normal-mode label, matching the
Python selector. A recognized platform subset takes precedence only within
its matching speaker pack; missing or unknown platforms use top-level lines.
Resource lines use the same key with final field `RESOURCES`, and appear only
for `E0009` in `normal` mode. Exact-source Easter eggs are consulted only after
the compiler has already rejected that complete source, never on a valid
program or a near-match.

The compiler owns stable facts and canonical rendering. The CLI owns flag
parsing, terminal detection, original source provenance, platform selection,
and suppression for `--json`. This component gate proves selector behavior;
it does not claim those separate integration hooks have executed.

Regenerate with `python tools/embed_diagnostic_cast.py`. Verify freshness and
data with `python tests/v3_v35_diagnostic_cast.py --static`. Execute the native
parity gate with an explicitly fresh V3 compiler:

```
python tests/v3_v35_diagnostic_cast.py --compiler /path/to/freakc_stage2 \
  --runtime-root /path/to/runtime --clang clang --report /path/to/report.json
```

The gate checks C and LLVM at O0/O2/O3 with strict ownership and runtime owner
audits. `--sanitize --optimization 2` additionally checks ASan/UBSan/function
with a failing sanitizer control. Linux link-time SHA failure controls prove
`off` does not hash; the enabled branch triggers the same trap. Native macOS
and Windows execution remain separate platform gates.
