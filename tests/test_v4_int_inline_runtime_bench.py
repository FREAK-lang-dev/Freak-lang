"""Adversarial deterministic controls for the checked-int runtime gate."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("int_inline_runtime_bench", ROOT / "tests/v4_int_inline_runtime_bench.py")
gate = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gate
SPEC.loader.exec_module(gate)


def wrapper(op):
    return f'''define internal i64 @freak_v4_int_{op}_inline(i64 %lhs, i64 %rhs) alwaysinline {{
entry:
  %checked = call {{ i64, i1 }} @llvm.s{op}.with.overflow.i64(i64 %lhs, i64 %rhs)
  %overflow = extractvalue {{ i64, i1 }} %checked, 1
  br i1 %overflow, label %failure, label %success
failure:
  %unused = call i64 @freak_v4_int_{op}(i64 %lhs, i64 %rhs)
  unreachable
success:
  %result = extractvalue {{ i64, i1 }} %checked, 0
  ret i64 %result
}}
'''


def module():
    return "".join(wrapper(op) for op in gate.OPERATIONS) + '''define ccc i64 @int_checked_hot_loop(i64 %seed, i64 %iterations) {
entry:
  br label %loop
loop:
  %a = call i64 @freak_v4_int_add_inline(i64 %seed, i64 17)
  %b = call i64 @freak_v4_int_add_inline(i64 %a, i64 1)
  %c = call i64 @freak_v4_int_sub_inline(i64 %b, i64 65536)
  %d = call i64 @freak_v4_int_sub_inline(i64 %c, i64 65536)
  %e = call i64 @freak_v4_int_sub_inline(i64 %d, i64 65536)
  %f = call i64 @freak_v4_int_mul_inline(i64 %e, i64 3)
  br i1 true, label %loop, label %done
done:
  ret i64 %f
}
'''


def report(sanitized=False):
    variants = ["current", "helper-mutation"]
    empty = gate.text_sha("")
    value = {"variants": variants, "sanitized": sanitized, "samples": 3, "iterations": 100,
             "seed": 17, "structural": gate.validate_inline(module()),
             "negative_control": gate.validate_helper(gate.helper_mutation(module())[0]),
             "boundaries": [], "dynamic": [], "optimized": [], "timings": [], "medians": [],
             "controls": [f"audit-{kind}-O{opt}" for kind in ("C", "LLVM") for opt in gate.OPTS],
             "build_flags": {}, "runtime_objects": {}}
    pin = "a" * 64
    value.update(compiler_head="b" * 40, clang={"sha256": pin}, source_sha256=pin,
                 compiler_inputs={"benchmarks/v4/int_checked_hot_loop.fk": pin},
                 compiler={"binary_sha256": pin, "generated_c_sha256": pin, "live_handle_limit": 1024},
                 runtime_sources={f"source-{i}": pin for i in range(7)},
                 runtime_headers={f"header-{i}": pin for i in range(7)},
                 artifact_sha256={f"runtime-{i}": pin for i in range(7)})
    for opt in gate.OPTS:
        value["build_flags"][str(opt)] = [f"-O{opt}", "-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1", "-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1"]
        if sanitized:
            value["build_flags"][str(opt)].append("-fsanitize=address,undefined,float-cast-overflow")
        value["runtime_objects"][str(opt)] = {f"runtime-{i}": "a" * 64 for i in range(7)}
        for variant in variants:
            for n, seed in gate.BOUNDARY_INPUTS:
                value["boundaries"].append({"variant": variant, "optimization": opt,
                    "iterations": n, "seed": seed, "exit": 0,
                    "module_sha256": pin, "binary_sha256": pin,
                    "stdout_sha256": gate.text_sha(str(gate.checksum(n, seed)) + "\n"), "stderr_sha256": empty})
            value["optimized"].append({"variant": variant, "optimization": opt,
                "module_sha256": pin, "binary_sha256": pin, "optimized_module_sha256": pin,
                "facts": {"reachable_cycle": True, "dynamic_int64_inputs": 2}})
            if not sanitized:
                for sample in range(3):
                    value["timings"].append({"variant": variant, "optimization": opt, "sample": sample,
                        "elapsed_ns": 1000 + sample, "exit": 0,
                        "module_sha256": pin, "binary_sha256": pin,
                        "stdout_sha256": gate.text_sha(str(gate.checksum(100, 17)) + "\n"), "stderr_sha256": empty})
                value["medians"].append({"variant": variant, "optimization": opt, "samples": 3, "median_ns": 1001})
        for index, case in enumerate(gate.dynamic_cases()):
            value["dynamic"].append({"case": index, "optimization": opt,
                "module_sha256": pin, "binary_sha256": pin,
                "argv": case["argv"], "exit": case["exit"],
                "stdout_sha256": gate.text_sha(case["stdout"]), "stderr_sha256": gate.text_sha(case["stderr"])})
    if sanitized:
        value["controls"] += ["sanitizer-address", "sanitizer-undefined"]
    return value


class IntRuntimeOracles(unittest.TestCase):
    def test_geometric_oracle_against_unbounded_direct_integer_recurrence(self):
        for seed in (0, 1, 17, 21845, 65535):
            state = seed
            for n in range(513):
                self.assertEqual(gate.checksum(n, seed), state)
                state = (state * 3 + 17) % 65536
        for n, seed in ((-1, 0), (100000001, 0), (0, -1), (0, 65536)):
            with self.assertRaises(gate.GateError):
                gate.checksum(n, seed)

    def test_wrappers_require_actual_intrinsic_and_cold_same_operation_failure(self):
        clean = module()
        gate.validate_inline(clean)
        mutations = [clean.replace("internal i64", "i64", 1),
                     clean.replace("alwaysinline", "noinline", 1),
                     clean.replace("sadd.with.overflow.i64", "sadd.with.overflow.i32", 1),
                     clean.replace("label %failure, label %success", "label %success, label %failure", 1),
                     clean.replace("%unused = call i64 @freak_v4_int_add", "%unused = call i64 @freak_v4_int_sub", 1),
                     clean.replace("unreachable", "ret i64 0", 1),
                     clean.replace("ret i64 %result", "ret i64 %lhs", 1),
                     clean.replace("%checked, 1", "%checked, 0", 1),
                     clean.replace("%checked, 0", "%checked, 1", 1)]
        for changed in mutations:
            with self.subTest(changed=changed[:100]), self.assertRaises(gate.GateError):
                gate.validate_inline(changed)

    def test_helper_declarations_comments_and_unrelated_bodies_do_not_count(self):
        clean = module()
        gate.validate_inline("declare i64 @freak_v4_int_add(i64, i64)\n" + clean)
        without = clean.replace("  %f = call i64 @freak_v4_int_mul_inline(i64 %e, i64 3)",
                                "  ; %f = call i64 @freak_v4_int_mul_inline(i64 %e, i64 3)")
        with self.assertRaises(gate.GateError):
            gate.validate_inline(without)
        with self.assertRaises(gate.GateError):
            gate.validate_inline(clean.replace("@int_checked_hot_loop", "@unrelated"))
        with self.assertRaises(gate.GateError):
            gate.validate_inline(clean + clean)

    def test_negative_control_changes_executable_calls_preserving_cold_wrapper_bodies(self):
        clean = module()
        changed, manifest = gate.helper_mutation(clean)
        self.assertEqual(len(manifest["rewrites"]), 6)
        self.assertEqual(manifest["original_module_sha256"], gate.text_sha(clean))
        self.assertEqual(manifest["mutated_module_sha256"], gate.text_sha(changed))
        self.assertEqual(gate.definitions(changed)["freak_v4_int_add_inline"],
                         gate.definitions(clean)["freak_v4_int_add_inline"])
        self.assertEqual(gate.validate_helper(changed)["actual_helper_calls"], {"add": 2, "sub": 3, "mul": 1})
        with self.assertRaisesRegex(gate.GateError, "hot loop calls original numeric helpers"):
            gate.validate_inline(changed)
        with self.assertRaises(gate.GateError):
            gate.validate_helper(clean)

    def test_optimized_evidence_requires_reachable_cycle_dynamic_inputs_and_no_wrapper_calls(self):
        changed, _ = gate.helper_mutation(module())
        gate.validate_live_loop(changed, helpers=True)
        for bad in (changed.replace("label %loop, label %done", "label %done, label %done"),
                    changed.replace("i64 %iterations", "i32 %iterations"),
                    changed.replace("call i64 @freak_v4_int_mul(", "call i64 @freak_v4_int_mul_inline(")):
            with self.assertRaises(gate.GateError):
                gate.validate_live_loop(bad, helpers=True)

    def test_dynamic_cases_cover_both_overflow_directions_boundaries_and_effects(self):
        cases = {tuple(row["argv"]): row for row in gate.dynamic_cases()}
        for mode, left, right in ((0, gate.MAXIMUM, 1), (0, gate.MINIMUM, -1),
                                  (1, gate.MINIMUM, 1), (1, gate.MAXIMUM, -1),
                                  (2, gate.MINIMUM, -1), (2, -1, gate.MINIMUM)):
            row = cases[(str(mode), str(left), str(right))]
            self.assertEqual(row["exit"], 1)
            self.assertEqual(row["stdout"], f"{left}\n{right}\n")
            self.assertIn("overflow", row["stderr"])
        for mode in (4, 5):
            row = cases[(str(mode), str(gate.MAXIMUM), "1")]
            self.assertEqual((row["exit"], row["stdout"], row["stderr"]), (0, "short-circuit\n", ""))
        self.assertEqual(cases[("3", "19", "23")]["stdout"], "19\n23\ndiscarded\n")

    def test_report_rejects_incomplete_opts_references_outputs_and_medians(self):
        clean = report()
        gate.validate_report(clean)
        changed = []
        bad = deepcopy(clean); bad["boundaries"].pop(); changed.append(bad)
        bad = deepcopy(clean); bad["boundaries"][-1] = bad["boundaries"][0]; changed.append(bad)
        bad = deepcopy(clean); bad["boundaries"][0]["stdout_sha256"] = gate.text_sha("wrong\n"); changed.append(bad)
        bad = deepcopy(clean); bad["dynamic"][0]["exit"] = 86; changed.append(bad)
        bad = deepcopy(clean); bad["dynamic"][0]["stderr_sha256"] = gate.text_sha("sanitizer error\n"); changed.append(bad)
        bad = deepcopy(clean); bad["timings"].pop(); changed.append(bad)
        bad = deepcopy(clean); bad["timings"][0]["elapsed_ns"] = 0; changed.append(bad)
        bad = deepcopy(clean); bad["medians"][0]["median_ns"] = 2000; changed.append(bad)
        bad = deepcopy(clean); bad["controls"].pop(); changed.append(bad)
        bad = deepcopy(clean); bad["optimized"][0]["facts"]["reachable_cycle"] = False; changed.append(bad)
        bad = deepcopy(clean); bad["runtime_objects"]["2"].popitem(); changed.append(bad)
        bad = deepcopy(clean); bad["build_flags"]["3"].pop(); changed.append(bad)
        bad = deepcopy(clean); bad["variants"] = []; changed.append(bad)
        bad = deepcopy(clean); bad["source_sha256"] = "wrong"; changed.append(bad)
        bad = deepcopy(clean); bad["clang"]["sha256"] = "wrong"; changed.append(bad)
        bad = deepcopy(clean); bad["runtime_headers"].popitem(); changed.append(bad)
        bad = deepcopy(clean); bad["artifact_sha256"]["runtime-0"] = "b" * 64; changed.append(bad)
        bad = deepcopy(clean); bad["dynamic"][0].pop("binary_sha256"); changed.append(bad)
        for bad in changed:
            with self.assertRaises(gate.GateError):
                gate.validate_report(bad)

    def test_sanitized_proofs_cannot_supply_runtime_speed_numbers(self):
        clean = report(True)
        gate.validate_report(clean)
        clean["timings"] = report()["timings"]
        with self.assertRaisesRegex(gate.GateError, "sanitizer timings"):
            gate.validate_report(clean)


if __name__ == "__main__":
    unittest.main()
