from __future__ import annotations

import io
import json
import os
import hashlib
import shutil
import sys
import tempfile
import subprocess
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from freakc.__main__ import main
from freakc.academy import (
    export_progress,
    first_exercise,
    format_course_listing,
    format_progress,
    import_progress,
    load_course,
    load_lesson,
    load_progress,
    mark_lesson_complete,
    reset_progress,
)
from tools.academy.check_academy_examples import iter_academy_examples


def test_seed_course_loads():
    course = load_course("freak-basics")

    assert course["compilerTrack"] == "v3"
    assert course["lessons"] == [
        "hello-freak",
        "variables",
        "primitive-types",
        "arithmetic",
        "conditions",
        "loops",
        "functions",
    ]


def test_seed_lesson_has_v3_exercise_contracts():
    lesson = load_lesson("hello-freak")
    exercise = first_exercise(lesson)

    assert lesson["supportLevel"] == "v3-mvp"
    assert exercise["id"] == "hello-exercise"
    assert [req["kind"] for req in exercise["requirements"]] == [
        "parses",
        "compiles",
        "expected_output",
    ]


def test_course_listing_mentions_seed_lesson():
    listing = format_course_listing()

    assert "freak-basics" in listing
    assert "hello-freak" in listing
    assert "functions" in listing
    assert "freak learn check <lesson-id> <file.fk>" in listing
    assert "freak learn web-assets <dir>" in listing
    assert "freak learn check-examples" in listing
    assert "freak learn worker-parity" in listing
    assert "freak learn wasm-evaluator [dir]" in listing
    assert "Bootstrap fallback: python -m freakc learn <cmd>" in listing


def test_learn_list_cli_outputs_seed_course():
    out = io.StringIO()

    with redirect_stdout(out):
        code = main(["learn", "list"])

    assert code == 0
    assert "FREAK Academy" in out.getvalue()
    assert "hello-freak" in out.getvalue()


