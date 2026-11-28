# V4 safety suites

Small FREAK programs that pin what Maverick (V4) must accept, refuse, or trap
on, for the borrow checker (Meiya) and every other safety contract the V4
pipeline enforces today. Each case is one `.fk` file whose leading `--`
directives state the expected outcome; `run_safety.py` compiles every case with
the V4 compiler binary in strict root mode and checks the stage lines and
diagnostic records it prints. Run cases are linked against the native runtime
and executed.

```sh
python -u tests/v4_safety/run_safety.py                      # builds V4 (about 45 s), then runs all cases
python -u tests/v4_safety/run_safety.py --compiler PATH      # reuse a built compiler (or set FREAK_V4_COMPILER)
python -u tests/v4_safety/run_safety.py --area borrowck_lends --case shared_ --verbose
python -u tests/v4_safety/run_safety.py --list               # validate directives without compiling
python -B -m unittest discover -s tests/v4_safety -p "test_*.py"   # compiler-free runner tests
```

The whole corpus compiles in a few seconds: the compiler is invoked once per
case, there is no crate prepending as in the `src/compiler/v4/tests` smokes.

## Areas

| Area | What it covers |
|---|---|
| `borrowck_moves` | Copy vs move, use after move into calls/shapes/tuples/arrays/routes, reinitialization, branch and loop moves, partial moves and repair, by-value `self`, `for each` lending |
| `borrowck_lends` | `lend`/`lend mut` parameters, shared vs exclusive overlap, observation during an exclusive lend, move/rewrite while borrowed, last-use (non-lexical) expiry, aliased call arguments, call-site lend markers, temporaries, holders, reloans |
| `borrowck_lifetimes` | returned loans, named and elided lifetimes, outlives bounds (direct, reversed, transitive), `'static`, `'_`, returned-loan liveness at the caller, lends in tuples/shapes/arrays/lists/`some` |
| `borrowck_closures` | borrow/copy/move/mut capture modes, live captures, OneShot and MutCallable linearity |
| `mutability` | `fixed pilot` writes through every place form, root constants, strict root scope |
| `numeric` | checked arithmetic and conversion traps, explicit `.to_int`/`.to_uint`/`.to_tiny`, implicit fraction drops, literal range |
| `bounds` | fixed-array reads/writes/compound writes, nested arrays, word `char_at`/`substring`, tuple slots, index types, array lengths |
| `option_result` | `maybe`/`result` never unwrap implicitly, `check` arm completeness, `?`, `or else`, payload types, no null |
| `exhaustiveness` | `when`/`check route` exhaustiveness, unreachable arms, unknown cases, missing returns, `never` |
| `init` | definite initialization of locals |
| `unsafe` | `trust me` gating of raw-pointer read/write/deref/offset/cast, honor levels, `*const` writes, closures |
| `ffi` | FFI-safe extern parameter/return types, `@layout(C)`, `@repr`, unwinder imports, `@extern_callback`, callback types, `lend word` extern parameters (bytes and length, loans, refused word forms) |
| `shared` | `Shared<T>`/`Weak<T>`/`SharedMut<T>` surface rules |
| `dyn` | owned and boxed `dyn D` values: boxing, moves and by-value `self`, drops under flags and in slots, `List<dyn D>`, `lend dyn D` locals, and the surfaces still fenced by name |
| `types` | Yuuko: infinite shapes/variants, alias nominality and cycles, constant cycles, basic mismatches |
| `diagnostics` | message wording, spans, help text and error counts |

## Directives

See the docstring at the top of `run_safety.py` for the full list. The main
ones:

- `-- expect: check` means lex through borrowck report no errors. Native
  codegen is not consulted, so frontend rules can be tested before tier 3
  lowers the feature.
- `-- expect: reject <stage>` with one or more `-- error: <text>` lines. The
  text is matched against `message|help`. `-- at: L:C` pins the first error's
  position (file line and column) and `-- errors: N` pins the count.
- `-- expect: run` / `-- expect: panic` build, link and execute the program.
  Panics default to exit 101. `-- exit: nonzero` accepts any failure status
  (see #250).
- `-- known: #N note` marks a case that states the correct behavior for a
  filed bug and currently fails. The runner reports it as known. If it starts
  passing, the run fails with XPASS so the directive gets removed along with
  the fix.

Prefer `check` over `build` or `run` unless the case is about runtime
behavior. Keep cases independent of native features that tier 3 has not
lowered yet, so a backend change never flips a frontend expectation.
