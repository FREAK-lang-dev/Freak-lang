# Maverick Bootstrap Workspace

Compiler name: **Maverick** | codename: **00-unit**

This directory is the implementation home for Maverick (00-unit), the V4 compiler architecture described in `freakc-v4-00-unit-architecture.md`.

Bootstrap status: complete for the executable 00-Unit architecture slice. This proves the modular, query-backed V4 shape and its tooling protocols; it is not yet a full V3 replacement.

## Bootstrap Completion Marker

The **Bootstrap V4** finish line is considered met when all of the following remain true in the tree:

- `python src/compiler/v4/check_v4.py` passes from the repository root.
- `freak_driver` stays limited to source orchestration, core query access, diagnostics, and restore accessors needed by snapshot restore.
- `freak_editor` owns semantic-at, hover, definition, document-symbol, and completion fact storage plus their query APIs.
- `freak_snapshot` owns snapshot formats, manifests, diffs, health reports, restore coordination, and invalidation contract reporting.
- `freak_lsp` stays transport-facing and wraps compiler results as line-protocol `ok|...` or `error|...` envelopes.
- `src/compiler/v4/tests` continues to exercise the bootstrap slice end to end, including query invalidation, LSP dispatch, unit snapshot restore/diff/health, and the current typed MIR lowering smoke set.

Anything beyond this marker belongs to the next phase: richer language coverage, deeper Meiya borrow analysis, and backend/codegen integration. Do not push those concerns back into `freak_driver` to move faster; that is how the rewrite loop returns.

## Post-Bootstrap Sequencing

After the bootstrap slice, V4 work advances by dependency strata rather than by
bible chapter order or by isolated crate ownership:

1. Semantic Core: stabilize value shapes, variants/routes, aliases, tuple/array
   type forms, and generic propagation as vertical slices across
   `lex -> parse -> HIR -> TY -> MIR -> editor/snapshot/LSP -> smokes`.
2. Borrow Checker: finish Meiya only after the semantic surface is stable enough
   that new value forms are no longer reopening ownership analysis every week.
3. FFI And Systems Boundary: extend ABI, layout, raw-pointer, and LLVM carriage
   once TY/MIR contracts are settled.
4. Concurrency: land `xm3`, `sortie`, `formation`, `briefing room`, and
   `wingman` only after ownership semantics are coherent.
5. Advanced And Anime Surface: enforce `mood`, `prob`, `power`, `causality`,
   narrative strictness, and richer error voices on top of the stabilized core.

The anti-rewrite rule is simple: do not try to "finish borrowck first" while
Semantic Core forms are still moving. Each new source form must become a full
vertical slice before the next dependency gate opens.

