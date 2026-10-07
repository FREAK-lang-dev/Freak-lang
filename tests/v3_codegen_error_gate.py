#!/usr/bin/env python3
"""Executable regression checks for the V3 diagnostic/codegen gate."""

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
from dataclasses import dataclass
from pathlib import Path

from windows_private_fixture import WindowsPrivateFixture


SENTINEL = "stale output from an older successful invocation\n"
NEGATIVE_CORPUS_SCHEMA = "freak-v3-negative-corpus-v1"


def derived_binary(source: Path) -> Path:
    """Derive the platform-specific executable path for a source file.

    Parameters:
        source (Path): The source file path.

    Returns:
        Path: The source path with an executable suffix on Windows and no suffix elsewhere.
    """
    return source.with_suffix(".exe" if sys.platform == "win32" else "")


def run_cache(binary: Path) -> Path:
    """Derive the cache path associated with an executable.

    Parameters:
        binary (Path): Path to the executable.

    Returns:
        Path to the executable's run cache.
    """
    return Path(str(binary) + ".freak-run-cache")


def seed_stale_outputs(*paths: Path) -> None:
    """Create stale output files containing the test sentinel value.

    Parameters:
        paths (Path): Output paths to seed; duplicate paths are written once.
    """
    for path in dict.fromkeys(paths):
        path.write_text(SENTINEL, encoding="utf-8")


def assert_outputs_absent(paths: tuple[Path, ...], label: str) -> None:
    """
    Assert that none of the specified output paths exist.

    Parameters:
        paths (tuple[Path, ...]): Output paths to verify.
        label (str): Label included in the failure message.
    """
    leftovers = [path for path in dict.fromkeys(paths) if path.exists()]
    assert not leftovers, f"{label}: stale output survived: {leftovers}"


def assert_outputs_preserved(paths: tuple[Path, ...], label: str) -> None:
    """
    Assert that each specified output retains the sentinel content.

    Parameters:
        paths (tuple[Path, ...]): Output paths to verify.
        label (str): Context included in the assertion message.
    """
    for path in dict.fromkeys(paths):
        assert path.read_text(encoding="utf-8") == SENTINEL, (
            f"{label}: non-emitting check changed {path}"
        )


def assert_unreadable_diagnostic(output: str, label: str) -> None:
    """
    Verify that command output contains an accepted unreadable-input diagnostic.

    Parameters:
        output (str): Command output to inspect.
        label (str): Label identifying the command or test case.
    """
    lowered = output.lower()
    accepted = (
        "could not read file",
        "could not read source file",
        "cannot open file",
    )
    assert any(message in lowered for message in accepted), (
        f"{label}: missing unreadable-input diagnostic\n{output}"
    )


@dataclass(frozen=True)
class NegativeCase:
    name: str
    kind: str
    source: Path
    diagnostic: str
    flags: tuple[str, ...]
    direct: bool
    public_cli: bool


def load_negative_corpus(repo: Path) -> list[NegativeCase]:
    """
    Load and validate the V3 negative-test corpus manifest.

    Parameters:
        repo (Path): Repository root containing the negative-test corpus.

    Returns:
        list[NegativeCase]: Validated negative test cases described by the manifest.
    """
    corpus = repo / "tests" / "v3_legacy" / "negative"
    manifest_path = corpus / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest.get("schema") == NEGATIVE_CORPUS_SCHEMA, (
        f"unexpected V3 negative corpus schema in {manifest_path}"
    )
    entries = manifest.get("cases")
    assert isinstance(entries, list) and entries, "V3 negative corpus is empty"

    cases: list[NegativeCase] = []
    names: set[str] = set()
    sources: set[str] = set()
    for entry in entries:
        assert isinstance(entry, dict), f"invalid negative corpus entry: {entry!r}"
        name = entry.get("name")
        kind = entry.get("kind")
        file_name = entry.get("file")
        diagnostic = entry.get("diagnostic")
        flags = entry.get("flags", [])
        direct = entry.get("direct", False)
        public_cli = entry.get("public_cli", True)
        assert isinstance(name, str) and name, f"negative case has no name: {entry!r}"
        assert name not in names, f"duplicate negative case name: {name}"
        assert kind in {"lex", "parse", "type", "borrow"}, (
            f"negative case {name} has invalid kind: {kind!r}"
        )
        assert isinstance(file_name, str) and Path(file_name).name == file_name, (
            f"negative case {name} must name one local .fk file"
        )
        assert file_name.endswith(".fk"), f"negative case {name} is not a .fk source"
        assert file_name not in sources, f"negative source listed twice: {file_name}"
        assert isinstance(diagnostic, str) and diagnostic, (
            f"negative case {name} has no diagnostic oracle"
        )
        assert isinstance(flags, list) and all(isinstance(flag, str) for flag in flags), (
            f"negative case {name} has invalid flags"
        )
        assert isinstance(direct, bool), f"negative case {name} has invalid direct flag"
        assert isinstance(public_cli, bool), f"negative case {name} has invalid public_cli flag"
        source = corpus / file_name
        assert source.is_file(), f"negative corpus source missing: {source}"
        names.add(name)
        sources.add(file_name)
        cases.append(
            NegativeCase(
                name=name,
                kind=kind,
                source=source,
                diagnostic=diagnostic.lower(),
                flags=tuple(flags),
                direct=direct,
                public_cli=public_cli,
            )
        )

    on_disk = {path.name for path in corpus.glob("*.fk")}
    assert sources == on_disk, (
        "negative corpus manifest/file mismatch: "
        f"unlisted={sorted(on_disk - sources)}, missing={sorted(sources - on_disk)}"
    )
    assert {case.name for case in cases if not case.public_cli} == {"forward_shape_constructor"}, (
        "only the documented forward-shape direct-stage fixture may differ at the public CLI"
    )
    assert all(case.direct for case in cases if not case.public_cli), (
        "a public CLI exception must retain direct-stage rejection"
    )
    return cases


def task_body(source: str, task_name: str) -> str:
    """
    Extract the source text for a named task.

    Parameters:
        source (str): FREAK source code containing the task.
        task_name (str): Name of the task to extract.

    Returns:
        str: The task declaration and body through the next task declaration or the end of the source.

    Raises:
        ValueError: If the named task is not present in the source.
    """
    start = source.index(f"task {task_name}")
    next_task = source.find("\ntask ", start + 1)
    return source[start:] if next_task < 0 else source[start:next_task]


def assert_builtin_signature_parity(repo: Path) -> None:
    """
    Verify that builtin mappings, type and parameter signatures, and reserved namespaces remain consistent across compiler stages.

    Parameters:
        repo (Path): Repository root containing the compiler source files.
    """
    c_source = (repo / "src/compiler/v3/emit_c.fk").read_text(encoding="utf-8")
    llvm_source = (repo / "src/compiler/v3/emit_llvm.fk").read_text(encoding="utf-8")
    checker_source = (repo / "src/compiler/v3/checker.fk").read_text(encoding="utf-8")
    globals_source = (repo / "src/compiler/v3/globals.fk").read_text(encoding="utf-8")
    runtime_header = (repo / "freakc/runtime/freak_runtime.h").read_text(encoding="utf-8")
    runtime_c = (repo / "freakc/runtime/freak_runtime.c").read_text(encoding="utf-8")
    llvm_runtime_c = (repo / "freakc/runtime/freak_llvm_runtime.c").read_text(
        encoding="utf-8"
    )
    compiler_main = (repo / "src/compiler/v3/main.fk").read_text(encoding="utf-8")
    c_mapped = set(
        re.findall(r'val == "([^"]+)"', task_body(c_source, "c_map_call"))
    )
    llvm_mapped = set(
        re.findall(r'val == "([^"]+)"', task_body(llvm_source, "llvm_map_call_name"))
    )
    mapped = c_mapped | llvm_mapped
    removed_internal_symbols = {"freak_internal_delete_file_checked"}
    assert removed_internal_symbols.isdisjoint(mapped)
    classified = set(
        re.findall(
            r'name == "([^"]+)"', task_body(checker_source, "tc_builtin_call_type")
        )
    )
    assert removed_internal_symbols.isdisjoint(classified)
    assert "freak_internal_delete_file_checked" not in globals_source
    assert "freak_internal_delete_file_checked" not in llvm_source
    assert "freak_llvm_fs_delete_checked" not in llvm_source
    assert "freak_internal_delete_file_checked" not in runtime_header
    assert "freak_internal_delete_file_checked" not in runtime_c
    assert "freak_llvm_fs_delete_checked" not in llvm_runtime_c
    assert "--compiler-internal" not in compiler_main
    assert "bool freak_fs_delete(freak_word path);" in runtime_header
    assert "bool freak_fs_delete(freak_word path)" in runtime_c
    assert (
        'if name == "fs::exists" or name == "fs::delete" { give back "bool" }'
        in checker_source
    )
    signature_classified = set(
        re.findall(
            r'name == "([^"]+)"',
            task_body(checker_source, "tc_builtin_call_params"),
        )
    )
    # These guarded routes map exactly the classifier's admitted namespace
    # members. Literal-equality matches alone omit their real builtin calls.
    prefix_pattern = (
        r'if val\.starts_with\("([^"]+)"\) and tc_builtin_call_type\(val\) != ""\s*'
        r'\{\s*give back "([^"]+)" \+ val\.replace\("::", "_"\)\s*\}'
    )
    expected_prefixes = {"fs::", "process::command_", "json_document::", "http_server::"}
    for source, task_name, mapped_names, symbol_prefix in (
        (c_source, "c_map_call", c_mapped, "freak_"),
        (llvm_source, "llvm_map_call_name", llvm_mapped, "@freak_llvm_"),
    ):
        prefix_routes = dict(re.findall(prefix_pattern, task_body(source, task_name)))
        assert set(prefix_routes) == expected_prefixes, prefix_routes
        assert set(prefix_routes.values()) == {symbol_prefix}, prefix_routes
        mapped_names.update(
            name for name in classified if any(name.startswith(prefix) for prefix in prefix_routes)
        )
    mapped = c_mapped | llvm_mapped
    # These are declared externs whose C Word ABI needs a scalar LLVM bridge,
    # not names that ordinary source may call without a declaration.
    extern_aliases = dict(
        re.findall(
            r'if val == "([^"]+)" and emt_is_extern\(val\)\s*'
            r'\{\s*give back "(@[^"]+)"\s*\}',
            task_body(llvm_source, "llvm_map_call_name"),
        )
    )
    assert extern_aliases == {"freak_word_compare": "@freak_llvm_word_compare"}
    extern_names = set(extern_aliases)
    assert extern_names <= llvm_mapped
    assert extern_names.isdisjoint(c_mapped)
    assert extern_names.isdisjoint(classified)
    assert extern_names.isdisjoint(signature_classified)
    assert "extern task freak_word_compare(a: word, b: word) -> int" in (
        repo / "std/algorithm.fk"
    ).read_text(encoding="utf-8")
    assert "int64_t freak_word_compare(freak_word a, freak_word b);" in runtime_header
    assert "int64_t freak_word_compare(freak_word a, freak_word b) {" in runtime_c
    assert "int64_t freak_llvm_word_compare(int64_t left,int64_t right);" in runtime_header
    assert (
        "int64_t freak_llvm_word_compare(int64_t left,int64_t right) {\n"
        "    return freak_word_compare(freak_llvm_word_view(left),freak_llvm_word_view(right));\n}"
        in llvm_runtime_c
    )
    assert 'llvm_emit_line("declare i64 @freak_llvm_word_compare(i64, i64)")' in llvm_source
    internal_lowering_intrinsics = {
        "shape::alloc",
        "shape::get",
        "shape::set",
    }
    implicit_mapped = mapped - extern_names
    missing = sorted(implicit_mapped - classified - internal_lowering_intrinsics)
    assert not missing, f"builtin return-type inventory missing: {missing}"
    missing_signatures = sorted(
        implicit_mapped - signature_classified - internal_lowering_intrinsics
    )
    assert not missing_signatures, (
        f"builtin parameter-signature inventory missing: {missing_signatures}"
    )
    assert internal_lowering_intrinsics <= llvm_mapped
    assert internal_lowering_intrinsics.isdisjoint(classified)
    assert internal_lowering_intrinsics.isdisjoint(signature_classified)
    assert classified - c_mapped == set()
    assert classified - llvm_mapped == set()
    assert signature_classified == classified
    builtin_params = task_body(checker_source, "tc_builtin_call_params")
    assert 'name == "array_push" { give back "word-array,word" }' in builtin_params
    assert 'name == "array_set" { give back "word-array,int,word" }' in builtin_params
    assert 'destination == "word-array" { give back source == "int" or source == "List<word>" }' in task_body(checker_source, "tc_type_assignable")

    canonical_namespace_owners = {
        name.split("::", 1)[0] for name in classified if "::" in name
    }
    reserved_owner_body = task_body(
        checker_source, "tc_reserved_builtin_namespace_owner"
    )
    reserved_namespace_owners = set(
        re.findall(r'name == "([^"]+)"', reserved_owner_body)
    )
    assert reserved_namespace_owners == canonical_namespace_owners | {"shape", "List"}, (
        "reserved shape namespace owners drifted from compiler builtins: "
        f"reserved={sorted(reserved_namespace_owners)}, "
        f"canonical={sorted(canonical_namespace_owners)}"
    )


