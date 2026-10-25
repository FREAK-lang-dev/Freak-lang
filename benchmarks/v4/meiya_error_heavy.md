# V4 Meiya on error-heavy input

This closes the tier 2 row "Meiya on error-heavy input: bounded time and memory". At the last recorded baseline (probe built at `4f895d6`), 10 compiler crates timed out or exceeded 2 GiB in Meiya when each was compiled alone in strict mode.

Setup: one Linux x64 host (4 vCPU) with Ubuntu Clang 18.1.3. `benchmarks/v4/meiya_error_heavy.py` builds a probe from `tools/build_llvm.fk` (Python-built, `-O0`, like the smoke harness) that keeps going after errors and stops after Meiya. Each process runs under `prlimit --as` 2 GiB with a 60 s timeout per crate (300 s per synthetic size; 120 s for the "before" run). "Before" is `main` at `5ffec30`; "after" is this branch. Raw rows, probe hashes and source hashes are in the [JSON report](meiya_error_heavy.json).

## Compiler crates, strict, one at a time

Diagnostics are stage totals (inherited between stages). Except for `freak_borrowck`, whose source this branch changes, every crate reports the same counts before and after.

| Crate | Lines | Parse | MIR | Meiya | Meiya s before | Meiya s after | Total s before | Total s after | Peak MiB after |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| freak_span | 200 | 2 | 2 | 14 | 0.05 | 0.04 | 0.15 | 0.10 | 6 |
| freak_diag | 78 | 4 | 4 | 9 | 0.01 | 0.01 | 0.05 | 0.05 | 0 |
| freak_macro_api | 583 | 20 | 20 | 231 | 0.24 | 0.20 | 0.51 | 0.46 | 27 |
| freak_arena | 96 | 3 | 3 | 3 | 0.02 | 0.01 | 0.05 | 0.05 | 0 |
| freak_intern | 57 | 2 | 2 | 2 | 0.01 | 0.01 | 0.05 | 0.06 | 2 |
| freak_session | 178 | 6 | 6 | 8 | 0.03 | 0.02 | 0.10 | 0.10 | 8 |
| freak_target | 367 | 32 | 32 | 88 | 0.12 | 0.17 | 0.30 | 0.36 | 20 |
| freak_lex | 1,044 | 24 | 30 | 152 | 0.55 | 0.50 | 0.96 | 1.01 | 48 |
| freak_parse | 2,534 | 36 | 38 | 256 | 0.85 | 0.79 | 1.82 | 1.82 | 94 |
| freak_expand | 548 | 8 | 8 | 42 | 0.16 | 0.13 | 0.36 | 0.35 | 24 |
| freak_hir | 7,304 | 80 | 91 | 812 | 3.84 | 2.89 | 7.14 | 6.58 | 276 |
| freak_resolve | 997 | 14 | 19 | 122 | 0.25 | 0.27 | 0.66 | 0.76 | 34 |
| freak_ty | 14,210 | 105 | 110 | 2,374 | 9.70 | 6.88 | 16.59 | 13.88 | 494 |
| freak_mir | 6,926 | 139 | 162 | 1,373 | 26.75 | 6.08 | 31.51 | 10.73 | 386 |
| freak_mir_build | 10,474 | 17 | 28 | 1,989 | 6.44 | 4.51 | 12.25 | 10.31 | 376 |
| freak_borrowck | 9,206 | 180 | 191 | 1,376 | 3.83 | 3.91 | 8.36 | 9.69 | 333 |
| freak_codegen_llvm | 4,367 | 39 | 55 | 758 | 2.89 | 2.24 | 5.37 | 4.76 | 199 |
| freak_query | 1,530 | 27 | 33 | 169 | 2.38 | 0.54 | 2.93 | 1.07 | 55 |
| freak_driver | 785 | 6 | 6 | 103 | 0.18 | 0.17 | 0.46 | 0.46 | 28 |
| freak_editor | 3,572 | 51 | 61 | 62 | 0.24 | 0.21 | 1.82 | 1.58 | 103 |
| freak_snapshot | 4,670 | 14 | 26 | 986 | 4.48 | 2.37 | 6.49 | 4.62 | 176 |
| freak_lsp | 952 | 4 | 4 | 131 | 0.42 | 0.35 | 0.76 | 0.66 | 36 |

Counts are the "after" run (the `freak_borrowck` "before" Meiya count was 1,342 on its old source).

Tier 1 work since the old baseline already brought every crate under the limits on `main`. The outlier was `freak_mir`: 27 s of Meiya, 21 s of it in one 415-line task (`v4_mir_snapshot_validate`) that passes `payload` to many word-taking calls, so strict mode sees one move per call.

## Synthetic: one word moved N times

One task moves the same word in N sibling `if` branches (N partial-move conflicts, 5N + 9 lines).

| Moves | Before | After |
| ---: | --- | --- |
| 100 | 6.78 s, 54 MiB | 0.51 s, 18 MiB |
| 200 | 62.54 s, 326 MiB | 1.57 s, 40 MiB |
| 400 | timeout at 120 s (607 MiB) | 5.48 s, 106 MiB |
| 800 | timeout at 120 s (686 MiB) | 21.61 s, 332 MiB |

Before grew about 9x per doubling (cubic). After grows about 3.5x to 4x (quadratic: one CFG walk per move). Without the reach row below, 800 moves ran out of memory in the cold `block_reaches` scan once the 1M-cell reach cache was full.

## What changed

`check_partial_moves` asked `move_repaired_before_use` for every overlapping move/use pair, and each question allocated two memo arrays and walked the CFG. Now each move builds one summary the first time it is needed:

- the move's open region: blocks entered unrepaired from the move block's successors, marked repairing or not;
- whether that region holds an unrepaired cycle (the memo walk answers false for every open question then);
- the move block's reachability row, so cross-block uses no longer go through the shared reach cache.

A use then needs two block scans: the move block after the move, and the use block from its start if the region entered it. The answer is the memo walk's, when every terminator target is in range (a repaired state can then never answer false). A body with an out-of-range target, a failed allocation or a use missing from its block's statement list falls back to the memo walk. `borrowck_cfg_scaling_smoke.fk` compares the summary answer and its reach row with the cold walks for every move/use pair of its bodies, and all 14 Meiya smokes pass.
