"""Pure adversarial checks for the closed cross-target C scalar IR oracle."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location("c_integer_oracle", Path(__file__).with_name("v4_c_integer_oracle.py"))
oracle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oracle)


def sample(target: str, *, extension: str = "") -> str:
    lines = [f'target triple = "{target}"', 'target datalayout = "e-m:e-i64:64-n32:64-S128"']
    attr = extension + " " if extension else ""
    for key in oracle.SCALARS:
        size = oracle.TARGET_LONG_BYTES[target] if key in ("c_long", "c_ulong") else 4
        signed = int(key in ("c_int", "c_long"))
        carrier = f"i{size * 8}"
        for name, value in (("size", size), ("align", size), ("signed", signed)):
            lines.append(f"@oracle_{name}_{key} = constant i64 {value}, align 8")
        for mode in ("identity", "direct", "indirect"):
            parameters = f"{carrier} {attr}noundef %value"
            if mode == "indirect":
                parameters = "ptr noundef %callback, " + parameters
            lines.append(f"define dso_local {attr}{carrier} @oracle_{mode}_{key}({parameters}) {{")
            if mode != "identity":
                callee = f"@oracle_identity_{key}" if mode == "direct" else "%callback"
                lines.append(f"  %result = call {attr}{carrier} {callee}({carrier} {attr}noundef %value)")
            lines.extend((f"  ret {carrier} %value", "}"))
    return "\n".join(lines) + "\n"


class CIntegerOracle(unittest.TestCase):
    def test_all_four_requested_targets_and_signed_storage(self):
        for target, long_bytes in oracle.TARGET_LONG_BYTES.items():
            with self.subTest(target=target):
                facts = oracle.parse_oracle(sample(target), target)
                self.assertEqual(facts["scalars"]["c_long"]["size"], long_bytes)
                self.assertEqual(facts["scalars"]["c_int"]["width"], 32)
                self.assertEqual(facts["scalars"]["c_int"]["signed"], 1)
                self.assertEqual(facts["scalars"]["c_uint"]["signed"], 0)

    def test_measured_extension_is_retained_without_inventing_policy(self):
        target = "x86_64-unknown-linux-gnu"
        facts = oracle.parse_oracle(sample(target, extension="signext"), target)
        self.assertEqual(facts["scalars"]["c_int"]["return"]["extension"], "signext")
        self.assertEqual(facts["scalars"]["c_uint"]["parameter"]["extension"], "signext")

    def test_host_output_cannot_satisfy_another_target(self):
        with self.assertRaisesRegex(ValueError, "target triple"):
            oracle.parse_oracle(sample("x86_64-unknown-linux-gnu"), "x86_64-w64-windows-gnu")
        with self.assertRaisesRegex(ValueError, "unknown requested target"):
            oracle.parse_oracle(sample("x86_64-unknown-linux-gnu"), "host")

    def test_darwin_normalization_is_explicit_and_architecture_bound(self):
        requested = "aarch64-apple-darwin"
        text = sample(requested).replace(requested, "arm64-apple-macosx11.0.0")
        self.assertEqual(oracle.parse_oracle(text, requested)["observed_triple"], "arm64-apple-macosx11.0.0")
        with self.assertRaisesRegex(ValueError, "target triple"):
            oracle.parse_oracle(text.replace("arm64-", "x86_64-"), requested)

    def test_missing_duplicate_and_forged_layout_measurements_reject(self):
        target = "x86_64-w64-windows-gnu"
        text = sample(target)
        row = "@oracle_size_c_long = constant i64 4, align 8\n"
        for malformed in (text.replace(row, ""), text + row,
                          text.replace(row, row.replace("i64 4", "i64 8")),
                          text.replace("@oracle_signed_c_uint = constant i64 0", "@oracle_signed_c_uint = constant i64 1"),
                          text.replace('target datalayout = "e-', 'target datalayout = "E-')):
            with self.subTest(malformed=malformed[:100]), self.assertRaises(ValueError):
                oracle.parse_oracle(malformed, target)

    def test_missing_or_duplicate_function_and_call_reject(self):
        target = "x86_64-unknown-linux-gnu"
        text = sample(target)
        for malformed in (text.replace("@oracle_identity_c_int(", "@not_oracle_identity_c_int(", 1),
                          text + "define i32 @oracle_identity_c_int(i32 %v) {\n ret i32 %v\n}\n",
                          text.replace("  %result = call i32 @oracle_identity_c_int(i32 noundef %value)\n", ""),
                          text.replace("  %result = call i32 %callback(i32 noundef %value)\n", "", 1)):
            with self.subTest(malformed=malformed[:100]), self.assertRaises(ValueError):
                oracle.parse_oracle(malformed, target)

    def test_direct_and_indirect_call_width_and_extension_mismatches_reject(self):
        target = "x86_64-unknown-linux-gnu"
        text = sample(target)
        for old, new in (
            ("call i32 @oracle_identity_c_int", "call i64 @oracle_identity_c_int"),
            ("call i32 @oracle_identity_c_int", "call signext i32 @oracle_identity_c_int"),
            ("call i32 %callback(i32 noundef %value)", "call i32 %callback(i32 zeroext noundef %value)"),
            ("ptr noundef %callback, i32", "i64 noundef %callback, i32"),
            ("define dso_local i32 @oracle_direct_c_int", "define dso_local zeroext i32 @oracle_direct_c_int"),
        ):
            with self.subTest(new=new), self.assertRaises(ValueError):
                oracle.parse_oracle(text.replace(old, new, 1), target)


if __name__ == "__main__":
    unittest.main()
