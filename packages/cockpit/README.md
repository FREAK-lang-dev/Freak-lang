# COCKPIT

COCKPIT is the preserved source preview for FREAK's immediate-mode UI
framework. Its supported implementation belongs to Maverick / 00-Unit; the
frozen V3 compiler does not provide a complete executable COCKPIT surface.

It is built on top of `std::ui` and gives you:
- layout
- widgets
- themes
- input handling
- simple animation helpers

No widget trees. No callbacks. No retained-mode ceremony. The source records
the intended call-in-order design, but it is not a V3 release package.

## Preserved design sketch

The following shows the intended Maverick-facing API. It is kept as design
evidence and is not expected to build on frozen V3:

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

## Preserved themes

- `Theme::default()`
- `Theme::light()`
- `Theme::terminal()`
- `Theme::alternative()`
- `Theme::muvluv()`

## Design examples

- [`examples/showcase.fk`](./examples/showcase.fk)
- [`examples/calculator.fk`](./examples/calculator.fk)

Legacy note: older docs may still refer to this package as `freak-ui`. The official public name is now `cockpit`.

V3 does retain a smaller `std::ui` floor for LLVM builds on Windows using the
Win32/GDI runtime. That floor exposes indexed raw events and drawing calls; it
does not provide COCKPIT's collection/widget requirements, a POSIX UI backend,
or executable C-backend shape storage.
