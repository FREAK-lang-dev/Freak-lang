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

Each compiler runs twice. Acceptance, normalized diagnostic class, and its own
phase summary must be stable across the two runs. Phase counts are not compared
numerically between V3 and V4 because their representations differ.

The manifest taxonomy is strict:

- `equal`: both frontends have the same accepted/class outcome.
- `negative`: both reject with the same diagnostic class.
- `v3_only`: V3 accepts and V4 rejects for an explicit reason.
- `v4_extension`: V4 accepts and V3 rejects for an explicit reason.
- `intentional_divergence`: both expected observations and an explicit reason
  document a deliberate difference.

The manifest is closed over every `.fk` file below `cases/`. Runtime fields are
rejected while `capabilities.v4_native` is false. Exit values, stdout, stderr,
filesystem effects, ownership/drop observations, object generation, linking,
and target-program determinism therefore remain outside this bootstrap. They
must be added only after a real V4 native source-to-executable adapter exists.

The harness uses isolated temporary directories and applies time, process-tree
memory, and output ceilings. V4 work must still be serialized with other V4
compiler checks on the same host.
