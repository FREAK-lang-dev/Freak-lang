"""
FREAK Lite CLI — transpile, compile, and run .fk programs.

Usage:
    python -m freakc run <file.fk>     Transpile + compile + execute
    python -m freakc build <file.fk>   Transpile + compile only
    python -m freakc check <file.fk>   Type-check only (no compilation)
    python -m freakc test              Run all tests/*.fk files
    python -m freakc <file.fk>         Same as 'run' (default)

Options:
    --keep-c        Keep the generated .c file
    -o, --output    Output binary name
"""

from __future__ import annotations

import glob

# ── Colour helpers ──────────────────────────────────────────────────
# Force UTF-8 on Windows
import io
import os
import shutil
import subprocess
import sys
from pathlib import Path

from .auditor import (
    audit_conformance,
    audit_miracles,
    audit_science,
    audit_trust,
    foreshadow_audit,
)
from .diagnostics import (
    format_emit_error,
    format_legacy_diagnostic,
    format_parse_error,
)
from .emitter import CEmitter, EmitError
from .parser import ParseError, Parser
from .type_checker import TypeChecker

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def _c(code: str, msg: str) -> str:
    if not sys.stderr.isatty():
        return msg
    return f"\033[{code}m{msg}\033[0m"


def _dim(msg):
    return _c("90", msg)


def _green(msg):
    return _c("92", msg)


def _yellow(msg):
    return _c("93", msg)


def _red(msg):
    return _c("91", msg)


def _bold(msg):
    return _c("1", msg)


# ── Import resolution ─────────────────────────────────────────────

# Map module paths to .fk source files (relative to project root).
# Order matters — dependencies listed first.
_MODULE_FILES: dict[str, list[str]] = {
    "std::ui": ["std/ui/window.fk"],
    "std::math3d": ["std/math3d.fk"],
    "std::zip": ["std/zip.fk"],
    "cockpit": [
        # Order: containers → theme → layout → widgets → ui
        "packages/cockpit/src/containers.fk",
        "packages/cockpit/src/theme.fk",
        "packages/cockpit/src/layout.fk",
        "packages/cockpit/src/widgets.fk",
        "packages/cockpit/src/ui.fk",
    ],
    "freak-ui": [
        "packages/cockpit/src/containers.fk",
        "packages/cockpit/src/theme.fk",
        "packages/cockpit/src/layout.fk",
        "packages/cockpit/src/widgets.fk",
        "packages/cockpit/src/ui.fk",
    ],
    "freak_ui": [
        "packages/cockpit/src/containers.fk",
        "packages/cockpit/src/theme.fk",
        "packages/cockpit/src/layout.fk",
        "packages/cockpit/src/widgets.fk",
        "packages/cockpit/src/ui.fk",
    ],
}


def _find_project_root(start: Path) -> Path:
    """Walk up from start looking for CLAUDE.md or .git as project root marker."""
    p = start.resolve()
    for _ in range(20):
        if (p / "CLAUDE.md").exists() or (p / ".git").exists():
            return p
        parent = p.parent
        if parent == p:
            break
        p = parent
    return start.resolve().parent  # fallback: file's directory


