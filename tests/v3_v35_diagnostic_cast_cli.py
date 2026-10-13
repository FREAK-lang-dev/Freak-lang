#!/usr/bin/env python3
"""Verify opt-in cast presentation through an explicitly supplied native CLI.

This gate does not build a compiler or CLI. --static checks the receipt oracle's
failing controls without executing the native candidate. Native runs use the
actual payload, canonical compiler locations and the pinned data selector.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from v3_v35_acceptance import run_command


ROOT = Path(__file__).resolve().parents[1]
ANSI = re.compile(rb"\x1b\[[0-9;]*m")
HEADER = re.compile(rb"^(?:error|type error|borrowck):")
LOCATION = re.compile(rb"^ --> (.+):([0-9]+):([0-9]+)\r?$")
CAST = re.compile(rb"^\[E[0-9]{4}(?: [A-Z]+)?\] ", re.M)
CASES = {
    "unbound": ('task main() { say missing; }\n', ("E0001",)),
    "type": ('task main() { pilot x: int = "word"; }\n', ("E0002",)),
    "move": ('task take(text: word) {} task main() { pilot text = "owner" + " word"; take(text); say text; }\n', ("E0003",)),
    "immutable": ('task main() { fixed pilot x = 1; x = 2; }\n', ("E0004", "E0004")),
    "call": ('task choose(value: int) {} task main() { choose(); }\n', ("E0005",)),
    "numeric_parse": ('task main() { say 1.2.3; }\n', ("E0007",)),
    "overflow": ('task main() { say 99999999999999999999999; }\n', ("E0008",)),
    "multiple": ('task main() { say missing_one; say missing_two; }\n', ("E0001", "E0001")),
    "egg": ('task main() { missing(1, 2, 3) }', ("E0005",)),
    "egg_near_miss": ('task main() { missing(1, 2, 3) }\n', ("E0005",)),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@contextlib.contextmanager
def retain_evidence(evidence: dict, report: Path | None):
    def save(_=None):
        if report:
            report.parent.mkdir(parents=True, exist_ok=True)
            report.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    save()
    try:
        yield save
    except BaseException as error:
        evidence.update(status="fail", failure=f"{type(error).__name__}: {error}")
        raise
    finally:
        save()


def load_selector(repo: Path):
    spec = importlib.util.spec_from_file_location("v35_cli_cast_oracle", repo / "src/diagnostics/selector.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_blocks(output: bytes) -> list[tuple[bytes, str, int, int]]:
    """Keep complete canonical messages/source/carets byte for byte.

    Locations are read from canonical output, never inferred from its error
    message. Expected site codes are explicit fixture contracts.
    """
    lines = output.splitlines(keepends=True)
    blocks = []
    for index, line in enumerate(lines):
        if not HEADER.match(ANSI.sub(b"", line)):
            continue
        assert index + 1 < len(lines), "canonical diagnostic lost its location"
        location = ANSI.sub(b"", lines[index + 1]).rstrip(b"\r\n")
        matched = LOCATION.fullmatch(location)
        assert matched, ("canonical diagnostic lost its structured location", location)
        end = index + 2
        while end < len(lines):
            clean = ANSI.sub(b"", lines[end])
            if not (clean.startswith(b"  |") or re.match(rb"^[0-9]+ \|", clean)):
                break
            end += 1
        block = b"".join(lines[index:end])
        assert b"^" in block, "canonical diagnostic lost its caret"
        blocks.append((block, matched[1].decode("utf-8"), int(matched[2]), int(matched[3])))
    return blocks


def stable_cli_text(output: bytes) -> bytes:
    """Normalize only existing timing rows and the existing random fail quote."""
    lines = output.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if line.startswith(b"  OK  "):
            lines[index] = re.sub(rb" \([0-9]+ms\)(\r?\n)$", rb" (<elapsed>ms)\1", line)
        if index and lines[index - 1].rstrip(b"\r\n") == b"  X BUILD FAILED":
            assert line.startswith(b'  "'), ("unexpected build-failure quote row", line)
            lines[index] = b"  <existing random failure quote>\n"
    return b"".join(lines)


def assert_presentation(baseline, observed, expected_suffix: bytes) -> list:
    assert observed.returncode == baseline.returncode, "cast changed exit status"
    assert observed.stderr == baseline.stderr, "cast changed canonical stderr"
    original = canonical_blocks(baseline.stdout)
    actual = canonical_blocks(observed.stdout)
    assert actual == original, "cast changed a canonical message, source line, location or caret"
    if expected_suffix:
        assert observed.stdout.endswith(expected_suffix), (
            "missing, changed, duplicated or misplaced cast suffix",
            expected_suffix, observed.stdout[-len(expected_suffix) - 200:])
        prefix = observed.stdout[:-len(expected_suffix)]
    else:
        assert not CAST.search(observed.stdout), "default/off or unclassified failure emitted a cast line"
        prefix = observed.stdout
    assert not CAST.search(prefix), "cast appeared before the canonical failure finished"
    assert stable_cli_text(prefix) == stable_cli_text(baseline.stdout), "cast altered canonical CLI output"
    return original


def expected_suffix(selector, baseline, codes: tuple[str, ...], sources: dict[Path, str],
                    mode: str, version: str, platform: str) -> bytes:
    blocks = canonical_blocks(baseline.stdout)
    assert len(blocks) == len(codes), ("fixture canonical fact count changed", codes, blocks)
    newline = b"\r\n" if blocks and blocks[0][0].splitlines(keepends=True)[0].endswith(b"\r\n") else b"\n"
    suffix = bytearray()
    for (_, file, line, column), code in zip(blocks, codes):
        path = Path(file).resolve(strict=True)
        assert path in sources, ("diagnostic provenance escaped original source", path, list(sources))
        source = sources[path]
        assert path.read_text(encoding="utf-8") == source, "fixture source unexpectedly mutated"
        speaker = selector.load_codes()[code]["default_speaker"]
        text = selector.render("", mode=mode, version=version, code=code, file=file,
                               line=line, column=column, source=source,
                               speaker=speaker, platform=platform)
        suffix.extend(text.encode("utf-8").replace(b"\n", newline) + newline)
    return bytes(suffix)


def inert_controls() -> int:
    canonical = (b'\x1b[1;31merror\x1b[0m: fixture\n --> /source.fk:2:3\n'
                 b'  |\n2 | missing\n\x1b[1;31m  |   ^ hint\x1b[0m\n\n  X FAILED\n')
    baseline = subprocess.CompletedProcess([], 1, canonical, b"canonical stderr\n")
    suffix = b"\n[E0001 MEIYA] deterministic line\n"
    assert_presentation(baseline, subprocess.CompletedProcess([], 1, canonical + suffix, baseline.stderr), suffix)
    controls = [
        subprocess.CompletedProcess([], 0, canonical + suffix, baseline.stderr),
        subprocess.CompletedProcess([], 1, canonical + suffix, b"changed stderr\n"),
        subprocess.CompletedProcess([], 1, canonical.replace(b"missing", b"changed") + suffix, baseline.stderr),
        subprocess.CompletedProcess([], 1, canonical.replace(b"^ hint", b"hint") + suffix, baseline.stderr),
        subprocess.CompletedProcess([], 1, canonical + suffix + suffix, baseline.stderr),
        subprocess.CompletedProcess([], 1, suffix + canonical, baseline.stderr),
        subprocess.CompletedProcess([], 1, canonical + suffix.replace(b"MEIYA", b"YUUKO"), baseline.stderr),
        subprocess.CompletedProcess([], 1, canonical, baseline.stderr),
    ]
    for observed in controls:
        try:
            assert_presentation(baseline, observed, suffix)
        except AssertionError:
            continue
        raise AssertionError("receipt oracle admitted its malformed-output control")
    return len(controls)


def snapshot(directory: Path) -> dict:
    return {str(path.relative_to(directory)): ("directory" if path.is_dir() else sha256(path))
            for path in sorted(directory.rglob("*"))}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--static", action="store_true")
    parser.add_argument("--freak", type=Path, help="actual native CLI; never rebuilt or substituted")
    parser.add_argument("--payload-home", type=Path, help="actual installed/extracted payload")
    parser.add_argument("--clang", type=Path, help="exact supported native Clang")
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--backend", choices=("c", "llvm"), action="append")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    controls = inert_controls()
    if args.static:
        print(f"PASS diagnostic CLI receipt oracle: {controls} failing controls; native verification not run", flush=True)
        return
    if not (args.freak and args.payload_home and args.clang):
        parser.error("native verification requires --freak, --payload-home and --clang")
    repo = args.repo.resolve(strict=True)
    freak = args.freak.resolve(strict=True)
    home = args.payload_home.resolve(strict=True)
    clang = args.clang.resolve(strict=True)
    assert freak.is_file() and clang.is_file()
    assert (home / "runtime/third_party/llhttp/UPSTREAM.json").is_file(), "actual bundled runtime is required"
    selector = load_selector(repo)
    manifest = repo / "packaging/cli-sources.manifest"
    source_paths = [repo / line.strip() for line in manifest.read_text().splitlines()
                    if line.strip() and not line.startswith("#")]
    pinned = [freak, clang, manifest, Path(__file__).resolve(), *source_paths,
              repo / "tests/v3_v35_acceptance.py",
              repo / "src/diagnostics/selector.py", repo / "src/diagnostics/embedded_cast.fk",
              repo / "src/cli/diagnostic_cast.fk", repo / "src/cli/diagnostic_cast_adapter.fk",
              *sorted((repo / "src/diagnostics").glob("*.json")),
              *sorted((repo / "src/diagnostics/packs").glob("*.json"))]
    for directory in ("runtime", "std", "templates"):
        pinned.extend(path for path in sorted((home / directory).rglob("*")) if path.is_file())
    before = {str(path.resolve()): sha256(path) for path in pinned}
    evidence = {"schema": "freak.v35.diagnostic-cast.cli.v1", "freak": str(freak),
                "payload_home": str(home), "pinned_input_sha256": before,
                "inert_failing_controls": controls, "compiler_or_cli_rebuilt": False,
                "backend_matrices": [], "receipts": [], "command_records": [], "status": "running"}
    with retain_evidence(evidence, args.report) as save, tempfile.TemporaryDirectory(prefix="freak-v35-cast-cli-") as temporary:
        scratch = Path(temporary).resolve(strict=True)
        temp_root = scratch / "temporary"
        temp_root.mkdir()
        env = os.environ.copy()
        for name in tuple(env):
            if name.startswith(("FREAK_DOCTOR_TEST_", "FREAK_V35_TEST_")):
                del env[name]
        env.update(FREAK_HOME=str(home), FREAK_CLANG=str(clang), NO_COLOR="1",
                   FREAK_NO_COLOR="1", FREAK_ASCII="1", FREAK_UNICODE="0",
                   TMPDIR=str(temp_root), TEMP=str(temp_root), TMP=str(temp_root))

        def invoke(name, command, cwd=scratch):
            log_root = args.report.parent if args.report else scratch
            result = run_command([str(freak), *map(str, command)], cwd=cwd, env=env,
                label=name, prefix=log_root / f"diagnostic-cli-command-{len(evidence['receipts'])}",
                records=evidence["command_records"], expected=None, timeout=120, on_record=save)
            evidence["receipts"].append({"name": name, "command": [str(freak), *map(str, command)],
                "cwd": str(cwd), "exit_code": result.returncode,
                "stdout_hex": result.stdout.hex(), "stderr_hex": result.stderr.hex()})
            save()
            return result

        doctor = invoke("doctor-json", ["doctor", "--json"])
        health = json.loads(doctor.stdout)
        assert doctor.returncode == 0 and health["schema"] == "freak.doctor.v1", (doctor.stdout, doctor.stderr)
        assert not CAST.search(doctor.stdout) and not doctor.stderr
        version = health["version"]
        platform = health["platform"]["os"]
        assert platform in ("windows", "linux", "macos")
        evidence.update(version=version, platform=platform)

        for backend in args.backend or ("c", "llvm"):
            matrix = {"backend": backend, "coded_cases": [], "dispatch_commands": []}
            for name, (source, codes) in CASES.items():
                path = scratch / f"{backend}-{name}.fk"
                path.write_text(source, encoding="utf-8", newline="")
                sources = {path: source}
                command = ["check", path, "--" + backend, "--strict-borrow"]
                baseline = invoke(f"{backend}/{name}/default", command)
                assert baseline.returncode == 1, (name, baseline.stdout, baseline.stderr)
                assert not CAST.search(baseline.stdout)
                for mode in ("off", "minimal", "normal", "NORMAL"):
                    observed = invoke(f"{backend}/{name}/{mode}", [*command, "--diagnostic-cast=" + mode])
                    suffix = b"" if mode == "off" else expected_suffix(selector, baseline, codes, sources, mode.lower(), version, platform)
                    assert_presentation(baseline, observed, suffix)
                matrix["coded_cases"].append({"name": name, "codes": codes,
                    "source_sha256": sha256(path), "canonical_blocks_sha256":
                    [hashlib.sha256(row[0]).hexdigest() for row in canonical_blocks(baseline.stdout)]})

            # Every public compiler-failure exit hook is exercised in both
            # emit targets; check above covers all seven currently coded sites.
            for subcommand in ("build", "run", "transpile"):
                for name in ("unbound", "type", "overflow"):
                    source, codes = CASES[name]
                    path = scratch / f"{backend}-{name}.fk"
                    command = [subcommand, path, "--" + backend, "--strict-borrow"]
                    baseline = invoke(f"{backend}/{subcommand}/{name}/off", [*command, "--diagnostic-cast=off"])
                    assert baseline.returncode == 1
                    observed = invoke(f"{backend}/{subcommand}/{name}/normal", [*command, "--diagnostic-cast=normal"])
                    suffix = expected_suffix(selector, baseline, codes, {path: source}, "normal", version, platform)
                    assert_presentation(baseline, observed, suffix)
                    matrix["dispatch_commands"].append(subcommand + "/" + name)

            for name, source, wanted_status in (
                    ("generic", 'task main() { say "\\q"; }\n', 1),
                    ("valid", 'task main() { say 7; }\n', 0)):
                path = scratch / f"{backend}-{name}.fk"
                path.write_text(source, encoding="utf-8", newline="")
                command = ["check", path, "--" + backend, "--strict-borrow"]
                baseline = invoke(f"{backend}/{name}/default", command)
                assert baseline.returncode == wanted_status
                for mode in ("off", "minimal", "normal"):
                    observed = invoke(f"{backend}/{name}/{mode}", [*command, "--diagnostic-cast=" + mode])
                    assert_presentation(baseline, observed, b"")

            missing = scratch / f"{backend}-missing.fk"
            for subcommand in ("build", "run", "check", "transpile"):
                command = [subcommand, missing, "--" + backend]
                baseline = invoke(f"{backend}/{subcommand}/unreadable/default", command)
                assert baseline.returncode == 1 and not canonical_blocks(baseline.stdout)
                observed = invoke(f"{backend}/{subcommand}/unreadable/normal", [*command, "--diagnostic-cast=normal"])
                assert_presentation(baseline, observed, b"")

            runtime_failure = scratch / f"{backend}-runtime-exit.fk"
            runtime_failure.write_text('task main() { say "cast-runtime-exit"; process::exit(23) }\n', encoding="utf-8")
            for mode in ("off", "normal"):
                result = invoke(f"{backend}/runtime-exit/{mode}",
                    ["run", runtime_failure, "--" + backend, "--diagnostic-cast=" + mode])
                assert result.returncode == 23 and b"cast-runtime-exit" in result.stdout.splitlines()
                assert not canonical_blocks(result.stdout) and not CAST.search(result.stdout)
                assert not result.stderr

            imported = scratch / (backend + "-imported")
            imported.mkdir()
            entry = imported / "main.fk"
            module = imported / "bad.fk"
            entry_source = "use bad::{value}\ntask main() { say value() }\n"
            module_source = "task value() -> int { say missing; give back 7 }\n"
            entry.write_text(entry_source, encoding="utf-8", newline="")
            module.write_text(module_source, encoding="utf-8", newline="")
            (imported / "hangar.toml").write_text('[project]\nname="cast_import"\nversion="1.0.0"\nkind="app"\nentry="main.fk"\n[modules]\nbad="bad.fk"\n', encoding="utf-8")
            command = ["check", entry, "--" + backend, "--strict-borrow"]
            baseline = invoke(f"{backend}/imported/off", command, imported)
            assert baseline.returncode == 1
            sources = {module: module_source}
            for mode in ("minimal", "normal"):
                observed = invoke(f"{backend}/imported/{mode}", [*command, "--diagnostic-cast=" + mode], imported)
                suffix = expected_suffix(selector, baseline, ("E0001",), sources, mode, version, platform)
                assert_presentation(baseline, observed, suffix)
            matrix["imported_original_snapshot"] = True
            evidence["backend_matrices"].append(matrix)

        # Preserve old output bytes and every directory entry when admission
        # rejects an invalid/conflicting option, including flags before input.
        admission = scratch / "admission"
        admission.mkdir()
        source = admission / "invalid.fk"
        source.write_text(CASES["unbound"][0], encoding="utf-8")
        for suffix in (".c", ".ll", ".obj", ".exe", ".build.json"):
            Path(str(source) + suffix).write_bytes(b"stale output must survive invalid options\x00\xff")
        protected = snapshot(admission)
        protected_temp = snapshot(temp_root)
        invalid = [("--diagnostic-cast=" + value,) for value in ("", "verbose", "normal ", "nörmal", "off:minimal")]
        invalid += [("--diagnostic-cast", "normal"), ("--diagnostic-cast=off", "--diagnostic-cast=normal")]
        for subcommand in ("build", "run", "check", "transpile"):
            for index, flags in enumerate(invalid):
                observed = invoke(f"admission/{subcommand}/{index}", [subcommand, source, *flags], admission)
                assert observed.returncode == 1 and not CAST.search(observed.stdout)
                assert not canonical_blocks(observed.stdout), "invalid option reached compiler facts"
                assert snapshot(admission) == protected, "invalid option changed source/output/project state"
                assert snapshot(temp_root) == protected_temp, "invalid option created temporary compiler/project state"
            observed = invoke(f"admission/{subcommand}/before-input", [subcommand, "--diagnostic-cast=wrong"], admission)
            assert observed.returncode == 1 and snapshot(admission) == protected
            assert snapshot(temp_root) == protected_temp
        duplicate = ["check", source, "--strict-borrow", "--diagnostic-cast=normal"]
        baseline = invoke("same-duplicate/single", duplicate, admission)
        observed = invoke("same-duplicate/double", [*duplicate, "--diagnostic-cast=NORMAL"], admission)
        assert CAST.search(baseline.stdout) and CAST.search(observed.stdout)
        assert canonical_blocks(observed.stdout) == canonical_blocks(baseline.stdout)
        assert stable_cli_text(observed.stdout) == stable_cli_text(baseline.stdout)
        assert observed.returncode == baseline.returncode == 1 and observed.stderr == baseline.stderr

        tests_project = scratch / "json-project"
        tests_project.mkdir()
        (tests_project / "hangar.toml").write_text('[project]\nname="cast_json"\nversion="1.0.0"\nkind="app"\nentry="main.fk"\n[tests]\ninvalid="invalid.fk"\n', encoding="utf-8")
        (tests_project / "main.fk").write_text("task main() {}\n", encoding="utf-8")
        (tests_project / "invalid.fk").write_text(CASES["unbound"][0], encoding="utf-8")
        result = invoke("test-json/default", ["test", "--json"], tests_project)
        payload = json.loads(result.stdout)
        assert result.returncode == 1 and payload["schema"] == 1
        assert payload["summary"] == {"total": 1, "passed": 0, "failed": 1}
        assert payload["cases"][0]["status"] == "build_failed"
        captured = bytes.fromhex(payload["cases"][0]["build"]["stdout_hex"])
        assert canonical_blocks(captured) and not CAST.search(captured)
        assert not CAST.search(result.stdout) and not result.stderr
        for command in ("doctor", "test"):
            rejected = invoke(command + "-json/cast-rejected", [command, "--json", "--diagnostic-cast=normal"], tests_project)
            assert rejected.returncode == 1 and not CAST.search(rejected.stdout)
            if command == "test":
                report = json.loads(rejected.stdout)
                assert report["schema"] == 1 and report["cases"] == []
        evidence.update(canonical_blocks_preserved=True, statuses_preserved=True,
                        deterministic_repeat=True, invalid_options_before_effects=True,
                        equal_normalized_duplicates=True, json_modes_preserved=True)
        after = {str(path.resolve()): sha256(path) for path in pinned}
        assert before == after, "pinned CLI/source/runtime/data/payload inputs changed during gate"
        evidence["pinned_inputs_unchanged"] = True
        evidence["status"] = "pass"
    print(f"PASS native diagnostic cast CLI: {len(evidence['backend_matrices'])} backend matrices, {len(evidence['receipts'])} actual command receipts", flush=True)


if __name__ == "__main__":
    main()
