# FREAK ACADEMY V3-FIRST DISCLAIMER

This plan is intentionally ambitious, but the first FREAK Academy release must be built on the compiler and repositories that exist today.

- **First implementation target:** V3 / v0.13.x. Use the current native `freak` CLI, the V3 LLVM pipeline, and small helper tools where the V4 query compiler does not exist yet.
- **Future implementation target:** V4. Query APIs, incremental semantic services, browser WASM execution, richer IDE/model integrations, and full semantic exercise grading are V4-era work unless a small V3-compatible slice is explicitly called out.
- **Working location:** stage the shared learning data, schemas, validators, terminal MVP, and WASM work in this main `Freak-lang` repository only until a dedicated FREAK Academy repository exists. Those files must stay split-ready and avoid unnecessary coupling to compiler internals.
- **Future repository target:** all Academy internals except the website connector belong in the future dedicated FREAK Academy repository.
- **Website location:** only the web connector, routes, and rendering integration should live in `C:\Users\razva\Documents\GitHub\freaklang.dev`. The site should consume exported Academy packages; it should not become the source of truth for lessons, schemas, engine code, or compiler adapters.
- **Scope rule:** when this document describes a V4-only architecture, treat it as a destination, not as a blocker for the first V3 Academy release.

---

# Freak Academy Implementation Plan

> Status: Draft  
> Intended audience: Freak contributors, maintainers, and coding agents such as Codex  
> Scope: V3-first terminal Learning Mode, shared lesson data, schemas, web Learning Mode for `freaklang.dev`, achievements, The Freak Book, language reference, and later V4 query-based compiler/model integrations  
> Primary objective: Build one shared semantic foundation that powers compilation, teaching, documentation, IDE features, and model tooling without duplicating language logic

---

## 0. V3-First Delivery Tracks

Use these as separate `./goal` objectives when the work spans multiple sessions:

1. **Goal A - Plan and contracts:** keep this plan accurate, add schemas, add seed content, and validate all Academy data.
2. **Goal B - V3 terminal MVP:** build `freak learn` around V3-compatible checks, output comparison, and conservative structural requirements.
3. **Goal C - V3 compiler surface:** add structured `freak check` output and small public result types without waiting for the V4 query engine.
4. **Goal D - Content and docs:** create the first seven lessons, the Book skeleton, and example checking.
5. **Goal E - WASM immediately after terminal:** build the browser-safe compiler/interpreter target as soon as the terminal MVP proves the lesson/evaluation contracts.
6. **Goal F - Website connector:** add routes/components to `C:\Users\razva\Documents\GitHub\freaklang.dev` that load exported Academy packages and call the WASM/browser adapter.
7. **Goal G - V4 upgrade path:** replace V3 adapters with V4 query APIs, richer semantic grading, and model tooling when V4 is ready.

The first active goal is Goal A plus the smallest usable start of Goal B.

---

## 1. Executive Summary

Freak should grow into more than a compiler. The proposed ecosystem has five public surfaces:

1. **The Freak compiler**  
   The authoritative implementation of Freak syntax and semantics.

2. **Freak Learning Mode**  
   An interactive terminal course built into the CLI. It demonstrates concepts, explains them, asks the learner to complete guided and independent exercises, reviews submissions semantically, administers quizzes, tracks progress, and awards achievements.

3. **Freak Academy for the web**  
   A no-install browser version of Learning Mode surfaced through the existing `freaklang.dev` app. Only the website connector belongs there; Academy content, schemas, engines, and compiler adapters belong in the future Academy repo after they are staged here. The near-term implementation should prioritize WebAssembly or a browser-safe interpreter immediately after the terminal MVP.

4. **The Freak Book and Reference**  
   A Rust-style book for humans, plus a precise language reference. All Freak examples should be compiler-checked in continuous integration.

5. **The Freak Model Kit**  
   Versioned, machine-readable language context, grammar, semantic rules, structured diagnostics, verified examples, and callable compiler queries for coding models and agents.

The key architectural rule is:

> Compiler queries answer facts about Freak programs. Product-specific layers decide how those facts are displayed, taught, scored, indexed, or exposed to tools.

No learning lesson, web component, documentation page, or model integration may reimplement language semantics with regular expressions or duplicated hand-written rules when the compiler can provide the answer.

---

## 2. Goals

### 2.1 Product goals

- Allow a new user to learn Freak entirely from a terminal.
- Allow a new user to try Freak in a browser without installing the compiler.
- Keep lesson content data-driven and versioned.
- Evaluate exercises semantically, not only by output or exact source text.
- Explain compiler behavior using the same query results used by the real compiler.
- Provide a canonical book and precise reference.
- Make Freak easy for coding agents to understand and validate.
- Keep all public surfaces synchronized with compiler versions.
- Make contribution tasks small, testable, and suitable for agent-assisted implementation.
- Preserve offline-first operation for the terminal and eventual browser implementation.
- Avoid mandatory accounts, telemetry, or cloud services in the MVP.

### 2.2 Engineering goals

- Establish stable internal boundaries between the compiler, learning engine, documentation tooling, and user interfaces.
- Expose structured compiler results with stable schemas.
- Support incremental recomputation through the query engine.
- Keep lesson schemas independent from compiler implementation details.
- Validate all examples, lessons, diagnostics, and schemas in CI.
- Make every milestone independently releasable.
- Design browser support without forcing the native compiler to depend on browser-specific code.
- Allow optional adapters for JSON-RPC, language servers, MCP-compatible tool servers, or other agent protocols without coupling the compiler core to one protocol.

---

## 3. Non-Goals for the Initial MVP

The following features should not block the first useful release:

- Global online leaderboards.
- User accounts.
- Cloud synchronization.
- AI-generated lessons.
- Natural-language grading.
- Multiplayer classrooms.
- Teacher dashboards.
- A custom terminal text editor.
- A custom documentation renderer.
- Full native code execution in the browser.
- A public model-training service.
- Fine-tuning a model specifically for Freak.
- A plugin marketplace for lessons.
- Telemetry-based personalization.
- Real-money rewards or competitive ranking.
- Automatic plagiarism detection.
- Remote arbitrary-code execution without a hardened sandbox.
- Perfect feature parity between terminal and web on day one.

These may be added later through explicit design proposals.

---

## 4. Core Design Principles

### 4.1 The compiler is authoritative

If a lesson claims that an expression has type `int`, that answer must come from the compiler. If documentation claims that code compiles, CI must compile it. If a model tool reports a diagnostic, the report must come from the compiler.

### 4.2 Queries produce facts; frontends produce experiences

Examples:

- Compiler query: `type_of(expression) -> Type`
- Learning engine: “The quotation marks make this value a string.”
- CLI: renders the explanation as terminal text.
- Web: highlights the expression and displays an interactive card.
- Model tool: returns structured JSON containing expected and actual types.

### 4.3 Stable educational contracts, unstable internal implementation

Lesson files must use stable requirement names such as:

- `symbol_exists`
- `symbol_type`
- `constant_value`
- `calls_function`
- `printed_symbol`
- `construct_used`
- `expected_output`
- `tests_pass`

They must not invoke internal compiler functions such as `resolve_symbol_internal_v4`.

### 4.4 Data-driven where data is appropriate

Data-driven content should include:

