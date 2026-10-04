#!/usr/bin/env python3
"""Guarded private compiler-array prerequisite proof, not List/self-hosting.

Default is mandatory Linux ASan/UBSan; --plain is additional portability.
Every real tool/native command uses the central process-tree guard. Artifacts
are retained in a fresh directory, with source-only imports and final identity
checks before any PASS publication. No silently skipped capability is accepted.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
OPTS = (0, 2, 3)
COMPILE_SECONDS, COMPILE_MIB = 120, 1024
RUN_SECONDS, RUN_MIB = 60, 64
AUDIT_FLAGS = ("-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1", "-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1")
SANITIZER_FLAGS = ("-fsanitize=address,undefined", "-fno-sanitize-recover=all", "-fno-omit-frame-pointer")
PROFILES = {
    "pressure": ("-DFREAK_V4_COMPILER_ARRAY_LIVE_LIMIT=1024",),
    "dynamic": ("-DFREAK_V4_COMPILER_ARRAY_LIVE_LIMIT=0",),
    "retire": ("-DFREAK_V4_COMPILER_ARRAY_LIVE_LIMIT=1024", "-DFREAK_V4_COMPILER_ARRAY_GENERATION_MAX=3"),
    "capacity": ("-DFREAK_V4_COMPILER_ARRAY_LIVE_LIMIT=1024", "-DFREAK_V4_COMPILER_ARRAY_CAPACITY_LIMIT=2"),
}
POSITIVE_CASES = (
    ("pressure", "normal"), ("pressure", "quota"), ("pressure", "table-failure"),
    ("dynamic", "dynamic"), ("retire", "retire"), ("capacity", "capacity"),
)
NORMAL_ROWS = (
    "compiler-array-ownership=ok", "compiler-array-tickets=ok",
    "compiler-array-integer-facts=ok", "compiler-array-snapshot-join=ok",
    "compiler-array-rollback-recovery=ok",
)
PROFILE_ROWS = {
    "quota": "compiler-array-quota1024=ok", "dynamic": "compiler-array-dynamic100000=ok",
    "retire": "compiler-array-generation-retirement=ok", "capacity": "compiler-array-capacity-rollback=ok",
    "table-failure": "compiler-array-table-rollback=ok",
}
EXIT_CASES = {
    "fatal-null-out": "FREAK: V4 compiler arrays: invalid result slot\n",
    "fatal-index-negative": "FREAK: array_set index -1 out of bounds (len 0)\n",
    "fatal-index-end": "FREAK: array_set index 0 out of bounds (len 0)\n",
    "fatal-push-resource": "FREAK: V4 compiler arrays: out of memory growing array\n",
    "fatal-set-resource": "FREAK: V4 compiler arrays: out of memory replacing array word\n",
    "fatal-get-resource": "FREAK: V4 compiler arrays: out of memory copying array word\n",
    "fatal-join-resource": "FREAK: V4 compiler arrays: out of memory joining words\n",
    "fatal-get-empty-malloc": "FREAK: V4 compiler arrays: out of memory copying array word\n",
    "fatal-get-empty-adopt": "FREAK: V4 compiler arrays: out of memory copying array word\n",
    "fatal-join-empty-malloc": "FREAK: V4 compiler arrays: out of memory joining words\n",
    "fatal-join-empty-adopt": "FREAK: V4 compiler arrays: out of memory joining words\n",
}
ABORT_CASES = {
    "fatal-word-null": "word value has been consumed",
    "fatal-word-foreign": "word value is not live owned storage",
    "fatal-word-released": "word value is not live owned storage",
    "fatal-word-utf8": "invalid UTF-8",
}


def output_bytes(value: bytes | str) -> bytes:
    return value.encode("utf-8") if isinstance(value, str) else value


def normalized(value: bytes | str, platform: str) -> bytes:
    data = output_bytes(value)
    return data.replace(b"\r\n", b"\n") if platform == "win32" else data


def exact_result(result, status: int, stdout: bytes, stderr: bytes, *, platform: str = sys.platform) -> None:
    actual = (result.returncode, normalized(result.stdout, platform), normalized(result.stderr, platform))
    expected = (status, stdout, stderr)
    if actual != expected:
        raise AssertionError(f"expected {expected!r}; actual {actual!r}")


def positive_stdout(case: str) -> bytes:
    rows = NORMAL_ROWS if case == "normal" else (PROFILE_ROWS[case],)
    return ("\n".join(rows) + "\n").encode()


def assert_positive(result, case: str, *, platform: str = sys.platform) -> None:
    exact_result(result, 0, positive_stdout(case), b"", platform=platform)


def assert_rejection(result, case: str, *, platform: str = sys.platform) -> None:
    if case in EXIT_CASES:
        status, diagnostic = 1, EXIT_CASES[case]
    else:
        status = 3 if platform == "win32" else -signal.SIGABRT
        diagnostic = "FREAK: V4 word panic: " + ABORT_CASES[case] + "\n"
    exact_result(result, status, b"", diagnostic.encode(), platform=platform)


def assert_audit(result, kind: str, *, platform: str = sys.platform) -> None:
    if kind not in ("C", "LLVM"):
        raise AssertionError("unknown ownership capability")
    exact_result(result, 87 if kind == "C" else 86, b"",
                 f"FREAK: {kind} ownership audit found 1 unreleased word allocation(s)\n".encode(), platform=platform)


def assert_sanitizer(result, kind: str) -> None:
    signatures = {
        "address": (b"ERROR: AddressSanitizer: heap-use-after-free", b"SUMMARY: AddressSanitizer:"),
        "undefined": (b"runtime error: signed integer overflow", b"SUMMARY: UndefinedBehaviorSanitizer:"),
    }
    if kind not in signatures:
        raise AssertionError("unknown sanitizer capability")
    stderr = output_bytes(result.stderr)
    if (result.returncode != 88 or output_bytes(result.stdout) or
            any(token not in stderr for token in signatures[kind]) or
            any(token in stderr for token in (b"ownership audit", b"V4 word panic", b"LeakSanitizer"))):
        raise AssertionError("missing real sanitizer capability")


def validate_flags(flags: list[str], profile: str, sanitized: bool) -> None:
    required = (*AUDIT_FLAGS, "-DFREAK_ARRAY_LIVE_LIMIT=1024", *PROFILES[profile],
                *(SANITIZER_FLAGS if sanitized else ()))
    if any(flag not in flags for flag in required) or "-DNDEBUG" in flags:
        raise AssertionError("required assertions, quotas, audits or sanitizer flags missing")


def validate_completion(report: dict, sanitized: bool) -> None:
    positives = [(opt, profile, case) for opt in OPTS for profile, case in POSITIVE_CASES]
    rejections = [(opt, case) for opt in OPTS for case in (*EXIT_CASES, *ABORT_CASES)]
    capabilities = [f"audit-{kind}-O{opt}" for opt in OPTS for kind in ("C", "LLVM")]
    if sanitized:
        capabilities += ["sanitizer-address", "sanitizer-undefined"]
    actual_positive = [(row["opt"], row["profile"], row["case"]) for row in report["positives"]]
    actual_rejections = [(row["opt"], row["case"]) for row in report["rejections"]]
    actual_production = [(row["opt"], row["profile"]) for row in report["production"]]
    expected_production = [(opt, profile) for opt in OPTS for profile in PROFILES]
    if (OPTS != (0, 2, 3) or report["sanitized"] != sanitized or
            actual_positive != positives or actual_rejections != rejections or
            actual_production != expected_production or report["capabilities"] != capabilities or
            any(not re.fullmatch(r"[a-f0-9]{64}", row["binary_sha256"]) for row in report["positives"]) or
            any(not re.fullmatch(r"[a-f0-9]{64}", row["object_sha256"]) for row in report["production"])):
        raise AssertionError("incomplete mandatory optimization/profile/capability matrix")


def namespace_source_guard(source: str) -> None:
    """Pin the concrete legacy pool fence on which biased tickets depend."""
    if not re.search(r"^#define FREAK_LLVM_MAX_ARRAYS 1024\s*$", source, re.M):
        raise AssertionError("legacy LLVM pool capacity changed: revalidate private ticket namespace")
    start = source.index("static int64_t freak_llvm_array_slot_for_handle(")
    end = source.index("\nint64_t freak_llvm_array_new(", start)
    decoder = source[start:end]
    constructor_end = source.index("\nint64_t freak_llvm_word_snapshot_lines(", end)
    constructor = source[end:constructor_end]
    if ("if (handle < 0) return -1;" not in decoder or
            "slot >= freak_llvm_array_count" not in decoder or
            "freak_llvm_arrays[slot]" not in decoder or
            "freak_llvm_array_count >= FREAK_LLVM_MAX_ARRAYS" not in constructor):
        raise AssertionError("legacy LLVM slot admission changed: revalidate private ticket namespace")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def head_identity() -> str:
    dotgit = ROOT / ".git"
    gitdir = dotgit if dotgit.is_dir() else Path(dotgit.read_text().strip().removeprefix("gitdir: "))
    if not gitdir.is_absolute():
        gitdir = (ROOT / gitdir).resolve()
    head = (gitdir / "HEAD").read_text().strip()
    if head.startswith("ref: "):
        common = gitdir
        if (gitdir / "commondir").exists():
            common = (gitdir / (gitdir / "commondir").read_text().strip()).resolve()
        ref = head.removeprefix("ref: ")
        path = common / ref
        if path.exists():
            head = path.read_text().strip()
        else:
            rows = (common / "packed-refs").read_text().splitlines()
            head = next(row.split(" ", 1)[0] for row in rows if row.endswith(" " + ref))
    if not re.fullmatch(r"[a-f0-9]{40}", head):
        raise AssertionError("invalid source HEAD identity")
    return head


def source_paths() -> tuple[Path, ...]:
    relative = (
        "freakc/runtime/freak_runtime.c", "freakc/runtime/freak_runtime.h",
        "freakc/runtime/freak_llvm_runtime.c", "freakc/runtime/freak_v4_word_runtime.c",
        "freakc/runtime/freak_v4_word_runtime.h", "freakc/runtime/freak_v4_compiler_array_runtime.c",
        "freakc/runtime/freak_v4_compiler_array_runtime.h", "tests/v4_compiler_array_runtime_probe.c",
        "tests/v4_compiler_array_runtime.py", "tests/test_v4_compiler_array_runtime.py",
        "src/compiler/v4/COMPILER_ARRAY_RUNTIME_CONTRACT.md", "src/compiler/v4/check_v4.py",
    )
    return tuple(ROOT / path for path in relative) + tuple(sorted((ROOT / "freakc").glob("**/*.py")))


def restore_proof_environment(kind: str, name: str, value) -> None:
    """Dispatch pre-created cleanup records inside the caller's error fence."""
    if kind == "sys":
        setattr(sys, name, value)
    elif value is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = value


