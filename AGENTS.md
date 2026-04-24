# AGENTS.md — FREAK Language Project
## Context & Continuity Guide for AI Sessions

> This file gives any Codex session everything it needs to continue work on the FREAK project without re-reading every spec file from scratch. It is a living document — update it when significant decisions are made or milestones are completed.

---

## Git Commit Policy

**Commit after every significant change.** Do not let work accumulate uncommitted. Specifically:

- **Always commit after**: completing a milestone, fixing a compiler bug, adding a new runtime function, adding a new CLI subcommand, updating CI/release workflows, changing the build system, or any change that took more than ~15 minutes of work.
- **Commit message style**: short imperative summary line, then blank line, then bullet points if needed. Example: `Add process::exec and process::exec_capture to runtime`
- **Stage specific files** — avoid `git add -A`. Never commit `.env`, credentials, or multi-GB build artifacts.
- **Before starting risky work** (refactors, parser changes, emitter rewrites): make sure the current state is committed so you can revert if needed.
- **After a successful build/test cycle**: if you just verified something works end-to-end, that's a natural commit point. Don't wait.
- **Commit automatically** — do not ask for permission before committing. Just commit after completing significant work. Push silently when appropriate.
- **No AI attribution** — do NOT include `Co-Authored-By` trailers or any other AI/Codex attribution in commit messages. Commits should look like they came from the repo owner alone.

The cost of committing too often is zero. The cost of losing work because you forgot to commit is real — it has happened before on this project.

---

## What Is FREAK?

**FREAK** is a compiled, statically-typed, memory-safe systems programming language with syntax and aesthetics inspired by anime and visual novels. It is intentionally weird and the weirdness is load-bearing — the naming, the keywords, the error system, the themes — all of it is part of the design, not decoration.

Key facts:
- Files use the `.fk` extension
- The authoritative spec is `freak-full-bible.md` — if code disagrees with the bible, **the bible wins**
- Version name: **Alternative-4 Edition** — current release **v0.13.2 "Shiranui"**
- The self-hosting compiler (`freakc_self.exe`) is a major credibility milestone and should be prominently featured in public materials

---

## Task Log

- **2026-04-24**: Updated project version to v0.13.2 across documentation (README.md, AGENTS.md, CLAUDE.md) and packaging manifests.

---

## The Ecosystem

| Component | Description | Status |
|---|---|---|
| **FREAK** | Core language, `.fk` files | ✅ Self-hosting |
| **Hangar** | Package manager (`hangar.toml`) | ✅ v2 native FREAK |
| **COCKPIT** | Immediate-mode UI framework for FREAK (official public name; replaces freak-ui) | 🚧 In progress (MA–MG track) |
| **HFML** | Hyper-Freak Markup Language (like Blazor/Razor, compiles to COCKPIT) | 📐 Planned (MH0–MH9) |
| **CFS** | Cascading Freak Sheets (CSS-inspired, compiles to COCKPIT Theme structs) | 📐 Roadmapped |
| **FreakScript** | Lighter GC'd sibling (JS to FREAK's Java), browser/embeddable runtimes | 📐 Specced (`freakscript-bible.md`) |
| **PEAK** | "Pure Expression, Anime Kernel" — fully independent functional language, immutability-first | 📐 Roadmapped |
| **Sortie** | JetBrains-style IDE written in FREAK, with FREAK-specific tooling | 📐 Specced (`sortie-ide-spec.md`) |
| **NEXUS** | Native game framework, scene/actor/stage vocabulary | 📐 Roadmapped |
| **SIGNAL** | Full-stack web framework, end-to-end type sharing FREAK ↔ FreakScript | 📐 Roadmapped |
| **freak-pilot** | FREAK-specialized coding assistant (long-term, needs community/dataset) | 🔮 Future |

> **PEAK is a fully independent language, not a transpiler to FREAK.** This distinction matters for architecture decisions.

