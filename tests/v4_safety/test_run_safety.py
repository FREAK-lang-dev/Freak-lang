"""Compiler-free tests for the V4 safety runner: case parsing and judging."""
from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_safety as rs  # noqa: E402


def write_case(directory: Path, name: str, text: str) -> Path:
    path = directory / f"{name}.fk"
    path.write_text(text, encoding="utf-8")
    return path


class FakeRunner(rs.Runner):
    """Returns canned compiler output instead of running the V4 compiler."""

    def __init__(self, stdout: str, run_result=None):
        super().__init__(Path("unused"), "clang", "x86_64-unknown-linux-gnu")
        self.stdout = stdout
        self.run_result = run_result

    def compile(self, case):
        return rs.parse_compiler_output(self.stdout)

    def execute(self, case, module):
        return self.run_result


CLEAN = "".join(f"v4-build-stage={s} diagnostics=0\n" for s in rs.FRONTEND_STAGES) + \
    "v4-build-stage=codegen diagnostics=0\nv4-errors=0\n@@V4-MODULE\ntarget triple = \"x\"\n"
BORROWCK_ERROR = "".join(f"v4-build-stage={s} diagnostics=0\n" for s in rs.FRONTEND_STAGES[:-1]) + \
    "v4-build-stage=borrowck diagnostics=1\n" \
    "2|0@6:9|Meiya refuses this rewrite while the value is borrowed|a stays on loan\n" \
    "v4-errors=1\nv4-aborted-after=borrowck\n"
CODEGEN_ERROR = "".join(f"v4-build-stage={s} diagnostics=0\n" for s in rs.FRONTEND_STAGES) + \
    "v4-build-stage=codegen diagnostics=0\n" \
    "v4-native-contract-error=native rvalue not yet supported: Unknown\n" \
    "v4-errors=1\nv4-aborted-after=codegen\n"


class ParseCaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_reject_directives(self):
        case = rs.parse_case(write_case(self.dir, "c", "-- prose line\n-- expect: reject borrowck\n"
                                        "-- error: one\n-- error: two\n-- at: 3:5\n-- errors: 2\n\ntask main() -> int { give back 0 }\n"))
        self.assertEqual((case.expect, case.stage, case.errors, case.at, case.error_count),
                         ("reject", "borrowck", ["one", "two"], (3, 5), 2))

    def test_directives_stop_at_code(self):
        case = rs.parse_case(write_case(self.dir, "c", "-- expect: check\ntask main() -> int { give back 0 }\n-- expect: run\n"))
        self.assertEqual(case.expect, "check")

    def test_panic_defaults_and_overrides(self):
        case = rs.parse_case(write_case(self.dir, "c", "-- expect: panic\n-- panic: boom\n"))
        self.assertEqual((case.exit, case.panic), (rs.PANIC_EXIT, ["boom"]))
        case = rs.parse_case(write_case(self.dir, "d", "-- expect: panic\n-- exit: nonzero\n"))
        self.assertEqual(case.exit, "nonzero")

    def test_run_stdout_lines(self):
        case = rs.parse_case(write_case(self.dir, "c", "-- expect: run\n-- stdout: a\n-- stdout: b\n-- exit: 3\n-- argv: x y\n"))
        self.assertEqual((case.stdout, case.exit, case.argv), (["a", "b"], 3, ["x", "y"]))

    def test_malformed(self):
        bad = {
            "none": "task main() -> int { give back 0 }\n",
            "two": "-- expect: check\n-- expect: build\n",
            "kind": "-- expect: maybe\n",
            "stage": "-- expect: reject later\n-- error: x\n",
            "noerror": "-- expect: reject ty\n",
            "argument": "-- expect: check ty\n",
            "at": "-- expect: reject ty\n-- error: x\n-- at: five\n",
            "errorcheck": "-- expect: check\n-- error: x\n",
            "stdoutcheck": "-- expect: check\n-- stdout: x\n",
            "known": "-- expect: check\n-- known: someday\n",
            "exit": "-- expect: run\n-- exit: lots\n",
        }
        for name, text in bad.items():
            with self.subTest(name=name), self.assertRaises(rs.CaseError):
                rs.parse_case(write_case(self.dir, name, text))