- Lesson ordering and prerequisites.
- Demonstration code.
- Exercise prompts and starter code.
- Semantic requirements.
- Quiz questions.
- Achievement definitions.
- Concept identifiers.
- Links among book, reference, lessons, and diagnostics.

Human prose should remain separately authored where pacing and explanation matter.

### 4.5 Offline first

The terminal MVP must work without a network connection. The browser target should eventually work offline after assets are cached. Accounts and network synchronization remain optional.

### 4.6 Version everything

Every public artifact must identify the language/compiler version it describes:

- Lessons.
- Book.
- Reference.
- Model context.
- Example corpus.
- Diagnostic catalog.
- Grammar.
- Exercise evaluator.
- Progress export format.

### 4.7 Progressive disclosure

Beginners see simple explanations. Advanced users can inspect:

- Tokens.
- Syntax trees.
- Name resolution.
- Types.
- Intermediate representation.
- Query dependencies.
- Optimization results.

### 4.8 Harmless humor only

Competitive Mode and achievements may be theatrical, but they must never silently corrupt output, inject bugs, alter semantics, leak data, or sabotage other compilers. Joke features must be opt-in, deterministic, documented, and testable.

---

## 5. Product Surfaces

### 5.1 Native compiler

Example commands:

```bash
freak build
freak run
freak check
freak test
freak fmt
freak explain E0214
freak inspect ast src/main.fk
freak inspect ir src/main.fk
```

### 5.2 Terminal Learning Mode

Example commands:

```bash
freak learn
freak learn list
freak learn start variables
freak learn continue
freak learn status
freak learn review
freak learn achievements
freak learn leaderboard
freak learn export progress.freaklearn
freak learn import progress.freaklearn
```

### 5.3 Web Learning Mode

The website connector belongs in `C:\Users\razva\Documents\GitHub\freaklang.dev`, not in a new `web/` app inside this repository. This repository is a temporary staging area for Academy internals until they move to the dedicated Academy repo. `freaklang.dev` should consume exported lesson packages and browser compiler artifacts; it should not own them.

Suggested route structure:

```text
/learn
/learn/course/freak-basics
/learn/course/freak-basics/variables
/playground
/book
/reference
/model-context
```

### 5.4 Documentation

- **The Freak Book:** conceptual and tutorial material.
- **Freak Reference:** exact syntax and semantics.
- **Diagnostics index:** stable error codes with explanations and examples.
- **Examples repository:** complete programs and small snippets.

### 5.5 Model-facing tools

- Compact model context.
- Machine-readable language manifest.
- Grammar.
- Semantic rule files.
- Structured compiler output.
- Verified valid/invalid examples.
- Local tool server.
- Agent instructions template.
- Optional benchmark suite.

---

## 6. Proposed Repository Layout

Adapt names to the existing repository, but preserve the boundaries. For the V3-first phase, stage shared Academy contracts in this repository with a clean transfer path to a dedicated Academy repo. Implement only the website connector/surface in the existing sibling `freaklang.dev` repo.

```text
/
├── compiler/
│   ├── core/
│   │   ├── source/
│   │   ├── lexer/
│   │   ├── parser/
│   │   ├── syntax/
│   │   ├── queries/
│   │   ├── resolve/
│   │   ├── types/
│   │   ├── diagnostics/
│   │   ├── ir/
│   │   ├── interpreter/
│   │   └── codegen/
│   ├── public-api/
│   └── tests/
│
├── cli/
│   ├── commands/
│   │   ├── build/
│   │   ├── check/
│   │   ├── inspect/
│   │   └── learn/
│   ├── terminal/
│   └── tests/
│
├── learning/
│   ├── engine/
│   │   ├── catalog/
│   │   ├── session/
│   │   ├── evaluation/
│   │   ├── feedback/
│   │   ├── scoring/
│   │   ├── progress/
│   │   └── achievements/
│   ├── schema/
│   ├── lessons/
│   │   └── freak-basics/
│   ├── quizzes/
│   └── tests/
│
├── website integration (sibling repo)
│   └── C:\Users\razva\Documents\GitHub\freaklang.dev
│
├── docs/
│   ├── book/
│   ├── reference/
│   ├── diagnostics/
│   ├── model-context/
│   ├── grammar/
│   └── examples/
│
├── model-kit/
│   ├── manifest/
│   ├── semantic-rules/
│   ├── corpus/
│   │   ├── valid/
│   │   ├── invalid/
│   │   └── repairs/
│   ├── tools/
│   ├── agent-instructions/
│   └── benchmark/
│
├── schemas/
│   ├── lesson.schema.json
│   ├── course.schema.json
│   ├── achievement.schema.json
│   ├── progress.schema.json
│   ├── diagnostic.schema.json
│   ├── exercise-evaluation.schema.json
│   └── model-manifest.schema.json
│
├── tools/
│   ├── validate-lessons/
│   ├── test-docs/
│   ├── build-model-kit/
│   ├── build-web-assets/
│   └── release/
│
├── examples/
│   ├── hello-world/
│   ├── variables/
│   ├── functions/
│   └── small-project/
│
├── PLAN.md
├── CONTRIBUTING.md
├── AGENTS.md
└── CODEX.md
```

If the project is a monorepo, use packages/crates/projects matching these boundaries. If it is not a monorepo, keep the same conceptual separation across repositories.

---

## 7. Shared Domain Model

### 7.1 Stable identifiers

Use stable IDs rather than display names.

Examples:

```text
course:freak-basics
lesson:variables
concept:variable-declaration
exercise:variables.score-variable
quiz:variables.basics
achievement:first-variable
diagnostic:E0214
reference:variables.declaration
book:core-language.variables
```

IDs must:

- Be lowercase.
- Use ASCII.
- Remain stable after display-name changes.
- Be unique within their namespace.
- Be included in progress and analytics records.
- Never depend on array position.

### 7.2 Concept registry

Create a central concept registry:

```yaml
id: variable-declaration
title: Variable declarations
since: 0.1.0
book: core-language/variables
reference: declarations/variable-declarations
lesson: freak-basics/variables
diagnostics:
  - E0201
  - E0214
examples:
  - examples/variables/basic.fk
```

The registry allows the website, book, CLI, and model kit to cross-link consistently.

---

## 8. Compiler Query API

### 8.1 Required query layers

The exact query engine implementation is project-specific, but the public semantic layer should support at least:

```text
source_text(file_id)
tokens(file_id)
syntax_tree(file_id)
parse_diagnostics(file_id)
declarations(file_id)
symbol_at(file_id, position)
resolved_symbol(reference_id)
declaration_of(symbol_id)
references_of(symbol_id)
names_in_scope(file_id, position)
type_of(expression_id)
type_of_symbol(symbol_id)
expected_type_at(file_id, position)
constant_value(expression_id)
semantic_diagnostics(file_id)
lowered_ir(item_id)
program_entry_point(project_id)
program_output(run_request)
test_results(test_request)
format_edits(file_id)
```

### 8.2 Learning-oriented facade

Do not expose raw compiler internals directly to lesson data. Add a learning facade:

```text
evaluate_requirement(submission, requirement)
explain_requirement_result(result, learner_context)
analyze_submission(submission)
compare_attempts(previous, current)
suggest_hint(failure, hint_level)
```

### 8.3 Structured result requirements

Every diagnostic or semantic result exposed outside the compiler should include stable, serializable data:

