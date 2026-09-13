# FREAK Lite — Development Checklist
**Language:** Python → transpiles to C  
**Goal:** Get FREAK source files compiling to native binaries via Clang/GCC  
**Reference:** freak-lite-bible.md for all syntax/mapping details

---

## PHASE 0 — Project Setup
*Do this first. Takes 20 minutes.*

- [x] Create project folder structure
- [x] Set up `__main__.py` so `python -m freakc file.fk` works
- [x] Create `tests/hello.fk` — first target program:
  ```
  pilot name = "Takeru"
  pilot power = 9001
  say "Hello from FREAK! {name} has power {power}."
  ```
- [x] Confirm Python 3.10+
- [x] Create `run.sh`: compile → clang → execute in one command

---

## PHASE 1 — Lexer
*Source string → list of Token objects*

- [x] Define `Token` dataclass: `type`, `value`, `line`, `col`
- [x] Define `TokenType` enum (all types from Bible Section 6.1)
- [x] Implement `Lexer` class with `tokenize(source: str) -> list[Token]`
- [x] Whitespace skipping, line number tracking
- [x] `--` line comments (skip to end of line)
- [x] Integer literals: `42`, `0xFF`, `0b1010`
- [x] Float literals: `3.14`
- [x] String literals `"..."` with `{interp}` markers
- [x] Bool literals: `true`, `false`, `yes`, `no`, `hai`, `iie`
- [x] Single-char tokens: `{ } ( ) [ ] , : . @ _`
- [x] Multi-char operators: `-> => |> :: == != <= >= ** += -= *= /=`
- [x] Identifiers and keywords (keyword list from Bible 6.1)
- [x] Multi-word keywords (lex greedily):
  - `give back`, `or else`, `trust me`, `for each`
  - `training arc`, `on my honor as`
  - `knowing this will hurt`, `for science`
  - `PLUS ULTRA`, `FINAL FORM`
- [x] `done` keyword as synonym for `}`
- [x] TEST: tokenize `hello.fk`, print all tokens, visually verify

---

## PHASE 2 — Parser
*Token list → Program AST*

- [x] Define all AST dataclasses (Bible Section 7.1)
- [x] Implement `Parser` class with `parse() -> Program`
- [x] `pilot x = expr` variable declarations
- [x] `pilot x: Type = expr` with type annotation
- [x] `say expr` print statement
- [x] String interpolation: extract `{expr}` spans
- [x] Literals: int, float, bool
- [x] Identifiers and field access `a.b.c`
- [x] Binary operators with correct precedence
- [x] Unary operators: `not`, `-`
- [x] Function calls `f(a, b)`
- [x] `task` declarations (block, arrow, done forms)
- [x] `give back expr`
- [x] `if / else if / else` blocks
- [x] `when` pattern match with arms and `_`
- [x] `for each x in y { }` loop
- [x] `repeat N times { }` loop
- [x] `shape Name { }` struct declaration
- [x] `impl` blocks (with and without doctrine)
- [x] `{ }` and `done` blocks (identical)
- [x] `[1, 2, 3]` list literals
- [x] `{ "key": value }` map literals
- [x] `(a, b)` tuple literals and destructuring
- [x] `|x| => expr` and `|x| { block }` lambdas
- [x] Generic type expressions: `maybe<T>`, `result<T,E>`, `List<T>`
- [x] `some(x)`, `nobody`, `ok(x)`, `err(x)`
- [x] `check expr { got x -> ... nobody -> ... }`
- [x] `check result expr { ok(x) -> ... err(e) -> ... }`
- [x] `expr?` error propagation
- [x] `expr or else expr` fallback
- [x] `use module::{items}` imports
- [x] `launch` modifier
- [x] `@annotation` annotations
- [x] `trust me "msg" on my honor as .level { }`
- [x] `training arc until cond max N sessions { }`
- [x] `foreshadow pilot x = expr` and `payoff x`
- [x] `knowing this will hurt, call()` and `sadly call()`
- [x] `for science, call()`
- [x] Anime operators as binary ops
- [x] TEST: parse `hello.fk`, pretty-print AST, visually verify

---

## PHASE 3 — Minimal C Emitter (Hello World target)
*AST → C source string. Skip type checker. Get something running.*

- [x] `CEmitter` class with `emit(program: Program) -> str`
- [x] Emit `#include "freak_runtime.h"`
- [x] Emit `int main() { freak_main(); return 0; }`
- [x] `pilot x = 42` → `int64_t x = 42;`
- [x] `pilot x = "hello"` → `freak_word x = freak_word_lit("hello");`
- [x] `pilot x = true` → `bool x = true;`
- [x] `say "Hello {name}!"` → `freak_say(freak_interpolate(...));`
- [x] `task f(a: int) -> int { give back a; }` → C function
- [x] Function forward declarations before definitions
- [x] **★ MILESTONE: hello.fk compiles and runs ★**

