#!/usr/bin/env python3
"""Guard the existing private FS void/outslot helper, not typed fs204 admission.

Import is process-free. Actual native work needs the lead's separate execution
lease. --plain is an additional all-OS gate; Linux ASan+UBSan is mandatory.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
OPTS = (0, 2, 3)
SCOPE = "private fs void/outslot helper prerequisite; no typed fs204 admission"
OWNED_NAMES = ("tests/v4_fs_read_bridge_probe.c", "tests/v4_fs_read_bridge.py",
               "tests/test_v4_fs_read_bridge.py", "tests/v4_fs_read_bridge_vectors.json",
               "src/compiler/v4/FS_READ_BRIDGE_CONTRACT.md")
SUPPORT_NAME = "tests/v4_c_integer_runtime.py"
SUPPORT_SHA = "1fe37e9bf8f33c72193e85cfa87ffef78ed29bc0663ff447acd35a42f6fbd8e2"
GUARD_NAME = "src/compiler/v4/check_v4.py"
SOURCE_NAMES = (*OWNED_NAMES, "freakc/runtime/freak_runtime.c", "freakc/runtime/freak_runtime.h",
                "freakc/runtime/freak_v4_word_runtime.c", "freakc/runtime/freak_v4_word_runtime.h",
                "freakc/runtime/freak_v4_system_runtime.c", "freakc/runtime/freak_v4_system_runtime.h",
                SUPPORT_NAME, GUARD_NAME)
VECTOR_PATH = ROOT / "tests/v4_fs_read_bridge_vectors.json"
COUNTS = {"linux": 55, "darwin": 55, "win32": 57}
CAPABILITIES = ("asan-heap", "ubsan-overflow", "ubsan-division")
FAULT_REASONS = {
    "path-allocation": "filesystem path allocation failed", "open": "could not open filesystem file",
    "stat": "filesystem path is not a readable regular file", "nonregular": "filesystem path is not a readable regular file",
    "stream": "could not open filesystem stream", "negative-size": "filesystem file size overflow",
    "seek": "could not seek filesystem file", "contents-allocation": "filesystem contents allocation failed",
    "short-read": "could not read complete filesystem file", "read-error": "could not read complete filesystem file",
    "extra-data": "could not read complete filesystem file", "eof-error": "could not read complete filesystem file",
    "close": "could not close filesystem file", "adopt": "filesystem contents ownership allocation failed",
    "large-allocation": "filesystem contents allocation failed", "seek-close": "could not seek filesystem file",
    "allocation-close": "filesystem contents allocation failed", "short-close": "could not read complete filesystem file",
    "read-error-close": "could not read complete filesystem file",
    "stat-descriptor-close": "filesystem path is not a readable regular file",
    "wide-first": "could not convert filesystem path", "wide-second": "could not convert filesystem path"}
PATH_REASONS = {"empty": "filesystem path is empty", "nul": "filesystem path contains NUL",
                "nul-invalid": "filesystem path contains NUL", "invalid": "filesystem path is not valid UTF-8",
                "size-max": "filesystem path size overflow", "windows-size": "filesystem path size overflow"}
FATAL_MODES = ("null-tag", "null-payload", "null-both", "alias", "null", "foreign", "unknown", "stale", "error-copy", "error-track")
EXPECTED_IDS = ({name + "-file" for name in ("empty", "binary", "nul-only", "crlf", "ascii", "max-scalar")} |
                {"path-first-binary", "missing", "directory", "fifo", "llvm-owner-audit", "c-owner-audit"} |
                {f"invalid-file-{index}" for index in range(8)} |
                {"path-" + name for name in PATH_REASONS} | {"fault-" + name for name in FAULT_REASONS} |
                {"fatal-" + name for name in FATAL_MODES})


def scenario_spec(identity):
    """Require the named scenario's real mode, fixture and host coverage."""
    hosts = list(COUNTS)
    if identity in {name + "-file" for name in ("empty", "binary", "nul-only", "crlf", "ascii", "max-scalar")}:
        argv = ["--read", "@" + identity[:-5], "payload-first"]
    elif identity == "path-first-binary": argv = ["--read", "@binary", "path-first"]
    elif identity.startswith("invalid-file-"): argv = ["--read", "@invalid-" + identity[13:], "path-first"]
    elif identity in ("missing", "directory", "fifo"):
        argv = ["--read", "@" + identity, "directory-boundary" if identity == "directory" else "payload-first"]
        if identity == "fifo": hosts = ["linux", "darwin"]
    elif identity.startswith("path-") and identity[5:] in PATH_REASONS:
        argv = ["--path", identity[5:]]
        if identity == "path-windows-size": hosts = ["win32"]
    elif identity.startswith("fault-") and identity[6:] in FAULT_REASONS:
        argv = ["--fault", identity[6:], "@binary"]
        if identity in ("fault-wide-first", "fault-wide-second"): hosts = ["win32"]
    elif identity.startswith("fatal-") and identity[6:] in FATAL_MODES: argv = ["--fatal", identity[6:], "@binary"]
    elif identity in ("llvm-owner-audit", "c-owner-audit"): argv = ["--" + identity]
    else: raise GateError("unknown named scenario")
    return argv, hosts