```json
{
  "code": "E0214",
  "severity": "error",
  "message": "expected `int`, found `word`",
  "primaryRange": {
    "file": "src/main.fk",
    "start": { "line": 1, "column": 17 },
    "end": { "line": 1, "column": 22 }
  },
  "relatedRanges": [],
  "data": {
    "expectedType": "int",
    "actualType": "word"
  },
  "fixes": [
    {
      "title": "Replace string literal with an integer literal",
      "applicability": "machine-applicable",
      "edits": [
        {
          "range": {
            "startOffset": 16,
            "endOffset": 21
          },
          "replacement": "17"
        }
      ]
    }
  ]
}
```

### 8.4 Query invalidation

The browser and IDE integrations need incremental behavior. Document:

- Query keys.
- Inputs and dependencies.
- Invalidation rules.
- Cache ownership.
- Thread-safety guarantees.
- Serialization constraints.
- Whether query results contain stable IDs across edits.

For early versions, correctness is more important than perfect incremental performance. It is acceptable to invalidate an entire file initially, provided the API permits finer invalidation later.

---

## 9. Learning Content Model

### 9.1 Lesson lifecycle

Every complete lesson should support this sequence:

1. Introduction and objectives.
2. Working demonstration.
3. Detailed explanation.
4. Guided exercise.
5. Semantic review.
6. Independent exercise.
7. Semantic review.
8. Quiz.
9. Lesson summary.
10. Achievement and progress update.

A lesson may omit a stage only when the schema explicitly allows it.

### 9.2 Course schema

Illustrative shape:

```json
{
  "schemaVersion": 1,
  "id": "freak-basics",
  "title": "Freak Basics",
  "languageVersion": "0.13.3",
  "description": "A first course in the Freak programming language.",
  "lessons": [
    "hello-freak",
    "variables",
    "types",
    "arithmetic",
    "conditions",
    "loops",
    "functions"
  ]
}
```

### 9.3 Lesson schema

```json
{
  "schemaVersion": 1,
  "id": "variables",
  "courseId": "freak-basics",
  "title": "Variables",
  "order": 2,
  "languageVersion": "0.13.3",
  "prerequisites": ["hello-freak"],
  "objectives": [
    "Declare an immutable variable",
    "Understand inferred primitive types",
    "Use a declared variable in an expression"
  ],
  "sections": [
    {
      "type": "demonstration",
      "id": "basic-variable",
      "source": "pilot age = 17\nsay age",
      "expectedOutput": "17\n"
    },
    {
      "type": "explanation",
      "id": "declaration-parts",
      "conceptIds": ["variable-declaration", "integer-literal"]
    },
    {
      "type": "exercise",
      "id": "score-variable",
      "mode": "guided",
      "prompt": "Create a variable named `score` with value `100`, then print it.",
      "starter": "pilot _____ = _____\nsay _____",
      "requirements": [
        {
          "kind": "symbol_exists",
          "name": "score"
        },
        {
          "kind": "symbol_type",
          "name": "score",
          "expected": "integer"
        },
        {
          "kind": "constant_value",
          "symbol": "score",
          "expected": 100
        },
        {
          "kind": "printed_symbol",
          "name": "score"
        }
      ]
    }
  ]
}
```

### 9.4 Requirement registry

Implement a registry of stable requirement kinds.

MVP requirement kinds:

- `parses`
- `compiles`
- `symbol_exists`
- `symbol_type`
- `constant_value`
- `function_exists`
- `function_signature`
- `calls_function`
- `printed_symbol`
- `construct_used`
- `operator_used`
- `expected_output`
- `tests_pass`
- `diagnostic_expected`
- `diagnostic_absent`

Each requirement handler must have:

- A schema.
- An evaluator.
- A human feedback renderer.
- A structured result representation.
- Unit tests.
- At least one valid and invalid fixture.

### 9.5 Exercise evaluation result

```json
{
  "schemaVersion": 1,
  "exerciseId": "variables.score-variable",
  "passed": false,
  "compilerVersion": "0.13.3",
  "requirements": [
    {
      "id": "score-exists",
      "kind": "symbol_exists",
      "passed": true,
      "evidence": {
        "symbolId": "sym:18",
        "range": {
          "startOffset": 4,
          "endOffset": 9
        }
      }
    },
    {
      "id": "prints-score",
      "kind": "printed_symbol",
      "passed": false,
      "evidence": {
        "printCallsFound": 0
      },
      "hintKeys": [
        "variables.score-variable.print-small",
        "variables.score-variable.print-strong"
      ]
    }
  ]
}
```

### 9.6 Hints

Hints should be authored in levels:

1. Directional hint.
2. Concept reminder.
3. Near-solution hint.
4. Full solution.

The engine must record the strongest hint revealed. Scoring should not punish normal reading time, but may reduce bonus points for increasingly explicit hints.

### 9.7 Review generation

Review should distinguish:

- Compiler-invalid code.
- Compiler-valid code that fails the lesson objective.
- Correct result achieved using the wrong concept.
- Correct semantic solution.
- Partial progress.
- Regression from the previous attempt.

Example:

```text
Your program prints `32`, but the lesson requires the result to be
calculated from `width` and `height`.

Freak found:

    say 32

Try declaring `area` using multiplication so that changing either input
also changes the result.
```

---

## 10. Terminal Learning Mode

### 10.1 Command design

```bash
freak learn
freak learn list [--course <id>]
freak learn start <lesson-id>
freak learn continue
freak learn status [--json]
freak learn review [--lesson <id>]
freak learn achievements
freak learn leaderboard
freak learn profile create <name>
freak learn profile use <name>
freak learn export <path>
freak learn import <path>
freak learn reset [lesson-id|course-id|all]
```

### 10.2 Interactive session state machine

```text
Course selection
  -> Lesson introduction
  -> Demonstration
  -> Explanation
  -> Guided exercise
  -> Review
  -> Independent exercise
  -> Review
  -> Quiz
  -> Summary
  -> Save progress
```

Persist after every transition.

### 10.3 Terminal input modes

MVP supports:

1. Inline multiline input terminated by `.submit`.
2. `$EDITOR`.
3. Save starter file and submit a path.

Example:

```text
Enter your program below.
Type `.submit` on a new line to evaluate it.
Type `.hint` for a hint or `.exit` to save and leave.

> pilot score = 100
> say score
> .submit
```

Do not build a full-screen editor during the MVP.

### 10.4 Accessibility and compatibility

- Detect whether ANSI color is supported.
- Support `NO_COLOR`.
- Provide `--plain`.
- Avoid relying exclusively on color.
- Make prompts screen-reader-friendly.
- Keep output usable in narrow terminals.
- Support JSON output for automation.
- Avoid Unicode box drawing when `--plain` is selected.

### 10.5 Local storage

Suggested default paths:

```text
~/.freak/learning/profiles.json
~/.freak/learning/progress/<profile-id>.json
~/.freak/learning/achievements/<profile-id>.json
~/.freak/learning/submissions/<profile-id>/
```

Platform-specific application data directories are preferred over hardcoded Unix paths. The examples above are conceptual.

### 10.6 Progress data

Record:

- Profile ID and display name.
- Course version.
- Lesson state.
- Completed objectives.
- Attempts.
- Hints used.
- Quiz answers.
- Best score.
- Achievement unlocks.
- Submission hashes.
- Optional local elapsed active time.
- Data format version.

