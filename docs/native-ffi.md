# Calling C libraries from FREAK

FREAK can call functions in prebuilt C shared libraries (`.so` on Linux,
`.dylib` on macOS, `.dll` on Windows) directly. Neither side has to go
through LLVM IR. This works on both backends (`--llvm`, the default, and
`--c`) from FREAK 0.16.0. The contract lives in the bible, §16.2 and §16.7.

## Link at build time: `link=`

```fk
use std::ffi

extern [C, link="greet"] {
    task greet_add(a: c_int, b: c_int) -> c_int
    task greet_hello() -> *const c_char

    @link_name("greet_add")
    task plus(a: c_int, b: c_int) -> c_int
}

task main() -> void {
    say word_from_int(greet_add(40, 2))          -- 42
    say ffi::from_cstring(greet_hello())
}
```

```
freak build app.fk                 # links -lgreet, searches app.fk's folder
freak run app.fk --lib-dir=vendor  # also search ./vendor
freak build app.fk --link=sqlite3  # link a library the source doesn't name
```

- `link="greet"` becomes `-lgreet`. A value with a path separator or a
  library suffix (`link="./vendor/libgreet.so"`) is used as a file, relative
  to the source file.
- The source file's folder is always searched. `--lib-dir=DIR` adds more
  folders, and `--link=NAME` adds libraries. Both flags can be repeated.
- On Linux and macOS the binary gets an rpath for its own folder and for
  every `--lib-dir`, so a library sitting next to the executable is found at
  run time. A macOS dylib should use an `@rpath/...` install name
  (`clang -dynamiclib -install_name @rpath/libgreet.dylib`).
- On Windows the linker needs the DLL's import library (`greet.lib` or
  `libgreet.dll.a`), and at run time the DLL must sit next to the `.exe` or
  on `PATH`. If you only have the DLL, use `load=` instead.

## Load at run time: `load=`

```fk
extern [C, load="greet"] {
    task greet_add(a: c_int, b: c_int) -> c_int
}
```

The program doesn't link against the library at all. Each task is resolved
the first time it is called (`dlopen` / `LoadLibrary`). The loader looks next
to the executable first, then on the platform's normal search path. A bare
name becomes `libgreet.so`, `libgreet.dylib` or `greet.dll`, and a value
with a path or suffix is used as written. If the library or a symbol is
missing, the program stops with a message that names it:

```
FFI: could not load library 'greet': libgreet.so: cannot open shared object file
```

An extern block takes one `link=` or one `load=`, not both.

## Types at the boundary

Use the `std::ffi` C aliases in extern signatures. They're declared at their
real C width, and inside FREAK they behave as ordinary values:

| In the extern signature | C type | In FREAK |
|---|---|---|
| `c_int`, `c_uint`, `c_short`, `c_ushort`, `c_char`, `c_uchar` | `int`, `unsigned`, `short`, ... | `int` |
| `c_long`, `c_ulong` | `long` (32-bit on Windows) | `int` |
| `usize`, `c_size`, `isize`, `c_isize` | `size_t`, `ptrdiff_t` | `int` |
| `c_double`, `c_float` | `double`, `float` | `num` |
| `c_bool` | `_Bool` | `bool` |
| `*T`, `*const T`, `*mut T` | any pointer | `int` (an address) |
| `-> void` / `-> c_void` / no arrow | `void` | — |

FREAK's own `int`, `num`, `bool` and `word` aren't allowed in extern
signatures, because they make no promise about C's layout. A `word` isn't a
`char*`, so convert it explicitly:

```fk
pilot text = ffi::cstring("freak")   -- malloc'd, NUL-terminated copy
greet_shout(text)                    -- C writes into it
say ffi::from_cstring(text)          -- copy back into a word
ffi::free(text)
```

## std::ffi helpers

| Helper | What it does |
|---|---|
| `ffi::cstring(w) -> int` | Copy a word into new C memory (free it with `ffi::free`) |
| `ffi::from_cstring(p) -> word` | Copy a NUL-terminated C string (null reads as `""`) |
| `ffi::alloc(size) -> int` / `ffi::free(p)` | Zeroed C memory |
| `ffi::read_i8/u8/i16/u16/i32/u32/i64/f32/f64(p)` | Read a value at an address |
| `ffi::write_i8/.../f64(p, value)` | Write a value at an address |
| `ffi::open(name) -> int` | Load a library (0 on failure) |
| `ffi::symbol(lib, name) -> int` | Address of a symbol (0 if missing) |
| `ffi::close(lib)` / `ffi::last_error() -> word` | Unload, and explain the last failure |

Pointers are plain integers, so pointer arithmetic is addition:
`ffi::read_i32(array + 4 * i)`.

## Platform-specific blocks

```fk
extern [system, link="user32", if target_os = "windows"] {
    task MessageBeep(kind: c_uint) -> c_bool
}
extern [C, link="m", if target_os = "linux"] {
    @link_name("cbrt")
    task cube_root(x: c_double) -> c_double
}
```

A block whose condition doesn't match the build target (including
`--target=` cross builds) is skipped. `target_arch = "x86_64"` /
`"aarch64"` works the same way.

## Not yet (V4)

Variadic functions (`printf`), callbacks into FREAK, `@layout(C)` shapes
passed by value, calling conventions other than the platform C one,
`trust me` gating of pointer helpers, checked narrowing of out-of-range
integers, and extern declarations inside Hangar package modules all arrive
with the V4 compiler.
