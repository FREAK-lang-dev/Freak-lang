#!/usr/bin/env python3
"""Installed public CLI runtime-object cache controls, with retained raw evidence.

The native gate deliberately requires a qualified installed CLI and selected
Clang. It never builds a replacement CLI or falls back to a repository compiler.
Linux strace records real child execve argv; other platforms record the declared
conservative tool-closure boundary and must receive separate native coverage.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "freak-runtime-object-v1"
EVENT = re.compile(r"^FREAK_RUNTIME_CACHE (hit|compile|fallback) (\S+) ([0-9a-f]{64})?$", re.M)
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def task_source(source: str, name: str) -> str:
    """Extract the actual FREAK task, preserving its body for native controls."""
    pattern = re.compile(rf"^task {re.escape(name)}\([^\n]+", re.M)
    match = pattern.search(source)
    if not match:
        raise AssertionError(f"missing task {name}")
    cursor = source.index("{", match.start())
    start = match.start()
    depth = 0
    quoted = False
    comment = False
    escaped = False
    for index in range(cursor, len(source)):
        ch = source[index]
        if comment:
            if ch == "\n":
                comment = False
            continue
        if quoted:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                quoted = False
            continue
        if ch == '"':
            quoted = True
        elif source[index:index + 2] == "--":
            comment = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return source[start:index + 1] + "\n"
    raise AssertionError(f"unterminated task {name}")


def fk_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t") + '"'


def dependency_harness(source: str) -> tuple[str, int]:
    # These are Make/Clang grammar examples, not a Python reimplementation.
    rows = [
        (False, "freak-cache: /a.c /b.h\n", ["/a.c", "/b.h"]),
        (False, "freak-cache: /a\\ b.h /hash\\#name.h\n", ["/a b.h", "/hash#name.h"]),
        (False, "freak-cache: /a.c \\\n /b.h\n", ["/a.c", "/b.h"]),
        (False, "freak-cache: /a.c \\\r\n\t/b.h\r\n", ["/a.c", "/b.h"]),
        (False, "freak-cache: /cash$$name.h /colon\\:name.h\n", ["/cash$name.h", "/colon:name.h"]),
        (True, r"freak-cache: C\:/a.c C:\SDK\header.h" + "\n", ["C:/a.c", r"C:\SDK\header.h"]),
        (True, r"freak-cache: C\:/Program\ Files/h.h" + "\n", ["C:/Program Files/h.h"]),
        (False, "wrong-target: /a.h\n", None),
        (False, "freak-cache:\n", None),
        (False, "freak-cache: /a.h # ignored.h\n", None),
        (False, "freak-cache: /cash$name.h\n", None),
        (False, "freak-cache: /unfinished\\", None),
        (False, "freak-cache: /unknown\\q.h\n", None),
        (False, "freak-cache: " + " /a.h" * 4097 + "\n", None),
    ]
    chunks = [
        'pilot CLI_RUNTIME_CACHE_META_LIMIT = 1048576\npilot CLI_RUNTIME_CACHE_DEP_LIMIT = 4096\n',
        'pilot mut simulated_windows = false\npilot mut observed = 0\n',
        'task cli_is_windows() -> bool { give back simulated_windows }\n',
        'task cli_runtime_cache_raw_pin(path: word, retain: bool) -> word { array_push(observed, path) give back "pin:" + path }\n',
        task_source(source, "cli_runtime_cache_dependencies"),
        'task require(value: bool, label: word) -> void { if not value { say label process::exit(1) } }\n',
        'task main() -> int {\n',
    ]
    for index, (windows, text, expected) in enumerate(rows):
        chunks.extend([
            f"simulated_windows = {'true' if windows else 'false'}\nobserved = array_new()\n",
            f"pilot result{index} = cli_runtime_cache_dependencies({fk_quote(text)}, false)\n",
            f"require((result{index} != \"\") == {'true' if expected is not None else 'false'}, \"dependency admission {index}\")\n",
        ])
        if expected is not None:
            chunks.append(f'require(array_len(observed) == {len(expected)}, "dependency count {index}")\n')
            for item, path in enumerate(expected):
                chunks.append(f'require(array_get(observed, {item}) == {fk_quote(path)}, "dependency path {index}/{item}")\n')
        chunks.append("array_release(observed)\n")
    chunks.append('say "dependency controls passed"\ngive back 0\n}\n')
    return "".join(chunks), len(rows)


class SourceControls(unittest.TestCase):
    """Small source guards for review boundaries; these are not native proof."""
    def setUp(self) -> None:
        self.source = (ROOT / "src/cli/runtime_cache.fk").read_text()

    def test_gate_extracts_actual_dependency_task(self) -> None:
        harness, cases = dependency_harness(self.source)
        self.assertIn(task_source(self.source, "cli_runtime_cache_dependencies"), harness)
        self.assertEqual(cases, 14)

    def test_syntax_extractor_respects_literals_and_comments(self) -> None:
        self.assertEqual(task_source('task demo() -> void { say "}" -- }\n}\n', "demo"), 'task demo() -> void { say "}" -- }\n}\n')

    def test_no_shell_cache_commands_or_unbounded_cache_reads(self) -> None:
        self.assertNotIn("process::exec", self.source)
        self.assertNotIn("fs::read(", self.source)
        self.assertNotIn("fs::write(", self.source)
        self.assertNotIn("fs::delete(", self.source)
        self.assertIn("CLI_RUNTIME_CACHE_FILE_LIMIT = 67108864", self.source)
        self.assertIn("CLI_RUNTIME_CACHE_META_LIMIT = 1048576", self.source)
        self.assertIn("CLI_RUNTIME_CACHE_DEP_LIMIT = 4096", self.source)

    def test_publication_cleans_only_unpublished_owner(self) -> None:
        body = task_source(self.source, "cli_runtime_cache_publish")
        self.assertIn("if not completed {", body)
        self.assertNotIn("remove_relative_file", body)
        self.assertNotIn("rename_relative", body)
        self.assertIn("publish_temp_dir_checked(entry, root, key)", body)


class Evidence:
    def __init__(self, root: Path) -> None:
        root.mkdir(parents=True, exist_ok=False)
        self.root = root.resolve()
        self.report = {"schema": "freak.runtime-cache-gate.v1", "outcome": "running", "commands": [], "cases": [], "inputs": []}
        self.save()

    def save(self) -> None:
        staging = self.root / "report.new"
        staging.write_text(json.dumps(self.report, indent=2) + "\n")
        staging.replace(self.root / "report.json")

    def pin(self, path: Path) -> None:
        path = path.resolve()
        self.report["inputs"].append({"path": str(path), "sha256": sha(path)})
        self.save()

    def invoke(self, argv: list[str], cwd: Path, env: dict[str, str], label: str, *, trace: bool = False, timeout: int = 240) -> tuple[int, str, str]:
        number = len(self.report["commands"])
        prefix = self.root / f"{number:03}-{label}"
        trace_path = prefix.with_suffix(".execve")
        actual = list(argv)
        if trace:
            actual = ["strace", "-f", "-s", "65536", "-e", "trace=execve", "-o", str(trace_path), "--", *argv]
        record = {"argv": actual, "cwd": str(cwd), "label": label, "timeout_seconds": timeout, "status": "running"}
        self.report["commands"].append(record)
        self.save()
        started = time.monotonic()
        with prefix.with_suffix(".stdout").open("wb") as output, prefix.with_suffix(".stderr").open("wb") as errors:
            try:
                result = subprocess.run(actual, cwd=cwd, env=env, stdout=output, stderr=errors, timeout=timeout, check=False, start_new_session=os.name != "nt")
            except subprocess.TimeoutExpired:
                record.update(status="timed_out", elapsed_ms=int((time.monotonic() - started) * 1000))
                self.save()
                raise
        record.update(status="completed", returncode=result.returncode, elapsed_ms=int((time.monotonic() - started) * 1000))
        for suffix in (".stdout", ".stderr"):
            path = prefix.with_suffix(suffix)
            record[suffix[1:]] = {"path": str(path), "bytes": path.stat().st_size, "sha256": sha(path)}
        if trace:
            record["execve"] = {"path": str(trace_path), "sha256": sha(trace_path)}
        self.save()
        text = ANSI.sub("", prefix.with_suffix(".stdout").read_bytes().decode("utf-8", "replace") + prefix.with_suffix(".stderr").read_bytes().decode("utf-8", "replace"))
        return result.returncode, text, trace_path.read_text(errors="replace") if trace else ""

    def case(self, label: str, **facts: object) -> None:
        self.report["cases"].append({"label": label, "outcome": "passed", **facts})
        self.save()


def events(output: str) -> list[tuple[str, str, str]]:
    return [(event, unit, key or "") for event, unit, key in EVENT.findall(output)]


def runtime_compiles(trace: str) -> int:
    # Count successful driver execve launches, not the integrated cc1 row.
    return sum('execve(' in row and '"-c"' in row and '"cpp-output"' in row and '"-###"' not in row and '= 0' in row for row in trace.splitlines())


def native_gate(args: argparse.Namespace, evidence: Evidence) -> None:
    freak = args.freak.resolve(strict=True)
    clang = args.clang.resolve(strict=True)
    payload = args.payload.resolve(strict=True)
    assert (payload / "runtime/freak_runtime.c").is_file(), payload
    assert (payload / "std/freak_abi").is_file(), payload
    assert sys.platform.startswith("linux"), "This milestone qualifies Linux reuse; Windows/macOS closure/native coverage remains pending."
    assert shutil.which("strace"), "Linux qualification requires actual execve evidence."
    for path in (freak, clang, ROOT / "src/cli/runtime_cache.fk", ROOT / "src/cli/build.fk", ROOT / "src/cli/run.fk", Path(__file__)):
        evidence.pin(path)
    work = evidence.root / "work"
    work.mkdir(mode=0o700)
    owned_payload = work / "payload"
    shutil.copytree(payload, owned_payload)
    cache_parent = work / "cache"
    cache_parent.mkdir(mode=0o700)
    env = dict(os.environ, FREAK_HOME=str(owned_payload), FREAK_CLANG=str(clang), XDG_CACHE_HOME=str(cache_parent), FREAK_RUNTIME_CACHE_TRACE="1")
    env.pop("FREAK_RUNTIME_CACHE", None)
    source_a = work / "a.fk"
    source_b = work / "b.fk"
    source_a.write_text('task main() -> int { say 41 give back 0 }\n')
    source_b.write_text('task main() -> int { say 42 give back 0 }\n')

    def build(source: Path, label: str, *, target: str = "c", optimization: int = 0, lto: str = "off", selected_env: dict[str, str] | None = None, compile_count: int | None = None) -> list[tuple[str, str, str]]:
        active = selected_env or env
        code, output, trace = evidence.invoke([str(freak), "build", str(source), "--" + target, f"--clang-opt={optimization}", f"--lto={lto}"], work, active, label, trace=True)
        assert code == 0, output
        found = events(output)
        actual_count = runtime_compiles(trace)
        if compile_count is not None:
            assert actual_count == compile_count, (label, actual_count, compile_count, output, trace)
        assert sum(event == "compile" for event, _, _ in found) == actual_count, (label, found, actual_count)
        binary = source.with_suffix("")
        generated = str(source) + (".ll" if target == "llvm" else ".c")
        links = [row for row in trace.splitlines() if "execve(" in row and "= 0" in row and json.dumps(generated) in row and json.dumps(str(binary)) in row and '"-E"' not in row and '"-###"' not in row]
        assert len(links) == 1, (label, "user code was not freshly compiled/linked", links)
        assert "/freak/runtime-v1/" not in links[0], "linked a live persistent-cache pathname"
        evidence.case(label, events=found, actual_runtime_compiles=actual_count, binary_sha256=sha(binary))
        return found

    def execute(source: Path, expected: str, label: str) -> None:
        code, output, _ = evidence.invoke([str(source.with_suffix(""))], work, env, label)
        assert code == 0 and output == expected, (code, output, expected)
        evidence.case(label, stdout=output)

    cold = build(source_a, "cold-common", compile_count=1)
    assert cold and cold[0][0] == "compile", cold
    key = next(key for event, unit, key in cold if unit == "freak_runtime.c")
    root = cache_parent / "freak/runtime-v1"
    entry = root / key
    initial = {path.name: sha(path) for path in entry.iterdir() if path.is_file()}
    build(source_b, "different-program-warm", compile_count=0)
    execute(source_a, "41\n", "execute-a")
    execute(source_b, "42\n", "execute-b")
    source_b.write_text('task main() -> int { say 43 give back 0 }\n')
    build(source_b, "changed-user-warm", compile_count=0)
    execute(source_b, "43\n", "execute-changed-b")
    assert initial == {path.name: sha(path) for path in entry.iterdir() if path.is_file()}, "warm hit mutated the entry"
    evidence.case("immutable-warm-entry", key=key)

    runtime_header = owned_payload / "runtime/freak_runtime.h"
    original_header = runtime_header.read_bytes()
    original_stat = runtime_header.stat()
    changed = original_header.replace(b"runtime", b"runtimE", 1)
    assert changed != original_header and len(changed) == len(original_header)
    runtime_header.write_bytes(changed)
    os.utime(runtime_header, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))
    build(source_b, "same-mtime-header-miss", compile_count=1)
    runtime_header.write_bytes(original_header)
    os.utime(runtime_header, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))
    build(source_b, "restored-header-hit", compile_count=0)

    runtime_inc = owned_payload / "runtime/freak_v35_http.inc"
    original_inc = runtime_inc.read_bytes()
    original_inc_stat = runtime_inc.stat()
    runtime_inc.write_bytes(original_inc + b"\n/* raw dependency cache control */\n")
    os.utime(runtime_inc, ns=(original_inc_stat.st_atime_ns, original_inc_stat.st_mtime_ns))
    build(source_b, "runtime-inc-raw-change-miss", compile_count=1)
    runtime_inc.write_bytes(original_inc)
    os.utime(runtime_inc, ns=(original_inc_stat.st_atime_ns, original_inc_stat.st_mtime_ns))
    build(source_b, "restored-runtime-inc-hit", compile_count=0)

    include_shadow = work / "sdk-shadow"
    include_shadow.mkdir()
    shadow_env = dict(env, CPATH=str(include_shadow))
    build(source_b, "sdk-search-context-cold", selected_env=shadow_env, compile_count=1)
    build(source_b, "sdk-search-context-warm", selected_env=shadow_env, compile_count=0)
    shadow = include_shadow / "stdio.h"
    shadow.write_text('#include_next <stdio.h>\n/* shadow version 01 */\n')
    build(source_b, "new-higher-priority-header-miss", selected_env=shadow_env, compile_count=1)
    shadow_stat = shadow.stat()
    shadow.write_text('#include_next <stdio.h>\n/* shadow version 02 */\n')
    os.utime(shadow, ns=(shadow_stat.st_atime_ns, shadow_stat.st_mtime_ns))
    build(source_b, "same-mtime-sdk-header-miss", selected_env=shadow_env, compile_count=1)
    execute(source_b, "43\n", "execute-sdk-shadow")

    driver_root = work / "selected-driver"
    driver_bin = driver_root / "bin"
    driver_bin.mkdir(parents=True)
    selected_driver = driver_bin / "clang"
    shutil.copy2(clang, selected_driver)
    # Preserve the selected distribution's relative library/resource layout;
    # only the test-owned executable is mutated, never the supplied SDK.
    original_lib = clang.parent.parent / "lib"
    if original_lib.is_dir():
        (driver_root / "lib").symlink_to(original_lib, target_is_directory=True)
    code, resource, _ = evidence.invoke([str(clang), "-print-resource-dir"], work, env, "selected-resource-dir")
    assert code == 0 and Path(resource.strip()).is_dir(), resource
    (driver_bin / "clang.cfg").write_text("-resource-dir=" + resource.strip() + "\n")
    driver_env = dict(env, FREAK_CLANG=str(selected_driver))
    build(source_a, "selected-driver-cold", selected_env=driver_env, compile_count=1)
    build(source_b, "selected-driver-warm", selected_env=driver_env, compile_count=0)
    original_driver_stat = selected_driver.stat()
    before_driver = sha(selected_driver)
    with selected_driver.open("ab") as stream:
        stream.write(b"FREAK runtime cache executable-byte control\n")
    os.utime(selected_driver, ns=(original_driver_stat.st_atime_ns, original_driver_stat.st_mtime_ns))
    assert sha(selected_driver) != before_driver
    build(source_b, "same-path-driver-byte-change-miss", selected_env=driver_env, compile_count=1)
    build(source_a, "changed-driver-warm", selected_env=driver_env, compile_count=0)

    for optimization in (1, 2, 3):
        build(source_a, f"O{optimization}-cold", optimization=optimization, compile_count=1)
        build(source_b, f"O{optimization}-warm", optimization=optimization, compile_count=0)
    llvm_cold = build(source_a, "llvm-bridge-cold", target="llvm", compile_count=1)
    assert any(event == "hit" and unit == "freak_runtime.c" for event, unit, _ in llvm_cold), llvm_cold
    build(source_b, "llvm-bridge-warm", target="llvm", compile_count=0)
    execute(source_b, "43\n", "execute-llvm")
    for lto in ("thin", "full"):
        build(source_a, f"{lto}-cold", lto=lto, compile_count=1)
        build(source_b, f"{lto}-warm", lto=lto, compile_count=0)
        execute(source_b, "43\n", f"execute-{lto}")

    object_path = entry / "runtime.o"
    object_bytes = object_path.read_bytes()
    object_path.write_bytes(object_bytes[:max(1, len(object_bytes) // 2)])
    truncated_hash = sha(object_path)
    build(source_a, "truncated-object-miss", compile_count=1)
    assert sha(object_path) == truncated_hash, "corrupt occupied entry was overwritten"
    object_path.write_bytes(object_bytes)
    receipt_path = entry / "receipt"
    receipt = receipt_path.read_bytes()
    receipt_path.write_bytes(receipt.replace(key.encode(), b"f" * 64, 1))
    wrong_receipt_hash = sha(receipt_path)
    build(source_b, "wrong-key-receipt-miss", compile_count=1)
    assert sha(receipt_path) == wrong_receipt_hash, "invalid occupied receipt was overwritten"
    receipt_path.write_bytes(receipt)
    build(source_b, "repaired-by-test-owner-hit", compile_count=0)
    object_path.unlink()
    foreign_object = work / "foreign-object"
    foreign_object.write_bytes(object_bytes)
    object_path.symlink_to(foreign_object)
    build(source_b, "symlink-object-miss", compile_count=1)
    assert sha(foreign_object) == hashlib.sha256(object_bytes).hexdigest() and object_path.is_symlink()
    object_path.unlink()
    object_path.write_bytes(object_bytes)
    with object_path.open("wb") as stream:
        stream.truncate(67108865)
    build(source_b, "oversized-object-miss", compile_count=1)
    assert object_path.stat().st_size == 67108865
    object_path.write_bytes(object_bytes)
    receipt_path.write_bytes(b"x" * 1048577)
    build(source_b, "oversized-receipt-miss", compile_count=1)
    assert receipt_path.stat().st_size == 1048577
    receipt_path.write_bytes(receipt)

    import fcntl
    with (root / f"{key}.lock").open("r+b") as held:
        fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
        build(source_a, "contended-key-uncached-object", compile_count=1)
    build(source_a, "lock-released-hit", compile_count=0)
    incomplete = entry / "receipt.saved"
    receipt_path.rename(incomplete)
    build(source_b, "partial-entry-miss", compile_count=1)
    assert not receipt_path.exists() and incomplete.read_bytes() == receipt
    incomplete.rename(receipt_path)

    # A detached partially written stage is never a candidate hit or repair
    # target. Its test-owned bytes are preserved through a successful warm hit.
    partial_stage = root / "freak-runtime-entry-interrupted-control"
    partial_stage.mkdir(mode=0o700)
    (partial_stage / "runtime.o").write_bytes(object_bytes[:17])
    build(source_b, "unpublished-partial-stage-ignored", compile_count=0)
    assert (partial_stage / "runtime.o").read_bytes() == object_bytes[:17]

    root.chmod(0o777)
    fallback = build(source_a, "insecure-root-source-fallback", compile_count=0)
    assert any(event == "fallback" and unit == "cache-root" for event, unit, _ in fallback), fallback
    assert root.stat().st_mode & 0o777 == 0o777, "foreign/insecure root was repaired"
    root.chmod(0o700)
    foreign = work / "foreign"
    foreign.mkdir()
    marker = foreign / "marker"
    marker.write_bytes(b"preserve foreign cache target\n")
    freak_container = cache_parent / "freak"
    relocated = cache_parent / "freak-owned"
    freak_container.rename(relocated)
    freak_container.symlink_to(foreign, target_is_directory=True)
    fallback = build(source_b, "symlink-root-source-fallback", compile_count=0)
    assert any(event == "fallback" and unit == "cache-root" for event, unit, _ in fallback)
    assert marker.read_bytes() == b"preserve foreign cache target\n" and list(foreign.iterdir()) == [marker]
    freak_container.unlink()
    relocated.rename(freak_container)
    disabled = dict(env, FREAK_RUNTIME_CACHE="off")
    build(source_a, "explicit-cache-off-source-build", selected_env=disabled, compile_count=0)
    unavailable = dict(env, XDG_CACHE_HOME="/proc")
    build(source_a, "unwritable-root-source-fallback", selected_env=unavailable, compile_count=0)
    default_home = work / "default-cache-home"
    default_home.mkdir(mode=0o700)
    default_env = dict(env, HOME=str(default_home), XDG_CACHE_HOME="relative-is-ignored")
    build(source_a, "relative-xdg-default-home-cold", selected_env=default_env, compile_count=1)
    build(source_b, "default-home-warm", selected_env=default_env, compile_count=0)
    assert (default_home / ".cache/freak/runtime-v1").is_dir()

    # A complete-program run hit must not bypass the same SDK closure.
    def run(label: str) -> str:
        code, output, _ = evidence.invoke([str(freak), "run", str(source_b), "--c", "--clang-opt=0", "--lto=off"], work, shadow_env, label, trace=True)
        assert code == 0 and "43\n" in output, output
        evidence.case(label, complete_program_hit="run cache hit" in output)
        return output
    first = run("run-context-cold")
    second = run("run-context-warm")
    assert "run cache hit" not in first and "run cache hit" in second, (first, second)
    shadow_stat = shadow.stat()
    shadow.write_text('#include_next <stdio.h>\n/* shadow version 03 */\n')
    os.utime(shadow, ns=(shadow_stat.st_atime_ns, shadow_stat.st_mtime_ns))
    third = run("run-sdk-change-invalidates-program")
    assert "run cache hit" not in third, third
    assert "run cache hit" in run("run-sdk-change-warm"), "new SDK context never became fresh"

    # Compile grammar controls from the implementation, using this installed
    # CLI's normal build path and selected runtime, rather than a Python model.
    harness, cases = dependency_harness((ROOT / "src/cli/runtime_cache.fk").read_text())
    parser_source = work / "dependency-controls.fk"
    parser_source.write_text(harness)
    build(parser_source, "dependency-parser-build", compile_count=0)
    execute(parser_source, "dependency controls passed\n", "dependency-parser-execute")
    evidence.case("actual-freak-dependency-parser", controls=cases)

    # Failure and complete publication controls require no injected fallbacks.
    bad_source = work / "bad.fk"
    bad_source.write_text('task main() -> int { say unknown_name give back 0 }\n')
    code, output, _ = evidence.invoke([str(freak), "build", str(bad_source), "--c"], work, env, "source-failure-preserved", trace=True)
    assert code != 0 and not bad_source.with_suffix("").exists(), output
    evidence.case("source-failure-preserved", returncode=code)
    evidence.report["boundaries"] = [
        "Linux native only at this milestone; Windows/macOS tool closure and installed archive gates remain pending.",
        "Unknown Windows DLL selection and unresolved/static support closure disable cache reuse.",
        "Private owned staging excludes arbitrary concurrent same-user pathname replacement; no anchored child-I/O primitive is claimed.",
        "Native same-path driver/support mutation, concurrent publication, target/UI/profile partitioning and interruption controls remain required before PR readiness.",
    ]
    evidence.report["outcome"] = "passed-focused-linux"
    evidence.save()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pure", action="store_true", help="run source controls only; no compiler/native qualification")
    parser.add_argument("--freak", type=Path)
    parser.add_argument("--clang", type=Path)
    parser.add_argument("--payload", type=Path)
    parser.add_argument("--evidence-dir", type=Path)
    args = parser.parse_args()
    if args.pure:
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(SourceControls))
        return 0 if result.wasSuccessful() else 1
    if not all((args.freak, args.clang, args.payload, args.evidence_dir)):
        parser.error("native mode requires --freak, --clang, --payload and a new --evidence-dir")
    evidence = Evidence(args.evidence_dir)
    try:
        native_gate(args, evidence)
    except BaseException as error:
        evidence.report.update(outcome="failed", error=f"{type(error).__name__}: {error}")
        evidence.save()
        raise
    print(json.dumps({"outcome": evidence.report["outcome"], "report": str(evidence.root / "report.json")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
