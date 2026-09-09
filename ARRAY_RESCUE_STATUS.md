# Operation Array Rescue

State: scoped -> active. Base: `0cd5404fed18ab8f38b7229cf8eb6cbfa2895940`.
Integration: `fix/v3-array-rescue`, `C:/tmp/freak-v3-array-rescue`.

## Contract and exit gates

Repair shipping V3 list literals, indexing and indexed assignment, length,
iteration, checked bounds, numeric/bool storage, and supported owned word/shape
elements. Preserve language identity and existing compiler architecture. No V4,
Meiya/lifetime work, generics rewrite, or removal of benchmark safety checks.

Require executable LLVM/C parity, diagnostics and adversarial ownership checks,
one-million-element math workloads with recorded performance, V3 regression and
self-host verification, conformance documentation, immutable-head self-review
and independent review. Deliver scoped commits and a draft PR; readiness needs
current-head applicable CI and review disposition. No merge is authorized.

## Lane ledger

Four concurrent agent slots; requested roles run in dependency waves.

| Role | Responsibility | Current ownership |
| --- | --- | --- |
| Agent 0 / lead | failures, contract, integration, docs, harness coordination | integration worktree |
| Agent 1 | parser/checker/types and iteration AST | `fix/v3-array-types`, parser/checker/globals |
| Agent 2 | runtime storage/bounds/ownership | `fix/v3-array-runtime`, runtime C/header |
| Agent 3 | LLVM backend and iteration lowering | `fix/v3-array-llvm`, emit_llvm.fk |
| Agent 4 | C parity | lead initial exploration; worker pending |
| Agent 5 | iteration | pending semantic/storage contract |
| Agent 6 | benchmarks | pending executable baseline |
| Agent 7 | torture/negative tests | pending executable baseline |
| Agent 8 | independent V3 stability guard | pending immutable integrated head |

Write lanes receive isolated worktrees and explicit ownership before edits.
Integrate commits only. Lead owns root docs, auditor, workflows, and shared
test coordination. Resource budget: four agents, isolated workload processes,
serialized broad compiler gates, bounded execution with recorded session IDs.

## Baseline observations

Original main checkout contains unrelated untracked artifacts and is untouched.
The C index emitter currently emits `.data[index]` while array literals produce
integer runtime handles. Baseline reproduction and remaining findings pending.

Fresh seed -> current-source compiler reconstruction succeeded under Visual
Studio Developer PowerShell with Clang. The supplied sample fails in parsing
at `for each`; omitting its loop yields eight checker errors, including numeric
literal rejection, indexing, assignment target and length. Recorded launcher
session: 28805 (completed). Temporary artifacts: `C:/tmp/freak-array-evidence`.

Shared semantic contract: `List<T>`, `tc_is_list`, `tc_list_element`;
`STMT_FOREACH=18`, names=binder, exprs=receiver, bodies=normal block CSV.
Typed storage is separate from legacy compiler `array_*` word handles. Runtime
owns checked contiguous storage and retain/release operations. Existing word
literal callers of legacy `array_get/release` need an explicit compatibility
path and cleanup validation.

The baseline negative corpus deliberately rejects `[1]`; this status fixture
must become a meaningful incompatible-element negative when numeric arrays
land, rather than continuing to assert an obsolete implementation boundary.
