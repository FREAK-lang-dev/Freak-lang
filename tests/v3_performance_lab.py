#!/usr/bin/env python3
"""Static and executable acceptance checks for the V3 performance lab."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Callable
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "v3_performance_lab.py"
MANIFEST = ROOT / "benchmarks" / "v3" / "manifest.json"


def _load_tool() -> Any:
    specification = importlib.util.spec_from_file_location("freak_v3_performance_lab", TOOL)
    if specification is None or specification.loader is None:
        raise AssertionError(f"cannot import {TOOL}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


LAB = _load_tool()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _expect_lab_error(
    action: Callable[[], Any],
    message: str,
    expected_diagnostic: str | None = None,
) -> str:
    try:
        action()
    except LAB.LabError as error:
        diagnostic = str(error)
        if expected_diagnostic is not None and expected_diagnostic not in diagnostic:
            raise AssertionError(
                f"{message}: expected diagnostic {expected_diagnostic!r}, got {diagnostic!r}"
            ) from error
        return diagnostic
    raise AssertionError(message)


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _process_is_running(pid: int) -> bool:
    if sys.platform == "win32":
        import ctypes.wintypes

        wintypes = ctypes.wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel32.WaitForSingleObject.restype = wintypes.DWORD
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL
        handle = kernel32.OpenProcess(0x00100000, False, pid)  # SYNCHRONIZE
        if not handle:
            error = ctypes.get_last_error()
            if error == 5:  # ERROR_ACCESS_DENIED still proves that the PID exists.
                return True
            if error == 87:  # ERROR_INVALID_PARAMETER for a PID that no longer exists.
                return False
            raise ctypes.WinError(error)
        try:
            return kernel32.WaitForSingleObject(handle, 0) == 0x00000102  # WAIT_TIMEOUT
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    if sys.platform.startswith("linux"):
        # kill(pid, 0) also succeeds for an exited, unreaped child. A zombie
        # cannot execute or escape containment; waiting for an unrelated PID 1
        # to reap it makes the oracle fail spuriously in Linux containers.
        try:
            with open(f"/proc/{pid}/stat", "rb") as status_file:
                status = status_file.read(4097)
        except OSError:
            # Includes exit/reap races and restricted or unavailable procfs.
            # Keep the successful kill probe authoritative until the next poll.
            return True
        if len(status) > 4096 or not status.endswith(b"\n"):
            return True
        prefix = f"{pid} (".encode("ascii")
        name, separator, fields = status.rpartition(b") ")
        # comm is unescaped and may itself contain spaces, ')' or newlines.
        # Only the final delimiter precedes the state and numeric stat fields.
        # Require fields through starttime, not a truncated state-only record.
        values = fields.split()
        if (separator and name.startswith(prefix) and len(values) >= 20
                and values[0] == b"Z"
                and all(value.removeprefix(b"-").isdigit() for value in values[1:])):
            return False
    # Other POSIX hosts retain the conservative kill-only oracle: no procfs
    # assumption and no additional external ps process in every polling step.
    return True


def _assert_pid_stopped(pid: int, context: str) -> None:
    deadline = time.monotonic() + 5.0
    while _process_is_running(pid) and time.monotonic() < deadline:
        time.sleep(0.05)
    assert not _process_is_running(pid), f"{context}: process {pid} survived containment cleanup"


def _assert_descendant_stopped(pid_path: Path, ready_path: Path, context: str) -> None:
    if not pid_path.is_file():
        raise AssertionError(f"{context}: launcher did not publish the descendant PID")
    if not ready_path.is_file():
        raise AssertionError(f"{context}: descendant did not publish its ready marker")
    pid = int(pid_path.read_text(encoding="ascii"))
    _assert_pid_stopped(pid, context)


def _descendant_launcher(
    pid_path: Path,
    ready_path: Path,
    action: str,
    *,
    detached: bool = False,
    child_sleep: float = 60.0,
) -> list[str]:
    child_code = (
        "import os, sys, time\n"
        "from pathlib import Path\n"
        "Path(sys.argv[1]).write_text(str(os.getpid()), encoding='ascii')\n"
        "Path(sys.argv[2]).write_text('ready', encoding='ascii')\n"
        f"time.sleep({child_sleep!r})\n"
    )
    detached_option = ", start_new_session=True" if detached else ""
    launcher_code = (
        "import subprocess, sys, time\n"
        "from pathlib import Path\n"
        f"child = subprocess.Popen([sys.executable, '-c', {child_code!r}, sys.argv[1], sys.argv[2]]"
        f"{detached_option})\n"
        "deadline = time.monotonic() + 5.0\n"
        "while not Path(sys.argv[2]).is_file():\n"
        "    if child.poll() is not None:\n"
        "        raise SystemExit('descendant exited before publishing ready')\n"
        "    if time.monotonic() >= deadline:\n"
        "        raise SystemExit('descendant readiness timed out')\n"
        "    time.sleep(0.01)\n"
        f"{action}\n"
    )
    return [sys.executable, "-c", launcher_code, str(pid_path), str(ready_path)]


def _resource_handle_count() -> int | None:
    if sys.platform == "win32":
        import ctypes.wintypes

        wintypes = ctypes.wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        kernel32.GetProcessHandleCount.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel32.GetProcessHandleCount.restype = wintypes.BOOL
        count = wintypes.DWORD()
        if not kernel32.GetProcessHandleCount(kernel32.GetCurrentProcess(), ctypes.byref(count)):
            raise ctypes.WinError(ctypes.get_last_error())
        return int(count.value)
    fd_root = Path("/proc/self/fd")
    return len(list(fd_root.iterdir())) if fd_root.is_dir() else None


def _assert_no_capture_threads(context: str) -> None:
    active = [
        thread.name
        for thread in threading.enumerate()
        if thread.name.startswith("freak-v3-capture-")
    ]
    assert not active, f"{context}: capture threads leaked: {active}"


def _process_tree_checks(temporary: Path) -> None:
    expected_capture = b"capture-drain" * 8192
    captured = LAB._run_bytes(
        [
            sys.executable,
            "-c",
            "import sys; sys.stdout.buffer.write(b'capture-drain' * 8192); sys.stdout.buffer.flush()",
        ],
        cwd=temporary,
        environment=os.environ,
        timeout=5.0,
    )
    assert captured.returncode == 0
    assert captured.stdout == expected_capture and captured.stderr == b""
    _assert_no_capture_threads("capture drain warmup")
    baseline_handles = _resource_handle_count()

    exit_pid = temporary / "exit-descendant.pid"
    exit_ready = temporary / "exit-descendant.ready"
    completed = LAB._run_bytes(
        _descendant_launcher(exit_pid, exit_ready, "raise SystemExit(0)"),
        cwd=temporary,
        environment=os.environ,
        timeout=5.0,
    )
    assert completed.returncode == 0
    _assert_descendant_stopped(exit_pid, exit_ready, "normal launcher exit")

    timeout_pid = temporary / "timeout-descendant.pid"
    timeout_ready = temporary / "timeout-descendant.ready"
    _expect_lab_error(
        lambda: LAB._run_bytes(
            _descendant_launcher(timeout_pid, timeout_ready, "time.sleep(60)"),
            cwd=temporary,
            environment=os.environ,
            timeout=1.0,
        ),
        "timed-out launcher left its process tree running",
        "timed out after",
    )
    _assert_descendant_stopped(timeout_pid, timeout_ready, "launcher timeout")

    overflow_pid = temporary / "overflow-descendant.pid"
    overflow_ready = temporary / "overflow-descendant.ready"
    old_capture_bound = LAB.MAX_CAPTURE_BYTES
    LAB.MAX_CAPTURE_BYTES = 32
    try:
        _expect_lab_error(
            lambda: LAB._run_bytes(
                _descendant_launcher(
                    overflow_pid,
                    overflow_ready,
                    "sys.stdout.write('x' * (128 * 1024)); sys.stdout.flush(); time.sleep(60)",
                ),
                cwd=temporary,
                environment=os.environ,
                timeout=5.0,
            ),
            "overflowing launcher left its process tree running",
            "command output exceeds",
        )
    finally:
        LAB.MAX_CAPTURE_BYTES = old_capture_bound
    _assert_descendant_stopped(overflow_pid, overflow_ready, "launcher output overflow")

    if sys.platform == "win32":
        import msvcrt

        sentinel_path = temporary / "must-not-inherit.handle"
        sentinel_path.write_bytes(b"sentinel\n")
        handle_probe = (
            "import ctypes, os, sys\n"
            "from ctypes import wintypes\n"
            "kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)\n"
            "kernel32.GetFinalPathNameByHandleW.argtypes = "
            "[wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD]\n"
            "kernel32.GetFinalPathNameByHandleW.restype = wintypes.DWORD\n"
            "buffer = ctypes.create_unicode_buffer(32768)\n"
            "ctypes.set_last_error(0)\n"
            "length = kernel32.GetFinalPathNameByHandleW("
            "wintypes.HANDLE(int(sys.argv[1])), buffer, len(buffer), 0)\n"
            "def normalize(path):\n"
            "    if path.startswith('\\\\\\\\?\\\\UNC\\\\'):\n"
            "        path = '\\\\\\\\' + path[8:]\n"
            "    elif path.startswith('\\\\\\\\?\\\\'):\n"
            "        path = path[4:]\n"
            "    return os.path.normcase(os.path.abspath(path))\n"
            "if length and length < len(buffer) and normalize(buffer.value) == normalize(sys.argv[2]):\n"
            "    print('sentinel file handle inherited', file=sys.stderr)\n"
            "    raise SystemExit(91)\n"
            "print('sentinel file handle excluded')\n"
        )
        for probe_index in range(16):
            sentinel_fd = os.open(sentinel_path, os.O_RDONLY | os.O_BINARY)
            os.set_inheritable(sentinel_fd, True)
            sentinel_handle = msvcrt.get_osfhandle(sentinel_fd)
            try:
                if probe_index == 0:
                    inherited_result = subprocess.run(
                        [sys.executable, "-c", handle_probe, str(sentinel_handle), str(sentinel_path.resolve())],
                        cwd=temporary,
                        env=os.environ,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=5.0,
                        close_fds=False,
                        check=False,
                    )
                    assert inherited_result.returncode == 91, (
                        b"identity oracle did not recognize the inherited sentinel: "
                        + inherited_result.stdout
                        + inherited_result.stderr
                    )
                handle_result = LAB._run_bytes(
                    [sys.executable, "-c", handle_probe, str(sentinel_handle), str(sentinel_path.resolve())],
                    cwd=temporary,
                    environment=os.environ,
                    timeout=5.0,
                )
            finally:
                os.set_inheritable(sentinel_fd, False)
                os.close(sentinel_fd)
            assert handle_result.returncode == 0, (
                f"handle isolation probe {probe_index} failed: "
                + (handle_result.stdout + handle_result.stderr).decode(errors="replace")
            )
            assert handle_result.stdout.strip() == b"sentinel file handle excluded", handle_result.stdout

        assignment_pid: list[int] = []
        original_assign = LAB._WindowsJob.assign

        def reject_assignment(job: Any, process: Any) -> None:
            del job
            assignment_pid.append(process.pid)
            raise OSError("injected job assignment failure")

        LAB._WindowsJob.assign = reject_assignment
        try:
            never_pid = temporary / "assignment-failure-descendant.pid"
            never_ready = temporary / "assignment-failure-descendant.ready"
            _expect_lab_error(
                lambda: LAB._run_bytes(
                    _descendant_launcher(never_pid, never_ready, "time.sleep(60)"),
                    cwd=temporary,
                    environment=os.environ,
                    timeout=5.0,
                ),
                "job assignment failure allowed the suspended launcher to run",
                "cannot atomically enroll and resume Windows process",
            )
        finally:
            LAB._WindowsJob.assign = original_assign
        assert len(assignment_pid) == 1
        _assert_pid_stopped(assignment_pid[0], "job assignment failure")
        assert not never_pid.exists() and not never_ready.exists(), (
            "suspended launcher executed before successful Job Object enrollment"
        )

        resume_pid: list[int] = []
        original_resume = LAB._WindowsProcess.resume

        def reject_resume(process: Any) -> None:
            resume_pid.append(process.pid)
            raise OSError("injected primary thread resume failure")

        LAB._WindowsProcess.resume = reject_resume
        try:
            resume_never_pid = temporary / "resume-failure-descendant.pid"
            resume_never_ready = temporary / "resume-failure-descendant.ready"
            _expect_lab_error(
                lambda: LAB._run_bytes(
                    _descendant_launcher(
                        resume_never_pid,
                        resume_never_ready,
                        "time.sleep(60)",
                    ),
                    cwd=temporary,
                    environment=os.environ,
                    timeout=5.0,
                ),
                "primary thread resume failure left the enrolled launcher alive",
                "cannot atomically enroll and resume Windows process",
            )
        finally:
            LAB._WindowsProcess.resume = original_resume
        assert len(resume_pid) == 1
        _assert_pid_stopped(resume_pid[0], "primary thread resume failure")
        assert not resume_never_pid.exists() and not resume_never_ready.exists(), (
            "suspended launcher executed after failed primary-thread resume"
        )

    if sys.platform != "win32":
        detached_pid = temporary / "detached-descendant.pid"
        detached_ready = temporary / "detached-descendant.ready"
        _expect_lab_error(
            lambda: LAB._run_bytes(
                _descendant_launcher(
                    detached_pid,
                    detached_ready,
                    "raise SystemExit(0)",
                    detached=True,
                    child_sleep=4.0,
                ),
                cwd=temporary,
                environment=os.environ,
                timeout=5.0,
            ),
            "detectable detached POSIX descendant was accepted as contained",
            "POSIX toolchain descendants must not detach",
        )
        _assert_descendant_stopped(detached_pid, detached_ready, "detached-boundary control")

    def check_capture_start_failure(fail_at: int) -> None:
        launched_pids: list[int] = []
        original_start = LAB.threading.Thread.start
        capture_starts = 0
        original_create_descriptor: Any | None = None
        original_popen: Any | None = None

        if sys.platform == "win32":
            original_create_descriptor = LAB._WindowsProcess.__dict__["create_suspended"]
            original_create = LAB._WindowsProcess.create_suspended

            def tracked_create(
                cls: Any,
                command: list[str],
                cwd: Path,
                environment: dict[str, str],
            ) -> Any:
                del cls
                process = original_create(command, cwd, environment)
                launched_pids.append(process.pid)
                return process

            LAB._WindowsProcess.create_suspended = classmethod(tracked_create)
        else:
            original_popen = LAB.subprocess.Popen

            def tracked_popen(*args: Any, **kwargs: Any) -> Any:
                process = original_popen(*args, **kwargs)
                launched_pids.append(process.pid)
                return process

            LAB.subprocess.Popen = tracked_popen

        def injected_start(reader: Any) -> None:
            nonlocal capture_starts
            if reader.name.startswith("freak-v3-capture-"):
                capture_starts += 1
                if capture_starts == fail_at:
                    raise RuntimeError(f"injected capture reader start failure {fail_at}")
            original_start(reader)

        before_handles = _resource_handle_count()
        LAB.threading.Thread.start = injected_start
        try:
            diagnostic = _expect_lab_error(
                lambda: LAB._run_bytes(
                    [sys.executable, "-c", "import time; time.sleep(60)"],
                    cwd=temporary,
                    environment=os.environ,
                    timeout=5.0,
                ),
                f"capture reader {fail_at} start failure escaped cleanup",
                f"cannot start capture reader {fail_at - 1}: "
                f"injected capture reader start failure {fail_at}",
            )
        finally:
            LAB.threading.Thread.start = original_start
            if original_create_descriptor is not None:
                LAB._WindowsProcess.create_suspended = original_create_descriptor
            if original_popen is not None:
                LAB.subprocess.Popen = original_popen
        assert "cleanup failed" not in diagnostic, diagnostic
        assert len(launched_pids) == 1, launched_pids
        _assert_pid_stopped(launched_pids[0], f"capture reader {fail_at} start failure")
        _assert_no_capture_threads(f"capture reader {fail_at} start failure")
        after_handles = _resource_handle_count()
        if before_handles is not None and after_handles is not None:
            assert after_handles <= before_handles, (
                f"capture reader {fail_at} start failure leaked handles/fds: "
                f"{before_handles} -> {after_handles}"
            )

    check_capture_start_failure(1)
    check_capture_start_failure(2)

    for _ in range(8):
        completed = LAB._run_bytes(
            [sys.executable, "-c", "raise SystemExit(0)"],
            cwd=temporary,
            environment=os.environ,
            timeout=5.0,
        )
        assert completed.returncode == 0
    _assert_no_capture_threads("repeated process launch")
    final_handles = _resource_handle_count()
    if baseline_handles is not None and final_handles is not None:
        assert final_handles <= baseline_handles, (
            f"repeated process launch leaked handles/fds: {baseline_handles} -> {final_handles}"
        )


def _foundation_workload_checks(manifest: dict[str, Any]) -> None:
    """Pin workload sizes and independently derive quick content oracles."""
    cases = {case["id"]: case for case in manifest["cases"]}
    idiomatic = {"word_repeated_100m", "word_builder_known_capacity",
                 "word_builder_unknown_capacity", "bytes_copy_1gb"}
    algorithms = {
        **{name: "fnv1a64-low63" for name in idiomatic | {"word_dynamic_append_100m"}},
        "bytes_write_100m": "ordered-polynomial-131-mod-1000000007",
        "bytes_sequential_read": "int64-sum-modulo-pattern65521",
        "bytes_sequential_write": "int64-sum-modulo-pattern65521",
        "bytes_endian_roundtrip": "sum-of-verified-signed-le-be-pairs",
    }
    for case in cases.values():
        for mode in case["modes"].values():
            assert mode["parameters"]["comparison_class"] == (
                "idiomatic-fast" if case["id"] in idiomatic else "same-work"
            )
            if case["id"] in algorithms:
                assert mode["parameters"]["checksum_algorithm"] == algorithms[case["id"]]
            assert mode["parameters"]["timing_scope"] == "whole-process-including-setup-and-verification"

    def fnv(pattern: bytes, count: int) -> int:
        value = 14695981039346656037
        for index in range(count):
            value = ((value ^ pattern[index % len(pattern)]) * 1099511628211) & ((1 << 64) - 1)
        return value & ((1 << 63) - 1)

    word_cases = (
        "word_dynamic_append_100m", "word_repeated_100m",
        "word_builder_known_capacity", "word_builder_unknown_capacity",
    )
    for name in word_cases:
        case = cases[name]
        assert case["modes"]["default"]["arguments"] == ["100000000"]
        assert case["modes"]["default"]["expected_stdout"] == "100000000\n6013327376115300133\n"
        quick = case["modes"]["quick"]
        assert quick["arguments"] == ["4096"]
        assert quick["expected_stdout"] == f"4096\n{fnv(b'x', 4096)}\n"
        for mode in case["modes"].values():
            count = int(mode["arguments"][0])
            assert mode["parameters"]["bytes"] == count
            assert mode["parameters"]["verification_bytes"] == count
            assert mode["parameters"]["construction_calls"] == (
                1 if name == "word_repeated_100m" else count
            )

    copied = cases["bytes_copy_1gb"]
    assert copied["modes"]["default"]["arguments"] == ["1000000000"]
    assert copied["modes"]["default"]["expected_stdout"] == "1000000000\n0\n15648848027658085\n"
    assert copied["modes"]["quick"]["arguments"] == ["65536"]
    assert copied["modes"]["quick"]["expected_stdout"] == f"65536\n0\n{fnv(b'FREAK0123456789!', 65536)}\n"
    for mode in copied["modes"].values():
        count = int(mode["arguments"][0])
        assert mode["parameters"]["bytes"] == mode["parameters"]["copy_bytes"] == count
        assert mode["parameters"]["verification_bytes"] == count
        assert mode["parameters"]["copy_calls"] == 1

    byte_write = cases["bytes_write_100m"]
    assert byte_write["modes"]["default"]["arguments"] == ["100000000"]
    assert byte_write["modes"]["default"]["expected_stdout"] == "100000000\n355950708\n100000000\n0\n"
    checksum = 0
    for index in range(4096):
        checksum = (checksum * 131 + index % 256) % 1000000007
    assert byte_write["modes"]["quick"]["arguments"] == ["4096"]
    assert byte_write["modes"]["quick"]["expected_stdout"] == f"4096\n{checksum}\n4096\n0\n"
    for mode in byte_write["modes"].values():
        count = int(mode["arguments"][0])
        assert mode["parameters"]["bytes"] == count
        assert mode["parameters"]["read_calls"] == mode["parameters"]["write_calls"] == count

    for name, passes in (("bytes_sequential_write", 1), ("bytes_sequential_read", 4)):
        for mode_name, mode in cases[name]["modes"].items():
            count = 4096 if mode_name == "quick" else 100000000
            assert mode["arguments"] == [str(count)]
            quotient, remainder = divmod(count // 8, 65521)
            checksum = (quotient * 65521 * 65520 // 2 + remainder * (remainder - 1) // 2) * passes
            assert mode["expected_stdout"] == f"{count}\n{checksum}\n{count}\n0\n"
            assert mode["parameters"]["bytes"] == count
            assert mode["parameters"]["read_calls"] == count // 8 * passes
            assert mode["parameters"]["write_calls"] == count // 8
            assert mode["parameters"]["read_passes"] == passes

    for mode_name, mode in cases["bytes_endian_roundtrip"]["modes"].items():
        records = 256 if mode_name == "quick" else 1000000
        assert mode["arguments"] == [str(records)]
        assert mode["expected_stdout"] == f"{records * 16}\n{records ** 2}\n{records * 16}\n0\n"
        assert mode["parameters"]["records"] == records
        assert mode["parameters"]["bytes"] == records * 16
        assert mode["parameters"]["read_calls"] == mode["parameters"]["write_calls"] == records * 2


def _static_checks(temporary: Path) -> dict[str, Any]:
    _linker_identity_timeout_checks()
    manifest = LAB.load_manifest(MANIFEST)
    assert manifest["schema"] == LAB.MANIFEST_SCHEMA
    assert [case["id"] for case in manifest["cases"]] == [
        "cpu_integer_10m",
        "word_dynamic_append",
        "startup_empty",
        "compile_hello",
        "word_dynamic_append_100m",
        "word_repeated_100m",
        "word_builder_known_capacity",
        "word_builder_unknown_capacity",
        "bytes_write_100m",
        "bytes_copy_1gb",
        "bytes_sequential_write",
        "bytes_sequential_read",
        "bytes_endian_roundtrip",
    ]
    _foundation_workload_checks(manifest)

    crlf = temporary / "crlf"
    shutil.copytree(MANIFEST.parent, crlf)
    for source in crlf.glob("*.fk"):
        normalized = source.read_bytes().decode("utf-8").replace("\r\n", "\n")
        source.write_bytes(normalized.replace("\n", "\r\n").encode("utf-8"))
    LAB.load_manifest(crlf / "manifest.json")

    cr_only = temporary / "cr-only"
    shutil.copytree(MANIFEST.parent, cr_only)
    cr_source = cr_only / "startup_empty.fk"
    cr_text = cr_source.read_bytes().decode("utf-8").replace("\r\n", "\n")
    cr_source.write_bytes(cr_text.replace("\n", "\r").encode("utf-8"))
    _expect_lab_error(
        lambda: LAB.load_manifest(cr_only / "manifest.json"),
        "lone-CR source mutation was canonicalized as LF",
    )

    snapshot = temporary / "snapshot"
    LAB._snapshot_sources(manifest, MANIFEST.parent, snapshot)
    snapshot_hashes = {
        case["source"]: LAB._sha256_source_file(snapshot / case["source"])
        for case in manifest["cases"]
    }
    assert snapshot_hashes == {
        case["source"]: case["source_sha256"] for case in manifest["cases"]
    }

    valid_stats = {
        "schema": LAB.RUNTIME_STATS_SCHEMA,
        "source": LAB.RUNTIME_STATS_SOURCE,
        "counters": {"allocations": 0, "copied_bytes": 42},
    }
    clean, record, failures = LAB._strip_runtime_stats(
        LAB.RUNTIME_STATS_PREFIX + json.dumps(valid_stats) + "\n"
    )
    assert clean == "" and record == valid_stats and failures == []
    invalid_stats = copy.deepcopy(valid_stats)
    invalid_stats["counters"]["allocations"] = -1
    _, record, failures = LAB._strip_runtime_stats(
        LAB.RUNTIME_STATS_PREFIX + json.dumps(invalid_stats) + "\n"
    )
    assert record is None and failures
    duplicate_stats = (
        '{"schema":"freak-v3-runtime-stats-v1","source":"freak-v3-runtime",'
        '"counters":{"allocations":0,"allocations":1}}'
    )
    _, record, failures = LAB._strip_runtime_stats(LAB.RUNTIME_STATS_PREFIX + duplicate_stats + "\n")
    assert record is None and failures

    stale = temporary / "stale"
    shutil.copytree(MANIFEST.parent, stale)
    with (stale / "cpu_integer_10m.fk").open("a", encoding="utf-8") as stream:
        stream.write("\n-- stale probe\n")
    _expect_lab_error(lambda: LAB.load_manifest(stale / "manifest.json"), "stale source hash was accepted")

    malformed = temporary / "malformed"
    shutil.copytree(MANIFEST.parent, malformed)
    malformed_value = json.loads((malformed / "manifest.json").read_text(encoding="utf-8"))
    del malformed_value["cases"][0]["modes"]["quick"]["expected_stdout_sha256"]
    _write_json(malformed / "manifest.json", malformed_value)
    _expect_lab_error(
        lambda: LAB.load_manifest(malformed / "manifest.json"),
        "malformed manifest mode was accepted",
    )

    duplicate_manifest = temporary / "duplicate-manifest"
    shutil.copytree(MANIFEST.parent, duplicate_manifest)
    duplicate_path = duplicate_manifest / "manifest.json"
    duplicate_text = duplicate_path.read_text(encoding="utf-8")
    duplicate_text = duplicate_text.replace(
        '"schema": "freak-v3-performance-manifest-v1"',
        '"schema": "freak-v3-performance-manifest-v1",\n  "schema": "freak-v3-performance-manifest-v1"',
        1,
    )
    duplicate_path.write_text(duplicate_text, encoding="utf-8")
    _expect_lab_error(lambda: LAB.load_manifest(duplicate_path), "duplicate manifest key was accepted")

    unbound = temporary / "unbound"
    shutil.copytree(MANIFEST.parent, unbound)
    (unbound / "unlisted.fk").write_text("task main() {}\n", encoding="utf-8")
    _expect_lab_error(lambda: LAB.load_manifest(unbound / "manifest.json"), "unbound source was accepted")

    malformed_output = temporary / "malformed-output.json"
    _write_json(malformed_output, {})
    _expect_lab_error(lambda: LAB.validate_output(malformed_output), "malformed output was accepted")
    help_text = LAB._parser().format_help()
    normalized_help = " ".join(help_text.split())
    assert "not digitally signed" in normalized_help
    assert "live compiler, Clang, and linker" in normalized_help
    assert "process containment is cooperative" in normalized_help
    assert "must not detach from the isolated session/process group" in normalized_help
    posix_wrapper = LAB._recording_wrapper_bytes(
        "posix-sh",
        "/tmp/python with spaces",
        "/tmp/recorder with spaces.py",
        "ignored",
    ).decode("utf-8")
    assert posix_wrapper.startswith("#!/bin/sh\nexec ")
    assert "'/tmp/python with spaces'" in posix_wrapper
    assert "'/tmp/recorder with spaces.py'" in posix_wrapper
    _expect_lab_error(
        lambda: LAB._decode_bytes("QUFBQUFB", "bounded base64", maximum=2),
        "oversized base64 was decoded before rejection",
    )
    bounded_json = temporary / "bounded.json"
    bounded_json.write_text("{}\n", encoding="utf-8")
    _expect_lab_error(
        lambda: LAB._strict_json(bounded_json, maximum=1),
        "oversized JSON input was accepted",
    )

    observed_input = temporary / "invocation-input.c"
    observed_output = temporary / "invocation-output.o"
    observed_input.write_bytes(b"int x;\n")
    observed_output.write_bytes(b"object\n")
    raw_invocation = {
        "argv": ["-c", str(observed_input), "-o", str(observed_output)],
        "cwd": str(temporary),
        "exit_code": 0,
        "inputs": [
            {
                "argument_index": 1,
                "path": str(observed_input),
                "bytes": observed_input.stat().st_size,
                "sha256": LAB._sha256_file(observed_input),
            }
        ],
        "output": {
            "path": str(observed_output),
            "bytes": observed_output.stat().st_size,
            "sha256": LAB._sha256_file(observed_output),
        },
    }
    stored_invocation = LAB._invocation_record(raw_invocation, "static invocation")
    stored_invocation["output"]["sha256"] = "0" * 64
    _expect_lab_error(
        lambda: LAB._validate_invocation_record(stored_invocation, "mutated invocation"),
        "full invocation digest omitted output evidence",
    )

    _process_tree_checks(temporary)
    assert LAB._available_profiles("baseline help") == ["O0", "O1", "O2", "O3"]
    plus03_help = "profiles: \x1b[33m+03 — FINAL FORM\x1b[0m; LTO: --lto[=MODE]"
    assert LAB._available_profiles(plus03_help) == ["O0", "O1", "O2", "O3", "+03"]
    assert LAB._selected_profiles(None, LAB._available_profiles("baseline help")) == ["O0", "O1", "O2", "O3"]
    _expect_lab_error(
        lambda: LAB._selected_profiles(["+03"], LAB._available_profiles("baseline help")),
        "feature-unavailable +03 was accepted",
    )
    return manifest


def _mutate_and_reject(
    temporary: Path,
    document: dict[str, Any],
    name: str,
    mutation: Callable[[dict[str, Any]], None],
    cli: Path,
    expected_diagnostic: str | None = None,
) -> None:
    candidate = copy.deepcopy(document)
    mutation(candidate)
    path = temporary / f"reject-{name}.json"
    _write_json(path, candidate)
    _expect_lab_error(
        lambda: LAB.validate_output(path, cli_override=str(cli)),
        f"malformed/stale result mutation was accepted: {name}",
        expected_diagnostic,
    )


def _mutate_recorded_optimization(document: dict[str, Any]) -> None:
    observation = document["results"][0]["compile"]["observation"]
    selected_link = _selected_link(document)
    changed = False
    for invocation in observation["invocations"]:
        invocation["argv"] = [
            "-O2" if argument == "-O0" else argument for argument in invocation["argv"]
        ]
        _refresh_invocation_record(invocation)
        changed = changed or "-O2" in invocation["argv"]
    assert changed
    observation["optimization_flags"] = ["-O2"]
    observation["link_invocation_sha256"] = selected_link["record_sha256"]
    observation["linker"]["link_invocation_sha256"] = selected_link["record_sha256"]


def _replace_embedded_content(record: dict[str, Any], content: bytes) -> None:
    record["bytes"] = len(content)
    record["sha256"] = LAB._sha256_bytes(content)
    record["content_zlib_base64"] = LAB._encode_zlib_bytes(content)


def _refresh_invocation_record(invocation: dict[str, Any]) -> None:
    raw = {name: invocation[name] for name in LAB._RAW_INVOCATION_KEYS}
    invocation["record_sha256"] = LAB._json_sha256(raw)


def _selected_link(document: dict[str, Any]) -> dict[str, Any]:
    observation = document["results"][0]["compile"]["observation"]
    selected = observation["link_invocation_sha256"]
    return next(item for item in observation["invocations"] if item["record_sha256"] == selected)


def _mutate_link_output(document: dict[str, Any]) -> None:
    observation = document["results"][0]["compile"]["observation"]
    invocation = _selected_link(document)
    output_index = invocation["argv"].index("-o")
    invocation["argv"][output_index + 1] = str(Path(invocation["cwd"]) / "detached-output.exe")
    _refresh_invocation_record(invocation)
    observation["link_invocation_sha256"] = invocation["record_sha256"]
    observation["linker"]["link_invocation_sha256"] = invocation["record_sha256"]


def _detach_link_runtime_input(document: dict[str, Any]) -> None:
    observation = document["results"][0]["compile"]["observation"]
    invocation = _selected_link(document)
    for index, input_record in enumerate(invocation["inputs"]):
        if Path(input_record["path"]).name in LAB._RUNTIME_INPUT_NAMES:
            del invocation["inputs"][index]
            _refresh_invocation_record(invocation)
            observation["link_invocation_sha256"] = invocation["record_sha256"]
            observation["linker"]["link_invocation_sha256"] = invocation["record_sha256"]
            return
    raise AssertionError("selected link invocation did not contain a runtime input")


def _mutate_canonical_recorder(document: dict[str, Any]) -> None:
    recording = document["recording"]
    content = b"#!/usr/bin/env python3\nraise SystemExit(0)\n"
    recording["recorder_content_base64"] = LAB._encode_bytes(content)
    recording["recorder_sha256"] = LAB._sha256_bytes(content)
    recording["combined_sha256"] = LAB._recording_identity_digest(recording)


def _coherently_replace_binary_fields(document: dict[str, Any]) -> None:
    result = document["results"][0]
    content = b"detached executable binary"
    _replace_embedded_content(result["binary"], content)
    invocation = _selected_link(document)
    invocation["output"]["bytes"] = len(content)
    invocation["output"]["sha256"] = LAB._sha256_bytes(content)
    # Each nested record is now self-consistent. The full invocation digest must
    # still reject the coherent replacement.


def _coherently_replace_artifact_fields(document: dict[str, Any]) -> None:
    observation = document["results"][0]["compile"]["observation"]
    artifact = observation["backend_artifact"]
    old_path = artifact["path"]
    content = b"detached backend artifact"
    _replace_embedded_content(artifact, content)
    for invocation in observation["invocations"]:
        for input_record in invocation["inputs"]:
            if input_record["path"] == old_path:
                input_record["bytes"] = len(content)
                input_record["sha256"] = LAB._sha256_bytes(content)


def _substitute_linker_identity(document: dict[str, Any]) -> None:
    observation = document["results"][0]["compile"]["observation"]
    linker = observation["linker"]
    clang = Path(document["toolchain"]["path"])
    completed = subprocess.run(
        [str(clang), "--version"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=5.0,
    )
    trace = f'"{clang}" fabricated linker trace\n'.encode("utf-8")
    linker.update(
        {
            "observed_path": str(clang),
            "path": str(clang),
            "sha256": LAB._sha256_file(clang),
            "bytes": clang.stat().st_size,
            "version_exit_code": completed.returncode,
            "version_stdout_base64": LAB._encode_bytes(completed.stdout),
            "version_stderr_base64": LAB._encode_bytes(completed.stderr),
            "trace_raw_base64": LAB._encode_bytes(trace),
            "trace_sha256": LAB._sha256_bytes(trace),
        }
    )


def _linker_identity_timeout_checks() -> None:
    document = {"toolchain": {"path": "mock-clang"},
                "results": [{"compile": {"observation": {"linker": {}}}}]}
    with patch.object(subprocess, "run", side_effect=subprocess.TimeoutExpired(
            ["mock-clang", "--version"], 5.0)) as probe:
        try:
            _substitute_linker_identity(document)
        except subprocess.TimeoutExpired:
            pass
        else:
            raise AssertionError("timed-out version probe was silently accepted")
        probe.assert_called_once_with(["mock-clang", "--version"],
                                      stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE, check=False, timeout=5.0)
    assert document["results"][0]["compile"]["observation"]["linker"] == {}


def _profile_matrix_checks(temporary: Path, cli: Path, clang: Path | None) -> None:
    output = temporary / "profile-matrix.json"
    command = [
        sys.executable,
        "-u",
        str(TOOL),
        "--cli",
        str(cli),
        "--manifest",
        str(MANIFEST),
        "--output",
        str(output),
        "--quick",
        "--case",
        "startup_empty",
        "--backend",
        "c",
        "--backend",
        "llvm",
        "--samples",
        "1",
        "--warmups",
        "1",
    ]
    if clang is not None:
        command.extend(["--clang", str(clang)])
    completed = subprocess.run(
        command,
        cwd=str(ROOT),
        env=os.environ.copy(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=600,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(
            f"profile matrix failed with {completed.returncode}\n"
            f"stdout:\n{completed.stdout.decode('utf-8', errors='replace')}\n"
            f"stderr:\n{completed.stderr.decode('utf-8', errors='replace')}"
        )
    document = LAB.validate_output(output, cli_override=str(cli))
    profiles = document["configuration"]["profiles"]
    assert profiles == document["configuration"]["available_profiles"]
    assert profiles[:4] == ["O0", "O1", "O2", "O3"]
    assert {result["profile"] for result in document["results"]} == set(profiles)
    assert {result["backend"] for result in document["results"]} == {"c", "llvm"}
    assert len(document["results"]) == len(profiles) * 2
    for result in document["results"]:
        observation = result["compile"]["observation"]
        spec = LAB._PROFILE_SPECS[result["profile"]]
        assert observation["optimization_flags"] == [spec["opt"]]
        assert observation["lto_flags"] == spec["lto"]
        assert observation["linker_flags"] == LAB._expected_linker_flags(result["profile"])
        assert len(result["run"]["warmups"]) == 1
        if result["profile"] == "+03":
            assert observation["runtime_plan"] == "source"
            assert observation["runtime_attempt_plan"] == "source"
    _mutate_and_reject(
        temporary,
        document,
        "warmup-executable-provenance",
        lambda value: value["results"][0]["run"]["warmups"][0].__setitem__(
            "executable_sha256_before", "0" * 64
        ),
        cli,
    )


def _live_checks(temporary: Path, manifest: dict[str, Any], cli: Path, clang: Path | None) -> None:
    before = {path.relative_to(MANIFEST.parent).as_posix(): _sha256(path) for path in MANIFEST.parent.rglob("*") if path.is_file()}
    output = temporary / "quick.json"
    command = [
        sys.executable,
        "-u",
        str(TOOL),
        "--cli",
        str(cli),
        "--manifest",
        str(MANIFEST),
        "--output",
        str(output),
        "--quick",
        "--profile",
        "O0",
        "--backend",
        "c",
        "--backend",
        "llvm",
        "--samples",
        "1",
        "--warmups",
        "0",
    ]
    if clang is not None:
        command.extend(["--clang", str(clang)])
    environment = os.environ.copy()
    environment["FREAK_HOME"] = str(temporary / "must-not-leak-freak-home")
    environment["FREAK_CLANG"] = str(temporary / "must-not-leak-fake-clang")
    environment["CFLAGS"] = "-Ofast must-not-leak"
    environment["LDFLAGS"] = "-fuse-ld=must-not-leak"
    environment["FREAK_UNRELATED_TEST_POISON"] = "must-not-leak"
    completed = subprocess.run(
        command,
        cwd=str(ROOT),
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=600,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(
            f"quick lab failed with {completed.returncode}\n"
            f"stdout:\n{completed.stdout.decode('utf-8', errors='replace')}\n"
            f"stderr:\n{completed.stderr.decode('utf-8', errors='replace')}"
        )

    document = LAB.validate_output(output, cli_override=str(cli))
    assert document["schema"] == LAB.RESULT_SCHEMA
    assert document["trust_model"] == {
        "schema": LAB.TRUST_MODEL_SCHEMA,
        "scope": LAB.TRUST_MODEL_SCOPE,
        "limitation": LAB.TRUST_MODEL_LIMITATION,
    }
    assert document["compiler"]["path"] == str(cli)
    assert document["compiler"]["sha256"] == _sha256(cli)
    assert document["compiler"]["version"]
    assert document["recording"]["schema"] == LAB.RECORDING_SCHEMA
    assert document["recording"]["combined_sha256"] == LAB._recording_identity_digest(document["recording"])
    assert document["configuration"]["mode"] == "quick"
    assert document["configuration"]["profiles"] == ["O0"]
    assert document["configuration"]["backends"] == ["c", "llvm"]
    assert len(document["results"]) == len(manifest["cases"]) * 2
    assert {result["backend"] for result in document["results"]} == {"c", "llvm"}
    assert all(result["profile"] == "O0" for result in document["results"])
    assert all(result["verification"] == {"passed": True, "failures": []} for result in document["results"])
    expected_quick = {case["id"]: case["modes"]["quick"] for case in manifest["cases"]}
    for result in document["results"]:
        mode = expected_quick[result["case"]]
        assert result["workload"]["parameters"] == mode["parameters"]
        assert result["workload"]["expected_stdout_sha256"] == mode["expected_stdout_sha256"]
        assert result["run"]["samples"][0]["stdout_sha256"] == mode["expected_stdout_sha256"]
        observation = result["compile"]["observation"]
        assert observation["schema"] == LAB.COMPILE_OBSERVATION_SCHEMA
        assert observation["optimization_flags"] == ["-O0"]
        assert observation["lto_flags"] == []
        assert observation["backend_artifact"]["suffix"] == (
            ".c" if result["backend"] == "c" else ".ll"
        )
        assert observation["recording_identity_sha256"] == document["recording"]["combined_sha256"]
        assert observation["recording_before_sha256"] == document["recording"]["combined_sha256"]
        assert observation["recording_after_sha256"] == document["recording"]["combined_sha256"]
        assert observation["runtime_plan"] in {"source", "bundle"}
        assert observation["runtime_attempt_plan"] in {"source", "bundle", "bundle-source-fallback"}
        assert observation["linked_runtime_inputs"]
        link = next(
            invocation
            for invocation in observation["invocations"]
            if invocation["record_sha256"] == observation["link_invocation_sha256"]
        )
        assert link["exit_code"] == 0 and link["output"]["sha256"] == result["binary"]["sha256"]
        sample = result["run"]["samples"][0]
        assert sample["command"][0] == result["binary"]["path"]
        assert sample["executable_sha256_before"] == result["binary"]["sha256"]
        assert sample["executable_sha256_after"] == result["binary"]["sha256"]
        assert result["run"]["warmups"] == []
        assert result["peak_rss_bytes"] is None and result["peak_rss_reason"]
        assert result["runtime_counters"] is None and result["runtime_counters_reason"]
    assert "must-not-leak" not in output.read_text(encoding="utf-8")

    after = {path.relative_to(MANIFEST.parent).as_posix(): _sha256(path) for path in MANIFEST.parent.rglob("*") if path.is_file()}
    assert after == before, "the lab modified or generated files in the permanent benchmark tree"

    _mutate_and_reject(
        temporary,
        document,
        "schema",
        lambda value: value.__setitem__("schema", "freak-v3-performance-lab-v0"),
        cli,
    )
    _mutate_and_reject(
        temporary,
        document,
        "trust-model",
        lambda value: value["trust_model"].__setitem__(
            "limitation", "fabricated authentication claim"
        ),
        cli,
    )
    _mutate_and_reject(
        temporary,
        document,
        "recording-identity-hash",
        lambda value: value["recording"].__setitem__("combined_sha256", "0" * 64),
        cli,
    )
    _mutate_and_reject(
        temporary,
        document,
        "recording-canonical-content",
        _mutate_canonical_recorder,
        cli,
    )
    _mutate_and_reject(
        temporary,
        document,
        "recording-before-build",
        lambda value: value["results"][0]["compile"]["observation"].__setitem__(
            "recording_before_sha256", "0" * 64
        ),
        cli,
    )
    _mutate_and_reject(
        temporary,
        document,
        "warmup-count",
        lambda value: value["configuration"].__setitem__("warmups", 999),
        cli,
    )
    _mutate_and_reject(
        temporary,
        document,
        "compiler-hash",
        lambda value: value["compiler"].__setitem__("sha256", "0" * 64),
        cli,
    )
    _mutate_and_reject(
        temporary,
        document,
        "backend-artifact-recomputed",
        lambda value: _replace_embedded_content(
            value["results"][0]["compile"]["observation"]["backend_artifact"],
            b"detached backend artifact",
        ),
        cli,
    )
    _mutate_and_reject(
        temporary,
        document,
        "backend-artifact-coherent-fields",
        _coherently_replace_artifact_fields,
        cli,
    )
    _mutate_and_reject(
        temporary,
        document,
        "extra-result-key",
        lambda value: value["results"][0].__setitem__("unknown", True),
        cli,
    )
    _mutate_and_reject(
        temporary,
        document,
        "binary-recomputed",
        lambda value: _replace_embedded_content(
            value["results"][0]["binary"],
            b"detached executable binary",
        ),
        cli,
    )
    _mutate_and_reject(
        temporary,
        document,
        "binary-link-output-coherent-fields",
        _coherently_replace_binary_fields,
        cli,
    )
    _mutate_and_reject(
        temporary,
        document,
        "exact-linker-substitution",
        _substitute_linker_identity,
        cli,
    )
    _mutate_and_reject(temporary, document, "link-output", _mutate_link_output, cli)
    _mutate_and_reject(
        temporary,
        document,
        "detached-link-runtime",
        _detach_link_runtime_input,
        cli,
        "runtime_inputs are detached",
    )

    duplicate_output = temporary / "reject-duplicate-nested-key.json"
    duplicate_text = output.read_text(encoding="utf-8")
    binary_path_text = json.dumps(document["results"][0]["binary"]["path"])
    binary_start = duplicate_text.index('"binary": {')
    path_start = duplicate_text.index(f'"path": {binary_path_text}', binary_start)
    needle = f'"path": {binary_path_text}'
    duplicate_text = duplicate_text[:path_start] + needle + ",\n        " + duplicate_text[path_start:]
    duplicate_output.write_text(duplicate_text, encoding="utf-8")
    _expect_lab_error(
        lambda: LAB.validate_output(duplicate_output, cli_override=str(cli)),
        "duplicate nested artifact key was accepted",
    )

    _profile_matrix_checks(temporary, cli, clang)
    _mutate_and_reject(
        temporary,
        document,
        "median",
        lambda value: value["results"][0]["run"].__setitem__(
            "median_ns", value["results"][0]["run"]["median_ns"] + 1
        ),
        cli,
    )
    _mutate_and_reject(
        temporary,
        document,
        "checksum",
        lambda value: value["results"][0]["run"]["samples"][0].__setitem__("stdout_sha256", "0" * 64),
        cli,
    )
    _mutate_and_reject(
        temporary,
        document,
        "raw-checksum",
        lambda value: value["results"][0]["run"]["samples"][0].__setitem__(
            "stdout_raw_sha256", "0" * 64
        ),
        cli,
    )
    _mutate_and_reject(
        temporary,
        document,
        "toolchain-version",
        lambda value: value["toolchain"].__setitem__("version", "fabricated toolchain"),
        cli,
    )
    _mutate_and_reject(
        temporary,
        document,
        "available-profiles",
        lambda value: value["configuration"]["available_profiles"].append("+03"),
        cli,
    )
    _mutate_and_reject(
        temporary,
        document,
        "peak-rss",
        lambda value: value["results"][0].__setitem__("peak_rss_bytes", 123),
        cli,
    )

    def fabricate_counters(value: dict[str, Any]) -> None:
        result = value["results"][0]
        result["runtime_counters"] = {
            "samples": [
                {
                    "schema": LAB.RUNTIME_STATS_SCHEMA,
                    "source": LAB.RUNTIME_STATS_SOURCE,
                    "counters": {"allocations": 999},
                }
            ]
        }
        result["runtime_counters_reason"] = None

    _mutate_and_reject(temporary, document, "fabricated-counters", fabricate_counters, cli)
    _mutate_and_reject(
        temporary,
        document,
        "ignored-optimization",
        _mutate_recorded_optimization,
        cli,
        "optimization flags do not implement O0",
    )
    _mutate_and_reject(
        temporary,
        document,
        "ignored-backend",
        lambda value: value["results"][0]["compile"]["observation"]["backend_artifact"].__setitem__(
            "suffix", ".ll"
        ),
        cli,
    )
    _mutate_and_reject(
        temporary,
        document,
        "backend-artifact-hash",
        lambda value: value["results"][0]["compile"]["observation"]["backend_artifact"].__setitem__(
            "sha256", "0" * 64
        ),
        cli,
    )
    _mutate_and_reject(
        temporary,
        document,
        "binary-hash",
        lambda value: value["results"][0]["binary"].__setitem__("sha256", "0" * 64),
        cli,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cli", nargs="?", help="exact fresh FREAK CLI for executable C/LLVM checks")
    parser.add_argument("--clang", help="exact Clang executable")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="freak-v3-performance-test-") as name:
        temporary = Path(name).resolve()
        manifest = _static_checks(temporary)
        if args.cli:
            cli = Path(args.cli).expanduser().resolve(strict=True)
            clang = Path(args.clang).expanduser().resolve(strict=True) if args.clang else None
            _live_checks(temporary, manifest, cli, clang)
    mode = "static + C/LLVM quick" if args.cli else "static only"
    print(f"v3 performance lab tests passed ({mode})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
