# FREAK CLI Rewrite Plan — Python to FREAK

## Goal

Replace the Python `freakc` CLI (`python -m freakc`) with a native FREAK binary that handles the full compilation and package management pipeline. This is the logical next step after self-hosting the compiler (M15).

## Current State

The Python CLI (`freakc/__main__.py`) does:
1. **Parse/transpile** `.fk` source via Python lexer/parser/emitter → C
2. **Compile** generated C with `clang`/`gcc`
3. **Run** the resulting binary
4. **Package management** via `freakc/hangar.py`
5. **Audit** commands (static analysis)
6. **JIT** execution via llvmlite

The v2 self-hosted compiler (`build/freakc_v2.exe`) already handles step 1 (producing `.c` or `.ll` output). What's missing is wrapping it in a full CLI that handles compilation, linking, running, and package management.

## Architecture

```
freakc (native FREAK binary)
├── src/cli/main.fk          — CLI entry point, flag parsing
├── src/cli/build.fk         — Compile pipeline (invoke clang/lld)
├── src/cli/run.fk           — Build + execute
├── src/cli/hangar.fk        — Package manager (hangar.toml I/O)
├── src/cli/version.fk       — Version management (uses std/version.fk)
├── src/compiler/             — Existing v2 compiler sources (unchanged)
│   ├── ast.fk
│   ├── lexer.fk
│   ├── parser.fk
│   ├── checker.fk
│   ├── emitter.fk
│   └── backend/llvm.fk
└── std/version.fk           — Semver library
```

## What FREAK Already Has (capabilities we can use)

| Capability | Available via |
|---|---|
| File I/O | `fs::read()`, `fs::write()`, `fs::append()`, `fs::exists()` |
| Process execution | `process::exec()` (needs implementation) |
| Command line args | `process::args_count()`, `process::arg(N)` |
| String manipulation | `.length()`, `.char_at()`, `.starts_with()`, `.ends_with()`, `.contains()`, `.replace()`, `word_to_int()`, `word_from_int()` |
| Dynamic arrays | `array_new()`, `array_push()`, `array_get()`, `array_set()`, `array_len()` |
| Math/time | `time::now_ms()`, `time::sleep()`, `math::*` |

## What FREAK Needs Before CLI Rewrite

### Must Have (blockers)

1. **`process::exec(cmd) -> int`** — Execute a shell command and return exit code
   - Runtime: `freak_process_exec(freak_word cmd)` → calls `system()` or `popen()`
   - This is the critical missing piece — without it we can't invoke `clang`

2. **`process::exec_capture(cmd) -> word`** — Execute and capture stdout
   - Runtime: `freak_process_exec_capture(freak_word cmd)` → calls `popen()` + reads

3. **`process::exit(code: int)`** — Exit with specific code
   - Runtime: `freak_process_exit(int64_t code)` → calls `exit()`

4. **`fs::exists(path) -> bool`** — Check if file exists (already in runtime, needs v2 emitter mapping)

5. **`fs::delete(path)`** — Delete a file (already in runtime, needs v2 emitter mapping)

### Nice to Have (can work around)

6. **`fs::list_dir(path) -> word`** — List directory (for `hangar install`)
7. **`process::env(name) -> word`** — Read environment variable
8. **Simple TOML parser** — For `hangar.toml` reading (can be written in FREAK)
9. **HTTP client** — For `hangar install freak` (download from GitHub)
   - Workaround: shell out to `curl`/`wget`

## Implementation Phases

### Phase 1: Add Missing Runtime Functions
- Add `process::exec`, `process::exec_capture`, `process::exit` to C runtime
- Add emitter mappings in v2 compiler for these + `fs::exists`, `fs::delete`
- Test with simple programs

### Phase 2: CLI Skeleton
- `src/cli/main.fk` — Parse args, dispatch to subcommands
- Subcommands: `build`, `run`, `check`, `version`
- Build pipeline: read `.fk` → tokenize → parse → check → emit → invoke clang

### Phase 3: Hangar in FREAK
- TOML parser (simple, our subset only)
- `hangar init`, `hangar add`, `hangar remove`, `hangar install`
- `hangar version` (uses std/version.fk)

### Phase 4: Self-Contained Binary
- Single binary that includes compiler + CLI + package manager
- Concatenate all sources: `cat src/cli/*.fk src/compiler/*.fk std/version.fk > freakc_full.fk`
- Compile to native binary
- Replace Python CLI entirely

### Phase 5: Drop Python Dependency
- Update install scripts to ship only the native binary
- Update CI to build the native CLI
- Keep Python CLI as fallback/bootstrap only

## Build Process

```bash
# Concatenate all sources
cat std/version.fk \
    src/compiler/ast.fk \
    src/compiler/lexer.fk \
    src/compiler/parser.fk \
    src/compiler/checker.fk \
    src/compiler/emitter.fk \
    src/compiler/backend/llvm.fk \
    src/cli/build.fk \
    src/cli/run.fk \
    src/cli/hangar.fk \
    src/cli/version.fk \
    src/cli/main.fk \
    > build/freakc_full.fk

# Compile with existing v2
./build/freakc_v2.exe build/freakc_full.fk --c
clang -o build/freakc.exe build/freakc_full.fk.c \
    freakc/runtime/freak_runtime.c -Ifreakc/runtime -w -O2

# Test
./build/freakc.exe --version
./build/freakc.exe build tests/hello.fk
./build/freakc.exe run tests/hello.fk
```

## Timeline Estimate

- **Phase 1** (runtime functions): ~1 session
- **Phase 2** (CLI skeleton): ~1 session
- **Phase 3** (Hangar): ~1-2 sessions
- **Phase 4** (integration): ~1 session
- **Phase 5** (migration): ~1 session

## Key Decisions

1. **CLI is a superset of the compiler** — The CLI binary includes the full compiler. `freakc build` = transpile + compile. `freakc run` = transpile + compile + execute.

2. **TOML parser written in FREAK** — No external dependency. Our hangar.toml format is simple enough.

3. **HTTP via shell** — `process::exec("curl ...")` for downloading. No need for a FREAK HTTP client yet.

4. **Backwards compatible** — `freakc build file.fk` works exactly like `python -m freakc build file.fk`.

5. **Python stays as bootstrap** — The Python CLI is needed to bootstrap the first native binary. After that, the native binary compiles itself.
