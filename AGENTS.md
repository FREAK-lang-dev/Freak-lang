# AGENTS.md - FREAK Language Project
## Continuity Guide For Codex And Parallel Agent Sessions

This file is the operating manual for AI sessions working on FREAK. It should let a new session move safely without rereading the entire repo. Keep it current when major architecture, workflow, release, or milestone decisions change.

FREAK is intentionally weird. The anime/VN identity is not decoration; it is part of the language design, diagnostics, docs, and tooling. Preserve that tone while keeping engineering decisions concrete.

---

## Current Ground Truth

- Project: **FREAK**, a compiled, statically typed, memory-safe systems language with `.fk` source files.
- Current public release: **v0.14.0 "Maverick"**.
- Version strings live in:
  - `src/cli/version.fk`
  - `src/compiler/v3/globals.fk`
- Authoritative language spec: `freak-full-bible.md`. If implementation and bible disagree, the bible wins unless the task is explicitly to amend the bible status.
- Conformance tracker: `freak-conformance-audit.md`.
- V4 architecture: `freakc-v4-00-unit-architecture.md`.
- V4 implementation home: `src/compiler/v4/`.
- V4 bootstrap status: the executable 00-Unit slice is complete. V4 is not yet a full V3 replacement.
- Current V4 feature strategy: dependency-strata vertical slices, not subsystem isolation.

Core repo commands:

```powershell
python -m freakc audit-conformance
python src/compiler/v4/check_v4.py --fast
python src/compiler/v4/check_v4.py --smoke "MIR loop desugaring"
python tests/suite/run_tests.py
```

Use targeted checks while iterating. Use broader checks before commit/PR when the touched surface justifies it.

---

## Non-Negotiables

1. **The bible wins.** Treat `freak-full-bible.md` as the language contract.
2. **Do not collapse V4 back into a monolith.** Keep `freak_driver`, `freak_editor`, `freak_snapshot`, and `freak_lsp` boundaries intact.
3. **Commit after significant work.** Do not let large uncommitted changes accumulate.
4. **Stage specific files.** Avoid `git add -A` unless the worktree is intentionally single-purpose and clean.
5. **Never push directly to `main`.** All changes go through topic branches and PRs.
6. **Do not revert user work.** The worktree may be dirty. Ignore unrelated changes unless they block the task.
7. **No AI attribution in commits.** No `Co-Authored-By`, no generated-by trailers.
8. **Use worktrees for parallel agents.** Two agents touching one checkout is how work disappears.
9. **Docs and conformance move with behavior.** When a V4 contract promotes from planned to partial/implemented, update bible status, audit doc, and `freakc/auditor.py` guards as needed.
10. **Leave the repo runnable.** Every milestone should have a clear verification story.

---

## Git, Branches, Commits, PRs

### Branch Policy

`main` is protected. Never push to it directly.

Preferred branch shapes:

- `feat/<slug>` for features
- `fix/<slug>` for bug fixes
- `docs/<slug>` for documentation-only changes
- `refactor/<slug>` for mechanical structure changes
- `release/v0.X.Y` for release prep
- Existing harness branches such as `claude/...` or `TeRiRi/...` may be continued when the session starts there

If you are on `main`, a deleted remote branch, or a mixed local checkout, create a fresh topic branch or worktree from `origin/main`.

### Commit Policy

Commit automatically after:

- a compiler bug fix
- a meaningful V4 slice
- a CI/release workflow change
- a runtime or stdlib feature
- a doc/audit milestone
- any risky edit that took more than about 15 minutes
- a successful end-to-end verification cycle

Commit format:

```text
Add V4 route constructor diagnostics

- Wire TY diagnostic facts through editor queries
- Add MIR smoke and audit-conformance guard
```

Keep the summary imperative and short. Use bullet details only when useful.

### PR Policy

Open PRs targeting `main` when the user asks, or when the active project convention says to produce PRs for completed work. Default to draft PRs unless the user explicitly asks for ready-for-review.

Before opening a PR:

1. Confirm the branch and staged files.
2. Run relevant checks.
3. Push the branch.
4. Include a PR body with summary, why it changed, validation, and remaining risk.

### Dirty Worktree Rule

This repo often has unrelated dirt. Before staging:

```powershell
git status --short --branch
git diff -- <intended-file>
git diff --cached --name-only
```

If unrelated files are dirty, leave them alone. If the intended branch is stale or unsafe, create a separate worktree from `origin/main`.

---

## Parallel Agent Workflows

