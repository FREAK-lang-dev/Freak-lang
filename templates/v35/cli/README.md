# @@NAME@@

A native FREAK command-line application. The manifest declares its entry,
module, exported task, and standalone test. It has no external dependencies.

From this directory:

```sh
freak build
freak run -- Ada
freak test
```

The default backend is LLVM. Use `--c` to exercise the portability backend.
Arguments after `--` reach the program as exact arguments; the application
does not invoke a shell. The example prints `Hello, Ada!`.

Requirements: a V3.5 compiler and its matching runtime/std/template payload,
Clang with the host SDK, and the native project/package/test capabilities.
This template does not require Git, network access, Python, or build hooks.

The CLI owns generated project build output and test staging. Do not remove
source files to clean a build. To discard the entire example, stop its
processes and explicitly remove this generated directory after checking that
it contains no work you want to keep. Review the license before publication.
