# FREAK for Zed

Syntax highlighting, bracket matching, indentation, document outline, comment
toggling, and snippet completions for `.fk` files.

## Install a release

1. Download `freak-zed-<version>.zip` from the
   [FREAK release](https://github.com/FREAK-lang-dev/Freak-lang/releases).
2. Extract the archive into a permanent directory.
3. In Zed, open Extensions and choose **Install Dev Extension**, then select the
   extracted `freak-zed` directory containing `extension.toml`.

Zed fetches the grammar from the exact FREAK commit recorded in the manifest and
builds it. Internet access and Git are required for this first install; Zed may
download its grammar build tools. Follow Zed's
[development prerequisites](https://zed.dev/docs/extensions/developing-extensions).
Keep the extracted directory while the dev extension is installed. To update,
extract the new release and install that directory through the same command.

This is a source extension archive for Zed's dev installer, not a precompiled
Zed Gallery package. Gallery publication remains a separate step.

## Completions and boundaries

Type `task`, `pilot`, `fixed`, `if`, `repeat`, `foreach`, `shape`, `say`, or
`giveback` and choose the corresponding snippet. Tab moves between placeholders.
These templates work without a language server. Type-aware completion,
diagnostics, hover, and go-to-definition are not provided yet.

The grammar covers common FREAK syntax, not every V4 form. Highlighting does not
guarantee compiler support for a construct.

## Develop

You can also install `editors/zed/freak-lang` directly from a checkout. The source
manifest pins a known grammar commit; release packaging stamps the release SHA.
Queries live beside `languages/freak/config.toml`, as required by Zed.

To work on the bundled grammar:

```sh
cd editors/zed/freak-lang/grammars/tree-sitter-freak
npm ci
npx tree-sitter generate
npx tree-sitter test
```

For unpublished grammar edits, point the manifest's grammar repository at a
local Git repository using a `file://` URL and pin its committed revision.
