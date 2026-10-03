"""Check native ABI admission against real C signatures and the V4 compiler."""
import contextlib
import importlib.util
import io
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("abi_checks", ROOT / "src/compiler/v4/check_v4.py")
checks = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checks)
SPEC = importlib.util.spec_from_file_location("abi_build", ROOT / "src/compiler/v4/build_v4.py")
build = importlib.util.module_from_spec(SPEC)
with patch.dict(sys.modules, {"check_v4": checks}):
    SPEC.loader.exec_module(build)

C_HELPERS = '''#include <stdint.h>
intptr_t echo_isize(intptr_t value) { return value; }
uintptr_t echo_size(uintptr_t value) { return value; }
float echo_float(float value) { return value; }
double echo_double(double value) { return value; }
static unsigned char marker;
unsigned char *probe_ptr(void) { return &marker; }
unsigned char *echo_ptr(unsigned char *value) { return value; }
intptr_t accept_ptr(unsigned char *value) { return value == &marker ? 42 : 0; }
static int void_calls;
void touch_void(void) { ++void_calls; }
intptr_t count_void(void) { return void_calls; }
intptr_t invoke_callback(intptr_t (*callback)(intptr_t), intptr_t value) {
    return callback(value);
}
'''


class NativeCAbi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.clang = shutil.which("clang")
        if cls.clang is None:
            raise AssertionError("Clang is required for the native C ABI gate")
        cls.compiler = build.bootstrap(cls.clang)
        cls.target = build.host_target()

    def emit(self, directory, source_text):
        source = directory / "source.fk"
        source.write_text(source_text, encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            return build.emit_module(self.compiler, source, self.target)

    def test_admitted_scalars_and_callbacks_match_real_c(self):
        """Check both directions, including nonzero upper bits and pointer transport."""
        source = '''extern [C] {
    task echo_isize(value: std::ffi::c_isize) -> std::ffi::c_isize
    @link_name("echo_isize")
    task same_isize(value: std::ffi::c_isize) -> std::ffi::c_isize
    task echo_size(value: std::ffi::c_size) -> std::ffi::c_size
    task echo_float(value: std::ffi::c_float) -> std::ffi::c_float
    task echo_double(value: std::ffi::c_double) -> std::ffi::c_double
    task probe_ptr() -> *mut tiny
    task echo_ptr(value: *mut tiny) -> *mut tiny
    task accept_ptr(value: *mut tiny) -> std::ffi::c_isize
    task touch_void() -> std::ffi::c_void
    task count_void() -> std::ffi::c_isize
    task invoke_callback(callback: extern [C] task(value: std::ffi::c_isize) -> std::ffi::c_isize, value: std::ffi::c_isize) -> std::ffi::c_isize
}
@extern_callback("C")
task identity(value: std::ffi::c_isize) -> std::ffi::c_isize { give back value }
task main() -> int {
    if echo_isize(0 - 4294967338) != 0 - 4294967338 { give back 1 }
    if same_isize(4294967338) != 4294967338 { give back 2 }
    if echo_size(4294967338) != 4294967338 { give back 3 }
    if echo_float(1.5) != 1.5 { give back 4 }
    if echo_double(42.125) != 42.125 { give back 5 }
    if accept_ptr(echo_ptr(probe_ptr())) != 42 { give back 6 }
    touch_void()
    if count_void() != 1 { give back 7 }
    if invoke_callback(identity, 0 - 4294967338) != 0 - 4294967338 { give back 8 }
    if invoke_callback(identity, 4294967338) != 4294967338 { give back 9 }
    give back 42
}
'''
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            module = self.emit(directory, source)
            self.assertEqual(module.count("declare ccc i64 @echo_isize(i64) nounwind"), 1, module)
            llvm = directory / "module.ll"
            llvm.write_text(module, encoding="utf-8")
            helper = directory / "helpers.c"
            helper.write_text(C_HELPERS, encoding="utf-8")
            executable = directory / ("native.exe" if sys.platform == "win32" else "native")
            command = build.native_link_command(self.clang, llvm, executable)
            command.insert(command.index("-o"), str(helper))
            linked = subprocess.run(command, capture_output=True, text=True, timeout=120)
            self.assertEqual(linked.returncode, 0, linked.stdout + linked.stderr)
            executed = subprocess.run([str(executable)], capture_output=True, timeout=10)
            self.assertEqual((executed.returncode, executed.stdout, executed.stderr), (42, b"", b""))

    def test_unimplemented_c_widths_fail_before_native_publication(self):
        """Raw aliases, callbacks, pointer payloads and casts cannot erase the fence."""
        cases = []
        for scalar in ("c_int", "c_uint", "c_long", "c_ulong", "c_char", "c_uchar", "c_bool", "wchar"):
            cases.append((scalar, f'extern [C] {{ task outside(value: std::ffi::{scalar}) -> std::ffi::{scalar} }}\n',
                          "native C scalar ABI not yet supported:"))
        cases.extend([
            ("alias", 'alias Width = std::ffi::c_int\nextern [C] { task outside(value: Width) -> Width }\n', "native C scalar ABI not yet supported:"),
            ("pointer_alias", 'alias Pointer = *mut std::ffi::c_int\nextern [C] { task outside(value: Pointer) -> void }\n', "native C scalar ABI not yet supported:"),
            ("nested_callback", 'extern [C] { task outside(callback: extern [C] task(value: std::ffi::c_int) -> std::ffi::c_int) -> void }\n', "native C scalar ABI not yet supported:"),
            ("callback", '@extern_callback("C")\ntask callback(value: std::ffi::c_int) -> std::ffi::c_int { give back value }\n', "native C scalar ABI not yet supported:"),
            ("impl", 'shape A { marker: int }\nimpl A { task width(value: std::ffi::c_int) -> std::ffi::c_int { give back value } }\n', "native C scalar ABI not yet supported:"),
            ("impl_local", 'shape A { marker: int }\nimpl A { task width(value: std::ffi::c_isize) -> std::ffi::c_isize {\n pilot local: std::ffi::c_int = value\n give back local\n } }\n', "native C scalar ABI not yet supported:"),
            ("variadic", 'extern [C] { task outside(value: std::ffi::c_isize, args: ...) -> std::ffi::c_isize }\n', "native C variadic ABI not yet supported"),
        ])
        for name, prefix, reason in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                with self.assertRaises(RuntimeError) as failure:
                    self.emit(Path(temporary), prefix + 'task main() -> int { give back 42 }\n')
                self.assertIn(reason, str(failure.exception))
                self.assertIn("v4-aborted-after=codegen", str(failure.exception))
                self.assertNotIn("@@V4-MODULE", str(failure.exception))
        for name, prefix, body, reason in (
            ("local", "", "pilot value: std::ffi::c_int = 42", "native C scalar ABI not yet supported:"),
            ("inferred_cast", 'extern [C] { task probe_ptr() -> *mut tiny }\n',
             'pilot p = probe_ptr()\n trust me "test raw C width cast" on my honor as .ace {\n'
             ' pilot value = p.cast<std::ffi::c_int>()\n }', "native C scalar ABI not yet supported:"),
        ):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                with self.assertRaises(RuntimeError) as failure:
                    self.emit(Path(temporary), prefix + 'task main() -> int {\n' + body + '\n give back 42\n}\n')
                self.assertIn(reason, str(failure.exception))
                self.assertIn("v4-aborted-after=codegen", str(failure.exception))
                self.assertNotIn("@@V4-MODULE", str(failure.exception))


if __name__ == "__main__":
    unittest.main()
