# COCKPIT for V3

COCKPIT is a procedural immediate-mode UI package for the shipping V3 compiler.
It follows the primitives V3 actually ships:
integer window handles, indexed `ui::event_*` accessors, raw integer geometry
and colors, explicitly released array handles, and an opaque `ByteBuffer`
layout stack.

Declare COCKPIT as an ordinary Hangar dependency in the consuming project:

```toml
[project]
name = "demo"
version = "1.0.0"
kind = "app"
entry = "src/main.fk"

[dependencies]
cockpit = { path = "../cockpit" }
```

Select the public symbols used by the application. The manifest maps these
names to their declaring modules; sibling modules use explicit `self` imports.
Event, popup, clipping and focus state share one internal module. Mutable state
and implementation helpers are absent from the public exports.

The façade is procedural and single-window. Construct long-lived state once,
reuse it across frames, then release it explicitly:

```fk
use cockpit::{
    cockpit_ui_open, cockpit_ui_should_close, cockpit_ui_begin_frame,
    cockpit_ui_end_frame, cockpit_ui_close, cockpit_widget_heading,
    cockpit_widget_button, cockpit_theme_dark, cockpit_theme_release,
    cockpit_layout_capacity, cockpit_layout_release
}

task main() {
    pilot window = cockpit_ui_open("Demo", 640, 480, true)
    pilot layout: ByteBuffer = ByteBuffer::with_capacity(cockpit_layout_capacity())
    pilot theme = cockpit_theme_dark()

    repeat until cockpit_ui_should_close() {
        cockpit_ui_begin_frame(window, layout, theme)
        cockpit_widget_heading(window, layout, theme, "COCKPIT")
        cockpit_widget_button(window, layout, theme, "Launch", 120)
        cockpit_ui_end_frame(window)
    }

    cockpit_theme_release(theme)
    cockpit_layout_release(layout)
    cockpit_ui_close(window)
}
```

Available mechanics include owned integer/bool/word collections, nested row
and column layout, themes, indexed event processing, labels, buttons,
checkboxes, text inputs, sliders, separators, progress bars, tabs, popup
dropdowns, clipped panels/scrolling, tooltips and modal input capture.

Text input applies delivered events in order. Inputs keep a UTF-8 caret:
Left/Right move by scalar, Up/Down jump to the start/end, a click places the
caret, Backspace and Delete remove one scalar, and long text scrolls
horizontally. Tab and Shift+Tab move focus between inputs (wrapping at the
ends), Enter submits and Escape releases the keyboard. Selection, clipboard
and IME composition still need a richer text model. The platform event queue
is bounded to 64 events; COCKPIT's replay storage holds 256 delivered edits.
The package cannot recover events discarded by the platform.

Keep widget call order stable so sequential widget identifiers preserve focus
and dragging. Callers own widget values, themes and item arrays. The event and
clip tables are owned by `cockpit_ui_open` / `cockpit_ui_close`. Empty frames
reuse these tables; text edits and scalar clip/theme updates may allocate words.

The reusable layout API is the V3 compatibility surface. Ordinary task
parameters typed `ByteBuffer` have move semantics under `--strict-borrow`, and
V3 has no borrowed parameter syntax for these repeated layout calls. These
APIs use the default checking mode; the package does not claim strict borrowed
layout parameters.

Rows and columns pair with `cockpit_container_end(layout)`. A
`cockpit_panel_begin(window, layout, theme, width, height)` pairs with
`cockpit_panel_end(window, layout)`. `cockpit_scroll_begin(window, layout,
theme, width, height, content_height, offset)` returns the clamped offset;
retain that value and pair with `cockpit_scroll_end(window, layout)`.

Call `cockpit_modal_open()` to capture input. Draw the modal after the page:
when `cockpit_modal_begin(window, layout, theme, width, height)` returns true,
draw its content and call `cockpit_modal_end(window, layout)`.
`cockpit_modal_close()` dismisses it.

