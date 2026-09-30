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
python -u -m unittest discover -s tests/v4_differential -p test_run_differential.py
python -u src/compiler/v4/tools/campaign_probe.py --self-test
```

The manifest self-test is compiler-free and exercises rejected schemas. The
unit tests are also compiler-free: fake bounded adapters exercise original-file
edits/deletions, snapshot tampering, byte identity, and source-bound reports. The
probe self-test is executable: it compiles and runs generated probes for an
opaque CRLF/Unicode/control-character source, a syntax negative, and a type
negative. On Windows it prefers `x86_64-w64-mingw32-clang`; an explicit
LLVM-MinGW compiler may be supplied with `--clang`.
The generated program reports both source byte length and the runtime's stable
word checksum; the adapter binds those to the exact requested UTF-8 bytes.

Before either frontend runs, each selected fixture is read exactly once into
an immutable byte buffer and a private, read-only temporary `input.fk`. Both V3
runs and the V4 probe receive that same snapshot, preserving Unicode, CRLF, and
control bytes without text normalization. Later edits or deletion of the
original fixture do not alter the comparison. Each case report includes its
original source label and the SHA-256/byte count of the captured input; V4's
digest, byte count, and checksum are validated against that captured buffer,
never a fresh read of the original fixture.

The harness checks snapshot integrity at adapter boundaries and before/after
each V3 process and the V4 probe process. Missing, replaced-by-nonregular-file,
or changed snapshot bytes are harness errors (exit 2), not expected diagnostics
or compiler mismatches. Read-only files and these checks guard against
accidental writes and persistent tampering; they are not a security sandbox
against a hostile same-user process that swaps and restores input between
checks. The V4 probe itself embeds the captured input once for both of its runs.

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

The declaration corpus adds eight cases to the original four bootstrap cases:

| Family | Cases | Expected frontend result |
|---|---|---|
| Shapes | `aggregates-shape-root-constant`, `aggregates-shape-field-type-mismatch`, `aggregates-shape-missing-field` | Both accept the complete, correctly typed root constructor; both reject the wrong field type and missing field with class `type`. |
| Fieldless routes | `routes-fieldless-legacy-separator`, `routes-repr-discriminant-division` | V3 rejects unsupported declaration syntax; V4 accepts the legacy case separator and represented integer division forms. |
| Invalid discriminant | `routes-repr-zero-divisor` | V3 rejects unsupported parameterized `repr`/variant syntax; V4 rejects the represented zero-divisor expression with class `type`. |
| Generic shapes | `generics-shape-root-constant`, `generics-shape-signature-arity` | V3 rejects generic declaration syntax; V4 accepts the explicit root constructor and rejects a signature supplying only one argument to `Pair<A, B>` with class `type`. |

Shape constructor negatives are root `fixed pilot` initializers so V4 checks
them during TY; ordinary task-body constructor diagnostics may arise later in
MIR and are outside this adapter. The generic arity negative is a signature
contract, and the zero-divisor negative retains `@repr(i32)` to activate the
represented-discriminant validator. V3 rejection classes reflect its shipping
frontend grammar boundary. This compares the acceptance and diagnostic class
of these exact declarations, not general V3/V4 type-semantic parity.

The harness does not inspect the resulting field types, generic substitution
environment, numeric discriminant values, or declaration spans. Those facts
retain their separate V4 semantic smokes. In particular, accepting `A = 4 / 2`
does not by itself prove that its value is `2` or that the following implicit
case has value `3`.

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
