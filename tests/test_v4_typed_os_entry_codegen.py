"""Pure closed-oracle, driver dispatch and failure-retention controls.

All child results in matrix replay are explicit inert metadata. No compiler,
transpiler, executable tool/image or project harness is imported or invoked.
"""
from contextlib import ExitStack
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

DRIVER = Path(__file__).with_name("v4_typed_os_entry_codegen.py")
NAME = "v4_typed_os_entry_pure_subject"
_spec = importlib.util.spec_from_file_location(NAME, DRIVER)
gate = importlib.util.module_from_spec(_spec)
sys.modules[NAME] = gate
_spec.loader.exec_module(gate)


def fixture_count_ast(source):
    """Parse the actual FK helper with pinned bootstrap syntax, without a pipeline.

    Only the lexer/parser sources enter a fresh private namespace. The evaluator
    admits the helper's closed AST subset and ASCII Word primitives; substring
    follows the existing runtime's (start, length), with no native execution.
    """
    package = "v4_typed_os_count_ast"
    names = (package, package + ".lexer", package + ".parser")
    if any(name in sys.modules for name in names):
        raise AssertionError("count AST namespace is not fresh")
    pins = {
        "lexer": "de70a25c8130b58574572c2e2ec27856dbfffd901cfc84ea59f684a6ea4f6f8c",
        "parser": "64fb824507b14a92fdb99d69707b2828ef01879f1f430c6fae67ba3149b9b821",
    }
    try:
        namespace = types.ModuleType(package)
        namespace.__path__ = []
        sys.modules[package] = namespace
        for role, expected in pins.items():
            path = gate.ROOT / "freakc" / (role + ".py")
            content = path.read_bytes()
            if hashlib.sha256(content).hexdigest() != expected:
                raise AssertionError("count AST bootstrap source pin drift")
            module = types.ModuleType(package + "." + role)
            module.__file__ = str(path)
            module.__package__ = package
            sys.modules[module.__name__] = module
            exec(compile(content, str(path), "exec"), module.__dict__)
        program = module.Parser.from_source(source)
        functions = [node for node in program.statements
                     if type(node).__name__ == "TaskDecl"
                     and node.name == "v4_typed_os_contract_count"]
        if len(functions) != 1:
            raise AssertionError("exact count helper is missing or duplicated")
        return functions[0]
    finally:
        for name in reversed(names):
            sys.modules.pop(name, None)


def evaluate_fixture_count(function, text, needle):
    if not text.isascii() or not needle.isascii() or not needle or len(text) > 4096:
        raise AssertionError("count AST controls require bounded nonempty ASCII needles")
    env = {"text": text, "needle": needle}
    class Returned(Exception):
        def __init__(self, value): self.value = value
    def expression(node):
        kind = type(node).__name__
        if kind == "IntLit": return node.value
        if kind == "Ident": return env[node.name]
        if kind == "BinOp":
            left, right = expression(node.left), expression(node.right)
            if node.op == "+": return left + right
            if node.op == ">": return left > right
            if node.op == "==": return left == right
        if kind == "MethodCall":
            value = expression(node.obj)
            args = [expression(arg) for arg in node.args]
            if node.method == "length" and not args: return len(value)
            if node.method == "substring" and len(args) == 2:
                start, length = args
                return value[start:start + length] if 0 <= start < len(value) and length > 0 else ""
        raise AssertionError("count AST expression outside closed subset: " + kind)
    def block(statements):
        for node in statements:
            kind = type(node).__name__
            if kind == "PilotDecl": env[node.name] = expression(node.value)
            elif kind == "Assign" and node.op == "+=" and type(node.target).__name__ == "Ident":
                env[node.target.name] += expression(node.value)
            elif kind == "RepeatUntil":
                remaining = len(text) + 1
                while not expression(node.condition):
                    remaining -= 1
                    if remaining < 0: raise AssertionError("count AST loop budget exceeded")
                    block(node.body.statements)
            elif kind == "IfExpr" and not node.elif_branches and node.else_block is None:
                if expression(node.condition): block(node.then_block.statements)
            elif kind == "GiveBack": raise Returned(expression(node.value))
            else: raise AssertionError("count AST statement outside closed subset: " + kind)
    try: block(function.body.statements)
    except Returned as result: return result.value
    raise AssertionError("count AST helper did not return")


