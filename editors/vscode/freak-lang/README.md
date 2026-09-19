# FREAK for Visual Studio Code

Syntax highlighting, bracket matching, comment toggling, file icons, and snippet
completions for `.fk` files. No compiler or language server is required.

Download `freak-vscode-<version>.vsix` from the
[FREAK release](https://github.com/FREAK-lang-dev/Freak-lang/releases), then run
**Extensions: Install from VSIX...** in VS Code, or:

```sh
code --install-extension freak-vscode-<version>.vsix
```

Type `task`, `pilot`, `fixed`, `if`, `repeat`, `foreach`, `shape`, `say`, or
`giveback` and select a FREAK snippet from the completion menu. Tab moves between
placeholders. These are syntax templates, not type-aware symbol completions.

The grammar colors language syntax; highlighting does not guarantee that every
highlighted feature is supported by the shipping compiler. Compiler diagnostics,
hover, go-to-definition, and type-aware completion are not included yet.
