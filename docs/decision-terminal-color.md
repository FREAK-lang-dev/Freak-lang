# Terminal Color API — Decision Record (spec-only)

Status: **decided, not implemented**. This document records the contract and
the std-vs-package split so implementations converge. No code changes ship
with it; the estimated implementation touches two runtimes and exceeds the
50-line threshold for bundling code with a decision doc.

## Observed state (evidence)

- `freakc/diagnostics.py::_supports_color()`: disables on `NO_COLOR` (set and
  non-empty), forces on with `FORCE_COLOR`, otherwise colors only when
  `sys.stderr` is a TTY. This is the most complete contract in-tree.
- `freakc/__main__.py::_c()`: checks `sys.stderr.isatty()` only — honors
  non-TTY but ignores `NO_COLOR`/`FORCE_COLOR`, contradicting diagnostics.py.
- `src/cli/version.fk::cli_configure_output()`: disables colors when
  `NO_COLOR` is non-empty or `FREAK_NO_COLOR` is truthy; selects ASCII vs
  Unicode decorations via `FREAK_ASCII` / `FREAK_UNICODE` with a legacy-Windows
  fallback. It never checks TTY-ness, so piped native output stays colored
  unless the user opts out.

## Decision

1. **One contract, both runtimes.** Colored output is enabled only when ALL
   of the following hold:
   - `NO_COLOR` is unset or empty (per https://no-color.org: present and
     non-empty means off), AND `FREAK_NO_COLOR` is not truthy
     (`1`/`true`/`TRUE`/`yes`/`YES`), AND
   - the target stream is a TTY, OR `FORCE_COLOR` is set (Python) /
     a future `FREAK_FORCE_COLOR` is truthy (native) to override non-TTY.
2. **Stream rule.** Diagnostics color follows `stderr`; human progress output
   follows `stdout`. A check must query the stream it guards — the current
   `__main__._c()` (stderr probe for all output) is grandfathered but new
   code probes per-stream.
3. **Unicode rule.** Keep the existing `FREAK_ASCII` / `FREAK_UNICODE`
   override pair and the legacy-Windows ASCII default; ASCII mode must also
   strip box-drawing/symbol glyphs (as `cli_use_ascii_decorations` does),
   not just colors.

## std vs package split

- **NOT a third-party Hangar package.** Color touches diagnostics, CLI
  progress, and every backend's error path — it must work before any package
  can load and identically in `freakc` and the native CLI.
- **NOT duplicated per-crate in V4 either.** The decision is: one `std`
  surface (provisional name `std::term`: `supports_color(stream)`,
  `paint(code, text)`, `ascii_mode()`) owned by the Ministry of the Shelves,
  with thin per-runtime shims (Python `diagnostics.py`, native `version.fk`)
  delegating to it. V4 crates consume `std::term`; they do not reimplement
  TTY/`NO_COLOR` probing.

## Exit condition

This record closes when `__main__._c()` honors `NO_COLOR`/`FORCE_COLOR` and
the native CLI honors non-TTY — verified by a non-TTY pipe test asserting
zero escape bytes with `NO_COLOR` set, piped, and unset respectively.
