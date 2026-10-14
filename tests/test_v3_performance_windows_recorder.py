#!/usr/bin/env python3
"""Check canonical Windows recorder construction and native forwarding.

Pure controls run on every host. Native PE rebuilding and forwarding controls
run only on Windows; a non-Windows run makes no native Windows claim.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile
from typing import Any, Callable
from unittest.mock import patch


def _reject(lab: Any, action: Callable[[], Any], diagnostic: str) -> None:
    try:
        action()
    except lab.LabError as error:
        assert diagnostic in str(error), (diagnostic, str(error))
    else:
        raise AssertionError(f"accepted invalid recorder evidence: {diagnostic}")


def static_checks(lab: Any) -> None:
    python = r'C:\Python space\python.exe'
    recorder = 'C:\\recorder space 日本語 😀 %NAME% &\\record_clang.py'
    source = lab._windows_recording_launcher_source(python, recorder)
    assert source.isascii()
    text = source.decode("ascii")
    for name, expected in (("python_executable", python), ("recorder_path", recorder)):
        match = re.search(rf"static wchar_t {name}\[\]=\{{([^}}]+)\}};", text)
        assert match
        units = [int(unit, 16) for unit in match.group(1).split(",")]
        assert units[-1] == 0
        raw = b"".join(unit.to_bytes(2, "little") for unit in units[:-1])
        assert raw.decode("utf-16-le") == expected
    assert "CreateProcessW(executable,line" in text
    assert "STARTF_USESTDHANDLES" in text
    assert "GetExitCodeProcess(child.hProcess,&exit_code)" in text
    assert "cmd.exe" not in text and "_wspawnv" not in text and "system(" not in text
    _reject(lab, lambda: lab._windows_recording_launcher_source("bad\0path", recorder), "contains NUL")
    _reject(lab, lambda: lab._windows_recording_launcher_source("bad\ud800path", recorder), "not valid Unicode")
    clang = Path(sys.executable).resolve(strict=True)
    msvc = lab._windows_recording_launcher_command(clang, "x86_64-pc-windows-msvc")
    mingw = lab._windows_recording_launcher_command(clang, "x86_64-w64-windows-gnu")
    assert "-Wl,/Brepro" in msvc and "-Wl,--no-insert-timestamp" in mingw
    assert "-fuse-ld=lld" in msvc and "-fuse-ld=lld" in mingw
    assert msvc[-4:] == ["record_clang_launcher.c", "-o", "record-clang.exe", "-lshell32"]
    _reject(lab, lambda: lab._windows_recording_launcher_command(clang, "x86_64-linux-gnu"), "requires a Windows Clang target")
    _reject(lab, lambda: lab._recording_wrapper_bytes("windows-cmd", python, recorder, ""), "unknown recording wrapper kind")

    # Exercise the admission checks without claiming that mock bytes are a PE.
    compiler = {"path": str(clang), "sha256": "1" * 64, "bytes": 10, "version": "mock", "target_triple": "x86_64-pc-windows-msvc"}
    command = lab._windows_recording_launcher_command(clang, compiler["target_triple"])
    wrapper = b"mock canonical executable bytes"
    build = {
        "compiler": compiler, "command": command, "command_sha256": lab._json_sha256(command),
        "stdout_raw_base64": lab._encode_bytes(b""), "stdout_sha256": lab._sha256_bytes(b""),
        "stderr_raw_base64": lab._encode_bytes(b""), "stderr_sha256": lab._sha256_bytes(b""),
        "linker": {},
    }
    identity = {
        "launcher_source_content_base64": lab._encode_bytes(source),
        "launcher_source_sha256": lab._sha256_bytes(source),
        "launcher_build": build, "wrapper_sha256": lab._sha256_bytes(wrapper),
    }
    def validate_trace_source(_value: Any, _context: str, _clang: Path, arguments: list[str], *_rest: Any) -> None:
        inputs = [Path(argument) for argument in arguments if argument.endswith("record_clang_launcher.c")]
        assert len(inputs) == 1 and inputs[0].is_absolute() and inputs[0].read_bytes() == source

    with patch.object(lab, "_tool_identity", return_value=compiler), patch.object(
        lab, "_validate_linker_identity", side_effect=validate_trace_source,
    ), patch.object(lab, "_build_windows_recording_launcher", return_value=(source, wrapper, build)):
        lab._validate_windows_recording_launcher(identity, wrapper, python, recorder, "control")
        forged_wrapper = b"different executable with coherent supplied hash"
        forged = copy.deepcopy(identity)
        forged["wrapper_sha256"] = lab._sha256_bytes(forged_wrapper)
        _reject(lab, lambda: lab._validate_windows_recording_launcher(forged, forged_wrapper, python, recorder, "control"), "differs from the canonical source rebuild")
        wrong_source = copy.deepcopy(identity)
        wrong_source["launcher_source_content_base64"] = lab._encode_bytes(source + b"\n")
        wrong_source["launcher_source_sha256"] = lab._sha256_bytes(source + b"\n")
        _reject(lab, lambda: lab._validate_windows_recording_launcher(wrong_source, wrapper, python, recorder, "control"), "source is not canonical")
        wrong_command = copy.deepcopy(identity)
        wrong_command["launcher_build"]["command"].append("-DUNREVIEWED=1")
        wrong_command["launcher_build"]["command_sha256"] = lab._json_sha256(wrong_command["launcher_build"]["command"])
        _reject(lab, lambda: lab._validate_windows_recording_launcher(wrong_command, wrapper, python, recorder, "control"), "command is not canonical")
        wrong_compiler = copy.deepcopy(identity)
        wrong_compiler["launcher_build"]["compiler"]["sha256"] = "2" * 64
        _reject(lab, lambda: lab._validate_windows_recording_launcher(wrong_compiler, wrapper, python, recorder, "control"), "compiler identity is stale")
        wrong_capture = copy.deepcopy(identity)
        wrong_capture["launcher_build"]["stderr_sha256"] = "0" * 64
        _reject(lab, lambda: lab._validate_windows_recording_launcher(wrong_capture, wrapper, python, recorder, "control"), "stderr checksum is invalid")


def native_checks(lab: Any, temporary: Path, clang: Path) -> None:
    if sys.platform != "win32":
        raise AssertionError("native Windows recorder controls require Windows")
    directory = temporary / "recorder space 日本語 😀 %NAME% &"
    directory.mkdir()
    wrapper, log, identity = lab._write_recording_clang(directory, clang)
    assert identity["kind"] == "windows-native" and wrapper.name == "record-clang.exe"
    assert lab._rehash_recording_files(identity, "native control before") == identity["combined_sha256"]
    environment = lab._clean_environment(clang)
    environment.update({
        "FREAK_PERF_REAL_CLANG": str(clang), "FREAK_PERF_CLANG_LOG": str(log),
        "FREAK_RECORDER_EXPANSION": "must stay literal",
    })
    real_version = lab._run_bytes([str(clang), "--version"], cwd=directory, environment=environment, timeout=30.0)
    recorded_version = lab._run_bytes([str(wrapper), "--version"], cwd=directory, environment=environment, timeout=30.0)
    assert recorded_version.returncode == real_version.returncode == 0
    assert recorded_version.stdout == real_version.stdout and recorded_version.stderr == real_version.stderr
    records = lab._read_recording_log(log)
    assert len(records) == 1 and records[0]["argv"] == ["--version"] and records[0]["exit_code"] == 0
    log.unlink()

    values = ["", "path with spaces", "日本語😀", 'literal"quote', "trailing\\\\", "%FREAK_RECORDER_EXPANSION%", "&|<>^!", 'backslashes\\\\\\"quoted']
    observer = (
        "import json,os,sys;"
        "os.write(1,json.dumps(sys.argv[1:],ensure_ascii=False,separators=(',',':')).encode('utf-8'));"
        "os.write(2,b'perf-recorder-stderr\\xff');sys.exit(7)"
    )
    arguments = ["-c", observer, *values]
    environment["FREAK_PERF_REAL_CLANG"] = str(Path(sys.executable).resolve(strict=True))
    completed = lab._run_bytes([str(wrapper), *arguments], cwd=directory, environment=environment, timeout=30.0)
    assert completed.returncode == 7
    assert completed.stdout == json.dumps(values, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    assert completed.stderr == b"perf-recorder-stderr\xff"
    records = lab._read_recording_log(log)
    assert len(records) == 1 and records[0]["argv"] == arguments and records[0]["exit_code"] == 7
    assert lab._rehash_recording_files(identity, "native control after") == identity["combined_sha256"]

    # Observe the launcher's complete DWORD child status independently of the
    # canonical recorder's Python SystemExit behavior for unusually large codes.
    recorder = Path(identity["recorder_path"])
    canonical_recorder = recorder.read_bytes()
    try:
        for code in (0x80000037, 0xFFFFFFFF):
            recorder.write_text(f"import ctypes\nctypes.WinDLL('kernel32').ExitProcess({code})\n", encoding="ascii")
            status = lab._run_bytes([str(wrapper)], cwd=directory, environment=environment, timeout=30.0)
            assert status.returncode == code and status.stdout == status.stderr == b""
    finally:
        recorder.write_bytes(canonical_recorder)
    assert lab._rehash_recording_files(identity, "native DWORD control restored") == identity["combined_sha256"]
    lab._validate_recording_identity(identity, "native control")

    # A coherent hash replacement must still fail exact source-to-PE rebuilding.
    forged = copy.deepcopy(identity)
    altered = bytearray(lab._decode_bytes(forged["wrapper_content_base64"], "native wrapper"))
    altered[-1] ^= 1
    forged["wrapper_content_base64"] = lab._encode_bytes(bytes(altered))
    forged["wrapper_sha256"] = lab._sha256_bytes(bytes(altered))
    forged["combined_sha256"] = lab._recording_identity_digest(forged)
    _reject(lab, lambda: lab._validate_recording_identity(forged, "native control"), "differs from the canonical source rebuild")
    source_path = wrapper.with_name("record_clang_launcher.c")
    canonical_source = source_path.read_bytes()
    source_path.write_bytes(canonical_source + b"\n")
    _reject(lab, lambda: lab._rehash_recording_files(identity, "native source tamper"), "launcher source changed")
    source_path.write_bytes(canonical_source)
    assert lab._rehash_recording_files(identity, "native source restored") == identity["combined_sha256"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clang", help="exact Clang executable for native Windows controls")
    args = parser.parse_args()
    path = Path(__file__).resolve().parents[1] / "tools" / "v3_performance_lab.py"
    specification = importlib.util.spec_from_file_location("recorder_control_lab", path)
    assert specification is not None and specification.loader is not None
    lab = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(lab)
    static_checks(lab)
    if sys.platform == "win32":
        with tempfile.TemporaryDirectory(prefix="freak-v3-recorder-controls-") as temporary:
            native_checks(lab, Path(temporary).resolve(), lab._resolve_clang(args.clang))
    print("Windows recorder controls passed (" + ("native + pure" if sys.platform == "win32" else "pure; native Windows pending") + ")")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
