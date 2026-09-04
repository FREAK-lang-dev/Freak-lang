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
  carry the separate monotonic `freak-v3-runtime-api-2` capability marker. A
  compiler requiring a newer capability must reject an older same-ABI payload
  before emission/linking.
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
| 5 | Allocation observability | Word/builder/buffer counters exist; audit broader allocation coverage | System audit concurrency correction and remaining resource classes | Word and buffer deterministic counter fixtures | Test-controlled instrumentation | Enables work-based gates | Partial |
| 6 | System runtime | Scalar APIs integrated at `dcdc0f0`; worker correcting ownership/thread/clock tests | Bootstrap env_var ownership, concurrent audit state, clock edges; process/fs/random still pending | `tests/v3_system_runtime_foundation.py` | Additive APIs | Unmeasured | Corrections required |
| 7 | Networking floor | Managed TCP integrated at `6ccc2a5`; worker correcting HTTP/Win32/tests | Exclusive bind, host length guard, slow-client timeout, audit positive control | TCP and HTTP Ordnance tests | Additive socket handles; API marker 2 | Unmeasured | Corrections required |
| 8 | COCKPIT V3 | Compatibility facade integrated at `38d2e3c`; independent review active | Close signal, event loss, nested layout; remaining widgets and actual native run | `tests/v3_cockpit_compat.py` | Uses existing UI/buffer mechanisms | Unmeasured | Corrections required |
| 9 | ABI / preservation | API marker updated at `b735fc0`; strengthen old-payload tests | Final gate must consume actual installed CLI/runtime; all new gates need registration | Doctor/install/freshness plus lane tests | Frozen ABI 1, additive capability 2 | Gate only | Pending final evidence |
| 10 | Hangar / Ordnance | Existing loader/install paths inspected; graph implementation pending | Structured process mechanism; immutable graph/native declaration contract | No new graph acceptance yet | Compiler remains registry-independent | Unmeasured | No |
| 11 | Stdlib boundary | HTTP and COCKPIT remain packages; full std/novelty audit pending | Manifest/import graph work | No import-side-effect regression yet | Classification only | None | No |

Current write ownership: the lead owns integration documentation, capability
markers, audit guards, workflows, and final gates. The `system_correction`
worker owns system-only changes in `v3-system-runtime-foundation` from
`0e92ce5`; `network_correction` owns TCP/HTTP changes in
`v3-networking-foundation` from `85728d2`. After completing its read-only review
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

Updated 2026-09-04. Checked items below describe landed implementation or
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
- [ ] Push the topic branch and open the requested **ready, non-draft PR**.
  The user's explicit non-draft request overrides the default draft workflow;
  it does not waive correctness or merge gates.
- [ ] Set occasional comment/CI monitoring; remain quiet on unchanged state.
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
- [ ] Verify concurrent environment snapshots cannot race ownership audit state.

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
- [ ] Close bootstrap owned-environment rejection and clock boundary findings.
- [ ] Strengthen filesystem rename/copy/metadata/size/canonical/temp/directory
  operations, explicit errors, hostile paths and Unicode path tests.
- [ ] Implement structured process spawn/wait/status/stdout/stderr/stdin/
  environment/cwd mechanisms without shell argument interpolation.
- [ ] Complete environment/path join/absolute/separator/executable path helpers.
- [ ] Separate pseudo-random values from OS secure random bytes and test failures.
- [x] Add managed TCP connect/listen/accept/send/receive/close/status/options floor.
- [ ] Close Windows binding, oversized host and slow-client review findings;
  verify repeated/large/partial traffic and exact leaked-socket audit control.
- [ ] Document and test C length-bearing versus LLVM NUL-terminated word
  boundaries without claiming identical behavior for non-equivalent raw inputs.
- [ ] Run real clean-project Hangar net/http/json HTTP-200 JSON acceptance on
  Windows and Linux; TLS remains outside the first milestone.

### COCKPIT and package ecosystem

- [x] Replace unsupported Squad/window-poll assumptions with buffer storage and
  indexed std::ui events; add initial widgets and calculator/showcase sources.
- [ ] Fix close handling, ordered input, Unicode deletion, nested layout gaps,
  allocated rectangle bounds, missing calculator addition and Clang selection.
- [ ] Finish button/label/checkbox/input/slider/panel/scrolling/dropdown/tooltip/
  modal/layout stack on frozen UI mechanisms.
- [ ] Deliver usable calculator, settings and widget showcase examples with
  bounded smoke mode separate from normal interactive operation.
- [ ] Run injected-event C/LLVM tests and a real bounded Windows window lifecycle.
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
- [ ] Keep broader TLS/GPU/Android/additional platform/package roadmap work in
  the explicitly requested future list rather than expanding the current sprint.
