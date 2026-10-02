# V4 backend checkpoint - 2026-10-02

The profiled token-boundary bottleneck is fixed. V4 now assembles and runs scalar
LLVM modules, including local mutation, scoped bindings, control flow, ordered
short-circuit evaluation, numeric conversions and scalar associated impl tasks.
The W1 follow-up below adds literal `say` and runtime linking. General word
values and compiler self-hosting remain open.

## Scaling evidence

The uninstrumented native C pipeline uses the same 1,403-line input: 200 copies
of the handoff's seven-line task plus `main`. Stage-only timings use the runtime
monotonic clock at generated-C call boundaries, compiled with clang 19 `-O2`.

| Stage | Before | Indexed | Speedup |
| --- | ---: | ---: | ---: |
| HIR | 7.783944 s | 0.007345 s | 1060x |
| TY | 33.445372 s | 0.243043 s | 138x |
| MIR construction | 69.157836 s | 0.141704 s | 488x |

The baseline is `3da4205e85748417b506e1b92e4303dc84b3a6cc`; the index was
introduced in `d3310985ac498d3cec6002d2ddc02d7a92356257`. These are single-run
measurements, not confidence intervals. Every timed/profiled synthetic stage
reported zero diagnostics. Decimal span-range decoding in the larger MIR profile
fell from approximately 117.2 million calls to 27,296.

The lexer decodes span boundaries once, using binary search for ordered streams
and cached linear lookup for unordered restored streams. Parser, HIR, TY and MIR
retain their original start/end boundary contracts. Snapshot vocabulary stays
unchanged. The indexed fixture checks duplicate, malformed, empty, unordered,
restored and reused streams, including extreme offsets.

Doubling the workload still grows TY by 3.79x and MIR by 2.94x; residual quadratic
work remains. Lexer index construction adds linear work. The result proves a fix
for the measured dominant lookup cost, not linear scaling of every stage.

## Executable backend evidence

The registered LLVM gate runs these emitted modules through clang:

| Program | Result |
| --- | --- |
| `fib_collatz.fk` | exit 166 |
| `scalar_locals.fk` | exit 42; parameters, copies, mutation, sibling names, nested loop exits |
| `short_circuit.fk` | exit 42; aborting RHS stays unevaluated, including a later call argument |
| `short_circuit_order.fk` | exit 42; stdout exactly `ABCD` |
| `scalar_numeric.fk` | exit 42; floating and unsigned arithmetic/comparisons |
| `scalar_coercions.fk` | exit 42; conversions at calls, returns and local stores |
| `impl_scalar.fk` | exit 42; associated methods, named arguments and numeric conversion |
| `raw_pointer_coercions.fk` | exit 42; int->tiny pointer write and tiny->int read |
| `hello_world.fk` | exit 0; stdout exactly `Hello, world!\n` |
| `literal_say.fk` | exit 0; exact escapes/UTF-8, argument setup, void entry and source-main calls |

Each program validates/restores MIR before native execution and compares module
text byte for byte after restoration. Scalar storage uses local identities and
private dotted LLVM names. Computed MIR rvalues supply branch conditions. MIR
owns short-circuit CFG and captures operands in evaluation order while preserving
snapshot child-before-parent references.

TY validates impl identities and supplies declared callable facts through MIR.
Ordinary signature IDs remain separate for generic/lifetime/returned-loan
contracts. Unsupported impl borrowed returns fail explicitly. Generic
monomorphization and receiver/aggregate/lend native ABI are outside this proof.

The build tool preserves warnings and stops after the first stage with errors.
Unsupported root declarations therefore fail during parsing before downstream
allocation. Its gates check warning-only native execution, MIR error rejection
and strict root rejection. Host linking is tested; complete cross-platform FFI
ABI behavior is not established.

```sh
python src/compiler/v4/check_v4.py
python src/compiler/v4/check_v4.py --smoke "LLVM module execution"
python -u -m freakc audit-conformance
python tools/release_version.py check
python src/compiler/v4/build_v4.py src/compiler/v4/examples/fib_collatz.fk -o build/v4-demo
```

