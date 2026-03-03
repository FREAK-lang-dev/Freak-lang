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
- [ ] `when` → switch (int) or strcmp chain (word)
- [ ] `for each x in list` → C for loop
- [ ] `repeat N times` → C for loop
- [ ] `training arc` → C while with session counter
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
- [ ] Anime operators → C expressions (Bible Section 2.12)
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
- [ ] `freak vibe file.fk` — Opus vibe analysis
- [ ] `--output / -o` flag
- [ ] `--keep-c` flag (keep emitted C for debugging)
- [ ] `--voice` flag (yuuko / meiya / sumika / mana)
- [ ] Friendly errors: filename, line number, highlighted bad line

---

## PHASE 8 — Opus API Integration

- [ ] `pip install anthropic`
- [ ] `opus.py` with API client (`ANTHROPIC_API_KEY` from env)
- [ ] `check_death_flags(ast_node, context)` → JSON response
- [ ] `generate_narrative_error(error_type, details, voice)` → string
- [ ] `analyze_vibe(source_code)` → vibe report string
- [ ] Response caching keyed by hash(input)
- [ ] Graceful fallback if API fails or times out
- [ ] `freak audit-science` — list all `for science` calls
- [ ] `freak audit-trust` — list all `trust me` blocks with honor levels

---

## PHASE 9 — Hangar Package Manager (v1)

- [ ] `hangar.toml` parsing (use `tomllib`, built-in since Python 3.11)
- [ ] `freak hangar init` — project skeleton + hangar.toml
- [ ] `freak hangar install` — download deps to `hangar_cache/`
- [ ] `freak hangar add [package]` — add dep + update hangar.toml
- [ ] Basic registry: GitHub releases is fine for v1
- [ ] Resolve `use muvluv::{}` imports to downloaded files

---

## PHASE 10 — muvluv Package (Official)
*The flagship Hangar package. You maintain this.*

- [ ] `Eishi` type: name, power, status, callsign
- [ ] `BETA::Tier` enum: Soldier → Grappler → Destroyer → Tank → Laser → Fort → BRAIN
- [ ] `Tier::required_power()` method
- [ ] `TSF` type: model, variant, mounted_weapon, os_version
- [ ] `COSMO` module: request_strike() (stub — prints confirmation)
- [ ] `YuukoLab` helpers for @experiment scaffolding
- [ ] Write the BETA early warning system as the showcase example
- [ ] Publish to Hangar registry

---

## MILESTONES

```
[ ] M1  — hello.fk compiles and runs              (Phase 0-3)
[ ] M2  — variables, tasks, if/when/loops all work (Phase 5 partial)
[ ] M3  — closures and pipes work
[ ] M4  — maybe<T> and result<T,E> fully work
[ ] M5  — type checker catching real errors        (Phase 6)
[ ] M6  — `freak run` CLI works end-to-end         (Phase 7)
[ ] M7  — Opus error voices working                (Phase 8)
[ ] M8  — muvluv installable via Hangar            (Phase 9-10)
[ ] M9  — BETA early warning system runs in FREAK
[ ] M10 — GitHub repo public, README written       ← tell people
```

---

## QUICK TIPS

**How to use Opus when building:**
Paste `freak-lite-bible.md` into the context window first.
Then ask for one phase at a time. e.g.:
- *"Write the Python Lexer class for FREAK based on Section 6 of this spec"*
- *"Write the C emitter for closures based on Section 2.6 of this spec"*

**The one rule:**
Get M1 working before doing anything else.
A running Hello World beats a perfect unfinished type checker every time.