class GateError(ValueError):
    pass


def require(value, message):
    if not value:
        raise GateError(message)


def sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes():
    return {name: sha(ROOT / name) for name in SOURCE_NAMES}


def protocol(tag: int, payload: bytes, recovery: int = 0):
    return (f"fs-tag:{tag}\nfs-bytes:{payload.hex()}\npath:unchanged\npayloads:independent\n"
            f"recovery:{recovery}\nowners:0\ndescriptors:0\nraw-allocations:0\n").encode()


def directory_receipt(boundary):
    require(boundary in ("admitted", "rejected"), "invalid real directory boundary")
    count = 1 if boundary == "admitted" else 0
    return f"directory-open:{boundary};stat:{count};raw-close:{count};stream:0;read:0;adopt:0\n".encode()


def expected_case(case, fixtures, host, directory_boundary="admitted"):
    require(host in COUNTS, "unknown host")
    args = case["argv"]
    require(type(args) is list and all(type(value) is str for value in args), "invalid case arguments")
    status, stdout, stderr = 0, b"", b""
    if args and args[0] == "--read":
        require(len(args) == 3 and args[2] in ("path-first", "payload-first", "directory-boundary") and args[1].startswith("@"), "bad read case")
        fixture = fixtures[args[1][1:]]
        if fixture["kind"] == "file":
            data = bytes.fromhex(fixture["hex"])
            try:
                data.decode("utf-8", "strict")
                tag, payload = 1, data
            except UnicodeDecodeError:
                tag, payload = 0, b"filesystem file is not valid UTF-8"
        else:
            require(fixture["kind"] in ("missing", "directory", "fifo"), "wrong filesystem fixture kind")
            tag = 0
            payload = (b"could not open filesystem file" if fixture["kind"] == "missing" else
                       b"filesystem path is not a readable regular file")
        stdout = protocol(tag, payload)
        if args[2] == "directory-boundary":
            require(fixture["kind"] == "directory" and (host == "win32" or directory_boundary == "admitted"), "wrong directory boundary host")
            payload = b"could not open filesystem file" if directory_boundary == "rejected" else b"filesystem path is not a readable regular file"
            stdout = directory_receipt(directory_boundary) + protocol(0, payload)
    elif args and args[0] == "--path":
        require(len(args) == 2 and args[1] in PATH_REASONS, "bad path case")
        stdout = protocol(0, PATH_REASONS[args[1]].encode())
    elif args and args[0] == "--fault":
        require(len(args) == 3 and args[1] in FAULT_REASONS and args[2] == "@binary", "bad fault case")
        stdout = protocol(0, FAULT_REASONS[args[1]].encode(), 64)
    elif args and args[0] == "--fatal":
        require(len(args) == 3 and args[2] == "@binary", "bad private fatal case")
        mode = args[1]
        if mode in ("error-copy", "error-track"):
            status = 3 if host == "win32" else -signal.SIGABRT
            reason = "out of memory copying owned storage" if mode == "error-copy" else "out of memory tracking owned storage"
            stderr = ("FREAK: V4 word panic: " + reason + "\n").encode()
        else:
            require(mode in ("null-tag", "null-payload", "null-both", "alias", "null", "foreign", "unknown", "stale"), "unknown fatal case")
            status = 1
            reason = "invalid filesystem result slots" if mode in ("null-tag", "null-payload", "null-both", "alias") else "filesystem path is not a live owned word"
            stderr = ("FREAK: V4 system runtime: " + reason + "\n").encode()
    elif args == ["--llvm-owner-audit"]:
        status, stderr = 86, b"FREAK: LLVM ownership audit found 1 unreleased word allocation(s)\n"
    elif args == ["--c-owner-audit"]:
        status, stderr = 87, b"FREAK: C ownership audit found 1 unreleased word allocation(s)\n"
    else:
        raise GateError("unknown closed probe scenario")
    return {"status": status, "stdout": stdout.decode(), "stderr": stderr.decode()}


