"""Bootstrap result matching must inspect one result and preserve its payload."""
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

from freakc.emitter import CEmitter
from freakc.lexer import Lexer
from freakc.parser import Parser

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "freakc/runtime"


def emit(source):
    """Generate C through the production bootstrap lexer, parser and emitter."""
    return CEmitter().emit(Parser(Lexer(source).tokenize()).parse())


class CheckedResultOnce(unittest.TestCase):
    def test_direct_checked_read_is_evaluated_once(self):
        """The tag and both arms must refer to the same checked-read result."""
        source = '''task main() {
    check result fs::read_checked("input.fk") {
        ok(value) -> { say value }
        err(error) -> { say error }
    }
}
'''
        generated = emit(source)
        self.assertEqual(generated.count("freak_fs_read_checked("), 1)
        match = re.search(r"freak_result_word_word (__check_result_\d+) = freak_fs_read_checked", generated)
        self.assertIsNotNone(match)
        temporary = match.group(1)
        for field in ("is_ok", "data.ok_val", "data.err_val"):
            self.assertIn(temporary + "." + field, generated)

    def test_all_supported_result_types_capture_expressions_once(self):
        """The four frozen C result layouts share the single-evaluation rule."""
        for kind, literal, suffix in (("int", "42", "int_word"),
                                     ("num", "4.2", "num_word"),
                                     ("bool", "true", "bool_word"),
                                     ("word", '"value"', "word_word")):
            with self.subTest(kind=kind):
                source = f'''task main() {{
    check result ok({literal}) {{
        ok(value) -> {{ say value }}
        err(error) -> {{ say error }}
    }}
}}
'''
                generated = emit(source)
                self.assertRegex(generated, rf"freak_result_{suffix} __check_result_\d+ = ")
                self.assertEqual(generated.count(f"(freak_result_{suffix})"), 1)

    def test_stored_result_keeps_one_read(self):
        """Existing stored-result callers retain their direct binding accesses."""
        generated = emit('''task main() {
    pilot source_read = fs::read_checked("input.fk")
    check result source_read {
        ok(value) -> { say value }
        err(error) -> { say error }
    }
}
''')
        self.assertEqual(generated.count("freak_fs_read_checked("), 1)
        self.assertIn("if (source_read.is_ok)", generated)
        self.assertNotIn("__check_result_", generated)

    def test_temporary_avoids_subject_and_pattern_names(self):
        """A generated binding cannot shadow a visible subject or arm binding."""
        generated = emit('''task inspect(__check_result_1: word) {
    check result fs::read_checked(__check_result_1) {
        ok(__check_result_2) -> { say __check_result_2 }
        err(__check_result_3) -> { say __check_result_3 }
    }
}
task main() { inspect("input.fk") }
''')
        self.assertIn("freak_result_word_word __check_result_4 = freak_fs_read_checked(__check_result_1);", generated)
        self.assertIn("freak_word __check_result_2 = __check_result_4.data.ok_val;", generated)
        self.assertIn("freak_word __check_result_3 = __check_result_4.data.err_val;", generated)

    def test_temporary_avoids_wrapped_loop_references_in_both_arms(self):
        """Loop names omitted from the old vars table remain visible inside matches."""
        for subject in ('ok(__check_result_2)', 'fs::read_checked("input.fk")'):
            with self.subTest(subject=subject):
                generated = emit(f'''task main() {{
    for each __check_result_2 in [1] {{
        check result {subject} {{
            ok(value) -> {{ say __check_result_2 }}
            err(error) -> {{ say __check_result_2 }}
        }}
    }}
}}
''')
                # The for-each index consumes counter 1; its binding is not
                # registered in vars. The result must skip counter 2 anyway.
                self.assertRegex(generated, r"freak_result_(?:int|word)_word __check_result_3 = ")
                self.assertNotRegex(generated, r"freak_result_\w+ __check_result_2 = ")

    def test_changed_file_preserves_first_tag_payload_and_ownership(self):
        """Generated direct matches survive both file outcome changes without leaks."""
        clang = shutil.which("clang")
        self.assertIsNotNone(clang, "Clang is required for the generated-C result gate")
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            c_file = directory / "result.c"
            executable = directory / ("result.exe" if sys.platform == "win32" else "result")
            source = '''task main() {
    check result fs::read_checked("input.fk") {
        ok(value) -> {
            probe_release(value)
            give back 0
        }
        err(error) -> {
            probe_release(error)
            give back 0
        }
    }
}
'''
            prefix = '''#include "freak_runtime.h"
#include <stdio.h>
#include <stdlib.h>
freak_result_word_word probe_read_checked(freak_word path);
int64_t freak_probe_release(freak_word value);
#define freak_fs_read_checked probe_read_checked
'''
            suffix = r'''
#undef freak_fs_read_checked
static int reads, releases;
static freak_word expected_payload;
static void report(void) {
    if (reads != 1 || releases != 1) exit(71);
    printf("reads=%d releases=%d\n", reads, releases);
}
freak_result_word_word probe_read_checked(freak_word path) {
    if (++reads == 1 && atexit(report) != 0) exit(72);
    freak_result_word_word result = freak_fs_read_checked(path);
    expected_payload = result.is_ok ? result.data.ok_val : result.data.err_val;
    if (result.is_ok) {
        if (remove(freak_word_to_cstr(path)) != 0) exit(73);
    } else {
        FILE *file = fopen(freak_word_to_cstr(path), "wb");
        if (!file || fwrite("changed", 1, 7, file) != 7 || fclose(file) != 0) exit(74);
    }
    return result;
}
int64_t freak_probe_release(freak_word value) {
    if (reads != 1 || releases != 0 || value.data != expected_payload.data ||
        value.length != expected_payload.length || value.heap != expected_payload.heap)
        exit(75);
    bool was_owned = value.heap;
    freak_word_release_owned(&value);
    if (value.data != NULL || value.length != 0 || value.heap) exit(76);
    releases++;
    printf("payload-owned=%d\n", was_owned ? 1 : 0);
    return 0;
}
'''
            c_file.write_text(prefix + emit(source) + suffix, encoding="utf-8")
            link = ["-lws2_32"] if sys.platform == "win32" else ["-lm", "-pthread"]
            built = subprocess.run([clang, "-w", "-O0", "-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT",
                                    str(c_file), str(RUNTIME / "freak_runtime.c"),
                                    "-I" + str(RUNTIME), "-o", str(executable), *link],
                                   capture_output=True, text=True, timeout=60)
            self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
            path = directory / "input.fk"
            for initially_exists in (True, False):
                with self.subTest(initially_exists=initially_exists):
                    if path.exists():
                        path.unlink()
                    if initially_exists:
                        path.write_bytes(b"original")
                    result = subprocess.run([str(executable)], cwd=directory,
                                            capture_output=True, text=True, timeout=10)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertEqual(result.stdout,
                                     f"payload-owned={int(initially_exists)}\nreads=1 releases=1\n")
                    self.assertEqual(result.stderr, "")
                    self.assertEqual(path.exists(), not initially_exists)


if __name__ == "__main__":
    unittest.main()
