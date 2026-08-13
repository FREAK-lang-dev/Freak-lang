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

    def assign_and_resume(self, process: subprocess.Popen[bytes]) -> None:
        if not self.kernel32.AssignProcessToJobObject(self.handle, process._handle):
            raise ctypes.WinError(ctypes.get_last_error())
        status = self.ntdll.NtResumeProcess(process._handle)
        if status != 0:
            raise RuntimeError(f"NtResumeProcess failed with status {status}")

    def memory_bytes(self) -> int:
        info = self.info_type()
        if not self.kernel32.QueryInformationJobObject(
            self.handle, 9, ctypes.byref(info), ctypes.sizeof(info), None
        ):
            return 0
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


def _posix_group_memory(group_id: int) -> int:
    proc_root = Path("/proc")
    if not proc_root.is_dir():
        return 0
    total_kb = 0
    for entry in proc_root.iterdir():
        if not entry.name.isdigit():
            continue
        try:
            stat = (entry / "stat").read_text(encoding="ascii", errors="replace")
            close_paren = stat.rfind(")")
            fields = stat[close_paren + 2 :].split()
            if close_paren < 0 or len(fields) < 3 or int(fields[2]) != group_id:
                continue
            for line in (entry / "status").read_text(
                encoding="ascii", errors="replace"
            ).splitlines():
                if line.startswith("VmRSS:") or line.startswith("VmSwap:"):
                    total_kb += int(line.split()[1])
        except (OSError, ValueError):
            continue
    return total_kb * 1024


def run_bounded(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout_seconds: int = 60,
    memory_limit_mb: int = 512,
    output_limit_mb: int = 4,
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
        creationflags = 0x00000004 if windows_job is not None else 0
        with stdout_path.open("wb") as stdout_file, stderr_path.open("wb") as stderr_file:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=env,
                stdout=stdout_file,
                stderr=stderr_file,
                creationflags=creationflags,
                start_new_session=windows_job is None,
            )
            try:
                if windows_job is not None:
                    windows_job.assign_and_resume(process)
                started = time.monotonic()
                peak_memory = 0
                failure = ""
                while process.poll() is None:
                    elapsed = time.monotonic() - started
                    measured = (
                        windows_job.memory_bytes()
                        if windows_job is not None
                        else _posix_group_memory(process.pid)
                    )
                    peak_memory = max(peak_memory, measured)
                    if elapsed > timeout_seconds:
                        failure = f"timeout after {timeout_seconds}s"
                    elif measured > memory_limit:
                        failure = (
                            f"memory limit exceeded: {measured} > {memory_limit} bytes"
                        )
                    elif stdout_path.stat().st_size > output_limit or stderr_path.stat().st_size > output_limit:
                        failure = f"output limit exceeded: {output_limit_mb}MB per stream"
                    if failure:
                        if windows_job is not None:
                            windows_job.terminate()
                        else:
                            os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
                        break
                    time.sleep(0.05)
                measured = (
                    windows_job.memory_bytes()
                    if windows_job is not None
                    else _posix_group_memory(process.pid)
                )
                peak_memory = max(peak_memory, measured)
            finally:
                if process.poll() is None:
                    if windows_job is not None:
                        windows_job.terminate()
                    else:
                        os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
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


