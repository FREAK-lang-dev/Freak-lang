# Backend delivery lane: evidence

Evidence for the rows of the release checklist's
[Backend delivery lane](RELEASE_CHECKLIST.md#backend-delivery-lane-deferred)
(B0 to B5). Each section names the row it answers.

## B0: the minimum LLVM the text backend supports

**Answer: LLVM / Clang 15** (upstream Clang 15, Apple Clang 15). This closes
open decision 17.

The V4 text backend writes opaque `ptr` types. Clang 15 is the first release
that reads them by default, and LLVM 17 removed typed pointers, so the module
must keep to the syntax LLVM 15 already parses and must never go back to
typed pointers.

Measured on 2026-11-23 with
[`benchmarks/v4/llvm_major_matrix.py`](../../../benchmarks/v4/llvm_major_matrix.py)
([receipt](../../../benchmarks/v4/llvm_major_matrix.json)): V4 emits a module
for 50 of the 55 programs in `examples/` (the other five are V3.5-only
counted-loop programs that V4 refuses by name). Every one of the 50 compiles
with Clang 15.0.7, 16.0.6, 17.0.6, 18.1.3, 19.1.7 and 20.1.2, and the 48
that link without extra C fixtures produce the same stdout, stderr and exit
status on every release. The older releases are the Clang inside the
`ziglang` wheels (`zig cc` reads `.ll` files); each object is linked with the
host Clang against the V4 runtime. LLVM 14.0.6 (through `llvmlite` 0.42)
rejects the same modules with `ptr type is only supported in
-opaque-pointers mode`.

What keeps it true:

- [`llvm_text_floor.py`](llvm_text_floor.py) holds `MIN_LLVM_MAJOR = 15`, a
  list of IR syntax that only newer LLVM parses (`memory(...)`, `zext nneg`,
  `or disjoint`, `trunc nuw`, `getelementptr nuw`, `range(...)`,
  `icmp samesign`, `captures(...)` and others) and a typed-pointer check.
  `build_v4.py` runs it on every module it emits, and the LLVM module smokes
  in `check_v4.py` run it on theirs, so a codegen change that needs a newer
  LLVM fails the gate with the construct and the release it needs.
- `build_v4.py` refuses a Clang whose `--version` names a major below 15.
- `freak doctor` already enforces the same floor
  (`CLI_DOCTOR_MINIMUM_CLANG_MAJOR` and `CLI_DOCTOR_MINIMUM_APPLE_CLANG_MAJOR`
  in `src/cli/doctor.fk`); `check_llvm_text_floor` in `check_v4.py` fails if
  either constant drifts from `MIN_LLVM_MAJOR`.

Raising the floor is a decision, not a side effect: change
`MIN_LLVM_MAJOR`, the doctor constants and this section together.

## B0: how many past backend defects were malformed text

The proposal's first question asks how much a structured module would have
prevented. The corpus is every fixed backend defect whose symptom is on
record: the handoff 6 findings in [BACKEND_CHECKPOINT.md](BACKEND_CHECKPOINT.md),
closed GitHub issues against the LLVM backends, and commits to
`freak_codegen_llvm` (V4) and `src/compiler/v3/emit_llvm.fk` (V3) that state
what went wrong. Review rounds whose commits do not state a symptom are left
out, as are refusals (a named "not yet supported" fence is a scope limit,
not a defect), front-end bugs (such as #130, a route-case splitter in HIR)
and performance work. "Backend" here means MIR lowering and codegen. Counted on 2026-11-23
against `b883830`.

**Malformed text: 10.** Clang or the LLVM verifier rejected the module.

| # | Backend | Where | Defect | Kind |
|---|---|---|---|---|
| 1 | V4 | F04, #136 | A callback's callee SSA value was defined twice and passed to itself | duplicate SSA name |
| 2 | V4 | F06, #136 | `ret i1 yes`: a boolean alias reached the IR as text | bad operand spelling |
| 3 | V4 | F08, #136 | Shape and field code referenced an undefined `%P` layout type | undefined type |
| 4 | V4 | #137, `a21b361e` | Two ordinary methods emitted two `A::value` definitions | duplicate symbol |
| 5 | V4 | #136 | Extern/body and literal-global name collisions, and repeated generated callback definitions | duplicate symbol |
| 6 | V4 | `e100ae51` | LLVM Sum type braces were eaten by string interpolation in the compiler source | quoting |
| 7 | V4 | `18f60ed7` | Modules whose only word owners were aggregates called word drop glue without declaring the word runtime | undefined symbol |
| 8 | V4 | `1dd86175` | A dispatch-only module used a vtable type it never defined | undefined type |
| 9 | V3 | `2978c904` | A field store targeted an undefined SSA register named after the field | undefined value |
| 10 | V3 | `bc093681` | `time::now_ms` was called without a declaration | undefined symbol |

**Valid IR, wrong behaviour: 8.** The module verified and the program did the
wrong thing.

| # | Backend | Where | Defect |
|---|---|---|---|
| 1 | V4 | F02, #136 | Nested counted loops shared a local: three levels returned 8 instead of 24 |
| 2 | V4 | `af1d5aeb` | A field or index store evaluated its value before its target |
| 3 | V4 | `c90fcdf8` | Compound element updates evaluated the index twice (`a[f()] += 1`); `[v; 0]` handling |
| 4 | V4 | `babe566b` | Overloaded `+=` on an indexed place evaluated the index twice |
| 5 | V4 | `40d08324` | A discarded `or else` skipped its fallback on the empty edge |
| 6 | V4 | `2ba1a21f` | Field places did not carry the declared field type, so loads and stores could use the wrong width |
| 7 | V3 | `58dc12bc` | Method dispatch picked the first shape with a matching method name and crashed on the wrong layout |
| 8 | V3 | `2978c904` | User method calls dropped their arguments (`c.add(5)` became `Counter_add(c)`) |

**Runtime and link contract: 2** (`0fbf94a0`, `aa6e4a88`, V3): declarations
and runtime definitions disagreed by name or were defined twice at link
time. The IR was valid; a structured module would not have caught these, the
packaged runtime objects (B3) would.

What it says:

- About half of the recorded backend defects (10 of 20) were malformed text.
  Every one was loud: Clang refused the module, so none shipped as a
  miscompile. A typed module with the B1 structural checks (every operand
  defined, no duplicate symbols, typed constants, a printer that owns
  quoting) would have caught all ten inside the compiler, with a named
  error instead of a Clang message.
- The other half verified and ran wrong. The text backend did not cause
  those and a structured module does not prevent them; MIR facts and native
  gates do.
- So B1 is worth doing for diagnostics and as the step towards B2, but it
  is not a correctness fix for the defects that cost the most to find.

## B2: the LLVM bridge

Started 2026-11-23, ahead of the A4 gate by the maintainer's choice: the
bridge is new code beside codegen and changes nothing the text backend
emits. B1 (the typed module inside `freak_codegen_llvm`) still waits for
tier 3 and A4.

**Pinned LLVM: 22.1.8** ([`llvm.lock`](llvm.lock)). 22.1.8 is the last
point release of 22 (checked 2026-11-23: there is no 22.1.9). 23 also
qualifies under decision 16 (it is at 23.1.6), but its point series is still
running; moving to it is a one-line lock change plus checksums. The lock holds one
SHA-256 per host archive; `build_llvm_bridge.py` downloads the official
release archive, checks it, and keeps only the C API headers, `llvm-config`
and the static libraries (313 MB on Linux x86-64, cached in CI by the lock's
hash). Only Linux x86-64 is pinned so far.

**The bridge** is [`llvm_bridge/freak_llvm_bridge.c`](llvm_bridge/freak_llvm_bridge.c)
over LLVM's C API; its header states the contract:

- A session owns one LLVM context, module, builder, target machine and data
  layout. FREAK holds int64 tickets (kind, session slot, session generation,
  index); no LLVM pointer crosses into FREAK. Releasing a session disposes
  everything and every ticket of it is refused afterwards, even when the
  slot is reused.
- Every call returns an int64: a ticket, 0, or a negative error code with a
  message. Kinds and types are checked before LLVM is called (a type where a
  value belongs, a load from a non-pointer, a second terminator, an argument
  of the wrong type, a duplicate symbol), so misuse is an error result.
- No C++ exception can cross: only the C API is used and no C++ shim has
  been needed yet. LLVM's fatal-error handler is installed to name the
  bridge before LLVM ends the process.
- Names and paths are (bytes, length) pairs, copied. The core is
  independent of FREAK's word ABI; `freak_llvm_bridge_v35.c` adapts V3.5
  `freak_word`s for tools built by `v35_seed.py`, and a V4-native host gets
  its own adapter.
- It covers types (integers, floats, pointers, arrays, named and literal
  structs, function types), functions, parameters, byte-string globals,
  blocks, constants, alloca (always in the entry block), load, store,
  arithmetic, comparisons, casts, select, field and element addresses,
  extract and insert, calls (variadic too), phis, terminators, enum
  attributes, verification, the `default<O0..O3>` pass pipelines, object,
  assembly and IR text output, and the target's sizes, alignments and field
  offsets.

**The gate** (`build_llvm_bridge.py --check`, CI job "V4 LLVM bridge"):
[`tools/llvm_bridge_probe.fk`](tools/llvm_bridge_probe.fk) builds a module
in FREAK (a loop with phis, select, calls between its own functions, a float
conversion, struct field loads, a call to the C library's `puts` on a
private string), refuses twelve kinds of misuse with the exact error codes,
verifies, optimises and emits an object at O0, O1, O2 and O3, and reports
layouts for the four release targets. The gate checks the report line for
line, links each object with a C driver and checks its output exactly.

First measurement for the size row: the probe, which links only the core,
pass pipeline, x86-64 and AArch64 libraries, is 65 MB on Linux x86-64
(53 MB stripped). The full compiler with LLD will be larger.