def load_vectors(path: Path = VECTOR_PATH):
    data = json.loads(path.read_text(encoding="utf-8"))
    require(set(data) == {"schema", "count", "counts", "fixtures", "cases", "sanitizer_capabilities"} and
            type(data["schema"]) is int and data["schema"] == 1 and type(data["count"]) is int and
            data["count"] == 58 and len(data["cases"]) == 58 and data["counts"] == COUNTS and
            data["sanitizer_capabilities"] == list(CAPABILITIES), "incomplete frozen fs vectors")
    seen, counts = set(), {host: 0 for host in COUNTS}
    for name, fixture in data["fixtures"].items():
        require(re.fullmatch(r"[a-z0-9-]+", name) and type(fixture["name"]) is str and
                Path(fixture["name"]).name == fixture["name"] and fixture["name"] not in ("", ".", "..") and
                not any(character in fixture["name"] for character in ("/", "\\", ":", "\0")) and
                fixture["kind"] in ("file", "missing", "directory", "fifo"), "unsafe fixture descriptor")
        require(set(fixture) == ({"kind", "name", "hex"} if fixture["kind"] == "file" else
                                {"kind", "name", "platforms"} if fixture["kind"] == "fifo" else {"kind", "name"}), "unexpected fixture fields")
        if fixture["kind"] == "file":
            require(re.fullmatch(r"(?:[0-9a-f]{2})*", fixture["hex"]), "noncanonical fixture bytes")
        if fixture["kind"] == "fifo":
            require(fixture["platforms"] == ["linux", "darwin"], "FIFO cannot be a Windows stand-in")
    require(len({fixture["name"] for fixture in data["fixtures"].values()}) == len(data["fixtures"]), "aliased fixture names")
    for case in data["cases"]:
        require(set(case) == {"id", "argv", "platforms", "expected"} and re.fullmatch(r"[a-z0-9-]+", case["id"]) and
                case["id"] not in seen and case["platforms"] in (["linux", "darwin", "win32"], ["linux", "darwin"], ["win32"]), "invalid/duplicate case identity")
        seen.add(case["id"])
        require((case["argv"], case["platforms"]) == scenario_spec(case["id"]), "named scenario mode/host drift")
        for host in case["platforms"]:
            counts[host] += 1
            boundaries = ("admitted", "rejected") if case["id"] == "directory" and host == "win32" else ("admitted",)
            if case["id"] == "directory": require(set(case["expected"]) == {"admitted", "rejected"}, "missing exact directory branches")
            for boundary in boundaries:
                wanted = expected_case(case, data["fixtures"], host, boundary)
                expected = case["expected"][boundary] if case["id"] == "directory" else case["expected"]
                require(set(expected) == {"status", "stdout_hex", "stderr_hex"} and
                        all(re.fullmatch(r"(?:[0-9a-f]{2})*", expected[field]) for field in ("stdout_hex", "stderr_hex")), "invalid golden fields")
                expected_status = 3 if host == "win32" else -signal.SIGABRT
                frozen_status = expected_status if expected["status"] == "word-abort" else expected["status"]
                require(type(frozen_status) is int and wanted == {"status": frozen_status,
                        "stdout": bytes.fromhex(expected["stdout_hex"]).decode(),
                        "stderr": bytes.fromhex(expected["stderr_hex"]).decode()}, "frozen golden disagrees with independent oracle")
    require(counts == COUNTS and seen == EXPECTED_IDS, "missing closed or host-specific scenarios")
    require({case["argv"][1] for case in data["cases"] if case["argv"][0] == "--fault"} == set(FAULT_REASONS) and
            {case["argv"][1] for case in data["cases"] if case["argv"][0] == "--path"} == set(PATH_REASONS), "missing fault or path family")
    return data


