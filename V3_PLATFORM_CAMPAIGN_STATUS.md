# FREAK V3 Platform Campaign Status

Pinned integration base: `db2afbb839c283c7cfe4d74a4ea9d08057a21c9d`
(`v0.14.1`)

Integration branch: `feat/v3-platform-foundation`

Campaign objective: make the stable V3 runtime, standard library, tooling, and
ecosystem substantially faster and more useful without introducing V3.5
compiler architecture or semantics.

## Stability boundary

| Area | Campaign state | Rule |
|---|---|---|
| Compiler semantics | Frozen | No new type, ownership, lifetime, MIR, query, or frontend architecture. |
| Runtime and standard library | Active | Compatible APIs and implementation improvements are allowed with explicit ownership and error behavior. |
| Ordnance and Hangar | Active | Package resolution remains outside the compiler; the compiler consumes a resolved immutable graph. |
| C and LLVM backends | Required | Claimed V3 behavior needs parity coverage until V4 formally retires C. |
| Public runtime ABI | Frozen by default | Additive ABI requires classification and tests; layout/signature replacement requires explicit approval. |
| `word += word` | Not approved | It is a backward-compatible source extension, not a runtime-only optimization. Preserve the negative corpus until separately approved. |

## Approved first-tranche contracts

- `word.repeated(count: int) -> word` is approved as a class-D additive source
  extension explicitly requested by this campaign. It repeats complete pattern
  byte sequences, returns empty for `count <= 0`, performs one checked exact
  allocation for nonempty output, and preserves the existing V3 UTF-8/byte
  boundary rather than redefining indexing semantics.
- General word construction is approved through generation-checked opaque
  integer handles under `word_builder::*`. A nominal `shape WordBuilder` is
  rejected because C shape storage is not an executable parity surface.
  `finish` and `discard` consume a handle; V3 does not gain automatic
  destruction or move-only semantics.
- ByteBuffer is approved through generation-checked opaque integer handles and
  explicit release. Raw borrowed views and automatic destruction are deferred
  to Maverick. The legacy public `freak_byte_buffer` struct and symbols remain
  unchanged for compatibility.
- `+03` is approved as the canonical internal profile `plus03`, displayed as
  `+03 — FINAL FORM`: LLVM O3, ThinLTO by default, and semantics-preserving
  runtime policy. It is not the Bible's V4-only `final_form` build mode and
  never enables fast-math, `-Ofast`, target-native tuning, or UB-dependent
  behavior.
- `--lto`, `--lto=thin`, `--lto=full`, and `--lto=off` are approved CLI
  additions. LTO must compile runtime sources into the link unit and must fail
  clearly when unsupported rather than silently degrading to packaged O2
  objects.
- Runtime layout/signature ABI remains `freak-v3-abi-1`. Additive runtime APIs
  carry the separate monotonic `freak-v3-runtime-api-3` capability marker. A
  compiler requiring a newer capability must reject an older same-ABI payload
  before emission/linking.
- Standard-library source helpers carry `std/freak_std_api`, currently
  `freak-v3-std-api-1`, independently of the frozen layout ABI. Build/run and
  Doctor require an exact capability match; missing or incompatible std
  payloads cannot bypass a runtime repair by supplying older source helpers.
  Doctor reports this as `checks.stdlib_api` and repairs the distribution
  through the existing single staged-upgrade route.
- Runtime metrics are compile-time/test controlled and emit one versioned JSON
  record. Default production builds incur no large instrumentation overhead.

## Discovery dispositions

- Public ByteBuffer completeness claims are currently false for shipping V3:
  only the Python bootstrap and dormant C runtime know the old API. The new
  implementation must land before those claims can remain “complete.”
- The old ByteBuffer implementation has no release, aliases storage on value
  copy, contains `from`/`to_list` stubs, accepts malformed/NUL-containing text,
  and has unchecked capacity arithmetic. It will not be exposed to native V3
  unchanged.
- `time::now_ms` currently disagrees across backends (wall clock on C/POSIX
  LLVM, monotonic-since-boot on Windows LLVM). Preserve it as wall-clock epoch
  time everywhere and add a separately named monotonic clock.
- Several historical process APIs are FREAK Lite placeholders. New process
  work must use native argv/cwd/environment handles and must not forward
  structured arguments through a shell.
- Native `--opt=` parsing currently truncates to one character and ignores
  malformed/unknown flags. Profile work must validate the entire value before
  artifact invalidation and include canonical profile/LTO/link-plan fields in
  freshness identity.

## Lane matrix

