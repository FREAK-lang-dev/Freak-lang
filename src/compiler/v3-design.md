# FREAK v3 Compiler Design (Historical Proposal)

> **Preservation note:** This is the original v2-to-v3 design record. It is
> retained to explain the constraints and decisions that produced V3; it is
> not the current build or reconstruction guide. Several planned file names
> below changed during implementation, and the v2 bootstrap executable was
> retired. See [`v3/README.md`](v3/README.md) for the as-built eight-file
> architecture, exact source order, checked-in C bootstrap seed, clean
> self-host fixed-point procedure, supported surface, and legacy status.

## Why v3?

The v2 compiler has fundamental architectural limitations that prevent further development:

1. **O(n^2) output buffer** - `emit()` does `out_buf = out_buf + s` which copies the entire output on every call. When self-compiling (~167KB source → ~5500 lines C), this causes massive slowdown and silent truncation.

2. **If/else chains generate nested braces** - `else if` compiles to `else { if { } }`, creating N levels of nesting for N branches. At ~30+ branches, the generated C hits compiler nesting limits.

3. **No streaming in C backend** - LLVM backend flushes every 50 lines, but C backend accumulates everything in one string. Large programs get truncated.

4. **Cannot bootstrap new features** - Adding new tasks or modifying existing large functions causes the old binary to silently drop the changes. The compiler cannot evolve.

5. **String-encoded block bodies** - Statement blocks are comma-separated ID strings ("5,12,18,...") parsed character-by-character. Fragile and slow.

## v3 Architecture

### Core Principle: Stream Everything

v3 writes output directly to a file handle. No output buffer. Every `emit()` call writes immediately to disk.

```fk
-- v3 emit: direct file I/O
pilot out_fd = 0  -- file descriptor

task emit(s: word) -> void {
    fs::append_fd(out_fd, s)
}
```

Since FREAK doesn't have file descriptors yet, we use `fs::append(filename, s)` which the runtime supports.

### Key Design Changes

#### 1. Streaming Output (fixes truncation)
```fk
pilot out_file = ""

task emit(s: word) -> void {
    fs::append(out_file, s)
}

task emit_line(s: word) -> void {
    fs::append(out_file, s + "\n")
}
```

No buffer. No O(n^2). Output goes directly to file.

#### 2. Flat If Dispatch (fixes nesting)

Instead of `else if` chains, use lookup arrays or early-return patterns:

```fk
-- v2 style (broken at depth):
if val == "say" { ... }
else if val == "fs::read" { ... }
else if val == "ui::create_window" { ... }  -- dropped at depth 30+

-- v3 style (flat, never nests):
task map_builtin(val: word) -> word {
    if val == "say" { give back "@freak_llvm_say" }
    if val == "fs::read" { give back "@freak_llvm_fs_read" }
    if val == "ui::create_window" { give back "@freak_llvm_ui_create_window" }
    give back ""
}

task is_void_builtin(val: word) -> bool {
    if val == "say" { give back true }
    if val == "ui::destroy_window" { give back true }
    give back false
}
```

Flat `if` with early return — zero nesting depth.

#### 3. Block Bodies as Arrays (fixes fragility)

```fk
-- v2: bodies stored as comma-separated string "5,12,18"
-- v3: bodies stored as array handles

pilot ast_stmt_body_arrays = 0  -- array of array handles

task alloc_block() -> int {
    pilot arr = array_new()
    give back arr
}

task block_push(block: int, stmt_id: int) -> void {
    array_push(block, word_from_int(stmt_id))
}

task emit_block(block_handle: int) -> void {
    pilot count = array_len(block_handle)
    pilot bi = 0
    repeat count times {
        pilot sid = word_to_int(array_get(block_handle, bi))
        emit_stmt(word_from_int(sid))
        bi += 1
    }
}
```

No string parsing. Direct array iteration.

#### 4. Modular Emitter Functions

Split the monolithic emitter into focused functions that each handle a subset:

```fk
-- Instead of one 200-line emit_llvm_program():

task llvm_emit_declarations() -> void { ... }
task llvm_emit_globals() -> void { ... }
task llvm_emit_tasks() -> void { ... }
task llvm_emit_init_globals() -> void { ... }
task llvm_emit_main_wrapper() -> void { ... }

task emit_llvm_program() -> void {
    llvm_emit_declarations()
    llvm_emit_globals()
    llvm_emit_tasks()
    llvm_emit_init_globals()
    llvm_emit_main_wrapper()
}
```

Each function is small enough to never hit v2's truncation limits.

#### 5. Unified Backend Interface

Both C and LLVM backends use the same streaming emit infrastructure:

```fk
pilot out_file = ""
pilot emit_target = ""  -- "c" or "llvm"

task emit(s: word) -> void {
    fs::append(out_file, s)
}
```

### Planned File Structure (Historical)

The following was the proposed split. The preserved implementation uses
`globals.fk` and `helpers.fk` rather than separate `ast.fk`, `builtins.fk`, and
`runtime.fk`; the authoritative current inventory is in `v3/README.md`.

```
src/compiler/v3/
    main.fk          -- Entry point, CLI arg parsing
    lexer.fk         -- Tokenizer (reuse v2 lexer, it works fine)
    parser.fk        -- Parser (fix else-if to use flat if chains internally)
    ast.fk           -- AST node types and array storage
    checker.fk       -- Type checker
    emit_c.fk        -- C backend emitter
    emit_llvm.fk     -- LLVM IR backend emitter
    builtins.fk      -- Builtin function name/type mappings
    runtime.fk       -- Runtime function registry
```

### Original Bootstrap Strategy (Historical)

This describes the one-time transition from v2. A modern reconstruction does
not require `freakc_v2.exe`: it links the reviewed
`build/freakc_v3.fk.c` seed, regenerates V3 twice from a fresh ordered source
aggregate, and requires the two generated C stages to be byte-identical. See
`v3/README.md` for that procedure.

v3 is compiled by v2 (the existing `freakc_v2.exe`). Key constraint:
- Each v3 source file must be small enough for v2 to handle
- No file can have functions longer than ~100 lines
- All if/else chains must stay under ~20 branches
- No new tasks added to existing v2 functions (add new files instead)

Since v3 is split into multiple files, we concatenate them before compilation:
```bat
type src\compiler\v3\ast.fk src\compiler\v3\lexer.fk ... > build\freakc_v3.fk
freakc_v2.exe build\freakc_v3.fk
```

### Migration Path

1. Build v3 compiled by v2 (Stage 0)
2. v3 compiles hello.fk (validation)
3. v3 compiles calculator.fk (UI validation)
4. v3 compiles itself (self-hosting, Stage 1)
5. Stage 1 v3 compiles itself (Stage 2, bootstrap complete)
6. v2 retired

### What v3 Preserves from v2

- Lexer design (character-by-character, dynamic arrays for tokens)
- AST parallel array storage (proven pattern, fast)
- Shape registry
- LLVM IR generation patterns (string constants, register naming)
- All runtime bridge functions

### What v3 Changes

| v2 | v3 | Why |
|---|---|---|
| `out_buf = out_buf + s` | `fs::append(file, s)` | O(1) vs O(n) per emit |
| `else if` chains (nested) | Flat `if` + early return | Avoids nesting limits |
| Comma-separated block IDs | Array handles for blocks | Robust, fast |
| Monolithic emitter | Split into 6-8 functions | Fits v2 compile limits |
| Single 4500-line file | 8-10 files, concatenated | Maintainable, bootstrappable |
| C-only streaming (via LLVM hack) | Streaming for both backends | Uniform |
| 53-branch call mapping | Lookup via sorted if-chains | Never truncated |
