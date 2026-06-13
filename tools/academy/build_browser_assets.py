#!/usr/bin/env python3
"""Build FREAK Academy browser-consumable assets."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from freakc.academy import build_browser_assets


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build FREAK Academy browser assets.")
    parser.add_argument("output", help="Directory to receive package, worker, and manifest files.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the generated manifest JSON instead of a human summary.",
    )
    args = parser.parse_args(argv)

    output_dir = Path(args.output)
    manifest = build_browser_assets(output_dir, root=ROOT)

    if args.json:
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return 0

    print(f"Academy browser assets exported to {output_dir}")
    print(f"  package: {manifest['packagePath']}")
    print(f"  worker:  {manifest['workerPath']} ({manifest['artifactStatus']})")
    print(f"  manifest: academy-assets-manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
