# CLAUDE.md — FREAK Language Project
## Context & Continuity Guide for AI Sessions

> This file gives any Claude session everything it needs to continue work on the FREAK project without re-reading every spec file from scratch. It is a living document — update it when significant decisions are made or milestones are completed.

---

## What Is FREAK?

**FREAK** is a compiled, statically-typed, memory-safe systems programming language with syntax and aesthetics inspired by anime and visual novels. It is intentionally weird and the weirdness is load-bearing — the naming, the keywords, the error system, the themes — all of it is part of the design, not decoration.

Key facts:
- Files use the `.fk` extension
- The authoritative spec is `freak-full-bible.md` — if code disagrees with the bible, **the bible wins**
- Version name: **Alternative-4 Edition**
- The self-hosting compiler (`freakc_self.exe`) is a major credibility milestone and should be prominently featured in public materials

---

## The Ecosystem

| Component | Description | Status |
|---|---|---|
| **FREAK** | Core language, `.fk` files | ✅ Self-hosting |
| **Hangar** | Package manager (`hangar.toml`) | ✅ v1 working |
| **freak-ui** | Immediate-mode UI framework | 🚧 In progress (MA–MG track) |
| **HFML** | Hyper-Freak Markup Language (like Blazor/Razor, compiles to freak-ui) | 📐 Planned (MH0–MH9) |
| **CFS** | Cascading Freak Sheets (CSS-inspired, compiles to freak-ui Theme structs) | 📐 Roadmapped |
| **FreakScript** | Lighter GC'd sibling (JS to FREAK's Java), browser/embeddable runtimes | 📐 Specced (`freakscript-bible.md`) |
| **PEAK** | "Pure Expression, Anime Kernel" — fully independent functional language, immutability-first | 📐 Roadmapped |
| **Sortie** | JetBrains-style IDE written in FREAK, with FREAK-specific tooling | 📐 Specced (`sortie-ide-spec.md`) |
| **NEXUS** | Native game framework, scene/actor/stage vocabulary | 📐 Roadmapped |
| **SIGNAL** | Full-stack web framework, end-to-end type sharing FREAK ↔ FreakScript | 📐 Roadmapped |
| **freak-pilot** | FREAK-specialized coding assistant (long-term, needs community/dataset) | 🔮 Future |

> **PEAK is a fully independent language, not a transpiler to FREAK.** This distinction matters for architecture decisions.

> **HFML codegen requires freak-ui Phase C to be complete.** Lexer/parser work can proceed independently.

---

## Repository Structure

```
Freak-lang/
├── freakc/                    # Python → C transpiler (v1 compiler)
│   ├── __main__.py            # Entry: python -m freakc file.fk
│   ├── lexer.py
│   ├── parser.py
│   ├── checker.py             # Type checker
│   ├── emitter.py             # C emitter (primary backend)
│   ├── auditor.py             # Audit commands (science/trust/miracles/foreshadow)
│   └── runtime/
│       ├── freak_runtime.h    # Runtime type definitions
│       └── freak_runtime.c    # Runtime implementations
├── src/
│   └── compiler/              # Self-hosting compiler source (.fk files)
│       ├── main.fk
│       ├── lexer.fk
│       ├── parser.fk
│       ├── ast.fk
│       ├── checker.fk
│       ├── emitter.fk
│       └── backend/
│           └── llvm.fk        # LLVM IR backend (in progress)
├── self_hosted/               # Self-hosting bootstrap output
│   ├── main.fk                # Self-hosting compiler entry point
│   ├── freakc_self.exe        # Stage 1: Python-compiled self-hosting binary
│   ├── freakc_self2.exe       # Stage 2: Self-compiled binary (M15 achieved)
│   ├── muvluv/                # muvluv Hangar package
│   └── ui/                    # freak-ui prototype
├── build/
│   ├── compiler/              # Build artifacts
│   ├── freakc_v2.fk           # v2 compiler source
│   └── freakc_v2.exe
├── tests/                     # Test programs (.fk + compiled binaries)
│   ├── hello.fk               # Canonical hello world
│   ├── anime.fk
│   ├── closures.fk
│   ├── maybe.fk
│   ├── operator_overload.fk
│   ├── process.fk
│   ├── bytes.fk
│   ├── shapes.fk
│   ├── rpg_console.fk
│   └── ...
├── std/                       # Standard library stubs
├── packages/                  # Hangar packages
├── freak-full-bible.md        # ⭐ AUTHORITATIVE LANGUAGE SPEC
├── freak-todo.md              # Development checklist with milestone tracking
├── freak-distribution-llvm-plan.md  # LLVM backend + distribution strategy
├── freak-ui-plan.md           # freak-ui implementation plan
├── README.md                  # Public-facing README (M10 complete)
├── bootstrap.bat              # Windows self-hosting bootstrap script
├── run.sh                     # Linux/macOS run helper
└── CLAUDE.md                  # This file
```

