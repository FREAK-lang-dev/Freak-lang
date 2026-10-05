"""Process-free FS bridge oracles and real guarded-driver fault controls."""
import ast
from contextlib import ExitStack
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
gate = types.ModuleType("private_fs_bridge_oracles_under_test")
gate.__file__ = str(ROOT / "tests/v4_fs_read_bridge.py")
sys.modules[gate.__name__] = gate
exec(compile(Path(gate.__file__).read_bytes(), gate.__file__, "exec"), gate.__dict__)


def capability(kind):
    if kind == "asan-heap":
        return {"status": 86, "stdout": "", "stderr": "ERROR: AddressSanitizer: heap-buffer-overflow\nSUMMARY: AddressSanitizer: heap-buffer-overflow\n"}
    detail = "signed integer overflow: 2147483647 + 1" if kind == "ubsan-overflow" else "division of -2147483648 by -1 cannot be represented in type 'int'"
    return {"status": 85, "stdout": "", "stderr": "runtime error: " + detail + "\nSUMMARY: UndefinedBehaviorSanitizer: undefined-behavior\n"}


def synthetic_report(data, sanitize=False, host="linux"):
    sources = {name: "a" * 64 for name in gate.SOURCE_NAMES}
    sources[gate.SUPPORT_NAME] = gate.SUPPORT_SHA
    fixtures = {}
    for name, fixture in data["fixtures"].items():
        if host not in fixture.get("platforms", gate.COUNTS): continue
        fixtures[name] = {"kind": fixture["kind"], "name": fixture["name"]}
        if fixture["kind"] == "file":
            payload = bytes.fromhex(fixture["hex"])
            fixtures[name].update(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
    binaries = {f"/metadata/fs-O{opt}": "c" * 64 for opt in gate.OPTS}
    report = {"complete": True, "scope": gate.SCOPE, "platform": host, "sanitized": sanitize,
              "source_hashes": sources, "final_source_hashes": dict(sources), "final_frozen_source_hashes": dict(sources),
              "compiler": {"sha256": "b" * 64, "selected": "/metadata/compiler-alias", "path": "/metadata/compiler", "target": "x86_64-pc-linux-gnu"},
              "final_compiler_sha256": "b" * 64, "final_selected_compiler": "/metadata/compiler",
              "fixture_facts": fixtures, "final_fixture_facts": deepcopy(fixtures),
              "binary_hashes": binaries, "final_binary_hashes": dict(binaries), "matrices": []}
    for opt in gate.OPTS:
        report["matrices"].append({"optimization": opt, "flags": gate.build_flags(opt, sanitize),
                                  "binary_path": f"/metadata/fs-O{opt}", "binary_sha256": "c" * 64,
                                  "cases": [{"id": case["id"], "actual": gate.expected_case(case, data["fixtures"], host)}
                                            for case in data["cases"] if host in case["platforms"]],
                                  "capabilities": [{"kind": kind, "actual": capability(kind)} for kind in gate.CAPABILITIES] if sanitize else []})
    return report


class FsBridgePure(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.attempts = {name: 0 for name in ("Popen", "run", "call", "check_call", "check_output")}
        for name in self.attempts:
            def forbidden(*args, name=name, **kwargs):
                self.attempts[name] += 1
                raise AssertionError("process forbidden: " + name)
            self.stack.enter_context(patch.object(subprocess, name, forbidden))
        self.temporary = self.stack.enter_context(tempfile.TemporaryDirectory())
        self.directory = Path(self.temporary).resolve()
        self.data = gate.load_vectors()
        self.stack.callback(sys.modules.pop, "v4_fs_read_bridge_frozen_support", None)

    def tearDown(self):
        self.stack.close()
        self.assertFalse(any(self.attempts.values()), self.attempts)
        self.assertNotIn("v4_fs_read_bridge_frozen_process_guard", sys.modules)
        self.assertNotIn("v4_c_integer_runtime_checks", sys.modules)

    def fixture(self):
        root, work = self.directory / "source", self.directory / "work"
        work.mkdir()
        frozen = work / "frozen-source"
        for name in gate.SOURCE_NAMES:
            data = (ROOT / name).read_bytes()
            for base in (root, frozen):
                target = base / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
        compiler = self.directory / "non-executable-compiler"
        compiler.write_bytes(b"never execute this compiler fixture")
        self.stack.enter_context(patch.object(gate, "ROOT", root))
        support = gate.load_support(frozen)
        report = {"complete": False, "scope": gate.SCOPE, "platform": sys.platform, "sanitized": False,
                  "source_hashes": gate.source_hashes(),
                  "compiler": {"selected": str(compiler), "path": str(compiler), "sha256": gate.sha(compiler)}, "matrices": []}
        return root, work, frozen, compiler, support, report

    def test_closed58_vectors_and_platform_counts(self):
        self.assertEqual(len(self.data["cases"]), 58)
        self.assertEqual(self.data["counts"], {"linux":55, "darwin":55, "win32":57})
        self.assertEqual({case["id"] for case in self.data["cases"]}, gate.EXPECTED_IDS)
        from freakc.v4_native_runtime import RUNTIME_FILE_NAMES, runtime_file
        expected_runtime_sources = {runtime_file(ROOT / "freakc/runtime", name).relative_to(ROOT).as_posix()
                                    for name in RUNTIME_FILE_NAMES}
        self.assertEqual(set(gate.RUNTIME_SOURCE_NAMES), expected_runtime_sources)
        self.assertEqual(set(gate.SOURCE_NAMES), expected_runtime_sources |
                         set(gate.OWNED_NAMES) | set(gate.INVENTORY_NAMES) |
                         {gate.SUPPORT_NAME, gate.GUARD_NAME})
        self.assertEqual(len(gate.SOURCE_NAMES), len(set(gate.SOURCE_NAMES)))
        self.assertEqual(len(gate.OWNED_NAMES), 5)

    def test_sized_nul_and_crlf_are_ok_exact_data(self):
        for identity, payload in (("empty-file", b""), ("binary-file", b"A\0\xc3\xa9\xe4\xb8\xad\xf0\x9f\x98\x80"),
                                  ("nul-only-file", b"\0\0\0"), ("crlf-file", b"\r\n")):
            case = next(case for case in self.data["cases"] if case["id"] == identity)
            wanted = gate.expected_case(case, self.data["fixtures"], "linux")
            self.assertEqual(wanted, {"status":0, "stdout":gate.protocol(1,payload).decode(), "stderr":""})

    def test_invalid_utf8_and_missing_nonregular_errors_are_named_owned_protocols(self):
        for case in self.data["cases"]:
            if case["id"].startswith("invalid-file-"):
                self.assertEqual(gate.expected_case(case,self.data["fixtures"],"linux")["stdout"],
                                 gate.protocol(0,b"filesystem file is not valid UTF-8").decode())
        fifo = next(case for case in self.data["cases"] if case["id"] == "fifo")
        self.assertEqual(fifo["platforms"], ["linux","darwin"])
        self.assertEqual(gate.expected_case(fifo,self.data["fixtures"],"linux")["stdout"],
                         gate.protocol(0,b"filesystem path is not a readable regular file").decode())

    def test_path_priority_and_compound_fault_first_cause_goldens(self):
        for identity, reason in (("path-nul-invalid","filesystem path contains NUL"),
                                 ("fault-seek-close","could not seek filesystem file"),
                                 ("fault-allocation-close","filesystem contents allocation failed"),
                                 ("fault-short-close","could not read complete filesystem file"),
                                 ("fault-stat-descriptor-close","filesystem path is not a readable regular file")):
            case = next(case for case in self.data["cases"] if case["id"] == identity)
            recovery = 64 if identity.startswith("fault-") else 0
            self.assertEqual(gate.expected_case(case,self.data["fixtures"],"linux")["stdout"], gate.protocol(0,reason.encode(),recovery).decode())

    def test_system_exit_and_word_abort_audit_deaths_are_distinct(self):
        for host in gate.COUNTS:
            for mode in ("error-copy","error-track"):
                case = next(case for case in self.data["cases"] if case["id"] == "fatal-"+mode)
                correct = gate.expected_case(case,self.data["fixtures"],host)
                self.assertEqual(correct["status"],3 if host == "win32" else -signal.SIGABRT)
                gate.validate_exact(correct,correct,host)
                for wrong in (0,1,85,86,87,99,-signal.SIGSEGV):
                    with self.subTest(host=host,mode=mode,wrong=wrong), self.assertRaises(gate.GateError):
                        gate.validate_exact(dict(correct,status=wrong),correct,host)
                for suffix in ("ERROR: AddressSanitizer\n", "runtime error: injected\n", "SUMMARY: UndefinedBehaviorSanitizer:\n"):
                    with self.assertRaises(gate.GateError): gate.validate_exact(dict(correct,stderr=correct["stderr"]+suffix),correct,host)

    def test_exact_oracle_rejects_status_extra_channels_and_wrong_bytes(self):
        case = self.data["cases"][0]
        wanted = gate.expected_case(case,self.data["fixtures"],"linux")
        for wrong in (dict(wanted,status=True),dict(wanted,status=1),dict(wanted,stdout=wanted["stdout"]+"extra\n"),
                      dict(wanted,stderr="extra\n"),dict(wanted,stdout=wanted["stdout"].replace("fs-tag:1","fs-tag:0"))):
            with self.assertRaises(gate.GateError): gate.validate_exact(wrong,wanted,"linux")

    def test_windows_normalizes_only_protocol_line_crlf(self):
        case = next(case for case in self.data["cases"] if case["id"] == "crlf-file")
        wanted = gate.expected_case(case,self.data["fixtures"],"win32")
        observed = dict(wanted,stdout=wanted["stdout"].replace("\n","\r\n"))
        gate.validate_exact(observed,wanted,"win32")
        with self.assertRaises(gate.GateError): gate.validate_exact(observed,wanted,"linux")
        with self.assertRaises(gate.GateError): gate.validate_exact(dict(observed,stdout=observed["stdout"].replace("0d0a","0a")),wanted,"win32")

    def test_directory_oracle_requires_real_boundary_receipt_and_exact_stage_error(self):
        case = next(case for case in self.data["cases"] if case["id"] == "directory")
        for boundary in ("admitted","rejected"):
            correct = gate.expected_case(case,self.data["fixtures"],"win32",boundary)
            gate.validate_case(correct,case,self.data["fixtures"],"win32")
            gate.validate_case(dict(correct,stdout=correct["stdout"].replace("\n","\r\n")),case,self.data["fixtures"],"win32")
            for wrong in (dict(correct,stdout=correct["stdout"].split("\n",1)[1]),
                          dict(correct,stdout=correct["stdout"].replace("stream:0","stream:1")),
                          dict(correct,stdout=correct["stdout"].replace("raw-close:0","raw-close:1") if boundary == "rejected" else correct["stdout"].replace("stat:1","stat:0")),
                          dict(correct,stderr="unexpected\n")):
                with self.assertRaises(gate.GateError): gate.validate_case(wrong,case,self.data["fixtures"],"win32")
            if boundary == "rejected":
                with self.assertRaises(gate.GateError): gate.validate_case(correct,case,self.data["fixtures"],"linux")
        admitted = gate.expected_case(case,self.data["fixtures"],"win32","admitted")
        rejected = gate.expected_case(case,self.data["fixtures"],"win32","rejected")
        wrong = dict(admitted,stdout=gate.directory_receipt("admitted").decode()+rejected["stdout"].split("\n",1)[1])
        with self.assertRaises(gate.GateError): gate.validate_case(wrong,case,self.data["fixtures"],"win32")

    def test_asan_ubsan_require_actual_diagnostic_operation_summary_status(self):
        for kind in gate.CAPABILITIES:
            correct = capability(kind)
            gate.validate_capability(correct,kind)
            for wrong in (dict(correct,status=0),dict(correct,status=1),dict(correct,status=True),dict(correct,stdout="extra"),
                          dict(correct,stderr=""),dict(correct,stderr=correct["stderr"].replace("SUMMARY:","missing-summary:")),
                          dict(correct,stderr="FREAK: "+correct["stderr"])):
                with self.subTest(kind=kind,wrong=wrong), self.assertRaises(gate.GateError): gate.validate_capability(wrong,kind)

    def test_vector_missing_family_duplicate_wrong_oracle_and_unsafe_fixture_rejected(self):
        changed = []
        bad = deepcopy(self.data); bad["cases"].pop(); changed.append(bad)
        bad = deepcopy(self.data); bad["cases"][1]["id"] = bad["cases"][0]["id"]; changed.append(bad)
        bad = deepcopy(self.data); bad["cases"][0]["expected"]["stdout_hex"] = "00"; changed.append(bad)
        bad = deepcopy(self.data); bad["cases"][0]["expected"]["status"] = True; changed.append(bad)
        bad = deepcopy(self.data); bad["fixtures"]["empty"]["name"] = "..\\escape"; changed.append(bad)
        bad = deepcopy(self.data); bad["cases"][0]["id"] = "missing-family"; changed.append(bad)
        bad = deepcopy(self.data); bad["cases"][0]["argv"] = deepcopy(bad["cases"][1]["argv"]); bad["cases"][0]["expected"] = deepcopy(bad["cases"][1]["expected"]); changed.append(bad)
        bad = deepcopy(self.data); bad["cases"][0]["platforms"] = ["win32"]; changed.append(bad)
        path = self.directory / "bad.json"
        for bad in changed:
            path.write_text(json.dumps(bad))
            with self.assertRaises(gate.GateError): gate.load_vectors(path)

    def test_report_complete_matrix_fixture_tool_copy_binary_conservation(self):
        for sanitize in (False,True): gate.validate_report(synthetic_report(self.data,sanitize),self.data,sanitize)
        for host in ("darwin","win32"):
            gate.validate_report(synthetic_report(self.data,False,host),self.data,False)
            with self.assertRaises(gate.GateError): gate.validate_report(synthetic_report(self.data,True,host),self.data,True)
        good = synthetic_report(self.data,True)
        mutations = []
        bad = deepcopy(good); bad["complete"] = False; mutations.append(bad)
        bad = deepcopy(good); bad["matrices"].pop(); mutations.append(bad)
        bad = deepcopy(good); bad["matrices"][0]["cases"].pop(); mutations.append(bad)
        bad = deepcopy(good); bad["matrices"][0]["flags"].remove("-fsanitize=address,undefined"); mutations.append(bad)
        bad = deepcopy(good); bad["matrices"][0]["capabilities"].pop(); mutations.append(bad)
        bad = deepcopy(good); bad["final_frozen_source_hashes"].pop(gate.GUARD_NAME); mutations.append(bad)
        bad = deepcopy(good); bad["final_selected_compiler"] = "/metadata/drift"; mutations.append(bad)
        bad = deepcopy(good); bad["final_binary_hashes"]["/metadata/fs-O0"] = "d"*64; mutations.append(bad)
        bad = deepcopy(good); bad["final_fixture_facts"]["binary"]["sha256"] = "d"*64; mutations.append(bad)
        bad = deepcopy(good); bad["fixture_facts"] = bad["final_fixture_facts"] = {}; mutations.append(bad)
        bad = deepcopy(good)
        for field in ("source_hashes","final_source_hashes","final_frozen_source_hashes"): bad[field][gate.SUPPORT_NAME] = "d"*64
        mutations.append(bad)
        for bad in mutations:
            with self.assertRaises(gate.GateError): gate.validate_report(bad,self.data,True)

    def test_fixture_changes_missing_alias_and_directory_mutation_rejected(self):
        fixture_dir = self.directory / "fixtures"
        facts = gate.create_fixtures(fixture_dir,self.data,"win32")
        self.assertNotIn("fifo",facts)
        self.assertEqual(facts,gate.fixture_facts(fixture_dir,self.data,"win32"))
        path = fixture_dir / self.data["fixtures"]["binary"]["name"]
        data = path.read_bytes(); path.write_bytes(data+b"drift")
        with self.assertRaises(gate.GateError): gate.fixture_facts(fixture_dir,self.data,"win32")
        path.write_bytes(data)
        missing = fixture_dir / self.data["fixtures"]["missing"]["name"]
        missing.write_bytes(b"created")
        with self.assertRaises(gate.GateError): gate.fixture_facts(fixture_dir,self.data,"win32")
        missing.unlink()
        extra = fixture_dir / self.data["fixtures"]["directory"]["name"] / "extra"
        extra.write_bytes(b"changed")
        with self.assertRaises(gate.GateError): gate.fixture_facts(fixture_dir,self.data,"win32")

    def test_frozen_support_admitted_source_fresh_namespace_and_bounds(self):
        _, _, frozen, _, support, _ = self.fixture()
        self.assertEqual(support.COMPILE_SECONDS,120)
        self.assertEqual(support.COMPILE_MIB,512)
        self.assertEqual((support.RUN_SECONDS,support.RUN_MIB),(10,128))
        self.assertEqual(set(support.source_hashes()),set(gate.SOURCE_NAMES))
        with self.assertRaises(gate.GateError): gate.load_support(frozen)

    def test_transitive_runtime_and_vendor_inputs_retain_original_and_frozen_pins(self):
        root, _, frozen, compiler, support, report = self.fixture()
        pins = support.Conservation(compiler, frozen, report)
        pins.check()
        for name in ("freakc/runtime/freak_v35_process.inc",
                     "third_party/llhttp/freak_amalgamation.inc",
                     "third_party/llhttp/src/llhttp.c"):
            self.assertIn(name, report["source_hashes"])
            for directory, reason in ((root, "original source"), (frozen, "frozen source")):
                with self.subTest(name=name, directory=directory):
                    path = directory / name
                    original = path.read_bytes()
                    path.write_bytes(original + b"dependency drift\n")
                    with self.assertRaisesRegex(support.GateError, reason + " conservation failed"):
                        pins.check()
                    path.write_bytes(original)
                    pins.check()

    def test_sanitizer_options_are_clean_and_restored_without_harness(self):
        _, _, _, _, support, _ = self.fixture()
        previous = {name:"caller-value" for name in ("ASAN_OPTIONS","LSAN_OPTIONS","UBSAN_OPTIONS")}
        with patch.object(os,"environ",dict(previous)):
            with gate.sanitizer_environment(support,True):
                self.assertEqual(os.environ["ASAN_OPTIONS"],"halt_on_error=1:detect_leaks=1:exitcode=86")
                self.assertEqual(os.environ["UBSAN_OPTIONS"],"halt_on_error=1:print_stacktrace=1:exitcode=86")
                self.assertNotIn("LSAN_OPTIONS",os.environ)
            self.assertEqual(dict(os.environ),previous)
            with gate.sanitizer_environment(support,False):
                self.assertFalse(any(name in os.environ for name in previous))
            self.assertEqual(dict(os.environ),previous)

    def test_each_sanitizer_control_uses_agreeing_exit_codes_and_restores_outer_policy(self):
        _, _, _, _, support, _ = self.fixture()
        original = {name:"caller-option" for name in ("ASAN_OPTIONS","UBSAN_OPTIONS","LSAN_OPTIONS")}
        with patch.object(os,"environ",dict(original)):
            with gate.sanitizer_environment(support,True):
                outer = dict(os.environ)
                self.assertEqual(outer,gate.sanitizer_options(86))
                for kind in gate.CAPABILITIES:
                    code = 86 if kind == "asan-heap" else 85
                    with gate.sanitizer_environment(support,True,code):
                        self.assertEqual(dict(os.environ),gate.sanitizer_options(code))
                        self.assertTrue(all(value.endswith("exitcode="+str(code)) for value in os.environ.values()))
                    self.assertEqual(dict(os.environ),outer)
            self.assertEqual(dict(os.environ),original)
        for invalid in (True,84,87,"86",None):
            with self.assertRaises(gate.GateError): gate.sanitizer_options(invalid)

    @unittest.skipUnless(sys.platform == "linux", "the Linux sanitizer dispatch control needs real FIFO fixture support")
    def test_real_run_gate_dispatches_each_capability_under_its_fixed_exit_policy(self):
        _, work, _, compiler, support, report = self.fixture()
        rows = []
        data = self.data
        class MetadataOnly:
            def run_with_heartbeat(self,argv,**kwargs):
                if argv[1] == "--version": status,out,err = 0,"clang inert metadata\n",""
                elif argv[1] == "-dumpmachine": status,out,err = 0,"inert-host-metadata\n",""
                elif "-o" in argv:
                    Path(argv[argv.index("-o")+1]).write_bytes(b"inert binary fixture; never executable")
                    status,out,err = 0,"",""
                elif argv[1][2:] in gate.CAPABILITIES:
                    kind = argv[1][2:]
                    wanted = capability(kind)
                    code = 86 if kind == "asan-heap" else 85
                    observed = {name:os.environ.get(name) for name in ("ASAN_OPTIONS","UBSAN_OPTIONS")}
                    rows.append((kind,observed))
                    if observed != gate.sanitizer_options(code): raise AssertionError("wrong sanitizer policy at callback")
                    status,out,err = wanted["status"],wanted["stdout"],wanted["stderr"]
                else:
                    case = next(case for case in data["cases"] if "linux" in case["platforms"] and
                                argv[1:] == [str(work / "fixtures" / data["fixtures"][v[1:]]["name"]) if v.startswith("@") else v for v in case["argv"]])
                    wanted = gate.expected_case(case,data["fixtures"],"linux")
                    status,out,err = wanted["status"],wanted["stdout"],wanted["stderr"]
                return subprocess.CompletedProcess(argv,status,out,err)
        report["platform"],report["sanitized"] = "linux",True
        with patch.object(sys,"platform","linux"),patch.object(gate,"load_guard",lambda _:MetadataOnly()), \
                patch.object(os,"environ",{}),patch.object(gate,"print",lambda *a,**k:None,create=True):
            with gate.sanitizer_environment(support,True):
                pins = gate.run_gate(compiler,work,report,True,support,data)
                self.assertEqual(dict(os.environ),gate.sanitizer_options(86))
            self.assertEqual(dict(os.environ),{})
            self.assertEqual([kind for kind,_ in rows],list(gate.CAPABILITIES)*3)
            pins.check()
        self.assertIs(report["complete"],False)

    def test_run_gate_post_source_or_fixture_drift_rejects_before_second_metadata_callback(self):
        for target in ("source","fixture"):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as parent:
                self.directory = Path(parent).resolve()
                _, work, frozen, compiler, support, report = self.fixture()
                calls = []
                class MetadataOnly:
                    def run_with_heartbeat(self,argv,**kwargs):
                        calls.append(argv)
                        path = frozen / gate.OWNED_NAMES[0] if target == "source" else work / "fixtures" / self.data["fixtures"]["binary"]["name"]
                        path.write_bytes(path.read_bytes()+b"drift")
                        return subprocess.CompletedProcess(argv,0,"clang metadata fixture\n","")
                fake = MetadataOnly(); fake.data = self.data
                with patch.object(gate,"load_guard",lambda _:fake), self.assertRaises((gate.GateError,support.GateError)):
                    gate.run_gate(compiler,work,report,False,support,self.data)
                self.assertEqual(len(calls),1)
                self.assertIs(report["complete"],False)
                sys.modules.pop("v4_fs_read_bridge_frozen_support",None)

    def test_driver_main_primary_cancellation_and_each_failure_publication_fault(self):
        raw = Path.write_text
        for primary_type in (RuntimeError,KeyboardInterrupt):
            with self.subTest(primary_type=primary_type), tempfile.TemporaryDirectory() as parent:
                self.directory = Path(parent).resolve()
                _, _, _, compiler, _, _ = self.fixture()
                sys.modules.pop("v4_fs_read_bridge_frozen_support",None)
                work = self.directory / ("main-"+primary_type.__name__)
                class Hostile(primary_type):
                    def __str__(self): raise MemoryError("formatter must not run")
                primary, cause, writes = Hostile("original main failure"), ValueError("prior cause"), []
                primary.__cause__ = cause
                def no_gate(*args,**kwargs): raise primary
                def write(path,data,*args,**kwargs):
                    if path == work / "report.json":
                        writes.append(data)
                        if len(writes) == 2: raise MemoryError("failure publication failed")
                    return raw(path,data,*args,**kwargs)
                with patch.object(sys,"argv",["gate","--plain","--clang",str(compiler),"--work",str(work)]), \
                        patch.object(gate,"run_gate",no_gate),patch.object(Path,"write_text",write),self.assertRaises(primary_type) as seen:
                    gate.main()
                self.assertIs(seen.exception,primary)
                self.assertIs(primary.__cause__,cause)
                self.assertEqual(len(writes),2)
                self.assertIs(json.loads((work/"report.json").read_text())["complete"],False)
                sys.modules.pop("v4_fs_read_bridge_frozen_support",None)

    def test_driver_main_failure_attribution_is_independent_of_publication(self):
        raw_write, raw_load = Path.write_text, gate.load_support
        for primary_type in (RuntimeError,KeyboardInterrupt):
            for secondary_type in (MemoryError,KeyboardInterrupt):
                with self.subTest(primary_type=primary_type,secondary_type=secondary_type), tempfile.TemporaryDirectory() as parent:
                    self.directory = Path(parent).resolve()
                    _, _, _, compiler, _, _ = self.fixture()
                    sys.modules.pop("v4_fs_read_bridge_frozen_support",None)
                    work = self.directory / "main-attribution"
                    primary, secondary, cause, events = primary_type("first"), secondary_type("second"), ValueError("cause"), []
                    primary.__cause__ = cause
                    def load(frozen):
                        support = raw_load(frozen)
                        def descriptor(error):
                            events.append("attribution")
                            raise secondary
                        support.exception_descriptor = descriptor
                        return support
                    def no_gate(*args,**kwargs): raise primary
                    def write(path,data,*args,**kwargs):
                        if path == work / "report.json": events.append("publication")
                        return raw_write(path,data,*args,**kwargs)
                    with patch.object(sys,"argv",["gate","--plain","--clang",str(compiler),"--work",str(work)]), \
                            patch.object(gate,"run_gate",no_gate),patch.object(gate,"load_support",load), \
                            patch.object(Path,"write_text",write),self.assertRaises(primary_type) as seen:
                        gate.main()
                    self.assertIs(seen.exception,primary)
                    self.assertIs(primary.__cause__,cause)
                    self.assertEqual(events.count("publication"),2)
                    self.assertEqual(events[-1],"publication")
                    self.assertIs(json.loads((work / "report.json").read_text())["complete"],False)
                    sys.modules.pop("v4_fs_read_bridge_frozen_support",None)

    def test_fs_sanitizer_setup_and_body_first_cause_restore_all_options(self):
        _, _, _, _, support, _ = self.fixture()
        names = ("ASAN_OPTIONS","LSAN_OPTIONS","UBSAN_OPTIONS")
        for stage in ("setup","body","success"):
            for primary_type in (RuntimeError,KeyboardInterrupt):
                for secondary_type in (MemoryError,KeyboardInterrupt):
                    with self.subTest(stage=stage,primary_type=primary_type,secondary_type=secondary_type):
                        primary, secondary, cause, restored = primary_type("first"), secondary_type("cleanup"), ValueError("cause"), []
                        primary.__cause__ = cause
                        class Environment(dict):
                            def __setitem__(self,key,value):
                                if value.startswith("previous-"):
                                    restored.append(key)
                                    if key == "ASAN_OPTIONS": raise secondary
                                elif key == "UBSAN_OPTIONS" and stage == "setup": raise primary
                                super().__setitem__(key,value)
                        environment = Environment({name:"previous-"+name for name in names})
                        with patch.object(os,"environ",environment),self.assertRaises(secondary_type if stage == "success" else primary_type) as seen:
                            with gate.sanitizer_environment(support,True):
                                if stage == "setup": self.fail("setup failure entered body")
                                if stage == "body": raise primary
                        self.assertIs(seen.exception,secondary if stage == "success" else primary)
                        if stage != "success": self.assertIs(primary.__cause__,cause)
                        self.assertEqual(restored,list(names))
                        for name in names[1:]: self.assertEqual(environment[name],"previous-"+name)

    def test_probe_keeps_real_source_includes_typed_abi_and_prepublication_hooks(self):
        probe = (ROOT / gate.OWNED_NAMES[0]).read_text()
        header = (ROOT / "freakc/runtime/freak_v4_system_runtime.h").read_text()
        self.assertIn("void freak_v4_fs_read(int64_t path, int64_t *out_is_ok, int64_t *out_payload);",header)
        self.assertIn("static void (*const probe_fs_abi)(int64_t, int64_t *, int64_t *) = freak_v4_fs_read;",probe)
        for source in ("freak_runtime.c","freak_v4_word_runtime.c","freak_v4_system_runtime.c"):
            self.assertEqual(probe.count('#include "'+source+'"'),1)
        self.assertRegex(probe,r"if \(probe_fault & P_ADOPT\) return 0;\s+int64_t result = freak_llvm_word_try_adopt_sized")
        self.assertIn("return probe_fault & P_STREAM ? NULL : fdopen",probe)
        self.assertIn("return probe_fault & P_STREAM ? NULL : _fdopen",probe)
        self.assertIn("int result = fclose(file);",probe)
        self.assertIn("assert((flags & O_NONBLOCK) != 0);",probe)
        self.assertIn("record->length = probe_storage_length;",probe)
        self.assertIn("index < 64",probe)
        self.assertIn("probe_stat_calls == 1 && probe_stat_nonregular && probe_descriptor_closes == 1",probe)
        self.assertIn("freak_word owned = freak_word_from_int(1234);",probe)
        self.assertIn("owned.heap && owned.data && owned.length == 4",probe)
        self.assertIn('!memcmp(owned.data, "1234", 4) && freak_c_owned_word_count == 1',probe)
        self.assertIn("_set_abort_behavior(0, _WRITE_ABORT_MSG | _CALL_REPORTFAULT);",probe)


if __name__ == "__main__":
    unittest.main()
