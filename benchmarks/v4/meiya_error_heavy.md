# V4 Meiya on error-heavy input

This closes the tier 2 row "Meiya on error-heavy input: bounded time and memory". At the last recorded baseline (probe built at `4f895d6`), 10 compiler crates timed out or exceeded 2 GiB in Meiya when each was compiled alone in strict mode.

Setup: one Linux x64 host (4 vCPU) with Ubuntu Clang 18.1.3. `benchmarks/v4/meiya_error_heavy.py` builds a probe from `tools/build_llvm.fk` (Python-built, `-O0`, like the smoke harness) that keeps going after errors and stops after Meiya. Peak memory is the probe's `ru_maxrss` from `wait4`; it includes about 19 MiB inherited from the small Python launcher at fork, so tiny crates read 19 MiB. Each process runs under `prlimit --as` 2 GiB with a 60 s timeout per crate (300 s per synthetic size; 120 s for the "before" run). "Before" is `main` at `5ffec30`; "after" is this branch. Raw rows, probe hashes and source hashes are in the [JSON report](meiya_error_heavy.json).

## Compiler crates, strict, one at a time

Diagnostics are stage totals (inherited between stages). Except for `freak_borrowck`, whose source this branch changes, every crate reports the same counts before and after.

| Crate | Lines | Parse | MIR | Meiya | Meiya s before | Meiya s after | Total s before | Total s after | Peak MiB before | Peak MiB after |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| freak_span | 200 | 2 | 2 | 14 | 0.04 | 0.05 | 0.10 | 0.12 | 19 | 19 |
| freak_diag | 78 | 4 | 4 | 9 | 0.01 | 0.01 | 0.03 | 0.03 | 19 | 19 |
| freak_macro_api | 583 | 20 | 20 | 231 | 0.24 | 0.20 | 0.58 | 0.42 | 28 | 27 |
| freak_arena | 96 | 3 | 3 | 3 | 0.01 | 0.01 | 0.03 | 0.03 | 19 | 19 |
| freak_intern | 57 | 2 | 2 | 2 | 0.00 | 0.00 | 0.02 | 0.02 | 19 | 19 |
| freak_session | 178 | 6 | 6 | 8 | 0.02 | 0.02 | 0.06 | 0.06 | 19 | 19 |
| freak_target | 367 | 32 | 32 | 88 | 0.12 | 0.11 | 0.27 | 0.25 | 20 | 20 |
| freak_lex | 1,044 | 24 | 30 | 152 | 0.63 | 0.55 | 1.08 | 0.97 | 48 | 49 |
| freak_parse | 2,534 | 36 | 38 | 256 | 0.85 | 0.88 | 1.99 | 2.00 | 95 | 94 |
| freak_expand | 548 | 8 | 8 | 42 | 0.17 | 0.12 | 0.37 | 0.28 | 25 | 25 |
| freak_hir | 7,304 | 80 | 91 | 812 | 4.15 | 2.91 | 7.81 | 6.33 | 284 | 277 |
| freak_resolve | 997 | 14 | 19 | 122 | 0.22 | 0.21 | 0.51 | 0.50 | 35 | 35 |
| freak_ty | 14,210 | 105 | 110 | 2,374 | 11.62 | 7.28 | 18.06 | 13.93 | 512 | 496 |
| freak_mir | 6,926 | 139 | 162 | 1,373 | 29.18 | 6.71 | 33.97 | 10.94 | 516 | 386 |
| freak_mir_build | 10,474 | 17 | 28 | 1,989 | 7.27 | 5.82 | 12.48 | 10.63 | 382 | 377 |
| freak_borrowck | 9,206 | 180 | 191 | 1,376 | 3.58 | 3.13 | 8.07 | 7.54 | 330 | 334 |
| freak_codegen_llvm | 4,367 | 39 | 55 | 758 | 2.75 | 2.13 | 4.89 | 4.37 | 204 | 199 |
| freak_query | 1,530 | 27 | 33 | 169 | 2.36 | 0.64 | 2.93 | 1.18 | 69 | 56 |
| freak_driver | 785 | 6 | 6 | 103 | 0.21 | 0.16 | 0.45 | 0.40 | 28 | 28 |
| freak_editor | 3,572 | 51 | 61 | 62 | 0.24 | 0.26 | 1.71 | 1.89 | 107 | 107 |
| freak_snapshot | 4,670 | 14 | 26 | 986 | 4.50 | 2.46 | 6.47 | 4.43 | 190 | 176 |
| freak_lsp | 952 | 4 | 4 | 131 | 0.41 | 0.46 | 0.77 | 0.98 | 37 | 37 |

Counts are the "after" run (the `freak_borrowck` "before" Meiya count was 1,342 on its old source).

Tier 1 work since the old baseline already brought every crate under the limits on `main`. The outlier was `freak_mir`: 29 s of Meiya, about 21 s of it in one 415-line task (`v4_mir_snapshot_validate`) that passes `payload` to many word-taking calls, so strict mode sees one move per call.

## Synthetic: one word moved N times

One task moves the same word in N sibling `if` branches (N partial-move conflicts, 5N + 9 lines).

| Moves | Before | After |
| ---: | --- | --- |
| 100 | 6.97 s, 54 MiB | 0.41 s, 19 MiB |
| 200 | 55.86 s, 326 MiB | 1.35 s, 40 MiB |
| 400 | timeout at 120 s (599 MiB) | 5.08 s, 107 MiB |
| 800 | timeout at 120 s (663 MiB) | 19.36 s, 334 MiB |

Before grew about 8x to 9x per doubling (cubic). After grows about 3.3x to 3.8x (quadratic: one CFG walk per move). Without the reach row below, 800 moves ran out of memory in the cold `block_reaches` scan once the 1M-cell reach cache was full.

## What changed

`check_partial_moves` asked `move_repaired_before_use` for every overlapping move/use pair, and each question allocated two memo arrays and walked the CFG. Now each move builds one summary the first time it is needed:

- the move's open region: blocks entered unrepaired from the move block's successors, marked repairing or not;
- whether that region holds an unrepaired cycle (the memo walk answers false for every open question then);
- the move block's reachability row, so cross-block uses no longer go through the shared reach cache.

A use then needs two block scans: the move block after the move, and the use block from its start if the region entered it. The answer is the memo walk's, when every terminator target is in range (a repaired state can then never answer false). A body with an out-of-range target, a failed allocation or a use missing from its block's statement list falls back to the memo walk. `borrowck_cfg_scaling_smoke.fk` compares the summary answer and its reach row with the cold walks for every move/use pair of its bodies, and all 14 Meiya smokes pass.
