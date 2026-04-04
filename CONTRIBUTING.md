# Contributing to FREAK

> *"The mission doesn't end just because you closed the PR."*

First of all — thank you. FREAK is a weird language and you chose to work on it anyway. That takes a certain kind of person. We respect that.

This document explains how to contribute to the FREAK compiler, standard library, runtime, CLI, Hangar package manager, and surrounding ecosystem.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [What Can I Work On?](#what-can-i-work-on)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Making Changes](#making-changes)
- [Commit Policy](#commit-policy)
- [Pull Request Guidelines](#pull-request-guidelines)
- [Language Design Contributions](#language-design-contributions)
- [The Identity Rule](#the-identity-rule)

---

## Code of Conduct

Be excellent to each other. This is a project built on earnestness and weird passion. Do not bring cynicism here.

Specifically:
- Criticism of code is welcome. Criticism of people is not.
- "This is a dumb feature" is not useful feedback. "This feature conflicts with X because Y" is.
- The anime/VN aesthetic is intentional and load-bearing. Do not try to strip it out.

---

## What Can I Work On?

Check `freak-todo.md` for the full milestone tracker. Open issues on GitHub for bugs and feature requests.

**Good first contributions:**
- Fixing a compiler bug with a clear repro case
- Adding a missing standard library function to an existing module
- Writing test `.fk` files for untested language features
- Improving error messages (anime-themed diagnostics are encouraged)
- Documentation fixes

**Larger contributions (discuss first):**
- New language features (open an issue before writing code — syntax changes require spec alignment)
- New standard library modules
- New CLI subcommands
- Changes to the LLVM IR backend
- freak-ui widget additions

**Do not:**
- Submit PRs that rename `pilot` to `var`, `task` to `fn`, or otherwise de-anime the language. This will be closed without comment.
- Add a feature that exists in the compiler but contradicts `freak-full-bible.md`. The bible wins. Fix the bible first via an issue.

---

## Getting Started

### Prerequisites

- Python 3.10+ (for the bootstrap compiler)
- `clang` in your PATH (for compiling generated C/LLVM IR)
- Git

### Setup

```bash
git clone https://github.com/FREAK-lang-dev/Freak-lang.git
cd Freak-lang

# Verify the Python compiler works
python -m freakc build tests/hello.fk -o tests/hello_test.exe
./tests/hello_test.exe
```

### Building the Native CLI

```bash
# Windows
build_cli.bat

# Verify
./build/freak.exe --version
```

### Running the Self-Hosting Bootstrap

```bash
# Windows only
bootstrap.bat
```

This produces `freakc_self.exe` (Python-compiled) and then `freakc_self2.exe` (self-compiled). If both produce the same output for `tests/hello.fk`, the bootstrap is clean.

---

## Project Structure

```
Freak-lang/
├── freakc/          # Python bootstrap compiler (v1)
│   └── runtime/     # C runtime: freak_runtime.h / .c / freak_llvm_runtime.c
├── src/
│   ├── compiler/    # Self-hosting compiler source (.fk files)
│   └── cli/         # Native CLI source (.fk files)
├── std/             # Standard library (.fk modules)
├── tests/           # Test programs
├── self_hosted/     # Self-hosting bootstrap output
├── build/           # Build artifacts (not committed, except key binaries)
├── packages/        # Hangar packages
└── .github/
    └── workflows/   # CI and release pipelines
```

The authoritative language specification is `freak-full-bible.md`. If the compiler behavior contradicts the spec, the spec is correct.

---

## Making Changes

### Compiler Changes (Python backend — `freakc/`)

The Python compiler is the bootstrap path. Changes here must:
1. Not break any existing test in `tests/` that previously compiled
2. Be tested against at least `hello.fk`, `closures.fk`, and `shapes.fk`
3. Emit valid C that compiles cleanly with `clang -w`

### Compiler Changes (Self-hosting — `src/compiler/`)

The self-hosting compiler is written in FREAK. Changes here must:
1. Compile with the current `freakc_self.exe`
2. Produce output that compiles correctly with clang
3. Pass the bootstrap test: `freakc_self2.exe tests/hello.fk` produces working output

### Standard Library (`std/`)

Standard library modules are pure FREAK where possible. C runtime backing is only for platform I/O, time, process, and networking. Adding a new module requires:
1. A `.fk` file in `std/`
2. At least one test file in `tests/`
3. An entry in the module table in `CLAUDE.md` and `freak-full-bible.md`

### Runtime Changes (`freakc/runtime/`)

The C runtime (`freak_runtime.c` / `freak_llvm_runtime.c`) backs stdlib functions that need system calls. Changes must:
- Compile cleanly on Windows (MSVC + clang), Linux (GCC + clang), and macOS (clang)
- Add `-D_CRT_SECURE_NO_WARNINGS` guards for MSVC deprecations
- Be accompanied by a FREAK-level test that exercises the new function

---

## Commit Policy

**Commit often.** The project has lost work before by not committing enough. The cost of an extra commit is zero.

- **Commit after**: every working milestone, every bug fix, every new test that passes, any change you'd be annoyed to redo
- **Message format**: short imperative summary, then bullets if needed

  ```
  Add str::repeat to std::string

  - Repeats a word N times with optional separator
  - Backed by pure FREAK (no runtime changes needed)
  - Added tests/string_repeat.fk
  ```

- **Stage specific files** — do not `git add -A`. Never commit `.env`, credentials, or build artifacts larger than a few hundred KB
- **No fixup commits for trivial typos** — just fix and include in the next logical commit

---

## Pull Request Guidelines

1. **One concern per PR.** A PR that fixes a bug and adds a feature is two PRs.
2. **Include a test.** If you fixed a bug, add a test that would have caught it. If you added a feature, add a test that demonstrates it.
3. **Update `freak-todo.md`** if your PR completes or progresses a milestone.
4. **Do not update `CLAUDE.md`** — that file is maintained separately as a session continuity guide.
5. **CI must pass.** The pipeline runs on Linux, macOS, and Windows. A PR that breaks any platform will not be merged.
6. **Keep the diff readable.** Reformat sparingly and only in files you're already touching.

### PR Title Format

```
[area] Short description of what changed

Examples:
[compiler] Fix off-by-one in string interpolation parser
[std::fs] Add fs::read_lines returning List<word>
[cli] Add freak check --strict flag
[runtime] Fix freak_word_concat on empty strings
[ci] Add arm64 Linux build target
```

---

## Language Design Contributions

FREAK's syntax and semantics are defined in `freak-full-bible.md`. Before proposing a new language feature:

1. Open a GitHub issue tagged `language-design`
2. Describe the feature in FREAK syntax — show example code
3. Explain what problem it solves that existing syntax cannot
4. Describe how it interacts with the type checker, the C backend, and the LLVM backend

Language features that will not be accepted regardless of quality:
- Features that require garbage collection (FREAK is manually managed / ownership-based)
- Syntax that conflicts with the visual novel / anime aesthetic without a compelling systems-level reason
- Features already in the spec that just have not been implemented yet (open a tracking issue instead)

---

## The Identity Rule

FREAK is not trying to be Rust with funny keywords. It is not a joke language. It is a real compiled systems language that happens to use `pilot` for variables and `training arc` for bounded loops, and this is intentional.

Every contribution should ask: *does this feel like FREAK?*

If a feature or change would fit equally well in any other language, it probably needs to be framed differently here. The weirdness is the design.

---

*"It was always going to end this way."*
*— freak-ui mono_no_aware theme*
