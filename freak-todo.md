# FREAK Lite — Development Checklist
**Language:** Python → transpiles to C  
**Goal:** Get FREAK source files compiling to native binaries via Clang/GCC  
**Reference:** freak-lite-bible.md for all syntax/mapping details

---

## PHASE 0 — Project Setup
*Do this first. Takes 20 minutes.*

- [ ] Create project folder structure
- [ ] Set up `__main__.py` so `python -m freakc file.fk` works
- [ ] Create `tests/hello.fk` — first target program:
  ```
  pilot name = "Takeru"
  pilot power = 9001
  say "Hello from FREAK! {name} has power {power}."
  ```
- [ ] Confirm Python 3.10+
- [ ] Create `run.sh`: compile → clang → execute in one command

---

## PHASE 1 — Lexer
*Source string → list of Token objects*

- [ ] Define `Token` dataclass: `type`, `value`, `line`, `col`
- [ ] Define `TokenType` enum (all types from Bible Section 6.1)
- [ ] Implement `Lexer` class with `tokenize(source: str) -> list[Token]`
- [ ] Whitespace skipping, line number tracking
- [ ] `--` line comments (skip to end of line)
- [ ] Integer literals: `42`, `0xFF`, `0b1010`
- [ ] Float literals: `3.14`
- [ ] String literals `"..."` with `{interp}` markers
- [ ] Bool literals: `true`, `false`, `yes`, `no`, `hai`, `iie`
- [ ] Single-char tokens: `{ } ( ) [ ] , : . @ _`
- [ ] Multi-char operators: `-> => |> :: == != <= >= ** += -= *= /=`
- [ ] Identifiers and keywords (keyword list from Bible 6.1)
- [ ] Multi-word keywords (lex greedily):
  - `give back`, `or else`, `trust me`, `for each`
  - `training arc`, `on my honor as`
  - `knowing this will hurt`, `for science`
  - `PLUS ULTRA`, `FINAL FORM`
- [ ] `done` keyword as synonym for `}`
- [ ] TEST: tokenize `hello.fk`, print all tokens, visually verify

---

## PHASE 2 — Parser
*Token list → Program AST*

- [ ] Define all AST dataclasses (Bible Section 7.1)
- [ ] Implement `Parser` class with `parse() -> Program`
- [ ] `pilot x = expr` variable declarations
- [ ] `pilot x: Type = expr` with type annotation
- [ ] `say expr` print statement
- [ ] String interpolation: extract `{expr}` spans
- [ ] Literals: int, float, bool
- [ ] Identifiers and field access `a.b.c`
- [ ] Binary operators with correct precedence
- [ ] Unary operators: `not`, `-`
- [ ] Function calls `f(a, b)`
- [ ] `task` declarations (block, arrow, done forms)
- [ ] `give back expr`
- [ ] `if / else if / else` blocks
- [ ] `when` pattern match with arms and `_`
- [ ] `for each x in y { }` loop
- [ ] `repeat N times { }` loop
- [ ] `shape Name { }` struct declaration
- [ ] `impl` blocks (with and without doctrine)
- [ ] `{ }` and `done` blocks (identical)
- [ ] `[1, 2, 3]` list literals
- [ ] `{ "key": value }` map literals
- [ ] `(a, b)` tuple literals and destructuring
- [ ] `|x| => expr` and `|x| { block }` lambdas
- [ ] Generic type expressions: `maybe<T>`, `result<T,E>`, `List<T>`
- [ ] `some(x)`, `nobody`, `ok(x)`, `err(x)`
- [ ] `check expr { got x -> ... nobody -> ... }`
- [ ] `check result expr { ok(x) -> ... err(e) -> ... }`
- [ ] `expr?` error propagation
- [ ] `expr or else expr` fallback
- [ ] `use module::{items}` imports
- [ ] `launch` modifier
- [ ] `@annotation` annotations
- [ ] `trust me "msg" on my honor as .level { }`
- [ ] `training arc until cond max N sessions { }`
- [ ] `foreshadow pilot x = expr` and `payoff x`
- [ ] `knowing this will hurt, call()` and `sadly call()`
- [ ] `for science, call()`
- [ ] Anime operators as binary ops
- [ ] TEST: parse `hello.fk`, pretty-print AST, visually verify

