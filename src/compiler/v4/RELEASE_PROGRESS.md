# V4 release progress

Delivery order: Preview (Tier 1), followed by self-hosting and V3 replacement
(Tiers 1–4 and 8). The uploaded release checklist is the scope; it does not
override the language bible. Strict root scope remains the default. Compiler
crate initialization must use explicit per-file bootstrap compatibility mode.
The public release remains v0.14.2; this work does not create a release.

## Preview prerequisites

| Requirement | Implemented and verified scope | Remaining gate |
| --- | --- | --- |
| Module/body assembly and lookup scaling | Existing fragment assembly and derived TY/HIR/resolve indexes; one integrated Linux workload with 3,200 tasks and 22,403 lines completed all stages without diagnostics in 12.895 s, peak 806.15 MiB under 2 GiB | Repeat relevant resource tests after compiler changes; no claim of a measured growth rate or other platforms from that run |
| Optimized compiler build | `build_v4.py --compiler-opt 0\|1\|2\|3`, isolated optimization-specific compiler cache, optimized Hello World checkpoint | Final coherent-head platform CI |
| Owned Word values | NonCopy locals, parameters, returns, replacements and temporary cleanup; borrowed observers, comparisons, concatenation and display; generated native ownership audits and sanitizer controls | Final coherent-head platform CI |
| Sized Unicode and interpolation | Embedded NUL, character indexing/slicing, lower-case runtime and HIR interpolation plans with restoration/invalidation coverage | Generated bounds driver passes independent source/pure review; actual generated matrix remains pending |
| Literal/general `say` | Updated fixture passes its 27 static byte cases, seven owned/general positives, seven typed diagnostics, ten forgeries and snapshot roundtrip | Final coherent-head platform CI |
| `say_err` and hosted runtime portability | Generated owned-message lane and exact raw output tests; source fixes for finite Unicode fixture construction, a known Darwin linker warning and Windows CRT declaration warning | Fresh Linux/macOS/Windows CI on the corrected head |
| Process arguments and typed OS results | Existing C entry argument setup; isolated closed `maybe<int>`/`result<word,word>` and typed `process::arg`, `process::args_count`, `fs::read` vertical slice | Closed Sum successor passes independent source/pure review and all 76 compiler cases; generated native gate, typed OS gate and integration remain pending |
| Filesystem bridge | Linux plain and ASan/UBSan O0/O2/O3 bridge proof, exact owned Ok/Err slots, Unicode/NUL/nonregular-file controls | Typed source integration and macOS/Windows native gates |
| Integer arithmetic | Checked native overflow and divide-by-zero contract; private C32 arithmetic lane passes hosted Linux/macOS/Windows | Fresh coherent-head CI; C-width native ABI admission remains fenced by B01 |
| Panic and bounds | Explicit `--panic=abort` path and checked integer/runtime boundaries; isolated private panic-context runtime has passed source review | Default compiler unwind and cleanup are not implemented; private context plain matrix passes six builds and 306 outcomes; context sanitizer proof and generated Word-bounds execution remain pending |

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
  illegal borrowed Word return. Two hosted runs preserve all three messages and
  help strings. Source-bound controls distinguish the declaration and operand
  spans and accept observers and typed reborrows; focused execution is pending.
- The drop fixture correctly blocks repeated consumption of an owned Word in
  a loop. Focused execution passes the exact single diagnostic, help and
  local-declaration span, alongside the preserved drop/DropIf ordering facts.
- Independent review blocked the first closed Sum checkpoint: native equality
  could emit an invalid aggregate `icmp`, downstream builtin identities omitted
  available binding eligibility, and inner payload aliases had inconsistent
  carrier/constructor/extraction treatment. Later review found ordered
  comparisons and a formal-parameter shadow guard gap. The bounded bootstrap
  diagnostic also exposed interpolation in two LLVM type strings. The reviewed
  successor fixes those findings and passes all 76 compiler cases. Generated
  native checks remain required before integration.
- Independent review blocked the new Word-bounds driver because it could
  report success after a retained image changed and had first-cause, cleanup,
  deadline and provenance gaps. The reviewed successor passes 49 independent
  fault controls and all 28 pure methods. Its generated native matrix remains
  required; pure success does not complete that proof.

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

The main release PR remains a draft. The previous `b5e300f` run had nine V4
failures and six green shipping jobs. Later fixes passed the complete Linux
and macOS runtime-helper jobs at `c399400`. The `6e108e7` wave exposed three
remaining failures: the lend diagnostic count, Windows test-source decoding,
and a Linux sanitizer capability exceeding its 64 MiB guard while reporting
an error. Reviewed fixes preserve diagnostics and all resource limits. The
sanitizer environment disables symbolization while retaining detection, leak
checks, stack printing, summaries and exit status. Fresh full platform CI and
current independent review are required before readiness. No merge or release
is performed automatically.