def test_native_cli_learn_list_dispatches_to_academy():
    native_cli = ROOT / "build" / "freak.exe"
    if sys.platform != "win32" or not native_cli.exists():
        return

    result = subprocess.run(
        [str(native_cli), "learn", "list"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "FREAK Academy" in result.stdout
    assert "hello-freak" in result.stdout


def test_learn_show_cli_outputs_lesson_outline():
    out = io.StringIO()

    with redirect_stdout(out):
        code = main(["learn", "show", "hello-freak"])

    assert code == 0
    assert "Hello, FREAK" in out.getvalue()
    assert "Compiler track: v3 / v3-mvp" in out.getvalue()


def test_progress_records_completed_lesson():
    lesson = load_lesson("hello-freak")

    with tempfile.TemporaryDirectory() as tmp:
        progress_path = Path(tmp) / "progress.json"

        assert mark_lesson_complete(lesson, path=progress_path) is True
        assert mark_lesson_complete(lesson, path=progress_path) is False

        progress = load_progress(progress_path)
        assert progress["completedLessons"] == ["freak-basics/hello-freak"]
        assert "[DONE] 1. hello-freak" in format_progress(path=progress_path)


def test_progress_export_import_and_reset():
    lesson = load_lesson("hello-freak")
    variables = load_lesson("variables")

    with tempfile.TemporaryDirectory() as tmp:
        progress_path = Path(tmp) / "progress.json"
        export_path = Path(tmp) / "export.freaklearn"
        imported_path = Path(tmp) / "imported.json"

        mark_lesson_complete(lesson, path=progress_path)
        mark_lesson_complete(variables, path=progress_path)
        export_progress(export_path, path=progress_path)
        import_progress(export_path, path=imported_path)

        imported = load_progress(imported_path)
        assert imported["completedLessons"] == [
            "freak-basics/hello-freak",
            "freak-basics/variables",
        ]

        assert reset_progress("hello-freak", path=imported_path) == 1
        assert load_progress(imported_path)["completedLessons"] == ["freak-basics/variables"]
        assert reset_progress("freak-basics", path=imported_path) == 1
        assert load_progress(imported_path)["completedLessons"] == []


def test_learn_status_cli_uses_progress_override():
    with tempfile.TemporaryDirectory() as tmp:
        progress_path = Path(tmp) / "progress.json"
        old_progress = os.environ.get("FREAK_ACADEMY_PROGRESS")
        os.environ["FREAK_ACADEMY_PROGRESS"] = str(progress_path)
        try:
            out = io.StringIO()
            with redirect_stdout(out):
                code = main(["learn", "status"])
        finally:
            if old_progress is None:
                os.environ.pop("FREAK_ACADEMY_PROGRESS", None)
            else:
                os.environ["FREAK_ACADEMY_PROGRESS"] = old_progress

    assert code == 0
    assert "FREAK Academy Progress" in out.getvalue()
    assert "[TODO] 1. hello-freak" in out.getvalue()


def test_learn_progress_cli_export_import_reset():
    lesson = load_lesson("hello-freak")

    with tempfile.TemporaryDirectory() as tmp:
        progress_path = Path(tmp) / "progress.json"
        export_path = Path(tmp) / "progress.freaklearn"
        old_progress = os.environ.get("FREAK_ACADEMY_PROGRESS")
        os.environ["FREAK_ACADEMY_PROGRESS"] = str(progress_path)
        try:
            mark_lesson_complete(lesson)

            out = io.StringIO()
            with redirect_stdout(out):
                export_code = main(["learn", "export", str(export_path)])
            assert export_code == 0
            assert export_path.exists()

            reset_out = io.StringIO()
            with redirect_stdout(reset_out):
                reset_code = main(["learn", "reset", "all"])
            assert reset_code == 0
            assert load_progress(progress_path)["completedLessons"] == []

            import_out = io.StringIO()
            with redirect_stdout(import_out):
                import_code = main(["learn", "import", str(export_path)])
            assert import_code == 0
            assert load_progress(progress_path)["completedLessons"] == ["freak-basics/hello-freak"]
        finally:
            if old_progress is None:
                os.environ.pop("FREAK_ACADEMY_PROGRESS", None)
            else:
                os.environ["FREAK_ACADEMY_PROGRESS"] = old_progress


def test_academy_package_exporter_outputs_browser_package():
    with tempfile.TemporaryDirectory() as tmp:
        package_path = Path(tmp) / "academy-package.json"
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                "tools/academy/export_academy_package.py",
                "--output",
                str(package_path),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=10,
        )

        assert result.returncode == 0, result.stderr
        package = json.loads(package_path.read_text(encoding="utf-8"))

    assert package["schemaVersion"] == 1
    assert package["packageId"] == "freak-academy-v3-mvp"
    assert package["websiteConnector"] == "freaklang.dev"
    assert package["workerProtocolVersion"] == 1
    assert package["courses"][0]["id"] == "freak-basics"
    assert len(package["courses"][0]["lessonData"]) == 7


def test_learn_package_cli_exports_browser_package():
    with tempfile.TemporaryDirectory() as tmp:
        package_path = Path(tmp) / "academy-package.json"
        out = io.StringIO()
        with redirect_stdout(out):
            code = main(["learn", "package", str(package_path)])

        assert code == 0
        package = json.loads(package_path.read_text(encoding="utf-8"))

    assert "Academy package exported" in out.getvalue()
    assert package["packageId"] == "freak-academy-v3-mvp"
    assert package["courses"][0]["id"] == "freak-basics"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_learn_web_assets_cli_exports_browser_manifest():
    with tempfile.TemporaryDirectory() as tmp:
        assets_dir = Path(tmp) / "academy-assets"
        out = io.StringIO()
        with redirect_stdout(out):
            code = main(["learn", "web-assets", str(assets_dir)])

        package_path = assets_dir / "freak-academy-package.json"
        book_path = assets_dir / "freak-academy-book.json"
        reference_path = assets_dir / "freak-academy-reference.json"
        worker_path = assets_dir / "academy-worker.mjs"
        manifest_path = assets_dir / "academy-assets-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        assert code == 0
        assert "Academy browser assets exported" in out.getvalue()
        assert "book: freak-academy-book.json" in out.getvalue()
        assert "reference: freak-academy-reference.json" in out.getvalue()
        assert package_path.exists()
        assert book_path.exists()
        assert reference_path.exists()
        assert worker_path.exists()
        assert manifest["artifactStatus"] == "browser-safe-js-reference"
        assert manifest["wasmStatus"] == "pending-v4-compiler-owned-artifact"
        assert manifest["packagePath"] == "freak-academy-package.json"
        assert manifest["bookPath"] == "freak-academy-book.json"
        assert manifest["referencePath"] == "freak-academy-reference.json"
        assert manifest["workerPath"] == "academy-worker.mjs"
        assert "wasmEvaluatorPath" not in manifest
        assert not (assets_dir / "academy-wasm-evaluator.wasm").exists()

        assets = {item["role"]: item for item in manifest["assets"]}
        assert assets["academy-package"]["sha256"] == sha256_file(package_path)
        assert assets["academy-book"]["sha256"] == sha256_file(book_path)
        assert assets["academy-reference"]["sha256"] == sha256_file(reference_path)
        assert assets["worker-entrypoint"]["sha256"] == sha256_file(worker_path)


def test_learn_web_assets_cli_can_include_wasm_evaluator():
    if shutil.which("clang") is None:
        return

    with tempfile.TemporaryDirectory() as tmp:
        assets_dir = Path(tmp) / "academy-assets"
        out = io.StringIO()
        with redirect_stdout(out):
            code = main(["learn", "web-assets", str(assets_dir), "--with-wasm-evaluator"])

        package_path = assets_dir / "freak-academy-package.json"
        book_path = assets_dir / "freak-academy-book.json"
        reference_path = assets_dir / "freak-academy-reference.json"
        worker_path = assets_dir / "academy-worker.mjs"
        wasm_path = assets_dir / "academy-wasm-evaluator.wasm"
        wasm_manifest_path = assets_dir / "academy-wasm-evaluator-manifest.json"
        manifest_path = assets_dir / "academy-assets-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        wasm_manifest = json.loads(wasm_manifest_path.read_text(encoding="utf-8"))

        assert code == 0
        assert "book: freak-academy-book.json" in out.getvalue()
        assert "reference: freak-academy-reference.json" in out.getvalue()
        assert "wasm: academy-wasm-evaluator.wasm (preview)" in out.getvalue()
        assert package_path.exists()
        assert book_path.exists()
        assert reference_path.exists()
        assert worker_path.exists()
        assert wasm_path.exists()
        assert wasm_manifest_path.exists()
        assert manifest["artifactStatus"] == "wasm-preview"
        assert manifest["wasmStatus"] == "preview"
        assert manifest["bookPath"] == "freak-academy-book.json"
        assert manifest["referencePath"] == "freak-academy-reference.json"
        assert manifest["wasmEvaluatorPath"] == "academy-wasm-evaluator.wasm"
        assert manifest["wasmEvaluatorManifestPath"] == "academy-wasm-evaluator-manifest.json"
        assert manifest["wasmEvaluator"]["supportedLessons"] == [
            "hello-freak",
            "variables",
            "primitive-types",
            "arithmetic",
            "conditions",
            "loops",
        ]
        assert manifest["wasmEvaluator"]["sha256"] == sha256_file(wasm_path)
        assert manifest["wasmEvaluator"]["bytes"] == wasm_path.stat().st_size
        assert manifest["wasmEvaluator"]["target"] == "wasm32"
        assert wasm_manifest["sha256"] == sha256_file(wasm_path)

        assets = {item["role"]: item for item in manifest["assets"]}
        assert assets["academy-package"]["sha256"] == sha256_file(package_path)
        assert assets["academy-book"]["sha256"] == sha256_file(book_path)
        assert assets["academy-reference"]["sha256"] == sha256_file(reference_path)
        assert assets["worker-entrypoint"]["sha256"] == sha256_file(worker_path)
        assert assets["wasm-evaluator"]["sha256"] == sha256_file(wasm_path)
        assert assets["wasm-evaluator-manifest"]["sha256"] == sha256_file(wasm_manifest_path)

        node = shutil.which("node")
        if node is not None:
            result = subprocess.run(
                [node, "tools/academy/verify_wasm_evaluator.mjs", str(wasm_path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                timeout=10,
            )
            assert result.returncode == 0, result.stdout + result.stderr


def test_learn_wasm_status_cli_builds_browser_loadable_probe():
    if shutil.which("clang") is None:
        return

    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp) / "wasm"
        out = io.StringIO()
        with redirect_stdout(out):
            code = main(["learn", "wasm-status", str(out_dir)])

        wasm_path = out_dir / "academy-wasm-probe.wasm"
        manifest_path = out_dir / "academy-wasm-probe-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        assert code == 0
        assert "Academy WASM probe built" in out.getvalue()
        assert wasm_path.exists()
        assert manifest["artifactStatus"] == "wasm-preview-probe"
        assert manifest["workerProtocolVersion"] == 1
        assert manifest["sha256"] == sha256_file(wasm_path)
        assert manifest["exports"] == [
            "academy_protocol_version",
            "academy_wasm_probe_version",
            "academy_supported_lesson_count",
        ]

        node = shutil.which("node")
        if node is not None:
            result = subprocess.run(
                [node, "tools/academy/verify_wasm_probe.mjs", str(wasm_path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                timeout=10,
            )
            assert result.returncode == 0, result.stdout + result.stderr
            assert "Academy WASM probe verified" in result.stdout


def test_learn_wasm_evaluator_cli_builds_basics_worker_artifact():
    if shutil.which("clang") is None:
        return

    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp) / "wasm"
        out = io.StringIO()
        with redirect_stdout(out):
            code = main(["learn", "wasm-evaluator", str(out_dir)])

        wasm_path = out_dir / "academy-wasm-evaluator.wasm"
        manifest_path = out_dir / "academy-wasm-evaluator-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        assert code == 0
        assert "Academy WASM evaluator built" in out.getvalue()
        assert wasm_path.exists()
        assert manifest["artifactStatus"] == "wasm-preview-basics-evaluator"
        assert manifest["workerProtocolVersion"] == 1
        assert manifest["supportedLessons"] == [
            "hello-freak",
            "variables",
            "primitive-types",
            "arithmetic",
            "conditions",
            "loops",
        ]
        assert manifest["sha256"] == sha256_file(wasm_path)
        assert "academy_evaluate_hello_freak" in manifest["exports"]
        assert "academy_evaluate_variables" in manifest["exports"]
        assert "academy_evaluate_primitive_types" in manifest["exports"]
        assert "academy_evaluate_arithmetic" in manifest["exports"]
        assert "academy_evaluate_conditions" in manifest["exports"]
        assert "academy_evaluate_loops" in manifest["exports"]

        node = shutil.which("node")
        if node is not None:
            result = subprocess.run(
                [node, "tools/academy/verify_wasm_evaluator.mjs", str(wasm_path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                timeout=10,
            )
            assert result.returncode == 0, result.stdout + result.stderr
            assert "Academy WASM evaluator verified" in result.stdout


def run_worker_request(request: dict) -> dict:
    result = subprocess.run(
        [sys.executable, "-B", "tools/academy/worker_host.py"],
        cwd=ROOT,
        input=json.dumps(request),
        text=True,
        capture_output=True,
        timeout=30,
    )
    response = json.loads(result.stdout)
    assert result.returncode == (0 if response["ok"] else 1), result.stderr
    return response


def test_worker_host_package_info():
    response = run_worker_request({
        "protocolVersion": 1,
        "requestId": "req-package",
        "method": "package.info",
        "params": {},
    })

    assert response["ok"] is True
    assert response["requestId"] == "req-package"
    assert response["result"]["packageId"] == "freak-academy-v3-mvp"
    assert response["result"]["workerProtocolVersion"] == 1


def test_worker_host_evaluate_exercise():
    response = run_worker_request({
        "protocolVersion": 1,
        "requestId": "req-eval",
        "method": "evaluateExercise",
        "params": {
            "lessonId": "hello-freak",
            "source": 'say "Hello, FREAK Academy!"\n',
        },
    })

    result = response["result"]
    assert response["ok"] is True
    assert result["lessonId"] == "hello-freak"
    assert result["exerciseId"] == "hello-exercise"
    assert result["passed"] is True
    assert [item["kind"] for item in result["requirements"]] == [
        "parses",
        "compiles",
        "expected_output",
    ]


def test_worker_host_reports_bad_request():
    response = run_worker_request({
        "protocolVersion": 1,
        "requestId": "req-bad",
        "method": "evaluateExercise",
        "params": {
            "lessonId": "hello-freak"
        },
    })

    assert response["ok"] is False
    assert response["requestId"] == "req-bad"
    assert response["error"]["code"] == "bad_request"


def test_worker_fixtures_match_host():
    result = subprocess.run(
        [sys.executable, "-B", "tools/academy/verify_worker_fixtures.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "evaluate_hello.request.json: OK" in result.stdout
    assert "evaluate_functions.request.json: OK" in result.stdout
    assert "run_loops.request.json: OK" in result.stdout
    assert "package_info.request.json: OK" in result.stdout


def test_browser_worker_fixtures_match_golden_contract():
    node = shutil.which("node")
    if node is None:
        return

    result = subprocess.run(
        [node, "tools/academy/verify_browser_worker_fixtures.mjs"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "evaluate_hello.request.json: OK" in result.stdout
    assert "evaluate_functions.request.json: OK" in result.stdout
    assert "run_loops.request.json: OK" in result.stdout
    assert "demo functions/double-demo: OK" in result.stdout


def test_learn_worker_parity_cli_compares_native_and_browser_reference():
    node = shutil.which("node")
    if node is None:
        return

    out = io.StringIO()
    with redirect_stdout(out):
        code = main(["learn", "worker-parity", "--limit", "2"])

    assert code == 0
    assert "native/browser OK" in out.getvalue()
    assert "Academy worker parity passed: 2 request(s)." in out.getvalue()


def test_learn_worker_cli_runs_protocol_request():
    request_path = ROOT / "learning" / "wasm" / "fixtures" / "package_info.request.json"
    out = io.StringIO()

    with redirect_stdout(out):
        code = main(["learn", "worker", str(request_path)])

    response = json.loads(out.getvalue())
    assert code == 0
    assert response["ok"] is True
    assert response["result"]["packageId"] == "freak-academy-v3-mvp"


def test_academy_example_extraction_covers_lessons_reference_and_book():
    examples = iter_academy_examples(ROOT)
    by_source = {}
    for example in examples:
        by_source[example.source_name] = by_source.get(example.source_name, 0) + 1

    assert by_source == {
        "lesson": 7,
        "reference": 8,
        "book": 5,
    }
    assert "book:getting-started/hello-freak:smallest-program:1" in {
        example.stable_id for example in examples
    }


def test_learn_check_examples_cli_runs_book_examples():
    out = io.StringIO()

    with redirect_stdout(out):
        code = main(["learn", "check-examples", "--source", "book"])

    assert code == 0
    assert "book book:getting-started/hello-freak:smallest-program:1: OK" in out.getvalue()
    assert "Academy example checks passed: 5/5 example(s)." in out.getvalue()


def test_ci_runs_all_academy_contract_checks():
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert "python -B tools/academy/validate_academy.py" in workflow
    assert "python -B tools/academy/verify_worker_parity.py" in workflow
    assert "python -B tools/academy/check_academy_examples.py" in workflow
    assert "python -B tests/test_academy.py" in workflow


def test_learn_start_collects_submission_and_records_progress():
    captured: dict[str, str] = {}

    def fake_evaluate(exercise, path):
        captured["exercise"] = exercise["id"]
        captured["source"] = Path(path).read_text(encoding="utf-8")
        return [
            {
                "id": "parses",
                "kind": "parses",
                "passed": True,
                "message": "source parses",
            }
        ]

    with tempfile.TemporaryDirectory() as tmp:
        progress_path = Path(tmp) / "progress.json"
        old_progress = os.environ.get("FREAK_ACADEMY_PROGRESS")
        os.environ["FREAK_ACADEMY_PROGRESS"] = str(progress_path)
        try:
            out = io.StringIO()
            stdin = io.StringIO('\ufeffsay "Hello, FREAK Academy!"\n.submit\n1\n1\n')
            with (
                redirect_stdout(out),
                patch("sys.stdin", stdin),
                patch("freakc.__main__._academy_evaluate_submission", side_effect=fake_evaluate),
            ):
                code = main(["learn", "start", "hello-freak"])
        finally:
            if old_progress is None:
                os.environ.pop("FREAK_ACADEMY_PROGRESS", None)
            else:
                os.environ["FREAK_ACADEMY_PROGRESS"] = old_progress

        progress = load_progress(progress_path)

    assert code == 0
    assert captured["exercise"] == "hello-exercise"
    assert captured["source"] == 'say "Hello, FREAK Academy!"\n'
    assert progress["completedLessons"] == ["freak-basics/hello-freak"]
    assert "Starting: Hello, FREAK" in out.getvalue()
    assert "Quiz passed." in out.getvalue()
    assert "Progress saved." in out.getvalue()


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"{name}: OK")
