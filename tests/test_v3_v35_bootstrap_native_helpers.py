"""Replay the native bootstrap evidence reads without launching a bootstrap."""
import ast
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import v3_v35_bootstrap_native as native


class BootstrapReportEncoding(unittest.TestCase):
    def test_both_report_reads_preserve_utf8_under_a_cp1252_default(self):
        tree = ast.parse(Path(native.__file__).read_bytes())
        reads = [node for node in ast.walk(tree) if isinstance(node, ast.Assign)
                 and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                 and node.targets[0].id in ("report", "git_report")
                 and "bootstrap-report.json" in ast.unparse(node.value)]
        self.assertEqual(len(reads), 2, "exercise the first and second public bootstrap report reads")
        read_text = Path.read_text
        defaults = []

        def cp1252_default(path, encoding=None, errors=None):
            defaults.append(encoding)
            return read_text(path, encoding=encoding or "cp1252", errors=errors)

        with tempfile.TemporaryDirectory(prefix="freak-bootstrap-report-utf8-") as directory:
            output = Path(directory) / "output é 日本 ' $ &"
            output.mkdir()
            installed = Path(directory) / "installed é 日本 ' $ &" / "freak.exe"
            document = {"builder_executable": str(installed), "builder_sha256": "a" * 64,
                        "source_inventory": "byte-verified", "git_verification": "commit-source-bytes-verified"}
            report_path = output / "bootstrap-report.json"
            report_path.write_bytes((json.dumps(document, ensure_ascii=False) + "\n").encode("utf-8"))
            with patch.object(Path, "read_text", cp1252_default):
                # Keep the historical decoding failure as a negative control.
                self.assertNotEqual(json.loads(report_path.read_text())["builder_executable"], str(installed))
                for node in reads:
                    scope = {"json": json, "output": output, "git_output": output}
                    module = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
                    exec(compile(module, str(native.__file__), "exec"), scope)
                    self.assertEqual(scope[node.targets[0].id], document)
            self.assertEqual(defaults, [None, "utf-8", "utf-8"])


if __name__ == "__main__":
    unittest.main()
