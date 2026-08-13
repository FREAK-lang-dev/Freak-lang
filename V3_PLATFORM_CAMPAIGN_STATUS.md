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
  will carry a separate monotonic runtime-API capability marker. A compiler
  requiring a newer capability must reject an older same-ABI payload before
  emission/linking.
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
| 0 | Campaign command / integration | Pin base, establish ownership ledger, define first tranche | Discovery contracts pending | None yet | None | None | No |
| 1 | Word performance | Audit `word.repeated` and WordBuilder contracts | API and ABI classification pending | None yet | Expected additive runtime API | Expected exact-allocation and builder gains | No |
| 2 | Bytes / ByteBuffer | Audit current buffer ABI and production-hardening tranche | Bounds, error, ownership, and UTF-8 contracts pending | None yet | Expected additive runtime API; layout change not approved | Expected amortized growth and binary I/O gains | No |
| 3 | Performance lab | Audit benchmark harness and result schema | Depends on deterministic counters and first primitives | None yet | None | Measurement only | No |
| 4 | CLI / `+03` / LTO | Audit profile parsing, link flags, and freshness identity | Depends on benchmark lab for performance claims | None yet | None | Release-build policy only | No |
| 5 | Allocation observability | Inventory existing audit counters and missing byte/builder metrics | Runtime instrumentation contract pending | None yet | Test-only/additive instrumentation expected | Enables deterministic regression gates | No |
| 6 | System runtime | Audit filesystem/process/time/environment/random floor | First dependency-ordered slice pending | None yet | Additive runtime APIs expected | Unmeasured | No |
| 7 | Networking floor | Waiting for ByteBuffer and system-runtime contracts | Agents 2 and 6 | None yet | Additive socket APIs expected | Unmeasured | No |
| 8 | COCKPIT V3 | Waiting for mechanism inventory and buffer foundation | V3 `std::ui` and V3-compatible storage audit pending | None yet | No compiler ABI change intended | Unmeasured | No |
| 9 | ABI / preservation | Define classification and final cross-backend gates for first tranche | Implementation contracts pending | None yet | Guardian; no ownership of feature ABI | Gate only | No |
| 10 | Hangar / Ordnance | Waiting for runtime and native-package foundation inventory | Networking/native declaration design pending | None yet | No compiler ABI change intended | Unmeasured | No |
| 11 | Stdlib boundary | Classify proposals as runtime/std versus Ordnance | Proposals pending | None yet | Classification only | None | No |

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

- [ ] Exact repeated-word operation exists and is tested.
- [ ] High-performance general word construction exists.
- [ ] ByteBuffer is production-grade.
- [ ] Allocation and deterministic work counters exist.
- [ ] Permanent performance lab exists.
- [ ] `+03` exists as a FREAK optimization profile.
- [ ] LTO/ThinLTO can be tested for release builds.
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