Do not record source submissions outside the local machine by default.

---

## 11. Achievements and Local Leaderboards

### 11.1 Achievement categories

- Learning progression.
- Compiler exploration.
- Code quality.
- Tooling usage.
- Humor/competitive mode.
- Contributor/developer achievements.

Examples:

- `first-program`: Compile the first program.
- `first-variable`: Correctly declare and use a variable.
- `clean-room`: Complete a build with no warnings.
- `fearless`: Build with warnings treated as errors.
- `ast-archaeologist`: Inspect an AST.
- `etu-bootstrap`: Compile a compiler with Freak.
- `recursive-narcissism`: Use Freak to compile Freak.
- `peer-reviewed-development`: Select the Stack Overflow joke response.
- `speed-freak`: Complete a lesson quickly with no incorrect answers.

### 11.2 Achievement schema

```json
{
  "schemaVersion": 1,
  "id": "first-variable",
  "title": "Variable Interest",
  "description": "Declare and correctly use your first variable.",
  "category": "learning",
  "visibility": "public",
  "trigger": {
    "event": "lesson.requirement_passed",
    "where": {
      "requirementKind": "symbol_exists",
      "conceptId": "variable-declaration"
    }
  }
}
```

### 11.3 Event system

Define internal events:

```text
compiler.build_succeeded
compiler.build_failed
compiler.diagnostic_emitted
compiler.inspect_used
learning.lesson_started
learning.exercise_submitted
learning.requirement_passed
learning.lesson_completed
learning.quiz_answered
competitive_mode.rival_detected
```

Achievements subscribe to events. They must not directly inspect arbitrary compiler internals.

### 11.4 Local leaderboard

MVP leaderboard ranks local profiles by:

- Total XP.
- Lessons completed.
- Quiz accuracy.
- Achievements.

Avoid ranking by time as the primary measure.

### 11.5 Online leaderboard deferral

Do not add online leaderboards until there is:

- Authentication.
- Anti-cheat policy.
- Moderation.
- Privacy policy.
- Version-aware scoring.
- Rate limiting.
- Data deletion.
- Abuse reporting.

---

## 12. Competitive Mode

Competitive Mode is an optional joke feature.

### 12.1 Rules

- Must be explicitly enabled.
- Must never alter compiled semantics.
- Must never inject bugs.
- Must never modify unrelated files.
- Must never phone home.
- Must not rely on covert intent detection.
- May refuse or display theatrical warnings.
- May attach harmless, documented metadata only when explicitly requested.

### 12.2 Suggested triggers

- Project manifest: `kind = "compiler"`.
- Sentinel file: `.rival-toolchain`.
- Explicit flag: `--project-kind=compiler`.
- Compiler test fixture metadata.

Heuristic detection may produce warnings only.

### 12.3 Commands

```bash
freak build --competitive-mode
freak build --competitive-mode --permit-competition
```

### 12.4 Example output

```text
error[E9001]: rival compiler project detected

Freak declines to participate in its own replacement.

help: pass `--permit-competition` to acknowledge Freak's continued
      strategic superiority.
```

---

## 13. Web Learning Mode

### 13.1 Target architecture

```text
Browser UI
  -> Learning adapter
  -> Web Worker
  -> Freak compiler/interpreter compiled to WebAssembly
  -> Query database
```

The UI thread must not perform parsing, type checking, or execution.

### 13.2 Compiler adapter interface

```typescript
export interface FreakCompilerClient {
  initialize(options: InitializeOptions): Promise<CompilerInfo>;
  check(request: CheckRequest): Promise<CheckResult>;
  run(request: RunRequest): Promise<RunResult>;
  format(request: FormatRequest): Promise<FormatResult>;
  evaluateExercise(
    request: EvaluateExerciseRequest
  ): Promise<ExerciseEvaluation>;
  typeAt(request: TypeAtRequest): Promise<TypeAtResult>;
  symbolAt(request: SymbolAtRequest): Promise<SymbolAtResult>;
  inspectAst(request: InspectRequest): Promise<AstResult>;
}
```

The terminal implementation should have an equivalent interface even if it is not asynchronous.

### 13.3 Worker protocol

Use versioned message envelopes:

```json
{
  "protocolVersion": 1,
  "requestId": "req-123",
  "method": "check",
  "params": {
    "fileId": "lesson:variables:exercise-1",
    "source": "pilot score = 100"
  }
}
```

Response:

```json
{
  "protocolVersion": 1,
  "requestId": "req-123",
  "ok": true,
  "result": {
    "diagnostics": []
  }
}
```

Support cancellation for obsolete editor requests.

### 13.4 Browser execution strategy

Preferred order:

1. Browser-side interpreter.
2. Browser-side WASM code generation and execution.
3. Remote server sandbox only as a temporary bridge.

The first web release may support only a language subset if it is clearly labeled and tested.

### 13.5 Editor

MVP requirements:

- Syntax highlighting.
- Line numbers.
- Diagnostics.
- Run/check button.
- Reset starter code.
- Keyboard navigation.
- Mobile-compatible fallback.
- Paste support.
- No dependency on IDE-level completion for the first release.

CodeMirror is a suitable lightweight default. Monaco is acceptable if bundle size and mobile behavior are acceptable.

### 13.6 Web lesson layout

Suggested components:

```text
CourseNavigation
LessonHeader
LessonContent
ExampleRunner
CodeEditor
CompilerOutput
ExerciseReview
HintPanel
QuizPanel
ProgressPanel
AchievementToast
```

### 13.7 Browser storage

Use IndexedDB for:

- Profiles.
- Progress.
- Lesson packages.
- Saved submissions.
- Compiler artifacts.
- Imported/exported progress.

Use `localStorage` only for very small preferences such as theme and last-opened course.

### 13.8 Offline support

Later web milestone:

- Cache static assets.
- Cache lesson packages.
- Cache compiler WASM.
- Provide an offline indicator.
- Queue no server-dependent actions.
- Keep all core lessons functional offline.

---

## 14. The Freak Book

### 14.1 Role

The Book is a linear human-readable guide. It should explain:

- Why a feature exists.
- How to use it.
- Common mistakes.
- Complete examples.
- Idiomatic Freak.

It is not the precise language specification and not a replacement for interactive exercises.

### 14.2 Initial structure

```text
Part I: Getting Started
  1. Introduction
  2. Installation
  3. Hello, Freak
  4. Projects, building, and running
  5. Reading diagnostics

Part II: Core Language
  6. Variables and mutability
  7. Primitive types
  8. Expressions and operators
  9. Control flow
  10. Functions
  11. Collections
  12. User-defined types
  13. Modules

Part III: Freak-Specific Design
  14. Query-based compilation
  15. Incremental behavior
  16. Introspection
  17. Error handling
  18. Memory model
  19. Metaprogramming

Part IV: Real Programs
  20. Testing
  21. Project organization
  22. A command-line project
  23. A multi-module project

Part V: Tooling
  24. Editors
  25. Formatter and linter
  26. Inspecting AST and IR
  27. Learning Mode
```

Only write chapters for implemented features. Unimplemented chapters may exist as clearly marked design placeholders outside released documentation.

### 14.3 mdBook

Use mdBook initially unless repository constraints require another static documentation tool.

