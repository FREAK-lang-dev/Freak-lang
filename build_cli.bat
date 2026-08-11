@echo off
setlocal enabledelayedexpansion

echo [Stage 1] Concatenating V3 compiler + CLI sources into build\freakc_cli.fk...
if not exist build mkdir build
call :remove_final_aliases
if errorlevel 1 exit /b !ERRORLEVEL!
if exist build\freakc_cli.fk del build\freakc_cli.fk

rem Standard library
type std\version.fk > build\freakc_cli.fk

rem V3 Compiler internals
type src\compiler\v3\globals.fk >> build\freakc_cli.fk
type src\compiler\v3\helpers.fk >> build\freakc_cli.fk
type src\compiler\v3\lexer.fk >> build\freakc_cli.fk
type src\compiler\v3\parser.fk >> build\freakc_cli.fk
type src\compiler\v3\checker.fk >> build\freakc_cli.fk
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
type src\cli\audit.fk >> build\freakc_cli.fk
type src\cli\main.fk >> build\freakc_cli.fk

echo [Stage 2] Building fresh V3 stage1 + stage2 compilers...
if not exist build\freakc_v3.fk.c (
    echo [ERROR] Missing tracked bootstrap seed build\freakc_v3.fk.c
    exit /b 1
)
if exist build\freakc_v3_stage1.fk del build\freakc_v3_stage1.fk
if exist build\freakc_v3_stage2.fk del build\freakc_v3_stage2.fk
if exist build\freakc_v3_stage1.fk.c del build\freakc_v3_stage1.fk.c
if exist build\freakc_v3_stage2.fk.c del build\freakc_v3_stage2.fk.c
if exist build\freakc_v3_seed.exe del build\freakc_v3_seed.exe
if exist build\freakc_v3_stage1.exe del build\freakc_v3_stage1.exe
if exist build\freakc_v3_stage2.exe del build\freakc_v3_stage2.exe

type src\compiler\v3\globals.fk > build\freakc_v3_stage1.fk
type src\compiler\v3\helpers.fk >> build\freakc_v3_stage1.fk
type src\compiler\v3\lexer.fk >> build\freakc_v3_stage1.fk
type src\compiler\v3\parser.fk >> build\freakc_v3_stage1.fk
type src\compiler\v3\checker.fk >> build\freakc_v3_stage1.fk
type src\compiler\v3\emit_c.fk >> build\freakc_v3_stage1.fk
type src\compiler\v3\emit_llvm.fk >> build\freakc_v3_stage1.fk
type src\compiler\v3\main.fk >> build\freakc_v3_stage1.fk
copy /y build\freakc_v3_stage1.fk build\freakc_v3_stage2.fk >nul

echo   Linking immutable bootstrap seed...
clang -o build\freakc_v3_seed.exe build\freakc_v3.fk.c freakc\runtime\freak_runtime.c -Ifreakc\runtime -O2 -w -D_CRT_SECURE_NO_WARNINGS -lws2_32
if errorlevel 1 (
    echo [ERROR] Failed to link immutable V3 bootstrap seed
    exit /b !ERRORLEVEL!
)

echo   Compiling current sources with bootstrap seed...
build\freakc_v3_seed.exe build\freakc_v3_stage1.fk --c
if errorlevel 1 (
    echo [ERROR] Bootstrap seed failed to compile current V3 sources
    exit /b !ERRORLEVEL!
)
clang -o build\freakc_v3_stage1.exe build\freakc_v3_stage1.fk.c freakc\runtime\freak_runtime.c -Ifreakc\runtime -O2 -w -D_CRT_SECURE_NO_WARNINGS -lws2_32
if errorlevel 1 (
    echo [ERROR] Failed to link V3 stage1 compiler
    exit /b !ERRORLEVEL!
)

echo   Recompiling current sources with stage1...
build\freakc_v3_stage1.exe build\freakc_v3_stage2.fk --c
if errorlevel 1 (
    echo [ERROR] V3 stage1 failed to compile V3 stage2
    exit /b !ERRORLEVEL!
)
clang -o build\freakc_v3_stage2.exe build\freakc_v3_stage2.fk.c freakc\runtime\freak_runtime.c -Ifreakc\runtime -O2 -w -D_CRT_SECURE_NO_WARNINGS -lws2_32
if errorlevel 1 (
    echo [ERROR] Failed to link V3 stage2 compiler
    exit /b !ERRORLEVEL!
)

echo [Stage 3] Compiling build\freakc_cli.fk with fresh V3 stage2...
build\freakc_v3_stage2.exe build\freakc_cli.fk --c

if errorlevel 1 (
    echo [ERROR] V3 compiler failed to compile freakc_cli.fk
    exit /b !ERRORLEVEL!
)

echo [Stage 4] Linking freak.exe with Clang...
clang -o build\freak.exe build\freakc_cli.fk.c freakc\runtime\freak_runtime.c -Ifreakc\runtime -O2 -w -D_CRT_SECURE_NO_WARNINGS -lws2_32

if errorlevel 1 (
    echo [ERROR] Clang failed to link freak.exe
    call :remove_final_aliases
    exit /b 1
)
if not exist build\freak.exe (
    echo [ERROR] Clang reported success but build\freak.exe is missing
    call :remove_final_aliases
    exit /b 1
)

rem Also create hangar.exe (same binary, BusyBox pattern)
call :copy_final_alias build\freak.exe build\hangar.exe
if errorlevel 1 exit /b !ERRORLEVEL!

rem Backwards compat aliases
call :copy_final_alias build\freak.exe build\freakc.exe
if errorlevel 1 exit /b !ERRORLEVEL!
call :copy_final_alias build\freakc_v3_stage2.exe build\freakc_v3.exe
if errorlevel 1 exit /b !ERRORLEVEL!

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
exit /b 0

:remove_final_aliases
for %%F in (build\freak.exe build\hangar.exe build\freakc.exe build\freakc_v3.exe) do (
    if exist "%%F" del /f /q "%%F"
    if exist "%%F" (
        echo [ERROR] Could not remove stale final alias %%F
        exit /b 1
    )
)
exit /b 0

:copy_final_alias
copy /y "%~1" "%~2" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to create final alias %~2
    call :remove_final_aliases
    exit /b 1
)
if not exist "%~2" (
    echo [ERROR] Final alias %~2 is missing after copy
    call :remove_final_aliases
    exit /b 1
)
exit /b 0