def validate_exact(actual, wanted, host):
    require(set(actual) == {"status", "stdout", "stderr"} and type(actual["status"]) is int and
            type(actual["stdout"]) is str and type(actual["stderr"]) is str, "invalid child status/channel fields")
    normalized = {"status": actual["status"], **{key: actual[key].replace("\r\n", "\n") if host == "win32" else actual[key]
                                                    for key in ("stdout", "stderr")}}
    require(normalized == wanted, "strict fs status/channel oracle mismatch")


def validate_case(actual, case, fixtures, host):
    boundary = "admitted"
    if case["id"] == "directory" and host == "win32" and type(actual.get("stdout")) is str:
        if actual["stdout"].replace("\r\n", "\n").startswith(directory_receipt("rejected").decode()): boundary = "rejected"
    validate_exact(actual, expected_case(case, fixtures, host, boundary), host)


def validate_capability(actual, kind):
    require(kind in CAPABILITIES and set(actual) == {"status", "stdout", "stderr"} and
            type(actual["status"]) is int and actual["stdout"] == "" and type(actual["stderr"]) is str, "invalid sanitizer capability fields")
    stderr = actual["stderr"]
    if kind == "asan-heap":
        require(actual["status"] == 86 and "ERROR: AddressSanitizer: heap-buffer-overflow" in stderr and
                "SUMMARY: AddressSanitizer: heap-buffer-overflow" in stderr and "FREAK:" not in stderr,
                "missing real ASan heap diagnostic/status86")
    else:
        tokens = ("runtime error: signed integer overflow",) if kind == "ubsan-overflow" else (
            "runtime error: division of", "cannot be represented in type")
        require(actual["status"] == 85 and all(token in stderr for token in (*tokens, "SUMMARY: UndefinedBehaviorSanitizer:")) and
                "AddressSanitizer" not in stderr and "FREAK:" not in stderr, "missing real UBSan diagnostic/status85")


def build_flags(opt, sanitize):
    require(type(opt) is int and opt in OPTS, "invalid optimization level")
    return ["-std=c11", "-g", f"-O{opt}", "-Werror=implicit-function-declaration", "-Werror=incompatible-pointer-types",
            "-Werror=int-conversion", "-Werror=return-type", "-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1", "-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1",
            *(["-fsanitize=address,undefined", "-fno-sanitize-recover=all", "-fno-omit-frame-pointer"] if sanitize else [])]