> **HFML codegen requires COCKPIT Phase C to be complete.** Lexer/parser work can proceed independently.

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
│   ├── compiler/              # Self-hosting compiler source (.fk files)
│   │   ├── main.fk
│   │   ├── lexer.fk
│   │   ├── parser.fk
│   │   ├── ast.fk
│   │   ├── checker.fk
│   │   ├── emitter.fk
│   │   └── backend/
│   │       └── llvm.fk        # LLVM IR backend
│   └── cli/                   # Native CLI (replaces Python CLI)
│       ├── main.fk            # CLI entry point, subcommand dispatch
│       ├── build.fk           # Compile pipeline (transpile + clang)
│       ├── run.fk             # Build + execute
│       ├── version.fk         # Version display and help
│       ├── toml.fk            # TOML parser/writer for hangar.toml
│       └── hangar.fk          # Package manager (init/add/remove/install/version)
├── self_hosted/               # Self-hosting bootstrap output
│   ├── main.fk                # Self-hosting compiler entry point
│   ├── freakc_self.exe        # Stage 1: Python-compiled self-hosting binary
│   ├── freakc_self2.exe       # Stage 2: Self-compiled binary (M15 achieved)
│   ├── muvluv/                # muvluv Hangar package
│   └── ui/                    # COCKPIT prototype
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
├── freak-ui-plan.md           # COCKPIT implementation plan
├── .github/
│   └── workflows/
│       ├── ci.yml             # CI: test on push/PR (3 platforms)
│       └── release.yml        # Release: build binaries on tag push (4 platforms)
├── README.md                  # Public-facing README (M10 complete)
├── bootstrap.bat              # Windows self-hosting bootstrap script
├── run.sh                     # Linux/macOS run helper
├── install.sh                 # Linux/macOS installer (curl | bash)
├── install.ps1                # Windows installer (irm | iex)
└── AGENTS.md                  # This file
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
[x] M13 — freak-http and freak-json published to Hangar
[ ] M14 — freak-image and freak-zip exist
[x] M15 — self-hosting compiler bootstrap COMPLETE (freakc_self.exe compiles hello.fk)
[x] M16 — std::fs, std::math, std::time integrated in v2 compiler
```

### COCKPIT Milestones (MA–MG track)
```
[x] MA  — Window system (std::ui platform abstraction + Win32 backend, emitter wired)
[x] MB  — Layout engine (flex-like immediate-mode layout)
[x] MC  — Widget library (buttons, labels, text input, sliders, checkbox)
[x] MD  — Theming system (5 themes: default/light/terminal/alternative/muvluv)
[x] ME  — Extended widgets (dropdown, tabs, progress bar, tooltip, modal, scroll area)
[x] MF  — Animation system (delta_time, easing functions, tween system)
[ ] MG  — Polish and publish COCKPIT to Hangar
```

### HFML Milestones (MH0–MH9 track)
Pending — depends on COCKPIT Phase C for codegen; lexer/parser can start earlier.

### LLVM Backend Milestones (LB-series)
```
[x] LB1  — LLVM IR emitter: hello world compiles via clang
[x] LB2  — All FREAK primitives map to LLVM types
[x] LB3  — All control flow emits correct IR (if/when/loops/break/continue)
[x] LB4  — Shapes (structs) and impl methods work
[x] LB5  — freak_runtime.h functions replaced by IR intrinsics (platform-dependent C remains: stdin, popen, sockets, UI)
[x] LB6  — freak build uses LLVM backend by default
[ ] LB7  — JIT mode: freak run executes via OrcJIT (no binary written)
[x] LB8  — Optimization levels: --opt=0/1/2/3
[x] LB9  — Cross-compilation: freak build --target x86_64-linux
[ ] LB10 — Debug info: source line numbers in DWARF via DIBuilder
```

### Distribution Milestones (D-series)
```
[x] D1  — GitHub Actions CI on Linux/macOS/Windows
[x] D2  — Release workflow: 4-platform binary matrix on tag push
[x] D3  — v0.8.0 released with downloadable binaries
[x] D4  — Install scripts: install.sh (Linux/macOS) + install.ps1 (Windows)
[x] D5  — Hangar bootstrap: hangar install freak / hangar upgrade freak
[ ] D6  — Homebrew formula
[ ] D7  — Scoop/Winget manifests
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

