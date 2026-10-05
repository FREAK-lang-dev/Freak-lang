"""Adversarial deterministic controls for the checked-int runtime gate."""
from copy import deepcopy
import hashlib
import importlib.util
import io
import json
from pathlib import Path, PureWindowsPath
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

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


def historical_report():
    value = report()
    value["target"] = "x86_64-unknown-linux-gnu"
    value["clang"]["resolved"] = "/toolchain/clang"
    value["variants"].append("historical-baseline")
    for name in ("boundaries", "optimized", "timings", "medians"):
        for row in list(value[name]):
            if row["variant"] == "helper-mutation":
                value[name].append({**row, "variant": "historical-baseline"})
    pin, head, tree = "a" * 64, "b" * 40, "c" * 40
    work = Path("/evidence/historical-producer")
    bundle = work / "compiler"
    entries = {name: {"mode": "100644", "blob": "d" * 40, "size": 1, "sha256": pin}
               for name in ("src/compiler/v4/build_v4.py", "src/compiler/v4/check_v4.py")}
    provenance = {"kind": gate.BASELINE_KIND, "compiler_head": head, "compiler_tree": tree,
        "compiler_inputs": entries, "compiler_manifest_sha256": gate.baseline_manifest_sha(entries),
        "bundle_path": str(bundle), "target": value["target"], "module_bytes_equal": True,
        "source_sha256": pin, "module_sha256": pin, "regenerated_module_sha256": pin}
    for path_key, hash_key, name in (("archive_path", "archive_sha256", "compiler.tar"),
            ("source_path", "source_sha256", "hot-loop.fk"), ("path", "module_sha256", "supplied.ll"),
            ("regenerated_module_path", "regenerated_module_sha256", "regenerated.ll"),
            ("verified_object_path", "verified_object_sha256", "verified.o"),
            ("producer_audit_path", "producer_audit_sha256", "producer.json"),
            ("producer_wrapper_path", "producer_wrapper_sha256", "produce.py"),
            ("manifest_path", "manifest_file_sha256", "compiler-inputs.json")):
        provenance[path_key], provenance[hash_key] = str(work / name), pin
        value["artifact_sha256"][provenance[path_key]] = pin
    provenance["git"] = {"selected": "git", "resolved": "/tools/git", "sha256": pin}
    provenance["python"] = {"selected": sys.executable, "resolved": "/tools/python", "sha256": pin}
    value["artifact_sha256"].update({"/tools/git": pin, "/tools/python": pin})
    compiler, generated = str(work / "bootstrap/build_llvm"), str(work / "bootstrap/build_llvm.fk.c")
    value["artifact_sha256"].update({compiler: pin, generated: pin})
    commands = [[value["clang"]["resolved"], "-DFREAK_ARRAY_LIVE_LIMIT=1024", "-O2"],
        [compiler, provenance["source_path"], value["target"]],
        [value["clang"]["resolved"], "--target=" + value["target"], "-x", "ir", "-c",
         provenance["regenerated_module_path"], "-o", provenance["verified_object_path"]]]
    labels = ["runtime compile: src/compiler/v4/tools/build_llvm.fk", "V4 compile: hot-loop.fk", "V4 LLVM verification"]
    producer_jobs = [{"command": command, "label": label, "exit": 0, "elapsed_ns": 100,
                      "timeout_seconds": 120, "memory_limit_mib": 512, "output_limit_mib_per_stream": 8,
                      "stdout_sha256": pin, "stderr_sha256": pin} for command, label in zip(commands, labels)]
    provenance["producer"] = {"exit": 0, "fresh_bootstrap": True,
        "entrypoint": str(bundle / "src/compiler/v4/build_v4.py"), "compiler_binary": compiler,
        "compiler_binary_sha256": pin, "generated_c": generated, "generated_c_sha256": pin, "jobs": producer_jobs}
    git_prefix = ["git", "-C", str(gate.ROOT)]
    commands = [[*git_prefix, "rev-parse", "--verify", head + "^{commit}"],
        [*git_prefix, "rev-parse", "--verify", head + "^{tree}"],
        [*git_prefix, "ls-tree", "-r", "-l", "-z", "--full-tree", head],
        [*git_prefix, "archive", "--format=tar", "--output=" + provenance["archive_path"], head],
        [sys.executable, "-I", "-B", provenance["producer_wrapper_path"], json.dumps({"bundle": str(bundle),
          "work": str(work), "source": provenance["source_path"], "module": provenance["regenerated_module_path"],
          "clang": value["clang"]["resolved"], "target": value["target"]}, sort_keys=True)]]
    labels = ["baseline resolve commit", "baseline resolve tree", "baseline list Git blobs",
              "baseline archive pinned compiler", "baseline regenerate and verify LLVM"]
    value["jobs"] = [{"serial": i, "command": command, "label": label, "exit": 0,
                      "timeout_seconds": 120, "memory_limit_mib": 512, "output_limit_mib_per_stream": 8,
                      "stdout_sha256": gate.text_sha(head + "\n") if i == 1 else gate.text_sha(tree + "\n") if i == 2 else pin}
                     for i, (command, label) in enumerate(zip(commands, labels), 1)]
    provenance["producer_job_serials"] = list(range(1, 6))
    value["historical_baseline"] = provenance
    return value