def resolve_imports(source: str, source_path: Path) -> tuple[str, bool]:
    """Scan source for `use` statements, resolve to .fk files, concatenate.

    Returns (combined_source, uses_ui).
    The combined source has library code prepended (with their own `use` lines
    stripped) so the parser sees one big compilation unit.
    """
    project_root = _find_project_root(source_path)
    uses_ui = False
    needed_modules: list[str] = []  # preserve order, no dupes

    for line in source.splitlines():
        stripped = line.strip()
        if not stripped.startswith("use "):
            continue
        # Extract module path: "use std::ui::{...}" → "std::ui"
        rest = stripped[4:].strip()
        # Find the module part before the last ::{ or ::Name
        # e.g. "std::ui::{Window, Canvas}" → module = "std::ui"
        # e.g. "cockpit::{UI, Theme}" → module = "cockpit"
        parts = rest.split("::")
        # Build module name by taking parts until we hit { or a capitalized name
        module_parts = []
        for part in parts:
            clean = part.strip().rstrip(",").rstrip("}")
            if clean.startswith("{") or (clean and clean[0].isupper()):
                break
            if clean == "*":
                break
            module_parts.append(clean)
        module = "::".join(module_parts)

        if module in _MODULE_FILES and module not in needed_modules:
            needed_modules.append(module)
            if module == "std::ui" or module == "cockpit" or module == "freak-ui" or module == "freak_ui":
                uses_ui = True

    # Also detect direct ui:: calls without a use statement
    if not uses_ui and "ui::" in source:
        uses_ui = True

    if not needed_modules:
        return source, uses_ui

    # Ensure std::ui comes before cockpit/freak-ui (UI package depends on std::ui types)
    if ("cockpit" in needed_modules or "freak-ui" in needed_modules or "freak_ui" in needed_modules) and "std::ui" not in needed_modules:
        needed_modules.insert(0, "std::ui")

    # Collect library sources in order
    lib_sources: list[str] = []
    already_included: set[str] = set()

    for module in needed_modules:
        for rel_path in _MODULE_FILES[module]:
            if rel_path in already_included:
                continue
            already_included.add(rel_path)

            fk_path = project_root / rel_path
            if not fk_path.exists():
                print(_yellow(f"  warning: cannot resolve '{rel_path}' for module '{module}'"),
                      file=sys.stderr)
                continue

            lib_src = fk_path.read_text(encoding="utf-8")
            # Join multi-line expressions first (so multi-line `use` becomes one line)
            lib_src = _join_continuation_lines(lib_src)
            # Strip `use` lines from library files (they reference modules
            # we're already including in this compilation unit)
            filtered_lines = []
            for lib_line in lib_src.splitlines():
                if lib_line.strip().startswith("use "):
                    filtered_lines.append(f"-- [resolved] {lib_line.strip()}")
                else:
                    filtered_lines.append(lib_line)
            lib_sources.append("\n".join(filtered_lines))

    # Only join continuation lines in user source if it has resolved imports
    # (avoids breaking large single-file programs like the v2 compiler)
    if needed_modules:
        source = _join_continuation_lines(source)
    # Strip `use` lines from the user's source too (for resolved modules)
    user_lines = []
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("use "):
            # Check if this use references a resolved module
            resolved = False
            for module in needed_modules:
                if module.replace("::", "::") in stripped:
                    resolved = True
                    break
            if resolved:
                user_lines.append(f"-- [resolved] {stripped}")
            else:
                user_lines.append(line)
        else:
            user_lines.append(line)

    combined = "\n\n".join(lib_sources) + "\n\n" + "\n".join(user_lines)
    return combined, uses_ui


def _join_continuation_lines(source: str) -> str:
    """Collapse multi-line expressions into single lines.

    FREAK's parser treats newlines as statement terminators, so multi-line
    function calls like:
        Color::rgb(
            255, 0, 0
        )
    must become: Color::rgb(255, 0, 0)

    Also joins multi-line `use` statements (which use { } for import lists).
    """
    lines = source.splitlines()
    result: list[str] = []
    paren_depth = 0
    bracket_depth = 0
    brace_depth = 0  # only tracked for `use` statements
    in_use = False  # whether we're inside a multi-line `use` statement
    accumulator = ""

    for line in lines:
        stripped = line.strip()
        # Skip comments for depth counting but preserve them
        if stripped.startswith("--"):
            if paren_depth > 0 or bracket_depth > 0 or in_use:
                # Inside an open expression — skip comment lines
                continue
            else:
                result.append(line)
                continue

        is_continuation = paren_depth > 0 or bracket_depth > 0 or in_use

        if is_continuation:
            # Continuation: append to accumulator (strip leading whitespace)
            accumulator += " " + stripped
        else:
            # Flush previous accumulator if any
            if accumulator:
                result.append(accumulator)
                accumulator = ""
            accumulator = line
            # Check if this is a `use` statement with braces
            if stripped.startswith("use "):
                in_use = True
                brace_depth = 0

        # Count parens/brackets/braces in this line (ignoring strings)
        in_string = False
        for ch in stripped:
            if ch == '"' and not in_string:
                in_string = True
            elif ch == '"' and in_string:
                in_string = False
            elif not in_string:
                if ch == '(':
                    paren_depth += 1
                elif ch == ')':
                    paren_depth = max(0, paren_depth - 1)
                elif ch == '[':
                    bracket_depth += 1
                elif ch == ']':
                    bracket_depth = max(0, bracket_depth - 1)
                elif ch == '{' and in_use:
                    brace_depth += 1
                elif ch == '}' and in_use:
                    brace_depth = max(0, brace_depth - 1)
                    if brace_depth == 0:
                        in_use = False

        # If balanced, flush
        if paren_depth == 0 and bracket_depth == 0 and not in_use and accumulator:
            result.append(accumulator)
            accumulator = ""

    if accumulator:
        result.append(accumulator)

    return "\n".join(result)


