# Private native compiler arrays: additive runtime contract

This prerequisite is based on `f96d1f5994719928a8ca162c232255a617a7d209`.
It does not enable a FREAK intrinsic, `List<T>`, a public C ABI, module globals,
or compiler self-hosting. The native compiler still needs typed array-call
admission/lowering, linear Word cleanup for every clone-out, distinct global
identities, initialization once, and snapshot/query isolation for explicit
bootstrap mode. Bible §17.4 remains the strict default. A later vertical slice
must integrate those requirements; this additive runtime alone closes none of
the release checklist's language or self-hosting items.

## Storage and ABI

`freak_v4_compiler_array_runtime.h` defines a private `int64_t` ticket. Each
live cell owns one registered V4 Word. `push` and `set` borrow their Word and
create an independent sized copy. `get` returns a new owner, including empty
words; callers must drop it. `release` invalidates all ticket aliases and drops
all cells. An integer or child-array ticket encoded as decimal Word data is
ordinary cell data; releasing a parent does not recursively release child
arrays. Existing compiler row owners must still retire their children.

The pool is single-threaded; no allocator/adoption callback may reenter it.
Checked output pointers must be nonnull unowned writable slots disjoint from runtime
and input storage. Word arguments must be live native V4 registry owners.
Borrowed C literals, C `array_get` views, and arbitrary foreign pointers are
not admitted Word inputs. This bridge allocates exact sized copies and uses
`freak_llvm_word_try_adopt_sized` once per fresh allocation. It does not use
`word_view`, C `word_clone`, or `word_take`: C cloning a native nonheap view
does not clone, and taking a borrowed C array cell creates conflicting owners.
Registry adoption is idempotent for an existing pointer/length, not a retain.

Tickets use domain `0x4000000000000000`, a nonzero 29-bit generation, and a
low 32-bit slot encoded as `index + 1024`. Decode rejects low slots below1024,
foreign domains, generation zero, stale generations, inactive slots, and slots
outside the actual table. Generations increase on reuse and retire at their
maximum; shutdown retains the history so old tickets cannot resurrect.

This domain is disjoint from the pinned core C array/builder/buffer/socket
domains. Legacy LLVM arrays use a wider untagged31-bit generation; that can
overlap the private high bits, but their pinned `FREAK_LLVM_MAX_ARRAYS=1024`
and `slot < count` check admit only low slots0–1023. The private slot offset
therefore separates the complete admitted legacy LLVM generation range at
this source version. Changing that legacy pool capacity requires revalidating
this invariant before linking/interop. The newer typed-V3 container pool has
untagged positive tickets and a larger dynamic slot range: slot1024 and
generation `0x40000001` can numerically equal private slot0/generation1.
**Typed-V3 container IDs must not enter this private compiler-array ABI.**
Future bootstrap profile/closed intrinsic identities must enforce this rule
before self-hosting admission. This prerequisite does not claim universally
disjoint runtime handles or silently reject a numerically identical token.
Numeric tickets are runtime identities,
not authenticated capabilities: raw C can forge a current private ticket.
V4 Word pointer ownership is independently authenticated by its registry;
future typed lowering must preserve the ticket/Word distinction.

## Failure, allocation, and compatibility mapping

| Operation | Private behavior | Existing C compiler adapter difference |
| --- | --- | --- |
| `new()` | Fresh positive ticket; `-1` on resource or injected live quota | Retains the compiler's `<0` failure test |
| `len(ticket)` | Invalid/stale returns0 | Same |
| `push(ticket, word)` | Invalid/stale no-op; live input cloned; resource named exit1 | Ordinary C arrays borrow; snapshot C arrays clone |
| `set(ticket, index, word)` | Invalid/stale no-op; live OOB exact legacy exit1; clone before replacing | Every private cell owns, unlike ordinary C arrays |
| `get(ticket, index)` | Fresh owner; invalid/stale/OOB fresh owning empty | Legacy C returns a borrowed cell/empty literal |
| `release(ticket)` | Invalid/stale no-op; valid drops all cells | Private behavior consistently matches owned storage |
| `join(ticket)` | Fresh owner and consumes ticket on success; invalid fresh owning empty | C `word_join` already consumes its collector |
| `snapshot_lines(word)` | Borrow source; empty has0rows; LF split preserves blanks/trailing/CR/NUL; `-1` on rollback | Uses native registered row owners, not C heap views |