---

## PHASE 3 — Minimal C Emitter (Hello World target)
*AST → C source string. Skip type checker. Get something running.*

- [ ] `CEmitter` class with `emit(program: Program) -> str`
- [ ] Emit `#include "freak_runtime.h"`
- [ ] Emit `int main() { freak_main(); return 0; }`
- [ ] `pilot x = 42` → `int64_t x = 42;`
- [ ] `pilot x = "hello"` → `freak_word x = freak_word_lit("hello");`
- [ ] `pilot x = true` → `bool x = true;`
- [ ] `say "Hello {name}!"` → `freak_say(freak_interpolate(...));`
- [ ] `task f(a: int) -> int { give back a; }` → C function
- [ ] Function forward declarations before definitions
- [ ] **★ MILESTONE: hello.fk compiles and runs ★**

---

## PHASE 4 — Runtime Header (freak_runtime.h)

- [ ] `freak_word` struct: data pointer + byte_length + char_count
- [ ] `freak_word_lit(const char* s)`
- [ ] `freak_say(freak_word msg)` — print with newline
- [ ] `freak_ask(freak_word prompt)` — read stdin
- [ ] `freak_interpolate(...)` — handle `{x}` substitution
- [ ] `freak_word_concat`, `freak_word_eq`
- [ ] `freak_word_from_int`, `freak_word_from_double`
- [ ] `freak_panic(freak_word msg)` — print + exit(1)
- [ ] Generated `freak_maybe_T` structs per type used
- [ ] Generated `freak_result_T_E` structs per type combo used
- [ ] Generated `freak_list_T` structs with push/get/length/filter/map/fold

---

## PHASE 5 — Full C Emitter

- [ ] `if / else if / else` → C if/else
- [x] `when` → switch (int) or strcmp chain (word)
- [ ] `for each x in list` → C for loop
- [ ] `repeat N times` → C for loop
- [x] `training arc` → C while with session counter
- [ ] `shape` → C typedef struct (topologically sorted)
- [ ] `impl` methods → C functions with shape pointer first arg
- [ ] Closures → capture struct + function pointer (Bible Section 2.6)
- [ ] `|>` pipe → desugar to nested calls or temp vars
- [ ] `?` operator → inline result check + early return
- [ ] `check` (maybe) → if/else on has_value
- [ ] `check result` → if/else on is_ok
- [ ] `or else` → ternary fallback
- [ ] `some/nobody/ok/err` → macro calls
- [ ] List literals → new() + push calls
- [ ] Destructuring → temp var + field assignments
- [ ] `launch` → non-static; no launch → static
- [ ] `trust me` → plain C block + compile-time log
- [ ] `foreshadow/payoff` → C comments + symbol table tracking
- [ ] Annotations → C comments
- [ ] `knowing this will hurt` / `sadly` / `for science` → strip prefix, call normally
- [ ] `route` return type → generated enum + tagged union
- [x] Anime operators → C expressions (Bible Section 2.12)
- [ ] Generics → monomorphise per concrete type used

---

## PHASE 6 — Type Checker

- [ ] Symbol table: variables and types per scope
- [ ] Type inference for all literals (Bible Section 8.3)
- [ ] All referenced variables declared before use
- [ ] Function call argument counts match signature
- [ ] Explicit annotations consistent with inferred types
- [ ] `give back` type matches task return type
- [ ] `check` only on `maybe<T>` values
- [ ] `check result` only on `result<T,E>` values
- [ ] `?` only inside result-returning tasks
- [ ] `foreshadow` variables paid off before scope ends
- [ ] `@nakige` tasks called with acknowledgement
- [ ] Only ONE `@season_finale` per program
- [ ] Annotate every AST node with resolved type
- [ ] Clear, line-numbered error messages

---

## PHASE 7 — CLI

- [ ] `freak run file.fk` — compile and run
- [ ] `freak build file.fk` — compile to binary
- [ ] `freak check file.fk` — type check only
- [ ] `freak test` — run all test blocks
- [ ] `--output / -o` flag
- [ ] `--keep-c` flag (keep emitted C for debugging)
- [ ] Friendly errors: filename, line number, highlighted bad line

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
- Suite at **14 passed, 0 failed, 0 skipped**

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