# ── Compiler pipeline ──────────────────────────────────────────────


def find_c_compiler() -> str | None:
    for cc in ("gcc", "clang", "cc"):
        if shutil.which(cc):
            return cc
    return None


def transpile(source: str, path: Path):
    """Parse + type-check + emit C.  Returns (c_source, diagnostics, uses_ui)."""
    file_path = str(path)

    # Resolve imports: concatenate library .fk files into one compilation unit
    source, uses_ui = resolve_imports(source, path)

    try:
        program = Parser.from_source(source)
    except ParseError as e:
        # Use structured location info if available, falling back to string parsing
        formatted = format_parse_error(str(e), source=source, file_path=file_path)
        return None, [formatted], uses_ui

    # Type check
    checker = TypeChecker()
    diagnostics = checker.check(program)
    diag_msgs = []
    has_errors = False
    for d in diagnostics:
        formatted = format_legacy_diagnostic(
            level=d.level,
            message=d.message,
            source=source,
            file_path=file_path,
            line=d.line,
            column=d.column,
        )
        diag_msgs.append(formatted)
        if d.level == "error":
            has_errors = True

    # Emit C even if there are warnings (but not errors)
    emitter = CEmitter()
    try:
        c_source = emitter.emit(program)
    except EmitError as e:
        formatted = format_emit_error(str(e), source=source, file_path=file_path)
        diag_msgs.append(formatted)
        return None, diag_msgs, uses_ui

    return c_source, diag_msgs, uses_ui


def compile_c(c_path: Path, out_bin: Path, runtime_dir: Path,
              opt_level: str = "0", uses_ui: bool = False) -> tuple[bool, str]:
    """Compile the generated C file. Returns (success, message)."""
    cc = find_c_compiler()
    if not cc:
        return False, "No C compiler found (gcc/clang). Install one to compile."
    cc_name = Path(cc).name.lower()

    runtime_c = runtime_dir / "freak_runtime.c"
    import sys
    cmd = [
        cc,
        "-o",
        str(out_bin),
        str(c_path),
        str(runtime_c),
        f"-I{runtime_dir}",
        f"-O{opt_level}",
        "-std=c11",
        "-w",
        "-D_CRT_SECURE_NO_WARNINGS",
    ]

    # UI runtime: add win32_backend.c + platform libs
    if uses_ui:
        ui_backend = runtime_dir / "ui" / "win32_backend.c"
        if ui_backend.exists():
            cmd.append(str(ui_backend))
            cmd.append(f"-I{runtime_dir / 'ui'}")
        if sys.platform == "win32":
            if "gcc" in cc_name:
                cmd.append("-mwindows")
            else:
                cmd.append("-Wl,/SUBSYSTEM:WINDOWS,/ENTRY:mainCRTStartup")
            cmd.extend(["-luser32", "-lgdi32"])

    # Platform-specific linker flags
    if sys.platform.startswith("linux"):
        cmd.append("-lm")
    elif sys.platform == "win32":
        cmd.append("-lws2_32")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return False, result.stderr.strip()
    return True, ""


