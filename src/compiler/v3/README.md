# FREAK V3: Final Self-Hosted Architecture

V3 is FREAK's shipping self-hosted compiler generation. It is the final
compiler built in the original concatenated-source architecture and remains in
the repository as an implementation, compatibility oracle, and historical
record while the V4 Maverick / 00-Unit architecture develops under
`src/compiler/v4/`. The shipping V3 identity also currently reports
`Maverick`; that name overlap is historical, not evidence that V3 and V4 are
the same compiler.

V3 is not frozen merely because this document exists. The intended sequence is
to finish the Last Sortie correctness and release gates, publish the separately
approved final patch release, and only then create an immutable generation
marker such as `compiler-v3-final`. This document neither creates that tag nor
changes the product version.

## Authority and scope

The language specification remains `freak-full-bible.md`; implementation
status and deliberate V4 boundaries remain in `freak-conformance-audit.md`.
This file owns only V3 architecture, reconstruction, preservation tests, and
historical placement. If it conflicts with the bible, the bible wins.

Maintenance work on V3 should preserve behavior it already promises. Suitable
changes are correctness, diagnostics, runtime ownership, pathological
performance, ABI integrity, reproducibility, and release validation. New
syntax, new semantics, new type-system concepts, and backports of the V4
query/IR architecture belong in Maverick instead.

## Architecture

V3 still compiles one flattened FREAK translation unit. Its modularity is a
source-maintenance convention: files are concatenated in dependency order and
use globally unique symbols. The standalone compiler pipeline is:

```text
source bytes
  -> lexer and source map
  -> parser and parallel-array AST
  -> type checker / optional Phase-1 borrow checks
  -> streaming C or LLVM emitter
  -> Clang and the packaged V3 runtime
```

The eight standalone sources have this exact order:

1. `globals.fk`
2. `helpers.fk`
3. `lexer.fk`
4. `parser.fk`
5. `checker.fk`
6. `emit_c.fk`
7. `emit_llvm.fk`
8. `main.fk`

| File | Responsibility |
|---|---|
| `globals.fk` | product/compiler identity, compiler state, tokens, AST tables, source mapping, and backend options |
| `helpers.fk` | shared arrays, diagnostics, source-location helpers, AST allocation, and streaming emit helpers |
| `lexer.fk` | tokenization and lexical diagnostics |
| `parser.fk` | recursive-descent parsing into parallel AST arrays |
| `checker.fk` | type checks, callable/nominal indexes, and opt-in Phase-1 ownership checks |
| `emit_c.fk` | streaming C lowering and C-runtime ownership calls |
| `emit_llvm.fk` | streaming LLVM IR lowering and LLVM runtime bridge calls |
| `main.fk` | standalone `freakc` argument parsing and parse/check/emission gates |

The public `freak`/`hangar` binary embeds the first seven compiler files but
uses the CLI entry point instead of `v3/main.fk`. Its exact aggregate order is:

```text
std/version.fk
src/compiler/v3/globals.fk
src/compiler/v3/helpers.fk
src/compiler/v3/lexer.fk
src/compiler/v3/parser.fk
src/compiler/v3/checker.fk
src/compiler/v3/emit_c.fk
src/compiler/v3/emit_llvm.fk
src/cli/version.fk
src/cli/toml.fk
src/cli/lockfile.fk
src/cli/build.fk
src/cli/run.fk
src/cli/hangar.fk
src/cli/doctor.fk
src/cli/audit.fk
src/cli/main.fk
```

The C and LLVM backends share the runtime contract in `freakc/runtime/`.
Installed builds use the runtime and stdlib selected by the CLI's distribution
resolution rules and require matching `freak-v3-abi-1` markers. The canonical
payload inventory is `packaging/distribution-files.manifest`; repository-local
files are a development fallback, not an installed-program trust source.

## Bootstrap root and fixed point

`build/freakc_v3.fk.c` is the version-controlled bootstrap seed. It is generated
C, but it is intentionally retained so a C compiler can reconstruct V3 without
an older FREAK executable. Treat it as a reviewed root of trust.

The other tracked files beneath `build/`, including `build/freakc_v3.fk`,
`build/freakc_cli.fk`, and native executables, are historical/convenience
artifacts. They are not canonical aggregate source and must not be reused for a
reproducibility claim. `build_cli.bat` is useful for local iteration but also
reuses existing aggregate files and binaries; it is not the clean-room
reproduction procedure.

A valid reconstruction always starts from a clean temporary directory:

```text
checked-in bootstrap C + current runtime -> seed compiler
fresh ordered V3 aggregate -> seed compiler -> generation-1 C -> generation-1 compiler
same aggregate -> generation-1 compiler -> generation-2 C -> generation-2 compiler
same aggregate -> generation-2 compiler -> generation-3 C
generation-2 C == generation-3 C
generation-2 compiler -> fresh CLI aggregate -> freak + hangar
```