| Agent | Scope | Current task | Blockers | Tests added | ABI impact | Performance impact | Ready to integrate? |
|---:|---|---|---|---|---|---|---|
| 0 | Campaign command / integration | Integrate corrections; register gates; maintain delivery evidence | Full campaign incomplete | Ledger and capability rejection coverage | API marker 2; layout ABI 1 | None | Integration active |
| 1 | Word performance | Repetition and builder integrated through `d81a432`; common-operation audit remains | Final campaign review and full workload evidence | `tests/v3_word_foundation.py` | Additive API | Exact repetition and amortized construction counters | Foundation integrated |
| 2 | Bytes / ByteBuffer | Managed buffer integrated through `22bde2d`; complete width inventory next | u16/u32/u64 requirements not yet all demonstrated | `tests/v3_byte_buffer_foundation.py` | Additive handles; legacy struct unchanged | Growth/copy counters | Foundation integrated |
| 3 | Performance lab | Lab v2 and process containment integrated through `a252bb6` | Remaining benchmark categories and final CI registration | `tests/v3_performance_lab.py` | None | Measurement, no broad speed claim | Foundation integrated |
| 4 | CLI / `+03` / LTO | Profiles and provenance cache v6 integrated | Final installed-payload/platform gates | `tests/v3_build_profiles.py`, freshness | None | O3/ThinLTO source-runtime builds | Foundation integrated |
| 5 | Allocation observability | Word/builder/buffer counters and synchronized C owned-word audit exist | Remaining resource classes; bootstrap numeric-print ownership gap discovered | Word/buffer counters and two-reader audit/leak controls | Test-controlled instrumentation | Enables work-based gates | Partial |
| 6 | System runtime | Corrections integrated at `eac885c`; focused gate and independent review clean | Structured process/fs/random and Linux execution still pending | `tests/v3_system_runtime_foundation.py` | Additive APIs | Unmeasured | Scalar slice integrated |
| 7 | Networking floor | Corrections integrated through `6f6e09c`; integrated HTTP gate passed | Independent networking correction review and Linux/graph acceptance pending; TCP no-delay not implemented | TCP/HTTP, exclusive bind, oversized host, idle/trickle, exact leak control | Additive socket handles; API marker 2 | Unmeasured | Correction integrated; review pending |
| 8 | COCKPIT V3 | Worker correcting facade and completing widgets; separate clipping worker active | Ordered input/layout/close fixes, clipping mechanism, actual native run | `tests/v3_cockpit_compat.py` | Additive UI clipping planned; no language redesign | Unmeasured | Work active |
| 9 | ABI / preservation | Cold/warm API-1 rejection passed; installed foundation gates registered through `7816f1f` | Full installed archive and platform CI execution pending; COCKPIT registration awaits its correction | Doctor/install/freshness plus lane tests | Frozen ABI 1, additive capability 2 | Gate only | Pending final evidence |
| 10 | Hangar / Ordnance | Existing loader/install paths inspected; graph implementation pending | Structured process mechanism; immutable graph/native declaration contract | No new graph acceptance yet | Compiler remains registry-independent | Unmeasured | No |
| 11 | Stdlib boundary | HTTP and COCKPIT remain packages; full std/novelty audit pending | Manifest/import graph work | No import-side-effect regression yet | Classification only | None | No |

Current write ownership: the lead owns integration documentation, capability
markers, audit guards, workflows, and final gates. The system and network
correction worktrees are clean committed handoffs. `system_correction` now owns
UI clipping runtime/compiler mechanism work in `v3-ui-clipping` from
`eac885c`. `network_correction` is an independent read-only system/docs/gate
reviewer, never an independent reviewer of its networking code. After its review
at `38d2e3c`, `cockpit_review` was explicitly reassigned as the COCKPIT worker
in `v3-cockpit-compat` from `920da97`; it cannot independently review its fixes.
Workers hand off commits; the lead resolves overlapping runtime and
bootstrap hunks in the integration worktree. No worker may independently
approve its own changes.

## First tranche dependency order

1. Freeze the API, ownership, overflow, and ABI contracts for
   `word.repeated`, WordBuilder, ByteBuffer, counters, benchmarks, and build
   profiles.
2. Land deterministic instrumentation and the benchmark result schema before
   making broad performance claims.
3. Implement exact repetition and builder/buffer primitives with C and LLVM
   coverage.
4. Add `+03` and optional LTO only after freshness identity and benchmark
   evidence are in place.
5. Run the preservation, negative, ownership, ABI, installer, release-shaped,
   and C/LLVM parity gates on the integrated head.

## Frozen implementation details from discovery

- `word.repeated` borrows its receiver, treats `count <= 0` or an empty pattern
  as empty, returns independent owned storage for positive results, checks
  `pattern_bytes * count + 1`, and copies only complete existing byte
  sequences. It does not redefine V3 character indexing or normalization.
- `word_builder::*` owns storage behind generation-checked integer handles.
  `finish` transfers the accumulated buffer into an owned `word`; `discard`
  releases it. Both consume the handle, and stale handles fail deterministically.
- ByteBuffer will use a separate generation-checked handle pool with explicit
  release and sticky status. It will not expose raw borrowed views, automatic
  destruction, or the Python bootstrap's unsafe by-value buffer aliasing.
- The first ByteBuffer surface is binary and bounds-oriented: reserve,
  capacity/length/position/remaining, clear/truncate/seek, fixed-width
  little/big-endian reads and writes, copying slices, and strict NUL-free UTF-8
  conversion. List conversion waits for a stable native list ABI.
- `time::now_ms` remains epoch wall time on both backends. A separately named
  monotonic nanosecond clock will support elapsed-time measurements.
- The benchmark lab records provenance, deterministic work/checksums, raw
  samples, binary size, and nullable RSS/runtime counters. CI never gates on a
  wall-clock threshold.

## Pinned baseline evidence

- Fresh immutable-seed to stage1 to stage2 to full CLI rebuild passed from the
  pinned base with Clang 22 and the installed Visual Studio SDK environment.
  The rebuilt CLI reports `0.14.1 (Maverick)`.
- `python -u tests/v3_word_concat.py build/freak.exe` passed on C and LLVM.
  Every 8,192-append scaling lane used 11 growth allocations and copied 24,551
  bytes, including C/LLVM locals and globals plus the LLVM field boundary.