Create a Freak documentation checker:

```bash
freak test-docs docs/book
```

Supported code block annotations:

````markdown
```freak
pilot message = "Hello"
say message
```

```freak compile_fail,E0214
pilot age: int = "17"
```

```freak run,output="17\n"
pilot age = 17
say age
```
````

### 14.4 Documentation CI

CI must:

- Extract code blocks.
- Compile successful examples.
- Confirm expected failures.
- Confirm expected diagnostic codes.
- Run examples with expected output.
- Validate links.
- Validate concept IDs.
- Build the static site.

---

## 15. Freak Reference

### 15.1 Role

The Reference defines exact behavior:

- Grammar.
- Scope.
- Name resolution.
- Types.
- Conversions.
- Evaluation order.
- Error behavior.
- Module behavior.
- ABI or interoperability when stable.

### 15.2 Reference page template

Each reference page should contain:

- Stable ID.
- Feature status.
- Since version.
- Grammar.
- Static semantics.
- Dynamic semantics.
- Examples.
- Diagnostics.
- Related concepts.
- Compatibility notes.

### 15.3 Generated versus authored content

Generate:

- Grammar fragments.
- Diagnostic lists.
- Feature availability tables.
- Version metadata.

Author:

- Explanatory semantic prose.
- Edge cases.
- Rationale when useful.

---

## 16. Freak Model Kit

### 16.1 Purpose

The Model Kit enables existing coding models to work with Freak through retrieval and compiler calls. Training-specific datasets are secondary.

### 16.2 Required artifacts

```text
model-context.md
language-manifest.json
grammar.ebnf
tokens.json
diagnostics.json
semantic-rules/
examples-valid.jsonl
examples-invalid.jsonl
repairs.jsonl
tool-schema.json
AGENTS.template.md
```

### 16.3 Compact model context

The model context must be:

- Versioned.
- Dense.
- Explicit.
- Free of marketing prose.
- Clear about implemented and unimplemented features.
- Rich in valid and invalid examples.
- Linked to authoritative sources.

### 16.4 Language manifest

```json
{
  "schemaVersion": 1,
  "language": "Freak",
  "languageVersion": "0.13.3",
  "compilerVersion": "0.13.3",
  "fileExtensions": [".fk"],
  "entryPoint": {
    "kind": "function",
    "name": "main"
  },
  "features": {
    "typeInference": true,
    "modules": true,
    "generics": false
  }
}
```

### 16.5 Semantic rule format

```yaml
id: variable-declaration
since: 0.1.0
syntax:
  pattern: "pilot <name> [: <type>] = <initializer>"
constraints:
  - initializer_required
  - declared_type_accepts_initializer
inference:
  result_type: type_of(initializer)
diagnostics:
  missing_initializer: E0201
  incompatible_initializer: E0214
valid_examples:
  - "pilot count = 10"
invalid_examples:
  - source: 'pilot count: int = "10"'
    diagnostic: E0214
```

These rule files are documentation and tooling inputs. They are not required to become the compiler’s implementation language.

### 16.6 Structured command output

Required commands:

```bash
freak check --message-format=json
freak check --message-format=jsonl
freak test --message-format=json
freak fmt --check --message-format=json
freak inspect type-at --file src/main.fk --offset 42 --json
```

### 16.7 Local tool server

Provide a local adapter exposing:

- `check`
- `run`
- `format`
- `test`
- `type_at`
- `expected_type_at`
- `symbol_at`
- `find_references`
- `explain_diagnostic`
- `inspect_ast`
- `inspect_ir`
- `evaluate_exercise`

The internal server can use JSON-RPC. Protocol adapters may expose the same operations through MCP or other agent ecosystems. Keep protocol-specific code outside the compiler core.

### 16.8 Agent instructions

Generate a project-local `AGENTS.md`:

```markdown
# Freak project instructions

1. Read `freak.toml` before modifying code.
2. Run `freak check --message-format=json`.
3. Treat compiler diagnostics as authoritative.
4. Do not invent standard-library APIs.
5. After edits, run:
   - `freak fmt --check`
   - `freak check`
   - `freak test`
6. Do not modify generated files under `build/`.
```

### 16.9 Verified corpus

Every corpus record must include:

- Compiler version.
- Language version.
- Validity.
- Purpose.
- Source.
- Expected result.
- Diagnostic code for invalid examples.
- Tags.
- License metadata.
- Origin.

Invalid examples must be clearly labeled so they are not accidentally treated as normal training code.

---

## 17. Codex-Oriented Development Workflow

### 17.1 Repository instruction files

Create:

- `AGENTS.md`: high-level repository instructions.
- `CODEX.md`: practical task execution rules.
- Per-directory `AGENTS.md` where modules have special constraints.

Suggested `CODEX.md` contents:

```markdown
# Codex execution rules

- Work on one issue ID at a time.
- Do not refactor unrelated code.
- Read the nearest `AGENTS.md`.
- Run focused tests before full tests.
- Update schemas and fixtures together.
- Preserve public JSON compatibility unless the issue explicitly changes a schema version.
- Include tests for success, failure, and malformed input.
- Do not implement language semantics outside compiler query APIs.
- Do not add network access to terminal Learning Mode.
- Do not silently change lesson scoring.
- Report changed files, tests run, and unresolved risks.
```

### 17.2 Task sizing

Each Codex task should:

- Affect one subsystem.
- Have a clear input and output.
- Name likely files.
- Include acceptance criteria.
- Include required tests.
- Avoid ambiguous design decisions.
- Be small enough for one reviewable pull request.

Use size labels:

- **XS:** One schema or isolated helper.
- **S:** One module with tests.
- **M:** Cross-module feature with stable interface.
- **L:** Milestone-level integration; split before assigning when possible.

### 17.3 Codex task template

```markdown
## Task: LEARN-012 Implement `symbol_exists`

### Context
Learning exercises need to verify whether a submission declares a symbol
with a requested name. The compiler resolver remains authoritative.

### Scope
- Add the `symbol_exists` requirement schema.
- Add an evaluator using the public semantic query API.
- Return structured evidence with symbol ID and source range.
- Add human feedback for pass and fail.
- Add fixtures.

### Out of scope
- Type checking the symbol.
- Multiple-file search.
- Web rendering.

### Suggested files
- `learning/engine/evaluation/requirements/symbol_exists.*`
- `learning/schema/requirement.*`
- `learning/tests/requirements/symbol_exists.*`

### Acceptance criteria
- A valid variable declaration passes.
- A function with the same name is rejected when `symbolKind=variable`.
- A misspelled name fails with no crash.
- Malformed requirement data fails schema validation.
- JSON result matches `exercise-evaluation.schema.json`.

### Tests
- Unit tests for evaluator.
- Schema test.
- Golden feedback output.
```

### 17.4 Agent completion report

Require each task response to include:

- Summary.
- Files changed.
- Public API changes.
- Tests run.
- Test results.
- Deferred work.
- Risks.
- Suggested next task.

### 17.5 Review gates

Do not merge agent-generated work unless:

- Tests pass.
- Schemas validate.
- No unrelated changes exist.
- New public behavior is documented.
- Error cases are tested.
- Generated files are reproducible.
- Security-sensitive code receives human review.

---

## 18. Implementation Milestones

## Milestone 0: Foundation and contracts

