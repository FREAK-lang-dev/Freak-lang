#!/usr/bin/env python3
"""Run the permanent V3 preservation corpus against an explicit distribution."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


SCHEMA = "freak.v3.legacy-golden.v2"
BACKENDS = {
    "c": ("--c", ".c"),
    "llvm": ("--llvm", ".ll"),
}

if not __debug__:
    raise SystemExit("v3_legacy_golden.py requires assertions; do not run with python -O")


def normalize_newlines(value: str) -> str:
    """Normalize only platform newline representation, never content spacing."""
    return value.replace("\r\n", "\n").replace("\r", "\n")


def corpus_fingerprint(corpus: Path) -> dict[str, str]:
    """
    Record a stable fingerprint for every member of the corpus.
    
    Parameters:
    	corpus (Path): Root directory of the corpus.
    
    Returns:
    	dict[str, str]: Mapping of relative member paths to content hashes or entry descriptors.
    """
    result: dict[str, str] = {}
    for path in sorted(corpus.rglob("*")):
        relative = path.relative_to(corpus).as_posix()
        if path.is_symlink():
            result[relative] = f"symlink:{os.readlink(path)}"
        elif path.is_dir():
            result[f"{relative}/"] = "directory"
        elif path.is_file():
            result[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
        else:
            result[relative] = "special"
    return result


def manifest_member(corpus: Path, value: Any, suffix: str) -> Path:
    """
    Validate a manifest filename and resolve it within the corpus.
    
    Parameters:
    	corpus (Path): Root directory containing the corpus.
    	value (Any): Manifest value expected to name a file.
    	suffix (str): Required filename suffix.
    
    Returns:
    	Path: Resolved path to the validated regular file.
    """
    assert isinstance(value, str) and value, f"manifest member is not a filename: {value!r}"
    assert "/" not in value and "\\" not in value and value not in (".", ".."), value
    relative = Path(value)
    assert relative.name == value and not relative.is_absolute(), value
    assert relative.suffix == suffix, value
    resolved = (corpus / relative).resolve()
    resolved.relative_to(corpus.resolve())
    assert resolved.is_file() and not resolved.is_symlink(), resolved
    return resolved


def load_cases(corpus: Path) -> list[dict[str, Any]]:
    """
    Load and validate the golden corpus manifest and return its normalized case metadata.
    
    Parameters:
    	corpus (Path): Directory containing the manifest and corpus files.
    
    Returns:
    	list[dict[str, Any]]: Validated case definitions with normalized source, output, backend, and generated-content marker metadata.
    """
    manifest_path = corpus / "cases.json"
    document = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert isinstance(document, dict), "golden manifest must be an object"
    assert set(document) == {"schema", "cases"}, "unexpected golden manifest keys"
    assert document["schema"] == SCHEMA, document["schema"]
    raw_cases = document["cases"]
    assert isinstance(raw_cases, list) and raw_cases, "golden manifest has no cases"

    cases: list[dict[str, Any]] = []
    names: set[str] = set()
    sources: set[str] = set()
    outputs: set[str] = set()
    canonical_backend_order = list(BACKENDS)
    for raw_case in raw_cases:
        assert isinstance(raw_case, dict), raw_case
        assert set(raw_case) == {
            "name",
            "source",
            "stdout",
            "backends",
            "generated_contains",
        }, raw_case
        name = raw_case["name"]
        assert isinstance(name, str) and name and name not in names, name
        assert all(
            character.islower() or character.isdigit() or character == "_"
            for character in name
        ), name
        source = manifest_member(corpus, raw_case["source"], ".fk")
        stdout = manifest_member(corpus, raw_case["stdout"], ".stdout")

        backends = raw_case["backends"]
        assert isinstance(backends, list) and backends, (
            f"{name}: backends must be a non-empty ordered list"
        )
        assert all(isinstance(backend, str) and backend in BACKENDS for backend in backends), (
            f"{name}: unknown backend in {backends!r}"
        )
        assert len(backends) == len(set(backends)), f"{name}: duplicate backend"
        assert backends == [
            backend for backend in canonical_backend_order if backend in backends
        ], f"{name}: backends are not in canonical order"

        generated_contains = raw_case["generated_contains"]
        assert isinstance(generated_contains, dict), (
            f"{name}: generated_contains must be backend-keyed"
        )
        assert set(generated_contains) <= set(backends), (
            f"{name}: markers declared for a backend the case does not run"
        )
        normalized_markers: dict[str, list[str]] = {}
        for backend, markers in generated_contains.items():
            assert isinstance(markers, list) and markers, (
                f"{name}/{backend}: marker list must be non-empty"
            )
            assert all(isinstance(marker, str) and marker for marker in markers), (
                f"{name}/{backend}: marker must be a non-empty string"
            )
            assert len(markers) == len(set(markers)), (
                f"{name}/{backend}: duplicate generated marker"
            )
            normalized_markers[backend] = markers

        assert source.name not in sources, source.name
        assert stdout.name not in outputs, stdout.name
        names.add(name)
        sources.add(source.name)
        outputs.add(stdout.name)
        cases.append(
            {
                "name": name,
                "source": source.name,
                "stdout": stdout.name,
                "backends": backends,
                "generated_contains": normalized_markers,
            }
        )

    discovered_sources = {path.name for path in corpus.glob("*.fk")}
    discovered_outputs = {path.name for path in corpus.glob("*.stdout")}
    assert sources == discovered_sources, (
        f"golden source inventory mismatch: missing={sorted(sources - discovered_sources)} "
        f"extra={sorted(discovered_sources - sources)}"
    )
    assert outputs == discovered_outputs, (
        f"golden output inventory mismatch: missing={sorted(outputs - discovered_outputs)} "
        f"extra={sorted(discovered_outputs - outputs)}"
    )
    allowed_members = {"README.md", "cases.json"} | sources | outputs
    discovered_members = {path.name for path in corpus.iterdir()}
    assert discovered_members == allowed_members, (
        "golden corpus contains untracked members: "
        f"missing={sorted(allowed_members - discovered_members)} "
        f"extra={sorted(discovered_members - allowed_members)}"
    )
    for member in corpus.iterdir():
        assert member.is_file() and not member.is_symlink(), (
            f"golden corpus member must be a regular file: {member}"
        )
    return cases


def run(
    command: list[str], cwd: Path, env: dict[str, str]
) -> subprocess.CompletedProcess[bytes]:
    """
    Execute a command in the specified directory and environment.
    
    Parameters:
    	command (list[str]): The command and its arguments.
    	cwd (Path): The working directory for the command.
    	env (dict[str, str]): Environment variables for the subprocess.
    
    Returns:
    	subprocess.CompletedProcess[bytes]: The completed process result with captured output.
    """
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        timeout=180,
        check=False,
    )


def show_output(result: subprocess.CompletedProcess[bytes]) -> str:
    """Combine and decode captured standard output and standard error.
    
    Parameters:
    	result (subprocess.CompletedProcess[bytes]): Completed subprocess result containing captured output.
    
    Returns:
    	str: The decoded standard output followed by standard error.
    """
    return (result.stdout + result.stderr).decode("utf-8", errors="replace")


def copy_adjacent_distribution(repo: Path, freak: Path, install: Path) -> Path:
    """
    Create an adjacent compiler installation from the distribution manifest.
    
    Parameters:
    	repo (Path): Repository containing the compiler and distribution manifest.
    	freak (Path): Compiler executable to install.
    	install (Path): Destination installation directory.
    
    Returns:
    	Path: Path to the installed compiler executable.
    """
    bin_dir = install / "bin"
    bin_dir.mkdir(parents=True)
    installed_freak = bin_dir / freak.name
    shutil.copy2(freak, installed_freak)

    manifest = repo / "packaging" / "distribution-files.manifest"
    for raw_line in manifest.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("|")
        assert len(parts) == 2, f"invalid distribution manifest row: {raw_line!r}"
        source_name, destination_name = parts
        source = (repo / source_name).resolve()
        destination = (install / destination_name).resolve()
        source.relative_to(repo.resolve())
        destination.relative_to(install.resolve())
        assert source.is_file(), source
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    assert (install / "runtime" / "freak_abi").is_file()
    assert (install / "std" / "freak_abi").is_file()
    return installed_freak


def assert_corpus_closure_controls(corpus: Path, root: Path) -> None:
    """
    Validate that corpus closure checks detect untracked files, nested artifact directories, and newly added directories.
    
    Parameters:
    	corpus (Path): Path to the golden corpus.
    	root (Path): Temporary root used for validation copies.
    """
    generated_copy = root / "generated-member"
    shutil.copytree(corpus, generated_copy)
    (generated_copy / "01_core.fk.ll").write_text("unlisted generated IR\n", encoding="utf-8")
    try:
        load_cases(generated_copy)
    except AssertionError as error:
        assert "untracked members" in str(error), error
    else:
        raise AssertionError("golden closure accepted an unlisted generated file")

    nested_copy = root / "nested-artifact"
    shutil.copytree(corpus, nested_copy)
    artifact_dir = nested_copy / "artifacts"
    artifact_dir.mkdir()
    (artifact_dir / "probe.ll").write_text("nested generated IR\n", encoding="utf-8")
    try:
        load_cases(nested_copy)
    except AssertionError as error:
        assert "untracked members" in str(error), error
    else:
        raise AssertionError("golden closure accepted a nested artifact directory")

    mutation_copy = root / "late-directory"
    shutil.copytree(corpus, mutation_copy)
    before = corpus_fingerprint(mutation_copy)
    (mutation_copy / "late-artifact").mkdir()
    after = corpus_fingerprint(mutation_copy)
    assert after != before, "corpus fingerprint ignored a late empty directory"
    print(
        "PASS corpus closure controls "
        "[unlisted-file,nested-directory,late-empty-directory]"
    )


def run_corpus(
    *, freak: Path, corpus: Path, env: dict[str, str], outside_root: Path
) -> None:
    """
    Compile and execute every declared golden-corpus case across its configured backends.
    
    Parameters:
        freak (Path): Path to the compiler executable.
        corpus (Path): Root directory of the golden corpus.
        env (dict[str, str]): Environment variables for compiler and executable runs.
        outside_root (Path): Directory where isolated case workspaces are created.
    """
    before = corpus_fingerprint(corpus)
    cases = load_cases(corpus)
    run_count = 0
    root = outside_root / "isolated corpus"
    root.mkdir()
    for case in cases:
        expected = normalize_newlines(
            (corpus / case["stdout"]).read_text(encoding="utf-8")
        )
        for backend in case["backends"]:
            flag, generated_suffix = BACKENDS[backend]
            case_root = root / case["name"] / backend
            case_root.mkdir(parents=True)
            source = case_root / case["source"]
            source.write_bytes((corpus / case["source"]).read_bytes())

            compiled = run([str(freak), "build", str(source), flag], case_root, env)
            assert compiled.returncode == 0, (
                f"{case['name']} ({backend}) did not compile\n{show_output(compiled)}"
            )
            generated = Path(str(source) + generated_suffix)
            assert generated.is_file(), (
                f"{case['name']} ({backend}) did not emit {generated.name}"
            )
            generated_text = generated.read_text(encoding="utf-8")
            for marker in case["generated_contains"].get(backend, []):
                assert marker in generated_text, (
                    f"{case['name']} ({backend}) omitted preserved generated marker "
                    f"{marker!r}"
                )
            executable_suffix = ".exe" if sys.platform == "win32" else ""
            binary = source.with_suffix(executable_suffix)
            assert binary.is_file(), (
                f"{case['name']} ({backend}) did not link {binary.name}"
            )

            executed = run([str(binary)], case_root, env)
            stderr = normalize_newlines(
                executed.stderr.decode("utf-8", errors="replace")
            )
            assert executed.returncode == 0, (
                f"{case['name']} ({backend}) exited {executed.returncode}\n{stderr}"
            )
            actual = normalize_newlines(
                executed.stdout.decode("utf-8", errors="strict")
            )
            assert stderr == "", f"{case['name']} ({backend}) wrote stderr:\n{stderr}"
            assert actual == expected, (
                f"{case['name']} ({backend}) stdout mismatch\n"
                f"expected={expected!r}\nactual={actual!r}"
            )
            run_count += 1
            print(f"PASS {case['name']} [{backend}]")

    after = corpus_fingerprint(corpus)
    assert after == before, "golden runner modified its source corpus"
    print(f"V3 legacy golden corpus: PASS ({len(cases)} cases, {run_count} backend runs)")


def run_internal_child(freak: Path, expected_poison: Path) -> int:
    """
    Runs the golden corpus in an isolated child environment using adjacent compiler payloads.
    
    Parameters:
    	freak (Path): Path to the compiler executable.
    	expected_poison (Path): Expected poisoned runtime path inherited through `FREAK_HOME`.
    
    Returns:
    	An exit status of zero after the isolated corpus passes.
    """
    repo = Path(__file__).resolve().parents[1]
    inherited = os.environ.get("FREAK_HOME")
    assert inherited is not None, "isolation child did not inherit FREAK_HOME poison"
    assert Path(inherited).resolve() == expected_poison.resolve(), (
        f"isolation child inherited the wrong poison: {inherited}"
    )
    env = os.environ.copy()
    env.pop("FREAK_HOME", None)
    assert "FREAK_HOME" not in env
    install = freak.parent.parent
    assert (install / "runtime" / "freak_abi").is_file(), (
        "explicit CLI has no adjacent runtime payload"
    )
    assert (install / "std" / "freak_abi").is_file(), (
        "explicit CLI has no adjacent standard-library payload"
    )
    try:
        Path.cwd().resolve().relative_to(repo.resolve())
    except ValueError:
        pass
    else:
        raise AssertionError("isolation child ran from inside the repository")
    env["NO_COLOR"] = "1"
    corpus = Path(__file__).resolve().parent / "v3_legacy" / "golden"
    with tempfile.TemporaryDirectory(prefix="freak-v3-golden-child-") as temporary:
        run_corpus(
            freak=freak,
            corpus=corpus,
            env=env,
            outside_root=Path(temporary),
        )
    print("PASS explicit adjacent payload after inherited FREAK_HOME removal")
    return 0


def main() -> int:
    """
    Validate the explicit V3 compiler against the permanent backend-specific golden corpus.
    
    Returns:
    	int: 0 after successful corpus validation, isolation checks, and corpus preservation checks.
    """
    parser = argparse.ArgumentParser(
        description="Compile and execute the permanent backend-specific V3 corpus."
    )
    parser.add_argument("freak", type=Path, help="explicit path to a real V3 freak binary")
    parser.add_argument("--internal-child", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--expected-poison", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()

    freak = args.freak.resolve()
    assert freak.is_file(), f"FREAK compiler not found: {freak}"
    if args.internal_child:
        assert args.expected_poison is not None
        return run_internal_child(freak, args.expected_poison.resolve())

    repo = Path(__file__).resolve().parents[1]
    corpus = Path(__file__).resolve().parent / "v3_legacy" / "golden"
    before = corpus_fingerprint(corpus)
    load_cases(corpus)
    with tempfile.TemporaryDirectory(prefix="freak-v3-legacy-golden-") as temporary:
        root = Path(temporary)
        assert_corpus_closure_controls(corpus, root)
        install = root / "explicit install"
        installed_freak = copy_adjacent_distribution(repo, freak, install)

        poison = root / "poison home"
        (poison / "runtime").mkdir(parents=True)
        (poison / "std").mkdir()
        (poison / "runtime" / "freak_abi").write_text(
            "poison-runtime-abi\n", encoding="utf-8"
        )
        (poison / "std" / "freak_abi").write_text(
            "poison-std-abi\n", encoding="utf-8"
        )
        poison_env = os.environ.copy()
        poison_env["FREAK_HOME"] = str(poison)
        poison_env["NO_COLOR"] = "1"
        probe = root / "poison_probe.fk"
        probe.write_text('say "poison must win"\n', encoding="utf-8")
        rejected = run(
            [str(installed_freak), "build", str(probe), "--llvm"], root, poison_env
        )
        assert rejected.returncode != 0, (
            "explicit FREAK_HOME poison did not override the healthy adjacent payload\n"
            + show_output(rejected)
        )
        assert "ABI MISMATCH" in show_output(rejected), show_output(rejected)
        assert not Path(str(probe) + ".ll").exists()
        assert not probe.with_suffix(".exe" if sys.platform == "win32" else "").exists()
        print("PASS inherited poison wins direct-build resolution")

        child = run(
            [
                sys.executable,
                "-u",
                str(Path(__file__).resolve()),
                str(installed_freak),
                "--internal-child",
                "--expected-poison",
                str(poison),
            ],
            root,
            poison_env,
        )
        assert child.returncode == 0, (
            f"isolated golden child failed ({child.returncode})\n{show_output(child)}"
        )
        assert child.stderr == b"", show_output(child)
        print(child.stdout.decode("utf-8", errors="strict"), end="")

    after = corpus_fingerprint(corpus)
    assert after == before, "preservation controls modified the tracked corpus"
    print("V3 preservation isolation/closure gate: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
