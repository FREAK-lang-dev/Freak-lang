# FREAK Language — Zed Extension

Syntax highlighting, bracket matching, indentation, and document outline for `.fk` files in Zed.

## Install (dev mode)

1. Open Zed
2. Open the command palette (`Ctrl+Shift+P`)
3. Run **zed: install dev extension**
4. Select the `editors/zed/freak-lang` directory from this repo

The extension will reload automatically when you edit files.

## Features

- Full syntax highlighting (keywords, types, strings, annotations, etc.)
- String interpolation support (`{expr}` inside double-quoted strings)
- Rainbow bracket matching
- Auto-indentation for blocks
- Document outline (shapes, tasks, impls, routes, tests)
- Comment toggling (`--`)

## Publishing

Once the tree-sitter grammar is hosted at `github.com/FREAK-lang-dev/tree-sitter-freak`:

1. Update `extension.toml` with the correct `rev` (commit SHA)
2. Submit to [Zed Extensions](https://github.com/zed-industries/extensions)

## Building the Tree-sitter grammar

```bash
cd grammars/tree-sitter-freak
npm install
npx tree-sitter generate
npx tree-sitter test
```
