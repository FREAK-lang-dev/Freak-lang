# FREAK V4 release checklist

Work remaining after merged PR #136 (`main` at
`c06376799eb145595546f5fe1b7710a8fc9888d3`, 2026-10-03) toward a V4
that replaces V3. Sources: the branch itself,
`BACKEND_CHECKPOINT.md`, `docs/bootstrap-map.md` (phases A to F), every
V4-tagged missing or partial row in `freak-conformance-audit.md`, the V4
README, and `freakc-v4-00-unit-architecture.md`.

Sizes are judgment calls: **S** hours, **M** a day or two, **L** about a
week, **XL** more. "Front done" means V4 already carries the feature through
parse, HIR, TY, MIR, Meiya and editor facts, so only native lowering is
missing.

## Delivery target and evidence

The maintainer selected **Preview first (tier 1), then continue toward V3
replacement (tiers 1–4 and 8)** on 2026-10-03. A preview is complete only when
all tier-1 behavioral gates below have executable evidence. A V3 replacement
requires the later parity and bootstrap gates; this checklist does not label
the current scalar checkpoint a release.

Checked items reflect implementation and evidence, not the estimates in the
original handoff. The merged baseline already includes the scaling joins and
indexes described in [BACKEND_CHECKPOINT.md](BACKEND_CHECKPOINT.md#handoff-4-whole-module-memory-and-lookup-scaling).
`build_v4.py --compiler-opt 2` selects an optimized bootstrap compiler and
keeps its cache separate from the default smoke build. The historical large
input measurements retain their original compiler pins. The refreshed scalar
resource proof at `47f9354a0ddb434099d55a82e6dbf27a97d6dd9c` compiles all
22,403 lines / 3,200 tasks in 6.09 seconds with a native VmHWM of 596 MiB
under the unchanged 2 GiB process-tree guard, zero diagnostics in all nine
stages, real LLVM link/execute and expected exit 6. The byte-identical merged
baseline's 800-body resource fixture passed at 15.3 MiB against its fixed
128 MiB ceiling; the long-body fixture passed at 35.2 MiB.
[Refreshed scalar report](../../../benchmarks/v4/release_preview_scaling.json)
records compiler/source/module hashes. Reverify affected resource contracts
after the owned-word changes; this single size does not measure growth.

PR [#136](https://github.com/FREAK-lang-dev/Freak-lang/pull/136) merged after
[V4 CI](https://github.com/FREAK-lang-dev/Freak-lang/actions/runs/37122646691)
passed 17 jobs and [shipping CI](https://github.com/FREAK-lang-dev/Freak-lang/actions/runs/37122646705)
passed 6 jobs at `3f201b11a9cad00f9f807dc3eb73fcc792e9005b`.
Linux executed all 314 fixtures exactly once; macOS and Windows each executed
33 focused fixtures and 16 native programs, including exact CLI Hello World
and 12 negative contracts. Each platform's fast lane passed 122 guards and
transpiled all 314 fixtures exactly once. These results belong to that head;
new compiler changes require fresh verification.

The confirmed ordinary-method symbol collision merged in
[PR #138](https://github.com/FREAK-lang-dev/Freak-lang/pull/138) at
`59a27d4c30c452b0005936346d2ab55111e9692e`. Its 23 CI jobs passed at
`56e6840a4b66554d191df391d46b127aa0e798a0`, including macOS, Windows and
the guarded benchmark. Four authored collision fixtures pass at
64 MiB / 1,024 handles. The subsequent automatic review identified a
conditional optional-diagnostic cleanup failure; the independently reviewed
fix is in [PR #140](https://github.com/FREAK-lang-dev/Freak-lang/pull/140).
PR #140 merged at `af1d10b` after all 23 CI jobs passed at `807ecff`.
The follow-up [PR #142](https://github.com/FREAK-lang-dev/Freak-lang/pull/142)
passed all 23 jobs at `4a48fd7`. Reviewed successor `2424c7f` fixes subsequent
tool-image, missing-identity and cleanup-evidence findings and the confirmed HIR
memory failure. Its complete 38-method Linux benchmark passes; the 125 registered
HIR expectations passed separately at `51d960d` on unchanged compiler/runtime
sources. Current-head Mac and Windows native-backend jobs pass, while complete CI
and a new mutable-inode image finding remain pending. CodeRabbit's incremental
review was rate limited; its earlier review belongs to `51d960d`.
The earlier real parent/descendant cleanup control passes.

The integration harness now executes the three owned-word fixture groups as
13 independent resource cases, preserving 64 MiB / 1,024 handles and exact
MIR restoration/sealed-module/native outputs. Six runtime objects and all 12
source/header inputs are frozen, hashed and collision-checked by the benchmark;
its ten regressions and a real one-task LLVM link/execute pass. These are
integration checkpoints, not preview completion. The reviewed numeric emitter
`1b8e221` and repository driver `13a0991` now pass 141 compiler contracts,
147 native executions at O0/O2/O3 and eight real sanitizer/audit capability
controls. The registered numeric/restore gate adds 61 process-isolated cases
at the original limits. The long-body checked-helper fixture passes at
84.8 MiB against 128 MiB.

The repair for [#139](https://github.com/FREAK-lang-dev/Freak-lang/issues/139)
is implemented in reviewed `80520d5`: checked transactional admission precedes
retirement, repeated 13-body restores conserve handles, and malformed/pressure
failures preserve retained raw facts and sealed modules. The original numeric
snapshot now restores and produces an identical fresh module at 64 MiB and
1,024 handles. The issue remains open pending delivery and broader integration.

Interpolation's reviewed `67598fe` milestone has packed HIR v11 plans, targeted
component diagnostics and exact NUL/UTF-8 native output at O0/O2 with sanitizers
and both audits. Seven editor cases pass at `6b60100`, including first-field
navigation when tolerant recovery admits duplicate declarations. The `e492ef1`
resource fixture passes 24 restores, 42-handle growth/shrink/regrowth, decoder
conservation and transitive editor invalidation at 9.0 MiB under 64 MiB.
Nine existing HIR fixtures pass 257 expectations at `b080c64`, including v10
atomic rejection and v11 storage reuse. Reviewed transactional cold query,
expansion and HIR admission fixes are integrated. All 335 fixtures transpiled
at `55678bc`, where native HIR snapshot scaling reached 66.8 MiB against its
unchanged 64 MiB ceiling. The reviewed allocation-free scalar/prefix reads at
`ea1ebe8` preserve HIR v11 and all 122 original scaling assertions. Four exact
field-equivalence controls, the original plain scaling fixture and its complete
instrumented run pass at 64 MiB / 1,024 handles; the maximum recorded VmHWM is
65,597,440 bytes (62.56 MiB), distinct from the lower final-row value. Original
failed attempts and their stale failure-file disposition remain preserved as
historical evidence. One differential fixture is registered (342 total).
At `678fea7`, all four selected HIR/target fixtures pass their 190 registered
expectations, including the original 122-row HIR scaling fixture at its unchanged
64 MiB / 1,024-handle ceiling. The complete inventory and hosted platform gates
remain pending. At `5608f27`, all
80 selected merged word/cold/interpolation/resource/legacy-MIR cases pass,
and 129 cold-query/expansion case executions cover 42 allocation-fault positions
and one bootstrap-row failure scenario over three recovery cycles under the original
limits. This verifies the selected contracts, rather
than the complete runtime inventory or the failing HIR scaling fixture.
The W4 lowercase slice adds five registrations (340 total) and 54 focused
contracts. Its reviewed `361d110` candidate and fresh integrated `5608f27`
both pass O0/O2/O3; the integrated run includes mandatory ASan/UBSan, a
separate plain matrix and both ownership audits. Whole-inventory and platform
gates remain pending. Native aggregate fields and typed OS Result wiring remain fenced.
The explicit panic-abort compiler slice is imported with MIR v8, sealed
policy/never/CFG facts, borrowed sized messages, ordered loan validation, and
literal/dynamic short-circuit coverage. The isolated `94cb533` checkpoint
passed 188 compiler cases, 66 native executions at O0/O2/O3, and eight real
audit/sanitizer controls. Root registers 353 fixtures and links seven runtime
objects with 14 source/header inputs. Earlier six-object and fixture-count
reports above retain their historical scope. Fresh root CLI, full inventory,
resource and hosted-platform gates remain pending; default native unwinding
and runtime `trust me` honor failures remain pending.
The reviewed checked integer parser prerequisite (`433270a`) borrows a sized
UTF-8 word without allocation or legacy status mutation. Strict ASCII signed
decimal text must consume the full input and fit int64; invalid text or range
returns a private none/zero pair. Historical Linux sanitized and separate plain
O0/O2/O3 runs on source-identical committed bytes each pass six matrices, 234
semantic rows and 180 named private-boundary failures, with real ownership and
capability controls. All 1,678 retained artifact records and eight input hashes
passed independent review; these runs do not establish a fresh integrated-head
or hosted-platform result. Fifteen process-free oracle methods pass. All-OS plain
and Linux sanitizer gates are wired; public `word.to_int() -> maybe<int>` typing,
ownership, snapshot and native lowering remain pending.
The reviewed target C integer prerequisite (`2c91aa4`) exposes validated
int32/LP64-long64/Windows-long32 layout descriptors and agrees with four actual
Clang IR/object pairs. Its strengthened oracle rejects commented calls and
non-C conventions. Its fixture joins the current 342-fixture inventory. At
`678fea7`, all 64 registered target expectations and nine mandatory Clang
identity/IR/object commands pass for the four explicit targets; no foreign
binary is executed. Distinct per-target/type output keys preserve the exact
unique-output gate, and impossible unique-output registrations fail before
compilation. All-OS oracle CI is wired; hosted platform checks remain pending.
B01 native C-width admission remains fenced until target-bound typing and
lowering are complete.

Broader native words retain the owned/borrowed contracts and cleanup described
in the V4 README.
Unicode character indexing follows the bible. Root initialization is planned
as an explicit bootstrap compatibility mode with strict language mode as the default.
The maintainer selected checked native integer arithmetic at every optimization
level: overflow and division by zero report runtime errors. Checked arithmetic
and conversion native boundaries are covered; the combined row remains open
for the remaining bounds and complete compiler/platform integration gates.

`docs/bootstrap-map.md` distinguishes V3 parity from its broader A–F
bible-conformance sequence. Concurrency and advanced features that V3 never
shipped remain later gates; V3 parity does not mark A–F complete.
Release version, public tags and distribution changes wait for their executable
gates and the maintainer's release choice.

## Where the release line could sit

| Line | Tiers | What you can honestly call it |
|---|---|---|
| Preview | 1 | V4 runs real programs that compute and print |
| Self-hosted | 1, 2 | V4 compiles V4 |
| Replaces V3 | 1 to 4, 8 | "V4 release": everything V3 ships today, on the new compiler |
| Bible-complete | 1 to 8 | The 1.0 the audit describes |

The replacement line requires tiers 1–4 and 8, including the self-hosting
fixed point and V3 preservation tests. The broader A–F sequence in
`docs/bootstrap-map.md` describes complete bible conformance.

## Tier 0: done

- [x] Lexer, resilient parser, HIR, resolve, TY, MIR, Meiya, editor, snapshot, LSP facade (22 crates; 314 registered smokes at the merged baseline)
- [x] Token-boundary index (HIR 1060x, TY 138x, MIR build 488x at 1,403 lines)
- [x] Scalar locals, mutation, scoped bindings, control flow
- [x] Short-circuit `and` / `or` with ordered evaluation
- [x] Numeric conversions, float and unsigned arithmetic
- [x] Scalar associated impl methods with named arguments
- [x] Raw-pointer read/write coercions
- [x] LLVM module assembly, `build_v4.py`, native link on Linux x86_64
- [x] Literal `say` with escapes and UTF-8; C entry wrapper and argument setup
- [x] FFI surface checks: calling conventions, `@layout`, `@repr`, variadics, callbacks, `link=`, `@link_name`

## Tier 1: programs that compute and print

Scaling (from handoff 4):

- [x] **S** Module assembly memory: `word_join` or streaming in `v4_codegen_llvm_module_text`
- [x] **S** Same audit for per-body line concatenation in codegen
- [x] **M** Name index for `v4_ty_*_signature_id_for_name` (alias, route, shape, type)
- [x] **M** Index for HIR task-param owner and record lookups
- [x] **M** Index for `v4_resolve_lookup_symbol` / `lookup_any`
- [x] **S** Resource smoke: 800+ bodies under a memory ceiling; 22,403-line file completes
- [x] **S** `-O2` option for the V4 tool build in `build_v4.py`

Words (checkpoint W2 to W4):

- [ ] **L** Word locals, parameters, returns, assignment with nonCopy transfer rules
- [ ] **M** Borrowed-input contracts for read-only word intrinsics so Meiya does not move a receiver
- [ ] **M** `say` of a word value
- [ ] **M** Word `==` / `!=`, concatenation
- [ ] **M** `word_from_int`, `word_to_int`, `word_from_bool`, display conversions for `say`
- [ ] **L** Owned-word cleanup: release calls from Meiya drop and `DropIf` facts
- [ ] **M** Sanitizer lane for leaks and double release in generated code
- [ ] **M** Sized storage for embedded NUL
- [ ] **L** Interpolation: packed HIR plan, snapshot version bump, `say "x = {x}"`
- [ ] **M** Interpolation coverage: unmatched braces, shadowing, invalid paths, restore, invalidation
- [ ] **M** Word methods: `length`, `char_at`, `substring`, `starts_with`, `ends_with`, `contains`, `to_lower`
- [x] **S** Decision: byte or character semantics for index and slice (bible §7.2 specifies character semantics)
- [ ] **S** `say_err` (stderr)

Entry and build:

- [ ] **S** `main` with parameters / process arguments from FREAK code
- [ ] **M** `process::arg`, `process::args_count`, `fs::read` as typed intrinsics
- [ ] **M** Runtime panic path: message, exit code, `trust me` honor failures at runtime
- [ ] **M** Integer overflow, divide-by-zero, and bounds behavior defined and tested in native code

## Tier 2: V4 compiles V4

- [ ] **L** Root `pilot` globals with distinct HIR/TY/MIR identity (718 at `3fc7f76`)
- [ ] **L** Root statements and synthetic module-init body, run once before `main`
- [ ] **M** Explicit per-file bootstrap mode; strict mode stays default (bible 17.4)
- [ ] **M** Mode and global facts in versioned snapshots
- [ ] **L** Array-handle builtins: `array_new`, `push`, `get`, `set`, `len`, `release` (about 4,000 call sites)
- [ ] **M** `word_join` and the `word.snapshot_*` primitives
- [ ] **M** Multi-file build: flatten in `CRATE_ORDER` or real module loading
- [ ] **M** Re-run the 22-crate baseline once words and root init land; record diagnostics per crate
- [ ] **L** Meiya on error-heavy input: bounded time and memory (10 crates timed out or exceeded 2 GiB)
- [ ] **M** `freak_ty` (13,128 lines) through MIR without exceeding memory
- [ ] **L** Each crate to zero diagnostics, in dependency order
- [ ] **L** Stage 1: V4 (built by Python) compiles all crates to one native V4
- [ ] **M** Stage 2: that V4 compiles itself; outputs match (fixed point)
- [ ] **M** `check_v4.py` smokes run on the self-built compiler
- [ ] **M** Retire the Python compiler from the V4 build path

## Tier 3: native lowering for what the front end already has

Aggregates:

- [ ] **L** Target layout queries in `freak_target` (size, align, field offsets); never guessed
- [ ] **L** Shapes: struct types, construction, field read/write (front done)
- [ ] **M** Tuples: literal, slot access, destructuring (front done)
- [ ] **M** Fixed arrays `[T; N]`: literal, repeat-fill, index, destructuring (front done)
- [ ] **L** Routes and variants: tag plus payload, constructors (front done)
- [ ] **M** `@repr` discriminants and explicit discriminant values in codegen
- [ ] **L** `when`: literal, tuple, array, and payload patterns; exhaustiveness already checked
- [ ] **M** `check` / `check route`
- [ ] **L** Aggregate calling convention: by-value params and returns
- [ ] **M** `maybe<T>`: `some`, `nobody`, `check`, `or else`
- [ ] **M** `result<T, E>`: `ok`, `err`, `?`, `or else`

Methods and generics:

- [ ] **M** Impl methods with `self`, `lend self`, `lend mut self` receivers
- [ ] **XL** Generic monomorphization for tasks, shapes, routes
- [ ] **M** Doctrine-bound calls `T::method()` and UFCS in native code (front done)
- [ ] **L** `dyn Doctrine`: fat pointer plus vtable (front done)
- [ ] **M** Operator overloading in codegen: `Add` through `Neg`, `Eq`, `Ord`, `Index`
- [ ] **M** `IndexMut` (`a[i] = x`)

Ownership in generated code:

- [ ] **L** Drops for all owned types from Meiya facts, including `DropIf` runtime flags
- [ ] **M** Drop order and partial-move repair in native code
- [ ] **L** `lend` / `lend mut` native ABI (pointers), borrowed returns
- [ ] **L** `Shared<T>` / `Weak<T>`: ref-count header, clone, downgrade, upgrade
- [ ] **M** `.borrow()` / `.borrow_mut()` / `.get_mut()` runtime borrow state
- [ ] **M** Raw allocation and free; remaining honor-rank operation matrix

Collections and loops:

- [ ] **L** `List<T>`: literal, push, get, length, typed storage
- [ ] **L** `Map<K, V>`: literal, access, mutation
- [ ] **M** `Set<T>`
- [ ] **M** `for each` over lists, with pattern bindings (front done)
- [ ] **S** Decision: does `for each x in xs` consume `xs`? (Meiya currently says yes)
- [ ] **M** `repeat N times`, `training arc ... max N sessions`, `with growth`
- [ ] **M** Map and list destructuring

Closures:

- [ ] **L** Closure environment struct plus function pointer (front done for captures)
- [ ] **M** `Callable` / `MutCallable` / `OneShot` call paths
- [ ] **M** Closure return-type inference (currently `unknown`)
- [ ] **M** Nested and generic closures
- [ ] **M** Closure effect summaries so mutable writes through captures are allowed safely

Remaining token-facing boundaries (invariant: no syntax past HIR):

- [ ] **M** Impl, doctrine, extern signatures as HIR facts
- [ ] **L** MIR body families still reading tokens: patterns, initializer boundaries, places, CFG
- [ ] **S** Shrink the six allowlisted `v4_ty_type_text` consumers to zero
- [ ] **M** Editor token-at-cursor helpers moved to semantic owners

## Tier 4: everything V3 ships (the "replaces V3" line)

Language surface V3 has:

- [ ] **M** `|>` pipe
- [ ] **M** `eventually` (V3 emits inline; decide inline or true deferred)
- [ ] **M** `isekai` blocks
- [ ] **M** `foreshadow` / `payoff`
- [ ] **S** `knowing this will hurt,` / `sadly` / `for science,` prefixes
- [ ] **M** Anime operators `PLUS ULTRA`, `NAKAMA`, `FINAL FORM`, `TSUNDERE` (combined-token lexing open)
- [ ] **M** Annotations carried to codegen where V3 does
- [ ] **M** `use module::{items}`, glob imports across files
- [ ] **M** `launch` visibility in generated symbols
- [ ] **S** `done` as block terminator in all positions

Modules and packages:

- [ ] **L** Module graph query; real resolver beyond file-local (`freak_resolve` is 841 lines)
- [ ] **L** Hangar package loading in V4 builds
- [ ] **M** `launch(package)` package-private visibility
- [ ] **M** Per-module incremental invalidation

Standard library through V4:

- [ ] **L** `std::fs`, `std::process`, `std::time`, `std::math`, `std::random`
- [ ] **L** `std::json`, `std::http`, TCP
- [ ] **M** `ByteBuffer`
- [ ] **M** `std::algorithm`, `math3d`
- [ ] **L** COCKPIT UI facade (currently a V3 source preview)
- [ ] **M** `std/` files borrow-clean under Meiya

Toolchain:

- [ ] **L** `freak build` / `freak run` / `freak test` routed through V4 in the native CLI
- [ ] **M** `-o`, `--opt=N`, `--target=TRIPLE`, `--emit-llvm`
- [ ] **M** Optimization pipeline and LTO flags V3 exposes
- [ ] **M** DWARF line tables (V3 has LB10 minimal)
- [ ] **M** Diagnostics rendered with spans and source snippets on the CLI
- [ ] **L** Windows x64 native link verified
- [ ] **M** macOS arm64 native link verified
- [ ] **M** Linux arm64 native link verified
- [ ] **M** Cross-compilation for the four `freak_target` triples

Parity proof:

- [ ] **L** `tests/suite` passing on V4
- [ ] **L** V3 legacy golden corpus passing on V4 (compatibility oracle)
- [ ] **M** Differential conformance campaign (`tests/v4_differential`) widened from frontend to execution
- [ ] **M** Performance lab: V4 within an agreed factor of V3 -> C on compile time
- [ ] **M** Runtime benchmarks: V4 output at least as fast as V3 output
- [ ] **M** Conformance audit rows promoted with executable evidence; bible section 0.2 in sync

## Tier 5: bible features tagged "V4" that V3 never had

Concurrency (phase D, nothing started):

- [ ] **XL** `xm3 { branch }`, timeout, fallback
- [ ] **L** `sortie[callsign] { }` and `debrief`
- [ ] **L** `formation { }` and `formation first { }`
- [ ] **M** `Comms::open<T>()`, `Comms::buffered<T>(n)` (partial)
- [ ] **L** `BriefingRoom<T>`
- [ ] **L** `wingman` actors
- [ ] **L** `Send` / `Sync` proof for captures and `Shared`
- [ ] **M** `thread::spawn`, `Atomic<T>`, LLVM atomics
- [ ] **L** Cross-thread capture rejection in Meiya
- [ ] **M** Panic, unwind and cancellation semantics across tasks

Advanced types (phase E, nothing started):

- [ ] **L** `mood` (11 variants, compound arithmetic, `.done`), compiles to `uint8`
- [ ] **L** `prob[lo..hi]`, `.resolve()`, `.expected()`, `prob[p] chance { }`, lexer form
- [ ] **M** `prob_when`
- [ ] **L** `power<N>`, `power<over9000>`, arithmetic checks
- [ ] **L** `causality<T>`, `.write()`, `.read()`, `declare was`
- [ ] **M** `big` arbitrary precision runtime
- [ ] **M** `char` full Unicode scalar validation
- [ ] **M** `never` divergence and control-flow inference
- [ ] **M** `uint`, `tiny`, `float32` complete runtime semantics

Borrow checker completion (phase B):

- [ ] **L** General region inference beyond declared relations
- [ ] **M** `'static` binders and global-storage provenance
- [ ] **L** Lends inside lists, maps, `some` / `ok` / `err`
- [ ] **L** Lend forwarding through methods, `dyn`, callbacks, closures
- [ ] **M** Non-ordinary aggregate task parameters and returns
- [ ] **M** Alias-target, doctrine and method lend contracts
- [ ] **L** `direct_order [arch] { asm }` inline assembly

Anime layer enforcement:

- [ ] **M** `@protagonist` auto power and mood
- [ ] **M** `@nakige` and `@experiment` caller-prefix enforcement
- [ ] **M** `@side_character` death-flag tiers
- [ ] **M** `@classified` redaction, `--clearance`, debug-symbol stripping
- [ ] **S** `@rival`, `@fixed_fate`
- [ ] **S** Exactly one `@season_finale`
- [ ] **M** Narrative routes: `route TrueRoute...`, `check route`, `only on ... from result`
- [ ] **M** Foreshadow/payoff pairing as a compile error
- [ ] **M** Isekai export validation
- [ ] **M** `eventually` true LIFO on return, panic, break; `eventually if`
- [ ] **S** `trust me` count limits (more than 3 warns, more than 10 errors)
- [ ] **M** `deus_ex_machina` lowering

Error voices:

- [ ] **L** Yuuko, Sagiri, Sumika, Kasumi, Mana, Hayase, 00-Unit; finish Meiya and Takeru
- [ ] **S** `--voice=[character]`

Build modes and CLI:

- [ ] **M** `slice_of_life`, `mecha`, `shonen_jump`, `final_form`, `alternative`; `--build-mode`
- [ ] **S** `freak vibe file.fk`

Standard library additions:

- [ ] **L** `std::test`: `test "name" { expect X to be Y }`
- [ ] **M** `std::anime`, `std::narrative`
- [ ] **L** `std::os` platform modules; `result<T, OsError>`; errno / GetLastError preservation
- [ ] **L** `std::panic`: PanicInfo, unwind, `panic=abort`, `catch`
- [ ] **M** `std::regex`
- [ ] **M** `Lineup<T>`, lazy iterators `.filter` / `.collect`
- [ ] **M** `size_of<T>()`, numeric `checked_*` methods
- [ ] **M** Async `TcpSocket::connect`
- [ ] **S** `hangar search`

FFI completion (phase C):

- [ ] **M** Runtime panic-catch inside callback trampolines; panic-abort guarantee
- [ ] **M** Symbol-valued annotated locals (the phantom-local-IR limitation)
- [ ] **M** Layout annotation validation against target ABI tests
- [ ] **L** Complete cross-platform FFI ABI behavior

## Tier 6: architecture the manifesto promises

- [ ] **XL** Real attribute macro execution: hosts, hygiene, gensyms, third-party macros (`freak_expand` is identity-only)
- [ ] **M** Official anime attributes moved to plugin form; `@protagonist` out of compiler hardcode
- [ ] **L** Type-aware lint plugins
- [ ] **XL** Replace encoded-word and parallel-array internals with real shapes and arenas (possible only after tier 2)
- [ ] **L** Word arena reclamation in the bootstrap runtime
- [ ] **L** Persistent query cache across runs
- [ ] **L** Build daemon reusing HIR/MIR/codegen artifacts
- [ ] **XL** XM3 parallel query execution
- [ ] **M** Language mode in query cache keys
- [ ] **L** Incremental and cancellable parsing; stable AST node ids across edits
- [ ] **M** `IncompleteNode` coverage; autocomplete on incomplete code
- [ ] **M** Compiler panic in IDE mode becomes a diagnostic
- [ ] **L** JIT (`freak run` via OrcJIT, LB7)
- [ ] **XL** No-C-runtime path: `std::sys` with direct OS bindings (phase V4-H)
- [ ] **M** Decide the fate of `feat/v4-runtime-core` (runtime profiles and link plans)

## Tier 7: editor and IDE

- [ ] **L** `freak_lsp` over real JSON-RPC (today it is a line protocol)
- [ ] **M** References, rename, signature help
- [ ] **M** Diagnostics push on edit without full rebuild
- [ ] **L** VS Code extension (Sortie IDE phase 1)
- [ ] **M** HFML lexer and parser (MH0 to MH3)

## Tier 8: release engineering

- [x] **S** Merge `fix/v4-backend-scaling`; CI green on Linux, macOS, Windows
- [x] **M** V4 native execution lane in CI on all three platforms
- [ ] **M** Installers (`install.sh`, `install.ps1`) ship the V4 compiler
- [ ] **M** Homebrew, Scoop, Winget packages updated
- [ ] **M** Packaged runtime objects for the V4 link path
- [ ] **S** Version bump and name; `tools/release_version.py check`
- [ ] **M** Migration guide: what changes for V3 programs
- [ ] **M** README, bible section 0.2, conformance audit, V4 README all in sync
- [ ] **S** `compiler-v3-final` tag after V3's Last Sortie gates
- [ ] **M** Security review of generated-code memory safety claims before the README says "memory safe"
- [ ] **S** Rename `crates/` if you are going to (cheapest before release)
- [x] **S** Remove committed build outputs (`.exe`, `.pdb`, `.ilk` under `tests/` and `self_hosted/`): 68 baseline-verified generated files removed; authored fixtures and V3 bootstrap seed preserved

## Open decisions only the maintainers can make

1. Where the release line sits (table at the top).
2. Word indexing: bytes or characters.
3. Whether `for each` consumes its source.
4. `eventually`: inline as V3, or true deferred.
5. Revive or drop `feat/v4-runtime-core`.
6. Whether V4 keeps any C backend for compatibility (manifesto says optional).
7. Which tier 5 features are release blockers and which ship later.
