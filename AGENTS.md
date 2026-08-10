# AGENTS.md - FREAK Language Project

## Purpose

This is the operating contract for AI sessions working on FREAK. It records
repository rules, delivery gates, and current architecture boundaries. It is
not the language specification, roadmap history, CLI reference, or changelog.
Use the canonical documents listed below for those facts.

FREAK is a compiled, statically typed, memory-safe systems language. Sources use
the `.fk` extension and anime/visual-novel vocabulary. That identity is
load-bearing: preserve it in syntax, diagnostics, documentation, and tooling
while keeping engineering decisions precise.

## Ground Truth

| Concern | Authority |
|---|---|
| Normative language semantics | `freak-full-bible.md` |
| Tracked implementation gaps | `freak-conformance-audit.md`, verified against code and executable checks |
| V4 architecture | `freakc-v4-00-unit-architecture.md` |
| V4 crate boundaries and protocols | `src/compiler/v4/README.md` |
| Public usage and installation | `README.md` |
| Distribution and LLVM history | `freak-distribution-llvm-plan.md` |
| Current COCKPIT implementation | `packages/cockpit/` |
| COCKPIT design history | `freak-ui-plan.md` |

Current facts:

- Public release: **v0.14.0 "Maverick"**.
- Shipping compiler: self-hosted V3, emitting LLVM IR and linking natively. The
  C backend remains a portability target.
- V4 implementation: `src/compiler/v4/`.
- V4 00-Unit bootstrap is complete, but V4 is not a full V3 replacement.
- Current primary V4 gate: **Meiya borrow/lifetime analysis**. Named/elided
  multi-source returned loans, body-derived source discovery through locals,
  aggregate moves, statically resolved call results, acyclic joins, and loop
  fixed points have landed; general lexical region inference, general
  outlives relations, `'static`, and non-ordinary aggregate task boundaries
  remain constrained.
- `VERSION` is the release-version authority. Change it only through
  `python -u tools/release_version.py set <major.minor.patch>`; that one command
  synchronizes the compiled `FREAK_VERSION`, CLI/compiler display aliases,
  package metadata, WinGet release directory, and this public-release fact.
  Never hand-edit those mirrors for a release bump. Run
  `python -u tools/release_version.py check` before committing; tagged release
  workflows additionally require the exact `v<major.minor.patch>` tag before
  any platform asset is built.

If implementation semantics and the bible disagree, the bible wins unless the
task explicitly amends or clarifies the language. If an implementation-status
claim disagrees with executable evidence, treat that as a blocking documentation
defect: verify the behavior and update the status documents rather than
regressing working code to match a stale matrix. Never silently redefine the
language to match an implementation shortcut.

## Non-Negotiables

1. Keep V4 modular. Do not move editor facts, snapshot formats, or transport
   state back into `freak_driver`.
2. Land language features as vertical slices, not isolated crate promises.
3. Update conformance documentation with semantic behavior.
4. Never push directly to `main`; use a topic branch and pull request.
5. Do not revert, stage, or commit unrelated user changes.
6. Stage explicit paths. Avoid `git add -A` in mixed worktrees.
7. Commit after meaningful milestones and successful verification.
8. Do not add AI attribution or `Co-Authored-By` trailers.
9. Every PR gets self-review; every non-typo PR also gets an independent
   reviewer.
10. Passing tests do not override an unresolved correctness finding.
11. Do not weaken tests, diagnostics, or contracts merely to make CI green.
12. Leave the branch clean, documented, and reproducibly verifiable.

## Starting A Task

1. Inspect `git status --short --branch`, current worktrees, and recent history.
2. Fetch `origin` before creating a new branch or worktree when network and
   repository mutation are allowed.
3. Read the relevant authority documents and nearby implementation before
   choosing a design.
4. Identify unrelated dirty files and exclude them from the work.
5. Define the behavioral exit gate and the smallest checks that prove it.
6. Decide whether the task needs one lane, parallel read-only exploration, or
   isolated write lanes. Unclear work may use parallel explorers, but writers
   wait until ownership and contracts are concrete.

When the user explicitly asks for a formal goal, create one concrete goal with
an end state, non-goals, a pinned base commit, verification requirements,
delivery expectations, lane dependencies, and a resource budget. Do not infer
a formal goal from ordinary work. Track substantial goals through `scoped ->
active -> integrating -> verifying -> complete`; `blocked` and `cancelled` are
terminal alternatives. Mark a goal complete only after every stated gate is
satisfied; difficulty or slow CI is not a blocker by itself.

