# V4 release progress

Delivery order: Preview (Tier 1), followed by self-hosting and V3 replacement
(Tiers 1–4 and 8). The uploaded release checklist is the scope; it does not
override the language bible. Strict root scope remains the default. Compiler
crate initialization must use explicit per-file bootstrap compatibility mode.
The public release remains v0.14.2; this work does not create a release.

## Preview prerequisites

| Requirement | Implemented and verified scope | Release gate |
| --- | --- | --- |
| Module/body assembly and lookup scaling | Existing fragment assembly and derived TY/HIR/resolve indexes; one integrated Linux workload with 3,200 tasks and 22,403 lines completed all stages without diagnostics in 12.895 s, peak 806.15 MiB under 2 GiB | Repeat relevant resource tests after compiler changes; no claim of a measured growth rate or other platforms from that run |
| Optimized compiler build | `build_v4.py --compiler-opt 0\|1\|2\|3`, isolated optimization-specific compiler cache, optimized Hello World checkpoint | Final coherent-head platform CI |
| Owned Word values | NonCopy locals, parameters, returns, replacements and temporary cleanup; borrowed observers, comparisons, concatenation and display; generated native ownership audits and sanitizer controls | Final coherent-head platform CI |
| Sized Unicode and interpolation | Embedded NUL, character indexing/slicing, lower-case runtime and HIR interpolation plans; coherent Linux Word-bounds plain/sanitizer matrix at `4e3847c` passes 715 guarded jobs with independent artifact review | Current-head platform CI and explicit transfer of retained source evidence |
| Literal/general `say` | Updated fixture passes its 27 static byte cases, seven owned/general positives, seven typed diagnostics, ten forgeries and snapshot roundtrip | Final coherent-head platform CI |
| `say_err` and hosted runtime portability | Generated owned-message lane and exact raw output tests; source fixes for finite Unicode fixture construction, a known Darwin linker warning and Windows CRT declaration warning | Fresh Linux/macOS/Windows CI on the corrected head |
| Process arguments and typed OS results | Existing C entry argument setup; the closed `maybe<int>`/`result<word,word>` slice passes all 76 compiler cases, 30 generated O0/O2/O3 programs and eight mandatory audit/sanitizer controls on coherent `4e3847c` | Typed process/FS generated gate and coherent-head platform CI |
| Filesystem bridge | Linux plain and ASan/UBSan O0/O2/O3 bridge proof, exact owned Ok/Err slots, Unicode/NUL/nonregular-file controls | Typed result generated gate and macOS/Windows native gates |
| Integer arithmetic | Checked native overflow and divide-by-zero contract; private C32 arithmetic lane passes hosted Linux/macOS/Windows | Fresh coherent-head CI; C-width native ABI admission remains fenced by B01 |
| Panic and bounds | Explicit `--panic=abort` path and checked integer/runtime boundaries; isolated private C panic-context runtime passes plain and full sanitizer matrices | Default compiler unwind and cleanup are not implemented; the private panic context still requires compiler/LLVM integration |

The bible does not currently specify a new main-parameter ABI or a concrete
runtime-honor failure trigger. Process argument access can be implemented
without inventing either. Default panic remains a language requirement; explicit
abort does not complete it. Catch, general PanicInfo payloads, sortie containment
and general deferred cleanup also remain open.

## Current correctness work

- Exhaustive route construction now avoids a reachable synthetic Unreachable
  endpoint. Both `when` and `check route` producers are fixed. Fourteen focused
  cases, including setup-proven hostile snapshots, pass on the integration
  checkout. Structural validation remains strict.
- The region fixture produces 44 diagnostics rather than its old 45. Original
  and diagnostic-instrumented images produce identical output. Full membership
  and actual old/new helper execution establish a false LocalID/PlaceID
  collision; focused regressions preserve the real loan conflict and reject
  the false carrier-move error.
- The lend-contract fixture receives a third ownership diagnostic for the same
  illegal borrowed Word return. The official focused run passes all 43 strict,
  unique assertions, preserving all three messages and help strings. Reviewed
  producer facts distinguish declaration spans, operand trivia and actual
  ReturnValue storage; accepted observers and typed reborrows remain covered.
