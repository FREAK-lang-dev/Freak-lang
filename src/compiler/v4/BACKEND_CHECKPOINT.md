# V4 backend checkpoint - 2026-10-02

Handoff 6 fixes nested counted loops, literal grammar scans, boolean aliases,
and indirect callback calls. Unsupported native MIR now receives named errors;
diagnostic restoration and source-loading failures preserve live state. The
handoff 4 memory and handoff 5 lookup results remain the measured scaling
checkpoints below. This scalar backend still leaves general word ownership,
aggregate layout, target-width C ABI fidelity, and compiler self-hosting open.

## Handoff 6: correctness

The pinned integration base is `5cb1d2b2ad1653efc5b116a8a6e3d03bf371b85c`.
Baseline reproduction uses the frozen handoff-5 compiler at
`3db07fb68e8d370fef3551d074c843418ce4e705`, whose compiler sources match that
base. These x86_64 Linux cases reproduce the handoff's five REAL findings:

| Finding | Baseline evidence | Current behavior and regression |
|---|---|---|
| F02, nested counted loops | Three levels returned 8 instead of 24; four returned 4 instead of 16 | Every counted loop allocates a fresh local identity. Native checks cover depths 3/4/5, siblings, source-name collisions, break and continue. |
| F03, literal delimiters | `two(",", ")")` falsely reports three arguments | Structural token readers exclude String/Char payloads. Frontend and MIR checks preserve delimiter/keyword/operator data in lists, tuples, arrays, maps, constructors, calls, returns, conditions and compact patterns. Raw display text stays intact. |
| F04, empty callback arguments | LLVM repeats a callee SSA definition and passes it to itself | The callee is separate from the argument list and computed targets become MIR children. Native zero/one/multiple-argument callbacks, local and returned targets execute; the producer prints exactly once per evaluation. Unsupported field callbacks are fenced. |
| F06, boolean aliases | `ret i1 yes` fails clang verification | MIR stores canonical true/false; Codegen also normalizes older restored aliases. Eighteen lower/upper/title-case spellings execute as returns, locals, arguments and conditions. Reserved literal spellings diagnose at parameter/local declarations. |
| F08, unsupported native facts | Shape/field code emits an undefined `%P` layout | Codegen seals named errors before assembling bodies. Checks reject 23 unsupported rvalue kinds, three place kinds, 14 type families, incompatible literal types and malformed references, including restored facts; no module is returned. |
| F09, diagnostic restore storage | Replacement children were abandoned in source | Direct replacements release old children; whole v1 restore stages an overlay and publishes atomically. 600 direct and 600 whole restores keep handle capacity stable. Exhaustion/partial failures preserve live bytes and recover; sparse, dense and duplicate-order cases retain validation semantics. |
| F10, source reads and executable entry | Driver confuses empty contents with an I/O error | Checked bootstrap reads accept empty regular files and return errors for failed/nonregular reads before source/query publication. File APIs retain cached/live facts on failure. Executable builds require main; library Codegen can omit it. |

F10's missing-file build claim is stale at this pinned base: Python already
rejects non-files and the old C read helper exits on open failure. The new helper
provides an explicit error result for the driver and bootstrap tool, including
metadata, seek/tell, short-read, allocation and close failures. Its C fault
fixture checks nine injected faults and exact successful contents/recovery;
POSIX coverage additionally rejects FIFOs without blocking. LF is pinned for
the exact-content source fixture on Windows checkouts. Windows native execution
has not been performed here.

Empty void returns now have an absent operand rather than an Unknown sentinel,
so the strengthened native fence preserves existing `ret void` behavior. The
checks retain F01/F05/F07 native behavior and F11's literal-say rejection.
Indirect returned loans remain opaque to Meiya and diagnose at the invocation
with a blocked result. Generic pointer-cast frontend/MIR coverage is retained,
while native scalar emission uses a unit without the unsupported aggregate
receiver and the generic unit explicitly requires a named no-module fence.
C-width ABI lowering (B01) remains deferred. No language semantics, public wire
versions, or root-scope rules change. The additive checked read uses the existing
bootstrap C result representation; it does not add a native word/result ABI or
complete the standard filesystem surface.

### Resource boundary and verification

