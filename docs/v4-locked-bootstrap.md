# Locked native V4 bootstrap

This checkpoint focuses on building a separate V4 preview from one immutable
source revision. The locked V4 source commit is
`b8c5e99d10af59ffcc103ef572bb1a4e36470f19`; `src/compiler/v4/bootstrap.toml`
and `bootstrap.lock` record its entry, ordered source bytes, compatibility
profile and private generated-program runtime inventory.

From a native toolchain installation, run one command:

```sh
freak bootstrap-v4 --source=/absolute/locked-v4-source --output=/absolute/new-v4-preview --locked
```

`freak bootstrap --v4` accepts the same options. The source directory must
contain the recorded metadata and source files. The output directory must be
new. Set `FREAK_CLANG` to the absolute path of a supported Clang installation
when automatic discovery does not select it. Bootstrap targets the current
host; plain MSVC linking is unsupported.

The command validates the locked inputs, compiles the V4 engine and launcher,
tests query invalidation and generated programs, and publishes the preview only
after those checks pass. The shipping V3 executable is preserved. The output
includes `bootstrap-report.json`, copied lock and metadata, native engine and
launcher, and the preview's private runtime. Keep the whole directory when
relocating it.

```sh
/absolute/new-v4-preview/freak-v4 --version
/absolute/new-v4-preview/freak-v4 check program.fk
/absolute/new-v4-preview/freak-v4 emit program.fk --output=/absolute/program.ll
/absolute/new-v4-preview/freak-v4 build program.fk --output=/absolute/program
```

The preview has V4's current language and backend limits; it is not a complete
V3 replacement or evidence of V4 self-hosting. This checkpoint does not declare
the wider V3.5 P0 package, HTTP, editor, diagnostic or cache work complete.

The production verification entry point is
`tests/v3_v35_bootstrap_native.py`, supplied with the freshly reconstructed or
installed native CLI, real Clang, the frozen source bundle, and an optional Git
checkout for exact source-object checks. It invokes the real public command;
Python is only its test orchestrator. Linux x86-64 can be verified in this
workspace. Native Windows and macOS verification remains pending GitHub CI.