class IntRuntimeOracles(unittest.TestCase):
    def test_historical_helper_mutation_cannot_be_relabelled_by_three_caller_hashes(self):
        genuine = historical_report()
        gate.validate_report(genuine)
        supplied_only = deepcopy(genuine)
        supplied_only["historical_baseline"] = {key: genuine["historical_baseline"][key]
            for key in ("compiler_head", "source_sha256", "module_sha256", "path")}
        with self.assertRaisesRegex(gate.GateError, "regeneration provenance"):
            gate.validate_report(supplied_only)
        helper_only = report()
        helper_only["historical_baseline"] = genuine["historical_baseline"]
        with self.assertRaisesRegex(gate.GateError, "helper-only"):
            gate.validate_report(helper_only)

    def test_historical_producer_matrix_requires_real_successful_bounded_jobs(self):
        clean = historical_report()
        mutations = []
        for key, value in (("compiler_head", "wrong"), ("compiler_tree", "wrong"),
                ("source_sha256", "b" * 64), ("target", "foreign-target"),
                ("regenerated_module_sha256", "b" * 64), ("module_bytes_equal", False),
                ("compiler_manifest_sha256", "b" * 64)):
            bad = deepcopy(clean); bad["historical_baseline"][key] = value; mutations.append(bad)
        for key, value in (("exit", 1), ("fresh_bootstrap", False), ("compiler_binary_sha256", "b" * 64)):
            bad = deepcopy(clean); bad["historical_baseline"]["producer"][key] = value; mutations.append(bad)
        for key, value in (("exit", 1), ("memory_limit_mib", 513), ("timeout_seconds", 121),
                ("command", ["unverified-clang"]), ("label", "claimed verification")):
            bad = deepcopy(clean); bad["historical_baseline"]["producer"]["jobs"][-1][key] = value; mutations.append(bad)
        bad = deepcopy(clean); bad["historical_baseline"]["producer"]["jobs"].pop(); mutations.append(bad)
        bad = deepcopy(clean); bad["historical_baseline"]["producer_job_serials"].pop(); mutations.append(bad)
        bad = deepcopy(clean); bad["jobs"][0]["stdout_sha256"] = "a" * 64; mutations.append(bad)
        bad = deepcopy(clean); bad["jobs"][-1]["exit"] = 1; mutations.append(bad)
        for bad in mutations:
            with self.subTest(provenance=bad["historical_baseline"]), self.assertRaises(gate.GateError):
                gate.validate_report(bad)

    def test_historical_module_comparison_does_not_normalize_caller_mutations(self):
        with tempfile.TemporaryDirectory() as temporary:
            generated, supplied = Path(temporary) / "generated.ll", Path(temporary) / "supplied.ll"
            clean = module().encode("utf-8")
            generated.write_bytes(clean); supplied.write_bytes(clean)
            gate.require_baseline_match(generated, supplied)
            for changed in (gate.helper_mutation(module())[0].encode("utf-8"),
                            clean.replace(b"\n", b"\r\n"), clean + b"; caller mutation\n"):
                supplied.write_bytes(changed)
                with self.assertRaisesRegex(gate.GateError, "module bytes differ"):
                    gate.require_baseline_match(generated, supplied)

    def test_git_archive_is_bound_to_actual_blob_bytes_and_safe_member_paths(self):
        head = "b" * 40
        content = b"compiler source\n"
        blob = hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()
        inventory = gate.baseline_tree(f"100644 blob {blob} {len(content)}\tcompiler.py\0")
        def packed(path, *, name="compiler.py", data=content, commit=head, link=False):
            with tarfile.open(path, "w", format=tarfile.PAX_FORMAT, pax_headers={"comment": commit}) as archive:
                member = tarfile.TarInfo(name)
                if link:
                    member.type, member.linkname = tarfile.SYMTYPE, "../outside"
                    archive.addfile(member)
                else:
                    member.size = len(data)
                    archive.addfile(member, io.BytesIO(data))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "compiler.tar"
            packed(archive)
            entries = gate.extract_baseline(archive, root / "clean", head, inventory)
            gate.check_baseline_bundle(root / "clean", entries)
            (root / "clean/compiler.py").write_bytes(b"tampered source\n")
            with self.assertRaisesRegex(gate.GateError, "inputs changed"):
                gate.check_baseline_bundle(root / "clean", entries)
            for index, kwargs in enumerate(({"data": b"caller mutation\n"}, {"commit": "c" * 40},
                    {"name": "../outside"}, {"link": True})):
                packed(archive, **kwargs)
                with self.assertRaises(gate.GateError):
                    gate.extract_baseline(archive, root / f"rejected-{index}", head, inventory)
            self.assertFalse((root / "outside").exists())

    def test_git_tree_rejects_links_aliases_traversal_and_excessive_bundles(self):
        row = "100644 blob " + "a" * 40 + " 1\t"
        for text in (row + "../outside\0", row + "compiler.py\0" + row + "Compiler.py\0",
                row.replace("100644", "120000") + "linked\0", row + "D:/outside\0",
                row.replace(" 1\t", f" {gate.BASELINE_BUNDLE_LIMIT + 1}\t") + "huge.py\0"):
            with self.assertRaises(gate.GateError):
                gate.baseline_tree(text)

    def test_windows_input_identity_uses_portable_keys_and_detects_source_changes(self):
        root = PureWindowsPath("D:/checkout with spaces/Freak-lang")
        source = root / "benchmarks/v4/int_checked_hot_loop.fk"
        clang = PureWindowsPath("C:/LLVM/bin/clang.exe")
        pins = {source: "a" * 64, clang: "b" * 64}
        with patch.object(gate, "ROOT", root), patch.object(gate, "head_identity", return_value="c" * 40), \
                patch.object(gate, "sha", side_effect=lambda path: pins[path]):
            identity = gate.Identity([source], clang)
            self.assertEqual(identity.inputs, {"benchmarks/v4/int_checked_hot_loop.fk": "a" * 64})
            actual = report()
            actual["compiler_inputs"] = identity.inputs
            gate.validate_report(actual)
            identity.check()
            pins[source] = "d" * 64
            with self.assertRaisesRegex(gate.GateError, "identity changed"):
                identity.check()

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