def assert_ci_shell_contract(repo: Path) -> None:
    """
    Verify that required CI workflow steps explicitly use Bash shells.
    """
    workflow = (repo / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    for step_name in (
        "V3 parser/type errors gate code generation",
        "V3 word replacement ownership",
    ):
        marker = f"      - name: {step_name}\n"
        start = workflow.index(marker)
        end = workflow.find("\n      - name: ", start + len(marker))
        block = workflow[start:] if end < 0 else workflow[start:end]
        assert "\n        shell: bash\n" in block, (
            f"{step_name} must use bash so $EXT expands on Windows"
        )


def assert_checker_callable_index(repo: Path) -> None:
    """Verify that checker callable indexing tasks exist and avoid rescanning all top-level statements."""
    checker = (repo / "src/compiler/v3/checker.fk").read_text(encoding="utf-8")
    assert "task tc_callable_entry(name: word) -> int" in checker
    assert "task tc_index_callable(stmt_id: int) -> void" in checker
    for task_name in (
        "tc_task_return_type",
        "tc_impl_method_arity",
        "tc_has_impl_method",
    ):
        body = task_body(checker, task_name)
        assert "ast_top_stmts" not in body, f"{task_name} still rescans every top-level statement"


def assert_parser_required_token_contract(repo: Path) -> None:
    """Verify that required parser tokens use the standard identifier parser and delimiter diagnostics preserve opener context.

    Parameters:
        repo (Path): Repository root containing the V3 parser source.

    Raises:
        AssertionError: If a required token context bypasses the standard parser or a delimiter context lacks opener provenance.
    """
    parser = (repo / "src/compiler/v3/parser.fk").read_text(encoding="utf-8")
    required_contexts = (
        "namespace segment after '::'",
        "shape constructor field",
        "member name",
        "pipe target",
        "annotation name",
        "fixed binding name",
        "fixed binding type",
        "binding name",
        "binding type",
        "parameter name",
        "parameter type",
        "shape name",
        "shape field name",
        "shape field type",
        "impl target",
        "impl owner",
        "impl method name",
        "impl method return type",
        "extern task name",
        "extern parameter name",
        "extern parameter type",
        "extern return type",
        "task name",
        "task return type",
    )
    for context in required_contexts:
        reader = "parser_take_type" if context.endswith(" type") else "parser_take_ident"
        assert f'{reader}("{context}")' in parser, (
            f"required parser token bypasses {reader}: {context}"
        )
    assert "parser_take_ident(context)" in task_body(parser, "parser_take_type")

    delimiter_contexts = (
        "shape constructor",
        "call argument list",
        "parenthesized expression",
        "array literal",
        "method argument list",
        "index expression",
        "pipe argument list",
        "parameter list",
        "shape declaration",
        "impl declaration",
        "when expression",
        "extern parameter list",
    )
    for context in delimiter_contexts:
        assert f'parser_diag_unclosed_at("{context}"' in parser, (
            f"delimiter EOF diagnostic lacks opener provenance: {context}"
        )


def run(
    freak: Path,
    repo: Path,
    source: Path,
    *args: str,
    env: dict[str, str] | None = None,
    timeout: int = 60,
) -> subprocess.CompletedProcess[str]:
    """
    Run the V3 command-line tool for a source file and capture its completed result.

    Parameters:
        env (dict[str, str] | None): Environment variables for the subprocess.
        timeout (int): Maximum time in seconds allowed for the subprocess.

    Returns:
        subprocess.CompletedProcess[str]: The captured subprocess result.
    """
    command, *flags = args
    return subprocess.run(
        [str(freak), command, str(source), *flags],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
        env=env,
    )


def assert_rejected(result: subprocess.CompletedProcess[str], label: str) -> None:
    """
    Verify that a rejected compilation fails before code generation.

    Parameters:
        label (str): Context label included in assertion messages.
    """
    output = result.stdout + result.stderr
    assert result.returncode != 0, f"{label}: invalid input exited successfully\n{output}"
    assert "code generation skipped" in output.lower(), (
        f"{label}: missing hard-gate diagnostic\n{output}"
    )
    assert "emit llvm ir" not in output.lower(), f"{label}: LLVM emitter ran\n{output}"
    assert "emit c" not in output.lower(), f"{label}: C emitter ran\n{output}"


def assert_check_rejected(
    result: subprocess.CompletedProcess[str], label: str
) -> None:
    """
    Verify that a check command rejects invalid input and reports an error.

    Parameters:
        result (subprocess.CompletedProcess[str]): Completed check-command result.
        label (str): Label used to identify the test in assertion messages.
    """
    output = result.stdout + result.stderr
    assert result.returncode != 0, f"{label}: check accepted invalid input\n{output}"
    assert "error" in output.lower(), f"{label}: missing diagnostic\n{output}"
    assert "passed" not in output.lower(), f"{label}: check printed PASSED\n{output}"


def assert_case_diagnostics(case: NegativeCase, output: str) -> None:
    """
    Validate that compiler output contains the diagnostics required for a negative test case.
    """
    lowered = output.lower()
    assert case.diagnostic in lowered, (
        f"{case.name}: missing diagnostic {case.diagnostic!r}\n{output}"
    )
    if case.name == "semantic_ui_num_geometry":
        for builtin in ("fill_rect", "stroke_rect", "fill_circle", "draw_line"):
            expected = (
                f"call to 'ui::{builtin}' argument 2 expects int, got num"
            )
            assert expected in lowered, (
                f"{case.name}: missing {builtin} geometry diagnostic\n{output}"
            )
    if case.name == "semantic_condition_types":
        for expected in (
            "repeat count must have type int, got bool",
            "training arc condition must have type bool, got int",
            "training arc max must have type int, got bool",
        ):
            assert expected in lowered, (
                f"{case.name}: missing condition diagnostic {expected!r}\n{output}"
            )


def assert_bound_diagnostic_source_labels(freak: Path, repo: Path, work: Path) -> None:
    """Preserve source type labels, including names resembling internal symbols."""
    for name in ('Vector3', 'pkg_' + '0' * 64 + '_Vector3'):
        source = work / (name + '.fk')
        source.write_text(
            f'shape {name} {{ value: int }}\n'
            f'task main() {{ pilot a: {name} = {name} {{ value: 1 }} '
            f'pilot b: {name} = {name} {{ value: 2 }} say a + b }}\n',
            encoding='utf-8',
        )
        expected = f"operator '+' does not accept {name} and {name}"
        for action, flag in (('check', ''), ('transpile', '--c'), ('transpile', '--llvm')):
            result = run(freak, repo, source, action, *([flag] if flag else []))
            output = result.stdout + result.stderr
            if action == 'check':
                assert_check_rejected(result, f'{name}/{action}')
            else:
                assert_rejected(result, f'{name}/{flag}')
            assert expected in output, (
                f'{name}/{action}/{flag}: missing exact source-name diagnostic\n{output}'
            )


def assert_bound_declaration_namespaces(
    freak: Path, repo: Path, work: Path, private_fixture: WindowsPrivateFixture | None = None
) -> None:
    """Exercise type/value and impl-member binding through the public CLI."""
    cases = {
        'type-and-task': (
            'shape Shared { value: int }\n'
            'task Shared() -> int { give back 8 }\n'
            'task main() { pilot item: Shared = Shared { value: 7 } say item.value say Shared() }\n'),
        'type-and-fixed': (
            'shape Shared { value: int }\nfixed pilot Shared: int = 7\n'
            'task main() { pilot item: Shared = Shared { value: Shared } say item.value say Shared }\n'),
        'fixed-and-impl-member': (
            'shape Shared { value: int }\nfixed pilot Shared_read: int = 19\n'
            'impl Shared { task read(self) -> int { give back self.value } }\n'
            'task main() { pilot item: Shared = Shared { value: 7 } say item.read() say Shared_read }\n'),
    }
    for label, body in cases.items():
        source = work / (label + '.fk')
        source.write_text(body, encoding='utf-8')
        for action, flag in (('check', ''), ('transpile', '--c'), ('transpile', '--llvm')):
            result = run(freak, repo, source, action, *([flag] if flag else []))
            assert result.returncode == 0, (
                f'{label}/{action}/{flag}: rejected disjoint declaration namespaces\n'
                + result.stdout + result.stderr
            )
    project = work / 'import-namespace-project'
    project.mkdir()
    if private_fixture is not None:
        private_fixture.claim_fresh_directories(project)
    (project / 'hangar.toml').write_text(
        '[project]\nname = "namespace-gate"\nversion = "1.0.0"\nkind = "app"\n'
        'entry = "main.fk"\n[modules]\ncore = "core.fk"\n', encoding='utf-8')
    (project / 'core.fk').write_text(
        'shape Point { value: int }\ntask measure() -> int { give back 8 }\n', encoding='utf-8')
    source = project / 'main.fk'
    source.write_text(
        'use self::core::{Point as Shared, measure as Shared}\n'
        'task main() { pilot item: Shared = Shared { value: 7 } say item.value say Shared() }\n',
        encoding='utf-8')
    for action, flag in (('check', ''), ('transpile', '--c'), ('transpile', '--llvm')):
        result = run(freak, repo, source, action, *([flag] if flag else []))
        assert result.returncode == 0, (
            f'imported type/value aliases/{action}/{flag}: incorrect namespace collision\n'
            + result.stdout + result.stderr
        )
    (project / 'core.fk').write_text('fixed pilot seed: int = 11\n', encoding='utf-8')
    source.write_text(
        'use self::core::{seed as std_abs}\ntask main() { say std_abs(-2) }\n', encoding='utf-8')
    for action, flag in (('check', ''), ('transpile', '--c'), ('transpile', '--llvm')):
        result = run(freak, repo, source, action, *([flag] if flag else []))
        output = result.stdout + result.stderr
        if action == 'check':
            assert_check_rejected(result, f'imported fixed value ambient fallback/{action}')
        else:
            assert_rejected(result, f'imported fixed value ambient fallback/{flag}')
        assert "unknown callable 'std_abs'" in output, output


def assert_generated_package_identity_access(
    freak: Path, repo: Path, work: Path, private_fixture: WindowsPrivateFixture | None = None
) -> None:
    """Generated identities cannot widen the source import/export surface."""
    project = work / 'generated-identity-project'
    library = project / 'lib'
    app = project / 'app'
    library.mkdir(parents=True)
    app.mkdir()
    if private_fixture is not None:
        private_fixture.claim_fresh_directories(project, library, app)
    (library / 'hangar.toml').write_text(
        '[project]\nname="identity-library"\nversion="1.0.0"\nkind="lib"\n'
        '[modules]\ncore="core.fk"\n[exports]\napi="core::api"\nother="core::other"\n')
    (library / 'core.fk').write_text(
        'fixed pilot secret: int = 4\nshape Hidden { value: int }\n'
        'impl Hidden { task make() -> Hidden { give back Hidden { value: 6 } } }\n'
        'task helper() -> int { give back secret }\n'
        'task api() -> int { pilot item = Hidden::make() give back helper() + item.value }\n'
        'task other() -> int { give back 9 }\n')
    (app / 'hangar.toml').write_text(
        '[project]\nname="identity-app"\nversion="1.0.0"\nkind="app"\nentry="main.fk"\n'
        '[dependencies]\nlib={path="../lib"}\n')
    source = app / 'main.fk'
    source.write_text('use lib::{api}\ntask main() { say api() }\n')
    admitted = run(freak, repo, source, 'transpile', '--c')
    assert admitted.returncode == 0, admitted.stdout + admitted.stderr
    emitted = Path(str(source) + '.c').read_text()
    matches = re.findall(r'__freak_user_(pkg_[0-9a-f]{64}_)helper\(', emitted)
    assert len(set(matches)) == 1, 'missing unique emitted private helper identity'
    prefix = matches[0]
    cases = {
        'private-call': f'say {prefix}helper()',
        'private-value': f'say {prefix}secret',
        'private-annotation': f'task consume(item: {prefix}Hidden) {{}}\ntask main() {{}}',
        'private-list-annotation': f'task consume(item: List<{prefix}Hidden>) {{}}\ntask main() {{}}',
        'private-associated': f'pilot item = {prefix}Hidden::make() say item.value',
        'unimported-public-call': f'say {prefix}other()',
    }
    for label, body in cases.items():
        declaration = body if 'annotation' in label else f'task main() {{ {body} }}'
        source.write_text(f'use lib::{{api}}\n{declaration}\n')
        for action, flag in (('check', ''), ('transpile', '--c'), ('transpile', '--llvm')):
            artifact = Path(str(source) + ('.c' if flag == '--c' else '.ll'))
            if flag:
                seed_stale_outputs(artifact)
            result = run(freak, repo, source, action, *([flag] if flag else []))
            output = result.stdout + result.stderr
            if action == 'check':
                assert_check_rejected(result, f'{label}/{action}')
            else:
                assert_rejected(result, f'{label}/{flag}')
                assert_outputs_absent((artifact,), f'{label}/{flag}')
            assert 'missing or unimported' in output and str(source) in output, output
    controls = {
        'source-declarations-and-local': (
            'use lib::{api}\n'
            f'task {prefix}helper() -> int {{ give back 7 }}\n'
            f'fixed pilot {prefix}secret: int = 8\n'
            f'shape {prefix}Hidden {{ value: int }}\n'
            f'task main() {{ {{ pilot {prefix}helper: int = 1 say {prefix}helper }} '
            f'say {prefix}helper() say {prefix}secret '
            f'pilot item: {prefix}Hidden = {prefix}Hidden {{ value: 2 }} say item.value say api() }}\n'),
        'explicit-alias': (
            f'use lib::{{api as {prefix}helper}}\n'
            f'task main() {{ say {prefix}helper() }}\n'),
    }
    for label, body in controls.items():
        source.write_text(body)
        for action, flag in (('check', ''), ('transpile', '--c'), ('transpile', '--llvm')):
            result = run(freak, repo, source, action, *([flag] if flag else []))
            assert result.returncode == 0, f'{label}/{action}/{flag}\n' + result.stdout + result.stderr
    # Standalone externs are supported; their parameter/return types need the
    # same source admission and nominal binding as ordinary task signatures.
    source = work / 'standalone-extern-identity.fk'
    source.write_text('shape Hidden { value: int }\n'
                      'task identity_probe() -> int { give back 1 }\n'
                      'task main() { say identity_probe() }\n')
    result = run(freak, repo, source, 'transpile', '--c')
    assert result.returncode == 0, result.stdout + result.stderr
    emitted = Path(str(source) + '.c').read_text()
    prefixes = re.findall(r'__freak_user_(pkg_[0-9a-f]{64}_)identity_probe\(', emitted)
    assert len(set(prefixes)) == 1, 'missing unique standalone emitted identity'
    own = prefixes[0] + 'Hidden'
    for label, signature in (
        ('parameter', f'extern task consume(item: {own}) -> void'),
        ('list-parameter', f'extern task consume(item: List<{own}>) -> void'),
        ('return', f'extern task consume() -> {own}'),
    ):
        source.write_text(f'shape Hidden {{ value: int }}\n{signature}\ntask main() {{}}\n')
        for action, flag in (('check', ''), ('transpile', '--c'), ('transpile', '--llvm')):
            artifact = Path(str(source) + ('.c' if flag == '--c' else '.ll'))
            if flag:
                seed_stale_outputs(artifact)
            result = run(freak, repo, source, action, *([flag] if flag else []))
            output = result.stdout + result.stderr
            if action == 'check':
                assert_check_rejected(result, f'extern own-generated {label}/{action}')
            else:
                assert_rejected(result, f'extern own-generated {label}/{flag}')
                assert_outputs_absent((artifact,), f'extern own-generated {label}/{flag}')
            assert "missing or unimported type '" + own + "'" in output and str(source) in output, output
    for label, declarations in (
        ('source-nominal', 'shape Hidden { value: int }\nextern task consume(item: Hidden) -> Hidden\n'),
        ('scalar', 'extern task consume(item: int) -> int\n'),
        ('source-exact-lookalike', f'shape {own} {{ value: int }}\nextern task consume(item: {own}) -> {own}\n'),
    ):
        source.write_text(declarations + 'task main() {}\n')
        for action, flag in (('check', ''), ('transpile', '--c'), ('transpile', '--llvm')):
            result = run(freak, repo, source, action, *([flag] if flag else []))
            assert result.returncode == 0, f'extern {label}/{action}/{flag}\n' + result.stdout + result.stderr


def assert_local_value_call_shadowing(
    freak: Path, direct_compiler: Path | None, repo: Path, work: Path
) -> None:
    """Local values and parameters shadow callable VALUE names until scope exit."""
    for label, body in (
        ('ordinary', 'task main() { pilot measure: int = 7 say measure() }\n'),
        ('fixed', 'task main() { fixed pilot measure: int = 7 say measure() }\n'),
        ('parameter', 'task consume(measure: int) { say measure() }\ntask main() {}\n'),
        ('outer-scope', 'task main() { pilot measure: int = 7 { say measure() } }\n'),
        ('range-binder', 'task main() { for each measure in 0..1 { say measure() } }\n'),
        ('repeat-binder', 'task main() { repeat 1 times with measure { say measure() } }\n'),
    ):
        source = work / ('local-call-' + label + '.fk')
        source.write_text('task measure() -> int { give back 8 }\n' + body, encoding='utf-8')
        for flag in ('--c', '--llvm'):
            artifact = Path(str(source) + ('.c' if flag == '--c' else '.ll'))
            seed_stale_outputs(artifact)
            result = run(freak, repo, source, 'transpile', flag)
            output = result.stdout + result.stderr
            assert_rejected(result, f'local {label} shadow/{flag}/public')
            assert "unknown callable 'measure': local value shadows this name" in output, output
            assert_outputs_absent((artifact,), f'local {label} shadow/{flag}/public')
            if direct_compiler is not None:
                seed_stale_outputs(artifact)
                result = run_direct_compiler(direct_compiler, repo, str(source), flag)
                output = result.stdout + result.stderr
                assert result.returncode != 0, f'local {label} shadow/{flag}/direct accepted\n{output}'
                assert "unknown callable 'measure': local value shadows this name" in output, output
                assert 'emitting' not in output.lower(), output
                assert_outputs_absent((artifact,), f'local {label} shadow/{flag}/direct')
    source = work / 'local-call-scope-exit.fk'
    source.write_text(
        'shape measure { value: int }\ntask measure() -> int { give back 8 }\n'
        'task main() { { pilot measure: int = 7 '
        'pilot item: measure = measure { value: measure } say item.value } say measure() }\n',
        encoding='utf-8')
    for flag in ('--c', '--llvm'):
        result = run(freak, repo, source, 'transpile', flag)
        assert result.returncode == 0, result.stdout + result.stderr
        if direct_compiler is not None:
            result = run_direct_compiler(direct_compiler, repo, str(source), flag)
            assert result.returncode == 0, result.stdout + result.stderr


def assert_bound_lexical_error_counts(
    freak: Path, direct_compiler: Path | None, repo: Path, work: Path,
    private_fixture: WindowsPrivateFixture | None = None
) -> None:
    """Early source admission preserves the lexer count in both scan phases."""
    for count in (1, 2):
        invalid = 'task lexical_probe() { say "' + 'before\\x00after' * count + '" }\n'
        loaded = work / f'lexical-count-{count}.fk'
        loaded.write_text(invalid + 'task main() {}\n', encoding='utf-8')
        project = work / f'lexical-export-count-{count}'
        library, app = project / 'lib', project / 'app'
        library.mkdir(parents=True)
        app.mkdir()
        if private_fixture is not None:
            private_fixture.claim_fresh_directories(project, library, app)
        (library / 'hangar.toml').write_text(
            '[project]\nname="lexical-count-library"\nversion="1.0.0"\nkind="lib"\n'
            '[modules]\ncore="core.fk"\nother="other.fk"\n'
            '[exports]\napi="core::api"\nexposed="other::exposed"\n', encoding='utf-8')
        (library / 'core.fk').write_text('task api() -> int { give back 8 }\n', encoding='utf-8')
        unloaded = library / 'other.fk'
        unloaded.write_text('task exposed() -> int { give back 4 }\n' + invalid, encoding='utf-8')
        (app / 'hangar.toml').write_text(
            '[project]\nname="lexical-count-app"\nversion="1.0.0"\nkind="app"\nentry="main.fk"\n'
            '[dependencies]\nlib={path="../lib"}\n', encoding='utf-8')
        entry = app / 'main.fk'
        entry.write_text('use lib::{api}\ntask main() { say api() }\n', encoding='utf-8')
        for phase, source, lexical_source in (
            ('loaded', loaded, loaded), ('unloaded-export', entry, unloaded)
        ):
            for action, flag in (('check', ''), ('transpile', '--c'), ('transpile', '--llvm')):
                artifact = Path(str(source) + ('.c' if flag == '--c' else '.ll'))
                if flag:
                    seed_stale_outputs(artifact)
                result = run(freak, repo, source, action, *([flag] if flag else []))
                output = result.stdout + result.stderr
                if action == 'check':
                    assert_check_rejected(result, f'{phase} lexical count {count}/{action}')
                else:
                    assert_rejected(result, f'{phase} lexical count {count}/{flag}')
                    assert_outputs_absent((artifact,), f'{phase} lexical count {count}/{flag}')
                assert f'{count} syntax error(s)' in output, output
                assert output.count('embedded NUL escape is not supported') == count, output
                assert str(lexical_source) in output, output
            if direct_compiler is not None:
                for flag in ('--c', '--llvm'):
                    artifact = Path(str(lexical_source) + ('.c' if flag == '--c' else '.ll'))
                    seed_stale_outputs(artifact)
                    result = run_direct_compiler(direct_compiler, repo, str(lexical_source), flag)
                    output = result.stdout + result.stderr
                    assert result.returncode != 0, output
                    assert f'aborting: {count} error(s) found' in output, output
                    assert output.count('embedded NUL escape is not supported') == count, output
                    assert 'emitting' not in output.lower(), output
                    assert_outputs_absent((artifact,), f'direct {phase} lexical count {count}/{flag}')


def assert_public_forward_shape_constructor(freak: Path, repo: Path, work: Path) -> None:
    """The package binder discovers headers before parsing constructor bodies."""
    original = (repo / 'tests/v3_legacy/negative/forward_shape_constructor.fk').read_text()
    assert 'say "unreachable"' in original
    source = work / 'public-forward-shape-constructor.fk'
    source.write_text(original.replace('say "unreachable"', 'say make().value'))
    checked = run(freak, repo, source, 'check')
    assert checked.returncode == 0, checked.stdout + checked.stderr
    for flag in ('--c', '--llvm'):
        emitted = run(freak, repo, source, 'transpile', flag)
        assert emitted.returncode == 0, emitted.stdout + emitted.stderr
        built = run(freak, repo, source, 'build', flag)
        assert built.returncode == 0, built.stdout + built.stderr
        executed = subprocess.run([str(derived_binary(source))], cwd=work, capture_output=True,
                                  text=True, encoding='utf-8', timeout=10, check=False)
        assert executed.returncode == 0 and executed.stdout == '1\n' and not executed.stderr, (
            executed.stdout + executed.stderr
        )


def assert_bound_source_reservations(
    freak: Path, direct_compiler: Path | None, repo: Path, work: Path
) -> None:
    """Compiler name reservations apply to authored names before flattening."""
    cases = {
        'reserved-shape-owner': ('shape math { value: num }\n', "shape name 'math' conflicts with a compiler builtin namespace"),
        'reserved-shape-type': ('shape CheckedReadResult { value: int }\n', "shape name 'CheckedReadResult' conflicts with a built-in type"),
        'reserved-task': ('task word_to_int(value: word) -> int { give back 99 }\n', "callable 'word_to_int' conflicts with a compiler builtin"),
        'reserved-runtime-task': ('task llvm_fs_read(value: word) -> int { give back 99 }\n', "callable 'llvm_fs_read' conflicts with a compiler builtin"),
    }
    for label, (declarations, expected) in cases.items():
        source = work / (label + '.fk')
        source.write_text(declarations + 'task main() {}\n')
        for action, flag in (('check', ''), ('transpile', '--c'), ('transpile', '--llvm')):
            artifact = Path(str(source) + ('.c' if flag == '--c' else '.ll'))
            if flag:
                seed_stale_outputs(artifact)
            result = run(freak, repo, source, action, *([flag] if flag else []))
            output = result.stdout + result.stderr
            if action == 'check':
                assert_check_rejected(result, f'{label}/{action}')
            else:
                assert_rejected(result, f'{label}/{flag}')
                assert_outputs_absent((artifact,), f'{label}/{flag}')
            assert expected in output, output
            if flag and direct_compiler is not None:
                result = run_direct_compiler(direct_compiler, repo, str(source), flag)
                assert result.returncode != 0 and expected in result.stdout + result.stderr, result.stdout + result.stderr
    source = work / 'source-reservation-lookalikes.fk'
    source.write_text('shape pkg_' + '0' * 64 + '_math { value: int }\n'
                      'task chr(value: int) -> int { give back value }\n'
                      'task main() { say chr(7) }\n')
    for flag in ('--c', '--llvm'):
        result = run(freak, repo, source, 'transpile', flag)
        assert result.returncode == 0, result.stdout + result.stderr
        if direct_compiler is not None:
            for profile in ((), ('--bootstrap-compat=v4-host-bootstrap-v1',)):
                result = run_direct_compiler(direct_compiler, repo, str(source), flag, *profile)
                assert result.returncode == 0, result.stdout + result.stderr


def assert_fixed_value_namespace_collisions(
    freak: Path, direct_compiler: Path | None, repo: Path, work: Path
) -> None:
    """Fixed root bindings share the callable value namespace in both front doors."""
    for label, declarations in (
        ('fixed-before-task', 'fixed pilot overlap: int = 7\ntask overlap() -> int { give back 8 }\n'),
        ('task-before-fixed', 'task overlap() -> int { give back 8 }\nfixed pilot overlap: int = 7\n'),
        ('fixed-before-extern', 'fixed pilot overlap: int = 7\nextern task overlap() -> int\n'),
        ('extern-before-fixed', 'extern task overlap() -> int\nfixed pilot overlap: int = 7\n'),
    ):
        source = work / (label + '.fk')
        source.write_text(declarations + 'task main() {}\n', encoding='utf-8')
        for flag in ('--c', '--llvm'):
            result = run(freak, repo, source, 'transpile', flag)
            assert_rejected(result, f'{label}/{flag}/public')
            assert 'duplicate module declaration' in result.stdout + result.stderr
            if direct_compiler is not None:
                direct = run_direct_compiler(direct_compiler, repo, str(source), flag)
                output = direct.stdout + direct.stderr
                assert direct.returncode != 0, f'{label}/{flag}/direct accepted fixed collision\n{output}'
                assert 'conflicts with a callable in the value namespace' in output
                assert 'emitting' not in output.lower(), f'{label}/{flag}/direct entered emission\n{output}'


def run_direct_compiler(
    compiler: Path,
    repo: Path,
    *args: str,
    timeout: int = 10,
) -> subprocess.CompletedProcess[str]:
    """
    Run the direct compiler with captured text output.

    Parameters:
        compiler (Path): Path to the compiler executable.
        repo (Path): Working directory for the compiler process.
        *args (str): Arguments passed to the compiler.
        timeout (int): Maximum execution time in seconds.

    Returns:
        subprocess.CompletedProcess[str]: The completed compiler process result.
    """
    return subprocess.run(
        [str(compiler), *args],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )


def assert_word_compare_extern_contract(
    freak: Path, repo: Path, tmp_path: Path, direct_compiler: Path | None
) -> None:
    """Prove declared comparison typing, its native ABI, and extern-only aliasing."""
    public = tmp_path / "word_compare_public.fk"
    public.write_text(
        'task main() {\n'
        '    pilot smaller: int = freak_word_compare("a", "b")\n'
        '    pilot equal: int = freak_word_compare("same", "same")\n'
        '    pilot greater: int = freak_word_compare("Ω", "a")\n'
        '    say smaller say equal say greater\n'
        '}\n',
        encoding="utf-8",
    )
    for backend, flag in (("LLVM", "--llvm"), ("C", "--c")):
        built = run(freak, repo, public, "build", flag, "--strict-borrow")
        assert built.returncode == 0, built.stdout + built.stderr
        executed = subprocess.run(
            [str(derived_binary(public))], cwd=tmp_path, capture_output=True,
            text=True, encoding="utf-8", timeout=10, check=False,
        )
        assert executed.returncode == 0, executed.stdout + executed.stderr
        assert executed.stdout == "-1\n0\n1\n", f"{backend}: {executed.stdout!r}"
        assert not executed.stderr, executed.stderr

    if direct_compiler is None:
        return
    declaration = 'extern task freak_word_compare(a: word, b: word) -> int\n'
    positives = {
        "declared": declaration + 'task main() { pilot outcome: int = freak_word_compare("a", "b") say outcome }\n',
        "shadow": 'task freak_word_compare(a: int, b: int) -> int { give back a + b }\ntask main() { say freak_word_compare(20, 22) }\n',
    }
    negatives = {
        "argument": (declaration + 'task main() { say freak_word_compare(1, "b") }\n', "argument 1 expects word, got int"),
        "return": (declaration + 'task main() { pilot outcome: word = freak_word_compare("a", "b") say outcome }\n', "cannot initialize word binding 'outcome' with int"),
        "undeclared": ('task main() { say freak_word_compare("a", "b") }\n', "unknown callable 'freak_word_compare'"),
    }
    for backend, flag, suffix in (("LLVM", "--llvm", ".ll"), ("C", "--c", ".c")):
        for name, source_text in positives.items():
            source = tmp_path / f"word_compare_{name}_{backend.lower()}.fk"
            source.write_text(source_text, encoding="utf-8")
            result = run_direct_compiler(direct_compiler, repo, str(source), flag, "--strict-borrow")
            assert result.returncode == 0, result.stdout + result.stderr
            emitted = Path(str(source) + suffix).read_text(encoding="utf-8")
            if backend == "LLVM":
                target = "freak_llvm_word_compare" if name == "declared" else "__freak_user_freak_word_compare"
                assert f"call i64 @{target}(i64 " in emitted, emitted
                if name == "shadow":
                    assert "call i64 @freak_llvm_word_compare(" not in emitted
            elif name == "shadow":
                main_body = emitted.split("void __freak_user_main(void) {", 1)[1]
                assert "__freak_call_arg_0 = 20;" in main_body
                assert "__freak_call_arg_1 = 22;" in main_body
                assert " = __freak_user_freak_word_compare(__freak_call_arg_0, __freak_call_arg_1);" in main_body
                assert not re.search(r"(?<![A-Za-z_0-9])freak_word_compare\(", main_body)
            else:
                main_body = emitted.split("void __freak_user_main(void) {", 1)[1]
                assert re.search(r" = freak_word_compare\(__freak_borrow_arg_\d+_0, __freak_borrow_arg_\d+_1\);", main_body)
        for name, (source_text, diagnostic) in negatives.items():
            source = tmp_path / f"word_compare_{name}_{backend.lower()}.fk"
            source.write_text(source_text, encoding="utf-8")
            artifact = Path(str(source) + suffix)
            seed_stale_outputs(artifact)
            result = run_direct_compiler(direct_compiler, repo, str(source), flag)
            output = result.stdout + result.stderr
            assert result.returncode != 0, output
            assert diagnostic in output, output
            assert_outputs_absent((artifact,), f"{backend} word compare {name}")


def main() -> int:
    """
    Run the V3 compiler diagnostic and code-generation regression suite.

    Returns:
        int: Zero when all checks pass.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("freak", type=Path)
    parser.add_argument(
        "--freakc",
        type=Path,
        help="current direct V3 stage compiler (auto-detected beside freak in CI)",
    )
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    freak = args.freak.resolve()
    assert freak.is_file(), f"FREAK CLI not found: {freak}"
    direct_compiler = args.freakc.resolve() if args.freakc else None
    if direct_compiler is None:
        stage_name = "freakc_v3_stage2.exe" if sys.platform == "win32" else "freakc_v3_stage2"
        stage_candidate = freak.parent / stage_name
        if stage_candidate.is_file():
            direct_compiler = stage_candidate.resolve()
    if direct_compiler is not None:
        assert direct_compiler.is_file(), f"direct V3 compiler not found: {direct_compiler}"
    elif os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
        raise AssertionError("CI requires the current direct V3 stage compiler")
    assert_builtin_signature_parity(repo)
    assert_ci_shell_contract(repo)
    assert_checker_callable_index(repo)
    assert_parser_required_token_contract(repo)
    negative_cases = load_negative_corpus(repo)

    with tempfile.TemporaryDirectory(prefix="freak-v3-codegen-gate-") as tmp:
        # Installed payload admission refuses symlinked directory components.
        # macOS temporary roots may use aliases such as /var -> /private/var.
        tmp_path = Path(tmp).resolve()
        private_fixture = WindowsPrivateFixture(tmp_path)
        assert_word_compare_extern_contract(freak, repo, tmp_path, direct_compiler)
        for name, source_text, diagnostic in (
            ("root_execution", 'say "outside entry"\ntask main() {}\n', "executable statement at top level is unsupported"),
            ("missing_entry", 'task helper() { say "no entry" }\n', "requires a usable task main() entry"),
        ):
            source = tmp_path / f"{name}.fk"
            source.write_text(source_text, encoding="utf-8")
            for backend, flag, suffix in (("LLVM", "--llvm", ".ll"), ("C", "--c", ".c")):
                artifact = Path(str(source) + suffix)
                seed_stale_outputs(artifact)
                rejected = run(freak, repo, source, "transpile", flag)
                assert_rejected(rejected, f"{backend} {name}")
                assert diagnostic in rejected.stdout + rejected.stderr
                assert_outputs_absent((artifact,), f"{backend} {name}")
                if direct_compiler is not None:
                    seed_stale_outputs(artifact)
                    direct = run_direct_compiler(direct_compiler, repo, str(source), flag)
                    assert direct.returncode != 0, direct.stdout + direct.stderr
                    assert diagnostic in direct.stdout + direct.stderr
                    assert_outputs_absent((artifact,), f"direct {backend} {name}")
        staged_cases: dict[str, Path] = {}
        for case in negative_cases:
            malformed = tmp_path / case.source.name
            shutil.copy2(case.source, malformed)
            staged_cases[case.name] = malformed
            if not case.public_cli:
                continue

            binary = derived_binary(malformed)
            cache = run_cache(binary)
            check_outputs = (
                Path(str(malformed) + ".c"),
                Path(str(malformed) + ".ll"),
                binary,
                cache,
            )
            seed_stale_outputs(*check_outputs)

            checked = run(
                freak, repo, malformed, "check", *case.flags, timeout=10
            )
            assert_check_rejected(checked, case.name)
            assert_case_diagnostics(case, checked.stdout + checked.stderr)
            if case.name == "semantic_control_context":
                checked_output = (checked.stdout + checked.stderr).replace("\\", "/")
                assert f"/{malformed.name}:1:1" in checked_output, checked_output
                assert "1 | give back 1" in checked_output, checked_output
            if case.name == "semantic_multiline_operator":
                checked_output = (checked.stdout + checked.stderr).replace("\\", "/")
                assert f"/{malformed.name}:4:1" in checked_output, checked_output
                assert '4 |         + 7' in checked_output, checked_output
            if case.name == "semantic_multiline_condition":
                checked_output = (checked.stdout + checked.stderr).replace("\\", "/")
                assert f"/{malformed.name}:3:1" in checked_output, checked_output
                assert "3 |         1" in checked_output, checked_output
            if case.name == "semantic_multiline_member":
                checked_output = (checked.stdout + checked.stderr).replace("\\", "/")
                assert f"/{malformed.name}:6:1" in checked_output, checked_output
                assert "6 |         .missing()" in checked_output, checked_output
            if case.name == "semantic_impl_method_missing_return":
                checked_output = (checked.stdout + checked.stderr).replace("\\", "/")
                assert f"/{malformed.name}:4:1" in checked_output, checked_output
                assert "4 |     task unfinished(" in checked_output, checked_output
            if case.name == "immutable_reassignment":
                checked_output = (checked.stdout + checked.stderr).replace("\\", "/")
                assert f"/{malformed.name}:6:1" in checked_output, checked_output
                assert '6 |     name = "Meiya"' in checked_output, checked_output
            assert_outputs_preserved(check_outputs, f"{case.name} check")
            for output in dict.fromkeys(check_outputs):
                output.unlink()

            for backend, flag, suffix in (
                ("LLVM", "--llvm", ".ll"),
                ("C", "--c", ".c"),
            ):
                artifact = Path(str(malformed) + suffix)
                artifact.write_text(SENTINEL, encoding="utf-8")
                transpiled = run(
                    freak,
                    repo,
                    malformed,
                    "transpile",
                    flag,
                    *case.flags,
                    timeout=10,
                )
                assert_rejected(transpiled, f"{case.name} {backend} transpile")
                assert_case_diagnostics(
                    case, transpiled.stdout + transpiled.stderr
                )
                assert_outputs_absent(
                    (artifact,), f"{case.name} {backend} transpile"
                )

                seed_stale_outputs(artifact, binary, cache)
                built = run(
                    freak,
                    repo,
                    malformed,
                    "build",
                    flag,
                    *case.flags,
                    timeout=10,
                )
                assert_rejected(built, f"{case.name} {backend} build")
                assert_case_diagnostics(case, built.stdout + built.stderr)
                assert_outputs_absent(
                    (artifact, binary, cache), f"{case.name} {backend} build"
                )

        if direct_compiler is not None:
            missing_args = run_direct_compiler(direct_compiler, repo)
            assert missing_args.returncode != 0, (
                "direct V3 compiler accepted missing arguments\n"
                + missing_args.stdout
                + missing_args.stderr
            )
            missing_source = tmp_path / "direct_missing.fk"
            for backend, flag, suffix in (
                ("LLVM", "--llvm", ".ll"),
                ("C", "--c", ".c"),
            ):
                artifact = Path(str(missing_source) + suffix)
                seed_stale_outputs(artifact)
                unreadable = run_direct_compiler(
                    direct_compiler, repo, str(missing_source), flag
                )
                assert unreadable.returncode != 0, (
                    f"direct {backend} accepted an unreadable input\n"
                    + unreadable.stdout
                    + unreadable.stderr
                )
                assert_unreadable_diagnostic(
                    unreadable.stdout + unreadable.stderr,
                    f"direct {backend} unreadable input",
                )
                assert_outputs_absent(
                    (artifact,), f"direct {backend} unreadable input"
                )

            for case in negative_cases:
                if not case.direct:
                    continue
                malformed = staged_cases[case.name]
                for backend, flag, suffix in (
                    ("LLVM", "--llvm", ".ll"),
                    ("C", "--c", ".c"),
                ):
                    artifact = Path(str(malformed) + suffix)
                    seed_stale_outputs(artifact)
                    rejected = run_direct_compiler(
                        direct_compiler, repo, str(malformed), flag, *case.flags
                    )
                    output = rejected.stdout + rejected.stderr
                    assert rejected.returncode != 0, (
                        f"direct {backend} accepted {case.name}\n{output}"
                    )
                    assert "error" in output.lower(), output
                    assert_case_diagnostics(case, output)
                    assert_outputs_absent(
                        (artifact,), f"direct {backend} {case.name}"
                    )

        cli_missing = tmp_path / "cli_missing.fk"
        missing_binary = derived_binary(cli_missing)
        missing_cache = run_cache(missing_binary)
        for backend, flag, suffix in (
            ("LLVM", "--llvm", ".ll"),
            ("C", "--c", ".c"),
        ):
            artifact = Path(str(cli_missing) + suffix)
            seed_stale_outputs(artifact)
            unreadable_transpile = run(
                freak, repo, cli_missing, "transpile", flag, timeout=10
            )
            unreadable_output = (
                unreadable_transpile.stdout + unreadable_transpile.stderr
            )
            assert unreadable_transpile.returncode != 0, unreadable_output
            assert_unreadable_diagnostic(
                unreadable_output, f"{backend} unreadable CLI transpile"
            )
            assert_outputs_absent(
                (artifact,), f"{backend} unreadable CLI transpile"
            )

            seed_stale_outputs(artifact, missing_binary, missing_cache)
            unreadable_build = run(
                freak, repo, cli_missing, "build", flag, timeout=10
            )
            unreadable_output = unreadable_build.stdout + unreadable_build.stderr
            assert unreadable_build.returncode != 0, unreadable_output
            assert_unreadable_diagnostic(
                unreadable_output, f"{backend} unreadable CLI build"
            )
            assert_outputs_absent(
                (artifact, missing_binary, missing_cache),
                f"{backend} unreadable CLI build",
            )

            legacy_artifact = Path(str(cli_missing) + suffix)
            seed_stale_outputs(legacy_artifact)
            legacy_unreadable = subprocess.run(
                [str(freak), str(cli_missing), flag],
                cwd=repo,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                check=False,
            )
            assert legacy_unreadable.returncode != 0
            assert_unreadable_diagnostic(
                legacy_unreadable.stdout + legacy_unreadable.stderr,
                f"{backend} unreadable legacy CLI",
            )
            assert_outputs_absent(
                (legacy_artifact,), f"{backend} unreadable legacy CLI"
            )

        blocked_cleanup = tmp_path / "blocked_cleanup.fk"
        blocked_cleanup.write_text('task main() { say "never emitted" }\n', encoding="utf-8")
        for backend, flag, suffix in (
            ("LLVM", "--llvm", ".ll"),
            ("C", "--c", ".c"),
        ):
            blocked_artifact = Path(str(blocked_cleanup) + suffix)
            blocked_artifact.mkdir()
            blocked_result = run(
                freak, repo, blocked_cleanup, "transpile", flag, timeout=10
            )
            blocked_output = blocked_result.stdout + blocked_result.stderr
            assert blocked_result.returncode != 0, (
                f"{backend} blocked cleanup unexpectedly succeeded\n{blocked_output}"
            )
            assert "untrusted stale artifact" in blocked_output.lower(), (
                f"{backend} blocked cleanup: missing diagnostic\n{blocked_output}"
            )
            assert blocked_artifact.is_dir(), (
                f"{backend} blocked cleanup removed the directory: {blocked_artifact}"
            )
            blocked_artifact.rmdir()

        if os.name != "nt":
            dangling_root = tmp_path / "dangling-artifact-targets"
            dangling_root.mkdir()
            for backend, flag, suffix in (
                ("LLVM", "--llvm", ".ll"),
                ("C", "--c", ".c"),
            ):
                dangling_artifact = Path(str(blocked_cleanup) + suffix)
                outside_target = dangling_root / f"outside-{backend.lower()}{suffix}"
                dangling_artifact.symlink_to(outside_target)
                dangling_result = run(
                    freak, repo, blocked_cleanup, "transpile", flag, timeout=10
                )
                dangling_output = dangling_result.stdout + dangling_result.stderr
                assert dangling_result.returncode == 0, dangling_output
                assert not dangling_artifact.is_symlink(), dangling_artifact
                assert dangling_artifact.is_file(), dangling_artifact
                assert not outside_target.exists(), outside_target
                dangling_artifact.unlink()

                if direct_compiler is not None:
                    dangling_artifact.symlink_to(outside_target)
                    direct_dangling = run_direct_compiler(
                        direct_compiler,
                        repo,
                        str(blocked_cleanup),
                        flag,
                    )
                    direct_output = direct_dangling.stdout + direct_dangling.stderr
                    assert direct_dangling.returncode == 0, direct_output
                    assert not dangling_artifact.is_symlink(), dangling_artifact
                    assert dangling_artifact.is_file(), dangling_artifact
                    assert not outside_target.exists(), outside_target
                    dangling_artifact.unlink()

            protected_root = tmp_path / "protected-dangling-artifacts"
            protected_root.mkdir()
            protected_source = protected_root / "protected.fk"
            protected_source.write_text('say "never redirected"\n', encoding="utf-8")
            for backend, flag, suffix in (
                ("LLVM", "--llvm", ".ll"),
                ("C", "--c", ".c"),
            ):
                protected_artifact = Path(str(protected_source) + suffix)
                outside_target = dangling_root / f"protected-{backend.lower()}{suffix}"
                protected_artifact.symlink_to(outside_target)
                protected_root.chmod(0o500)
                try:
                    protected_result = run(
                        freak, repo, protected_source, "transpile", flag, timeout=10
                    )
                    protected_output = protected_result.stdout + protected_result.stderr
                    assert protected_result.returncode != 0, protected_output
                    assert "untrusted stale artifact" in protected_output.lower()
                    assert protected_artifact.is_symlink(), protected_artifact
                    assert not outside_target.exists(), outside_target

                    if direct_compiler is not None:
                        direct_protected = run_direct_compiler(
                            direct_compiler,
                            repo,
                            str(protected_source),
                            flag,
                        )
                        direct_output = direct_protected.stdout + direct_protected.stderr
                        assert direct_protected.returncode != 0, direct_output
                        assert "untrusted stale artifact" in direct_output.lower()
                        assert protected_artifact.is_symlink(), protected_artifact
                        assert not outside_target.exists(), outside_target
                finally:
                    protected_root.chmod(0o700)
                    protected_artifact.unlink(missing_ok=True)

        blocked_binary = derived_binary(blocked_cleanup)
        blocked_binary.mkdir()
        blocked_binary_result = run(
            freak, repo, blocked_cleanup, "build", "--c", timeout=10
        )
        blocked_binary_output = (
            blocked_binary_result.stdout + blocked_binary_result.stderr
        )
        assert blocked_binary_result.returncode != 0, blocked_binary_output
        assert "untrusted stale artifact" in blocked_binary_output.lower()
        assert blocked_binary.is_dir(), blocked_binary
        blocked_binary.rmdir()

        blocked_cache = run_cache(blocked_binary)
        blocked_cache.mkdir()
        blocked_cache_result = run(
            freak, repo, blocked_cleanup, "build", "--c", timeout=10
        )
        blocked_cache_output = blocked_cache_result.stdout + blocked_cache_result.stderr
        assert blocked_cache_result.returncode != 0, blocked_cache_output
        assert "untrusted stale artifact" in blocked_cache_output.lower()
        assert blocked_cache.is_dir(), blocked_cache
        blocked_cache.rmdir()

        if direct_compiler is not None:
            blocked_direct = Path(str(blocked_cleanup) + ".c")
            blocked_direct.mkdir()
            direct_blocked_result = run_direct_compiler(
                direct_compiler, repo, str(blocked_cleanup), "--c"
            )
            direct_blocked_output = (
                direct_blocked_result.stdout + direct_blocked_result.stderr
            )
            assert direct_blocked_result.returncode != 0, direct_blocked_output
            assert "untrusted stale artifact" in direct_blocked_output.lower()
            assert blocked_direct.is_dir(), blocked_direct
            blocked_direct.rmdir()

        abi_source = tmp_path / "preflight_abi_failure.fk"
        abi_source.write_text('say "never compiled"\n', encoding="utf-8")
        abi_binary = derived_binary(abi_source)
        abi_cache = run_cache(abi_binary)
        bad_home = tmp_path / "preflight-bad-abi-home"
        (bad_home / "runtime").mkdir(parents=True)
        (bad_home / "std").mkdir()
        (bad_home / "runtime" / "freak_abi").write_text(
            "freak-v3-abi-stale\n", encoding="utf-8"
        )
        (bad_home / "std" / "freak_abi").write_text(
            "freak-v3-abi-stale\n", encoding="utf-8"
        )
        bad_abi_env = os.environ.copy()
        bad_abi_env["FREAK_HOME"] = str(bad_home)
        for backend, flag, suffix in (
            ("LLVM", "--llvm", ".ll"),
            ("C", "--c", ".c"),
        ):
            artifact = Path(str(abi_source) + suffix)
            seed_stale_outputs(artifact, abi_binary, abi_cache)
            rejected = run(
                freak, repo, abi_source, "build", flag, env=bad_abi_env, timeout=10
            )
            output = rejected.stdout + rejected.stderr
            assert rejected.returncode != 0, output
            assert "abi mismatch" in output.lower(), output
            assert_outputs_absent(
                (artifact, abi_binary, abi_cache),
                f"{backend} preflight ABI failure",
            )

        non_fk_source = tmp_path / "non_fk_source_must_survive"
        non_fk_text = "say )\n"
        non_fk_source.write_text(non_fk_text, encoding="utf-8")
        for backend, flag, suffix in (
            ("LLVM", "--llvm", ".ll"),
            ("C", "--c", ".c"),
        ):
            artifact = Path(str(non_fk_source) + suffix)
            seed_stale_outputs(artifact)
            rejected = run(
                freak, repo, non_fk_source, "build", flag, timeout=10
            )
            output = rejected.stdout + rejected.stderr
            assert rejected.returncode != 0, output
            assert "source path must end in .fk" in output.lower(), output
            assert non_fk_source.read_text(encoding="utf-8") == non_fk_text
            assert_outputs_preserved((artifact,), f"{backend} non-.fk neighbor")

            if direct_compiler is not None:
                direct_non_fk = run_direct_compiler(
                    direct_compiler, repo, str(non_fk_source), flag
                )
                direct_non_fk_output = direct_non_fk.stdout + direct_non_fk.stderr
                assert direct_non_fk.returncode != 0, direct_non_fk_output
                assert "source path must end in .fk" in direct_non_fk_output.lower()
                assert_outputs_preserved(
                    (artifact,), f"direct {backend} non-.fk neighbor"
                )

        scale_source = tmp_path / "callable_index_scale.fk"
        scale_source.write_text(
            "\n".join(
                [f"task helper_{index}() -> int {{ give back {index} }}" for index in range(600)]
                + ["task main() { say helper_599().to_word() }"]
            )
            + "\n",
            encoding="utf-8",
        )
        scale_check = run(freak, repo, scale_source, "check")
        assert scale_check.returncode == 0, scale_check.stdout + scale_check.stderr

        global_scale_source = tmp_path / "prior_global_alias_scale.fk"
        global_scale_source.write_text(
            "\n".join(
                ["pilot alias_127: num = 1.5"]
                + [
                    f"pilot alias_{index} = alias_{index + 1}"
                    for index in range(126, -1, -1)
                ]
                + [
                    "task consume_num(value: num) { say value }",
                    "task main() { consume_num(alias_0) }",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        global_scale_check = run(freak, repo, global_scale_source, "check")
        assert global_scale_check.returncode == 0, (
            global_scale_check.stdout + global_scale_check.stderr
        )

        dependency_scale_source = tmp_path / "global_callable_dependency_scale.fk"
        dependency_scale_source.write_text(
            "\n".join(
                [
                    "pilot dependency_base: int = 7",
                    "pilot dependency_result: int = dependency_0()",
                ]
                + [
                    f"task dependency_{index}() -> int {{ give back dependency_{index + 1}() }}"
                    for index in range(127)
                ]
                + [
                    "task dependency_127() -> int { give back dependency_base }",
                    "task main() { say dependency_result }",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        dependency_scale_check = run(
            freak, repo, dependency_scale_source, "check", timeout=30
        )
        assert dependency_scale_check.returncode == 0, (
            dependency_scale_check.stdout + dependency_scale_check.stderr
        )

        assert_bound_diagnostic_source_labels(freak, repo, tmp_path)
        assert_bound_declaration_namespaces(freak, repo, tmp_path, private_fixture)
        assert_generated_package_identity_access(freak, repo, tmp_path, private_fixture)
        assert_fixed_value_namespace_collisions(freak, direct_compiler, repo, tmp_path)
        assert_local_value_call_shadowing(freak, direct_compiler, repo, tmp_path)
        assert_bound_source_reservations(freak, direct_compiler, repo, tmp_path)
        assert_bound_lexical_error_counts(freak, direct_compiler, repo, tmp_path, private_fixture)
        assert_public_forward_shape_constructor(freak, repo, tmp_path)

        # This matrix proves checker acceptance only. Some of these contracts
        # (mixed numeric lowering, num/word when equality, and int-returning
        # main ABI) have backend-specific executable coverage in their owning
        # emitter regressions; this gate makes sure the semantic pass does not
        # overreject them while still exercising both emission front doors.
        semantic_positive = tmp_path / "semantic_positive_matrix.fk"
        semantic_positive.write_text(
            "shape Meter { value: num }\n"
            "shape Marker {}\n"
            "impl Marker {}\n"
            "impl Meter {\n"
            "    task from_value(value: num) -> Meter { give back Meter { value: value } }\n"
            "    task add(self, delta: num) -> num { give back self.value + delta }\n"
            "}\n"
            "pilot global_associated_meter = Meter::from_value(1)\n"
            "pilot global_instance_num: num = global_associated_meter.add(1)\n"
            "extern task external_num(value: num) -> num\n"
            "pilot top_num: num = 1\n"
            "pilot prior_target: num = 1.5\n"
            "pilot prior_alias = prior_target\n"
            "pilot dependency_base: int = 7\n"
            "pilot dependency_earlier: int = read_dependency_base()\n"
            "pilot dependency_pure: int = pure_increment(1)\n"
            "pilot dependency_shadowed: int = use_shadowed_later(3)\n"
            "pilot later_shadowed_global: int = 7\n"
            "pilot namespace_overlap: int = 7\n"
            "task main() -> int {\n"
            "    say \"entry execution remains valid\"\n"
            "    pilot mut widened: num = 1\n"
            "    widened = 2\n"
            "    pilot sum: num = 1 + 2.5\n"
            "    pilot comparison: bool = 1 < 2.5\n"
            "    pilot joined: word = \"na\" + \"kama\"\n"
            "    pilot truth_yes: bool = yes\n"
            "    pilot truth_hai: bool = hai\n"
            "    pilot false_no: bool = no\n"
            "    pilot false_iie: bool = iie\n"
            "    if truth_yes and truth_hai and not false_no and not false_iie { say joined }\n"
            "    pilot mut meter = Meter { value: 1 }\n"
            "    pilot associated_meter = Meter::from_value(1)\n"
            "    meter.value = 2\n"
            "    pilot method_num: num = meter.add(1)\n"
            "    pilot associated_num: num = associated_meter.add(1)\n"
            "    pilot forward_num: num = 1 |> later_num()\n"
            "    pilot extern_num: num = external_num(1)\n"
            "    pilot alias_num: num = later_num(prior_alias)\n"
            "    say dependency_earlier + dependency_pure\n"
            "    pilot shadowed: int = 1\n"
            "    if true {\n"
            "        pilot shadowed: int = 2\n"
            "        say shadowed\n"
            "    }\n"
            "    say shadowed\n"
            "    pilot signed_int: int = -1\n"
            "    when signed_int {\n"
            "        -1 -> say signed_int\n"
            "        _ -> say namespace_overlap\n"
            "    }\n"
            "    pilot signed_num: num = -1.5\n"
            "    when signed_num {\n"
            "        -1.5 -> say alias_num\n"
            "        _ -> say namespace_overlap()\n"
            "    }\n"
            "    when widened {\n"
            "        1 -> say comparison\n"
            "        2.5 -> say method_num\n"
            "        _ -> say extern_num\n"
            "    }\n"
            "    when joined {\n"
            "        \"nakama\" -> say joined\n"
            "        _ -> say \"other\"\n"
            "    }\n"
            "    give back 0\n"
            "}\n"
            "task later_num(value: num) -> num { give back 1 }\n"
            "task read_dependency_base() -> int { give back dependency_base }\n"
            "task pure_increment(value: int) -> int { give back value + 1 }\n"
            "task use_shadowed_later(later_shadowed_global: int) -> int { give back later_shadowed_global }\n"
            "task namespace_overlap() -> int { give back 8 }\n",
            encoding="utf-8",
        )
        semantic_check = run(freak, repo, semantic_positive, "check")
        assert semantic_check.returncode == 0, (
            semantic_check.stdout + semantic_check.stderr
        )
        for backend, flag, suffix in (
            ("LLVM", "--llvm", ".ll"),
            ("C", "--c", ".c"),
        ):
            semantic_transpile = run(
                freak, repo, semantic_positive, "transpile", flag
            )
            assert semantic_transpile.returncode == 0, (
                f"{backend} semantic positive transpile failed\n"
                + semantic_transpile.stdout
                + semantic_transpile.stderr
            )
            assert Path(str(semantic_positive) + suffix).is_file()
            if direct_compiler is not None:
                direct_semantic = run_direct_compiler(
                    direct_compiler, repo, str(semantic_positive), flag
                )
                assert direct_semantic.returncode == 0, (
                    f"direct {backend} semantic positive transpile failed\n"
                    + direct_semantic.stdout
                    + direct_semantic.stderr
                )

        internal_collision = tmp_path / "internal_checked_delete_collision.fk"
        collision_sentinel = tmp_path / "internal-bridge-must-not-delete.txt"
        collision_path = str(collision_sentinel).replace("\\", "/")
        internal_collision.write_text(
            "task freak_internal_delete_file_checked(path: word) -> bool { give back false }\n"
            "task main() {\n"
            f'    if freak_internal_delete_file_checked("{collision_path}") {{\n'
            '        say "runtime bridge called"\n'
            "    } else {\n"
            '        say "user task called"\n'
            "    }\n"
            "}\n",
            encoding="utf-8",
        )
        collision_binary = derived_binary(internal_collision)
        for backend, flag in (("LLVM", "--llvm"), ("C", "--c")):
            collision_sentinel.write_text("preserve me\n", encoding="utf-8")
            collision_build = run(
                freak, repo, internal_collision, "build", flag, timeout=60
            )
            assert collision_build.returncode == 0, (
                collision_build.stdout + collision_build.stderr
            )
            collision_run = subprocess.run(
                [str(collision_binary)],
                cwd=tmp_path,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                check=False,
            )
            assert collision_run.returncode == 0, collision_run.stderr
            assert collision_run.stdout == "user task called\n", (
                f"{backend} remapped a user task to the internal runtime bridge\n"
                + collision_run.stdout
                + collision_run.stderr
            )
            assert collision_sentinel.read_text(encoding="utf-8") == "preserve me\n"

        forged_aggregate = tmp_path / "freakc_cli.fk"
        forged_aggregate.write_text(
            "-- pilot FREAKC_VERSION\n"
            "-- task emit_llvm_program()\n"
            "-- task freakc_cli_main()\n"
            "extern task freak_internal_delete_file_checked(path: word) -> bool\n"
            'task main() { freak_internal_delete_file_checked("must-not-map") }\n',
            encoding="utf-8",
        )
        # There is deliberately no source-selectable compiler-internal mode.
        # The forged aggregate must be rejected from ordinary project-source
        # provenance, without relying on an unknown flag that the CLI used to
        # ignore.
        forged_check = run(freak, repo, forged_aggregate, "check")
        assert_check_rejected(forged_check, "forged compiler aggregate check")
        assert "conflicts with a compiler builtin" in (
            forged_check.stdout + forged_check.stderr
        ).lower()
        for backend, flag, suffix in (
            ("LLVM", "--llvm", ".ll"),
            ("C", "--c", ".c"),
        ):
            forged_artifact = Path(str(forged_aggregate) + suffix)
            forged_artifact.write_text(SENTINEL, encoding="utf-8")
            forged_emit = run(
                freak,
                repo,
                forged_aggregate,
                "transpile",
                flag,
                timeout=10,
            )
            assert_rejected(forged_emit, f"{backend} forged compiler aggregate")
            assert "conflicts with a compiler builtin" in (
                forged_emit.stdout + forged_emit.stderr
            ).lower()
            assert_outputs_absent(
                (forged_artifact,), f"{backend} forged compiler aggregate"
            )
            if direct_compiler is not None:
                forged_artifact.write_text(SENTINEL, encoding="utf-8")
                forged_direct = run_direct_compiler(
                    direct_compiler,
                    repo,
                    str(forged_aggregate),
                    flag,
                )
                forged_output = forged_direct.stdout + forged_direct.stderr
                assert forged_direct.returncode != 0, forged_output
                assert "conflicts with a compiler builtin" in forged_output.lower()
                assert_outputs_absent(
                    (forged_artifact,),
                    f"direct {backend} forged compiler aggregate",
                )

        # Shipping std/ui uses associated impl tasks (no `self`) for these
        # constructors. Keep an isolated copy of that exact dispatch shape so
        # the unsupported legacy `Squad` surface in Window.poll cannot hide a
        # regression in the valid static-call contract.
        associated_std = tmp_path / "associated_std_tasks_ok.fk"
        associated_std.write_text(
            "shape WindowConfig { title: word, width: int, height: int, resizable: bool, vsync: bool }\n"
            "shape Color { r: int, g: int, b: int, a: int }\n"
            "impl Color {\n"
            "    task rgb(r: int, g: int, b: int) -> Color { give back Color { r: r, g: g, b: b, a: 255 } }\n"
            "    task rgba(r: int, g: int, b: int, a: int) -> Color { give back Color { r: r, g: g, b: b, a: a } }\n"
            "    task red() -> Color { give back Color::rgb(255, 45, 45) }\n"
            "}\n"
            "shape Font { size: int, bold: bool, italic: bool }\n"
            "impl Font { task default() -> Font { give back Font { size: 14, bold: false, italic: false } } }\n"
            "shape Window { handle: int, width: int, height: int }\n"
            "impl Window {\n"
            "    task open(config: WindowConfig) -> Window {\n"
            "        pilot resizable = 1\n"
            "        if not config.resizable { resizable = 0 }\n"
            "        pilot h = ui::create_window(config.title, config.width, config.height, resizable)\n"
            "        give back Window { handle: h, width: config.width, height: config.height }\n"
            "    }\n"
            "}\n"
            "shape Canvas { handle: int }\n"
            "impl Canvas { task from_window(win: Window) -> Canvas { give back Canvas { handle: win.handle } } }\n"
            "task main() {\n"
            "    pilot color = Color::red()\n"
            "    pilot rgba = Color::rgba(color.r, color.g, color.b, color.a)\n"
            "    pilot font = Font::default()\n"
            "    pilot config = WindowConfig { title: \"FREAK\", width: 640, height: 480, resizable: true, vsync: true }\n"
            "    pilot window = Window::open(config)\n"
            "    pilot canvas = Canvas::from_window(window)\n"
            "    say font.size\n"
            "    say rgba.a\n"
            "    say canvas.handle\n"
            "}\n",
            encoding="utf-8",
        )
        associated_check = run(freak, repo, associated_std, "check")
        assert associated_check.returncode == 0, (
            associated_check.stdout + associated_check.stderr
        )
        for backend, flag, suffix in (
            ("LLVM", "--llvm", ".ll"),
            ("C", "--c", ".c"),
        ):
            associated_emit = run(freak, repo, associated_std, "transpile", flag)
            assert associated_emit.returncode == 0, (
                associated_emit.stdout + associated_emit.stderr
            )
            generated = Path(str(associated_std) + suffix).read_text(encoding="utf-8")
            for symbol in (
                "Color_rgb",
                "Color_rgba",
                "Color_red",
                "Font_default",
                "Window_open",
                "Canvas_from_window",
            ):
                assert symbol in generated, f"{backend} lost associated symbol {symbol}"
            if direct_compiler is not None:
                direct_associated = run_direct_compiler(
                    direct_compiler, repo, str(associated_std), flag
                )
                assert direct_associated.returncode == 0, (
                    direct_associated.stdout + direct_associated.stderr
                )

        nominal_bad = tmp_path / "nominal_bad.fk"
        nominal_bad.write_text(
            "shape Known { value: int }\n"
            "shape Other { value: int }\n"
            "impl Other { task not_a_method(self) { say \"wrong impl\" } }\n"
            "pilot known = Known { value: 7 }\n"
            "task main() {\n"
            "    pilot missing = known.not_a_field\n"
            "    known.not_a_method()\n"
            "}\n",
            encoding="utf-8",
        )
        for backend, flag, suffix in (("LLVM", "--llvm", ".ll"), ("C", "--c", ".c")):
            nominal_artifact = Path(str(nominal_bad) + suffix)
            nominal_artifact.write_text(SENTINEL, encoding="utf-8")
            nominal_result = run(freak, repo, nominal_bad, "transpile", flag)
            assert_rejected(nominal_result, f"{backend} nominal member gate")
            nominal_output = nominal_result.stdout + nominal_result.stderr
            assert "has no field 'not_a_field'" in nominal_output
            assert "has no method 'not_a_method'" in nominal_output
            assert "nominal_bad.fk:6:1" in nominal_output
            assert "nominal_bad.fk:7:1" in nominal_output
            assert "6 |     pilot missing = known.not_a_field" in nominal_output
            assert "7 |     known.not_a_method()" in nominal_output
            assert_outputs_absent(
                (nominal_artifact,), f"{backend} nominal member transpile"
            )

            nominal_binary = derived_binary(nominal_bad)
            nominal_cache = run_cache(nominal_binary)
            seed_stale_outputs(nominal_artifact, nominal_binary, nominal_cache)
            nominal_build = run(freak, repo, nominal_bad, "build", flag)
            assert_rejected(nominal_build, f"{backend} nominal member build gate")
            assert_outputs_absent(
                (nominal_artifact, nominal_binary, nominal_cache),
                f"{backend} nominal member build",
            )

        nested_nominal_bad = tmp_path / "nested_nominal_bad.fk"
        nested_nominal_bad.write_text(
            "shape Known { value: int }\n"
            "impl Known { task again(self) -> Known { give back self } }\n"
            "pilot known = Known { value: 7 }\n"
            "extern task imported() -> Known\n"
            "task Known_spoof() { say \"not an impl\" }\n"
            "pilot shadowed = Known { value: 8 }\n"
            "task shadow_param(shadowed: int) { say shadowed.value shadowed.not_primitive() }\n"
            "task main() {\n"
            "    when known.missing_when_target {\n"
            "        known.missing_when_case -> say known.missing_when_body\n"
            "        _ -> say \"fallback\"\n"
            "    }\n"
            "    training arc until false max known.missing_max sessions { break }\n"
            "    say known.again().missing_chain\n"
            "    say imported().missing_extern\n"
            "    known.spoof()\n"
            "    shadow_param(7)\n"
            "    pilot primitive: int = 7\n"
            "    say primitive.trim()\n"
            "    say \"x\".trim(1)\n"
            "    say word_from_int(1).not_call_method()\n"
            "    say (1 + 2).missing_expr_field\n"
            "    say (\"a\" + \"b\").not_expr_method()\n"
            "    when known.value {\n"
            "        known.missing_multiline\n"
            "        ->\n"
            "        say \"case\"\n"
            "    }\n"
            "}\n",
            encoding="utf-8",
        )
        for backend, flag, suffix in (("LLVM", "--llvm", ".ll"), ("C", "--c", ".c")):
            artifact = Path(str(nested_nominal_bad) + suffix)
            artifact.write_text(SENTINEL, encoding="utf-8")
            result = run(freak, repo, nested_nominal_bad, "transpile", flag)
            assert_rejected(result, f"{backend} nested nominal traversal gate")
            output = result.stdout + result.stderr
            for member in (
                "missing_when_target",
                "missing_when_case",
                "missing_when_body",
                "missing_max",
                "missing_chain",
                "missing_extern",
            ):
                assert member in output, f"{backend}: did not validate {member}\n{output}"
            assert "has no method 'spoof'" in output
            assert "non-shape value has no fields" in output
            assert "non-shape value has no method 'not_primitive'" in output
            assert "non-shape value has no method 'trim'" in output
            assert "method 'trim' expects 0 argument(s), got 1" in output
            assert "non-shape value has no method 'not_call_method'" in output
            assert "non-shape value has no method 'not_expr_method'" in output
            assert "missing_expr_field" in output
            assert "nested_nominal_bad.fk:9:1" in output
            assert "nested_nominal_bad.fk:10:1" in output
            assert "10 |         known.missing_when_case -> say known.missing_when_body" in output
            assert "nested_nominal_bad.fk:13:1" in output
            assert "nested_nominal_bad.fk:25:1" in output
            assert "25 |         known.missing_multiline" in output
            assert_outputs_absent(
                (artifact,), f"{backend} nested nominal traversal transpile"
            )

        install_home = tmp_path / "malformed-stdlib-home"
        shutil.copytree(repo / "freakc" / "runtime", install_home / "runtime")
        shutil.copytree(repo / "std", install_home / "std")
        broken_math = install_home / "std" / "math.fk"
        broken_math.write_text(
            "task broken_std() {\n    say )\n}\n", encoding="utf-8"
        )
        std_user = tmp_path / "malformed_std_user.fk"
        std_user.write_text('task main() {\n    say "user"\n}\n', encoding="utf-8")
        std_env = os.environ.copy()
        std_env["FREAK_HOME"] = str(install_home)
        std_result = run(freak, repo, std_user, "build", "--c", env=std_env)
        assert_rejected(std_result, "malformed installed std source origin")
        std_output = (std_result.stdout + std_result.stderr).replace("\\", "/")
        assert "malformed-stdlib-home/std/math.fk:2:" in std_output, std_output
        assert "2 |     say )" in std_output, std_output

        broken_math.write_text(
            (repo / "std" / "math.fk").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        broken_version = install_home / "std" / "version.fk"
        broken_version.write_text("task broken_std() {\n", encoding="utf-8")
        std_user.write_text('say "user"\n', encoding="utf-8")
        unclosed_result = run(freak, repo, std_user, "build", "--c", env=std_env)
        assert_rejected(unclosed_result, "unclosed installed std block origin")
        unclosed_output = (unclosed_result.stdout + unclosed_result.stderr).replace(
            "\\", "/"
        )
        assert "malformed-stdlib-home/std/version.fk:1:" in unclosed_output
        assert "1 | task broken_std() {" in unclosed_output

        broken_version.write_text(
            "task broken_std() { say helper(", encoding="utf-8"
        )
        std_user.write_text("-- user source remains intentionally token-free\n", encoding="utf-8")
        delimiter_result = run(freak, repo, std_user, "build", "--c", env=std_env)
        assert_rejected(delimiter_result, "installed std delimiter opener origin")
        delimiter_output = (
            delimiter_result.stdout + delimiter_result.stderr
        ).replace("\\", "/")
        assert "unexpected end of file inside call argument list" in delimiter_output
        assert "malformed-stdlib-home/std/version.fk:1:" in delimiter_output
        assert "1 | task broken_std() { say helper(" in delimiter_output

        nominal_shadow_ok = tmp_path / "nominal_shadow_ok.fk"
        nominal_shadow_ok.write_text(
            "shape Known { value: int }\n"
            "pilot shadowed: int = 7\n"
            "task previous(shadowed: Known) { say shadowed.value }\n"
            "task read_global() { say shadowed.to_word() }\n"
            "task by_param(shadowed: int) { say shadowed.to_word() }\n"
            "task main() {\n"
            "    read_global()\n"
            "    pilot shadowed: int = 9\n"
            "    say shadowed.to_word()\n"
            "    by_param(shadowed)\n"
            "}\n",
            encoding="utf-8",
        )
        shadow_check = run(freak, repo, nominal_shadow_ok, "check")
        assert shadow_check.returncode == 0, shadow_check.stdout + shadow_check.stderr

        reserved_extern = tmp_path / "reserved_extern_bad.fk"
        reserved_extern.write_text(
            "extern task __freak_param_0(value: int) -> int\n"
            "task main() { say __freak_param_0(7) }\n",
            encoding="utf-8",
        )
        for backend, flag in (("LLVM", "--llvm"), ("C", "--c")):
            reserved_result = run(freak, repo, reserved_extern, "transpile", flag)
            assert_rejected(reserved_result, f"{backend} reserved extern namespace")
            assert "compiler-reserved '__freak_' prefix" in (
                reserved_result.stdout + reserved_result.stderr
            )

        builtin_task = tmp_path / "builtin_task_bad.fk"
        builtin_task.write_text(
            "task word_concat(a: word, b: word) -> word { give back a }\n"
            "task main() { say word_concat(\"a\", \"b\") }\n",
            encoding="utf-8",
        )
        for backend, flag in (("LLVM", "--llvm"), ("C", "--c")):
            builtin_task_result = run(freak, repo, builtin_task, "transpile", flag)
            assert_rejected(builtin_task_result, f"{backend} builtin task collision")
            assert "conflicts with a compiler builtin" in (
                builtin_task_result.stdout + builtin_task_result.stderr
            )

        spoofed_runtime = tmp_path / "spoof-project" / "std" / "runtime.fk"
        spoofed_runtime.parent.mkdir(parents=True)
        spoofed_runtime.write_text(
            "task llvm_fs_read(path: word) -> word { give back path }\n"
            "task main() { say \"spoof\" }\n",
            encoding="utf-8",
        )
        for backend, flag in (("LLVM", "--llvm"), ("C", "--c")):
            spoof_result = run(freak, repo, spoofed_runtime, "transpile", flag)
            assert_rejected(spoof_result, f"{backend} spoofed std runtime source")
            assert "conflicts with a compiler builtin" in (
                spoof_result.stdout + spoof_result.stderr
            )

        impl_collision = tmp_path / "impl_task_collision.fk"
        impl_collision.write_text(
            "shape Box { value: int }\n"
            "task Box_ping(value: int) -> int { give back value }\n"
            "impl Box { task ping(self) -> int { give back self.value } }\n"
            "task main() { pilot box = Box { value: 7 } say box.ping() }\n",
            encoding="utf-8",
        )
        for backend, flag in (("LLVM", "--llvm"), ("C", "--c")):
            collision_result = run(freak, repo, impl_collision, "transpile", flag)
            assert_rejected(collision_result, f"{backend} impl task lowering collision")
            assert "conflicts with another task or extern declaration" in (
                collision_result.stdout + collision_result.stderr
            )

        callable_collisions = (
            "extern task helper(value: int) -> int\n"
            "task helper(value: int) -> int { give back value }\n"
            "task main() { say helper(7).to_word() }\n",
            "extern task helper(value: int) -> int\n"
            "extern task helper(value: int) -> int\n"
            "task main() { say helper(7).to_word() }\n",
        )
        for collision_index, collision_source in enumerate(callable_collisions):
            collision_file = tmp_path / f"callable_collision_{collision_index}.fk"
            collision_file.write_text(collision_source, encoding="utf-8")
            for backend, flag in (("LLVM", "--llvm"), ("C", "--c")):
                callable_result = run(
                    freak, repo, collision_file, "transpile", flag
                )
                assert_rejected(
                    callable_result, f"{backend} task/extern collision"
                )
                assert "conflicts with another task or extern declaration" in (
                    callable_result.stdout + callable_result.stderr
                )

        extern_builtin = tmp_path / "extern_builtin_collision.fk"
        extern_builtin.write_text(
            "extern task word_concat(value: int) -> int\n"
            "task main() { say word_concat(7).to_word() }\n",
            encoding="utf-8",
        )
        for backend, flag in (("LLVM", "--llvm"), ("C", "--c")):
            extern_builtin_result = run(
                freak, repo, extern_builtin, "transpile", flag
            )
            assert_rejected(
                extern_builtin_result, f"{backend} extern/builtin collision"
            )
            assert "conflicts with a compiler builtin" in (
                extern_builtin_result.stdout + extern_builtin_result.stderr
            )

        process_args_bad = tmp_path / "process_args_v3_bad.fk"
        process_args_bad.write_text(
            "task main() { pilot values = process::args() say values }\n",
            encoding="utf-8",
        )
        for backend, flag in (("LLVM", "--llvm"), ("C", "--c")):
            process_args_result = run(
                freak, repo, process_args_bad, "transpile", flag
            )
            assert_rejected(
                process_args_result, f"{backend} process::args V3 ABI gate"
            )
            process_args_output = (
                process_args_result.stdout + process_args_result.stderr
            )
            assert "process::args() has no List<word> ABI in V3" in process_args_output
            assert "process::args_count()" in process_args_output
            assert "process::arg(index)" in process_args_output

        primitive_ok = tmp_path / "primitive_methods_ok.fk"
        primitive_ok.write_text(
            "pilot inferred_global = 1.5 + 2.25\n"
            "pilot __freak_param_0: int = 42\n"
            "task truth_result() -> bool { give back true }\n"
            "task decimal_result() -> num { give back 6.75 }\n"
            "task read_collision(other: int) -> int { give back __freak_param_0 }\n"
            "task main() {\n"
            "    pilot integer: int = 7\n"
            "    say integer.to_word()\n"
            "    pilot decimal: num = 8.0\n"
            "    pilot decimal_int: int = decimal.to_int()\n"
            "    say decimal_int.to_word()\n"
            "    pilot truth: bool = true\n"
            "    say truth.to_word()\n"
            "    pilot text: word = \"9\"\n"
            "    pilot text_int: int = text.to_int()\n"
            "    say text_int.to_word()\n"
            "    pilot source_integer = 7\n"
            "    pilot inferred_num = source_integer.to_num()\n"
            "    say inferred_num.to_word()\n"
            "    pilot inferred_sum = 1.5 + 2.25\n"
            "    say inferred_sum.to_word()\n"
            "    pilot inferred_checksum = \"a\".checksum()\n"
            "    say (inferred_checksum > 0).to_word()\n"
            "    say (1 < 2).to_word()\n"
            "    say \"x\".contains(\"x\").to_word()\n"
            "    say truth_result().to_word()\n"
            "    say decimal_result().to_int().to_word()\n"
            "    say fs::exists(\"definitely-missing-v3-type-probe\").to_word()\n"
            "    say math::sqrt(9.0).to_int().to_word()\n"
            "    say inferred_global.to_word()\n"
            "    say read_collision(7).to_word()\n"
            "    say (source_integer.to_num() + 1.5).to_word()\n"
            "    say (\"a\".checksum() == \"a\".checksum()).to_word()\n"
            "    say \"abc\".replace(\"a\", \"z\")\n"
            "    say word_concat(\"a\", \"b\")\n"
            "    say (time::now_ms() >= 0).to_word()\n"
            "    if false { panic(\"not reached\") }\n"
            "}\n",
            encoding="utf-8",
        )
        for backend, flag in (("LLVM", "--llvm"), ("C", "--c")):
            built = run(freak, repo, primitive_ok, "build", flag)
            assert built.returncode == 0, f"{backend} primitive build failed\n{built.stdout}{built.stderr}"
            binary = primitive_ok.with_suffix(".exe" if sys.platform == "win32" else "")
            executed = subprocess.run(
                [str(binary)],
                cwd=tmp_path,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
                check=False,
            )
            assert executed.returncode == 0, executed.stdout + executed.stderr
            expected_output = [
                "7",
                "8",
                "true",
                "9",
                "7",
                "3.75",
                "true",
                "true",
                "true",
                "true",
                "6",
                "false",
                "3",
                "3.75",
                "42",
                "8.5",
                "true",
                "zbc",
                "ab",
                "true",
            ]
            actual_output = executed.stdout.strip().splitlines()
            assert actual_output == expected_output, (
                f"{backend} primitive execution mismatch\n"
                f"expected: {expected_output!r}\nactual: {actual_output!r}\n"
                f"stderr: {executed.stderr}"
            )
            if backend == "C":
                generated_c = primitive_ok.with_suffix(".fk.c").read_text(
                    encoding="utf-8"
                )
                assert "freak_time_now_ms()" in generated_c
                assert "freak_panic(" in generated_c
                assert "__freak_user_time_now_ms" not in generated_c
                assert "__freak_user_panic" not in generated_c

        builtin_marker = tmp_path / "builtin-wrapper-marker.txt"
        builtin_marker.write_text("marker", encoding="utf-8")
        builtin_deletable = tmp_path / "builtin-wrapper-deletable.txt"
        builtin_directory = tmp_path / "builtin-wrapper-directory"
        builtin_wrappers = tmp_path / "builtin_wrappers.fk"
        builtin_wrappers.write_text(
            "task main() {\n"
            "    pilot mut env_value: word = process::env(\"FREAK_BUILTIN_PROBE\")\n"
            "    say env_value\n"
            "    env_value = \"released\"\n"
            f"    pilot mut listing: word = fs::list_dir(\"{tmp_path.as_posix()}\")\n"
            "    say listing.contains(\"builtin-wrapper-marker.txt\").to_word()\n"
            "    listing = \"released\"\n"
            "    pilot mut letter: word = char_to_word(65)\n"
            "    say letter\n"
            "    letter = \"released\"\n"
            f"    say fs::exists(\"{builtin_marker.as_posix()}\").to_word()\n"
            f"    say fs::exists(\"{(tmp_path / 'builtin-wrapper-missing').as_posix()}\").to_word()\n"
            f"    fs::write(\"{builtin_deletable.as_posix()}\", \"delete me\")\n"
            f"    say fs::delete(\"{builtin_deletable.as_posix()}\").to_word()\n"
            f"    say fs::exists(\"{builtin_deletable.as_posix()}\").to_word()\n"
            f"    say fs::delete(\"{builtin_deletable.as_posix()}\").to_word()\n"
            f"    fs::make_dir(\"{builtin_directory.as_posix()}\")\n"
            f"    say fs::exists(\"{builtin_directory.as_posix()}\").to_word()\n"
            f"    fs::delete(\"{builtin_directory.as_posix()}\")\n"
            f"    say fs::exists(\"{builtin_directory.as_posix()}\").to_word()\n"
            "}\n",
            encoding="utf-8",
        )
        wrapper_env = os.environ.copy()
        wrapper_env["FREAK_BUILTIN_PROBE"] = "ok"
        for backend, flag in (("C", "--c"), ("LLVM", "--llvm")):
            wrapper_build = run(
                freak, repo, builtin_wrappers, "build", flag, env=wrapper_env
            )
            assert wrapper_build.returncode == 0, (
                wrapper_build.stdout + wrapper_build.stderr
            )
            wrapper_binary = builtin_wrappers.with_suffix(
                ".exe" if sys.platform == "win32" else ""
            )
            wrapper_run = subprocess.run(
                [str(wrapper_binary)],
                cwd=tmp_path,
                env=wrapper_env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
                check=False,
            )
            assert wrapper_run.returncode == 0, wrapper_run.stdout + wrapper_run.stderr
            wrapper_lines = wrapper_run.stdout.strip().splitlines()
            assert wrapper_lines == [
                "ok", "true", "A", "true", "false", "true", "false", "true", "true", "true"
            ], (
                f"{backend} builtin wrapper output mismatch: {wrapper_lines!r}\n"
                f"stderr: {wrapper_run.stderr}"
            )
            assert builtin_directory.is_dir()
            builtin_directory.rmdir()

        nominal_methods = tmp_path / "nominal_primitive_names.fk"
        nominal_methods.write_text(
            "shape PrimitiveNamed { value: int }\n"
            "shape NumberBox { pad: int value: int }\n"
            "shape WordBox { value: word pad: int }\n"
            "impl PrimitiveNamed {\n"
            "    task to_word(self) -> word { give back \"shape\" }\n"
            "    task length(self) -> int { give back 77 }\n"
            "    task trim(self) -> word { give back \"nominal\" }\n"
            "}\n"
            "task consume_number(value: int) -> int { give back value }\n"
            "task main() {\n"
            "    pilot named = PrimitiveNamed { value: 1 }\n"
            "    say named.to_word()\n"
            "    say named.length().to_word()\n"
            "    say named.trim()\n"
            "    pilot number = NumberBox { pad: 9, value: 7 }\n"
            "    say consume_number(number.value).to_word()\n"
            "}\n",
            encoding="utf-8",
        )
        nominal_llvm = run(freak, repo, nominal_methods, "build", "--llvm")
        assert nominal_llvm.returncode == 0, nominal_llvm.stdout + nominal_llvm.stderr
        nominal_binary = nominal_methods.with_suffix(".exe" if sys.platform == "win32" else "")
        nominal_executed = subprocess.run(
            [str(nominal_binary)],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            check=False,
        )
        assert nominal_executed.returncode == 0, nominal_executed.stdout + nominal_executed.stderr
        assert nominal_executed.stdout.strip().splitlines() == [
            "shape",
            "77",
            "nominal",
            "7",
        ]

        nominal_c = run(freak, repo, nominal_methods, "build", "--c")
        assert nominal_c.returncode == 0, nominal_c.stdout + nominal_c.stderr
        nominal_c_text = nominal_methods.with_suffix(".fk.c").read_text(encoding="utf-8")
        standalone_prefix = "pkg_" + hashlib.sha256(b"standalone\n@entry").hexdigest() + "_"
        method_symbol = "__freak_user_" + standalone_prefix + "PrimitiveNamed_to_word"
        number_symbol = "__freak_user_" + standalone_prefix + "consume_number"
        assert f"freak_word {method_symbol}(int64_t __freak_param_0)" in nominal_c_text
        assert f"freak_word __freak_result = {method_symbol}(__freak_call_arg_0);" in nominal_c_text
        assert f"int64_t __freak_result = {number_symbol}(__freak_call_arg_0);" in nominal_c_text
        assert "__freak_user_PrimitiveNamed_to_word(" not in nominal_c_text
        assert "__freak_user_consume_number(__freak_call_arg_0)" not in nominal_c_text
        assert "__freak_user_pkg_" + "0" * 64 + "_PrimitiveNamed_to_word(" not in nominal_c_text
        assert "int64_t __freak_index = 1;" in nominal_c_text
        assert "int64_t __freak_value = freak_v3_shape_get(__freak_recv, __freak_index)" in nominal_c_text
        assert "freak_word_clone(freak_v3_shape_get(" not in nominal_c_text
        nominal_c_executed = subprocess.run(
            [str(derived_binary(nominal_methods))], cwd=tmp_path,
            capture_output=True, text=True, timeout=30,
        )
        assert nominal_c_executed.returncode == 0, nominal_c_executed.stdout + nominal_c_executed.stderr
        assert nominal_c_executed.stdout.strip().splitlines() == ["shape", "77", "nominal", "7"]

        unknown_method_receiver = tmp_path / "unknown_receiver_method.fk"
        unknown_method_receiver.write_text(
            "shape Alpha { value: int }\n"
            "shape Beta { value: int }\n"
            "impl Ping for Alpha { task ping(self) {} }\n"
            "impl Ping for Beta { task ping(self) {} }\n"
            "task main() { missing_binding.ping() }\n",
            encoding="utf-8",
        )
        for backend, flag, suffix in (("C", "--c", ".c"), ("LLVM", "--llvm", ".ll")):
            artifact = Path(str(unknown_method_receiver) + suffix)
            artifact.write_text(SENTINEL, encoding="utf-8")
            rejected = run(freak, repo, unknown_method_receiver, "transpile", flag)
            assert_rejected(rejected, f"{backend} unknown method receiver gate")
            output = rejected.stdout + rejected.stderr
            assert "cannot resolve the receiver type for method 'ping'" in output
            assert_outputs_absent(
                (artifact,), f"{backend} unknown method receiver transpile"
            )

        doctrine_impls = tmp_path / "doctrine_impl_owners.fk"
        doctrine_impls.write_text(
            "shape Alpha { value: int }\n"
            "shape Beta { value: int }\n"
            "impl Labelled for Alpha {\n"
            "    task label(self) -> word { give back \"alpha\" }\n"
            "}\n"
            "impl Labelled for Beta {\n"
            "    task label(self) -> word { give back \"beta\" }\n"
            "}\n"
            "task main() {\n"
            "    pilot alpha = Alpha { value: 1 }\n"
            "    pilot beta = Beta { value: 2 }\n"
            "    say alpha.label()\n"
            "    say beta.label()\n"
            "}\n",
            encoding="utf-8",
        )
        for backend, flag, suffix in (("C", "--c", ".c"), ("LLVM", "--llvm", ".ll")):
            transpiled = run(freak, repo, doctrine_impls, "transpile", flag)
            assert transpiled.returncode == 0, transpiled.stdout + transpiled.stderr
            generated = Path(str(doctrine_impls) + suffix).read_text(encoding="utf-8")
            assert "Alpha_label" in generated
            assert "Beta_label" in generated
            assert "Labelled_label" not in generated

        # The release CLI must be compiled by a current self-host stage.  This
        # full stdlib case used to expose parser errors yet continue into LLVM
        # with duplicate doctrine symbols when the stale bootstrap built it.
        math3d_probe = tmp_path / "math3d_release_probe.fk"
        math3d_source = (repo / "tests" / "math3d_test.fk").read_text(encoding="utf-8")
        math3d_declarations, math3d_body = math3d_source.split("\npilot a =", 1)
        math3d_probe.write_text(
            math3d_declarations + "\ntask main() {\npilot a =" + math3d_body + "\n}\n",
            encoding="utf-8",
        )
        math3d_build = run(freak, repo, math3d_probe, "build", "--llvm")
        assert math3d_build.returncode == 0, math3d_build.stdout + math3d_build.stderr
        math3d_binary = math3d_probe.with_suffix(".exe" if sys.platform == "win32" else "")
        assert math3d_binary.is_file(), math3d_binary
        math3d_executed = subprocess.run(
            [str(math3d_binary)],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            check=False,
        )
        assert math3d_executed.returncode == 0, (
            math3d_executed.stdout + math3d_executed.stderr
        )
        assert "FAIL" not in math3d_executed.stdout, math3d_executed.stdout
        assert "OK" in math3d_executed.stdout, math3d_executed.stdout

        literal_matrix = tmp_path / "string_literal_fixed_point.fk"
        literal_matrix.write_text(
            'task main() {\n'
            'say "|"\n'
            'say "<<PIPE>>"\n'
            'say "\\x41\\x42"\n'
            'say "z\\x41q\\x42"\n'
            'say "\\x41BC"\n'
            '}\n',
            encoding="utf-8",
        )
        expected_literals = ["|", "<<PIPE>>", "AB", "zAqB", "ABC"]
        for backend, flag in (("LLVM", "--llvm"), ("C", "--c")):
            literal_build = run(freak, repo, literal_matrix, "build", flag)
            assert literal_build.returncode == 0, (
                f"{backend} string literal matrix failed to build\n"
                + literal_build.stdout
                + literal_build.stderr
            )
            literal_binary = literal_matrix.with_suffix(
                ".exe" if sys.platform == "win32" else ""
            )
            literal_run = subprocess.run(
                [str(literal_binary)],
                cwd=tmp_path,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
                check=False,
            )
            assert literal_run.returncode == 0, (
                literal_run.stdout + literal_run.stderr
            )
            assert literal_run.stdout.splitlines() == expected_literals, (
                f"{backend} string literal matrix changed meaning\n"
                f"expected={expected_literals!r}\n"
                f"actual={literal_run.stdout.splitlines()!r}\n"
                f"stderr={literal_run.stderr}"
            )

        llvm_interp_hex = tmp_path / "llvm_interpolation_hex.fk"
        llvm_interp_hex.write_text(
            'pilot value: int = 7\n'
            'task main() { say "\\x41{value}\\x42" }\n',
            encoding="utf-8",
        )
        llvm_interp_build = run(freak, repo, llvm_interp_hex, "build", "--llvm")
        assert llvm_interp_build.returncode == 0, (
            "LLVM interpolation fragments with hex escapes failed to build\n"
            + llvm_interp_build.stdout
            + llvm_interp_build.stderr
        )
        llvm_interp_binary = llvm_interp_hex.with_suffix(
            ".exe" if sys.platform == "win32" else ""
        )
        llvm_interp_run = subprocess.run(
            [str(llvm_interp_binary)],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            check=False,
        )
        assert llvm_interp_run.returncode == 0, (
            llvm_interp_run.stdout + llvm_interp_run.stderr
        )
        assert llvm_interp_run.stdout.splitlines() == ["A7B"], (
            "LLVM interpolation fragment byte lengths changed meaning\n"
            f"actual={llvm_interp_run.stdout.splitlines()!r}\n"
            f"stderr={llvm_interp_run.stderr}"
        )

        embedded_nul = tmp_path / "embedded_nul_bad.fk"
        embedded_nul.write_text('say "before\\x00after"\n', encoding="utf-8")
        embedded_nul_binary = derived_binary(embedded_nul)
        embedded_nul_cache = run_cache(embedded_nul_binary)
        for backend, flag, suffix in (
            ("LLVM", "--llvm", ".ll"),
            ("C", "--c", ".c"),
        ):
            artifact = Path(str(embedded_nul) + suffix)
            seed_stale_outputs(artifact, embedded_nul_binary, embedded_nul_cache)
            nul_build = run(freak, repo, embedded_nul, "build", flag)
            assert_rejected(nul_build, f"{backend} embedded NUL escape")
            nul_output = nul_build.stdout + nul_build.stderr
            assert "embedded NUL escape is not supported" in nul_output, nul_output
            assert "1 syntax error(s)" in nul_output, nul_output
            assert_outputs_absent(
                (artifact, embedded_nul_binary, embedded_nul_cache),
                f"{backend} embedded NUL escape",
            )
            if direct_compiler is not None:
                seed_stale_outputs(artifact)
                direct_nul = run_direct_compiler(
                    direct_compiler, repo, str(embedded_nul), flag
                )
                direct_output = direct_nul.stdout + direct_nul.stderr
                assert direct_nul.returncode != 0, direct_output
                assert "embedded NUL escape is not supported" in direct_output
                assert "aborting: 1 error(s) found" in direct_output, direct_output
                assert_outputs_absent(
                    (artifact,), f"direct {backend} embedded NUL escape"
                )

        missing_input = subprocess.run(
            [str(freak), "check"],
            cwd=repo,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            check=False,
        )
        assert missing_input.returncode != 0, (
            "check without a file argument exited successfully\n"
            + missing_input.stdout
            + missing_input.stderr
        )

    print("V3 codegen error gate: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