All 20 added executable smokes use the unchanged 64 MiB process guard and
1,024 live-array ceiling. Five added native programs each run in a separate
compiler fixture process, validate/restore MIR, compare modules byte for byte,
and require exact native exit/stdout/stderr. The Bool source combines 18 return
helpers into one selector; the ordinary computed-callback source splits its
multiple-argument case into a second program. Both preserve the original case
checks. These sizes fit the existing authoritative MIR lifetime policy: larger
initial fixtures exhausted handles during Meiya or MIR restore, which can stall
under exhausted storage. This checkpoint fixes diagnostic restoration only;
it does not claim general MIR/Meiya restore lifetime or exhaustion recovery.

The full gate passes all 302 registered smokes and all 15 native LLVM programs
on compiler/checker/fixture sources at `cd8b82d63faf74cefacb9a8e37f483c9647f5351`. It includes exact
Hello World output, the checked-read C fault fixture, warning-only execution,
and stage-owned build-command rejection. Peak retained runner memory is
107.9 MiB against the 256 MiB limit. Independent review reports no unresolved
source findings. Conformance and the 0.14.2 version invariant pass at
`00b51831f1b550ecc12279aa95b5ef1d37d3f4d5`, with the existing warning that the shipping native CLI is not
built in this workspace. The conformance follow-up changes only its duplicate
callback oracle. Report and documentation changes preserve the tested compiler,
check_v4 harness and fixtures.

Portable baseline/tool hashes, source hashes and gate evidence are in
[`benchmarks/v4/correctness_handoff6.json`](../../../benchmarks/v4/correctness_handoff6.json).
Raw captures and independent reviews remain in `/workspace/v4-correctness6`.

```sh
python src/compiler/v4/check_v4.py --smoke H6
python src/compiler/v4/check_v4.py
python -u -m freakc audit-conformance
python -u tools/release_version.py check
```

## Handoff 5: six-shape lookup scaling

The baseline compiler is `9f6986f6ec1aa4fa70dd52c6ac45c9a3de031368`;
the final measured compiler and independently reviewed integration is
`3db07fb68e8d370fef3551d074c843418ce4e705`. The baseline PG checkout is
`b57ab5bf42d5cb55d22cefa95f3c8d36aac9785c`, which changes only the benchmark
and its tests relative to the baseline; generated compiler C is identical.
The portable measurements, complete nine-stage timings, source/module hashes,
compiler/runtime hashes, growth factors and selected profile counts are in
[`benchmarks/v4/scaling_handoff5.json`](../../../benchmarks/v4/scaling_handoff5.json).

All six shapes run at sizes 200, 400 and 800, plus task sizes 3,200 and 8,000.
Every one of these 20 inputs reports zero diagnostics in all nine phases,
links and executes with its exact expected exit status, stdout and stderr.
Source and LLVM modules match the baseline byte for byte in every case.
The 56,003-line case is below the handoff's 30-second target.

The following are single serialized x86_64 Linux runs with clang 19 `-O2`,
excluding clang compilation/linking of the generated module. Native monotonic
clocks measure stages; Linux `VmHWM` supplies the compiler's actual peak RSS,
without the inherited parent high-water floor of `getrusage`. Stage peaks are
cumulative. The process-tree guard is 5,000 MiB with a 400-second compiler
limit. Shared-host timings have about 30% noise. Table cells show baseline
→ final; increased memory reflects the additional derived facts and remains
proportional to input across this matrix.

| Workload | Total s | TY s | MIR s | Meiya s | Codegen s | VmHWM MiB | Speedup |
|---|---:|---:|---:|---:|---:|---:|---:|
| tasks 800 | 1.518 → 1.185 | 0.145 → 0.107 | 0.435 → 0.250 | 0.240 → 0.245 | 0.411 → 0.264 | 132.3 → 149.0 | 1.28× |
| long 800 | 4.664 → 1.437 | 0.001 → 0.000 | 0.767 → 0.330 | 3.535 → 0.813 | 0.205 → 0.085 | 76.6 → 84.4 | 3.24× |
| calls 800 | 2.527 → 1.891 | 0.122 → 0.083 | 0.860 → 0.538 | 0.221 → 0.206 | 1.019 → 0.736 | 162.1 → 178.5 | 1.34× |
| impl 800 | 32.157 → 2.397 | 0.304 → 0.290 | 21.731 → 0.614 | 0.551 → 0.211 | 8.942 → 0.687 | 354.0 → 384.7 | 13.41× |
| say 800 | 1.179 → 0.511 | 0.087 → 0.061 | 0.077 → 0.090 | 0.038 → 0.032 | 0.835 → 0.159 | 101.1 → 110.4 | 2.30× |
| mixed 800 | 7.434 → 1.235 | 0.107 → 0.093 | 4.479 → 0.341 | 0.234 → 0.140 | 2.340 → 0.349 | 154.3 → 169.3 | 6.02× |

