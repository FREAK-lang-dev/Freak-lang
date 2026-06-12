#!/usr/bin/env python3
"""Export FREAK Academy lessons as one browser-consumable JSON package."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from freakc.academy import build_academy_package


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export FREAK Academy lesson package JSON.")
    parser.add_argument("--output", "-o", help="Write package JSON to this path instead of stdout.")
    args = parser.parse_args(argv)

    package = build_academy_package(ROOT)
    payload = json.dumps(package, indent=2, sort_keys=True) + "\n"

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
