# V3.5 LLVM IRBuilder backend

Since 0.16.0, `freak build` and `freak run` lower V3.5 programs straight into
an LLVM module in process, through LLVM's own IRBuilder. The released `freak`
carries LLVM 22.1.8: it verifies the module, runs the `default<O0..O3>`
pipeline, emits an object for the clang target and only asks clang to link.

```
.fk → lexer/parser/checker → emit_llvm.fk ─┬─ ir_* sinks → IRBuilder bridge → object → clang (link)
                                            └─ ir_* sinks → textual .ll (shadow / fallback)
```

## One lowering, two sinks

`src/compiler/v3/emit_llvm.fk` lowers each program once. Every instruction goes
through a small sink task (`ir_call`, `ir_load`, `ir_store`, `ir_int`,
`ir_icmp`, `ir_br`, `ir_label`, `ir_declare`, `ir_begin_function`, ...). The text
sink prints exactly the IR the 0.15 emitter printed. The builder sink calls
`freak_ib2_*` in `src/compiler/v3/llvm_builder/ib_bridge.c`, which resolves the
same operand names (`%t3`, `@g_x`, `@.str.2`, literals) in per-function tables
on top of the LLVM C API.

The textual `.ll` is still written next to the source as a shadow. It is what
these use:

- `--llvm-text` for a single build, or `FREAK_IRBUILDER=off` for a whole shell;
- `--lto=thin|full` and `+03` builds, which link textual IR;
- the automatic fallback when this `freak` has no IRBuilder (source builds of
  the CLI link stubs from `freak_runtime.c`), when a lowering has no builder
  form yet (any raw `llvm_emit_line` in builder mode marks the module), or
  when the bridge reports an error. A bridge error prints one dim line and the
  build continues from the shadow `.ll`.

`FREAK_IRBUILDER_TRACE=1` prints which path a build took. `freak doctor` reports
the backend and the LLVM version, and `freak doctor --json` has
`checks.irbuilder {linked, enabled, llvm}`.

## Target matching

Before emitting, the CLI asks the selected clang (`clang -### -c`) for the
target triple, CPU, target features and relocation model it would use. The
builder's object therefore matches what clang would have produced from the
`.ll`, including PIE on Linux, the macOS deployment triple and the MinGW or
MSVC Windows ABI.

## Release builds

`tools/irbuilder_cli.py` fetches, checks and trims the LLVM release pinned in
`src/compiler/v4/llvm.lock` (shared with the V4 backend) and links the CLI:

- Linux x86-64/arm64 and macOS arm64 link LLVM's static libraries. libstdc++ is
  linked statically on Linux, and `zstd_unavailable.c` replaces LLVM's unused
  zstd dependency. The result only needs libc.
- On Windows, `freak.exe` binds the official `LLVM-C.dll` at run time through a
  generated `LoadLibrary` table. The DLL ships as `runtime/LLVM-C.dll`, so a
  missing DLL only means the text path.

```sh
python3 tools/irbuilder_cli.py fetch --dest .llvm-irbuilder
python3 tools/irbuilder_cli.py link --llvm .llvm-irbuilder \
    --cli-c build/freakc_cli.fk.c --out build/freak
```

## Gate

`tests/v3_irbuilder_differential.py --freak build/freak` builds every corpus
program through the builder and with `--llvm-text`, runs both binaries and
requires identical stdout, stderr and exit status. It also fails on any bridge
error and on any text fallback beyond `--max-fallbacks`. A program whose text
build fails, or whose text binary times out, is skipped. The programs in its
`NONDETERMINISTIC` set (wall-clock or network output) are built both ways but
not run, and are counted as "built only". So the gate compares behavior for
most of the corpus, not all of it, and it fails if no program was compared at
all. The CI lane
"V3.5 IRBuilder differential" runs it on Linux, macOS and Windows, and
`build-and-test` gates on it.

## Writing emitter code

New lowering must use the `ir_*` sinks. A raw `llvm_emit_line` instruction
still works, but it silently moves every module that uses it onto the text
fallback, and the differential gate counts that as a fallback.