Current Phase 1 landings already cover routes/variants, alias-backed pattern
surfaces, exhaustive route/variant `when` and `check route` diagnostics through
alias-backed scrutinee types, direct recursive shape/variant rejection unless
the cycle crosses a real builtin indirection carrier, import-expanded recursion
checks with local/imported carrier shadows, local-name import precedence,
phantom generic alias erasure, and bounded recursive generic walks, tuple and fixed-array local/editor facts, module/glob import call
resolution, root `fixed pilot` constants with cycle diagnostics plus composite
tuple/list/repeat-fill inference, generic shape/route constructor inference,
constructor-payload validation, const-task-call type inference plus
diagnostics, and declared-initializer mismatch diagnostics, fixed-array
compile-time lengths with root-constant integer arithmetic,
generic doctrine bounds plus multi-bound method/editor enforcement, first-pass
`dyn Doctrine` type positions with object-safety/coercion diagnostics and
MIR/editor method facts, named call-site arguments across task calls plus
instance/associated method calls, and concrete impl UFCS lowering for
`Type::method(receiver, ...)`. Doctrine-bound generic owners now support both
static calls such as `T::baseline()` and UFCS calls such as
`T::score(value, bonus: 2)`, preserving instantiated doctrine arguments through
MIR parameter/return typing and editor hover, definition, and completion facts.
Doctrine substitution runs before alias canonicalization, body generics outrank
same-named global aliases, and overlapping bound methods diagnose ambiguity
instead of selecting whichever doctrine Yuuko happened to inspect first.
Closures now form a complete first-pass frontend/query slice. The resilient
parser records arrow and block forms as `ClosureExpr` trees and leaves
`IncompleteNode` recovery facts for missing pipes, body markers, expressions,
or parameter names. HIR normalizes default/`copy`/`move`/`mut`; TY assigns
`Callable`, `MutCallable`, or `OneShot` closure identities; and MIR lowers a
`Closure` aggregate with explicit `CaptureBorrow`, `CaptureBorrowMut`,
`CaptureCopy`, or `CaptureMove` children. Capture discovery tracks declaration
order and nested block scope, excludes member-name tokens, and treats only
`Callable` closure environments as Copy. Meiya keeps stored borrow captures
live through the closure holder's final reachable use, recognizes assignment
and resolved `lend mut self`/Shared mutable receiver calls, requires exclusive
access for mutable captures, and consumes OneShot closures on call. Closure
effect summaries do not exist yet, so MIR rejects mutable closure writes into
captured storage whose type may retain a lend instead of silently losing the
installed loan at invocation. Closure parameter editor facts likewise exclude
`.`/`::` member positions. Capture
mode is visible through semantic, hover, definition, completion, LSP, MIR and
borrowck snapshots, and deterministic all-family invalidation/diff reports.
Nested and generic closure inference, borrowed-return closure contracts,
`Send`/`Sync`, and native closure-environment codegen remain later slices.
The Borrow Checker gate has now started with `lend` / `lend mut` parameter
contracts and explicit `lend value` / `lend mut value` expressions carried
through TY and MIR into Meiya: immutable lends cannot be written, borrowed
params cannot be moved out of, borrowed params are not dropped by the callee,
and explicit borrow expressions create loan paths. Explicit loans bound to a
local now block later rewrites and ownership moves only while that local has a
later reachable use; owned call arguments participate in move checking, while
call-only loans expire at the call boundary. Mutable explicit loans now retain
their `LoanMut` identity and cannot overlap another live explicit loan,
including aliased arguments in one call; a call-only mutable loan remains
exclusive during that call. A live `LoanMut` also blocks reading the original
owner, including Copy-valued call arguments and reads in successor blocks,
until the loan holder's final reachable use. Loan holders can now project
typed shape fields and indexed elements: Copy-valued reads stay usable,
`lend mut` holders may write through their projections, and neither kind of
holder may move a non-Copy projected value out of its owner. A later projected
mutable write keeps the exclusive loan live against earlier owner
observations. Partial moves now recognize repair writes across CFG branches
only when every route to the later whole-owner use restores the moved field;
one unrepaired branch remains blocked. Linear bodies now get first static
drop flags: a full-local move removes that local from final drop tracking
until an exact local reassignment reinitializes it, including same-statement
move-and-reassign forms that evaluate the RHS before the destination write.
Multi-block bodies now suppress final drops only when every real CFG exit
has moved the local without reinitializing it; loop backedges and unreachable
checker tails are no-exit edges. Mixed exits now produce `DropIf` paths,
marking the runtime drop-flag site for locals moved on only some branches;
loop re-entry preserves the incoming drop state instead of replaying one-time
header declarations. Borrowck snapshots preserve those `DropIf` path
records through restore, so editor and 00-Unit tooling keep the same
conditional-drop metadata that Meiya computed.
Borrowed return types now carry through TY/MIR. Ordinary tasks may write
`lend 'a value: T`, `lend mut 'a value: T`, `-> lend 'a U`, and
`-> lend mut 'a U`. Ordinary-task generic lists also carry explicit outlives
relations: `'long: 'short` means that `'long` may supply a loan returned for
`'short`. Every declared lifetime is reflexively reachable from itself, direct
edges close transitively, and relation cycles make their members mutually
reachable. TY computes this closure with an iterative, cycle-safe worklist, so
converging relation graphs and long chains use constant call-stack space. Its
queue/visited arrays are high-water scratch: each traversal resets the
active prefix and reuses capacity without growing for repeated same-sized work. `'_`
keeps elision semantics but cannot be declared or used
as a bound. Declaring `'static` binders or using `'static` lend
parameters/returns remains blocked until global-storage provenance exists.

TY builds deterministic, controlled, mode-compatible returned-loan source sets.
A named
return admits every borrowed parameter whose lifetime equals or outlives the
return lifetime; an elided return admits every mode-compatible borrowed
parameter. Shared `lend` returns accept `lend` and `lend mut` sources, while
`lend mut` returns accept only `lend mut` sources. Candidate selection is
independent of top-level pointee type because a valid return may project a
field from its source. The returned-loan source set of eligible formal
parameter ids is built lazily once per immutable `(ty_id, sig_id)` and shared
by count and indexed lookups. The cache is a bounded flat ring with encoded,
ordered parameter-id payloads, so a source set does not allocate a child arena
and a known-empty set remains distinct from a cache miss. Eviction causes a
deterministic rebuild. A TY file or signature restore invalidates its matching
rows before the restored contract can be queried again.

