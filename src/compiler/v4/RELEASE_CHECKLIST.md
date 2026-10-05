# FREAK V4 release checklist (revision 3.1)

Working revision reconciled on 2026-10-05 against merged `main` at
`116dae0ddea810252f1ad8af0ac71fddc0594c2f`. PR #143 is merged with a regular
merge commit preserving all 249 original commits. The reviewed head was
`4ddde2d47303358d69f34f616fedd7a0827e2ea5`; its tree is identical to the
merge tree. Historical observations below retain their original pins.

Sources: `main` itself, PR #143, `BACKEND_CHECKPOINT.md`,
`docs/bootstrap-map.md` (phases A to F), every V4-tagged missing or partial
row in `freak-conformance-audit.md`, the V4 README,
`freakc-v4-00-unit-architecture.md`, the post-HIR architecture roadmap, and
the TY / TIR / MIR split plan.

Sizes are judgment calls: **S** hours, **M** a day or two, **L** about a
week, **XL** more. "Front done" means V4 already carries the feature through
parse, HIR, TY, MIR, Meiya and editor facts, so only native lowering is
missing.

## Delivery target and reconciled evidence

The maintainer selected **Preview first (Tier 1), then V3 replacement**.
Revision 3.1 adds A0, A1 and A4 to the replacement prerequisites. Capability
and architecture work proceed in bounded lanes; strict root scope remains
the default and compiler initialization requires explicit per-file bootstrap
compatibility. Integer overflow produces a runtime error at every optimization
level; Word indexing and slicing use character semantics. The public release
remains `0.14.2`; no version bump or release tag is authorized by this checklist.