def fixture_facts(directory, data, host):
    facts = {}
    for identity, fixture in data["fixtures"].items():
        if host not in fixture.get("platforms", COUNTS): continue
        path = directory / fixture["name"]
        kind = fixture["kind"]
        require(not path.is_symlink(), "fixture alias is forbidden")
        if kind == "missing": require(not path.exists(), "missing-file fixture was created")
        else:
            mode = path.stat().st_mode
            require((stat.S_ISREG(mode) if kind == "file" else stat.S_ISDIR(mode) if kind == "directory" else stat.S_ISFIFO(mode)), "fixture kind drift")
            if kind == "directory": require(not any(path.iterdir()), "directory fixture changed")
        facts[identity] = {"kind": kind, "name": fixture["name"]}
        if kind == "file":
            facts[identity].update(bytes=path.stat().st_size, sha256=sha(path))
            require(path.read_bytes() == bytes.fromhex(fixture["hex"]), "fixture byte drift")
    require({path.name for path in directory.iterdir()} == {row["name"] for row in facts.values() if row["kind"] != "missing"}, "unexpected fixture object")
    return facts


def create_fixtures(directory, data, host):
    directory.mkdir(exist_ok=False)
    for fixture in data["fixtures"].values():
        if host not in fixture.get("platforms", COUNTS): continue
        path = directory / fixture["name"]
        if fixture["kind"] == "file": path.write_bytes(bytes.fromhex(fixture["hex"]))
        elif fixture["kind"] == "directory": path.mkdir()
        elif fixture["kind"] == "fifo": os.mkfifo(path)
    return fixture_facts(directory, data, host)


def load_support(frozen):
    require(sha(frozen / SUPPORT_NAME) == SUPPORT_SHA, "accepted checked32 guard support drift")
    name = "v4_fs_read_bridge_frozen_support"
    require(name not in sys.modules, "support namespace must be fresh")
    module = types.ModuleType(name)
    module.__file__ = str(ROOT / SUPPORT_NAME)
    sys.modules[name] = module
    exec(compile((frozen / SUPPORT_NAME).read_bytes(), module.__file__, "exec"), module.__dict__)
    module.OWNED_SOURCE_NAMES = tuple(name for name in SOURCE_NAMES if name != GUARD_NAME)
    module.COMPILE_SECONDS, module.COMPILE_MIB = 120, 512
    module.RUN_SECONDS, module.RUN_MIB = 10, 128
    return module


def load_guard(frozen):
    name = "v4_fs_read_bridge_frozen_process_guard"
    require(name not in sys.modules, "process guard namespace must be fresh")
    module = types.ModuleType(name)
    module.__file__ = str(ROOT / GUARD_NAME)
    sys.modules[name] = module
    exec(compile((frozen / GUARD_NAME).read_bytes(), module.__file__, "exec"), module.__dict__)
    return module


