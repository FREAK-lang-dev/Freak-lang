#!/usr/bin/env python3
"""Guard generated checked int64 loops and retain matched native timings.

O0/O2/O3, exact dynamic arithmetic/overflow/evaluation oracles, real helper-call
negative controls and both ownership audits are mandatory. Default Linux mode
also requires ASan/UBSan and never publishes speed measurements. --plain adds
portable measurements: three or more repeated native runs, no time threshold.
An optional historical module is regenerated from its pinned Git compiler
commit and must match byte-for-byte; it remains separate from the executable
helper-call mutation.
Every child uses the existing numerical gate's bounded process-tree runner.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import statistics
import subprocess
import sys
import tarfile
import time

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "benchmarks/v4/int_checked_hot_loop.fk"
OPTS = (0, 2, 3)
OPERATIONS = ("add", "sub", "mul")
HOT_NAME = "int_checked_hot_loop"
BOUNDARY_INPUTS = ((0, 0), (0, 65535), (1, 0), (1, 65535),
                   (2, 17), (257, 0), (257, 17), (257, 65535), (100000, 17))
MINIMUM, MAXIMUM = -(1 << 63), (1 << 63) - 1
BASELINE_BUNDLE_LIMIT = 128 * 1024 * 1024
BASELINE_FILE_LIMIT = 4096
BASELINE_KIND = "git-archive-regeneration-v1"


class GateError(RuntimeError):
    pass


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def checksum(iterations: int, seed: int) -> int:
    if not 0 <= iterations <= 100000000 or not 0 <= seed < 65536:
        raise GateError("hot-loop inputs are outside the admitted exact-int workload")
    # Compute the geometric series modulo 2*M before division by two.
    return (seed * pow(3, iterations, 65536)
            + 17 * ((pow(3, iterations, 131072) - 1) // 2)) % 65536


def definitions(module: str) -> dict[str, tuple[str, str]]:
    rows = {}
    for match in re.finditer(r"(?ms)^(define[^\n]*@([A-Za-z0-9_.$-]+)\([^\n]*\)[^\n]*\{)\n(.*?)^\}", module):
        if match[2] in rows:
            raise GateError("duplicate LLVM function definition: " + match[2])
        rows[match[2]] = (match[1], "\n".join(line.split(";", 1)[0].rstrip() for line in match[3].splitlines()))
    return rows


def call_count(body: str, symbol: str, result_type: str = "i64") -> int:
    return len(re.findall(r"\bcall\s+" + re.escape(result_type) + r"\s+@" + re.escape(symbol) + r"\(", body))


def validate_inline(module: str) -> dict:
    funcs = definitions(module)
    if HOT_NAME not in funcs:
        raise GateError("missing actual hot-loop LLVM body")
    hot = funcs[HOT_NAME][1]
    direct = {op: call_count(hot, "freak_v4_int_" + op) for op in OPERATIONS}
    if any(direct.values()):
        raise GateError("hot loop calls original numeric helpers: " + json.dumps(direct, sort_keys=True))
    wrapper_calls = {op: call_count(hot, "freak_v4_int_" + op + "_inline") for op in OPERATIONS}
    if wrapper_calls != {"add": 2, "sub": 3, "mul": 1}:
        raise GateError("hot loop is missing its six live checked arithmetic calls")
    for op in OPERATIONS:
        name = "freak_v4_int_" + op + "_inline"
        if name not in funcs:
            raise GateError("missing checked wrapper definition: " + name)
        header, body = funcs[name]
        if not re.fullmatch(r"define internal i64 @" + name + r"\(i64 %lhs, i64 %rhs\) alwaysinline \{", header):
            raise GateError("checked wrapper must have the internal alwaysinline int64 contract")
        expected = ("entry:",
                    f"%checked = call {{ i64, i1 }} @llvm.s{op}.with.overflow.i64(i64 %lhs, i64 %rhs)",
                    "%overflow = extractvalue { i64, i1 } %checked, 1",
                    "br i1 %overflow, label %failure, label %success", "failure:",
                    f"%unused = call i64 @freak_v4_int_{op}(i64 %lhs, i64 %rhs)",
                    "unreachable", "success:",
                    "%result = extractvalue { i64, i1 } %checked, 0", "ret i64 %result")
        actual = tuple(line.strip() for line in body.splitlines() if line.strip())
        if actual != expected:
            raise GateError("checked wrapper intrinsic/result/failure CFG differs: " + name)
    return {"wrapper_calls": wrapper_calls, "direct_helper_calls": direct,
            "checked_failure_cfg": True}


def validate_helper(module: str) -> dict:
    funcs = definitions(module)
    if HOT_NAME not in funcs:
        raise GateError("helper control is missing the hot loop")
    hot = funcs[HOT_NAME][1]
    calls = {op: call_count(hot, "freak_v4_int_" + op) for op in OPERATIONS}
    if calls != {"add": 2, "sub": 3, "mul": 1}:
        raise GateError("helper control must execute the same six actual helper calls")
    try:
        validate_inline(module)
    except GateError as exc:
        if not str(exc).startswith("hot loop calls original numeric helpers:"):
            raise GateError("helper control rejected for an unrelated structural reason") from exc
        return {"actual_helper_calls": calls, "inline_rejection": str(exc)}
    raise GateError("actual old-helper lowering escaped the inline guard")


def helper_mutation(module: str) -> tuple[str, dict]:
    validate_inline(module)
    rows = []
    pattern = r"(?m)^(\s*%[^\n=]+ = call i64 @freak_v4_int_)(add|sub|mul)(_inline)(\(i64 [^\n]+)$"
    def replace(match):
        rows.append({"operation": match[2], "before": match[0],
                     "after": match[1] + match[2] + match[4]})
        return rows[-1]["after"]
    changed = re.sub(pattern, replace, module)
    if len(rows) < 6 or changed == module:
        raise GateError("helper-call mutation did not replace executable call targets")
    validate_helper(changed)
    return changed, {"kind": "executable-helper-call-mutation", "original_module_sha256": text_sha(module),
                     "mutated_module_sha256": text_sha(changed), "rewrites": rows}


def validate_live_loop(module: str, *, helpers: bool) -> dict:
    funcs = definitions(module)
    if HOT_NAME not in funcs:
        raise GateError("optimized module lost its runtime-bound hot-loop function")
    header, body = funcs[HOT_NAME]
    if len(re.findall(r"\bi64\b", header.split("(", 1)[1].split(")", 1)[0])) != 2:
        raise GateError("optimized hot loop lost its two dynamic int64 inputs")
    blocks = {}
    current = "entry"
    for line in body.splitlines():
        label = re.fullmatch(r"\s*([A-Za-z0-9_.$-]+):\s*", line)
        if label:
            current = label[1]
        blocks.setdefault(current, set()).update(re.findall(r"\blabel %([A-Za-z0-9_.$-]+)", line))
    visiting, visited = set(), set()
    def cyclic(block):
        if block in visiting:
            return True
        if block in visited:
            return False
        visiting.add(block)
        if any(cyclic(child) for child in blocks.get(block, ())):
            return True
        visiting.remove(block)
        visited.add(block)
        return False
    if not cyclic(next(iter(blocks))):
        raise GateError("optimized LLVM no longer contains a reachable runtime loop")
    actual = {op: call_count(body, "freak_v4_int_" + op) for op in OPERATIONS}
    if helpers and any(not count for count in actual.values()):
        raise GateError("optimized helper reference lost its actual arithmetic helper calls")
    if any(call_count(body, "freak_v4_int_" + op + "_inline") for op in OPERATIONS):
        raise GateError("alwaysinline wrappers remain in optimized hot-loop calls")
    return {"reachable_cycle": True, "dynamic_int64_inputs": 2, "helper_calls": actual}


def dynamic_source(source: str) -> str:
    marker = "task int_checked_hot_loop("
    if source.count(marker) != 1:
        raise GateError("benchmark parser/source boundary changed")
    return source.split(marker, 1)[0] + '''task runtime_int_effect(value: int) -> int {
    say value
    give back value
}
task main() -> int {
    if process::args_count() != 4 { give back 64 }
    pilot mode = runtime_int_argument(1)
    pilot left = runtime_int_argument(2)
    pilot right = runtime_int_argument(3)
    if mode == 0 { pilot value = runtime_int_effect(left) + runtime_int_effect(right); say value; give back 0 }
    if mode == 1 { pilot value = runtime_int_effect(left) - runtime_int_effect(right); say value; give back 0 }
    if mode == 2 { pilot value = runtime_int_effect(left) * runtime_int_effect(right); say value; give back 0 }
    if mode == 3 { runtime_int_effect(left) + runtime_int_effect(right); say "discarded"; give back 0 }
    if mode == 4 { if false and runtime_int_effect(left) + runtime_int_effect(right) > 0 { give back 70 }; say "short-circuit"; give back 0 }
    if mode == 5 { if true or runtime_int_effect(left) + runtime_int_effect(right) > 0 { say "short-circuit"; give back 0 }; give back 71 }
    give back 72
}
'''


def dynamic_cases() -> list[dict]:
    inputs = (
        (0, MAXIMUM, 0), (0, MINIMUM, 0), (0, MAXIMUM, -1), (0, MINIMUM, 1),
        (0, -7, 9), (0, MAXIMUM, 1), (0, MINIMUM, -1),
        (1, MAXIMUM, 0), (1, MINIMUM, 0), (1, MAXIMUM, MAXIMUM), (1, -7, -9),
        (1, MINIMUM, 1), (1, MAXIMUM, -1), (1, 0, MINIMUM),
        (2, MAXIMUM, 1), (2, MINIMUM, 1), (2, MAXIMUM, 0), (2, MINIMUM, 0),
        (2, -7, 9), (2, -7, -9), (2, MINIMUM, -1), (2, -1, MINIMUM),
        (2, MAXIMUM, 2), (2, MINIMUM, 2),
        (3, 19, 23), (3, MAXIMUM, 1), (3, MINIMUM, -1),
        (4, MAXIMUM, 1), (5, MAXIMUM, 1),
    )
    rows = []
    for mode, left, right in inputs:
        stdout, stderr, status = "", "", 0
        if mode >= 4:
            stdout = "short-circuit\n"
        else:
            stdout = f"{left}\n{right}\n"
            value = (left + right if mode in (0, 3) else left - right if mode == 1 else left * right)
            if not MINIMUM <= value <= MAXIMUM:
                status = 1
                operation = "addition" if mode in (0, 3) else "subtraction" if mode == 1 else "multiplication"
                stderr = "FREAK V4: int " + operation + " overflow\n"
            else:
                stdout += "discarded\n" if mode == 3 else str(value) + "\n"
        rows.append({"argv": [str(mode), str(left), str(right)], "exit": status,
                     "stdout": stdout, "stderr": stderr})
    return rows


@contextmanager
def source_imports(work: Path):
    prefix = work / "unused-source-cache"
    if prefix.exists():
        raise GateError("source import cache namespace must be fresh")
    old = (sys.pycache_prefix, sys.dont_write_bytecode)
    sys.pycache_prefix, sys.dont_write_bytecode = str(prefix), True
    try:
        yield prefix
        if prefix.exists():
            raise GateError("source-only proof unexpectedly produced repository bytecode")
    finally:
        sys.pycache_prefix, sys.dont_write_bytecode = old


def dependencies():
    sys.path[:0] = [str(ROOT), str(ROOT / "tests"), str(ROOT / "src/compiler/v4")]
    import v4_checked_numeric_codegen as numeric
    import v4_scalar_sum_codegen as scalar
    import build_v4 as build
    from freakc import v4_native_runtime as inventory
    expected = ((numeric, ROOT / "tests/v4_checked_numeric_codegen.py"),
                (scalar, ROOT / "tests/v4_scalar_sum_codegen.py"),
                (build, ROOT / "src/compiler/v4/build_v4.py"),
                (build.checks, ROOT / "src/compiler/v4/check_v4.py"),
                (inventory, ROOT / "freakc/v4_native_runtime.py"))
    if any(Path(module.__file__).resolve() != path.resolve() for module, path in expected):
        raise GateError("native runtime gate imported a different checkout's compiler/harness")
    return numeric, scalar, build, inventory.SOURCE_NAMES, inventory.HEADER_NAMES


def head_identity() -> str:
    result = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                            capture_output=True, text=True, timeout=10)
    if result.returncode or re.fullmatch(r"[a-f0-9]{40}\n?", result.stdout) is None:
        raise GateError("cannot pin compiler Git head")
    return result.stdout.strip()


class Identity:
    def __init__(self, inputs: list[Path], clang: Path):
        self.head = head_identity()
        self.inputs = {path.relative_to(ROOT).as_posix(): sha(path) for path in inputs}
        self.clang, self.clang_sha = clang, sha(clang)
        self.artifacts = {}
        self.extra_checks = []

    def seal(self, path: Path):
        digest = sha(path)
        if str(path) in self.artifacts and self.artifacts[str(path)] != digest:
            raise GateError("sealed artifact was replaced")
        self.artifacts[str(path)] = digest

    def check(self):
        if (head_identity() != self.head or sha(self.clang) != self.clang_sha
                or any(sha(ROOT / path) != digest for path, digest in self.inputs.items())
                or any(sha(Path(path)) != digest for path, digest in self.artifacts.items())):
            raise GateError("compiler/source/tool/runtime/artifact identity changed during proof")
        for check in self.extra_checks:
            check()


def baseline_path(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if (not name or path.is_absolute() or path.as_posix() != name or "\\" in name
            or ":" in name or any(ord(character) < 32 or ord(character) == 127 for character in name)
            or any(part in ("", ".", "..") for part in name.split("/"))
            or any(part.endswith((" ", ".")) or re.fullmatch(
                r"(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", part) for part in path.parts)):
        raise GateError("unsafe historical compiler archive path")
    return path


def baseline_tree(text: str) -> dict:
    entries, aliases, size = {}, set(), 0
    for row in text.split("\0"):
        if not row:
            continue
        metadata, separator, name = row.partition("\t")
        fields = metadata.split()
        if (not separator or len(fields) != 4 or fields[0] not in ("100644", "100755")
                or fields[1] != "blob" or re.fullmatch(r"[a-f0-9]{40}", fields[2]) is None
                or re.fullmatch(r"\d+", fields[3]) is None):
            raise GateError("historical compiler tree contains unsupported non-file Git objects")
        baseline_path(name)
        if name.casefold() in aliases:
            raise GateError("historical compiler tree contains duplicate/case-aliased paths")
        aliases.add(name.casefold())
        size += int(fields[3])
        entries[name] = {"mode": fields[0], "blob": fields[2], "size": int(fields[3])}
    if not entries or len(entries) > BASELINE_FILE_LIMIT or size > BASELINE_BUNDLE_LIMIT:
        raise GateError("historical compiler tree exceeds the bounded archive inventory")
    return entries


def baseline_manifest_sha(entries: dict) -> str:
    return text_sha(json.dumps(entries, sort_keys=True, separators=(",", ":")))


def extract_baseline(archive: Path, bundle: Path, head: str, entries: dict) -> dict:
    # Avoid extractall: no archive member may create links, devices or aliases.
    if archive.stat().st_size > BASELINE_BUNDLE_LIMIT + BASELINE_FILE_LIMIT * 4096:
        raise GateError("historical compiler archive exceeds its bounded inventory")
    bundle.mkdir(exist_ok=False)
    observed, seen, aliases = {}, set(), set()
    with tarfile.open(archive, "r:") as packed:
        if packed.pax_headers.get("comment") != head:
            raise GateError("historical compiler archive is not bound to the pinned Git commit")
        for member in packed:
            name = member.name.rstrip("/") if member.isdir() else member.name
            relative = baseline_path(name)
            if name in seen or name.casefold() in aliases:
                raise GateError("historical compiler archive contains duplicate/case-aliased paths")
            seen.add(name); aliases.add(name.casefold())
            destination = bundle.joinpath(*relative.parts)
            if member.isdir():
                if not any(path.startswith(name + "/") for path in entries):
                    raise GateError("historical compiler archive contains an untracked directory")
                destination.mkdir(parents=True, exist_ok=True)
                continue
            expected = entries.get(name)
            if not member.isfile() or expected is None or member.size != expected["size"]:
                raise GateError("historical compiler archive differs from its Git blob inventory")
            stream = packed.extractfile(member)
            if stream is None:
                raise GateError("historical compiler archive cannot read a tracked blob")
            with stream:
                content = stream.read(BASELINE_BUNDLE_LIMIT + 1)
            blob = hashlib.sha1(b"blob " + str(len(content)).encode("ascii") + b"\0" + content).hexdigest()
            if len(content) != member.size or blob != expected["blob"]:
                raise GateError("historical compiler archive bytes differ from the pinned Git blob")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
            destination.chmod(0o755 if expected["mode"] == "100755" else 0o644)
            observed[name] = {**expected, "sha256": hashlib.sha256(content).hexdigest()}
    if set(observed) != set(entries):
        raise GateError("historical compiler archive omits pinned Git blobs")
    return observed


def check_baseline_bundle(bundle: Path, entries: dict) -> None:
    actual = {path.relative_to(bundle).as_posix() for path in bundle.rglob("*") if not path.is_dir()}
    if actual != set(entries) or any(path.is_symlink() for path in bundle.rglob("*")):
        raise GateError("historical compiler bundle file inventory changed during proof")
    for name, entry in entries.items():
        path = bundle / name
        if (not path.is_file() or path.stat().st_size != entry["size"] or sha(path) != entry["sha256"]
                or (os.name != "nt" and path.stat().st_mode & 0o777 != (0o755 if entry["mode"] == "100755" else 0o644))):
            raise GateError("historical compiler bundle inputs changed during proof")


BASELINE_PRODUCER = '''import hashlib, json, os, shutil, sys, time
from pathlib import Path
config = json.loads(sys.argv[1])
bundle = Path(config["bundle"]).resolve()
work = Path(config["work"]).resolve()
os.chdir(bundle)
sys.path[:0] = [str(bundle / "src/compiler/v4"), str(bundle)]
import build_v4 as build
checks = build.checks
if Path(build.__file__).resolve() != bundle / "src/compiler/v4/build_v4.py" or checks.ROOT.resolve() != bundle:
    raise RuntimeError("historical producer imported a different compiler bundle")
checks.RUNTIME_BUILD_ROOT = work / "bootstrap"
checks.RUNTIME_BUILD_ROOT.mkdir(exist_ok=False)
original_which = shutil.which
shutil.which = lambda name, *a, **kw: config["clang"] if name == "clang" else original_which(name, *a, **kw)
original_run, original_compile = checks.run_with_heartbeat, checks.compile_runtime_smoke
proof = {"jobs": [], "fresh_bootstrap": False, "entrypoint": str(Path(build.__file__).resolve())}
def guarded_run(command, **kwargs):
    command = list(command)
    if kwargs.get("label") == "V4 LLVM verification":
        command[command.index("-o") + 1] = str(work / "verified.o")
    kwargs["timeout_seconds"] = min(kwargs.get("timeout_seconds") or 120, 120)
    kwargs["memory_limit_mb"] = min(kwargs.get("memory_limit_mb") or 512, 512)
    kwargs["output_limit_mb"] = 8
    row = {"command": command, "label": kwargs.get("label"), "timeout_seconds": kwargs["timeout_seconds"],
           "memory_limit_mib": kwargs["memory_limit_mb"], "output_limit_mib_per_stream": 8}
    proof["jobs"].append(row)
    serial = len(proof["jobs"])
    stem = work / ("producer-%03d" % serial)
    stem.with_suffix(".command.json").write_text(json.dumps(command) + "\\n", encoding="utf-8")
    started = time.perf_counter_ns()
    result = original_run(command, **kwargs)
    row.update(exit=result.returncode, elapsed_ns=time.perf_counter_ns() - started,
               stdout_sha256=hashlib.sha256(result.stdout.encode("utf-8")).hexdigest(),
               stderr_sha256=hashlib.sha256(result.stderr.encode("utf-8")).hexdigest())
    stem.with_suffix(".stdout").write_bytes(result.stdout.encode("utf-8"))
    stem.with_suffix(".stderr").write_bytes(result.stderr.encode("utf-8"))
    return result
def fresh_compile(*args, **kwargs):
    flags = args[6] if len(args) > 6 else kwargs.get("extra_cflags", ())
    flags = tuple(flags) + ("-DFREAK_ARRAY_LIVE_LIMIT=1024",)
    if len(args) > 6:
        args = (*args[:6], flags, *args[7:])
    else:
        kwargs["extra_cflags"] = flags
    executable, compiled = original_compile(*args, **kwargs)
    if not compiled:
        raise RuntimeError("historical producer reused a cached compiler")
    proof["fresh_bootstrap"] = True
    proof["compiler_binary"] = str(executable)
    proof["generated_c"] = str(executable.parent / "build_llvm.fk.c")
    return executable, compiled
checks.run_with_heartbeat, checks.compile_runtime_smoke = guarded_run, fresh_compile
sys.argv = [str(bundle / "src/compiler/v4/build_v4.py"), config["source"], "-o", config["module"],
            "--emit-llvm", "--target", config["target"], "--compiler-opt", "2"]
try:
    proof["exit"] = build.main()
finally:
    (work / "producer.json").write_text(json.dumps(proof, indent=2, sort_keys=True) + "\\n", encoding="utf-8")
raise SystemExit(proof["exit"])
'''


def require_baseline_match(generated: Path, supplied: Path) -> None:
    if generated.read_bytes() != supplied.read_bytes():
        raise GateError("historical baseline module bytes differ from the pinned compiler regeneration")


def historical_baseline(args, report: dict, runner, identity: Identity, clang: Path, target: str) -> str:
    supplied = args.baseline_module.resolve(strict=True)
    identity.seal(supplied)
    if args.baseline_source_sha256 != report["source_sha256"]:
        raise GateError("historical baseline source hash differs from the live workload")
    git = shutil.which("git")
    if git is None:
        raise GateError("Git is required to regenerate the historical compiler baseline")
    git_path, python_path = Path(git).resolve(strict=True), Path(sys.executable).resolve(strict=True)
    identity.seal(git_path); identity.seal(python_path)
    git_command = [git, "-C", str(ROOT)]
    first_job = len(report["jobs"])
    def git_run(arguments, label):
        result = runner.run([*git_command, *arguments], label, timeout=120, memory=512)
        if result.returncode:
            raise GateError("cannot resolve/archive the pinned historical compiler commit")
        return result.stdout
    head = git_run(["rev-parse", "--verify", args.baseline_compiler_head + "^{commit}"], "baseline resolve commit").strip()
    tree = git_run(["rev-parse", "--verify", head + "^{tree}"], "baseline resolve tree").strip()
    if head != args.baseline_compiler_head or re.fullmatch(r"[a-f0-9]{40}", tree) is None:
        raise GateError("historical compiler commit/tree identity differs from the requested pin")
    entries = baseline_tree(git_run(["ls-tree", "-r", "-l", "-z", "--full-tree", head], "baseline list Git blobs"))
    work = args.work / "historical-producer"
    work.mkdir(exist_ok=False)
    archive, bundle = work / "compiler.tar", work / "compiler"
    git_run(["archive", "--format=tar", "--output=" + str(archive), head], "baseline archive pinned compiler")
    identity.seal(archive)
    entries = extract_baseline(archive, bundle, head, entries)
    check_baseline_bundle(bundle, entries)
    identity.extra_checks.append(lambda: check_baseline_bundle(bundle, entries))
    manifest = work / "compiler-inputs.json"
    manifest.write_text(json.dumps(entries, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    identity.seal(manifest)
    source, module, wrapper = work / "hot-loop.fk", work / "regenerated.ll", work / "produce.py"
    source.write_bytes(SOURCE.read_bytes())
    wrapper.write_text(BASELINE_PRODUCER, encoding="utf-8")
    identity.seal(source); identity.seal(wrapper)
    config = {"bundle": str(bundle), "work": str(work), "source": str(source), "module": str(module),
              "clang": str(clang), "target": target}
    producer = runner.run([sys.executable, "-I", "-B", str(wrapper), json.dumps(config, sort_keys=True)],
                          "baseline regenerate and verify LLVM", timeout=120, memory=512)
    if producer.returncode:
        raise GateError("historical compiler regeneration/LLVM verification failed")
    proof_path = work / "producer.json"
    proof = json.loads(proof_path.read_text(encoding="utf-8"))
    identity.seal(proof_path)
    require_baseline_match(module, supplied)
    for key in ("compiler_binary", "generated_c"):
        artifact = Path(proof[key]).resolve(strict=True)
        if not artifact.is_relative_to(work / "bootstrap"):
            raise GateError("historical producer compiler artifact is outside its fresh bootstrap")
        identity.seal(artifact)
        proof[key + "_sha256"] = sha(artifact)
    verified = work / "verified.o"
    identity.seal(module); identity.seal(verified)
    baseline = module.read_bytes().decode("utf-8")
    # Equality above compares the original bytes. Windows native stream EOL
    # handling happens only afterwards, as for the gate's current compiler.
    if sys.platform.startswith("win"):
        baseline = baseline.replace("\r\n", "\n")
    if not baseline.startswith('target triple = "' + target + '"\n'):
        raise GateError("historical baseline target differs from the current compiler target")
    report["historical_baseline"] = {"kind": BASELINE_KIND, "compiler_head": head, "compiler_tree": tree,
        "compiler_inputs": entries, "compiler_manifest_sha256": baseline_manifest_sha(entries),
        "manifest_path": str(manifest), "manifest_file_sha256": sha(manifest),
        "archive_path": str(archive), "archive_sha256": sha(archive), "bundle_path": str(bundle),
        "git": {"selected": git, "resolved": str(git_path), "sha256": sha(git_path)},
        "python": {"selected": sys.executable, "resolved": str(python_path), "sha256": sha(python_path)},
        "source_path": str(source), "source_sha256": sha(source), "target": target,
        "path": str(supplied), "module_sha256": sha(supplied), "regenerated_module_path": str(module),
        "regenerated_module_sha256": sha(module), "module_bytes_equal": True,
        "verified_object_path": str(verified), "verified_object_sha256": sha(verified),
        "producer_audit_path": str(proof_path), "producer_audit_sha256": sha(proof_path),
        "producer_wrapper_path": str(wrapper), "producer_wrapper_sha256": sha(wrapper),
        "producer": proof, "producer_job_serials": [row["serial"] for row in report["jobs"][first_job:]],
        "inline_rejection": validate_helper(baseline),
        "provenance_note": "regenerated from verified pinned Git blobs; exact supplied source/module bytes; matched current runtime objects/flags"}
    identity.check()
    validate_historical_provenance({**report, "artifact_sha256": identity.artifacts})
    return baseline


def validate_historical_provenance(report: dict) -> None:
    pin = report.get("historical_baseline", {})
    def digest(value, length=64):
        return isinstance(value, str) and re.fullmatch(r"[a-f0-9]{%d}" % length, value) is not None
    if (pin.get("kind") != BASELINE_KIND or not digest(pin.get("compiler_head"), 40)
            or not digest(pin.get("compiler_tree"), 40) or pin.get("target") != report.get("target")
            or pin.get("source_sha256") != report.get("source_sha256")
            or pin.get("module_bytes_equal") is not True or not digest(pin.get("module_sha256"))
            or pin.get("regenerated_module_sha256") != pin.get("module_sha256")):
        raise GateError("historical baseline lacks exact pinned compiler regeneration provenance")
    entries = pin.get("compiler_inputs", {})
    if (not entries or len(entries) > BASELINE_FILE_LIMIT or not digest(pin.get("compiler_manifest_sha256"))
            or pin["compiler_manifest_sha256"] != baseline_manifest_sha(entries)):
        raise GateError("historical baseline lacks the verified Git compiler blob manifest")
    total_size, aliases = 0, set()
    for name, entry in entries.items():
        baseline_path(name)
        if name.casefold() in aliases:
            raise GateError("historical compiler blob manifest contains case-aliased paths")
        aliases.add(name.casefold())
        if (entry.get("mode") not in ("100644", "100755") or not digest(entry.get("blob"), 40)
                or not digest(entry.get("sha256")) or not isinstance(entry.get("size"), int) or entry["size"] < 0):
            raise GateError("historical compiler blob manifest is incomplete")
        total_size += entry["size"]
    if total_size > BASELINE_BUNDLE_LIMIT:
        raise GateError("historical compiler blob manifest exceeds its bounded inventory")
    for path_key, digest_key in (("archive_path", "archive_sha256"), ("source_path", "source_sha256"),
            ("path", "module_sha256"), ("regenerated_module_path", "regenerated_module_sha256"),
            ("verified_object_path", "verified_object_sha256"), ("producer_audit_path", "producer_audit_sha256"),
            ("producer_wrapper_path", "producer_wrapper_sha256"), ("manifest_path", "manifest_file_sha256")):
        if not digest(pin.get(digest_key)) or report["artifact_sha256"].get(pin.get(path_key)) != pin.get(digest_key):
            raise GateError("historical baseline provenance artifact is not sealed")
    for name in ("git", "python"):
        tool = pin.get(name, {})
        if (not tool.get("selected") or not digest(tool.get("sha256"))
                or report["artifact_sha256"].get(tool.get("resolved")) != tool.get("sha256")):
            raise GateError("historical baseline is missing its pinned Git/Python tool identity")
    producer = pin.get("producer", {})
    bundle = Path(pin.get("bundle_path", ""))
    if (producer.get("exit") != 0 or producer.get("fresh_bootstrap") is not True
            or producer.get("entrypoint") != str(bundle / "src/compiler/v4/build_v4.py")
            or "src/compiler/v4/build_v4.py" not in entries or "src/compiler/v4/check_v4.py" not in entries):
        raise GateError("historical baseline did not build its frozen compiler entrypoint")
    for key in ("compiler_binary", "generated_c"):
        if (not digest(producer.get(key + "_sha256"))
                or report["artifact_sha256"].get(producer.get(key)) != producer.get(key + "_sha256")):
            raise GateError("historical baseline lacks fresh bootstrap compiler identities")
    jobs = producer.get("jobs", [])
    if (len(jobs) != 3 or not str(jobs[0].get("label", "")).startswith("runtime compile: ")
            or jobs[1].get("label") != "V4 compile: hot-loop.fk"
            or jobs[2].get("label") != "V4 LLVM verification"):
        raise GateError("historical baseline lacks real bootstrap/emission/LLVM verification jobs")
    for row in jobs:
        if (row.get("exit") != 0 or not 0 < row.get("timeout_seconds", 0) <= 120
                or not 0 < row.get("memory_limit_mib", 0) <= 512 or row.get("output_limit_mib_per_stream") != 8
                or not digest(row.get("stdout_sha256")) or not digest(row.get("stderr_sha256"))
                or not isinstance(row.get("elapsed_ns"), int) or row["elapsed_ns"] <= 0):
            raise GateError("historical compiler producer job failed or exceeded the original budgets")
    clang = report["clang"]["resolved"]
    if (jobs[0]["command"][0] != clang or "-DFREAK_ARRAY_LIVE_LIMIT=1024" not in jobs[0]["command"]
            or jobs[1]["command"] != [producer["compiler_binary"], pin["source_path"], pin["target"]]
            or jobs[2]["command"] != [clang, "--target=" + pin["target"], "-x", "ir", "-c",
                                      pin["regenerated_module_path"], "-o", pin["verified_object_path"]]):
        raise GateError("historical compiler producer used mismatched source/tool/target/handle inputs")
    serials = pin.get("producer_job_serials", [])
    retained = {row.get("serial"): row for row in report.get("jobs", [])}
    if len(serials) != 5 or len(set(serials)) != 5 or any(serial not in retained for serial in serials):
        raise GateError("historical compiler provenance is missing its guarded Git/producer job matrix")
    matrix = [retained[serial] for serial in serials]
    labels = ["baseline resolve commit", "baseline resolve tree", "baseline list Git blobs",
              "baseline archive pinned compiler", "baseline regenerate and verify LLVM"]
    if [row.get("label") for row in matrix] != labels or any(
            row.get("exit") != 0 or row.get("timeout_seconds") != 120 or row.get("memory_limit_mib") != 512
            or row.get("output_limit_mib_per_stream") != 8 for row in matrix):
        raise GateError("historical baseline guarded producer jobs are missing or failed")
    git = matrix[0]["command"][0]
    if git != pin["git"]["selected"]:
        raise GateError("historical baseline Git jobs used a different Git executable")
    git_prefix = [git, "-C", str(ROOT)]
    expected_commands = [
        [*git_prefix, "rev-parse", "--verify", pin["compiler_head"] + "^{commit}"],
        [*git_prefix, "rev-parse", "--verify", pin["compiler_head"] + "^{tree}"],
        [*git_prefix, "ls-tree", "-r", "-l", "-z", "--full-tree", pin["compiler_head"]],
        [*git_prefix, "archive", "--format=tar", "--output=" + pin["archive_path"], pin["compiler_head"]]]
    if (any(row["command"] != command for row, command in zip(matrix, expected_commands))
            or matrix[0].get("stdout_sha256") != text_sha(pin["compiler_head"] + "\n")
            or matrix[1].get("stdout_sha256") != text_sha(pin["compiler_tree"] + "\n")):
        raise GateError("historical baseline compiler/tree pin was not resolved by the retained Git jobs")
    command = matrix[-1]["command"]
    if (len(command) != 5 or command[0] != pin["python"]["selected"]
            or command[1:4] != ["-I", "-B", pin["producer_wrapper_path"]]
            or json.loads(command[4]) != {"bundle": str(bundle), "work": str(Path(pin["archive_path"]).parent),
                "source": pin["source_path"], "module": pin["regenerated_module_path"], "clang": clang, "target": pin["target"]}):
        raise GateError("historical baseline producer did not use its frozen archive/workload/tool configuration")


def validate_report(report: dict) -> None:
    def digest(value):
        return isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) is not None
    if (re.fullmatch(r"[a-f0-9]{40}", report.get("compiler_head", "")) is None
            or not digest(report.get("clang", {}).get("sha256"))
            or not digest(report.get("source_sha256"))
            or report.get("compiler_inputs", {}).get("benchmarks/v4/int_checked_hot_loop.fk") != report.get("source_sha256")
            or not digest(report.get("compiler", {}).get("binary_sha256"))
            or not digest(report.get("compiler", {}).get("generated_c_sha256"))
            or report.get("compiler", {}).get("live_handle_limit") != 1024):
        raise GateError("missing frozen source/compiler/tool/handle identity")
    for key in ("runtime_sources", "runtime_headers"):
        if len(report.get(key, {})) != 7 or any(not digest(value) for value in report[key].values()):
            raise GateError("missing frozen runtime source/header identity")
    if not report.get("artifact_sha256") or any(not digest(value) for value in report["artifact_sha256"].values()):
        raise GateError("missing frozen compiled artifact identities")
    variants = report["variants"]
    if variants not in (["current", "helper-mutation"], ["current", "helper-mutation", "historical-baseline"]):
        raise GateError("required current/helper variants are missing or mislabeled")
    if "historical-baseline" in variants:
        validate_historical_provenance(report)
    elif "historical_baseline" in report:
        raise GateError("historical provenance cannot label a helper-only run")
    if report["structural"].get("wrapper_calls") != {"add": 2, "sub": 3, "mul": 1} or report["structural"].get("checked_failure_cfg") is not True:
        raise GateError("missing actual inline/failure structural evidence")
    if report["negative_control"].get("actual_helper_calls") != {"add": 2, "sub": 3, "mul": 1}:
        raise GateError("missing genuine original-helper negative control")
    audit_flags = ("-DFREAK_RUNTIME_OWNERSHIP_AUDIT=1", "-DFREAK_C_RUNTIME_OWNERSHIP_AUDIT=1")
    for opt in OPTS:
        flags = report["build_flags"].get(str(opt), [])
        if f"-O{opt}" not in flags or not set(audit_flags).issubset(flags):
            raise GateError("optimization or required audit flags missing")
        if report["sanitized"] and "-fsanitize=address,undefined,float-cast-overflow" not in flags:
            raise GateError("mandatory sanitizer native build flags missing")
        if len(report["runtime_objects"].get(str(opt), {})) != 7:
            raise GateError("incomplete frozen native runtime object inventory")
        if any(not digest(value) or report["artifact_sha256"].get(path) != value
               for path, value in report["runtime_objects"][str(opt)].items()):
            raise GateError("runtime objects differ from sealed compiled artifacts")
    expected = {(variant, opt, n, seed) for variant in variants for opt in OPTS for n, seed in BOUNDARY_INPUTS}
    observed = [(r["variant"], r["optimization"], r["iterations"], r["seed"]) for r in report["boundaries"]]
    if len(observed) != len(expected) or set(observed) != expected:
        raise GateError("incomplete/duplicate O0/O2/O3 runtime-bound workload matrix")
    for row in report["boundaries"]:
        if not digest(row.get("binary_sha256")) or not digest(row.get("module_sha256")):
            raise GateError("native workload lacks module/binary identity")
        if (row["exit"] != 0 or row["stdout_sha256"] != text_sha(str(checksum(row["iterations"], row["seed"])) + "\n")
                or row["stderr_sha256"] != text_sha("")):
            raise GateError("runtime-bound workload report has incorrect checksum/status/output")
    wanted = {(opt, index) for opt in OPTS for index in range(len(dynamic_cases()))}
    observed = [(r["optimization"], r["case"]) for r in report["dynamic"]]
    if len(observed) != len(wanted) or set(observed) != wanted:
        raise GateError("incomplete dynamic signed/evaluation case matrix")
    for row in report["dynamic"]:
        if not digest(row.get("binary_sha256")) or not digest(row.get("module_sha256")):
            raise GateError("dynamic signed execution lacks module/binary identity")
        expected_case = dynamic_cases()[row["case"]]
        if any(row[key] != expected_case[key] for key in ("argv", "exit")) or any(
                row[key + "_sha256"] != text_sha(expected_case[key]) for key in ("stdout", "stderr")):
            raise GateError("dynamic signed report has an incorrect exact native oracle")
    wanted_optimized = {(variant, opt) for variant in variants for opt in OPTS}
    observed_optimized = [(r["variant"], r["optimization"]) for r in report["optimized"]]
    if len(observed_optimized) != len(wanted_optimized) or set(observed_optimized) != wanted_optimized:
        raise GateError("missing optimized LLVM loop evidence")
    for row in report["optimized"]:
        if row["facts"].get("reachable_cycle") is not True or row["facts"].get("dynamic_int64_inputs") != 2:
            raise GateError("optimized loop evidence is not live/dynamic")
        if any(not digest(row.get(key)) for key in ("module_sha256", "optimized_module_sha256", "binary_sha256")):
            raise GateError("optimized loop module/binary hashes are missing")
    wanted_controls = {f"audit-{kind}-O{opt}" for kind in ("C", "LLVM") for opt in OPTS}
    if report["sanitized"]:
        wanted_controls |= {"sanitizer-address", "sanitizer-undefined"}
    if len(report["controls"]) != len(wanted_controls) or set(report["controls"]) != wanted_controls:
        raise GateError("missing working audit/sanitizer controls")
    if report["sanitized"]:
        if report["timings"] or report["medians"]:
            raise GateError("sanitizer timings must not be published as performance evidence")
    else:
        samples = report["samples"]
        wanted = {(variant, opt, sample) for variant in variants for opt in OPTS for sample in range(samples)}
        observed = [(r["variant"], r["optimization"], r["sample"]) for r in report["timings"]]
        if samples < 3 or len(observed) != len(wanted) or set(observed) != wanted:
            raise GateError("matched native timing matrix is incomplete")
        for row in report["timings"]:
            if not digest(row.get("binary_sha256")) or not digest(row.get("module_sha256")):
                raise GateError("native timing lacks module/binary identity")
            if (row["exit"] != 0 or row["stdout_sha256"] != text_sha(str(checksum(report["iterations"], report["seed"])) + "\n")
                    or row["stderr_sha256"] != text_sha("") or not isinstance(row["elapsed_ns"], int)
                    or row["elapsed_ns"] <= 0):
                raise GateError("native timing lacks live exact checksum/exit/elapsed evidence")
        wanted_medians = {(variant, opt) for variant in variants for opt in OPTS}
        observed_medians = [(row["variant"], row["optimization"]) for row in report["medians"]]
        if len(observed_medians) != len(wanted_medians) or set(observed_medians) != wanted_medians:
            raise GateError("matched native timing medians are incomplete")
        for row in report["medians"]:
            times = [r["elapsed_ns"] for r in report["timings"] if r["variant"] == row["variant"] and r["optimization"] == row["optimization"]]
            if row["samples"] != samples or row["median_ns"] != statistics.median(times):
                raise GateError("native timing median differs from retained samples")


def run_gate(args, report: dict) -> None:
    numeric, scalar, build, source_names, header_names = dependencies()
    checks = build.checks
    work = args.work.resolve()
    selected = shutil.which(args.clang)
    if selected is None:
        raise GateError("required Clang executable was not found")
    clang = Path(selected).resolve(strict=True)
    runtime_paths = [checks.RUNTIME_ROOT / name for name in source_names]
    header_paths = [checks.RUNTIME_ROOT / name for name in header_names]
    inputs = [SOURCE, Path(__file__), ROOT / "tests/test_v4_int_inline_runtime_bench.py",
              ROOT / "tests/v4_checked_numeric_codegen.py", ROOT / "tests/v4_scalar_sum_codegen.py",
              Path(checks.__file__), ROOT / "src/compiler/v4/build_v4.py",
              checks.TESTS_ROOT / "checked_numeric_execute_smoke.fk", checks.TESTS_ROOT / "checked_numeric_contract_smoke.fk",
              *runtime_paths, *header_paths, *(checks.crate_path(name) for name in checks.CRATE_ORDER),
              *sorted((ROOT / "freakc").glob("**/*.py"))]
    identity = Identity(list(dict.fromkeys(inputs)), clang)
    report.update(compiler_head=identity.head, compiler_inputs=identity.inputs,
                  clang={"selected": selected, "resolved": str(clang), "sha256": identity.clang_sha},
                  runtime_sources={p.name: sha(p) for p in runtime_paths},
                  runtime_headers={p.name: sha(p) for p in header_paths})

    class PinnedRunner(numeric.Runner):
        def run(self, command, label, *, timeout=60, memory=64):
            identity.check()
            started = time.perf_counter_ns()
            result = super().run(command, label, timeout=timeout, memory=memory)
            elapsed = time.perf_counter_ns() - started
            identity.check()
            row = {"serial": self.serial, "command": command, "label": label, "exit": result.returncode,
                   "timeout_seconds": timeout, "memory_limit_mib": memory, "output_limit_mib_per_stream": 8,
                   "elapsed_ns": elapsed, "stdout_sha256": text_sha(numeric.normalized(result.stdout, sys.platform)),
                   "stderr_sha256": text_sha(numeric.normalized(result.stderr, sys.platform))}
            report["jobs"].append(row)
            return result

    runner = PinnedRunner(checks, work)
    version = runner.run([str(clang), "--version"], "Clang identity", timeout=30, memory=128)
    numeric.require_compile(version, "Clang identity")
    report["clang"]["version"] = version.stdout
    target = build.host_target()
    report["target"] = target
    link_target = scalar.native_link_target(str(clang), runner, work, target, report)
    execution = checks.read_text(checks.TESTS_ROOT / "checked_numeric_execute_smoke.fk")
    contracts = checks.read_text(checks.TESTS_ROOT / "checked_numeric_contract_smoke.fk")
    assembled = numeric.assemble_probe(execution, contracts, target)
    (work / "probe.fk").write_text(assembled, encoding="utf-8")
    identity.seal(work / "probe.fk")
    fake_fixture = checks.TESTS_ROOT / "int_inline_runtime_probe.fk"
    c_source, diagnostics, uses_ui = checks.transpile(checks.check_flattened_crates() + "\n" + assembled,
                                                     fake_fixture.with_suffix(".flat.fk"))
    if diagnostics or not c_source or uses_ui:
        raise GateError("int runtime compiler assembly failed: " + str(diagnostics))
    old_root = checks.RUNTIME_BUILD_ROOT
    checks.RUNTIME_BUILD_ROOT = work
    try:
        probe, _ = checks.compile_runtime_smoke(str(clang), f"-I{checks.RUNTIME_ROOT}",
            checks.RUNTIME_ROOT / "freak_runtime.c", checks.read_text(checks.RUNTIME_ROOT / "freak_runtime.c"),
            fake_fixture, c_source, ("-DFREAK_ARRAY_LIVE_LIMIT=1024", "-O2"))
    finally:
        checks.RUNTIME_BUILD_ROOT = old_root
    if checks.C_ARRAY_HANDLE_RESOURCE_LIMIT != 1024:
        raise GateError("compiler live-handle gate changed from 1024")
    identity.seal(probe)
    identity.seal(work / "int_inline_runtime_probe.fk.c")
    report["compiler"] = {"binary_sha256": sha(probe), "generated_c_sha256": sha(work / "int_inline_runtime_probe.fk.c"),
                          "live_handle_limit": 1024, "memory_limit_mib": 64, "optimization": 2}
    source = SOURCE.read_text(encoding="utf-8")
    copied_source = work / "hot-loop.fk"
    copied_source.write_bytes(SOURCE.read_bytes())
    identity.seal(copied_source)
    report["source_sha256"] = sha(copied_source)

    def emit(path, name):
        result = runner.run([str(probe), str(path), target], "emit " + name)
        module = numeric.parse_module(result)
        llvm = work / (name + ".ll")
        llvm.write_text(module, encoding="utf-8")
        identity.seal(llvm)
        return module

    module = emit(copied_source, "current")
    report["structural"] = validate_inline(module)
    mutated, report["mutation"] = helper_mutation(module)
    modules = {"current": module, "helper-mutation": mutated}
    report["negative_control"] = validate_helper(mutated)
    if args.baseline_module:
        modules["historical-baseline"] = historical_baseline(args, report, runner, identity, clang, target)
    report["variants"] = list(modules)
    controls_path = work / "dynamic-signed.fk"
    controls_path.write_text(dynamic_source(source), encoding="utf-8")
    identity.seal(controls_path)
    controls_module = emit(controls_path, "dynamic-signed")
    report["dynamic_source_sha256"] = sha(controls_path)
    modules["dynamic-signed"] = controls_module
    suffix = ".exe" if sys.platform.startswith("win") else ".native"
    objects, binaries = {}, {}
    for opt in OPTS:
        flags = ["-w", f"-O{opt}", f"-I{checks.RUNTIME_ROOT}", *numeric.AUDIT_FLAGS]
        if not args.plain:
            flags += list(numeric.SANITIZER_FLAGS)
        numeric.validate_build_flags(flags, not args.plain)
        report["build_flags"][str(opt)] = flags
        objects[opt] = []
        for runtime in runtime_paths:
            obj = work / (runtime.stem + f".O{opt}.o")
            compiled = runner.run([str(clang), *flags, "-c", str(runtime), "-o", str(obj)],
                                  f"compile {runtime.name} O{opt}", timeout=120, memory=512)
            numeric.require_compile(compiled, "runtime object")
            identity.seal(obj)
            objects[opt].append(str(obj))
        report["runtime_objects"][str(opt)] = {path: sha(Path(path)) for path in objects[opt]}
        for variant, text in modules.items():
            llvm = work / (variant + ".native.ll")
            if opt == OPTS[0]:
                llvm.write_text(scalar.native_link_module(text, target, link_target), encoding="utf-8")
                identity.seal(llvm)
            binary = work / (variant + f".O{opt}" + suffix)
            compiled = runner.run([str(clang), *flags, str(llvm), *objects[opt], "-o", str(binary),
                                  *checks.runtime_platform_final_link_args()],
                                 f"link {variant} O{opt}", timeout=120, memory=512)
            numeric.require_compile(compiled, "native benchmark")
            identity.seal(binary)
            binaries[variant, opt] = binary
            if variant != "dynamic-signed":
                optimized = work / (variant + f".optimized.O{opt}.ll")
                compiled = runner.run([str(clang), f"-O{opt}", "-S", "-emit-llvm", str(llvm), "-o", str(optimized)],
                                      f"retain optimized {variant} O{opt}", timeout=120, memory=512)
                numeric.require_compile(compiled, "optimized LLVM evidence")
                identity.seal(optimized)
                facts = validate_live_loop(optimized.read_text(encoding="utf-8"), helpers=variant != "current")
                report["optimized"].append({"variant": variant, "optimization": opt,
                    "module_sha256": sha(llvm), "optimized_module_sha256": sha(optimized),
                    "binary_sha256": sha(binary), "facts": facts})

    def execute(variant, opt, argv, label):
        result = runner.run([str(binaries[variant, opt]), *argv], label, timeout=30, memory=128)
        row = dict(report["jobs"][-1])
        row.update(variant=variant, optimization=opt, binary_sha256=sha(binaries[variant, opt]),
                   module_sha256=sha(work / (variant + ".native.ll")))
        return result, row

    for opt in OPTS:
        for variant in report["variants"]:
            for n, seed in BOUNDARY_INPUTS:
                result, row = execute(variant, opt, [str(n), str(seed)], f"{variant} O{opt} n{n} seed{seed}")
                numeric.exact_result(result, 0, str(checksum(n, seed)) + "\n", "", "hot-loop checksum")
                row.update(iterations=n, seed=seed)
                report["boundaries"].append(row)
        for index, case in enumerate(dynamic_cases()):
            result, row = execute("dynamic-signed", opt, case["argv"], f"dynamic signed {index} O{opt}")
            numeric.exact_result(result, case["exit"], case["stdout"], case["stderr"], "dynamic signed/evaluation oracle")
            row.update(case=index, argv=case["argv"])
            report["dynamic"].append(row)

    audit_source = work / "audit-probe.c"
    audit_source.write_text('''#include "freak_runtime.h"
#include "freak_v4_word_runtime.h"
int main(int argc, char **argv) {
    if (argc != 2) return 9;
    if (argv[1][0] == 'C') { volatile freak_word value = freak_word_from_int(7); (void)value; }
    else { volatile int64_t value = freak_v4_word_from_int(7); (void)value; }
    return 0;
}
''', encoding="utf-8")
    identity.seal(audit_source)
    for opt in OPTS:
        binary = work / (f"audit-probe.O{opt}" + suffix)
        compiled = runner.run([str(clang), *report["build_flags"][str(opt)], str(audit_source), *objects[opt],
                              "-o", str(binary), *checks.runtime_platform_final_link_args()],
                             f"link audit O{opt}", timeout=120, memory=512)
        numeric.require_compile(compiled, "audit capability")
        identity.seal(binary)
        for kind, status in (("C", 87), ("LLVM", 86)):
            result = runner.run([str(binary), kind], f"audit {kind} O{opt}", timeout=30, memory=128)
            numeric.exact_result(result, status, "", f"FREAK: {kind} ownership audit found 1 unreleased word allocation(s)\n", "audit capability")
            report["controls"].append(f"audit-{kind}-O{opt}")
    if not args.plain:
        sanitizer = work / "sanitizer-probe.c"
        sanitizer.write_text('''#include <stdlib.h>
#include <limits.h>
int main(int argc, char **argv) {
    if (argc != 2) return 9;
    if (argv[1][0] == 'a') { volatile char *p = malloc(1); free((void *)p); return p[0]; }
    volatile int value = INT_MAX; volatile int one = 1; return value + one;
}
''', encoding="utf-8")
        identity.seal(sanitizer)
        binary = work / ("sanitizer-probe" + suffix)
        compiled = runner.run([str(clang), "-O0", *numeric.SANITIZER_FLAGS, str(sanitizer), "-o", str(binary)],
                             "link sanitizer capabilities", timeout=120, memory=512)
        numeric.require_compile(compiled, "sanitizer capability")
        identity.seal(binary)
        for kind in ("address", "undefined"):
            result = runner.run([str(binary), kind], "sanitizer " + kind, timeout=30, memory=128)
            numeric.validate_sanitizer_probe(result, kind)
            report["controls"].append("sanitizer-" + kind)
    else:
        argv = [str(args.iterations), str(args.seed)]
        expected = str(checksum(args.iterations, args.seed)) + "\n"
        for opt in OPTS:
            for variant in report["variants"]:
                result, _ = execute(variant, opt, argv, f"warmup {variant} O{opt}")
                numeric.exact_result(result, 0, expected, "", "warmup live checksum")
            for sample in range(args.samples):
                order = report["variants"] if sample % 2 == 0 else list(reversed(report["variants"]))
                for variant in order:
                    result, row = execute(variant, opt, argv, f"sample{sample} {variant} O{opt}")
                    numeric.exact_result(result, 0, expected, "", "measured live checksum")
                    row.update(sample=sample, iterations=args.iterations, seed=args.seed)
                    report["timings"].append(row)
            for variant in report["variants"]:
                times = [row["elapsed_ns"] for row in report["timings"] if row["variant"] == variant and row["optimization"] == opt]
                report["medians"].append({"variant": variant, "optimization": opt,
                    "samples": len(times), "median_ns": statistics.median(times)})
    identity.check()
    report["artifact_sha256"] = identity.artifacts
    validate_report(report)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clang", default=os.environ.get("FREAK_CLANG") or shutil.which("clang"))
    parser.add_argument("--plain", action="store_true", help="portable exact oracles and unsanitized matched native timings")
    parser.add_argument("--work", type=Path, required=True, help="fresh evidence directory")
    parser.add_argument("--iterations", type=int, default=5000000)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--baseline-module", type=Path)
    parser.add_argument("--baseline-source-sha256")
    parser.add_argument("--baseline-compiler-head")
    args = parser.parse_args(argv)
    if not args.clang:
        parser.error("Clang is mandatory; generated runtime benchmarks cannot be skipped")
    if not args.plain and not sys.platform.startswith("linux"):
        parser.error("default mandatory sanitizer proof requires Linux; --plain adds portability")
    checksum(args.iterations, args.seed)
    if args.iterations < 1 or args.samples < 3:
        parser.error("measurements require positive iterations and at least three native samples")
    provenance = (args.baseline_module, args.baseline_source_sha256, args.baseline_compiler_head)
    if any(provenance) and (not all(provenance) or re.fullmatch(r"[a-f0-9]{64}", args.baseline_source_sha256 or "") is None
                           or re.fullmatch(r"[a-f0-9]{40}", args.baseline_compiler_head or "") is None):
        parser.error("historical baseline requires its module, exact source SHA256 and original compiler commit")
    args.work = args.work.resolve()
    args.work.mkdir(parents=True, exist_ok=False)
    report = {"schema": "v4-int-inline-runtime-v1", "passed": False, "sanitized": not args.plain,
        "iterations": args.iterations, "seed": args.seed, "samples": args.samples,
        "timing_protocol": "plain guarded native job wall time including bounded capture/logging; compiler excluded; alternating variant order; one warmup; no speed threshold",
        "variants": [], "boundaries": [], "dynamic": [], "optimized": [], "controls": [],
        "timings": [], "medians": [], "jobs": [], "build_flags": {}, "runtime_objects": {}}
    try:
        with source_imports(args.work):
            numeric, _, _, _, _ = dependencies()
            with numeric.sanitizer_environment(not args.plain):
                run_gate(args, report)
        report["passed"] = True
        print("checked int64 runtime gate PASS" + (" (matched plain timings)" if args.plain else " (ASan + UBSan; no timings)"), flush=True)
        return 0
    except Exception as exc:
        report["error"] = str(exc)
        print("checked int64 runtime gate FAILED: " + str(exc), file=sys.stderr, flush=True)
        return 1
    finally:
        (args.work / "results.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
