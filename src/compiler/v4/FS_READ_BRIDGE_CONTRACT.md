# Existing private FS read bridge prerequisite

This additive test slice is based on release root
`f96d1f5994719928a8ca162c232255a617a7d209` and the accepted source-only
`FS_ENTRY_IMPLEMENTATION_HANDOFF.md` SHA
`11b66b19c95ba8735efd1f4b503cfc44e388abeb65931ea79713e16cf6d4544e`.
It tests the existing `freak_v4_fs_read` directly. It adds no production alias,
runtime source/header, compiler descriptor, inventory registration or public
source admission. The later scalar-sum MIRv9 owner still must implement the
typed fs204 vertical with its own fresh compiler/native/platform evidence.

The established private prototype is:

```c
void freak_v4_fs_read(int64_t borrowed_path,
    int64_t *out_is_ok, int64_t *out_payload);
```

The path is a live owned Word borrowed for the call. Output pointers are
nonnull, distinct writable i64 slots. Tag1 transfers one fresh owned Ok Word;
tag0 transfers one fresh nonempty owned error Word. Both outcomes keep the path
live and unchanged. Empty readable files are Ok. Sized UTF-8 content preserves
NUL and CR/LF bytes; invalid UTF-8 is Err. This is not arbitrary binary data
admission or `fs::read_bytes`, which needs a separate owned List ABI.

The helper initializes valid output slots to zero before validating the path
registry owner. Invalid slots fail before that initialization. Invalid private
owners and slots use the existing system fatal exit1 boundary. These callers
must not seed slots with live owners or imply the helper consumes replacements.
Allocation failure preventing construction of any error owner uses the existing
named Word panic: real SIGABRT on POSIX or CRT status3 on Windows. Abort bypasses
atexit. Probe observations immediately before abort prove the borrowed owner is
still live and unchanged, slots remain zero, and private raw buffers/descriptors
are rolled back. They do not claim ordinary caller cleanup after abort.

The probe includes the unchanged production core, Word and system sources, and
binds the helper through an exact typed function pointer. Its hooks fail
ownership/stream adoption before publication. Raw descriptor and FILE close
hooks close the real resource exactly once before returning an injected error.
They never hide an adopted owner or FILE. Named errors take precedence over
later close errors. Registry table capacity may remain grown; the contract
requires exact live-owner, raw-buffer and descriptor conservation and recovery,
not identical allocator capacity.

Ordinary cases hold two distinct returned payload owners concurrently. Both
payload-first and path-first cleanup are tested. Private malformed path controls
corrupt otherwise fresh live storage deliberately, and restore poisoned size
metadata before dropping it; they are not ordinary FREAK Word construction.
NUL plus malformed UTF-8 selects the path NUL error before UTF-8 validation.
A stale pointer control makes no intervening owner allocation after drop.

The frozen dataset contains 58 process-isolated scenarios: 55 on Linux/macOS
and 57 on Windows. It includes six exact readable byte fixtures, paired fresh
payloads, path-first release, eight malformed UTF-8 files, missing/directory
errors, a real POSIX FIFO, private path/slot/owner boundaries, 20 portable
I/O/storage/compound faults, two Windows path conversion faults, and both
LLVM-owned and C-owned audit death controls. Each ordinary injected fault must
recover through 64 further successful reads while its first Err owner stays live.
The C audit control uses the actual owning numeric Word constructor and asserts
heap/data, exact payload and one C owner before exit. Cloning a non-owning
literal preserves its nonownership and cannot establish this death capability.
The large metadata case rejects the selected contents allocation without
actually requesting a multi-gigabyte allocation.

POSIX open must retain O_NONBLOCK so a FIFO read cannot wait for a writer before
nonregular-file rejection. Windows reads use the established Unicode path and
binary-open behavior. The real directory case retains an exact boundary receipt:
rejected `_wopen` requires the named open error and zero stat/stream/read/adopt
or descriptor-close calls; admitted `_wopen` requires an actual successful
nonregular stat, the named nonregular error and exactly one real raw close,
with zero stream/read/adopt calls. POSIX requires the latter branch. Both
hold two fresh Err owners and finish with zero owners/descriptors/raw buffers.
No unverified claim about all Windows CRT directory spellings selects the oracle.
The private probe uses the established argument snapshot
only to obtain exact Unicode fixture paths on Windows; this does not prove
typed-process generated entry setup, parameterized main or process::args().

Probe stdout is a strict ASCII observer protocol, containing the tag and exact
payload byte hex, unchanged-path/fresh-payload checks, recovery count and zero
owner/descriptor/raw-buffer counts after ordinary cleanup. The helper itself
must add no stdout/stderr on Ok or Err. Fatal cases require empty stdout and
their exact named stderr and termination. Only Windows CRT CRLF normalization
is permitted; hex payload data is never normalized. Sanitizer diagnostics,
audit deaths, extra text and alternate termination cannot pass ordinary/fatal
oracles.

O0/O2/O3 are mandatory. Plain mode is an additional Linux/macOS/Windows gate;
Linux ASan+UBSan is the default gate. Sanitized matrices additionally require
three actual controls: ASan heap-buffer-overflow with status86, UBSan signed
overflow and MIN32/-1 division with status85, their operation diagnostic and
sanitizer summary, and empty stdout. Missing compiler/instrumentation or silent
capability controls fail. Prepared native invocation totals are 165 plain
Linux/macOS, 171 plain Windows, or 174 sanitized Linux, plus three Clang builds
and two compiler-identity commands per driver. These are obligations, not results.

The guarded driver reuses the independently accepted checked32 source's Runner,
bounded secondary-error retention, sanitizer restoration and Conservation
machinery, loaded from frozen source with SHA
`1fe37e9bf8f33c72193e85cfa87ffef78ed29bc0663ff447acd35a42f6fbd8e2`.
No cached bytecode or preloaded support/guard namespace may substitute it. The
freeze includes all five new files, six unchanged runtime source/header files,
that support source and the central process guard: 13 inputs. Original/copy,
selected/resolved compiler, every produced binary and all fixture bytes/kinds
are checked around guarded jobs and final publication. Compiler/identity jobs
are capped at 120 seconds/512MiB; native jobs at 10 seconds/128MiB; every stream
at 1MiB. Only one child runs at a time. The report stays incomplete through
environment restoration and final pins; pending reports are nonauthoritative.
Secondary attribution/publication errors preserve the original failure and
cancellation. A zero driver exit and complete validated report are both required.

Process-free preparation executes no compiler/native child or project harness:

```sh
python -B -u -m unittest discover -s tests -p test_v4_fs_read_bridge.py -v
```

Actual commands require a separate root execution lease and virgin external
evidence directories, after independent source/pure review:

```sh
python -B -u tests/v4_fs_read_bridge.py --plain --clang <pinned-clang> --work <virgin-plain-dir>
python -B -u tests/v4_fs_read_bridge.py --clang <pinned-clang> --work <virgin-asan-ubsan-dir>
```

The helper's void/i64/two-outslot ABI fits the accepted scalar-sum `{i1,i64}`
carrier plan: two distinct per-call alloca slots, one void call, explicit loads,
tag-based construction and one owned payload to transfer/drop in either arm.
No C struct ABI or auxiliary sum object is introduced. Binding-aware fs204
admission, explicit immutable path Lend, loan end ordering, SumTake, drop flags,
live/detached validation, snapshot/editor/cache integration and source ownership
cleanup remain the sole compiler owner's next vertical. B01, raw/foreign sum,
List, generic/nested/indirect sum and main-parameter fences remain unchanged.
