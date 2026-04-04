@echo off
setlocal enabledelayedexpansion

echo [Stage 1] Concatenating V3 compiler + CLI sources into build\freakc_cli.fk...
if not exist build mkdir build
if exist build\freakc_cli.fk del build\freakc_cli.fk

rem Standard library
type std\version.fk >> build\freakc_cli.fk

rem V3 Compiler internals
type src\compiler\v3\globals.fk >> build\freakc_cli.fk
type src\compiler\v3\helpers.fk >> build\freakc_cli.fk
type src\compiler\v3\lexer.fk >> build\freakc_cli.fk
type src\compiler\v3\parser.fk >> build\freakc_cli.fk
type src\compiler\v3\emit_c.fk >> build\freakc_cli.fk
type src\compiler\v3\emit_llvm.fk >> build\freakc_cli.fk

rem CLI modules (dependencies before dependents, main last)
type src\cli\version.fk >> build\freakc_cli.fk
type src\cli\toml.fk >> build\freakc_cli.fk
type src\cli\lockfile.fk >> build\freakc_cli.fk
type src\cli\build.fk >> build\freakc_cli.fk
type src\cli\run.fk >> build\freakc_cli.fk
type src\cli\hangar.fk >> build\freakc_cli.fk
type src\cli\doctor.fk >> build\freakc_cli.fk
type src\cli\main.fk >> build\freakc_cli.fk

echo [Stage 2] Building V3 bootstrap compiler...
if not exist build\freakc_v3.fk (
    type src\compiler\v3\globals.fk > build\freakc_v3.fk
    type src\compiler\v3\helpers.fk >> build\freakc_v3.fk
    type src\compiler\v3\lexer.fk >> build\freakc_v3.fk
    type src\compiler\v3\parser.fk >> build\freakc_v3.fk
    type src\compiler\v3\emit_c.fk >> build\freakc_v3.fk
    type src\compiler\v3\emit_llvm.fk >> build\freakc_v3.fk
    type src\compiler\v3\main.fk >> build\freakc_v3.fk
)

rem Bootstrap V3 compiler from pre-compiled C if not present
if not exist build\freakc_v3.exe (
    echo   Linking freakc_v3.exe from pre-compiled bootstrap...
    clang -o build\freakc_v3.exe build\freakc_v3.fk.c freakc\runtime\freak_runtime.c -Ifreakc\runtime -O2 -w -D_CRT_SECURE_NO_WARNINGS
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to link freakc_v3.exe
        exit /b %ERRORLEVEL%
    )
    echo   freakc_v3.exe ready.
)

echo [Stage 3] Compiling build\freakc_cli.fk with V3 compiler...
build\freakc_v3.exe build\freakc_cli.fk --c

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] V3 compiler failed to compile freakc_cli.fk
    exit /b %ERRORLEVEL%
)

echo [Stage 4] Linking freak.exe with Clang...
clang -o build\freak.exe build\freakc_cli.fk.c freakc\runtime\freak_runtime.c -Ifreakc\runtime -O2 -w -D_CRT_SECURE_NO_WARNINGS

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Clang failed to link freak.exe
    exit /b %ERRORLEVEL%
)

rem Also create hangar.exe (same binary, BusyBox pattern)
copy /y build\freak.exe build\hangar.exe >nul 2>&1

rem Backwards compat alias
copy /y build\freak.exe build\freakc.exe >nul 2>&1

echo .
echo FREAK CLI build complete! Binaries at build\freak.exe + build\hangar.exe
echo .
echo Usage:
echo   build\freak.exe build file.fk          Compile to native binary
echo   build\freak.exe run file.fk            Build and run
echo   build\freak.exe check file.fk          Type-check only
echo   build\freak.exe hangar init            Initialize project
echo   build\hangar.exe init                  Standalone package manager
echo   build\freak.exe --version              Show version
echo .