Parallelism is a force multiplier only when lanes are isolated. Treat every multi-agent run as a small integration project with a lead agent, lane ownership, and explicit merge gates.

### Lead Agent Responsibilities

The lead agent owns:

- defining the goal and exit gate
- splitting work into independent lanes
- assigning file and subsystem ownership
- creating isolated worktrees/branches
- giving each agent a precise brief
- collecting lane summaries and validation evidence
- merging or cherry-picking lane work
- resolving conflicts
- running integration checks
- opening the final PR or one PR per lane

The lead does not assume agents coordinated with each other. The lead verifies the final tree.

### When To Use Parallel Agents

Use parallel agents when at least two lanes can make progress without editing the same files:

- V4 vertical feature plus separate docs/audit lane
- independent smoke fixture expansion
- CI failure investigation while another agent fixes local code
- editor/LSP work separate from TY/MIR work
- stdlib module work separate from compiler work
- release packaging work separate from V4 feature work
- PR review-comment triage across unrelated files

Do not use parallel agents when:

- the work centers on one parser function, one emitter function, or one fragile file
- the feature shape is not understood yet
- all lanes need `check_v4.py`, bible status, or audit docs at the same time
- the task is a small bug fix that one agent can finish faster than coordination overhead

### Mandatory Worktree Isolation

For two or more agents, each agent gets a separate git worktree and branch.

Example:

```powershell
git fetch origin main
git worktree add -b feat/v4-routes-ty C:\tmp\freak-v4-routes-ty origin/main
git worktree add -b feat/v4-routes-mir C:\tmp\freak-v4-routes-mir origin/main
git worktree add -b docs/v4-routes-audit C:\tmp\freak-v4-routes-audit origin/main
```

Rules:

- Do not run two agents in the same checkout.
- Do not share uncommitted changes between agents.
- Each agent commits on its own branch.
- The lead integrates from committed branches, not from loose patches.
- If a lane produces no useful changes, delete the worktree/branch instead of merging noise.

### Lane Ownership

Assign each lane an ownership boundary before agents start.

Good boundaries:

| Lane | Owns | Avoids |
|---|---|---|
| Lex/parse | `freak_lex`, `freak_parse`, syntax fixtures | TY/MIR semantics |
| HIR/resolve | `freak_hir`, `freak_resolve` | LLVM/codegen |
| TY | `freak_ty`, type diagnostics, TY smokes | MIR lowering unless agreed |
| MIR | `freak_mir`, MIR smokes | Borrowck policy unless agreed |
| Meiya | `freak_borrowck`, borrow smokes | New syntax design |
| Editor | `freak_editor`, editor query smokes | LSP transport framing |
| Snapshot | `freak_snapshot`, snapshot protocols | Driver ownership |
| LSP | `freak_lsp`, transport endpoints | Analysis storage |
| Codegen | `freak_codegen_llvm`, LLVM smokes | TY semantics except ABI handoff |
| Docs/audit | bible, audit doc, `freakc/auditor.py` | core implementation unless acting as integrator |

Integration-owned files:

- `AGENTS.md`
- `README.md`
- `freak-full-bible.md`
- `freak-conformance-audit.md`
- `freakc/auditor.py`
- `src/compiler/v4/check_v4.py`
- CI workflow files

Agents may edit these only if their lane brief explicitly grants ownership. Otherwise the lead does the final doc/audit/check harness pass.

### Agent Brief Template

Give each agent a brief like this:

```text
Goal: Implement V4 variant constructor TY diagnostics.
Branch/worktree: feat/v4-variant-ty at C:\tmp\freak-v4-variant-ty.
Owned files: src/compiler/v4/crates/freak_ty/**, TY smoke fixtures only.
Do not edit: freak_mir, freak_borrowck, bible/audit docs, check_v4.py.
Required checks:
- python src/compiler/v4/check_v4.py --smoke "variant constructor typing"
Output:
- commit hash
- files changed
- checks run
- known risks/blockers
```

If the brief cannot name owned files and checks, the task is not ready for parallel execution.

### Per-Agent Workflow

Every agent should:

1. Confirm branch and worktree with `git status --short --branch`.
2. Read the local docs for its lane.
3. Implement only its assigned slice.
4. Add focused tests/smokes.
5. Run required checks.
6. Commit scoped files.
7. Report commit hash, validation, and unresolved risks.

Agents must not:

- broaden scope without reporting it
- silently stage unrelated files
- resolve merge conflicts by guessing
- mark work complete with failing required checks
- rewrite shared architecture rules to fit their local patch

