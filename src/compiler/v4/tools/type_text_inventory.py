#!/usr/bin/env python3
"""Architecture lane A2 inventory: every type-word read past TY.

Counts call sites of the word-returning type accessors (MIR's local, place,
rvalue, global, signature and row type accessors, and TY's word-returning type
helpers) in the crates past TY, and groups each call site by the question the
surrounding line asks of the spelling. Prints Markdown. Classification is
line-based and deliberately simple: it sizes the TypeId migration, it does not
prove anything about a single site.

Usage: python src/compiler/v4/tools/type_text_inventory.py [--json]
"""
from __future__ import annotations

import collections
import json
from pathlib import Path
import re
import subprocess
import sys

V4 = Path(__file__).resolve().parents[1]
CRATES = V4 / "crates"
CONSUMERS = ("freak_mir", "freak_mir_build", "freak_borrowck", "freak_codegen_llvm")

# MIR accessors that hand a type spelling to later stages.
MIR_TYPE_ACCESSORS = (
    "v4_mir_local_ty",
    "v4_mir_place_ty",
    "v4_mir_rvalue_ty",
    "v4_mir_local_ty_for_name",
    "v4_mir_expected_return_type",
    "v4_mir_global_ty",
    "v4_mir_body_callable_return_type",
    "v4_mir_body_callable_param_type",
    "v4_mir_builtin_shared_method_result_type",
    "v4_mir_control_row_type",
)

# Ordered: the first matching question wins for a call site.
QUESTIONS = (
    ("compares the spelling to a literal", re.compile(r'(?:==|!=)\s*"[^"]*"|"[^"]*"\s*(?:==|!=)|\.starts_with\(|\.ends_with\(|\.index_of\(|\.contains\(')),
    ("asks a TY predicate (is lend, is pointer, is Copy, compatible, ...)", re.compile(r"\bv4_ty_(?:is_[a-z0-9_]+|types_compatible|type_may_store_lend|native_sum_payload_[a-z_]+|param_mode_[a-z_]+)\s*\(")),
    ("decomposes the type (target, element, slot, generic argument, case)", re.compile(r"\bv4_ty_(?:lend_target_type|lend_mode|raw_pointer_target_type|fixed_array_[a-z_]+|tuple_slot_[a-z_]+|generic_(?:arg|arg_count|base_name)|native_sum_[a-z_]+|dyn_doctrine_[a-z_]+|canonical_type|normalize_ffi_alias_type|alias_[a-z_]+)\s*\(")),
    ("looks up a nominal signature by type name", re.compile(r"\bv4_ty_[a-z0-9_]*(?:_for_name|_sig)\s*\(")),
    ("selects an LLVM type or layout", re.compile(r"\bv4_codegen_llvm_[a-z0-9_]*(?:type|_ty|layout|size|align|abi|llvm)[a-z0-9_]*\s*\(")),
    ("decides ownership (Copy, move, drop, owned word)", re.compile(r"\bv4_(?:borrowck|mir)_[a-z0-9_]*(?:copy|move|drop|owned|word_local|loan|lend)[a-z0-9_]*\s*\(")),
    ("builds diagnostic or display text", re.compile(r"\bv4_diag_|error\s*=|\+\s*\"|\"\s*\+")),
    ("binds the spelling for a later question", re.compile(r"^\s*(?:pilot\s+[A-Za-z0-9_]+(?::\s*word)?|[A-Za-z0-9_]+)\s*=\s*")),
)
OTHER = "passes the spelling on (argument or return)"


def mask_comments(text: str) -> str:
    out = []
    for line in text.splitlines():
        in_string = False
        cut = len(line)
        index = 0
        while index < len(line):
            ch = line[index]
            if ch == "\\" and in_string:
                index += 2
                continue
            if ch == '"':
                in_string = not in_string
            elif not in_string and line.startswith("--", index):
                cut = index
                break
            index += 1
        out.append(line[:cut])
    return "\n".join(out)


def ty_word_type_accessors() -> list[str]:
    text = (CRATES / "freak_ty/src/lib.fk").read_text(encoding="utf-8")
    names = re.findall(r"(?m)^task\s+(v4_ty_[a-z0-9_]*(?:type|_ty)[a-z0-9_]*)\s*\([^\n]*\)\s*->\s*word\b", text)
    return sorted(set(names))