### Objective

Create repository boundaries, schemas, stable IDs, and public compiler result structures before building interfaces.

### Deliverables

- Repository/module layout.
- `AGENTS.md` and `CODEX.md`.
- Concept ID conventions.
- Schema versioning policy.
- Diagnostic JSON schema.
- Lesson/course schemas.
- Progress schema.
- Exercise evaluation schema.
- Compiler public API boundary.
- Initial golden fixtures.

### Acceptance criteria

- All schemas validate example files.
- CI runs schema validation.
- Public diagnostic output can be serialized.
- No lesson evaluator depends on private compiler structures.

### Suggested Codex tasks

- `FOUND-001`: Add schema directory and validation command.
- `FOUND-002`: Define stable source range structure.
- `FOUND-003`: Define diagnostic JSON schema.
- `FOUND-004`: Define course and lesson schemas.
- `FOUND-005`: Add concept registry format.
- `FOUND-006`: Add repository agent instructions.
- `FOUND-007`: Add golden test harness.

---

## Milestone 1: Structured compiler interface

### Objective

Expose the minimum compiler queries required by Learning Mode and model tools.

### Deliverables

- Parse/check API.
- Stable diagnostics.
- Symbol lookup.
- Type lookup.
- Constant evaluation where supported.
- Structured format/check output.
- CLI JSON output.

### Acceptance criteria

- `freak check --message-format=json` works.
- Diagnostics include stable code and ranges.
- Symbol and type queries are callable without rendering terminal text.
- Results have deterministic serialization.

### Suggested Codex tasks

- `COMP-001`: Add serializable compiler result types.
- `COMP-002`: Implement `check` public API.
- `COMP-003`: Add `symbol_at` and `declaration_of`.
- `COMP-004`: Add `type_of_symbol`.
- `COMP-005`: Add `constant_value`.
- `COMP-006`: Implement JSON and JSONL CLI renderers.
- `COMP-007`: Add compatibility snapshot tests.

---

## Milestone 2: Learning engine core

### Objective

Evaluate data-driven lessons independently of the terminal and web UIs.

### Deliverables

- Course catalog loader.
- Lesson loader.
- Schema validation.
- Session state machine.
- Requirement registry.
- Initial requirement handlers.
- Review result model.
- Progress persistence interface.

### Initial requirements

- `parses`
- `compiles`
- `symbol_exists`
- `symbol_type`
- `constant_value`
- `calls_function`
- `expected_output`

### Acceptance criteria

- A test lesson can be loaded and completed programmatically.
- Invalid lesson data fails clearly.
- Exercise evaluation produces structured results.
- Learning logic has no terminal dependencies.

### Suggested Codex tasks

- `LEARN-001`: Course catalog loader.
- `LEARN-002`: Lesson loader and validation.
- `LEARN-003`: Session state machine.
- `LEARN-004`: Requirement registry.
- `LEARN-005`: `parses` and `compiles`.
- `LEARN-006`: `symbol_exists`.
- `LEARN-007`: `symbol_type`.
- `LEARN-008`: `constant_value`.
- `LEARN-009`: `calls_function`.
- `LEARN-010`: `expected_output`.
- `LEARN-011`: Structured review generator.
- `LEARN-012`: Progress storage interface.

---

## Milestone 3: Terminal Learning Mode MVP

### Objective

Deliver a complete terminal lesson experience.

### Deliverables

- `freak learn`.
- Course and lesson navigation.
- Demonstration runner.
- Explanation renderer.
- Inline exercise input.
- `$EDITOR` integration.
- Hints.
- Semantic review.
- Quiz engine.
- Progress saving.
- Basic scoring.
- Plain output mode.

### Initial course

1. Hello, Freak.
2. Variables.
3. Primitive types.
4. Arithmetic.
5. Conditions.
6. Loops.
7. Functions.

### Acceptance criteria

- A new profile can complete all seven lessons offline.
- Progress survives process exit.
- Each lesson has a demonstration, exercise, review, and quiz.
- Terminal output works without color.
- No exercise relies on exact source string matching.

### Suggested Codex tasks

- `CLI-LEARN-001`: Command routing.
- `CLI-LEARN-002`: Course list renderer.
- `CLI-LEARN-003`: Lesson session runner.
- `CLI-LEARN-004`: Inline multiline source input.
- `CLI-LEARN-005`: `$EDITOR` adapter.
- `CLI-LEARN-006`: Demonstration and explanation renderer.
- `CLI-LEARN-007`: Review renderer.
- `CLI-LEARN-008`: Quiz renderer.
- `CLI-LEARN-009`: Progress commands.
- `CONTENT-001` through `CONTENT-007`: Initial lessons.

---

## Milestone 4: Achievements and polish

### Objective

Add motivation and personality without compromising learning.

### Deliverables

- Achievement schema.
- Event bus.
- Achievement evaluator.
- Local profiles.
- Local leaderboard.
- Competitive Mode.
- Achievement notifications.

### Acceptance criteria

- Achievements unlock deterministically.
- Replaying an event does not duplicate unlocks.
- Competitive Mode never changes semantic output.
- Leaderboard remains local.
- Achievement data exports with progress.

### Suggested Codex tasks

- `ACH-001`: Event model.
- `ACH-002`: Achievement schema and loader.
- `ACH-003`: Trigger evaluator.
- `ACH-004`: Unlock persistence.
- `ACH-005`: CLI achievement output.
- `ACH-006`: Local leaderboard.
- `COMPETE-001`: Safe Competitive Mode.

---

## Milestone 5: The Freak Book and Reference MVP

### Objective

Publish canonical human documentation with compiler-checked examples.

### Deliverables

- mdBook setup.
- Six initial chapters.
- Reference skeleton.
- Diagnostic index.
- Documentation test tool.
- Link/concept validation.

### Acceptance criteria

- All Freak code blocks are checked in CI.
- Expected failures verify diagnostic codes.
- Book links to matching lessons.
- Reference pages identify supported compiler versions.

### Suggested Codex tasks

- `DOC-001`: mdBook setup.
- `DOC-002`: Freak code-block extractor.
- `DOC-003`: Compile-success verifier.
- `DOC-004`: Compile-fail verifier.
- `DOC-005`: Expected-output verifier.
- `DOC-006`: Concept link validator.
- `DOC-CONTENT-001` through `006`: Initial chapters.

---

## Milestone 6: WebAssembly compiler integration

### Objective

Run the required compiler subset entirely in the browser as soon as the terminal MVP proves the lesson and evaluation contracts.

### Deliverables

- WASM build target or browser-safe interpreter target.
- Exportable Academy lesson package and worker protocol contract.
- Browser-compatible query/evaluation boundary.
- Worker initialization.
- Incremental check where supported.
- Browser execution path for initial lessons.
- Bundle size reporting.
- Cancellation and timeout handling.

### Acceptance criteria

- All initial terminal lessons can be checked in a browser worker without a server.
- Repeated edits reuse compiler state where supported.
- A long-running program is terminated safely.
- UI remains responsive.
- Browser and native evaluation results match golden tests for supported lessons.

### Suggested Codex tasks

- `WASM-001`: Minimal browser-safe compiler or interpreter target.
- `WASM-002`: Serialization boundary.
- `WASM-003`: Worker state manager.
- `WASM-004`: Incremental check integration.
- `WASM-005`: Browser execution adapter.
- `WASM-006`: Resource limits.
- `WASM-007`: Cross-target conformance tests.

