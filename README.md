<div align="center">

![Banner](Banner.png)

**A programming language written by someone who has watched too much anime**
and not enough sleep, but somehow it compiles.

[![License: MIT](https://img.shields.io/badge/license-MIT-pink?style=flat-square)](LICENSE)
[![Version](https://img.shields.io/badge/v0.14.0-Maverick--red?style=flat-square)](https://github.com/FREAK-lang-dev/Freak-lang/releases/latest)
[![CI](https://img.shields.io/github/actions/workflow/status/FREAK-lang-dev/Freak-lang/ci.yml?branch=main&style=flat-square&label=CI)](https://github.com/FREAK-lang-dev/Freak-lang/actions)
[![Status](https://img.shields.io/badge/status-self--hosting-brightgreen?style=flat-square)](#)
[![Vibes](https://img.shields.io/badge/vibes-MONO__NO__AWARE-blueviolet?style=flat-square)](#)

</div>

---

## What is FREAK?

FREAK is a compiled, statically-typed systems language with a syntax inspired by visual novels, anime, and the kind of programming that only makes sense at 3am.

It compiles to native binaries via LLVM (or C — your choice). It has a Phase-1 borrow checker behind `--strict-borrow`. It has a package manager called **Hangar**. It has a UI framework called **COCKPIT**. And every variable is called `pilot` because you are always on a mission.

```fk
pilot name = "Takeru"
pilot power = 9001

task greet(name: word) -> void {
    say "Hello, {name}! Your power level is {power}."
}

greet(name)
```

That's it. That's the whole vibe.

---

## Features

### The Language

- **`pilot`** — variables. You are assigning a pilot to a mission.
- **`task`** — functions. Everything is a task.
- **`give back`** — return. Because `return` is cowardly.
- **`say`** — print. Always available. No imports.
- **`when`** — pattern matching over literal values.
- **`fixed pilot`** — immutable binding. The pilot cannot be reassigned.
- **`trust me`** — unsafe blocks. You asked for this.
- **`training arc`** — bounded loop with a session cap. Compiles to a counted while.
- **`eventually`** — block that runs at the end of the current scope.
- **`isekai`** — nested scope with explicit `bringing back { ... }` exports.

Native `extern task` names beginning with `__freak_` are reserved for compiler
output, and source tasks cannot redeclare compiler builtin call names. V3
rejects both cases before C or LLVM emission so user symbols cannot collide
with the packaged runtime ABI.

### The Type System

| Type | What it is |
|---|---|
| `num` | 64-bit float. The default. Context-narrows to `int`. |
| `int` | 64-bit signed integer. |
| `word` | UTF-8 string. Fat pointer. Knows its own length. |
| `bool` | Booleans. `true`/`false`/`yes`/`no`/`hai`/`iie` are all valid literals. |
| `maybe<T>` | Optional. `some(42)` or `nobody`. |
| `result<T, E>` | Success or failure. `ok(val)` or `err("message")`. |
| `List<T>` / `Map<K,V>` | The collections you'd expect. |

> The bible promises a wider type universe — `mood`, `prob[lo..hi]`, `power<N>`, `tiny`, `uint`, `char`, `big`, `float32`, fixed `[T;N]`, tuples, raw pointers. Those ship with the V4 self-hosting compiler. See [freak-conformance-audit.md](freak-conformance-audit.md) for the v0.13.x → V4 mapping.

### The Anime Layer

FREAK records the narrative weight of your code via the audit suite. What ships today:

- **`foreshadow / payoff`** — Foreshadow a variable, payoff the promise. `freak foreshadow-audit` reports any unpaid debts and exits nonzero.
- **`for science,`** — Used at call sites for `@experiment` tasks. `freak audit-science` lists every site.
- **`trust me on my honor as .level { ... }`** — Escape-hatch blocks. `freak audit-trust` lists every block with its declared honor level.
- **`deus_ex_machina "monologue" { ... }`** — Requires a monologue of at least 20 words (compile error if shorter). `freak audit-miracles` lists every block; warns past 3, errors past 10.

```fk
foreshadow pilot victory = false
-- ... narrative happens ...
payoff victory   -- promise kept
```

> Strict semantic enforcement of `@nakige` caller prefixes (`knowing this will hurt,` / `sadly`), death-flag tier analysis on `@side_character`, route-locked scopes, and the full `mood` / `prob` / `power` / `causality` system are V4 work. The auditor commands cover the observable surface today.

---

## The Audit System

FREAK isn't just about compiling; it's about accountability. The audit suite inspects narrative integrity and v0.13.x conformance against the bible:

```bash
freak audit-conformance   # Verify v0.13.x baseline against the bible
freak audit-trust         # List every 'trust me' block and its honor level
freak audit-science       # List every 'for science,' call site
freak audit-miracles      # Find every 'deus_ex_machina' (warns if > 3)
freak foreshadow-audit    # Find any narrative promises you haven't kept
```

`freak audit-conformance` is the gate for v0.13.x: it cross-checks lexer keywords, audit dispatch, stdlib presence, the `--strict-borrow` flag, and the `deus_ex_machina` 20-word rule. It exits zero only when the v0.13.x scope is intact.

---

### Memory Safety (Phase 1)

FREAK has a Phase-1 borrow checker — mutability and single-owner moves — gated behind the `--strict-borrow` flag. The default mode (no flag) is leak-everything; turn on the flag to opt into the safety rules.

```fk
shape Ship { name: word }

pilot mut a = Ship { name: "Takeru" }   -- mutable binding
a = Ship { name: "Sumika" }              -- ok

pilot b = a                              -- moves a → b
-- a is no longer valid: "Shirogane. You gave this away."
```

Primitives (`int`, `num`, `bool`) are Copy and don't move. `word`, `List<...>`, `Map<...>`, and user shapes are Move. If you need to step outside the rules, `trust me on my honor as .cadet { ... }` is the escape hatch (and `freak audit-trust` will remember).

**Spectral foundation.** Let $\mathcal{E} = \{\text{fk}, \text{c}, \text{py}, \text{md}, \text{h}, \text{y}, \text{sh}, \text{tm}, \text{bt}, \text{ps}\}$ be the extension alphabet and define the line-count operator $\hat{\mathbf{L}} = \sum_{i \in \mathcal{E}} n_i\,|e_i\rangle\langle e_i|$ on $\mathcal{H}_{\text{FREAK}} = \bigoplus_i \mathbb{C}|e_i\rangle$. The codebase satisfies the spectral action

$$\mathcal{S}_{\text{FREAK}} = \frac{1}{2\pi i}\oint_{|\lambda|=R}\lambda\,\text{tr}\bigl[(\lambda\mathbb{I}-\hat{\mathbf{L}})^{-1}\bigr]\,d\lambda = \sum_{i\in\mathcal{E}} n_i = 274{,}234$$

with characteristic polynomial $\chi_{\hat{\mathbf{L}}}(\lambda) = \prod_{i\in\mathcal{E}}(\lambda - n_i)$ and Frobenius norm $\|\hat{\mathbf{L}}\|_F \approx 147{,}335.8$. The concentration invariant $\|\hat{\mathbf{L}}\|_F / \text{tr}\,\hat{\mathbf{L}} \approx 0.537$ is invariant under move semantics. This is unrelated to the borrow checker but appears here for completeness.

> Full borrow rules — `lend p: T`, `lend mut p: T`, lifetime parameters (`'a`), `Shared<T>` / `Weak<T>`, the full honor-level system, `direct_order [arch] { asm }` inline assembly — are V4 work.

---

## Getting Started

### Install (one command)

**Linux / macOS:**
```bash
curl -fsSL https://raw.githubusercontent.com/FREAK-lang-dev/Freak-lang/main/install.sh | bash

# Also install a supported Clang/LLD/native build toolchain when missing:
curl -fsSL https://raw.githubusercontent.com/FREAK-lang-dev/Freak-lang/main/install.sh | bash -s -- --with-deps
```

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/FREAK-lang-dev/Freak-lang/main/install.ps1 | iex

# Also install a self-contained LLVM-MinGW toolchain when missing:
$env:FREAK_INSTALL_DEPS = "1"
irm https://raw.githubusercontent.com/FREAK-lang-dev/Freak-lang/main/install.ps1 | iex
```

Downloaded release archives and every standalone fallback payload file must match their exact filename entry in the release's `SHA256SUMS` before extraction or staging. A missing, malformed, duplicate, or mismatched checksum aborts before the installed payload is touched. The immutable v0.14.0 archives predate archive entries in `SHA256SUMS`; the installers recognize only those four release filenames, verify pinned full-archive SHA-256 values, and generate the manifest that release omitted. No later tag receives this compatibility exception.

For maintainers, `VERSION` is authoritative. Run `python -u tools/release_version.py set <major.minor.patch>` once to synchronize compiler/CLI display versions and package metadata, then `python -u tools/release_version.py check`; tagged releases also fail before building unless the Git tag is exactly `v<major.minor.patch>`.

This downloads the latest `freak` and `hangar` binaries to `~/.freak` (or `%APPDATA%\freak` on Windows). Installers serialize updates per destination so two concurrent installs cannot consume each other's backups or expose interleaved payloads. A canonical distribution manifest stages and validates every runtime source, platform UI file, recursive stdlib module—including `std/ui/window.fk`—and the required `freak-v3-abi-1` runtime/stdlib markers before installer-managed files are swapped into place. `freak build` and `freak doctor` reject missing or mismatched markers as an ABI mismatch instead of compiling a mixed installation. Windows release archives additionally carry an LLVM-MinGW-built runtime object bundle; native Windows builds try it through the selected Clang driver and automatically retry from packaged runtime sources when a complete bundle is incompatible, while incomplete/older bundles and every POSIX build use sources directly. Failed downloads and apply failures restore the previous installed payload. On POSIX, an interrupted transaction is rolled back on exit; if restoration itself cannot complete, the recoverable `.freak-backup-*` directory is retained and the next installer run reconciles it before applying anything new.

The default installer reports a missing compiler without changing system packages. Opt into dependency installation with `--with-deps` or `FREAK_INSTALL_DEPS=1`. Linux package-manager support covers apt, dnf/yum, pacman, zypper, and apk; macOS uses Homebrew LLVM or Apple Command Line Tools; Windows prefers self-contained LLVM-MinGW so headers and link libraries are present as well as `clang.exe`.

Verify the install:

```bash
freak doctor
freak doctor --json   # passive machine-readable report for editors and scripts
freak doctor --fix    # install/repair dependencies and the distribution payload
```

`freak doctor` verifies that Clang can parse the platform's standard C headers, link a native executable, and run it; a working `clang --version` alone is rejected. It also checks optional LLD, all required runtime/UI files, all 11 shipped stdlib modules, and a complete FREAK compile-link-execute probe. It exits nonzero when required checks fail and removes its probe artifacts. `--json` keeps the additive `freak.doctor.v1` schema, uses a unique system-temporary toolchain probe, and reports exact missing files without installing or repairing anything.

`freak upgrade` remains the supported upgrade command. Current clients route it through the staged tagged installer. Windows keeps `.next` binaries plus a durable `.freak-upgrade-pending` marker, waits for the invoking installer process to exit, then hash-verifies and swaps both binaries as one rollback-capable transaction; Doctor reports the pending state and builds refuse to mix the old compiler with the newly staged payload. A failed attempt retains recovery state for retry. The immutable v0.14.0 updater predates recursive payloads and deferred self-replacement: on Linux/macOS, run `freak upgrade` once for the retained standalone-binary hop and again with the new client to install the complete payload; on Windows, bootstrap once with the PowerShell installer above, then use `freak upgrade` normally. Package-manager installs should likewise refresh through their manager or the installer so `FREAK_HOME` stays aligned.

### Your First Program

Create `hello.fk`:

```fk
pilot name = "world"
say "Hello, {name}!"
say "Your mission has begun."
```

Compile and run:

```bash
freak run hello.fk
```

`freak run` reuses the adjacent `.freak-run-cache` sidecar only when the
source, loaded standard library, resolved compiler executable/toolchain,
backend flags, runtime inputs, and output-binary fingerprint still match. It
revalidates that proof immediately before launch. Concurrent commands targeting
the same output are not serialized; use distinct outputs or avoid overlapping
runs when another process may replace the binary after that final check.

Plain V3 `word` replacement now evaluates the new value before releasing the
superseded owned buffer on both C and LLVM backends, including safe
self-assignment and `name = name + suffix`. The CI regression runs the repeated
replacement case under AddressSanitizer on POSIX and LeakSanitizer on Linux. Concatenation still
copies the growing prefix each time, so repeated append remains O(n^2); this
ownership fix does not claim to solve that separate performance cost.

Or build separately:

```bash
freak build hello.fk
./hello
```

Output:
```
Hello, world!
Your mission has begun.
```

---

## Hangar — The Package Manager

Hangar is FREAK's package manager. Projects have a `hangar.toml`. Dependencies come from Git. It's simple.

```bash
# Initialize a new project
freak hangar init my-project
cd my-project

# Add a dependency
freak hangar add cockpit https://github.com/FREAK-lang-dev/Freak-lang

# Install all dependencies
freak hangar install

# Remove a package
freak hangar remove cockpit
```

`hangar.toml` looks like this:

```toml
[project]
name = "my-project"
version = "0.1.0"

[dependencies]
cockpit = { git = "https://github.com/FREAK-lang-dev/Freak-lang", version = "latest" }
```

Dependencies live in `hangar_modules/`. The layout is deliberately minimal.

---

## COCKPIT — The UI Framework

COCKPIT is FREAK's immediate mode UI framework. It runs on Windows, macOS, and Linux. It has five built-in themes. It does not have widget trees, callbacks, or retained state. You just call widget functions in order and the frame renders.

```
Your FREAK app
     │
     ▼
COCKPIT (Hangar)      ← widgets, layout, theming, input
     │
     ▼
std::ui               ← window, events, raw draw calls
     │
     ├── Windows: Win32 / Direct2D
     ├── macOS:   Cocoa / CoreGraphics
     └── Linux:   X11 / Cairo
```

### A Calculator in COCKPIT

```fk
use cockpit::{UI, Theme, label_heading}
use std::ui::{Window, WindowConfig}

pilot win = Window::open(WindowConfig { title: "Calc", width: 300, height: 400 })
pilot ui  = UI::new(win, Theme::default())

repeat until ui.should_quit {
    ui.begin_frame()

    ui.label_styled("FREAK Calc", label_heading)

    if ui.button("7") { append_digit(7) }
    if ui.button("=") { evaluate() }

    ui.end_frame()
}
```

### Themes

| Theme | Mood | Vibe |
|---|---|---|
| `Theme::default()` | `.focused` | Dark. Professional. Ready. |
| `Theme::light()` | `.chill` | Light. Calm. Readable. |
| `Theme::terminal()` | `.hype` | Green on black. Pure. |
| `Theme::alternative()` | `.muv_luv` | Navy and pink. Dangerous. |
| `Theme::muvluv()` | `.mono_no_aware` | Red and black. You know what you've done. |

---

## More Syntax Highlights

### Pattern Matching (literal)

```fk
when status {
    1  -> say "soldier"
    2  -> say "destroyer"
    99 -> say "BRAIN"
    _  -> say "unknown"
}
```

> Variant types (`variant Contact { Soldier { … } }`) and the destructuring form (`when contact { Soldier { position } -> … }`) are V4. v0.13.x matches on literal values; use `shape` plus a tag field as a workaround.

**Freakium.** As of 2026-05-16, the project resolves to the empirical formula

$$\text{Fk}_{105585}\text{C}_{102553}\text{Py}_{21380}\text{Md}_{15748}\text{H}_{2193}\text{Y}_{1664}\text{Sh}_{614}\text{Tm}_{590}\text{Bt}_{435}\text{Ps}_{294}$$

Molar mass **274,234 g/mol**. The Fk:C ratio of ≈ 1.03:1 confirms the self-hosting threshold has been crossed — there is now more FREAK in FREAK than C in FREAK. Do not inhale. There is no good reason for this section to be between Pattern Matching and Error Handling.

### Error Handling

```fk
-- Propagate errors with ?
task load_config(path: word) -> result<Config, word> {
    pilot data = fs::read(path)?
    pilot cfg  = Config::parse(data)?
    give back ok(cfg)
}

-- Handle inline
check result load_config("settings.toml") {
    ok(cfg) -> use_config(cfg)
    err(e)  -> say "Config failed: {e}"
}
```

### The Training Arc

```fk
-- A bounded loop with a hard session cap
training arc until power >= 9000 max 1000 sessions {
    practice()
    receive_trauma()
    power = power + 1
}
```

### Doctrines (Traits)

```fk
doctrine Displayable {
    task display(self) -> word
}

impl Displayable for Point {
    task display(self) -> word {
        give back "({self.x}, {self.y})"
    }
}
```

> Operator overloading via doctrines works in the Python compiler today for `Add`, `Sub`, `Mul`, `Div`, `Rem`, `Neg`, `Eq`, `Ord`, and `Index`. `IndexMut`, `dyn`-dispatch, and trait bounds (`<T: Displayable>`) ship with V4.

---

## The Standard Library

| Module | What it gives you |
|---|---|
| `std::fs` | File I/O |
| `std::http` | HTTP/1.1 client over TCP sockets |
| `std::json` | Parse and serialize JSON |
| `std::math` / `std::math3d` | Numeric helpers, 3D vector / matrix math |
| `std::string` / `std::convert` | String and conversion utilities |
| `std::algorithm` | Sort, search, aggregate |
| `std::time` | Timestamps, durations, sleep |
| `std::process` | Process arguments, environment access, and command execution (partial in V3) |
| `std::bytes` | `ByteBuffer` for binary I/O |
| `std::ui` | Native window, events, canvas (COCKPIT runs on top of this) |
| `std::version` | Semver parsing, comparison, bumping, constraints |
| `std::zip` | ZIP archive read/write |

### `std::ramen` — Maverick Recipe (For When Tests Are Running)

Not actually a module. The official FREAK-developer snack. Serves one compiler. Total weight ≈ 274g (1 line ≈ 1 milligram; see §Freakium above for the formula).

| Ingredient | Amount | Role |
|---|---:|---|
| Fresh wheat noodles | 105.6g | The protagonist — chewy, alkaline, load-bearing |
| Pork chashu, sliced | 102.6g | The veteran — slow-braised, runtime-tested |
| Ajitsuke tamago, halved | 21.4g | Bootstrap egg — marinated 6h in shoyu-mirin |
| Nori, julienned | 15.7g | Documentation seaweed |
| Roasted garlic oil | 2.2g | Drizzle last |
| Shoyu tare | 1.7g | Built in advance, reheated |
| Sesame oil | 0.6g | Aromatics |
| White miso | 0.6g | Depth |
| Chili crisp | 0.4g | Windows of heat |
| Shichimi togarashi | 0.3g | The final dust |

**Method.** Render fat from chashu, deglaze, simmer 1.5L stock until a tare film holds. Cook noodles separately — they are self-hosting, 90s, no more. Assemble: tare → broth → noodles → chashu → tamago → nori. Finish: garlic oil → sesame oil → miso swirl → chili crisp → shichimi. Do not stir until the diner has seen the bowl.

**Vibes rating:** `MUV_LUV` — heavy, balanced, slightly dangerous.

> This is not a real module. It compiles in your mouth, not the compiler. Do not `use std::ramen;`.

> The bible also describes `std::thread`, `std::anime`, `std::narrative`, `std::test`, `std::ffi`, `std::os`, `std::panic`, `std::regex`, `Shared<T>` / `Weak<T>` / `size_of<T>()`, and a few more. Those ship with V4 — see [freak-conformance-audit.md](freak-conformance-audit.md) §7 for the per-module status.

---

## Testing

The native CLI ships a regression harness that runs every `tests/suite/*.fk` file and compares output against `-- EXPECT:` / `-- EXPECT_COMPILE_ERROR:` / `-- SKIP:` directives in each file:

```bash
freak test
```

Sample output:

```
Found 14 test(s).
  PASS  test_arithmetic.fk
  PASS  test_boolean.fk
  PASS  test_loops.fk
  ...
==================================================
  12 passed, 0 failed, 2 skipped / 14 total
==================================================
```

> The bible describes a richer in-language test framework — `test "name" { expect X to be Y }` blocks, `@nakige` test annotations, vibes ratings on output. That ships with V4. Today, write one `.fk` per test under `tests/suite/` with an `EXPECT` directive and `freak test` will pick it up.

---

## Compiler Pipeline

FREAK is **self-hosting** — the compiler is written in FREAK itself.

```
.fk source
    │
    ▼
  Lexer          → tokens
    │
    ▼
  Parser         → AST
    │
    ▼
  Type Checker   → typed AST
    │
    ├──── LLVM backend (default) ──→ .ll (LLVM IR) ──→ native binary
    │
    └──── C backend (--c flag) ────→ .fk.c ──────────→ native binary
```

Both backends produce native binaries via Clang. The LLVM IR path supports cross-compilation (`--target=`) and optimization levels (`--opt=0/1/2/3`).

---

## Project Status

FREAK is under active development. The compiler is **self-hosting** — FREAK compiles itself.

| Milestone | Status |
|---|---|
| Self-hosting compiler | ✅ Complete |
| LLVM IR backend (default) | ✅ Complete |
| C backend (`--c`) | ✅ Complete |
| Native CLI (`freak build`/`run`/`check`/`transpile`/`test`) | ✅ Complete |
| Hangar package manager | ✅ Complete |
| Cross-compilation (`--target=`) | ✅ Complete |
| Optimization levels (`--opt=0..3`) | ✅ Complete |
| One-command install (Linux/macOS/Windows) | ✅ Complete |
| CI/CD with 4-platform releases | ✅ Complete |
| Phase-1 borrow checker (`--strict-borrow`) | ✅ Complete |
| Audit suite (`audit-conformance` / `audit-trust` / `audit-science` / `audit-miracles` / `foreshadow-audit`) | ✅ Complete |
| `std::fs`, `std::time`, `std::bytes`, `std::http`, `std::json` | ✅ Complete |
| `std::process` | ⚠️ Partial — V3 exposes `args_count()` / `arg(index)`, environment access, and command execution; `args() -> List<word>` waits for a real list ABI |
| COCKPIT UI framework | 🚧 In progress (MA–MF done, MG pending) |
| LLVM JIT mode + DWARF debug info | 🚧 In progress |
| V4 self-hosting compiler (variants, full BC, mood/prob/power, squadron concurrency, FFI surface, error voices) | 🔜 Roadmapped |
| HFML (markup language) | 📐 Planned |

The language specification is in [`freak-full-bible.md`](freak-full-bible.md). The bible-vs-implementation audit — and the roadmap from v0.13.x to V4 to 1.0.0 — lives in [`freak-conformance-audit.md`](freak-conformance-audit.md). Development checklist: [`freak-todo.md`](freak-todo.md).

---

## Contributing

Read the bible first (`freak-full-bible.md`). It is the authoritative source. If something in the code disagrees with the bible, the bible wins.

Then:
1. Fork the repo
2. Create your branch: `git checkout -b feature/something-cool`
3. Write tests
4. Submit a PR

---

## License

MIT. Do whatever you want. Just know the `std::narrative` death flag system is watching.

---

<div align="center">

*"It was always going to end this way."*  
*— COCKPIT mono_no_aware theme, on program exit*

</div>
