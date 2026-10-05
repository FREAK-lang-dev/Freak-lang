"""Adversarial deterministic controls for the checked-int runtime gate."""
from copy import deepcopy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path, PureWindowsPath
import shutil
import subprocess
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


def historical_report(work):
    value = report()
    value["target"] = "x86_64-unknown-linux-gnu"
    value["clang"]["resolved"] = "/toolchain/clang"
    value["variants"].append("historical-baseline")
    for name in ("boundaries", "optimized", "timings", "medians"):
        for row in list(value[name]):
            if row["variant"] == "helper-mutation":
                value[name].append({**row, "variant": "historical-baseline"})
    work = work / "historical-producer"
    work.mkdir()
    bundle, pin = work / "compiler", "a" * 64
    contents = {name: name.encode("utf-8") + b"\n" for name in
                ("src/compiler/v4/build_v4.py", "src/compiler/v4/check_v4.py")}
    entries = {name: {"mode": "100644", "blob": gate.git_object_sha("blob", content),
                     "size": len(content), "sha256": hashlib.sha256(content).hexdigest()}
               for name, content in contents.items()}
    tree = gate.baseline_tree_oid(entries)
    commit = "tree " + tree + "\nauthor Fixture <fixture@example.invalid> 1 +0000\ncommitter Fixture <fixture@example.invalid> 1 +0000\n\nFixture\n"
    head = gate.git_object_sha("commit", commit.encode("utf-8"))
    listing = "".join(f"{row['mode']} blob {row['blob']} {row['size']:7}\t{name}\0" for name, row in sorted(entries.items()))
    provenance = {"kind": gate.BASELINE_KIND, "compiler_head": head, "compiler_tree": tree,
        "compiler_inputs": entries, "compiler_manifest_sha256": gate.baseline_manifest_sha(entries),
        "bundle_path": str(bundle), "target": value["target"], "module_bytes_equal": True,
        "source_sha256": pin, "module_sha256": pin, "regenerated_module_sha256": pin,
        "commit_object": commit, "git_tree_listing": listing}
    for path_key, hash_key, name in (("archive_path", "archive_sha256", "compiler.tar"),
            ("source_path", "source_sha256", "hot-loop.fk"), ("path", "module_sha256", "supplied.ll"),
            ("regenerated_module_path", "regenerated_module_sha256", "regenerated.ll"),
            ("verified_object_path", "verified_object_sha256", "verified.o"),
            ("producer_audit_path", "producer_audit_sha256", "producer.json"),
            ("producer_wrapper_path", "producer_wrapper_sha256", "produce.py"),
            ("manifest_path", "manifest_file_sha256", "compiler-inputs.json"),
            ("commit_object_path", "commit_object_sha256", "commit-object.txt"),
            ("git_tree_listing_path", "git_tree_listing_sha256", "git-tree-listing.txt")):
        provenance[path_key], provenance[hash_key] = str(work / name), pin
        value["artifact_sha256"][provenance[path_key]] = pin
    def write_pin(path_key, hash_key, content):
        path = Path(provenance[path_key])
        path.write_bytes(content)
        provenance[hash_key] = gate.sha(path)
        value["artifact_sha256"][str(path)] = provenance[hash_key]
    write_pin("commit_object_path", "commit_object_sha256", commit.encode("utf-8"))
    write_pin("git_tree_listing_path", "git_tree_listing_sha256", listing.encode("utf-8"))
    with tarfile.open(provenance["archive_path"], "w", format=tarfile.PAX_FORMAT, pax_headers={"comment": head}) as archive:
        for name, content in contents.items():
            member = tarfile.TarInfo(name)
            member.size = len(content)
            archive.addfile(member, io.BytesIO(content))
    provenance["archive_sha256"] = gate.sha(Path(provenance["archive_path"]))
    value["artifact_sha256"][provenance["archive_path"]] = provenance["archive_sha256"]
    raw = ('target triple = "' + value["target"] + '"\n' + gate.helper_mutation(module())[0]).encode("utf-8")
    write_pin("path", "module_sha256", raw)
    write_pin("regenerated_module_path", "regenerated_module_sha256", raw)
    provenance["git"] = {"selected": "git", "resolved": "/tools/git", "sha256": pin}
    provenance["python"] = {"selected": sys.executable, "resolved": "/tools/python", "sha256": pin}
    value["artifact_sha256"].update({"/tools/git": pin, "/tools/python": pin})
    compiler = str(work / "bootstrap/compiler_O2/build_llvm")
    generated = str(work / "bootstrap/compiler_O2/build_llvm.fk.c")
    value["artifact_sha256"].update({compiler: pin, generated: pin})
    provenance["producer"] = {"exit": 0, "fresh_bootstrap": True,
        "entrypoint": str(bundle / "src/compiler/v4/build_v4.py"), "compiler_binary": compiler,
        "compiler_binary_sha256": pin, "generated_c": generated, "generated_c_sha256": pin}
    runtime = bundle / "freakc/runtime"
    commands = [[value["clang"]["resolved"], "-o", compiler, generated, str(runtime / "freak_runtime.c"),
                 "-I" + str(runtime), "-w", "-O0", "-O2", "-DFREAK_ARRAY_LIVE_LIMIT=1024", "-lm"],
        [compiler, provenance["source_path"], value["target"]],
        [value["clang"]["resolved"], "--target=" + value["target"], "-x", "ir", "-c",
         provenance["regenerated_module_path"], "-o", provenance["verified_object_path"]]]
    labels = ["runtime compile: src/compiler/v4/tools/build_llvm.fk", "V4 compile: hot-loop.fk", "V4 LLVM verification"]
    provenance["producer"]["jobs"] = [{"command": command, "label": label, "exit": 0, "elapsed_ns": 100,
                      "timeout_seconds": 120, "memory_limit_mib": 512, "output_limit_mib_per_stream": 8,
                      "stdout_sha256": pin, "stderr_sha256": pin} for command, label in zip(commands, labels)]
    git_prefix = gate.baseline_git_command("git")
    commands = [[*git_prefix, "rev-parse", "--verify", head + "^{commit}"],
        [*git_prefix, "rev-parse", "--verify", head + "^{tree}"], [*git_prefix, "cat-file", "commit", head],
        [*git_prefix, "ls-tree", "-r", "-l", "-z", "--full-tree", head],
        [*git_prefix, "archive", "--format=tar", "--output=" + provenance["archive_path"], head],
        [sys.executable, "-I", "-B", provenance["producer_wrapper_path"], json.dumps({"bundle": str(bundle),
          "work": str(work), "source": provenance["source_path"], "module": provenance["regenerated_module_path"],
          "clang": value["clang"]["resolved"], "target": value["target"]}, sort_keys=True)]]
    labels = ["baseline resolve commit", "baseline resolve tree", "baseline read Git commit object", "baseline list Git blobs",
              "baseline archive pinned compiler", "baseline regenerate and verify LLVM"]
    outputs = [gate.text_sha(head + "\n"), gate.text_sha(tree + "\n"), gate.text_sha(commit), gate.text_sha(listing), pin, pin]
    value["jobs"] = [{"serial": i, "command": command, "label": label, "exit": 0,
                      "timeout_seconds": 120, "memory_limit_mib": 512, "output_limit_mib_per_stream": 8,
                      "git_environment_isolated": True, "stdout_sha256": output}
                     for i, (command, label, output) in enumerate(zip(commands, labels, outputs), 1)]
    provenance["producer_job_serials"] = list(range(1, 7))
    native = work.parent / "historical-baseline.native.ll"
    native.write_bytes(raw)
    native_sha = gate.sha(native)
    value["artifact_sha256"][str(native)] = native_sha
    derivative = {"kind": "regenerated-native-module-v1", "platform": "linux", "link_target": value["target"],
                  "raw_module_sha256": provenance["regenerated_module_sha256"], "module_path": str(native),
                  "module_sha256": native_sha, "binaries": {}, "optimized_modules": {},
                  "runtime_object_paths": {}, "link_job_serials": {}, "optimize_job_serials": {}}
    def append_job(command, label, **fields):
        row = {"serial": len(value["jobs"]) + 1, "command": command, "label": label, "exit": 0,
               "timeout_seconds": 120, "memory_limit_mib": 512, "output_limit_mib_per_stream": 8, **fields}
        value["jobs"].append(row)
        return row
    for opt in gate.OPTS:
        key = str(opt)
        binary = work.parent / f"historical-baseline.O{opt}.native"
        binary.write_bytes(f"fixture native {opt}".encode())
        optimized = work.parent / f"historical-baseline.optimized.O{opt}.ll"
        optimized.write_bytes(raw + f"; fixture optimization {opt}\n".encode())
        binary_sha, optimized_sha = gate.sha(binary), gate.sha(optimized)
        value["artifact_sha256"].update({str(binary): binary_sha, str(optimized): optimized_sha})
        derivative["binaries"][key], derivative["optimized_modules"][key] = binary_sha, optimized_sha
        objects = list(value["runtime_objects"][key])
        derivative["runtime_object_paths"][key] = objects
        linked = append_job([value["clang"]["resolved"], *value["build_flags"][key], str(native), *objects,
                             "-o", str(binary), "-lm", "-Wl,-z,muldefs"], f"link historical-baseline O{opt}")
        derivative["link_job_serials"][key] = linked["serial"]
        retained = append_job([value["clang"]["resolved"], f"-O{opt}", "-S", "-emit-llvm", str(native), "-o", str(optimized)],
                              f"retain optimized historical-baseline O{opt}")
        derivative["optimize_job_serials"][key] = retained["serial"]
        for family in ("boundaries", "optimized", "timings"):
            for row in value[family]:
                if row["variant"] != "historical-baseline" or row["optimization"] != opt:
                    continue
                row["module_sha256"], row["binary_sha256"] = native_sha, binary_sha
                if family == "optimized":
                    row["optimized_module_sha256"] = optimized_sha
                else:
                    argv = [str(row["iterations"]), str(row["seed"])] if family == "boundaries" else [str(value["iterations"]), str(value["seed"])]
                    job = append_job([str(binary), *argv], "fixture historical execution", timeout_seconds=30, memory_limit_mib=128,
                        stdout_sha256=row["stdout_sha256"], stderr_sha256=row["stderr_sha256"], elapsed_ns=row.get("elapsed_ns", 1000))
                    row.update(serial=job["serial"], command=job["command"], elapsed_ns=job["elapsed_ns"])
    provenance["native_derivative"] = derivative
    value["historical_baseline"] = provenance
    return value