@contextmanager
def sanitizer_environment(support, sanitize):
    with support.sanitizer_environment(False):
        if sanitize:
            os.environ["ASAN_OPTIONS"] = "halt_on_error=1:detect_leaks=1:exitcode=86"
            os.environ["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1:exitcode=85"
        yield


def validate_report(report, data, sanitize):
    host = report.get("platform")
    require(report.get("complete") is True and report.get("scope") == SCOPE and report.get("sanitized") is sanitize and
            host in COUNTS and (not sanitize or host == "linux"), "wrong/incomplete fs report")
    sources = report.get("source_hashes", {})
    require(set(sources) == set(SOURCE_NAMES) and sources == report.get("final_source_hashes") == report.get("final_frozen_source_hashes") and
            all(re.fullmatch(r"[0-9a-f]{64}", value) for value in sources.values()) and
            sources[SUPPORT_NAME] == SUPPORT_SHA, "source/copy conservation missing")
    compiler = report.get("compiler", {})
    require(compiler.get("sha256") == report.get("final_compiler_sha256") and re.fullmatch(r"[0-9a-f]{64}", compiler.get("sha256", "")) and
            type(compiler.get("selected")) is str and compiler["selected"] and type(compiler.get("path")) is str and compiler["path"] and
            compiler["path"] == report.get("final_selected_compiler") and
            type(compiler.get("target")) is str and compiler["target"], "compiler pins missing")
    expected_fixtures = {}
    for identity, fixture in data["fixtures"].items():
        if host not in fixture.get("platforms", COUNTS): continue
        expected_fixtures[identity] = {"kind": fixture["kind"], "name": fixture["name"]}
        if fixture["kind"] == "file":
            payload = bytes.fromhex(fixture["hex"])
            expected_fixtures[identity].update(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
    require(report.get("fixture_facts") == report.get("final_fixture_facts") == expected_fixtures,
            "fixture conservation missing")
    matrices = report.get("matrices", [])
    require([row.get("optimization") for row in matrices] == list(OPTS), "missing optimization matrix")
    binaries = report.get("binary_hashes", {})
    require(len(binaries) == 3 and binaries == report.get("final_binary_hashes") and
            set(binaries) == {row.get("binary_path") for row in matrices}, "missing final binary identities")
    cases = [case for case in data["cases"] if host in case["platforms"]]
    for matrix in matrices:
        require(matrix.get("flags") == build_flags(matrix["optimization"], sanitize) and
                matrix.get("binary_sha256") == binaries.get(matrix["binary_path"]) and
                re.fullmatch(r"[0-9a-f]{64}", matrix.get("binary_sha256", "")), "binary flags/hash mismatch")
        require([row.get("id") for row in matrix.get("cases", [])] == [case["id"] for case in cases], "missing/reordered native case")
        for case, row in zip(cases, matrix["cases"]): validate_case(row["actual"], case, data["fixtures"], host)
        require([row.get("kind") for row in matrix.get("capabilities", [])] == (list(CAPABILITIES) if sanitize else []), "missing sanitizer capability")
        for row in matrix["capabilities"]: validate_capability(row["actual"], row["kind"])


def run_gate(clang, directory, report, sanitize, support, data):
    fixture_dir = directory / "fixtures"
    report["fixture_facts"] = create_fixtures(fixture_dir, data, sys.platform)
    frozen = directory / "frozen-source"
    class Pins(support.Conservation):
        def check(self):
            super().check()
            require(fixture_facts(fixture_dir, data, sys.platform) == report["fixture_facts"], "fixture final pins drift")
        def final_pins(self):
            self.check()
            report["final_fixture_facts"] = fixture_facts(fixture_dir, data, sys.platform)
            super().final_pins()
    pins = Pins(clang, frozen, report)
    pins.check()
    checks = load_guard(frozen)
    pins.check()
    runner = support.Runner(checks, directory, pins)
    version = runner.run([str(clang), "--version"], "compiler-version", compiling=True)
    require(version.returncode == 0 and "clang" in version.stdout.lower(), "Clang identity unavailable")
    target = runner.run([str(clang), "-dumpmachine"], "compiler-target", compiling=True)
    target_text = target.stdout.replace("\r\n", "\n") if sys.platform == "win32" else target.stdout
    require(target.returncode == 0 and re.fullmatch(r"[^\s]+\n?", target_text), "native target unavailable")
    report["compiler"].update(version=version.stdout, target=target_text.rstrip("\n"))
    cases = [case for case in data["cases"] if sys.platform in case["platforms"]]
    for opt in OPTS:
        flags = build_flags(opt, sanitize)
        binary = directory / (f"fs-O{opt}" + (".exe" if sys.platform == "win32" else ""))
        libraries = ["-lws2_32", "-lshell32"] if sys.platform == "win32" else ["-lm"]
        command = [str(clang), *flags, "-I", str(frozen / "freakc/runtime"),
                   str(frozen / "tests/v4_fs_read_bridge_probe.c"), "-o", str(binary), *libraries]
        result = runner.run(command, f"compile-O{opt}", compiling=True)
        require(result.returncode == 0, "FS probe compilation failed")
        pins.admit_binary(binary)
        matrix = {"optimization": opt, "flags": flags, "binary_path": str(binary), "binary_sha256": sha(binary), "cases": [], "capabilities": []}
        report["matrices"].append(matrix)
        for case in cases:
            argv = [str(fixture_dir / data["fixtures"][value[1:]]["name"]) if value.startswith("@") else value for value in case["argv"]]
            actual = support.observed(runner.run([str(binary), *argv], f"O{opt}-{case['id']}"))
            matrix["cases"].append({"id": case["id"], "actual": actual})
            validate_case(actual, case, data["fixtures"], sys.platform)
        if sanitize:
            for kind in CAPABILITIES:
                actual = support.observed(runner.run([str(binary), "--" + kind], f"O{opt}-{kind}"))
                matrix["capabilities"].append({"kind": kind, "actual": actual})
                validate_capability(actual, kind)
        pins.check()
        print(f"fs O{opt}: {len(cases)} exact cases, {len(matrix['capabilities'])} sanitizer controls verified; final pins pending", flush=True)
    pins.final_pins()
    validate_report(dict(report, complete=True), data, sanitize)
    return pins


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clang", default=os.environ.get("FREAK_CLANG") or shutil.which("clang"))
    parser.add_argument("--plain", action="store_true")
    parser.add_argument("--work", required=True, type=Path)
    args = parser.parse_args()
    if sys.platform not in COUNTS or (not args.plain and sys.platform != "linux"):
        parser.error("plain proof requires Linux/macOS/Windows; mandatory ASan+UBSan requires Linux")
    if not args.clang: parser.error("Clang is required; missing capabilities cannot be skipped")
    selected = Path(shutil.which(args.clang) or args.clang).absolute()
    clang = selected.resolve(strict=True)
    if clang.name.lower() in ("cl", "cl.exe", "clang-cl", "clang-cl.exe"): parser.error("use the Clang C driver for O0/O2/O3")
    directory = args.work.resolve()
    if directory.is_relative_to(ROOT): parser.error("--work must be outside the repository")
    directory.mkdir(parents=True, exist_ok=True)
    if any(directory.iterdir()): parser.error("--work must be virgin; stale artifacts cannot satisfy the gate")
    report = {"complete": False, "scope": SCOPE, "platform": sys.platform, "sanitized": not args.plain,
              "source_hashes": source_hashes(), "compiler": {"selected": str(selected), "path": str(clang), "sha256": sha(clang)}, "matrices": []}
    path = directory / "report.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    support = None
    try:
        frozen = directory / "frozen-source"
        for name, digest in report["source_hashes"].items():
            target = frozen / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / name).read_bytes())
            require(sha(target) == digest, "source changed during freeze")
        support = load_support(frozen)
        data = load_vectors(frozen / "tests/v4_fs_read_bridge_vectors.json")
        with sanitizer_environment(support, not args.plain):
            pins = run_gate(clang, directory, report, not args.plain, support, data)
        pins.final_pins()
        candidate = dict(report, complete=True)
        validate_report(candidate, data, not args.plain)
        pending = directory / "report.pending.json"
        pending.write_text(json.dumps(candidate, indent=2) + "\n")
        pins.check()
        os.replace(pending, path)
        pins.check()
        report["complete"] = True
    except BaseException as primary:
        try:
            if support is not None:
                evidence = support._Evidence()
                evidence.attempt("fs-failure-attribution", lambda: report.update(complete=False, failure=support.exception_descriptor(primary)))
                evidence.attempt("fs-failure-publication", lambda: path.write_text(json.dumps(report, indent=2) + "\n"))
                evidence.attach(primary)
            else:
                # Before support loading the live report is already false.
                # Do not put a fallible attribution before its publication.
                path.write_text(json.dumps(report, indent=2) + "\n")
        except BaseException:
            pass
        raise
    print("FS_READ_BRIDGE_PREREQUISITE_PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
