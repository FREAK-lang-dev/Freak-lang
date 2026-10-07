#!/usr/bin/env python3
"""Native run-cache identity for literal Clang paths and driver-selected linkers."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from windows_private_fixture import WindowsPrivateFixture

ANSI = re.compile(r"\x1b\[[0-9;]*m")
MARKER = "RAW_TOOL_EXECUTED"

# The recorder is a native image on every platform. The installed runtime
# forwards individual argv entries, including Windows Unicode paths, to the
# real compiler/linker. Neither the recorder nor the CLI uses a batch facade.
RECORDER = r'''
#include "freak_runtime.c"
#include <signal.h>
static void json_word(FILE *file, freak_word word) {
    fputc('"', file);
    for (size_t i = 0; i < word.length; ++i) {
        unsigned char ch = (unsigned char)word.data[i];
        if (ch == '"' || ch == '\\') { fputc('\\', file); fputc(ch, file); }
        else if (ch < 32) fprintf(file, "\\u%04x", ch);
        else fputc(ch, file);
    }
    fputc('"', file);
}
static FILE *open_log(freak_word name) {
#ifdef _WIN32
    int count = MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, name.data, -1, NULL, 0);
    if (!count) return NULL;
    wchar_t *wide = (wchar_t *)malloc((size_t)count * sizeof(wchar_t));
    if (!wide) return NULL;
    if (!MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, name.data, -1, wide, count)) {
        free(wide); return NULL;
    }
    FILE *file = _wfopen(wide, L"ab"); free(wide); return file;
#else
    return fopen(name.data, "ab");
#endif
}
int main(int argc, char **argv) {
    freak_argc = argc; freak_argv = argv;
    freak_word image = freak_process_executable_path();
    freak_word log = freak_process_env(freak_word_lit("FREAK_TOOL_LOG"));
    FILE *file = open_log(log); if (!file) return 92;
    fputs("{\"image\":", file); json_word(file, image); fputs(",\"argv\":[", file);
    for (int64_t i = 0; i < freak_process_args_count(); ++i) {
        if (i) fputc(',', file); json_word(file, freak_process_arg(i));
    }
    fputs("]}\n", file); if (fclose(file)) return 93;
    freak_word probe = freak_process_env(freak_word_lit("FREAK_TOOL_PROBE_EXECUTABLE"));
    if (probe.length) {
        int64_t command = freak_process_command_new(probe);
        freak_process_command_arg(command, freak_word_lit("--version"));
        freak_process_command_env(command, freak_word_lit("FREAK_TOOL_PROBE_EXECUTABLE"), freak_word_lit(""));
        int64_t state = freak_process_command_run_inherit(command, 0);
        int code = state == 2 ? (int)freak_process_command_exit_code(command) : 94;
        freak_process_command_release(command); return code;
    }
    const char *leaf = image.data;
    for (const char *p = image.data; *p; ++p) if (*p == '/' || *p == '\\') leaf = p + 1;
    freak_word linker_name = freak_process_env(freak_word_lit("FREAK_TOOL_LINKER_NAME"));
    bool linker = !strcmp(leaf, linker_name.data);
    freak_word first = freak_process_arg(1);
    bool version = !strcmp(first.data, "--version");
    freak_word mode = freak_process_env(freak_word_lit(linker ? "FREAK_TOOL_LINKER_VERSION" : "FREAK_TOOL_CLANG_VERSION"));
    if (version && !strcmp(mode.data, "empty")) return 91;
    if (version && !strcmp(mode.data, "invalid")) { fputc(255, stdout); return 0; }
    if (version && !strcmp(mode.data, "nul")) { fwrite("bad\0version", 1, 11, stdout); return 0; }
    if (version && !strcmp(mode.data, "signal")) { raise(SIGTERM); return 91; }
    if (version && !strcmp(mode.data, "stderr")) { fputs("native linker diagnostic\n", stderr); return 64; }
    if (version && !strcmp(mode.data, "both")) {
        fputs("native linker stdout version\n", stdout); fputs("native linker stderr diagnostic\n", stderr); return 64;
    }
    freak_word trace_mode = freak_process_env(freak_word_lit("FREAK_TOOL_TRACE_MODE"));
    if (!linker && !strcmp(first.data, "-###") && trace_mode.length) {
        freak_word trace = freak_process_env(freak_word_lit("FREAK_TOOL_TRACE"));
        fwrite(trace.data, 1, trace.length, stderr); return 0;
    }
    freak_word real = freak_process_env(freak_word_lit(linker ? "FREAK_TOOL_REAL_LINKER" : "FREAK_TOOL_REAL_CLANG"));
    int64_t command = freak_process_command_new(real);
    for (int64_t i = 1; i < freak_process_args_count(); ++i)
        freak_process_command_arg(command, freak_process_arg(i));
    if (!linker && !version && strcmp(first.data, "-dumpmachine")) {
        freak_word flag = freak_process_env(freak_word_lit("FREAK_TOOL_LINKER_FLAG"));
        if (flag.length) freak_process_command_arg(command, flag);
        flag = freak_process_env(freak_word_lit("FREAK_TOOL_LINKER_FLAG2"));
        if (flag.length) freak_process_command_arg(command, flag);
    }
    int64_t state = freak_process_command_run_inherit(command, 0);
    int code = state == 2 ? (int)freak_process_command_exit_code(command) : 94;
    freak_process_command_release(command);
    if (version && !strcmp(mode.data, "nonzero")) return 91;
    return code;
}
'''


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def linker_from_trace(text: str) -> Path:
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith('"'):
            continue
        token, end = json.JSONDecoder().raw_decode(line)
        if not isinstance(token, str) or (end < len(line) and not line[end].isspace()):
            continue
        leaf = Path(token).name.lower()
        if leaf in {"ld", "ld.exe", "ld.lld", "ld.lld.exe", "lld-link", "lld-link.exe", "link.exe", "ld64", "ld.bfd", "ld.gold"} or leaf.endswith(("-ld", "-ld.exe")):
            result = Path(token)
            if sys.platform == "win32" and not result.exists():
                result = Path(token + ".exe")
            assert result.is_file(), (result, text)
            return result.absolute()
    raise AssertionError(text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freak", type=Path)
    parser.add_argument("--clang", type=Path)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    freak = (args.freak or repo / "build" / ("freak.exe" if os.name == "nt" else "freak")).resolve()
    report: dict = {"schema": "freak.run-tool-identity.v1", "commands": [], "witnesses": [],
                    "fixture_sha256": sha(Path(__file__)),
                    "recorder_source_sha256": hashlib.sha256(RECORDER.encode()).hexdigest()}

    def run(argv: list[str], cwd: Path, env: dict[str, str], *, timeout: int = 120) -> tuple[int, str]:
        result = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, timeout=timeout, check=False)
        report["commands"].append({"argv": argv, "cwd": str(cwd), "returncode": result.returncode,
                                   "identity_environment": {key: value for key, value in env.items() if key in {"FREAK_CLANG", "FREAK_HOME", "PATH"} or key.startswith("FREAK_TOOL_")},
                                   "stdout_hex": result.stdout.hex(), "stderr_hex": result.stderr.hex()})
        if env.get("FREAK_TOOL_LOG") and Path(env["FREAK_TOOL_LOG"]).is_file():
            report["native_tool_entries"] = [json.loads(line) for line in Path(env["FREAK_TOOL_LOG"]).read_text(encoding="utf-8").splitlines()]
        return result.returncode, ANSI.sub("", (result.stdout + result.stderr).decode("utf-8", "replace"))

    try:
        assert freak.is_file(), freak
        base_env = os.environ.copy()
        clang = str(args.clang) if args.clang else base_env.get("FREAK_CLANG", "")
        if not clang:
            code, output = run([str(freak), "doctor", "--json"], repo, base_env)
            assert code == 0, output
            clang = json.loads(output)["checks"]["clang"]["executable"]
        if len(clang) >= 2 and clang.startswith('"') and clang.endswith('"'):
            clang = clang[1:-1]  # Exactly the selector's legacy outer-pair contract.
        real_clang = Path(shutil.which(clang) or clang).absolute()
        assert real_clang.is_file(), real_clang
        report["freak"] = {"path": str(freak), "sha256": sha(freak)}
        report["clang"] = {"path": str(real_clang), "sha256": sha(real_clang)}
        with tempfile.TemporaryDirectory(prefix="freak-run-tool-identity-") as temporary:
            root = Path(temporary).resolve()
            private = WindowsPrivateFixture(root)
            install = root / "install"
            created: set[Path] = set()
            for row in (repo / "packaging" / "distribution-files.manifest").read_text(encoding="utf-8").splitlines():
                if not row or row.startswith("#"):
                    continue
                original, relative = row.split("|", 1)
                destination = install / relative
                parent = destination.parent
                while parent != root:
                    created.add(parent)
                    parent = parent.parent
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(repo / original, destination)
            private.claim_fresh_directories(*sorted(created))
            report["installed_inputs"] = {path.relative_to(install).as_posix(): sha(path) for path in install.rglob("*") if path.is_file()}
            env = base_env.copy()
            env["FREAK_HOME"] = str(install)
            source_dir = root / "source"
            source_dir.mkdir()
            private.claim_fresh_directories(source_dir)
            source = source_dir / "literal.fk"
            source.write_text(f'task main() {{\n    say "{MARKER}"\n}}\n', encoding="utf-8")
            binary = source.with_suffix(".exe" if os.name == "nt" else "")
            cache = Path(str(binary) + ".freak-run-cache")
            recorder_source = root / "recorder.c"
            recorder_source.write_text(RECORDER, encoding="utf-8")
            recorder = root / ("recorder.exe" if os.name == "nt" else "recorder")
            code, output = run([str(real_clang), "-O2", "-D_CRT_SECURE_NO_WARNINGS", str(recorder_source), "-I", str(install / "runtime"), "-o", str(recorder), "-lws2_32" if os.name == "nt" else "-lm"], root, env)
            assert code == 0 and recorder.is_file(), output
            report["recorder"] = {"path": str(recorder), "sha256": sha(recorder)}
            code, output = run([str(real_clang), "-###", "-x", "c", os.devnull, "-o", os.devnull], root, env)
            assert code == 0, output
            real_linker = linker_from_trace(output)
            report["linker"] = {"path": str(real_linker), "sha256": sha(real_linker)}
            names = ["plain", "spaces in path", "apostrophe'path", "日本語", "dollar$percent%"]
            if os.name != "nt":
                names.append('literal"quote\\path')
            wrappers: list[Path] = []
            for name in names:
                directory = root / name
                directory.mkdir()
                private.claim_fresh_directories(directory)
                wrapper = directory / ("tool-clang.exe" if os.name == "nt" else "tool-clang")
                shutil.copy2(recorder, wrapper)
                wrappers.append(wrapper)
            linker_dir = root / "linker space'apostrophe日本語$%"
            linker_dir.mkdir()
            private.claim_fresh_directories(linker_dir)
            linker = linker_dir / real_linker.name
            shutil.copy2(recorder, linker)
            env.update(FREAK_TOOL_LOG=str(root / "tool-log.jsonl"), FREAK_TOOL_REAL_CLANG=str(real_clang),
                       FREAK_TOOL_REAL_LINKER=str(real_linker), FREAK_TOOL_LINKER_NAME=real_linker.name,
                       FREAK_TOOL_LINKER_VERSION="stderr")
            if os.name == "nt" and real_linker.name.lower() in {"link.exe", "lld-link.exe"}:
                env["FREAK_TOOL_LINKER_FLAG"] = "-B" + str(linker_dir)
                env["FREAK_TOOL_LINKER_FLAG2"] = "-fuse-ld=" + ("link.exe" if real_linker.name.lower() == "link.exe" else "lld-link")
            else:
                env["FREAK_TOOL_LINKER_FLAG"] = "--ld-path=" + str(linker)

            def invoke(backend: str, *, hit: bool | None, supplied: dict[str, str] | None = None) -> None:
                active = supplied or env
                before = (binary.read_bytes(), cache.read_bytes()) if hit is None else None
                code, output = run([str(freak), "run", source.name, backend], source_dir, active)
                if hit is None:
                    assert code != 0 and MARKER not in output and "run cache hit" not in output, output
                    assert (binary.read_bytes(), cache.read_bytes()) == before, output
                else:
                    assert code == 0 and MARKER in output, output
                    assert ("run cache hit" in output) is hit, output
                report["witnesses"].append({"backend": backend, "clang": active.get("FREAK_CLANG"), "cache_hit": hit,
                                            "controls": {key: value for key, value in active.items() if key.startswith("FREAK_TOOL_")},
                                            "path": active.get("PATH"), "binary_sha256": sha(binary), "cache_sha256": sha(cache)})

            for wrapper in wrappers:
                env["FREAK_CLANG"] = str(wrapper)
                invoke("--c", hit=False)
                invoke("--c", hit=True)
            # Compare bare-name admission with the same installed native argv
            # runtime. Windows explicit application-name search differs from
            # POSIX; an unsupported PATH-only name must fail closed.
            decoy = source_dir / wrappers[0].name
            env["PATH"] = str(wrappers[0].parent) + os.pathsep + base_env.get("PATH", os.defpath)
            env["FREAK_CLANG"] = wrappers[0].name
            if os.name != "nt":
                decoy.write_bytes(b"cwd decoy must never be hashed or executed\n")
            code, output = run([str(recorder)], source_dir, env | {"FREAK_TOOL_PROBE_EXECUTABLE": wrappers[0].name})
            report["bare_path_native_status"] = code
            if os.name != "nt":
                assert code == 0, output
            if code == 0:
                invoke("--c", hit=False)
                invoke("--c", hit=True)
                if os.name != "nt":
                    decoy.write_bytes(b"changed cwd decoy\n")
                    invoke("--c", hit=True)
                wrappers[0].write_bytes(wrappers[0].read_bytes() + b"\ncompiler generation 2\n")
                invoke("--c", hit=False)
                invoke("--c", hit=True)
            else:
                invoke("--c", hit=None)
            if os.name == "nt":
                shutil.copy2(recorder, decoy)
                invoke("--c", hit=False)
                invoke("--c", hit=True)
            else:
                # PATH order must select the same image for hashing and argv.
                alternate_dir = root / "alternate PATH"
                alternate_dir.mkdir()
                private.claim_fresh_directories(alternate_dir)
                alternate = alternate_dir / wrappers[0].name
                shutil.copy2(recorder, alternate)
                alternate.write_bytes(alternate.read_bytes() + b"\nalternate compiler bytes\n")
                ordered = env | {"PATH": str(alternate_dir) + os.pathsep + env["PATH"]}
                invoke("--c", hit=False, supplied=ordered)
                invoke("--c", hit=True, supplied=ordered)
                invoke("--c", hit=False)
                # Empty PATH selects the actual cwd executable. Make only the
                # existing platform hash utility reachable there as well.
                shutil.copy2(recorder, decoy)
                for utility in ("sha256sum", "shasum"):
                    actual = shutil.which(utility)
                    if actual:
                        (source_dir / utility).symlink_to(actual)
                empty_path = env | {"PATH": ""}
                invoke("--c", hit=False, supplied=empty_path)
                invoke("--c", hit=True, supplied=empty_path)
                unset_path = empty_path.copy()
                del unset_path["PATH"]
                invoke("--c", hit=None, supplied=unset_path)
                invoke("--c", hit=True, supplied=empty_path)
                decoy.unlink()
            env["FREAK_CLANG"] = str(wrappers[-1])
            invoke("--llvm", hit=False)
            invoke("--llvm", hit=True)
            for backend in ("--c", "--llvm"):
                invoke(backend, hit=False)
                invoke(backend, hit=True)
                wrappers[-1].write_bytes(wrappers[-1].read_bytes() + b"\ncompiler generation 3\n")
                invoke(backend, hit=False)
                invoke(backend, hit=True)
                linker.write_bytes(linker.read_bytes() + b"\nlinker generation 2\n")
                invoke(backend, hit=False)
                invoke(backend, hit=True)
                for mode in ("nonzero", "empty", "invalid", "nul", "signal"):
                    bad = env | {"FREAK_TOOL_CLANG_VERSION": mode}
                    invoke(backend, hit=None, supplied=bad)
                invoke(backend, hit=None, supplied=env | {"FREAK_CLANG": str(root / "missing-clang")})
                for trace in ('"' + str(linker) + '"suffix\n', '"' + str(linker) + '\\q"\n', '"' + str(linker), ""):
                    invoke(backend, hit=None, supplied=env | {"FREAK_TOOL_TRACE_MODE": "override", "FREAK_TOOL_TRACE": trace})
                held = linker.read_bytes()
                linker.unlink()
                invoke(backend, hit=None)
                linker.write_bytes(held)
                linker.chmod(0o755)
                invoke(backend, hit=True)
            entries = [json.loads(line) for line in Path(env["FREAK_TOOL_LOG"]).read_text(encoding="utf-8").splitlines()]
            for wrapper in wrappers:
                assert any(Path(entry["image"]).samefile(wrapper) for entry in entries), wrapper
            assert any(Path(entry["image"]).samefile(linker) and entry["argv"][1:] == ["--version"] for entry in entries)
            assert any(Path(entry["image"]).samefile(linker) and entry["argv"][1:] != ["--version"] for entry in entries)
            report["native_tool_entries"] = entries
            report["private_setup"] = private.report
        report["status"] = "pass"
        print("run tool identity: literal paths, selected linker, replacement and fail-closed cache checks passed")
        return 0
    except BaseException as error:
        report["status"] = "fail"
        report["error"] = repr(error)
        raise
    finally:
        if args.json:
            args.json.parent.mkdir(parents=True, exist_ok=True)
            args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