**Docs generated so far** (in `.projects/` knowledge folder):
- `freak-docs.html` — full HTML docs site
- `freak-std.html` — standard library reference (11 modules documented)
- `freakscript-bible.md` — FreakScript spec
- `hfml-plan.md` — HFML implementation plan
- `sortie-ide-spec.md` — Sortie IDE spec
- `freak-future-roadmap.md` — CFS, PEAK, NEXUS, SIGNAL roadmap

---

## Milestone Status

### Core Milestones (M-series)

```
[x] M1  — hello.fk compiles and runs
[x] M2  — variables, tasks, if/when/loops all work
[x] M3  — closures and pipes work
[x] M4  — maybe<T> and result<T,E> fully work
[x] M5  — type checker catching real errors
[x] M6  — `freak run` CLI works end-to-end
[x] M7  — Audit commands (freak audit-science/trust/miracles/foreshadow-audit)
[x] M8  — muvluv installable via Hangar
[x] M9  — BETA early warning system runs in FREAK
[x] M10 — GitHub repo public, README written
[x] M11 — std::process, std::thread, std::bytes done
[x] M12 — operator overloading (Add/Sub/Mul/Div/Neg/Eq via doctrines)
[ ] M13 — freak-http and freak-json published to Hangar
[ ] M14 — freak-image and freak-zip exist
[x] M15 — self-hosting compiler bootstrap COMPLETE (freakc_self.exe compiles hello.fk)
[x] M16 — std::fs, std::math, std::time integrated in v2 compiler
```

### freak-ui Milestones (MA–MG track)
Pending — window system, layout engine, calculator app demo, five themes.

### HFML Milestones (MH0–MH9 track)
Pending — depends on freak-ui Phase C for codegen; lexer/parser can start earlier.

### LLVM Backend Milestones (LB-series) — NEXT PRIORITY
```
[ ] LB1  — LLVM IR emitter: hello world compiles via llc + lld
[ ] LB2  — All FREAK primitives map to LLVM types
[ ] LB3  — All control flow emits correct IR (if/when/loops)
[ ] LB4  — Shapes (structs) and impl methods work
[ ] LB5  — freak_runtime.h functions replaced by IR intrinsics
[ ] LB6  — freak build uses LLVM backend by default
[ ] LB7  — JIT mode: freak run executes via OrcJIT (no binary written)
[ ] LB8  — Optimization levels: --opt=0/1/2/3
[ ] LB9  — Cross-compilation: freak build --target x86_64-linux
[ ] LB10 — Debug info: source line numbers in DWARF via DIBuilder
```

---

## Compiler Architecture

### Current Pipeline (Python → C → native)

```
.fk source
    ↓  python -m freakc
    ↓  Lexer (lexer.py)       → tokens
    ↓  Parser (parser.py)     → AST
    ↓  Type Checker           → typed AST
    ↓  C Emitter (emitter.py) → .fk.c
    ↓  clang / MSVC           → native binary
```

**The C backend is not going away** — it becomes `freak build --target c` for portability.

### Target Pipeline (FREAK → LLVM IR → native)

```
.fk source
    ↓  Lexer / Parser (unchanged)
    ↓  Type Checker (unchanged)
    ↓  IR Lowering (freakc/ir/emitter.py)
    ↓  LLVM IR (.ll / bitcode)
    ↓  llc / opt
    ↓  LLD (LLVM's linker)
    native binary
```

Why LLVM: removes Clang dependency, enables JIT, direct DWARF debug info, proper LTO, cross-compilation built in. See `freak-distribution-llvm-plan.md` for full details.

**LLVM IR type mapping:**
| FREAK | LLVM IR |
|---|---|
| `int` | `i64` |
| `uint` | `i64` (unsigned semantics) |
| `num` | `double` |
| `tiny` | `i8` |
| `bool` | `i1` |
| `word` | `%freak_word = type { i8*, i64, i64 }` |
| `maybe<T>` | `%freak_maybe_T = type { i1, T }` |
| `result<T,E>` | `%freak_result_T_E = type { i1, T, E }` |
| `List<T>` | `%freak_list_T = type { T*, i64, i64 }` |
| `shape Foo {}` | `%Foo = type { fields... }` |

