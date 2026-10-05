# V4 compiler scaling checkpoint

Compare `8ffb389508b8a8f37455ad83b4813062b3d11c2f` with
`d4bd677927a1ebd6d0e04608fc0e051f734fb7bc`. These are the measured
compiler inputs; subsequent documentation commits do not change those inputs.

Measurements use one Linux x64 host with Clang 19.1.7.

Median compiler execution seconds from three ordinary `-O2` runs per case:

| Shape | Size | Lines | Before | After | Time reduction |
|---|---:|---:|---:|---:|---:|
| tasks | 400 | 2,803 | 1.367 | 1.322 | 3.3% |
| tasks | 800 | 5,603 | 2.965 | 2.639 | 11.0% |
| tasks | 1600 | 11,203 | 5.897 | 5.531 | 6.2% |
| long | 400 | 2,075 | 1.319 | 0.739 | 44.0% |
| long | 800 | 4,131 | 3.883 | 1.366 | 64.8% |
| long | 1600 | 8,243 | 13.011 | 2.922 | 77.5% |
| calls | 400 | 1,627 | 1.883 | 1.938 | -2.9% |
| calls | 800 | 3,227 | 3.944 | 4.267 | -8.2% |

Long-body total doubling falls from 2.94x/3.35x to 1.85x/2.14x. At size1600,
MIR falls from 3.116 to 0.650 seconds, Meiya from 4.226 to 0.545 seconds, and
codegen from 5.290 to 1.349 seconds. Median peak memory falls from 292.0 to
231.9 MiB. Medians are calculated separately for every metric, so stage
medians need not sum to the median total.

The targeted work is repeated Parse closure-child scans, per-block MIR
predecessor scans, Meiya's write-by-all-path scan, and MIR Build's repeated
all-prior-rvalue Never scan. Owners retain derived facts or request scratch;
the existing validators, diagnostics and cold authoritative scanners remain.
Deterministic fixtures count actual reads/work and execute the original
scanners as controls, under 64 MiB and 1,024 live array handles.

Separate `-pg -O1 -fno-inline` profiles are excluded from timing medians.
For long1600, actual type getter calls fall from 21,060,043 to 948,359,
and path-kind getter calls from 47,609,934 to 3,665,686. For tasks1600,
Parse parent getter calls fall from 2,564,802 to zero.

All 33 matched row pairs (31 ordinary and two profile cases per compiler)
have identical generated sources, emitted LLVM modules and native exit/stdout/
stderr oracles. The seven runtime C files, seven headers and seven linked
runtime objects are identical. The checked-in
[JSON report](compiler_superlinear_speed.json) retains raw ordinary timings,
ranges, peaks, individual output hashes, stage diagnostics, tool/input pins,
profile counts and the full receipt digest.

Calls400/800 use the original support sample plus two repeats. Their baseline
repeats were collected in an earlier interleaved baseline/intermediate run;
final compiler repeats were collected later. Calls800 ranges were
3.943-4.049 seconds before and 3.906-4.269 seconds after. The observed medians
are slower; these results do not establish that every workload improves.
Other support shapes and tasks3200 have one matched run each, retained in the
JSON as single observations. Genuine spanning loans can still require
quadratic comparisons. This checkpoint measures compiler execution, not
generated-program runtime, and makes no global linearity or V3 parity claim.

Reproduce from either pinned checkout with Clang and LLVM symbol tools:

```sh
python -B -u v4_scale_bench.py --shapes tasks long --sizes 400 800 1600 --check \
  --timeout 300 --build-timeout 120 --mem-limit-mb 2048 --output-limit-mb 64 \
  --work /tmp/freak-scale-run-1 --json /tmp/freak-scale-run-1.json
```

Repeat three times with separate work/output paths. Use `--shapes calls
--sizes 400 800` for the call-count series and `--profile` for the separate
attribution run. Measured compiler execution caps are 300 seconds, 2,048 MiB
for the process group and 64 MiB per output stream. Native oracle execution
caps are 60 seconds, 128 MiB and 8 MiB per stream. Peaks are cumulative Linux
VmHWM, not incremental per-stage allocation. Hosted CI runs the checked
400/800/1600 task/long series and the deterministic fixtures; it has no
performance-regression threshold on measured wall times.