- The historical `tests/bytes.fk` is not V3 acceptance evidence: the shipping
  compiler rejects its legacy `check`/`got`/`nobody`/`result` syntax before
  reaching ByteBuffer behavior. ByteBuffer work requires a new V3-compatible
  executable corpus.
- The tracked convenience CLI at the pinned base was stale (`0.13.2`), so no
  campaign verification may use it without an exact-source rebuild.

## Classification legend

| Class | Meaning | Approval |
|---|---|---|
| A | Implementation-only | Normal reviewed campaign work |
| B | Compatible runtime API | Allowed after ABI inventory and regression coverage |
| C | Compatible standard-library API | Allowed after backend and documentation coverage |
| D | Backward-compatible source extension | Explicit campaign-lead approval required |
| E | Runtime ABI break | Explicit approval and versioned migration required |
| F | Language-semantic break | Out of scope for V3; Maverick/V4 owns it |

## Campaign-wide acceptance ledger

- [x] Exact repeated-word operation exists and has focused C/LLVM tests.
- [x] General word construction exists with deterministic growth tests.
- [ ] ByteBuffer is production-grade.
- [ ] Allocation and deterministic work counters exist.
- [x] Permanent performance lab exists; full category completion remains below.
- [x] `+03` exists as a FREAK optimization profile.
- [x] LTO/ThinLTO can be tested; final release-platform evidence remains pending.
- [ ] Filesystem/process/time/environment primitives are stronger.
- [ ] Networking floor supports a real HTTP server Ordnance.
- [ ] COCKPIT runs on the real V3 `std::ui` surface.
- [ ] Hangar builds useful Ordnance dependency graphs.
- [ ] Native Ordnance has a controlled declarative path.
- [ ] C/LLVM parity remains intact.
- [ ] Ownership and leak tests remain green.
- [ ] Frozen ABI remains intact unless an explicitly approved revision exists.
- [ ] Preservation and negative corpora remain intentional.
- [ ] V3 remains recognizably V3.

## Full requested to-do list and work record

Updated 2026-09-05. Checked items below describe landed implementation or
recorded focused evidence, not a claim that final CI/review/release gates pass.
Unchecked items preserve the original campaign scope. Future-work sections in
the request remain future work and are not silently pulled into this campaign.

### Command, stability, and delivery

- [x] Isolate the campaign from unrelated V4 work at the pinned base above.
- [x] Classify additive runtime APIs separately from frozen layout ABI.
- [x] Keep ordinary `word += word` rejected; approval has not been requested or granted.
- [x] Integrate Word, ByteBuffer, performance lab, profiles, scalar systems,
  managed TCP, and initial COCKPIT slices with their focused test programs.
- [ ] Complete every remaining subsystem requirement below.
- [ ] Update bible, conformance audit, public usage and ownership documentation
  from executable behavior; guard appropriate contracts in the auditor.
- [ ] Register all new executable gates in CI and the final installed-payload gate.
- [ ] Run final preservation, negative, golden, C/LLVM, ownership, ABI,
  installer/upgrade/freshness and release-shaped checks on the final integrated SHA.
- [ ] Complete lead self-review and independent review of that immutable SHA;
  disposition all actionable findings.