- The drop fixture correctly blocks repeated consumption of an owned Word in
  a loop. Focused execution passes the exact single diagnostic, help and
  local-declaration span, alongside the preserved drop/DropIf ordering facts.
- Independent review blocked the first closed Sum checkpoint: native equality
  could emit an invalid aggregate `icmp`, downstream builtin identities omitted
  available binding eligibility, and inner payload aliases had inconsistent
  carrier/constructor/extraction treatment. Later review found ordered
  comparisons and a formal-parameter shadow guard gap. The bounded bootstrap
  diagnostic also exposed interpolation in two LLVM type strings. The reviewed
  successor fixes those findings and passes all 76 compiler cases, all 30
  generated O0/O2/O3 programs and eight mandatory audit/sanitizer controls.
  Independent review verifies the completed coherent `94a62d9` artifacts.
  Later source changes have separate review and verification: the ordinary
  recursive collector's Linux O0 frame decreases from 3,264 to 2,736 bytes,
  and its original depth-256 contract passes locally and in Windows CI at
  `20724a8`. This does not identify the Windows crash's faulting function.
  Native target and fixture repairs must pass their current-head gates.
- Independent review blocked the new Word-bounds driver because it could
  report success after a retained image changed and had first-cause, cleanup,
  deadline and provenance gaps. The driver has independently reviewed fault
  controls. The coherent `4e3847c` Linux matrix passes 715 guarded jobs across
  plain and sanitizer stages, including 308 native executions. Independent
  endpoint review verifies all 6,303 artifacts, exact raw channels, original
  resource caps, source/tool hashes and process-group cleanup. All 24 generated
  UTF-8 source programs retain their original bytes. At `b6ea2b0`, Windows CI
  also passes all 34 pure methods and its plain generated native Word gate.
  These receipts retain their recorded revision and platform; later changes
  require explicit source transfer or fresh execution.
- The official focused MIR check run passes all three matching smokes. Its
  57 Maybe/Result assertions now inspect `SumTake`, `TakeSome`, the source
  `UseLocal` and its canonical `_check_subject` LocalID. The previous fixture
  queried a SumTake source RvalueID as a PlaceID; the general Result path still
  verifies its original `UsePlace`/`ok` projection facts.
- The private C panic-context runtime at isolated `24fad27` passes the full
  320-job sanitizer gate: ten C builds (six production and four capability),
  306 runtime outcomes and four mandatory capability executions. Independent
  endpoint review verifies ASan, UBSan, LeakSanitizer and double-free diagnostics
  and their required exit statuses. The earlier failed leak-probe attempt remains
  preserved. This establishes the private C runtime/helper ABI scope; compiler/LLVM
  generation, default unwind and language cleanup integration remain pending.

## Self-hosting and V3 replacement

Private compiler arrays have a reviewed Linux plain/sanitized proof for 188
guarded jobs, with exact rejection and actual ownership-fault controls. The
raw owner range check runs before UTF-8 traversal. The six private array files
are integrated and their hosted gates are registered. This is a prerequisite,
not public `List<T>` or native self-hosting: arbitrary mixed V3/private handles
are still prohibited until an origin/type fence exists.

Bootstrap globals, source-ordered once-only module initialization, mode/global
snapshot identity, array builtin lowering, word/snapshot primitives, coherent
multi-crate compilation, error-heavy Meiya limits, zero-diagnostic crate
compilation, Stage 1, Stage 2 fixed-point comparison and self-built smokes remain
open. Existing strict individual-crate diagnostics are not self-hosting proof.

Native aggregate layouts, general routes/variants/Maybe/Result, generic methods,
doctrine/vtable calls, shared ownership, public collections, closures and the
remaining semantic boundaries remain independently tracked Tier 3 work.
V3 syntax/module/stdlib/toolchain parity, all target platforms, the preservation
suite, runtime/compiler differential tests, benchmarks and Tier 8 distribution
are required before calling V4 a V3 replacement. Shipping V3 tests and goldens
must remain intact.

