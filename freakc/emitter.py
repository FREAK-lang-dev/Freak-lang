from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from .parser import (
    Annotation,
    Assign,
    BinOp,
    Block,
    BoolLit,
    Call,
    CheckMaybe,
    CheckResult,
    DoctrineDecl,
    ErrExpr,
    ExprStmt,
    FieldAccess,
    FloatLit,
    ForEach,
    ForeshadowDecl,
    GiveBack,
    Ident,
    IfExpr,
    ImplBlock,
    Index,
    IntLit,
    Lambda,
    ListLit,
    MapLit,
    MethodCall,
    Nobody,
    OkExpr,
    Param,
    PayoffStmt,
    PilotDecl,
    Program,
    RepeatTimes,
    RepeatUntil,
    SayStmt,
    ShapeDecl,
    ShapeInstantiation,
    SomeExpr,
    StrLit,
    TaskDecl,
    TrainingArc,
    TrustMeBlock,
    TupleLit,
    TypeExpr,
    UnaryOp,
    UseImport,
    WhenExpr,
)


class EmitError(Exception):
    pass


@dataclass
class VarInfo:
    c_type: str


# C reserved words that cannot be used as variable names
_C_RESERVED = {
    "auto", "break", "case", "char", "const", "continue", "default", "do",
    "double", "else", "enum", "extern", "float", "for", "goto", "if",
    "int", "long", "register", "return", "short", "signed", "sizeof",
    "static", "struct", "switch", "typedef", "union", "unsigned", "void",
    "volatile", "while", "inline", "restrict", "bool", "true", "false",
}


def _sanitize_name(name: str) -> str:
    """Escape C reserved words by appending underscore."""
    if name in _C_RESERVED:
        return f"{name}_"
    return name