All [20 V4 jobs](https://github.com/FREAK-lang-dev/Freak-lang/actions/runs/37239273024)
and [six shipping jobs](https://github.com/FREAK-lang-dev/Freak-lang/actions/runs/37239273042)
passed at `4ddde2d`, including Linux, macOS and Windows. Independent source,
current-head CI and actual postmerge history reviews are CLEAR. All twelve
review threads were resolved. These are reviewed-head hosted checks plus an
identical-tree merge proof, not a separately executed postmerge workflow.
Earlier Word715@`4e3847c`, Sum76/native30@`2ece941`, typed439@`376e477` and
focused19@`bea7372` receipts retain their actual revisions and qualified input
transfers. Green gates do not prove renewed speed or asymptotic growth rates.

Checked capability rows below cover the admitted owned-Word and closed scalar
Sum slices. General aggregates, arbitrary source-main parameters, default
panic unwind/cleanup, self-hosting, full V3 parity and distribution remain open.
The private C panic-context proof establishes only its helper ABI scope.

Next bounded batch, after this reconciliation is committed:

1. A0: enforce and document the `freak_mir` authority/construction boundary.
2. Enforce training-session caps with condition-first tests, a distinct counter
   and an increment epilogue used by `continue`; retain existing diagnostics.
3. Close fully returning ordinary conditional chains before MIR publication,
   retaining diagnostics for later source and strict snapshot/CFG admission.

The remaining correctness rows and A4 Runtime MIR transform stay separately
tracked. The reviewed U0 unwind plan must integrate with A4 ownership facts;
new cleanup policy must not be added to codegen.

## What changed in revision 3.1

Corrections found while writing Part I of The Freak Book, where every V4
statement is a program run at a pinned commit. Checked on `main` at
`7c9a1f3c` (11 commits after the revision 3 baseline; the code involved is
unchanged between the two) and on PR #143 at its current head `44f63bc4`.
Those are the incoming document's historical pins. The reconciled dispositions
above use the final reviewed head `4ddde2d` and merged `116dae0` instead.

- **A tier 0 tick was wrong.** `training arc ... max N sessions` runs
  natively, but the session cap is never enforced. The tick is split and
  the cap is a tier 1 correctness item.
- Eight more tier 1 correctness items. The one that will bite first: an
  `if` / `else if` / `else` chain in which every branch gives back does not
  build. The others: a num silently truncated into an int, `0xFF` read as 0,
  `fixed pilot` not enforced, unknown names reported only by codegen, tasks
  without a return type, `sessions` as a pilot name, and inner-block
  shadowing.
- One tier 4 item: the scalar conversion methods (`to_num()` and the rest).
- `with growth` (tier 3) is ticked: it runs natively and its mutation check
  rejects a stalled body.
- Three open decisions added (12 to 14) and one migration note (tier 8).

## What changed in revision 3

- The TY / TIR / MIR split plan is folded into the architecture lane:
  a `freak_mir` guard (A0), `freak_mir_transform` (A4), an ephemeral TIR
  view (A2), and `freak_ty_build` deferred behind a decision (A5).
- **A1 was undercounted.** Revision 2 counted syntax reads in MIR Build
  only. `freak_ty` also sits past HIR and reads tokens. The corrected total
  is 323 token reads (200 in MIR Build, 123 in TY), plus 42 stream and tree
  identity checks, 41 of them in TY.
- The architecture lane now has an order, and `freak_mir_transform` is
  first in it, because PR #143 put drop placement inside codegen.
- Tier 1 carries the PR #143 merge blockers from handoff 7 and marks which
  word items already run on that branch.
- Corrected a claim from revision 2: Meiya is super-linear on long bodies
  on `main`, not only TY.

Revision 2 (2026-10-04, `59a27d4`) added the architecture lane, moved tier 1
scaling to done, and recorded the `|>` finding.

## Where the release line could sit

| Line | Tiers | What you can honestly call it |
|---|---|---|
| Preview | 1 | V4 runs real programs that compute and print |
| Self-hosted | 1, 2 | V4 compiles V4 |
| Replaces V3 | 1 to 4, 8, A0, A1, A4 | "V4 release": everything V3 ships today, on the new compiler |
| Bible-complete | 1 to 8, A0 to A4 | The 1.0 the audit describes |

The replacement line follows `docs/bootstrap-map.md`: self-hosting, shipped-V3
language/runtime/tooling parity and preservation tests must hold. It does not
require the concurrency and advanced bible features V3 never shipped. Phases
A to F describe the broader bible-complete target.

## Two lanes

The roadmap orders all architecture work before any new capability.
Followed literally, V4 would compile no program it cannot compile today for
that whole stretch. This checklist runs them as two lanes instead:

- **Capability lane**: tiers 1 to 4, in order. Each step makes a new
  program compile and run.
- **Architecture lane**: A0 to A5 below, in bounded slices, in parallel.

One rule joins them: **every new native capability lands with its sealed
MIR fact and its Meiya fact. Codegen never infers meaning or ownership.**
The merged Word slice still places drops in codegen and has eight direct
Meiya call sites at `116dae0`; A4 repays this ownership boundary debt.

How the two planning documents map onto this checklist:

| Roadmap | Split plan | Here |
|---|---|---|
| | Phase A, M1: formalize the MIR split | A0 |
| M1 No syntax past HIR | Phase C, M3 | A1 |
| M2 No type text past TY | Phase D and E, M4 and M5 | A2 |
| M3 Seal MIR semantics | Phase G, M6 | A3, plus the lane rule |
| M4 Meiya ownership contracts | Phase H, I, J; M7 and M8 | A4 |
| | Phase B, M2: `freak_ty_build` | A5 (deferred) |
| | M9 inference and solver split, M10 persistent TIR | not planned |
| M5 Aggregate and word backend | | Tier 1 words, tier 3 aggregates |
| M6 ABI completion | | Tier 3 "C ABI" |
| M7 Monomorphization | | Tier 3 "Methods and generics" |
| M8 Self-hosting | | Tier 2 |

Both documents' anti-rewrite rule stands: no new persistent IR unless the
existing chain provably cannot express the fact. TIR stays a view.

## Tier 0: done

- [x] Lexer, resilient parser, HIR, resolve, TY, MIR, Meiya, editor, snapshot, LSP facade (22 crates, 58,712 lines, 318 smokes)
- [x] Token-boundary index (HIR 1060x, TY 138x, MIR build 488x at 1,403 lines)
- [x] Scalar locals, mutation, compound assignment, scoped bindings, control flow
- [x] Short-circuit `and` / `or` with ordered evaluation
- [x] Numeric conversions, float and unsigned arithmetic
- [x] Scalar associated impl methods with named arguments
- [x] Raw-pointer read/write coercions
- [x] LLVM module assembly, `build_v4.py`, native link on Linux x86_64
- [x] Literal `say` with escapes and UTF-8; C entry wrapper and argument setup
- [x] FFI surface checks: calling conventions, `@layout`, `@repr`, variadics, callbacks, `link=`, `@link_name`
- [x] Module assembly memory: collected pieces joined once
- [x] Per-body line concatenation in codegen
- [x] Name indexes for TY signature lookups (alias, route, shape, type)
- [x] Indexes for HIR task-param owner and record lookups
- [x] Index for resolve symbol lookup
- [x] Scaling guard: benchmark lane in CI; 22,403 lines complete in 6.3 s at 597 MiB
- [x] `--compiler-opt 0|1|2|3` for the V4 tool build in `build_v4.py`
- [x] Handoff 6 correctness: nested counted loops, literal delimiters, zero-argument callbacks, bool synonyms, diagnostic restore, empty-file reads
- [x] Named errors for every unsupported native rvalue, place and type (no invalid LLVM published)
- [x] Duplicate LLVM body symbols rejected before publication, with and without callbacks
- [x] Extern symbol collisions with bodies, literals and `main` rejected by name
- [x] C boundary fence: only pointer-sized integers, floats, void and raw pointers admitted; other C widths fail by name
- [x] Build refuses an output path that names the input source
- [x] Extern-member return types as HIR facts (HIR snapshot v10)
- [x] `repeat N times` on scalars, native
- [x] `training arc until cond` loop and condition on scalars, native (the `max N sessions` cap is **not** enforced: tier 1)
- [x] `when` on integer literals, native
- [x] `fix/v4-backend-scaling` merged to `main`
- [x] `freak_mir` holds no lowering code and no forbidden upstream/later-stage references; A0's registered guard is implemented

## Architecture lane

Unless qualified below, historical progress numbers are from `9d6270c5`.
The A1 source-text inventory was refreshed against merged `116dae0`; its
syntax-facing helper calls are counted separately from identity checks.
Performance observations retain their original source pins.

Order:

1. PR #143 is merged at `116dae0`; its 249 original commits are preserved.
   New crate work starts from this actual merged baseline.
2. A0, the `freak_mir` guard. Hours.
3. A4, starting with `freak_mir_transform`.
4. A1, counting TY as well as MIR Build.
5. A2, then the TIR view on top of it.
6. A5 decision.

A3 has no slot of its own; the lane rule finishes it as capabilities land.

### A0: `freak_mir` is an authority, not a lowering engine (split plan phase A)

`freak_mir` makes no lexer, parser, expansion, HIR or Resolve calls and defines
no lowering tasks. The registered A0 guard now keeps that boundary enforced.

- [x] **S** Exact guard in `check_v4.py`: `freak_mir` may not reference `v4_lex_`, `v4_parse_`, `v4_expand_`, `v4_hir_`, `v4_resolve_`, `v4_borrowck_` or `v4_codegen_`; builder-owned task references are rejected as well. Registered boundary checks and adverse direct/function-valued controls pass
- [x] **S** Document the `freak_mir` / `freak_mir_build` contract in the V4 README (who owns ids, records, snapshots; who owns lowering)

### A1: no syntax past HIR (roadmap M1, split plan phase C)

Two crates past HIR still read tokens. MIR and Meiya do not. Codegen retains
one `v4_lex_is_digit` helper call, separately tracked below.

| Crate | Token reads | Identity and revision checks | Allowlist in the gate |
|---|---|---|---|
| `freak_mir_build` | 219 | 1 | yes, exact and shrinking |
| `freak_ty` | 126 | 41 | none |
| Total | 345 | 42 | |

The most-used helpers:

| Helper | MIR Build | TY |
|---|---|---|
| `v4_lex_token_syntax_value` | 132 | 49 |
| `v4_lex_token_type` | 64 | 35 |
| `v4_lex_token_value` | 8 | 13 |
| `v4_parse_extern_member_*` and `v4_parse_extern_abi_*` | 0 | 10 |

TY's 41 identity and revision checks (`v4_parse_stream_id`,
`v4_lex_stream_revision`, `v4_parse_tree_exists` and similar) do not read
syntax; they check that a snapshot still matches its stream.

Editor, snapshot, driver and LSP crates also call the lexer and parser.
Those are source-facing by design and are not counted here.

Each slice follows the migration rule: pick one bounded family, store
normalized facts in HIR, snapshot and restore them, expose accessors, make
the consumer use them, add a guard, remove one allowlist entry.

- [ ] **S** Add an exact, shrinking allowlist for `freak_ty`, like the one MIR Build has
- [ ] **M** Impl return declarations as HIR facts
- [ ] **M** Doctrine return declarations as HIR facts
- [ ] **M** Non-ordinary parameter signatures as HIR facts
- [ ] **M** Extern-member attributes and ABI options as HIR facts (TY reads their token ranges directly)
- [ ] **M** Method type arguments
- [ ] **M** Raw-pointer instance-method and associated-method type facts
- [ ] **M** Shape and route constructor heads
- [ ] **M** Route-case expression facts
- [ ] **L** Pattern facts needed by MIR Build
- [ ] **M** Initializer-boundary facts
- [ ] **M** Place facts
- [ ] **M** CFG-relevant structural facts currently rediscovered from tokens
- [ ] **M** Remaining token-facing type families in TY
- [ ] **S** Put TY's identity and revision checks behind one reviewed shim
- [ ] **S** Remove the stray `v4_lex_is_digit` call in codegen
- [ ] **M** Editor token-at-cursor helpers moved to semantic owners
- [ ] **S** Finish: lexer and parser families are empty in both allowlists

### A2: no type text past TY (roadmap M2, split plan phases D and E)

Bigger than either document suggests. Types cross every later boundary as
words: `v4_mir_local_ty`, `v4_mir_place_ty` and `v4_mir_rvalue_ty` all
return `word`, and Meiya and codegen read them at **108 call sites** and
compare type spellings against string literals **36 times** (34 in
codegen). PR #143 raises the reads to 162. Replacing this with `TypeId`
changes the stored representation in MIR, Meiya, codegen and the snapshot
formats that carry them. It overlaps the tier 6 item "replace encoded-word
internals".

- [ ] **S** Size it: inventory every type-word read past TY, grouped by what question it asks
- [ ] **M** `TypeId` table owned by TY, with snapshot, restore and validation
- [ ] **M** Semantic accessors beside the textual ones: expression type, call callee, call signature, substitution, region, coercion
- [ ] **L** MIR stores `TypeId` for locals, places, rvalues, signatures
- [ ] **M** Meiya asks typed questions (is Copy, is lend, element type) instead of parsing spellings
- [ ] **M** Codegen selects LLVM types from `TypeId`, not from `ty == "float"`
- [ ] **S** Remove the six `v4_ty_type_text` call sites in MIR Build
- [ ] **M** Remove the remaining type-text helpers past TY (about 25 call sites: function return text, fixed-array length text, integer-literal text, signature display)
- [ ] **S** Guard: no `-> word` type accessor is reachable from MIR, Meiya or codegen

Ephemeral TIR (only after the accessors above exist):

- [ ] **M** Typed-expression view built per lowering request from HIR, Resolve and TY: callee, signature, receiver, argument types, result type, substitutions, coercions, all as ids
- [ ] **L** MIR Build lowers from the view instead of making repeated TY lookups
- [ ] **S** Guard: the view has no snapshot, no restore, no query family and no editor facts

Promote TIR to a persistent IR only on evidence: a measured incremental
win, an editor need for typed-expression identity, or more than one
consumer of the same typed graph.

### A3: no unresolved semantics past MIR (roadmap M3, split plan phase G)

Enforced by the lane rule as capabilities land. Standing items:

- [ ] **M** Sealed symbol identity: each callable body gets its canonical LLVM identity in MIR, so codegen receives it instead of detecting collisions after lowering
- [ ] **M** Exact callee, method, associated-task and operator identity on every call
- [ ] **M** Explicit coercion and conversion rvalues (no implicit widening decided in codegen)
- [ ] **M** Named-argument order resolved before MIR
- [ ] **M** Generic substitutions recorded per call (prerequisite for monomorphization)
- [ ] **M** Closure capture modes and route discriminant values as MIR facts
- [ ] **S** Guard: codegen makes no HIR calls (it makes none today; keep it so) and no TY name lookups

### A4: no ownership ambiguity past Runtime MIR (roadmap M4, split plan phases H to J)

MIR has three lifecycle states that share one storage: Built (from MIR
Build), Analysis (Built plus Meiya's side facts), and Runtime (after
`freak_mir_transform`, with every drop explicit). They are states, not
three serialized formats.

`freak_mir_transform`, the new stage between Meiya and LLVM. Do this first
in the lane:

- [ ] **S** Runtime MIR contract written down: what it contains, what it may no longer ask
- [ ] **L** `freak_mir_transform` crate: turn Meiya's drop facts into explicit `Drop` and `DropIf` statements and cleanup blocks
- [ ] **M** Move word drop placement out of codegen (drops at return, on reassignment, of temporaries); codegen's calls into Meiya go to zero
- [ ] **M** Runtime drop flags for values moved on only some paths
- [ ] **S** Runtime MIR validation; analysis-only pseudo operations are gone before codegen
- [ ] **S** The stage is reported by `v4_scale_bench.py` and stays linear on the `long` shape
- [ ] **S** Guard: the crate references no lexer, parser, HIR, Resolve or LLVM emission
- [ ] **S** No Runtime MIR snapshot until a consumer needs one

Meiya, remaining:

- [ ] **M** Sealed queries for the transform: is moved, needs drop, drop mode, drop flag required, loan set, return-loan origins, cleanup requirement
- [ ] **L** Aggregate-aware ownership, including partial move and drop interaction
- [ ] **M** Closure-environment ownership contract
- [ ] **M** Receiver and lend ABI ownership rules
- [ ] **L** Generic ownership after monomorphization
- [ ] **M** Panic-path ownership facts (once unwinding exists)
- [ ] **S** Guard: codegen performs no borrow, move or liveness analysis

### A5: `freak_ty_build` (split plan phase B, deferred)

`freak_ty` is 13,701 lines and 794 tasks, and mixes construction with
storage. Splitting it is a file move plus a guard: all crates are flattened
into one file before compiling, so the split buys no compile boundary and
no capability, and it touches most open branches. After A1 removes TY's
token reads the builder half is smaller and the line between the halves is
obvious.

- [ ] **S** Decision, after A1: split `freak_ty` or leave it whole
- [ ] **L** If split: move construction families one at a time, keeping ids, accessors and snapshots in `freak_ty`, with a guard per move

Not planned: `freak_ty_infer` and `freak_ty_solve` sub-crates, and a
persistent TIR. Both documents make them conditional on evidence that does
not exist yet.

## Tier 1: programs that compute and print

Historical "on #143" annotations refer to earlier branch observations.
The completed rows here are reconciled to the merged checkpoint and its
qualified evidence above; incomplete contracts remain unticked.

PR #143 handoff-7 dispositions and remaining performance work:

- [x] **M** Resolve the four handoff-7 Meiya smoke failures with exact ownership and diagnostic proofs. False LocalID/PlaceID collisions are removed; genuine repeated-loop-consumption and borrowed-return errors retain their messages, help, spans and drop facts
- [x] **S** Raw-pointer write range behavior: checked failure; exact legacy native/variadic-promotion proofs migrated, including the named int-to-tiny out-of-range native control. Wider native C variadic admission remains fenced
- [x] **S** Repair six stale smoke proofs for canonical LocalID/PlaceID facts, ordered short circuit, wire/native graph and literal/general say; preserve the semantic contracts and exact diagnostics
- [ ] **M** Generated code is 4x to 6x slower: emit overflow intrinsics inline instead of calling the numeric runtime for `+ - *`
- [ ] **S** Runtime benchmark in the gate, so generated-code speed cannot regress unnoticed
- [ ] **M** Compile time is 1.7x to 2.6x slower and codegen is super-linear on long bodies (0.26 s to 5.80 s at 8,243 lines)
- [x] **S** Integrate current main, resolve merge conflicts and complete all current-head gates; regular merge delivered with the original history preserved

Correctness:

- [ ] **M** `|>`: the pre-Word baseline silently dropped it (`3 |> inc |> dbl` returned 3 with zero diagnostics); merged `116dae0` rejects it only as `native rvalue not yet supported: Unknown`. Lower it, or reject it by name
- [ ] **S** `training arc ... max N sessions`: the cap is type-checked and then dropped. `v4_mir_lower_training_arc_stmt` lowers the cap expression, checks it is numeric, and wires a plain condition loop with no session counter. `training arc until drills > 10 max 3 sessions { drills += 1 }` leaves `drills` at 11 on `main` and on #143; V3 and bible §5.6 give 3. A condition that never becomes true does not terminate. Add the counter local and the `sessions < N` test, and a smoke that fails when the cap is ignored
- [ ] **M** An `if` / `else if` / `else` chain in which every branch gives back does not build: `mir cfg unreachable live block|sign block 5 has no predecessors but still carries live statements or control flow`. A plain `if` / `else` with both branches giving back works, and the chain works when the last `give back` follows it. Same on #143. This is the usual shape of a task that classifies a value
- [ ] **S** A num is accepted where an int is required (initialiser, assignment, argument, return value) and the fraction is dropped with no diagnostic: `pilot n: int = 2.5` gives 2. V3 rejects all four. Same on #143. Reject it, or make the narrowing an explicit conversion rvalue (A3, "no implicit widening decided in codegen")
- [ ] **S** `0xFF` is read as `0` with no diagnostic on `main`; on #143 it is rejected, but only as `native rvalue not yet supported: Unknown`. The bible defines no hexadecimal literal. Reject it by name in the lexer
- [ ] **S** `fixed pilot` is accepted and can be reassigned (`fixed pilot fuel = 50` then `fuel = 75` gives 75; same on #143). Bible §1.1 says it cannot be
- [ ] **S** An unknown name is reported only by codegen, as `native type not yet supported: unknown`, with no span and no name. Same for a call to an unknown task. Resolve or TY should report it by name (same on #143)
- [ ] **S** A task with no return type (`task greet() { ... }`, and `task main()`) fails with that same codegen message. Accept it as `-> void` like V3, or reject it by name (decision 13)
- [ ] **S** `sessions` is accepted as a pilot name, and a `training arc` heading that uses it (`until sessions >= 3 max 10 sessions`) then fails as `native rvalue not yet supported: Unknown`, because the heading is found by searching for the first `sessions` token. V3 reserves the word. Reserve it, or match the heading from the right
- [ ] **S** A `pilot` in an inner block with the name of an outer pilot is rejected as `duplicate local declaration`. V3 allows the shadow (decision 12; same on #143)
- [ ] **S** Sweep the remaining tier 4 surface forms for the same failure (accepted, no diagnostic, wrong code). `eventually`, `isekai` and `PLUS ULTRA` are rejected today, though with misleading messages. The `training arc` cap above was found this way

Scaling (residual, on `main`):

- [ ] **M** TY grows 3.2x to 3.6x per doubling at the largest benchmark sizes; 0.78 s at 22,403 lines
- [ ] **M** Meiya grows 3.6x per doubling on long bodies; 2.82 s at 8,243 lines

Words (checkpoint W2 to W4):

- [x] **L** Word locals, parameters, returns, assignment with nonCopy transfer rules
- [x] **M** Borrowed-input contracts for read-only word intrinsics so Meiya does not move a receiver
- [x] **M** `say` of a word value
- [x] **M** `say` of an int, bool or num value; explicitly typed `float` retains its named native fence
- [x] **M** Word `==` / `!=`, concatenation
- [x] **M** `word_from_int`, `word_to_int`, `word_from_bool`, display conversions for `say`
- [x] **L** Owned-word cleanup: release calls from Meiya drop and `DropIf` facts; currently placed by codegen from Meiya facts; extraction to the Runtime MIR transform remains A4
- [x] **M** Sanitizer lane for leaks and double release in generated code
- [x] **M** Sized storage for embedded NUL
- [x] **L** Interpolation: packed HIR plan, snapshot version bump, `say "x = {x}"`
- [x] **M** Interpolation coverage: unmatched braces, shadowing, invalid paths, restore, invalidation
- [x] **M** Word methods: `length`, `char_at`, `substring`, `starts_with`, `ends_with`, `contains`, `to_lower`
- [x] **S** Decision: character semantics for index and slice, as the bible says
- [x] **S** `say_err` (stderr)

Entry and build:

- [ ] **S** Source `main` with parameters: ABI decision and lowering remain open; typed process-argument access and C entry setup are implemented
- [x] **M** `process::arg`, `process::args_count`, `fs::read` as typed intrinsics
- [ ] **M** Complete default compiler panic unwind/cleanup and runtime honor failures; explicit abort/message/status plus checked overflow, divide-zero and bounds paths are implemented
- [x] **M** Integer overflow, divide-by-zero, and bounds behavior defined and tested in native code

## Tier 2: V4 compiles V4

- [ ] **L** Root `pilot` globals with distinct HIR/TY/MIR identity (about 700 in the crates; V4 rejects a top-level `pilot` today)
- [ ] **L** Root statements and synthetic module-init body, run once before `main`
- [ ] **M** Explicit per-file bootstrap mode; strict mode stays default (bible 17.4)
- [ ] **M** Mode and global facts in versioned snapshots
- [ ] **L** Array-handle builtins: `array_new`, `push`, `get`, `set`, `len`, `release` (about 4,700 call sites)
- [ ] **M** `word_join` and the `word.snapshot_*` primitives
- [ ] **M** Multi-file build: flatten in `CRATE_ORDER` or real module loading
- [ ] **M** Re-run the 22-crate baseline once words and root init land; record diagnostics per crate
- [ ] **L** Meiya on error-heavy input: bounded time and memory (10 crates timed out or exceeded 2 GiB at the last baseline; not re-measured since)
- [ ] **M** `freak_ty` (13,701 lines) through MIR without exceeding memory
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
- [ ] **L** `when`: tuple, array, and payload patterns; exhaustiveness already checked
- [ ] **M** `check` / `check route`
- [ ] **L** Aggregate calling convention: by-value params and returns
- [ ] **M** General `maybe<T>`: `some`, `nobody`, `check`, `or else`; the closed `maybe<int>` slice is implemented
- [ ] **M** General `result<T, E>`: `ok`, `err`, `?`, `or else`; the closed `result<word,word>` slice is implemented

C ABI (roadmap M6; fenced by name today, blocker B01):

- [ ] **L** C scalar widths: `c_int`, `c_long`, `c_short`, `c_char` and unsigned forms lowered at target width, not `i64`
- [ ] **M** Sign and zero extension attributes and default argument promotions
- [ ] **M** Native C variadic calls
- [ ] **M** Callback ABI details in both directions for the widened set

Methods and generics:

- [ ] **M** Impl methods with `self`, `lend self`, `lend mut self` receivers
- [ ] **XL** Generic monomorphization for tasks, shapes, routes (needs the A3 substitution facts)
- [ ] **M** Doctrine-bound calls `T::method()` and UFCS in native code (front done)
- [ ] **L** `dyn Doctrine`: fat pointer plus vtable (front done)
- [ ] **M** Operator overloading in codegen: `Add` through `Neg`, `Eq`, `Ord`, `Index`
- [ ] **M** `IndexMut` (`a[i] = x`)

Ownership in generated code (consumes A4 facts):

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
- [x] **S** `with growth` loop form: runs natively, and a body that does not change the condition's pilot is rejected (`training arc with growth must mutate condition subject`)
- [ ] **M** Map and list destructuring

Closures:

- [ ] **L** Closure environment struct plus function pointer (front done for captures)
- [ ] **M** `Callable` / `MutCallable` / `OneShot` call paths
- [ ] **M** Closure return-type inference (currently `unknown`)
- [ ] **M** Nested and generic closures
- [ ] **M** Closure effect summaries so mutable writes through captures are allowed safely

## Tier 4: everything V3 ships (the "replaces V3" line)

Language surface V3 has:

- [ ] **M** `|>` pipe (lowering; the silent drop is tracked in tier 1)
- [ ] **M** `eventually` (V3 emits inline; decide inline or true deferred)
- [ ] **M** `isekai` blocks
- [ ] **M** `foreshadow` / `payoff`
- [ ] **S** `knowing this will hurt,` / `sadly` / `for science,` prefixes
- [ ] **M** Anime operators `PLUS ULTRA`, `NAKAMA`, `FINAL FORM`, `TSUNDERE` (combined-token lexing open)
- [ ] **M** Annotations carried to codegen where V3 does
- [ ] **M** `use module::{items}`, glob imports across files
- [ ] **M** `launch` visibility in generated symbols
- [ ] **S** `done` as block terminator in all positions
- [ ] **M** Scalar conversion methods V3 has: `to_num()`, `to_int()`, `to_word()` on int, num and bool (`int offers no method to_num` today; same on #143); int/bool/num `.to_word()` is implemented, while `.to_num()` and broader `.to_int()` remain open

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
- [x] **L** Windows x64 native linking for the admitted backend/runtime gates, with exact current-head CI; broader V3 parity remains open
- [x] **M** macOS arm64 native linking for the admitted backend/runtime gates, with exact current-head CI; broader V3 parity remains open
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
- [ ] **XL** Replace encoded-word and parallel-array internals with real shapes and arenas (possible only after tier 2; overlaps A2)
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

- [ ] **S** Confirm CI is green on Linux, macOS and Windows after the merge (lanes exist; not verified from here)
- [ ] **M** V4 native execution lane in CI: macOS and Windows lanes exist; add Linux arm64
- [ ] **M** Installers (`install.sh`, `install.ps1`) ship the V4 compiler
- [ ] **M** Homebrew, Scoop, Winget packages updated
- [ ] **M** Packaged runtime objects for the V4 link path
- [ ] **S** Version bump and name; `tools/release_version.py check`
- [ ] **M** Migration guide: what changes for V3 programs. Known so far: missing task return types still fail; strict mode excludes top-level statements; keywords reserved in lowercase only; `TRUE` / `Yes` mean true (V3 reads them as false); semicolons and `pilot mut` accepted in the merged checkpoint. Resolve decisions 12–14 before documenting their final semantics
- [ ] **M** README, bible section 0.2, conformance audit, V4 README all in sync
- [ ] **S** `compiler-v3-final` tag after V3's Last Sortie gates
- [ ] **M** Security review of generated-code memory safety claims before the README says "memory safe"
- [ ] **S** Rename `crates/` if you are going to (cheapest before release)
- [ ] **S** Remove committed build outputs (`.exe`, `.pdb`, `.ilk` under `tests/` and `self_hosted/`)

## Open decisions only the maintainers can make

1. Closed for delivery order: Preview first, then V3 replacement (table at the top).
2. Closed: Word indexing and slicing use character semantics, as the bible specifies.
3. Whether `for each` consumes its source.
4. `eventually`: inline as V3, or true deferred.
5. Revive or drop `feat/v4-runtime-core`.
6. Whether V4 keeps any C backend for compatibility (manifesto says optional).
7. Which tier 5 features are release blockers and which ship later.
8. Whether A2 (`TypeId` everywhere, then the TIR view) is a release blocker or lands after self-hosting together with the tier 6 internals rewrite.
9. `|>`: lower it now or reject it by name.
10. Closed for the admitted scalar write path: checked range failure, with exact native regressions; broader ABI admission remains separate.
11. Whether to split `freak_ty` into builder and authority (A5), decided after A1.
12. Inner-block shadowing: allow it as V3 does, or keep rejecting it. The bible does not say.
13. A task with no return type: accept as `-> void`, or require the type.
14. Is a pilot mutable by default? Bible §1.1 says yes, with `fixed pilot` as the immutable form. The borrow-checker note in §4 describes V3's strict rule, where only `pilot mut` may be reassigned. The merged checkpoint accepts `pilot mut`. The book and the migration guide both depend on the answer.

## Appendix: re-measuring the progress numbers

Run from the repository root.

```sh
# A1: lexer and parser call sites left in MIR Build and in TY
# (in TY, the stream_/tree_/file_id helpers are identity checks, not token reads)
for c in freak_mir_build freak_ty; do
  grep -oE 'v4_(lex|parse|expand)_[a-z0-9_]+\(' src/compiler/v4/crates/$c/src/lib.fk | sort | uniq -c | sort -rn
done

# A0 and A4: what freak_mir and codegen reach into (both should print 0)
grep -cE 'v4_(lex|parse|expand|hir|resolve|borrowck|codegen)_' src/compiler/v4/crates/freak_mir/src/lib.fk
grep -cE 'v4_borrowck_' src/compiler/v4/crates/freak_codegen_llvm/src/lib.fk

# A2: type-word reads and spelling comparisons in Meiya and codegen
grep -oE 'v4_mir_[a-z_]*(_ty|type)[a-z_]*\(' src/compiler/v4/crates/freak_borrowck/src/lib.fk src/compiler/v4/crates/freak_codegen_llvm/src/lib.fk | wc -l
grep -oE '(ty|type)[a-z_]* (==|!=) "' src/compiler/v4/crates/freak_borrowck/src/lib.fk src/compiler/v4/crates/freak_codegen_llvm/src/lib.fk | wc -l

# Gate, and scaling with correctness checks
python src/compiler/v4/check_v4.py
python v4_scale_bench.py --check
```

The `training arc` cap repro (expected exit code 3; `main` and #143 give 11):

```
task main() -> int {
    pilot drills = 0
    training arc until drills > 10 max 3 sessions { drills += 1 }
    give back drills
}
```

The `|>` repro:

```
task inc(x: int) -> int { give back x + 1 }
task dbl(x: int) -> int { give back x * 2 }
task main() -> int { give back 3 |> inc |> dbl }
```

Expected exit code 8. `main` reports zero diagnostics and the program
exits 3. PR #143 rejects it with a generic unsupported-rvalue error.

## Retained historical gate provenance

The following checkpoint observations were retained from the previous working
checklist. Their pending/failure statements belong to their named historical
revisions and are superseded for PR #143 readiness by the reconciled merged
evidence above. They are not current-head executions or release completion.

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
