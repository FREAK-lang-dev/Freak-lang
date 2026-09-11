#!/usr/bin/env python3
"""V3 conversion harmonization: int/num/bool.to_word() methods plus legacy aliases.

Proves the coherent method surface and the kept compatibility aliases agree on
both native backends with C/LLVM parity.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from v3_array_rescue import execute_case, run

POSITIVE = {
    "int_to_word": ('''task main() {
    pilot a = 42
    pilot b = 0 - 7
    pilot c = 0
    say a.to_word()
    say b.to_word()
    say c.to_word()
}
''', ["42", "-7", "0"]),
    "num_to_word": ('''task main() {
    pilot a = 2.5
    pilot b = 2.0
    pilot c = 0 - 0.75
    say a.to_word()
    say b.to_word()
    say c.to_word()
}
''', ["2.5", "2", "-0.75"]),
    "bool_to_word": ('''task main() {
    pilot flag_yes = true
    pilot flag_no = false
    say flag_yes.to_word()
    say flag_no.to_word()
}
''', ["true", "false"]),
    "numeric_cross": ('''task main() {
    pilot i = 7
    pilot n = 2.9
    say i.to_num()
    say n.to_int()
}
''', ["7", "2"]),
    "legacy_aliases": ('''task main() {
    say word_from_int(42)
    say word_from_bool(false)
    say format_num(2.5)
}
''', ["42", "false", "2.5"]),
}

NEGATIVE = {
}


def main() -> int:
    """Run the selected V3 conversion regression matrix."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("compiler", type=Path)
    parser.add_argument("--backend", choices=("c", "llvm"))
    parser.add_argument("--case", choices=sorted(set(POSITIVE) | set(NEGATIVE)))
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    compiler = args.compiler.resolve()

    repo = Path(__file__).resolve().parents[1]
    records = []
    with tempfile.TemporaryDirectory(prefix="freak-v3-conversions-") as temporary:
        root = Path(temporary)
        for backend in ([args.backend] if args.backend else ["c", "llvm"]):
            for name, (source, expected) in POSITIVE.items():
                if args.case and args.case != name:
                    continue
                print(f"RUN {name}/{backend}", flush=True)
                records.append(execute_case(compiler, repo, root, backend, name, source, expected))
                print(f"PASS {name}/{backend}", flush=True)
    if args.report:
        args.report.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    print(f"V3 conversions: PASS ({len(records)} contracts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
