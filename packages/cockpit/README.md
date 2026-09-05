# COCKPIT for V3

COCKPIT is a procedural immediate-mode UI package for the shipping V3 compiler.
It follows the primitives V3 actually ships:
integer window handles, indexed `ui::event_*` accessors, raw integer geometry
and colors, explicitly released array handles, and an opaque `ByteBuffer`
layout stack.

The façade is procedural and single-window. Construct long-lived state once,
reuse it across frames, then release it explicitly:

```fk
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
```

Available mechanics include owned integer/bool/word collections, nested row
and column layout, themes, indexed event processing, labels, buttons,
checkboxes, text inputs, sliders, separators, progress bars, tabs, popup
dropdowns, clipped panels/scrolling, tooltips and modal input capture.

Text input applies delivered character/backspace events in order. Backspace
removes a UTF-8 scalar; grapheme navigation, selection, clipboard and IME
composition require a richer text model. The current platform event queue is
bounded to 64 events; COCKPIT's replay storage holds 256 delivered edits. The
package cannot recover events discarded by the platform.

Keep widget call order stable so sequential widget identifiers preserve focus
and dragging. Callers own widget values, themes and item arrays. The event and
clip tables are owned by `cockpit_ui_open` / `cockpit_ui_close`. Empty frames
reuse these tables; text edits and scalar clip/theme updates may allocate words.

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

Examples:

- `examples/smoke.fk` — bounded 30-frame lifecycle smoke
- `examples/showcase.fk` — the supported widget/layout surface
- `examples/calculator.fk` — procedural calculator state
- `examples/settings.fk` — name, notification toggle, slider, theme dropdown and confirmation modal; settings apply to the current session

The calculator, settings and showcase run until window close. The separate
smoke is bounded to 30 frames.

`python -u tests/v3_cockpit_compat.py [fresh-freak]` executes deterministic
event/layout/widget replays on C and LLVM and checks/links examples. On Windows
it launches their native windows and sends `WM_CLOSE` only to its child
process's own window, then verifies shutdown and ownership audits.
`--runtime-root` selects the exact runtime payload to link.

`--replay-only` executes and links against injected drawing/event functions
without native windows. It does not replace the Windows native gate.