| Module | What it provides | Status |
|---|---|---|
| `std::math` | abs, min, max, clamp, pow, sqrt, gcd, lcm, factorial, fibonacci | ✅ Pure FREAK |
| `std::math3d` | Vector2/3/4, Matrix4x4, dot/cross/normalize, transforms | ✅ Pure FREAK |
| `std::string` | starts_with, ends_with, contains, trim, replace, substring, index_of | ✅ Pure FREAK |
| `std::convert` | int_to_hex/bin/oct, char_to_digit, bool_to_word | ✅ Pure FREAK |
| `std::algorithm` | sort, binary_search, find, contains, reverse, copy, unique, sum/max/min | ✅ Pure FREAK |
| `std::json` | Parse and serialize JSON (recursive descent, value pool) | ✅ Pure FREAK |
| `std::http` | HTTP/1.1 client (GET/POST/PUT/DELETE) over TCP sockets | ✅ Pure FREAK + C runtime |
| `std::zip` | ZIP archive read/write for text entries | ✅ Pure FREAK + external backend |
| `std::fs` | File I/O | ✅ C runtime |
| `std::process` | Spawn processes, read env, CLI args | ✅ C runtime |
| `std::time` | Timestamps, durations, sleep | ✅ C runtime |
| `std::bytes` | `ByteBuffer` for binary I/O | ✅ C runtime |
| `std::thread` | Threads, atomics, channels | 📐 Planned |
| `std::net` | TCP, UDP sockets (low-level) | ✅ C runtime |
| `std::ui` | Native window, events, canvas | 🚧 In progress |
| `std::anime` | Mood arithmetic, power checks | 📐 Planned |
| `std::narrative` | Death flags, foreshadow logs | 📐 Planned |
| `std::test` | Tests with vibes ratings | 📐 Planned |

`std::narrative` ships with the compiler. The `foreshadow_log.unpaid` field should be 0 at program end — this is a compiler warning if it isn't.

---

## CLI Commands

```bash
# Native CLI (build/freak.exe)
freak build file.fk              # compile to native binary (default: LLVM backend)
freak build file.fk --c          # compile using C backend
freak build file.fk --opt=3      # set optimization level
freak build file.fk --target=x86_64-linux-gnu  # cross-compile
freak run file.fk                # build and execute
freak check file.fk              # type check only
freak transpile file.fk          # transpile only (emit .c or .ll)
freak --version                  # show version
freak help                       # show help

# Hangar package manager (standalone or via freak)
hangar init                       # create project skeleton + hangar.toml
hangar add pkg repo               # add dependency
hangar remove pkg                 # remove dependency
hangar install                    # install all dependencies
hangar install freak              # download freak binary
hangar version                    # show project version
hangar version patch              # bump patch version
# Also available as: freak hangar <cmd>

# Legacy Python CLI (still available as bootstrap)
python -m freakc build file.fk
python -m freakc run file.fk

# Audit commands (Python CLI only, not yet in native CLI)
freak audit-science
freak audit-trust
freak audit-miracles
freak foreshadow-audit
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
cockpit = { git = "https://github.com/yourname/cockpit", version = "latest" }
muvluv   = { git = "https://github.com/FREAK-lang-dev/muvluv", version = "latest" }
```

Dependencies install to `hangar_modules/` (or `hangar_cache/` for downloaded deps).

**Hangar cannot bootstrap FREAK itself** — an external install script is the necessary distribution entry point. This is a known architectural constraint.

Long-term vision: Hangar becomes the universal entry point (Rustup model). `hangar install freak` fetches the compiler. `hangar upgrade freak` updates it. A tiny Python/Go bootstrapper is the short-term solution; a pre-compiled Hangar binary is the correct long-term approach.

---

## COCKPIT Framework

Immediate-mode UI — no widget trees, no callbacks, no retained state. Call widget functions in order, frame renders.

```
Your FREAK app
     │
     ▼
COCKPIT (Hangar)      ← widgets, layout, theming, input
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

### Install Scripts (working)

```bash
# Linux/macOS
curl -fsSL https://raw.githubusercontent.com/FREAK-lang-dev/Freak-lang/main/install.sh | bash

# Windows
irm https://raw.githubusercontent.com/FREAK-lang-dev/Freak-lang/main/install.ps1 | iex

# Via Hangar (if you already have Python + freakc)
python -m freakc hangar install freak
python -m freakc hangar upgrade freak
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

