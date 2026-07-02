# FREAK Conformance Audit

**Snapshot:** v0.13.3 "Shiranui" — 2026-04-28
**Bible:** [freak-full-bible.md](freak-full-bible.md) (Alternative-4 Edition)
**Audit scope:** every testable contract in §1–§17 of the bible vs. observable behavior in `freakc/`, `src/compiler/v3/`, `src/cli/`, runtime, stdlib, and tests.
**Verdict policy:** unimplemented features default to a bible amendment tagging them **"Coming in V4"**. Code fixes are reserved for cheap wins (audit CLI wiring, missing operator doctrines, test shims). The V4 self-hosting compiler is the destination for the full bible surface.

**v0.13.x final-patch update (2026-04-28):** the cheap-win triage was executed. All 🛠 items shipped. Native `freak audit-conformance` reports clean. Suite at 14/14, no skips. LB10 minimal DWARF live. Homebrew/Scoop/Winget packaging complete. Remaining v0.13.x scope is empty — the next milestone is V4.

---

## 1. Executive summary

| Metric | Count | Notes |
|---|---|---|
| Bible sections audited | 17 (§1–§17) | + cheatsheet §15 |
| Testable contracts identified | ~445 | derived from Phase-1 exploration |
| Contracts ✅ aligned | ~150 (34%) | core syntax, primitives, basic stdlib, audit suite, Phase-1 BC, LB10 line-table DWARF |
| Contracts ⚠️ stubbed | ~108 (24%) | parsed but not enforced (anime layer, partial doctrines, Phase-1 BC default-off) |
| Contracts ❌ missing | ~187 (42%) | variants, mood/prob/power/causality, squadron, full BC, dyn dispatch, FFI surface, error voices |
| Verdict 🛠 fix code | 0 remaining | all 11 cheap fixes shipped (audit cmds, audit-conformance, Ord/Index, freak test, test_maybe + test_pipe, winget, LB10) |
| Verdict 📖 amend bible (V4 tag) | ~140 | bulk of the gaps — bible §0.2 reflects |
| Verdict ✅ already aligned | ~150 | preserved as-is |

**Top 18 divergences** (severity-ordered) — see §3 below.

**Test coverage gap:** ~50% of bible-promised features have zero automated tests. Surfaced as Appendix B; out of scope to fix in this audit but called out so we know what V4 needs to ship with.

---

## 2. Methodology

1. Read [freak-full-bible.md](freak-full-bible.md) end-to-end. Catalog every testable contract by section.
2. Read implementation across layers:
   - Python compiler (v1): [freakc/lexer.py](freakc/lexer.py), [freakc/parser.py](freakc/parser.py), [freakc/checker.py](freakc/checker.py), [freakc/emitter.py](freakc/emitter.py), [freakc/auditor.py](freakc/auditor.py)
   - V3 self-hosting: [src/compiler/v3/](src/compiler/v3/)
   - Native CLI: [src/cli/](src/cli/), [build/freak.exe](build/freak.exe)
   - Runtime: [freakc/runtime/freak_runtime.c](freakc/runtime/freak_runtime.c), [freakc/runtime/freak_llvm_runtime.c](freakc/runtime/freak_llvm_runtime.c)
   - Stdlib: [std/](std/)
3. Run the existing audit commands to capture observable signals (Appendix A).
4. Run [tests/suite/run_tests.py](tests/suite/run_tests.py) for the regression baseline.
5. For each contract: status (✅⚠️❌) + verdict (🛠 fix / 📖 amend / ✅ aligned) + bible/impl line citations.

The bible itself acknowledges (line 12) that "FREAK Lite (the Python → C transpiler) implements a subset of this. The full FREAK compiler (self-hosting, written in FREAK itself) implements all of it." This audit operationalizes that subset.

---

## 3. Top divergences

