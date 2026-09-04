#!/usr/bin/env python3
"""Keep legacy three-value bootstrap consumers compatible and fail-closed."""
from __future__ import annotations

from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from freakc import __main__ as pipeline


def check(source: str, *, errors: bool, diagnostics: bool) -> None:
    path = Path("bootstrap-contract.fk")
    # This is the existing unpacking contract used by the V4 harness. Do not
    # modify its consumers merely to accommodate a bootstrap return change.
    c_source, messages, uses_ui = pipeline.transpile(source, path)
    checked_c, checked_messages, checked_ui, has_errors = pipeline.transpile_checked(source, path)
    assert isinstance(uses_ui, bool) and uses_ui == checked_ui
    assert c_source == checked_c and messages == checked_messages
    assert bool(messages) == diagnostics, messages
    assert has_errors is errors
    assert (c_source is None) is errors


def main() -> int:
    check('say "ok"\n', errors=False, diagnostics=False)
    check('say )\n', errors=True, diagnostics=True)
    check('pilot value: ByteBuffer = ByteBuffer::with_capacity("wrong")\n', errors=True, diagnostics=True)
    with patch.object(pipeline.CEmitter, "emit", side_effect=pipeline.EmitError("forced emitter error")):
        check('say "ok"\n', errors=True, diagnostics=True)
    warning = SimpleNamespace(level="warning", message="controlled warning", line=1, column=1)
    with patch.object(pipeline.TypeChecker, "check", return_value=[warning]):
        check('say "ok"\n', errors=False, diagnostics=True)
    print("PASS legacy three-value and structured bootstrap APIs: success, parse/type/emission errors, nonfatal warnings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
