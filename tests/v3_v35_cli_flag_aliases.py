#!/usr/bin/env python3
"""Verify preferred V3.5 flags through a supplied installed native CLI.

The candidate is never rebuilt or replaced. A recorder delegates to the exact
selected Clang and retains its actual argv. --static checks only the receipt
oracles; it cannot qualify native parser, backend, linker or platform behavior.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import sys
import tempfile

from v3_build_profiles import compile_entries, read_log, write_recorder
from v3_final_release_gate import manifest_entries
from v3_v35_acceptance import run_command


ROOT = Path(__file__).resolve().parents[1]
ANSI = re.compile(rb"\x1b\[[0-9;]*m")
MARKER = b"FLAG_ALIAS_PROGRAM_OK\n"
PROGRAM = '''task main() {
    say "FLAG_ALIAS_PROGRAM_OK"
    say "FLAG_ALIAS_ARGS_BEGIN"
    pilot index = 1
    repeat until index >= process::args_count() {
        pilot argument: word = process::arg(index)
        say word_from_int(argument.length()) + ":" + argument
        index += 1
    }
    say "FLAG_ALIAS_ARGS_END"
}
'''
FORWARDED = ("--O4", "--O0", "--flto=value", "--tlto", "+03", "--", "",
             "two words", "café🙂")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(directory: Path) -> dict:
    return {str(path.relative_to(directory)): ("directory" if path.is_dir() else sha256(path))
            for path in sorted(directory.rglob("*"))}


def posix_recorder_launcher(python: str, recorder: Path) -> str:
    return f'#!/bin/sh\nexec {shlex.quote(python)} {shlex.quote(str(recorder))} "$@"\n'


def write_safe_recorder(root: Path, real_clang: str) -> tuple[Path, Path]:
    wrapper, log = write_recorder(root, real_clang)
    if sys.platform != "win32":
        # The inherited recorder is never invoked before its launcher paths
        # are made literal. Keep the Windows direct-executable helper intact.
        wrapper.write_text(posix_recorder_launcher(sys.executable, root / "record_clang.py"),
                           encoding="utf-8")
    return wrapper, log


def literal_path_controls() -> int:
    """Parse launcher text only; no shell or native child is executed."""
    spellings = (
        ('/tools/"literal quote"/python', '/scratch/"literal quote"/record.py'),
        ("/tools/$PYTHON/python", "/scratch/$TMPDIR/record.py"),
        ("/tools/`literal command`/python", "/scratch/`literal command`/record.py"),
        ("/tools/'literal quote'/python", "/scratch/'literal quote'/record.py"),
        ("/tools/space and café/python", "/scratch/space and café/record.py"),
        ('/tools/"quote"/$PYTHON/`literal`/python', '/scratch/"quote"/$TMPDIR/`literal`/record.py'),
    )
    for python, recorder in spellings:
        launcher = posix_recorder_launcher(python, Path(recorder))
        assert shlex.split(launcher, comments=True) == ["exec", python, recorder, "$@"]
        assert launcher == ("#!/bin/sh\nexec " + shlex.quote(python) + " " +
                            shlex.quote(recorder) + ' "$@"\n')
    python, recorder = spellings[-1]
    unsafe = f'#!/bin/sh\nexec "{python}" "{recorder}" "$@"\n'
    assert shlex.split(unsafe, comments=True) != ["exec", python, recorder, "$@"], (
        "unsafe inherited launcher control did not expose its literal-quote defect")
    return len(spellings)


def text(output: bytes) -> bytes:
    return ANSI.sub(b"", output).replace(b"\r\n", b"\n")


def assert_program(result, arguments: tuple[str, ...] = ()) -> None:
    assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
    assert not result.stderr, result.stderr
    output = text(result.stdout)
    expected = (MARKER + b"FLAG_ALIAS_ARGS_BEGIN\n" +
                b"".join(str(len(argument.encode("utf-8"))).encode() + b":" +
                         argument.encode("utf-8") + b"\n" for argument in arguments) +
                b"FLAG_ALIAS_ARGS_END\n")
    assert output.count(MARKER) == 1 and output.count(b"FLAG_ALIAS_ARGS_BEGIN\n") == 1
    assert output.count(b"FLAG_ALIAS_ARGS_END\n") == 1
    assert expected in output, (expected, output)


def assert_profile(result, entries: list[list[str]], level: int, lto: str,
                   *, plus03: bool = False) -> None:
    assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
    assert entries, "the actual selected Clang saw no compilation"
    arguments = [argument for row in entries for argument in row]
    optimization = {argument for argument in arguments if re.fullmatch(r"-O[0-3]", argument)}
    assert optimization == {f"-O{level}"}, (optimization, entries)
    actual_lto = {argument for argument in arguments if argument.startswith("-flto")}
    expected_lto = {"thin": {"-flto=thin"}, "full": {"-flto"}, "off": set()}[lto]
    assert actual_lto == expected_lto, (actual_lto, expected_lto, entries)
    assert not any(argument in ("-Ofast", "-ffast-math", "-march=native")
                   for argument in arguments), entries
    output = text(result.stdout)
    if plus03:
        assert b"+03" in output and b"FINAL FORM" in output, output
        assert b"Runtime: plus03" in output, output
    else:
        assert f"Profile: O{level}".encode() in output, output
        assert b"FINAL FORM" not in output and b"Runtime: plus03" not in output, output
        if lto != "off":
            assert b"Runtime: default" in output, output


def assert_refused(result, all_tool_calls: list[list[str]], before: dict, after: dict,
                   temp_before: dict, temp_after: dict, message: bytes) -> None:
    assert result.returncode == 1, (result.returncode, result.stdout, result.stderr)
    output = text(result.stdout + result.stderr)
    assert message in output, (message, output)
    assert MARKER not in output and b"FLAG_ALIAS_ARGS_BEGIN" not in output, output
    assert not all_tool_calls, ("invalid flags invoked Clang", all_tool_calls)
    assert before == after, "invalid flags changed source, project, graph or output artifacts"
    assert temp_before == temp_after, "invalid flags created temporary build/project state"


def inert_controls() -> int:
    """Prove the evidence oracles reject successful-looking wrong results."""
    from subprocess import CompletedProcess
    good = CompletedProcess([], 0, b"Profile: O3\n" + MARKER, b"")
    assert_profile(good, [["input.c", "-O3"]], 3, "off")
    bad_profiles = (
        (CompletedProcess([], 1, good.stdout, b""), [["-O3"]]),
        (good, []), (good, [["-O2"]]), (good, [["-O3", "-O2"]]),
        (good, [["-O3", "-flto=thin"]]), (good, [["-O3", "-Ofast"]]),
        (CompletedProcess([], 0, good.stdout + b"Runtime: plus03\n", b""), [["-O3"]]),
    )
    count = 0
    for result, entries in bad_profiles:
        try:
            assert_profile(result, entries, 3, "off")
        except AssertionError:
            count += 1
        else:
            raise AssertionError("profile oracle admitted an invalid result")
    refused = CompletedProcess([], 1, b"unknown or malformed flag --O4\n", b"")
    expected = {"output": "unchanged"}
    assert_refused(refused, [], expected, expected, {}, {}, b"unknown or malformed flag")
    bad_refusals = (
        (CompletedProcess([], 0, refused.stdout, b""), [], expected, {}),
        (refused, [["--version"]], expected, {}),
        (refused, [], {"output": "changed"}, {}),
        (refused, [], expected, {"new-temp": "file"}),
        (CompletedProcess([], 1, refused.stdout + MARKER, b""), [], expected, {}),
    )
    for result, calls, after, temp_after in bad_refusals:
        try:
            assert_refused(result, calls, expected, after, {}, temp_after,
                           b"unknown or malformed flag")
        except AssertionError:
            count += 1
        else:
            raise AssertionError("refusal oracle admitted an invalid result")
    argv = MARKER + b"FLAG_ALIAS_ARGS_BEGIN\n5:--O4\nFLAG_ALIAS_ARGS_END\n"
    # --O4 has four bytes; even a marker-complete wrong argument must fail.
    try:
        assert_program(CompletedProcess([], 0, argv, b""), ("--O4",))
    except AssertionError:
        count += 1
    else:
        raise AssertionError("argv oracle admitted a changed argument length")
    return count


@contextlib.contextmanager
def retain_evidence(evidence: dict, report: Path):
    def save(_=None):
        stage = report.with_suffix(report.suffix + ".pending")
        stage.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        stage.replace(report)
    save()
    try:
        yield save
    except BaseException as error:
        evidence.update(status="fail", failure=f"{type(error).__name__}: {error}")
        raise
    finally:
        primary = sys.exc_info()[1]
        try:
            save()
        except BaseException as recording_error:
            if primary is None:
                raise
            if hasattr(primary, "add_note"):
                primary.add_note(f"terminal evidence write failed: {recording_error!r}"[:1000])


def invalid_build_flags() -> list[tuple[list[str], bytes]]:
    malformed = ("--O", "--O4", "--O-1", "--O03", "--O3=", "--O=3", "--o3",
                 "--03", "--O٣", "--O3 ", "--flto=full", "--flto=thin",
                 "--flto=", "--tlto=thin", "--tlto=full", "--tlto=", "--FLTO")
    rows = [([flag], b"unknown or malformed flag") for flag in malformed]
    for first in range(4):
        for second in range(4):
            if first != second:
                rows += [([f"--O{first}", f"--O{second}"], b"conflicting --opt flags"),
                         ([f"--O{first}", f"--opt={second}"], b"conflicting --opt flags"),
                         ([f"--opt={second}", f"--O{first}"], b"conflicting --opt flags")]
    for level in range(4):
        rows += [(["+03", f"--O{level}"], b"+03 cannot be combined with --opt"),
                 ([f"--O{level}", "+03"], b"+03 cannot be combined with --opt")]
    for alias, incompatible in (("--flto", "--tlto"), ("--flto", "--lto"),
                                ("--flto", "--lto=thin"), ("--tlto", "--lto=full"),
                                ("--flto", "--lto=off"), ("--tlto", "--lto=off")):
        rows += [([alias, incompatible], b"conflicting --lto flags"),
                 ([incompatible, alias], b"conflicting --lto flags")]
    for alias in ("--flto", "--tlto"):
        target = "--target=x86_64-unknown-linux-gnu"
        rows += [([alias, target], b"LTO is not supported with --target"),
                 ([target, alias], b"LTO is not supported with --target")]
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--static", action="store_true")
    parser.add_argument("--freak", type=Path)
    parser.add_argument("--payload-home", type=Path)
    parser.add_argument("--clang", type=Path)
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--backend", choices=("c", "llvm"), action="append")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    controls = inert_controls()
    quoted_paths = literal_path_controls()
    if args.static:
        print(f"PASS flag receipt oracles: {controls} failing controls, {quoted_paths} literal path controls; native verification not run")
        return
    if not (args.freak and args.payload_home and args.clang and args.report):
        parser.error("native verification requires --freak, --payload-home, --clang and --report")
    repo = args.repo.resolve(strict=True)
    freak = args.freak.resolve(strict=True)
    home = args.payload_home.resolve(strict=True)
    clang = args.clang.resolve(strict=True)
    report = args.report.resolve()
    report.parent.mkdir(parents=True, exist_ok=True)
    assert not report.exists(), "retain old evidence; use a fresh --report path"
    assert not report.with_suffix(report.suffix + ".pending").exists(), "use a fresh evidence path"
    assert freak.is_file() and clang.is_file()
    assert freak == home / ("freak.exe" if os.name == "nt" else "freak"), "use the installed archive CLI"
    payload = manifest_entries(repo)
    for source, destination in payload:
        assert sha256(source) == sha256(home / destination), (source, destination, "payload mismatch")
    cli_manifest = repo / "packaging/cli-sources.manifest"
    cli_sources = [repo / line.strip() for line in cli_manifest.read_text().splitlines()
                   if line.strip() and not line.startswith("#")]
    pinned = [freak, clang, Path(sys.executable).resolve(), cli_manifest, Path(__file__).resolve(),
              repo / "packaging/distribution-files.manifest", *cli_sources,
              repo / "tests/v3_build_profiles.py", repo / "tests/v3_run_freshness.py",
              repo / "tests/v3_final_release_gate.py", repo / "tests/v3_v35_acceptance.py",
              repo / "tools/v3_performance_lab.py", *(source for source, _ in payload),
              *(home / destination for _, destination in payload)]
    before = {str(path.resolve()): sha256(path) for path in pinned}
    evidence = {"schema": "freak.v35.cli-flag-aliases.v1", "status": "running",
                "freak": str(freak), "payload_home": str(home), "clang": str(clang),
                "compiler_or_cli_rebuilt": False, "pinned_input_sha256": before,
                "inert_failing_controls": controls, "literal_path_controls": quoted_paths,
                "command_records": [], "receipts": [],
                "matrices": [], "refusals": []}
    with retain_evidence(evidence, report) as save, tempfile.TemporaryDirectory(prefix="freak-v35-flags-") as temporary:
        scratch = Path(temporary).resolve(strict=True)
        temp_root = scratch / "temporary"
        temp_root.mkdir()
        tools = scratch / "recorder"
        tools.mkdir()
        wrapper, log = write_safe_recorder(tools, str(clang))
        evidence.update(recorder=str(wrapper), recorder_sha256=sha256(wrapper),
                        recorder_source=(tools / "record_clang.py").read_text(encoding="utf-8"))
        save()
        env = os.environ.copy()
        for name in tuple(env):
            if name.startswith(("FREAK_PROFILE_", "FREAK_DOCTOR_TEST_", "FREAK_V35_TEST_")):
                del env[name]
        env.update(FREAK_HOME=str(home), FREAK_CLANG=str(wrapper),
                   FREAK_PROFILE_REAL_CLANG=str(clang), FREAK_PROFILE_CLANG_LOG=str(log),
                   NO_COLOR="1", FREAK_NO_COLOR="1", FREAK_ASCII="1", FREAK_UNICODE="0",
                   TMPDIR=str(temp_root), TEMP=str(temp_root), TMP=str(temp_root))

        def invoke(name: str, argv: list, cwd: Path = scratch):
            log.unlink(missing_ok=True)
            result = run_command([str(freak), *map(str, argv)], cwd=cwd, env=env,
                label=name, prefix=report.parent / f"flag-command-{len(evidence['receipts'])}",
                records=evidence["command_records"], expected=None, timeout=180, on_record=save)
            calls = read_log(log)
            compiles = compile_entries(log)
            evidence["receipts"].append({"name": name, "argv": list(map(str, argv)),
                "cwd": str(cwd), "exit_code": result.returncode,
                "stdout_hex": result.stdout.hex(), "stderr_hex": result.stderr.hex(),
                "actual_clang_argv": calls, "actual_compile_argv": compiles})
            save()
            return result, calls, compiles

        help_result, _, _ = invoke("help", ["help"])
        help_output = text(help_result.stdout)
        assert help_result.returncode == 0 and not help_result.stderr
        for token in (b"--O0..--O3", b"--flto / --tlto", b"Full / thin LTO",
                      b"Legacy: --opt=0..3; --lto[=MODE]", b"build and run only",
                      b"--c --O3", b"--O3 --flto"):
            assert token in help_output, (token, help_output)

        for backend in args.backend or ("c", "llvm"):
            for command in ("build", "run"):
                settings = [(level, "off", [f"--O{level}", f"--O{level}"],
                             [f"--opt={level}", "--lto=off"]) for level in range(4)]
                settings += [(2, mode, ["--O2", alias, alias],
                              ["--opt=2", f"--lto={mode}"])
                             for alias, mode in (("--flto", "full"), ("--tlto", "thin"))]
                for level, mode, aliases, legacy in settings:
                    source = scratch / f"{backend}-{command}-o{level}-{mode}.fk"
                    source.write_text(PROGRAM, encoding="utf-8")
                    if mode == "thin":
                        legacy += ["--lto"]
                    key = f"{backend}/{command}/o{level}/{mode}"
                    result, _, compiles = invoke(key + "/aliases", [command, source, "--" + backend, *aliases])
                    assert_profile(result, compiles, level, mode)
                    if command == "run":
                        assert_program(result)
                    else:
                        binary = source.with_suffix(".exe" if os.name == "nt" else "")
                        execution = run_command([str(binary)], cwd=scratch, env=env,
                            label=key + "/execute", prefix=report.parent / f"flag-execute-{len(evidence['matrices'])}",
                            records=evidence["command_records"], timeout=30, on_record=save)
                        assert_program(execution)
                    legacy_result, _, legacy_compiles = invoke(key + "/legacy", [command, source, "--" + backend, *legacy])
                    if command == "run":
                        assert_program(legacy_result)
                        assert b"run cache hit" in text(legacy_result.stdout), legacy_result.stdout
                        assert not legacy_compiles, "equivalent spellings rebuilt a warm run artifact"
                    else:
                        assert_profile(legacy_result, legacy_compiles, level, mode)
                    mixed_orders = []
                    if command == "run":
                        # The parser is shared by build/run. Warm native run
                        # checks both mixed orders independently without a
                        # legacy flag supplying the first alias-only level.
                        for order, flags in (("alias-first", [*aliases, *legacy]),
                                             ("legacy-first", [*legacy, *aliases])):
                            mixed, _, mixed_compiles = invoke(key + "/mixed/" + order,
                                [command, source, "--" + backend, *flags])
                            assert_program(mixed)
                            assert b"run cache hit" in text(mixed.stdout), mixed.stdout
                            assert not mixed_compiles, "equivalent mixed spellings rebuilt a warm run artifact"
                            mixed_orders.append({"order": order, "flags": flags})
                    evidence["matrices"].append({"backend": backend, "command": command,
                        "optimization": level, "lto": mode, "aliases": aliases, "legacy": legacy,
                        "mixed_orders": mixed_orders,
                        "source_sha256": sha256(source), "source": PROGRAM})
                    save()
            for alias, mode in (("--flto", "full"), ("--tlto", "thin")):
                source = scratch / f"{backend}-plus03-{mode}.fk"
                source.write_text(PROGRAM, encoding="utf-8")
                result, _, compiles = invoke(f"{backend}/plus03/{mode}", ["build", source, "--" + backend, "+03", alias])
                assert_profile(result, compiles, 3, mode, plus03=True)
            source = scratch / f"{backend}-forwarded.fk"
            source.write_text(PROGRAM, encoding="utf-8")
            result, _, compiles = invoke(f"{backend}/forwarded", ["run", source, "--" + backend, "--O0", "--", *FORWARDED])
            assert_profile(result, compiles, 0, "off")
            assert_program(result, FORWARDED)

        admission = scratch / "admission"
        admission.mkdir()
        source = admission / "protected.fk"
        source.write_text(PROGRAM, encoding="utf-8")
        for name in ("protected", "protected.exe", "protected.fk.c", "protected.fk.ll",
                     "protected.obj", "protected.build.json", "protected.freak-run-cache",
                     "protected.exe.freak-run-cache", "explicit-output", "graph.json", "hangar.lock"):
            (admission / name).write_bytes(b"protected artifact\x00\xff\n")
        protected = snapshot(admission)
        temp_before = snapshot(temp_root)
        for command in ("build", "run", "check", "transpile"):
            cases = invalid_build_flags() if command in ("build", "run") else [
                ([flag], b"only valid for build and run")
                for flag in ("--O0", "--O1", "--O2", "--O3", "--flto", "--tlto")]
            for index, (flags, message) in enumerate(cases):
                prefix = ["--output=explicit-output", "--graph-snapshot=graph.json"] if command in ("build", "run") else []
                result, calls, _ = invoke(f"admission/{command}/{index}", [command, source, *prefix, *flags], admission)
                assert_refused(result, calls, protected, snapshot(admission), temp_before,
                               snapshot(temp_root), message)
                evidence["refusals"].append({"command": command, "flags": flags, "message": message.decode()})
                save()
            result, calls, _ = invoke(f"admission/{command}/before-input", [command, "--O4"], admission)
            assert_refused(result, calls, protected, snapshot(admission), temp_before,
                           snapshot(temp_root), b"unknown or malformed flag")
        after = {str(path.resolve()): sha256(path) for path in pinned}
        assert after == before, "candidate, selected toolchain, payload or source inputs changed"
        evidence.update(status="pass", unchanged_input_pins=True,
                        matrix_count=len(evidence["matrices"]), refusal_count=len(evidence["refusals"]))
        save()
    print(f"PASS installed CLI flag aliases: {evidence['matrix_count']} matrices, "
          f"{evidence['refusal_count']} refusals, exact program argv, legacy cache equivalence")


if __name__ == "__main__":
    main()