Large task sets:

| Workload | Total s | TY s | MIR s | Meiya s | Codegen s | VmHWM MiB | Speedup |
|---|---:|---:|---:|---:|---:|---:|---:|
| tasks 3200 | 7.595 → 5.333 | 0.854 → 0.737 | 3.156 → 1.182 | 0.861 → 1.079 | 1.632 → 1.142 | 520.0 → 586.3 | 1.42× |
| tasks 8000 | 28.966 → 13.666 | 3.753 → 2.997 | 15.122 → 2.573 | 2.261 → 2.488 | 5.051 → 2.751 | 1298.7 → 1463.9 | 2.12× |

### Implemented lookup changes

- R1: HIR exposes ascending physical Impl IDs. MIR's method searches use
  those candidates; doctrine search uses the qualified subset in TY's packed
  compatibility cache. Existing doctrine, target, instance and method tests
  preserve first-match ordering, generic substitutions and custom primitive
  overloads. With ready indexes, a zero-candidate miss reads no item kinds or doctrine
  headers.
- R2: MIR keeps independent definition and name bucket tables in one packed
  child (`3 + 2C` cells for capacity C). Both retain their first physical
  match. LLVM signature lookup uses definitions; variadic promotion uses
  names, avoiding repeated whole-file misses for literal `say`.
- R3: Meiya indexes numeric statement IDs to physically ordered paths, with
  storage sized by observed rows, including sparse and negative keys. Its
  statement queries and block-state consumers retain Move-before-Write
  behavior. Mutable exclusivity separately checks actual Loan/LoanMut rows
  once and skips pair comparisons in loan-free results, regardless of stored
  summary counters.
- R4: MIR maintains per-block counts, first/last statement IDs and physical
  next links during live construction. Meiya and LLVM traverse those links;
  first condition/return selection and cold negative-block behavior remain
  unchanged. There are two derived children per body and no per-block handles.
- R5: TY retains item and Impl-method token bounds in one cache per observed
  HIR (`9 + 6I + 2M + Q` cells: I items, M methods, Q qualified Impls). Ready
  reads require current HIR/Parse/Lex revisions and tree/stream identities.
  Supported raw edits use the mutation hooks. Cold readers neither allocate
  nor publish derived cache storage; explicit finalization recovers after handle pressure clears.
- R6: Resolve rejects missing extern-member markers through the runtime
  substring primitive before its existing first-hit/suffix logic. Cached item
  bounds also reduce repeated span and decimal parsing.

All indexes are derived, absent from snapshot vocabulary, invalidated by
supported direct edits/restores, and rebuilt after complete construction or
restoration. Exact duplicates, collisions, empty keys, sparse rows, owner reuse,
rejected restoration and unavailable derived storage retain cold semantics.

### Profile evidence and resource coverage

Profiles use a separate frozen `-pg -O1 -fno-inline` compiler. These are flat
call counts; profile seconds and sampling percentages are excluded.

| Workload | Actual reader | Baseline calls | Final calls |
| --- | --- | ---: | ---: |
| tasks 3,200 | HIR item kind | 61,881,727 | 428,929 |
| tasks 3,200 | MIR body definition | 5,265,623 | 160,151 |
| tasks 3,200 | Meiya path statement | 1,171,200 | 316,801 |
| long 800 | Meiya path statement | 45,228,428 | 425,661 |
| long 800 | MIR statement block | 13,019,109 | 32,056 |
| impl 400 | TY skip item | 377,340 | 1,200 |
| impl 400 | TY matching brace | 299,154 | 400 |
| impl 400 | Lex token type | 78,989,000 | 2,675,066 |
| impl 400 | TY Impl doctrine header entry | 640,403 | 403 |
| tasks 3,200 | Decimal digit | 9,112,004 | 4,501,076 |

