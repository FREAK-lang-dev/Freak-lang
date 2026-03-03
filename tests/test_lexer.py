from __future__ import annotations

from freakc.lexer import Lexer, TokenType


def toks(source: str):
    return [t for t in Lexer(source).tokenize() if t.type is not TokenType.EOF]


def test_basic_pilot_and_say():
    ts = toks('pilot x = 42 and say "Hello, {x}!"')
    assert [t.type for t in ts[:7]] == [
        TokenType.PILOT,
        TokenType.IDENT,
        TokenType.EQ,
        TokenType.INT_LIT,
        TokenType.AND,
        TokenType.SAY,
        TokenType.STRING_LIT,
    ]


def test_comments_and_newlines():
    ts = toks("pilot x = 1 -- comment\npilot y = 2\n")
    types = [t.type for t in ts]
    assert types.count(TokenType.NEWLINE) == 2
    assert types[0] == TokenType.PILOT
    # Last real token before final newline is INT_LIT
    assert types[-2] == TokenType.INT_LIT


def test_int_hex_bin_and_suffixes():
    ts = toks("0xFF 0b1010 42u")
    assert [t.type for t in ts] == [TokenType.INT_LIT, TokenType.INT_LIT, TokenType.INT_LIT]
    assert ts[0].value == int("0xFF", 16)
    assert ts[1].value == int("0b1010", 2)
    assert ts[2].value == 42


def test_float_and_suffix():
    ts = toks("3.14 3.14f")
    assert [t.type for t in ts] == [TokenType.FLOAT_LIT, TokenType.FLOAT_LIT]
    assert ts[0].value == 3.14
    assert ts[1].value == 3.14


def test_bool_keywords():
    ts = toks("true false yes no hai iie")
    assert all(t.type == TokenType.BOOL_LIT for t in ts)
    vals = [t.value for t in ts]
    assert vals == [True, False, True, False, True, False]


def test_semicolons_skipped():
    ts = toks("42; 7")
    assert [t.type for t in ts] == [TokenType.INT_LIT, TokenType.INT_LIT]


def test_multiword_keywords():
    src = """
    give back
    or else
    trust me
    training arc
    on my honor as
    knowing this will hurt
    for science
    PLUS ULTRA
    FINAL FORM
    """
    types = [t.type for t in toks(src) if t.type is not TokenType.NEWLINE]
    expected = [
        TokenType.GIVE_BACK,
        TokenType.OR_ELSE,
        TokenType.TRUST_ME,
        TokenType.TRAINING_ARC,
        TokenType.ON_MY_HONOR,
        TokenType.KNOWING,
        TokenType.FOR_SCIENCE,
        TokenType.PLUS_ULTRA,
        TokenType.FINAL_FORM,
    ]
    assert types == expected


def test_done_keyword():
    ts = toks("done")
    assert len(ts) == 1
    assert ts[0].type == TokenType.DONE


if __name__ == "__main__":
    # Simple ad-hoc runner
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"{name}: OK")