Meiya verifies that each returned origin honors the declared lifetime, then
follows that origin through field projections, scalar local holders, nested
statically resolved ordinary calls, reordered named arguments, and CFG joins,
including loop headers and backedges. An explicit reborrow through a scalar lend holder preserves its projection
suffix, so `lend view.ship` resolves to the holder's concrete owner path rather
than becoming opaque. MIR erases a callee's binder spelling from the caller-local result type
while preserving a deterministic signature-source-to-call-argument candidate
mapping on the call rvalue. MIR does not own the resulting loan paths: Meiya
resolves those candidates to caller-local owners and emits each concrete path as
a queryable `ReturnLoan` / `ReturnLoanMut` fact.
Stored named or elided ordinary-call results and copied scalar holder aliases
keep all candidate owners live through the holder's final reachable use. Local rebinding kills
only that holder's provenance, exact self-assignment preserves it, and restoring
from a descendant alias establishes a new tracked state. Provenance expansion
is memoized by MIR/body/use location/rvalue within each borrowck generation.
Recursive lookups form an implicit dependency graph. Meiya discovers that graph
with an iterative memo worklist, records reverse dependency edges in per-memo
adjacency lists, and schedules only dependants of changed memos in deterministic
waves, so a long acyclic holder chain cannot consume the native call stack or
force an all-memo replay. A solved-memo frontier also seeds later top-level
queries from only the newly discovered roots; queued-state cleanup and empty-memo
finalization walk that same frontier instead of every memo accumulated so far.
Generation-stamped per-body memo chains keep each root lookup local to its MIR
body rather than scanning every previously solved body in the file.
One bounded phase propagates concrete owner paths, every unresolved empty memo
(including a source-less strongly connected component) is then made opaque, and
a second bounded phase propagates that opacity. Each phase is limited to
`new_memo_count + 1` rounds and a monotonic revision counter detects convergence
without rescanning all provenance states.
An identity cycle is stable, while a projected self-cycle that would grow an
owner path remains opaque. Failure to converge fails closed by making the
generation opaque. The generation also fails closed when it exceeds 4,096 memo
entries, 16,384 dependency edges, 65,536 work items, 1,024 concrete source
facts, or a 1,024-byte canonical owner path. Rounds, limits, solve counts,
convergence, resource exhaustion, and work-item counts are keyed by borrowck
result, persisted in borrowck snapshot v2, and pinned by executable restore and
budget smokes. Legacy v1 snapshots remain importable with conservative default
telemetry, while truncated v2 telemetry records are rejected. CFG block
reachability, holder liveness, and holder-alias expansion use explicit
cycle-safe worklists; a 64-diamond CFG
smoke proves forward/reverse reachability without recursive stack growth.
A 256-root solver smoke drives one valid MIR loan through distinct top-level
use-site keys and pins 256 solves to 512 processed work items, crossing the old
cumulative-replay failure threshold without unrelated global symbol-table stress.
Active scratch counts reset at generation boundaries and are bounded by the
active generation's visited provenance graph. State, source-row, and memo arrays
reuse high-water capacity across recomputation without historical growth, while
source-less or path-growing provenance cycles remain conservatively opaque. Meiya's integer-word,
canonical-value, and exact-input caches are bounded rings; evicted values rebuild
to the same canonical owner path, while hot entries reuse their existing row.
The bootstrap C runtime now grows its array-handle table dynamically instead of
imposing the former 256-handle ceiling. That removes a test-only capacity illusion,
but the words displaced by cache eviction still live in append-only bootstrap
arenas: general arena reclamation remains separate work.
Semantic, hover, and definition queries resolve repeated and forward
outlives-bound references to the declared binder; distinct definition records
and spans survive editor snapshot restore. Document-symbol and completion
requests participate in the same editor query lifecycle. Source edits invalidate
and explicit requests prove recomputation across all 17 report fields: 14
concrete query families (syntax, lex, parse, HIR, resolve, TY, MIR, borrowck,
diagnostics, semantic-at, hover, definition-at, document symbols, and
completion) plus three refreshed aggregate totals (`all`/`query`, `core`, and
`editor`). This includes an elided result changing from multiple candidate
owners to one and an isolated, byte-length-stable loop-backedge edit shrinking
a fixed point from two concrete owners to one without changing its signature.
The backedge fixture proves positive recomputation for every concrete family and
re-queries syntax, diagnostics, semantic, hover, definition, symbols, and
completion after 00-Unit restore.

The current sound boundary is deliberately narrow. Named or elided lends may be
outer ordinary-task parameter and borrowed-return contracts, and their results
may flow through scalar holders or task-local fixed-layout aggregates. The
local aggregate vocabulary is exactly tuples, fixed arrays, shapes, and route
payloads. Tuple slots and array indices are structural keys; MIR normalizes
shape and route constructor children into declaration order, so reordered
source fields cannot relabel a loan after lowering.

Meiya carries those keys through local aggregate holder aliases and projection-aware
provenance queries. A use of `.0`, `.field`, or a constant `[index]` extends the
loan stored in that child without making unrelated siblings live. Projection
chains may cross lend-valued fixed-layout slots; each indirection is resolved
at its defining statement before the final write is matched to the original
holder. Prefix selection canonicalizes indexed paths once after its bounded
scan and resolves reused local names at the statement where the projection is
used. Whole-value uses and non-constant fixed-array projections include every
possible child. A dynamic-index assignment overlaps every fixed slot, so it
cannot retire or launder only one child's loan. `LoanMut` remains exclusive
while its projected holder is live, and repeat-filling more than one fixed-array
slot with the same mutable lend is rejected instead of duplicating one
exclusive loan.

Moving a lend-valued child out of an owned aggregate transfers that loan and
uses the ordinary partial-move repair rules. Moving a child through an aggregate
that is itself held behind `lend` or `lend mut` remains rejected.

Dynamic containers remain outside closure-loan provenance. Meiya rejects both
container construction and later indexed writes when the stored closure still
captures a live loan.

Projection assignments are first-class holder definitions. Rebinding one field
retires only that field's previous loan, protects the newly stored owner through
the field's final use, and leaves sibling provenance unchanged. Moving an
aggregate into a projected destination rebases its children under that
destination while preserving each relative `.N`, `.field`, or `[N]` path.

