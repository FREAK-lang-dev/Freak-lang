# Checked signed-int64 native speed

Measured on 2026-10-05, Linux x86_64, Clang 19.1.7. The actual candidate
source is `d31c0965b71dd8313c9b2ec9c76d4f3403598db0`; the baseline compiler
is merged main `2b62e1cb1674336f52c3310a7dbf2e177d566a81`. Documentation
commits following the candidate do not represent additional native executions.
The [machine-readable receipt](int_checked_speed.json) retains every timing
sample, compiler/runtime/tool hashes, module/binary identities and raw-report
hashes.

The same [FREAK source](int_checked_hot_loop.fk), SHA256
`d4378f4621564112a89191231a90e1e552bea6a7307a297d35eea3ca240423f5`,
reads iteration count and seed at runtime. Its loop computes
`state = (3 * state + 17) mod 65536` using checked multiplication, addition
and conditional subtraction. It performs no Word operation, foreign call,
division or remainder inside the loop. The printed checksum keeps the result
observable; retained optimized LLVM proves a reachable loop and dynamic inputs
at O0/O2/O3. The independent checksum for 100,000,000 iterations and seed 17
is `36369`.

Five samples per variant and optimization level follow one warmup. Variant
order alternates. All variants reuse the same seven runtime objects and flags
at each level, including both ownership audits. Times are **guarded native job
wall time**: process startup, bounded capture/polling and log writes are included;
compiler work, input hashing and sanitizer runs are excluded. There is no timing
pass threshold.

| Optimization | Checked baseline median (range), s | Candidate median (range), s | Baseline / candidate |
|---|---:|---:|---:|
| O0 | 1.911 (1.870–1.955) | 0.750 (0.734–0.801) | 2.55x |
| O2 | 0.957 (0.946–1.014) | 0.214 (0.210–0.263) | 4.48x |
| O3 | 1.001 (0.966–1.004) | 0.211 (0.210–0.230) | 4.75x |

The historical module was emitted and LLVM-verified by the actual baseline
compiler, then compiled and executed by this matched campaign. A separate
executable mutation changes the six loop call sites back to the original
checked C helpers. Both references execute the exact checksum and fail the
inline guard specifically for those real helper calls. Their optimized LLVM
is identical at O2/O3 after removing only module/source path headers. The
mutation's O2 median is 0.957 s and O3 is 1.056 s; the 5.5% O3 difference from
the historical reference remains visible in the raw samples.

This establishes improvement for this workload on this host. It does not
reproduce the checklist's older 3.0 s / 0.88 s workload or establish overall
V3 performance parity. Uint, tiny, negation, division, remainder and checked
conversions retain their runtime helpers.

The successful signed-int64 `+`, `-`, `*` paths use internal `alwaysinline`
LLVM overflow wrappers. An overflow calls the original matching helper with
the same operands, then reaches `unreachable`; that helper retains its exact
diagnostic and `exit(1)`. No new runtime ABI, MIR/snapshot fields, ownership
policy or compiler handles are introduced.

Verification at the candidate source:

- Existing numeric gate: 48 original cases plus the checked-numerics and
  depth-256 controls; **150 native executions and 141 compiler contracts per
  mode**, plain and mandatory ASan/UBSan. Both modes prove snapshot restore,
  old-seal stability and fresh module equality at 64 MiB / 1,024 handles.
- New plain gate: 81 loop boundary executions, 87 dynamic signed/ordered/
  discarded/short-circuit executions, 45 measured executions, nine optimized
  module proofs and six real ownership-audit controls; 276 guarded jobs.
- New sanitizer gate: 54 loop boundary executions, 87 dynamic executions,
  six optimized module proofs and eight real audit/sanitizer controls; 192
  guarded jobs and no performance samples.
- Sixteen compiler cases prove wrapper shape, unchanged numeric carriers and
  conversions, sealed snapshots and authored/restored reserved-symbol errors.
  Existing 800-body and 12,000-statement/depth-2,048 resource oracles retain
  their original bounds. The 180 boundary and eight new oracle tests pass.

Source and physical-evidence reviews independently verify inputs, artifacts,
raw commands/output and medians. Linux/macOS/Windows workflow checks remain
required on the PR head before readiness. Preview completion, A4, self-hosting
and broader runtime/compile-time parity remain separate checklist items.

For a matched reproduction, emit this source with a worktree pinned to the
baseline commit using `build_v4.py --emit-llvm`, then run from the candidate
checkout with a fresh evidence directory:

```sh
python -B -u tests/v4_int_inline_runtime_bench.py --plain \
  --work /absolute/path/to/fresh-evidence --iterations 100000000 --samples 5 \
  --baseline-module /absolute/path/to/baseline.ll \
  --baseline-source-sha256 d4378f4621564112a89191231a90e1e552bea6a7307a297d35eea3ca240423f5 \
  --baseline-compiler-head 2b62e1cb1674336f52c3310a7dbf2e177d566a81
```

Omit `--plain` for the mandatory Linux sanitizer proof, using another fresh
directory. CI runs the plain gate on Linux, macOS and Windows and the sanitizer
gate on Linux, retaining source, LLVM, binaries, commands, output and JSON.