The intermediate compiler made 12,832,021 MIR body-name reads on `say` 800;
the final compiler makes 25,307 with the same 16,011 lookup requests. There is
no baseline Say PG capture. Extern-marker requests fall from 1,213,189 to
941,102 on tasks 3,200; request counts alone do not measure the removed miss
work inside the helper.

Nine added executable smokes use the existing 1,024-array-handle mode and a
64 MiB fixture ceiling. They cover cold/exhausted/recovered readers, supported
same-size mutation, duplicate ordering, snapshots, owner reuse and actual work
at increasing sizes. Work assertions count actual getters, rather than only
index probes. An external negative control restoring the three old MIR whole-
item loops fails exactly the two 200/800 work assertions. TY's qualified
fixture observes actual MIR operator consumers and demonstrates the old header
scan as a cold control; MIR's name fixture observes actual literal-say variadic
promotion. Its 200/800 identity-column-only rows exercise name lookup and are
explicitly excluded from valid-MIR snapshot or native-execution claims.

At the pinned handoff-4 checkpoint, source allocation counts and fixture
budgets agreed with README. HIR's then-current 39-child budget was also guarded
by conformance. HIR has 42 global
registries, 39 file children and four finalizer scratch handles;
MIR has 39 globals, 37 file children and 32 children per body; Meiya has
50 globals, 12 file children and five children per result (four authoritative
plus one derived). TY adds one item/method cache registry and one packed child
per observed HIR; Lex and Parse each add one revision registry without new
children. The qualified and body-name extensions add cells to existing
children, with no added handles. Derived replacement children are released;
authoritative restore-storage lifetimes and process-lifetime bootstrap Words
retain their existing separate policy.

The pre-interpolation owned-word checkpoint used HIR: 44 global registries and
41 file children. Interpolation now adds one packed-plan registry and child:
the current HIR inventory is 45 global registries and 42 file children, with
snapshot v11. MIR retains 40 global registries, 38 file children and 33 children
per body. MIR snapshot v6 adds lexical statement scopes and
validates their live and restored cross-facts atomically; v4/v5 snapshots are
rejected. These counts supersede the historical handoff-4 counts above.
The older counts remain historical measurements of their pinned checkpoints.

### Remaining scaling boundaries

The 3,200→8,000 task step grows total time 2.56x for 2.5x input: MIR 2.18x,
Meiya 2.30x and codegen 2.41x. TY grows 4.07x. Closure validation still asks
for each HIR item's child count by scanning Parse nodes; the 3,200-task profile
retains 10,249,602 Parse-parent reads even without closures.

`long` 800 improves overall by 3.24x, but its remaining Meiya work is
loan-bearing: 6,026,219 path-kind reads and 362,516 loan-holder/successor tests
remain. The no-loan preflight does not remove those comparisons. Many qualified
Impls combined with many queries can also remain superlinear because each
candidate step uses an upper-bound search followed by original semantic tests.
This checkpoint does not claim the handoff's near-2x target in every stage.
These families, general word ownership and explicit bootstrap initialization
remain separate follow-up work.

### Verification and reproduction

The full gate passes all 282 registered smokes on compiler/checker sources at
`3db07fb`, including ten native LLVM programs, exact `Hello, world!\n` output
and normal build-command checks. Peak retained runner memory is 65.3 MiB
against the 256 MiB limit. Independent review cleared this integrated source
and the portable measurement report. The five benchmark failure tests pass.

Conformance and the 0.14.2 version check pass, with the existing warning that
the shipping native CLI is not built.

This checkpoint/report and the README allocation wording are documentation-only
follow-ups; they do not change the tested compiler or smoke harness.


```sh
python v4_scale_bench.py --sizes 200 400 800 --check --mem-limit-mb 5000 --timeout 400 --json /tmp/v4-six.json
python v4_scale_bench.py --shapes tasks --sizes 3200 8000 --check --mem-limit-mb 5000 --timeout 400 --json /tmp/v4-big.json
python v4_scale_bench.py --shapes impl --sizes 400 --profile --check --json /tmp/v4-impl-profile.json
python src/compiler/v4/check_v4.py
python -u -m freakc audit-conformance
python tools/release_version.py check
```