This is local storage, not an aggregate calling convention. Ordinary-task
fixed-layout aggregate parameters and returns now preserve leaf provenance
across the boundary. TY still rejects named and elided lends nested inside
non-ordinary task parameter or return types.
Generic-call, owner-generic, and `Shared<T>::new` substitution checks recursively
expand nominal shapes and routes, so a type such as `Direct<'a>` cannot hide its
`lend 'a` field behind a nominal name. Direct nominal impl calls and overloaded
operator dispatch on lend-bearing aggregate owners fail closed at this boundary
instead of manufacturing a result type. The recursive storage classifier has a
bounded depth budget: exhaustion emits its own diagnostic, strict validators
reject it, and conservative Meiya queries treat it as possibly lend-bearing.
MIR continues to reject lend storage in list and map values plus the
`some(...)`, `ok(...)`, and `err(...)` wrapper constructors. Alias targets,
doctrine and method contracts, callbacks, extern/FFI boundaries, and
non-ordinary aggregate task parameters or returns remain outside fixed-layout provenance.
Malformed `lend 'a` and doubled-lifetime types receive spanned diagnostics.
Contract-boundary smokes also pin normalized source paths and exact `start:end`
byte ranges for signature-storage and unsupported-forwarding failures.
Method, dynamic, callback, extern, and FFI returned-loan forwarding calls are
explicitly rejected rather than silently accepted. Closure expressions now
carry capture ownership, but their types cannot yet express borrowed-return
contracts, so closure returned-loan forwarding remains unsupported. Lifetime
eligibility remains signature-derived from declared ordinary-task contracts.
Body-derived provenance/source discovery through reaching definitions is
implemented for local aliases, aggregate builds and moves, stored and
constructor-direct statically resolved call results, projection rebinding,
acyclic joins, and bounded loop fixed points. Signature-derived lifetime solving
beyond declared relations and general lexical region inference remain open.
Fixed-layout editor facts, MIR/borrowck snapshots, restore, and
source-change invalidation use the existing query families and 00-Unit
protocols; no aggregate-specific LSP endpoint or snapshot section is added.
Declaration-order aggregate children require `freak-mir-snapshot-v5`; v4 is
rejected rather than reinterpreted. Component restore, 00-Unit restore, and the
standalone `workspace/mirSnapshotRestore` path each start a fresh borrowck
provenance scratch generation. The query smoke proves `A -> B -> restore A` with
MIR, borrowck, and editor IDs re-resolved from restored arenas instead of reused.
This is a contract-region source-set and non-lexical liveness slice. It is not full region inference.
These TY/MIR/Meiya/editor facts do not imply a completed
production backend or runtime aggregate-loan ABI. Dynamic and wrapper-container
storage remains outside this slice.
The first `Shared<T>` / `Weak<T>` ownership surface now exists in TY/MIR:
`Shared<T>::new`, `.clone()`, `.downgrade()`, `.borrow()`, `.borrow_mut()`,
`.get_mut()`, and `Weak<T>.upgrade()` lower to stable wrapper types, while
direct `Weak<T>.borrow()` and escaping `SharedMut<T>` guards produce targeted
diagnostics. Guard escape checks are value-sensitive: an actual
`SharedMut<T>` return is blocked, while `result<SharedMut<T>, BorrowError>`
failure paths are not rejected just because the success arm could carry a
guard. Runtime reference counters, borrow-state guards, `Send`/`Sync`, and
backend allocation layout remain later slices.
`trust me "..." on my honor as .level` now carries the honor ladder in MIR:
`.cadet`, `.pilot`, `.ace`, `.commander`, and `.humanity` are validated,
unknown levels diagnose, raw-pointer reads require at least `.cadet`, and
raw-pointer writes require at least `.pilot`. The method forms `.read()` and
`.write(value)` now lower through MIR/LLVM as the same load/store operations as
`*ptr` and `*ptr = value`, including arity, mutability, and honor diagnostics.
Pointer arithmetic and raw retyping are now opened through `.offset(n)` and
`.cast<U>()`, lowering to LLVM `getelementptr` with preserved `*const`/`*mut`
shape and `.ace+` honor diagnostics. Raw allocation/freeing, `direct_order`,
and the higher-rank operation matrix remain later slices.
The FFI/type lane also carries `std::ffi` alias normalization, raw-pointer LLVM
carriage, `@layout(C)`, `@layout(C, packed=N)`, `@layout(transparent)`, and
fieldless route/variant `@repr(u8|u16|u32|u64|i8|i16|i32|i64)` contracts
through TY queries with boundary-safety diagnostics for non-FFI extern types,
raw-pointer pointee targets, non-FFI layout fields, bad repr kinds, payload
cases under repr, and non-constant explicit discriminants. Fieldless
`@repr(...)` routes and variants are now accepted as FFI-safe extern
parameters, returns, raw-pointer targets, and `@layout(C)` fields; payload or
unrepr'd variants stop with route-specific diagnostics. Extern blocks also carry `link="..."` library
metadata, member-level `@link_name("...")` symbol overrides, and final
extern-only `args: ...` variadics through TY, MIR, LLVM declaration/call
plans, scalar vararg promotion for `tiny`/`bool`/`char`/`float32` tails, query
diagnostics, snapshot restore, and LSP. Extern callback surface types like
`extern [C] task(...) -> T` and `extern [system] task(...) -> T` now validate
through TY as FFI-safe function pointers, now diagnose missing `extern`,
invalid callback ABI lists, and non-FFI callback parameter payloads including
raw-pointer pointees through query/snapshot/LSP, lower to LLVM `ptr`, and now call through MIR/LLVM as
indirect FFI calls from locals, returned callback values, and `@layout(C)`
field places. Plain FREAK task values now stop at that fence with dedicated
callback-boundary diagnostics instead of silently flowing into foreign
callback slots. Foreign LLVM declarations and call sites now carry `nounwind`
as groundwork for the extern/callback panic-boundary contract. The inbound
callback surface is now opened via `@extern_callback("C")` /
`@extern_callback("system")` on FREAK tasks: TY validates the ABI, FFI-safe
parameters/return, rejects variadics, and diagnoses missing/extra/invalid ABI
arguments, while codegen emits a `nounwind` LLVM trampoline
(`@__freak_callback_<task>`) that tail-calls the FREAK body. Bare references
to those tasks now type as the matching `extern [ABI] task(...) -> T`
function pointer, so they coerce into FFI callback slots at both call-arg
and return-site positions, and codegen rewrites the use-symbol to the
trampoline (so a `give back my_hook` from a function returning
`extern [C] task(...) -> T` emits `ret ptr @__freak_callback_my_hook`).
ABI/signature mismatches between the FREAK task and the callback slot
still trip the boundary-bridge `callback value must use extern ABI`
diagnostic. Coercion through intermediate `pilot slot: extern [ABI]... = my_hook`
let-bindings still hits a pre-existing V4 phantom-local-IR issue that
applies to any `pilot x: T = some_symbol`, so that surface is handled by
a follow-up rather than the FFI lane. The runtime panic-catch inside the
trampoline body remains later FFI work. Full panic-abort guarantees across
callback boundaries remain later FFI work.
The current smoke lane now also proves the full core calling-convention matrix
(`fastcall`, `thiscall`, `vectorcall`, `win64`, `sysv64`, plus the existing
`C`/`cdecl`/`stdcall`/`system`) through direct extern calls, indirect callback
calls, and LLVM declaration/call lowering.