class CEmitter:
    """
    FREAK Lite → C emitter.

    Emission order (per Bible Section 9):
      1. #include "freak_runtime.h"
      2. typedef struct for shapes
      3. typedef struct for generated types (maybe, result, closure envs)
      4. Forward declarations for all functions
      5. Function definitions
      6. int main() { return freak_main(); }
    """

    def __init__(self) -> None:
        self.indent: int = 0
        self.vars: Dict[str, VarInfo] = {}
        self.shapes: Dict[str, ShapeDecl] = {}
        self.impl_methods: Dict[str, List[TaskDecl]] = {}  # type_name -> methods
        self.func_sigs: Dict[str, str] = {}  # func_name -> return C type
        self._shape_defs: List[str] = []
        self._forward_decls: List[str] = []
        self._func_defs: List[str] = []
        self._main_body: List[str] = []
        self._lambda_counter: int = 0
        self._lambda_defs: List[str] = []  # closure env structs + functions
        self._temp_counter: int = 0
        self._closure_captures: Set[str] = set()  # names accessed as __env->name
        self._includes: Set[str] = set()  # extra #include from use imports

    def emit(self, program: Program) -> str:
        self.indent = 0
        self.vars = {}
        self.shapes = {}
        self.impl_methods = {}
        self.func_sigs = {}
        self._shape_defs = []
        self._forward_decls = []
        self._func_defs = []
        self._main_body = []
        self._lambda_counter = 0
        self._lambda_defs = []
        self._temp_counter = 0
        self._includes = set()

        # Collect shapes and impl blocks first
        top_stmts: list = []
        task_decls: list = []
        for stmt in program.statements:
            if isinstance(stmt, ShapeDecl):
                self.shapes[stmt.name] = stmt
            elif isinstance(stmt, ImplBlock):
                self.impl_methods.setdefault(stmt.target_type, []).extend(stmt.methods)
            elif isinstance(stmt, TaskDecl):
                task_decls.append(stmt)
            elif isinstance(stmt, DoctrineDecl):
                pass  # doctrines don't produce C output directly
            else:
                top_stmts.append(stmt)

        # Emit shapes
        for name, shape in self.shapes.items():
            self._emit_shape_def(shape)

        # Emit forward declarations for all tasks
        for td in task_decls:
            self._forward_decls.append(self._task_forward_decl(td) + ";")

        # Emit impl method forward declarations
        for type_name, methods in self.impl_methods.items():
            for m in methods:
                sig = self._impl_method_signature(type_name, m)
                self._forward_decls.append(sig + ";")

        # Emit task definitions
        for td in task_decls:
            self._emit_task_def(td)

        # Emit impl method definitions
        for type_name, methods in self.impl_methods.items():
            for m in methods:
                self._emit_impl_method_def(type_name, m)

        # Emit freak_main body
        self._main_body.append("int freak_main(void) {")
        self.indent = 1
        for stmt in top_stmts:
            self._emit_statement(stmt, self._main_body)
        self._main_body.append("    return 0;")
        self._main_body.append("}")

        # Assemble final output
        lines: List[str] = []
        lines.append('#include "freak_runtime.h"')
        lines.append("#include <string.h>")
        for inc in sorted(self._includes):
            lines.append(inc)
        lines.append("")

        if self._shape_defs:
            lines.append("/* --- Shape definitions --- */")
            lines.extend(self._shape_defs)
            lines.append("")

        if self._lambda_defs:
            lines.append("/* --- Closure support --- */")
            lines.extend(self._lambda_defs)
            lines.append("")

        if self._forward_decls:
            lines.append("/* --- Forward declarations --- */")
            lines.extend(self._forward_decls)
            lines.append("")

        if self._func_defs:
            lines.append("/* --- Function definitions --- */")
            lines.extend(self._func_defs)
            lines.append("")

        lines.extend(self._main_body)
        lines.append("")
        lines.append("int main(int argc, char** argv) {")
        lines.append("    (void)argc; (void)argv;")
        lines.append("    return freak_main();")
        lines.append("}")
        lines.append("")

        return "\n".join(lines)

    # ===================================================================
    #  Shape Definitions
    # ===================================================================

    def _emit_shape_def(self, shape: ShapeDecl) -> None:
        self._shape_defs.append(f"typedef struct {{")
        for f in shape.fields:
            c_type = self._type_to_c(f.type_ann) if f.type_ann else "int64_t"
            self._shape_defs.append(f"    {c_type} {f.name};")
        self._shape_defs.append(f"}} {shape.name};")
        self._shape_defs.append("")

    # ===================================================================
    #  Task (Function) Definitions
    # ===================================================================

    def _type_to_c(self, te: Optional[TypeExpr]) -> str:
        if te is None:
            return "int64_t"
        mapping = {
            "int": "int64_t",
            "uint": "uint64_t",
            "tiny": "uint8_t",
            "num": "double",
            "float": "double",
            "float32": "float",
            "word": "freak_word",
            "bool": "bool",
            "char": "uint32_t",
            "void": "void",
        }
        if te.is_pointer:
            inner = self._type_to_c(TypeExpr(name=te.name, params=te.params))
            return f"{inner}*"
        if te.name in mapping:
            return mapping[te.name]
        # Could be a shape name or other user-defined type
        if te.name in self.shapes:
            return te.name
        return te.name  # fallback

    def _resolve_task_return_type(self, td: TaskDecl) -> str:
        """Determine C return type: explicit annotation, or infer from arrow body."""
        if td.return_type:
            return self._type_to_c(td.return_type)
        # Arrow form: infer from the expression
        if not isinstance(td.body, Block):
            return self._infer_c_type_of_expr(td.body)
        return "void"

    def _task_forward_decl(self, td: TaskDecl) -> str:
        ret = self._resolve_task_return_type(td)
        # Track the function signature for call-site type inference
        self.func_sigs[td.name] = ret
        params_c = []
        for p in td.params:
            pt = self._type_to_c(p.type_ann) if p.type_ann else "int64_t"
            params_c.append(f"{pt} {p.name}")
        if not params_c:
            params_c = ["void"]
        params_str = ", ".join(params_c)
        prefix = "" if td.is_launch else "static "
        return f"{prefix}{ret} freak_{td.name}({params_str})"

    def _emit_task_def(self, td: TaskDecl) -> None:
        sig = self._task_forward_decl(td)
        self._func_defs.append(f"{sig} {{")

        # Register function parameters in vars so interpolation & type inference works
        saved_vars = dict(self.vars)
        for p in td.params:
            pt = self._type_to_c(p.type_ann) if p.type_ann else "int64_t"
            self.vars[p.name] = VarInfo(c_type=pt)

        if isinstance(td.body, Block):
            saved_indent = self.indent
            self.indent = 1
            for s in td.body.statements:
                self._emit_statement(s, self._func_defs)
            self.indent = saved_indent
        else:
            # Arrow form: single expression
            ret_c = self._expr_to_c(td.body)
            self._func_defs.append(f"    return {ret_c};")

        # Restore vars (exit function scope)
        self.vars = saved_vars
        self._func_defs.append("}")
        self._func_defs.append("")

    def _impl_method_signature(self, type_name: str, td: TaskDecl) -> str:
        ret = self._type_to_c(td.return_type) if td.return_type else "void"
        params_c = []
        for p in td.params:
            if p.name == "self":
                params_c.append(f"{type_name}* self")
            else:
                pt = self._type_to_c(p.type_ann) if p.type_ann else "int64_t"
                params_c.append(f"{pt} {p.name}")
        if not params_c:
            params_c = [f"{type_name}* self"]
        params_str = ", ".join(params_c)
        return f"{ret} {type_name}_{td.name}({params_str})"

    def _emit_impl_method_def(self, type_name: str, td: TaskDecl) -> None:
        sig = self._impl_method_signature(type_name, td)
        self._func_defs.append(f"{sig} {{")

        # Register parameters in vars
        saved_vars = dict(self.vars)
        for p in td.params:
            if p.name == "self":
                self.vars["self"] = VarInfo(c_type=f"{type_name}*")
            else:
                pt = self._type_to_c(p.type_ann) if p.type_ann else "int64_t"
                self.vars[p.name] = VarInfo(c_type=pt)

        if isinstance(td.body, Block):
            saved = self.indent
            self.indent = 1
            for s in td.body.statements:
                self._emit_statement(s, self._func_defs)
            self.indent = saved
        else:
            ret_c = self._expr_to_c(td.body)
            self._func_defs.append(f"    return {ret_c};")

        self.vars = saved_vars
        self._func_defs.append("}")
        self._func_defs.append("")

    # ===================================================================
    #  Statements
    # ===================================================================

    def _ind(self) -> str:
        return "    " * self.indent

    def _emit_statement(self, stmt, target: List[str]) -> None:
        if isinstance(stmt, PilotDecl):
            self._emit_pilot_decl(stmt, target)
        elif isinstance(stmt, SayStmt):
            self._emit_say(stmt, target)
        elif isinstance(stmt, GiveBack):
            self._emit_give_back(stmt, target)
        elif isinstance(stmt, IfExpr):
            self._emit_if(stmt, target)
        elif isinstance(stmt, WhenExpr):
            self._emit_when(stmt, target)
        elif isinstance(stmt, ForEach):
            self._emit_for_each(stmt, target)
        elif isinstance(stmt, RepeatTimes):
            self._emit_repeat_times(stmt, target)
        elif isinstance(stmt, RepeatUntil):
            self._emit_repeat_until(stmt, target)
        elif isinstance(stmt, TrainingArc):
            self._emit_training_arc(stmt, target)
        elif isinstance(stmt, CheckMaybe):
            self._emit_check_maybe(stmt, target)
        elif isinstance(stmt, CheckResult):
            self._emit_check_result(stmt, target)
        elif isinstance(stmt, Annotation):
            self._emit_annotation(stmt, target)
        elif isinstance(stmt, TrustMeBlock):
            self._emit_trust_me(stmt, target)
        elif isinstance(stmt, ForeshadowDecl):
            self._emit_foreshadow(stmt, target)
        elif isinstance(stmt, PayoffStmt):
            self._emit_payoff(stmt, target)
        elif isinstance(stmt, UseImport):
            self._emit_use_import(stmt, target)
        elif isinstance(stmt, Assign):
            self._emit_assign(stmt, target)
        elif isinstance(stmt, ExprStmt):
            c = self._expr_to_c(stmt.expr)
            target.append(f"{self._ind()}{c};")
        else:
            raise EmitError(f"Unsupported statement: {stmt!r}")

    def _emit_pilot_decl(self, decl: PilotDecl, target: List[str]) -> None:
        name = _sanitize_name(decl.name)
        c_type = self._infer_c_type(decl.value, decl.type_ann)
        init = self._expr_to_c(decl.value)
        self.vars[decl.name] = VarInfo(c_type=c_type)
        target.append(f"{self._ind()}{c_type} {name} = {init};")

    def _emit_say(self, stmt: SayStmt, target: List[str]) -> None:
        expr = stmt.value
        if isinstance(expr, StrLit) and expr.parts:
            # Interpolated string
            c_expr = self._emit_interpolated_string(expr)
            target.append(f"{self._ind()}freak_say({c_expr});")
        elif isinstance(expr, StrLit):
            c_expr = f'freak_word_lit("{self._escape_c_string(expr.value)}")'
            target.append(f"{self._ind()}freak_say({c_expr});")
        else:
            c_expr = self._expr_to_c(expr)
            # Determine type to pick conversion
            c_type = self._infer_c_type_of_expr(expr)
            if c_type == "freak_word":
                target.append(f"{self._ind()}freak_say({c_expr});")
            elif c_type == "double":
                target.append(f"{self._ind()}freak_say(freak_word_from_double({c_expr}));")
            elif c_type == "bool":
                target.append(f"{self._ind()}freak_say(freak_word_from_bool({c_expr}));")
            else:
                target.append(f"{self._ind()}freak_say(freak_word_from_int({c_expr}));")

    def _emit_give_back(self, stmt: GiveBack, target: List[str]) -> None:
        if stmt.value is None:
            target.append(f"{self._ind()}return;")
        else:
            c = self._expr_to_c(stmt.value)
            target.append(f"{self._ind()}return {c};")

    def _emit_if(self, stmt: IfExpr, target: List[str]) -> None:
        cond = self._expr_to_c(stmt.condition)
        target.append(f"{self._ind()}if ({cond}) {{")
        self.indent += 1
        for s in stmt.then_block.statements:
            self._emit_statement(s, target)
        self.indent -= 1

        for elif_cond, elif_block in stmt.elif_branches:
            ec = self._expr_to_c(elif_cond)
            target.append(f"{self._ind()}}} else if ({ec}) {{")
            self.indent += 1
            for s in elif_block.statements:
                self._emit_statement(s, target)
            self.indent -= 1

        if stmt.else_block:
            target.append(f"{self._ind()}}} else {{")
            self.indent += 1
            for s in stmt.else_block.statements:
                self._emit_statement(s, target)
            self.indent -= 1

        target.append(f"{self._ind()}}}")

    def _emit_when(self, stmt: WhenExpr, target: List[str]) -> None:
        subject_c = self._expr_to_c(stmt.subject)
        subject_type = self._infer_c_type_of_expr(stmt.subject)

        if subject_type == "freak_word":
            # Use strcmp chain for word matching
            first = True
            for arm in stmt.arms:
                if isinstance(arm.pattern, str) and arm.pattern == "_":
                    target.append(f"{self._ind()}}} else {{")
                else:
                    pattern_c = self._expr_to_c(arm.pattern)
                    if first:
                        target.append(f"{self._ind()}if (freak_word_eq({subject_c}, {pattern_c})) {{")
                        first = False
                    else:
                        target.append(f"{self._ind()}}} else if (freak_word_eq({subject_c}, {pattern_c})) {{")
                self.indent += 1
                if isinstance(arm.body, Block):
                    for s in arm.body.statements:
                        self._emit_statement(s, target)
                else:
                    c = self._expr_to_c(arm.body)
                    target.append(f"{self._ind()}{c};")
                self.indent -= 1
            target.append(f"{self._ind()}}}")
        else:
            # Use switch for numeric types
            target.append(f"{self._ind()}switch ({subject_c}) {{")
            self.indent += 1
            for arm in stmt.arms:
                if isinstance(arm.pattern, str) and arm.pattern == "_":
                    target.append(f"{self._ind()}default: {{")
                else:
                    pattern_c = self._expr_to_c(arm.pattern)
                    target.append(f"{self._ind()}case {pattern_c}: {{")
                self.indent += 1
                if isinstance(arm.body, Block):
                    for s in arm.body.statements:
                        self._emit_statement(s, target)
                else:
                    c = self._expr_to_c(arm.body)
                    target.append(f"{self._ind()}{c};")
                target.append(f"{self._ind()}break;")
                self.indent -= 1
                target.append(f"{self._ind()}}}")
            self.indent -= 1
            target.append(f"{self._ind()}}}")

    def _emit_for_each(self, stmt: ForEach, target: List[str]) -> None:
        # for each item in iterable → C for loop
        iterable_c = self._expr_to_c(stmt.iterable)
        idx = self._next_temp("__i")
        if isinstance(stmt.pattern, Ident):
            var_name = stmt.pattern.name
        else:
            var_name = "__item"
        target.append(
            f"{self._ind()}for (size_t {idx} = 0; {idx} < {iterable_c}.length; {idx}++) {{"
        )
        self.indent += 1
        target.append(
            f"{self._ind()}int64_t {var_name} = {iterable_c}.data[{idx}];"
        )
        for s in stmt.body.statements:
            self._emit_statement(s, target)
        self.indent -= 1
        target.append(f"{self._ind()}}}")

    def _emit_repeat_times(self, stmt: RepeatTimes, target: List[str]) -> None:
        count_c = self._expr_to_c(stmt.count)
        idx = self._next_temp("__rep")
        target.append(
            f"{self._ind()}for (int64_t {idx} = 0; {idx} < {count_c}; {idx}++) {{"
        )
        self.indent += 1
        for s in stmt.body.statements:
            self._emit_statement(s, target)
        self.indent -= 1
        target.append(f"{self._ind()}}}")

    def _emit_repeat_until(self, stmt: RepeatUntil, target: List[str]) -> None:
        cond_c = self._expr_to_c(stmt.condition)
        target.append(f"{self._ind()}while (!({cond_c})) {{")
        self.indent += 1
        for s in stmt.body.statements:
            self._emit_statement(s, target)
        self.indent -= 1
        target.append(f"{self._ind()}}}")

    def _emit_training_arc(self, stmt: TrainingArc, target: List[str]) -> None:
        cond_c = self._expr_to_c(stmt.condition)
        max_c = self._expr_to_c(stmt.max_sessions)
        arc_var = self._next_temp("__arc")
        target.append(f"{self._ind()}int64_t {arc_var} = 0;")
        target.append(
            f"{self._ind()}while (!({cond_c}) && {arc_var} < {max_c}) {{"
        )
        self.indent += 1
        for s in stmt.body.statements:
            self._emit_statement(s, target)
        target.append(f"{self._ind()}{arc_var}++;")
        self.indent -= 1
        target.append(f"{self._ind()}}}")

    def _emit_assign(self, stmt: Assign, target: List[str]) -> None:
        lhs = self._expr_to_c(stmt.target)
        rhs = self._expr_to_c(stmt.value)
        target.append(f"{self._ind()}{lhs} {stmt.op} {rhs};")

    def _emit_check_maybe(self, stmt: CheckMaybe, target: List[str]) -> None:
        """check expr { got x -> ... nobody -> ... } → if (subj.has_value)"""
        subject_c = self._expr_to_c(stmt.subject)
        tmp = self._next_temp("__maybe")
        target.append(f"{self._ind()}/* check maybe */")
        target.append(f"{self._ind()}if ({subject_c}.has_value) {{")
        self.indent += 1
        # Declare the got variable
        target.append(f"{self._ind()}int64_t {stmt.got_name} = {subject_c}.value;")
        saved_vars = dict(self.vars)
        self.vars[stmt.got_name] = VarInfo(c_type="int64_t")
        for s in stmt.got_body.statements:
            self._emit_statement(s, target)
        self.vars = saved_vars
        self.indent -= 1
        target.append(f"{self._ind()}}} else {{")
        self.indent += 1
        for s in stmt.nobody_body.statements:
            self._emit_statement(s, target)
        self.indent -= 1
        target.append(f"{self._ind()}}}")

    def _emit_check_result(self, stmt: CheckResult, target: List[str]) -> None:
        """check result expr { ok(x) -> ... err(e) -> ... } → if (subj.is_ok)"""
        subject_c = self._expr_to_c(stmt.subject)
        target.append(f"{self._ind()}/* check result */")
        target.append(f"{self._ind()}if ({subject_c}.is_ok) {{")
        self.indent += 1
        target.append(f"{self._ind()}int64_t {stmt.ok_name} = {subject_c}.data.ok_val;")
        saved_vars = dict(self.vars)
        self.vars[stmt.ok_name] = VarInfo(c_type="int64_t")
        for s in stmt.ok_body.statements:
            self._emit_statement(s, target)
        self.vars = saved_vars
        self.indent -= 1
        target.append(f"{self._ind()}}} else {{")
        self.indent += 1
        target.append(f"{self._ind()}freak_word {stmt.err_name} = {subject_c}.data.err_val;")
        saved_vars = dict(self.vars)
        self.vars[stmt.err_name] = VarInfo(c_type="freak_word")
        for s in stmt.err_body.statements:
            self._emit_statement(s, target)
        self.vars = saved_vars
        self.indent -= 1
        target.append(f"{self._ind()}}}")

    def _emit_annotation(self, stmt: Annotation, target: List[str]) -> None:
        """@name declaration → C comment + emit the decorated declaration."""
        target.append(f"{self._ind()}/* @{stmt.name} */")
        if stmt.target:
            self._emit_statement(stmt.target, target)

    def _emit_trust_me(self, stmt: TrustMeBlock, target: List[str]) -> None:
        """trust me block → plain C block with comment."""
        reason = self._escape_c_string(stmt.reason) if stmt.reason else "unsafe"
        target.append(f"{self._ind()}/* trust me: \"{reason}\" (honor: .{stmt.honor_level}) */")
        target.append(f"{self._ind()}{{")
        self.indent += 1
        for s in stmt.body.statements:
            self._emit_statement(s, target)
        self.indent -= 1
        target.append(f"{self._ind()}}}")

    def _emit_foreshadow(self, stmt: ForeshadowDecl, target: List[str]) -> None:
        """foreshadow pilot x = expr → pilot decl + tracking comment."""
        target.append(f"{self._ind()}/* foreshadow: {stmt.decl.name} */")
        self._emit_pilot_decl(stmt.decl, target)

    def _emit_payoff(self, stmt: PayoffStmt, target: List[str]) -> None:
        """payoff x → comment marking fulfillment."""
        target.append(f"{self._ind()}/* payoff: {stmt.name} */")

    def _emit_use_import(self, stmt: UseImport, target: List[str]) -> None:
        """use module::{names} → #include + comment."""
        names_str = ", ".join(stmt.names)
        if stmt.alias:
            target.append(f"{self._ind()}/* use {stmt.module}::{names_str} as {stmt.alias} */")
        else:
            target.append(f"{self._ind()}/* use {stmt.module}::{{{names_str}}} */")
        # In FREAK Lite, emit an #include for the module's generated C header
        self._includes.add(f'#include "{stmt.module}.h"')

    # ===================================================================
    #  Expressions → C
    # ===================================================================

    def _expr_to_c(self, expr) -> str:
        if isinstance(expr, IntLit):
            return f"((int64_t){expr.value})"
        if isinstance(expr, FloatLit):
            return repr(expr.value)
        if isinstance(expr, BoolLit):
            return "true" if expr.value else "false"
        if isinstance(expr, Ident):
            name = _sanitize_name(expr.name)
            # If inside a closure body, captured vars use __env->name
            if expr.name in self._closure_captures:
                return f"__env->{name}"
            return name
        if isinstance(expr, StrLit):
            if expr.parts:
                return self._emit_interpolated_string(expr)
            return f'freak_word_lit("{self._escape_c_string(expr.value)}")'
        if isinstance(expr, Nobody):
            return "/* nobody */ { .has_value = false }"
        if isinstance(expr, BinOp):
            return self._emit_binop(expr)
        if isinstance(expr, UnaryOp):
            return self._emit_unaryop(expr)
        if isinstance(expr, Call):
            return self._emit_call(expr)
        if isinstance(expr, MethodCall):
            return self._emit_method_call(expr)
        if isinstance(expr, FieldAccess):
            return self._emit_field_access(expr)
        if isinstance(expr, Index):
            obj_c = self._expr_to_c(expr.obj)
            idx_c = self._expr_to_c(expr.index)
            return f"{obj_c}.data[{idx_c}]"
        if isinstance(expr, ShapeInstantiation):
            return self._emit_shape_instantiation(expr)
        if isinstance(expr, ListLit):
            # For now, emit as C compound literal (basic)
            return self._emit_list_lit(expr)
        if isinstance(expr, TupleLit):
            # Emit as a struct literal
            parts = ", ".join(self._expr_to_c(e) for e in expr.elements)
            return f"{{ {parts} }}"
        if isinstance(expr, MapLit):
            # Maps are complex; emit a TODO comment for now
            return "/* MAP_LIT_TODO */ 0"
        if isinstance(expr, SomeExpr):
            val_c = self._expr_to_c(expr.value)
            return f"{{ .has_value = true, .value = {val_c} }}"
        if isinstance(expr, OkExpr):
            val_c = self._expr_to_c(expr.value)
            return f"{{ .is_ok = true, .data.ok_val = {val_c} }}"
        if isinstance(expr, ErrExpr):
            val_c = self._expr_to_c(expr.value)
            return f"{{ .is_ok = false, .data.err_val = {val_c} }}"
        if isinstance(expr, Lambda):
            return self._emit_lambda(expr)
        raise EmitError(f"Unsupported expression: {expr!r}")

    def _emit_binop(self, expr: BinOp) -> str:
        left = self._expr_to_c(expr.left)
        right = self._expr_to_c(expr.right)

        # Anime operators
        if expr.op == "PLUS ULTRA":
            return f"({left} * (1.0 + {right} * {right}))"
        if expr.op == "NAKAMA":
            return f"({left} + {right} + ({left} * {right} * 0.1))"

        # Pipe operator: desugar a |> f to f(a)
        if expr.op == "|>":
            # right should be a Call or Ident
            if isinstance(expr.right, Call):
                # Insert left as first argument
                args = [self._expr_to_c(expr.left)] + [self._expr_to_c(a) for a in expr.right.args]
                func = self._expr_to_c(expr.right.func)
                return f"{func}({', '.join(args)})"
            else:
                return f"{right}({left})"

        # or else: fallback for maybe/result
        if expr.op == "or else":
            return f"({left}.has_value ? {left}.value : {right})"

        # Logical operators
        if expr.op == "and":
            return f"({left} && {right})"
        if expr.op == "or":
            return f"({left} || {right})"

        # Power operator
        if expr.op == "**":
            return f"freak_pow_int({left}, {right})"

        # Standard C operators
        op_map = {
            "+": "+", "-": "-", "*": "*", "/": "/", "%": "%",
            "==": "==", "!=": "!=", "<": "<", ">": ">",
            "<=": "<=", ">=": ">=",
        }
        c_op = op_map.get(expr.op, expr.op)
        return f"({left} {c_op} {right})"

    def _emit_unaryop(self, expr: UnaryOp) -> str:
        operand = self._expr_to_c(expr.operand)
        if expr.op == "not" or expr.op == "!":
            return f"(!{operand})"
        if expr.op == "-":
            return f"(-{operand})"
        if expr.op == "FINAL FORM":
            return f"({operand} * {operand})"
        if expr.op == "PLUS ULTRA":
            return f"((double){operand} * 2.0)"
        if expr.op == "TSUNDERE":
            return f"(-({operand}))"
        if expr.op == "?":
            # ? error propagation — emit inline check
            return f"{operand}"
        return f"({expr.op}{operand})"

    def _emit_call(self, expr: Call) -> str:
        args_c = ", ".join(self._expr_to_c(a) for a in expr.args)
        if isinstance(expr.func, Ident):
            # Built-in functions
            if expr.func.name == "panic":
                return f"freak_panic({args_c})"
            if expr.func.name == "ask":
                return f"freak_ask({args_c})"
            # User function — add freak_ prefix
            return f"freak_{expr.func.name}({args_c})"
        func_c = self._expr_to_c(expr.func)
        return f"{func_c}({args_c})"

    def _emit_method_call(self, expr: MethodCall) -> str:
        obj_c = self._expr_to_c(expr.obj)
        args_c = ", ".join(self._expr_to_c(a) for a in expr.args)

        # Check if this is a method on a known shape
        obj_type = self._infer_c_type_of_expr(expr.obj)
        if obj_type in self.shapes:
            # Call as TypeName_method(&obj, args)
            if args_c:
                return f"{obj_type}_{expr.method}(&{obj_c}, {args_c})"
            return f"{obj_type}_{expr.method}(&{obj_c})"

        # Built-in word methods → freak_word_* functions
        WORD_METHODS = {
            "length":      ("freak_word_length",      0, False),  # (c_func, extra_args, pass_obj_as_ref)
            "to_upper":    ("freak_word_to_upper",    0, False),
            "to_lower":    ("freak_word_to_lower",    0, False),
            "contains":    ("freak_word_contains",    1, False),
            "starts_with": ("freak_word_starts_with", 1, False),
            "ends_with":   ("freak_word_ends_with",   1, False),
            "trim":        ("freak_word_trim",        0, False),
            "replace":     ("freak_word_replace",     2, False),
            "char_at":     ("freak_word_char_at",     1, False),
            "to_int":      ("freak_word_to_int",      0, False),
            "to_num":      ("freak_word_to_num",      0, False),
            "to_word":     ("freak_word_from_int",    0, False),  # on int, not word
        }
        if expr.method in WORD_METHODS:
            c_func, _, _ = WORD_METHODS[expr.method]
            if args_c:
                return f"{c_func}({obj_c}, {args_c})"
            return f"{c_func}({obj_c})"

        # Generic method call: try type_method pattern
        if args_c:
            return f"{obj_type}_{expr.method}(&{obj_c}, {args_c})"
        return f"{obj_type}_{expr.method}(&{obj_c})"

    def _emit_field_access(self, expr: FieldAccess) -> str:
        obj_c = self._expr_to_c(expr.obj)
        # Determine if object is a pointer type (use -> instead of .)
        obj_type = self._infer_c_type_of_expr(expr.obj)
        if obj_type.endswith('*'):
            accessor = '->'
        else:
            accessor = '.'
        # Check for built-in properties
        if expr.field == "length":
            return f"{obj_c}{accessor}length"
        return f"{obj_c}{accessor}{expr.field}"

    def _emit_shape_instantiation(self, expr: ShapeInstantiation) -> str:
        fields_c = ", ".join(
            f".{fname} = {self._expr_to_c(fval)}" for fname, fval in expr.fields
        )
        return f"({expr.shape_name}){{ {fields_c} }}"

    def _emit_list_lit(self, expr: ListLit) -> str:
        # For now, emit as a basic compound literal with known size
        # A proper implementation would use freak_list_T_new() + push
        if not expr.elements:
            return "{ .data = NULL, .length = 0, .capacity = 0 }"
        # Emit helper: create a static array and wrap
        elements_c = ", ".join(self._expr_to_c(e) for e in expr.elements)
        return f"/* list_literal */ {{ {elements_c} }}"

    def _emit_lambda(self, expr: Lambda) -> str:
        """Generate closure: env struct + static function + freak_closure literal."""
        idx = self._lambda_counter
        self._lambda_counter += 1

        env_name = f"__closure_env_{idx}"
        fn_name = f"__closure_fn_{idx}"

        # Determine captured variables: variables referenced in the body
        # that exist in the current scope (self.vars) but are NOT parameters
        param_names = {p.name for p in expr.params}
        body_refs = self._collect_idents(expr.body)
        captured = []
        for name in body_refs:
            if name not in param_names and name in self.vars:
                captured.append((name, self.vars[name].c_type))

        # --- Generate env struct ---
        if captured:
            self._lambda_defs.append(f"typedef struct {{")
            for cname, ctype in captured:
                self._lambda_defs.append(f"    {ctype} {cname};")
            self._lambda_defs.append(f"}} {env_name};")
            self._lambda_defs.append("")

        # --- Determine return type ---
        if isinstance(expr.body, Block):
            ret_type = "void"
        else:
            ret_type = self._infer_c_type_of_expr(expr.body)

        # --- Generate static function ---
        params_c = []
        if captured:
            params_c.append(f"{env_name}* __env")
        for p in expr.params:
            pt = self._type_to_c(p.type_ann) if p.type_ann else "int64_t"
            params_c.append(f"{pt} {p.name}")
        if not params_c:
            params_c = ["void"]
        params_str = ", ".join(params_c)

        self._lambda_defs.append(f"static {ret_type} {fn_name}({params_str}) {{")

        # Set up vars for body emission — params + captured vars via __env->
        saved_vars = dict(self.vars)
        for p in expr.params:
            pt = self._type_to_c(p.type_ann) if p.type_ann else "int64_t"
            self.vars[p.name] = VarInfo(c_type=pt)
        # Captured vars are accessed as __env->name, but for interpolation
        # they need to be in self.vars with correct type
        for cname, ctype in captured:
            self.vars[cname] = VarInfo(c_type=ctype)

        saved_indent = self.indent
        self.indent = 1

        # Track captured vars so Ident emits __env->name
        saved_captures = self._closure_captures
        self._closure_captures = {cname for cname, _ in captured}

        if isinstance(expr.body, Block):
            for s in expr.body.statements:
                self._emit_statement(s, self._lambda_defs)
        else:
            ret_c = self._expr_to_c(expr.body)
            self._lambda_defs.append(f"    return {ret_c};")

        self.indent = saved_indent
        self.vars = saved_vars
        self._closure_captures = saved_captures

        self._lambda_defs.append("}")
        self._lambda_defs.append("")

        # --- Return closure literal ---
        if captured:
            # Stack-allocate env and fill with current values
            # (For 'copy' capture this is correct; 'move' would need ownership transfer)
            init_parts = ", ".join(f".{cname} = {cname}" for cname, _ in captured)
            env_var = f"__env_{idx}"
            # We need this declaration in the calling scope, which is tricky.
            # Instead, use a compound literal for the env.
            return f"(freak_closure){{ .fn = (void*){fn_name}, .env = &({env_name}){{ {init_parts} }} }}"
        else:
            return f"(freak_closure){{ .fn = (void*){fn_name}, .env = NULL }}"

    def _collect_idents(self, node) -> set:
        """Recursively collect all Ident names referenced in an AST node."""
        result = set()
        if isinstance(node, Ident):
            result.add(node.name)
        elif isinstance(node, Block):
            for s in node.statements:
                result |= self._collect_idents(s)
        elif isinstance(node, BinOp):
            result |= self._collect_idents(node.left)
            result |= self._collect_idents(node.right)
        elif isinstance(node, UnaryOp):
            result |= self._collect_idents(node.operand)
        elif isinstance(node, Call):
            result |= self._collect_idents(node.func)
            for a in node.args:
                result |= self._collect_idents(a)
        elif isinstance(node, MethodCall):
            result |= self._collect_idents(node.obj)
            for a in node.args:
                result |= self._collect_idents(a)
        elif isinstance(node, FieldAccess):
            result |= self._collect_idents(node.obj)
        elif isinstance(node, Index):
            result |= self._collect_idents(node.obj)
            result |= self._collect_idents(node.index)
        elif isinstance(node, SayStmt):
            result |= self._collect_idents(node.value)
        elif isinstance(node, PilotDecl):
            result |= self._collect_idents(node.value)
        elif isinstance(node, GiveBack):
            if node.value:
                result |= self._collect_idents(node.value)
        elif isinstance(node, Assign):
            result |= self._collect_idents(node.target)
            result |= self._collect_idents(node.value)
        elif isinstance(node, IfExpr):
            result |= self._collect_idents(node.condition)
            result |= self._collect_idents(node.then_block)
            for cond, blk in node.elif_branches:
                result |= self._collect_idents(cond)
                result |= self._collect_idents(blk)
            if node.else_block:
                result |= self._collect_idents(node.else_block)
        elif isinstance(node, ExprStmt):
            result |= self._collect_idents(node.expr)
        elif isinstance(node, StrLit):
            if node.parts:
                for _, interp in node.parts:
                    if interp:
                        result |= self._collect_idents(interp)
        return result

    # ===================================================================
    #  String Interpolation
    # ===================================================================

    def _emit_interpolated_string(self, expr: StrLit) -> str:
        """Emit freak_interpolate() for a string with {var} interpolations."""
        if not expr.parts:
            return f'freak_word_lit("{self._escape_c_string(expr.value)}")'

        fmt_parts: List[str] = []
        args: List[str] = []

        for text, interp_expr in expr.parts:
            escaped = self._escape_c_string(text)
            if interp_expr is None:
                fmt_parts.append(escaped)
            else:
                # Determine format specifier from variable type
                if isinstance(interp_expr, Ident):
                    var_name = interp_expr.name
                    var_info = self.vars.get(var_name)
                    if var_info:
                        if var_info.c_type == "freak_word":
                            fmt_parts.append(f"{escaped}%s")
                            args.append(f"freak_word_to_cstr({var_name})")
                        elif var_info.c_type == "double":
                            fmt_parts.append(f"{escaped}%g")
                            args.append(var_name)
                        elif var_info.c_type == "bool":
                            fmt_parts.append(f"{escaped}%s")
                            args.append(f'({var_name} ? "true" : "false")')
                        else:
                            fmt_parts.append(f"{escaped}%lld")
                            args.append(f"(long long){var_name}")
                    else:
                        # Unknown variable — assume int
                        fmt_parts.append(f"{escaped}%lld")
                        args.append(f"(long long){var_name}")
                else:
                    # Use type inference for format specifier
                    c_expr = self._expr_to_c(interp_expr)
                    c_type = self._infer_c_type_of_expr(interp_expr)
                    if c_type == "freak_word":
                        fmt_parts.append(f"{escaped}%s")
                        args.append(f"freak_word_to_cstr({c_expr})")
                    elif c_type == "double":
                        fmt_parts.append(f"{escaped}%g")
                        args.append(c_expr)
                    elif c_type == "bool":
                        fmt_parts.append(f"{escaped}%s")
                        args.append(f'({c_expr} ? "true" : "false")')
                    else:
                        fmt_parts.append(f"{escaped}%lld")
                        args.append(f"(long long)({c_expr})")

        fmt_str = "".join(fmt_parts)
        if args:
            args_str = ", ".join(args)
            return f'freak_interpolate("{fmt_str}", {args_str})'
        else:
            return f'freak_word_lit("{fmt_str}")'

    # ===================================================================
    #  Type Inference Helpers
    # ===================================================================

    def _infer_c_type(self, expr, type_ann: Optional[TypeExpr] = None) -> str:
        """Infer the C type for a variable initializer."""
        if type_ann:
            return self._type_to_c(type_ann)
        return self._infer_c_type_of_expr(expr)

    def _infer_c_type_of_expr(self, expr) -> str:
        """Best-effort inference of C type for an expression."""
        if isinstance(expr, IntLit):
            return "int64_t"
        if isinstance(expr, FloatLit):
            return "double"
        if isinstance(expr, BoolLit):
            return "bool"
        if isinstance(expr, StrLit):
            return "freak_word"
        if isinstance(expr, Ident):
            info = self.vars.get(expr.name)
            return info.c_type if info else "int64_t"
        if isinstance(expr, BinOp):
            lt = self._infer_c_type_of_expr(expr.left)
            rt = self._infer_c_type_of_expr(expr.right)
            if lt == "double" or rt == "double":
                return "double"
            if lt == "freak_word" or rt == "freak_word":
                return "freak_word"
            if lt == "bool" and rt == "bool":
                return "bool"
            return "int64_t"
        if isinstance(expr, UnaryOp):
            if expr.op == "not" or expr.op == "!":
                return "bool"
            return self._infer_c_type_of_expr(expr.operand)
        if isinstance(expr, Call):
            if isinstance(expr.func, Ident):
                if expr.func.name == "ask":
                    return "freak_word"
                # Look up known function signatures
                ret = self.func_sigs.get(expr.func.name)
                if ret:
                    return ret
            return "int64_t"
        if isinstance(expr, FieldAccess):
            # Look up the field type from the shape definition
            obj_type = self._infer_c_type_of_expr(expr.obj)
            # Strip pointer suffix for self references in impl methods
            base_type = obj_type.rstrip("*").strip()
            if base_type in self.shapes:
                shape = self.shapes[base_type]
                for f in shape.fields:
                    if f.name == expr.field and f.type_ann:
                        return self._type_to_c(f.type_ann)
            return "int64_t"  # conservative fallback
        if isinstance(expr, ShapeInstantiation):
            return expr.shape_name
        if isinstance(expr, Lambda):
            return "freak_closure"
        if isinstance(expr, SomeExpr):
            return "freak_maybe_int"  # default; proper generics would refine this
        if isinstance(expr, Nobody):
            return "freak_maybe_int"
        if isinstance(expr, MethodCall):
            # Return types for built-in word methods
            METHOD_RETURN_TYPES = {
                "length": "int64_t", "to_int": "int64_t",
                "to_num": "double",
                "to_upper": "freak_word", "to_lower": "freak_word",
                "trim": "freak_word", "replace": "freak_word",
                "char_at": "freak_word", "to_word": "freak_word",
                "contains": "bool", "starts_with": "bool",
                "ends_with": "bool",
            }
            if expr.method in METHOD_RETURN_TYPES:
                return METHOD_RETURN_TYPES[expr.method]
            # For shape methods, look up func_sigs
            obj_type = self._infer_c_type_of_expr(expr.obj)
            sig_key = f"{obj_type}.{expr.method}"
            if sig_key in self.func_sigs:
                return self.func_sigs[sig_key]
            return "int64_t"
        return "int64_t"

    # ===================================================================
    #  Helpers
    # ===================================================================

    def _escape_c_string(self, s: str) -> str:
        return (
            s.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("\t", "\\t")
        )

    def _next_temp(self, prefix: str = "__tmp") -> str:
        self._temp_counter += 1
        return f"{prefix}_{self._temp_counter}"


__all__ = ["CEmitter", "EmitError"]