### Integration Workflow

The lead integrates lanes in this order:

1. Fetch or inspect each lane branch.
2. Review `git diff origin/main...lane`.
3. Reject noisy or out-of-scope changes before merge.
4. Merge/cherry-pick one lane at a time into an integration branch.
5. Resolve conflicts intentionally.
6. Run targeted checks after each merge if the lane changed compiler behavior.
7. Run broader checks after all lanes are integrated.
8. Do the docs/audit/check harness pass last.

For V4, prefer an integration branch when lanes together form one user-visible feature. Prefer separate PRs when lanes are independently useful and CI-stable.

### Parallel Sprint Patterns

Use these patterns instead of random lane splits.

#### Pattern A: V4 Semantic Core Feature

Goal: land a source form through the compiler without reopening every layer later.

- Agent 1: lex/parse/HIR/resolve representation
- Agent 2: TY rules and diagnostics
- Agent 3: MIR lowering and runtime-capable smokes
- Agent 4: editor/snapshot/LSP visibility plus docs/audit guards

Exit gate: stable HIR/TY/MIR representation, editor/query visibility, focused diagnostics, and conformance docs updated.

#### Pattern B: Borrow Checker Gate

Use only after the relevant value and pattern shapes are stable.

- Agent 1: loan/lifetime model in `freak_borrowck`
- Agent 2: MIR place/drop facts needed by Meiya
- Agent 3: Shared/Weak or trust-me boundary diagnostics
- Agent 4: borrowck smokes, snapshots, docs/audit

Exit gate: coherent Meiya behavior across all implemented forms touched by the slice.

#### Pattern C: FFI/System Boundary

- Agent 1: TY ABI/layout validation
- Agent 2: MIR ABI carriage and call representation
- Agent 3: LLVM lowering and runtime smoke
- Agent 4: `std::ffi` docs, LSP facts, audit checks

Exit gate: ABI/layout contract is visible in TY, MIR, diagnostics, LLVM lowering, and tooling.

#### Pattern D: Tooling/00-Unit

- Agent 1: query invalidation/reporting
- Agent 2: snapshot format/restore/diff/health
- Agent 3: LSP transport endpoint
- Agent 4: smoke runner and docs

Exit gate: `didChange`, snapshot diff, snapshot health, and LSP output agree on deterministic facts.

#### Pattern E: Release/CI

- Agent 1: workflow fix or matrix expansion
- Agent 2: local reproduction and check speed
- Agent 3: packaging/install scripts
- Agent 4: release docs and version audit

Exit gate: local check evidence plus green GitHub Actions on Linux, macOS, and Windows.

---

## V4 Roadmap Rules

Do not roadmap by crate. Roadmap by dependency gate and land vertical slices.

Current order:

1. **Semantic Core First**
   - variants/routes and constructors
   - exhaustive destructuring in `when`
   - aliases and ownership-relevant type forms
   - tuple/fixed-array place and value modeling
   - enough generics/bounds to stabilize body typing

2. **Borrow Checker As Its Own Gate**
   - `lend` / `lend mut`
   - explicit and inferred lifetimes
   - cross-block loan ranges
   - drop tracking and partial moves
   - closure/method captures
   - `Shared<T>` / `Weak<T>`
   - `trust me` and raw-pointer boundary diagnostics

3. **FFI And Systems Boundary**
   - `extern [C]` and ABI matrix
   - `@layout(C)` and repr rules
   - raw pointer legality
   - `std::ffi` / `std::mem`
   - LLVM ABI/layout carriage

4. **Concurrency After Ownership**
   - thread/channel baseline
   - `xm3`
   - `sortie`
   - `formation`
   - `briefing room`
   - `wingman`

5. **Advanced And Anime Surface**
   - `mood`, `prob`, `power`, `causality`
   - annotation enforcement
   - `foreshadow` / `payoff` strictness
   - `eventually` / `isekai` strict semantics
   - character-routed compiler error voices

6. **Conformance Sweep**
   - update `freak-full-bible.md`
   - update `freak-conformance-audit.md`
   - extend `audit-conformance`
   - close V4 test gaps

Anti-rewrite rule: do not try to finish Meiya while semantic shapes are still moving.

---

## V4 Crate Boundaries

V4 crate order:

