# Closed typed OS and native entry gate

This gate is prepared on `54baae3df0dbacf6864d02d6a7822a515f7d8e84` in
`feat/v4-typed-os-entry-gate`. It owns only the two new FREAK fixtures, the
new Python driver and its pure tests, and this document. Compiler code,
runtime code, central registration, inventory and workflows remain with
their existing owners. The six-crate Sum implementation is a prerequisite;
preparation or the independently accepted private Linux FS proof does not
establish this typed vertical. Compiler and native execution are **UNRUN**.

The accepted planning inputs are `NATIVE_SCALAR_SUM_PLAN_dff689d.md`
(SHA256 `4e90733732acd4e1dd066201d4a665940e4e8e0b9476a7d8aa02cad6a2c62498`)
and `FS_ENTRY_IMPLEMENTATION_HANDOFF.md`
(SHA256 `11b66b19c95ba8735efd1f4b503cfc44e388abeb65931ea79713e16cf6d4544e`).
The compiler owner confirmed the existing spelling `check value { got n ->
{ ... } nobody -> { ... } }` and `check result value { ok(text) -> { ... }
err(message) -> { ... } }`. No grammar change is proposed. Exact new native
diagnostic goldens must be reconciled with the first coherent immutable Sum
compiler commit before any actual launch freeze.

| Source | Descriptor | Result | Native bridge |
| --- | ---: | --- | --- |
| immutable Word `.to_int()` | 120 | prelude `maybe<int>` | `void(i64, ptr, ptr)` |
| `process::arg(int)` | 202 | prelude `result<word,word>` | `void(i64, ptr, ptr)` |
| `process::args_count()` | 203 | int | `i64()` |
| `fs::read(word)` | 204 | prelude `result<word,word>` | `void(i64, ptr, ptr)` |

Qualified ordinary root, parameter, local, import and full callable bindings
retain precedence. The first intrinsic forms are positional only. The two
internal LLVM types are distinct named `{ i1, i64 }` carriers. Both are
nonCopy. Some(0) and an empty Ok are valid; payload bits do not determine the
tag. Result owns one fresh Word in either arm. Parser and FS borrow their
input Word. `_` does not extract and leaves the subject for scope cleanup.

The contract fixture runs one complete pipeline per process. Its 25 closed
modes cover the four descriptors, exact immutable Word loan graph and three
nonconsuming canonical tag observers; detached MIRv9 rejection/recovery and
old/fresh module seals; live identity rejection; entry setup in scalar-only
and helper bodies; parser/FS library admission; ordinary qualified/shadowed
bindings and named argument rejection; and exact native process-library,
parameter-main, sum FFI/raw storage and private-symbol fences. More general
sum constructor, extraction, branch-proof and pressure hostility belongs to
the compiler owner's focused gate. Rejected detached snapshots must preserve
the original snapshot and sealed module bytes. These prepared source checks
are not actual MIR or compiler evidence.

The execute fixture emits one authored source per process, validates/restores
MIRv9, preserves the old seal and compares the freshly restored module
byte-for-byte. Its input loader uses the explicit bootstrap compatibility
surface. Only the emitted authored programs test the typed public surfaces.

Nine authored programs supply 40 Linux/macOS and 38 Windows invocations at
each of O0/O2/O3. Seven FS/entry programs follow the accepted addendum; two
add typed argument/parser relay and independent argument-boundary results.
They cover count including index0, empty/missing/negative/extreme arguments,
spaces/quotes/backslashes/non-ASCII argv, parser zero/min/max/leading-plus,
empty/sign-only/Unicode digit/whitespace/junk/range failures, sized NUL file
contents and paths, exact binary UTF-8 contents, empty files, named file
errors, borrowed path/text still usable, ordinary relay/move/rebind, ignored
and `_` outcomes, joins, loop-fresh reads, continue and break cleanup.