### Self-Hosting Compiler

The self-hosting compiler lives in `src/compiler/` (`.fk` sources) and `self_hosted/` (compiled artifacts).

Bootstrap sequence (`bootstrap.bat`):
1. **Stage 0** — Python `freakc` compiles `self_hosted/main.fk` → `freakc_self.exe`
2. **Stage 1** — `freakc_self.exe` compiles itself → `main.fk.c` → `freakc_self2.exe` (via clang)
3. **Stage 2** — `freakc_self2.exe` compiles `tests/hello.fk` → `hello_self.exe` ✅

**M15 is complete.** The self-hosting compiler can compile itself.

---

## Language Quick Reference

### Core Keywords

| FREAK | Meaning |
|---|---|
| `pilot` | variable declaration (`var`) |
| `fixed pilot` | immutable binding (`const`) |
| `task` | function declaration (`fn`/`func`) |
| `give back` | return |
| `say` | print (always available, no import) |
| `when` | pattern matching (`match`/`switch`) |
| `shape` | struct |
| `doctrine` | trait/interface |
| `impl` | implementation block |
| `trust-me` | unsafe block |
| `training arc` | bounded loop (compiler-verified termination) |
| `for each` | iterator loop |
| `repeat N times` | counted loop |
| `foreshadow` / `payoff` | narrative debt variables (must be resolved before scope end) |
| `deus_ex_machina` | dramatic escape hatch block (monologue ≥ 20 words required) |
| `isekai` | isolated fresh scope with `bringing back {}` exports |
| `eventually` | deferred execution block |
| `launch` | marks a task as public/exported |
| `done` | synonym for `}` |

### Type System

```
num          -- 64-bit float (default numeric, context-narrows to int)
int          -- 64-bit signed integer
uint         -- 64-bit unsigned integer
tiny         -- 8-bit unsigned (byte)
float        -- 64-bit IEEE 754
float32      -- 32-bit IEEE 754
big          -- arbitrary precision integer (never overflows)
word         -- UTF-8 string (fat pointer: data + byte_len + char_count)
bool         -- true/false/yes/no/hai/iie
char         -- Unicode scalar value (32-bit)
void         -- unit type
[T; N]       -- fixed-size array (stack)
(A, B, ...)  -- tuple
*T           -- raw pointer (trust-me blocks only)
*mut T       -- raw mutable pointer (trust-me blocks only)

maybe<T>     -- optional: some(42) | nobody
result<T,E>  -- success/failure: ok(val) | err("msg")
List<T>      -- dynamic array: [1, 2, 3]
Map<K,V>     -- hash map: { "key": value }
Set<T>       -- unique collection
Lineup<T>    -- FIFO queue
mood         -- .chill | .focused | .hype | .mono_no_aware | .muv_luv
prob[lo..hi] -- value constrained to probability range
power<N>     -- number guaranteed ≥ N at compile time
route        -- tagged union / enum with data
```

### Operator Overloading (via Doctrines)

Implemented in Phase 14. Emitter tracks `impl_doctrines` dict:
- `a + b` → `TypeName_add(&a, b)` when left type implements `Add`
- `a == b` → `TypeName_equals(&a, b)` when type implements `Eq`
- `word` implements `Add` for concatenation

Built-in operator doctrines: `Add`, `Sub`, `Mul`, `Div`, `Neg`, `Eq`, `Ord`, `Index`, `IndexMut`.

### String Interpolation

```fk
say "Hello, {name}! Power: {power}."
-- {expr} inside double-quoted strings
```

### Error Propagation

```fk
pilot data = fs::read(path)?   -- propagates err up, unwraps ok
pilot val = maybe_val or else default_val
```

### Concurrency

```fk
use std::thread::spawn
use std::sync::Channel

pilot (tx, rx) = Channel::new()
pilot handle = spawn(copy(tx) || {
    tx.send("message")
})
pilot msg = rx.recv()
handle.join()
```

Squadron model (structured concurrency) is preferred over raw `std::thread`. Use `std::thread` as the escape hatch.

### Annotations

```fk
@protagonist   -- main character (one per program)
@nakige        -- this will hurt (acknowledged sad content)
@experiment    -- scientific context
@season_finale -- one allowed per program
@deprecated    -- do not use
```