These are planning labels, not replacements for the goal tool's status
contract. User/system controls pause, resume, and cancellation; use `blocked`
only when the tool's repeated-blocker threshold is met.

Explicit read-only or no-network instructions take precedence: do not fetch,
prune, create branches/worktrees, touch the index, commit, push, or open a PR in
that mode.

### Dirty Worktrees

This repository often has unrelated local work. Never clean it speculatively.

```powershell
git status --short --branch
git diff -- <intended-path>
git diff --cached --name-only
```

If the checkout is mixed, stale, on `main`, or attached to a deleted remote
branch, create a clean worktree from the recorded intended `BASE_SHA`. Use
`origin/main` only for confirmed standalone work. Keep the original checkout
untouched.

## Git Delivery

### Branches And Worktrees

Preferred branches:

- `feat/<slug>` for features
- `fix/<slug>` for defects
- `docs/<slug>` for documentation
- `refactor/<slug>` for structural changes
- `chore/<slug>` for tooling and maintenance
- `release/v0.X.Y` for release preparation
- Existing harness prefixes such as `TeRiRi/...` or `claude/...` may be kept
  when work already belongs there

Create risky, long-running, or parallel write work in an isolated worktree.
Pin the intended baseline first; do not assume a moving `origin/main` is the
right base for work that depends on a topic branch:

```powershell
git fetch origin
$BASE_SHA = git rev-parse origin/main
git worktree add -b feat/v4-example C:\tmp\freak-v4-example $BASE_SHA
```

Before recursive removal or relocation, resolve and verify the exact absolute
path. Never broadly delete `C:\tmp`, the repository root, or a computed path
that has not been checked.

### Commits

Commit automatically after a compiler/runtime bug fix, semantic slice,
workflow change, conformance milestone, risky refactor, or verified end-to-end
checkpoint. Keep commits scoped and independently understandable.

Use an imperative summary:

```text
Add V4 returned-loan outlives diagnostics

- Carry relation facts through MIR queries
- Add Meiya and editor invalidation smokes
```

Do not accumulate unrelated subsystems into one commit solely to reduce commit
count. Do not rewrite or squash user commits unless explicitly asked.

### Pull Requests

Open a PR when the user asks, the active goal requires it, or the established
task convention says completed branches get PRs. Target `main`. Default to a
draft while review or CI is incomplete.

The PR body must state:

- what behavior changed
- why the design belongs at its chosen ownership boundary
- local validation performed
- CI or platform validation still pending
- known conservative boundaries or follow-up work

Agents do not merge unless the user explicitly requests it. Before updating or
declaring a PR ready, fetch its live merge state, checks, reviews, issue
comments, and inline review threads.

All readiness evidence is tied to the current PR head SHA. A new commit
invalidates earlier self-review, CI, and independent-review evidence until those
gates run on the new head or the reviewer explicitly verifies its delta.

## Goal And Agent Orchestration

Parallelism is useful only when work can be partitioned. Use as many agents as
there are independent lanes that materially shorten the critical path, not as
an arbitrary measure of effort.

### Roles

| Role | Responsibility | Writes? |
|---|---|---|
| Lead | contract, decomposition, integration, final checks, delivery | yes |
| Explorer | bounded codebase or design question | no |
| Worker | one owned implementation lane | yes |
| Reviewer | adversarial diff review and test-gap analysis | no |

Conformance, CI, release, security, and platform work are specializations of
these roles, not separate permission models. An agent has one role at a time.

The author of a patch cannot be its independent reviewer. Close agents when
their result has been integrated or recorded so concurrency remains available.

### Isolation And Ownership

- Read-only explorers and reviewers may inspect the same immutable commit or
  diff and do not need branches, worktrees, or commits. If a review tool must
  generate artifacts, write them outside the repository.
- Explorers and reviewers do not fetch, switch branches, mutate refs/worktrees,
  touch files or the index, commit, push, or resolve conflicts. Explicitly
  reassign the agent as a worker before granting writes; that agent can no
  longer independently review the resulting patch.
- Pin one `BASE_SHA` for a multi-agent goal and record any prerequisite commit
  used by a dependent lane.