The full gate passes all 268 executable smokes at the final W1 checkpoint,
including pointer-write, build-tool and literal-word regressions. Conformance
audit passes with one environment
warning: the shipping native CLI is not built in this worktree. The native V4
program tests use the bootstrap build tool and clang.

Independent source review found four scalar issues in the initial patch:
snapshot reference ordering, numeric boundary conversions, floating literal
syntax and warning rejection. All were fixed with executable regressions. Review
of the final pointer-write and early-abort changes found no actionable issue.

## Remaining handoff contracts

| Handoff step | Checkpoint status |
| --- | --- |
| 0: profile | Complete; baseline and after profiles retained |
| 1: locals/conditions | Scalar execution complete |
| 2: module/build command | Scalar host execution complete |
| 3: short circuit | Existing MIR CFG extended for call arguments and ordered operands |
| 4: words/interpolation/runtime | W1 literal say complete; W2/W3/W4 pending |
| 5: runtime root initialization | Explicit bootstrap mode selected; implementation pending |
| 6: impl callable signatures | Declared facts and scalar associated methods complete; broader ABI remains open |
| 7: dogfood | Strict individual-crate diagnostic baseline recorded; self-host compilation pending |

Normal root scope continues to follow bible section 17.4. Bootstrap compatibility
must be explicit and per file, initially exposed by the uncached build pipeline.
Normal driver/editor queries remain strict; their current cache keys do not
include a language mode. The planned module initializer supports one flattened
module, source-ordered scalar/word global initializers and root statements,
followed by an optional zero-parameter user `main`. Runtime import graphs and
aggregate/lend global storage require separate support.

Globals need distinct HIR/TY/MIR identities, global places/reads and a synthetic
void module-init body. They must not be seeded as task locals, which would create
incorrect local moves/drops and break shadowing. Native entry must initialize
arguments and call module initialization once before user main. The handoff's
correction is verified: `freak_llvm_setup_args`, `freak_llvm_say`, and the LLVM
process argument functions are ordinary C in `freak_runtime.c`. Linking both
runtime C files supplies them; comments in `freak_llvm_runtime.c` claiming they
are generated intrinsics are stale. Mode/global facts require
versioned snapshots and rejection of malformed references before mutation.

Words require compiler-owned typed intrinsic contracts. Read-only methods,
comparisons, concatenation and `say` borrow inputs; ordinary word value calls,
assignments and returns retain nonCopy transfer rules. Builtin calls need no
receiver in `lhs` and explicit borrowed argument facts, so Meiya does not move an
observed receiver. The runtime's private word handle ABI is i64; byte-indexed V3
methods must not silently redefine bible character-count/slice semantics.
Literal escape normalization belongs in HIR. Embedded NUL needs sized storage,
and owned temporaries/replacements/exits need cleanup before broader word claims.

A bounded HIR interpolation plan can store packed owner/literal/piece/path-part
rows. Closed Literal/DisplayPath pieces represent normalized ConcatMany and
Display conversions; paths store separate identifier/field components. TY
exposes facts and MIR resolves them at the literal offset, without parsing
braces. Persistence must enforce owner kinds, exact widths, dense unique
ordinals, contained spans, counts and atomic rejection, rebuild derived indexes
and retain query invalidation. Coverage must include malformed/unmatched brace
bodies staying literal, local shadowing, invalid path types, snapshot roundtrip
and source-edit invalidation.

## Individual compiler-crate baseline

These runs intentionally use strict mode on one crate at a time, without its
cross-crate definitions. They inspect compiler diagnostics; they do not verify,
link or run emitted LLVM. Diagnostics are inherited between stages, so columns
are stage totals, not independent defects. Unknown calls and zero codegen
messages do not establish executable support. Missing stage counts mean the
bounded probe did not finish that stage.

