from __future__ import annotations

from freakc.parser import (
    Parser,
    Program,
    PilotDecl,
    SayStmt,
    TaskDecl,
    GiveBack,
    Block,
    IfExpr,
    WhenExpr,
    WhenArm,
    ForEach,
    RepeatTimes,
    RepeatUntil,
    TrainingArc,
    ListLit,
    MapLit,
    TupleLit,
    IntLit,
    StrLit,
    Ident,
    BinOp,
)


def parse(source: str) -> Program:
    return Parser.from_source(source)


def test_pilot_and_say_hello():
    src = '''\
pilot name = "Takeru"
pilot power = 9001
say "Hello from FREAK! {name} has power {power}."
'''
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
    # Expect 1 + (2 * 3)
    assert isinstance(expr, BinOp)
    assert expr.op == "+"
    assert isinstance(expr.left, IntLit) and expr.left.value == 1
    assert isinstance(expr.right, BinOp)
    assert expr.right.op == "*"


def test_if_else_basic():
    src = """\
pilot x = 10
if x > 5 {
    say "big"
} else {
    say "small"
}
"""
    prog = parse(src)
    assert isinstance(prog.statements[1], IfExpr)
    if_stmt = prog.statements[1]
    assert isinstance(if_stmt.condition, BinOp)
    assert if_stmt.elif_branches == []
    assert if_stmt.else_block is not None
    # then_block has one SayStmt
    assert isinstance(if_stmt.then_block, Block)
    assert isinstance(if_stmt.then_block.statements[0], SayStmt)


def test_when_basic():
    src = """\
when x {
    1 -> 10
    _ -> 20
}
"""
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
    src = """\
for each item in my_list {
    say item
}
"""
    prog = parse(src)
    loop = prog.statements[0]
    assert isinstance(loop, ForEach)
    assert isinstance(loop.pattern, Ident)
    assert loop.pattern.name == "item"


def test_repeat_times_and_until():
    src = """\
repeat 5 times {
    say "FREAK!"
}

repeat until condition {
    say "loop"
}
"""
    prog = parse(src)
    rep_times = prog.statements[0]
    assert isinstance(rep_times, RepeatTimes)
    assert isinstance(rep_times.count, IntLit)
    rep_until = prog.statements[1]
    assert isinstance(rep_until, RepeatUntil)


def test_training_arc():
    src = """\
training arc until power >= 9000 max 100 sessions {
    say "train"
}
"""
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
    expr = prog.statements[0]
    assert isinstance(expr, MapLit)
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
    # Ensure grouping works: value should be a BinOp '*', whose left is a BinOp '+'
    assert isinstance(decl2.value, BinOp)
    assert decl2.value.op == "*"


def test_simple_task_block_and_arrow():
    src = '''\
task add(a: num, b: num) -> num {
    give back a + b
}

task square(x: num) => x * x
'''
    prog = parse(src)
    assert len(prog.statements) == 2

    add = prog.statements[0]
    assert isinstance(add, TaskDecl)
    assert add.name == "add"
    assert len(add.params) == 2
    assert add.return_type is not None
    assert add.return_type.name == "num"
    assert isinstance(add.body, Block)
    # Give back inside block
    gb = add.body.statements[0]  # type: ignore[union-attr]
    assert isinstance(gb, GiveBack)
    assert isinstance(gb.value, BinOp)

    square = prog.statements[1]
    assert isinstance(square, TaskDecl)
    assert square.name == "square"
    assert isinstance(square.body, BinOp)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"{name}: OK")