The first landing is intentionally small and isolated from the V3 compiler:

```text
crates/
  freak_span/      source ids, spans, line/column helpers
  freak_diag/      diagnostic encoding and severity helpers
  freak_arena/     append-only word arenas for early compiler storage
  freak_intern/    string interning table
  freak_session/   source database and revision tracking
  freak_lex/       lossless token streams with trivia and diagnostics
  freak_parse/     resilient top-level syntax tree and recovery nodes
  freak_hir/       top-level item lowering and stable def ids
  freak_resolve/   file-local semantic index and duplicate diagnostics
  freak_ty/        item-level signatures and primitive type helpers
  freak_mir/       typed task MIR bodies, CFG blocks, locals, places, rvalues, diagnostics
  freak_borrowck/  Meiya borrow-check paths and result scaffold over MIR bodies
  freak_codegen_llvm/ LLVM-facing declaration and call-plan lowering over MIR/TY
  freak_query/     memoized query cache prototype
  freak_driver/    early driver facade over the V4 services
  freak_editor/    semantic-at, hover, definition, symbols, and completion analysis
  freak_snapshot/  00-Unit workspace snapshots, manifests, diffs, health, restore
  freak_lsp/       transport-facing LSP facade over editor analysis and diagnostics
```

Current FREAK compilation still works best with concatenated source files, so these crates use globally unique `v4_` names and a dependency order that can be flattened by a later bootstrap script:

```text
freak_span -> freak_diag -> freak_arena -> freak_intern -> freak_session -> freak_lex -> freak_parse -> freak_hir -> freak_resolve -> freak_ty -> freak_mir -> freak_borrowck -> freak_codegen_llvm -> freak_query -> freak_driver -> freak_editor -> freak_snapshot -> freak_lsp
```

The boundary shape follows the architecture manifesto even though the initial code uses simple arrays and encoded words. That is deliberate: the first goal is to make the 00-Unit data model executable before replacing the internals with richer shapes, arenas, and persistent caches.

### Keyword Casing Contract

`freak_lex` owns keyword classification. Ordinary keyword words use their exact
lowercase spelling and are emitted as `keyword` tokens with that canonical
value. Noncanonical forms such as `Task`, `TASK`, and `ShApE` remain identifiers;
when used where a declaration keyword is required, `freak_parse` produces its
normal targeted recovery diagnostic. This preserves valid identifier spellings
such as `Pilot`, `Some`, and `SOME` instead of silently rewriting them.

The single-word anime operators `NAKAMA` and `TSUNDERE` are intentionally
uppercase-only and retain those uppercase token values; mixed- or lowercase
spellings remain identifiers. The bible-level `PLUS ULTRA` and `FINAL FORM`
operators use canonical uppercase token values after case-insensitive phrase
matching, but combined-token support for those multi-word forms remains
outside the current V4 lexer slice. The
`keyword casing matrix` smoke fixes the canonical and identifier spellings,
adjacent identifier boundaries, parser dispatch, snapshot token values, and
noncanonical-keyword recovery diagnostic in one table-driven contract.

## Public Tooling Protocols

V4 tools speak small line protocols. Every transport-facing method is wrapped by `freak_lsp` as either:

```text
ok|<method>
<body>
```

