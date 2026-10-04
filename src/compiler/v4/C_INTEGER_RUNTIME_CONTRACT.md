# Checked32 C runtime prerequisite

This source contract is based on release root
`88c79517e827417c01a4f821e72a9b6e69629ada` and the bounded B01 plan SHA
`c26d20b0c313060911d310160ba4c79afab05f08abaafb691244466bf055dfe0`.
It adds a disjoint, compiler-private C runtime prerequisite. V4 source
`c_int`/`c_long` admission, target-bound TY/MIR/LLVM, runtime source inventories,
existing V3/numeric helpers and public language semantics remain unchanged.
The later compiler vertical must preserve its named B01 fences until complete.

The new header declares exactly 16 default-C functions:

| Prefix | add/sub/mul/div/mod | neg | from_int | from_uint |
| --- | --- | --- | --- | --- |
| `freak_v4_i32_` | `(int32_t, int32_t) -> int32_t` | `(int32_t) -> int32_t` | `(int64_t) -> int32_t` | `(uint64_t) -> int32_t` |
| `freak_v4_u32_` | `(uint32_t, uint32_t) -> uint32_t` | `(uint32_t) -> uint32_t` | `(int64_t) -> uint32_t` | `(uint64_t) -> uint32_t` |

The signed range is [-2147483648, 2147483647]; the unsigned range is
[0, 4294967295]. Add/sub/mul/neg use checked mathematical values, at every
optimization level. Signed arithmetic widens to int64 before evaluation.
Unsigned multiplication widens to uint64: UINT32_MAX squared is
18446744065119617025, below UINT64_MAX. Unsigned subtraction checks order
before subtraction; negation accepts only zero. No failing result is narrowed.
Conversions preserve numerical value or fail before the narrowing cast.

Division truncates toward zero; remainder satisfies lhs = quotient * rhs +
remainder. Zero divisors always fail. Signed MIN32/-1 fails for both division
and remainder, even though a widened mathematical remainder would be zero.
Failures do not unwind across C. A private static failure routine matches the
existing numeric runtime's stderr/exit1 policy without changing its ABI.

Every failure has exit status 1, empty stdout, and exactly one diagnostic below
followed by LF. Windows CRT text-mode CRLF is normalized only for comparison;
the guarded driver retains the observed channels. No whitespace stripping,
substring matching, extra output, alternate status or sanitizer diagnostic can
satisfy a helper failure oracle.

| Operation | Exact stderr before the terminating LF |
| --- | --- |
| signed add | `FREAK V4: i32 addition overflow` |
| signed sub | `FREAK V4: i32 subtraction overflow` |
| signed mul | `FREAK V4: i32 multiplication overflow` |
| signed neg | `FREAK V4: i32 negation overflow` |
| signed div zero/overflow | `FREAK V4: i32 division by zero` / `FREAK V4: i32 division overflow` |
| signed mod zero/overflow | `FREAK V4: i32 remainder by zero` / `FREAK V4: i32 remainder overflow` |
| unsigned add/mul | `FREAK V4: u32 addition overflow` / `FREAK V4: u32 multiplication overflow` |
| unsigned sub/neg | `FREAK V4: u32 subtraction underflow` / `FREAK V4: u32 negation underflow` |
| unsigned div/mod zero | `FREAK V4: u32 division by zero` / `FREAK V4: u32 remainder by zero` |
| signed32 from int/uint | `FREAK V4: int to i32 conversion out of range` / `FREAK V4: uint to i32 conversion out of range` |
| unsigned32 from int/uint | `FREAK V4: int to u32 conversion out of range` / `FREAK V4: uint to u32 conversion out of range` |

`tests/v4_c_integer_runtime_vectors.json` freezes 58 vectors from the bounded
plan: 29 successes and 29 named failures. Each of the 16 helpers has both.
The independent Python oracle uses unbounded integers and explicit division
truncation, including both signed overflow edges, UINT32_MAX squared,
MIN32/-1 division/remainder, high unsigned values and checked narrowing.
The C probe binds all helpers through exact typed function pointers and rejects
malformed/out-of-source-range argv with status2 and empty channels.

Process-free oracle tests run without importing the existing compiler harness
or spawning a compiler/native process:

```sh
python -B -u -m unittest discover -s tests -p test_v4_c_integer_runtime.py -v
```

Future native commands require the lead's execution grant and a fresh external
directory. All three O0/O2/O3 levels are mandatory. Clang C driver is required;
MSVC O2 cannot stand in for O3. All-OS plain proof and Linux UBSan proof are
separate gates:

```sh
python -B -u tests/v4_c_integer_runtime.py --plain --clang <pinned-clang> --work <new-external-plain-dir>
python -B -u tests/v4_c_integer_runtime.py --clang <pinned-clang> --work <new-external-ubsan-dir>
```

The driver freezes/copies every owned source plus the central process guard
before compiling, records the selected compiler path, resolved hash/version/native
target, and checks original inputs, frozen copies, selected/resolved compiler and
every produced binary before and after each guarded job and final publication.
The final report requires all three matrix binary identities and matching final
original/frozen/tool/binary pins. It loads the frozen guard
source directly, so stale bytecode cannot replace it. Every subprocess goes
through `check_v4.run_with_heartbeat`, with 60 seconds/512MiB for Clang and
10 seconds/64MiB for native children; output is capped at 1MiB per stream.
It runs one child at a time and retains argv, limits, channels, results,
exceptions, frozen sources and binaries in the external evidence directory.
Primary errors and cancellation retain their identity and explicit cause when
secondary attribution, channel, conservation, report or cleanup operations fail.
Each independent evidence channel and sanitizer environment restoration is
attempted; bounded secondary records contain only stage and exception type.
Exception payloads are never formatted during failure retention. When a guarded
body succeeds, the first retention or cleanup error fails the gate after later
independent actions have been attempted.

The live report remains incomplete while matrices run and sanitizer settings are
restored. A candidate is validated and pinned around final atomic publication.
Failure attempts to republish an incomplete report without masking its primary
error. If the evidence medium itself fails, this publication is best effort:
only a zero driver exit with a validated complete `report.json` can satisfy the
gate; `report.pending.json` is never authoritative. Pure fault controls verify
these decisions with all five subprocess APIs forbidden, without importing the
project compiler harness or executing the non-executable fixture binaries.

Each plain matrix runs 58 vectors and 10 invalid-input controls. Each sanitized
matrix additionally requires two real UBSan capability controls: intentional
signed overflow and MIN32/-1 division, with empty stdout, status88 and their
actual UBSan diagnostic and summary. Missing tools, missing instrumentation,
ordinary helper errors or silent sanitizer controls fail the gate. The helper
vectors themselves must retain their exact numeric outputs or named status1
failures under UBSan. Required totals are 204 plain or 210 sanitized native
invocations across O0/O2/O3, plus three Clang builds and two compiler-identity
commands. These are prepared obligations, not execution results.

This prerequisite proves neither cross-target C/FREAK ABI parity nor native
source admission. The later target-bound vertical must register runtime
sources/private prefixes and prove actual C/FREAK signatures, source typing,
coercions, callbacks, raw pointees, cache/snapshot target identity and platform
execution before promoting B01. Host-native helper execution does not prove a
different compile target or the Windows GNU/UCRT link policy.
