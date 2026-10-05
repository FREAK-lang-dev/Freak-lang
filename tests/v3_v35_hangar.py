#!/usr/bin/env python3
"""Truthful Hangar failure and prior-generation preservation acceptance cases.

This first slice deliberately does not claim transactional replacement, lock v2,
package graph compilation, or archive/platform verification. Pass fresh native
binaries explicitly; Python is only an independent orchestration/oracle path.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile
from unittest import mock
from urllib.error import URLError

ANSI = re.compile(r"\x1b\[[0-9;]*m")
MANIFEST = '[project]\nname = "consumer"\nversion = "0.1.0"\n\n[dependencies]\n'
LOCK = ('# Prior verified generation\n[[package]]\nname = "existing"\n'
        'version = "1.0.0"\nsource = "owner/existing"\nsha256 = "' + 'a' * 64 + '"\n')
NATIVE_CASES = (
    "missing-add-argument", "missing-remove-argument", "unknown-command",
    "unavailable-registry-add", "unavailable-registry-install", "invalid-package-name",
    "failed-git-add", "failed-git-install", "failed-git-update", "failed-git-after-output",
    "preserved-existing-add", "preserved-existing-update", "unavailable-publication",
    "malformed-header", "unterminated-value", "duplicate-key", "duplicate-table",
    "invalid-inline-table", "unknown-manifest-escape", "unsupported-source-scheme",
    "revision-option-injection", "literal-git-metacharacters",
)


def snapshot(root: Path) -> dict[str, bytes]:
    result = {}
    for path in [root / "hangar.toml", root / "hangar.lock", root / "previous-build",
                 root / "previous-build.freak-run-cache"]:
        if path.exists():
            result[str(path.relative_to(root))] = path.read_bytes()
    modules = root / "hangar_modules" / "existing"
    if modules.exists():
        for path in sorted(modules.rglob("*")):
            if path.is_file():
                result[str(path.relative_to(root))] = path.read_bytes()
    return result


def project(root: Path, dependency: str = "") -> None:
    root.mkdir()
    (root / "hangar.toml").write_text(MANIFEST + dependency, encoding="utf-8")
    (root / "hangar.lock").write_text(LOCK, encoding="utf-8")
    package = root / "hangar_modules" / "existing"
    package.mkdir(parents=True)
    (package / "existing.fk").write_text('task value() -> int { give back 42 }\n', encoding="utf-8")
    (package / "hangar.toml").write_text('[project]\nname = "existing"\nversion = "1.0.0"\n', encoding="utf-8")
    (root / "previous-build").write_bytes(b"previous native executable\x00")
    (root / "previous-build.freak-run-cache").write_bytes(b"previous success proof\n")


def failed_git(tool_root: Path, clang: Path) -> None:
    tool_root.mkdir()
    source = tool_root / "git-failure.c"
    source.write_text(r'''#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static int put(const char *directory, const char *name, const char *data) {
    char path[4096];
    int length = snprintf(path, sizeof(path), "%s/%s", directory, name);
    if (length < 0 || (size_t)length >= sizeof(path)) return 24;
    FILE *file = fopen(path, "wb");
    if (!file) return 24;
    if (fputs(data, file) < 0 || fclose(file)) return 24;
    return 0;
}
int main(int argc, char **argv) {
    const char *report = getenv("FREAK_HANGAR_ARGV_REPORT");
    if (report) {
        FILE *file = fopen(report, "wb");
        if (!file) return 24;
        for (int i = 1; i < argc; ++i) {
            size_t length = strlen(argv[i]);
            fprintf(file, "%zu:", length); fwrite(argv[i], 1, length, file);
        }
        if (fclose(file)) return 24;
    }
    if (argc < 2) return 24;
    if (getenv("FREAK_HANGAR_WRITE_PARTIAL") || getenv("FREAK_HANGAR_FETCH_SUCCESS")) {
        if (put(argv[argc - 1], "partial.fk", "task value() -> int { give back 42 }\n")) return 24;
        if (put(".", "git-partial-proof", "wrote stage before returning\n")) return 24;
    }
    if (getenv("FREAK_HANGAR_FETCH_SUCCESS")) {
        return put(argv[argc - 1], "hangar.toml", "[project]\nname = \"missing\"\nversion = \"1.0.0\"\nkind = \"lib\"\n[modules]\ncore = \"partial.fk\"\n[exports]\napi = \"core::value\"\n");
    }
    fputs("injected Git fetch failure\n", stderr); return 23;
}
''', encoding="ascii")
    executable = tool_root / ("git.exe" if os.name == "nt" else "git")
    result = subprocess.run([str(clang), str(source), "-o", str(executable)],
                            capture_output=True, text=True, timeout=30, check=False)
    if result.returncode:
        raise AssertionError("Could not build native failure injector: " + result.stdout + result.stderr)


def native(freak: Path, hangar: Path, clang: Path, root: Path) -> None:
    tool_root = root / "tools"
    failed_git(tool_root, clang)
    env = os.environ.copy()
    env["PATH"] = str(tool_root) + os.pathsep + env.get("PATH", "")
    env["NO_COLOR"] = "1"
    cases = {
        "missing-add-argument": (["add"], "", "Usage:"),
        "missing-remove-argument": (["remove"], "", "Usage:"),
        "unknown-command": (["not-a-hangar-command"], "", "Unknown hangar command"),
        "unavailable-registry-add": (["add", "missing"], "", "Registry package sources are unavailable"),
        "unavailable-registry-install": (["install"], 'missing = "^1.0"\n', "Registry package sources are unavailable"),
        "invalid-package-name": (["add", "../escape", "owner/repository"], "", "Invalid package name"),
        "failed-git-add": (["add", "missing", "owner/repository"], "", "Could not fetch missing"),
        "failed-git-install": (["install"], 'missing = { git = "owner/repository", version = "latest" }\n', "Could not fetch missing"),
        "failed-git-update": (["update", "missing"], 'missing = { git = "owner/repository", version = "latest" }\n', "Could not fetch missing"),
        "failed-git-after-output": (["install"], 'missing = { git = "owner/repository", version = "latest" }\n', "Could not fetch missing"),
        "preserved-existing-add": (["add", "existing", "owner/repository"], "", "Cannot safely replace existing"),
        "preserved-existing-update": (["update", "existing"], 'existing = { git = "owner/repository", version = "latest" }\n', "Cannot safely replace existing"),
        "unavailable-publication": (["publish"], "", "Publication is unavailable"),
        "malformed-header": (["install"], "[dependencies\n", "Invalid manifest"),
        "unterminated-value": (["install"], 'missing = "unterminated\n', "Invalid manifest"),
        "duplicate-key": (["install"], 'missing = "1.0"\nmissing = "2.0"\n', "duplicate manifest key"),
        "duplicate-table": (["install"], "[project]\n", "duplicate table"),
        "invalid-inline-table": (["install"], 'missing = { git = "owner/repository", broken }\n', "expected key = value inside inline table"),
        "unknown-manifest-escape": (["install"], 'missing = "bad\\q"\n', "unsupported escape"),
        "unsupported-source-scheme": (["add", "missing", "ssh://example.invalid/repo"], "", "Unsupported or invalid Git package source"),
        "revision-option-injection": (["add", "missing", "owner/repository", "--upload-pack=evil"], "", "Invalid Git package revision"),
        "literal-git-metacharacters": (["add", "missing", "https://example.invalid/repo$(touch owned);&x"], "", "Could not fetch missing"),
    }
    assert tuple(cases) == NATIVE_CASES, "Failure acceptance inventory drift"
    for invocation, binary, prefix in [("freak", freak, ["hangar"]), ("standalone", hangar, [])]:
        for name, (args, dependency, diagnostic) in cases.items():
            cwd = root / f"{invocation}-{name}"
            project(cwd, dependency)
            before = snapshot(cwd)
            case_env = env.copy()
            report = cwd / "git-argv-report"
            case_env["FREAK_HANGAR_ARGV_REPORT"] = str(report)
            if name == "failed-git-after-output":
                case_env["FREAK_HANGAR_WRITE_PARTIAL"] = "1"
            completed = subprocess.run([str(binary), *prefix, *args], cwd=cwd, env=case_env,
                                       capture_output=True, text=True, encoding="utf-8",
                                       errors="replace", timeout=30, check=False)
            output = ANSI.sub("", completed.stdout + completed.stderr)
            assert completed.returncode > 0, (name, completed.returncode, output)
            assert diagnostic in output, (name, output)
            assert "INSTALLED" not in output and "PUBLISHED" not in output, (name, output)
            assert snapshot(cwd) == before, (name, "prior generation changed")
            assert not (cwd / "hangar_modules" / "missing").exists(), (name, "failed dependency materialized")
            assert not (root / "escape").exists(), (name, "package escaped project")
            assert not (cwd / "owned").exists(), (name, "shell syntax executed")
            assert not list((cwd / "hangar_modules").glob(".hangar-stage-*")), (name, "owned stage left behind")
            assert not (cwd / "hangar_modules" / ".hangar-install.lock").exists(), (name, "operation lock left behind")
            if name == "failed-git-after-output":
                assert (cwd / "git-partial-proof").read_text() == "wrote stage before returning\n"
                retry_env = env.copy()
                retry_env["FREAK_HANGAR_FETCH_SUCCESS"] = "1"
                retry = subprocess.run([str(binary), *prefix, *args], cwd=cwd, env=retry_env,
                                       capture_output=True, text=True, timeout=30, check=False)
                retry_output = ANSI.sub("", retry.stdout + retry.stderr)
                assert retry.returncode == 0 and "INSTALLED" in retry_output, retry_output
                assert (cwd / "hangar_modules" / "missing" / "partial.fk").is_file(), retry_output
                assert not list((cwd / "hangar_modules").glob(".hangar-stage-*")), retry_output
                assert not (cwd / "hangar_modules" / ".hangar-install.lock").exists(), retry_output
                print(f"native:{invocation}:failed-git-retry:passed")
            if name == "literal-git-metacharacters":
                data = report.read_bytes()
                values = []
                while data:
                    count, data = data.split(b":", 1)
                    length = int(count)
                    values.append(data[:length].decode("utf-8"))
                    data = data[length:]
                assert values[-2] == args[2], values
                assert values[-3] == "--", values
                assert "--template=" in values and "--no-recurse-submodules" in values, values
            print(f"native:{invocation}:{name}:passed")
        import tomllib
        cwd = root / f"{invocation}-manifest-round-trip"
        project(cwd)
        manifest = (MANIFEST.replace('version = "0.1.0"', 'version = "0.1.0"\nauthor = "comma, hash # and quote \\"data\\""') +
                    '[modules]\ncore = "src/core.fk"\n[exports]\napi = "core::api"\n[tool]\nenabled = true\ncount = 17\n')
        (cwd / "hangar.toml").write_text(manifest, encoding="utf-8")
        before_manifest = tomllib.loads(manifest)
        result = subprocess.run([str(binary), *prefix, "version", "patch"], cwd=cwd, env=env,
                                capture_output=True, text=True, timeout=30, check=False)
        assert result.returncode == 0, result.stdout + result.stderr
        after_manifest = tomllib.loads((cwd / "hangar.toml").read_text(encoding="utf-8"))
        before_manifest["project"]["version"] = "0.1.1"
        assert after_manifest == before_manifest, (after_manifest, before_manifest)
        print(f"native:{invocation}:manifest-round-trip:passed")


def python_compatibility(root: Path) -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from freakc import hangar as module
    for name, existing, operation in [("fetch-install", False, "install"),
                                       ("fetch-add", False, "add"),
                                       ("existing-add", True, "add")]:
        cwd = root / ("python-" + name)
        dependency = 'missing = { git = "owner/repository", version = "latest" }\n' if operation == "install" else ""
        project(cwd, dependency)
        package = "existing" if existing else "missing"
        before = snapshot(cwd)
        with mock.patch.object(module.request, "urlopen", side_effect=URLError("injected failure")), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            result = module.hangar_install(cwd) if operation == "install" else module.hangar_add(cwd, package, "owner/repository")
        assert result == 1, (name, result)
        assert snapshot(cwd) == before, (name, "prior generation changed")
        assert not (cwd / "hangar_modules" / "missing").exists(), (name, "stub created")
        print(f"python:{name}:passed")

    # The first entry extracts successfully before a real ZIP CRC mismatch in
    # the second entry. A network-only mock cannot expose a poisoned install.
    valid = io.BytesIO()
    with zipfile.ZipFile(valid, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr("repository-main/first.fk", "task value() -> int { give back 42 }\n")
        archive.writestr("repository-main/bad.fk", "unique CRC corruption payload")
        archive.writestr("repository-main/hangar.toml", '[project]\nname = "missing"\nversion = "1.0.0"\n')
    damaged = valid.getvalue().replace(b"unique CRC corruption payload", b"UNIQUE CRC corruption payload", 1)
    cwd = root / "python-partial-extraction"
    project(cwd)
    before = snapshot(cwd)
    with mock.patch.object(module.request, "urlopen", return_value=io.BytesIO(damaged)), \
            contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        result = module.hangar_add(cwd, "missing", "owner/repository")
    assert result == 1 and snapshot(cwd) == before, "partial ZIP failure changed prior generation"
    assert not (cwd / "hangar_modules" / "missing").exists(), "partial archive poisoned dependency path"
    assert not list((cwd / "hangar_modules").glob(".hangar-stage-*")), "partial ZIP stage left behind"
    with mock.patch.object(module.request, "urlopen", return_value=io.BytesIO(valid.getvalue())), \
            contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        result = module.hangar_add(cwd, "missing", "owner/repository")
    assert result == 0 and (cwd / "hangar_modules" / "missing" / "first.fk").is_file(), "valid retry failed"
    assert not list((cwd / "hangar_modules").glob(".hangar-stage-*")), "successful ZIP stage left behind"
    print("python:partial-extraction-and-retry:passed")

    cwd = root / "python-publication-collision"
    project(cwd)
    before = snapshot(cwd)
    publish = module._publish_initial_directory

    def collide(staged: Path, destination: Path) -> None:
        destination.mkdir()
        (destination / "unknown-owner").write_bytes(b"preserve concurrent content")
        publish(staged, destination)

    with mock.patch.object(module.request, "urlopen", return_value=io.BytesIO(valid.getvalue())), \
            mock.patch.object(module, "_publish_initial_directory", side_effect=collide), \
            contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        result = module.hangar_add(cwd, "missing", "owner/repository")
    assert result == 1 and snapshot(cwd) == before, "publication collision changed prior generation"
    assert (cwd / "hangar_modules" / "missing" / "unknown-owner").read_bytes() == b"preserve concurrent content"
    assert not list((cwd / "hangar_modules").glob(".hangar-stage-*")), "collision stage left behind"
    print("python:publication-collision:passed")

    if os.name != "nt":
        # A broken symlink is an existing destination even though exists() is false.
        cwd = root / "python-existing-broken-link"
        project(cwd)
        target = cwd / "hangar_modules" / "missing"
        target.symlink_to(cwd / "absent")
        with mock.patch.object(module.request, "urlopen", return_value=io.BytesIO(valid.getvalue())), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            result = module.hangar_add(cwd, "missing", "owner/repository")
        assert result == 1 and target.is_symlink(), "preexisting broken link replaced"
        print("python:existing-broken-link:passed")


GRAPH_CASES = ("diamond", "snapshot-owner", "identity-conflict", "cycle", "unresolved",
               "node-limit", "depth-limit", "edge-limit", "malformed-child")

GRAPH_PROBE = r'''
task probe_manifest(name: word, deps: word) -> word {
    pilot kind = "lib"
    pilot entry = ""
    if name == "app" { kind = "app"; entry = "entry = \"src/main.fk\"\n" }
    give back "[project]\nname = \"" + name + "\"\nversion = \"1.0.0\"\nkind = \"" + kind + "\"\n" + entry + "[modules]\ncore = \"src/core.fk\"\n[exports]\napi = \"core::api\"\n[dependencies]\n" + deps
}

task probe_diamond() -> int {
    hangar_graph_clear()
    pilot root = hangar_graph_add_manifest("root-tree", "/app/hangar.toml", probe_manifest("app", "a = { path = \"../a\" }\nb = { path = \"../b\" }\n"), "app")
    pilot a = hangar_graph_add_manifest("a-tree", "/a/hangar.toml", probe_manifest("a", "c = { path = \"../c\" }\n"), "app -> a")
    pilot b = hangar_graph_add_manifest("b-tree", "/b/hangar.toml", probe_manifest("b", "c = { path = \"../c\" }\n"), "app -> b")
    pilot c = hangar_graph_add_manifest("c-tree", "/c/hangar.toml", probe_manifest("c", ""), "app -> a -> c")
    if root != 0 or a != 1 or b != 2 or c != 3 { process::exit(11) }
    if not hangar_graph_link(0, a) or not hangar_graph_link(1, b) or not hangar_graph_link(2, c) or not hangar_graph_link(3, c) { process::exit(12) }
    give back root
}

task main() {
    pilot root = probe_diamond()
    pilot duplicate = hangar_graph_add_manifest("c-tree", "/c/hangar.toml", probe_manifest("c", ""), "app -> b -> c")
    if duplicate != 3 or hangar_graph_count != 4 or not hangar_graph_complete(root) { process::exit(13) }
    if array_len(hangar_graph_order) != 4 or array_get(hangar_graph_order, 0) != "3" or array_get(hangar_graph_order, 1) != "1" or array_get(hangar_graph_order, 2) != "2" or array_get(hangar_graph_order, 3) != "0" { process::exit(14) }
    say "graph:diamond:passed"
    if hangar_graph_fact(root, "project.name") != "app" or hangar_graph_fact(1, "dependencies.c.path") != "../c" or hangar_graph_fact(2, "exports.api") != "core::api" { process::exit(15) }
    say "graph:snapshot-owner:passed"
    pilot conflict = hangar_graph_add_manifest("other-c-tree", "/other/c/hangar.toml", probe_manifest("c", ""), "app -> b -> c")
    if conflict >= 0 or not hangar_graph_error.contains("app -> a -> c") or not hangar_graph_error.contains("app -> b -> c") { process::exit(16) }
    say "graph:identity-conflict:passed"

    hangar_graph_clear()
    root = hangar_graph_add_manifest("root-tree", "/app/hangar.toml", probe_manifest("app", "a = { path = \"../a\" }\n"), "app")
    pilot a = hangar_graph_add_manifest("a-tree", "/a/hangar.toml", probe_manifest("a", "back = { path = \"../app\" }\n"), "app -> a")
    if not hangar_graph_link(0, a) or not hangar_graph_link(1, root) { process::exit(17) }
    if hangar_graph_complete(root) or not hangar_graph_error.contains("app -> a -> back") { process::exit(18) }
    say "graph:cycle:passed"

    hangar_graph_clear()
    root = hangar_graph_add_manifest("root-tree", "/app/hangar.toml", probe_manifest("app", "missing = { path = \"../missing\" }\n"), "app")
    if hangar_graph_complete(root) or not hangar_graph_error.contains("app -> missing") { process::exit(19) }
    say "graph:unresolved:passed"

    hangar_graph_clear()
    hangar_graph_node_limit = 1
    root = hangar_graph_add_manifest("root-tree", "/app/hangar.toml", probe_manifest("app", ""), "app")
    a = hangar_graph_add_manifest("a-tree", "/a/hangar.toml", probe_manifest("a", ""), "app -> a")
    if root != 0 or a >= 0 or not hangar_graph_error.contains("node limit") { process::exit(20) }
    hangar_graph_node_limit = 1024
    say "graph:node-limit:passed"

    root = probe_diamond()
    hangar_graph_depth_limit = 1
    if hangar_graph_complete(root) or not hangar_graph_error.contains("depth limit") { process::exit(21) }
    hangar_graph_depth_limit = 64
    say "graph:depth-limit:passed"

    hangar_graph_clear()
    hangar_graph_edge_limit = 0
    root = hangar_graph_add_manifest("root-tree", "/app/hangar.toml", probe_manifest("app", "a = { path = \"../a\" }\n"), "app")
    if root >= 0 or not hangar_graph_error.contains("edge limit") { process::exit(22) }
    hangar_graph_edge_limit = 4096
    say "graph:edge-limit:passed"

    hangar_graph_clear()
    root = hangar_graph_add_manifest("bad-tree", "/a/hangar.toml", "[project\n", "app -> a")
    if root >= 0 or not hangar_graph_error.contains("/a/hangar.toml:1") { process::exit(23) }
    say "graph:malformed-child:passed"
}
'''


def task_source(source: str, name: str) -> str:
    start = source.index("task " + name + "(")
    end = source.find("\ntask ", start + 1)
    return source[start:] if end < 0 else source[start:end]


def graph_probe(freak: Path, clang: Path, runtime: Path, root: Path) -> None:
    import v3_word_foundation as foundation
    repo = Path(__file__).resolve().parents[1]
    toml = (repo / "src/cli/toml.fk").read_text(encoding="utf-8")
    # This probe exercises the parser/graph independently of filesystem adapters.
    for name in ("toml_load", "toml_write_file"):
        toml = toml.replace(task_source(toml, name), "")
    package = (repo / "src/cli/hangar.fk").read_text(encoding="utf-8")
    source = ((repo / "std/version.fk").read_text(encoding="utf-8") + "\n" + toml + "\n" +
              task_source(package, "hangar_valid_package_name") + "\n" +
              (repo / "src/cli/package_graph.fk").read_text(encoding="utf-8") + "\n" +
              GRAPH_PROBE.replace('kind = "app"; entry =', 'kind = "app"\n        entry ='))
    expected = "".join(f"graph:{case}:passed\n" for case in GRAPH_CASES)
    for backend in ("c", "llvm"):
        program = root / f"graph-{backend}.fk"
        program.write_text(source, encoding="utf-8")
        generated, _ = foundation.transpile(freak=freak, repo=repo, source=program, backend=backend)
        binary = root / (f"graph-{backend}.exe" if os.name == "nt" else f"graph-{backend}")
        foundation.compile_generated(clang=str(clang), repo=repo, runtime_root=runtime,
                                     generated=generated, backend=backend, binary=binary)
        result = foundation.run([str(binary)], root, foundation.sanitizer_env(), timeout=30)
        assert result.returncode == 0 and result.stdout == expected, (backend, result.returncode, result.stdout, result.stderr)
        if result.stderr:
            stats = foundation.parse_runtime_stats(result.stderr)
            assert len(result.stderr.splitlines()) == 1 and all(value == 0 for value in stats["counters"].values()), result.stderr
        print(f"native:{backend}:graph-probe:passed:{len(GRAPH_CASES)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freak", type=Path)
    parser.add_argument("--hangar", type=Path)
    parser.add_argument("--clang", type=Path)
    parser.add_argument("--python-only", action="store_true")
    parser.add_argument("--graph-only", action="store_true")
    parser.add_argument("--runtime-root", type=Path)
    parser.add_argument("--list", action="store_true", help="Print the expected native case inventory")
    args = parser.parse_args()
    if args.list:
        for invocation in ("freak", "standalone"):
            for case in NATIVE_CASES:
                if case == "failed-git-after-output":
                    print(f"native:{invocation}:failed-git-retry")
                print(f"native:{invocation}:{case}")
            print(f"native:{invocation}:manifest-round-trip")
        return 0
    if args.graph_only and not all((args.freak, args.clang)):
        parser.error("--graph-only requires --freak and --clang")
    if not args.python_only and not args.graph_only and not all((args.freak, args.hangar, args.clang)):
        parser.error("fresh --freak, --hangar, and native --clang paths are required")
    with tempfile.TemporaryDirectory(prefix="freak-v35-hangar-") as temporary:
        root = Path(temporary)
        if args.graph_only:
            runtime = args.runtime_root or Path(__file__).resolve().parents[1] / "freakc/runtime"
            graph_probe(args.freak.resolve(strict=True), args.clang.resolve(strict=True), runtime.resolve(strict=True), root)
            return 0
        python_compatibility(root)
        if not args.python_only:
            native(args.freak.resolve(strict=True), args.hangar.resolve(strict=True),
                   args.clang.resolve(strict=True), root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
