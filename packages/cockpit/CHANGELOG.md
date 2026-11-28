# Changelog

## 0.2.0 "kyuushin"

* Real text editing: a UTF-8 caret moved with Left/Right, Up/Down jumping to
  the start or end, click to place the caret, Delete as well as Backspace,
  and long text scrolling horizontally. Placeholders and password fields via
  `cockpit_widget_input_ex`.
* Keyboard focus: Tab and Shift+Tab move between inputs (wrapping at the
  ends), Enter submits (`cockpit_widget_input_submitted`), Escape releases the
  keyboard.
* Shortcuts: `cockpit_ui_shortcut(key, ctrl, shift, alt)` plus key helpers
  (`cockpit_key_letter`, `cockpit_key_digit`, `cockpit_key_function`, arrows,
  Enter, Escape, Tab, Space, Delete, Backspace) and `cockpit_ui_key_down` /
  `cockpit_ui_key_pressed`.
* New controls: radio groups, an animated toggle, a number stepper, a
  scrollable selectable list with arrow-key movement, collapsible sections
  and badges.
* Charts: sparklines and bar charts.
* Toasts that slide in and fade out (`cockpit_toast_info` / `_success` /
  `_danger` / `_timed`).
* Layout: grids and start/center/end aligned rows.
* Themes: the red-on-black `muvluv` theme, `cockpit_theme_for_mood`, and
  `cockpit_color_mix`.
* Motion: easing curves (`cockpit_ease_*`), `cockpit_lerp`,
  `cockpit_approach`, and per-id tweens (`cockpit_animate`). Buttons fade on
  hover.
* New example: `examples/mission_control.fk`, a dashboard using all of it.
* Behaviour changes: clicking in a text field now puts the caret where you
  click (it used to jump to the end), and buttons behind an open modal no
  longer light up on hover.
* Collapsing headers draw `>` / `v` and password fields draw `*`, all ASCII,
  because the Windows backend still draws text through the ANSI calls.

## 0.1.0

* First release on the Hangar registry: COCKPIT, the procedural
  immediate-mode UI package for the V3 compiler (Windows backend).
* Single-window façade (`cockpit_ui_open`, `begin_frame`/`end_frame`), owned
  integer/bool/word collections, nested row and column layout, four themes
  (dark, light, terminal, alternative), and indexed event processing.
* Widgets: labels, headings, buttons, checkboxes, text inputs, sliders,
  separators, progress bars, tabs, popup dropdowns, clipped panels and
  scrolling, tooltips, and modal input capture.