The probe compiler was built at `4f895d6`; each input SHA-256 is recorded in
the saved JSON, including the captured working-tree source. Every process has a
2 GiB memory limit. The first seven completed small crates
used a 900-second timeout; later probes use 60 seconds. An initial 900-second
freak_lex probe exceeded 2 GiB during Meiya; the resumed bounded run completed
MIR but timed out in Meiya. These probes overlap the full gate, so elapsed times
are not treated as benchmark results.

| Crate | Parse | MIR | Meiya | Codegen | Probe result |
| --- | ---: | ---: | ---: | ---: | --- |
| freak_span | 2 | 22 | 51 | 0 | counts recorded |
| freak_diag | 8 | 10 | 16 | 0 | counts recorded |
| freak_macro_api | 23 | 28 | 176 | 0 | counts recorded |
| freak_arena | 3 | 3 | 3 | 0 | counts recorded |
| freak_intern | 2 | 2 | 2 | 0 | counts recorded |
| freak_session | 6 | 9 | 15 | 0 | counts recorded |
| freak_target | 32 | 48 | 126 | 0 | counts recorded |
| freak_lex | 45 | 60 | - | - | borrowck timeout |
| freak_parse | 67 | 85 | - | - | borrowck memory limit |
| freak_expand | 13 | 14 | - | - | borrowck timeout |
| freak_hir | 131 | 169 | - | - | borrowck memory limit |
| freak_resolve | 24 | 41 | 129 | 0 | counts recorded |
| freak_ty | 126 | - | - | - | mir memory limit |
| freak_mir | 193 | 239 | - | - | borrowck timeout |
| freak_mir_build | 12 | 17 | 52 | 0 | counts recorded |
| freak_borrowck | 152 | 248 | - | - | borrowck timeout |
| freak_codegen_llvm | 28 | 44 | - | - | borrowck timeout |
| freak_query | 56 | 69 | - | - | borrowck timeout |
| freak_driver | 5 | 5 | 83 | 0 | counts recorded |
| freak_editor | 51 | 102 | - | - | borrowck timeout |
| freak_snapshot | 90 | 150 | - | - | borrowck timeout |
| freak_lsp | 31 | 34 | 144 | 0 | counts recorded |

The first crate, `freak_span`, reports unsupported root pilots and word methods.
The larger strict runs also expose downstream memory/time limits. Those limits
remain visible here; the token index and runnable scalar programs do not prove
self-hosting or bounded error-tolerant Meiya on all compiler crates.

## W1 hello-world follow-up

`examples/hello_world.fk` now builds and prints exactly `Hello, world!\n`, with
exit zero, first verified at 2026-10-02 07:27 UTC. This intentionally narrow
word slice admits only literal `say`.
HIR validates/decodes escapes through a TY facade; MIR uses a `#SayLiteral`
Call with a single static `ConstWord` argument and `void` result. LLVM words
use the private i64 handle ABI, and decoded literal bytes become private,
null-terminated globals. Static literals need no ownership release. Newline,
carriage return, tab, quote, backslash, empty strings, UTF-8, and non-path brace
bodies are supported. Embedded NUL, unsupported escapes, valid interpolation
paths, and nonliteral say fail explicitly. Native module assembly rejects
broader word locals, parameters, returns, and rvalues until W2 cleanup exists.

The native C entry initializes arguments and calls the source FREAK task under
`@freak.user.main`; source calls still target that task. Zero-argument main
returning int or void is supported. The build command links the LLVM adapter
and core runtime, matching the shipping CLI; no runtime-profile or component
link-plan mechanism was added. The suggested runtime-core branch/046147e is
unavailable among local refs, so its design remains a later review item.

MIR uses existing Call/ConstWord wire rows and unchanged snapshot vocabulary.
The reserved intrinsic shape is validated atomically before restore; decoded
bytes survive the existing text escaping. No HIR interpolation plan is added
in W1. W2 ownership/drops, W3 persisted interpolation, W4 character-indexed
methods, and explicit bootstrap root initialization remain open.