---

## Standard Library Modules

| Module | What it provides |
|---|---|
| `std::fs` | File I/O |
| `std::net` | TCP, UDP, HTTP client |
| `std::json` | Parse and serialize JSON |
| `std::thread` | Threads, atomics, channels |
| `std::math` | Everything `num` needs |
| `std::time` | Timestamps, durations, sleep |
| `std::process` | Spawn processes, read env, CLI args |
| `std::bytes` | `ByteBuffer` for binary I/O |
| `std::ui` | Native window, events, canvas |
| `std::anime` | Mood arithmetic, power checks |
| `std::narrative` | Death flags, foreshadow logs |
| `std::test` | Tests with vibes ratings |

`std::narrative` ships with the compiler. The `foreshadow_log.unpaid` field should be 0 at program end — this is a compiler warning if it isn't.

---

## CLI Commands

```bash
# Run via Python transpiler
python -m freakc build file.fk -o output.exe
python -m freakc run file.fk
python -m freakc check file.fk      # type check only
python -m freakc test               # run all test blocks
python -m freakc build file.fk --keep-c   # keep emitted C

# Audit commands (pure static analysis, no AI needed)
freak audit-science      # list every `for science,` call site
freak audit-trust        # list every `trust me` block with honor level
freak audit-miracles     # list every `deus_ex_machina` block (warns >3, errors >10)
freak foreshadow-audit   # show all foreshadow/payoff pairs and unpaid ones

# Hangar package manager
hangar init my-project
hangar add pkg-name https://github.com/...
hangar install
hangar remove pkg-name
```

### Bootstrap

```bat
# Windows — full self-hosting bootstrap
bootstrap.bat

# Linux/macOS — compile and run a .fk file
./run.sh file.fk
```

---

## Hangar Package Manager

`hangar.toml` format:

```toml
[project]
name = "my-project"
version = "0.1.0"

[dependencies]
freak-ui = { git = "https://github.com/yourname/freak-ui", version = "latest" }
muvluv   = { git = "https://github.com/FREAK-lang-dev/muvluv", version = "latest" }
```

Dependencies install to `hangar_modules/` (or `hangar_cache/` for downloaded deps).

**Hangar cannot bootstrap FREAK itself** — an external install script is the necessary distribution entry point. This is a known architectural constraint.

Long-term vision: Hangar becomes the universal entry point (Rustup model). `hangar install freak` fetches the compiler. `hangar upgrade freak` updates it. A tiny Python/Go bootstrapper is the short-term solution; a pre-compiled Hangar binary is the correct long-term approach.

---

## freak-ui Framework

Immediate-mode UI — no widget trees, no callbacks, no retained state. Call widget functions in order, frame renders.

```
Your FREAK app
     │
     ▼
freak-ui (Hangar)     ← widgets, layout, theming, input
     │
     ▼
std::ui               ← window, events, raw draw calls
     │
     ├── Windows: Win32 / Direct2D
     ├── macOS:   Cocoa / CoreGraphics
     └── Linux:   X11 / Cairo
```

### Themes

| Theme | Mood | Vibe |
|---|---|---|
| `Theme::default()` | `.focused` | Dark. Professional. Ready. |
| `Theme::light()` | `.chill` | Light. Calm. Readable. |
| `Theme::terminal()` | `.hype` | Green on black. Pure. |
| `Theme::alternative()` | `.muv_luv` | Navy and pink. Dangerous. |
| `Theme::muvluv()` | `.mono_no_aware` | Red and black. You know what you've done. |

---

## muvluv Package (Official Flagship)

The flagship Hangar package. Located in `self_hosted/muvluv/`. Installable via Hangar (M8 complete).

Key types:
- `Eishi` — name, power, status, callsign
- `BETA::Tier` — Soldier → Grappler → Destroyer → Tank → Laser → Fort → BRAIN
- `TSF` — model, variant, mounted_weapon, os_version
- `COSMO` module — `request_strike()` (orbital bombardment stub)
- `YuukoLab` — helpers for `@experiment` scaffolding

The **BETA early warning system** (M9) is the showcase program that uses this package.

---

## Distribution Strategy

See `freak-distribution-llvm-plan.md` for full detail.

### GitHub Releases Binary Matrix

Every tagged release builds:
- `freakc-linux-x64`, `freakc-linux-arm64`
- `freakc-macos-x64`, `freakc-macos-arm64`
- `freakc-windows-x64.exe`
- Same matrix for `hangar`
- `SHA256SUMS` checksum file

