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
V3 observations require the shipping `check` command's ordered completed-phase
markers and matching terminal success or syntax/type failure, with a consistent
exit status. Empty/no-op output, incomplete or duplicated phases, and generic
tool failures never count as successful compilation or expected syntax errors.
Both glyph and ASCII CLI output modes are accepted; timings are not compared.

Fixture category and compiler relationship are separate strict fields. Every
manifest declares the complete ordered category vocabulary, including phased
categories that do not have a fixture yet:

- Frontend bootstrap: `compatible`, `v4_extension`, and `negative`.
- Semantic expansion: `intentional_divergence`, `ownership`, `closures`,
  `aggregates`, `routes`, and `generics`.
- Native runtime: `control_flow` and `std_smoke`.

An unpopulated phased category must explicitly set `allow_empty` to `true`;
populated categories must set it to `false`. `compatible` accepts on both
frontends, `negative` rejects on both (with the expected diagnostic class), and
the two difference categories require their matching relationship.

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