or:

```text
error|<method>|<json-rpc-code>|<message>
```

Snapshot payloads are newline-delimited records. Fields are pipe-separated. Any field that can contain source text, snapshots, diagnostics, paths, or arbitrary payload bytes must be encoded by the snapshot helpers before it is placed on a line. Do not hand-roll escaping in transport code.

### Snapshot codec resource contract

Snapshot escaping, unescaping, line lookup, and field lookup must use the shared `word.snapshot_*` runtime primitives. Those primitives scan their input linearly and allocate each returned word at most once. A snapshot codec must never rebuild an escaped payload one character at a time with `char_at` plus concatenation: the bootstrap word runtime does not yet reclaim those intermediate heap words, so that pattern turns a small checkpoint into quadratic retained memory.

Record serializers must collect complete records in a temporary word array and finish with `word_join(parts)`. Repeatedly assigning `out = out + record` copies every prior record and retains every copied prefix. The native join computes the final byte count first, materializes the payload with one allocation, and consumes the temporary array. Its slot is returned to the runtime free list with a new generation on reuse, so repeated LSP snapshot requests cannot exhaust the LLVM array pool and a stale alias cannot address the replacement array.

Source validation records canonical IDs and paths while it performs the forward envelope scan. It must not reparse every earlier source line to detect duplicates. Manifest, diff-detail, and health serializers use the same join contract, while source diffs index source lines once before comparing paths. The `unit_snapshot_multisource_resource_smoke.fk` fixture exercises 192 source records through validate, manifest, diff, and health under a 64 MB process-tree ceiling.

Temporary graph, worklist, seen-set, and serializer arrays are request-scoped resources. Every path that allocates one must either consume it with `word_join` or release it with `array_release`, including failure exits. `mir_snapshot_resource_smoke.fk` repeatedly validates accepted and cyclic MIR graphs, and `query_invalidation_resource_smoke.fk` combines 96 `didChange` requests with 600 direct dependency invalidations. These C-backed resource fixtures are compiled with a test-only 1,024-live-handle limit matching the LLVM runtime pool; the production C runtime remains dynamically sized. Each fixture measures all remaining handle capacity before and after its workload and ends with a fresh-array probe under a 64 MB ceiling, so even one leaked handle fails instead of hiding behind low RSS or spare C table capacity.

Executable smoke runs report peak process-tree memory and have a 512 MB default ceiling. Every snapshot-named fixture uses a tighter 128 MB ceiling, and generated-C compilation is capped at 1 GB. Windows children start suspended, are assigned to a kill-on-close Job Object with an aggregate commit limit, and resume only after assignment, making that ceiling OS-enforced for the complete tree. POSIX runs use a fresh process group with group-wide RSS and swap monitoring; this is a sampled ceiling rather than a hard kernel allocation limit on hosts without an available cgroup controller. Stdout and stderr are drained by bounded readers with an 8 MB ceiling per stream, so a noisy descendant cannot move the same failure into Python's memory or a giant log file. Crossing a monitored ceiling terminates the entire process tree and fails the gate before sustained growth can expand the host pagefile.

The Python check coordinator streams generated C one fixture at a time. It never keeps a workspace-sized artifact dictionary: each C program is compiled or validated, released, and collected before the next fixture. Post-collection checkpoints enforce a 256 MB retained-memory ceiling and print the observed peak at the end of the run. The sample is current private usage on Windows, current RSS plus swap on Linux, and current RSS from `proc_pidinfo` on macOS; it is not a process-lifetime high-water mark. The checker self-tests this sampler before doing expensive work and fails closed if sampling is unavailable on Windows, Linux, or macOS. This ceiling covers the coordinator; the child-process ceilings above independently cover Clang and executable smokes.

The bootstrap `word` runtime still uses process-lifetime storage for completed word values. The 80-snapshot soak therefore measures and gates bounded linear retention under the 128 MB ceiling; request-scoped word arenas or full word reclamation remain runtime work beyond this bootstrap guard. The codec contract above removes the catastrophic quadratic copies and handle exhaustion, but it does not claim general-purpose garbage collection.

### `workspace/unitSnapshot`

Produces the current 00-Unit workspace snapshot. The method does not require a text payload.

```text
00-unit-snapshot|format=freak-00-unit-snapshot-v2|sources=<count>|sections=14|identity=<escaped-checkpoint-identity>
unit-source|<file-id>|<escaped-path>|<revision>|<escaped-fingerprint>|<escaped-text>
unit-section|<section-name>|<escaped-checkpoint-identity>|<escaped-section-payload>
end|freak-00-unit-snapshot-v2
```

The source records describe the current `freak_session` source database. The checkpoint identity folds the source identity and content digests for all 14 sections in canonical order, so a section cannot be transplanted from a different checkpoint even when source text is unchanged. This is an integrity checksum, not an authentication primitive. Section records are owned by `freak_snapshot`; each section is allowed to change internally only when its format helper and validator change together.

### `workspace/unitSnapshotManifest`

Validates and summarizes a 00-Unit snapshot. With no text payload, it summarizes the current workspace snapshot. With a text payload, the payload must be a `freak-00-unit-snapshot-v2` document.

