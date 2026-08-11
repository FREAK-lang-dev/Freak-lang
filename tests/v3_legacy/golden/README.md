# V3 Legacy Golden Corpus

This directory is the small, permanent positive corpus for the final
self-hosted V3 compiler generation. It preserves representative behavior; it
is not a replacement for the conformance audit or the broader regression
suite.

`cases.json` is the complete inventory. Every case has one FREAK source file
and one exact expected-stdout file:

| Case | Preserved behavior |
|---|---|
| `01_core` | typed primitive bindings, integer arithmetic, booleans, and output |
| `02_control_tasks` | task calls, repetition, branching, `when`, and `training arc` |
| `03_shapes_methods` | shape and impl-method declaration lowering shared by both backends |
| `04_words_stdlib` | word method calls plus deterministic math and string stdlib calls |

Run the corpus with an explicit real V3 CLI:

```text
python -u tests/v3_legacy_golden.py <path-to-freak>
```

The runner always compiles and executes every case through both the C and LLVM
backends. It copies sources into a temporary directory, compares stdout after
normalizing only newline representation, checks any declared generated-code
marker, rejects stderr, and verifies that the tracked corpus did not change.
Generated C, LLVM IR, objects, and executables must never be committed here.

The cases are deliberately deterministic and offline. Ownership/leak stress,
concatenation scaling, ABI mismatch, malformed-source diagnostics, and
installer recovery have dedicated V3 regressions elsewhere; duplicating those
contracts here would make this historical signal harder to interpret.