Dropdown popups draw at end-frame. A selection becomes available to the
control on the next frame. Keep the caller-owned item array and theme alive
while a popup is open. It captures background clicks until selection or
outside-click dismissal; long lists scroll with the wheel. Explicitly call
`cockpit_popup_close()` before releasing an open popup's data. Draw `cockpit_widget_tooltip(window, theme, text,
x, y, width, height)` after page widgets so its overlay remains visible.

Clipping uses the additive `ui::set_clip` and `ui::reset_clip` mechanisms.
COCKPIT owns nested rectangle intersection/restoration; the runtime owns only
the current drawing clip. Layout and clipping have explicit depth bounds.
Widgets use their allocated rectangle for drawing and hit-testing.

The native UI implementation currently ships only for Windows. C and LLVM
source transpilation remain useful portability contracts, but this package
does not claim a native macOS or Linux window backend or a retained widget tree.

## New in 0.2.0

**Keyboard.** `cockpit_widget_input_ex(window, layout, theme, text, width,
placeholder, password)` adds hint text and password masking.
`cockpit_widget_input_submitted()` is true when the input drawn just before it
received Enter. For app shortcuts, `cockpit_ui_shortcut(key, ctrl, shift, alt)`
matches a key pressed this frame with exactly those modifiers held, e.g.
`cockpit_ui_shortcut(cockpit_key_letter("S"), true, false, false)` for Ctrl+S.
`cockpit_ui_key_pressed`, `cockpit_ui_key_presses` and `cockpit_ui_key_down`
give raw access; `cockpit_ui_text_focused()` says whether an input owns the
keyboard. Key codes: `cockpit_key_letter("A")`, `cockpit_key_digit(0)`,
`cockpit_key_function(1)` and the named `cockpit_key_*` constants. Escape also
dismisses an open dropdown.

**Controls.**

- `cockpit_widget_radio(window, layout, theme, selected, items)` returns the chosen index.
- `cockpit_widget_toggle(window, layout, theme, text, on)` is an animated switch.
- `cockpit_widget_stepper(window, layout, theme, value, min, max, step)` has -/+ buttons and wheel stepping.
- `cockpit_widget_list(window, layout, theme, selected, items, visible_rows)` scrolls with the wheel and moves with Up/Down while hovered.
- `cockpit_widget_collapsing(window, layout, theme, title, open)` returns whether to draw the section body.
- `cockpit_widget_badge(window, layout, theme, text, color)` draws a pill label.
- `cockpit_widget_sparkline(window, layout, theme, values, width, height)` and
  `cockpit_widget_bar_chart(window, layout, theme, values, labels, width, height)`
  chart a `cockpit_values_*` series and show values on hover. `labels` may be 0.

Toggle animation and list scrolling live in per-widget memory keyed by call
order, like focus. A widget that lands on another kind's id starts fresh.

**Toasts.** `cockpit_toast(text, cockpit_toast_success)` (or `_info`,
`_danger`) shows a notification in the bottom-right corner for 3 seconds;
`cockpit_toast_timed` sets the duration. Toasts draw at end-frame with the
frame's theme, slide in, fade out and dismiss on click. Up to 8 show at once.
Swap themes between frames, after `cockpit_ui_end_frame`.

**Layout.** `cockpit_grid_begin(layout, columns, gap)` places widgets in
equal-width cells, wrapping rows that are as tall as their tallest cell; a
`cockpit_column_begin(layout, 0, gap)` inside a cell stacks several widgets
there (width 0 now means "fill"). `cockpit_row_begin_aligned(layout, height,
content_width, cockpit_align_center)` (or `_start`, `_end`) offsets a row's
content. Both close with `cockpit_container_end(layout)`.

**Themes.** `cockpit_theme_muvluv()` is red on black.
`cockpit_theme_for_mood("chill" | "focused" | "hype" | "muv_luv" |
"mono_no_aware")` picks the matching theme. `cockpit_theme_copy` and
`cockpit_theme_set(theme, field, color)` customize one; `cockpit_color_mix(a, b,
permille)` blends colors.

**Motion.** `cockpit_ease(cockpit_ease_out_back, t)` maps permille progress
through linear, quad, cubic, back and bounce curves. `cockpit_animate(slot,
target, duration_ms)` tweens one of 64 slots toward a target using the frame
clock (`cockpit_ui_delta_ms()`); `cockpit_animate_reset` snaps it. Buttons now
fade their hover color.

Examples:

- `examples/smoke.fk` — bounded 30-frame lifecycle smoke
- `examples/showcase.fk` — the supported widget/layout surface
- `examples/calculator.fk` — procedural calculator state
- `examples/settings.fk` — name, notification toggle, slider, theme dropdown and confirmation modal; settings apply to the current session
- `examples/mission_control.fk` — the 0.2.0 tour: grid dashboard, live sparkline, bar chart, list, radio, toggles, stepper, a Tab/Enter form, mood themes, Ctrl+L/Ctrl+T shortcuts, an eased readiness bar and toasts

The calculator, settings, showcase and mission control run until window close. The separate
smoke is bounded to 30 frames.

`freak test --manifest-path=packages/cockpit/hangar.toml` runs the declared pure
collection/theme/layout assertions. Examples are declared source modules and
can be selected explicitly with the same manifest.

`python -u tests/v3_v35_cockpit_package.py --repo . --freak <fresh-freak>
--clang <clang> --evidence <report.json>` checks a separate declared consumer,
private export rejection, and shared state through C and LLVM. Its deterministic
replays (`tests/replay.fk`, `tests/replay_input.fk`, `tests/replay_widgets.fk`) supply drawing/event functions at the native platform ABI and keeps
the package source unchanged. `--runtime-root` selects the exact runtime
payload. This replay does not replace the Windows native window gate.
