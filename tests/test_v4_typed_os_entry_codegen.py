"""Pure closed-oracle, driver dispatch and failure-retention controls.

Fresh bootstrap AST/type diagnostics are source-only. All child results in
matrix replay are explicit inert metadata. No compiler/transpiler pipeline,
executable tool/image or project harness is imported or invoked.
"""
from contextlib import ExitStack, contextmanager
import ast
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


@contextmanager
def bootstrap_fixture_types():
    """Fresh pinned bootstrap syntax/type readers, without emitters or harnesses."""
    package = "v4_typed_os_fixture_types"
    names = (package, package + ".lexer", package + ".parser", package + ".type_checker")
    if any(name in sys.modules for name in names):
        raise AssertionError("fixture type namespace is not fresh")
    pins = {
        "lexer": "de70a25c8130b58574572c2e2ec27856dbfffd901cfc84ea59f684a6ea4f6f8c",
        "parser": "64fb824507b14a92fdb99d69707b2828ef01879f1f430c6fae67ba3149b9b821",
        "type_checker": "15f9e19563d577cbecac653e1d38cd217a127c37f2ddd90e7a57c612d6d1e480",
    }
    try:
        namespace = types.ModuleType(package)
        namespace.__path__ = []
        sys.modules[package] = namespace
        for role, expected in pins.items():
            path = gate.ROOT / "freakc" / (role + ".py")
            content = path.read_bytes()
            if hashlib.sha256(content).hexdigest() != expected:
                raise AssertionError("fixture type bootstrap source pin drift")
            module = types.ModuleType(package + "." + role)
            module.__file__ = str(path)
            module.__package__ = package
            sys.modules[module.__name__] = module
            exec(compile(content, str(path), "exec"), module.__dict__)
        yield sys.modules[package + ".parser"].Parser, module.TypeChecker
    finally:
        for name in reversed(names): sys.modules.pop(name, None)


def fixture_core_source_root():
    # Isolated preparation precedes core integration. An external, frozen source
    # prototype tree may be selected for pure checks; actual gate paths are fixed.
    return Path(os.environ.get("FREAK_TYPED_OS_PURE_CORE_ROOT", str(gate.ROOT))).resolve()


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


def source_task_ast(Parser, source, name):
    marker = "task " + name + "("
    if source.count(marker) != 1:
        raise AssertionError("exact source task is missing or duplicated")
    start = source.index(marker)
    end = source.find("\ntask ", start + len(marker))
    program = Parser.from_source(source[start:] if end < 0 else source[start:end])
    tasks = [node for node in program.statements if type(node).__name__ == "TaskDecl"]
    if len(tasks) != 1 or tasks[0].name != name:
        raise AssertionError("source task parse changed")
    return tasks[0]


def evaluate_source_branch(function, arguments, helpers, constants):
    """Bounded actual FK AST, with explicit query/operation leaves only.

    This interprets source branches rather than compiling or executing a V4
    pipeline. Query answers are a declared model; unlisted operations reject.
    """
    if len(function.params) != len(arguments):
        raise AssertionError("source branch argument count differs")
    env = dict(zip((param.name for param in function.params), arguments))
    remaining = 20000
    class Returned(Exception):
        def __init__(self, value): self.value = value
    def expression(node):
        nonlocal remaining
        remaining -= 1
        if remaining < 0: raise AssertionError("source branch budget exhausted")
        kind = type(node).__name__
        if kind in ("IntLit", "BoolLit"): return node.value
        if kind == "StrLit":
            if any(value is not None for _, value in (node.parts or [])):
                raise AssertionError("interpolation outside source branch model")
            return node.value
        if kind == "Ident":
            if node.name in env: return env[node.name]
            if node.name in constants: return constants[node.name]
            raise AssertionError("undeclared source branch value: " + node.name)
        if kind == "UnaryOp":
            value = expression(node.operand)
            if node.op == "not": return not value
            if node.op == "-": return -value
        if kind == "BinOp":
            left = expression(node.left)
            if node.op == "and": return bool(left and expression(node.right))
            if node.op == "or": return bool(left or expression(node.right))
            right = expression(node.right)
            if node.op == "+": return left + right
            if node.op == "-": return left - right
            if node.op == "==": return left == right
            if node.op == "!=": return left != right
            if node.op == "<": return left < right
            if node.op == "<=": return left <= right
            if node.op == ">": return left > right
            if node.op == ">=": return left >= right
        if kind == "Call" and type(node.func).__name__ in ("Ident", "PathIdent"):
            name = node.func.name if type(node.func).__name__ == "Ident" else "::".join(node.func.parts)
            if name not in helpers:
                raise AssertionError("undeclared source branch operation: " + name)
            return helpers[name](*[expression(arg) for arg in node.args])
        if kind == "MethodCall" and node.method == "starts_with" and len(node.args) == 1:
            return expression(node.obj).startswith(expression(node.args[0]))
        raise AssertionError("AST outside closed source branch model: " + kind)
    def block(statements):
        for node in statements:
            kind = type(node).__name__
            if kind == "PilotDecl": env[node.name] = expression(node.value)
            elif kind == "Assign" and type(node.target).__name__ == "Ident":
                value = expression(node.value)
                if node.op == "=": env[node.target.name] = value
                elif node.op == "+=": env[node.target.name] += value
                else: raise AssertionError("assignment outside source branch model")
            elif kind == "ExprStmt": expression(node.expr)
            elif kind == "SayStmt": helpers["say"](expression(node.value))
            elif kind == "IfExpr":
                if expression(node.condition): block(node.then_block.statements)
                else:
                    for condition, body in node.elif_branches:
                        if expression(condition): block(body.statements); break
                    else:
                        if node.else_block is not None: block(node.else_block.statements)
            elif kind == "RepeatUntil":
                turns = 1024
                while not expression(node.condition):
                    turns -= 1
                    if turns < 0: raise AssertionError("source branch loop budget exhausted")
                    block(node.body.statements)
            elif kind == "GiveBack": raise Returned(expression(node.value) if node.value is not None else None)
            else: raise AssertionError("statement outside source branch model: " + kind)
    try: block(function.body.statements)
    except Returned as result: return result.value
    return None