```text
freak_span
-> freak_diag
-> freak_arena
-> freak_intern
-> freak_session
-> freak_lex
-> freak_parse
-> freak_hir
-> freak_resolve
-> freak_ty
-> freak_mir
-> freak_borrowck
-> freak_codegen_llvm
-> freak_query
-> freak_driver
-> freak_editor
-> freak_snapshot
-> freak_lsp
```

Boundary rules:

- `freak_lex` owns tokens and lexical recovery.
- `freak_parse` owns resilient parsing and syntax trees.
- `freak_hir` owns desugared high-level forms.
- `freak_resolve` owns names, scopes, and definition identity.
- `freak_ty` owns type inference, type contracts, and type diagnostics.
- `freak_mir` owns CFG lowering, places, drops, and MIR diagnostics.
- `freak_borrowck` owns Meiya loan, move, lifetime, and ownership analysis.
- `freak_codegen_llvm` owns LLVM lowering.
- `freak_query` owns memoized query storage and invalidation graph mechanics.
- `freak_driver` orchestrates services. It must not own editor fact arrays or snapshot serializers.
- `freak_editor` owns semantic-at, hover, definition, document-symbol, and completion arenas/query APIs.
- `freak_snapshot` owns snapshot formats, manifests, diffs, health reports, restore coordination, and invalidation contract reports.
- `freak_lsp` owns transport-facing wrappers only.

When adding a V4 endpoint:

1. Put the real analysis in the owning crate.
2. Put stable wire formats and validators in `freak_snapshot`.
3. Let `freak_driver` orchestrate, not store new ownership.
4. Let `freak_lsp` wrap transport.
5. Add smoke coverage.
6. Run `python src/compiler/v4/check_v4.py --fast` when practical.

---

## Verification Strategy

Choose the smallest check that proves the edit, then broaden before PR.

### V4 Checks

```powershell
python src/compiler/v4/check_v4.py --smoke "name"
python src/compiler/v4/check_v4.py --smoke extern --smoke module
python src/compiler/v4/check_v4.py --smoke-shard 1/6
python src/compiler/v4/check_v4.py --fast
python src/compiler/v4/check_v4.py
```

Notes:

- `--fast` is the broad local gate for V4 work, but it can be slow on Windows.
- Use targeted smokes during inner-loop work.
- If a long check times out, stop leftover Python/clang processes before continuing.
- CI is the final cross-platform proof for V4 fast/runtime lanes.

### Baseline Conformance

Run this when touching compiler, runtime, CLI, stdlib, bible/audit status, or V4 promoted contracts:

```powershell
python -m freakc audit-conformance
```

### Legacy Suite

Run this for V1/V3/runtime behavior:

```powershell
python tests/suite/run_tests.py
```

### Diff Hygiene

```powershell
git diff --check
```

Line-ending warnings are common on Windows. Treat whitespace errors as blockers; treat CRLF normalization warnings as informational unless they indicate unexpected churn.

---

## Project Map

```text
Freak-lang/
  freakc/                         Python bootstrap compiler and audit commands
    __main__.py
    lexer.py
    parser.py
    checker.py
    emitter.py
    auditor.py
    runtime/
      freak_runtime.h
      freak_runtime.c
      freak_llvm_runtime.c
  src/
    cli/                          Native FREAK CLI
    compiler/
      v3/                         Current self-hosting compiler
      v4/                         00-Unit modular/query compiler
        crates/
        tests/
        check_v4.py
        README.md
  std/                            Standard library modules
  tests/                          Language tests and fixtures
  packaging/                      Homebrew/Scoop/Winget/release assets
  .github/workflows/              CI and release workflows
  freak-full-bible.md             Authoritative spec
  freak-conformance-audit.md      Contract status and divergence tracker
  freakc-v4-00-unit-architecture.md
  AGENTS.md
```

High-value docs:

- `src/compiler/v4/README.md` - current V4 boundary and tooling protocol rules
- `freakc-v4-00-unit-architecture.md` - V4 manifesto and architecture
- `freak-full-bible.md` - language bible
- `freak-conformance-audit.md` - implemented vs partial vs V4 contracts
- `freak-distribution-llvm-plan.md` - LLVM/distribution history
- `freak-ui-plan.md` - COCKPIT plan

---

## Compiler Architecture Snapshot

### Current Shipping Path

```text
.fk source
-> V3 self-hosting compiler
-> LLVM IR
-> clang/lld
-> native binary
```

The C backend remains a portability target.

### V4 Target Path