The harness freezes generated C and runtimes in uniquely named compiler
bundles, validates hashes when reusing `--tool`, audits native export collisions,
continuously applies the shared process-group time/memory/output guards, and
records failure captures with a nonzero exit status. Five focused harness tests
cover diagnostic rejection, nonfinite timeout options, quiet-stage timeout and
descendant termination, wrong native exits and prelink duplicate symbols,
including failure JSON propagation. Raw manifests, programs, modules, captures, profiles and
review reports remain in `/workspace/v4-scaling5`.

The handoff's `yes`/`no` parameter example already fails at the baseline with
ordinary-parameter diagnostics. Those spellings are reserved Boolean literals;
this run does not change binding or Boolean-literal semantics.


## Handoff 4: whole-module memory and lookup scaling

The pinned before source is `1fa0461091db41d4e94a9c9af1d3cab55fbf0191`.
Memory-only measurements use `77a1b31e7b93c574333d596b1d6fef5350040033`;
the final indexed compiler uses `29447d7c17a853c9b41d1651e35540704e34f776`.
All three compile the same synthetic tasks with clang 19 `-O2` on x86_64 Linux.
Stage boundaries use the native monotonic clock, current RSS and `getrusage`
peak RSS. Runs are sequential, with a 2 GiB process-tree guard and a 300-second
timeout. Every stage reports zero diagnostics.

These measurements include module assembly and compiler output, excluding
clang compilation/linking of the emitted LLVM. The peak column uses native
`getrusage`, since polling can miss the short module-assembly peak. Timings are
single runs on a shared host; treat them as within about 30%.

| Lines | Before wall / peak RSS | Memory fix only | Memory fix and indexes |
| --- | ---: | ---: | ---: |
| 1,403 | 0.814 s / 79.7 MiB | 0.815 s / 34.9 MiB | 0.410 s / 35.3 MiB |
| 5,603 | 10.270 s / 820.6 MiB | 9.871 s / 130.8 MiB | 1.433 s / 132.1 MiB |
| 22,403 | Not retried locally | 152.390 s / 513.8 MiB | 7.870 s / 519.9 MiB |

The handoff's independent before run at 22,403 lines was killed near 6 GB after
176 seconds. Both new runs complete under the local 2 GiB guard. The final
22,403-line LLVM module is 2,408,214 bytes. It matches the memory-only module
byte for byte; the 1,403- and 5,603-line modules also match the original before
compiler byte for byte (146,412 and 590,412 bytes).
Clang also verifies and links the final 22,403-line module with both runtime C
files; executing it exits 6 with empty stdout/stderr, as `f0(1, 2)` requires.

### Module and body memory

`freak_codegen_llvm` now collects borrowed fragments and calls `word_join`
once for module assembly, body assembly, complete rvalue trees, globals,
literal escaping, mangled names and argument/parameter lists. Joining releases
the scratch array without consuming the retained words. A recursive rvalue
collector shares one accumulator through the expression tree, preserving
instruction order, casts and raw-pointer preludes. Module emission continues
to consume sealed codegen facts, preserving the existing epoch contract.

At 5,603 lines, before RSS rose from 140.6 MiB after codegen to 820.6 MiB after
module assembly. The indexed compiler rises from 131.7 to 132.3 MiB, about
0.66 MiB added. Module assembly time falls from 0.524440 to 0.000637 seconds.
The memory-only run already demonstrates the fix independently of the indexes.

Two registered smokes execute under a fixed 128 MiB ceiling:

- `codegen_llvm_module_resource_smoke.fk` assembles 800 valid LLVM bodies,
  padded with comments to exceed 3.3 MB, and checks exact header, body order,
  byte contents, newlines and retained body facts.
- `codegen_llvm_body_resource_smoke.fk` emits 12,000 statements and a
  depth-2,048 expression tree. It checks all 14,048 instruction IDs in order,
  exact repeated output, and suppression of a real instruction after the first
  return. The focused run used about 32 MiB.

The identical final fixtures fail the 128 MiB guard with the original codegen:
the module probe was sampled at 960.9 MiB and the body probe at 575.0 MiB before
their process groups were stopped. The guard polls, so those observations are
overshoots of the ceiling, not exact peaks or hard allocation limits.