class OutputTests(unittest.TestCase):
    def test_parse_output(self):
        compiled = rs.parse_compiler_output(BORROWCK_ERROR)
        self.assertEqual(compiled.aborted_after, "borrowck")
        self.assertEqual(len(compiled.errors()), 1)
        diag = compiled.errors()[0]
        self.assertEqual((diag.stage, diag.start, diag.end, diag.help), ("borrowck", 6, 9, "a stays on loan"))
        self.assertIsNone(compiled.module)
        self.assertEqual(rs.parse_compiler_output(CLEAN).module, 'target triple = "x"\n')

    def test_native_contract_error_is_codegen(self):
        compiled = rs.parse_compiler_output(CODEGEN_ERROR)
        self.assertEqual([d.stage for d in compiled.errors()], ["codegen"])

    def test_line_col(self):
        self.assertEqual(rs.line_col(b"ab\ncd\n", 4), (2, 2))


class JudgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def case(self, header: str, body: str = "task main() -> int { give back 0 }\n") -> rs.Case:
        return rs.parse_case(write_case(self.dir, "case", header + body))

    def test_reject_matches(self):
        case = self.case("-- expect: reject borrowck\n-- error: while the value is borrowed\n-- error: stays on loan\n")
        self.assertIsNone(FakeRunner(BORROWCK_ERROR).judge(case))

    def test_reject_wrong_stage_and_text(self):
        case = self.case("-- expect: reject mir\n-- error: borrowed\n")
        self.assertIn("expected rejection after mir", FakeRunner(BORROWCK_ERROR).judge(case))
        case = self.case("-- expect: reject borrowck\n-- error: no such words\n")
        self.assertIn("no borrowck error mentions", FakeRunner(BORROWCK_ERROR).judge(case))

    def test_reject_frontend_alias(self):
        case = self.case("-- expect: reject frontend\n-- error: borrowed\n")
        self.assertIsNone(FakeRunner(BORROWCK_ERROR).judge(case))
        self.assertIn("got rejection after codegen", FakeRunner(CODEGEN_ERROR).judge(case))

    def test_reject_position_and_count(self):
        case = self.case("-- expect: reject borrowck\n-- error: borrowed\n-- at: 1:7\n-- errors: 1\n")
        self.assertIsNone(FakeRunner(BORROWCK_ERROR).judge(case))
        case = self.case("-- expect: reject borrowck\n-- error: borrowed\n-- at: 2:1\n")
        self.assertIn("first error at 1:7", FakeRunner(BORROWCK_ERROR).judge(case))
        case = self.case("-- expect: reject borrowck\n-- error: borrowed\n-- errors: 2\n")
        self.assertIn("expected 2 errors", FakeRunner(BORROWCK_ERROR).judge(case))

    def test_check_ignores_codegen(self):
        case = self.case("-- expect: check\n")
        self.assertIsNone(FakeRunner(CODEGEN_ERROR).judge(case))
        self.assertIn("clean frontend", FakeRunner(BORROWCK_ERROR).judge(case))

    def test_build_needs_codegen(self):
        case = self.case("-- expect: build\n")
        self.assertIsNone(FakeRunner(CLEAN).judge(case))
        self.assertIn("clean build", FakeRunner(CODEGEN_ERROR).judge(case))

    def test_run_and_panic(self):
        case = self.case("-- expect: run\n-- stdout: 7\n")
        self.assertIsNone(FakeRunner(CLEAN, (0, "7\n", "")).judge(case))
        self.assertIn("stdout", FakeRunner(CLEAN, (0, "8\n", "")).judge(case))
        self.assertIn("exit 2", FakeRunner(CLEAN, (2, "7\n", "")).judge(case))
        case = self.case("-- expect: panic\n-- panic: out of bounds\n")
        self.assertIsNone(FakeRunner(CLEAN, (101, "", "PANIC: index 3 out of bounds (len 3)\n")).judge(case))
        self.assertIn("exit 1", FakeRunner(CLEAN, (1, "", "out of bounds")).judge(case))
        case = self.case("-- expect: panic\n-- exit: nonzero\n-- panic: overflow\n")
        self.assertIsNone(FakeRunner(CLEAN, (1, "", "int addition overflow\n")).judge(case))
        self.assertIn("exit 0", FakeRunner(CLEAN, (0, "", "overflow")).judge(case))

    def test_known_cases_are_strict(self):
        case = self.case("-- expect: check\n-- known: #12 not fixed yet\n")
        self.assertEqual(FakeRunner(BORROWCK_ERROR).run_case(case).status, "xfail")
        self.assertEqual(FakeRunner(CLEAN).run_case(case).status, "xpass")


class CorpusTests(unittest.TestCase):
    def test_every_case_parses(self):
        cases = rs.discover()
        self.assertGreater(len(cases), 200)
        names = [c.ident for c in cases]
        self.assertEqual(len(names), len(set(names)))
        for case in cases:
            with self.subTest(case=case.ident):
                if case.known:
                    self.assertRegex(case.known, r"^#\d+ \S")


if __name__ == "__main__":
    unittest.main()