Checked `push`, `set`, `get`, and `join` return `OK=1`, `RESOURCE=0`,
`INVALID=-1`, or `INDEX=-2` as applicable. Failed checked outputs are0, a
cleanup sentinel rather than a usable Word. Checked stores and joins preserve
ticket, cells, length, and existing owners on failure. Join consumes only after
its full output has been adopted. Snapshot failures drop all partial rows and
retire their unpublished ticket. Set clones before dropping the old cell,
including when its input aliases that cell.

The legacy-shaped wrappers preserve the exact live OOB set diagnostic
`FREAK: array_set index <index> out of bounds (len <length>)` and exit1.
Other private wrapper resource errors use `FREAK: V4 compiler arrays: ...`
and exit1. Invalid Word provenance/UTF-8 uses the existing V4 Word panic;
POSIX abort is SIGABRT and Windows CRT abort is3. Allocation failures never
return a usable zero Word. The adapter's new clone-out lifetime is a deliberate
private ownership rule; source lowering must schedule a drop for each result.
It must not mechanically keep the legacy borrowed-get cleanup behavior.
The existing C `array_push_owned`/`array_set_owned` helpers consume the incoming
Word even for an invalid ticket. This private ABI deliberately exposes borrowed
stores only, not those consuming variants; an owned-argument lowering must drop
its argument after the borrowed store regardless of ticket validity. Ordinary
C snapshot stores and native private stores both clone before replacement,
but C heap-marker behavior must not be copied into a native Word bridge.

The table and cell buffers grow dynamically, with checked multiplication,
`PTRDIFF_MAX`, signed-length bounds, and staged reallocations. The slot encoding
admits at most `2^32 - 1024` slots before a named resource result. Word copies
and joins require size+terminator to fit the signed allocation/pointer range.
There is no fixed1,024 production-slot ceiling or arbitrary per-word MiB cap.
`FREAK_V4_COMPILER_ARRAY_LIVE_LIMIT` and
`FREAK_V4_COMPILER_ARRAY_CAPACITY_LIMIT` default0; tests inject limits.
The generation maximum can also be reduced in a test translation unit.

The private live quota is separate from the core array quota. OS/process memory
guards cover both, but combined handle accounting is a pending prerequisite
before any self-hosting/resource-equivalence claim. A compiler MIR can require
31arrays per body; the default dynamic profile must prove100,000 simultaneously
live empty arrays, while a distinct injected profile must prove1,024 pressure
and immediate recovery. Runtime table/history allocation intentionally remains
reusable until exit; no automatic atexit drop conceals an owner leak.

## Proof and integration requirements

`tests/v4_compiler_array_runtime_probe.c` includes the unchanged core registry
and the additive array source byte for byte, intercepting only the additive
source's malloc/realloc/adoption calls. It checks actual owner counts, staged
raw allocations, alias safety, stale domains/full legacy generation families,
generation retirement, LF/NUL/CR snapshots, consuming join, resource failures
at each snapshot allocation/adoption position, recovery, live quota, default
dynamic growth, and table/cell rollback. These are probe-only injections, not
production allocator replacements. Successful cases end with zero C/LLVM Word
owners and zero live private arrays; the reusable private table remains.

The guarded driver retains commands, source hashes, production object/binary
hashes, every exact exit/channel, and completion matrix at O0/O2/O3. Default
requires Linux ASan/UBSan and real sanitizer/audit fault controls; `--plain`
is an additional explicit portability run, never a skipped sanitizer pass.
Compilation uses120seconds/1,024MiB, execution60seconds/64MiB, and the
pressure profile injects1,024 private live handles. Every Clang/native command
uses the central process-tree guard. Production TU checks use C11,
`-Wall -Wextra -Werror`. Source/cache identities are conserved before success.
Native execution is pending an independent immutable source/controller review
and the root's exclusive host grant; source preparation is not native evidence.

No existing runtime inventory/build/checker entry is changed here. Later
integration must link the new object once, reserve its private symbol prefix,
add typed signatures for the relevant compiler builtins, preserve checked
no-module failures, register exact executable fixtures and CI gates, and prove
global/array ownership across a native compiler workload. Bootstrap root mode
must remain explicit and isolated from strict/default query and snapshot state.