- Give a cohesive multi-worker goal a dedicated integration branch/worktree.
- Every write-capable lane gets its own branch and worktree from the pinned
  base or a recorded prerequisite commit.
- One write-capable owner per file at a time.
- Ownership transfer requires a committed handoff and explicit reassignment in
  the lane ledger.
- Agents integrate committed work, not loose patches or copied worktrees.
- The lead resolves conflicts and verifies the integrated tree.
- A lane that produces no useful change should not create merge noise.

Partition by independently testable feature responsibility. Prefer one owner
for an end-to-end vertical slice when its compiler layers are tightly coupled.
Crate-shaped lanes are acceptable only after the shared semantic contract is
stable and their write sets are genuinely disjoint; do not turn the roadmap
into a sequence of crate completions.

Integration-owned files normally stay with the lead: `AGENTS.md`, root
`README.md`, bible/audit documents, `freakc/auditor.py`,
`src/compiler/v4/check_v4.py`, and workflow files. If a worker owns one, record
the exception in the lane ledger. Ownership returns to the lead only after the
worker's committed handoff is accepted.

### Agent Brief

Every delegated task must name:

```text
Goal and observable exit condition
Pinned base commit and branch/worktree
Owned files or responsibility
Files and behaviors explicitly out of scope
Required focused checks
Expected output: commit hash or findings, files, checks, risks
```

Workers must be told other work may exist and must not revert it. If ownership
or checks cannot be stated, the work is not ready for a write agent.

### Integration Order

1. Inspect each lane diff, commit evidence, and focused checks.
2. Reject unrelated or generated churn.
3. Integrate stable contracts before their consumers, one committed lane at a
   time.
4. Re-run affected checks after each risky integration or conflict resolution.
5. Apply integration-owned docs, audit guards, and harness registration.
6. Review the final integrated diff. This review is mandatory when two or more
   workers contributed, even if every lane was reviewed separately.
7. Resolve findings, then run the broad gate once on the integrated branch.
8. Push and, when required, open or update the PR as a draft.
9. Complete remote CI and review disposition during verification.

Run at most one `check_v4.py` process at a time on one host, including focused
smokes and shards: every invocation initializes broad compiler state. Workers
prepare focused commands; the lead coordinates their serialized execution and
owns broad integration checks. This protects iteration time, RAM, pagefile, and
temporary storage without reducing coverage.

Only the lead rebases, resolves cross-lane conflicts, removes worktrees, deletes
branches, prunes repository state, or performs repository-wide cleanup. Before
cleanup, verify the exact path, a clean worktree, and that no unique commit
would be lost. Stop child processes before replacing a timed-out lane or check.

## Review Policy

Review is a correctness gate, not a ceremonial summary.

### Required Reviews

Every PR receives a lead self-review of the immutable
`git diff $BASE_SHA...$HEAD_SHA` before readiness.
Every PR except a literal typo-only change receives an independent review. The
reviewer must not have authored or fixed any commit under review; if they edit
the patch, assign a different reviewer. Record the reviewed SHA, checks, verdict,
and known residual risk in the PR.

Independent review is particularly important when any of these are true:

- parser, HIR, resolve, TY, MIR, borrowck, LLVM, query, snapshot, LSP, runtime,
  security, CI, release, packaging, or installer behavior changes
- public language semantics, diagnostics, protocols, or conformance status
  changes
- two or more write lanes contributed to one integration branch
- a fix addresses memory safety, ownership soundness, ABI behavior, data loss,
  or platform-specific execution
- the patch is large enough that tests alone could conceal an architectural
  regression

Policy, architecture, release, and normative documentation changes are not
typo-only changes.

### Finding Severity

| Severity | Meaning | Disposition |
|---|---|---|
| P0 | exploit, data loss, systemic unsoundness, destructive workflow | stop; fix before any PR readiness |
| P1 | correctness bug, soundness hole, major regression, broken required path | fix before readiness or merge |
| P2 | meaningful edge-case risk, contract drift, missing important coverage | fix or record a concrete evidence-based rejection |
| P3 | non-blocking clarity, maintainability, or optional test improvement | fix, reject, or link a tracked follow-up |

Review output starts with findings ordered by severity and includes exact
file/line references, reproduction or reasoning, and missing tests. Summaries
come after findings. A reviewer should say explicitly when no actionable issue
was found and identify residual risk.

