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

## B0: attributes on runtime helpers

Codegen now tells LLVM what the C runtime promises about its own helpers
(`v4_codegen_llvm_runtime_declare_attributes` in `freak_codegen_llvm`). It
touches only `declare` lines of `@freak_v4_` helpers, after the module's
runtime block is assembled; user declarations, definitions and helpers it
does not know pass through unchanged.

| Promise | Helpers | Why it holds |
|---|---|---|
| `nounwind` | every `@freak_v4_` helper except the panic entry points | The runtime is C built without exceptions; a panic reports and ends the process with `abort` or `_Exit`, it never unwinds. The panic entry points are left alone so a later unwinding panic strategy does not inherit a wrong promise. |
| `readonly` | `word_length`, `word_bytes`, `word_byte_length`, `word_equal`, `word_starts_with`, `word_ends_with`, `word_contains`, `word_checksum`, `word_snapshot_line_count`, `word_snapshot_field_count`, `compiler_array_len` | They read a word or an array and allocate nothing. Their only writes are the runtime's private scalar-count memo and, on a panic, the report written on the way out. The module cannot observe either; the same reading other language runtimes take for memoising accessors. |
| not given: `willreturn` | all | Any of them may panic, and a panic does not return. Without it LLVM still deletes nothing and keeps every panic in order. |
| not given: `nocapture` | `word_parse_int_checked`, `process_arg_checked`, `fs_read` | They compare their two result slots for aliasing. LLVM 21 counts that comparison as an address capture, so the promise would be too strong, and the slots are read back at once anyway. |
| not given: ranges, `memory(...)` | all | `range(...)` and `memory(read, inaccessiblemem: readwrite)` (the exact truth for the readonly group) need LLVM 19 and 16; the floor is 15 and `llvm_text_floor.py` rejects them. Call-site `!range` metadata would need every call emitter changed and is left for B1, where calls are built in one place. |

The spellings are LLVM 15's. LLVM 16 and newer read `readonly` as
`memory(read)`: checked by parsing the attributes with LLVM 22.1.8 (the B2
pin) and by compiling the modules with Clang 15.0.7 to 20.1.2.

### Measured

`benchmarks/v4/runtime_helper_attributes.py` builds each program once,
removes the attributes for the second build, and runs both alternately
(medians of 5, x86-64 Linux, Clang 18.1.3, O2):

| Program | Without | With | Speed-up |
|---|---:|---:|---:|
| `text.length()` in a loop condition (300,000 passes over 72 characters) | 1.856 s | 0.023 s | 80x |
| three queries per pass (3,000,000 passes) | 1.631 s | 1.122 s | 1.45x |
| control: a new word per pass (1,000,000 passes) | 4.063 s | 3.034 s | none (see below) |
| tier 1 hot loop (100,000,000 iterations) | 0.685 s | 0.623 s | none (see below) |

The control and tier 1 loops compile to the same instructions with and
without the attributes (only unwind-table directives differ). Linking the
same two control modules against prebuilt runtime objects instead turns
the gap around (about 3.1 s without, 4.3 s with), so gaps of that size are
the layout of the two binaries, not the attributes. Raw samples:
`benchmarks/v4/runtime_helper_attributes.json`.

What moved and why: when `text.length()` is in a loop condition, LLVM now
asks once per loop instead of every pass, because the helper reads memory
nothing in the loop writes. With several queries in one loop only the first
moves: the first may panic, so LLVM cannot assume the next one is reached
on every pass without `willreturn`. Where the loop also makes a new word,
nothing moves, and nothing should. The tier 1 hot loop calls no helper and
is unchanged, which is the judgement the row asks for: no regression where
there is nothing to gain.

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
  extract and insert, calls (variadic too), phis, terminators including
  `switch`, calling conventions on functions and calls (C, fast, cold, and
  the x86-64 Win64 and System V ones, refused on other targets), attributes
  on functions and on call sites (plain ones like `nounwind`, integer ones
  like `align` and `dereferenceable`, and type ones like `sret` and `byval`,
  each only through its own entry point and only where it can apply), DWARF
  line tables (one unit per session, a subprogram per function, the
  builder's current location), verification, the `default<O0..O3>` pass
  pipelines, object, assembly and IR text output, and the target's sizes,
  alignments and field offsets.

**The gate** (`build_llvm_bridge.py --check`, CI job "V4 LLVM bridge"):
[`tools/llvm_bridge_probe.fk`](tools/llvm_bridge_probe.fk) builds a module
in FREAK (a loop with phis, select, calls between its own functions, a float
conversion, struct field loads, a call to the C library's `puts` on a
private string, a `switch` with line-table locations, a `fastcc` internal
function, a 24-byte struct returned through `sret` as C returns it, and a
struct passed by `byval` copy), refuses 22 kinds of misuse with the exact
error codes, verifies, optimises and emits an object at O0, O1, O2 and O3,
and reports layouts for the four release targets. The gate checks the
report line for line, checks the module text for the attributes, calling
conventions and debug metadata, links each object with a C driver and
checks its output exactly.

First measurement for the size row: the probe, which links only the core,
pass pipeline, x86-64 and AArch64 libraries, is 65 MB on Linux x86-64
(53 MB stripped). The full compiler with LLD will be larger.