Real POSIX directories and FIFOs must produce the exact nonregular error.
The driver creates a real FIFO and the existing helper must reject it without
blocking. The real Windows directory case is excluded: `_wopen` rejection
and successful descriptor/nonregular `_fstat64` are two separate possible
source-selected boundaries, and no measured Windows CRT receipt has been
established for this typed gate. Other Windows cases remain required. This
does not claim Windows directory semantics; the separate private FS gate
contains deterministic branch controls. OS argv cannot contain NUL; parser
NUL coverage comes from sized Word data. Invalid UTF-8 file contents produce
the exact owned Err. Only Windows CRT line CRLF normalization is allowed.
All raw observed channels are retained before comparison; intended fixtures
contain no CR bytes that normalization could hide.

Entry retains exactly one legacy setup call. Any validated process202/203
anywhere in the module requires exactly one V4 setup call and declaration,
ordered after legacy setup and before zero-parameter source main. Parser/FS
only libraries need no process setup. Process-using libraries and
parameterized main remain fenced. Generated LLVM must use the existing void
bridges, two distinct statically allocated per-call slots, explicit zeroing,
tag/payload loads and aggregate construction. No compatibility Word-return
helper or invented C result-struct ABI may substitute for these operations.

The driver is process-free on import. Actual `main` requires
`FREAK_TYPED_OS_ENTRY_ROOT_GRANT=typed-os-entry-native-gate-v1` before
source/tool access; this token is a launch guard, not evidence of review or
execution. A lead-owned immutable source/tool/controller freeze and exclusive
host lease are still required. Evidence must use a virgin external directory.
All compiler libs, bootstrap Python inputs, seven native runtime sources and
seven headers, both fixtures, driver/test/doc, central guard and accepted
retention support are copied and conserved. Frozen Python modules use fresh
namespaces, no stale bytecode, and imports must resolve into the frozen tree.
Generated sources/modules, selected/resolved compiler and every known output
image are conserved around guarded jobs and before final publication.

The exact accepted checked32 `_Evidence`/Runner/conservation support remains
unchanged. Attribution, partial-channel retention and publication are
independent best-effort actions. An original failure, explicit cause or
cancellation keeps its identity. Sanitizer setup and all three caller options
use the reviewed independent restoration contract. ASan and UBSan both use
86 for ordinary and ASan children; both use 85 for each UBSan control child.
The scoped override restores the surrounding 86 and final caller values.
Strict sanitizer death statuses are not widened.

| Guarded job | Seconds | Memory MiB | Output MiB/stream |
| --- | ---: | ---: | ---: |
| bootstrap Clang | 120 | 1024 | 1 |
| compiler pipeline | 60 | 64 | 1 |
| runtime/native Clang and identity | 120 | 512 | 1 |
| native program or capability | 30 | 128 | 1 |

Bootstrap compilers retain the 1024 live-array-handle cap. Both C and LLVM
ownership audit macros apply to every native runtime object, program and
capability image. Three real C audit deaths and three real LLVM audit deaths
are required per stage. Linux ASan+UBSan additionally requires nine actual
heap/overflow/shift controls across O0/O2/O3; a missing capability cannot be
skipped. Plain Linux, macOS and Windows proof is separate from sanitizer
proof. Only registered host TargetSpecs are admitted; target emission is not
evidence of executing another platform.

Each complete stage creates 53 Clang images, performs two compiler identity
jobs and 34 process-isolated compiler jobs. Linux/macOS plain adds126 native
invocations for215 guarded jobs; Windows plain adds120 for209 jobs. Linux
sanitized adds135 for224 jobs. These are prepared counts, not observed results.
The closed reports require all25 contract modes, nine emissions, every
scenario/optimization pair, exact statuses/channels, every capability,
46 generated source/module inputs and53 output images with final hashes.
`complete` stays false through environment restoration, final conservation
and handled publication. Every failed attempt is retained.

General/nested/generic/borrowed sums, List and parameter-main entry,
callbacks/foreign/raw sum admission, native unwinding and target-bound B01
completion are outside this gate. Physical Linux/macOS/Windows execution,
public fs204 and the complete typed vertical remain unproved until the lead
records current immutable compiler and actual native evidence.
