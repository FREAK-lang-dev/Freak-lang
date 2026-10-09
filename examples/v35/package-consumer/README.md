# Diamond package consumer

Copy this complete directory outside the FREAK checkout, then run:

```sh
freak build --c --strict-borrow
freak run --c --strict-borrow
freak test --c --jobs=2
freak build --llvm --strict-borrow --frozen
freak run --llvm --strict-borrow --frozen
freak test --llvm --jobs=2 --frozen
```

The program prints `42`. Left and right each export `value` under an alias,
declare a private `helper` with the same name, and consume the same core
dependency. Core must resolve once. Consumers see only the declared exports;
there is no source concatenation step, private compiler API, or library main.

The first build creates `hangar.lock`. Frozen builds require exact recorded
inputs. Source edits require an ordinary build to record the new graph. Build
outputs follow the selected output path; graph snapshots and test staging use
`.freak`. Remove only this example's explicitly selected outputs and owned cache
when cleaning it. The acceptance harness has a separate `--story=freshness` gate
for transitive run-cache behavior; these component checks do not establish a
final release archive.
