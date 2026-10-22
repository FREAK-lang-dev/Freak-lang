# V4 sibling-loop residual

This follows the [sibling-loop checkpoint](sibling_loop_scaling.md). It closes the residual tier 1 row: sibling `training arc` loops that move words compiled 5x to 6.5x slower than V3 and grew about 3.3x per doubling.

Setup: one Linux x64 host (4 vCPU) with Ubuntu Clang 18.1.3. "Before" is `main` at `10f53f8`. `benchmarks/v4/v3_compare.py` measures source to LLVM IR text and reports medians of three alternating samples. V3 is a stage-2 V3 built from `src/compiler/v3` with the `ci.yml` steps and linked with the `main` runtime, so V3 gets none of this branch's runtime changes. Raw rows and binary hashes are in the [JSON report](sibling_loop_residual.json).

## Sibling loops

| Loops | Lines | V3 s | V4 before s | V4 after s | Before / V3 | After / V3 |
|---:|---:|---:|---:|---:|---:|---:|
| 16 | 119 | 0.011 | 0.082 | 0.045 | 7.31x | 3.97x |
| 64 | 455 | 0.074–0.079 | 0.509 | 0.205 | 6.84x | 2.61x |
| 128 | 903 | 0.276–0.283 | 1.868 | 0.508 | 6.77x | 1.80x |
| 256 | 1,799 | 1.052–1.152 | 7.628 | 1.334 | 7.25x | 1.16x |

V3 cells show the range of its two runs (one for each V4 side).

V4 now grows 2.5x to 2.6x per doubling from 64 loops up. V3 grows 3.6x to 4.1x. The gap narrows with size: V4 is 1.16x V3 at 256 loops and should overtake it beyond that. At 16 loops V4 still pays a fixed cost of about 0.03 s that does not depend on the loop count.

On the `loops`, `tasks`, `long` and `calls` shapes, at every measured size, the emitted LLVM module is byte-identical before and after. The full `check_v4.py` run passes.

## What changed

- **Runtime**
  - `word_to_int` parses plain decimals of up to 19 digits directly. Before, every array handle and id read went through `strtoll`, which was 43% of all instructions at 128 loops. Anything else still goes to `strtoll`. The fast path was fuzzed against `strtoll` on 4 million random inputs plus edge cases.
  - `word_from_int` formats digits directly instead of calling `snprintf`. Its output is byte-identical (3 million random cases, plus `INT64_MIN` and `INT64_MAX`).
- **Meiya**
  - Move/loan and partial-move pair checks only visit paths with the same overlap root. Paths with different roots never overlap.
  - The Word state walk keeps one cached block skeleton per body: first statement, terminator, target and else target. It also shares one seen table and clears only the cells it set. Before, each walk allocated two cells per block and re-parsed every block record.
  - The drop-table walk shares a seen table the same way. One walk now answers both questions for a local: is it alive at some exit, and is it moved at some exit. This walk has no failure path, so it gives the same answers as the two separate walks.
  - A body-scoped name index replaces the linear `find_local` scans used by path-mode and Word-path lookups.
- **Codegen**
  - Word cleanup on statement and edge boundaries parses each owned local's scope once per body, not once per edge.

Every fast path keeps the cold path it replaces, and a body falls back to it when a table cannot be built.

## Other shapes

Alternating A/B runs on the same host, three runs each, milliseconds:

| Shape | Before | After |
|---|---|---|
| tasks800 | 2205, 1959, 2043 | 1685, 1790, 1880 |
| calls800 | 2895, 3032, 3242 | 2654, 2576, 2638 |

## Limits

One host. The walks are still per owned local, so very large single bodies remain superlinear; they now grow more slowly than V3. These numbers cover compiler execution, not the runtime of the programs it generates.