The seed is allowed to predate the final source. The byte-for-byte equality of
generation 2 and generation 3 is the self-host fixed-point invariant: the
compiler built from generation 2 must reproduce its own generated C. Native
binary bytes are not expected to match across operating systems, Clang/linker
versions, SDKs, or build paths.

This is an acceptance oracle, not a claim that every development commit has
already converged. A failed comparison, including a stable multi-generation
cycle, blocks the preservation/release gate. Do not select one side of a cycle
and call it reproducible; fix the compiler, review any deliberate seed refresh,
and run the clean reconstruction again before creating the final generation
marker.

The cross-platform automated equivalent is `python -u tests/v3_fixed_point.py`.

### Manual clean reconstruction

Run this from the repository root with Bash, Clang, and Python available. Git
for Windows supplies the Bash used by the project's Windows CI. The recipe
chooses the same platform link libraries as the workflows and writes only to a
new temporary directory.

```bash
set -euo pipefail

repo="$PWD"
raw_work="$(mktemp -d)"
work="$raw_work"
exe=""
link_flags=()
case "${OSTYPE:-}" in
  linux*) link_flags=(-lm) ;;
  msys*|cygwin*)
    work="$(cygpath -m "$raw_work")"
    exe=".exe"
    link_flags=(-lws2_32)
    ;;
  darwin*) ;;
  *) echo "unsupported reproduction host: ${OSTYPE:-unknown}" >&2; exit 2 ;;
esac

compiler_sources=(
  src/compiler/v3/globals.fk
  src/compiler/v3/helpers.fk
  src/compiler/v3/lexer.fk
  src/compiler/v3/parser.fk
  src/compiler/v3/checker.fk
  src/compiler/v3/emit_c.fk
  src/compiler/v3/emit_llvm.fk
  src/compiler/v3/main.fk
)
cat "${compiler_sources[@]}" > "$work/freakc_v3.fk"

clang -o "$work/freakc-seed$exe" \
  "$repo/build/freakc_v3.fk.c" "$repo/freakc/runtime/freak_runtime.c" \
  -I"$repo/freakc/runtime" -O2 -w -D_CRT_SECURE_NO_WARNINGS "${link_flags[@]}"

"$work/freakc-seed$exe" "$work/freakc_v3.fk" --c
mv "$work/freakc_v3.fk.c" "$work/freakc-stage1.c"
clang -o "$work/freakc-stage1$exe" \
  "$work/freakc-stage1.c" "$repo/freakc/runtime/freak_runtime.c" \
  -I"$repo/freakc/runtime" -O2 -w -D_CRT_SECURE_NO_WARNINGS "${link_flags[@]}"

"$work/freakc-stage1$exe" "$work/freakc_v3.fk" --c
mv "$work/freakc_v3.fk.c" "$work/freakc-stage2.c"
clang -o "$work/freakc-stage2$exe" \
  "$work/freakc-stage2.c" "$repo/freakc/runtime/freak_runtime.c" \
  -I"$repo/freakc/runtime" -O2 -w -D_CRT_SECURE_NO_WARNINGS "${link_flags[@]}"

"$work/freakc-stage2$exe" "$work/freakc_v3.fk" --c
mv "$work/freakc_v3.fk.c" "$work/freakc-stage3.c"
cmp "$work/freakc-stage2.c" "$work/freakc-stage3.c"

cli_sources=(
  std/version.fk
  src/compiler/v3/globals.fk
  src/compiler/v3/helpers.fk
  src/compiler/v3/lexer.fk
  src/compiler/v3/parser.fk
  src/compiler/v3/checker.fk
  src/compiler/v3/emit_c.fk
  src/compiler/v3/emit_llvm.fk
  src/cli/version.fk
  src/cli/toml.fk
  src/cli/lockfile.fk
  src/cli/build.fk
  src/cli/run.fk
  src/cli/hangar.fk
  src/cli/doctor.fk
  src/cli/audit.fk
  src/cli/main.fk
)
cat "${cli_sources[@]}" > "$work/freakc_cli.fk"
"$work/freakc-stage2$exe" "$work/freakc_cli.fk" --c
install_home="$work/freak-home"
mkdir -p "$install_home/bin"
clang -o "$install_home/bin/freak$exe" \
  "$work/freakc_cli.fk.c" "$repo/freakc/runtime/freak_runtime.c" \
  -I"$repo/freakc/runtime" -O2 -w -D_CRT_SECURE_NO_WARNINGS "${link_flags[@]}"
cp "$install_home/bin/freak$exe" "$install_home/bin/hangar$exe"

while IFS='|' read -r source destination || [[ -n "$source$destination" ]]; do
  source=${source%$'\r'}
  destination=${destination%$'\r'}
  if [[ -z "$source" || "$source" == \#* ]]; then continue; fi
  mkdir -p "$install_home/$(dirname "$destination")"
  cp "$repo/$source" "$install_home/$destination"
done < "$repo/packaging/distribution-files.manifest"
cp "$repo/packaging/distribution-files.manifest" \
  "$install_home/distribution-files.manifest"

python -u tests/v3_legacy_golden.py "$install_home/bin/freak$exe"
printf 'reconstructed V3 under %s\n' "$work"
```

