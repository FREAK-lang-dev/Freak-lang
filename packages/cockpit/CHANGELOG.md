# Changelog

## 0.3.0 "zero-shiki"

* The `Cockpit` shape: `pilot p = sortie("Title", 640, 480)`, then
  `repeat until p.landed() { p.heading("Hi") ... p.over() }` and `p.land()`.
  Every widget is a method (`p.button`, `p.input_hint`, `p.slider`,
  `p.progress`, `p.dropdown`, `p.row` / `p.end`, `p.modal`, `p.toast_success`
  and the rest), with the window, layout and theme kept inside.
  `sortie_painted` takes your own theme and `p.color(cockpit_theme_success)`
  reads one of its colors.
* The black box: each frame is recorded as a list of draw commands (clear,
  fill, stroke, circle, line, text, clip) before it reaches the window.
  `cockpit_blackbox_count`, `_field`, `_text`, `_line`, `_dump` and
  `_find_text` read the last frame back.
* The flight sim: `cockpit_flight_open(w, h)` flies a cockpit with no window.
  Queue what the pilot does (`cockpit_flight_click_text("Launch")`,
  `cockpit_flight_type`, `cockpit_flight_key`, `cockpit_flight_chord`,
  `cockpit_flight_wheel`, `cockpit_flight_quit`), run a frame, check the black
  box. Animations follow a fixed clock, so a run is the same every time. The
  procedural flight API needs no window backend, so tests run on any OS.
  `sortie_sim(w, h)` is the same thing for the `Cockpit` shape.
* Frame drivers: `sortie_hosted(theme)` with `cockpit_frame_start` /
  `cockpit_frame_finish` lets another package draw the frames somewhere else.
  `cockpit-uplink` uses it to show a cockpit in a browser tab.
* Text width comes from the window's real font: COCKPIT measures each size
  once and keeps the advances, so `cockpit_blackbox_measure` and layout agree
  with what is drawn.
* New example: `examples/sortie.fk`, a pre-flight checklist written with the
  `Cockpit` shape.
* Fixed: keys typed in the same frame as a Shift+Tab (or a Tab that wraps to
  the first field) were dropped. They now land in the field that gets focus,
  one frame later. If a click follows in the same frame, the keys before the
  click still go to that field and the keys after it to the clicked one.
* `cockpit_ui_shortcut` checks the modifiers that were held when the key went
  down, so a Ctrl+S whose Ctrl comes back up before the frame begins still
  counts (`cockpit_flight_chord` relies on this).
* Text sizes are kept to 1-96 px, for measuring and drawing alike (a bigger
  theme font draws at 96).
* Fixed: closing a window or a sim frees all of COCKPIT's state.
* Toasts and the caret blink follow COCKPIT's frame clock (the sum of each
  frame's time) instead of the wall clock, so the flight sim replays them
  exactly.
* Note: the `Cockpit` shape still links the native window calls, so
  `sortie(...)` programs build on Windows only until the Linux and macOS
  window backends arrive with Freak-lang 0.17.

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
