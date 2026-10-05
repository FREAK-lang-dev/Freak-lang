#!/usr/bin/env python3
"""Truthful Hangar failure and prior-generation preservation acceptance cases.

This first slice deliberately does not claim transactional replacement, lock v2,
package graph compilation, or archive/platform verification. Pass fresh native
binaries explicitly; Python is only an independent orchestration/oracle path.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import os
from pathlib import Path
import re
import subprocess
import struct
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
    "failed-git-add", "failed-git-install", "failed-git-update", "failed-git-after-output", "failed-git-binary-diagnostic",
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
    fputs("injected Git fetch failure\n", stderr);
    if (getenv("FREAK_HANGAR_BINARY_DIAGNOSTIC")) {
        const unsigned char bytes[] = {'A', 0, 0xff, 'B'};
        fwrite(bytes, 1, sizeof(bytes), stderr);
    }
    return 23;
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
    env["FREAK_GIT"] = str(tool_root / ("git.exe" if os.name == "nt" else "git"))
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
        "failed-git-binary-diagnostic": (["install"], 'missing = { git = "owner/repository", version = "latest" }\n', "Could not fetch missing"),
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
            if name in ("failed-git-after-output", "failed-git-binary-diagnostic"):
                case_env["FREAK_HANGAR_WRITE_PARTIAL"] = "1"
            if name == "failed-git-binary-diagnostic":
                case_env["FREAK_HANGAR_BINARY_DIAGNOSTIC"] = "1"
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
            marker = cwd / "hangar_modules" / ".hangar-operations" / "install.lock"
            if marker.exists():
                assert marker.is_file() and not marker.is_symlink(), (name, "operation lock marker is unsafe")
                if os.name != "nt":
                    assert marker.stat().st_mode & 0o777 == 0o600, (name, "operation lock marker is not private")
                    assert marker.parent.stat().st_mode & 0o777 == 0o700, (name, "operation lock parent is not private")
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
                # A successful retry proves that the persistent marker is not
                # mistaken for active ownership of the held operating-system lock.
                assert (cwd / "hangar_modules" / ".hangar-operations" / "install.lock").is_file(), retry_output
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


def require_resource_conservation(foundation, stderr: str) -> None:
    if not stderr:
        return
    stats = foundation.parse_runtime_stats(stderr)
    assert len(stderr.splitlines()) == 1, stderr
    counters = stats["counters"]
    assert counters["byte_buffer_creations"] == counters["byte_buffer_releases"], stats
    assert counters["word_builder_creations"] == counters["word_builder_finishes"] + counters["word_builder_discards"], stats


def probe_transpile(foundation, freak: Path | None, compiler: Path | None, repo: Path,
                    source: Path, backend: str) -> Path:
    if compiler is None:
        assert freak is not None
        generated, _ = foundation.transpile(freak=freak, repo=repo, source=source, backend=backend)
        return generated
    flag = "--c" if backend == "c" else "--llvm"
    result = foundation.run([str(compiler), str(source), flag], repo)
    assert result.returncode == 0, result.stdout + result.stderr
    generated = Path(str(source) + (".c" if backend == "c" else ".ll"))
    assert generated.is_file(), result.stdout + result.stderr
    return generated


def graph_probe(freak: Path | None, clang: Path, runtime: Path, root: Path,
                compiler: Path | None = None) -> None:
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
        generated = probe_transpile(foundation, freak, compiler, repo, program, backend)
        binary = root / (f"graph-{backend}.exe" if os.name == "nt" else f"graph-{backend}")
        foundation.compile_generated(clang=str(clang), repo=repo, runtime_root=runtime,
                                     generated=generated, backend=backend, binary=binary)
        result = foundation.run([str(binary)], root, foundation.sanitizer_env(), timeout=30)
        assert result.returncode == 0 and result.stdout == expected, (backend, result.returncode, result.stdout, result.stderr)
        require_resource_conservation(foundation, result.stderr)
        print(f"native:{backend}:graph-probe:passed:{len(GRAPH_CASES)}")


INPUT_CASES = ("canonical-bytes", "sorted-inventory", "binary-stage", "unknown-ignored",
               "metadata-ignored", "declared-edit", "symlink-component", "secret-declaration", "protected-aliases", "case-collision", "byte-limit", "manifest-race")
INPUT_MANIFEST = ('[project]\nname = "inputs"\nversion = "1.0.0"\nkind = "lib"\n'
                  'readme = "README.md"\nlicense_file = "LICENSE"\n'
                  '[modules]\ncore = "src/é helper.fk"\n'
                  '[tests]\nmain = "tests/sample.fk"\n[assets]\nbinary = "assets/raw.bin"\n')
INPUT_PROGRAM = r'''
task main() {
    pilot root = process::arg(1)
    pilot stage = process::arg(2)
    hangar_graph_clear()
    package_inputs_clear()
    pilot manifest = fs::read_ticket(root + "/hangar.toml")
    if not fs::result_ok(manifest) { process::exit(51) }
    pilot content = fs::result_word(manifest)
    fs::result_release(manifest)
    pilot node = hangar_graph_add_manifest("input-tree", root + "/hangar.toml", content, "inputs")
    if node < 0 { process::exit(52) }
    if process::arg(3) == "limit" { package_input_file_limit = 1 }
    if process::arg(3) == "manifest-race" {
        pilot written = fs::write_checked(root + "/hangar.toml", content.replace("src/é helper.fk", "missing-late.fk"))
        if not fs::result_ok(written) { process::exit(53) }
        fs::result_release(written)
    }
    pilot hash = package_hash_declared_inputs(node, root, "hangar.toml", stage)
    if hash == "" { say "error:" + hangar_graph_error } else {
        say hash
        pilot index = 0
        repeat until index >= array_len(package_input_paths) {
            say array_get(package_input_paths, index) + "|" + array_get(package_input_hashes, index) + "|" + array_get(package_input_lengths, index) + "|" + array_get(package_input_roles, index)
            index += 1
        }
    }
    package_inputs_release()
    hangar_graph_release()
    toml_release()
}
'''


def inputs_probe(freak: Path | None, clang: Path, runtime: Path, root: Path,
                 compiler: Path | None = None) -> None:
    import v3_word_foundation as foundation
    repo = Path(__file__).resolve().parents[1]
    package = (repo / "src/cli/hangar.fk").read_text(encoding="utf-8")
    toml = (repo / "src/cli/toml.fk").read_text(encoding="utf-8")
    # The direct compiler has no implicit std/runtime wrapper injection. This
    # probe reads through checked tickets; unrelated legacy adapters are omitted.
    for name in ("toml_load", "toml_write_file"):
        toml = toml.replace(task_source(toml, name), "")
    source = ((repo / "std/version.fk").read_text(encoding="utf-8") + "\n" +
              toml + "\n" +
              task_source(package, "hangar_valid_package_name") + "\n" +
              "\n".join((repo / ("src/cli/" + name + ".fk")).read_text(encoding="utf-8")
                        for name in ("package_graph", "package_paths", "package_inputs")) + "\n" + INPUT_PROGRAM)
    files = {"hangar.toml": (INPUT_MANIFEST.encode("utf-8"), "manifest"),
             "src/é helper.fk": (b"task value() -> int { give back 42 }\n", "source"),
             "tests/sample.fk": (b"task main() { say 42 }\n", "test"),
             "assets/raw.bin": (b"A\0\xffB\r\n", "asset"), "README.md": (b"# Example\n", "documentation"),
             "LICENSE": (b"Example license\n", "documentation")}

    def create(cwd: Path, manifest: str = INPUT_MANIFEST) -> None:
        cwd.mkdir()
        for relative, (contents, _) in files.items():
            target = cwd / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(contents)
        (cwd / "hangar.toml").write_text(manifest, encoding="utf-8")

    def expected(cwd: Path) -> str:
        ordered = sorted(files, key=lambda path: path.encode("utf-8"))
        data = b"FREAK-source-input-tree-v2\n" + struct.pack(">q", len(ordered))
        lines = []
        for relative in ordered:
            name = relative.encode("utf-8")
            contents = (cwd / relative).read_bytes()
            data += struct.pack(">q", len(name)) + name + struct.pack(">qqq", 1, 0, len(contents)) + contents
            lines.append(f"{relative}|{hashlib.sha256(contents).hexdigest()}|{len(contents)}|{files[relative][1]}\n")
        return hashlib.sha256(data).hexdigest() + "\n" + "".join(lines)

    for backend in ("c", "llvm"):
        program = root / f"inputs-{backend}.fk"
        program.write_text(source, encoding="utf-8")
        generated = probe_transpile(foundation, freak, compiler, repo, program, backend)
        binary = root / (f"inputs-{backend}.exe" if os.name == "nt" else f"inputs-{backend}")
        foundation.compile_generated(clang=str(clang), repo=repo, runtime_root=runtime,
                                     generated=generated, backend=backend, binary=binary)

        def execute(cwd: Path, name: str, mode: str = "normal") -> tuple[str, Path]:
            stage = root / f"stage-{backend}-{name}"
            stage.mkdir()
            result = foundation.run([str(binary), str(cwd), str(stage), mode], root,
                                    foundation.sanitizer_env(), timeout=30)
            assert result.returncode == 0, (backend, name, result.returncode, result.stdout, result.stderr)
            require_resource_conservation(foundation, result.stderr)
            return result.stdout, stage

        cwd = root / f"input-project-{backend}"
        create(cwd)
        output, stage = execute(cwd, "initial")
        assert output == expected(cwd), (backend, output, expected(cwd))
        print(f"native:{backend}:inputs:canonical-bytes:passed")
        print(f"native:{backend}:inputs:sorted-inventory:passed")
        assert {(path.relative_to(stage).as_posix(), path.read_bytes()) for path in stage.rglob("*") if path.is_file()} == {(path, data) for path, (data, _) in files.items()}
        print(f"native:{backend}:inputs:binary-stage:passed")
        (cwd / "unknown-secret").write_bytes(b"never admit unknown content")
        again, _ = execute(cwd, "unknown")
        assert again == output, again
        print(f"native:{backend}:inputs:unknown-ignored:passed")
        changed = cwd / "src/é helper.fk"
        os.utime(changed, (1730000000, 1730000000))
        if os.name != "nt":
            changed.chmod(0o755)
        again, _ = execute(cwd, "metadata")
        assert again == output, again
        print(f"native:{backend}:inputs:metadata-ignored:passed")
        changed.write_bytes(b"task value() -> int { give back 43 }\n")
        again, _ = execute(cwd, "edit")
        assert again == expected(cwd) and again.splitlines()[0] != output.splitlines()[0], again
        print(f"native:{backend}:inputs:declared-edit:passed")
        if os.name != "nt":
            linked = root / f"input-linked-{backend}"
            create(linked)
            linked_source = linked / "src/é helper.fk"
            linked_source.unlink()
            (linked / "src").rmdir()
            (linked / "src").symlink_to(cwd / "src", target_is_directory=True)
            rejected, _ = execute(linked, "symlink")
            assert rejected.startswith("error:") and "symlink" in rejected, rejected
            print(f"native:{backend}:inputs:symlink-component:passed")
        else:
            raise AssertionError("native Windows symlink fixture requires an admitted reparse-point fixture")
        secret = root / f"input-secret-{backend}"
        create(secret, INPUT_MANIFEST.replace('binary = "assets/raw.bin"', 'binary = ".env"'))
        (secret / ".env").write_text("secret=forbidden", encoding="ascii")
        rejected, _ = execute(secret, "secret")
        assert rejected.startswith("error:") and "secret/cache/generated" in rejected, rejected
        print(f"native:{backend}:inputs:secret-declaration:passed")
        for index, alias in enumerate((".ENV", ".env.", ".GIT/config", "assets/raw.bin ")):
            aliased = root / f"input-secret-alias-{backend}-{index}"
            create(aliased, INPUT_MANIFEST.replace('binary = "assets/raw.bin"', f'binary = "{alias}"'))
            rejected, _ = execute(aliased, f"alias-{index}")
            assert rejected.startswith("error:") and "secret/cache/generated" in rejected, rejected
        print(f"native:{backend}:inputs:protected-aliases:passed")
        collision = root / f"input-case-collision-{backend}"
        create(collision, INPUT_MANIFEST + 'duplicate = "assets/RAW.bin"\n')
        rejected, _ = execute(collision, "case-collision")
        assert rejected.startswith("error:") and "case-insensitive" in rejected, rejected
        print(f"native:{backend}:inputs:case-collision:passed")
        rejected, _ = execute(cwd, "limit", "limit")
        assert rejected.startswith("error:") and "byte limit" in rejected, rejected
        print(f"native:{backend}:inputs:byte-limit:passed")
        changed_manifest = root / f"input-manifest-race-{backend}"
        create(changed_manifest)
        rejected, _ = execute(changed_manifest, "manifest-race", "manifest-race")
        assert rejected.startswith("error:") and "manifest changed after graph admission" in rejected, rejected
        print(f"native:{backend}:inputs:manifest-race:passed")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freak", type=Path)
    parser.add_argument("--compiler", type=Path, help="Fresh direct native compiler for isolated probes")
    parser.add_argument("--hangar", type=Path)
    parser.add_argument("--clang", type=Path)
    parser.add_argument("--python-only", action="store_true")
    parser.add_argument("--graph-only", action="store_true")
    parser.add_argument("--inputs-only", action="store_true")
    parser.add_argument("--runtime-root", type=Path)
    parser.add_argument("--probe-root", type=Path, help="Retain probe files in a new task-owned evidence directory")
    parser.add_argument("--list", action="store_true", help="Print the expected native case inventory")
    args = parser.parse_args()
    if args.list:
        if args.inputs_only:
            for backend in ("c", "llvm"):
                for case in INPUT_CASES:
                    print(f"native:{backend}:inputs:{case}")
            return 0
        if args.graph_only:
            for backend in ("c", "llvm"):
                for case in GRAPH_CASES:
                    print(f"native:{backend}:graph:{case}")
            return 0
        for invocation in ("freak", "standalone"):
            for case in NATIVE_CASES:
                if case == "failed-git-after-output":
                    print(f"native:{invocation}:failed-git-retry")
                print(f"native:{invocation}:{case}")
            print(f"native:{invocation}:manifest-round-trip")
        return 0
    if args.graph_only and not ((args.freak or args.compiler) and args.clang):
        parser.error("--graph-only requires --freak or --compiler, and --clang")
    if args.inputs_only and not ((args.freak or args.compiler) and args.clang):
        parser.error("--inputs-only requires --freak or --compiler, and --clang")
    if not args.python_only and not args.graph_only and not args.inputs_only and not all((args.freak, args.hangar, args.clang)):
        parser.error("fresh --freak, --hangar, and native --clang paths are required")
    if args.probe_root:
        args.probe_root.mkdir(parents=True, exist_ok=False)
    context = contextlib.nullcontext(str(args.probe_root.resolve())) if args.probe_root else tempfile.TemporaryDirectory(prefix="freak-v35-hangar-")
    with context as temporary:
        root = Path(temporary)
        if args.graph_only:
            runtime = args.runtime_root or Path(__file__).resolve().parents[1] / "freakc/runtime"
            graph_probe(args.freak.resolve(strict=True) if args.freak else None, args.clang.resolve(strict=True),
                        runtime.resolve(strict=True), root, args.compiler.resolve(strict=True) if args.compiler else None)
            return 0
        if args.inputs_only:
            runtime = args.runtime_root or Path(__file__).resolve().parents[1] / "freakc/runtime"
            inputs_probe(args.freak.resolve(strict=True) if args.freak else None, args.clang.resolve(strict=True),
                         runtime.resolve(strict=True), root, args.compiler.resolve(strict=True) if args.compiler else None)
            return 0
        python_compatibility(root)
        if not args.python_only:
            native(args.freak.resolve(strict=True), args.hangar.resolve(strict=True),
                   args.clang.resolve(strict=True), root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
