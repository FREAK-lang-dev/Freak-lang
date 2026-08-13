# V3/V4 compile-phase differential harness

This corpus compares the shipping V3 frontend with the V4 bootstrap frontend.
It intentionally stops after V4 TY. The V4 probe program executes only to ask
the compiler crates for diagnostics and phase counts; it never emits, links, or
executes the source program under test.

Run the complete corpus from the repository root:

```powershell
python -u tests/v4_differential/run_differential.py build/freak.exe
```

Run one case or validate the closed manifest without invoking either compiler:

```powershell
python -u tests/v4_differential/run_differential.py build/freak.exe --case compatible-basic-task
python -u tests/v4_differential/run_differential.py --self-test
python -u src/compiler/v4/tools/campaign_probe.py --self-test
```

The manifest self-test is compiler-free and exercises rejected schemas. The
probe self-test is executable: it compiles and runs generated probes for an
opaque CRLF/Unicode/control-character source, a syntax negative, and a type
negative. On Windows it prefers `x86_64-w64-mingw32-clang`; an explicit
LLVM-MinGW compiler may be supplied with `--clang`.
The generated program reports both source byte length and the runtime's stable
word checksum; the adapter binds those to the exact requested UTF-8 bytes.

Each compiler runs twice. Acceptance, normalized diagnostic class, and its own
phase summary must be stable across the two runs. Phase counts are not compared
numerically between V3 and V4 because their representations differ.

Fixture category and compiler relationship are separate strict fields. Every
manifest must contain all four required fixture categories:

- `compatible_positive`: both frontends accept.
- `syntax_negative`: both reject with normalized syntax diagnostics.
- `type_negative`: both reject with normalized type diagnostics.
- `intentional_difference`: the manifest records why the expected outcomes
  differ.

Relationships are `equal`, `v3_only`, `v4_extension`, or
`intentional_divergence`. Every non-equal relationship requires a reason.

The manifest is closed over every `.fk` file below `cases/`. Runtime fields are
rejected while `capabilities.v4_native` is false. Exit values, stdout, stderr,
filesystem effects, ownership/drop observations, object generation, linking,
and target-program determinism therefore remain outside this bootstrap. They
must be added only after a real V4 native source-to-executable adapter exists.

The harness uses isolated temporary directories and applies per-process time,
process-tree memory, and output ceilings. V4 work must still be serialized with
other V4 compiler checks on the same host. The lightweight `V3/V4 frontend
differential` job in V4 CI builds the current V3 CLI in an isolated runner
directory, runs the executable probe contract, and then runs the complete
frontend campaign.
