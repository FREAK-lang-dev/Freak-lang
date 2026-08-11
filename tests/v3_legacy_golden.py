#!/usr/bin/env python3
"""Run the permanent V3 preservation corpus through both native backends."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


SCHEMA = "freak.v3.legacy-golden.v1"
BACKENDS = (("c", "--c", ".c"), ("llvm", "--llvm", ".ll"))


def normalize_newlines(value: str) -> str:
    """Normalize only platform newline representation, never content spacing."""
    return value.replace("\r\n", "\n").replace("\r", "\n")


def corpus_fingerprint(corpus: Path) -> dict[str, str]:
    """Bind the read-only source corpus so the runner cannot hide artifacts."""
    result: dict[str, str] = {}
    for path in sorted(item for item in corpus.rglob("*") if item.is_file()):
        relative = path.relative_to(corpus).as_posix()
        result[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def manifest_member(corpus: Path, value: Any, suffix: str) -> Path:
    assert isinstance(value, str) and value, f"manifest member is not a filename: {value!r}"
    assert "/" not in value and "\\" not in value and value not in (".", ".."), value
    relative = Path(value)
    assert relative.name == value and not relative.is_absolute(), value
    assert relative.suffix == suffix, value
    resolved = (corpus / relative).resolve()
    resolved.relative_to(corpus.resolve())
    assert resolved.is_file(), resolved
    return resolved


def load_cases(corpus: Path) -> list[dict[str, str]]:
    manifest_path = corpus / "cases.json"
    document = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert isinstance(document, dict), "golden manifest must be an object"
    assert set(document) == {"schema", "cases"}, "unexpected golden manifest keys"
    assert document["schema"] == SCHEMA, document["schema"]
    raw_cases = document["cases"]
    assert isinstance(raw_cases, list) and raw_cases, "golden manifest has no cases"

    cases: list[dict[str, str]] = []
    names: set[str] = set()
    sources: set[str] = set()
    outputs: set[str] = set()
    for raw_case in raw_cases:
        assert isinstance(raw_case, dict), raw_case
        assert {"name", "source", "stdout"} <= set(raw_case) <= {
            "name",
            "source",
            "stdout",
            "generated_contains",
        }, raw_case
        name = raw_case["name"]
        assert isinstance(name, str) and name and name not in names, name
        assert all(character.islower() or character.isdigit() or character == "_" for character in name), name
        source = manifest_member(corpus, raw_case["source"], ".fk")
        stdout = manifest_member(corpus, raw_case["stdout"], ".stdout")
        generated_contains = raw_case.get("generated_contains", "")
        assert isinstance(generated_contains, str), generated_contains
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
                "generated_contains": generated_contains,
            }
        )

    discovered_sources = {path.name for path in corpus.glob("*.fk")}
    discovered_outputs = {path.name for path in corpus.glob("*.stdout")}
    assert sources == discovered_sources, (
        f"golden source inventory mismatch: missing={sorted(discovered_sources - sources)} "
        f"extra={sorted(sources - discovered_sources)}"
    )
    assert outputs == discovered_outputs, (
        f"golden output inventory mismatch: missing={sorted(discovered_outputs - outputs)} "
        f"extra={sorted(outputs - discovered_outputs)}"
    )
    allowed_members = {"README.md", "cases.json"} | sources | outputs
    discovered_members = {path.name for path in corpus.iterdir()}
    assert discovered_members == allowed_members, (
        f"golden corpus contains untracked members: "
        f"missing={sorted(allowed_members - discovered_members)} "
        f"extra={sorted(discovered_members - allowed_members)}"
    )
    for member in corpus.iterdir():
        assert member.is_file() and not member.is_symlink(), (
            f"golden corpus member must be a regular file: {member}"
        )
    return cases


def run(command: list[str], cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        timeout=180,
        check=False,
    )


def show_output(result: subprocess.CompletedProcess[bytes]) -> str:
    return (result.stdout + result.stderr).decode("utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compile and execute the permanent V3 golden corpus with C and LLVM."
    )
    parser.add_argument("freak", type=Path, help="explicit path to a real V3 freak binary")
    args = parser.parse_args()

    freak = args.freak.resolve()
    assert freak.is_file(), f"FREAK compiler not found: {freak}"
    corpus = Path(__file__).resolve().parent / "v3_legacy" / "golden"
    before = corpus_fingerprint(corpus)
    cases = load_cases(corpus)

    env = os.environ.copy()
    # The explicit compiler under test owns its adjacent payload. An ambient
    # override must never redirect this preservation oracle to another install.
    env.pop("FREAK_HOME", None)
    assert "FREAK_HOME" not in env
    env["NO_COLOR"] = "1"
    executable_suffix = ".exe" if sys.platform == "win32" else ""

    with tempfile.TemporaryDirectory(prefix="freak-v3-legacy-golden-") as temporary:
        root = Path(temporary) / "isolated corpus"
        root.mkdir()
        for case in cases:
            expected = normalize_newlines(
                (corpus / case["stdout"]).read_text(encoding="utf-8")
            )
            for backend, flag, generated_suffix in BACKENDS:
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
                if case["generated_contains"]:
                    generated_text = generated.read_text(encoding="utf-8")
                    assert case["generated_contains"] in generated_text, (
                        f"{case['name']} ({backend}) omitted preserved generated marker "
                        f"{case['generated_contains']!r}"
                    )
                binary = source.with_suffix(executable_suffix)
                assert binary.is_file(), f"{case['name']} ({backend}) did not link {binary.name}"

                executed = run([str(binary)], case_root, env)
                actual = normalize_newlines(executed.stdout.decode("utf-8", errors="strict"))
                stderr = normalize_newlines(executed.stderr.decode("utf-8", errors="replace"))
                assert executed.returncode == 0, (
                    f"{case['name']} ({backend}) exited {executed.returncode}\n{stderr}"
                )
                assert stderr == "", f"{case['name']} ({backend}) wrote stderr:\n{stderr}"
                assert actual == expected, (
                    f"{case['name']} ({backend}) stdout mismatch\n"
                    f"expected={expected!r}\nactual={actual!r}"
                )
                print(f"PASS {case['name']} [{backend}]")

    after = corpus_fingerprint(corpus)
    assert after == before, "golden runner modified its source corpus"
    print(f"V3 legacy golden corpus: PASS ({len(cases)} cases, {len(BACKENDS)} backends)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