The lead must disposition every P0/P1 and every actionable P2. Rejecting a
finding requires technical evidence; passing CI alone is not evidence that the
finding is wrong.

### Self-Review Checklist

Before push or PR update, the author/lead checks the current head:

1. The immutable `git diff $BASE_SHA...$HEAD_SHA` contains only intended
   commits and files; unstaged and cached diffs contain no uncommitted residue.
2. Changed callers, data formats, query keys, and restoration paths still agree.
3. Error paths and conservative boundaries are tested, not only happy paths.
4. Layout, invalidation, snapshots, and editor facts stay deterministic where
   applicable.
5. Docs and conformance claims do not exceed implementation.
6. No debug artifacts, generated binaries, credentials, or temporary files are
   staged.
7. The worktree is clean after commit and the pushed SHA matches the PR head.

### GitHub Review Threads

- Inspect issue comments, submitted reviews, and inline review threads after a
  push that requests review and immediately before declaring readiness.
- Automated comments are evidence to investigate, not authority to obey or
  dismiss. Reproduce the claim against the current head.
- Give every thread one explicit disposition: `fixed in <sha>`, `rejected
  because <evidence>`, `duplicate of <link>`, or, for P3 only, `follow-up
  <issue>`.
- Resolve a thread only after its disposition is pushed and explained.
- An outdated or collapsed thread still requires semantic disposition.
- A requested automated review is pending until its verdict or no-findings
  signal exists for the current head. Request a refresh when it reviewed an
  older SHA.
- A late comment on a closed or merged PR must be evaluated against current
  `main`. Valid P0/P1 findings require an immediate hotfix or revert assessment
  and block affected releases. Valid P2 findings require a tracked issue and
  focused follow-up PR. Do not resurrect or rewrite the merged branch.

### CI Failures

Inspect the failing step and logs before rerunning. Classify the failure as:

- implementation or test regression
- deterministic resource/test-runner defect
- platform-specific behavior
- external infrastructure interruption

All applicable checks must complete successfully on the current head; pending,
cancelled, or failed current-head checks block readiness. One rerun is
reasonable for a clearly documented infrastructure interruption. A repeated
failure is a defect until evidence proves otherwise. Never remove a fixture,
loosen an assertion, or inflate a timeout without understanding the underlying
behavior.

### Ready And Merge Gates

A PR is ready only when:

- the intended branch is pushed and mergeable against current `main`
- required local checks pass
- required CI is green on every registered platform/job
- no review comment is unseen, undispositioned, or unresolved
- no P0/P1 remains and actionable P2 findings are resolved or rejected with
  evidence
- conformance and public docs match the actual behavior
- the PR describes remaining conservative boundaries

Record the final evidence in a PR comment. Any subsequent commit invalidates
the record:

```text
Merge gate @ <head-sha>
Self-review: complete
Independent review: <reviewer>, <reviewed-sha>, <verdict>
CI: all applicable current-head checks green
Unresolved threads: 0
Deferred findings: <issue links or none>
```

Repository rulesets should enforce current-head required checks and review
thread resolution where the host supports them. These gates still apply when a
server-side setting lags behind policy.

## V4 Engineering Rules

### Dependency Order

Work by dependency gate, not bible chapter or crate completion:

1. Semantic shapes and type forms
2. Meiya ownership, loans, lifetimes, drops, captures, and shared ownership
3. FFI, layout, ABI, raw-pointer boundaries, and native OS surfaces
4. Concurrency after ownership rules are stable
5. Advanced/anime semantic layers
6. Conformance sweep and production backend depth

The current primary gate is step 2. Do not start concurrency semantics that
depend on unsettled ownership contracts.

### Vertical Slice Contract

A V4 language addition is complete only when every affected layer agrees:

```text
source/parse -> HIR/resolve -> TY -> MIR -> Meiya/codegen
             -> query/editor/snapshot/LSP -> smokes -> conformance docs
```

Not every slice changes every crate, but every crate that owns an affected fact
must be considered. Minimum coverage is one happy path and one targeted
diagnostic; add editor/invalidation/snapshot coverage when tooling facts change.

### Crate Ownership

V4 crate order is defined in `src/compiler/v4/check_v4.py`. Core boundaries:

