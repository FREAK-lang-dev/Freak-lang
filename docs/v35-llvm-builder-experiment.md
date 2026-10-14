# V3.5 LLVM IRBuilder experiment

This is a separate compiler prototype. Shipping `freak` still uses its existing
LLVM text emitter or C backend. The experiment has no release tag, installer,
package-manager entry or claim of full V3.5 coverage.

The compiler host reuses the actual V3 lexer, parser and semantic/strict-borrow
checker, then lowers their AST and recorded expression-type facts through
`src/compiler/v3/llvm_builder/emitter.fk`. A small C adapter calls LLVM 19.1.7's
official C API, which creates the real LLVM IRBuilder internally. This backend
never constructs textual IR or parses another backend's `.ll` output.

The first supported slice is deliberately small:

- `task main()` with int or void return and source tasks with int parameters
  and int/void results, including nested and recursive calls;
- int literals and bindings, local assignment and compound assignment;
- checked integer `+`, `-`, `*`, `/`, `%` and unary negation;
- int comparisons, boolean literals and `not` in `if` conditions;
- lexical blocks, `if`/`else`, `give back`, discarded scalar expressions and
  `say` of int values.

Word/num values and signatures, boolean local bindings, arrays, shapes, Result,
loops, `and`/`or`, `eventually`, globals, externs and runtime namespaces
are unsupported. Valid source using them receives an explicit experimental
backend diagnostic before an LLVM session or usable object is produced, even
when the unsupported form is unreachable. General ownership lowering, PHIs,
debug information, LTO, cross compilation and compiler self-host through this
backend remain future work. Normal V3 source/type/borrow errors still stop the
pipeline before backend admission.
The prototype accepts standalone source only: it has no CLI project/import
loader. Import declarations receive the existing frontend's rejection before
backend admission; no imported package or standard-library delivery is claimed.

The experimental host is assembled from the five existing frontend sources,
the new emitter and the new main, and compiled by stable V3 `--c`. It links the
C bridge, normal FREAK runtime and an explicitly selected LLVM 19.1.7 library.
The FREAK compiler logic uses FREAK's existing native C extern calls. For
example, the emitter contains this declaration:

```freak
extern task freak_ib_integer(session: int, value: int) -> int
```

A call such as `freak_ib_integer(ib_session, 42)` reaches the C symbol defined
in `bridge.c`, which creates an LLVM constant and returns its checked integer
ticket. The path is FREAK lowering code → native C extern call → C shim →
LLVM's C API (`LLVMConstInt` and `LLVMBuild*`). These extern declarations belong
to the compiler host; extern declarations in compiled applications remain
outside the experimental scalar slice.

The Bible's `extern [C] { ... }` blocks describe normative FFI syntax. Shipping
V3 currently parses `extern task`; it does not parse those extern blocks. This
experiment uses that existing extern-task implementation and adds no parser
or block-syntax support.

Its C word ABI is `freak_word`, so the bridge borrows and copies names/path bytes
before returning. This host cannot be bootstrapped through the current LLVM
backend using the same word prototypes. All other boundary values are int64
tickets/status values; native LLVM pointers and argument arrays remain inside
C. Tickets check generation, kind, owning session and function. A session owns
its context/module/builder and invalidates every associated ticket on release.
Bounds are eight sessions, 65,535 total tickets, 64 task arguments and 4,095
bytes per name/path/diagnostic copy. The bridge is private, single-threaded
compiler infrastructure, not a general public FFI or adversarial containment
boundary.

Mutable locals use entry-block allocas and typed `LLVMBuildLoad2`/store calls.
Task calls use typed `LLVMBuildCall2`; conditions use i1 and real block handles.
Checked arithmetic calls the existing `freak_int_*_checked` helpers, including
overflow, division-by-zero and signed-minimum division/remainder rules. Plain
LLVM add or `nsw` flags would not implement those runtime-error semantics.

The module is verified, assigned the native target machine's triple and data
layout, optimized using LLVM's `default<O0>`, `default<O2>` or `default<O3>`
pipeline, and verified again. The target machine emits genuine object bytes
to memory; the bridge exclusively creates the selected `.builder.o` path and
checks writing/closing. Failed ordinary writes remove only the output it owns.
The standalone host invalidates the selected derived object before frontend
work or option refusal. Existing C/LLVM outputs remain independent. An external
process interruption is an inconclusive attempt; the next invocation removes
its previous selected object before doing work.

LLVM is still internally C++. The C adapter avoids project-owned C++ code;
it does not remove LLVM's C++/platform dependencies or prove faster compilation,
smaller binaries, language ownership safety or semantic correctness. The LLVM
verifier checks structural IR validity rather than all FREAK language rules.

The native verification gate is prepared in
`tests/v3_llvm_builder_experimental.py`. Pure source controls check C/FREAK
boundary agreement and the cleanup table against the actual frontend handles:

```sh
python -u tests/v3_llvm_builder_experimental.py --source-controls
```

Native Linux qualification requires explicit immutable compiler/Clang/LLVM
inputs and a fresh evidence directory. It rebuilds the C-hosted experiment,
compares C/text-LLVM/builder executable output/status/error bytes at O0/O2/O3,
and exercises source failures, unsupported forms, stale-output removal,
wrong-kind/cross-session/cross-function/type tickets, malformed module
verification, output symlinks, registry exhaustion and cleanup. `--sanitize`
instruments the C bridge controls with ASan/UBSan. Every command's raw channels,
argv/status and source/input hashes remain in the evidence directory.

```sh
python -u tests/v3_llvm_builder_experimental.py \
  --compiler /absolute/current/freakc_stage2 \
  --clang /absolute/clang \
  --llvm-include /absolute/llvm-19.1.7/include \
  --llvm-library /absolute/libLLVM.so.19.1 \
  --evidence-dir /absolute/fresh/builder-evidence --sanitize
```

The existence of this gate is not a passing native verification receipt.
Linux, Windows, macOS and ARM delivery each require their own native SDK,
library/dependency closure, clean installed-archive check and source/ABI
regression coverage. No platform archive is currently published by this change.
Generated applications link FREAK's normal runtime through Clang and do not
need libLLVM; the experimental compiler host does.

If qualified for a preview, use an explicit separate executable such as
`freakc-irbuilder-experimental` and an asset such as
`freak-irbuilder-experimental-linux-x64-llvm19.tar.gz`, in a separate install
root and GitHub prerelease channel. Pin and record every actual SDK/library
dependency and LLVM license notice. Stable asset names, `releases/latest`,
default compiler selection and `VERSION` must retain their shipping meaning.
