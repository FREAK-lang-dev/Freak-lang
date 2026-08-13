#!/usr/bin/env python3
"""Bounded compile-phase probe for the V4 bootstrap compiler.

This is intentionally not a V4 compiler CLI.  It embeds one source file in a
temporary bootstrap program, asks the V4 crates for frontend facts through TY,
and executes that probe twice to prove that its phase summary is deterministic.
It never emits, links, or executes the source program being inspected.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path


SCHEMA = "freak.v4.campaign-probe.v1"
PROCESS_GROUP_HELD_ENV = "FREAK_CAMPAIGN_PROCESS_GROUP_HELD"
CRATE_ORDER = (
    "freak_span",
    "freak_diag",
    "freak_macro_api",
    "freak_arena",
    "freak_intern",
    "freak_session",
    "freak_lex",
    "freak_parse",
    "freak_expand",
    "freak_hir",
    "freak_resolve",
    "freak_ty",
)

if not __debug__:
    raise SystemExit("campaign_probe.py requires assertions; do not run with python -O")


def repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "freakc").is_dir() and (parent / "src/compiler/v4/crates").is_dir():
            return parent
    raise RuntimeError("could not locate repository root")


ROOT = repo_root()
CRATES_ROOT = ROOT / "src/compiler/v4/crates"
RUNTIME_ROOT = ROOT / "freakc/runtime"


@dataclass(frozen=True)
class BoundedResult:
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    peak_memory_bytes: int


class WindowsJob:
    """Kill-on-close Windows job with an aggregate commit limit."""

    def __init__(self, memory_limit_bytes: int) -> None:
        from ctypes import wintypes

        class BasicLimits(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", ctypes.c_int64),
                ("PerJobUserTimeLimit", ctypes.c_int64),
                ("LimitFlags", wintypes.DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD),
            ]

        class IoCounters(ctypes.Structure):
            _fields_ = [(name, ctypes.c_uint64) for name in (
                "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                "ReadTransferCount", "WriteTransferCount", "OtherTransferCount",
            )]

        class ExtendedLimits(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", BasicLimits),
                ("IoInfo", IoCounters),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t),
            ]

        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self.ntdll = ctypes.WinDLL("ntdll")
        self.info_type = ExtendedLimits
        self.kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        self.kernel32.CreateJobObjectW.restype = wintypes.HANDLE
        self.kernel32.SetInformationJobObject.argtypes = [
            wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD
        ]
        self.kernel32.SetInformationJobObject.restype = wintypes.BOOL
        self.kernel32.QueryInformationJobObject.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.c_void_p,
        ]
        self.kernel32.QueryInformationJobObject.restype = wintypes.BOOL
        self.kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        self.kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
        self.kernel32.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
        self.kernel32.TerminateJobObject.restype = wintypes.BOOL
        self.kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel32.CloseHandle.restype = wintypes.BOOL
        self.ntdll.NtResumeProcess.argtypes = [wintypes.HANDLE]
        self.ntdll.NtResumeProcess.restype = ctypes.c_long
        self.ntdll.RtlNtStatusToDosError.argtypes = [ctypes.c_long]
        self.ntdll.RtlNtStatusToDosError.restype = wintypes.ULONG
        self.handle = self.kernel32.CreateJobObjectW(None, None)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        info = self.info_type()
        info.BasicLimitInformation.LimitFlags = 0x00002000 | 0x00000200
        info.JobMemoryLimit = memory_limit_bytes
        if not self.kernel32.SetInformationJobObject(
            self.handle, 9, ctypes.byref(info), ctypes.sizeof(info)
        ):
            error = ctypes.WinError(ctypes.get_last_error())
            self.kernel32.CloseHandle(self.handle)
            self.handle = None
            raise error

    def assign(self, process: subprocess.Popen[bytes]) -> None:
        if not self.kernel32.AssignProcessToJobObject(self.handle, process._handle):
            raise ctypes.WinError(ctypes.get_last_error())

    def resume(self, process: subprocess.Popen[bytes]) -> None:
        status = self.ntdll.NtResumeProcess(process._handle)
        if status != 0:
            raise ctypes.WinError(self.ntdll.RtlNtStatusToDosError(status))

    def memory_bytes(self) -> int | None:
        if not self.handle:
            return None
        info = self.info_type()
        if not self.kernel32.QueryInformationJobObject(
            self.handle, 9, ctypes.byref(info), ctypes.sizeof(info), None
        ):
            return None
        return max(int(info.PeakProcessMemoryUsed), int(info.PeakJobMemoryUsed))

    def terminate(self) -> None:
        if self.handle:
            self.kernel32.TerminateJobObject(self.handle, 1)

    def close(self) -> None:
        if self.handle:
            self.kernel32.CloseHandle(self.handle)
            self.handle = None


@contextmanager
def v4_host_mutex(timeout_seconds: int = 3600):
    """Serialize bootstrap compiler processes with the repository-wide mutex."""

    if timeout_seconds <= 0 or timeout_seconds > 4_294_967:
        raise RuntimeError("V4 host mutex timeout must be between 1 and 4294967 seconds")
    if sys.platform.startswith("win"):
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
        kernel32.CreateMutexW.restype = wintypes.HANDLE
        kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel32.WaitForSingleObject.restype = wintypes.DWORD
        kernel32.ReleaseMutex.argtypes = [wintypes.HANDLE]
        kernel32.ReleaseMutex.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel32.CreateMutexW(None, False, "Global\\FreakCheckV4")
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            wait = kernel32.WaitForSingleObject(handle, timeout_seconds * 1000)
            if wait not in (0, 0x80):
                raise RuntimeError("timed out waiting for Global\\FreakCheckV4")
            try:
                yield
            finally:
                kernel32.ReleaseMutex(handle)
        finally:
            kernel32.CloseHandle(handle)
        return

    import fcntl

    lock_path = Path(tempfile.gettempdir()) / "freak-check-v4.lock"
    with lock_path.open("a+b") as lock_file:
        started = time.monotonic()
        while True:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() - started > timeout_seconds:
                    raise RuntimeError("timed out waiting for V4 host lock")
                time.sleep(0.1)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _posix_group_memory(group_id: int) -> int | None:
    proc_root = Path("/proc")
    try:
        if proc_root.is_dir():
            total_kb = 0
            found = False
            for entry in proc_root.iterdir():
                if not entry.name.isdigit():
                    continue
                try:
                    stat = (entry / "stat").read_text(encoding="ascii", errors="replace")
                    close_paren = stat.rfind(")")
                    if close_paren < 0:
                        continue
                    fields = stat[close_paren + 2 :].split()
                    if len(fields) < 3 or int(fields[2]) != group_id:
                        continue
                    found = True
                    for line in (entry / "status").read_text(
                        encoding="ascii", errors="replace"
                    ).splitlines():
                        if line.startswith("VmRSS:") or line.startswith("VmSwap:"):
                            total_kb += int(line.split()[1])
                except (OSError, ValueError):
                    continue
            return total_kb * 1024 if found else None

        measured = subprocess.run(
            ["ps", "-axo", "pgid=,rss="],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        if measured.returncode != 0:
            return None
        total_kb = 0
        found = False
        for line in measured.stdout.splitlines():
            fields = line.split()
            if len(fields) != 2 or int(fields[0]) != group_id:
                continue
            found = True
            total_kb += int(fields[1])
        return total_kb * 1024 if found else None
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def _terminate_process_tree(
    process: subprocess.Popen[bytes],
    windows_job: WindowsJob | None,
    owns_posix_process_group: bool,
) -> None:
    if windows_job is not None:
        windows_job.terminate()
    elif owns_posix_process_group:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
    if process.poll() is None:
        process.kill()
    process.wait()


def _owns_posix_process_group(on_windows: bool, inherit: bool) -> bool:
    return not on_windows and not inherit


def run_bounded(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout_seconds: int = 60,
    memory_limit_mb: int = 512,
    output_limit_mb: int = 4,
    inherit_posix_process_group: bool = False,
) -> BoundedResult:
    """Run one process tree with bounded time, memory, and captured output."""

    if timeout_seconds <= 0 or memory_limit_mb <= 0 or output_limit_mb <= 0:
        raise RuntimeError("time, memory, and output limits must all be positive")
    output_limit = output_limit_mb * 1024 * 1024
    memory_limit = memory_limit_mb * 1024 * 1024
    with tempfile.TemporaryDirectory(prefix="freak-campaign-output-") as temporary:
        capture_root = Path(temporary)
        stdout_path = capture_root / "stdout.txt"
        stderr_path = capture_root / "stderr.txt"
        windows_job = WindowsJob(memory_limit) if sys.platform.startswith("win") else None
        owns_posix_process_group = _owns_posix_process_group(
            windows_job is not None, inherit_posix_process_group
        )
        creationflags = 0x00000004 if windows_job is not None else 0
        with stdout_path.open("wb") as stdout_file, stderr_path.open("wb") as stderr_file:
            try:
                process = subprocess.Popen(
                    command,
                    cwd=cwd,
                    env=env,
                    stdout=stdout_file,
                    stderr=stderr_file,
                    creationflags=creationflags,
                    start_new_session=owns_posix_process_group,
                )
            except BaseException:
                if windows_job is not None:
                    windows_job.close()
                raise
            if windows_job is not None:
                try:
                    windows_job.assign(process)
                    windows_job.resume(process)
                except BaseException:
                    _terminate_process_tree(process, windows_job, False)
                    windows_job.close()
                    raise
            try:
                process_group_id = (
                    None
                    if windows_job is not None
                    else process.pid
                    if owns_posix_process_group
                    else os.getpgrp()
                )
                started = time.monotonic()
                peak_memory = 0
                failure = ""
                while process.poll() is None:
                    elapsed = time.monotonic() - started
                    measured = (
                        windows_job.memory_bytes()
                        if windows_job is not None
                        else _posix_group_memory(process_group_id)
                    )
                    if measured is not None:
                        peak_memory = max(peak_memory, measured)
                    if elapsed > timeout_seconds:
                        failure = f"timeout after {timeout_seconds}s"
                    elif measured is None and windows_job is None:
                        failure = "process-tree memory measurement unavailable"
                    elif measured is not None and measured > memory_limit:
                        failure = (
                            f"memory limit exceeded: {measured} > {memory_limit} bytes"
                        )
                    elif stdout_path.stat().st_size > output_limit or stderr_path.stat().st_size > output_limit:
                        failure = f"output limit exceeded: {output_limit_mb}MB per stream"
                    if failure:
                        _terminate_process_tree(
                            process, windows_job, owns_posix_process_group
                        )
                        break
                    time.sleep(0.05)
                measured = (
                    windows_job.memory_bytes()
                    if windows_job is not None
                    else _posix_group_memory(process_group_id)
                )
                if measured is not None:
                    peak_memory = max(peak_memory, measured)
            finally:
                if process.poll() is None or owns_posix_process_group:
                    _terminate_process_tree(
                        process, windows_job, owns_posix_process_group
                    )
                if windows_job is not None:
                    windows_job.close()

        stdout_bytes = stdout_path.read_bytes()
        stderr_bytes = stderr_path.read_bytes()
        if len(stdout_bytes) > output_limit or len(stderr_bytes) > output_limit:
            failure = failure or f"output limit exceeded: {output_limit_mb}MB per stream"
        if failure:
            raise RuntimeError(
                f"{' '.join(command)}: {failure}\n"
                f"stdout-tail={stdout_bytes[-2000:].decode('utf-8', errors='replace')}\n"
                f"stderr-tail={stderr_bytes[-2000:].decode('utf-8', errors='replace')}"
            )
        return BoundedResult(
            command=tuple(command),
            returncode=int(process.returncode),
            stdout=stdout_bytes.decode("utf-8", errors="replace"),
            stderr=stderr_bytes.decode("utf-8", errors="replace"),
            peak_memory_bytes=peak_memory,
        )


def _freak_source_builder(value: str) -> str:
    """Encode source as numeric Unicode scalars, never FREAK literal syntax."""

    statements = [
        "task v4_campaign_build_source() -> word {",
        "    pilot parts: int = array_new()",
    ]
    codepoints = [ord(character) for character in value]
    for start in range(0, len(codepoints), 12):
        encoded = " + ".join(f"chr({value})" for value in codepoints[start : start + 12])
        statements.append(f"    array_push(parts, {encoded})")
    statements.extend(["    give back word_join(parts)", "}"])
    return "\n".join(statements)


def stable_word_checksum(value: bytes) -> int:
    checksum = 14_695_981_039_346_656_037
    for byte in value:
        checksum ^= byte
        checksum = (checksum * 1_099_511_628_211) & 0xFFFF_FFFF_FFFF_FFFF
    return checksum & 0x7FFF_FFFF_FFFF_FFFF


def build_probe_fixture(source: str) -> str:
    """Build a fixed frontend probe; the inspected source is data, not the program."""

    return f'''-- Generated campaign probe. The source under test is opaque data.
{_freak_source_builder(source)}

task v4_campaign_lex_errors(stream_id: int) -> int {{
    pilot count = 0
    pilot i = 0
    repeat until i >= v4_lex_diag_count(stream_id) {{
        if v4_diag_severity(v4_lex_diag(stream_id, i)) >= v4_diag_error {{ count += 1 }}
        i += 1
    }}
    give back count
}}

task v4_campaign_parse_errors(tree_id: int) -> int {{
    pilot count = 0
    pilot i = 0
    repeat until i >= v4_parse_diag_count(tree_id) {{
        if v4_diag_severity(v4_parse_diag(tree_id, i)) >= v4_diag_error {{ count += 1 }}
        i += 1
    }}
    give back count
}}

task v4_campaign_hir_errors(hir_id: int) -> int {{
    pilot count = 0
    pilot i = 0
    repeat until i >= v4_hir_diag_count(hir_id) {{
        if v4_diag_severity(v4_hir_diag(hir_id, i)) >= v4_diag_error {{ count += 1 }}
        i += 1
    }}
    give back count
}}

task v4_campaign_resolve_errors(resolve_id: int) -> int {{
    pilot count = 0
    pilot i = 0
    repeat until i >= v4_resolve_diag_count(resolve_id) {{
        if v4_diag_severity(v4_resolve_diag(resolve_id, i)) >= v4_diag_error {{ count += 1 }}
        i += 1
    }}
    give back count
}}

task v4_campaign_ty_errors(ty_id: int) -> int {{
    pilot count = 0
    pilot i = 0
    repeat until i >= v4_ty_diag_count(ty_id) {{
        if v4_diag_severity(v4_ty_diag(ty_id, i)) >= v4_diag_error {{ count += 1 }}
        i += 1
    }}
    give back count
}}

pilot v4_campaign_source: word = v4_campaign_build_source()
pilot v4_campaign_file: int = v4_source_add("campaign-case.fk", v4_campaign_source)
pilot v4_campaign_stream: int = v4_lex_text(v4_campaign_file, v4_campaign_source)
pilot v4_campaign_tree: int = v4_parse_stream(v4_campaign_file, v4_campaign_stream)
pilot v4_campaign_expansion: int = v4_expand_identity(v4_campaign_file, v4_campaign_tree)
pilot v4_campaign_hir: int = v4_hir_lower_expanded(v4_campaign_file, v4_campaign_expansion)
pilot v4_campaign_resolve: int = v4_resolve_lower_hir(v4_campaign_file, v4_campaign_hir)
pilot v4_campaign_ty: int = v4_ty_lower_resolve(v4_campaign_file, v4_campaign_resolve)
pilot v4_campaign_lex_error_count: int = v4_campaign_lex_errors(v4_campaign_stream)
pilot v4_campaign_parse_error_count: int = v4_campaign_parse_errors(v4_campaign_tree)
pilot v4_campaign_hir_error_count: int = v4_campaign_hir_errors(v4_campaign_hir)
pilot v4_campaign_resolve_error_count: int = v4_campaign_resolve_errors(v4_campaign_resolve)
pilot v4_campaign_ty_error_count: int = v4_campaign_ty_errors(v4_campaign_ty)
pilot v4_campaign_class: word = "none"
if v4_campaign_lex_error_count > 0 {{
    v4_campaign_class = "lexical"
}} else if v4_campaign_parse_error_count > 0 {{
    v4_campaign_class = "syntax"
}} else if v4_campaign_hir_error_count > 0 {{
    v4_campaign_class = "hir"
}} else if v4_campaign_resolve_error_count > 0 {{
    v4_campaign_class = "resolve"
}} else if v4_campaign_ty_error_count > 0 {{
    v4_campaign_class = "type"
}}
pilot v4_campaign_accepted: bool = v4_campaign_lex_error_count == 0 and v4_campaign_parse_error_count == 0 and v4_campaign_hir_error_count == 0 and v4_campaign_resolve_error_count == 0 and v4_campaign_ty_error_count == 0
say "V4_CAMPAIGN|accepted=" + word_from_bool(v4_campaign_accepted) + "|diagnostic-class=" + v4_campaign_class + "|source-bytes=" + word_from_int(v4_campaign_source.length()) + "|source-checksum=" + word_from_int(v4_campaign_source.checksum())
say "V4_PHASE|tokens=" + word_from_int(v4_lex_token_count(v4_campaign_stream)) + "|lex-diags=" + word_from_int(v4_lex_diag_count(v4_campaign_stream)) + "|parse-nodes=" + word_from_int(v4_parse_node_count(v4_campaign_tree)) + "|parse-diags=" + word_from_int(v4_parse_diag_count(v4_campaign_tree)) + "|hir-items=" + word_from_int(v4_hir_item_count(v4_campaign_hir)) + "|hir-diags=" + word_from_int(v4_hir_diag_count(v4_campaign_hir)) + "|symbols=" + word_from_int(v4_resolve_symbol_count(v4_campaign_resolve)) + "|resolve-diags=" + word_from_int(v4_resolve_diag_count(v4_campaign_resolve)) + "|signatures=" + word_from_int(v4_ty_signature_count(v4_campaign_ty)) + "|ty-diags=" + word_from_int(v4_ty_diag_count(v4_campaign_ty))
'''


def _flattened_crates() -> str:
    chunks: list[str] = []
    for crate in CRATE_ORDER:
        path = CRATES_ROOT / crate / "src/lib.fk"
        if not path.is_file():
            raise RuntimeError(f"missing V4 crate: {path}")
        chunks.append(f"-- flattened from {crate}\n")
        chunks.append(path.read_text(encoding="utf-8"))
        chunks.append("\n")
    return "\n".join(chunks)


def _visual_studio_environment(base: dict[str, str]) -> dict[str, str]:
    if not sys.platform.startswith("win") or base.get("INCLUDE"):
        return base
    candidates: list[Path] = []
    for root in (Path("C:/Program Files/Microsoft Visual Studio"), Path("C:/Program Files (x86)/Microsoft Visual Studio")):
        if root.is_dir():
            candidates.extend(root.glob("*/*/VC/Auxiliary/Build/vcvars64.bat"))
    if not candidates:
        return base
    command = [
        "cmd.exe",
        "/d",
        "/s",
        "/c",
        f'call "{sorted(candidates)[-1]}" >nul && set',
    ]
    result = run_bounded(
        command,
        cwd=ROOT,
        env=base,
        timeout_seconds=30,
        memory_limit_mb=256,
        output_limit_mb=4,
    )
    if result.returncode != 0:
        return base
    enriched = dict(base)
    for line in result.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            enriched[key] = value
    return enriched


def _resolve_clang(requested: str | None, environment: dict[str, str]) -> str:
    candidates = [requested] if requested else []
    if sys.platform.startswith("win") and not requested:
        candidates.append("x86_64-w64-mingw32-clang")
    if not requested:
        candidates.append("clang")
    for candidate in candidates:
        if not candidate:
            continue
        found = shutil.which(candidate, path=environment.get("PATH"))
        if found:
            return str(Path(found).resolve())
        path = Path(candidate).expanduser()
        if path.is_file():
            return str(path.resolve())
    raise RuntimeError("clang not found; V4 semantic probe is unavailable")


def _compiler_environment(clang_path: str) -> tuple[dict[str, str], bool]:
    environment = os.environ.copy()
    lowered_clang = str(Path(clang_path)).lower()
    is_llvm_mingw = "w64-mingw32-clang" in Path(clang_path).name.lower() or "llvm-mingw" in lowered_clang
    if is_llvm_mingw:
        for key in (
            "INCLUDE",
            "LIB",
            "LIBPATH",
            "UniversalCRTSdkDir",
            "VCINSTALLDIR",
            "VCToolsInstallDir",
            "WindowsSdkDir",
        ):
            environment.pop(key, None)
        return environment, True
    return _visual_studio_environment(environment), False


def _inherits_campaign_process_group() -> bool:
    return (
        not sys.platform.startswith("win")
        and os.environ.get(PROCESS_GROUP_HELD_ENV) == "1"
    )


def _posix_nested_process_group_self_test() -> None:
    """Prove an outer bound observes and kills a nested bounded child tree."""

    assert _owns_posix_process_group(False, False) is True
    assert _owns_posix_process_group(False, True) is False
    assert _owns_posix_process_group(True, False) is False
    assert _owns_posix_process_group(True, True) is False
    if sys.platform.startswith("win"):
        return

    with tempfile.TemporaryDirectory(prefix="freak-campaign-process-tree-") as temporary:
        root = Path(temporary)
        inner_pid_path = root / "inner.pid"
        inner_code = "\n".join(
            [
                "import os",
                "import time",
                "from pathlib import Path",
                f"Path({str(inner_pid_path)!r}).write_text(str(os.getpid()), encoding='ascii')",
                "payload = bytearray(128 * 1024 * 1024)",
                "time.sleep(30)",
            ]
        )
        middle_code = "\n".join(
            [
                "import sys",
                "from pathlib import Path",
                f"sys.path.insert(0, {str(Path(__file__).resolve().parent)!r})",
                "from campaign_probe import run_bounded",
                "run_bounded(",
                f"    [sys.executable, '-c', {inner_code!r}],",
                f"    cwd=Path({str(root)!r}),",
                "    timeout_seconds=30,",
                "    memory_limit_mb=256,",
                "    output_limit_mb=1,",
                "    inherit_posix_process_group=True,",
                ")",
            ]
        )
        try:
            run_bounded(
                [sys.executable, "-c", middle_code],
                cwd=root,
                timeout_seconds=15,
                memory_limit_mb=96,
                output_limit_mb=1,
            )
        except RuntimeError as exc:
            assert "memory limit exceeded" in str(exc), str(exc)
        else:
            raise AssertionError("outer process bound missed nested child memory")
        assert inner_pid_path.is_file(), "nested process did not record its PID"
        inner_pid = int(inner_pid_path.read_text(encoding="ascii"))
        for _ in range(100):
            try:
                os.kill(inner_pid, 0)
            except ProcessLookupError:
                break
            time.sleep(0.05)
        else:
            raise AssertionError("outer process bound left the nested child alive")


def parse_probe_output(output: str) -> dict[str, object]:
    campaign_lines = [
        line for line in output.splitlines() if line.startswith("V4_CAMPAIGN|")
    ]
    phase_lines = [line for line in output.splitlines() if line.startswith("V4_PHASE|")]
    if len(campaign_lines) != 1 or len(phase_lines) != 1:
        raise RuntimeError(f"V4 probe markers missing from output: {output[-2000:]}")
    campaign_line = campaign_lines[0]
    phase_line = phase_lines[0]
    fields: dict[str, str] = {}
    for part in campaign_line.split("|")[1:]:
        if part.count("=") != 1:
            raise RuntimeError(f"V4 probe campaign marker is malformed: {campaign_line}")
        key, value = part.split("=", 1)
        if key in fields:
            raise RuntimeError(f"V4 probe campaign marker duplicates {key!r}")
        fields[key] = value
    if set(fields) != {"accepted", "diagnostic-class", "source-bytes", "source-checksum"}:
        raise RuntimeError(f"V4 probe campaign marker fields are invalid: {campaign_line}")
    if fields.get("accepted") not in {"true", "false"}:
        raise RuntimeError(f"V4 probe accepted marker is invalid: {campaign_line}")
    if fields.get("diagnostic-class") not in {
        "none", "lexical", "syntax", "hir", "resolve", "type"
    }:
        raise RuntimeError(f"V4 probe diagnostic class is invalid: {campaign_line}")
    if (fields["accepted"] == "true") != (fields["diagnostic-class"] == "none"):
        raise RuntimeError(f"V4 probe acceptance and diagnostic class disagree: {campaign_line}")
    if not fields["source-bytes"].isdigit() or str(int(fields["source-bytes"])) != fields["source-bytes"]:
        raise RuntimeError(f"V4 probe source byte count is invalid: {campaign_line}")
    if not fields["source-checksum"].isdigit() or str(int(fields["source-checksum"])) != fields["source-checksum"]:
        raise RuntimeError(f"V4 probe source checksum is invalid: {campaign_line}")
    phase_pattern = (
        r"V4_PHASE\|tokens=\d+\|lex-diags=\d+\|parse-nodes=\d+"
        r"\|parse-diags=\d+\|hir-items=\d+\|hir-diags=\d+\|symbols=\d+"
        r"\|resolve-diags=\d+\|signatures=\d+\|ty-diags=\d+"
    )
    if re.fullmatch(phase_pattern, phase_line) is None:
        raise RuntimeError(f"V4 probe phase marker is invalid: {phase_line}")
    return {
        "accepted": fields.get("accepted") == "true",
        "diagnostic_class": fields.get("diagnostic-class", "tool"),
        "phase_summary": phase_line,
        "source_bytes": int(fields["source-bytes"]),
        "source_checksum": int(fields["source-checksum"]),
    }


def probe_source(
    source_path: Path,
    *,
    clang: str | None,
    timeout_seconds: int,
    memory_limit_mb: int,
    output_limit_mb: int,
) -> dict[str, object]:
    source_raw = source_path.read_bytes()
    try:
        source = source_raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError(f"source is not valid UTF-8: {source_path}") from exc
    fixture = build_probe_fixture(source)
    full_source = _flattened_crates() + "\n\n" + fixture
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from freakc.__main__ import transpile

    with tempfile.TemporaryDirectory(prefix="freak-v4-campaign-probe-") as temporary:
        build_root = Path(temporary)
        flat_path = build_root / "campaign-probe.flat.fk"
        c_source, diagnostics, uses_ui = transpile(full_source, flat_path)
        if diagnostics or c_source is None:
            rendered = "\n".join(str(item) for item in diagnostics[:40])
            raise RuntimeError(f"campaign probe bootstrap transpile failed:\n{rendered}")
        if uses_ui:
            raise RuntimeError("campaign probe unexpectedly requires the UI runtime")
        c_path = build_root / "campaign-probe.c"
        c_path.write_text(c_source, encoding="utf-8")
        suffix = ".exe" if sys.platform.startswith("win") else ""
        executable = build_root / f"campaign-probe{suffix}"
        clang_path = _resolve_clang(clang, os.environ.copy())
        environment, is_llvm_mingw = _compiler_environment(clang_path)
        compile_command = [
            str(clang_path),
            "-o",
            str(executable),
            str(c_path),
            str(RUNTIME_ROOT / "freak_runtime.c"),
            f"-I{RUNTIME_ROOT}",
            "-w",
            "-O0",
        ]
        if sys.platform.startswith("win"):
            if not is_llvm_mingw:
                for include_dir in environment.get("INCLUDE", "").split(os.pathsep):
                    if include_dir:
                        compile_command.extend(["-isystem", include_dir])
                for library_dir in environment.get("LIB", "").split(os.pathsep):
                    if library_dir:
                        compile_command.append(f"-L{library_dir}")
            compile_command.append("-lws2_32")
        if sys.platform.startswith("linux"):
            compile_command.append("-lm")
        compiled = run_bounded(
            compile_command,
            cwd=build_root,
            env=environment,
            timeout_seconds=timeout_seconds,
            memory_limit_mb=memory_limit_mb,
            output_limit_mb=output_limit_mb,
            inherit_posix_process_group=_inherits_campaign_process_group(),
        )
        if compiled.returncode != 0:
            raise RuntimeError(
                "V4 campaign probe C compilation failed:\n"
                + "command="
                + json.dumps(compile_command)
                + "\n"
                + compiled.stderr[-4000:]
            )
        runs = [
            run_bounded(
                [str(executable)],
                cwd=build_root,
                env=environment,
                timeout_seconds=timeout_seconds,
                memory_limit_mb=memory_limit_mb,
                output_limit_mb=output_limit_mb,
                inherit_posix_process_group=_inherits_campaign_process_group(),
            )
            for _ in range(2)
        ]
        for result in runs:
            if result.returncode != 0:
                raise RuntimeError(
                    f"V4 campaign probe failed with exit {result.returncode}:\n"
                    + (result.stdout + result.stderr)[-4000:]
                )
        parsed = [parse_probe_output(result.stdout + result.stderr) for result in runs]
        expected_source_bytes = len(source_raw)
        if any(result["source_bytes"] != expected_source_bytes for result in parsed):
            raise RuntimeError(
                "V4 probe did not reconstruct the exact UTF-8 source byte length: "
                f"expected={expected_source_bytes} actual={[result['source_bytes'] for result in parsed]}"
            )
        expected_source_checksum = stable_word_checksum(source_raw)
        if any(result["source_checksum"] != expected_source_checksum for result in parsed):
            raise RuntimeError(
                "V4 probe did not reconstruct the exact UTF-8 source checksum: "
                f"expected={expected_source_checksum} "
                f"actual={[result['source_checksum'] for result in parsed]}"
            )
        deterministic = parsed[0] == parsed[1]
        out = dict(parsed[0])
        out.update(
            {
                "schema": SCHEMA,
                "adapter": "embedded-v4-frontend-through-ty",
                "deterministic": deterministic,
                "source_sha256": hashlib.sha256(source_raw).hexdigest(),
                "native_program_executed": False,
                "peak_memory_bytes": max(result.peak_memory_bytes for result in runs),
            }
        )
        return out


def self_test(
    *, clang: str | None, timeout_seconds: int, memory_limit_mb: int, output_limit_mb: int
) -> None:
    source = (
        '-- opaque {not_interpolation} "quote" \\ /\t\x00\x01 snowman=☃\r\n'
        "task main() -> int {\r\n    give back 0\r\n}\r\n"
    )
    fixture = build_probe_fixture(source)
    assert "{not_interpolation}" not in fixture
    assert "snowman=☃" not in fixture
    assert "chr(123)" in fixture and "chr(9731)" in fixture
    assert fixture.index("pilot v4_campaign_source: word") < fixture.index("v4_source_add(")
    assert "pilot v4_campaign_accepted: bool" in fixture
    parsed = parse_probe_output(
        "V4_CAMPAIGN|accepted=true|diagnostic-class=none|source-bytes=7|source-checksum=9\n"
        "V4_PHASE|tokens=10|lex-diags=0|parse-nodes=2|parse-diags=0|hir-items=1|"
        "hir-diags=0|symbols=1|resolve-diags=0|signatures=1|ty-diags=0\n"
    )
    assert parsed == {
        "accepted": True,
        "diagnostic_class": "none",
        "phase_summary": "V4_PHASE|tokens=10|lex-diags=0|parse-nodes=2|parse-diags=0|"
        "hir-items=1|hir-diags=0|symbols=1|resolve-diags=0|signatures=1|ty-diags=0",
        "source_bytes": 7,
        "source_checksum": 9,
    }
    assert tuple(CRATE_ORDER)[-1] == "freak_ty"
    if sys.platform.startswith("win"):
        old_include = os.environ.get("INCLUDE")
        old_lib = os.environ.get("LIB")
        try:
            os.environ["INCLUDE"] = "C:/incompatible-msvc/include"
            os.environ["LIB"] = "C:/incompatible-msvc/lib"
            isolated, is_llvm_mingw = _compiler_environment(
                "C:/toolchains/llvm-mingw/bin/x86_64-w64-mingw32-clang.exe"
            )
            assert is_llvm_mingw and "INCLUDE" not in isolated and "LIB" not in isolated
        finally:
            if old_include is None:
                os.environ.pop("INCLUDE", None)
            else:
                os.environ["INCLUDE"] = old_include
            if old_lib is None:
                os.environ.pop("LIB", None)
            else:
                os.environ["LIB"] = old_lib
    try:
        run_bounded(["must-not-run"], cwd=ROOT, timeout_seconds=0)
    except RuntimeError as exc:
        assert "must all be positive" in str(exc)
    else:
        raise AssertionError("non-positive process limit was accepted")
    _posix_nested_process_group_self_test()

    sources = {
        "opaque-positive.fk": (source.encode("utf-8"), True, "none"),
        "syntax-negative.fk": (b"task main() -> int\n", False, "syntax"),
        "type-negative.fk": (
            b"fixed pilot ANSWER: int = true\n\ntask main() -> int {\n    give back 0\n}\n",
            False,
            "type",
        ),
    }
    with tempfile.TemporaryDirectory(prefix="freak-v4-campaign-self-test-") as temporary:
        root = Path(temporary)
        for filename, (raw_source, accepted, diagnostic_class) in sources.items():
            path = root / filename
            path.write_bytes(raw_source)
            observation = probe_source(
                path,
                clang=clang,
                timeout_seconds=timeout_seconds,
                memory_limit_mb=memory_limit_mb,
                output_limit_mb=output_limit_mb,
            )
            assert observation["accepted"] is accepted, (filename, observation)
            assert observation["diagnostic_class"] == diagnostic_class, (
                filename,
                observation,
            )
            assert observation["source_bytes"] == len(raw_source), (filename, observation)
            assert observation["source_checksum"] == stable_word_checksum(raw_source)
            assert observation["source_sha256"] == hashlib.sha256(raw_source).hexdigest()
            assert observation["deterministic"] is True
            assert observation["native_program_executed"] is False
    print(f"campaign probe self-test: PASS compiled={len(sources)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--clang")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--memory-limit-mb", type=int, default=768)
    parser.add_argument("--output-limit-mb", type=int, default=4)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.timeout <= 0 or args.memory_limit_mb <= 0 or args.output_limit_mb <= 0:
        parser.error("time, memory, and output limits must all be positive")
    if args.self_test:
        if os.environ.get("FREAK_CAMPAIGN_MUTEX_HELD") == "1":
            self_test(
                clang=args.clang,
                timeout_seconds=args.timeout,
                memory_limit_mb=args.memory_limit_mb,
                output_limit_mb=args.output_limit_mb,
            )
        else:
            with v4_host_mutex(timeout_seconds=args.timeout):
                self_test(
                    clang=args.clang,
                    timeout_seconds=args.timeout,
                    memory_limit_mb=args.memory_limit_mb,
                    output_limit_mb=args.output_limit_mb,
                )
        return 0
    if args.source is None or not args.source.is_file():
        parser.error("--source must name an existing .fk file")
    try:
        if os.environ.get("FREAK_CAMPAIGN_MUTEX_HELD") == "1":
            result = probe_source(
                args.source.resolve(),
                clang=args.clang,
                timeout_seconds=args.timeout,
                memory_limit_mb=args.memory_limit_mb,
                output_limit_mb=args.output_limit_mb,
            )
        else:
            with v4_host_mutex(timeout_seconds=args.timeout):
                result = probe_source(
                    args.source.resolve(),
                    clang=args.clang,
                    timeout_seconds=args.timeout,
                    memory_limit_mb=args.memory_limit_mb,
                    output_limit_mb=args.output_limit_mb,
                )
    except Exception as exc:
        print(json.dumps({"schema": SCHEMA, "adapter_error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0 if result["deterministic"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