| Crate | Owns |
|---|---|
| `freak_lex` | tokens and lexical recovery |
| `freak_parse` | resilient syntax trees and recovery nodes |
| `freak_hir` | desugared high-level forms |
| `freak_resolve` | names, scopes, and definition identity |
| `freak_ty` | inference, type contracts, and type diagnostics |
| `freak_mir` | CFG lowering, places, drops, and MIR diagnostics |
| `freak_borrowck` | Meiya loans, moves, lifetimes, and ownership analysis |
| `freak_codegen_llvm` | LLVM lowering and backend contracts |
| `freak_query` | memoized storage and invalidation graph mechanics |
| `freak_driver` | orchestration, not editor/snapshot ownership |
| `freak_editor` | semantic, hover, definition, symbol, completion facts |
| `freak_snapshot` | formats, manifests, diffs, health, restore coordination |
| `freak_lsp` | transport-facing wrappers only |

When adding a tooling endpoint, put analysis in its owning crate, stable
serialization/validation in `freak_snapshot`, orchestration in `freak_driver`,
and transport framing in `freak_lsp`.

### Conformance Updates

When behavior promotes from planned to partial/implemented:

1. Update the relevant bible status and normative note.
2. Update `freak-conformance-audit.md` without overstating coverage.
3. Add or extend `freakc/auditor.py` when the contract should be guarded.
4. Register focused executable fixtures in `check_v4.py`.
5. Run `python -u -m freakc audit-conformance`.

## Verification And Resource Safety

Choose the smallest check that proves the edit, then broaden at integration.

```powershell
# Focused V4 executable smoke
python -u src/compiler/v4/check_v4.py --smoke "name"

# Deterministic runtime shard
python -u src/compiler/v4/check_v4.py --smoke-shard 1/6

# Broad parse/transpile gate
python -u src/compiler/v4/check_v4.py --fast

# Full local V4 runtime gate when justified
python -u src/compiler/v4/check_v4.py

# Baseline language/conformance contract
python -u -m freakc audit-conformance

# Shipping compiler/runtime suite
python -u tests/suite/run_tests.py

# Python syntax and diff hygiene
python -u -m py_compile <changed-python-files>
git diff --check
```

Rules:

- Use targeted smokes during implementation. Let CI provide the final full
  cross-platform matrix when local duplication adds no evidence.
- Run only one `check_v4.py` process at a time on one host. Run unfiltered
  `--fast` or full gates only with confirmed resource headroom or in CI.
- Run Python checks unbuffered (`-u`) so long phases remain observable.
- If RAM, pagefile, disk, or runtime grows unexpectedly, stop and isolate the
  exact fixture/process. Do not wait for host OOM.
- Before a long-running local check, record its exact command and launcher PID
  or tool session ID. Cancel through that session's termination API or an
  OS-specific PID-tree operation.
- Generated compiler smokes should avoid several complete compiler pipelines in
  one executable. Split independent contracts across process-isolated fixtures
  while preserving assertions.
- A new public tooling endpoint requires the full V4 gate before readiness.
- A timeout or OOM is an inconclusive verification failure until classified.
  Record the exact phase and fixture before retrying; do not reduce coverage.
- On interruption, terminate only the recorded launcher's process tree. Never
  kill Python, Clang, or test processes globally by process name.
- Treat CRLF normalization warnings as informational unless they accompany
  unintended content churn; whitespace errors are blockers.

## Repository Pointers

```text
freakc/                         Python bootstrap compiler, auditor, C runtimes
src/cli/                        Native CLI and Hangar dispatch
src/compiler/v3/                Shipping self-hosted compiler
src/compiler/v4/                Modular 00-Unit compiler and executable smokes
std/                            Standard library modules
tests/                          Shipping language/runtime tests
packaging/                      Homebrew, Scoop, Winget, release assets
.github/workflows/              CI, V4 CI, and release workflows
```

For syntax, types, annotations, stdlib inventory, and error voices, read the
bible and audit rather than copying snapshots here. For commands, installation,
and package-manager usage, read `README.md` and native CLI help. For release
assets and platform matrices, inspect the workflows and packaging manifests.

## Maintaining This Contract

Update this file only when repository-wide operating policy, current V4 gate,
canonical authority, or a repeated safety lesson changes. Keep historical
milestones in their proper roadmap/changelog documents. Prefer links over copied
inventories, and remove stale instructions when adding replacements.