### Install Scripts (planned)

```bash
# Linux/macOS
curl -fsSL https://freak-lang.dev/install.sh | bash

# Windows
irm https://freak-lang.dev/install.ps1 | iex
```

Long-term: Homebrew formula, Scoop/Winget manifests.

---

## Testing

Test syntax:

```fk
test "addition works" {
    expect 2 + 2 to be 4
}

test "sad path" @nakige {
    expect character.survives_ending to be false
}
```

Test output includes a **vibes rating**:
```
✓ addition works
✓ sad path

vibes: MONO_NO_AWARE  (almost there. so close.)
```

Test files in `tests/` directory. Run with `python -m freakc test` or `freak test`.

---

## Build System Notes

### Windows (current dev environment)

- Compiler: `clang` (MSVC toolchain available, use clang for FREAK builds)
- Runtime: `freakc/runtime/freak_runtime.c` + `freak_runtime.h`
- Build command: `clang -o output.exe source.fk.c freakc/runtime/freak_runtime.c -Ifreakc/runtime -w -O3`
- Bootstrap: `bootstrap.bat`

### Known Issues

- `freakc_v2.c` fails to compile with clang due to MSVC deprecation warnings for `strerror`, `getenv` — add `-D_CRT_SECURE_NO_WARNINGS` or use `strerror_s`/`_dupenv_s` variants

### LLVM Backend Progress

The `src/compiler/backend/llvm.fk` file exists. Initial LLVM IR tests are in `tests/` (`.fk.ll` files for hello, control_flow, operators, shapes, strings). The IR emitter is partially working — `tests/control_flow.fk.ll` and `tests/hello.fk.ll` have been generated.

---

## Key Design Principles

1. **The anime/VN identity is load-bearing.** Not superficial. It must be preserved in all documentation, contribution guidelines, error messages, and tooling.

2. **The bible wins.** `freak-full-bible.md` is authoritative. If the compiler disagrees, fix the compiler.

3. **Self-hosting is the credibility signal.** M15 is done. Lead with this in all public communications.

4. **FreakScript retains FREAK's personality, drops systems complexity.** The JS-to-Java analogy is the guiding frame.

5. **PEAK is independent.** It is not a transpiler target for FREAK. It compiles separately.

6. **Hangar can't bootstrap itself.** Install script is the entry point. This is a known constraint, not a bug.

7. **Get M1 working before doing anything else.** (Done. But the principle stands for new features — a running minimal version beats a perfect unfinished one.)

---

## Pending High-Priority Work

In rough priority order:

1. **LLVM IR backend (LB1–LB10)** — removes Clang dependency, enables JIT, proper cross-compilation. Start with `LB1`: hello world through llc + lld.
2. **GitHub Actions CI/CD** — cross-compilation matrix, automated releases on tag push.
3. **Hangar bootstrapper** — tiny Python/Go script that downloads the freakc binary and sets up PATH.
4. **freak-ui Phase MA–MG** — window system, layout engine, calculator demo app.
5. **HFML lexer/parser (MH0–MH3)** — can start before freak-ui Phase C is done.
6. **M13: freak-http + freak-json** — publish as official Hangar packages.
7. **Sortie IDE Phase 1** — VS Code extension (parallel workstream after CI is set up).

---

## File Quick Reference

| File | What it is |
|---|---|
| `freak-full-bible.md` | ⭐ Complete authoritative language spec (Alternative-4) |
| `freak-todo.md` | Development checklist, all milestones |
| `freak-distribution-llvm-plan.md` | LLVM backend + Hangar bootstrapping + distribution |
| `freak-ui-plan.md` | freak-ui implementation plan (MA–MG) |
| `freakc/__main__.py` | Python compiler entry point |
| `freakc/emitter.py` | C code emitter |
| `freakc/runtime/freak_runtime.h` | C runtime type definitions |
| `freakc/runtime/freak_runtime.c` | C runtime implementations |
| `self_hosted/main.fk` | Self-hosting compiler main entry point |
| `self_hosted/freakc_self.exe` | Python-bootstrapped self-hosting binary |
| `tests/hello.fk` | Canonical hello world |
| `tests/rpg_console.fk` | Larger showcase program |
| `bootstrap.bat` | Full self-hosting bootstrap (Windows) |
| `run.sh` | Compile + run helper (Linux/macOS) |

---

*"It was always going to end this way."*
*— freak-ui mono_no_aware theme, on program exit*