```text
00-unit-manifest|format=freak-00-unit-manifest-v1|ok=<0-or-1>|payload-format=<format>|payload-bytes=<bytes>|payload-lines=<lines>|sources=<count>|declared-sources=<count>|sections=<count>|declared-sections=<count>|malformed=<count>|validation=<escaped-message>
source|<file-id>|path=<escaped-path>|revision=<revision>|fingerprint-bytes=<bytes>|text-bytes=<bytes>
section|<section-name>|bytes=<bytes>|lines=<lines>|records=<records>|ok=<0-or-1>|validation=<escaped-message>
end|freak-00-unit-manifest-v1
```

Use this endpoint for import validation when a caller does not want to mutate compiler state. Validation can run in a fresh process: TY records receive detached structural validation, then `freak_snapshot` installs only the serialized source/lex/parse/HIR/resolve context, runs strict TY linkage checks, and rolls the parent arenas back before returning. There is no public `workspace/unitSnapshotImport` endpoint yet; validation-only imports are modeled as manifest or health requests.

### `workspace/unitSnapshotDiff`

Compares two complete unit snapshots. The text payload must be a diff input envelope:

```text
00-unit-diff-input|format=freak-00-unit-snapshot-diff-input-v1
before|<escaped-before-snapshot>
after|<escaped-after-snapshot>
end|freak-00-unit-snapshot-diff-input-v1
```

For in-process tooling and smoke runners, the same envelope also accepts snapshot refs:

```text
00-unit-diff-input|format=freak-00-unit-snapshot-diff-input-v1
before-ref|<escaped-before-ref>
after-ref|<escaped-after-ref>
end|freak-00-unit-snapshot-diff-input-v1
```

The response starts with a summary record, then optional detail records, then the terminator:

```text
00-unit-diff|format=freak-00-unit-snapshot-diff-v1|ok=<0-or-1>|before-ok=<0-or-1>|after-ok=<0-or-1>|before-manifest-bytes=<bytes>|after-manifest-bytes=<bytes>|before-manifest-lines=<lines>|after-manifest-lines=<lines>|sources-added=<count>|sources-changed=<count>|sources-removed=<count>|sources-unchanged=<count>|sections-added=<count>|sections-changed=<count>|sections-removed=<count>|sections-unchanged=<count>|query-invalidations-added=<count>|core-invalidations-added=<count>|syntax-invalidations-added=<count>|lex-invalidations-added=<count>|parse-invalidations-added=<count>|hir-invalidations-added=<count>|resolve-invalidations-added=<count>|ty-invalidations-added=<count>|mir-invalidations-added=<count>|borrowck-invalidations-added=<count>|diagnostics-invalidations-added=<count>|editor-invalidations-added=<count>|semantic-at-invalidations-added=<count>|hover-invalidations-added=<count>|definition-at-invalidations-added=<count>|document-symbols-invalidations-added=<count>|completion-invalidations-added=<count>|query-entries-added=<count>|query-entries-changed=<count>|query-entries-removed=<count>|before-validation=<escaped-message>|after-validation=<escaped-message>
source-diff|...
section-diff|...
query-invalidation-diff|...
query-entry-diff|...
end|freak-00-unit-snapshot-diff-v1
```

The invalidation counters are the public contract for source-change reporting. `textDocument/didChange` summaries and 00-Unit diff health must agree on all 17 report-field names and their classification into 14 concrete query families plus the three aggregate totals (`all`/`query`, `core`, and `editor`).

### `workspace/unitSnapshotHealth`

Runs health checks against a snapshot or a snapshot diff input. With no text payload, it checks the current workspace snapshot. With a snapshot payload, it checks that snapshot. With a diff input payload, it checks both snapshots and appends a `health-diff` record.

The diff-input form accepted here is the same `00-unit-diff-input` envelope documented under `workspace/unitSnapshotDiff`, including the `before-ref` / `after-ref` variant for in-process tooling.

```text
00-unit-health|format=freak-00-unit-health-v1|ok=<0-or-1>|snapshot-ok=<0-or-1>|snapshot-bytes=<bytes>|manifest-bytes=<bytes>|manifest-lines=<lines>|sources=<count>|sections-ok=<count>|sections-bad=<count>|query-entries=<count>|query-dirty=<count>|query-invalidations=<count>|query-hits=<count>|query-misses=<count>|query-stores=<count>|validation=<escaped-message>
health-query|ok=<0-or-1>|generation=<id>|generations=<count>|entries=<count>|dirty=<count>|edges=<count>|invalidations=<count>|telemetry=<count>|hits=<count>|misses=<count>|stores=<count>|validation=<escaped-message>
health-section|name=<section-name>|ok=<0-or-1>|bytes=<bytes>|records=<records>|validation=<escaped-message>
health-diff|ok=<0-or-1>|sources-added=<count>|sources-changed=<count>|sources-removed=<count>|sections-added=<count>|sections-changed=<count>|sections-removed=<count>|query-invalidations-added=<count>|core-invalidations-added=<count>|syntax-invalidations-added=<count>|lex-invalidations-added=<count>|parse-invalidations-added=<count>|hir-invalidations-added=<count>|resolve-invalidations-added=<count>|ty-invalidations-added=<count>|mir-invalidations-added=<count>|borrowck-invalidations-added=<count>|diagnostics-invalidations-added=<count>|editor-invalidations-added=<count>|semantic-at-invalidations-added=<count>|hover-invalidations-added=<count>|definition-at-invalidations-added=<count>|document-symbols-invalidations-added=<count>|completion-invalidations-added=<count>|query-entries-added=<count>|query-entries-changed=<count>|query-entries-removed=<count>
end|freak-00-unit-health-v1
```

