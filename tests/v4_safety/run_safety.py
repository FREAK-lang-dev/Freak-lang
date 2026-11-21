"""Run the V4 safety suites: borrow checking and every other safety contract.

Each case under ``cases/<area>/`` is one small FREAK program whose leading
``--`` comment lines say what V4 must do with it. The runner compiles every
case with the V4 compiler binary (strict root mode, host target) and compares
the stage lines and diagnostic records it prints against those directives.

Directives (one per line, before the first code line):

    -- expect: check            lex..borrowck report no errors (codegen ignored)
    -- expect: build            every stage, codegen included, reports no errors
    -- expect: run              build, link, execute; see stdout/exit below
    -- expect: panic            build, link, execute; must exit 101
    -- expect: reject <stage>   compilation stops after <stage> with errors;
                                "frontend" accepts any stage from lex to borrowck
    -- error: <text>            (reject) some error's "message|help" contains text
    -- at: <line>:<col>         (reject) the first error's span starts here (file line)
    -- errors: <n>              (reject) exactly n errors
    -- stdout: <line>           (run) expected stdout, one directive per line
    -- exit: <n>|nonzero        (run/panic) expected exit status; run defaults
                                to 0, panic to 101 (the V4 unwind panic status)
    -- panic: <text>            (panic) stdout+stderr contains text
    -- argv: <arg> ...          (run/panic) program arguments
    -- known: <issue> <note>    a filed bug: the case states the correct
                                behavior and must currently FAIL. A known case
                                that passes is reported as XPASS and fails the
                                suite, so the directive gets removed once fixed.
    -- bible: <section>         informational cross-reference

Usage (from the repository root):

    python -u tests/v4_safety/run_safety.py                # builds V4 first
    python -u tests/v4_safety/run_safety.py --compiler build/v4_smoke/.../freak_v4_compiler
    python -u tests/v4_safety/run_safety.py --area borrowck --case moves_
    python -u tests/v4_safety/run_safety.py --list

FREAK_V4_COMPILER also selects a prebuilt compiler, as for build_v4.py.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import dataclasses
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CASES_ROOT = HERE / "cases"
V4_ROOT = ROOT / "src" / "compiler" / "v4"
RUNTIME_ROOT = ROOT / "freakc" / "runtime"
WORK_ROOT = ROOT / "build" / "v4_safety"

STAGES = ("lex", "parse", "hir", "resolve", "ty", "mir", "borrowck", "entry", "codegen")
FRONTEND_STAGES = STAGES[:7]
EXPECT_KINDS = ("check", "build", "run", "panic", "reject")
DIRECTIVES = ("expect", "error", "at", "errors", "stdout", "exit", "panic",
              "argv", "known", "bible")
PANIC_EXIT = 101
DIAG_RE = re.compile(r"^(\d+)\|(\d+)@(\d+):(\d+)\|(.*)$")
STAGE_RE = re.compile(r"^v4-build-stage=(\w+) diagnostics=(\d+)$")


class CaseError(ValueError):
    """A malformed case file."""


@dataclasses.dataclass
class Case:
    path: Path
    area: str
    name: str
    expect: str
    stage: str | None = None
    errors: list[str] = dataclasses.field(default_factory=list)
    at: tuple[int, int] | None = None
    error_count: int | None = None
    stdout: list[str] | None = None
    exit: int | str = 0
    panic: list[str] = dataclasses.field(default_factory=list)
    argv: list[str] = dataclasses.field(default_factory=list)
    known: str | None = None
    bible: str | None = None

    @property
    def ident(self) -> str:
        return f"{self.area}/{self.name}"


@dataclasses.dataclass
class Diag:
    severity: int
    start: int
    end: int
    message: str
    help: str
    stage: str

    @property
    def text(self) -> str:
        return f"{self.message}|{self.help}"


@dataclasses.dataclass
class Compiled:
    stages: dict[str, int]
    diags: list[Diag]
    aborted_after: str | None
    module: str | None
    raw: str

    def errors(self) -> list[Diag]:
        return [d for d in self.diags if d.severity >= 2]


@dataclasses.dataclass
class Outcome:
    case: Case
    status: str  # pass, fail, xfail, xpass
    detail: str = ""
    seconds: float = 0.0


def parse_case(path: Path, area: str | None = None) -> Case:
    text = path.read_text(encoding="utf-8")
    area = area or path.parent.name
    fields: dict[str, list[str]] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if not stripped.startswith("--"):
            break
        body = stripped[2:].strip()
        match = re.match(r"^([a-z]+):(.*)$", body)
        if not match or match.group(1) not in DIRECTIVES:
            continue  # prose comment
        fields.setdefault(match.group(1), []).append(match.group(2).strip())
    if "expect" not in fields or len(fields["expect"]) != 1:
        raise CaseError(f"{path}: needs exactly one '-- expect:' directive")
    expect_words = fields["expect"][0].split()
    if not expect_words or expect_words[0] not in EXPECT_KINDS:
        raise CaseError(f"{path}: unknown expectation {fields['expect'][0]!r}")
    case = Case(path=path, area=area, name=path.stem, expect=expect_words[0])
    if case.expect == "reject":
        if len(expect_words) != 2 or expect_words[1] not in (*STAGES, "frontend"):
            raise CaseError(f"{path}: 'expect: reject' needs one stage of {', '.join(STAGES)} or frontend")
        case.stage = expect_words[1]
        case.errors = fields.get("error", [])
        if not case.errors:
            raise CaseError(f"{path}: a reject case needs at least one '-- error:' directive")
    elif len(expect_words) != 1:
        raise CaseError(f"{path}: 'expect: {case.expect}' takes no argument")
    if "at" in fields:
        match = re.fullmatch(r"(\d+):(\d+)", fields["at"][-1])
        if not match:
            raise CaseError(f"{path}: '-- at:' wants <line>:<col>")
        case.at = (int(match.group(1)), int(match.group(2)))
    if "errors" in fields:
        case.error_count = int(fields["errors"][-1])
    if "stdout" in fields:
        case.stdout = fields["stdout"]
    if case.expect == "panic":
        case.exit = PANIC_EXIT
        case.panic = fields.get("panic", [])
    if "exit" in fields:
        value = fields["exit"][-1]
        if value != "nonzero" and not re.fullmatch(r"-?\d+", value):
            raise CaseError(f"{path}: '-- exit:' wants an integer or nonzero")
        case.exit = value if value == "nonzero" else int(value)
    if "argv" in fields:
        case.argv = fields["argv"][-1].split()
    if case.expect != "reject" and ("error" in fields or "at" in fields or "errors" in fields):
        raise CaseError(f"{path}: error/at/errors directives need 'expect: reject'")
    if case.expect not in ("run", "panic") and ("stdout" in fields or "exit" in fields or "argv" in fields):
        raise CaseError(f"{path}: stdout/exit/argv directives need 'expect: run' or 'expect: panic'")
    if "known" in fields:
        case.known = fields["known"][-1]
        if not re.match(r"^#\d+\b", case.known):
            raise CaseError(f"{path}: '-- known:' must start with an issue number like #123")
    if "bible" in fields:
        case.bible = fields["bible"][-1]
    return case


def discover(areas: list[str] | None = None, patterns: list[str] | None = None) -> list[Case]:
    cases = []
    for path in sorted(CASES_ROOT.glob("*/*.fk")):
        area = path.parent.name
        if areas and area not in areas:
            continue
        if patterns and not any(p in f"{area}/{path.stem}" for p in patterns):
            continue
        cases.append(parse_case(path, area))
    return cases


def parse_compiler_output(stdout: str) -> Compiled:
    stages: dict[str, int] = {}
    diags: list[Diag] = []
    aborted = None
    module = None
    current = "lex"
    lines = stdout.split("\n")
    for index, raw in enumerate(lines):
        line = raw.rstrip("\r")
        if line == "@@V4-MODULE":
            module = "\n".join(lines[index + 1:])
            break
        stage = STAGE_RE.match(line)
        if stage:
            current = stage.group(1)
            stages[current] = int(stage.group(2))
            continue
        diag = DIAG_RE.match(line)
        if diag:
            message, _, help_text = diag.group(5).partition("|")
            diags.append(Diag(int(diag.group(1)), int(diag.group(3)), int(diag.group(4)),
                              message, help_text, current))
            continue
        if line.startswith("v4-native-contract-error="):
            diags.append(Diag(2, 0, 0, line.split("=", 1)[1], "", "codegen"))
            continue
        if line.startswith("v4-aborted-after="):
            aborted = line.split("=", 1)[1]
    return Compiled(stages, diags, aborted, module, stdout)


def line_col(source: bytes, offset: int) -> tuple[int, int]:
    prefix = source[:offset]
    line = prefix.count(b"\n") + 1
    return line, offset - (prefix.rfind(b"\n") + 1) + 1


def describe(compiled: Compiled, source: bytes) -> str:
    rows = []
    for d in compiled.diags:
        line, col = line_col(source, d.start) if d.start or d.end else (0, 0)
        kind = {0: "note", 1: "warning"}.get(d.severity, "error")
        rows.append(f"  {d.stage} {kind} {line}:{col}: {d.message}" + (f" | help: {d.help}" if d.help else ""))
    if compiled.aborted_after:
        rows.append(f"  aborted after {compiled.aborted_after}")
    return "\n".join(rows) if rows else "  (no diagnostics)"


class Runner:
    def __init__(self, compiler: Path, clang: str, target: str, keep: bool = False,
                 timeout: float = 60.0):
        self.compiler = compiler
        self.clang = clang
        self.target = target
        self.keep = keep
        self.timeout = timeout
        self.runtime_objects: list[Path] | None = None

    def runtime(self) -> list[Path]:
        """Compile the native runtime once; every run case links the objects."""
        if self.runtime_objects is not None:
            return self.runtime_objects
        sys.path.insert(0, str(ROOT))
        from freakc.v4_native_runtime import SOURCE_NAMES
        out_dir = WORK_ROOT / "runtime"
        out_dir.mkdir(parents=True, exist_ok=True)
        objects = []
        for name in SOURCE_NAMES:
            source = RUNTIME_ROOT / name
            obj = out_dir / (Path(name).stem + ".o")
            if not obj.exists() or obj.stat().st_mtime < source.stat().st_mtime:
                subprocess.run([self.clang, "-w", "-O1", "-c", str(source), f"-I{RUNTIME_ROOT}",
                                "-o", str(obj)], check=True)
            objects.append(obj)
        self.runtime_objects = objects
        return objects

    def link_args(self) -> list[str]:
        # The same final link flags build_v4.py uses for native programs.
        sys.path.insert(0, str(V4_ROOT))
        sys.path.insert(0, str(ROOT))
        import check_v4
        return list(check_v4.runtime_platform_final_link_args())

    def compile(self, case: Case) -> Compiled:
        proc = subprocess.run([str(self.compiler), str(case.path.resolve()), self.target],
                              capture_output=True, text=True, encoding="utf-8", errors="replace",
                              timeout=self.timeout)
        compiled = parse_compiler_output(proc.stdout)
        if proc.returncode != 0:
            compiled.aborted_after = compiled.aborted_after or f"crash(exit={proc.returncode})"
            compiled.raw += proc.stderr
        return compiled

    def execute(self, case: Case, module: str) -> tuple[int, str, str] | str:
        work = WORK_ROOT / "cases" / case.area
        work.mkdir(parents=True, exist_ok=True)
        ll = work / f"{case.name}.ll"
        exe = work / (f"{case.name}.exe" if sys.platform == "win32" else case.name)
        ll.write_text(module, encoding="utf-8")
        exe.unlink(missing_ok=True)
        linked = subprocess.run([self.clang, "-w", "-O0", str(ll), *map(str, self.runtime()),
                                 "-o", str(exe), *self.link_args()],
                                capture_output=True, text=True, timeout=self.timeout)
        if linked.returncode != 0:
            return f"link failed:\n{linked.stdout}{linked.stderr}"
        try:
            ran = subprocess.run([str(exe), *case.argv], capture_output=True, text=True,
                                 encoding="utf-8", errors="replace", timeout=self.timeout)
        except subprocess.TimeoutExpired:
            return "program timed out"
        finally:
            if not self.keep:
                ll.unlink(missing_ok=True)
        if not self.keep:
            exe.unlink(missing_ok=True)
        return ran.returncode, ran.stdout.replace("\r\n", "\n"), ran.stderr

    def judge(self, case: Case) -> str | None:
        """None when the case behaves as stated, else why not."""
        source = case.path.read_bytes()
        compiled = self.compile(case)
        if compiled.aborted_after and compiled.aborted_after.startswith("crash"):
            return f"compiler {compiled.aborted_after}\n" + compiled.raw[-2000:]
        errors = compiled.errors()
        listing = describe(compiled, source)
        if case.expect == "reject":
            stage_ok = (compiled.aborted_after in FRONTEND_STAGES if case.stage == "frontend"
                        else compiled.aborted_after == case.stage)
            if not stage_ok:
                return f"expected rejection after {case.stage}, got " + \
                       (f"rejection after {compiled.aborted_after}" if compiled.aborted_after else "no errors") + \
                       "\n" + listing
            for wanted in case.errors:
                if not any(wanted in d.text for d in errors):
                    return f"no {compiled.aborted_after} error mentions {wanted!r}\n{listing}"
            if case.error_count is not None and len(errors) != case.error_count:
                return f"expected {case.error_count} errors, got {len(errors)}\n{listing}"
            if case.at is not None:
                got = line_col(source, errors[0].start)
                if got != case.at:
                    return f"first error at {got[0]}:{got[1]}, expected {case.at[0]}:{case.at[1]}\n{listing}"
            return None
        frontend_errors = [d for d in errors if d.stage in FRONTEND_STAGES]
        if frontend_errors:
            return f"expected a clean frontend, got errors\n{listing}"
        if case.expect == "check":
            return None
        if errors or compiled.module is None:
            return f"expected a clean build\n{listing}"
        if case.expect == "build":
            return None
        result = self.execute(case, compiled.module)
        if isinstance(result, str):
            return result
        code, out, err = result
        if (code == 0) if case.exit == "nonzero" else (code != case.exit):
            return f"exit {code}, expected {case.exit}\nstdout: {out!r}\nstderr: {err!r}"
        if case.expect == "panic":
            for wanted in case.panic:
                if wanted not in out + err:
                    return f"panic output lacks {wanted!r}\nstdout: {out!r}\nstderr: {err!r}"
            return None
        if case.stdout is not None:
            expected = "".join(line + "\n" for line in case.stdout)
            if out != expected:
                return f"stdout {out!r}, expected {expected!r}"
        return None

    def run_case(self, case: Case) -> Outcome:
        started = time.monotonic()
        try:
            problem = self.judge(case)
        except subprocess.TimeoutExpired:
            problem = "compiler timed out"
        except Exception as exc:  # report, keep going
            problem = f"runner error: {exc!r}"
        seconds = time.monotonic() - started
        if case.known:
            if problem is None:
                return Outcome(case, "xpass", f"known bug {case.known} no longer reproduces; drop the known directive", seconds)
            return Outcome(case, "xfail", problem, seconds)
        return Outcome(case, "pass" if problem is None else "fail", problem or "", seconds)


def find_compiler(explicit: Path | None, clang: str) -> Path:
    if explicit:
        return explicit.resolve()
    env = os.environ.get("FREAK_V4_COMPILER", "")
    if env:
        return Path(env).resolve()
    sys.path.insert(0, str(V4_ROOT))
    sys.path.insert(0, str(ROOT))
    import build_v4
    return build_v4.bootstrap(clang)


def host_target() -> str:
    sys.path.insert(0, str(V4_ROOT))
    sys.path.insert(0, str(ROOT))
    import build_v4
    return build_v4.host_target()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--compiler", type=Path, default=None, help="prebuilt V4 compiler binary")
    parser.add_argument("--clang", default=None)
    parser.add_argument("--area", action="append", default=None, help="only this area (repeatable)")
    parser.add_argument("--case", action="append", default=None, help="only cases whose area/name contains this")
    parser.add_argument("--jobs", type=int, default=os.cpu_count() or 2)
    parser.add_argument("--list", action="store_true", help="validate and list cases without compiling")
    parser.add_argument("--keep", action="store_true", help="keep linked programs under build/v4_safety")
    parser.add_argument("--json", type=Path, default=None, help="write a JSON report")
    parser.add_argument("--verbose", action="store_true", help="print every case")
    args = parser.parse_args(argv)

    try:
        cases = discover(args.area, args.case)
    except CaseError as error:
        print(f"malformed case: {error}")
        return 2
    if not cases:
        print("no cases selected")
        return 2
    if args.list:
        for case in cases:
            flag = f"  known {case.known}" if case.known else ""
            print(f"{case.ident}: {case.expect}{' ' + case.stage if case.stage else ''}{flag}")
        print(f"{len(cases)} cases")
        return 0

    clang = args.clang or os.environ.get("CLANG") or shutil.which("clang") or "clang"
    compiler = find_compiler(args.compiler, clang)
    runner = Runner(compiler, clang, host_target(), keep=args.keep)
    if any(c.expect in ("run", "panic") for c in cases):
        runner.runtime()

    started = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        outcomes = list(pool.map(runner.run_case, cases))
    elapsed = time.monotonic() - started

    by_area: dict[str, dict[str, int]] = {}
    for outcome in outcomes:
        counts = by_area.setdefault(outcome.case.area, {"pass": 0, "fail": 0, "xfail": 0, "xpass": 0})
        counts[outcome.status] += 1
        if outcome.status in ("fail", "xpass") or args.verbose:
            label = outcome.status.upper()
            print(f"{label} {outcome.case.ident} ({outcome.case.expect})")
            if outcome.detail and outcome.status != "pass":
                for line in outcome.detail.rstrip().splitlines():
                    print(f"    {line}")
    print()
    for area, counts in sorted(by_area.items()):
        print(f"{area:<14} pass={counts['pass']} known={counts['xfail']} fail={counts['fail']} xpass={counts['xpass']}")
    total = {k: sum(c[k] for c in by_area.values()) for k in ("pass", "fail", "xfail", "xpass")}
    known = sorted({o.case.known.split()[0] for o in outcomes if o.status == "xfail"}, key=lambda s: int(s[1:]))
    print(f"V4 safety: cases={len(outcomes)} pass={total['pass']} known={total['xfail']} "
          f"fail={total['fail']} xpass={total['xpass']} elapsed={elapsed:.1f}s"
          + (f" known-issues={','.join(known)}" if known else ""))
    if args.json:
        args.json.write_text(json.dumps([{
            "case": o.case.ident, "expect": o.case.expect, "status": o.status,
            "known": o.case.known, "detail": o.detail, "seconds": round(o.seconds, 3),
        } for o in outcomes], indent=2), encoding="utf-8")
    return 1 if total["fail"] or total["xpass"] else 0


if __name__ == "__main__":
    sys.exit(main())