## Evidence and readiness

All actual evidence is tied to its recorded source revision and platform.
Worker-only evidence is not a whole integration-checkout proof. Official
focused checker runs retain aggregate guard logs and output counts; the six-job
diagnostic run additionally retains every raw child channel. Resource caps and
semantic assertions are not relaxed to obtain green checks.

PR #143 is a preview prerequisite milestone. Readiness requires current-head
Linux/macOS/Windows CI, the generated Word-bounds and typed OS matrices,
independent review and resolved review findings. The PR description and retained
verification receipts record the candidate SHA and actual gate outcomes.

At `b6ea2b0`, all six shipping jobs pass, including Windows bootstrap and its
three test suites. The native macOS Sum gate passes all 30 O0/O2/O3 program runs
and six C/LLVM ownership controls. Its Darwin-only bounded C-to-LLVM probe
discovers the initialized SDK deployment target. A separate link module changes
only that target header; original module bodies and layout bytes remain exact.
This replaces the earlier versionless IR-frontend override. Linux sanitizer
evidence comes from the separately reviewed `4e3847c` native gate.

The `b6ea2b0` helper failures identify the remaining correction scope: Windows
Sum tests wrote a fake LLVM module using CRLF and read two UTF-8 source files
with the default locale, while Linux/macOS typed-operation tests expected the
wrong rejection stage for valid ordinary shadows. Independent source review
verifies explicit UTF-8 reads and LF byte writes without changing the production
parser. The typed diagnostic measures all 25 original contract sources; this
initial-query report does not establish strict forgery or native readiness.
Valid root constants and FFI-safe private-symbol declarations must exercise
their original zero-identity and exact named fences in the strict gate. A closed
Sum crossing the C ABI must retain both frontend rejection and the named native
error before any module is published. Current-head strict and generated typed
gates, platform CI and independent review remain required before PR readiness.

At `1917f3e`, one compiler bootstrap and all 25 strict typed contracts pass
with independent endpoint review. All 26 CI jobs complete: 23 pass; Windows
finds a platform-path spelling mismatch in a Sum test, while Linux/macOS find
an unreachable live MIR join in the first typed filesystem program. Separate
bounded nine-input facts and ten-job getter diagnostics confirm the exact MIR
error in seven unchanged programs; these observations are not native gate
passes. The test now derives the expected runtime path from its path object.

Built-MIR closes a completed Maybe/Result join only when it has no predecessors.
It checks later source through a private diagnostic continuation, then uses
existing checked compaction before validation or publication. Nested terminal
if/else joins receive this treatment only within check arms, whose construction
context saves and restores its previous value. Missing bindings in later
source retain a named error and original span. Result display targets compact
with the actual block edges. CFG validation, detached snapshot admission,
native seals, ABI fences and the nine-program/forty-case typed matrix retain
their original contracts. Fifteen registered regressions cover terminal and
live joins, nested checks/if arms, loop exits, later source errors, ownership,
canonical roundtrips and hostile live/detached endpoints. Current-head focused,
Sum compiler/native, typed generated gates and all platform CI remain readiness
requirements; historical receipts retain their recorded revisions.

At `2ece941`, the renewed Sum gates pass all 76 compiler cases with six
bootstrap builds, followed by 30 native executions and eight mandatory
ownership/sanitizer controls. Linux native targets and original/link module
hashes match. Later changes require explicit unchanged-input transfer.

The typed module validator accepts both implicit and explicit default-C calls
while requiring one user-main reference and the original entry setup order.
It permits the compiler's single unused Word conversion declaration while
rejecting legacy calls, references and malformed prototypes. The fifteen-mode
fixture constructs embedded source braces with `chr` to avoid V3 interpolation;
all intended program bytes, arguments, assertions and caps remain unchanged.
Fresh focused and full typed native gates remain required before readiness.

These checks do not complete default compiler unwind, self-hosting or V3
replacement. The release version remains unchanged; no release tag is created.
