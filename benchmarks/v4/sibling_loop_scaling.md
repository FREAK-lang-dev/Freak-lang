# V4 sibling-loop and compile-time checkpoint

This checkpoint compares `main` at `2cee8686f8988a18b391060f5eab3e1eef9840a1` (before) with this branch (after). The pinned rows use `74a992e`. `e0c4dff` adds only the supplied-borrow reuse guard; the `tasks3200` row and the V3 comparison were taken on it.

Setup: one Linux x64 host with Ubuntu Clang 18.1.3, using the [superlinear checkpoint](compiler_superlinear_speed.md) method (`v4_scale_bench.py --check`, three ordinary `-O2` runs per side, medians per metric). Raw rows are in the [JSON report](sibling_loop_scaling.json).

## Sibling loops (#161)

The `loops` shape has N sibling `training arc` loops. Each loop moves a fresh word and prints it, which is the #161 pattern.

| Loops | Lines | Before | After |
|---:|---:|---:|---:|
| 16 | 119 | over 300 s (killed) | 0.078 s |
| 32 | 231 | over 300 s (killed) | not run |
| 64 | 455 | over 300 s (killed) | 0.653 s |
| 128 | 903 | not run | 2.181 s |

Before, Meiya's move-repair walk visited every CFG path, so its cost grew exponentially with the number of loops. A narrower `say`-only variant of 64 loops took 11.3 s before and 0.18 s after; 256 such loops took 41.8 s and 2.3 GB before, and about 2 s after.

What changed:

- **Meiya**
  - Reachability rows are scoped to one body.
  - Drop states live in a hashed table.
  - The repair walk is memoized.
  - Overlap is checked before any CFG query.
  - Holders are memoized per loan.
  - Each block keeps a set of the locals it mentions.
- **Codegen**
  - Cleanup uses an owned-locals list.
  - Meiya results are looked up by def index.
  - Edge scopes are computed once per edge.
  - Codegen reuses the build tool's Meiya result instead of running a second `check_mir`.

Every fast path keeps the cold scan it replaces. `borrowck_cfg_scaling_smoke.fk` compares each fast path against its cold scan, and it checks that a word reused by the next iteration is still refused.

Residual cost: sibling-loop bodies still grow about 3.3x per doubling. The remaining work is owned locals × CFG edges: the per-local Word state walk and the per-edge scope cleanup. Each step is now cheap, but the product is still quadratic.

## Pinned shapes

| Shape | Size | Lines | Before s | After s | Change | TY before | TY after |
|---|---:|---:|---:|---:|---:|---:|---:|
| tasks | 400 | 2,803 | 1.401 | 1.196 | -14.6% | 0.051 | 0.048 |
| tasks | 800 | 5,603 | 2.714 | 2.213 | -18.4% | 0.092 | 0.094 |
| tasks | 1600 | 11,203 | 5.592 | 4.710 | -15.8% | 0.203 | 0.194 |
| tasks | 3200 | 22,403 | 12.322 | 9.650 | -21.7% | 0.400 | 0.437 |
| long | 400 | 2,075 | 0.774 | 0.636 | -17.8% | - | - |
| long | 800 | 4,131 | 1.500 | 1.249 | -16.7% | - | - |
| long | 1600 | 8,243 | 3.405 | 2.568 | -24.6% | - | - |
| calls | 400 | 1,627 | 1.955 | 1.802 | -7.8% | 0.034 | 0.036 |
| calls | 800 | 3,227 | 4.240 | 3.526 | -16.8% | 0.071 | 0.073 |
| calls | 1600 | 6,427 | 8.647 | 7.285 | -15.8% | 0.167 | 0.157 |

The `tasks3200` row is a single run per side. Most of the gain is codegen: at `calls1600` it falls from 5.000 to 3.713 s, and at `long1600` from 1.580 to 0.854 s. Median peak memory falls on every row, for example from 498 to 453 MiB at `calls1600`.

On every pinned row and every run, the emitted LLVM module hashes are identical before and after, and so are the native exit and stdout oracles.

**TY.** TY now grows 1.9x to 2.3x per doubling (0.048, 0.094, 0.194, 0.437 s). At 22,403 lines it takes 0.437 s, against the historical 0.78 s observation of 3.2x to 3.6x growth. TY was already at this level on the baseline (0.400 s): the change came from earlier `main` work, and this branch does not touch TY.

## V3 comparison

`benchmarks/v4/v3_compare.py` measures source to LLVM IR text: V3 with `--llvm`, V4 with the benchmark compiler. Each cell is the median of three samples, and the samples alternate which compiler runs first.

| Shape | Size | Lines | V3 s | V4 s | V4/V3 |
|---|---:|---:|---:|---:|---:|
| tasks | 200 | 1,403 | 0.498 | 0.575 | 1.15x |
| tasks | 800 | 5,603 | 5.844 | 2.460 | 0.42x |
| tasks | 1600 | 11,203 | 21.831 | 4.923 | 0.23x |
| long | 200 | 1,043 | 0.358 | 0.343 | 0.96x |
| long | 800 | 4,131 | 4.146 | 1.377 | 0.33x |
| long | 1600 | 8,243 | 16.706 | 2.687 | 0.16x |
| calls | 200 | 827 | 0.868 | 0.924 | 1.06x |
| calls | 800 | 3,227 | 10.020 | 3.864 | 0.39x |
| calls | 1600 | 6,427 | 37.421 | 7.620 | 0.20x |
| loops | 16 | 119 | 0.015 | 0.078 | 5.18x |
| loops | 64 | 455 | 0.108 | 0.653 | 6.07x |
| loops | 128 | 903 | 0.333 | 2.181 | 6.54x |

Results by input size:

- **Small inputs:** V4 is within 15% of V3.
- **800 lines and up:** V4 is 2.4x to 6x faster, because V3 itself grows superlinearly on these shapes.
- **Sibling-loop bodies:** V4 is still 5x to 6.5x slower than V3. This is the residual row in the release checklist.

The historical handoff-7 figure, 1.7x to 2.6x slower, is superseded for the tasks, long and calls shapes.

## Limits

These numbers measure compiler execution only, not the runtime of generated programs. They come from one host and do not establish global linearity. The V4 timings use the instrumented benchmark compiler. Native linking is excluded on both sides.

## Reproduce

Run from each checkout:

```sh
python -B -u v4_scale_bench.py --shapes tasks long calls --sizes 400 800 1600 --check \
  --timeout 300 --build-timeout 300 --mem-limit-mb 2048 --output-limit-mb 64 \
  --work /tmp/freak-loops-run-1 --json /tmp/freak-loops-run-1.json
python -B -u benchmarks/v4/v3_compare.py --v3 <v3 binary> --v4 /tmp/freak-loops-run-1/compiler/*/v4c \
  --shapes tasks long calls --sizes 200 800 1600 --repeats 3
python -B -u benchmarks/v4/v3_compare.py --v3 <v3 binary> --v4 /tmp/freak-loops-run-1/compiler/*/v4c \
  --shapes loops --sizes 16 64 128 --repeats 3
```
