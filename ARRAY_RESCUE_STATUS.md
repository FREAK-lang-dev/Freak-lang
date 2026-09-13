# Operation Array Rescue

State: scoped -> active -> integrating -> verifying -> complete (merged as PR #102 `62879be`, in `main`).
Base: `0cd5404fed18ab8f38b7229cf8eb6cbfa2895940`.
New base after rebase: `3fa1638` (V3 runtime and platform campaign).
Integration: `fix/v3-array-rescue`, `C:/tmp/freak-v3-array-rescue`.
Conflict repair: `teriri/pr102-conflict-repair`
(`C:/Users/TeRiRi/.codex/worktrees/pr102-conflict-repair`).

**CLOSED OUT — merged.** PR #102 rebase-merged into `main` as `62879be`.
The no-merge authorization gate and pending-CI language preserved below are
the historical record of the in-flight campaign, superseded by the merge.

## Contract and exit gates

Repair shipping V3 list literals, indexing and indexed assignment, length,
iteration, checked bounds, numeric/bool storage, and supported owned word/shape
elements. Preserve language identity and existing compiler architecture. No V4,
Meiya/lifetime work, generics rewrite, or removal of benchmark safety checks.

Require executable LLVM/C parity, diagnostics and adversarial ownership checks,
one-million-element math workloads with recorded performance, V3 regression and
self-host verification, conformance documentation, immutable-head self-review
and independent review. Deliver scoped commits and a draft PR; readiness needs
current-head applicable CI and review disposition. Merged as PR #102
(`62879be`, in `main`); the authorization gate is retired.

## Lane ledger

Four concurrent agent slots; requested roles run in dependency waves.

| Role | Responsibility | Current ownership |
| --- | --- | --- |
| Agent 0 / lead | failures, contract, integration, docs, harness coordination | integration worktree |
| Agent 1 | parser/checker/types | integrated `95730e8` |
| Agent 2 | runtime storage/bounds/ownership | integrated `395c726` |
| Agent 3 | LLVM backend | integrated `500ae08`, `2cc0b3f` |
| Agent 4 | C parity | reused first child; integrated `22c117f`, `00defd1`, `2a7af46` |
| Agent 5 | iteration | parser/checker and backend portions owned by their respective implementation lanes |
| Agent 6 | benchmarks | reused runtime child; integrated `2d8ae14` |
| Agent 7 | torture/negative tests | reused LLVM child; integrated `2b293cd`, `a071ad1`, `c71b0e7` |
| Agent 8 | V3 stability and independent review | compiler reviewer excludes runtime author; runtime reviewer excludes compiler author; stability verifier runs native suites |

Write lanes receive isolated worktrees and explicit ownership before edits.
Integrate commits only. Lead owns root docs, auditor, workflows, and shared
test coordination. Resource budget: four agents, isolated workload processes,
serialized broad compiler gates, bounded execution with recorded session IDs.

## Baseline observations

Original main checkout contains unrelated untracked artifacts and is untouched.
The baseline C index emitter emits `.data[index]` while array literals produce
integer runtime handles. The integrated backends now use the typed runtime ABI.

Fresh seed -> current-source compiler reconstruction succeeded under Visual
Studio Developer PowerShell with Clang. The supplied sample fails in parsing
at `for each`; omitting its loop yields eight checker errors, including numeric
literal rejection, indexing, assignment target and length. Recorded launcher
session: 28805 (completed). Temporary artifacts: `C:/tmp/freak-array-evidence`.

Shared semantic contract: `List<T>`, `tc_is_list`, `tc_list_element`;
`STMT_FOREACH=18`, names=binder, exprs=receiver, bodies=normal block CSV.
Typed storage is separate from legacy compiler `array_*` word handles. Runtime
owns checked contiguous storage and retain/release operations. Existing word
literal callers of legacy `array_get/release` need an explicit compatibility
path and cleanup validation.

The baseline negative corpus deliberately rejects `[1]`; this status fixture
must become a meaningful incompatible-element negative when numeric arrays
land, rather than continuing to assert an obsolete implementation boundary.

## Integrated evidence

Compiler implementation checkpoint: `2c923a9947da6d0720ed0936ead91378059fb4b7`.
All commands below use a freshly reconstructed standalone compiler or public
CLI in the integration checkout; no installed compiler is used as evidence.

- `tests/v3_array_rescue.py`: 14 native executions, both backends, allocation
  auditing enabled; requested example, numeric/bool, word, owned shapes,
  task boundaries and single evaluation pass.
- `tests/v3_array_torture.py`: 82 contracts pass across both backends, including
  bounds/overflow failures, strict mode, aliases, temporary projections,
  explicit release, nested loops and early exits.
- `tests/v3_array_review_regressions.py`: 24 contracts pass across both backends
  for effectful fill counts/shape append, extern temporary ownership, and
  strict iteration/literal moves.
- `tests/v3_array_runtime.py --sanitize`: Clang/MSVC AddressSanitizer passes;
  1M elements, 4096 handles, 20000-deep shape destruction, six negative cases,
  C/LLVM actual-allocation retention-positive controls and zero live objects.
  The harness locates the selected Windows compiler's ASan runtime DLL.
- `tests/v3_array_benchmarks.py`: C/LLVM checksum parity and same-binary checked
  failure controls pass. This Windows run measured 1M-element medians of
  0.164s LLVM and 0.194s C (100k: 0.023s / 0.025s), three measured runs after
  warmup, optimized native programs with bounds checks enabled. These are
  host measurements, not portable performance promises.
- `tests/v3_legacy_golden.py`: six unchanged output cases, twelve C/LLVM runs,
  distribution closure/isolation checks pass.
- `tests/v3_interpolation.py`: native expression/ownership contracts pass.
- `tests/v3_word_ownership.py`: passes, including native C numeric shape fields.
- `tests/v3_word_concat.py`: existing local/global C/LLVM and LLVM field scaling
  pass (8192 appends, 11 allocation/growth events, 24551 copied bytes). Native
  C/LLVM field correctness now verifies zero live containers/words after scope
  exit; Linux leak checking remains enabled. Launcher session: 93129.
- `tests/v3_codegen_error_gate.py`: passes, including native C nominal arrays
  and shapes, artifact rejection, and diagnostic contracts.
- `tests/v3_fixed_point.py`: clean self-host reconstruction passes at `824b8dd`,
  generation 2 equals generation 3 (`a4b8b687f75ba735c993d7c3933e4e81eac3ec9b3fb0d0fac59e53489c0f5b2d`).
  Recorded launcher session: 80809; tracked inputs remained unchanged.
- `python -u -m freakc audit-conformance`: passes, including new V3 array
  wiring guard. This static audit is separate from native execution evidence.

Local machine reports are in `C:/tmp/freak-array-evidence/`; CI uploads its own
per-platform benchmark report. PR #102 has merged into `main` as `62879be`,
which retires the pending-CI checkpoint note; all required local gates had
passed.

## Review disposition

Independent compiler review at `2c923a9` reports no remaining actionable
finding. Earlier findings are fixed and covered by the 24 review contracts:
preserve filled values before effectful counts; snapshot shape append operands;
classify owned iteration binders and walk literal moves; release borrowed extern
container temporaries. A C prefix-dispatch defect and null cleanup after
explicit release were also fixed with executable regressions.

Independent runtime review at `1551b78` found no actionable issue; runtime
implementation is unchanged since that review. Independent docs/tests/CI review
at `dab26e2`, including Windows sanitizer DLL discovery, reports no actionable
finding; the reviewer also accepted the native C codegen-gate delta in `824b8dd`.

Conservative boundaries: no nested lists, List-valued shape fields, typed empty
numeric literals, container covariance or temporary-root indexed writes.
The existing V3 numeric compound-assignment domain is preserved. Native extern
implementations remain responsible for the owned return convention. No V4
compiler checks or implementation changes were made.

## Cross-platform verification follow-up

PR #102 at `e95e73b`: Linux and macOS CI passed. Windows passed the array and
ownership gates but exposed a real regression in the existing UI smoke: LLVM
associated factory calls lost their semantic return type, so a subsequent method
could release an unretained caller-owned shape. Associated callable lookup now
uses the checker's impl provenance for return and parameter types. The new
cross-platform regression reproduces the old failure and covers repeated shape
methods, owned shape/list/word factory results, numeric coercion and void calls.
Fresh compiler/CLI reconstruction and all 26 C/LLVM review contracts pass;
the exact Windows UI smoke now passes (launcher session 58768). Conformance and
release invariants pass. Current-head CI remains required for final delivery.

## Main-sync conflict repair (at user request)

`origin/main` advanced to `3fa1638` while the PR was verifying, so GitHub
reported the PR as conflicting. The branch was rebased onto `3fa1638` (22
commits replayed, no content dropped: the rebased diff is the same 27 files,
2728 insertions, 372 deletions). Prior pinned SHAs in this ledger and in PR
comments still exist as the pre-rebase history; evidence below is on the new
head and supersedes head-bound claims only.

Textual conflicts (all resolved as unions, both sides preserved):

- `checker.fk` `tc_is_known_value_type`: array-rescue List-element rule kept,
  platform-campaign `ByteBuffer` rule kept.
- `checker.fk` `tc_reserved_builtin_namespace_owner`: `List` kept,
  `ByteBuffer` and `word_builder` kept.
- `checker.fk` `tc_builtin_call_params`: legacy `array_*` keeps the
  array-rescue `word-array` signatures (`int` stays assignable to `word-array`);
  `word_builder::*` entries kept.
- `checker.fk` `tc_builtin_method_allowed`: `List.length` kept, `ByteBuffer`
  method table kept.
- `emit_llvm.fk` `llvm_type_code`: `List<T>`/`a:` mapping kept, `ByteBuffer`
  `q` mapping kept.
- `emit_llvm.fk` method dispatch: `length` on `a:` receivers kept, `q`
  (ByteBuffer) dispatch kept.

Semantic break found by the fixed-point gate (not visible textually): the
platform campaign changed `bc_walk_call_args` from 2 to 4 parameters
(`borrow_args`, `consume_first`); the array-rescue `EXPR_ARRAY_LIT` site still
used the old form and the merged tree did not compile. Ported with
`(false, false)`, which reproduces the original consume-all policy exactly
(copy-typed elements are unaffected since only non-copy bindings move).
A full task-signature inventory confirms this was the only changed existing
signature on either side (platform: 1 changed, array-rescue: 0 changed).

Verification on the rebased head (repair worktree, llvm-mingw toolchain):

- `tests/v3_fixed_point.py`: PASS, generation 2 == generation 3.
- `tests/v3_array_rescue.py`: PASS (14 native executions, C + LLVM).
- `tests/v3_array_torture.py`: PASS (82 contracts).
- `tests/v3_array_review_regressions.py`: PASS (26 contracts).
- `tests/v3_array_benchmarks.py`: PASS, 1M-element checksums verified on both
  backends (Windows medians ~0.12s LLVM / ~0.12s C; host measurements, not
  portable guarantees).
- `tests/v3_codegen_error_gate.py`, `tests/v3_word_ownership.py`,
  `tests/v3_word_concat.py`, `tests/v3_word_foundation.py`,
  `tests/v3_word_length_parity.py`, `tests/v3_byte_buffer_foundation.py`,
  `tests/v3_interpolation.py`, `tests/v3_legacy_golden.py`: all PASS.
- `python -u -m freakc audit-conformance`: PASS (incl. V3 typed-array guard).
- `python -u tools/release_version.py check`: 0.14.1 invariant holds.
- `git diff --check`: clean; locally rebuilt `build/` artifacts restored, so
  no binary churn is pushed.

The standing "no merge authorized" note was superseded first by the explicit
rebase-merge request and then by the merge itself (PR #102, `62879be` in
`main`). Historical merge gate, with the CI reference corrected: the branch
had to be mergeable after push and required strict CI — `build-and-test` on
Linux/macOS plus the sharded Windows legs (`windows-bootstrap-build`,
`windows-test-suites-a/b/c`) — had to run green on the new head before the
rebase-merge completed; independent-review delta (this repair + arity port)
is recorded here and in the PR comment.