def fake_module(program, target=None):
    arg, parser, fs, argc = gate.BRIDGE_COUNTS[program]
    lines = [] if target is None else ['target triple = "' + target + '"']
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
    def test_shadow_namespace_source_branches_preserve_zero_builtin_identity(self):
        rows = {row["name"]:row for row in gate.contract_cases()}
        core = fixture_core_source_root()
        ty_source = (core / "src/compiler/v4/crates/freak_ty/src/lib.fk").read_text()
        parse_source = (core / "src/compiler/v4/crates/freak_parse/src/lib.fk").read_text()
        hir_source = (core / "src/compiler/v4/crates/freak_hir/src/lib.fk").read_text()
        builder = (core / "src/compiler/v4/crates/freak_mir_build/src/lib.fk").read_text()
        llvm = (core / "src/compiler/v4/crates/freak_codegen_llvm/src/lib.fk").read_text()
        with bootstrap_fixture_types() as (Parser, _):
            constants = {"v4_tok_keyword":"Keyword", "v4_node_const":"ConstDecl", "v4_hir_const":"Const"}
            root = rows["root-process"]
            self.assertEqual(root["source"], "fixed pilot process: int = 1\ntask main() -> int { give back process::arg(1) }\n")
            tokens = root["source"].split()[:2]
            leaves = {"v4_lex_token_count":lambda stream:2,
                      "v4_lex_token_type":lambda stream, index:"Keyword",
                      "v4_lex_token_value":lambda stream, index:tokens[index],
                      "v4_parse_skip_trivia":lambda stream, index:index}
            fixed = source_task_ast(Parser, parse_source, "v4_parse_is_fixed_pilot_keyword")
            self.assertTrue(evaluate_source_branch(fixed, [0, 0], leaves, constants))
            leaves["v4_parse_is_fixed_pilot_keyword"] = lambda *args:evaluate_source_branch(fixed, args, leaves, constants)
            keyword = source_task_ast(Parser, parse_source, "v4_parse_top_keyword_text")
            self.assertEqual(evaluate_source_branch(keyword, [0, 0], leaves, constants), "fixed pilot")
            kind = source_task_ast(Parser, parse_source, "v4_parse_kind_for_keyword")
            self.assertEqual(evaluate_source_branch(kind, ["fixed pilot"], {}, constants), "ConstDecl")
            hir_kind = source_task_ast(Parser, hir_source, "v4_hir_kind_from_parse")
            constants.update({"v4_node_"+key:key for key in ("task", "shape", "route", "alias")})
            self.assertEqual(evaluate_source_branch(hir_kind, ["ConstDecl"], {}, constants), "Const")
            admission = source_task_ast(Parser, ty_source, "v4_ty_system_intrinsic_named_kind")
            intrinsic = source_task_ast(Parser, builder, "v4_mir_try_lower_system_named_intrinsic")
            for name in ("local-fs", "root-process", "import-fs"):
                case = rows[name]
                self.assertEqual(case["mode"], "ordinary-native-reject")
                self.assertEqual(case["expected"], "native rvalue not yet supported: Unknown")
                public = "process::arg" if name == "root-process" else "fs::read"
                namespace = public.split("::")[0]
                trace = []
                def const(ty, binding):
                    trace.append(("const",binding)); return 0 if name == "root-process" and binding == "process" else -1
                def expanded(resolve, binding):
                    trace.append(("import",binding))
                    return "user::filesystem::read" if name == "import-fs" and binding == "fs::read" else binding
                leaves = {"v4_ty_file_exists":lambda *args:True,
                          "v4_ty_task_signature_id_for_name":lambda *args:-1,
                          "v4_ty_const_signature_id_for_name":const,
                          "v4_ty_type_signature_id_for_name":lambda *args:-1,
                          "v4_ty_resolve_id":lambda *args:0,
                          "v4_resolve_def_for_name":lambda *args:"",
                          "v4_resolve_expand_import_name":expanded}
                admitted = evaluate_source_branch(admission, [0, public], leaves, {})
                self.assertEqual(admitted, "fs_read" if name == "local-fs" else "")
                if name == "root-process": self.assertEqual(trace, [("const","process")])
                if name == "import-fs": self.assertIn(("import","fs::read"), trace)
                tokens = (namespace,"::",public.split("::")[1],"(","1",")")
                leaves.update({"v4_lex_token_syntax_value":lambda stream, index:tokens[index],
                               "v4_mir_next_nontrivia":lambda stream, index, end:index,
                               "v4_mir_find_matching_paren":lambda *args:5,
                               "v4_mir_ty_id":lambda *args:0,
                               "v4_ty_system_intrinsic_named_kind":lambda *args:admitted,
                               "v4_mir_find_local_visible_at":lambda mir, body, binding, offset:0 if name == "local-fs" and binding == "fs" else -1,
                               "v4_span_start":lambda *args:0})
                # No descriptor-allocation leaf is admitted: entering it fails the test.
                self.assertEqual(evaluate_source_branch(intrinsic, [0,0,0,0,5,"span"], leaves, {}), -1)
                leaves.update({"v4_mir_find_open_paren_token":lambda *args:3,
                               "v4_mir_shape_ctor_name":lambda *args:public,
                               "v4_mir_signature_id_for_name":lambda *args:-1,
                               "v4_mir_rvalue_kind":lambda *args:"Unknown",
                               "v4_codegen_llvm_scalar_sum_rvalue_is_supported":lambda *args:False})
                ordinary = source_task_ast(Parser, builder, "v4_mir_try_lower_named_call")
                self.assertEqual(evaluate_source_branch(ordinary, [0,0,0,0,5,"span"], leaves, {}), -1)
                fallback = source_task_ast(Parser, builder, "v4_mir_lower_expr_expected").body.statements[-1]
                self.assertEqual(fallback.value.args[2].name,"v4_mir_rvalue_unknown")
                native = source_task_ast(Parser, llvm, "v4_codegen_llvm_native_rvalue_error")
                mir_source = (core / "src/compiler/v4/crates/freak_mir/src/lib.fk").read_text()
                constants = {node.name:node.value.value for node in Parser.from_source(mir_source.split("\ntask ",1)[0]).statements
                             if type(node).__name__ == "PilotDecl" and type(node.value).__name__ == "StrLit"}
                constants["v4_codegen_llvm_active_owned_mir"] = 0
                self.assertEqual(evaluate_source_branch(native,[0,0,0],leaves,constants),case["expected"])

    def test_private_fs_extern_source_alias_reaches_exact_reserved_symbol_fence(self):
        case = next(row for row in gate.contract_cases() if row["name"] == "private-fs-symbol")
        self.assertEqual(case["mode"], "native-reject")
        self.assertEqual(case["source"], "extern [C] { task freak_v4_fs_read() -> std::ffi::c_isize }\ntask main() -> int { give back 0 }\n")
        core = fixture_core_source_root()
        ty_source = (core / "src/compiler/v4/crates/freak_ty/src/lib.fk").read_text()
        llvm = (core / "src/compiler/v4/crates/freak_codegen_llvm/src/lib.fk").read_text()
        with bootstrap_fixture_types() as (Parser, _):
            constants = {"v4_ty_unknown":"<unknown>","v4_ty_int":"int","v4_ty_void":"void"}
            normalize = source_task_ast(Parser, ty_source, "v4_ty_normalize_ffi_alias_type")
            leaves = {"v4_ty_surface_ffi_alias_name":lambda text:text.removeprefix("std::ffi::")}
            self.assertEqual(evaluate_source_branch(normalize, ["int"], leaves, constants), "")
            self.assertEqual(evaluate_source_branch(normalize, ["std::ffi::c_isize"], leaves, constants), "int")
            leaves["v4_ty_normalize_ffi_alias_type"] = lambda text:evaluate_source_branch(normalize, [text], leaves, constants)
            for name in ("v4_ty_is_raw_pointer_type", "v4_ty_is_surface_extern_function_pointer_type", "v4_ty_is_surface_task_function_type", "v4_ty_is_fixed_array_type", "v4_ty_is_tuple_type", "v4_ty_ffi_seen_contains", "v4_ty_surface_ffi_safe_repr_route_seen"):
                leaves[name] = lambda *args:False
            leaves.update({"v4_ty_alias_target_type":lambda *args:"", "v4_ty_shape_signature_id_for_name":lambda *args:-1})
            safe = source_task_ast(Parser, ty_source, "v4_ty_surface_ffi_safe_type_seen")
            self.assertFalse(evaluate_source_branch(safe, [0,"int",True,""], leaves, constants))
            self.assertTrue(evaluate_source_branch(safe, [0,"std::ffi::c_isize",True,""], leaves, constants))
            reserved = source_task_ast(Parser, llvm, "v4_codegen_llvm_numeric_reserved_symbol_error")
            symbol = "@freak_v4_fs_read"
            self.assertEqual(evaluate_source_branch(reserved, [symbol], {}, {}), case["expected"])
            leaves = {"v4_codegen_llvm_body_count":lambda *args:0,
                      "v4_codegen_llvm_decl_count":lambda *args:1,
                      "v4_codegen_llvm_decl_symbol":lambda *args:symbol,
                      "v4_codegen_llvm_numeric_reserved_symbol_error":lambda value:evaluate_source_branch(reserved,[value],{}, {})}
            error = source_task_ast(Parser, llvm, "v4_codegen_llvm_numeric_runtime_symbol_error")
            self.assertEqual(evaluate_source_branch(error,[0],leaves,{}),case["expected"])

    def test_ffi_frontend_and_exact_native_fence_protocol(self):
        case = next(row for row in gate.contract_cases() if row["name"] == "foreign-maybe")
        self.assertEqual(case["mode"], "ffi-native-reject")
        self.assertEqual(case["expected"], "native scalar sum C ABI is not yet supported")
        source = (gate.ROOT / gate.OWNED_NAMES[0]).read_text()
        with bootstrap_fixture_types() as (Parser, _):
            task = source_task_ast(Parser, source, "v4_typed_os_contract_run")
            assertion = source_task_ast(Parser, source, "v4_typed_os_contract_assert")
            class Rejected(Exception): pass
            controls = ((None,None),("lex",1),("parse",1),("hir",1),("resolve",1),
                        ("ty",0),("mir",0),("error","wrong"),("module","published"),
                        ("mode","native-reject"),("mode","ordinary-native-reject"))
            for field,value in controls:
                facts = {"mode":case["mode"],"lex":0,"parse":0,"hir":0,"resolve":0,"ty":2,"mir":2,"error":case["expected"],"module":""}
                if field is not None: facts[field] = value
                said = []
                def panic(label): raise Rejected(label)
                leaves = {"process::arg":lambda index:{1:facts["mode"],2:"source",3:"target",4:case["expected"],5:""}[index],
                          "fs::read":lambda *args:case["source"],"v4_target_spec_new":lambda *args:0,
                          "v4_codegen_llvm_lower_owned_mir_with_panic":lambda *args:0,
                          "v4_codegen_llvm_native_module_error":lambda *args:facts["error"],
                          "v4_codegen_llvm_module_text":lambda *args:facts["module"],"panic":panic,"say":said.append}
                for name in ("v4_lex_text","v4_parse_stream","v4_hir_lower_tree","v4_resolve_lower_hir","v4_ty_lower_resolve","v4_mir_lower_ty"):
                    leaves[name] = lambda *args:0
                for phase in ("lex","parse","hir","resolve","ty","mir"):
                    leaves["v4_"+phase+"_diag_count"] = lambda *args,phase=phase:facts[phase]
                leaves["v4_typed_os_contract_assert"] = lambda condition,label:evaluate_source_branch(assertion,[condition,label],leaves,{})
                with self.subTest(field=field,value=value):
                    if field is None:
                        evaluate_source_branch(task,[],leaves,{})
                        self.assertEqual(said,["typed-os-entry-contract mode=ffi-native-reject=passed"])
                    else:
                        with self.assertRaises(Rejected): evaluate_source_branch(task,[],leaves,{})
                        self.assertEqual(said,[])

    def test_formal_shadow_actual_source_branches_and_named_native_fence(self):
        case = next(row for row in gate.contract_cases() if row["name"] == "parameter-process")
        self.assertEqual(case["mode"], "ordinary-native-reject")
        self.assertEqual(case["expected"], "native rvalue not yet supported: Unknown")
        self.assertEqual(case["identity"], "builtin::system::process_arg")
        self.assertEqual(case["source"], "task inspect(process: int) -> int { give back process::arg(1) }\ntask main() -> int { give back inspect(0) }\n")
        core = fixture_core_source_root()
        builder = (core / "src/compiler/v4/crates/freak_mir_build/src/lib.fk").read_text()
        llvm = (core / "src/compiler/v4/crates/freak_codegen_llvm/src/lib.fk").read_text()
        mir = (core / "src/compiler/v4/crates/freak_mir/src/lib.fk").read_text()
        with bootstrap_fixture_types() as (Parser, _):
            tasks = Parser.from_source(case["source"]).statements
            self.assertEqual([(node.name, [p.name for p in node.params]) for node in tasks], [("inspect", ["process"]), ("main", [])])
            constants = {node.name:node.value.value for node in Parser.from_source(mir.split("\ntask ", 1)[0]).statements
                         if type(node).__name__ == "PilotDecl" and type(node.value).__name__ == "StrLit"}
            constants["v4_codegen_llvm_active_owned_mir"] = 0
            trace = []
            tokens = ("process", "::", "arg", "(", "1", ")")
            def visible(mir_id, body, name, offset):
                trace.append(("visible", name, offset)); return 0 if name == "process" else -1
            helpers = {
                "v4_lex_token_syntax_value": lambda stream, index: tokens[index],
                "v4_mir_next_nontrivia": lambda stream, index, end: index,
                "v4_mir_find_matching_paren": lambda stream, first, end: 5,
                "v4_mir_ty_id": lambda mir_id: 0,
                "v4_ty_system_intrinsic_named_kind": lambda ty, name: "process_arg",
                "v4_mir_find_local_visible_at": visible,
                "v4_span_start": lambda span: 49,
                "v4_mir_find_open_paren_token": lambda stream, first, last: 3,
                "v4_mir_shape_ctor_name": lambda stream, first, opening: "process::arg",
                "v4_mir_signature_id_for_name": lambda mir_id, name: -1,
                "v4_mir_rvalue_kind": lambda mir_id, body, value: "Unknown",
                "v4_codegen_llvm_scalar_sum_rvalue_is_supported": lambda *args: False,
            }
            intrinsic = source_task_ast(Parser, builder, "v4_mir_try_lower_system_named_intrinsic")
            ordinary = source_task_ast(Parser, builder, "v4_mir_try_lower_named_call")
            self.assertEqual(evaluate_source_branch(intrinsic, [0, 0, 0, 0, 5, "span"], helpers, constants), -1)
            self.assertEqual(trace, [("visible", "process", 49)])
            self.assertEqual(evaluate_source_branch(ordinary, [0, 0, 0, 0, 5, "span"], helpers, constants), -1)
            expression = source_task_ast(Parser, builder, "v4_mir_lower_expr_expected")
            fallback = expression.body.statements[-1]
            self.assertEqual(type(fallback).__name__, "GiveBack")
            self.assertEqual(fallback.value.func.name, "v4_mir_add_rvalue")
            self.assertEqual(fallback.value.args[2].name, "v4_mir_rvalue_unknown")
            self.assertEqual(fallback.value.args[4].value, "")
            self.assertEqual(fallback.value.args[8].name, "v4_ty_unknown")
            native = source_task_ast(Parser, llvm, "v4_codegen_llvm_native_rvalue_error")
            self.assertEqual(evaluate_source_branch(native, [0, 0, 0], helpers, constants), case["expected"])

    def test_formal_shadow_actual_fixture_protocol_rejects_all_wrong_facts(self):
        source = (gate.ROOT / gate.OWNED_NAMES[0]).read_text()
        expected = "native rvalue not yet supported: Unknown"
        with bootstrap_fixture_types() as (Parser, _):
            task = source_task_ast(Parser, source, "v4_typed_os_contract_run")
            assertion = source_task_ast(Parser, source, "v4_typed_os_contract_assert")
            class Rejected(Exception): pass
            for field, value in ((None, None), ("mode", "admission-reject"), ("identity_count", 1),
                                 ("identity", ""), ("diag_count", 1), ("error", "wrong"), ("module", "published")):
                facts = {"mode":"ordinary-native-reject", "identity":"builtin::system::process_arg",
                         "identity_count":0, "diag_count":0, "error":expected, "module":""}
                if field is not None: facts[field] = value
                said = []
                def panic(label): raise Rejected(label)
                helpers = {
                    "process::arg": lambda index: {1:facts["mode"], 2:"source", 3:"target", 4:expected, 5:facts["identity"]}[index],
                    "fs::read": lambda path: "explicit source metadata",
                    "v4_target_spec_new": lambda target: 0,
                    "v4_lex_text": lambda *args: 0, "v4_parse_stream": lambda *args: 0,
                    "v4_hir_lower_tree": lambda *args: 0, "v4_resolve_lower_hir": lambda *args: 0,
                    "v4_ty_lower_resolve": lambda *args: 0, "v4_mir_lower_ty": lambda *args: 0,
                    "v4_lex_diag_count": lambda *args: 0, "v4_parse_diag_count": lambda *args: 0,
                    "v4_hir_diag_count": lambda *args: 0,
                    "v4_resolve_diag_count": lambda *args: facts["diag_count"],
                    "v4_ty_diag_count": lambda *args: 0, "v4_mir_diag_count": lambda *args: 0,
                    "v4_typed_os_contract_descriptors": lambda *args: facts["identity_count"],
                    "v4_codegen_llvm_lower_owned_mir_with_panic": lambda *args: 0,
                    "v4_codegen_llvm_native_module_error": lambda *args: facts["error"],
                    "v4_codegen_llvm_module_text": lambda *args: facts["module"],
                    "panic": panic, "say": said.append,
                }
                helpers["v4_typed_os_contract_assert"] = lambda condition, label: evaluate_source_branch(assertion, [condition, label], helpers, {})
                with self.subTest(field=field):
                    if field is None:
                        evaluate_source_branch(task, [], helpers, {})
                        self.assertEqual(said, ["typed-os-entry-contract mode=ordinary-native-reject=passed"])
                    else:
                        with self.assertRaises(Rejected) as caught: evaluate_source_branch(task, [], helpers, {})
                        self.assertEqual(said, [])
                        if field == "mode":
                            self.assertEqual(str(caught.exception), "typed-os-entry-contract source rejected before native publication")

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

    def test_actual_fixture_body_braces_are_fresh_bootstrap_typechecked(self):
        source = (gate.ROOT / gate.OWNED_NAMES[0]).read_text()
        declarations = ("%freak_maybe_int = type { i1, i64 }",
                        "%freak_result_word_word = type { i1, i64 }")
        old_source = source
        for text in declarations:
            chunks = '"' + text.split("{", 1)[0] + '{" + " i1, i64 " + "}"'
            self.assertEqual(source.count(chunks), 1)
            old_source = old_source.replace(chunks, '"' + text + '"')
        core = fixture_core_source_root()
        names = [name for name in gate.source_names()
                 if name.startswith("src/compiler/v4/crates/") and name.endswith("/src/lib.fk")]
        self.assertEqual(len(names), 22)
        with bootstrap_fixture_types() as (Parser, TypeChecker):
            programs = [Parser.from_source((core / name).read_text()) for name in names]
            target = "v4_typed_os_contract_run"
            def assembled(text):
                fixture = Parser.from_source(text)
                combined = copy.copy(programs[0]); combined.statements = []
                for program in (*programs, fixture):
                    for node in program.statements:
                        node = copy.copy(node)
                        if type(node).__name__ == "TaskDecl" and node.name != target:
                            node.body = []
                        combined.statements.append(node)
                return combined, next(node for node in fixture.statements
                                      if type(node).__name__ == "TaskDecl" and node.name == target)
            candidate, task = assembled(source)
            previous, _ = assembled(old_source)
            candidate_errors = [d for d in TypeChecker().check(candidate) if d.level == "error"]
            old_errors = [d for d in TypeChecker().check(previous) if d.level == "error"]
            self.assertEqual(candidate_errors, [])
            self.assertEqual(len(old_errors), 2)
            self.assertTrue(all(" i1, i64 " in d.message for d in old_errors))
            def walk(node):
                yield node
                if isinstance(node, (list, tuple)):
                    for child in node: yield from walk(child)
                elif hasattr(node, "__dict__"):
                    for child in vars(node).values(): yield from walk(child)
            def literal(node):
                if type(node).__name__ == "StrLit":
                    self.assertTrue(all(expression is None for _, expression in (node.parts or [])))
                    return node.value
                self.assertEqual(type(node).__name__, "BinOp"); self.assertEqual(node.op, "+")
                return literal(node.left) + literal(node.right)
            decoded = [literal(node.args[0]) for node in walk(task.body)
                       if type(node).__name__ == "MethodCall" and node.method == "contains"
                       and type(node.args[0]).__name__ == "BinOp"]
            self.assertEqual(decoded, list(declarations))
        self.assertFalse(any(name.startswith("v4_typed_os_fixture_types") for name in sys.modules))

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

    def test_native_entry_source_emits_explicit_c_calling_convention(self):
        core = fixture_core_source_root()
        source = (core / "src/compiler/v4/crates/freak_codegen_llvm/src/lib.fk").read_text()
        with bootstrap_fixture_types() as (Parser, _):
            convention = source_task_ast(Parser, source, "v4_codegen_llvm_calling_convention")
            entry = source_task_ast(Parser, source, "v4_codegen_llvm_native_entry")
        for abi in ("", "C", "cdecl", "system"):
            self.assertEqual(evaluate_source_branch(convention, (abi,), {}, {}), "ccc")
        for name in ("argument_parser", "fs_nul_path"):
            needs_process = sum(gate.BRIDGE_COUNTS[name][i] for i in (0, 3)) > 0
            calls = []
            def convention_query(abi):
                calls.append(abi)
                return evaluate_source_branch(convention, (abi,), {}, {})
            emitted = evaluate_source_branch(entry, (7,), {
                "v4_codegen_llvm_find_mir_body": lambda mir, name: 0 if (mir, name) == (7, "main") else -1,
                "v4_codegen_llvm_mir_uses_typed_process": lambda mir: needs_process,
                "v4_mir_body_callable_abi": lambda mir, body: "",
                "v4_codegen_llvm_calling_convention": convention_query,
                "v4_mir_body_callable_return_type": lambda mir, body: 0,
            }, {"v4_ty_never": -1, "v4_ty_void": -2})
            self.assertEqual(calls, [""])
            self.assertIn("%rc = call ccc i64 @freak.user.main()\n", emitted)
            self.assertIn("%rc32 = trunc i64 %rc to i32\n  ret i32 %rc32\n", emitted)
            module = fake_module(name).split("define i32 @main(", 1)[0] + emitted
            gate.validate_module(module, name)

    def test_entry_call_spelling_preserves_exact_count_and_setup_order(self):
        for name in ("argument_parser", "fs_nul_path"):
            implicit = fake_module(name)
            explicit = implicit.replace("call i64 @freak.user.main()", "call ccc i64 @freak.user.main()")
            for module in (implicit, explicit):
                gate.validate_module(module, name)
            call = "%result = call ccc i64 @freak.user.main()"
            mutants = [explicit.replace(call, ""),
                       explicit.replace(call, call + "\n%again = call ccc i64 @freak.user.main()"),
                       explicit.replace("call ccc i64", "call fastcc i64"),
                       explicit.replace("call ccc i64", "call ccc void"),
                       explicit.replace("@freak.user.main()", "@freak.user.main(i64 1)"),
                       explicit.replace(call, "%result = invoke ccc i64 @freak.user.main()")]
            if name == "argument_parser":
                setup = "call void @freak_v4_process_setup_args(i64 %argc.ext, i64 %argv.int)"
                legacy = "call void @freak_llvm_setup_args(i64 %argc.ext, i64 %argv.int)"
                mutants += [explicit.replace(setup + "\n" + call, call + "\n" + setup),
                            explicit.replace(legacy + "\n" + setup, setup + "\n" + legacy)]
            for index, module in enumerate(mutants):
                with self.subTest(program=name, mutant=index), self.assertRaises(RuntimeError):
                    gate.validate_module(module, name)

    def test_unconditional_word_declaration_does_not_admit_legacy_use(self):
        source = (fixture_core_source_root() / "src/compiler/v4/crates/freak_codegen_llvm/src/lib.fk").read_text()
        with bootstrap_fixture_types() as (Parser, _):
            declarations = source_task_ast(Parser, source, "v4_codegen_llvm_word_runtime_declarations")
        emitted = evaluate_source_branch(declarations, (), {}, {})
        prototype = "declare i64 @freak_v4_word_to_int(i64)\n"
        self.assertEqual(emitted.count(prototype), 1)
        self.assertEqual(emitted.count("@freak_v4_word_to_int"), 1)
        for name in ("argument_parser", "fs_nul_path", "fs_discard_scopes"):
            module = emitted + fake_module(name)
            gate.validate_module(module, name)
            mutants = [module + prototype,
                       module.replace(prototype, "declare i32 @freak_v4_word_to_int(i64)\n"),
                       module.replace(prototype, "declare i64 @freak_v4_word_to_int(ptr)\n"),
                       module + "%legacy = call i64 @freak_v4_word_to_int(i64 7)\n",
                       module + "%legacy = call ccc i64 @freak_v4_word_to_int(i64 7)\n",
                       module + "@legacy = global ptr @freak_v4_word_to_int\n",
                       module + "declare i64 @freak_v4_process_arg(i64)\n",
                       module + "declare i64 @freak_fs_read_checked(i64)\n"]
            for index, mutated in enumerate(mutants):
                with self.subTest(program=name, mutant=index), self.assertRaises(RuntimeError):
                    gate.validate_module(mutated, name)

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
            builds = dict.fromkeys(("bootstrap", "runtime", "capability", "module"), 0)
            machine = "arm64" if host == "darwin" else "x86_64"
            with patch.object(gate.sys, "platform", host), patch.object(gate.platform, "machine", return_value=machine):
                target_name = gate.host_target()
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
                    target_flags = [flag for flag in argv if flag.startswith("--target=") or flag in ("--target", "-target")]
                    self.assertEqual(target_flags, [] if bootstrap else ["--target=" + target_name], "native Clang command target must match the generated module exactly once")
                    kind = "bootstrap" if bootstrap else ("runtime" if label.startswith("runtime-") else ("capability" if label.startswith("capability-link-") else "module"))
                    builds[kind] += 1
                    if not bootstrap:
                        for flag in gate.AUDIT_FLAGS: self.assertIn(flag, argv)
                        for flag in gate.SANITIZER_FLAGS: self.assertEqual(flag in argv, sanitize)
                    Path(argv[argv.index("-o")+1]).write_bytes(b"non-executable inert image\n")
                    return subprocess.CompletedProcess(argv, 0, "", "")
                if label == "compiler-version":
                    self.assertEqual((timeout_seconds, memory_limit_mb), (120,512))
                    return subprocess.CompletedProcess(argv, 0, "clang inert metadata\n", "")
                if label == "compiler-target":
                    default_target = "x86_64-pc-windows-msvc" if host == "win32" else "unrelated-clang-default"
                    return subprocess.CompletedProcess(argv, 0, default_target + "\n", "")
                if label.startswith("contract-"):
                    case = next(contracts)
                    self.assertEqual((timeout_seconds,memory_limit_mb), (60,64))
                    self.assertEqual(argv[1:], [case["mode"], str(work / ("contract-"+case["name"]+".fk")), gate.host_target(), case["expected"], case["identity"]])
                    return subprocess.CompletedProcess(argv, 0, "typed-os-entry-contract mode="+case["mode"]+"=passed\n", "")
                if label.startswith("emit-"):
                    name = next(emissions)
                    self.assertEqual((timeout_seconds,memory_limit_mb), (60,64))
                    self.assertEqual(argv[1:], [str(work/(name+".fk")),gate.host_target()])
                    return subprocess.CompletedProcess(argv, 0, gate.PREFIX+"@@LLVM-MODULE-BEGIN\n"+fake_module(name,target_name)+"@@LLVM-MODULE-END\n", "")
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
            with patch.object(gate,"ROOT",original), patch.object(gate.sys,"platform",host), patch.object(gate,"host_target",return_value=target_name), patch.object(gate,"load_checks",return_value=checks), patch.dict(os.environ,previous,clear=True):
                supports = tuple(gate.load_support(frozen,names,role) for role in ("native","compiler","bootstrap"))
                report = {"complete":False,"platform":host,"sanitized":sanitize,"scope":gate.SCOPE,"data_sha256":gate.DATA_SHA,"work":str(work),"compiler_process_contract":{"seconds":60,"memory_mib":64,"live_handles":1024},"source_hashes":gate.source_hashes(),"compiler":{"selected":str(compiler),"path":str(compiler),"sha256":gate.sha(compiler)},"contracts":[],"emissions":[],"programs":[],"controls":[]}
                with gate.sanitizer_environment(supports[0],sanitize), patch("sys.stdout",io.StringIO()):
                    pins=gate.run_gate(compiler,work,frozen,report,supports)
                self.assertEqual(dict(os.environ),previous)
                pins.final_pins(); report["complete"]=True; gate.validate_report(report,sanitize)
                self.assertEqual(len(callbacks),224 if sanitize else (209 if host=="win32" else 215))
                self.assertEqual(builds, {"bootstrap":2,"runtime":21,"capability":3,"module":27})
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

    def test_actual_native_command_dispatch_rejects_historical_default_target(self):
        # Recreate only the two historical command expressions in the actual
        # run_gate body, then dispatch it through the same process-free replay.
        # The original body must fail at its first runtime command even when
        # Clang's Windows default identity differs from the generated GNU target.
        source = DRIVER.read_text(encoding="utf-8")
        current_flags = 'flags = ["--target=" + target_name, f"-O{opt}", "-I" + str(frozen / "freakc/runtime"), *AUDIT_FLAGS]'
        current_link = 'runner.run([str(clang), *flags, str(llvm), *objects, "-o", str(output), *checks.runtime_platform_final_link_args()]'
        self.assertEqual(source.count(current_flags), 1)
        self.assertEqual(source.count(current_link), 1)
        old_source = source.replace(current_flags, current_flags.replace('"--target=" + target_name, ', ''))
        old_source = old_source.replace(current_link, current_link.replace('[str(clang), *flags,', '[str(clang), "--target=" + target_name, *flags,'))
        functions = [node for node in ast.parse(old_source).body if isinstance(node, ast.FunctionDef) and node.name == "run_gate"]
        self.assertEqual(len(functions), 1)
        namespace = {}
        exec(compile(ast.Module(body=functions, type_ignores=[]), str(DRIVER) + ":historical-target-control", "exec"), gate.__dict__, namespace)
        with patch.object(gate, "run_gate", namespace["run_gate"]):
            for host, sanitize in (("win32", False),):
                with self.subTest(host=host, sanitize=sanitize), self.assertRaisesRegex(AssertionError, "native Clang command target must match the generated module exactly once"):
                    self.simulate(host, sanitize)

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