| # | Bible promise | Reality | Severity | Verdict |
|---|---|---|---|---|
| 1 | `variant` sum types with destructuring patterns | V4 parses `variant` through the route representation, carries payload constructors/patterns through TY/MIR/editor, and now pins alias-backed exhaustiveness diagnostics; backend layout still expands | 🟡 | 📖 V4 |
| 2 | `mood`, `prob`, `power`, `causality` types | No layer | 🔴 | 📖 V4 |
| 3 | `prob_when` branching | Not parsed | 🔴 | 📖 V4 |
| 4 | Pattern destructuring in `when` | V4 lowers tuple, fixed-array, and route/variant payload patterns with refutable-pattern and exhaustiveness diagnostics; broader pattern forms still expand | 🟡 | 📖 V4 |
| 5 | Squadron concurrency: `xm3`, `sortie`, `formation`, `briefing room`, `wingman` | Only `std::thread` | 🔴 | 📖 V4 |
| 6 | Full borrow checker: `lend`/`lend mut`, `'a` lifetimes, `Shared<T>`/`Weak<T>` | Phase-1 BC only (mut + move), behind `--strict-borrow` | 🟡 | 📖 split into Phase-1 (current) + V4 sections |
| 7 | `dyn Doctrine` dynamic dispatch | Not implemented | 🔴 | 📖 V4 |
| 8 | Operator doctrines `Ord`, `Index`, `IndexMut` | Only Add/Sub/Mul/Div/Neg/Eq wired | 🟡 | 🛠 fix if cheap, else 📖 V4 |
| 9 | `eventually` LIFO deferred execution | Emitted as inline block | 🟡 | 📖 clarify current; full deferred V4 |
| 10 | `payoff` strict enforcement, `isekai` export validation | Comments only | 🟡 | 📖 V4 strict mode |
| 11 | Death-flag tiers, `@nakige`/`@experiment` caller-prefix enforcement | Annotations parsed, enforcement absent | 🟡 | 📖 V4 |
| 12 | `tiny`, `uint`, `char`, `big`, `float32`, fixed `[T; N]` | Type checker knows int/num/word/bool/void only | 🔴 | 📖 V4 (add minimal aliases now) |
| 13 | Audit commands in native CLI | Python-only; `build/freak.exe` doesn't dispatch | 🟡 | 🛠 wire native CLI |
| 14 | Error voices (Meiya/Yuuko/Sagiri/Kasumi/Takeru/Mana/Hayase/Sumika/00-Unit) | Mostly generic errors | 🟡 | 📖 V4 |
| 15 | FFI surface: `extern [C]` calling conventions, `@layout`, raw pointer ops | V4 has landed substantial section-16 work; per-landing breakdown lives in [§16 below](#§16-system-boundaries-ffi). Trust-me-gated raw pointer ops, runtime panic-catch in trampoline bodies, and deeper ABI coverage still expand | 🟡 | 📖 V4 |
| 16 | Bible-promised stdlib (`std::thread`, `std::anime`, `std::narrative`, `std::test`) | Listed planned, no `.fk` files | 🔴 | 📖 confirm Planned |
| 17 | `freak vibe`, `freak test` CLI subcommands | Not in native CLI | 🟡 | 📖 OR 🛠 (`freak test` shim possible) |
| 18 | Test coverage gap (~50% of bible has zero tests) | See Appendix B | 🟡 | Out of scope; surfaced |

Bonus finding from Phase A baseline: **Python parser fails on ~30 files** (V3 self-hosting source, std/algorithm, std/runtime, math3d, several tests). Means Python (v1) and V3 compilers accept different language subsets — V3 is a superset that uses constructs (e.g. `give back` as a field name, certain bare statements) that v1 rejects. **Verdict: 📖 V4** — V3 is the compiler that conforms to bible; v1 is FREAK Lite.

---

## 4. Section-by-section conformance

Status legend: ✅ aligned, ⚠️ stubbed, ❌ missing.
Verdict legend: 🛠 code fix, 📖 amend bible, ✅ already aligned.

### §1 SYNTAX — COMPLETE REFERENCE

#### §1.1 Variables ([freak-full-bible.md:25-40](freak-full-bible.md))

| Contract | Status | Verdict | Notes |
|---|---|---|---|
| `pilot x = value` declares variable, mutable by default | ✅ | ✅ | [freakc/parser.py:900-950](freakc/parser.py); confirmed by `tests/suite/test_variables.fk` |
| `fixed pilot x = value` immutable | ✅ | ✅ | parsed and enforced |
| Type annotation optional / inferred | ✅ | ✅ | type checker infers from literal |
| `pilot mut x = ...` (Phase-1 BC) for explicit mutability under `--strict-borrow` | ✅ | 📖 | [src/compiler/v3/checker.fk](src/compiler/v3/checker.fk) — bible should mention this dual mode (default leak-everything vs `--strict-borrow`) |

#### §1.2 Functions ([freak-full-bible.md:42-71](freak-full-bible.md))

| Contract | Status | Verdict | Notes |
|---|---|---|---|
| `task name(...) -> type { ... }` | ✅ | ✅ | core feature |
| `give back` return keyword | ✅ | ✅ | |
| `say` print keyword always available | ✅ | ✅ | |
| String interpolation `"{expr}"` | ✅ | ✅ | [freakc/emitter.py:1050-1100](freakc/emitter.py) |
| Arrow shorthand `task square(x) => x*x` | ✅ | ✅ | parsed and emitted |
| `done` synonym for `}` | ✅ | ✅ | |
| Named parameters at call site `connect(host: "x", port: 80)` | ❌ | 📖 V4 | not parsed; bible promises it |

#### §1.3 Types — Primitive ([freak-full-bible.md:73-93](freak-full-bible.md))

| Contract | Status | Verdict | Notes |
|---|---|---|---|
| `num` | ✅ | ✅ | |
| `int` | ✅ | ✅ | |
| `uint` | ❌ | 📖 V4 | type checker treats as `int`; no unsigned semantics |
| `tiny` (u8) | ❌ | 📖 V4 | not in checker |
| `float` (f64) | ⚠️ | 📖 V4 | aliased to num at codegen |
| `float32` | ❌ | 📖 V4 | not in checker |
| `big` (arbitrary precision) | ❌ | 📖 V4 | no big-int runtime |
| `word` (UTF-8 string fat pointer) | ✅ | ✅ | runtime fat pointer; |
| `bool` (true/false/yes/no/hai/iie) | ✅ | ✅ | [freakc/lexer.py:130-137](freakc/lexer.py) |
| `char` (Unicode scalar 32-bit) | ❌ | 📖 V4 | no codepoint type |
| `void` | ✅ | ✅ | |
| `never` (bottom type) | ❌ | 📖 V4 | no never-type inference |
| `[T; N]` fixed-size array | ⚠️ | 📖 V4 | dynamic List<T> exists; fixed arrays not stack-allocated |
| `(A, B, ...)` tuple | ❌ | 📖 V4 | parser doesn't handle tuple types |
| `*T`, `*const T`, `*mut T` raw pointers | ⚠️ | 📖 V4 | via `extern` plus trust-me-gated deref/read/write/offset/cast operations; raw allocation/freeing still expand |

#### §1.4 Types — Compound

| Contract | Status | Verdict | Notes |
|---|---|---|---|
| `maybe<T>` with `some(x)` and `nobody` | ✅ | ✅ | C-backend cast fix landed; `tests/suite/test_maybe.fk` now PASSES |
| `result<T, E>` with `ok(x)` and `err(x)` | ✅ | ✅ | |
| `?` propagation operator | ✅ | ✅ | parsed and emitted |
| `or else default` fallback | ✅ | ✅ | |

#### §1.5 Shapes ([freak-full-bible.md:~120-200](freak-full-bible.md))

| Contract | Status | Verdict | Notes |
|---|---|---|---|
| `shape Foo { field: type }` declarations | ✅ | ✅ | |
| `impl Foo { task ... }` method blocks | ✅ | ✅ | |
| Field access `instance.field` | ✅ | ✅ | |
| `Foo { field: value }` instantiation | ✅ | ✅ | |
| Method calls `instance.method()` | ✅ | ✅ | |
| `shape::method(self)` UFCS form | ⚠️ | 📖 V4 | not commonly tested |

#### §1.6 Doctrines (Traits)

| Contract | Status | Verdict | Notes |
|---|---|---|---|
| `doctrine Name { task signatures }` | ✅ | ✅ | parsed |
| `impl Doctrine for Type { ... }` | ✅ | ✅ | |
| Operator overloading: `Add` | ✅ | ✅ | [freakc/emitter.py:1750-1800](freakc/emitter.py) |
| Operator overloading: `Sub`, `Mul`, `Div`, `Neg` | ✅ | ✅ | |
| Operator overloading: `Eq` | ✅ | ✅ | |
| Operator overloading: `Ord` (`<`, `>`, `<=`, `>=`) | ⚠️ | 🛠 wired in Python compiler (4 methods: lt/gt/le/ge); V3 emitter still missing — V4 |
| Operator overloading: `Index` | ✅ | ✅ wired in Python compiler ([freakc/emitter.py:924-934](freakc/emitter.py)); V3 emitter still missing — V4 |
| Operator overloading: `IndexMut` (`a[i] = x`) | ❌ | 📖 V4 | requires lvalue-assignment rewrite |
| `dyn Doctrine` dynamic dispatch with vtable | ❌ | 📖 V4 | no vtable codegen |
| Multi-bound generics `T: A + B` | ⚠️ | 📖 V4 | V4 parses top-level `+` bounds and carries them through TY/MIR/editor queries; dyn/object-safe surfaces still expand |
| `dyn` object-safety rules | ❌ | 📖 V4 | not implemented |

#### §1.7 Control Flow

| Contract | Status | Verdict | Notes |
|---|---|---|---|
| `if`/`else` | ✅ | ✅ | |
| `when` pattern matching with literal patterns | ⚠️ | 📖 V4 | V4 also lowers tuple, fixed-array, and route/variant payload patterns; production V3 remains narrower |
| `when` pattern destructuring `Variant::Case { field }` | ⚠️ | 📖 V4 | V4 carries payload destructuring, refutable-pattern checks, exhaustive route/variant `when`, and alias-backed duplicate/unreachable diagnostics; broader pattern ergonomics still expand |
| `for each item in list` | ✅ | ✅ | |
| `repeat N times` | ✅ | ✅ | |
| `repeat until condition` | ✅ | ✅ | |
| `training arc until cond max N sessions` | ✅ | ✅ | parsed and emitted as bounded while |
| `training arc with growth` variant | ❌ | 📖 V4 | not enforced |
| `prob_when expr { >= 0.9 -> ... }` | ❌ | 📖 V4 | not parsed |
| `break`/`continue` | ✅ | ✅ | |

#### §1.8 Closures

| Contract | Status | Verdict | Notes |
|---|---|---|---|
| `\|x\| => expr` lambda syntax | ✅ | ✅ | [freakc/emitter.py:1339-1424](freakc/emitter.py) |
| Default immutable-borrow capture | ⚠️ | 📖 V4 | no enforcement; closures capture by value |
| `copy` closure mode (thread-safe) | ❌ | 📖 V4 | parsed but no semantics |
| `move` closure (OneShot) | ❌ | 📖 V4 | parsed but no semantics |
| `mut` closure (MutCallable) | ❌ | 📖 V4 | parsed but no semantics |

#### §1.9 Pipe Operator

| Contract | Status | Verdict | Notes |
|---|---|---|---|
| `expr \|> task` left-to-right pipeline | ✅ | ✅ | desugaring routed through `_emit_call` (gets `freak_` prefix) + pipe-aware arity check; `tests/suite/test_pipe.fk` now PASSES |

#### §1.10 Error Handling — see §1.4 (maybe/result)

| Contract | Status | Verdict | Notes |
|---|---|---|---|
| `check val { got x -> ... nobody -> ... }` | ✅ | ✅ | |
| `check result val { ok(x) -> ... err(e) -> ... }` | ✅ | ✅ | |

#### §1.11 Generics

| Contract | Status | Verdict | Notes |
|---|---|---|---|
| `task name<T>(x: T)` parametric type params | ⚠️ | 📖 V4 | parsed; monomorphization via emitter is partial |
| Trait bounds `T: Doctrine` | ⚠️ | 📖 V4 | V4 enforces doctrine bounds on generic call sites and bound-method editor facts; backend/monomorphization depth still expands |
| Multi-bound `T: A + B` | ⚠️ | 📖 V4 | V4 parses and enforces multiple doctrine bounds across generic calls and bound-method tooling; broader generic depth remains |

#### §1.12 Borrow Checker — see §4 below

#### §1.13 Module System — see §6 below

#### §1.14 Variants and Aliases

| Contract | Status | Verdict | Notes |
|---|---|---|---|
| `variant Foo { Case1, Case2 { fields } }` sum types | ⚠️ | 📖 V4 | V4 parses `variant` as the route-family sum-type representation and carries cases through TY/MIR/editor/snapshot queries; final backend layout remains later |
| Pattern matching on variants exhaustive | ⚠️ | 📖 V4 | V4 diagnoses missing and unreachable route/variant arms, including alias-backed scrutinee types |
| `alias Matrix = [[num; 4]; 4]` type aliases | ⚠️ | 📖 V4 | V4 parses aliases, canonicalizes through TY/MIR, diagnoses alias cycles, and preserves editor/query facts; production V3 remains narrower |
| `fixed pilot NAME: T = const_expr` root-level constants | ⚠️ | 📖 V4 | cycle detection works; integer const chains/arithmetic, tuple/list/repeat-fill plus generic shape/route-constructor type inference, const task calls, constructor payload validation, and declared initializer mismatch diagnostics are in V4, full const-eval remains |

#### §1.15 Literals

| Contract | Status | Verdict | Notes |
|---|---|---|---|
| `[1, 2, 3]` becomes `List<int>` | ✅ | ✅ | |
| `[1, 2, 3]: [int; 3]` fixed array | ⚠️ | 📖 V4 | V4 lowers typed fixed-array literals; stack layout and deeper const semantics still expand |
| `[0; 100]` repeat-fill literal | ⚠️ | 📖 V4 | V4 lowers repeat-fill with literal and integer const arithmetic counts, including root-const inference/diagnostics; broader const-eval still expands |
| Number suffixes: `42u`, `3.14f`, `42t`, `999b` | ⚠️ | 📖 V4 | V4 lex/type layers carry suffixes; broader const-evaluation surface still expands |

---

### §2 ADVANCED TYPE SYSTEM ([freak-full-bible.md:552-739](freak-full-bible.md))

**Section verdict: 📖 entire section tagged V4.** Nothing in §2 is implemented in v0.13.x.

| §2 contract | Status | Verdict |
|---|---|---|
| §2.1 `power<N>` capability type, `power<over9000>`, `@protagonist` auto-grant | ❌ | 📖 V4 |
| §2.2 `prob[lo..hi]` distribution type, `.resolve()`, `.expected()` | ❌ | 📖 V4 |
| §2.2 `prob[0.3] chance { }` runtime probability gate | ❌ | 📖 V4 |
| §2.3 `causality<T>::new`, `.write()`, `.read()`, `declare was` | ❌ | 📖 V4 |
| §2.4 `mood` enum with 11 variants, compound arithmetic, `.done` terminal | ❌ | 📖 V4 |

---

### §3 CONCURRENCY — FULL MODEL ([freak-full-bible.md:740-834](freak-full-bible.md))

**Section verdict: 📖 entire section tagged V4 except `std::thread` reference.** None of the squadron primitives exist.

| §3 contract | Status | Verdict |
|---|---|---|
| §3.1 `xm3 { branch \|\| branch }` racing concurrency | ❌ | 📖 V4 |
| §3.1 `xm3[timeout: 500.milliseconds]` | ❌ | 📖 V4 |
| §3.1 `xm3 { } fallback { }` | ❌ | 📖 V4 |
| §3.2 `sortie[callsign: "name"] { }` structured spawn | ❌ | 📖 V4 |
| §3.2 `debrief mission` join | ❌ | 📖 V4 |
| §3.2 `formation { name: task() } debrief as` | ❌ | 📖 V4 |
| §3.2 `formation first { } debrief as winner` | ❌ | 📖 V4 |
| §3.2 `Comms::open<T>()`, `Comms::buffered<T>(n)` typed channels | ⚠️ | 📖 V4 (note: `std::sync::Channel` exists in CLAUDE.md examples) |
| §3.2 `BriefingRoom<T>::new`, `enter briefing`, `observe briefing` | ❌ | 📖 V4 |
| §3.2 `wingman ActorName { on msg(...) }` actor model | ❌ | 📖 V4 |
| `std::thread::spawn` (escape hatch) | ⚠️ | 📖 stub status — currently planned in CLAUDE.md table |

---

### §4 BORROW CHECKER — FULL RULES ([freak-full-bible.md:835-986](freak-full-bible.md))

**Section verdict: 📖 split into §4.0 Phase-1 (v0.13.x current) + §4.1+ Full Rules (V4).**

Phase-1 (currently shipped, behind `--strict-borrow`):

| §4 contract | Status | Verdict | Notes |
|---|---|---|---|
| Single-owner ownership rule | ✅ | ✅ | enforced for word, List, Map, Shapes |
| Move on assignment / function call | ✅ | ✅ | "Shirogane. You gave this away." diagnostic confirmed |
| Primitives are Copy | ✅ | ✅ | int/num/bool/tiny/char/float/float32/big copy |
| `pilot x` immutable, `pilot mut x` mutable | ✅ | ✅ | "This binding was sworn to silence." for immutable reassign |
| Default mode: leak-everything (no BC) | ✅ | ✅ | bible should make this explicit |

V4 (partially implemented unless marked otherwise):

| §4 contract | Status | Verdict |
|---|---|---|
| `lend p: T` immutable borrow parameter | ⚠️ | 📖 V4 — TY/MIR carry the contract; Meiya rejects immutable-lend writes and moves out of borrowed params |
| `lend mut p: T` exclusive mutable borrow | ⚠️ | 📖 V4 — TY/MIR carry the contract; mutable lends may write but still cannot be moved/dropped by the callee; explicit `LoanMut` paths reject overlapping live explicit loans and owner-side observations |
| `lend value` / `lend mut value` expressions | ⚠️ | 📖 V4 — MIR lowers explicit borrow rvalues and typed field/index projections through loan holders; Meiya permits writes only through `lend mut`, rejects non-Copy moves out through either holder mode, tracks projected mutable writes for liveness, rejects aliased `lend mut` call arguments and owner reads during live mutable loans, and expires sequential call-only lends at the call boundary |
| Borrowed returns `-> lend T` / `-> lend mut T` | ⚠️ | 📖 V4 — TY/MIR carry borrowed return shapes; Meiya validates direct and same-block local reloan provenance, rejects callee-owned escape and immutable-to-mutable upgrades, propagates stored borrowed-call results from explicit lend arguments through flow-sensitive caller-side local holder provenance states while preserving exact self-assignment, and still rejects forwarded call results until full interprocedural regions exist |
| Borrow-vs-move rules | ⚠️ | 📖 V4 — borrowed-parameter move blocking plus first-pass non-lexical explicit-loan rewrite and owned-move conflicts, including call arguments, all-path CFG repair proof for partial moves, statement-order-aware linear moved-local drop suppression, all-exit CFG drop suppression, and conditional `DropIf` markers for mixed moved/initialized exits with loop backedge state preservation, exist; full region inference still expands |
| Lifetime parameters `'a` | ⚠️ | 📖 V4 — lex/TY/editor diagnostics exist; full region inference remains |
| Inferred lifetimes / elision | ⚠️ | 📖 V4 — direct/same-block reloan returns use first-pass elision; ambiguous and forwarded return relationships still require explicit region solving |
| `Shared<T>` ref-counted | ⚠️ | 📖 V4 — TY/MIR recognize `Shared<T>`, `Shared<T>::new`, `.clone()`, and `.downgrade()` with receiver operands preserved as read-only call arguments; runtime counters/drop glue still expand |
| `Weak<T>` non-owning observer | ⚠️ | 📖 V4 — TY/MIR recognize `Weak<T>` and `.upgrade()` with receiver operands preserved; direct `.borrow()` / `.borrow_mut()` / `.get_mut()` on `Weak<T>` now diagnose before Meiya trusts a view |
| `.borrow()` / `.borrow_mut()` / `.get_mut()` | ⚠️ | 📖 V4 — Shared methods lower to `lend T`, `result<SharedMut<T>,BorrowError>`, and `maybe<lend mut T>`; escaping actual `SharedMut<T>` guards are rejected without rejecting `result<SharedMut<T>,BorrowError>` error paths, runtime guard state remains |
| `trust me "reason" on my honor as .level { }` honor levels (cadet/pilot/ace/commander/humanity) | ⚠️ | 📖 V4 — MIR validates the known honor ladder, rejects unknown levels, permits raw-pointer reads at `.cadet+`, requires `.pilot+` for raw-pointer writes, and requires `.ace+` for pointer offset/cast; inline asm and the full higher-rank operation matrix still expand |
| `direct_order [arch] { asm }` inline assembly | ❌ | 📖 V4 |

---

### §5 ANIME LAYER — FULL SPECIFICATION ([freak-full-bible.md:987-1250](freak-full-bible.md))

**Section verdict: split — annotations parsed (📖 V4 for enforcement); narrative debt partially tracked (auditors work).**

#### §5.1 Annotations

| Contract | Status | Verdict |
|---|---|---|
| `@protagonist` parsed; auto power<over9000> + mood.protagonist | ⚠️ | 📖 V4 (parsed; no semantic effect) |
| `@nakige` parsed; caller must use `knowing this will hurt,` / `sadly` prefix | ⚠️ | 📖 V4 (no caller enforcement) |
| `@side_character` parsed; death-flag tier monitoring | ⚠️ | 📖 V4 (no flag analysis) |
| `@experiment` parsed; caller must use `for science,` prefix | ⚠️ | 📖 V4 (no caller enforcement, but `audit-science` lists call sites) |
| `@classified` redaction with `--clearance=TOP_SECRET` flag | ❌ | 📖 V4 |
| `@rival(other)` mutual power boost | ❌ | 📖 V4 |
| `@fixed_fate` removes probability/error possibility | ❌ | 📖 V4 |
| `@season_finale` (one per codebase max) | ⚠️ | 📖 V4 (no count enforcement) |
| `@deprecated` | ✅ | ✅ |

#### §5.2 Narrative Debt

| Contract | Status | Verdict |
|---|---|---|
| `foreshadow pilot x = val` | ✅ | ✅ | parsed, comment-emitted |
| `payoff x` | ⚠️ | 📖 V4 (strict enforcement) | parsed, NOT enforced as compile error if missing |
| `freak foreshadow-audit` reports unpaid | ✅ | ✅ | [freakc/auditor.py:465-530](freakc/auditor.py) — confirmed: "6 paid, 0 unpaid" |

#### §5.3 Routes

| Contract | Status | Verdict |
|---|---|---|
| `route` keyword in lexer | ✅ | ✅ | [freakc/lexer.py:65](freakc/lexer.py) |
| `route TrueRoute, GoodEnd, NormalEnd, BadEnd` declarations | ❌ | 📖 V4 |
| `check route expr { TrueRoute -> ... }` | ❌ | 📖 V4 |
| `only on TrueRoute from result { }` route-locked scope | ❌ | 📖 V4 |

#### §5.4 Anime Operators

| Contract | Status | Verdict | Notes |
|---|---|---|---|
| `PLUS ULTRA emotion` (b * (1+e²)) | ⚠️ | 📖 V4 | parsed in tests/anime.fk; codegen unclear |
| `NAKAMA power` synergy | ⚠️ | 📖 V4 | similar |
| `FINAL FORM` squaring with build-time pause | ⚠️ | 📖 V4 | parsed; no pause |
| `TSUNDERE` inverter | ⚠️ | 📖 V4 | parsed |

#### §5.5 deus_ex_machina

| Contract | Status | Verdict |
|---|---|---|
| `deus_ex_machina "monologue ≥20 words" { body }` | ✅ | ✅ | 20-word check enforced; [freakc/parser.py:1011-1022](freakc/parser.py) |
| Suspends all safety checks within block | ⚠️ | 📖 V4 | currently a comment; checks not actually suspended |
| Logged in `freak audit-miracles` | ✅ | ✅ | confirmed: 1 deus_ex_machina found |
| >3 = warning, >10 = error | ❌ | 📖 V4 |

#### §5.6 Training Arc — see §1.7 above

#### §5.7 Isekai and Eventually

| Contract | Status | Verdict |
|---|---|---|
| `isekai { } bringing back { vars }` parsed | ✅ | ✅ | [freakc/parser.py:1024-1041](freakc/parser.py) |
| Isekai exports strictly enforced | ❌ | 📖 V4 | currently emitted as nested C scope only |
| `eventually { }` parsed | ✅ | ✅ | [freakc/parser.py:1043-1049](freakc/parser.py) |
| `eventually` LIFO deferred execution on scope exit (return/panic/break) | ❌ | 📖 V4 | currently emitted as immediate inline block — `tests/suite/test_eventually.fk` PASSES the inline interpretation |
| Multiple eventually blocks in LIFO order | ❌ | 📖 V4 |
| `eventually if cond { }` conditional cleanup | ⚠️ | 📖 V4 | parsed; semantics inline-only |

---

### §6 MODULE SYSTEM AND HANGAR ([freak-full-bible.md:1251-1313](freak-full-bible.md))

| Contract | Status | Verdict | Notes |
|---|---|---|---|
| `launch` makes item public | ✅ | ✅ | parsed and respected |
| `launch(package)` package-private visibility | ❌ | 📖 V4 | not parsed |
| Module-private (no launch) default | ⚠️ | 📖 V4 | enforcement not strict |
| `use module::{names}` | ✅ | ✅ | |
| `use module::*` glob import | ⚠️ | 📖 V4 | |
| `hangar.toml` schema (project, dependencies, build mode) | ✅ | ✅ | [src/cli/toml.fk](src/cli/toml.fk) |
| `hangar init` | ✅ | ✅ | [src/cli/hangar.fk](src/cli/hangar.fk) |
| `hangar add`, `hangar remove`, `hangar install` | ✅ | ✅ | |
| `hangar search [q]` | ❌ | 📖 V4 | no registry to search |
| `hangar version` (semver bump) | ✅ | ✅ | |
| `hangar install freak` (download compiler) | ✅ | ✅ | |

---

### §7 STD LIBRARY — COMPLETE REFERENCE ([freak-full-bible.md:1314-1668](freak-full-bible.md))

| Module | Status | Verdict | Notes |
|---|---|---|---|
| Prelude (`say`, `panic`, basic types) | ✅ | ✅ | |
| String methods (`length`, `bytes`, `split`, etc.) | ✅ | ✅ | [std/string.fk](std/string.fk) |
| `std::math` (abs, min, max, clamp, pow, sqrt, gcd, lcm, factorial, fibonacci, sin, cos, etc.) | ✅ | ✅ | |
| `std::math3d` | ✅ | ✅ | [std/math3d.fk](std/math3d.fk) |
| Numeric methods (`int::checked_add`, etc.) | ⚠️ | 📖 V4 | partial; many overflow-safe variants missing |
| `List<T>` / `Map<K,V>` / `Set<T>` operations | ⚠️ | 📖 V4 | List works; Map basic; Set NOT IMPLEMENTED |
| `Lineup<T>` FIFO queue | ❌ | 📖 V4 | not in stdlib |
| `.filter` / `.collect` lazy iterators | ❌ | 📖 V4 | List has eager methods only |
| `ask(prompt)` stdin | ✅ | ✅ | runtime |
| `say_err(msg)` stderr | ❌ | 📖 V4 | not in runtime |
| `fs::read`, `fs::write`, `fs::append`, `fs::exists`, `fs::delete` | ✅ | ✅ | C runtime |
| `TcpSocket::connect` async | ❌ | 📖 V4 | no promise type |
| `time::sleep`, duration literals | ⚠️ | 📖 V4 | sleep works; literals like `500.milliseconds` not parsed |
| `random::rand`, `random::seed` | ⚠️ | 📖 V4 | runtime present, FREAK API unclear |
| `process::run`, `process::exit` | ✅ | ✅ | runtime |
| `process::exec_capture` | ✅ | ✅ | runtime |
| `thread::spawn`, `Atomic<T>` | ❌ | 📖 V4 | std::thread Planned per CLAUDE.md |
| `std::anime` (mood/power/etc.) | ❌ | 📖 V4 | depends on §2 types |
| `std::narrative` (death flags, foreshadow logs) | ❌ | 📖 V4 | depends on §5 enforcement |
| `std::test` (`test "name" { expect ... to be ... }`) | ❌ | 📖 V4 | currently `tests/suite/run_tests.py` Python harness |
| `Shared::new`, `Weak::upgrade`, `size_of<T>()` | ❌ | 📖 V4 | depends on §4 |
| `std::ffi` C boundary types | ⚠️ | 📖 V4 | V4 normalizes core scalar aliases (`c_int`, `c_size`, `c_double`, `wchar`, etc.) through TY/codegen; target-width fidelity and the broader std::ffi surface still expand |
| `std::http` (HTTP/1.1 client) | ✅ | ✅ | [std/http.fk](std/http.fk) |
| `std::json` | ✅ | ✅ | [std/json.fk](std/json.fk) |
| `std::bytes` ByteBuffer | ✅ | ✅ | runtime |
| `std::ui` (window, widgets, themes, animation) | ⚠️ | partially shipped (Phase MA-MF), MG pending |
| `std::version` (semver) | ✅ | ✅ | [std/version.fk](std/version.fk) |
| `std::algorithm` | ✅ | ✅ | [std/algorithm.fk](std/algorithm.fk) |
| `std::convert` | ✅ | ✅ | [std/convert.fk](std/convert.fk) |
| `std::zip` | ✅ | ✅ | [std/zip.fk](std/zip.fk) |

---

### §8 LEXER ([freak-full-bible.md:1669-1740](freak-full-bible.md))

| Contract | Status | Verdict |
|---|---|---|
| All core keywords lexed | ✅ | ✅ |
| Multi-word keywords (`give back`, `for each`, `training arc`, `trust me`, `for science`, `repeat until`, etc.) | ✅ | ✅ |
| Multi-word operators (`PLUS ULTRA`, `FINAL FORM`, `NAKAMA`, `TSUNDERE`) | ⚠️ | 📖 V4 (parsed in lexer? need to verify in v3) |
| `--` line comment | ✅ | ✅ |
| `done` block delimiter | ✅ | ✅ |
| `\|\|` xm3 branch separator | ❌ | 📖 V4 (lexer treats as logical OR; xm3 not parsed) |
| `@identifier` annotation | ✅ | ✅ |
| `'identifier` lifetime | ❌ | 📖 V4 |
| `prob[lo..hi]` lex form | ❌ | 📖 V4 |
| Number suffixes `42u`, `3.14f`, `42t`, `999b` | ❌ | 📖 V4 |

---

### §9 PARSER ([freak-full-bible.md:1741-1943](freak-full-bible.md))

| Contract | Status | Verdict |
|---|---|---|
| Tolerant parsing — `ErrorNode` for invalid tokens | ⚠️ | 📖 V4 — Python parser bails; V3 parser has limited recovery |
| `IncompleteNode` for missing trailing syntax | ❌ | 📖 V4 |
| Recovery boundaries (newline, `}`, `done`, `,`, etc.) | ⚠️ | 📖 V4 |
| Codegen forbidden if ErrorNode reachable | ⚠️ | 📖 V4 — current behavior is to abort on any parse error |
| AST node has `node_id`, `span`, `kind`, `annotations`, `visibility`, `parent` | ⚠️ | 📖 V4 — partial |

Critical Phase-A finding: Python parser fails on **30+ files** including V3 self-hosting source, std/algorithm, math3d, several tests. V1 (Python) and V3 (self-hosting) parsers accept different language subsets. **Verdict: 📖 — bible should explicitly note this divergence.**

---

### §10 TYPE CHECKER — FULL RULES ([freak-full-bible.md:1944-1987](freak-full-bible.md))

| Contract | Status | Verdict |
|---|---|---|
| `power<N>` arithmetic verified | ❌ | 📖 V4 |
| `prob[lo..hi]` range tracking | ❌ | 📖 V4 |
| `causality<T>` write-broadcast tracking | ❌ | 📖 V4 |
| Mood compound arithmetic verification | ❌ | 📖 V4 |
| Route exhaustiveness | ❌ | 📖 V4 |
| Foreshadow/payoff pairing (compile-time error if unpaid) | ❌ | 📖 V4 |
| `deus_ex_machina` monologue ≥20 words | ✅ | ✅ |
| Exactly one `@season_finale` per codebase | ❌ | 📖 V4 |
| `@nakige` caller-prefix enforcement | ❌ | 📖 V4 |
| `@experiment` `for science,` prefix enforcement | ❌ | 📖 V4 |
| `@classified` redaction in output | ❌ | 📖 V4 |
| Isekai export validation | ❌ | 📖 V4 |
| Variant exhaustiveness | ❌ | 📖 V4 (no variants) |
| Type alias expansion | ❌ | 📖 V4 |
| Root-level `fixed pilot` cycle detection | ✅ | ✅ |
| Fixed array length compile-time constants | ⚠️ | 📖 V4 (literal + integer root-const arithmetic works; broader const-eval remains) |
| `dyn` object-safety rules | ❌ | 📖 V4 |
| FFI safety (FFI-safe types only in extern) | ⚠️ | 📖 V4 | V4 now rejects bare `word` / `int` extern boundaries, raw pointers to non-FFI pointees like `*const word` / `*const PlainShape`, and non-FFI-safe `@layout(...)` fields; fieldless `@repr(...)` routes/variants are accepted as FFI-safe boundary types; extern variadics now validate final-slot/ABI contracts plus scalar vararg promotion for `tiny`/`bool`/`char`/`float32`, extern callback values now invoke through MIR/LLVM, and plain task values now diagnose explicitly when they try to cross into foreign callback slots, while trust-me wrappers and panic-boundary callback rules still expand |
| Layout annotations validation | ❌ | 📖 V4 |
| Visibility rules enforcement | ⚠️ | 📖 V4 |

---

### §11 CODE GENERATION ([freak-full-bible.md:1988-2011](freak-full-bible.md))

| Contract | Status | Verdict |
|---|---|---|
| `power<N>` erased at runtime | N/A | 📖 V4 |
| `mood` compiles to uint8_t | ❌ | 📖 V4 |
| Variants → tag + payload | ❌ | 📖 V4 |
| `dyn` → fat pointer + vtable | ❌ | 📖 V4 |
| `Shared<T>` ref-count header | ❌ | 📖 V4 |
| Extern calls emit target ABI | ⚠️ | 📖 V4 |
| `deus_ex_machina` → pragma optimize | ❌ | 📖 V4 (currently plain block) |
| `isekai` → fresh stack frame | ⚠️ | 📖 V4 |
| `@classified` → debug-symbol stripping | ❌ | 📖 V4 |

---

### §12 BUILD MODES ([freak-full-bible.md:2012-2025](freak-full-bible.md))

| Build mode | Status | Verdict |
|---|---|---|
| `slice_of_life` | ❌ | 📖 V4 |
| `mecha` | ❌ | 📖 V4 |
| `shonen_jump` | ❌ | 📖 V4 |
| `final_form` (with build-time pause) | ❌ | 📖 V4 |
| `alternative` | ❌ | 📖 V4 |

Currently only `--opt=0/1/2/3` (LLVM opt levels) and `--c`/`--llvm` backend selection.

---

### §13 COMPILER CLI ([freak-full-bible.md:2026-2051](freak-full-bible.md))

| Subcommand | Status | Verdict | Notes |
|---|---|---|---|
| `freak run file.fk` | ✅ | ✅ | |
| `freak build file.fk` | ✅ | ✅ | |
| `freak check file.fk` | ✅ | ✅ | |
| `freak transpile file.fk` | ✅ | ✅ | |
| `freak test` | ✅ | ✅ shim wraps `python tests/suite/run_tests.py` |
| `freak vibe file.fk` | ❌ | 📖 V4 (or remove) |
| `freak audit-science` | ⚠️ | 🛠 wire native CLI | Python-only; native dispatch missing |
| `freak audit-trust` | ⚠️ | 🛠 wire native CLI | same |
| `freak audit-miracles` | ⚠️ | 🛠 wire native CLI | same |
| `freak foreshadow-audit` | ⚠️ | 🛠 wire native CLI | same |
| `freak audit-conformance` (NEW) | ❌ | 🛠 add | this audit's scaffolding |
| `--voice=[character]` flag | ❌ | 📖 V4 | error voices not implemented |
| `--clearance=TOP_SECRET` flag | ❌ | 📖 V4 | depends on @classified |
| `--build-mode=[mode]` flag | ❌ | 📖 V4 | depends on §12 build modes |
| `-o output_path` flag | ❌ | 📖 V4 | confirmed missing in `freak.exe help` output |

---

### §14 ERROR VOICES ([freak-full-bible.md:2052-2069](freak-full-bible.md))

**Section verdict: 📖 entire section tagged V4.** No voice routing implemented; error messages use generic phrasing. The borrow checker has signature anime phrases ("Shirogane. You gave this away.", "This binding was sworn to silence.") but they're not voice-routed by character.

| Voice | Trigger | Status | Verdict |
|---|---|---|---|
| Meiya | borrow errors | ⚠️ | 📖 V4 (Phase-1 BC has anime phrasing but not routed) |
| Yuuko | type mismatch | ❌ | 📖 V4 |
| Sagiri | power level errors | ❌ | 📖 V4 |
| Sumika | route errors / isekai scope | ❌ | 📖 V4 |
| Kasumi | @nakige missing prefix | ❌ | 📖 V4 |
| Takeru T3 | unused foreshadow | ⚠️ | 📖 V4 (foreshadow-audit has Yuuko voice in summary; not character-correct) |
| Mana | syntax errors | ❌ | 📖 V4 |
| Hayase | death-flag tier 3-4 | ❌ | 📖 V4 |
| 00-Unit | causality divergence | ❌ | 📖 V4 |

---

### §15 COMPLETE SYNTAX CHEATSHEET — derived from §1-§14, no new contracts.

---

### §16 SYSTEM BOUNDARIES — FFI ([freak-full-bible.md:2198-2390](freak-full-bible.md))

**Section verdict: ⚠️ partial in V4.**

**Landed (V4):**

- `extern` ABI metadata + calling conventions
- core `std::ffi` alias normalization
- raw-pointer LLVM carriage plus pointee-safety diagnostics
- `link="..."` library metadata
- `@link_name("...")` symbol overrides
- final extern-only `args: ...` variadics with scalar vararg promotion
- `extern [C]/[system] task(...) -> T` callback surface validation with missing-`extern` / bad-ABI / bad-payload diagnostics
- explicit plain-task-to-extern callback boundary diagnostics
- indirect callback call lowering
- `@layout(C)` / `@layout(C, packed=N)` / `@layout(transparent)` validation
- `@extern_callback("ABI")` task export with `nounwind` LLVM trampolines plus bare-reference coercion into FFI callback slots at call-arg and return-site positions
- teaching warning on known stack-unwinder extern imports (`setjmp`/`longjmp`/`_Unwind_*`/`__cxa_*`/`RaiseException`)
- `@allow_unwinder` member-level and block-level opt-out for the stack-unwinder warning
- call-site warning when a FREAK task invokes a known unwinder extern, sharing the same `@allow_unwinder` opt-out
- trust-me-free raw-pointer `.is_null()` method lowered to LLVM `icmp eq ptr %p, null`
- `trust me "reason" on my honor as .level { ... }` block parses (reason and honor clauses optional); body lowers transparently through MIR with malformed-form diagnostics
- `*ptr` raw-pointer deref read: requires `*T`/`*mut T` operand, gated on being inside a trust-me block (bible §16.4), lowers to LLVM `load <pointee>, ptr %op`; diagnoses both wrong-type derefs and outside-trust-me derefs
- `*ptr = value` raw-pointer deref write: requires `*mut T` operand (not `*T`/`*const T`), gated on being inside a trust-me block, lowers to LLVM `store <pointee> <value>, ptr <ptr>`; diagnoses non-pointer LHS, `*const`/`*` mutability mismatch, and outside-trust-me writes
- raw-pointer `.read()` and `.write(value)` method forms: lower to the same LLVM `load`/`store` operations as `*ptr` / `*ptr = value`, preserve `.cadet+` read and `.pilot+` write honor gates, diagnose const-write and arity errors, and stay out of the normal LLVM call index
- raw-pointer `.offset(n)` and `.cast<U>()` method forms: lower to LLVM `getelementptr`, preserve raw-pointer const/mut shape, require `.ace+` honor, diagnose outside-trust, low-honor, arity, missing target type, and non-integer offset cases, and disambiguate generic method calls before binary `<` / `>` lowering
- fieldless `@repr(u8|u16|u32|u64|i8|i16|i32|i64)` route/variant validation plus FFI-safe boundary acceptance

**Still V4:**

- runtime panic-catch inside the trampoline body
- raw pointer allocation/freeing helpers beyond the existing method surface
- `std::os` platform modules
- error-code translation
- deeper ABI/runtime guarantees

| Contract | Status | Verdict |
|---|---|---|
| FFI-safe types only in extern | ⚠️ | 📖 V4 | V4 rejects bare `word`/`int` extern signatures, raw pointers to non-FFI pointees, validates `extern [C]/[system] task(...) -> T` callback surfaces with explicit missing-`extern`, bad-ABI, and non-FFI callback payload diagnostics, accepts fieldless `@repr(...)` routes/variants as extern params/returns/pointer targets/layout fields, lowers indirect callback calls, rejects non-FFI-safe layout fields, and validates `@extern_callback("ABI")` task signatures against the same FFI-safety rules, but the full section-16 surface is not complete |
| `extern [C]` (and other ABIs) | ⚠️ | partial — `tests/extern_test.fk` and `tests/extern_llvm_test.fk` (failing in v1 parser per Phase-A) |
| Calling conventions: cdecl, stdcall, fastcall, thiscall, vectorcall, win64, sysv64, system | ⚠️ | 📖 V4 | V4 carries and validates the core ABI list plus duplicate/unknown-option diagnostics; final extern variadics now enforce C-compatible ABI selection, callback surface types plus indirect callback calls reuse the same ABI validation, `@extern_callback("ABI")` task exports normalize through the same list, and the executable smoke lane now proves the full matrix through direct extern calls, callback surface types, indirect callback calls, and LLVM calling-convention lowering, while panic-boundary callback rules still expand |
| `link="name"` library binding | ⚠️ | 📖 V4 | V4 carries library metadata through TY/codegen/query/LSP and diagnoses malformed or duplicate link entries |
| `@link_name("symbol")` | ⚠️ | 📖 V4 | V4 carries per-member symbol overrides through TY/codegen/query/LSP and diagnoses malformed or duplicate attributes |
| Variadic `args: ...` | ⚠️ | 📖 V4 | V4 now supports final extern-only `args: ...` signatures through TY/MIR/LLVM plus scalar vararg promotion and query/LSP/snapshot diagnostics; deeper runtime guarantees still expand |
| `@layout(C)`, `@layout(C, packed=N)`, `@layout(transparent)` | ⚠️ | 📖 V4 | V4 parses and carries all three through TY queries; it validates packed positivity, transparent single-field rules, and field-level FFI safety, but deeper ABI-stability checks still expand |
| `@extern_callback("ABI")` task export | ⚠️ | 📖 V4 | V4 validates ABI, FFI-safe parameters/return, and rejects variadics; codegen emits a `nounwind` LLVM trampoline (`@__freak_callback_<task>`) that tail-calls the FREAK body; bare references coerce into matching `extern [ABI] task(...) -> T` slots at call-arg and return-site positions; runtime panic-catch in the trampoline body remains later FFI work |
| Stack-unwinder import diagnostic | ⚠️ | 📖 V4 | V4 TY emits a warning when an extern block declares `setjmp`/`_setjmp`/`sigsetjmp`/`__sigsetjmp`, `longjmp`/`_longjmp`/`siglongjmp`, an Itanium `_Unwind_*` or `__cxa_*` primitive, or Windows `RaiseException` — matched by member name or `@link_name("...")` override; help text points users at C shims that translate to integer error codes; `@allow_unwinder` on the member or the enclosing extern block silences the warning for low-level code (kernels, JITs, coroutine engines) that genuinely needs the primitive |
| Stack-unwinder call-site warning | ⚠️ | 📖 V4 | V4 MIR fires a second warning at every call site that invokes a known unwinder extern, sharing the same `@allow_unwinder` opt-out as the declaration warning; the call-site help text mentions both the C-shim fix and the opt-out attribute |
| `@repr(u32)` discriminant size | ⚠️ | 📖 V4 | V4 now carries `@repr(u8|u16|u32|u64|i8|i16|i32|i64)` through TY, rejects bad repr kinds, payload cases, and non-constant explicit discriminants, accepts valid fieldless repr routes/variants in FFI-safe type positions, and exposes discriminant text/value plus boundary diagnostics through the smoke/query/tooling lanes; codegen-level tagged-layout guarantees still expand |
| Raw pointer ops (`*ptr`, `.read()`, `.write(value)`, `.offset()`, `.cast<U>()`, `.is_null()`) | ⚠️ | 📖 V4 | V4 lowers `.is_null()` to LLVM `icmp eq ptr %p, null` outside `trust me` (bible §16.4 explicitly permits null-checks anywhere), `*ptr` and `.read()` reads to LLVM `load <pointee>, ptr %op` gated on a surrounding `.cadet+` `trust me` block (`raw-pointer deref needs trust me block` diagnostic for derefs outside one), `*ptr = value` / `.write(value)` writes to LLVM `store <pointee> <value>, ptr <ptr>` with `.pilot+` honor gating plus `raw-pointer write needs *mut T`, type-mismatch, and method-arity diagnostics, and `.offset(n)` / `.cast<U>()` lower to LLVM `getelementptr` with `.ace+` honor gating plus arity, missing-target, and non-integer-offset diagnostics; allocation and freeing are still 🔜 V4 |
| `std::os` platform modules | ❌ | 📖 V4 |
| Error code → `result<T, OsError>` wrapping | ❌ | 📖 V4 |
| errno/GetLastError preservation | ❌ | 📖 V4 |

---

### §17 COMPILER INTERNALS AND IDE ([freak-full-bible.md:2391-2565](freak-full-bible.md))

**Section verdict: 📖 entire section tagged V4. The IDE-grade tolerant parser, incremental parsing, and node IDs are V4 work.**

| Contract | Status | Verdict |
|---|---|---|
| Panic infrastructure (PanicInfo, unwind, panic=abort) | ❌ | 📖 V4 |
| `std::panic::catch` | ❌ | 📖 V4 |
| Tolerant parsing → ErrorNode/IncompleteNode | ❌ | 📖 V4 |
| AST node IDs preserved across edits | ❌ | 📖 V4 |
| Module resolution phases 1-7 | ❌ | 📖 V4 |
| Alias cycle detection | ⚠️ | 📖 V4 | direct and generic alias loops are diagnosed in V4 TY; the full phase-5 resolution surface is still in progress |
| Constant evaluation cycle detection | ⚠️ | 📖 V4 |
| Visibility levels (module/package/universe) | ⚠️ | 📖 V4 |
| Cancellable parsing | ❌ | 📖 V4 |
| Deterministic diagnostics | ⚠️ | 📖 V4 |
| Incremental parsing | ❌ | 📖 V4 |
| Autocomplete on incomplete code | ❌ | 📖 V4 |
| Compiler panic in IDE mode → diagnostic | ❌ | 📖 V4 |

---

## 5. Triage list

### 🛠 Code fixes for v0.13.x final patch — SHIPPED

All cheap-win items below landed across commits `035b33e`–`b0a05f9` plus the v0.13.x final-patch run on 2026-04-28. Status in parentheses.

1. **Wire `audit-science` to native CLI** ✅ — [src/cli/audit.fk](src/cli/audit.fk) shells out to Python.
2. **Wire `audit-trust` to native CLI** ✅ — same.
3. **Wire `audit-miracles` to native CLI** ✅ — same.
4. **Wire `foreshadow-audit` to native CLI** ✅ — same.
5. **Add `audit-conformance` Python implementation** ✅ — [freakc/auditor.py](freakc/auditor.py) + [freakc/__main__.py](freakc/__main__.py).
6. **Wire `audit-conformance` to native CLI** ✅ — same pattern.
7. **Wire `Ord` operator doctrine** ✅ — Python emitter; V3 emitter still missing operator-overload codegen entirely (V4).
8. **Index doctrine** ✅ — already wired in Python emitter (audit doc had a small inaccuracy at first pass). `IndexMut` deferred to V4 (lvalue-assignment rewrite).
9. **Add `freak test` shim** ✅ — [src/cli/main.fk](src/cli/main.fk) wraps `python tests/suite/run_tests.py`.
10. **Fix the two SKIP'd suite tests** ✅ — `test_maybe.fk` (compound-literal cast) + `test_pipe.fk` (pipe desugaring + arity check). Suite at 14/14.
11. **Restore winget manifest + dynamic release path** ✅ — `packaging/winget/manifests/F/FREAK/freak/0.13.2/` tracked; `release.yml` derives the path from `$VERSION`.
12. **LB10 minimal DWARF** ✅ — line-tables-only debug info live in V3 emit_llvm.fk. Source-line backtraces work in gdb/lldb.
13. **Add minimal `tiny`/`uint`/`char` type aliases** — DEFERRED to V4. Touching the checker for these would sprawl into the larger numeric-type work that V4 needs to do anyway.
14. **(Optional) Add `say_err`** — DEFERRED to V4. Not blocking; current `freak_say` to stderr workaround exists via `process::exec_capture` + redirect.

**No 🛠 items remain in v0.13.x scope.** The next milestone is V4.

### 📖 Bible amendments (in scope)

Massive — every ❌ in the tables above. Aggregated changes:

A. **Add §0.1 Implementation Status matrix** at top of bible — single-source-of-truth table mapping every section to v0.13.x status (Implemented / Partial / V4).

B. **Add a "Coming in V4" admonition style** — `> **V4:** This feature ships with the V4 self-hosting compiler. v0.13.x parsers may accept the syntax but enforcement is deferred.`

C. **Per-section Status headers** — `**Status (v0.13.3): Implemented | Partial | V4**` at the top of each top-level section (§1–§17).

D. **§3 Concurrency** — wholesale V4 tag, with a small "v0.13.x: only `std::thread::spawn` available" callout.

E. **§4 Borrow Checker** — split into:
   - §4.0 Phase-1 (v0.13.x): mut + move + Copy/Move types under `--strict-borrow`
   - §4.1+ Full Rules (V4): lend, lifetimes, Shared/Weak, honor levels, direct_order

F. **§5 Anime Layer** — per-feature status; `foreshadow-audit`/`audit-miracles`/`audit-trust`/`audit-science` are ✅; everything else 📖 V4.

G. **§7 Stdlib** — confirm planned modules (`std::thread`, `std::anime`, `std::narrative`, `std::test`) as Planned. Note shipped modules (`std::math`, `std::string`, `std::convert`, `std::algorithm`, `std::json`, `std::http`, `std::fs`, `std::process`, `std::time`, `std::bytes`, `std::math3d`, `std::version`, `std::zip`, `std::ui` partial).

H. **§13 CLI** — remove or V4-tag `freak vibe`, `--voice`, `--clearance`, `--build-mode`, `-o`. Add `audit-conformance` once Phase C lands.

I. **§14 Error Voices** — wholesale V4 tag.

J. **§16 FFI** — wholesale V4 tag with note that minimal `extern` works.

K. **§17 Internals/IDE** — wholesale V4 tag.

### Out-of-scope (V4 work, surfaced for tracking)

Variants, mood/prob/power/causality, prob_when, pattern destructuring, squadron concurrency, full borrow checker, dyn dispatch, FFI surface, error voice routing, eventually-as-truly-deferred, payoff strict enforcement, isekai export validation, death-flag tiers, missing numeric types (`tiny`/`uint`/`char`/`big`/`float32`/fixed `[T;N]`), `std::thread`, `std::anime`, `std::narrative`, `std::test`, build modes, named call-site arguments, glob imports, package-private visibility, lifetime annotations, raw pointer allocation/freeing, broader layout-stability enforcement, panic infrastructure, IDE-grade tolerant parser.

---

## 6. Appendix A — Phase-A baseline output

### `python -m freakc audit-science .`
```
Found 4 'for science' call site(s):
  .claude\worktrees\nice-booth\tests\anime.fk:26: for science
  .claude\worktrees\nice-booth\tests\audit_demo.fk:40: for science
  tests\anime.fk:26: for science
  tests\audit_demo.fk:40: for science
```
(2 unique sites; worktree dupes.)

### `python -m freakc audit-trust .`
```
Found 6 'trust me' block(s):
  ... muvluv.fk:181: (.commander) — "for humanity"
  ... anime.fk:11: (.pilot) — "dirct memory access"
  ... audit_demo.fk:29: (.cadet) — "raw pointer needed for legacy C interop"
```
(3 unique sites; worktree dupes.)

### `python -m freakc audit-miracles .`
```
Found 2 deus_ex_machina block(s):
  ... audit_demo.fk:44: (38 words) — "I know this is impossible..."
```
(1 unique site; worktree dupe.)

### `python -m freakc foreshadow-audit .`
```
Foreshadow audit: 6 total, 6 paid, 0 unpaid
✓ All foreshadows paid off. (Yuuko voice: "Good. Loose ends are for lesser writers.")
```
PLUS ~30 PARSE ERRORS from V3 source files, std/, and several tests — Python parser cannot accept what V3 parser does. See findings note in §3.

### `python tests/suite/run_tests.py`
```
14 passed, 0 failed / 14 total
```
Both previously-SKIP'd tests (`test_maybe.fk`, `test_pipe.fk`) now PASS after the v0.13.x cast + pipe-arity fixes landed in `freakc/emitter.py` and `freakc/type_checker.py`.

### `build\freak.exe build tests/hello.fk`
Both LLVM (default) and `--c` backends built `tests/hello.exe` successfully.
Note: native CLI has no `-o` flag — output path is fixed to source-file basename + `.exe`.

### `build\freakc_v3.exe tests/borrow_move_basic.fk --strict-borrow --c`
```
[3/4] Borrow checking...
borrowck: Shirogane. You gave this away. It no longer belongs to you. 'ship' (line 19)
aborting: 1 error(s) found
```
Phase-1 BC working as advertised.

---

## 7. Appendix B — Bible contracts with no automated test

This is where V4 will need test coverage. **Out of scope for this audit; surfaced for V4 milestone planning.**

- §1.6 doctrines: 0 standalone tests
- §1.11 generics: 0 tests
- §1.13 module imports: 0 tests
- §1.14 variants/aliases: 0 tests (variants don't exist)
- §2.1 power<N>: 0 tests
- §2.2 prob[lo..hi]: 0 tests
- §2.3 causality<T>: 0 tests
- §2.4 mood: 0 tests
- §3.1 xm3: 0 tests
- §3.2 squadron: 0 tests
- §4 borrow checker: 5 tests, **not in CI**
- §5.2 foreshadow: only `audit_demo.fk`, no error cases
- §5.3 routes: 0 tests
- §5.4 anime operators: `tests/anime.fk` only
- §5.5 deus_ex_machina: only `audit_demo.fk`
- §5.7 isekai/eventually: 2 files, no error cases
- §6.1 module visibility: 0 tests
- §6.2-3 hangar: manual smoke only
- §7.1-9 stdlib: piecemeal coverage
- §16 FFI: `extern_test.fk` and `extern_llvm_test.fk` (both fail Python parser per Phase A)
- §14 error voices: 0 tests
- §17 IDE/parser tolerance: 0 tests

Roughly half of bible-promised features have zero automated tests — V4 will need to ship these alongside the implementations.

---

*"It was always going to end this way."*
*— freak-ui mono_no_aware theme, on program exit*
