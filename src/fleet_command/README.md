# Fleet Command

`Fleet Command` is the first serious game-shaped stress test for FREAK inside the main language repository.

The target is not a full `Rule the Waves 3` clone. The target is a hard vertical slice that proves:

- FREAK can hold a medium-sized game state without collapsing into rewrite hell.
- The current UI/runtime stack can drive a native management game window.
- The language is comfortable for turn logic, AI turns, event logs, and battle resolution.
- We can debug compiler/runtime issues faster while the game lives next to the language itself.

## Current Scope

This first slice is intentionally narrow:

- Single-player.
- Native desktop window.
- Main menu, campaign screen, and ship-designer screen.
- Fleet management for one player nation versus one AI opponent.
- Selectable real-world nations: Britain, Germany, USA, Japan, France, Russia.
- A hand-drawn world-theater map with named sea zones instead of an abstract arena.
- Ship design math that feeds live build cost, build time, maintenance, and combat rating.
- Ship construction queue.
- Monthly turn advancement.
- Contact generation and battle resolution.
- Event log and basic theater display.

Not in scope for the first slice:

- Multiplayer.
- Networking.
- Cross-platform packaging.
- Historical hull design depth.
- Tactical ship movement.
- Save/load.

Those come after the local loop is fun and stable.

## Build

From the repository root:

```powershell
python -m freakc check src\fleet_command\main.fk
python -m freakc build src\fleet_command\main.fk
```

On Windows this produces:

```text
src\fleet_command\main.exe
```

## Controls

- Mouse: click buttons
- Mouse: use the main menu to start campaign or open the design bureau
- Mouse: click nation buttons to restart as a different country
- `Space`: advance month
- `Enter`: engage current contact
- `Escape`: back to menu or quit from menu

## Current Feel

The presentation now aims for a more normal strategy-game shell: flatter panels, quieter colors, a real menu, a campaign map, and a separate design bureau. It still needs deeper ship systems, but the structure is finally pointing in the right direction.

## Why It Lives Here For Now

Keeping the prototype in this repository is deliberate. If the window runtime, compiler, stdlib, or build flow breaks under real game pressure, we want the failure close to the language source until the slice is solid enough to extract.
