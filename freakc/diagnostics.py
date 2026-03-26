"""
FREAK Diagnostics — Anime-Themed Compiler Error Reporting

Each error category is voiced by a character from the FREAK universe:
  [SUMIKA]  — Parser errors. Confused, trying her best.
  [YUUKO]   — Type errors. Cold, precise, scientific.
  [MEIYA]   — Undefined variable/function. Serious, direct.
  [MARIMO]  — Missing returns, structural issues. Teacher-like.
  [KASUMI]  — Warnings. Quiet, gentle nudge.

Error codes: E001–E020 for common errors, W001–W010 for warnings.
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


# ===================================================================
#  Source Span
# ===================================================================


@dataclass
class SourceSpan:
    """Locates a region of source code."""
    file: str = "<unknown>"
    line: int = 0
    column: int = 0
    length: int = 1

    def __str__(self) -> str:
        return f"{self.file}:{self.line}:{self.column}"


# ===================================================================
#  Severity
# ===================================================================


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    NOTE = "note"


# ===================================================================
#  Error Codes
# ===================================================================

# Each error code maps to: (voice_character, short_title, thematic_note)
ERROR_CATALOG: Dict[str, Tuple[str, str, str]] = {
    # -- Lexer errors (E001-E005) --
    "E001": ("SUMIKA", "Unexpected character",
             "I found something I really don't recognize. Is this from another world?"),
    "E002": ("SUMIKA", "Unterminated string",
             "This string never ends... like a training arc with no resolution."),
    "E003": ("SUMIKA", "Unterminated escape sequence",
             "That escape sequence just... stopped. It needs somewhere to go."),

    # -- Parser errors (E004-E010) --
    "E004": ("SUMIKA", "Unexpected token",
             "I... I don't understand this syntax. Were you trying to write something else?"),
    "E005": ("SUMIKA", "Expected expression",
             "I was expecting an expression here, but I found something else entirely."),
    "E006": ("SUMIKA", "Expected block",
             "A block should start with '{' here. Did you forget it?"),
    "E007": ("SUMIKA", "Expected identifier",
             "I need a name here -- an identifier. Every pilot needs a callsign."),
    "E008": ("SUMIKA", "Expected type annotation",
             "I was hoping for a type here. What kind of value is this supposed to be?"),
    "E009": ("SUMIKA", "Unclosed block",
             "This block was opened but never closed. Every '{' needs its '}' or 'done'."),
    "E010": ("SUMIKA", "Invalid pattern",
             "This pattern doesn't make sense in a 'when' or 'check' arm."),

    # -- Type errors (E011-E016) --
    "E011": ("YUUKO", "Type mismatch",
             "Science demands precision. The types don't align."),
    "E012": ("YUUKO", "Invalid operation",
             "This operation is not defined for these types. Check the doctrines."),
    "E013": ("YUUKO", "Arity mismatch",
             "The number of arguments doesn't match the function signature. Count again."),
    "E014": ("YUUKO", "Return type mismatch",
             "The return type doesn't match what was promised. Precision matters."),

    # -- Undefined symbol errors (E015-E017) --
    "E015": ("MEIYA", "Undeclared variable",
             "This name has no meaning here. Did you forget to declare it as a pilot?"),
    "E016": ("MEIYA", "Undeclared function",
             "This function doesn't exist. Perhaps you forgot to define the task?"),
    "E017": ("MEIYA", "Unknown shape",
             "This shape has not been defined. You must declare it before you can use it."),

    # -- Structural errors (E018-E020) --
    "E018": ("MARIMO", "Missing return value",
             "Your task promises to give back a value, but some paths return nothing."),
    "E019": ("MARIMO", "Monologue too short",
             "A deus_ex_machina requires conviction. At least 20 words. This isn't enough."),
    "E020": ("MARIMO", "Invalid assignment",
             "You're trying to assign to something that isn't a valid target."),

    # -- Warnings (W001-W010) --
    "W001": ("KASUMI", "Unused variable",
             "This pilot was declared but never used. Every variable deserves a purpose."),
    "W002": ("KASUMI", "Type inference mismatch",
             "The declared type and the value's type seem different. Are you sure?"),
    "W003": ("KASUMI", "Condition type",
             "This condition doesn't look like a boolean. It might not work as expected."),
    "W004": ("KASUMI", "Missing export",
             "The isekai block exports a name that was never declared inside."),
    "W005": ("KASUMI", "Undeclared payoff",
             "A payoff was issued for a variable that doesn't exist. A foreshadow left unfulfilled."),
    "W006": ("KASUMI", "Return type inconsistency",
             "The value being given back doesn't match the expected return type."),
}


# ===================================================================
#  Diagnostic
# ===================================================================


@dataclass
class Diagnostic:
    """A single compiler diagnostic with source location and theming."""
    span: SourceSpan
    message: str
    severity: Severity
    error_code: str = ""
    notes: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        loc = ""
        if self.span.line > 0:
            loc = f"[line {self.span.line}] "
        return f"{self.severity.value}: {loc}{self.message}"


# ===================================================================
#  ANSI Color Support
# ===================================================================


def _supports_color() -> bool:
    """Detect whether the terminal supports ANSI color codes."""
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    if hasattr(sys.stderr, "isatty") and sys.stderr.isatty():
        return True
    return False


_USE_COLOR = _supports_color()


def _ansi(code: str, text: str) -> str:
    if not _USE_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"


def _red(text: str) -> str:
    return _ansi("91", text)


def _yellow(text: str) -> str:
    return _ansi("93", text)


def _cyan(text: str) -> str:
    return _ansi("96", text)


def _blue(text: str) -> str:
    return _ansi("94", text)


def _bold(text: str) -> str:
    return _ansi("1", text)


def _dim(text: str) -> str:
    return _ansi("90", text)


def _magenta(text: str) -> str:
    return _ansi("95", text)


def _white(text: str) -> str:
    return _ansi("97", text)


# ===================================================================
#  Source Line Formatting
# ===================================================================


def format_source_line(line_text: str, line_num: int, col: int, length: int) -> str:
    """
    Format a source line with carets pointing to the error region.

    Returns a multi-line string like:
       7 |     pilot x: int = "hello"
         |                     ^^^^^^^
    """
    # Sanitize: replace tabs with spaces for consistent display
    display_line = line_text.rstrip("\n\r").replace("\t", "    ")

    line_num_str = str(line_num)
    gutter_width = len(line_num_str) + 1

    # The source line
    gutter = f" {line_num_str} "
    separator = _blue("|")
    line_display = f"{_blue(gutter)}{separator} {display_line}"

    # The caret line — underline the error region
    # Adjust col for 0-based indexing in the display
    col_0 = max(0, col - 1)
    caret_length = max(1, length)

    # Don't go past end of line
    if col_0 + caret_length > len(display_line):
        caret_length = max(1, len(display_line) - col_0)

    spaces = " " * col_0
    carets = "^" * caret_length

    empty_gutter = " " * (len(line_num_str) + 2)
    caret_display = f"{_blue(empty_gutter)}{separator} {spaces}{_red(carets)}"

    return f"{line_display}\n{caret_display}"


# ===================================================================
#  Full Diagnostic Formatting
# ===================================================================


def format_diagnostic(diagnostic: Diagnostic, source_lines: Optional[List[str]] = None,
                      file_path: str = "") -> str:
    """
    Format a diagnostic into a rich, anime-themed error display.

    Output format:
        [E042] [YUUKO] Type mismatch
          --> tests/hello.fk:7:15
           |
         7 |     pilot x: int = "hello"
           |                     ^^^^^^^ expected int, got word
           |
           = note: Science demands precision. An int is not a word.
    """
    lines: List[str] = []

    code = diagnostic.error_code
    catalog_entry = ERROR_CATALOG.get(code)

    # Header line: [E042] [VOICE] Title
    if catalog_entry:
        voice, title, _ = catalog_entry
        severity_color = _red if diagnostic.severity == Severity.ERROR else _yellow
        header = f"{severity_color(f'[{code}]')} {_magenta(f'[{voice}]')} {_bold(severity_color(title))}"
    else:
        severity_color = _red if diagnostic.severity == Severity.ERROR else _yellow
        severity_label = diagnostic.severity.value
        header = f"{severity_color(_bold(severity_label))}: {_bold(diagnostic.message)}"

    lines.append(header)

    # Location line: --> file:line:col
    span = diagnostic.span
    display_file = file_path or span.file
    if span.line > 0:
        location = f"{display_file}:{span.line}:{span.column}"
        lines.append(f"  {_blue('-->')} {location}")

    # Source context
    if source_lines and 0 < span.line <= len(source_lines):
        source_line = source_lines[span.line - 1]
        gutter_width = len(str(span.line)) + 2

        # Empty gutter line
        empty_gutter = " " * gutter_width
        lines.append(f"{_blue(empty_gutter)}{_blue('|')}")

        # Source line with carets
        source_display = format_source_line(
            source_line, span.line, span.column, span.length
        )

        # Append the specific error message after the carets
        # Split the source_display to inject the message on the caret line
        display_parts = source_display.split("\n")
        if len(display_parts) >= 2:
            lines.append(display_parts[0])
            lines.append(f"{display_parts[1]} {_red(diagnostic.message)}")
        else:
            lines.append(source_display)

        # Closing empty gutter line
        lines.append(f"{_blue(empty_gutter)}{_blue('|')}")
    elif diagnostic.message:
        # No source available, just show the message inline
        lines.append(f"  = {diagnostic.message}")

    # Thematic note from the catalog
    if catalog_entry:
        _, _, thematic_note = catalog_entry
        lines.append(f"  {_blue('=')} {_cyan('note')}: {thematic_note}")

    # Additional notes
    for note in diagnostic.notes:
        lines.append(f"  {_blue('=')} {_cyan('note')}: {note}")

    return "\n".join(lines)


# ===================================================================
#  Diagnostic Builder — Convenience Functions
# ===================================================================


def make_diagnostic(
    error_code: str,
    message: str,
    severity: Severity = Severity.ERROR,
    file: str = "<unknown>",
    line: int = 0,
    column: int = 0,
    length: int = 1,
    notes: Optional[List[str]] = None,
) -> Diagnostic:
    """Create a Diagnostic with a SourceSpan from individual components."""
    span = SourceSpan(file=file, line=line, column=column, length=length)
    return Diagnostic(
        span=span,
        message=message,
        severity=severity,
        error_code=error_code,
        notes=notes or [],
    )


# ===================================================================
#  Error Code Classification Helpers
# ===================================================================


def classify_parser_error(message: str) -> str:
    """Determine the best error code for a parser error message."""
    msg_lower = message.lower()

    if "expected expression" in msg_lower:
        return "E005"
    if "expected '{'" in msg_lower or "expected block" in msg_lower:
        return "E006"
    if "expected identifier" in msg_lower:
        return "E007"
    if "expected '}'" in msg_lower or "expected 'done'" in msg_lower or "close block" in msg_lower:
        return "E009"
    if "expected '=>'" in msg_lower or "expected '->'" in msg_lower or "pattern" in msg_lower:
        return "E010"
    # General unexpected token
    return "E004"


def classify_type_error(message: str) -> str:
    """Determine the best error code for a type checker error message."""
    msg_lower = message.lower()

    if "undeclared variable" in msg_lower:
        return "E015"
    if "undeclared function" in msg_lower or "unknown function" in msg_lower:
        return "E016"
    if "unknown shape" in msg_lower:
        return "E017"
    if "type mismatch" in msg_lower or "declared as" in msg_lower:
        return "E011"
    if "expects" in msg_lower and "argument" in msg_lower:
        return "E013"
    if "give back" in msg_lower and "type" in msg_lower:
        return "E014"
    if "give back" in msg_lower and "without value" in msg_lower:
        return "E018"
    if "monologue" in msg_lower or "deus_ex_machina" in msg_lower:
        return "E019"
    if "assignment" in msg_lower:
        return "E020"
    if "condition" in msg_lower and "type" in msg_lower:
        return "W003"
    # Generic type error
    return "E012"


def classify_lexer_error(message: str) -> str:
    """Determine the best error code for a lexer error message."""
    msg_lower = message.lower()

    if "unexpected character" in msg_lower:
        return "E001"
    if "unterminated string" in msg_lower:
        return "E002"
    if "unterminated escape" in msg_lower:
        return "E003"
    return "E001"


def classify_warning(message: str) -> str:
    """Determine the best warning code for a type checker warning message."""
    msg_lower = message.lower()

    if "declared as" in msg_lower and "initialized with" in msg_lower:
        return "W002"
    if "condition" in msg_lower:
        return "W003"
    if "exports" in msg_lower and "never declared" in msg_lower:
        return "W004"
    if "payoff" in msg_lower and "undeclared" in msg_lower:
        return "W005"
    if "give back" in msg_lower and "doesn't match" in msg_lower:
        return "W006"
    return "W001"


# ===================================================================
#  Formatted Output
# ===================================================================


def format_compiler_diagnostics(
    diagnostics: List[Diagnostic],
    source: str = "",
    file_path: str = "",
) -> List[str]:
    """
    Format a list of diagnostics into displayable strings.

    This is the main entry point for the CLI to render diagnostics.
    """
    source_lines = source.split("\n") if source else []
    result = []
    for diag in diagnostics:
        result.append(format_diagnostic(diag, source_lines, file_path))
    return result


# ===================================================================
#  Legacy Adapter — Bridge from old Diagnostic to new format
# ===================================================================


def format_legacy_diagnostic(
    level: str,
    message: str,
    source: str = "",
    file_path: str = "",
    line: Optional[int] = None,
    column: Optional[int] = None,
) -> str:
    """
    Convert a legacy-style diagnostic (level + message + optional line)
    into the new anime-themed format.

    Used to bridge existing error paths in the type checker and emitter
    without rewriting them.
    """
    severity = Severity.ERROR if level == "error" else Severity.WARNING
    if severity == Severity.ERROR:
        code = classify_type_error(message)
    else:
        code = classify_warning(message)

    diag = make_diagnostic(
        error_code=code,
        message=message,
        severity=severity,
        file=file_path or "<unknown>",
        line=line or 0,
        column=column or 0,
        length=1,
    )

    source_lines = source.split("\n") if source else []
    return format_diagnostic(diag, source_lines, file_path)


def format_parse_error(
    error_message: str,
    source: str = "",
    file_path: str = "",
) -> str:
    """
    Format a ParseError message into the new anime-themed style.

    ParseError messages have the format: [line N, col M] message (found ...)
    Lexer errors propagated as ParseErrors have: ... at line N, column M
    This function extracts the location info and enriches the display.
    """
    # Try parser format first: [line N, col M] message (found ...)
    match = re.match(r"\[line (\d+),\s*col (\d+)\]\s*(.*)", error_message)
    if match:
        line = int(match.group(1))
        col = int(match.group(2))
        msg = match.group(3)
    else:
        # Try lexer error format: ... at line N, column M
        lex_match = re.search(r"at line (\d+)(?:,\s*column (\d+))?", error_message)
        if lex_match:
            line = int(lex_match.group(1))
            col = int(lex_match.group(2)) if lex_match.group(2) else 0
            msg = error_message
            # Use lexer error classification for these
            code = classify_lexer_error(msg)
            diag = make_diagnostic(
                error_code=code,
                message=msg,
                severity=Severity.ERROR,
                file=file_path or "<unknown>",
                line=line,
                column=col,
                length=1,
            )
            source_lines = source.split("\n") if source else []
            return format_diagnostic(diag, source_lines, file_path)
        else:
            line = 0
            col = 0
            msg = error_message

    # Extract the "found ..." part for length estimation
    found_match = re.search(r"\(found\s+\S+\s+'([^']+)'\)$", msg)
    length = 1
    if found_match:
        length = max(1, len(found_match.group(1)))

    code = classify_parser_error(msg)

    diag = make_diagnostic(
        error_code=code,
        message=msg,
        severity=Severity.ERROR,
        file=file_path or "<unknown>",
        line=line,
        column=col,
        length=length,
    )

    source_lines = source.split("\n") if source else []
    return format_diagnostic(diag, source_lines, file_path)


def format_lexer_error(
    error_message: str,
    source: str = "",
    file_path: str = "",
) -> str:
    """
    Format a LexerError message into the new anime-themed style.

    LexerError messages contain "at line N" or "at line N, column M".
    """
    # Extract line from LexerError format
    match = re.search(r"at line (\d+)(?:,\s*column (\d+))?", error_message)
    if match:
        line = int(match.group(1))
        col = int(match.group(2)) if match.group(2) else 0
    else:
        line = 0
        col = 0

    code = classify_lexer_error(error_message)

    diag = make_diagnostic(
        error_code=code,
        message=error_message,
        severity=Severity.ERROR,
        file=file_path or "<unknown>",
        line=line,
        column=col,
        length=1,
    )

    source_lines = source.split("\n") if source else []
    return format_diagnostic(diag, source_lines, file_path)


def format_emit_error(
    error_message: str,
    source: str = "",
    file_path: str = "",
) -> str:
    """Format an EmitError into the anime-themed style."""
    diag = make_diagnostic(
        error_code="E012",
        message=error_message,
        severity=Severity.ERROR,
        file=file_path or "<unknown>",
        notes=["The emitter encountered something it doesn't know how to translate."],
    )

    source_lines = source.split("\n") if source else []
    return format_diagnostic(diag, source_lines, file_path)


__all__ = [
    "SourceSpan",
    "Severity",
    "Diagnostic",
    "ERROR_CATALOG",
    "format_diagnostic",
    "format_source_line",
    "format_compiler_diagnostics",
    "format_legacy_diagnostic",
    "format_parse_error",
    "format_lexer_error",
    "format_emit_error",
    "make_diagnostic",
    "classify_parser_error",
    "classify_type_error",
    "classify_lexer_error",
    "classify_warning",
]
