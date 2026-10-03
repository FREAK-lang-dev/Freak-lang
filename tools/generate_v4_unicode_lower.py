#!/usr/bin/env python3
"""Generate locale-neutral Unicode 17 lowercase tables from pinned official UCD.

The checked-in header is sufficient for builds and runtime: neither reads UCD
files or accesses the network. Regeneration uses --ucd-dir; --download is an
explicit input-fetch step and --check verifies byte-for-byte determinism.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import urllib.error
import urllib.request

VERSION = "17.0.0"
MIRROR_COMMIT = "6661370193d31b1cfb28a5b854ee8a894a95edbf"
OFFICIAL_BASE = f"https://www.unicode.org/Public/{VERSION}/ucd/"
MIRROR_BASE = f"https://raw.githubusercontent.com/unicode-org/unicodetools/{MIRROR_COMMIT}/unicodetools/data/ucd/{VERSION}/"
INPUT_SHA256 = {
    "UnicodeData.txt": "2e1efc1dcb59c575eedf5ccae60f95229f706ee6d031835247d843c11d96470c",
    "SpecialCasing.txt": "efc25faf19de21b92c1194c111c932e03d2a5eaf18194e33f1156e96de4c9588",
    "DerivedCoreProperties.txt": "24c7fed1195c482faaefd5c1e7eb821c5ee1fb6de07ecdbaa64b56a99da22c08",
    "LICENSE.txt": "fe5c62b543e287981db198f2acfa0ca732d12591a1024536dc8fd85dacd77104",
}
LICENSE_URL = f"https://raw.githubusercontent.com/unicode-org/unicodetools/{MIRROR_COMMIT}/LICENSE"


def verified_inputs(directory: Path) -> dict[str, str]:
    result = {}
    for name, expected in INPUT_SHA256.items():
        data = (directory / name).read_bytes()
        actual = hashlib.sha256(data).hexdigest()
        if actual != expected:
            raise ValueError(f"Unicode {VERSION} {name} SHA256 mismatch: expected {expected}, got {actual}")
        result[name] = data.decode("utf-8")
    return result


def download_inputs(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for name, expected in INPUT_SHA256.items():
        path = directory / name
        if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == expected:
            continue
        urls = [LICENSE_URL] if name == "LICENSE.txt" else [OFFICIAL_BASE + name, MIRROR_BASE + name]
        problems = []
        for url in urls:
            try:
                data = urllib.request.urlopen(url, timeout=30).read()
                if hashlib.sha256(data).hexdigest() != expected:
                    raise ValueError("input digest does not match pinned Unicode data")
                path.write_bytes(data)
                break
            except (OSError, urllib.error.URLError, ValueError) as error:
                problems.append(f"{url}: {error}")
        else:
            raise RuntimeError("could not fetch pinned Unicode input: " + " | ".join(problems))


def scalar(value: int) -> bool:
    return 0 <= value <= 0x10FFFF and not 0xD800 <= value <= 0xDFFF


def merged_ranges(values: list[tuple[int, int]]) -> list[tuple[int, int]]:
    merged: list[tuple[int, int]] = []
    for first, last in sorted(values):
        if not scalar(first) or not scalar(last) or first > last:
            raise ValueError("invalid Unicode property range")
        if merged and first <= merged[-1][1]:
            raise ValueError("overlapping Unicode property ranges")
        if merged and first == merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], last)
        else:
            merged.append((first, last))
    return merged


def tables(inputs: dict[str, str]) -> tuple[dict[int, tuple[int, ...]], dict[str, list[tuple[int, int]]]]:
    mapping = {}
    for line in inputs["UnicodeData.txt"].splitlines():
        fields = line.split(";")
        if len(fields) != 15:
            raise ValueError("invalid UnicodeData record")
        if fields[13]:
            source, target = int(fields[0], 16), int(fields[13], 16)
            if not scalar(source) or not scalar(target) or source in mapping:
                raise ValueError("invalid or duplicate simple lowercase mapping")
            mapping[source] = (target,)
    if len(mapping) != 1488:
        raise ValueError("unexpected Unicode 17 simple lowercase cardinality")
    unconditional = 0
    contextual = []
    for raw in inputs["SpecialCasing.txt"].splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        fields = [field.strip() for field in line.split(";")]
        source = int(fields[0], 16)
        lower = tuple(int(value, 16) for value in fields[1].split())
        condition = fields[4]
        if condition:
            # Language tailoring is deliberately outside default casing.
            if not any(language in condition.split() for language in ("tr", "az", "lt")):
                contextual.append((source, lower, condition))
            continue
        unconditional += 1
        if not lower or not scalar(source) or any(not scalar(value) for value in lower):
            raise ValueError("invalid full lowercase mapping")
        if lower == (source,):
            mapping.pop(source, None)
        else:
            mapping[source] = lower
    if unconditional != 103 or contextual != [(0x03A3, (0x03C2,), "Final_Sigma")]:
        raise ValueError("unexpected Unicode 17 special casing contract")
    if max(map(len, mapping.values())) != 2 or mapping[0x0130] != (0x0069, 0x0307):
        raise ValueError("unexpected Unicode 17 lowercase expansion contract")
    ranges = {"Cased": [], "Case_Ignorable": []}
    for raw in inputs["DerivedCoreProperties.txt"].splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        fields = [field.strip() for field in line.split(";")]
        if fields[1] not in ranges:
            continue
        endpoints = fields[0].split("..")
        first, last = int(endpoints[0], 16), int(endpoints[-1], 16)
        ranges[fields[1]].append((first, last))
    ranges = {name: merged_ranges(values) for name, values in ranges.items()}
    for name, expected in (("Cased", 4632), ("Case_Ignorable", 2794)):
        if sum(last - first + 1 for first, last in ranges[name]) != expected:
            raise ValueError(f"unexpected Unicode 17 {name} cardinality")
    return mapping, ranges


def render(inputs: dict[str, str]) -> str:
    mapping, ranges = tables(inputs)
    lines = ["/* Generated by tools/generate_v4_unicode_lower.py. Do not edit.",
             f" * Unicode {VERSION}; default full lowercase only, no locale tailoring.",
             f" * Official UCD: {OFFICIAL_BASE}",
             f" * Official Unicode organization mirror: {MIRROR_BASE}"]
    lines += [f" * {name} SHA256 {digest}" for name, digest in INPUT_SHA256.items()]
    lines += [f" * License source: {LICENSE_URL}", " * Unicode data copyright 2025 Unicode, Inc.", " *", *[" * " + line for line in inputs["LICENSE.txt"].splitlines()], " */", "",
              "#ifndef FREAK_V4_UNICODE_LOWER_TABLES_H", "#define FREAK_V4_UNICODE_LOWER_TABLES_H", "", "#include <stdint.h>", "",
              '#define FREAK_V4_UNICODE_LOWER_VERSION "17.0.0"',
              "typedef struct { uint32_t source, first, second; uint8_t length; } freak_v4_unicode_lower_mapping;",
              "typedef struct { uint32_t first, last; } freak_v4_unicode_property_range;", "",
              "static const freak_v4_unicode_lower_mapping freak_v4_unicode_lower_mappings[] = {"]
    for source, output in sorted(mapping.items()):
        lines.append(f"    {{0x{source:06X}, 0x{output[0]:06X}, 0x{output[1] if len(output) == 2 else 0:06X}, {len(output)}}},")
    lines += ["};", ""]
    for name, identifier in (("Cased", "cased"), ("Case_Ignorable", "case_ignorable")):
        lines += [f"static const freak_v4_unicode_property_range freak_v4_unicode_{identifier}[] = {{"]
        lines += [f"    {{0x{first:06X}, 0x{last:06X}}}," for first, last in ranges[name]]
        lines += ["};", ""]
    lines += ["#endif", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ucd-dir", type=Path, required=True)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "freakc/runtime/freak_v4_unicode_lower_tables.h")
    args = parser.parse_args()
    if args.download:
        download_inputs(args.ucd_dir)
    data = render(verified_inputs(args.ucd_dir)).encode("utf-8")
    if args.check:
        if args.output.read_bytes() != data:
            raise SystemExit("checked-in Unicode lowercase tables differ from pinned deterministic output")
    else:
        args.output.write_bytes(data)
    print(f"Unicode {VERSION} lowercase tables: {len(data)} bytes SHA256 {hashlib.sha256(data).hexdigest()} {'verified' if args.check else 'generated'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
