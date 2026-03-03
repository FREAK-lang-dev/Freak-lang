"""Run all parser tests, reporting pass/fail."""
import sys
sys.path.insert(0, '.')

from freakc.parser import (
    Parser, Program, PilotDecl, SayStmt, TaskDecl, GiveBack, Block,
    IfExpr, WhenExpr, WhenArm, ForEach, RepeatTimes, RepeatUntil,
    TrainingArc, ListLit, MapLit, TupleLit, IntLit, StrLit, Ident, BinOp
)


def parse(source):
    return Parser.from_source(source)


def test_pilot_and_say_hello():
    src = 'pilot name = "Takeru"\npilot power = 9001\nsay "Hello from FREAK! {name} has power {power}."\n'
    prog = parse(src)
    assert len(prog.statements) == 3
    s0 = prog.statements[0]
    assert isinstance(s0, PilotDecl)
    assert s0.name == "name"
    assert isinstance(s0.value, StrLit)
    assert s0.value.value == 'Takeru'
    s1 = prog.statements[1]
    assert isinstance(s1, PilotDecl)
    assert s1.name == "power"
    assert isinstance(s1.value, IntLit)
    assert s1.value.value == 9001
    s2 = prog.statements[2]
    assert isinstance(s2, SayStmt)
    assert isinstance(s2.value, StrLit)


def test_binary_expression_precedence():
    prog = parse("pilot x = 1 + 2 * 3\n")
    s0 = prog.statements[0]
    assert isinstance(s0, PilotDecl)
    expr = s0.value
    assert isinstance(expr, BinOp)
    assert expr.op == "+"
    assert isinstance(expr.left, IntLit) and expr.left.value == 1
    assert isinstance(expr.right, BinOp)
    assert expr.right.op == "*"


def test_if_else_basic():
    src = 'pilot x = 10\nif x > 5 {\n    say "big"\n} else {\n    say "small"\n}\n'
    prog = parse(src)
    assert isinstance(prog.statements[1], IfExpr)
    if_stmt = prog.statements[1]
    assert isinstance(if_stmt.condition, BinOp)
    assert if_stmt.elif_branches == []
    assert if_stmt.else_block is not None
    assert isinstance(if_stmt.then_block, Block)
    assert isinstance(if_stmt.then_block.statements[0], SayStmt)


def test_when_basic():
    src = 'when x {\n    1 -> 10\n    _ -> 20\n}\n'
    prog = parse(src)
    assert isinstance(prog.statements[0], WhenExpr)
    when = prog.statements[0]
    assert len(when.arms) == 2
    arm0 = when.arms[0]
    assert isinstance(arm0.pattern, IntLit) and arm0.pattern.value == 1
    assert isinstance(arm0.body, IntLit) and arm0.body.value == 10
    arm1 = when.arms[1]
    assert isinstance(arm1.pattern, str) and arm1.pattern == "_"


def test_for_each_loop():
    src = 'for each item in my_list {\n    say item\n}\n'
    prog = parse(src)
    loop = prog.statements[0]
    assert isinstance(loop, ForEach)
    assert isinstance(loop.pattern, Ident)
    assert loop.pattern.name == "item"


def test_repeat_times_and_until():
    src = 'repeat 5 times {\n    say "FREAK!"\n}\n\nrepeat until condition {\n    say "loop"\n}\n'
    prog = parse(src)
    rep_times = prog.statements[0]
    assert isinstance(rep_times, RepeatTimes)
    assert isinstance(rep_times.count, IntLit)
    rep_until = prog.statements[1]
    assert isinstance(rep_until, RepeatUntil)


def test_training_arc():
    src = 'training arc until power >= 9000 max 100 sessions {\n    say "train"\n}\n'
    prog = parse(src)
    arc = prog.statements[0]
    assert isinstance(arc, TrainingArc)


def test_list_literal():
    prog = parse("pilot xs = [1, 2, 3]\n")
    decl = prog.statements[0]
    assert isinstance(decl, PilotDecl)
    assert isinstance(decl.value, ListLit)
    assert [e.value for e in decl.value.elements] == [1, 2, 3]


def test_map_literal():
    prog = parse('{ "a": 1, "b": 2 }\n')
    stmt = prog.statements[0]
    # In our updated parser, a bare expression is wrapped in ExprStmt
    from freakc.parser import ExprStmt
    if isinstance(stmt, ExprStmt):
        expr = stmt.expr
    else:
        expr = stmt
    assert isinstance(expr, MapLit), f"Expected MapLit, got {type(expr)}"
    keys = [k.value for k, _ in expr.pairs]
    vals = [v.value for _, v in expr.pairs]
    assert keys == ["a", "b"]
    assert vals == [1, 2]


def test_tuple_literal_vs_grouping():
    prog = parse("pilot t = (1, 2)\n")
    decl = prog.statements[0]
    assert isinstance(decl.value, TupleLit)
    assert [e.value for e in decl.value.elements] == [1, 2]

    prog2 = parse("pilot x = (1 + 2) * 3\n")
    decl2 = prog2.statements[0]
    assert isinstance(decl2.value, BinOp)
    assert decl2.value.op == "*"


def test_simple_task_block_and_arrow():
    src = 'task add(a: num, b: num) -> num {\n    give back a + b\n}\n\ntask square(x: num) => x * x\n'
    prog = parse(src)
    assert len(prog.statements) == 2
    add = prog.statements[0]
    assert isinstance(add, TaskDecl)
    assert add.name == "add"
    assert len(add.params) == 2
    assert add.return_type is not None
    assert add.return_type.name == "num"
    assert isinstance(add.body, Block)
    gb = add.body.statements[0]
    assert isinstance(gb, GiveBack)
    assert isinstance(gb.value, BinOp)
    square = prog.statements[1]
    assert isinstance(square, TaskDecl)
    assert square.name == "square"
    assert isinstance(square.body, BinOp)


# --- Run all tests ---
tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
passed = 0
failed = 0
for fn in tests:
    try:
        fn()
        print(f"  PASS: {fn.__name__}")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {fn.__name__}: {e}")
        failed += 1

print(f"\n{passed} passed, {failed} failed out of {len(tests)} tests")
if failed:
    sys.exit(1)