### Derived lookup indexes

All indexes are per owner and derived from authoritative rows. They preserve
the earliest physical match, do not alter snapshot vocabulary, invalidate on
direct mutation/restore, and rebuild after complete lowering or validated
whole-owner restoration. Cold/failure paths retain the original lookup
semantics. Query paths never allocate or publish a TY index.

- TY stores one packed hash table for name/category and definition lookups.
  Category-specific first-match and cross-kind type-union ordering remain
  intact, including resolve-first extern precedence and alias normalization.
- HIR stores stable sorted physical record IDs for parameter owners and
  `(item, ordinal)` parameters, queried with lower bounds. Sparse/directly
  restored rows and parameters written before their owner retain cold behavior.
- Resolve stores packed name and `(name, kind)` hash tables, retaining physical
  first-match behavior across duplicate names and loose v1 snapshot writes.

The HIR owner budget is now 38 child handles; its exact fixture, harness,
README and conformance audit agree. Existing storage-closure guards remain
unchanged. Three registered index smokes run under 64 MiB with
`FREAK_ARRAY_LIVE_LIMIT=1024`. They cover duplicates, collisions or extreme
keys, misses followed by appends, overwrite, reuse, rejected atomic restore,
snapshot roundtrips and real handle-exhaustion recovery. TY and resolve repeat
restoration with stable handle capacity; HIR retains its fresh-slot and bounded
scratch accounting. Resource failures preserve correct cold reads.

For four times the task count (200 to 800), measured middle-stage growth is:

| Stage | Before 1,403 / 5,603 lines | Before growth | Indexed 1,403 / 5,603 lines | Indexed growth |
| --- | ---: | ---: | ---: | ---: |
| TY | 0.233119 / 3.609409 s | 15.48x | 0.038701 / 0.151680 s | 3.92x |
| MIR construction | 0.137745 / 1.557357 s | 11.31x | 0.084484 / 0.426317 s | 5.05x |
| Meiya | 0.118459 / 1.547793 s | 13.07x | 0.047995 / 0.206009 s | 4.29x |
| LLVM lowering | 0.201864 / 2.687515 s | 13.31x | 0.082641 / 0.371908 s | 4.50x |

Whole-run gprof call counts at 5,603 lines (`-pg -O1 -fno-inline`) corroborate
the lookup reduction. The final profile has only 0.71 seconds of sampled time;
time percentages are not used as evidence.

| Function | Before calls | Indexed calls |
| --- | ---: | ---: |
| `freak_array_get` | 651,217,719 | 38,875,390 |
| `freak_v4_ty_signature_kind` | 97,602,674 | 108,959 |
| `freak_v4_hir_task_param_owner_items_handle` | 46,934,692 | 1,255,733 |
| `freak_v4_hir_task_param_items_handle` | 38,474,545 | 566,518 |
| `freak_v4_resolve_names_handle` | 40,715,649 | 6,074 |
| `freak_v4_resolve_kinds_handle` | 16,992,414 | 5,236 |

Resolve's indexed path reads individual symbols directly, so the old array
accessor counts do not represent all new resolve work. Lookup request counts
remain unchanged; the resource fixture separately checks bounded hash probes.

MIR still has residual global scans: `find_doctrine_impl_method_ref` is called
4,800 times and scans 801 HIR items on each miss, making 3,844,800 item-kind
checks. LLVM signature emission invokes MIR `lookup_body` 801 times, causing
321,201 definition checks. These scans are unchanged by this patch. MIR grows
7.62x between 800 and 3,200 tasks (0.426318 to 3.249518 seconds), so this
checkpoint does not claim linear scaling of every stage. Those two families
are a concrete future profiling target; W2 word ownership and explicit
bootstrap root initialization remain the next semantic roadmap work.

### Build flag, verification and reproduction

`build_v4.py --compiler-opt 0|1|2|3` chooses optimization for the bootstrap V4
compiler. Default 0 preserves the original smoke build; other levels use
isolated cache directories such as `build/v4_smoke/compiler_O2`. The shared
smoke compiler flags remain unchanged. An optimized Hello World run reports
zero diagnostics at every stage and exact `Hello, world!\n` output; repeated
optimized builds reuse the compiler cache without replacing the default build.