---

## Milestone 7: Web connector prototype

### Objective

Provide no-install interactive lessons through `freaklang.dev` using the shared Academy package and browser compiler adapter.

### Deliverables

- `freaklang.dev` Academy route shell.
- Course browser.
- Lesson renderer.
- Editor.
- Compiler client interface.
- Web Worker wrapper.
- Progress storage in IndexedDB.
- Import/export.
- Integration with the WASM/browser-safe compiler artifact.

### Acceptance criteria

- The variables lesson works end-to-end in a browser.
- Compilation does not block the UI thread.
- Progress persists locally.
- The same lesson data is used by terminal and web.
- The web app clearly reports unsupported features.

### Suggested Codex tasks

- `WEB-001`: `freaklang.dev` route shell and navigation.
- `WEB-002`: Shared lesson package loader.
- `WEB-003`: Compiler client interface.
- `WEB-004`: Worker protocol.
- `WEB-005`: Editor integration.
- `WEB-006`: Review UI.
- `WEB-007`: IndexedDB storage.
- `WEB-008`: Progress import/export.
- `WEB-009`: Browser execution adapter.

---

## Milestone 8: Freak Model Kit

### Objective

Make Freak easy for coding models and agents to understand and validate.

### Deliverables

- `model-context.md`.
- Language manifest.
- Grammar export.
- Diagnostic catalog export.
- Semantic rules.
- Valid/invalid/repair corpus.
- Local tool server.
- Agent instructions generator.

### Acceptance criteria

- Every corpus record is compiler-verified.
- Tool outputs validate against schemas.
- Model context identifies exact language version.
- An external agent can check and repair a simple Freak program through tools.
- Invalid examples are unambiguously labeled.

### Suggested Codex tasks

- `MODEL-001`: Language manifest generator.
- `MODEL-002`: Compact model context builder.
- `MODEL-003`: Diagnostic catalog exporter.
- `MODEL-004`: Corpus record schema.
- `MODEL-005`: Valid example exporter.
- `MODEL-006`: Invalid example exporter.
- `MODEL-007`: Repair pair generator.
- `MODEL-008`: Local tool server.
- `MODEL-009`: `AGENTS.md` generator.

---

## 19. Testing Strategy

### 19.1 Unit tests

Required for:

- Query adapters.
- Requirement handlers.
- Schema validators.
- Scoring.
- Achievement triggers.
- Progress migrations.
- Worker protocol.
- Corpus builders.

### 19.2 Golden tests

Use golden files for:

- Terminal diagnostics.
- Learning reviews.
- JSON compiler output.
- Lesson summaries.
- Achievement notifications.
- Book example extraction.
- Model context output.

Golden updates must be reviewed carefully.

### 19.3 Conformance tests

The same submission must produce equivalent semantic results in:

- Native compiler.
- Terminal Learning Mode.
- Web compiler/WASM.
- Model tool server.

### 19.4 Property tests

Useful targets:

- Parser never crashes on arbitrary input.
- Serializer round-trips.
- Progress export/import preserves state.
- Requirement evaluation is deterministic.
- Incremental and clean recomputation match.
- Formatting is idempotent.

### 19.5 End-to-end tests

Scenarios:

1. New profile completes a lesson.
2. User exits mid-exercise and continues.
3. Invalid code receives a compiler explanation.
4. Correct output using the wrong construct is rejected.
5. Achievement unlocks once.
6. Progress exports from terminal and imports into web.
7. Model tool checks and repairs code.
8. Book code examples compile.

### 19.6 Security tests

- Malformed lesson files.
- Oversized source input.
- Infinite loops.
- Deep recursion.
- Path traversal in lesson packages.
- Malicious progress imports.
- Invalid worker messages.
- Untrusted web execution.
- Resource exhaustion.
- Corpus injection from untrusted sources.

---

## 20. Security and Privacy

### 20.1 Terminal

- No network access by default.
- Store data in the platform application-data directory.
- Validate imported progress.
- Never execute shell commands from lesson data.
- Treat `$EDITOR` as an explicit user-controlled integration.
- Do not load lessons from arbitrary remote URLs in the MVP.

### 20.2 Web

- Run compiler work in a Worker.
- Apply execution limits.
- Avoid `eval`.
- Sanitize rendered Markdown.
- Validate lesson packages.
- Use a strict Content Security Policy.
- Never expose native filesystem paths.
- Keep user code local by default.

### 20.3 Server-backed fallback

If used temporarily:

- Run each compilation in an isolated sandbox.
- Apply CPU, memory, process, file, and time limits.
- Disable outbound network access.
- Rate limit.
- Do not persist user source.
- Log operational metadata, not source content.
- Document retention.
- Obtain a security review before public exposure.

### 20.4 Model kit

- Clearly label generated and human-authored records.
- Include licenses.
- Prevent secrets or private project code from entering public corpora.
- Do not upload user projects without explicit action.
- Make tool calls local by default.

---

## 21. Versioning and Migrations

### 21.1 Schema versions

Every persisted or public JSON object must include `schemaVersion`.

### 21.2 Language compatibility

Lessons declare:

- Minimum compiler version.
- Maximum tested compiler version, when needed.
- Required language features.

### 21.3 Progress migrations

Progress files should migrate forward:

```text
v1 -> v2 -> v3
```

Keep migrations deterministic and test them with fixtures.

### 21.4 Content compatibility

When a language change invalidates a lesson:

- Update the lesson version.
- Preserve old content under versioned documentation if practical.
- Migrate progress only when completion semantics remain equivalent.
- Otherwise mark the lesson as requiring review.

### 21.5 Diagnostic stability

Error codes should remain stable where possible. Message wording may evolve, but machine consumers should depend on codes and structured fields.

---

## 22. CI/CD Pipeline

Recommended stages:

```text
1. Format and lint
2. Unit tests
3. Schema validation
4. Compiler tests
5. Learning engine tests
6. Lesson validation
7. Documentation example tests
8. Model corpus verification
9. Native/web conformance
10. Web build
11. Documentation build
12. Artifact packaging
```

Release artifacts:

- Native compiler.
- Lesson package.
- Book site.
- Reference site.
- Web app.
- WASM compiler.
- Model Kit archive.
- JSON schemas.
- Checksums.

---

## 23. Observability

The MVP does not require telemetry.

Local debug modes should exist:

```bash
freak learn --trace
freak check --trace-queries
freak web-worker --debug-protocol
```

Debug output may include:

- Query cache hits and misses.
- Lesson state transitions.
- Requirement evaluations.
- Worker request timings.
- WASM initialization.
- Execution limits.

Never include private source in logs unless the user explicitly enables verbose source logging.

---

## 24. First Ten Pull Requests

A practical starting sequence:

### PR 1 — Repository instructions and schemas

- Add `AGENTS.md`.
- Add `CODEX.md`.
- Add `schemas/`.
- Add schema validation command.

### PR 2 — Structured diagnostic type

- Stable diagnostic code.
- Severity.
- Source range.
- Structured data.
- JSON serializer.

### PR 3 — `freak check --message-format=json`

- Wire diagnostics into CLI JSON output.
- Add snapshot tests.

### PR 4 — Course and lesson loader