@contextmanager
def proof_environment(directory: Path, sanitized: bool):
    names = ("ASAN_OPTIONS", "LSAN_OPTIONS", "UBSAN_OPTIONS", "PYTHONPYCACHEPREFIX", "PYTHONDONTWRITEBYTECODE")
    previous = {name: os.environ.get(name) for name in names}
    old_prefix, old_write = sys.pycache_prefix, sys.dont_write_bytecode
    # All restoration records are constructed before any environment mutation
    # or body execution. No closure/callback is allocated during unwinding.
    restores = (("sys", "pycache_prefix", old_prefix), ("sys", "dont_write_bytecode", old_write),
                *(("env", name, previous[name]) for name in names))
    prefix = directory / "unused-source-cache"
    if prefix.exists():
        raise AssertionError("source cache namespace must be virgin")
    try:
        for name in names:
            os.environ.pop(name, None)
        os.environ["PYTHONPYCACHEPREFIX"] = str(prefix)
        os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
        sys.pycache_prefix, sys.dont_write_bytecode = str(prefix), True
        if sanitized:
            os.environ["ASAN_OPTIONS"] = "halt_on_error=1:detect_leaks=1:exitcode=88"
            os.environ["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1:exitcode=88"
        yield prefix
    finally:
        primary = sys.exception()
        first_cleanup = None

        for kind, name, value in restores:
            try:
                # Dispatch setup and the action share one independent fence,
                # so a failed entry still permits every later restoration.
                restore_proof_environment(kind, name, value)
            except BaseException as error:
                if first_cleanup is None:
                    first_cleanup = error
                target = primary if primary is not None else first_cleanup
                if target is not error:
                    try:
                        BaseException.add_note(target, "private array environment cleanup: " + type(error).__name__)
                    except BaseException:
                        pass

        if primary is None and first_cleanup is not None:
            raise first_cleanup


def load_checks():
    def source_audit(event, args):
        if event == "open" and args and isinstance(args[0], (str, bytes, os.PathLike)):
            path = Path(os.fsdecode(args[0])).resolve()
            if path.suffix == ".pyc" and (path == ROOT or ROOT in path.parents):
                raise AssertionError("unsealed repository bytecode input")
    sys.addaudithook(source_audit)
    path = ROOT / "src/compiler/v4/check_v4.py"
    spec = importlib.util.spec_from_file_location("private_array_runtime_checks", path)
    module = importlib.util.module_from_spec(spec)
    # Compile the authoritative source explicitly; the import loader never gets
    # an opportunity to consume a stale cached check_v4 module.
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


class ProofIdentity:
    def __init__(self, paths, selected: Path, resolved: Path, prefix: Path, *, head=None, sources=None):
        self.head = head_identity() if head is None else head
        self.sources = {str(path.relative_to(ROOT)): sha(path) for path in paths} if sources is None else dict(sources)
        self.selected, self.resolved, self.prefix = selected, resolved, prefix
        self.tool_sha = sha(resolved)
        self.artifacts = {}

    def pin(self, *, check_imports=True):
        if (head_identity() != self.head or self.selected.resolve(strict=True) != self.resolved or
                sha(self.resolved) != self.tool_sha or self.prefix.exists() or
                (check_imports and (sys.pycache_prefix != str(self.prefix) or not sys.dont_write_bytecode or
                 os.environ.get("PYTHONPYCACHEPREFIX") != str(self.prefix) or
                 os.environ.get("PYTHONDONTWRITEBYTECODE") != "1")) or
                any(sha(ROOT / path) != digest for path, digest in self.sources.items()) or
                any(sha(path) != digest for path, digest in self.artifacts.items())):
            raise AssertionError("source/tool/binary/cache identity changed during native proof")

    def seal(self, path: Path):
        if path in self.artifacts:
            raise AssertionError("compiled artifact identity was already published")
        self.artifacts[path] = sha(path)


class Runner:
    def __init__(self, checks, directory: Path, identity=None):
        self.checks, self.directory, self.serial = checks, directory, 0
        self.identity = identity

    def run(self, command: list[str], label: str, *, compile_job: bool = False):
        self.serial += 1
        stem = self.directory / f"{self.serial:03d}-{re.sub(r'[^a-zA-Z0-9_-]', '-', label)}"
        timeout = COMPILE_SECONDS if compile_job else RUN_SECONDS
        memory = COMPILE_MIB if compile_job else RUN_MIB
        result = None
        try:
            if self.identity:
                self.identity.pin()
            stem.with_suffix(".command.json").write_text(json.dumps(
                {"argv": command, "timeout_seconds": timeout, "memory_limit_mib": memory,
                 "output_limit_mib_per_stream": 8}, indent=2) + "\n")
            if self.identity:
                self.identity.pin()
            result = self.checks.run_with_heartbeat(command, label=label, timeout_seconds=timeout,
                                                  memory_limit_mb=memory, output_limit_mb=8)
            if self.identity:
                self.identity.pin()
                if compile_job and result.returncode == 0:
                    self.identity.seal(Path(command[command.index("-o") + 1]))
            stem.with_suffix(".stdout").write_bytes(output_bytes(result.stdout))
            stem.with_suffix(".stderr").write_bytes(output_bytes(result.stderr))
            stem.with_suffix(".result.json").write_text(json.dumps({"exit": result.returncode}) + "\n")
            if self.identity:
                self.identity.pin()
        except BaseException:
            # Central guard owns reaping and structured first-cause output.
            # Optional artifact attribution must not mask cancellation/failure.
            error = sys.exception()
            for suffix, attribute in (("failure.txt", None), ("stdout", "output"), ("stderr", "stderr")):
                try:
                    if attribute is None:
                        value = type(error).__name__ + "\n"
                    elif result is not None:
                        value = getattr(result, "stdout" if attribute == "output" else attribute)
                    else:
                        value = getattr(error, attribute, None)
                    if value is not None:
                        stem.with_suffix("." + suffix).write_bytes(output_bytes(value))
                except BaseException:
                    pass
            raise
        return result


def run_gate(args, directory: Path, report: dict, prefix: Path) -> ProofIdentity:
    paths = source_paths()
    head = head_identity()
    frozen = {str(path.relative_to(ROOT)): sha(path) for path in paths}
    report.update({"head": head, "source_hashes": frozen, "source_cache": str(prefix)})
    namespace_source_guard((ROOT / "freakc/runtime/freak_llvm_runtime.c").read_text())
    checks = load_checks()
    selected = Path(shutil.which(args.clang) or args.clang).absolute()
    clang = selected.resolve(strict=True)
    identity = ProofIdentity(paths, selected, clang, prefix, head=head, sources=frozen)
    identity.pin()
    runner = Runner(checks, directory, identity)
    report["clang"] = {"requested": args.clang, "selected": str(selected), "resolved": str(clang), "sha256": identity.tool_sha}
    runtime = ROOT / "freakc/runtime"
    production, word = runtime / "freak_v4_compiler_array_runtime.c", runtime / "freak_v4_word_runtime.c"
    probe = ROOT / "tests/v4_compiler_array_runtime_probe.c"
    suffix = ".exe" if sys.platform == "win32" else ""
    libs = ["-lws2_32"] if sys.platform == "win32" else ["-lm"]
    sanitized = not args.plain
    for opt in OPTS:
        binaries = {}
        for profile, profile_flags in PROFILES.items():
            flags = ["-std=c11", f"-O{opt}", "-g", *AUDIT_FLAGS, "-DFREAK_ARRAY_LIVE_LIMIT=1024",
                     *profile_flags, "-I", str(runtime), *(SANITIZER_FLAGS if sanitized else ())]
            validate_flags(flags, profile, sanitized)
            report["flags"][f"{profile}-O{opt}"] = flags
            obj = directory / f"production-{profile}.O{opt}.o"
            result = runner.run([str(clang), *flags, "-Wall", "-Wextra", "-Werror", "-c", str(production),
                                 "-o", str(obj)], f"production {profile} O{opt}", compile_job=True)
            exact_result(result, 0, b"", b"")
            report["production"].append({"opt": opt, "profile": profile, "object_sha256": sha(obj)})
            binary = directory / f"compiler-arrays-{profile}.O{opt}{suffix}"
            result = runner.run([str(clang), *flags, str(probe), str(word), "-o", str(binary), *libs],
                                f"compile {profile} O{opt}", compile_job=True)
            if result.returncode != 0:
                raise AssertionError("native private-array probe failed compilation; see retained channels")
            binaries[profile] = binary
        for profile, case in POSITIVE_CASES:
            binary = binaries[profile]
            assert_positive(runner.run([str(binary), case], f"positive {profile} O{opt} {case}"), case)
            report["positives"].append({"opt": opt, "profile": profile, "case": case, "binary_sha256": sha(binary)})
        binary = binaries["pressure"]
        for case in (*EXIT_CASES, *ABORT_CASES):
            assert_rejection(runner.run([str(binary), case], f"reject O{opt} {case}"), case)
            report["rejections"].append({"opt": opt, "case": case})
        for kind, mode in (("C", "audit-c-word"), ("LLVM", "audit-word")):
            assert_audit(runner.run([str(binary), mode], f"audit {kind} O{opt}"), kind)
            report["capabilities"].append(f"audit-{kind}-O{opt}")
        if sanitized and opt == 0:
            for kind in ("address", "undefined"):
                assert_sanitizer(runner.run([str(binary), "sanitizer-" + kind], "sanitizer " + kind), kind)
                report["capabilities"].append("sanitizer-" + kind)
    # Capability ordering follows actual execution; final matrix is canonical.
    report["capabilities"].sort(key=lambda value: (value.startswith("sanitizer-"),
                                                int(value.rsplit("O", 1)[1]) if "-O" in value else 0,
                                                value.startswith("audit-LLVM"), value))
    validate_completion(report, sanitized)
    identity.pin()
    report["compiled_artifact_hashes"] = {str(path): digest for path, digest in identity.artifacts.items()}
    report["final_conservation"] = True
    return identity


def publish(directory: Path, report: dict) -> None:
    (directory / "results.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    manifest = {path.name: {"bytes": path.stat().st_size, "sha256": sha(path)}
                for path in sorted(directory.iterdir()) if path.is_file() and path.name != "artifact-hashes.json"}
    (directory / "artifact-hashes.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--clang", default=os.environ.get("FREAK_CLANG") or shutil.which("clang"))
    parser.add_argument("--plain", action="store_true")
    parser.add_argument("--work", type=Path)
    args = parser.parse_args()
    if not args.clang:
        parser.error("Clang is required; the private-array capability gate cannot be skipped")
    if not args.plain and not sys.platform.startswith("linux"):
        parser.error("mandatory sanitizer gate requires Linux; --plain is additional portability")
    directory = args.work.resolve() if args.work else Path(tempfile.mkdtemp(prefix="freak-v4-compiler-arrays-"))
    if args.work:
        directory.mkdir(parents=True, exist_ok=False)
    report = {"complete": False, "platform": sys.platform, "sanitized": not args.plain,
              "budgets": {"compile_seconds": COMPILE_SECONDS, "compile_mib": COMPILE_MIB,
                          "run_seconds": RUN_SECONDS, "run_mib": RUN_MIB,
                          "pressure_private_live_quota": 1024, "default_private_live_quota": 0},
              "flags": {}, "production": [], "positives": [], "rejections": [], "capabilities": []}
    print(f"Private compiler-array artifacts: {directory}", flush=True)
    try:
        with proof_environment(directory, not args.plain) as prefix:
            identity = run_gate(args, directory, report, prefix)
        identity.pin(check_imports=False)
        report["complete"] = True
        publish(directory, report)
        identity.pin(check_imports=False)
    except BaseException:
        # First failure/cancellation stays authoritative even if optional JSON
        # attribution/retention fails. Never print PASS from a finally block.
        try:
            report["complete"] = False
            report["failure_type"] = type(sys.exception()).__name__
        except BaseException:
            pass
        try:
            publish(directory, report)
        except BaseException:
            pass
        raise
    print(f"Private compiler-array prerequisite PASS: 18 positive executions,45 exact rejections, "
          f"{len(report['capabilities'])} real capabilities; {'plain' if args.plain else 'ASan/UBSan'}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