def classify(line: str) -> str:
    for label, pattern in QUESTIONS:
        if pattern.search(line):
            return label
    return OTHER


def inventory() -> dict:
    ty_accessors = ty_word_type_accessors()
    families = {"MIR type accessors": MIR_TYPE_ACCESSORS, "TY word type accessors": tuple(ty_accessors)}
    report: dict = {"crates": {}, "accessors": {}, "ty_accessor_count": len(ty_accessors)}
    for crate in CONSUMERS:
        lines = mask_comments((CRATES / crate / "src/lib.fk").read_text(encoding="utf-8")).splitlines()
        crate_report: dict = {}
        for family, names in families.items():
            pattern = re.compile(r"\b(" + "|".join(map(re.escape, names)) + r")\s*\(")
            questions: collections.Counter = collections.Counter()
            per_accessor: collections.Counter = collections.Counter()
            for line in lines:
                hits = pattern.findall(line)
                if not hits:
                    continue
                question = classify(line)
                for hit in hits:
                    questions[question] += 1
                    per_accessor[hit] += 1
            crate_report[family] = {"total": sum(per_accessor.values()), "questions": dict(questions)}
            for name, count in per_accessor.items():
                report["accessors"].setdefault(name, {})[crate] = count
        compares = [
            match
            for line in lines
            for match in re.findall(r'\b[A-Za-z0-9_]*(?:ty|type)[A-Za-z0-9_]*\s*(?:==|!=)\s*"([^"]*)"', line)
        ]
        crate_report["type spelling compared to a literal"] = len(compares)
        for spelling in compares:
            report.setdefault("literals", collections.Counter())[spelling or "(empty)"] += 1
        report["crates"][crate] = crate_report
    try:
        report["source"] = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=V4, capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        report["source"] = "unknown"
    return report


def markdown(report: dict) -> str:
    out = [f"Generated by `tools/type_text_inventory.py` at `{report['source']}`.", ""]
    out.append("| Crate | MIR type accessor reads | TY word type accessor reads | Type spelling compared to a literal |")
    out.append("|---|---|---|---|")
    totals = [0, 0, 0]
    for crate, data in report["crates"].items():
        row = (data["MIR type accessors"]["total"], data["TY word type accessors"]["total"], data["type spelling compared to a literal"])
        totals = [a + b for a, b in zip(totals, row)]
        out.append(f"| `{crate}` | {row[0]} | {row[1]} | {row[2]} |")
    out.append(f"| Total | {totals[0]} | {totals[1]} | {totals[2]} |")
    out.append("")
    out.append(f"TY word type accessors scanned: {report['ty_accessor_count']}.")
    out.append("")
    for family in ("MIR type accessors", "TY word type accessors"):
        out.append(f"### {family}, by question")
        out.append("")
        header = "| Question | " + " | ".join(f"`{c}`" for c in report["crates"]) + " |"
        out.append(header)
        out.append("|---|" + "---|" * len(report["crates"]))
        labels = [label for label, _ in QUESTIONS] + [OTHER]
        for label in labels:
            counts = [report["crates"][c][family]["questions"].get(label, 0) for c in report["crates"]]
            if any(counts):
                out.append(f"| {label} | " + " | ".join(str(n) for n in counts) + " |")
        out.append("")
    out.append("### Spellings compared against")
    out.append("")
    out.append("| Literal | Sites |")
    out.append("|---|---|")
    for spelling, count in report.get("literals", collections.Counter()).most_common(15):
        out.append(f"| `{spelling}` | {count} |")
    out.append("")
    out.append("### Most-read accessors")
    out.append("")
    out.append("| Accessor | " + " | ".join(f"`{c}`" for c in CONSUMERS) + " | Total |")
    out.append("|---|" + "---|" * (len(CONSUMERS) + 1))
    ranked = sorted(report["accessors"].items(), key=lambda kv: -sum(kv[1].values()))
    for name, per_crate in ranked[:20]:
        counts = [per_crate.get(c, 0) for c in CONSUMERS]
        out.append(f"| `{name}` | " + " | ".join(str(n) for n in counts) + f" | {sum(counts)} |")
    out.append("")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    report = inventory()
    if "--json" in argv:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
