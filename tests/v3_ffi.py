#!/usr/bin/env python3
"""Native FFI contracts: FREAK calls a real C shared library.

Builds tests/ffi/greet.c into a platform shared library (libgreet.so,
libgreet.dylib or greet.dll plus its import library) with the host Clang,
then checks that extern [C, link="greet"] and extern [C, load="greet"]
programs produce identical results on the LLVM and C backends, that
--link=/--lib-dir= link a library from another directory, that a missing
load= library fails by name, and that unsafe signatures are rejected.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "ffi"

EXPECTED = [
    "add: 42",
    "negate: -5",
    "wrap: 0",
    "twice: -600",
    "big: 9000000000",
    "scale: 6",
    "halve: 2.5",
    "even 4: true",
    "even 7: false",
    "not true: false",
    "plus: 3",
    "long: -8",
    "strlen: 5",
    "shout changed: 5",
    "shouted: FREAK",
    "hello: hello from C",
    "square 4: 16",
    "poked: -9",
    "count: 2",
    "pair: 34",
]

FLAGS_PROGRAM = '''extern [C, if target_os = "windows"] {
    task GetTickCount() -> c_uint
}
extern [C, if target_os = "linux"] {
    @link_name("getpid")
    task native_pid() -> c_int
}
extern [C, if target_os = "macos"] {
    @link_name("getpid")
    task native_pid() -> c_int
}
-- Each block's convention only has to match when its condition holds.
extern [C, win64, if target_os = "windows"] {
    @link_name("GetTickCount")
    task win_ticks() -> c_uint
}
extern [C, sysv64, if target_os = "linux", if target_arch = "x86_64"] {
    @link_name("getpid")
    task sysv_pid() -> c_int
}
extern [C] {
    task greet_add(a: c_int, b: c_int) -> c_int
}
say "sum " + word_from_int(greet_add(2, 3))
'''

BAD_PROGRAM = '''extern [C, link="x", load="y", stdcall, frob] {
    task takes_word(s: word) -> c_int
    task takes_list(x: List) -> c_void
    task takes_void(x: c_void) -> c_int
    task takes_int(x: int) -> c_int
    @nope
    task variadic(x: int, more: ...) -> int
}
task f() -> void {
    extern [C] { task nested() -> void }
}
'''

BAD_MESSAGES = [
    "an extern block takes one link= or load= option",
    "calling convention stdcall is not supported by V3.5 yet",
    "unknown extern ABI option frob",
    "word is not FFI-safe in extern parameter 's' of takes_word",
    "type 'List' is not FFI-safe in extern parameter 'x' of takes_list",
    "c_void is only valid behind a pointer or as a return type",
    "type 'int' is a FREAK type, not a C type",
    "unknown extern member attribute @nope",
    "variadic extern tasks are not supported by V3.5 yet",
    "extern blocks are only allowed at the top level",
]


def run(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, env=env, text=True, encoding="utf-8", errors="replace",
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)


def require(condition: bool, message: str, result: subprocess.CompletedProcess[str] | None = None) -> None:
    if condition:
        return
    print(f"FAIL: {message}")
    if result is not None:
        print(result.stdout[-4000:])
    sys.exit(1)


def clang_command() -> str:
    for candidate in ("clang", "clang-18", "clang-17", "clang-16", "clang-15"):
        if shutil.which(candidate):
            return candidate
    print("FAIL: clang is required to build the test library")
    sys.exit(1)


def build_library(clang: str, directory: Path) -> None:
    source = directory / "greet.c"
    if sys.platform == "win32":
        machine = run([clang, "-dumpmachine"], directory).stdout.strip()
        command = [clang, "-shared", "-O2", "-o", str(directory / "greet.dll"), str(source)]
        if "msvc" not in machine:
            command.append("-Wl,--out-implib," + str(directory / "libgreet.dll.a"))
    elif sys.platform == "darwin":
        command = [clang, "-dynamiclib", "-O2", "-o", str(directory / "libgreet.dylib"), str(source),
                   "-install_name", "@rpath/libgreet.dylib"]
    else:
        command = [clang, "-shared", "-fPIC", "-O2", "-o", str(directory / "libgreet.so"), str(source)]
    result = run(command, directory)
    require(result.returncode == 0, "could not build the greet test library", result)


def executable(directory: Path, stem: str) -> Path:
    return directory / (stem + (".exe" if sys.platform == "win32" else ""))


def output_lines(text: str) -> list[str]:
    return [line.rstrip("\r") for line in text.splitlines() if line.strip()]


# Set by the IRBuilder CI lane: default LLVM builds must lower through the
# in-process IRBuilder, never fall back to the textual module.
REQUIRE_IRBUILDER = os.environ.get("FREAK_TEST_REQUIRE_IRBUILDER", "") == "1"


def check_program(freak: str, directory: Path, stem: str, backend: list[str]) -> None:
    label = f"{stem} {' '.join(backend) or '--llvm'}"
    env = None
    if REQUIRE_IRBUILDER and not backend:
        env = dict(os.environ, FREAK_IRBUILDER_TRACE="1")
    built = run([freak, "build", stem + ".fk", *backend], directory, env)
    require(built.returncode == 0, f"{label}: build failed", built)
    if env is not None:
        require("irbuilder: irbuilder" in built.stdout, f"{label}: did not build through the IRBuilder", built)
    binary = executable(directory, stem)
    # Run from another directory: the library must be found next to the
    # executable (rpath $ORIGIN / @executable_path, or the DLL search order).
    ran = run([str(binary)], ROOT)
    require(ran.returncode == 0, f"{label}: program exited {ran.returncode}", ran)
    require(output_lines(ran.stdout) == EXPECTED, f"{label}: unexpected output", ran)
    print(f"ok {label}")


def check_missing_library(freak: str, directory: Path) -> None:
    lonely = directory / "lonely"
    lonely.mkdir()
    shutil.copy(directory / "ffi_load.fk", lonely / "ffi_load.fk")
    built = run([freak, "build", "ffi_load.fk"], lonely)
    require(built.returncode == 0, "missing-library build failed", built)
    ran = run([str(executable(lonely, "ffi_load"))], lonely)
    require(ran.returncode == 1, f"missing load= library should exit 1, got {ran.returncode}", ran)
    require("FFI: could not load library 'greet'" in ran.stdout, "missing library message", ran)
    print("ok load= missing library fails by name")


ESCAPED_PROGRAM = '''extern [C, load="missing_dir\\\\greet"] {
    task greet_add(a: c_int, b: c_int) -> c_int
}
say word_from_int(greet_add(1, 2))
'''


def check_escaped_name(freak: str, directory: Path) -> None:
    folder = directory / "escaped"
    folder.mkdir()
    (folder / "escaped.fk").write_text(ESCAPED_PROGRAM, encoding="utf-8")
    for backend in ([], ["--c"]):
        built = run([freak, "build", "escaped.fk", *backend], folder)
        require(built.returncode == 0, f"backslash load= name build {backend} failed", built)
        ran = run([str(executable(folder, "escaped"))], folder)
        require(ran.returncode == 1, f"backslash load= name should fail to load {backend}", ran)
        require("could not load library 'missing_dir\\greet'" in ran.stdout, f"backslash load= name {backend}", ran)
    print("ok load= name with a backslash reaches the loader intact")


CACHE_PROGRAMS = {
    "spaced": '''extern [C, link = "./libcalc.a"] {
    task calc_value() -> c_int
}
say "calc " + word_from_int(calc_value())
''',
    "newline": '''extern [C, link =
    "./libcalc.a"] {
    task calc_value() -> c_int
}
say "calc " + word_from_int(calc_value())
''',
    "comment": '''extern [C, link -- the archive next to this file
    = "./libcalc.a"] {
    task calc_value() -> c_int
}
say "calc " + word_from_int(calc_value())
''',
}


def check_run_cache(freak: str, clang: str, directory: Path) -> None:
    """Replacing a linked static archive at the same path must rebuild."""
    archiver = shutil.which("llvm-ar") or shutil.which("ar")
    if sys.platform == "win32" or archiver is None:
        print("skip run cache archive check (needs a POSIX ar)")
        return
    for label, program in CACHE_PROGRAMS.items():
        folder = directory / f"cache_{label}"
        folder.mkdir()
        (folder / "app.fk").write_text(program, encoding="utf-8")
        for value in (1, 2):
            (folder / "calc.c").write_text(f"int calc_value(void) {{ return {value}; }}\n", encoding="utf-8")
            compiled = run([clang, "-c", "calc.c", "-o", "calc.o"], folder)
            require(compiled.returncode == 0, "compile calc.c", compiled)
            (folder / "libcalc.a").unlink(missing_ok=True)
            archived = run([archiver, "rcs", "libcalc.a", "calc.o"], folder)
            require(archived.returncode == 0, "archive libcalc.a", archived)
            ran = run([freak, "run", "app.fk"], folder)
            require(ran.returncode == 0 and f"calc {value}" in ran.stdout, f"{label}: freak run after archive v{value}", ran)
    if sys.platform.startswith("linux"):
        # A bare link="calc" found through LIBRARY_PATH, outside the source
        # folder and every --lib-dir.
        folder = directory / "cache_library_path"
        vendor = folder / "vendor"
        vendor.mkdir(parents=True)
        (folder / "app.fk").write_text(CACHE_PROGRAMS["spaced"].replace("./libcalc.a", "calc"), encoding="utf-8")
        env = dict(os.environ)
        env["LIBRARY_PATH"] = str(vendor)
        for value in (1, 2):
            (vendor / "calc.c").write_text(f"int calc_value(void) {{ return {value}; }}\n", encoding="utf-8")
            compiled = run([clang, "-c", "calc.c", "-o", "calc.o"], vendor)
            require(compiled.returncode == 0, "compile vendor calc.c", compiled)
            (vendor / "libcalc.a").unlink(missing_ok=True)
            archived = run([archiver, "rcs", "libcalc.a", "calc.o"], vendor)
            require(archived.returncode == 0, "archive vendor libcalc.a", archived)
            ran = run([freak, "run", "app.fk"], folder, env)
            require(ran.returncode == 0 and f"calc {value}" in ran.stdout, f"LIBRARY_PATH: freak run after archive v{value}", ran)
        # An empty LIBRARY_PATH component means the current directory, here
        # the folder above the source file.
        folder = directory / "cache_library_path_empty"
        (folder / "app").mkdir(parents=True)
        (folder / "app" / "main.fk").write_text(CACHE_PROGRAMS["spaced"].replace("./libcalc.a", "calc"), encoding="utf-8")
        env = dict(os.environ)
        env["LIBRARY_PATH"] = ":" + str(directory / "no_such_dir")
        for value in (1, 2):
            (folder / "calc.c").write_text(f"int calc_value(void) {{ return {value}; }}\n", encoding="utf-8")
            compiled = run([clang, "-c", "calc.c", "-o", "calc.o"], folder)
            require(compiled.returncode == 0, "compile cwd calc.c", compiled)
            (folder / "libcalc.a").unlink(missing_ok=True)
            archived = run([archiver, "rcs", "libcalc.a", "calc.o"], folder)
            require(archived.returncode == 0, "archive cwd libcalc.a", archived)
            ran = run([freak, "run", "app/main.fk"], folder, env)
            require(ran.returncode == 0 and f"calc {value}" in ran.stdout, f"empty LIBRARY_PATH entry: freak run after archive v{value}", ran)
    print("ok run cache rebuilds when a linked archive changes (spaced, newline, comment, LIBRARY_PATH)")


def check_flags(freak: str, directory: Path) -> None:
    app = directory / "flags" / "app"
    libs = directory / "flags" / "libs"
    app.mkdir(parents=True)
    libs.mkdir(parents=True)
    for item in directory.iterdir():
        if item.is_file() and (item.name.startswith("libgreet") or item.name.startswith("greet.")) and item.suffix != ".c":
            shutil.copy(item, libs / item.name)
    (app / "flags.fk").write_text(FLAGS_PROGRAM, encoding="utf-8")
    for backend in ([], ["--c"]):
        built = run([freak, "build", "app/flags.fk", "--link=greet", "--lib-dir=libs", *backend], directory / "flags")
        require(built.returncode == 0, f"--link/--lib-dir build {backend} failed", built)
        env = dict(os.environ)
        if sys.platform == "win32":
            env["PATH"] = str(libs) + os.pathsep + env.get("PATH", "")
        ran = run([str(executable(app, "flags"))], ROOT, env)
        require(ran.returncode == 0 and output_lines(ran.stdout) == ["sum 5"], f"--link/--lib-dir run {backend}", ran)
    print("ok --link= and --lib-dir= with target_os blocks")


def check_diagnostics(freak: str, directory: Path) -> None:
    (directory / "bad.fk").write_text(BAD_PROGRAM, encoding="utf-8")
    checked = run([freak, "check", "bad.fk"], directory)
    require(checked.returncode != 0, "unsafe extern signatures must fail", checked)
    for message in BAD_MESSAGES:
        require(message in checked.stdout, f"missing diagnostic: {message}", checked)
    print("ok unsafe extern signatures rejected by name")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("freak", help="path to the freak CLI")
    args = parser.parse_args()
    freak = str(Path(args.freak).resolve())
    clang = clang_command()
    with tempfile.TemporaryDirectory(prefix="freak-ffi-") as temporary:
        directory = Path(temporary)
        for name in ("greet.c", "ffi_link.fk", "ffi_load.fk"):
            shutil.copy(FIXTURES / name, directory / name)
        build_library(clang, directory)
        for stem in ("ffi_link", "ffi_load"):
            for backend in ([], ["--c"]):
                check_program(freak, directory, stem, backend)
        check_missing_library(freak, directory)
        check_escaped_name(freak, directory)
        check_run_cache(freak, clang, directory)
        check_flags(freak, directory)
        check_diagnostics(freak, directory)
    print("native FFI contracts passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