def fake_module(program):
    arg, parser, fs, argc = gate.BRIDGE_COUNTS[program]
    lines = []
    if arg or fs: lines.append("%freak_result_word_word = type { i1, i64 }")
    if parser: lines.append("%freak_maybe_int = type { i1, i64 }")
    if arg or argc: lines.append("declare void @freak_v4_process_setup_args(i64, i64)")
    if argc: lines.append("declare i64 @freak_v4_process_args_count()")
    for symbol, count in (("freak_v4_process_arg_checked", arg), ("freak_v4_word_parse_int_checked", parser), ("freak_v4_fs_read", fs)):
        if count: lines.append("declare void @" + symbol + "(i64, ptr, ptr)")
        for index in range(count):
            stem = "%sum.out." + symbol + "." + str(index)
            lines += [stem + ".tag = alloca i64", stem + ".payload = alloca i64",
                      "store i64 0, ptr " + stem + ".tag", "store i64 0, ptr " + stem + ".payload",
                      "call void @" + symbol + "(i64 7, ptr " + stem + ".tag, ptr " + stem + ".payload)",
                      "load i64, ptr " + stem + ".tag", "load i64, ptr " + stem + ".payload"]
    lines += ["%count." + str(i) + " = call i64 @freak_v4_process_args_count()" for i in range(argc)]
    lines += ["define i32 @main(i32 %argc, ptr %argv) {", "call void @freak_llvm_setup_args(i64 %argc.ext, i64 %argv.int)"]
    if arg or argc: lines.append("call void @freak_v4_process_setup_args(i64 %argc.ext, i64 %argv.int)")
    lines += ["%result = call i64 @freak.user.main()", "ret i32 0", "}"]
    return "\n".join(lines) + "\n"


def capability(kind):
    if kind in ("C", "LLVM"):
        return subprocess.CompletedProcess([], 87 if kind == "C" else 86, "", f"FREAK: {kind} ownership audit found 1 unreleased word allocation(s)\n")
    if kind == "asan-heap":
        return subprocess.CompletedProcess([], 86, "", "ERROR: AddressSanitizer: heap-buffer-overflow\nSUMMARY: AddressSanitizer: heap-buffer-overflow\n")
    message = "signed integer overflow" if kind == "ubsan-overflow" else "shift exponent"
    return subprocess.CompletedProcess([], 85, "", "runtime error: " + message + "\nSUMMARY: UndefinedBehaviorSanitizer: " + message + "\n")


class PureGateTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.attempts = {name: 0 for name in ("Popen", "run", "call", "check_call", "check_output")}
        for name in self.attempts:
            def blocked(*args, name=name, **kwargs):
                self.attempts[name] += 1
                raise AssertionError("process API forbidden: " + name)
            self.stack.enter_context(patch.object(subprocess, name, blocked))
        self.previous_modules = set(sys.modules)
    def tearDown(self):
        for name in set(sys.modules) - self.previous_modules:
            if name.startswith("v4_typed_os_support_"): sys.modules.pop(name)
        self.stack.close()
        self.assertEqual(self.attempts, dict.fromkeys(self.attempts, 0))
        self.assertNotIn("v4_typed_os_frozen_checks", sys.modules)
        self.assertFalse(any(name == "freakc" or name.startswith("freakc.") for name in sys.modules))

    def test_actual_fk_count_ast_nonzero_offsets_trailing_bytes_and_mutation(self):
        source = (gate.ROOT / gate.OWNED_NAMES[0]).read_text()
        function = fixture_count_ast(source)
        samples = (("abc!", "abc", 1), ("xabc!", "abc", 1),
                   ("xabc!yabc!", "abc", 2), ("xaaaa!", "aa", 3),
                   ("xabc", "abc", 1), ("xno-match!", "abc", 0),
                   ("", "abc", 0), ("ab", "abc", 0))
        for text, needle, expected in samples:
            with self.subTest(text=text, needle=needle):
                self.assertEqual(evaluate_fixture_count(function, text, needle), expected)
        markers = ("call void @freak_v4_process_setup_args(",
                   "declare void @freak_v4_process_setup_args(",
                   "call void @freak_llvm_setup_args(")
        module = ("target triple = \"x86_64-unknown-linux-gnu\"\n\n"
                  "declare void @freak_v4_process_setup_args(i64, i64)\n"
                  "declare void @freak_llvm_setup_args(i64, i64)\n\n"
                  "define i32 @main(i32 %argc, ptr %argv) {\nentry:\n"
                  "  call void @freak_llvm_setup_args(i64 1, i64 0)\n"
                  "  call void @freak_v4_process_setup_args(i64 1, i64 0)\n"
                  "  ret i32 0\n}\n")
        for needle in markers:
            self.assertEqual(evaluate_fixture_count(function, module, needle), 1)
        # Reparse the historical defect into a real FK AST. This mutation must
        # miss later matches with trailing bytes and all three setup markers.
        fixed = "text.substring(offset, needle.length())"
        self.assertEqual(source.count(fixed), 1)
        old = fixture_count_ast(source.replace(fixed, "text.substring(offset, offset + needle.length())"))
        self.assertEqual(evaluate_fixture_count(old, "abc!", "abc"), 1)
        self.assertEqual(evaluate_fixture_count(old, "xabc!", "abc"), 0)
        self.assertEqual(evaluate_fixture_count(old, "xabc!yabc!", "abc"), 0)
        for needle in markers:
            self.assertEqual(evaluate_fixture_count(old, module, needle), 0)
        self.assertFalse(any(name.startswith("v4_typed_os_count_ast") for name in sys.modules))

    def test_closed_data_source_counts_and_no_nul_argv(self):
        gate.validate_data()
        self.assertEqual(len(gate.PROGRAMS), 9)
        self.assertEqual(len(gate.CASES), 40)
        self.assertEqual(len(gate.contract_cases()), 25)
        self.assertEqual(sum("win32" in row["platforms"] for row in gate.CASES), 38)
        self.assertEqual({row["program"] for row in gate.CASES}, set(gate.BRIDGE_COUNTS))
        self.assertTrue(all("\0" not in arg for row in gate.CASES for arg in row["argv"]))

    def test_data_mutation_rejects_before_jobs(self):
        for field, value in (("status", 99), ("stdout_hex", "00"), ("argv", ["N\0L"]), ("platforms", ["unknown"])):
            mutated = copy.deepcopy(gate.CASES)
            mutated[0][field] = value
            with self.subTest(field=field), patch.object(gate, "CASES", mutated):
                with self.assertRaises(RuntimeError): gate.validate_data()

    def test_all_exact_semantic_oracles_and_wrong_status_channels(self):
        for host in gate.COUNTS:
            for case in gate.CASES:
                if host not in case["platforms"]: continue
                stdout = bytes.fromhex(case["stdout_hex"]).decode()
                stderr = bytes.fromhex(case["stderr_hex"]).decode()
                result = subprocess.CompletedProcess([], case["status"], stdout, stderr)
                gate.assert_exact(result, case["status"], stdout.encode(), stderr.encode(), host)
                for field, value in (("returncode", 255), ("stdout", stdout + "extra"), ("stderr", "unexpected")):
                    forged = copy.copy(result); setattr(forged, field, value)
                    with self.subTest(host=host, case=case["id"], field=field):
                        with self.assertRaises(RuntimeError): gate.assert_exact(forged, case["status"], stdout.encode(), stderr.encode(), host)

    def test_windows_line_normalization_preserves_sized_nul(self):
        result = subprocess.CompletedProcess([], 0, "ok\r\nA\0é\r\n", "")
        gate.assert_exact(result, 0, "ok\nA\0é\n".encode(), b"", "win32")
        with self.assertRaises(RuntimeError): gate.assert_exact(result, 0, "ok\nAé\n".encode(), b"", "win32")
        with self.assertRaises(RuntimeError): gate.assert_exact(result, 0, "ok\nA\0é\n".encode(), b"", "linux")

    def test_parser_boundaries_and_nonascii_failure_goldens(self):
        table = {case["id"]:case for case in gate.CASES}
        for identity, number in (("zero", 0), ("minimum", -(1 << 63)), ("maximum", (1 << 63)-1), ("leading-plus", 42)):
            case = table["argument-" + identity]
            self.assertEqual(case["status"], 0)
            self.assertTrue(bytes.fromhex(case["stdout_hex"]).endswith((str(number)+"\n").encode()))
        for identity in ("empty", "unicode-digit", "space", "junk", "overflow", "sign-only"):
            case = table["argument-" + identity]
            self.assertEqual(case["status"], 2)
            self.assertTrue(bytes.fromhex(case["stdout_hex"]).endswith(b"nobody\n"))
        self.assertEqual(table["argument-missing"]["argv"], [])
        self.assertEqual(table["argument-missing"]["status"], 3)
        self.assertIn(b"4\x002", bytes.fromhex(table["parse-sized-nul"]["stdout_hex"]))

    def test_ownership_dataflow_program_shapes(self):
        for name in ("fs_echo", "fs_parse", "fs_discard_scopes", "fs_move_rebind", "fs_loop_edges"):
            self.assertIn("if path != saved", gate.PROGRAMS[name])
        self.assertIn("if text != saved", gate.PROGRAMS["fs_parse"])
        self.assertIn("relay_maybe(text.to_int())", gate.PROGRAMS["argument_parser"])
        self.assertIn("continue", gate.PROGRAMS["fs_loop_edges"])
        self.assertIn("break", gate.PROGRAMS["fs_loop_edges"])
        self.assertIn("ok(_) ->", gate.PROGRAMS["fs_discard_scopes"])
        self.assertIn("pilot first = process::arg(1)", gate.PROGRAMS["argument_bounds"])
        self.assertIn("pilot second = process::arg(1)", gate.PROGRAMS["argument_bounds"])
        self.assertIn('if path.contains("rebind-ok") { first = fs::read(path) } else { first = fs::read(path) }', gate.PROGRAMS["fs_move_rebind"])

    def test_closed_module_bridge_entry_shapes(self):
        for name in gate.PROGRAMS: gate.validate_module(fake_module(name), name)
        original = fake_module("argument_parser")
        mutants = [original.replace("ptr %sum.out.freak_v4_process_arg_checked.0.payload", "ptr %sum.out.freak_v4_process_arg_checked.0.tag"),
                   original.replace("declare void @freak_v4_process_arg_checked(i64, ptr, ptr)", "declare i64 @freak_v4_process_arg_checked(i64)"),
                   original.replace("load i64, ptr %sum.out.freak_v4_process_arg_checked.0.payload\n", ""),
                   original.replace("store i64 0, ptr %sum.out.freak_v4_process_arg_checked.0.tag\n", ""),
                   original.replace("call void @freak_v4_process_setup_args(i64 %argc.ext, i64 %argv.int)", ""),
                   original.replace("call void @freak_llvm_setup_args(i64 %argc.ext, i64 %argv.int)", "call void @freak_llvm_setup_args(i64 %argc.ext, i64 %argv.int)\ncall void @freak_llvm_setup_args(i64 %argc.ext, i64 %argv.int)"),
                   original + "call void @freak_v4_process_arg_checked(i64 7, ptr %extra.tag, ptr %extra.payload)\n",
                   original + "call i64 @freak_v4_process_arg(i64 1)\n"]
        for index, mutant in enumerate(mutants):
            with self.subTest(mutant=index), self.assertRaises(RuntimeError): gate.validate_module(mutant, "argument_parser")

    def test_module_protocol_rejects_failure_empty_duplicates(self):
        module = fake_module("argument_parser")
        text = gate.PREFIX + "@@LLVM-MODULE-BEGIN\n" + module + "@@LLVM-MODULE-END\n"
        result = subprocess.CompletedProcess([], 0, text, "")
        self.assertEqual(gate.extract_module(result, "linux"), module)
        for mutated in (subprocess.CompletedProcess([], 1, text, ""), subprocess.CompletedProcess([], 0, text, "error"), subprocess.CompletedProcess([], 0, text+text, ""), subprocess.CompletedProcess([], 0, gate.PREFIX+"@@LLVM-MODULE-BEGIN\n@@LLVM-MODULE-END\n", "")):
            with self.assertRaises(RuntimeError): gate.extract_module(mutated, "linux")

    def test_capability_status_channel_and_diagnostic_rejection(self):
        for kind in ("C", "LLVM", "asan-heap", "ubsan-overflow", "ubsan-shift"):
            good = capability(kind); gate.validate_capability(good, kind, "linux")
            for field, value in (("returncode", 0), ("stdout", "unexpected"), ("stderr", "")):
                mutated = copy.copy(good); setattr(mutated, field, value)
                with self.subTest(kind=kind, field=field), self.assertRaises(RuntimeError): gate.validate_capability(mutated, kind, "linux")

    def test_missing_root_grant_precedes_source_tool_reads(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(gate, "source_hashes", side_effect=AssertionError("source read forbidden")), patch.object(gate, "sha", side_effect=AssertionError("tool read forbidden")):
            with self.assertRaisesRegex(RuntimeError, "root compiler/native lease required"): gate.main(["--work", "/unreachable"])

    def test_frozen_bytecode_rejected_before_guard_import(self):
        for name in ("freakc/__pycache__/parser.pyc", "freakc/parser.pyo", "freakc/__pycache__"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                base = Path(temp).resolve(); path = base / name
                path.parent.mkdir(parents=True, exist_ok=True)
                if path.name == "__pycache__": path.mkdir()
                else: path.write_bytes(b"inert forbidden cache")
                with self.assertRaisesRegex(RuntimeError, "bytecode/cache is forbidden"): gate.load_checks(base)

    def test_sanitizer_first_cause_and_independent_cleanup(self):
        class Hostile(RuntimeError):
            def __str__(self): raise MemoryError("formatting forbidden")
        class Environment(dict):
            def __init__(self):
                super().__init__({"ASAN_OPTIONS":"caller-as", "LSAN_OPTIONS":"caller-ls", "UBSAN_OPTIONS":"caller-us"})
                self.restores=[]; self.fail=False
            def __setitem__(self,key,value):
                if value.startswith("caller-"):
                    self.restores.append(key)
                    if key == "ASAN_OPTIONS" and self.fail:
                        self.fail=False
                        raise MemoryError("secondary restore")
                return super().__setitem__(key,value)
        with tempfile.TemporaryDirectory() as temp:
            frozen=Path(temp).resolve(); path=frozen/gate.SUPPORT_NAME
            path.parent.mkdir(parents=True); path.write_bytes((gate.ROOT/gate.SUPPORT_NAME).read_bytes())
            support=gate.load_support(frozen,[gate.SUPPORT_NAME,gate.GUARD_NAME],"native")
            for error_type in (Hostile,KeyboardInterrupt):
                for exitcode in (85,86):
                    environment=Environment(); primary=error_type(); cause=RuntimeError("cause"); primary.__cause__=cause
                    with patch.object(os,"environ",environment):
                        try:
                            with gate.sanitizer_environment(support,True,exitcode):
                                self.assertIn("exitcode="+str(exitcode),environment["ASAN_OPTIONS"])
                                self.assertIn("exitcode="+str(exitcode),environment["UBSAN_OPTIONS"])
                                environment.fail=True; raise primary
                        except BaseException as actual:
                            self.assertIs(actual,primary); self.assertIs(actual.__cause__,cause)
                        else: self.fail("primary vanished")
                    self.assertEqual(environment.restores,["ASAN_OPTIONS","LSAN_OPTIONS","UBSAN_OPTIONS"])
                    self.assertEqual(environment["LSAN_OPTIONS"],"caller-ls")
                    self.assertEqual(environment["UBSAN_OPTIONS"],"caller-us")

    def prepare_fake_tree(self, base):
        original = base / "original"; original.mkdir()
        names = [*gate.OWNED_NAMES, gate.SUPPORT_NAME, gate.GUARD_NAME,
                 *("src/compiler/v4/crates/" + crate + "/src/lib.fk" for crate in gate.CRATES),
                 *("freakc/runtime/" + name for name in (*gate.RUNTIME_SOURCES, *gate.RUNTIME_HEADERS)),
                 "freakc/__main__.py"]
        for name in names:
            path = original / name; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((gate.ROOT / gate.SUPPORT_NAME).read_bytes() if name == gate.SUPPORT_NAME else b"inert source-only metadata\n")
        compiler = base / "fake-clang"; compiler.write_bytes(b"non-executable fake compiler\n")
        work = base / "work"; work.mkdir()
        frozen = work / "frozen-source"
        for name in names:
            path = frozen / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes((original / name).read_bytes())
        return original, compiler.resolve(), work, frozen, names

    def simulate(self, host, sanitize):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp).resolve()
            original, compiler, work, frozen, names = self.prepare_fake_tree(base)
            callbacks = []
            fixtures = work / "fixtures"
            rows = [case for case in gate.CASES if host in case["platforms"]]
            controls = ("C", "LLVM", "asan-heap", "ubsan-overflow", "ubsan-shift") if sanitize else ("C", "LLVM")
            contracts = iter(gate.contract_cases())
            emissions = iter(gate.PROGRAMS)
            native = iter((kind, opt) for opt in gate.OPTS for kind in controls)
            cases = iter((case, opt) for opt in gate.OPTS for case in rows)
            def guard(argv, *, label, timeout_seconds, memory_limit_mb, output_limit_mb):
                self.assertEqual(output_limit_mb, 1)
                callbacks.append(label)
                if "-o" in argv:
                    bootstrap = label.startswith("bootstrap-")
                    self.assertEqual((timeout_seconds, memory_limit_mb), (120,1024 if bootstrap else 512))
                    if not bootstrap:
                        for flag in gate.AUDIT_FLAGS: self.assertIn(flag, argv)
                        for flag in gate.SANITIZER_FLAGS: self.assertEqual(flag in argv, sanitize)
                    Path(argv[argv.index("-o")+1]).write_bytes(b"non-executable inert image\n")
                    return subprocess.CompletedProcess(argv, 0, "", "")
                if label == "compiler-version":
                    self.assertEqual((timeout_seconds, memory_limit_mb), (120,512))
                    return subprocess.CompletedProcess(argv, 0, "clang inert metadata\n", "")
                if label == "compiler-target": return subprocess.CompletedProcess(argv, 0, "inert-target\n", "")
                if label.startswith("contract-"):
                    case = next(contracts)
                    self.assertEqual((timeout_seconds,memory_limit_mb), (60,64))
                    self.assertEqual(argv[1:], [case["mode"], str(work / ("contract-"+case["name"]+".fk")), gate.host_target(), case["expected"], case["identity"]])
                    return subprocess.CompletedProcess(argv, 0, "typed-os-entry-contract mode="+case["mode"]+"=passed\n", "")
                if label.startswith("emit-"):
                    name = next(emissions)
                    self.assertEqual((timeout_seconds,memory_limit_mb), (60,64))
                    self.assertEqual(argv[1:], [str(work/(name+".fk")),gate.host_target()])
                    return subprocess.CompletedProcess(argv, 0, gate.PREFIX+"@@LLVM-MODULE-BEGIN\n"+fake_module(name)+"@@LLVM-MODULE-END\n", "")
                self.assertEqual((timeout_seconds,memory_limit_mb), (30,128))
                if label.startswith("capability-"):
                    kind, opt = next(native)
                    self.assertEqual(argv, [str(work / (f"capability-O{opt}"+(".exe" if host=="win32" else ""))),kind])
                    result = capability(kind)
                else:
                    case, opt = next(cases)
                    expected_argv = [str(fixtures / case["fixture"]["relative_path"]) if value == "@fixture-path" else value for value in case["argv"]]
                    self.assertEqual(argv, [str(work/(case["program"]+f"-O{opt}"+(".exe" if host=="win32" else ""))),*expected_argv])
                    result = subprocess.CompletedProcess(argv, case["status"], bytes.fromhex(case["stdout_hex"]).decode(), "")
                if sanitize:
                    code = 85 if label.endswith(("ubsan-overflow", "ubsan-shift")) else 86
                    self.assertEqual(os.environ.get("ASAN_OPTIONS"), f"halt_on_error=1:detect_leaks=1:exitcode={code}")
                    self.assertEqual(os.environ.get("UBSAN_OPTIONS"), f"halt_on_error=1:print_stacktrace=1:exitcode={code}")
                    self.assertNotIn("LSAN_OPTIONS", os.environ)
                else: self.assertTrue(all(name not in os.environ for name in ("ASAN_OPTIONS","LSAN_OPTIONS","UBSAN_OPTIONS")))
                return result
            checks = types.SimpleNamespace(flattened_crates=lambda:"inert flat",transpile_fixture=lambda flat,fixture:("inert generated C",False),runtime_platform_link_args=lambda:[],runtime_platform_final_link_args=lambda:[],run_with_heartbeat=guard)
            previous = {"ASAN_OPTIONS":"caller-as","LSAN_OPTIONS":"caller-ls","UBSAN_OPTIONS":"caller-us"}
            with patch.object(gate,"ROOT",original), patch.object(gate.sys,"platform",host), patch.object(gate,"host_target",return_value="inert-target"), patch.object(gate,"load_checks",return_value=checks), patch.dict(os.environ,previous,clear=True):
                supports = tuple(gate.load_support(frozen,names,role) for role in ("native","compiler","bootstrap"))
                report = {"complete":False,"platform":host,"sanitized":sanitize,"scope":gate.SCOPE,"data_sha256":gate.DATA_SHA,"work":str(work),"compiler_process_contract":{"seconds":60,"memory_mib":64,"live_handles":1024},"source_hashes":gate.source_hashes(),"compiler":{"selected":str(compiler),"path":str(compiler),"sha256":gate.sha(compiler)},"contracts":[],"emissions":[],"programs":[],"controls":[]}
                with gate.sanitizer_environment(supports[0],sanitize), patch("sys.stdout",io.StringIO()):
                    pins=gate.run_gate(compiler,work,frozen,report,supports)
                self.assertEqual(dict(os.environ),previous)
                pins.final_pins(); report["complete"]=True; gate.validate_report(report,sanitize)
                self.assertEqual(len(callbacks),224 if sanitize else (209 if host=="win32" else 215))
                self.assertEqual(len(report["binary_hashes"]),53)
                self.assertEqual(len(report["artifact_hashes"]),46)
                for field in ("contracts","emissions","programs","controls"):
                    forged=copy.deepcopy(report); forged[field]=forged[field][:-1]
                    with self.subTest(host=host, missing=field), self.assertRaises(RuntimeError): gate.validate_report(forged,sanitize)
                for field in ("source_hashes","final_artifact_hashes","final_binary_hashes"):
                    forged=copy.deepcopy(report); forged[field]={}
                    with self.subTest(host=host, forged=field), self.assertRaises(RuntimeError): gate.validate_report(forged,sanitize)
                image=Path(next(iter(pins.binaries))); image.write_bytes(b"drifted inert image")
                with self.assertRaises(supports[0].GateError): pins.check()

    @unittest.skipUnless(sys.platform == "linux", "full inert replay uses POSIX FIFO; physical platform/native proof is separate")
    def test_full_inert_linux_plain_matrix_and_conservation(self): self.simulate("linux",False)
    @unittest.skipUnless(sys.platform == "linux", "full inert replay uses POSIX FIFO; physical platform/native proof is separate")
    def test_full_inert_linux_sanitized_matrix_and_policies(self): self.simulate("linux",True)
    @unittest.skipUnless(sys.platform == "linux", "full inert replay uses POSIX FIFO; physical platform/native proof is separate")
    def test_full_inert_darwin_plain_matrix(self): self.simulate("darwin",False)
    def test_full_inert_windows_plain_matrix(self): self.simulate("win32",False)

    def test_pre_support_primary_preserved_when_report_publication_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp).resolve(); compiler=base/"fake-clang"; compiler.write_bytes(b"non-executable")
            primary=KeyboardInterrupt("first"); cause=RuntimeError("explicit"); primary.__cause__=cause
            real_write=Path.write_text; writes=[]
            def write(path,*args,**kwargs):
                writes.append(path.name)
                if len(writes)>1: raise MemoryError("secondary")
                return real_write(path,*args,**kwargs)
            with patch.dict(os.environ,{gate.GRANT_NAME:gate.GRANT_VALUE},clear=True), patch.object(gate,"source_hashes",side_effect=primary), patch.object(Path,"write_text",write):
                try: gate.main(["--plain","--clang",str(compiler),"--work",str(base/"out")])
                except BaseException as actual:
                    self.assertIs(actual,primary); self.assertIs(actual.__cause__,cause)
                else: self.fail("primary vanished")
            self.assertEqual(writes,["report.json","report.json"])
            self.assertFalse(json.loads((base/"out/report.json").read_text())["complete"])


if __name__ == "__main__": unittest.main()