---

## PHASE 4 — Runtime Header (freak_runtime.h)

- [x] `freak_word` struct: data pointer + byte_length + char_count
- [x] `freak_word_lit(const char* s)`
- [x] `freak_say(freak_word msg)` — print with newline
- [x] `freak_ask(freak_word prompt)` — read stdin
- [x] `freak_interpolate(...)` — handle `{x}` substitution
- [x] `freak_word_concat`, `freak_word_eq`
- [x] `freak_word_from_int`, `freak_word_from_double`
- [x] `freak_panic(freak_word msg)` — print + exit(1)
- [x] Generated `freak_maybe_T` structs per type used
- [x] Generated `freak_result_T_E` structs per type combo used
- [x] Generated `freak_list_T` structs with push/get/length/filter/map/fold

---

## PHASE 5 — Full C Emitter

- [x] `if / else if / else` → C if/else
- [x] `when` → switch (int) or strcmp chain (word)
- [x] `for each x in list` → C for loop
- [x] `repeat N times` → C for loop
- [x] `training arc` → C while with session counter
- [x] `shape` → C typedef struct (topologically sorted)
- [x] `impl` methods → C functions with shape pointer first arg
- [x] Closures → capture struct + function pointer (Bible Section 2.6)
- [x] `|>` pipe → desugar to nested calls or temp vars
- [x] `?` operator → inline result check + early return
- [x] `check` (maybe) → if/else on has_value
- [x] `check result` → if/else on is_ok
- [x] `or else` → ternary fallback
- [x] `some/nobody/ok/err` → macro calls
- [x] List literals → new() + push calls
- [x] Destructuring → temp var + field assignments
- [x] `launch` → non-static; no launch → static
- [x] `trust me` → plain C block + compile-time log
- [x] `foreshadow/payoff` → C comments + symbol table tracking
- [x] Annotations → C comments
- [x] `knowing this will hurt` / `sadly` / `for science` → strip prefix, call normally
- [x] `route` return type → generated enum + tagged union
- [x] Anime operators → C expressions (Bible Section 2.12)
- [x] Generics → monomorphise per concrete type used

---

## PHASE 6 — Type Checker

- [x] Symbol table: variables and types per scope
- [x] Type inference for all literals (Bible Section 8.3)
- [x] All referenced variables declared before use
- [x] Function call argument counts match signature
- [x] Explicit annotations consistent with inferred types
- [x] `give back` type matches task return type
- [x] `check` only on `maybe<T>` values
- [x] `check result` only on `result<T,E>` values
- [x] `?` only inside result-returning tasks
- [x] `foreshadow` variables paid off before scope ends
- [x] `@nakige` tasks called with acknowledgement
- [x] Only ONE `@season_finale` per program
- [x] Annotate every AST node with resolved type
- [x] Clear, line-numbered error messages

---

## PHASE 7 — CLI

- [x] `freak run file.fk` — compile and run
- [x] `freak build file.fk` — compile to binary
- [x] `freak check file.fk` — type check only
- [x] `freak test` — run the Python bootstrap test suite (`tests/suite/run_tests.py` shim; native runner is V4)
- [x] `--output / -o` flag
- [x] `--keep-c` flag (keep emitted C for debugging)
- [x] Friendly errors: filename, line number, highlighted bad line

---

## PHASE 8 — Audit Commands
*No AI API needed — these are pure static analysis over the AST*

- [x] `freak audit-science` — list every `for science,` call site in the project
- [x] `freak audit-trust` — list every `trust me` block with file, line, honor level, and message
- [x] `freak audit-miracles` — list every `deus_ex_machina` block with monologue preview
- [x] `freak foreshadow-audit` — show all foreshadow/payoff pairs and any unpaid ones

---

## PHASE 9 — Hangar Package Manager (v1)
*Basic dependency management for the Sortie toolchain*

- [x] `hangar.toml` parsing (using `tomllib`)
- [x] `freak hangar init` — project skeleton + hangar.toml
- [x] `freak hangar install` — download deps to `hangar_cache/`
- [x] `freak hangar add [package]` — add dep + update hangar.toml
- [x] Basic registry: GitHub releases integration
- [x] Resolve `use muvluv::{}` imports to downloaded files

---

## PHASE 10 — muvluv Package (Official)
*The flagship Hangar package. You maintain this.*

- [x] `Eishi` type: name, power, status, callsign
- [x] `BETA::Tier` enum: Soldier → Grappler → Destroyer → Tank → Laser → Fort → BRAIN
- [x] `Tier::required_power()` method
- [x] `TSF` type: model, variant, mounted_weapon, os_version
- [x] `COSMO` module: request_strike() (stub — prints confirmation)
- [x] `YuukoLab` helpers for @experiment scaffolding
- [x] Write the BETA early warning system as the showcase example
- [x] Publish to Hangar registry