- Load one test course.
- Validate schema.
- Report useful errors.

### PR 5 — Learning session state machine

- Start.
- Continue.
- Save.
- Resume.
- Complete.

### PR 6 — `parses`, `compiles`, and `symbol_exists`

- Requirement registry.
- Evaluators.
- Fixtures.

### PR 7 — Minimal terminal lesson runner

- List lessons.
- Start lesson.
- Render demonstration.
- Collect `.submit` input.
- Show structured review.

### PR 8 — Variables lesson

- Full lesson data.
- Guided exercise.
- Independent exercise.
- Quiz.
- Golden terminal output.

### PR 9 — Progress persistence

- Local profile.
- Save attempts and completion.
- Resume after exit.

### PR 10 — Documentation checker skeleton

- Extract `freak` code blocks.
- Compile successful examples.
- Add CI job.

This sequence proves the architecture before large content or web work begins.

---

## 25. Definition of Done

A feature is done only when:

- The implementation is complete.
- Public behavior is documented.
- Unit tests cover success and failure.
- Schemas are updated if needed.
- Golden files are updated intentionally.
- CLI plain output works where applicable.
- Structured output validates.
- No unrelated refactor is included.
- Security implications are considered.
- Existing lessons and documentation still validate.
- The task’s acceptance criteria are demonstrably satisfied.

A milestone is done only when its end-to-end acceptance scenario passes.

---

## 26. Open Design Decisions

These decisions should be made through small design records before implementation:

1. Which query engine implementation does Freak use?
2. Are expression and symbol IDs stable across edits?
3. What execution model is available for lessons: interpreter, native backend, or both?
4. What subset is realistic for the first WASM build?
5. Is lesson source authored in JSON, YAML, or TOML?
6. Is Markdown allowed inside lesson content?
7. How should future repository packaging expose `.fk` lesson files to the website?
8. How are modules represented in browser exercises?
9. How are standard-library APIs versioned?
10. Which error codes are considered stable public API?
11. Does Freak permit shadowing?
12. What type inference rules are stable enough to teach?
13. What syntax highlighting grammar will be canonical?
14. Which `freaklang.dev` domain paths will be used for Academy, Book, and Reference?
15. Which license applies to code, documentation, and datasets?
16. Is the local tool server shipped with the compiler or separately?
17. Should the model tool protocol support MCP in the first release or through an adapter later?
18. How are lesson packages signed or trusted if third-party lessons are eventually allowed?

Until resolved, use interfaces that do not force irreversible answers.

---

## 27. Risk Register

### Risk: Duplicated language logic

**Impact:** Web, lessons, and compiler disagree.  
**Mitigation:** All semantic checks call compiler queries; add conformance tests.

### Risk: Lesson schemas expose private compiler details

**Impact:** Internal refactors break content.  
**Mitigation:** Stable requirement registry and adapter layer.

### Risk: WASM port consumes too much effort

**Impact:** Web launch is delayed.  
**Mitigation:** Build web against an interface; use interpreter or limited adapter first.

### Risk: Terminal UI becomes a custom editor project

**Impact:** MVP stalls.  
**Mitigation:** Use multiline input and `$EDITOR`.

### Risk: Book examples become stale

**Impact:** Documentation loses trust.  
**Mitigation:** Compile all examples in CI.

### Risk: Scoring rewards speed over understanding

**Impact:** Poor learning experience.  
**Mitigation:** Base score on correctness, hints, and concepts; keep speed achievements optional.

### Risk: Online leaderboard abuse

**Impact:** Cheating, privacy, moderation burden.  
**Mitigation:** Keep leaderboard local during MVP.

### Risk: Model corpus contains invalid unlabeled code

**Impact:** Models learn broken syntax.  
**Mitigation:** Explicit validity fields and compiler verification.

### Risk: Browser execution can be abused

**Impact:** Resource exhaustion or service compromise.  
**Mitigation:** Browser Workers, limits, and no server execution unless sandboxed.

### Risk: Too many simultaneous products

**Impact:** None reach usable quality.  
**Mitigation:** Follow milestones; terminal engine first, then WASM/browser compiler, then the website connector, then docs/model kit.

---

## 28. Recommended Priority Order

1. Stable compiler result types.
2. Lesson schemas.
3. Learning engine.
4. One excellent terminal lesson.
5. Progress persistence.
6. Seven-lesson terminal course.
7. WASM or browser-safe compiler/interpreter for initial lessons.
8. `freaklang.dev` web connector prototype.
9. Documentation testing.
10. Initial Book.
11. Achievements.
12. Model Kit.
13. Optional accounts and synchronization.
14. Global competitive features only after the core is mature.

---

## 29. Success Criteria

The ecosystem is successful when:

- A user can discover Freak, open the web course, and complete a lesson without installation.
- The same user can install Freak and continue in the terminal.
- Exercise feedback identifies what the learner actually wrote.
- Book examples always match the current compiler.
- A coding agent can call Freak to validate generated code.
- Lessons, documentation, web, and model tools use the same compiler semantics.
- Language changes produce clear failures in CI instead of silent documentation drift.
- Contributors can implement work through small, precise, reviewable tasks.

---

## 30. FREAK Rewrite Endgame

The bootstrapping implementation may use Python and other host-language tooling while V3 and V4 are still maturing. That is a temporary implementation strategy, not the final identity of the project.

The actual FREAK Academy should eventually be written in FREAK:

- The lesson engine, progress model, requirement evaluators, content validators, exporters, and terminal learner should move to FREAK after V4 can support them cleanly.
- The WASM/browser-safe compiler adapter should become a FREAK-owned artifact, not a permanent Python or JavaScript reimplementation.
- The dedicated FREAK Academy repository should treat FREAK source as the primary implementation once the rewrite begins.
- The `freaklang.dev` site remains the web connector unless and until the FREAK web stack can host the Academy UI itself.
- Host-language shims are allowed only at platform boundaries such as browser APIs, filesystem packaging, process execution, or deployment glue.

### Rewrite readiness criteria

Do not start the rewrite merely for aesthetics. Start it when:

- V4 has the semantic/query APIs needed by lessons.
- FREAK can read/write JSON or the chosen lesson format robustly.
- FREAK can run the terminal learner with acceptable startup time.
- The browser/WASM path has a stable serialization boundary.
- Existing Python/bootstrap tests can be reused as compatibility fixtures.
- The rewrite can happen module by module without stopping Academy releases.

### Rewrite acceptance criteria

The rewrite is successful when:

- The FREAK implementation can validate all lesson packages.
- The FREAK terminal learner can complete the full basics course.
- Progress import/export remains compatible with the bootstrapped implementation.
- Browser and native evaluation results still match golden tests.
- The old host-language implementation is either removed or clearly marked as bootstrap-only.

---

## 31. Final Architectural Rule

The compiler should not merely compile Freak programs. It should be the semantic service that the rest of the Freak ecosystem depends on.

```text
Compiler queries
  ├── Native compiler CLI
  ├── IDE and editor support
  ├── Terminal Learning Mode
  ├── Web Learning Mode
  ├── The Freak Book validation
  ├── Language Reference generation
  ├── Model Kit
  ├── Agent tool server
  └── FreakBench
```

Build that shared foundation first. Every later feature becomes smaller, more consistent, and easier for both humans and Codex to implement.
