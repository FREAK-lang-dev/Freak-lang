"""The Linux runtime commands must execute the complete smoke inventory."""
from collections import Counter
import contextlib
import importlib.util
import io
from pathlib import Path
import re
import shlex
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("ci_smoke_coverage_guard", ROOT / "src/compiler/v4/check_v4.py")
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)
MATRIX_SHARD = "__V4_MATRIX_SHARD__"


class CiSmokeCoverage(unittest.TestCase):
    def runtime_selectors(self, job):
        commands = []
        lines = job.splitlines()
        for index, line in enumerate(lines):
            if not line.startswith("        run: "):
                continue
            command = line.removeprefix("        run: ").strip()
            if command in (">", "|-", "|", ">-"):
                parts = []
                for continuation in lines[index + 1:]:
                    if not continuation.startswith("          "):
                        break
                    parts.append(continuation.strip())
                command = " ".join(parts)
            tokens = shlex.split(command.replace("${{ matrix.shard }}", MATRIX_SHARD))
            if "src/compiler/v4/check_v4.py" in tokens:
                commands.append(tokens)
        self.assertEqual(len(commands), 1, "Each runtime job needs one executable checker command")
        tokens = commands[0]
        self.assertEqual(tokens[:3], ["python", "-u", "src/compiler/v4/check_v4.py"])
        selectors = {"--smoke": [], "--smoke-exclude": [], "--smoke-shard": []}
        arguments = tokens[3:]
        self.assertEqual(len(arguments) % 2, 0, "Unsupported executable-gate flags")
        for flag, value in zip(arguments[::2], arguments[1::2], strict=True):
            self.assertIn(flag, selectors, f"Unsupported executable-gate flag: {flag}")
            selectors[flag].append(value)
        return selectors

    def assert_complete_coverage(self, workflow):
        jobs = dict(re.findall(r"^  (v4-runtime-linux[^:]*):\n(.*?)(?=^  [a-z][\w-]*:|\Z)",
                               workflow, re.MULTILINE | re.DOTALL))
        sharded = jobs.pop("v4-runtime-linux")
        selectors = self.runtime_selectors(sharded)
        self.assertEqual(selectors["--smoke-shard"], [MATRIX_SHARD])
        matrix = re.search(r"shard:\s*\[([^\]]+)\]", sharded)
        self.assertIsNotNone(matrix)
        shards = re.findall(r'["\'](\d+/\d+)["\']', matrix.group(1))
        self.assertTrue(shards)
        selected = []
        try:
            for shard in shards:
                with contextlib.redirect_stdout(io.StringIO()):
                    selected.extend(guard.select_smokes(selectors["--smoke"], selectors["--smoke-exclude"], shard))
            for name, job in jobs.items():
                selectors = self.runtime_selectors(job)
                self.assertTrue(selectors["--smoke"], name)
                self.assertFalse(selectors["--smoke-shard"], name)
                with contextlib.redirect_stdout(io.StringIO()):
                    selected.extend(guard.select_smokes(selectors["--smoke"], selectors["--smoke-exclude"], ""))
        except SystemExit as error:
            self.fail(f"Runtime selectors reject their inventory: {error}")
        actual = Counter(smoke["fixture"] for smoke in selected)
        expected = Counter(smoke["fixture"] for smoke in guard.EXECUTABLE_SMOKES)
        self.assertEqual(actual, expected, f"Missing: {sorted((expected - actual).elements())}; "
                                          f"repeated: {sorted((actual - expected).elements())}")

    def test_linux_jobs_cover_every_fixture_exactly_once(self):
        self.assert_complete_coverage((ROOT / ".github/workflows/v4-ci.yml").read_text())

    def test_guard_rejects_reduced_or_repeated_execution(self):
        workflow = (ROOT / ".github/workflows/v4-ci.yml").read_text()
        mutations = {
            "broad snapshot exclusion": workflow.replace("--smoke-exclude unit_snapshot_smoke.fk", "--smoke-exclude unit_snapshot", 1),
            "narrowed shard": workflow.replace("--smoke-exclude unit_snapshot_smoke.fk", "--smoke h6_ --smoke-exclude unit_snapshot_smoke.fk", 1),
            "transpile shard": workflow.replace("--smoke-exclude unit_snapshot_smoke.fk", "--fast --smoke-exclude unit_snapshot_smoke.fk", 1),
            "fixed shard": workflow.replace("--smoke-shard ${{ matrix.shard }}", "--smoke-shard 1/6", 1),
            "missing shard": workflow.replace("--smoke-shard ${{ matrix.shard }}", "", 1),
            "dedicated exclusion": workflow.replace("--smoke unit_snapshot_smoke", "--smoke unit_snapshot_smoke --smoke-exclude unit_snapshot", 1),
            "transpile dedicated": workflow.replace("--smoke unit_snapshot_smoke", "--fast --smoke unit_snapshot_smoke", 1),
        }
        for label, mutated in mutations.items():
            with self.subTest(label=label), self.assertRaises(AssertionError):
                self.assert_complete_coverage(mutated)


class SmokeExecutionCases(unittest.TestCase):
    def test_cases_preserve_guards_and_cover_every_independent_program(self):
        registered = [smoke for smoke in guard.EXECUTABLE_SMOKES
                      if smoke["fixture"].startswith("owned_word_")]
        before = repr(registered)
        expanded = list(guard.smoke_execution_cases(registered))
        self.assertEqual(len(expanded), 12)
        contracts = [smoke for smoke in expanded if smoke["fixture"] == "owned_word_contract_smoke.fk"]
        self.assertEqual([smoke["argv"] for smoke in contracts], [[str(i)] for i in range(8)])
        programs = [smoke for smoke in expanded if smoke["fixture"] == "owned_word_execute_smoke.fk"]
        self.assertEqual([smoke["llvm_programs"][0][0] for smoke in programs],
                         ["owned_words.fk", "owned_word_scopes.fk", "owned_word_return_temporary.fk"])
        self.assertIn("A\0B\n", programs[0]["llvm_programs"][0][2])
        for smoke in expanded:
            self.assertEqual(smoke["memory_limit_mb"], 64)
            self.assertIn(smoke["fixture"], guard.C_ARRAY_HANDLE_RESOURCE_FIXTURES)
            self.assertNotIn("runtime_cases", smoke)
        self.assertEqual(guard.C_ARRAY_HANDLE_RESOURCE_LIMIT, 1024)
        self.assertEqual(repr(registered), before)

    def test_case_cannot_override_fixture_resource_or_timeout_guards(self):
        for cases in ([], {}, [None], [{"fixture": "other.fk"}],
                      [{"memory_limit_mb": 4096}], [{"timeout": 3600}], [{"runtime_cases": [{}]}]):
            with self.subTest(cases=cases), self.assertRaises(ValueError):
                list(guard.smoke_execution_cases([{"name": "bad", "runtime_cases": cases}]))


if __name__ == "__main__":
    unittest.main()
