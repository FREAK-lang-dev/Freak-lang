# Decision: bounded V3.5 bootstrap and ecosystem work

Status: accepted for implementation; release acceptance pending.

The V3 architecture ordinarily reserves new language work for V4. The
V3.5 all-P0 goal, authorized for implementation on 2026-10-05, makes a bounded
exception: semicolon statement separators, the checked word/word result form
used by the pinned V4 compiler, the three promised counted-loop forms, and both
`repeat while` and `while`. It also permits reproduced V3 correctness repairs,
resolved source-package binding, and additive public runtime/tooling APIs.

The baseline and initial V4 input are pinned to
`8ffb389508b8a8f37455ad83b4813062b3d11c2f`. The source order remains derived
from the existing compiler inventories. Compiler-private bootstrap helpers
require an explicit capability contract; ordinary packages cannot opt into
them by filename or name. Runtime identities for V3.5 programs, the V4 host,
and V4-generated programs remain distinct.

Hangar owns dependency identities, fetching and locks. The compiler consumes
a completed immutable source graph, binds exports/references and source maps,
then may flatten the resolved source closure. No network resolution enters
the parser or checker. Scoped source packages remain required: a unique-prefix
bundle is a narrower delivery profile, not completion of the all-P0 goal.

Source binding resolves declarations by their type or value role, preserves
nominal type identity, and displays source names in diagnostics. Fixed root
pilots and ordinary task/extern declarations share value-name collision checks
where those declarations are admitted. A lexical local value shadows a callable;
calling a non-callable value fails before emission. Source references cannot
gain access through generated private names. Package extern declarations remain
unsupported. Unloaded export headers validate the supported task/fixed/shape
surface; they do not promise validation of every unused unsupported declaration.
The unused extern-collision boundary is tracked in
[issue #151](https://github.com/FREAK-lang-dev/Freak-lang/issues/151).
Original source names retain builtin type, namespace and callable reservations
before package name generation, including the established trusted-runtime and
bootstrap-profile allowances.

The shipping V3 checker retains its established contextual lookup for a
non-fixed root pilot and a same-named task. This is a legacy V3 compatibility
boundary, not a new language namespace or a flag-gated rule. Bible section 17.4
still defines the V4 value namespace and forbids mutable root bindings. This
repair does not promote full V4 namespace or root-constant conformance.
The public CLI registers shape headers before parsing bodies and accepts forward
shape constructors. The legacy direct parser retains its declaration-order
limitation; regression checks preserve its original rejection and separately
verify public C/LLVM construction and field access.

Public process launching uses explicit executable/argument vectors and owned,
generation-checked command tickets. Checked filesystem and byte APIs support
transactional publication. Legacy explicit shell APIs remain a compatibility
surface; package/build/bootstrap/test consumers migrate to shell-free launch.
Words returned from filesystem entry/error, process error, JSON-document error
and HTTP server/request error getters own independent storage. Releasing,
reusing or growing the source ticket cannot invalidate the returned word.
Generic cloning of immutable literal words retains its existing sharing rule.
Windows owned temporary directories explicitly select the effective caller as
owner and receive a protected, inheritable caller-only DACL at creation. The
runtime verifies the held object's owner and DACL before returning it.
Publication still requires caller-owned safe parents; generic directory
creation, existing parent ACL checks and the process's default-owner setting
remain unchanged.

The HTTP profile is synchronous, bounded and one request per connection,
defaulting to loopback with configurable framing/size/deadline limits. The
toolchain owns the reusable transport floor and acceptance corpus. The first
user owns his server/router package; an independent consumer fixture proves
the floor through public APIs without replacing his work.

The stronger FIX-05 failure oracle governs unusable entry, stray expressions,
skipped root statements, invalid interpolation and invalid word indexing.
Invalid indexing must fail controllably on both backends; valid LLVM indexing
matches C's word-valued result. Continued silent legacy filesystem failure is
not repaired merely by introducing another checked API. Reproductions against
the current reconstructed native baseline determine which old reports still
need a correction. The user selected controlled runtime errors for integer
overflow, matching V4 at O0/O2/O3 on the C and LLVM backends.

The selected stronger FIX-05 interpolation rule is a breaking change from
silently printing unsupported expression-like brace bodies. Such bodies now
produce a diagnostic; unterminated paths and call/operator expressions also
fail. Spell intentional literal braces with `\{` and `\}`. Empty braces and
object/JSON-like literal text retain their existing behavior. The normative
bible and V3 conformance row record this rule; these V3 checks do not establish
V4 interpolation parity. Include this change in the eventual release notes.

The declared native LLVM profile requires Clang major 15 or later; Apple Clang
also has a conservative major-15 support floor. Version identification is
separate from the required real compile/link/execute probe and native platform
evidence. The initial local verification toolchain is Clang 19.1.7.

No V4 IR/query architecture, borrow checker, full generic Result/type system,
async runtime, LLVM API migration, registry service or native TLS is added to
the critical path. Preserve the checked-in seed and prove V3 generated-C
generation-2/generation-3 convergence after compiler changes.

Completion requires all B/P/H/T/L acceptance stories from the actual extracted
candidate archives, C/LLVM parity, required native platform and sanitizer
evidence, accurate documentation, and independent source/artifact review.
Version changes, merging, tagging and publication are separate delivery
decisions. The proposed date does not replace a gate.