---

## MILESTONES

```
[x] M1  — hello.fk compiles and runs              (Phase 0-3)
[x] M2  — variables, tasks, if/when/loops all work (Phase 5 partial)
[x] M3  — closures and pipes work
[x] M4  — maybe<T> and result<T,E> fully work
[x] M5  — type checker catching real errors        (Phase 6)
[x] M6  — `freak run` CLI works end-to-end         (Phase 7)
[x] M7  — Audit commands (freak audit-science/trust/miracles/foreshadow-audit)
[x] M8  — muvluv installable via Hangar            (Phase 9-10)
[x] M9  — BETA early warning system runs in FREAK
[x] M10 — GitHub repo public, README written       ← tell people
[x] M11 — std::process, std::thread, std::bytes done (runtime stubs + emitter + tests)
[x] M12 — operator overloading works (Add/Sub/Mul/Div/Rem/Neg/Eq/Ord/Index via doctrines, Python emitter)
[x] M13 — freak-http and freak-json shipped (std/http.fk, std/json.fk pure FREAK)
[~] M14 — std::zip done (std/zip.fk), std::image deferred to V4
[x] M15 — self-hosting compiler bootstrap COMPLETE (freakc_self.exe compiles hello.fk)
[x] M16 — std::fs, std::math, std::time integrated in v2 compiler
[x] M17 — LLVM IR backend core complete (LB1-LB4: hello, types, control flow, shapes, impl)
[x] M18 — CI/CD: GitHub Actions on Linux/macOS/Windows, auto-release on tag push
[x] M19 — Distribution: install.sh, install.ps1, hangar install freak, v0.9.0 released
[x] M20 — Conformance audit + freak audit-conformance command (v0.13.x baseline gate)

---

## PHASE 16 — LLVM IR Backend (v2 self-hosting compiler)
*Emit LLVM IR from the self-hosting compiler written in FREAK*

- [x] LLVM IR emitter framework (`src/compiler/backend/llvm.fk`)
- [x] Variables (int, word, bool, num) → alloca/store/load
- [x] Functions with proper void/i64 return types
- [x] String interpolation with type-aware formatting
- [x] If/else → conditional branching
- [x] When (pattern matching) → chained comparisons
- [x] Repeat until / repeat N times / training arc loops
- [x] Break/continue with label save/restore
- [x] Shapes (structs) with typed field registry
- [x] Impl methods (ShapeName_method mangling)
- [x] Pipe operator (`|>` desugaring)
- [x] Eventually (defer) blocks
- [x] Boolean logic (and/or/not)
- [x] Comparisons (==, !=, <, >, <=, >=)
- [x] Cross-compilation targets (`--target`)
- [x] Runtime intrinsics (LLVM-compatible array pool + libc wrappers in freak_llvm_runtime.c; platform-dep C remains for stdin/popen/sockets/UI)
- [ ] JIT mode via OrcJIT (LB7 — deferred to V4)
- [x] Optimization levels (--opt=0/1/2/3)
- [x] DWARF debug info — minimal LineTablesOnly (LB10): DISubprogram per function + per-instruction !dbg metadata in IR; verified with !llvm.dbg.cu / !llvm.module.flags

---

## PHASE 17 — CI/CD & Distribution

- [x] GitHub Actions CI on Linux/macOS/Windows
- [x] Release workflow: 4-platform binary matrix on tag push
- [x] v0.9.0 released with downloadable binaries
- [x] `install.sh` — Linux/macOS curl installer
- [x] `install.ps1` — Windows PowerShell installer
- [x] `hangar install freak` / `hangar upgrade freak` — toolchain bootstrap
- [x] Homebrew formula (packaging/homebrew/freak.rb, checksum-patched on tag)
- [x] Scoop manifest (packaging/scoop/freak.json, checksum-patched on tag)
- [x] Winget manifests (packaging/winget/manifests/F/FREAK/freak/<version>/, dynamic path on release)

---

## SESSION NOTES — v0.13.3 "Shiranui" final patch

Released 2026-04-28. Ships the last v0.13.x patch before V4 work begins.

### Conformance audit + V4 roadmap
- New `freak-conformance-audit.md` — per-section bible-vs-implementation mapping, top-18 divergences, triage list, untested-contract list for V4 milestone planning
- New `freak audit-conformance` command (Python + native CLI) — verifies the v0.13.x baseline (lexer keywords, audit dispatch consistency, stdlib presence, `--strict-borrow` flag, `deus_ex_machina` 20-word rule); exits nonzero on real divergence; skips V4-tagged contracts so it stays green during V4 development
- Bible §0 added: Implementation Status legend + per-section status matrix (✅ Implemented / ⚠️ Partial / 🔜 V4)
- V4 admonitions added across §1-§17 — every contract that doesn't ship in v0.13.x is explicitly tagged so readers know not to depend on it yet

### Native CLI audit dispatch
- `src/cli/audit.fk` — new module shells `audit-science` / `audit-trust` / `audit-miracles` / `foreshadow-audit` / `audit-conformance` out to `python -m freakc <subcommand>` (native FREAK port lands with V4)
- `build_cli.bat`, `.github/workflows/ci.yml`, `.github/workflows/release.yml` — added `src/cli/audit.fk` to the cat chain so `cli_audit_dispatch` resolves at link time

### Compiler fixes
- **Maybe / Result compound-literal cast** — `freakc/emitter.py` now wraps `some(...)`, `nobody`, `ok(...)`, `err(...)` in `(freak_maybe_T)` / `(freak_result_T_word)` casts so the literal is valid in assignment context, not just declaration initializers. `_infer_c_type_of_expr` extended to pick the right T per inner type.
- **Pipe operator** — pipe desugaring in `_emit_binop` now synthesizes a `Call` node and dispatches through `_emit_call`, so user-function `freak_` prefixing applies. Type checker grew a `|>` short-circuit that bumps expected arity by 1 (the LHS injection) instead of falsely flagging arity mismatches.
- **Ord operator doctrine** — `<`, `>`, `<=`, `>=` mapped to `Ord/lt`, `Ord/gt`, `Ord/le`, `Ord/ge` in the Python emitter's `_OP_DOCTRINE` table. `tests/ord_doctrine_test.fk` covers all four.

### Test suite
- `tests/suite/test_maybe.fk` and `tests/suite/test_pipe.fk` un-skipped — both PASS
- `freak test` shim added in `src/cli/main.fk` — wraps `python tests/suite/run_tests.py` (in-language `test "..." { expect ... }` framework lands with V4)
- Suite at **14 passed, 0 failed, 0 skipped** (verified against the tree: 14 `test_*.fk` files under `tests/suite/`, 0 `SKIP:` directives)

### LB10 minimal DWARF
- `src/compiler/v3/emit_llvm.fk:llvm_dbg_begin_func` flipped on: now emits a DISubprogram per function, sets the current scope, and returns `!dbg !N` for the function attribute. Per-instruction `!dbg` annotations were already wired in `llvm_emit_line` — they just needed the scope id.
- Compile-unit emission kind changed from `FullDebug` to `LineTablesOnly` to keep the metadata footprint bounded
- Source-line backtraces in gdb/lldb work today; full DWARF (variables, types) ships with V4

### Distribution
- D6 Homebrew formula (`packaging/homebrew/freak.rb`) — release workflow patches checksums on tag
- D7 Scoop manifest (`packaging/scoop/freak.json`) — release workflow patches checksums + version on tag
- D7 Winget manifests (`packaging/winget/manifests/F/FREAK/freak/<version>/`) — 0.13.2 manifest tracked, 0.13.3 manifest added; `release.yml` path made dynamic from `$VERSION` so future bumps just need the new subdirectory
- v0.13.3 release shipped clean: 4-platform binary matrix, 13 release assets

### What's left for v0.13.x
Nothing in scope. v0.13.x final patch is on `main` and tagged at v0.13.3. The remaining bible promises (variants, `mood`/`prob`/`power`/`causality`, full borrow checker, squadron concurrency, FFI surface, error-voice routing, JIT/LB7, in-language `test` framework, COCKPIT MG accessibility/polish) all ship with **V4**.

V4 work is now landing on `main` — see commits prefixed `Add V4 …` for the latest. As V4 features land, promote the matching rows in `freak-full-bible.md` §0.2 and `freak-conformance-audit.md` from 🔜 to ⚠️/✅, and grow the matching check in `freakc/auditor.py:audit_conformance`.

---

## STATUS NOTE — v0.14.x (2026-09-12)

Phases 0–7 above are complete: boxes checked against the shipped bootstrap
(`freakc/` lexer/parser/emitter/type-checker, `freakc/runtime/freak_runtime.h`,
`tests/hello.fk`, `run.sh`, the `freak run/build/check/test` CLI) and this
file's own M1–M10 milestone record.

- Next Campaign wave-1 merged: PR #109 (`2147d91`) — lists, parsing, targets, diagnostics, docs.
- Next Campaign wave-2 merged: PR #112 (`e6e5aea`) — conversions, benchmarks, response seed, leftovers; shipped `word += word`.
- Default PR merge method is now rebase-merge: PR #110 (`935bda7`).
- Issues closed with evidence: #103, #105, #106, #108. #87 deferred (still open; ASan-revert verdict recorded). #104 open (needs V4 design).
- v0.14.1 "Maverick" tagged; v0.14.2 in prep: PR #115 (`VERSION` 0.14.2).