The runtime argv reference was also verified independently: linking both C
files prints exactly `from-argv\n` with arguments `from-argv extra`, exit 3.
Clean stage-only follow-up timings at pinned scalar checkpoint `db51c43`:

| Native stage | 703 lines | 1,403 lines | Growth |
| --- | ---: | ---: | ---: |
| Meiya | 0.042133 s | 0.132976 s | 3.16x |
| LLVM lowering | 0.062382 s | 0.205893 s | 3.30x |

Every measured stage reports zero diagnostics; whole-process max RSS stays
below 35 MiB. LLVM lowering includes complete body generation, but excludes
final module assembly and clang/link execution. These are single-run samples.
Follow-up stage-only gprof call counts locate repeated TY signature/alias and
HIR parameter-owner scans. Sampling windows are too short for reliable time
percentages. This clean result does not resolve error-driven individual-crate
blowup; that baseline needs repeating after words and root initialization.

Raw argv verification, timings, stage-only profiles, pinned source copies and
reproduction scripts are in `/workspace/v4-backend-after/words-explorer`.

The focused integrated gate passes the literal/snapshot and module-epoch smokes, LLVM ABI plan
smoke, ten native programs, and the build command's hello-world, warning-only,
nonliteral-say, unsupported-word, main-parameter, MIR-error, and strict-root
checks. Literal delimiter/keyword text is now excluded from structural parsing
and HIR/MIR scans, so strings like `"{"`, `";"`, or `"pilot"` retain their bytes.
This preserves the MIR builder's existing token-kind allowlist.

Independent review found three W1 issues: text-only keyword dispatch for an
ordinary `"say"` expression, mixed old body/new literal facts after MIR restore,
and duplicate explicit runtime declarations. The fixes require a keyword token,
seal all module facts at lowering, and share compatible runtime declarations
while rejecting incompatible emitted symbols (including link-name aliases).
Regressions cover each case; imported NUL text fails native emission without
changing previously sealed plans.

Final executable validation is tied to
`66f9558a0dc31c83d57ed9c84537848c9b2dc4b1`: all 268 registered runtime smokes,
ten native LLVM programs, and the build-command gates passed with clang 19 on
x86_64 Linux. Peak retained runner memory was 73.9 MiB against its 256 MiB
limit. Conformance audit and the 0.14.2 release-version invariant passed;
the audit retains only the existing missing-shipping-CLI warning.

Both independent reviewers cleared that SHA, including the tests/docs-only
delta from `6154f23`. The first broad run exposed old fixtures that ignored
nonliteral `say` inside checked/guarded arms. Their source programs and original
diagnostic assertions remain intact; exact counts and messages now cover all
nine added W1 rejection diagnostics across three fixtures. The final full run
passes those checks. Windows/macOS native linking remains unverified.

The final full log is
`/workspace/v4-backend-after/w1-final-full-v4-check-66f9558.log`.
Independent review disposition is saved in
`/workspace/v4-backend-after/w1-review/FINAL_VERDICT.md`.
The delivered binary is `/workspace/v4-native/hello-world-v4`, with LLVM text
beside it and exact-output/provenance verification in
`/workspace/v4-backend-after/hello-world-verification.json`.

## Saved measurement artifacts

The workspace retains the handoff probe inputs, generated C, instrumentation,
raw timing JSON and stage-only gprof output outside the repository:

- `/workspace/v4-backend-profile`: unchanged baseline and Appendix B report.
- `/workspace/v4-backend-after`: indexed timing comparison, verification logs.
- `/workspace/v4-backend-dogfood`: strict crate probe, guarded runner and counts.

Reproduction scripts assert generated-C instrumentation points and compile
separate timed and `-pg` binaries. gprof sampling/call counting is enabled only
around the selected HIR/TY/MIR, Meiya, or LLVM lowering stage via `moncontrol`.
Synthetic files contain
703/1,403 lines. Timed and profiling jobs run sequentially, with process-tree
monitoring and fixed time/memory budgets.