`health-diff` is optional and appears only for diff input payloads.

### Restore And Import Paths

`workspace/unitSnapshotRestore` mutates compiler state from a complete 00-Unit snapshot payload:

```text
ok|workspace/unitSnapshotRestore
00-unit-snapshot-restore ok=<0-or-1> ...
```

Per-section restore endpoints accept a section snapshot payload and return the section restore report:

```text
workspace/lexSnapshotRestore
workspace/parseSnapshotRestore
workspace/hirSnapshotRestore
workspace/resolveSnapshotRestore
workspace/tySnapshotRestore
workspace/mirSnapshotRestore
workspace/borrowckSnapshotRestore
workspace/diagnosticsSnapshotRestore
workspace/semanticSnapshotRestore
workspace/hoverSnapshotRestore
workspace/definitionSnapshotRestore
workspace/documentSymbolsSnapshotRestore
workspace/completionSnapshotRestore
```

Requests without the required text payload return `error|<method>|-32602|method requires snapshot text`.

Query cache import and restore are separate because the query engine is allowed to validate cache payloads without installing them:

```text
workspace/querySnapshotImport
workspace/querySnapshotRestore
workspace/querySnapshotConfirm
```

## Crate Boundary Rules

Future V4 work must preserve the split that 00-Unit exists to prove:

```text
storage/query owner -> freak_snapshot formats -> freak_lsp transport wrapper
```

- `freak_driver` orchestrates source setup, core compiler queries, and diagnostics. It must not own snapshot serializers, editor-facing arenas, hover data, completion data, definition records, or document-symbol records.
- `freak_editor` owns editor analysis: semantic-at, hover, definition, document-symbol, and completion arenas plus their query APIs.
- `freak_snapshot` owns all snapshot wire formats, validators, manifests, diffs, health reports, restore coordination, and invalidation contract reports.
- `freak_lsp` owns request dispatch and response envelopes only. It should call compiler APIs and wrap the result as `ok|` or `error|`; it should not store compiler facts or define snapshot formats.

When adding a new V4 tool endpoint:

1. Put the fact storage and query computation in the crate that owns the domain.
2. Put every line format, validator, restore helper, manifest field, diff field, and health field in `freak_snapshot`.
3. Add only the transport method name and wrapper in `freak_lsp`.
4. Add a smoke fixture under `src/compiler/v4/tests`.
5. Run `python src/compiler/v4/check_v4.py`.

## Checks

Run the V4 bootstrap checks from the repository root:

```powershell
python src/compiler/v4/check_v4.py
```

The harness verifies crate existence/order, ASCII source, individual parser acceptance, flattened-crate type checking, and transpilation of every `src/compiler/v4/tests/*.fk` smoke fixture.

The bootstrap contract is now stricter: every `src/compiler/v4/tests/*.fk`
fixture must also appear in `EXECUTABLE_SMOKES` inside
`src/compiler/v4/check_v4.py`. If a fixture exists without a runtime smoke
entry, the harness fails before transpilation.

The harness also machine-checks the 00-Unit crate boundaries: `freak_driver`
must stay out of snapshot/editor ownership, `freak_snapshot` must own the
wire formats and invalidation reports, and `freak_lsp` must remain a transport
wrapper instead of growing compiler fact storage.

It also locks the public 00-Unit inventories: the fixed snapshot section set,
the fixed invalidation report-field set and concrete-family/aggregate
classification, and the documented section restore endpoints must all stay in
sync with the implementation.

For faster local iteration, the harness also supports:

```powershell
python src/compiler/v4/check_v4.py --fast
python src/compiler/v4/check_v4.py --smoke "query invalidation"
python src/compiler/v4/check_v4.py --smoke extern --smoke module
python src/compiler/v4/check_v4.py --smoke-shard 1/6
python src/compiler/v4/check_v4.py --smoke unit_snapshot_smoke
python src/compiler/v4/check_v4.py --smoke unit_snapshot_const_smoke
python src/compiler/v4/check_v4.py --smoke unit_snapshot_diff_smoke
python src/compiler/v4/check_v4.py --smoke-exclude unit_snapshot --smoke-shard 1/6
```

- `--fast` keeps the full front-end and fixture-transpile coverage, but skips runtime executable smokes.
- `--smoke` narrows execution to matching runtime smokes by name, fixture file, or fixture stem.
- `--smoke-exclude` removes matching runtime smokes before shard selection; CI uses this to keep the unit-snapshot, unit-snapshot-const, and unit-snapshot-diff lanes out of the general shard matrix.
- `--smoke-shard INDEX/TOTAL` deterministically partitions the selected runtime smokes; CI uses it to fan the executable lane out without changing what each smoke proves.
- Full mode still remains the bootstrap gate; the harness now reuses runtime smoke transpiles and skips unchanged `clang` rebuilds when the generated C and runtime shim are identical.
