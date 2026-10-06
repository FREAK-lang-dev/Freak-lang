# Locked native V4 bootstrap

This checkpoint focuses on building a separate V4 preview from one immutable
source revision. The locked V4 source commit is
`b43127c4e0d3beb9fc3b11b082799c3ef6e0403a`; `src/compiler/v4/bootstrap.toml`
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
host. Windows requires Windows 8 or newer and a GNU-targeting LLVM-MinGW UCRT
toolchain; release and bootstrap CI pin the 20260616 UCRT SDK. Plain MSVC
linking and legacy MSVCRT SDKs are unsupported by this bootstrap profile.
Windows arguments are decoded from the CRT's wide vector into UTF-8. Invalid
Unicode or allocation failure during that initialization is fatal: the runtime
frees staging, flushes its diagnostic and stops without invoking user exit
callbacks. Successfully decoded argument views remain valid through normal
exit callbacks and process teardown.

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
Python is only its test orchestrator. The dedicated `Locked V4 bootstrap`
workflow reconstructs and verifies this installed command on native Linux,
macOS and Windows. Its Linux job also runs the word ownership and copied-byte
gate with ASan and UBSan. Platform results must be read at the current PR head.

The scout's official V4 revision is used without input patches. On Linux,
480 identical source inputs produced byte-identical stdout, stderr and status
against a freshly Python-built compiler of the same revision: 54 modules and
426 diagnostic cases. Additional abort/read-failure controls and three larger
sources agreed. The C emitter now borrows read-only word identifiers after
proving the callee and argument expressions safe; uncertain alias, escape,
mutation, call or recursion cases retain copies. Owning ABI and cleanup remain
intact. The 4096-byte nested reader removes 4097 clones and 16,781,312 copied
bytes. Controlled native O2 comparisons measured 2.08x, 2.72x and 3.79x faster
compilation on three large Linux fixtures, with identical raw output and status
across three interleaved trials per engine. These measurements describe that
host and workload; product bootstrap optimization flags are unchanged.