def _freak_word_literal(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def _freak_source_initialization(value: str) -> str:
    statements = ["pilot v4_campaign_source = \"\""]
    for line in value.splitlines(keepends=True):
        statements.append(
            "v4_campaign_source = v4_campaign_source + " + _freak_word_literal(line)
        )
    return "\n".join(statements)


def build_probe_fixture(source: str) -> str:
    """Build a fixed frontend probe; the inspected source is data, not the program."""

    return f'''-- Generated campaign probe. The source under test is embedded as data.
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

{_freak_source_initialization(source)}
pilot v4_campaign_file = v4_source_add("campaign-case.fk", v4_campaign_source)
pilot v4_campaign_stream = v4_lex_text(v4_campaign_file, v4_campaign_source)
pilot v4_campaign_tree = v4_parse_stream(v4_campaign_file, v4_campaign_stream)
pilot v4_campaign_expansion = v4_expand_identity(v4_campaign_file, v4_campaign_tree)
pilot v4_campaign_hir = v4_hir_lower_expanded(v4_campaign_file, v4_campaign_expansion)
pilot v4_campaign_resolve = v4_resolve_lower_hir(v4_campaign_file, v4_campaign_hir)
pilot v4_campaign_ty = v4_ty_lower_resolve(v4_campaign_file, v4_campaign_resolve)
pilot v4_campaign_lex_error_count = v4_campaign_lex_errors(v4_campaign_stream)
pilot v4_campaign_parse_error_count = v4_campaign_parse_errors(v4_campaign_tree)
pilot v4_campaign_hir_error_count = v4_campaign_hir_errors(v4_campaign_hir)
pilot v4_campaign_resolve_error_count = v4_campaign_resolve_errors(v4_campaign_resolve)
pilot v4_campaign_ty_error_count = v4_campaign_ty_errors(v4_campaign_ty)
pilot v4_campaign_class = "none"
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
pilot v4_campaign_accepted = v4_campaign_class == "none"
say "V4_CAMPAIGN|accepted=" + word_from_bool(v4_campaign_accepted) + "|diagnostic-class=" + v4_campaign_class
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


def parse_probe_output(output: str) -> dict[str, object]:
    campaign_line = next(
        (line for line in output.splitlines() if line.startswith("V4_CAMPAIGN|")), ""
    )
    phase_line = next(
        (line for line in output.splitlines() if line.startswith("V4_PHASE|")), ""
    )
    if not campaign_line or not phase_line:
        raise RuntimeError(f"V4 probe markers missing from output: {output[-2000:]}")
    fields: dict[str, str] = {}
    for part in campaign_line.split("|")[1:]:
        key, value = part.split("=", 1)
        fields[key] = value
    if fields.get("accepted") not in {"true", "false"}:
        raise RuntimeError(f"V4 probe accepted marker is invalid: {campaign_line}")
    if fields.get("diagnostic-class") not in {
        "none", "lexical", "syntax", "hir", "resolve", "type"
    }:
        raise RuntimeError(f"V4 probe diagnostic class is invalid: {campaign_line}")
    return {
        "accepted": fields.get("accepted") == "true",
        "diagnostic_class": fields.get("diagnostic-class", "tool"),
        "phase_summary": phase_line,
    }


def probe_source(
    source_path: Path,
    *,
    clang: str | None,
    timeout_seconds: int,
    memory_limit_mb: int,
    output_limit_mb: int,
) -> dict[str, object]:
    source = source_path.read_text(encoding="utf-8")
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
        environment = _visual_studio_environment(os.environ.copy())
        clang_path = clang or shutil.which("clang", path=environment.get("PATH"))
        if not clang_path:
            raise RuntimeError("clang not found; V4 semantic probe is unavailable")
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
            for include_dir in environment.get("INCLUDE", "").split(os.pathsep):
                if include_dir:
                    compile_command.extend(["-isystem", include_dir])
            for library_dir in environment.get("LIB", "").split(os.pathsep):
                if library_dir:
                    compile_command.append(f"-L{library_dir}")
        if sys.platform.startswith("linux"):
            compile_command.append("-lm")
        compiled = run_bounded(
            compile_command,
            cwd=build_root,
            env=environment,
            timeout_seconds=timeout_seconds,
            memory_limit_mb=1024,
            output_limit_mb=output_limit_mb,
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
        deterministic = parsed[0] == parsed[1]
        out = dict(parsed[0])
        out.update(
            {
                "schema": SCHEMA,
                "adapter": "embedded-v4-frontend-through-ty",
                "deterministic": deterministic,
                "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
                "native_program_executed": False,
                "peak_memory_bytes": max(result.peak_memory_bytes for result in runs),
            }
        )
        return out


def self_test() -> None:
    source = 'task main() -> int {\n    give back 0\n}\n'
    fixture = build_probe_fixture(source)
    assert 'v4_campaign_source = v4_campaign_source + "task main() -> int {\\n"' in fixture
    parsed = parse_probe_output(
        "V4_CAMPAIGN|accepted=true|diagnostic-class=none\n"
        "V4_PHASE|tokens=10|lex-diags=0|parse-nodes=2|parse-diags=0\n"
    )
    assert parsed == {
        "accepted": True,
        "diagnostic_class": "none",
        "phase_summary": "V4_PHASE|tokens=10|lex-diags=0|parse-nodes=2|parse-diags=0",
    }
    assert tuple(CRATE_ORDER)[-1] == "freak_ty"
    try:
        run_bounded(["must-not-run"], cwd=ROOT, timeout_seconds=0)
    except RuntimeError as exc:
        assert "must all be positive" in str(exc)
    else:
        raise AssertionError("non-positive process limit was accepted")
    print("campaign probe self-test: PASS")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--clang")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--memory-limit-mb", type=int, default=512)
    parser.add_argument("--output-limit-mb", type=int, default=4)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
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
            with v4_host_mutex():
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
