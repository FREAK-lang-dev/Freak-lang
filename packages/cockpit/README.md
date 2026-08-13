# COCKPIT V3 compatibility façade

COCKPIT includes a source-only façade that the shipping self-hosted V3
compiler can check and transpile. It follows the primitives V3 actually ships:
integer window handles, indexed `ui::event_*` accessors, raw integer geometry
and colors, explicitly released array handles, and an opaque `ByteBuffer`
layout stack.

The façade is procedural and single-window. Construct long-lived state once,
reuse it across frames, then release it explicitly:

```fk
pilot window = cockpit_ui_open("Demo", 640, 480, true)
pilot layout: ByteBuffer = ByteBuffer::with_capacity(cockpit_layout_capacity())
pilot theme = cockpit_theme_dark()

repeat 120 times {
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
checkboxes, a basic text input, separators, progress bars, tabs, and a compact
dropdown that cycles its selection when clicked.

The basic input appends indexed character events but its backspace operation is
byte-oriented; applications that require full Unicode grapheme editing should
provide a dedicated text model above this floor.

The native UI implementation currently ships only for Windows. C and LLVM
source transpilation remain useful portability contracts, but this package
does not claim a native macOS or Linux window backend. Clipping, modal input
capture, scrolling, retained widget trees, and popup dropdown guarantees are
not part of this compatibility floor.

Examples:

- `examples/smoke.fk` — bounded 30-frame lifecycle smoke
- `examples/showcase.fk` — the supported widget/layout surface
- `examples/calculator.fk` — procedural calculator state
