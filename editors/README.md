# FREAK editor packages

Tagged releases built with the editor packaging workflow attach:

| Asset | Installation | Features |
|---|---|---|
| `freak-vscode-<version>.vsix` | VS Code: **Extensions: Install from VSIX...** | TextMate highlighting, brackets, comments, file icon, snippet completions |
| `freak-zed-<version>.zip` | Extract, then Zed: **Install Dev Extension** on `freak-zed` | Tree-sitter highlighting, brackets, indentation, outline, snippet completions |

Both assets are included in the release's `SHA256SUMS`. VS Code-compatible
editors that support VSIX installation can use the VS Code package. Other
editors can reuse the TextMate grammar or bundled Tree-sitter grammar, but no
additional editor integration is packaged yet.

Snippets provide common syntax templates without installing a compiler. Full
type-aware autocomplete, diagnostics, hover, and definition navigation need a
released language server. V4 currently exposes internal editor facts and a
line protocol; these packages do not advertise that as a JSON-RPC LSP server.

The packages are release downloads; Marketplace, Open VSX, and Zed Gallery
publication are separate distribution steps. See the individual
[VS Code](vscode/freak-lang/README.md) and [Zed](zed/freak-lang/README.md) guides.

## Build and verify

Use Node.js 22+ and Python 3.11+. From the repository root:

```sh
npm ci --prefix editors
npm test --prefix editors
python -u tools/package_editors.py --output dist/editors
python -u tests/editor_packages.py --artifacts dist/editors
```

Release packaging reads `VERSION` and stamps both **staged** manifests with that
version, leaving checked-in development manifests unchanged. It pins the Zed
grammar repository to the checkout's full commit SHA, so publish that commit
before distributing a locally built Zed archive. Neither a publisher token nor
an editor Marketplace account is needed to build the downloads.

The editor CI job also compiles the checked-in Tree-sitter parser and each Zed
query, and parses a representative FREAK source fixture. Keep the two snippet
JSON files identical; the artifact test enforces this.
