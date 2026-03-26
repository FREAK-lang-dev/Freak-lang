# FREAK Language Support for VS Code

Syntax highlighting, snippets, and language configuration for the **FREAK** programming language.

FREAK is a compiled, statically-typed, memory-safe systems programming language with syntax and aesthetics inspired by anime and visual novels. Files use the `.fk` extension.

## Features

- Full syntax highlighting for `.fk` files
- 25+ code snippets for common patterns
- Bracket matching and auto-closing
- Comment toggling (`--`)
- String interpolation highlighting (`{expr}` in strings)

## Syntax Highlighting

The grammar covers all FREAK language features:

- **Keywords**: `pilot`, `task`, `give back`, `shape`, `doctrine`, `impl`, `when`, `eventually`, etc.
- **Types**: `int`, `word`, `bool`, `maybe<T>`, `result<T,E>`, `List<T>`, etc.
- **Annotations**: `@protagonist`, `@nakige`, `@experiment`, `@season_finale`
- **Booleans**: `true`, `false`, `yes`, `no`, `hai`, `iie`
- **Operators**: `|>` (pipe), `->` (return type), `?` (error propagation)
- **String interpolation**: `"Hello, {name}!"`
- **Namespace access**: `std::fs::read(path)`

## Snippets

| Prefix | Description |
|--------|-------------|
| `main` | Main entry point with `@protagonist` |
| `task` | Function declaration |
| `shape` | Struct declaration |
| `impl` | Implementation block |
| `pilot` | Mutable variable |
| `fixed` | Immutable variable |
| `if` / `ifelse` | Conditionals |
| `when` | Pattern matching |
| `repeat` | Loop (repeat until) |
| `times` | Counted loop |
| `training` | Training arc (bounded loop) |
| `foreach` | Iterator loop |
| `say` | Print output |
| `give` | Return value |
| `eventually` | Deferred execution |
| `test` | Test block |
| `use` | Module import |
| `extern` | External function |
| `isekai` | Isolated scope |
| `trust` | Unsafe block |

## Example

```freak
use std::math

@protagonist
task main() -> void {
    pilot name: word = "Takeru"
    pilot power: int = 9001

    say "Welcome, {name}!"
    say "Power level: {power}"

    if power > 9000 {
        say "It's over 9000!"
    }

    training arc i from 1 to 5 {
        say "Training round {i}..."
    }
}
```

## Links

- [FREAK Language Repository](https://github.com/FREAK-lang-dev/Freak-lang)
- [Language Specification](https://github.com/FREAK-lang-dev/Freak-lang/blob/main/freak-full-bible.md)

---

*"It was always going to end this way."*