### Version String (hardcoded — update before tagging releases!)

The version is hardcoded in **two files** that must be updated together before tagging a release:

- `src/cli/version.fk` → `pilot CLI_VERSION = "0.13.2"` and `CLI_CODENAME = "Shiranui"` (shown by `freak version`)
- `src/compiler/v3/globals.fk` → `pilot FREAKC_VERSION = "0.13.2"` and `FREAKC_CODENAME = "Shiranui"` (shown by `freakc_v3 --version`)

If you forget, the installed binary will report the old version even though the release tag is newer. This has happened before (v0.10.0 shipped reporting 0.9.0).

### LLVM Backend Progress (V3 — current default)

The V3 LLVM IR backend (`src/compiler/v3/emit_llvm.fk`) is the **default** backend as of v0.13.2. The pipeline is:

```
.fk source → V3 compiler (freakc_v3.exe) → .ll → clang/lld → native binary
```

Bootstrap: `build_cli.bat` (Windows) or CI workflow. Pre-compiled bootstrap at `build/freakc_v3.fk.c`.

**Working features:** all control flow, shapes/impl, arrays (LLVM-compatible pool), string methods, fs::read/write/append/exists/delete (via std/runtime.fk), process, math, UI, TCP, JSON, HTTP.

**Runtime:** LLVM builds link `freak_llvm_runtime.c` (libc wrappers, LLVM-compatible array pool, time, process_exec_capture) + `freak_runtime.c` (word/string methods, C-backend arrays — separate pool).

**Not yet implemented:** JIT (LB7), debug info (LB10).

---

## Key Design Principles

1. **The anime/VN identity is load-bearing.** Not superficial. It must be preserved in all documentation, contribution guidelines, error messages, and tooling.

2. **The bible wins.** `freak-full-bible.md` is authoritative. If the compiler disagrees, fix the compiler.

3. **Self-hosting is the credibility signal.** M15 is done. Lead with this in all public communications.

4. **FreakScript retains FREAK's personality, drops systems complexity.** The JS-to-Java analogy is the guiding frame.

5. **PEAK is independent.** It is not a transpiler target for FREAK. It compiles separately.

6. **Hangar can now bootstrap FREAK.** `hangar install freak` downloads the compiler. Install scripts are the entry point for first-time users without Python.

7. **Get M1 working before doing anything else.** (Done. But the principle stands for new features — a running minimal version beats a perfect unfinished one.)

---

## Pending High-Priority Work

In rough priority order:

1. ~~**LLVM IR backend (LB1–LB4)**~~ — ✅ Done.
2. ~~**GitHub Actions CI/CD**~~ — ✅ Done.
3. ~~**Hangar bootstrapper**~~ — ✅ Done.
4. ~~**Native CLI rewrite**~~ — ✅ Done. `build/freak.exe` replaces `python -m freakc`. Includes compiler + CLI + Hangar + semver library in a single ~450KB binary. `hangar.exe` is a BusyBox-style copy that dispatches to package manager mode.
5. ~~**LLVM IR backend (LB5, LB7, LB10)**~~ — ~~LB5 (runtime intrinsics)~~, ~~LB6 (default backend)~~, ~~LB8 (opt levels)~~, ~~LB9 (cross-compilation)~~ done. **LB7 (JIT)** and **LB10 (debug info)** remain.
6. ~~**COCKPIT Phase MA–MF**~~ — ✅ Done. Window system, layout, widgets (core + extended), themes, animation. **MG (polish + Hangar publish)** remains.
7. **HFML lexer/parser (MH0–MH3)** — can start before COCKPIT Phase C is done.
8. ~~**M13: freak-http + freak-json**~~ — ✅ Done. std::json (pure FREAK) + std::http (TCP sockets + pure FREAK).
9. **Sortie IDE Phase 1** — VS Code extension.
10. ~~**Update CI/release workflows**~~ — ✅ Done. Workflows build `freak.exe` + `hangar.exe`. Install scripts updated with `runtime.fk`.

---

## Agent Teams (Parallel Development)