def compile_llvm(ll_path: Path, out_bin: Path, runtime_dir: Path,
                 opt_level: str = "2", target: str = "") -> tuple[bool, str]:
    """Compile LLVM IR (.ll) to native binary via clang. Returns (success, message)."""
    cc = find_c_compiler()
    if not cc:
        return False, "No C compiler found (gcc/clang). Install one to compile."

    runtime_c = runtime_dir / "freak_llvm_runtime.c"
    if not runtime_c.exists():
        return False, f"LLVM runtime not found at {runtime_c}"

    cmd = [
        cc,
        "-o",
        str(out_bin),
        str(ll_path),
        str(runtime_c),
        f"-I{runtime_dir}",
        f"-O{opt_level}",
        "-w",
        "-D_CRT_SECURE_NO_WARNINGS",
    ]
    if target:
        cmd.extend(["--target", target])
    # Platform-specific linker flags
    if sys.platform.startswith("linux"):
        cmd.append("-lm")
    elif sys.platform == "win32":
        cmd.append("-lws2_32")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return False, result.stderr.strip()
    return True, ""


# ── Subcommands ─────────────────────────────────────────────────────


def cmd_run(path: Path, keep_c: bool = False, output: str = None,
            backend: str = "c", opt_level: str = "2", target: str = "") -> int:
    """Transpile → compile → run."""
    source = path.read_text(encoding="utf-8")
    c_source, diags, uses_ui = transpile(source, path)

    for d in diags:
        print(d, file=sys.stderr)

    if c_source is None:
        return 1

    # Write C output
    out_c = path.with_suffix(".c")
    out_c.write_text(c_source, encoding="utf-8")
    print(_dim(f"→ Wrote {out_c}"))

    # Compile
    runtime_dir = Path(__file__).parent / "runtime"
    if output:
        out_bin = Path(output)
    else:
        out_bin = (
            path.with_suffix(".exe")
            if sys.platform == "win32"
            else path.with_suffix("")
        )

    if uses_ui:
        print(_dim("→ COCKPIT detected — linking UI runtime"))
    print(_dim(f"→ Compiling ({backend} backend, -O{opt_level})..."))
    ok, err_msg = compile_c(out_c, out_bin, runtime_dir, opt_level, uses_ui=uses_ui)
    if not ok:
        print(_red("✗ Compilation failed:"), file=sys.stderr)
        print(err_msg, file=sys.stderr)
        return 1

    print(_green(f"✓ Built {out_bin}"))

    if not keep_c:
        try:
            out_c.unlink()
        except OSError:
            pass

    # Run
    print(_dim("→ Running..."))
    print("─" * 40)
    result = subprocess.run([str(out_bin)], text=True)
    print("─" * 40)

    if result.returncode != 0:
        print(_red(f"✗ Process exited with code {result.returncode}"))

    return result.returncode


def cmd_build(path: Path, keep_c: bool = False, output: str = None,
              backend: str = "c", opt_level: str = "2", target: str = "") -> int:
    """Transpile → compile (no run)."""
    source = path.read_text(encoding="utf-8")
    c_source, diags, uses_ui = transpile(source, path)

    for d in diags:
        print(d, file=sys.stderr)

    if c_source is None:
        return 1

    out_c = path.with_suffix(".c")
    out_c.write_text(c_source, encoding="utf-8")
    print(_dim(f"→ Wrote {out_c}"))

    runtime_dir = Path(__file__).parent / "runtime"
    if output:
        out_bin = Path(output)
    else:
        out_bin = (
            path.with_suffix(".exe")
            if sys.platform == "win32"
            else path.with_suffix("")
        )

    if uses_ui:
        print(_dim("→ COCKPIT detected — linking UI runtime"))
    print(_dim(f"→ Compiling ({backend} backend, -O{opt_level})..."))
    ok, err_msg = compile_c(out_c, out_bin, runtime_dir, opt_level, uses_ui=uses_ui)
    if not ok:
        print(_red("✗ Compilation failed:"), file=sys.stderr)
        print(err_msg, file=sys.stderr)
        return 1

    print(_green(f"✓ Built {out_bin}"))

    if not keep_c:
        try:
            out_c.unlink()
        except OSError:
            pass

    return 0


def cmd_check(path: Path) -> int:
    """Type-check only (no compilation)."""
    source = path.read_text(encoding="utf-8")
    _, diags, _ = transpile(source, path)

    if not diags:
        print(_green(f"✓ {path.name}: No issues found"))
        return 0

    print(f"{_bold(str(path))}:")
    has_errors = False
    for d in diags:
        print(d, file=sys.stderr)
        if "error" in d.lower() if isinstance(d, str) else False:
            has_errors = True
    return 1 if has_errors else 0


