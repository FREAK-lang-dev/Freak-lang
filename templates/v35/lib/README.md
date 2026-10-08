# @@NAME@@

A source library with one declared module and one public task, `greet`.
It has no entry program, executable statements, or initialization side effects.
Tests import the local declared module. The example consumer imports only the
public export through its explicit local dependency alias, `demo`.
The three consumer files are explicit assets in the library source inventory;
they remain a separate application and do not execute during library import.

From this directory:

```sh
freak test
cd examples/consumer
freak build
freak run
freak test
```

The consumer prints `Hello, consumer!`. Importing the library prints nothing.
The library itself has no executable to run; build/run the consumer. Its
`demo = { path = "../.." }` dependency reads this local library during ordinary
development. Local source edits are mutable; use a matching lock/vendor
snapshot when requiring reproducible frozen builds.

Requirements: matching V3.5 compiler/runtime/std/template payload, Clang with
the host SDK, and native project/package/test capabilities. No registry,
network, Git, Python, lifecycle hook, or undeclared dependency is needed.
Use `--c` for the portability backend; the default is LLVM.

Build/test output belongs to the CLI. To discard this generated example,
explicitly remove its directory after stopping its processes and checking
for work to keep. Review the license before publication.