- [x] Push the topic branch and open the requested **ready, non-draft PR**:
  [PR #99](https://github.com/FREAK-lang-dev/Freak-lang/pull/99).
  The user's explicit non-draft request overrides the default draft workflow;
  it does not waive correctness or merge gates.
- [x] Set hourly comment/CI monitoring attached to this task; remain quiet on
  unchanged state. Monitor: `review-and-deliver-freak-v3-pr-99`.
- [ ] Address comments and CI failures, refresh review evidence after changes,
  and merge only once all applicable gates pass.
- [ ] Publish an agreed new version after practical tests and merge.
  Remote `v0.14.1` already exists at the campaign base (reverified 2026-09-04);
  do not move that tag. A replacement version choice is pending with the user.
- [ ] Deliver the PR/merge/tag links and the completed-versus-pending checklist.

### Word and memory

- [x] Implement exact repeated construction with checked size, explicit
  nonpositive-count behavior, UTF-8 byte preservation and owned return values.
- [x] Implement generation-checked builder new/with_capacity/reserve/capacity/
  length/clear/append/append_char/append_int/finish/discard and explicit lifetime.
- [ ] Audit builder valid-byte append requirements against the final API.
- [ ] Audit and optimize avoidable allocations in join, replace, split, find,
  count, trim, starts_with, ends_with, substring, interpolation and conversions.
- [ ] Record 1M/100M dynamic append and exact repetition comparison evidence;
  distinguish same algorithm from idiomatic fast construction.
- [x] Add deterministic repetition/builder/buffer work counters and ownership probes.
- [ ] Complete allocations/frees/outstanding/reallocations/allocated and freed
  bytes/peak live bytes/copies/append/growth coverage with low production overhead.
- [ ] Complete leak/stress fixtures for collections, filesystem and networking
  buffers alongside concat, replacement, interpolation, builder and repetition.
- [x] Verify concurrent environment snapshots cannot race C ownership audit state.

### Binary foundation

- [x] Implement managed ByteBuffer lifetime, capacity/cursor operations, sticky
  status, bounds checking, copying slices and validated NUL-free UTF-8 conversion.
- [x] Correct release validation and slice behavior across handle-table growth.
- [ ] Complete and test explicit u16/u32/u64 LE/BE reads and writes, binary
  writes, seek/remaining/truncate and justified signed/float encodings.
- [ ] Record large-buffer and growth-complexity evidence as well as endian,
  malformed-text, bounds, lifetime and cross-backend coverage.
- [x] Investigate views: copied slices retain explicit ownership; borrowed views
  are not introduced without a safe lifetime contract in existing V3 semantics.

### Performance lab and build profiles

- [x] Implement machine-readable benchmark metadata/results and deterministic
  checksums/work counts with compiler/profile/toolchain/linker provenance.
- [x] Harden benchmark subprocess containment, bounded output and timing evidence.
- [x] Implement strict O0-O3/+03 and LTO option parsing, source-runtime LTO,
  semantics-preserving defaults and cache schema v6 invalidation.
- [ ] Complete requested words, bytes, collections, JSON, filesystem, process,
  startup, TCP echo, HTTP plaintext and HTTP JSON benchmark categories.
- [ ] Complete requested timing/throughput/RSS/allocation/copy/binary-size/compile
  measurements; unavailable platform measurements must be explicit.
- [ ] Verify one core command and deterministic regression gates in CI across
  O0/O1/O2/O3/+03, with full/ThinLTO evidence where supported.

### System runtime and networking

- [x] Add separate epoch wall clock and monotonic nanosecond clock plus PID,
  copied environment lookup and environment mutation.
- [x] Close bootstrap owned-environment rejection and clock boundary findings.
- [ ] Strengthen filesystem rename/copy/metadata/size/canonical/temp/directory
  operations, explicit errors, hostile paths and Unicode path tests.
- [ ] Implement structured process spawn/wait/status/stdout/stderr/stdin/
  environment/cwd mechanisms without shell argument interpolation.
- [ ] Complete environment/path join/absolute/separator/executable path helpers.
- [ ] Separate pseudo-random values from OS secure random bytes and test failures.
- [x] Add managed TCP connect/listen/accept/send/receive/close/status/options floor.
- [x] Implement Windows binding, oversized host and slow-client corrections;
  focused repeated/large/partial traffic and exact leaked-socket audit tests pass.
- [ ] Independently review those networking corrections on the integrated tree.
- [ ] Document and test C length-bearing versus LLVM NUL-terminated word
  boundaries without claiming identical behavior for non-equivalent raw inputs.
- [ ] Run real clean-project Hangar net/http/json HTTP-200 JSON acceptance on
  Windows and Linux; TLS remains outside the first milestone.

### COCKPIT and package ecosystem

- [x] Replace unsupported Squad/window-poll assumptions with buffer storage and
  indexed std::ui events; add initial widgets and calculator/showcase sources.
- [x] Fix close handling, ordered input, Unicode deletion, nested layout gaps,
  allocated rectangle bounds, missing calculator addition and Clang selection.
- [x] Finish button/label/checkbox/input/slider/panel/scrolling/dropdown/tooltip/
  modal/layout stack on frozen UI mechanisms.
- [x] Deliver usable calculator, settings and widget showcase examples with
  bounded smoke mode separate from normal interactive operation.
- [x] Run injected-event C/LLVM tests and a real bounded Windows window lifecycle.
- [ ] Inventory required clipboard/title/sizing/DPI/clipping/keyboard/image
  mechanisms; add compatible primitives only where the requested UI needs them.
- [ ] Define canonical Ordnance manifests, stable locks, transitive closure,
  deterministic source roots/build order and immutable compiler graph input.
- [ ] Implement integrity-checked fetch/cache and declarative native sources,
  headers/objects/libraries/platform linkage without install-time scripts.
- [ ] Replace unsafe/fail-open legacy package fetching and source loading;
  test hostile paths, corrupt inputs and atomic failure recovery.
- [ ] Complete clean init/add/resolve/lock/fetch/native-build/FREAK-build/link/run
  acceptance, keeping registry/download/SemVer logic outside the compiler.
- [ ] Audit std/runtime versus domain-specific Ordnance ownership, including
  novelty packages; imports must not run showcase programs.
- [x] Move muvluv's historical BETA showcase into `examples/`; keep the library
  declaration-only and prove an LLVM consumer emits no unsolicited output.
- [ ] Keep broader TLS/GPU/Android/additional platform/package roadmap work in
  the explicitly requested future list rather than expanding the current sprint.

## Verification recorded on 2026-09-04

- Fresh compiler reconstructed from `b735fc0` passed the full updated
  `tests/v3_run_freshness.py`: missing/API-1 cold C/LLVM build/run rejection,
  warm-cache rejection/recovery and the existing freshness/installer checks.
  A separately archived exact `962055a` runtime/std payload (API-1, ABI-1)
  also rejected all four cold operations before creating artifacts.
- The selected-runtime ByteBuffer gate passed using that compiler and a copied
  integration runtime payload. This proves the new arguments are executable;
  it is not a substitute for the final installed archive gate.
- System corrections `a00ecef..eac885c` passed the integrated default gate with
  a newly reconstructed CLI. Independent reviewer `network_correction` returned
  CLEAN, with a separate 200,000-case arithmetic oracle. Review excludes its
  authored networking code and does not claim Linux execution.
- Integrated HTTP acceptance passed with the selected CLI/runtime interface,
  including idle/trickle clients followed by successful JSON responses.
- CI now invokes live profile/LTO and performance-lab checks. The final
  release-shaped gate passes its installed CLI/runtime to WordBuilder,
  ByteBuffer, system, TCP and HTTP tests. These registrations still await a
  complete final gate run and remote platform matrix.
- Python syntax, conformance audit and release-version invariant checks passed.
  No campaign PR, merge, or new tag has been created yet.

## Integration and review checkpoint: 2026-09-05

This newer checkpoint supersedes the in-flight assignments in the lane matrix.
The full campaign remains active and incomplete. PR #99 is open non-draft
for external review, not as an assertion that the merge gates have passed.

- Integrated UI clipping `52e0a71` and COCKPIT correction `d0c0df7`.
  Clipping received an independent clean review of original `fb918e3`, including
  C/LLVM pixel probes, bounds/reset/resize/stale handles and GDI resource counts.
  COCKPIT's worker tested ordered events and all four native examples on both
  backends. Its independent integrated review is pending.
- Integrated muvluv import hygiene `0b13f29`: historical showcase preserved,
  declaration-only library, silent LLVM consumer passed. This is not proof
  that Hangar's pending immutable package graph works. Independent review pending.
- Integrated benchmark expansion `ba19161`: 13 Word/ByteBuffer/startup/CPU cases,
  with all 26 quick O0 C/LLVM results verified. Full 100M/1GB executions remain
  unrun because of limited host memory. Whole-process timings include setup
  and verification; no isolated-kernel or full-size performance claim is made.
- The installed archive gate at `2c04250` passed discovery, ABI rejection,
  golden/negative/ownership/concat/WordBuilder/ByteBuffer/system/TCP/HTTP checks,
  then failed its final upgrade. This is a failed overall gate, not a pass.
  The failure reproduces when a native launcher passes PowerShell 7 module
  paths into Windows PowerShell and `Get-FileHash` cannot autoload. A streaming
  .NET SHA-256 repair is committed at `3c00408`. Module-disabled known-hash,
  binary/literal-path/closed-handle tests and existing downloaded-checksum
  checks pass. The targeted exact-archive rollback/upgrade transaction also
  passed, including deferred replacement and cleanup retries. The complete
  installed gate still needs rerunning on the final integrated head.
- Independent networking review found a release-blocking source parity defect:
  `"127.0.0.1" + char_to_word(0)` has length 10 and is rejected on C, but
  LLVM truncates it to length 9 and connects. Raw explicit-length ABI checks
  do not close this defect. `system_correction` now owns a length-preserving
  runtime repair in `v3-word-length-parity`, based on `ba19161`, with no new
  ownership/type architecture and no global NUL-free-word restriction.
- `network_correction` is a read-only reviewer of COCKPIT/muvluv;
  `cockpit_review` is a read-only benchmark reviewer. Neither reviews its own
  authored changes. The lead owns installer repair, capability markers,
  documentation, CI, delivery and final integration checks.
- Before merge: close the NUL defect and all review findings, complete the
  remaining original subsystem requirements, register UI/package gates, advance
  additive runtime capability requirements for the new helpers, and rerun
  exact-head practical/installed/platform gates. Remote `v0.14.1` still exists;
  it must not be overwritten. The replacement-version choice remains pending.

### Follow-up gate evidence

- The first macOS V4-fast CI failure was a V3 conformance guard requiring the
  obsolete `Get-FileHash` spelling, before V4 execution. Fixed at `c1d1c3d`;
  conformance and module-disabled hash tests pass locally. No V4 implementation
  was changed. Remote current-head validation remains required.
- Clipping and COCKPIT gates both passed against the integrated runtime using
  the clipping-enabled compiler. COCKPIT exercised injected C/LLVM events and
  all four actual Windows example lifecycles. An independent reviewer is
  investigating a possible two-input focus-switch case not covered by that gate.
- The installed release gate now registers clipping, COCKPIT and muvluv
  import-hygiene children with its selected runtime. UI pixels and native
  windows execute on Windows; other platforms retain lowering/replay coverage.
  Muvluv's test is LLVM-only; earlier C/LLVM wording was incorrect and corrected.

### Review-repair checkpoint: 2026-09-05

This checkpoint supersedes earlier in-flight ownership and repair statements.

- [x] Restore the shared bootstrap `transpile` three-value API; the structured
  four-value API is now `transpile_checked` (`a577726`). Focused success,
  parse/type/emission-error and warning cases passed; independent review clean.
  No V4 source or harness changes were required.
- [x] Replace stale UI preservation assertions and root documentation with the
  actual procedural COCKPIT boundary (`25a2a02`). Native UI floor test passed;
  independent review clean. Final platform CI is still pending.
- [x] Fix ordered text-focus replay and failed container pushes (`e5ee8fd`).
  Independent event permutations and native C/LLVM lifecycle tests passed.
- [x] Integrate embedded-NUL Word lengths (`ad33837`, original `4dd3ba4`).
  Registry, transforms, builders, files/input/capture, socket/env validation and
  ownership tests passed on C and LLVM. Independent all-byte transfer/clone/
  forced-moving append probes passed. Unknown foreign pointers retain their
  historical C-string interpretation; the public layout ABI remains 1.
- [x] Rebuild from the checked-in bootstrap seed with runtime capability 3.
  Explicit checker annotation repairs the seed-inference failure (`153e8e8`).
  API-1/API-2 cold/warm rejection and cache recovery passed, as did integrated
  Word parity and strict-handle baseline tests. New helpers require API 3 and
  standard-library capability 1; an old payload must not reach a linker error.
- [x] Emit `process::set_env` with a void LLVM call (`05b0afc`). Full system
  runtime gate and an explicit emitted-signature assertion passed.
- [ ] Finish strict-borrow review repair: basic builtin borrowing and consuming
  `word_join` are implemented, but nested consumers can invalidate an outer
  borrowed argument/ByteBuffer receiver. `system_correction` owns that isolated
  checker/test correction; it cannot independently approve its own patch.
- [ ] Finish damaged standard-library marker handling: a directory or unreadable
  marker currently aborts before Doctor JSON/repair. `network_correction` owns
  the isolated recoverable marker-reader and regression; lead reviews it.
- [ ] Finish calculator division-by-zero and malformed HTTP-field handling.
  `cockpit_review` owns these isolated package/test corrections. The claimed
  HTTP Content-Length defect was rejected with byte evidence: the body is
  exactly 28 bytes, matching the current header; do not change it to 27.
- [ ] Disposition remaining external comments, including benchmark argument
  bounds, cross-target `+03` guidance, the linker identity probe timeout, UI
  symbol documentation and review nitpicks. Reproduce each against current code.
- [ ] Push the coherent reviewed repair set, inspect all new current-head CI and
  review results, and rerun the complete final installed archive gate. The PR
  remains non-draft for review, not merge-ready. Hourly monitoring is active.
- [ ] Complete the original campaign requirements still unchecked above,
  including wider ByteBuffer APIs, remaining benchmark/resource/system work and
  immutable Hangar/native-package end-to-end delivery. These are not waived by
  opening a PR. No merge or release tag has been created.

PR91 overlap is recorded, not imported: reviewed head `12c4352e8598c7eff9f0d9441314232d0383c3b6`
adds recoverable Word registry reservation and owned snapshot arrays. Any later
integration must retain dynamic-NUL lengths in its LLVM splitter, check reserve
failure before bucket access, preserve caller ownership on failed adoption,
and carry the snapshot-array ownership/reuse changes atomically. It requires
fresh integrated tests and independent review; no local V4 checks were run here.

### Latest handoff and remaining blockers

- Nested direct-handle revalidation is integrated at `4af12a8`; full seed
  bootstrap and 17 negative C/LLVM cases passed. The integrated gate also
  passed with the configured `FREAK_CLANG` while PATH selected a different
  compiler. Broader derived-borrow behavior is not approved by that evidence;
  an additional candidate remains unverified and no clean full ownership
  review is claimed.
- Calculator recovery (`3d8f3d4`) and malformed HTTP-field validation (`753c2c5`)
  passed independent lead source review and actual C/LLVM package tests.
  CodeRabbit withdrew its incorrect 27-byte response-length finding after
  the exact 28-byte evidence was posted; that thread is resolved.
- The first recoverable std-marker reader (`886ecfe`) is NOT accepted as final:
  independent review proved Windows text capture truncates Ctrl-Z plus a
  malformed suffix into the expected capability. A bounded complete-byte
  reader with safe diagnostics is being prepared in the isolated
  `v3-marker-byte-validation` lane. Its completed review and tests are required
  before this repair batch is pushed. Control-byte Doctor JSON handling is
  covered by that scoped marker repair, not claimed fixed globally.
- Benchmark bounds and the version-probe deadline are integrated at `0618935`
  (worker `3d9f8c7`), with clean independent review, C/LLVM focused checks and
  a real hung-version-probe timeout. Installed gate registration is `20f4ba9`.
- Root profile-diagnostic (`2168157`), configured-Clang/C-symbol documentation
  (`ccc783d`) and length-aware conformance guards/docs (`de3f481`) are verified
  locally and independently reviewed clean. The full current-head installed/platform gate remains
  pending. Older terminal passes are not substitutes for that gate.
- PR #99 is still non-draft at remote `c1d1c3d`; its failing CI is unchanged
  until the coherent repair batch is pushed. Existing `v0.14.1` still points
  to `db2afbb839c283c7cfe4d74a4ea9d08057a21c9d`. No merge, version bump or tag
  mutation occurred, and the replacement version is still a user choice.

### Conflict-resolution and continued implementation checkpoint

This checkpoint supersedes the older in-flight marker and PR91 integration
statements above. Historical test results remain tied to their recorded heads.

- [x] Merge current `origin/main` (`25ecabdd1b7930b9d28f93bbf65f026ab7bf66ed`)
  into the campaign branch at `cfb60df`. Preserve PR91's recoverable registry
  allocation and owned snapshot-array lifecycle together with the campaign's
  embedded-NUL Word lengths and ByteBuffer signatures. V4 files match the
  incoming main tree exactly; no local V4 checks or paused-lane edits occurred.
- [x] Self-review and independently review that merge. Independent registry
  allocation/resize/node-failure probes, duplicate/conflicting metadata checks,
  and the full native snapshot fixture passed. Added native regression coverage
  for registered binary lines, static NUL, independent source lifetime and
  leak-free join/release. Fresh checked-in-seed compiler and full CLI build passed.
- [x] Integrate the complete-byte std-marker repair at `c72ecab` (original
  `1d93842789d21bf5b0a1d314ef2630cf68c00024`). Bounded raw-byte transports replace
  the rejected text-mode reader. Author end-to-end malformed/unreadable marker,
  Doctor JSON and repair tests passed; independent C/LLVM decoder tests covered
  all 256 byte classes, complete framing, path encoding and 4096/4097 boundaries.
  Native POSIX transport execution remains a CI requirement.
- [x] Verify the combined marker/merge head and push `dc309a3`; GitHub confirms
  mergeable, non-draft, and fresh CI. Full C/LLVM Word/snapshot, strict-handle,
  std-marker/Doctor repair/cache, bootstrap tuple and conformance/version gates
  passed. The full installed archive gate remains in progress, not passed.
- [x] Post pushed-commit evidence and resolve 17 fixed external review threads,
  plus a duplicate exception-transport report. The original strict-borrow
  thread remains open for broader ownership review; refreshed automated reviews
  are requested and still need disposition on their reviewed heads.
- [ ] Complete the isolated explicit u16/u32/u64 LE/BE and bulk-copy ByteBuffer
  slice, then integrate after tests and independent review. Preserve the existing
  signed-int representation for u64 bit patterns and the frozen layout ABI.
- [ ] Finish remaining campaign requirements and final installed/platform gates
  before merge. The existing `v0.14.1` tag is unchanged; a new version choice
  remains pending, and no release is authorized by a passing intermediate test.

### Fresh CI follow-up at `dc309a3`

- Linux/macOS V4 fast jobs passed. Runtime jobs fail in the standalone LLVM
  primitive fixture: raw `free` bypasses registered Word ownership cleanup.
  Approved isolated harness exception `e5b7264` replaces both raw frees with
  registered release and adds its prototype, preserving every assertion and
  cache invalidation. Independent source review is clean. Original/repaired
  diagnostic probes reproduced failure/success, including ownership audits;
  those ran before the additional mutex requirement arrived and are not counted
  as serialized gate evidence. Exact-source revalidation waits for the shared
  `Global\\FreakCheckV4` lock. No V4 runner is launched from this lane.
- Linux/macOS V3 CI reached freshness and failed an obsolete diagnostic string:
  early flag parsing now rejects the unsafe target before backend validation.
  The test now expects the actual early diagnostic on every platform and also
  verifies artifact/cache bytes and mtimes are unchanged. The full Windows
  freshness/installer-cleanup gate passed with the fresh merged CLI.
- ByteBuffer follow-up is committed in its isolated lane: `f128fcd` widths and
  copy, `cda31c6` Python unknown-builder diagnostics, `f609143` LLVM extern
  declaration deduplication. Author C/LLVM/Python and prior foundation gates
  passed. Independent exhaustive u16, seeded u32/u64 and 13,090 copy-range
  probes passed; the identified declaration-registry P2 is corrected and its
  final delta review is pending. Root capability/docs/CI integration is pending.
- Full installed checkpoint gate has passed through ownership/concat, Word,
  strict borrowing, benchmark bounds, ByteBuffer, system, TCP/HTTP, UI clipping,
  COCKPIT and import hygiene. Final marker and exact-archive upgrade completion
  remain pending. No overall gate pass, merge or release is claimed.

### Completed checkpoint validation

- [x] Complete the Windows installed release-shaped gate for the `dc309a3`
  compiler/runtime/archive checkpoint: all registered children, malformed-marker
  recovery, exact-archive rollback and public upgrade routing passed; terminal
  `V3 FINAL RELEASE GATE: PASS` (session 28416). This is checkpoint evidence,
  not completion of the original campaign or a Linux/macOS release claim.
- [x] Validate `e5b7264` cleanup from the exact committed embedded C source,
  without importing or invoking the V4 runner. Acquired `Global\\FreakCheckV4`,
  compiled/executed normal and both ownership-audit modes, observed exact
  `llvm-runtime-primitives=ok` with empty stderr, `CHECK_EXIT=0`, then released
  the mutex. Independent source review is clean. The earlier uncoordinated
  diagnostic is not used as gate evidence.
- [x] Validate and independently review `ad4044a` target diagnostic/artifact
  preservation repair. Full Windows freshness and installer cleanup passed.
- [x] Close the ByteBuffer declaration-registry P2 through independent source
  review of `f609143`; all 13 registry/declaration names agree, and author
  execution covers extern deduplication/linking plus conflict diagnostics.
- [ ] Integrate that reviewed ByteBuffer/Python-builder slice with capability,
  documentation and gate updates; rerun applicable checks after integration.
- [ ] Obtain successful fresh current-head CI and completed refreshed reviews
  before any merge. The existing release tag remains unchanged.

### Latest review queue and main synchronization

- [x] Normally merge newly landed, reviewed main `5a93263` (PR92) at `a192ab4`.
  Independent merge review confirms exact incoming V4 crate blobs, the retained
  cleanup-only primitive fixture delta, unchanged V3 runtime/compiler/CLI/tests,
  and preservation of both incoming MIR guards and campaign auditor guards.
  Conformance/version checks pass; the extracted cleanup source still matches
  its serialized-tested hash. No unpublished PR92 follow-up was imported.
- [ ] Fix refreshed P1: C task-return lowering for `ByteBuffer` and strict
  consumption of semantically typed ByteBuffer fields. Prepared in the isolated
  width lane; existing Phase-1 full-parent ownership remains the contract.
- [ ] Fix refreshed P1: bounded nonfatal runtime API marker diagnostics and
  repair, equivalent to the completed std-marker protection. Isolated lane:
  `v3-runtime-marker-recovery`; only build helper and new regression are owned.
- [ ] Fix refreshed P2: exactly one valid Host field for the supported HTTP/1.1
  request surface. Isolated lane: `v3-http-host-validation`; parser, package
  documentation and acceptance tests only.
- [ ] Validate those prepared corrections after the shared compiler-check slot
  is available, independently review and integrate their immutable commits.
  Current local Windows installed-checkpoint success does not waive these new
  findings or the original unfinished campaign requirements.

### Babysitting checkpoint: current remote head `c0603fc`

- [x] Recheck live PR99: non-draft and mergeable against current main; merge
  remains blocked by CI and unresolved review findings. No merge or tag change.
- [x] Confirm the freshness/installer-cleanup correction passes on Windows,
  Linux and macOS CI. All three shipping jobs subsequently fail in the
  controlled-linker portion of `v3_build_profiles.py` (run `33961735490`).
- [ ] Repair that test's platform assumptions without dropping the selected
  linker identity/cache invalidation oracle: Linux loses the driver-selected
  alias when resolving its path; relocated Apple `ld` loses its `libtapi`
  dependency; MSVC-target Clang ignores the test's `-B` linker override.
  Source-only correction is assigned; these are not infrastructure reruns.
- [x] Complete the first serialized ByteBuffer return/field validation slot:
  exact-source fresh CLI build, return/extern/typed-field tests, widths/copy,
  strict-handle and foundation gates all pass (session 53870, `CHECK_EXIT=0`,
  shared mutex released). Commit `dd27b4d` preserves those tested source blobs.
  This is not a checked-in-seed bootstrap or C shape-execution claim.
- [ ] Independently review `dd27b4d`, then validate the separate prepared
  typed-field owner revalidation delta. It rejects a later argument consuming
  the owner of an earlier borrowed ByteBuffer field without re-evaluating the
  field expression. Four compile-only negatives and valid controls are prepared.
- [ ] Fix the newly confirmed strict-borrow `STMT_WHEN` omission: executable
  arms currently bypass consumption tracking. A bounded arm-traversal and
  conservative post-arm state-merge design is assigned; implementation and
  C/LLVM regressions remain pending.
- [ ] Validate runtime-marker preparation `cab556c` and HTTP Host preparation
  `bb9571c`, then independently review and integrate. Their source/static checks
  pass, but native/platform success is not claimed.
- [ ] Obtain the next explicit shared compiler/native validation lease before
  running any queued native checks. Source-only preparation continues while
  the coordinator owns its V4 validation slot. Current-head V4 runtime jobs
  are green, but remaining fast jobs and every shipping job must also pass.
- [ ] Complete the remaining original campaign requirements, current-head
  reviews, installed practical tests and all-platform CI before merge. Existing
  `v0.14.1` still points to `db2afbb`; replacement version choice remains pending.

### Second ByteBuffer correction validation

- [x] Investigate the independent `dd27b4d` review: extracting a nested shape
  could leave two live roots reaching the same ByteBuffer. Include declared
  shape projections in the existing conservative full-parent move rule.
- [x] Commit the cohesive projection-owner correction at `eb58fbe` after a
  fresh exact-source CLI build and all four agreed regression gates passed:
  return/field ownership, widths/copy, strict handles and ByteBuffer foundation.
  C/LLVM compile-only negatives cover later-argument root consumption and nested
  shape extraction/call/return transfers, with valid observation/transfer controls.
  Session 85606 ended with `CHECK_EXIT=0` and mutex release; exact checker/test
  blobs were unchanged before and after. No checked-in-seed bootstrap or C shape
  execution is claimed by this slot.
- [ ] Complete independent immutable review of `eb58fbe` before integration;
  the broader strict-borrow finding remains open until `when` is corrected too.
- [x] Prepare linker-test portability correction `ed68141`; five pure mocked
  helper tests pass, including a root rerun. Independent source review found no
  actionable issue. Original linker roles and miss/hit/byte-invalidation oracles
  remain covered; real Linux/macOS/MSVC execution is still pending.
- [ ] Prepare `when` target/arm traversal with isolated arm state and a
  conservative post-arm join. Source-only work is assigned as a separate delta.
- [x] Return the compiler/native slot to the coordinator after all agreed
  ByteBuffer checks terminated. No further native checks may start without a
  new explicit handoff; HTTP, marker and platform gates were not run in this slot.

### Reviewed CI correction and refreshed ownership queue

- [x] Independently review `eb58fbe`: both projection-owner P2s are corrected
  within the documented scope, and committed blobs match the serialized-tested
  candidate. `when` and generic call/index-derived borrow boundaries remain.
- [x] Integrate linker-test correction `ed68141` as `8a7f81e`; the five pure
  helper tests pass again in the integration worktree. Linux/macOS/MSVC execution
  remains a fresh CI requirement, not a local native-test claim.
- [x] Confirm all V4 jobs passed on remote checkpoint `c0603fc`. This evidence
  belongs to that head and does not replace fresh CI after the next push.
- [ ] Validate the frozen `when` candidate: 16 positive and 29 negative
  compile-only fixtures are prepared for both C and LLVM, not yet executed.
- [ ] Address refreshed P1 `3940401454`: explicit `int` annotations can erase
  builder/socket ownership identity, allowing aliases to outlive consumption.
  Source-only design is assigned; ordinary integer Copy behavior must remain.
- [ ] Address refreshed P2 `3940401457`: the performance acceptance gate treats
  unreaped POSIX zombies as live descendants. A scoped source/mock correction is
  assigned; actual containment behavior and assertions must not be weakened.
- [ ] Recheck fresh CI and reviews after publishing the scoped linker-test fix.
  Duplicate linker-prefix report `3940401461` matches this correction, but its
  real-platform validation remains pending. All other open review gates remain.