This project uses Codex agent teams to parallelize work. Enable with `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in `.Codex/settings.local.json` (already configured).

### How to Use

Ask Codex to create a team with 2–4 agents targeting independent work streams. Example:
```
Create a team: one agent works on X, another on Y, a third on Z.
```

### Parallelizable Sprint Ideas

These are groups of tasks that can safely run in parallel (no merge conflicts, independent subsystems):

**Sprint A — Language Features**
- Agent 1: **LB7 — JIT mode** (OrcJIT integration, `freak run` without writing a binary)
- Agent 2: **LB10 — DWARF debug info** (DIBuilder, source line mappings in IR)
- Agent 3: **M14 — freak-image + freak-zip** (new std library modules, pure FREAK + C runtime)

**Sprint B — UI Stack**
- Agent 1: **COCKPIT Phase MA completion** (wire extern declarations in emitter so std::ui calls compile)
- Agent 2: **COCKPIT Phase MB** (layout engine — flex-like immediate-mode positioning)
- Agent 3: **HFML lexer/parser (MH0–MH2)** (independent of COCKPIT runtime, just parsing)

**Sprint C — Tooling & Distribution**
- Agent 1: **Sortie IDE Phase 1** (VS Code extension — syntax highlighting, snippets, error lens)
- Agent 2: **D6 — Homebrew formula** + **D7 — Scoop/Winget manifests**
- Agent 3: **std::test framework** (test runner, vibes ratings, `freak test` command)

**Sprint D — Ecosystem Expansion**
- Agent 1: **FreakScript bootstrap** (lexer/parser from `freakscript-bible.md`, separate from FREAK compiler)
- Agent 2: **std::thread** (threads, atomics, channels — C runtime + FREAK wrappers)
- Agent 3: **std::anime + std::narrative** (mood arithmetic, death flags, foreshadow tracking)

**Sprint E — Compiler Hardening**
- Agent 1: **Error message improvements** (anime-themed diagnostics with source spans)
- Agent 2: **Compiler test suite** (automated regression tests for all language features)
- Agent 3: **Cross-platform CI validation** (ensure all tests pass on Linux/macOS/Windows)

### Guidelines

- Keep teams to 3–5 agents (token cost scales linearly)
- Each agent should work in a different directory/subsystem to avoid conflicts
- Commit after every significant change (per Git Commit Policy above)
- The team lead coordinates, reviews output, and resolves any conflicts

---

## File Quick Reference

| File | What it is |
|---|---|
| `freak-full-bible.md` | ⭐ Complete authoritative language spec (Alternative-4) |
| `freak-todo.md` | Development checklist, all milestones |
| `freak-distribution-llvm-plan.md` | LLVM backend + Hangar bootstrapping + distribution |
| `freak-ui-plan.md` | COCKPIT implementation plan (MA–MG) |
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
| `install.sh` | Linux/macOS binary installer |
| `install.ps1` | Windows binary installer |
| `.github/workflows/ci.yml` | CI workflow (3 platforms) |
| `.github/workflows/release.yml` | Release workflow (4 platform binaries) |
| `freakc/hangar.py` | Hangar package manager (Python, legacy) |
| `freakc/runtime/freak_llvm_runtime.c` | LLVM backend runtime |
| `src/cli/main.fk` | Native CLI entry point (replaces Python CLI) |
| `src/cli/build.fk` | CLI build pipeline (transpile + clang) |
| `src/cli/run.fk` | CLI run pipeline (build + execute) |
| `src/cli/toml.fk` | TOML parser/writer for hangar.toml |
| `src/cli/hangar.fk` | Hangar package manager (native FREAK) |
| `src/cli/version.fk` | Version display and help |
| `std/json.fk` | JSON parser and serializer (pure FREAK) |
| `std/http.fk` | HTTP/1.1 client (pure FREAK + TCP runtime) |
| `std/algorithm.fk` | Sort, search, aggregate algorithms (pure FREAK) |
| `std/convert.fk` | Type conversion utilities (pure FREAK) |
| `std/version.fk` | Semver library (parse, compare, bump, constraints) |
| `build_cli.bat` | Build script for native CLI binary |
| `build/freak.exe` | Native CLI binary (compiler + CLI + Hangar) |
| `build/hangar.exe` | Standalone package manager (BusyBox copy of freak.exe) |

---

*"It was always going to end this way."*
*— COCKPIT mono_no_aware theme, on program exit*
