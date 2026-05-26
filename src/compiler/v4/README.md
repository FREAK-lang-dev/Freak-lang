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
surfaces, tuple and fixed-array local/editor facts, module/glob import call
resolution, root `fixed pilot` constants with cycle diagnostics plus composite
tuple/list/repeat-fill inference, generic shape/route constructor inference,
constructor-payload validation, const-task-call type inference plus
diagnostics, and declared-initializer mismatch diagnostics, fixed-array
compile-time lengths with root-constant integer arithmetic,
generic doctrine bounds plus multi-bound method/editor enforcement, and named
call-site arguments across task calls plus instance/associated method calls.
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
exclusive during that call. That is the first non-lexical liveness slice, not
full region inference.
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

### `workspace/unitSnapshot`

Produces the current 00-Unit workspace snapshot. The method does not require a text payload.

```text
00-unit-snapshot|format=freak-00-unit-snapshot-v1|sources=<count>|sections=14
unit-source|<file-id>|<escaped-path>|<revision>|<escaped-fingerprint>|<escaped-text>
unit-section|<section-name>|<escaped-section-payload>
end|freak-00-unit-snapshot-v1
```

The source records describe the current `freak_session` source database. Section records are owned by `freak_snapshot`; each section is allowed to change internally only when its format helper and validator change together.

### `workspace/unitSnapshotManifest`

Validates and summarizes a 00-Unit snapshot. With no text payload, it summarizes the current workspace snapshot. With a text payload, the payload must be a `freak-00-unit-snapshot-v1` document.

```text
00-unit-manifest|format=freak-00-unit-manifest-v1|ok=<0-or-1>|payload-format=<format>|payload-bytes=<bytes>|payload-lines=<lines>|sources=<count>|declared-sources=<count>|sections=<count>|declared-sections=<count>|malformed=<count>|validation=<escaped-message>
source|<file-id>|path=<escaped-path>|revision=<revision>|fingerprint-bytes=<bytes>|text-bytes=<bytes>
section|<section-name>|bytes=<bytes>|lines=<lines>|records=<records>|ok=<0-or-1>|validation=<escaped-message>
end|freak-00-unit-manifest-v1
```

Use this endpoint for import validation when a caller does not want to mutate compiler state. There is no public `workspace/unitSnapshotImport` endpoint yet; validation-only imports are modeled as manifest or health requests.

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

The invalidation counters are the public contract for source-change reporting. `textDocument/didChange` summaries and 00-Unit diff health must agree on these family names.

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
the fixed invalidation family/report field set, and the documented section
restore endpoints must all stay in sync with the implementation.

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