```text
source
-> lex
-> parse with ErrorNode/IncompleteNode recovery
-> HIR desugaring
-> resolve
-> TY
-> MIR CFG/place/drop lowering
-> Meiya borrowck
-> LLVM/codegen
-> query-backed driver/LSP/snapshots
```

The V4 goal is not "rewrite the compiler again." The goal is to make every compiler fact queryable, memoized, invalidatable, and tool-visible.

---

## Language Quick Reference

Core vocabulary:

| FREAK | Meaning |
|---|---|
| `pilot` | variable binding |
| `fixed pilot` | immutable binding |
| `task` | function |
| `give back` | return |
| `say` | print |
| `when` | match/switch |
| `shape` | struct-like type |
| `variant` | V4 sum type surface |
| `doctrine` | trait/interface |
| `impl` | implementation block |
| `trust me` | unsafe/honor boundary |
| `training arc` | bounded loop |
| `for each` | iterator loop |
| `repeat` | counted or conditional loop |
| `foreshadow` / `payoff` | narrative debt |
| `deus_ex_machina` | dramatic escape hatch |
| `isekai` | isolated fresh scope |
| `eventually` | deferred cleanup surface |
| `launch` | public/exported item |

Important type surfaces:

```text
int, uint, num, tiny, bool, word, char, void
maybe<T>, result<T,E>
List<T>, Map<K,V>, Set<T>, Lineup<T>
[T; N], (A, B, C)
*T, *mut T
lend T, lend mut T
Shared<T>, Weak<T>
mood, prob[lo..hi], power<N>, causality<T>
extern [ABI] task(...) -> T
```

Many advanced forms are V4 partial or planned. Check bible status before promising behavior.

---

## Standard Library Snapshot

Implemented or substantially present:

- `std::math`
- `std::math3d`
- `std::string`
- `std::convert`
- `std::algorithm`
- `std::json`
- `std::http`
- `std::zip`
- `std::fs`
- `std::process`
- `std::time`
- `std::bytes`
- `std::net`
- `std::version`
- `std::ui` through COCKPIT MA-MF, with MG polish still pending

Planned or V4-expanding:

- `std::thread`
- `std::anime`
- `std::narrative`
- `std::test`
- `std::ffi`
- `std::os`
- `std::panic`
- `std::regex`
- `std::crypto`

---

## CLI Quick Reference

```powershell
build\freak.exe build file.fk
build\freak.exe build file.fk --c
build\freak.exe build file.fk --opt=3
build\freak.exe run file.fk
build\freak.exe check file.fk
build\freak.exe transpile file.fk
build\freak.exe --version
build\freak.exe help
build\freak.exe test
build\freak.exe audit-conformance

python -m freakc build file.fk
python -m freakc run file.fk
python -m freakc audit-conformance
```

Hangar:

```powershell
build\freak.exe hangar init
build\freak.exe hangar add pkg repo
build\freak.exe hangar install
build\freak.exe hangar version patch
```

---

## Release And Packaging Notes

Before tagging a release:

1. Update both hardcoded version files.
2. Run relevant local checks.
3. Confirm install scripts and packaging manifests.
4. Tag only after the branch intended for release is merged.

Release assets are built by GitHub Actions for:

- Linux x64/arm64
- macOS x64/arm64
- Windows x64
- `freak` and `hangar`
- checksum files

Packaging lives under `packaging/`.

---

## Common Failure Modes

- **Unrelated dirty files get committed.** Fix: stage explicit paths only.
- **Parallel agents overwrite each other.** Fix: one worktree per agent.
- **V4 work drifts into V3.** Fix: keep experimental compiler architecture under `src/compiler/v4/`.
- **Driver becomes a monolith again.** Fix: storage/query ownership belongs to editor/snapshot/query crates, not `freak_driver`.
- **A V4 feature lands without audit docs.** Fix: update bible, audit doc, and `audit-conformance` guards in the same slice.
- **Local V4 checks leave Python/clang running after timeout.** Fix: inspect and stop leftover processes before continuing.
- **GitHub PR looks green but is blocked.** Fix: check live review threads, merge state, and CI status.
- **Windows shell syntax causes command failures.** Fix: use PowerShell syntax, not bash `&&`.

---

## Updating This File

Update `AGENTS.md` when:

- a milestone completes
- branch/PR policy changes
- the V4 phase changes
- a new parallel workflow pattern becomes standard
- a repeated failure needs to become a rule
- release/version process changes

Keep this file operational. It is not a marketing doc; it is the cockpit checklist for future sessions.

---

*"It was always going to end this way."*