def cmd_test() -> int:
    """Run all tests/*.fk files."""
    test_dir = Path("tests")
    if not test_dir.exists():
        print(_red("✗ No tests/ directory found"))
        return 1

    fk_files = sorted(test_dir.glob("*.fk"))
    if not fk_files:
        print(_yellow("⚠ No .fk files found in tests/"))
        return 0

    passed = 0
    failed = 0

    for fk in fk_files:
        print(f"\n{_bold(fk.name)}:")
        result = cmd_run(fk, keep_c=False)
        if result == 0:
            passed += 1
        else:
            failed += 1

    print(f"\n{'─' * 40}")
    print(
        f"{_green(f'{passed} passed')}, {_red(f'{failed} failed') if failed else '0 failed'} "
        f"out of {len(fk_files)} tests"
    )
    return 1 if failed else 0


# ── Audit commands ─────────────────────────────────────────────────


def cmd_audit(sub: str, argv: list[str]) -> int:
    """Dispatch freak audit-* and freak foreshadow-audit commands."""
    from pathlib import Path as _P

    # Resolve target paths: remaining argv, or default to current dir
    raw_paths = argv if argv else ["."]
    paths = [_P(p) for p in raw_paths]

    if sub == "audit-science":
        return audit_science(paths)
    if sub == "audit-trust":
        return audit_trust(paths)
    if sub == "audit-miracles":
        return audit_miracles(paths)
    if sub == "foreshadow-audit":
        return foreshadow_audit(paths)
    if sub == "audit-conformance":
        return audit_conformance(paths)

    print(_red(f"✗ Unknown audit command: '{sub}'"), file=sys.stderr)
    return 1


def cmd_v2(path: Path, output: str = None, backend: str = "llvm",
           opt_level: str = "2", target: str = "", run_after: bool = False) -> int:
    """Use the self-hosted v2 compiler (supports LLVM + C backends)."""
    v2_exe = Path("build/freakc_v2.exe") if sys.platform == "win32" else Path("build/freakc_v2")
    if not v2_exe.exists():
        print(_red(f"✗ v2 compiler not found at {v2_exe}"), file=sys.stderr)
        print(_dim("  Build it with: bootstrap.bat (Windows) or run.sh (Linux/macOS)"))
        return 1

    # Run v2 compiler with flags
    cmd = [str(v2_exe), str(path)]
    if backend == "c":
        cmd.append("--c")
    else:
        cmd.append("--llvm")
    if opt_level != "2":
        cmd.append(f"--opt={opt_level}")
    if target:
        cmd.append(f"--target={target}")

    print(_dim(f"→ v2 compiling {path} ({backend} backend)..."))
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.stdout.strip():
        print(res.stdout.strip())
    if res.returncode != 0:
        print(_red("✗ v2 compilation failed:"), file=sys.stderr)
        if res.stderr.strip():
            print(res.stderr.strip(), file=sys.stderr)
        return 1

    # Now compile the output to a native binary
    runtime_dir = Path(__file__).parent / "runtime"
    if output:
        out_bin = Path(output)
    else:
        out_bin = (
            path.with_suffix(".exe")
            if sys.platform == "win32"
            else path.with_suffix("")
        )

    if backend == "llvm":
        ll_path = Path(str(path) + ".ll")
        if not ll_path.exists():
            print(_red(f"✗ Expected LLVM IR at {ll_path}"), file=sys.stderr)
            return 1
        print(_dim(f"→ Compiling LLVM IR (-O{opt_level})..."))
        ok, err_msg = compile_llvm(ll_path, out_bin, runtime_dir, opt_level, target)
    else:
        c_path = Path(str(path) + ".c")
        if not c_path.exists():
            print(_red(f"✗ Expected C output at {c_path}"), file=sys.stderr)
            return 1
        print(_dim(f"→ Compiling C (-O{opt_level})..."))
        ok, err_msg = compile_c(c_path, out_bin, runtime_dir, opt_level)

    if not ok:
        print(_red("✗ Compilation failed:"), file=sys.stderr)
        print(err_msg, file=sys.stderr)
        return 1

    print(_green(f"✓ Built {out_bin}"))

    if run_after:
        print(_dim("→ Running..."))
        print("─" * 40)
        result = subprocess.run([str(out_bin)], text=True)
        print("─" * 40)
        if result.returncode != 0:
            print(_red(f"✗ Process exited with code {result.returncode}"))
        return result.returncode

    return 0


