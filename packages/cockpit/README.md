# COCKPIT

COCKPIT is FREAK's official immediate-mode UI framework.

It is built on top of `std::ui` and gives you:
- layout
- widgets
- themes
- input handling
- simple animation helpers

No widget trees. No callbacks. No retained-mode ceremony. You call UI functions in order and the frame renders.

## Install

```toml
[dependencies]
cockpit = { git = "https://github.com/FREAK-lang-dev/Freak-lang", version = "latest" }
```

## Use

```fk
use std::ui::{Window, WindowConfig}
use cockpit::{UI, Theme, label_heading}

@protagonist
task main() {
    pilot win = Window::open(WindowConfig {
        title: "COCKPIT Demo",
        width: 640,
        height: 480,
        resizable: true,
        vsync: true
    })

    pilot ui = UI::new(win, Theme::default())

    repeat until ui.should_quit {
        ui.begin_frame()
        ui.label_styled("COCKPIT", label_heading)
        ui.label("Immediate-mode UI for FREAK.")
        ui.end_frame()
    }

    win.close()
}
```

## Themes

- `Theme::default()`
- `Theme::light()`
- `Theme::terminal()`
- `Theme::alternative()`
- `Theme::muvluv()`

## Examples

- [`examples/showcase.fk`](./examples/showcase.fk)
- [`examples/calculator.fk`](./examples/calculator.fk)

Legacy note: older docs may still refer to this package as `freak-ui`. The official public name is now `cockpit`.
