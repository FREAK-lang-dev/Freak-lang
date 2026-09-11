# Hangar Package-Authoring Guide

How to write, version, depend on, and publish a Hangar package. Covers the
shipping Hangar commands (`init`, `add`, `remove`, `install`, `update`,
`outdated`, `version`, `audit`, `publish`); the registry web UI and search
remain in progress per `hangar-expansion-plan.md`.

## 1. Layout of a package

A package is a directory with a `hangar.toml` manifest at its root. The
convention (see `packages/cockpit/hangar.toml` and
`packages/muvluv/hangar.toml`) is:

```toml
[project]
name = "greeter"
version = "0.1.0"
author = "Your Name"
description = "A tiny greeting library for FREAK."

[dependencies]
```

- `[project] name` / `version` are required. `author` and `description` are
  optional but recommended — `hangar publish` surfaces them.
- `[dependencies]` starts empty. Each entry maps a package name to a Git
  source plus a version constraint (section 3).
- Consumers of your package get your source tree vendored under their
  `hangar_modules/<your-name>/`. Keep the root tidy: source files at the top
  level (or `src/`), one entry-point `<name>.fk` matching the package name.

## 2. Worked example — `greeter` 0.1.0

Create and scaffold the project:

```bash
freak hangar init greeter
cd greeter
```

`init` writes `hangar.toml`, a `src/main.fk` hello stub, and an empty
`hangar_modules/` directory. Replace the stub with the library:

```fk
-- greeter.fk -- a tiny greeting library
task greet(name: word) -> word {
    give back "Hello, {name}! Your mission has begun."
}
```

Set the manifest fields and check the version command:

```bash
freak hangar version        # shows: greeter v0.1.0
freak hangar version minor  # bumps to 0.2.0 (major | minor | patch | <explicit>)
```

Depend on it from an application using the Git form:

```bash
freak hangar add greeter https://github.com/example/greeter.git 0.1.0
```

which records in the application's `hangar.toml`:

```toml
[dependencies]
greeter = { git = "https://github.com/example/greeter.git", version = "0.1.0" }
```

then installs and pins:

```bash
freak hangar install   # clones into hangar_modules/, writes hangar.lock
freak hangar audit     # verifies installed trees against hangar.lock
```

`hangar.lock` pins each package (`[[package]]` with `name`, `version`,
`source`, `sha256`) — commit it so every checkout resolves identically.
`hangar update [name]` re-resolves to the newest matching version;
`hangar outdated` reports drift without changing anything.

## 3. Version constraints

For registry packages (no `git` key), depend with a SemVer constraint:

```toml
[dependencies]
muvluv = "^1.2.0"   # compatible with 1.x.x, >= 1.2.0
```

Supported operators: `^` (compatible), `~` (patch-compatible), `=` (exact),
`>=`, `<`, `>`, `<=`, and bare versions (treated as `^`). `latest` tracks the
newest release. Prefer `^` ranges in libraries and exact pins in applications.

## 4. Publishing checklist

1. `hangar.toml` has name, version, author, description.
2. `freak hangar publish --dry-run` is clean.
3. `freak hangar publish` uploads; `hangar.lock` consumers re-resolve on
   their next `hangar update`.
4. Tag the release in Git so `git`-form consumers can pin it.

Login once with `freak hangar login` before publishing. Transitive
dependencies are resolved from each dependency's own `hangar.toml` at install
time — keep yours accurate.
