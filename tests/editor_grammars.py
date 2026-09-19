#!/usr/bin/env python3
"""Exercise Zed's actual checked-in parser and queries using Tree-sitter."""
from pathlib import Path
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
GRAMMAR = ROOT / "editors/zed/freak-lang/grammars/tree-sitter-freak"
LANGUAGE = ROOT / "editors/zed/freak-lang/languages/freak"
SAMPLE = ROOT / "editors/tests/sample.fk"
CLI = ROOT / "editors/node_modules/tree-sitter-cli" / (
    "tree-sitter.exe" if os.name == "nt" else "tree-sitter"
)


def run(*args: str) -> str:
    result = subprocess.run([str(CLI), *args], cwd=GRAMMAR, text=True,
                            capture_output=True, check=True)
    return result.stdout


def main() -> None:
    parsed = run("parse", str(SAMPLE))
    assert "ERROR" not in parsed and "MISSING" not in parsed, parsed
    expected = {
        "highlights": [("keyword", "pilot"), ("function", "greet"),
                       ("type.builtin", "word"), ("number", "42"),
                       ("string", "Hello, "), ("keyword.control", "break"),
                       ("keyword.control", "continue")],
        "outline": [("name", "greet"), ("name", "Point")],
        "brackets": [("open", "{"), ("close", "}")],
        "indents": [("indent", "{"), ("outdent", "}")],
    }
    for name, captures in expected.items():
        result = run("query", str(LANGUAGE / f"{name}.scm"), str(SAMPLE))
        for capture, text in captures:
            assert any(f" - {capture}," in line and f"text: `{text}`" in line
                       for line in result.splitlines()), (name, capture, text, result)
    print("Zed: sample parses without errors; all four queries compile and capture expected syntax")


if __name__ == "__main__":
    main()