class IntRuntimeOracles(unittest.TestCase):
    def historical(self):
        temporary = tempfile.TemporaryDirectory(prefix="historical report ")
        self.addCleanup(temporary.cleanup)
        return historical_report(Path(temporary.name))

    def test_historical_helper_mutation_cannot_be_relabelled_by_three_caller_hashes(self):
        genuine = self.historical()
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
        clean = self.historical()
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
        bad = deepcopy(clean); bad["jobs"][5]["exit"] = 1; mutations.append(bad)
        bad = deepcopy(clean); bad["jobs"][0]["git_environment_isolated"] = False; mutations.append(bad)
        bad = deepcopy(clean)
        for row in bad["jobs"][:5]:
            row["command"].remove("--no-replace-objects")
        mutations.append(bad)
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

    def test_historical_bootstrap_binds_every_archived_compiler_input_and_flag(self):
        clean = self.historical()
        for index in (0, 2, 3, 4, 5, 7, 8, 9, 10):
            bad = deepcopy(clean)
            bad["historical_baseline"]["producer"]["jobs"][0]["command"][index] = "drifted-input"
            with self.subTest(index=index), self.assertRaises(gate.GateError):
                gate.validate_report(bad)
        bad = deepcopy(clean)
        bad["historical_baseline"]["producer"]["jobs"][0]["label"] = "runtime compile: unrelated.fk"
        with self.assertRaises(gate.GateError):
            gate.validate_report(bad)
        bad = deepcopy(clean)
        changed = bad["historical_baseline"]["producer"]["generated_c"] + ".unrelated"
        bad["historical_baseline"]["producer"]["generated_c"] = changed
        bad["historical_baseline"]["producer"]["jobs"][0]["command"][3] = changed
        bad["artifact_sha256"][changed] = bad["historical_baseline"]["producer"]["generated_c_sha256"]
        with self.assertRaises(gate.GateError):
            gate.validate_report(bad)

    def test_historical_native_rows_cannot_be_detached_or_replaced_by_helper_rows(self):
        clean = self.historical()
        for family, key in (("boundaries", "module_sha256"), ("boundaries", "binary_sha256"),
                ("timings", "module_sha256"), ("timings", "binary_sha256"),
                ("optimized", "module_sha256"), ("optimized", "binary_sha256"),
                ("optimized", "optimized_module_sha256"), ("timings", "command")):
            bad = deepcopy(clean)
            row = next(row for row in bad[family] if row["variant"] == "historical-baseline")
            row[key] = ["helper-mutation.O0.native", "100", "17"] if key == "command" else "d" * 64
            with self.subTest(family=family, key=key), self.assertRaises(gate.GateError):
                gate.validate_report(bad)
        bad = deepcopy(clean)
        for family in ("boundaries", "timings", "optimized"):
            bad[family] = [row for row in bad[family] if row["variant"] != "historical-baseline"]
            bad[family] += [{**row, "variant": "historical-baseline"} for row in list(bad[family]) if row["variant"] == "helper-mutation"]
        with self.assertRaises(gate.GateError):
            gate.validate_report(bad)
        bad = deepcopy(clean)
        derivative = bad["historical_baseline"]["native_derivative"]
        serial = derivative["link_job_serials"]["0"]
        next(row for row in bad["jobs"] if row["serial"] == serial)["command"][4] = "unrelated-runtime.o"
        with self.assertRaises(gate.GateError):
            gate.validate_report(bad)
        bad = deepcopy(clean)
        derivative = bad["historical_baseline"]["native_derivative"]
        derivative["binaries"]["0"], derivative["binaries"]["2"] = derivative["binaries"]["2"], derivative["binaries"]["0"]
        with self.assertRaises(gate.GateError):
            gate.validate_report(bad)

    def test_historical_native_derivative_cannot_change_even_with_coherent_row_hashes(self):
        bad = self.historical()
        derivative = bad["historical_baseline"]["native_derivative"]
        native = Path(derivative["module_path"])
        native.write_bytes(native.read_bytes() + b"; caller changed derivative\n")
        changed = gate.sha(native)
        derivative["module_sha256"] = changed
        bad["artifact_sha256"][str(native)] = changed
        for family in ("boundaries", "timings", "optimized"):
            for row in bad[family]:
                if row["variant"] == "historical-baseline":
                    row["module_sha256"] = changed
        with self.assertRaisesRegex(gate.GateError, "raw/platform derivative"):
            gate.validate_report(bad)

    def test_retained_git_object_graph_rejects_coherent_manifest_and_tree_relabelling(self):
        clean = self.historical()
        bad = deepcopy(clean)
        pin = bad["historical_baseline"]
        first = next(iter(pin["compiler_inputs"]))
        pin["compiler_inputs"][first]["blob"] = "d" * 40
        pin["compiler_manifest_sha256"] = gate.baseline_manifest_sha(pin["compiler_inputs"])
        with self.assertRaises(gate.GateError):
            gate.validate_report(bad)
        bad = deepcopy(clean)
        pin = bad["historical_baseline"]
        pin["compiler_inputs"][first]["sha256"] = "d" * 64
        pin["compiler_manifest_sha256"] = gate.baseline_manifest_sha(pin["compiler_inputs"])
        with self.assertRaisesRegex(gate.GateError, "blob/SHA256 manifest"):
            gate.validate_report(bad)
        bad = deepcopy(clean)
        pin = bad["historical_baseline"]
        pin["compiler_inputs"][first]["blob"] = "d" * 40
        pin["compiler_manifest_sha256"] = gate.baseline_manifest_sha(pin["compiler_inputs"])
        pin["git_tree_listing"] = "".join(f"{row['mode']} blob {row['blob']} {row['size']:7}\t{name}\0"
            for name, row in sorted(pin["compiler_inputs"].items()))
        pin["compiler_tree"] = gate.baseline_tree_oid(pin["compiler_inputs"])
        pin["commit_object"] = pin["commit_object"].replace(clean["historical_baseline"]["compiler_tree"], pin["compiler_tree"], 1)
        for field, path_field, hash_field, serial in (("commit_object", "commit_object_path", "commit_object_sha256", 3),
                ("git_tree_listing", "git_tree_listing_path", "git_tree_listing_sha256", 4)):
            changed = Path(pin[path_field]).with_name("coherent-" + Path(pin[path_field]).name)
            changed.write_bytes(pin[field].encode("utf-8"))
            pin[path_field], pin[hash_field] = str(changed), gate.sha(changed)
            bad["artifact_sha256"][str(changed)] = pin[hash_field]
            next(row for row in bad["jobs"] if row["serial"] == serial)["stdout_sha256"] = pin[hash_field]
        bad["jobs"][1]["stdout_sha256"] = gate.text_sha(pin["compiler_tree"] + "\n")
        with self.assertRaisesRegex(gate.GateError, "commit witness"):
            gate.validate_report(bad)

    def test_producer_artifacts_have_a_bounded_lifecycle_and_keep_native_checks(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            clang, archive, binary = work / "clang", work / "compiler.tar", work / "native"
            for path in (clang, archive, binary):
                path.write_bytes(path.name.encode())
            actual_sha, reads = gate.sha, []
            def counted(path):
                reads.append(path)
                return actual_sha(path)
            with patch.object(gate, "head_identity", return_value="a" * 40), patch.object(gate, "sha", side_effect=counted):
                identity = gate.Identity([], clang)
                identity.seal(archive, producer=True)
                identity.seal(binary)
                reads.clear()
                with patch.object(gate, "check_baseline_bundle") as bundle_check:
                    with gate.frozen_baseline_inputs(work / "compiler", {}, identity):
                        identity.check()
                    self.assertEqual(bundle_check.call_count, 2)
                self.assertEqual(reads.count(archive), 2)
                before = reads.count(binary)
                for _ in range(5):
                    identity.check()
                self.assertEqual(reads.count(archive), 2)
                self.assertEqual(reads.count(binary), before + 5)
                identity.check_producer()
                self.assertEqual(reads.count(archive), 3)
                archive.write_bytes(b"changed after production")
                identity.check()
                with self.assertRaisesRegex(gate.GateError, "producer evidence changed"):
                    identity.check_producer()

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

    def test_git_replacement_refs_cannot_substitute_the_pinned_compiler_archive(self):
        git = shutil.which("git")
        self.assertIsNotNone(git, "Git is required for historical compiler provenance controls")
        with tempfile.TemporaryDirectory(prefix="int provenance ") as temporary:
            work = Path(temporary)
            repository = work / "repo"
            repository.mkdir()
            ordinary = [git, "-C", str(repository)]
            def run(prefix, *arguments):
                result = subprocess.run([*prefix, *arguments], capture_output=True, text=True, timeout=10,
                                        env=gate.git_environment())
                self.assertEqual(result.returncode, 0, result.stderr)
                return result.stdout
            run(ordinary, "init", "-q")
            run(ordinary, "config", "user.name", "Provenance fixture")
            run(ordinary, "config", "user.email", "provenance-fixture@example.invalid")
            run(ordinary, "config", "commit.gpgsign", "false")
            hooks = work / "empty-hooks"
            hooks.mkdir()
            run(ordinary, "config", "core.hooksPath", str(hooks))
            compiler = repository / "compiler.py"
            original_bytes, replacement_bytes = b"original compiler\n", b"replacement compiler\n"
            compiler.write_bytes(original_bytes)
            run(ordinary, "add", "compiler.py")
            run(ordinary, "commit", "-q", "-m", "Original compiler")
            original = run(ordinary, "rev-parse", "HEAD").strip()
            original_tree = run(ordinary, "rev-parse", original + "^{tree}").strip()
            inventory = gate.baseline_tree(run(ordinary, "ls-tree", "-r", "-l", "-z", "--full-tree", original))
            self.assertEqual(gate.baseline_tree_oid(inventory), original_tree)
            compiler.write_bytes(replacement_bytes)
            run(ordinary, "add", "compiler.py")
            run(ordinary, "commit", "-q", "-m", "Replacement compiler")
            replacement = run(ordinary, "rev-parse", "HEAD").strip()
            replacement_tree = run(ordinary, "rev-parse", replacement + "^{tree}").strip()
            run(ordinary, "replace", original, replacement)
            # The unprotected commit label remains unchanged while its tree,
            # compiler bytes and archive are substituted by replacement refs.
            self.assertEqual(run(ordinary, "rev-parse", "--verify", original + "^{commit}").strip(), original)
            self.assertEqual(run(ordinary, "rev-parse", "--verify", original + "^{tree}").strip(), replacement_tree)
            substituted = work / "substituted.tar"
            run(ordinary, "archive", "--format=tar", "--output=" + str(substituted), original)
            with self.assertRaises(gate.GateError):
                gate.extract_baseline(substituted, work / "substituted", original, inventory)
            with patch.object(gate, "ROOT", repository):
                protected = gate.baseline_git_command(git)
                self.assertEqual(protected, [git, "--no-replace-objects", "-C", str(repository)])
                self.assertEqual(run(protected, "rev-parse", "--verify", original + "^{commit}").strip(), original)
                self.assertEqual(run(protected, "rev-parse", "--verify", original + "^{tree}").strip(), original_tree)
                self.assertEqual(gate.baseline_tree(run(protected, "ls-tree", "-r", "-l", "-z", "--full-tree", original)), inventory)
                archived = work / "original.tar"
                run(protected, "archive", "--format=tar", "--output=" + str(archived), original)
                entries = gate.extract_baseline(archived, work / "original", original, inventory)
                gate.check_baseline_bundle(work / "original", entries)
                self.assertEqual((work / "original/compiler.py").read_bytes(), original_bytes)

    def test_git_environment_cannot_redirect_fixture_or_producer_to_an_external_repository(self):
        poisoned_names = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
            "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_COMMON_DIR", "GIT_REPLACE_REF_BASE", "GIT_NAMESPACE",
            "GIT_CONFIG", "GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM", "GIT_CONFIG_COUNT",
            "GIT_CONFIG_KEY_0", "GIT_CONFIG_VALUE_0", "git_dir")
        scrubbed = gate.git_environment({**{name: "trap" for name in poisoned_names}, "PATH": "retained-path"})
        self.assertEqual(scrubbed, {"PATH": "retained-path"})
        git = shutil.which("git")
        self.assertIsNotNone(git, "Git is required for isolated repository controls")
        with tempfile.TemporaryDirectory(prefix="git environment trap ") as temporary:
            work = Path(temporary)
            trap, repository, hooks = work / "trap", work / "intended", work / "empty-hooks"
            for path in (trap, repository, hooks):
                path.mkdir()
            def run(repository, *arguments):
                result = subprocess.run([git, "-C", str(repository), *arguments], capture_output=True,
                                        text=True, timeout=10, env=gate.git_environment())
                self.assertEqual(result.returncode, 0, result.stderr)
                return result.stdout
            run(trap, "init", "-q")
            run(trap, "config", "user.name", "Trap fixture")
            run(trap, "config", "user.email", "trap-fixture@example.invalid")
            run(trap, "config", "commit.gpgsign", "false")
            run(trap, "config", "core.hooksPath", str(hooks))
            (trap / "sentinel").write_bytes(b"external repository must remain unchanged")
            run(trap, "add", "sentinel")
            run(trap, "commit", "-q", "-m", "External repository sentinel")
            def snapshot():
                return {path.relative_to(trap).as_posix(): gate.sha(path) for path in trap.rglob("*") if path.is_file()}
            before = snapshot()
            poisoned = {name: str(trap / ".git") for name in poisoned_names if name != "git_dir"}
            poisoned.update(GIT_WORK_TREE=str(trap), GIT_INDEX_FILE=str(trap / ".git/index"),
                GIT_OBJECT_DIRECTORY=str(trap / ".git/objects"), GIT_ALTERNATE_OBJECT_DIRECTORIES=str(trap / ".git/objects"),
                GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0="core.worktree", GIT_CONFIG_VALUE_0=str(trap))
            with patch.dict(os.environ, poisoned, clear=False):
                run(repository, "init", "-q")  # The fixture helper passes a clean environment.
                self.assertTrue((repository / ".git/config").is_file())
                run(repository, "config", "fixture.isolated", "true")
                self.assertEqual(run(repository, "config", "--get", "fixture.isolated").strip(), "true")
                with patch.object(gate, "ROOT", repository), gate.isolated_git_environment():
                    self.assertFalse(any(name.upper().startswith("GIT_") for name in os.environ))
                    result = subprocess.run([*gate.baseline_git_command(git), "rev-parse", "--absolute-git-dir"],
                                            capture_output=True, text=True, timeout=10)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(Path(result.stdout.strip()).resolve(), (repository / ".git").resolve())
                self.assertEqual(os.environ["GIT_DIR"], poisoned["GIT_DIR"])
            self.assertEqual(snapshot(), before)

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
