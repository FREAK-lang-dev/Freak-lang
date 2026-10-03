#!/usr/bin/env python3
"""Test actual owned-word Unicode lowercase against pinned Unicode 17 UCD.

The reference parser and backwards/forwards context oracle are independent of
the generator's range tables and the native linear state machine. No host
unicodedata or locale casing is used. Default mode requires ASan/UBSan; --plain
is an additional portability gate. Input fetching requires explicit --download.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import shutil
import signal
import subprocess
import sys
import tempfile


def assert_named_panic(result: subprocess.CompletedProcess[bytes], diagnostic: str,
                       *, platform: str = sys.platform) -> None:
    # POSIX abort must terminate with SIGABRT; Microsoft CRT abort exits 3.
    # The probe suppresses Windows abort reporting. Exact output also rejects
    # sanitizer reports, ownership audits and a crash after the diagnostic.
    expected = (3 if platform == "win32" else -signal.SIGABRT,
                b"", diagnostic.encode("ascii"))
    actual = (result.returncode, result.stdout,
              result.stderr.replace(b"\r\n", b"\n"))
    if actual != expected:
        raise AssertionError(f"expected named panic {expected!r}; actual {actual!r}")


def reference(inputs: dict[str, str]) -> tuple[dict[int, tuple[int, ...]], set[int], set[int]]:
    lower = {}
    for record in inputs["UnicodeData.txt"].splitlines():
        fields = record.split(";")
        if fields[13]:
            lower[int(fields[0], 16)] = (int(fields[13], 16),)
    default_context = []
    for record in inputs["SpecialCasing.txt"].splitlines():
        content = record.partition("#")[0].strip()
        if not content:
            continue
        fields = content.split(";")
        condition = fields[4].strip()
        if not condition:
            lower[int(fields[0], 16)] = tuple(int(cp, 16) for cp in fields[1].split())
        elif not set(condition.split()) & {"lt", "tr", "az"}:
            default_context.append((int(fields[0], 16), condition, fields[1].strip()))
    assert default_context == [(0x03A3, "Final_Sigma", "03C2")]
    properties = {"Cased": set(), "Case_Ignorable": set()}
    for record in inputs["DerivedCoreProperties.txt"].splitlines():
        content = record.partition("#")[0].strip()
        if not content:
            continue
        fields = [field.strip() for field in content.split(";")]
        if fields[1] in properties:
            endpoints = fields[0].split("..")
            properties[fields[1]].update(range(int(endpoints[0], 16), int(endpoints[-1], 16) + 1))
    cased, ignorable = properties["Cased"], properties["Case_Ignorable"]
    assert len(cased) == 4632 and len(ignorable) == 2794 and len(cased & ignorable) == 268
    return lower, cased, ignorable


def lowercase(text: str, mapping: dict[int, tuple[int, ...]], cased: set[int], ignorable: set[int]) -> str:
    scalars = tuple(map(ord, text))
    result = []
    for index, scalar in enumerate(scalars):
        output = mapping.get(scalar, (scalar,))
        if scalar == 0x03A3:
            before, after = index - 1, index + 1
            while before >= 0 and scalars[before] in ignorable:
                before -= 1
            while after < len(scalars) and scalars[after] in ignorable:
                after += 1
            if before >= 0 and scalars[before] in cased and (after == len(scalars) or scalars[after] not in cased):
                output = (0x03C2,)
        result.extend(map(chr, output))
    return "".join(result)


def vectors(mapping: dict[int, tuple[int, ...]], cased: set[int], ignorable: set[int]) -> list[tuple[str, str]]:
    manual = {
        "": "", "already lower": "already lower", "ASCII": "ascii",
        "ÀÉÇȺȾKİ": "àéçⱥⱦki\u0307", "Σ": "σ", "ΟΣ": "ος", "ΟΣΑ": "οσα",
        "AΣΣ": "aσς", "AΣ'B": "aσ'b", "AΣ'": "aς'", "AΣ🙂B": "aς🙂b",
        "AΣ\0B": "aς\0b", "A\0Σ": "a\0σ", "\0A\0": "\0a\0",
        "\u0345Σ": "\u0345σ", "AΣ\u0345": "aς\u0345", "AΣ\u0345B": "aσ\u0345b",
        "ǅΣ": "ǆς", "ⅠΣ": "ⅰς", "I\u0307İI\u0301": "i\u0307i\u0307i\u0301",
        "ßﬃς中🙂": "ßﬃς中🙂", "\U00010400": "\U00010428",
        "\U00016EA0Σ": "\U00016EBBς",
    }
    cases = {}
    for source, expected in manual.items():
        assert lowercase(source, mapping, cased, ignorable) == expected, (source, expected)
        cases[source] = "specified context/script/ownership semantics"
    for scalar in sorted(mapping):
        cases.setdefault(chr(scalar), "every UCD lowercase mapping source")
    for scalar in sorted(cased):
        cases.setdefault(chr(scalar) + "Σ", "every Cased property before sigma")
        cases.setdefault("AΣ" + chr(scalar), "every Cased property after sigma")
    for scalar in sorted(ignorable):
        cases.setdefault("AΣ" + chr(scalar) + "B", "every Case_Ignorable property before cased suffix")
        cases.setdefault("AΣ" + chr(scalar), "every Case_Ignorable property at word end")
        cases.setdefault(chr(scalar) + "Σ", "every Case_Ignorable property before sigma")
    # Every Unicode scalar, including unassigned/non-BMP values, is processed in
    # bounded 1024-scalar words; surrogates are not valid word input.
    chunk = []
    for scalar in range(0x110000):
        if 0xD800 <= scalar <= 0xDFFF:
            continue
        chunk.append(chr(scalar))
        if len(chunk) == 1024:
            cases.setdefault("".join(chunk), "complete Unicode scalar domain")
            chunk.clear()
    if chunk:
        cases.setdefault("".join(chunk), "complete Unicode scalar domain")
    random_source = random.Random("FREAK Unicode 17 default lowercase")
    alphabet = tuple(sorted(set(mapping) | cased | ignorable | {0, 0x20, 0x27, 0x03A3, 0x1F642, 0x16EA0, 0x10FFFF}))
    for _ in range(4000):
        source = []
        for _ in range(random_source.randrange(1, 25)):
            scalar = random_source.choice(alphabet) if random_source.randrange(4) else random_source.randrange(0x110000)
            if not 0xD800 <= scalar <= 0xDFFF:
                source.append(chr(scalar))
        cases.setdefault("".join(source), "arbitrary mixed Unicode reference oracle")
    cases["A" + "\u0301" * 4096 + "Σ" + "\u0345" * 4096] = "long original-string ignorable context"
    return list(cases.items())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ucd-dir", type=Path, required=True)
    parser.add_argument("--download", action="store_true", help="explicitly fetch hash-pinned official Unicode inputs before testing")
    parser.add_argument("--clang", default=os.environ.get("FREAK_CLANG") or shutil.which("clang"))
    parser.add_argument("--plain", action="store_true")
    parser.add_argument("--runtime-root", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if not args.clang:
        parser.error("clang is required; native Unicode verification cannot be skipped")
    repo = Path(__file__).resolve().parents[1]
    runtime = (args.runtime_root or repo / "freakc/runtime").resolve()
    generator_path = repo / "tools/generate_v4_unicode_lower.py"
    spec = importlib.util.spec_from_file_location("freak_unicode_generator", generator_path)
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    if args.download:
        generator.download_inputs(args.ucd_dir)
    inputs = generator.verified_inputs(args.ucd_dir)
    assert (runtime / "freak_v4_unicode_lower_tables.h").read_bytes() == generator.render(inputs).encode("utf-8"), "Unicode tables are stale or non-deterministic"
    # A changed upstream input must fail its digest guard before parsing it.
    with tempfile.TemporaryDirectory(prefix="freak-unicode-pin-") as changed:
        directory = Path(changed)
        for name in generator.INPUT_SHA256:
            shutil.copyfile(args.ucd_dir / name, directory / name)
        with (directory / "UnicodeData.txt").open("ab") as stream:
            stream.write(b"\n")
        try:
            generator.verified_inputs(directory)
        except ValueError as error:
            assert "UnicodeData.txt SHA256 mismatch" in str(error)
        else:
            raise AssertionError("modified Unicode input was accepted")
    mapping, cased, ignorable = reference(inputs)
    cases = vectors(mapping, cased, ignorable)
    payload = "\n".join(source.encode("utf-8").hex() for source, _ in cases) + "\n"
    expected = []
    for source, _ in cases:
        result = lowercase(source, mapping, cased, ignorable)
        encoded = result.encode("utf-8")
        expected.append(f"{encoded.hex()} {len(encoded)} {len(result)}")
    environment = dict(os.environ)
    for name in ("ASAN_OPTIONS", "LSAN_OPTIONS", "UBSAN_OPTIONS"):
        environment.pop(name, None)
    if not args.plain:
        environment["ASAN_OPTIONS"] = "halt_on_error=1:detect_leaks=1:exitcode=86"
        environment["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1:exitcode=85"
    rejected = {
        "consumed": "FREAK: V4 Unicode panic: word value has been consumed\n",
        "foreign": "FREAK: V4 Unicode panic: word value is not a live owner\n",
        "foreign-invalid-pointer": "FREAK: V4 Unicode panic: word value is not a live owner\n",
        "stale": "FREAK: V4 Unicode panic: word value is not a live owner\n",
        "size-overflow": "FREAK: V4 Unicode panic: lowercase byte length overflow\n",
        "size-max": "FREAK: V4 Unicode panic: lowercase byte length overflow\n",
        "allocation": "FREAK: V4 Unicode panic: out of memory lowercasing word\n",
        "mutated-utf8": "FREAK: V4 word panic: invalid UTF-8\n",
    }
    with tempfile.TemporaryDirectory(prefix="freak-v4-unicode-") as temporary:
        binary = Path(temporary) / ("unicode.exe" if sys.platform == "win32" else "unicode")
        command = [args.clang, "-std=c11", "-O1", "-g", "-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1", "-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1", "-I", str(runtime), str(repo / "tests/v4_unicode_runtime_probe.c"), str(runtime / "freak_v4_word_runtime.c"), "-o", str(binary)]
        command += ["-lws2_32"] if sys.platform == "win32" else ["-lm"]
        if not args.plain:
            command += ["-fsanitize=address,undefined", "-fno-omit-frame-pointer"]
        compiled = subprocess.run(command, capture_output=True, timeout=120, env=environment)
        assert compiled.returncode == 0, compiled.stdout + compiled.stderr
        def execute(*arguments: str, data: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
            return subprocess.run([str(binary), *arguments], input=data, cwd=temporary, capture_output=True, timeout=60, env=environment)
        accepted = execute()
        assert accepted.returncode == 0 and accepted.stdout.replace(b"\r\n", b"\n") == b"v4-unicode-storage=ok\n" and not accepted.stderr, (accepted.returncode, accepted.stdout, accepted.stderr)
        tested = execute("--batch", data=payload.encode("ascii"))
        assert tested.returncode == 0 and not tested.stderr, (tested.returncode, tested.stderr)
        actual = tested.stdout.decode("ascii").splitlines()
        assert len(actual) == len(expected), (len(actual), len(expected))
        for index, (result, wanted) in enumerate(zip(actual, expected)):
            assert result == wanted, (cases[index][1], cases[index][0].encode("unicode_escape"), result, wanted)
        for mode, diagnostic in rejected.items():
            failed = execute(mode)
            assert_named_panic(failed, diagnostic)
    report = {
        "unicode_version": generator.VERSION, "mode": "plain" if args.plain else "ASan+UBSan", "status": "pass",
        "reference_inputs_sha256": generator.INPUT_SHA256, "official_ucd": generator.OFFICIAL_BASE, "official_mirror": generator.MIRROR_BASE,
        "cases": len(cases), "source_scalars": sum(len(source) for source, _ in cases), "categories": dict(Counter(label for _, label in cases)),
        "all_unicode_scalars": 0x110000 - 0x800, "cased_property_scalars": len(cased), "case_ignorable_property_scalars": len(ignorable), "property_overlap": len(cased & ignorable),
        "named_failures": len(rejected), "exact_panic_status_and_output": True,
        "large_word_cleanup_iterations": 32, "both_ownership_audits": True,
        "source_sha256": {str(path.relative_to(repo)) if path.is_relative_to(repo) else str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in [generator_path, Path(__file__).resolve(), repo / "tests/v4_unicode_runtime_probe.c", runtime / "freak_v4_unicode_runtime.c", runtime / "freak_v4_unicode_runtime.h", runtime / "freak_v4_unicode_lower_tables.h", runtime / "freak_v4_word_runtime.c", runtime / "freak_v4_word_runtime.h", runtime / "freak_runtime.c", runtime / "freak_runtime.h"]},
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Unicode 17 owned lowercase: {len(cases)} oracle cases, complete scalar domain, 8 named failures, zero owners; {report['mode']} PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