def cmd_jit(path: Path) -> int:
    """Compile to LLVM IR and run directly in memory using llvmlite."""
    from .jit import run_jit

    # 1. First, transpile to get LLVM IR code
    # We want to skip C emitter and use the newly built self-hosted compiler LLVM output,
    # or we can modify Python CEmitter to emit LLVM? No, the Python transpiler emits C.
    # The self-hosted `freakc_v2.exe` emits LLVM.
    # So we should call the self-hosted compiler to get the .ll file!
    cmd = ["build/freakc_v2.exe", str(path), "--llvm"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(_red("✗ LLVM Compilation failed:"), file=sys.stderr)
        print(res.stderr.strip() or res.stdout.strip(), file=sys.stderr)
        return 1

    ll_path = Path(str(path) + ".ll")
    if not ll_path.exists():
        print(_red(f"✗ Failed to find generated IR at {ll_path}"), file=sys.stderr)
        return 1

    print(_dim("→ Executing via LLVM JIT..."))
    print("─" * 40)
    ir_code = ll_path.read_text(encoding="utf-8")
    runtime_dir = Path(__file__).parent / "runtime"

    try:
        ret = run_jit(ir_code, runtime_dir)
        print("─" * 40)
        if ret != 0:
            print(_red(f"✗ JIT process exited with code {ret}"))
        return ret
    except Exception as e:
        print("─" * 40)
        print(_red(f"✗ JIT execution crashed: {e}"), file=sys.stderr)
        return 1


# ── Main ────────────────────────────────────────────────────────────


def cmd_hangar(argv: list[str]) -> int:
    """Handle 'freak hangar <subcommand>' commands."""
    from .hangar import (
        hangar_add, hangar_init, hangar_install, hangar_remove,
        hangar_install_toolchain, hangar_version,
    )

    if not argv:
        print(_red("✗ Missing hangar subcommand. Use: init, install, add, remove, upgrade, version"))
        return 1

    sub = argv[0]
    project_dir = Path.cwd()

    if sub == "init":
        return hangar_init(project_dir)

    if sub == "install":
        # Special case: hangar install freak → toolchain bootstrap
        if len(argv) > 1 and argv[1] == "freak":
            return hangar_install_toolchain(upgrade=False)
        return hangar_install(project_dir)

    if sub == "upgrade":
        if len(argv) > 1 and argv[1] == "freak":
            return hangar_install_toolchain(upgrade=True)
        print(_red("✗ Usage: freak hangar upgrade freak"))
        return 1

    if sub == "add":
        if len(argv) < 3:
            print(_red("✗ Usage: freak hangar add <name> <owner/repo>"))
            return 1
        name = argv[1]
        repo = argv[2]
        version = argv[3] if len(argv) > 3 else "latest"
        return hangar_add(project_dir, name, repo, version)

    if sub == "remove":
        if len(argv) < 2:
            print(_red("✗ Usage: freak hangar remove <name>"))
            return 1
        return hangar_remove(project_dir, argv[1])

    if sub == "version":
        bump = argv[1] if len(argv) > 1 else ""
        return hangar_version(project_dir, bump)

    print(_red(f"✗ Unknown hangar subcommand: '{sub}'"))
    return 1


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    # Parse flags
    keep_c = "--keep-c" in argv
    argv = [a for a in argv if a != "--keep-c"]

    output = None
    if "-o" in argv:
        idx = argv.index("-o")
        if idx + 1 < len(argv):
            output = argv[idx + 1]
            argv = argv[:idx] + argv[idx + 2 :]
    if "--output" in argv:
        idx = argv.index("--output")
        if idx + 1 < len(argv):
            output = argv[idx + 1]
            argv = argv[:idx] + argv[idx + 2 :]

    # Backend selection
    backend = "llvm"  # LLVM is now the default (LB6)
    if "--c" in argv:
        backend = "c"
        argv = [a for a in argv if a != "--c"]
    if "--llvm" in argv:
        backend = "llvm"
        argv = [a for a in argv if a != "--llvm"]

    # Optimization level (LB8)
    opt_level = "2"
    filtered = []
    for a in argv:
        if a.startswith("--opt="):
            opt_level = a[6:]
        else:
            filtered.append(a)
    argv = filtered

    # Cross-compilation target (LB9)
    target = ""
    filtered = []
    for a in argv:
        if a.startswith("--target="):
            target = a[9:]
        else:
            filtered.append(a)
    argv = filtered

    if not argv:
        print("FREAK Compiler v0.8.0")
        print()
        print("Usage:")
        print("  python -m freakc run <file.fk>       Transpile + compile + run (Python transpiler)")
        print("  python -m freakc build <file.fk>     Transpile + compile (Python transpiler)")
        print("  python -m freakc v2 <file.fk>        Compile via v2 self-hosted compiler")
        print("  python -m freakc jit <file.fk>       Compile to LLVM IR and JIT execute")
        print("  python -m freakc check <file.fk>     Type check only")
        print("  python -m freakc test                Run all tests/*.fk")
        print("  python -m freakc hangar <cmd>        Package manager")
        print()
        print("Backend flags (for v2 command):")
        print("  --llvm             Use LLVM IR backend (default)")
        print("  --c                Use C backend")
        print("  --opt=N            Optimization level 0-3 (default: 2)")
        print("  --target=TRIPLE    Cross-compile target (e.g. x86_64-linux-gnu)")
        print()
        print("Other options:")
        print("  --keep-c           Keep generated .c file")
        print("  -o, --output       Output binary name")
        print()
        print("Hangar commands:")
        print("  hangar init                  Create project skeleton")
        print("  hangar install               Install all dependencies")
        print("  hangar add <name> <repo>     Add a dependency")
        print("  hangar remove <name>         Remove a dependency")
        print("  hangar install freak         Install FREAK compiler")
        print("  hangar upgrade freak         Update FREAK compiler")
        return 0

    cmd = argv[0]

    if cmd == "test":
        return cmd_test()

    if cmd == "hangar":
        return cmd_hangar(argv[1:])

    if cmd in (
        "audit-science",
        "audit-trust",
        "audit-miracles",
        "foreshadow-audit",
        "audit-conformance",
    ):
        return cmd_audit(cmd, argv[1:])

    if cmd == "v2":
        if len(argv) < 2:
            print(_red("✗ Missing file argument for 'v2'"), file=sys.stderr)
            return 1
        path = Path(argv[1])
        if not path.exists():
            print(_red(f"✗ File not found: {path}"), file=sys.stderr)
            return 1
        return cmd_v2(path, output, backend, opt_level, target, run_after=False)

    if cmd == "v2-run":
        if len(argv) < 2:
            print(_red("✗ Missing file argument for 'v2-run'"), file=sys.stderr)
            return 1
        path = Path(argv[1])
        if not path.exists():
            print(_red(f"✗ File not found: {path}"), file=sys.stderr)
            return 1
        return cmd_v2(path, output, backend, opt_level, target, run_after=True)

    if cmd in ("run", "build", "check", "jit"):
        if len(argv) < 2:
            print(_red(f"✗ Missing file argument for '{cmd}'"), file=sys.stderr)
            return 1
        path = Path(argv[1])
        if not path.exists():
            print(_red(f"✗ File not found: {path}"), file=sys.stderr)
            return 1

        if cmd == "run":
            return cmd_run(path, keep_c, output, backend, opt_level, target)
        elif cmd == "jit":
            return cmd_jit(path)
        elif cmd == "build":
            return cmd_build(path, keep_c, output, backend, opt_level, target)
        elif cmd == "check":
            return cmd_check(path)

    # Default: treat first arg as a file to run
    path = Path(cmd)
    if not path.exists():
        print(_red(f"✗ Unknown command or file: '{cmd}'"), file=sys.stderr)
        return 1
    return cmd_run(path, keep_c, output, backend, opt_level, target)


if __name__ == "__main__":
    raise SystemExit(main())
