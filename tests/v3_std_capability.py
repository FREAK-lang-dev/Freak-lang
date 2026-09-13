#!/usr/bin/env python3
"""Reject an older same-ABI std payload before codegen or cached execution."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import v3_word_foundation as foundation


@contextmanager
def damaged_marker(marker: Path, kind: str):
    """Own and restore a nonregular or genuinely unreadable marker fixture."""
    saved = marker.read_bytes()
    original_mode = marker.stat().st_mode
    handle = None
    if kind == "directory":
        marker.unlink()
        marker.mkdir()
    elif sys.platform == "win32":
        import ctypes.wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateFileW.argtypes = [ctypes.wintypes.LPCWSTR, ctypes.wintypes.DWORD,
                                       ctypes.wintypes.DWORD, ctypes.c_void_p,
                                       ctypes.wintypes.DWORD, ctypes.wintypes.DWORD,
                                       ctypes.wintypes.HANDLE]
        kernel32.CreateFileW.restype = ctypes.wintypes.HANDLE
        kernel32.CloseHandle.argtypes = [ctypes.wintypes.HANDLE]
        kernel32.CloseHandle.restype = ctypes.wintypes.BOOL
        # Deny readers while allowing replacement by the mocked repair. The
        # handle remains on the old file after repair unlinks/replaces its name.
        handle = kernel32.CreateFileW(str(marker), 0x80000000, 0x2 | 0x4, None, 3, 0, None)
        assert handle != ctypes.c_void_p(-1).value, ctypes.WinError(ctypes.get_last_error())
    else:
        marker.chmod(0)
    try:
        if kind != "directory":
            try:
                marker.read_bytes()
            except OSError:
                pass  # Required positive control: this process cannot read it.
            else:
                assert sys.platform != "win32", "share lock did not deny reads"
                print("SKIP unreadable marker: privileged POSIX user bypasses file permissions")
                yield False
                return
        yield True
    finally:
        if handle is not None:
            assert kernel32.CloseHandle(handle), ctypes.WinError(ctypes.get_last_error())
        if marker.is_dir():
            marker.rmdir()
        elif marker.exists():
            marker.chmod(original_mode)
        marker.write_bytes(saved)
        marker.chmod(original_mode)


def check_marker_decoder(repo: Path, root: Path, invoke) -> None:
    """Exercise the actual reader's decoder, including failed transport frames."""
    implementation = (repo / "src/cli/build.fk").read_text(encoding="utf-8")
    helpers = implementation[implementation.index("task cli_std_marker_path_hex("):
                             implementation.index("task cli_payload_std_api_value(")]
    token = b"freak-v3-std-api-1"
    frame = lambda data: "FREAK_STD_HEX:" + data.hex() + ":END"
    cases = [
        (frame(token), token.decode()),
        (frame(b" \t" + token + b"\r\n"), token.decode()),
        (frame(b""), "unreadable"),
        ("", "unreadable"),
        ("FREAK_STD_UNREADABLE", "unreadable"),
        (frame(token)[:-1], "invalid-marker"),
        (frame(token) + "extra", "invalid-marker"),
        ("FREAK_STD_HEX:6:END", "invalid-marker"),
        ("FREAK_STD_HEX:6 1:END", "invalid-marker"),
        ("FREAK_STD_HEX:GG:END", "invalid-marker"),
        ("FREAK_STD_HEX:61 \n62\t43:END", "abC"),
        (frame(token + b"\tinside"), "invalid-marker"),
        (frame(token + b"\ninside"), "invalid-marker"),
        (frame(b"x" * 4096), "x" * 4096),
        (frame(b"x" * 4097), "oversized-marker"),
        (frame(b"x" * 8210), "oversized-marker"),
    ]
    # Every byte is classified after transport decoding, not just the byte
    # patterns that triggered the original Windows Ctrl-Z regression.
    for byte in range(256):
        data = token + bytes([byte]) + b"end"
        expected = data.decode("ascii") if 32 <= byte <= 126 else "invalid-marker"
        cases.append((frame(data), expected))
    program = helpers + "\ntask main() {\n"
    for encoded, _ in cases:
        program += "say cli_std_marker_decode(" + json.dumps(encoded) + ")\n"
    program += 'say cli_std_marker_path_hex("path %HOME% & quote \' ")\n}\n'
    source = root / "marker_decoder.fk"
    source.write_text(program, encoding="utf-8")
    for backend in ("--c", "--llvm"):
        built = invoke("build", str(source), backend)
        assert built.returncode == 0, built.stdout + built.stderr
        binary = source.with_suffix(".exe" if sys.platform == "win32" else "")
        run = subprocess.run([str(binary)], cwd=root, capture_output=True,
                             text=True, encoding="utf-8", timeout=30)
        assert run.returncode == 0, run.stdout + run.stderr
        assert run.stdout.splitlines() == [value for _, value in cases] + [
            b"path %HOME% & quote ' ".hex()], run.stdout + run.stderr
    print("PASS C/LLVM exact marker decoder: framing, all 256 bytes, path encoding, 4096-byte bound")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("freak", nargs="?", type=Path)
    parser.add_argument("--runtime-root", type=Path)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    runtime = args.runtime_root.resolve() if args.runtime_root else repo / "freakc/runtime"
    clang = os.environ.get("FREAK_CLANG") or shutil.which("clang")
    assert clang, "Clang is required"
    with tempfile.TemporaryDirectory(prefix="freak-v3-std-capability-") as temporary:
        root = Path(temporary)
        freak = args.freak.resolve() if args.freak else foundation.build_fresh_cli(
            clang=clang, repo=repo, root=root, runtime_root=runtime)
        payload_name = "selected %FREAK_STD_DECOY% & quote ' payload"
        if sys.platform != "win32":
            # POSIX paths additionally exercise Unicode and shell substitution.
            # Windows narrow filesystem APIs currently reject non-ASCII roots
            # before this marker reader, at the existing ABI gate.
            payload_name += " Ω $(touch FREAK_STD_INJECTED)"
        payload = root / payload_name
        shutil.copytree(runtime, payload / "runtime")
        shutil.copytree(repo / "std", payload / "std")
        marker = payload / "std/freak_std_api"
        expected = marker.read_bytes()
        expected_text = expected.decode("utf-8").strip()
        env = os.environ.copy()
        env.update(FREAK_HOME=str(payload), FREAK_CLANG=clang, NO_COLOR="1",
                   FREAK_STD_DECOY="must-not-expand-to-another-payload")

        def invoke(*arguments: str) -> subprocess.CompletedProcess[str]:
            result = subprocess.run([str(freak), *arguments], cwd=root, env=env,
                                    capture_output=True, text=True, encoding="utf-8",
                                    errors="replace", timeout=240)
            assert not (root / "FREAK_STD_INJECTED").exists(), "payload path reached shell execution"
            return result

        fix = root / ("fix.ps1" if sys.platform == "win32" else "fix.sh")
        no_op_repair = ("param([switch]$Upgrade,[switch]$SkipDeps)\nexit 0\n"
                        if sys.platform == "win32" else "#!/bin/sh\nexit 0\n")
        fix.write_text(no_op_repair, encoding="utf-8")
        if sys.platform != "win32":
            fix.chmod(0o755)
        env["FREAK_UPGRADE_SCRIPT"] = str(fix)

        check_marker_decoder(repo, root, invoke)
        for backend in ("--c", "--llvm"):
            warm = root / f"warm{backend}.fk"
            cold = root / f"cold{backend}.fk"
            warm.write_text('say "STD_API_EXECUTED"\n', encoding="utf-8")
            cold.write_text('say "STD_API_COLD_EXECUTED"\n', encoding="utf-8")
            binary = warm.with_suffix(".exe" if sys.platform == "win32" else "")
            proof = Path(str(binary) + ".freak-run-cache")
            for attempt in range(2):
                result = invoke("run", str(warm), backend)
                output = result.stdout + result.stderr
                assert result.returncode == 0 and "STD_API_EXECUTED" in output, output
                assert ("run cache hit" in output) == (attempt == 1), output
            saved = [(path.read_bytes(), path.stat().st_mtime_ns) for path in (binary, proof)]
            for invalid in (None, b"freak-v3-std-api-0\n", b"freak-v3-std-api-999\n"):
                if invalid is None:
                    marker.unlink()
                else:
                    marker.write_bytes(invalid)
                report = invoke("doctor", "--json")
                assert report.returncode != 0, report.stdout + report.stderr
                document = json.loads(report.stdout)
                assert document["status"] == "issues", document
                assert document["checks"]["abi"]["ok"] is True, document
                assert document["checks"]["runtime_api"]["ok"] is True, document
                assert document["checks"]["stdlib_api"] == {
                    "ok": False, "expected": expected_text,
                    "stdlib": "missing" if invalid is None else invalid.decode().strip(),
                }, document
                for operation in ("build", "run"):
                    rejected = invoke(operation, str(cold), backend)
                    output = rejected.stdout + rejected.stderr
                    assert rejected.returncode != 0, output
                    assert "stdlib api mismatch" in output.lower(), output
                    assert "STD_API_COLD_EXECUTED" not in output, output
                    assert list(root.glob(cold.name + ".*")) == [], list(root.iterdir())
                    assert not cold.with_suffix(".exe" if sys.platform == "win32" else "").exists()
                rejected = invoke("run", str(warm), backend)
                output = rejected.stdout + rejected.stderr
                assert rejected.returncode != 0 and "stdlib api mismatch" in output.lower(), output
                assert "STD_API_EXECUTED" not in output and "run cache hit" not in output, output
                assert [(path.read_bytes(), path.stat().st_mtime_ns) for path in (binary, proof)] == saved
                marker.write_bytes(expected)
                recovered = invoke("run", str(warm), backend)
                assert recovered.returncode == 0 and "run cache hit" in recovered.stdout, recovered.stdout + recovered.stderr
                assert [(path.read_bytes(), path.stat().st_mtime_ns) for path in (binary, proof)] == saved
            for kind in ("directory", "unreadable"):
                with damaged_marker(marker, kind) as active:
                    if not active:
                        continue
                    report = invoke("doctor", "--json")
                    assert report.returncode != 0, report.stdout + report.stderr
                    document = json.loads(report.stdout)
                    assert document["checks"]["stdlib_api"] == {
                        "ok": False, "expected": expected_text, "stdlib": "unreadable",
                    }, document
                    for operation in ("build", "run"):
                        rejected = invoke(operation, str(cold), backend)
                        output = rejected.stdout + rejected.stderr
                        assert rejected.returncode != 0 and "stdlib api mismatch" in output.lower(), output
                        assert "STD_API_COLD_EXECUTED" not in output, output
                        assert list(root.glob(cold.name + ".*")) == []
                        assert not cold.with_suffix(".exe" if sys.platform == "win32" else "").exists()
                    rejected = invoke("run", str(warm), backend)
                    output = rejected.stdout + rejected.stderr
                    assert rejected.returncode != 0 and "stdlib api mismatch" in output.lower(), output
                    assert "STD_API_EXECUTED" not in output and "run cache hit" not in output, output
                    assert [(path.read_bytes(), path.stat().st_mtime_ns) for path in (binary, proof)] == saved
                    for doctor_arguments in (("doctor",), ("doctor", "--fix")):
                        rejected = invoke(*doctor_arguments)
                        output = rejected.stdout + rejected.stderr
                        assert rejected.returncode != 0 and "Stdlib API mismatch" in output, output
                        assert "compile, link, and execution work" not in output, output
                        if "--fix" in doctor_arguments:
                            assert "Repairing the compiler/runtime/stdlib payload" in output, output
                recovered = invoke("run", str(warm), backend)
                assert recovered.returncode == 0 and "run cache hit" in recovered.stdout, recovered.stdout + recovered.stderr
                assert [(path.read_bytes(), path.stat().st_mtime_ns) for path in (binary, proof)] == saved
            token = expected_text.encode("ascii")
            malformed = []
            for control in (b"\x00", b"\x01", b"\x1a", b"\x1f", b"\x7f", b"\xff"):
                for position in (0, len(token) // 2, len(token)):
                    malformed.append((token[:position] + control + token[position:], "invalid-marker"))
            malformed.extend([(b"", "unreadable"),
                              (token + b" " * (4097 - len(token)), "oversized-marker"),
                              (token + b"\x1a" + b"x" * (1024 * 1024), "oversized-marker")])
            for data, diagnostic in malformed:
                marker.write_bytes(data)
                report = invoke("doctor", "--json")
                assert report.returncode != 0, report.stdout + report.stderr
                document = json.loads(report.stdout)
                assert document["checks"]["stdlib_api"] == {
                    "ok": False, "expected": expected_text, "stdlib": diagnostic,
                }, document
                for operation in ("build", "run"):
                    rejected = invoke(operation, str(cold), backend)
                    output = rejected.stdout + rejected.stderr
                    assert rejected.returncode != 0 and "stdlib api mismatch" in output.lower(), output
                    assert "STD_API_COLD_EXECUTED" not in output, output
                    assert list(root.glob(cold.name + ".*")) == []
                    assert not cold.with_suffix(".exe" if sys.platform == "win32" else "").exists()
                rejected = invoke("run", str(warm), backend)
                output = rejected.stdout + rejected.stderr
                assert rejected.returncode != 0 and "stdlib api mismatch" in output.lower(), output
                assert "STD_API_EXECUTED" not in output and "run cache hit" not in output, output
                ineffective = invoke("doctor", "--fix")
                output = ineffective.stdout + ineffective.stderr
                assert ineffective.returncode != 0 and "Stdlib API mismatch" in output, output
                assert "Repairing the compiler/runtime/stdlib payload" in output, output
                assert "compile, link, and execution work" not in output, output
                assert marker.read_bytes() == data
                assert [(path.read_bytes(), path.stat().st_mtime_ns) for path in (binary, proof)] == saved
            # The limit is inclusive; ordinary edge whitespace remains valid.
            marker.write_bytes(token + b" " * (4096 - len(token)))
            recovered = invoke("run", str(warm), backend)
            assert recovered.returncode == 0 and "run cache hit" in recovered.stdout, recovered.stdout + recovered.stderr
            assert [(path.read_bytes(), path.stat().st_mtime_ns) for path in (binary, proof)] == saved
            marker.write_bytes(expected)
            print(f"PASS {backend} binary marker rejection/JSON/no-op repair/cache preservation")
        print("PASS C/LLVM cold build/run and warm-cache std API rejection/recovery; layout ABI unchanged")

        # Doctor --fix must detect an incompatible present marker as well as
        # a missing file, invoke the existing upgrade route, and re-read it.
        if sys.platform == "win32":
            fix.write_text("param([switch]$Upgrade,[switch]$SkipDeps)\n"
                           "$marker = Join-Path $env:FREAK_HOME 'std/freak_std_api'\n"
                           "Remove-Item -LiteralPath $marker -Force -ErrorAction Stop\n"
                           "[IO.File]::WriteAllText($marker, "
                           f"'{expected_text}')\nexit 0\n", encoding="utf-8")
        else:
            fix.write_text("#!/bin/sh\nset -eu\n"
                           'marker="$FREAK_HOME/std/freak_std_api"\n'
                           'if [ -d "$marker" ]; then rmdir "$marker"; else rm -f "$marker"; fi\n'
                           f"printf '%s\\n' '{expected_text}' > \"$FREAK_HOME/std/freak_std_api\"\n",
                           encoding="utf-8")
            fix.chmod(0o755)
        marker.write_text("freak-v3-std-api-0\n", encoding="utf-8")
        env["FREAK_UPGRADE_SCRIPT"] = str(fix)
        fixed = invoke("doctor", "--fix")
        output = fixed.stdout + fixed.stderr
        assert fixed.returncode == 0, output
        assert "Repairing the compiler/runtime/stdlib payload" in output, output
        assert "compile, link, and execution work" in output, output
        assert marker.read_text(encoding="utf-8").strip() == expected_text
        report = invoke("doctor", "--json")
        assert report.returncode == 0, report.stdout + report.stderr
        assert json.loads(report.stdout)["checks"]["stdlib_api"]["ok"] is True
        print("PASS Doctor std API repair and full pipeline recovery")

        for kind in ("directory", "unreadable"):
            with damaged_marker(marker, kind) as active:
                if not active:
                    continue
                fixed = invoke("doctor", "--fix")
                output = fixed.stdout + fixed.stderr
                assert fixed.returncode == 0, output
                assert "Repairing the compiler/runtime/stdlib payload" in output, output
                assert "compile, link, and execution work" in output, output
                assert marker.read_text(encoding="utf-8").strip() == expected_text
                report = invoke("doctor", "--json")
                assert report.returncode == 0, report.stdout + report.stderr
                assert json.loads(report.stdout)["checks"]["stdlib_api"]["ok"] is True
        print("PASS nonregular/unreadable marker repair and hostile literal payload paths")

        marker.write_text("freak-v3-std-api-0\n", encoding="utf-8")
        fix.write_text("param([switch]$Upgrade,[switch]$SkipDeps)\nexit 0\n"
                       if sys.platform == "win32" else "#!/bin/sh\nexit 0\n",
                       encoding="utf-8")
        ineffective = invoke("doctor", "--fix")
        output = ineffective.stdout + ineffective.stderr
        assert ineffective.returncode != 0, output
        assert "Stdlib API mismatch" in output, output
        assert "compile, link, and execution work" not in output, output
        assert marker.read_text(encoding="utf-8").strip() == "freak-v3-std-api-0"
        print("PASS ineffective std API repair remains fail-closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
