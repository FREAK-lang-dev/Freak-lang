# Editor integrations moved

Plugin sources, the lightweight Python language server, grammar/query checks,
and release packaging now live in
[FREAK-lang-dev/freak-editors](https://github.com/FREAK-lang-dev/freak-editors).

See its [installation and build guide](https://github.com/FREAK-lang-dev/freak-editors#readme)
for VS Code and Zed. The language release workflow calls a pinned version of
that repository's packaging workflow and attaches the resulting assets here.

Update both the reusable workflow ref and `revision` in
`.github/workflows/editor-packages.yml` together when adopting a reviewed
freak-editors update. This directory is a redirect, not a second plugin source.
