@echo off
setlocal enabledelayedexpansion

echo [Stage 1] Concatenating source files into build\freakc_cli.fk...
if not exist build mkdir build
if exist build\freakc_cli.fk del build\freakc_cli.fk

rem Standard library
type std\version.fk >> build\freakc_cli.fk

rem Compiler internals
type src\compiler\ast.fk >> build\freakc_cli.fk
type src\compiler\lexer.fk >> build\freakc_cli.fk
type src\compiler\parser.fk >> build\freakc_cli.fk
type src\compiler\checker.fk >> build\freakc_cli.fk
type src\compiler\emitter.fk >> build\freakc_cli.fk
type src\compiler\backend\llvm.fk >> build\freakc_cli.fk

rem CLI modules (dependencies before dependents, main last)
type src\cli\version.fk >> build\freakc_cli.fk
type src\cli\toml.fk >> build\freakc_cli.fk
type src\cli\build.fk >> build\freakc_cli.fk
type src\cli\run.fk >> build\freakc_cli.fk
type src\cli\hangar.fk >> build\freakc_cli.fk
type src\cli\main.fk >> build\freakc_cli.fk

echo [Stage 2] Compiling build\freakc_cli.fk with build\freakc_v2.exe...
build\freakc_v2.exe build\freakc_cli.fk --c

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] freakc_v2.exe failed to compile freakc_cli.fk
    exit /b %ERRORLEVEL%
)

echo [Stage 3] Building freakc.exe natively with Clang...
clang -o build\freakc.exe build\freakc_cli.fk.c freakc\runtime\freak_runtime.c -Ifreakc\runtime -O2 -w -D_CRT_SECURE_NO_WARNINGS

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Clang failed to compile freakc_cli.fk.c
    exit /b %ERRORLEVEL%
)

rem Also keep as freakc_cli.exe for backwards compat
copy /y build\freakc.exe build\freakc_cli.exe >nul 2>&1

echo .
echo FREAK CLI build complete! Binary at build\freakc.exe
echo .
echo This binary replaces 'python -m freakc'. Usage:
echo   build\freakc.exe build file.fk          Compile to native binary
echo   build\freakc.exe run file.fk            Build and run
echo   build\freakc.exe check file.fk          Type-check only
echo   build\freakc.exe hangar init            Initialize project
echo   build\freakc.exe hangar install         Install dependencies
echo   build\freakc.exe --version              Show version
echo .