For a historical reproduction, first check out the approved immutable V3 tag
in detached mode and record the commit ID. Until release approval, use an exact
commit rather than assuming that `compiler-v3-final` exists. Record at least:

- source commit and tag, if any;
- host OS and architecture;
- `clang --version` output;
- SHA-256 of `build/freakc_v3.fk.c`, generation-1 C, generation-2 C,
  generation-3 C, `freak`, `hangar`, and any release archive;
- golden-corpus and final release-gate results.

## Preserved supported surface

V3 preserves the behavior marked as shipping in the bible and conformance
audit, including both native backends, the current standard library payload,
the public build/run/check/transpile/Doctor/upgrade/Hangar CLI, and the
Phase-1 checker selected with `--strict-borrow`. Fatal frontend diagnostics
must stop before emission; preservation tests treat successful bogus output as
a compiler defect, not as compatibility.

The permanent positive corpus is under `tests/v3_legacy/golden/` and is run by:

```text
python -u tests/v3_legacy_golden.py <path-to-real-v3-freak>
```

It exercises deterministic representative programs through C and LLVM. The
broader V3 tests remain responsible for malformed programs, ownership,
performance, ABI mismatch, installation, upgrade, and platform behavior.

## Intentional limitations

- V3 is not the complete future surface described by V4-tagged bible sections.
  New type forms, lifetime concepts, concurrency semantics, macro/query
  architecture, and richer IDE recovery belong in Maverick.
- `--strict-borrow` is an opt-in Phase-1 mutability/move checker, not V4 Meiya.
- The parser supports shipping compilation and limited recovery; it is not an
  incremental or lossless editor parser.
- Source and stdlib inputs are flattened before compilation. V3 has no V4-style
  per-module query graph or IR ownership boundary.
- Generated C is the portable self-host fixed-point artifact. Reproducible
  native bytes require pinning the whole host toolchain and SDK and are not a
  cross-platform promise.
- V3 `std::ui` native execution is limited to the LLVM backend on Windows via
  the Win32/GDI runtime. The C backend may transpile the declarations but does
  not provide executable shape storage for UI programs; there is no macOS or
  Linux native UI backend. `WindowConfig.vsync` is retained but ignored, events
  use the raw indexed runtime API, and COCKPIT is a Maverick source preview.
- `freak test` is a source-checkout development shim that runs
  `python tests/suite/run_tests.py`; the current runner uses the Python
  bootstrap compiler. It is not the V3 preservation corpus and is not proof of
  a standalone release archive.
- The audit subcommands also shell out to `python -m freakc`. They require the
  Python bootstrap package and repository audit inputs; the native V3 binary
  does not contain that auditor.
- Historical generated executables, objects, IR, and aggregate files in the
  repository are evidence of earlier milestones, not canonical release
  payloads. Release archives are defined by the distribution manifest and
  release workflow.

## Historical placement

1. **V1 / FREAK Lite** — `freakc/` is the Python bootstrap compiler. It made
   early language work and C emission practical but implements a smaller
   grammar than the self-hosted compiler.
2. **M15 and V2** — `self_hosted/` records the first Python-to-FREAK
   self-hosting milestone. The compiler sources directly under `src/compiler/`
   are the later V2 generation. V2 proved the self-hosting path, but large
   string-buffer emission, nested dispatch, and monolithic compilation limited
   further growth.
3. **V3** — `src/compiler/v3/` split the compiler into an ordered source set,
   streamed backend output to files, flattened large dispatch paths, and became
   the shipping original-architecture compiler. Its current identity carries
   the `Maverick` name.
4. **V4 Maverick / 00-Unit** — `src/compiler/v4/` reuses the Maverick name for
   the successor compiler architecture and introduces modular crate ownership,
   query-driven compilation, HIR/TY/MIR boundaries, Meiya, snapshots, and editor
   protocols. It is the destination for new semantics; its current bootstrap is
   not permission to delete or silently redefine V3.

`src/compiler/v3-design.md` is retained as the original design record. Its
planned file names and v2-era bootstrap instructions describe the proposal at
the time, not the preserved reconstruction contract above.