The full gate passes all 273 registered smokes on compiler sources at
`29447d7`, including ten native LLVM programs, exact Hello World output and
the build-command checks. Peak retained runner memory is 64.1 MiB against its
256 MiB limit. Focused resource, restore, semantic, query and architecture
checks pass. Conformance and the 0.14.2 version check pass, with the existing
warning that the shipping native CLI is not built. Independent review cleared
the integrated compiler, optimization flag and auditor-only budget delta
`f29d804193af42c25e40c181d0f7ecaf85229030`. Later checkpoint documentation
does not change the tested compiler sources.

```sh
python src/compiler/v4/build_v4.py --compiler-opt 2 src/compiler/v4/examples/hello_world.fk -o /tmp/hello-v4
python src/compiler/v4/check_v4.py
python -u -m freakc audit-conformance
python tools/release_version.py check
```

Frozen generated C, runtime copies, SHA-256 manifests, synthetic inputs,
instrumentation scripts, timing JSON, whole-run gprof reports and fixture
failure/pass evidence are retained in `/workspace/v4-scaling4`. Measurements
are in `{baseline,memory,indexed}/timed-results.json`; call counts are in
`{baseline,indexed}/profile-800/{gprof,flat}.txt`. Input SHA-256 values are
`02c6afc41381503f6383db29fd38739c0608d19cfeb969f6af13a37ea011966c`
(200 tasks), `f8165e0450fe289fcfa024cde1fca27e03c8f79a00507bfefe0a1412dae2d2a7`
(800), and `38348bfc6b6a86ba36e832b19eb50b3935e7500540d18d943d4b23a3318a9999`
(3,200). `prepare_measurement.py` freezes source and asserts generated-C
instrumentation points; `run_measurement.py` runs guarded, sequential jobs.
The final full log is `/workspace/v4-scaling4/full-v4-29447d7.log`.
Large-module native execution and the final optimized Hello World cache proof
are saved in `/workspace/v4-scaling4/native-completion-verification.json`.
Independent review disposition is saved in
`/workspace/v4-scaling4/review/FINAL_VERDICT.md`.

## Earlier token-boundary scaling evidence

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
link-plan mechanism was added. The suggested `feat/v4-runtime-core` branch was
subsequently fetched and reviewed at `046147e19246d312b31ae4ed71f9ff0ace44e673`;
its planning groundwork is recorded below for the next runtime slices.

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

Every measured stage reports zero diagnostics; the process maximum observed
within this earlier stage-only run stays below 35 MiB. LLVM lowering includes
complete body generation, but this run stops before final module assembly and
clang/link execution. It is not a whole-compiler memory bound; the handoff 4
measurements above include module assembly. These are single-run samples.
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

## Runtime-core prior art

The fetched [runtime-core planning commit](https://github.com/FREAK-lang-dev/Freak-lang/commit/046147e19246d312b31ae4ed71f9ff0ace44e673)
adds a separate `freak_runtime` planning crate and LLVM link-plan accessors.
It recognizes freestanding, minimal, system, desktop and jit profiles, but
supports only minimal. That profile records seven components: startup,
allocator, panic-abort, word, list-array, shape and say. Its target string is
stored without TargetSpec validation, and its library field stays `none`.

The LLVM planner separately labels every nonempty codegen plan with
`v4rt_minimal_core` and deduplicates foreign-library labels from declaration
and call facts. It does not consume the runtime profile/component plan.
`v4rt_minimal_core` is a logical label; this commit supplies no matching native
artifact or linker consumer. Its smoke proves minimal-profile and link-plan
metadata, rather than native runtime execution.

This is useful prior art for owning profile/component facts separately from
LLVM link requirements. Adapt those boundaries when runtime selection is
implemented, keeping one planning mechanism. Integration must connect the two
plans to actual runtime files/artifacts, validate targets and unsupported
profiles, preserve sealed codegen facts and runtime ABI checks, and cover
foreign libraries plus native link/run behavior. Planning persistence and
invalidation need contracts before exposing these facts through cached queries.
Owned-word releases and explicit bootstrap initialization remain separate
semantic work; this branch does not implement them. The executing W1 build
continues to link both existing runtime C files directly.

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
