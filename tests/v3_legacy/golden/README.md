# V3 Legacy Golden Corpus

This directory is the small, permanent positive corpus for the final
self-hosted V3 compiler generation. It preserves representative behavior; it
is not a replacement for the conformance audit or the broader regression
suite.

`cases.json` is the complete schema-v2 inventory. Every case has one FREAK
source file, one exact expected-stdout file, an ordered unique backend list,
and backend-local generated-code markers:

| Case | Backends | Preserved behavior |
|---|---|---|
| `01_core` | C, LLVM | typed primitive bindings, integer arithmetic, booleans, and output |
| `02_control_tasks` | C, LLVM | task calls, repetition, branching, `when`, and `training arc` |
| `03_shapes_methods` | LLVM | real shape construction, field reads, and instance-method execution |
| `04_words_stdlib` | C, LLVM | word method calls plus deterministic math and string stdlib calls |
| `05_interpolation` | C, LLVM | scalar/path interpolation in direct, stored, and returned words |
| `06_shape_interpolation` | LLVM | dotted shape and `self` interpolation with method execution |

Run the corpus with an explicit real V3 CLI:

```text
python -u tests/v3_legacy_golden.py <path-to-freak>
```

The runner constructs an install-shaped temporary directory from the explicit
CLI plus only the runtime/std files in `packaging/distribution-files.manifest`,
then launches from outside the repository. An inherited poisoned `FREAK_HOME`
must override that healthy payload and fail a direct build; an internal child
must observe the poison, remove it, and pass the corpus through executable-local
payload discovery. This prevents an ambient installation or repository CWD
from certifying the wrong compiler payload.

Each case runs only its declared backends. The runner compares stdout after
normalizing only newline representation, checks backend-local generated-code
markers, rejects stderr, and verifies that the tracked corpus did not change.
Executable closure controls also reject an unlisted generated file and a
nested artifact directory. Generated C, LLVM IR, objects, and executables must
never be committed here.

The cases are deliberately deterministic and offline. Ownership/leak stress,
concatenation scaling, malformed-source diagnostics, and installer recovery
have dedicated V3 regressions elsewhere. ABI mismatch appears here only as the
payload-isolation control; duplicating broader contracts would make this
historical signal harder to interpret.
