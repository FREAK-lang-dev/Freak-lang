@echo off
setlocal enabledelayedexpansion

if /I "%~1"=="--self-test-remove-intermediate" goto self_test_remove_intermediate

echo [Stage 1] Concatenating V3 compiler + CLI sources into build\freakc_cli.fk...
call :prepare_build_dir
if errorlevel 1 exit /b 1
call :remove_final_aliases
if errorlevel 1 exit /b 1
for %%F in (build\freakc_cli.fk build\freakc_cli.fk.c build\freakc_v3_stage1.fk build\freakc_v3_stage2.fk build\freakc_v3_stage1.fk.c build\freakc_v3_stage2.fk.c build\freakc_v3_seed.exe build\freakc_v3_stage1.exe build\freakc_v3_stage2.exe) do (
    call :remove_intermediate "%%F"
    if errorlevel 1 exit /b 1
)

rem Standard library
call :append_source std\version.fk build\freakc_cli.fk new
if errorlevel 1 exit /b 1

rem V3 Compiler internals
for %%F in (src\compiler\v3\globals.fk src\compiler\v3\helpers.fk src\compiler\v3\lexer.fk src\compiler\v3\parser.fk src\compiler\v3\checker.fk src\compiler\v3\emit_c.fk src\compiler\v3\emit_llvm.fk) do (
    call :append_source "%%F" build\freakc_cli.fk append
    if errorlevel 1 exit /b 1
)

rem CLI modules (dependencies before dependents, main last)
for %%F in (src\cli\version.fk src\cli\toml.fk src\cli\lockfile.fk src\cli\build.fk src\cli\run.fk src\cli\hangar.fk src\cli\doctor.fk src\cli\audit.fk src\cli\main.fk) do (
    call :append_source "%%F" build\freakc_cli.fk append
    if errorlevel 1 exit /b 1
)

echo [Stage 2] Building fresh V3 stage1 + stage2 compilers...
call :require_file build\freakc_v3.fk.c "tracked bootstrap seed"
if errorlevel 1 exit /b 1
call :require_file freakc\runtime\freak_runtime.c "V3 runtime source"
if errorlevel 1 exit /b 1

call :append_source src\compiler\v3\globals.fk build\freakc_v3_stage1.fk new
if errorlevel 1 exit /b 1
for %%F in (src\compiler\v3\helpers.fk src\compiler\v3\lexer.fk src\compiler\v3\parser.fk src\compiler\v3\checker.fk src\compiler\v3\emit_c.fk src\compiler\v3\emit_llvm.fk src\compiler\v3\main.fk) do (
    call :append_source "%%F" build\freakc_v3_stage1.fk append
    if errorlevel 1 exit /b 1
)
call :copy_intermediate build\freakc_v3_stage1.fk build\freakc_v3_stage2.fk
if errorlevel 1 exit /b 1

echo   Linking immutable bootstrap seed...
clang -o build\freakc_v3_seed.exe build\freakc_v3.fk.c freakc\runtime\freak_runtime.c -Ifreakc\runtime -O2 -w -D_CRT_SECURE_NO_WARNINGS -lws2_32
if errorlevel 1 (
    echo [ERROR] Failed to link immutable V3 bootstrap seed
    exit /b 1
)
call :require_file build\freakc_v3_seed.exe "fresh V3 bootstrap executable"
if errorlevel 1 exit /b 1

echo   Compiling current sources with bootstrap seed...
build\freakc_v3_seed.exe build\freakc_v3_stage1.fk --c --compiler-internal
if errorlevel 1 (
    echo [ERROR] Bootstrap seed failed to compile current V3 sources
    exit /b 1
)
call :require_file build\freakc_v3_stage1.fk.c "fresh V3 stage1 C output"
if errorlevel 1 exit /b 1
clang -o build\freakc_v3_stage1.exe build\freakc_v3_stage1.fk.c freakc\runtime\freak_runtime.c -Ifreakc\runtime -O2 -w -D_CRT_SECURE_NO_WARNINGS -lws2_32
if errorlevel 1 (
    echo [ERROR] Failed to link V3 stage1 compiler
    exit /b 1
)
call :require_file build\freakc_v3_stage1.exe "fresh V3 stage1 executable"
if errorlevel 1 exit /b 1

echo   Recompiling current sources with stage1...
build\freakc_v3_stage1.exe build\freakc_v3_stage2.fk --c --compiler-internal
if errorlevel 1 (
    echo [ERROR] V3 stage1 failed to compile V3 stage2
    exit /b 1
)
call :require_file build\freakc_v3_stage2.fk.c "fresh V3 stage2 C output"
if errorlevel 1 exit /b 1
clang -o build\freakc_v3_stage2.exe build\freakc_v3_stage2.fk.c freakc\runtime\freak_runtime.c -Ifreakc\runtime -O2 -w -D_CRT_SECURE_NO_WARNINGS -lws2_32
if errorlevel 1 (
    echo [ERROR] Failed to link V3 stage2 compiler
    exit /b 1
)
call :require_file build\freakc_v3_stage2.exe "fresh V3 stage2 executable"
if errorlevel 1 exit /b 1

echo [Stage 3] Compiling build\freakc_cli.fk with fresh V3 stage2...
build\freakc_v3_stage2.exe build\freakc_cli.fk --c --compiler-internal

if errorlevel 1 (
    echo [ERROR] V3 compiler failed to compile freakc_cli.fk
    exit /b 1
)
call :require_file build\freakc_cli.fk.c "fresh FREAK CLI C output"
if errorlevel 1 exit /b 1

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
call :require_file build\freak.exe "fresh FREAK CLI executable"
if errorlevel 1 (
    call :remove_final_aliases
    exit /b 1
)

rem Also create hangar.exe (same binary, BusyBox pattern)
call :copy_final_alias build\freak.exe build\hangar.exe
if errorlevel 1 exit /b 1

rem Backwards compat aliases
call :copy_final_alias build\freak.exe build\freakc.exe
if errorlevel 1 exit /b 1
call :copy_final_alias build\freakc_v3_stage2.exe build\freakc_v3.exe
if errorlevel 1 exit /b 1

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

:self_test_remove_intermediate
if "%~2"=="" (
    echo [ERROR] --self-test-remove-intermediate requires an explicit path
    exit /b 2
)
call :remove_intermediate "%~2"
if errorlevel 1 exit /b 1
exit /b 0

:prepare_build_dir
if exist build (
    set "freak_path_attrs="
    for %%A in ("build") do set "freak_path_attrs=%%~aA"
    if "!freak_path_attrs:~0,1!"=="d" exit /b 0
    echo [ERROR] Expected build to be a directory
    exit /b 1
)
mkdir build >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Could not create build directory
    exit /b 1
)
if not exist build (
    echo [ERROR] Build directory is missing after creation
    exit /b 1
)
exit /b 0

:require_file
if exist "%~1" (
    set "freak_path_attrs="
    for %%A in ("%~1") do set "freak_path_attrs=%%~aA"
    if "!freak_path_attrs:~0,1!"=="d" (
        echo [ERROR] Expected %~2 file but found a directory: %~1
        exit /b 1
    )
)
if not exist "%~1" (
    echo [ERROR] Missing %~2 file: %~1
    exit /b 1
)
for %%S in ("%~1") do if %%~zS LEQ 0 (
    echo [ERROR] Empty %~2 file: %~1
    exit /b 1
)
exit /b 0

:remove_intermediate
if exist "%~1" (
    set "freak_path_attrs="
    for %%A in ("%~1") do set "freak_path_attrs=%%~aA"
    if "!freak_path_attrs:~0,1!"=="d" (
        echo [ERROR] Expected intermediate file but found a directory: %~1
        exit /b 1
    )
)
if exist "%~1" (
    del /f /q "%~1" >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Could not remove stale intermediate file: %~1
        exit /b 1
    )
)
if exist "%~1" (
    echo [ERROR] Stale intermediate file remains after deletion: %~1
    exit /b 1
)
exit /b 0

:append_source
call :require_file "%~1" "source input"
if errorlevel 1 exit /b 1
if /I "%~3"=="new" (
    call :remove_intermediate "%~2"
    if errorlevel 1 exit /b 1
    type "%~1" > "%~2"
) else (
    call :require_file "%~2" "source aggregate"
    if errorlevel 1 exit /b 1
    type "%~1" >> "%~2"
)
if errorlevel 1 (
    echo [ERROR] Failed to append %~1 into %~2
    call :remove_intermediate "%~2"
    exit /b 1
)
call :require_file "%~2" "source aggregate"
if errorlevel 1 (
    call :remove_intermediate "%~2"
    exit /b 1
)
exit /b 0

:copy_intermediate
call :require_file "%~1" "intermediate copy source"
if errorlevel 1 exit /b 1
call :remove_intermediate "%~2"
if errorlevel 1 exit /b 1
copy /y "%~1" "%~2" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to copy intermediate %~1 to %~2
    call :remove_intermediate "%~2"
    exit /b 1
)
call :require_file "%~2" "intermediate copy destination"
if errorlevel 1 exit /b 1
fc /b "%~1" "%~2" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Intermediate copy verification failed for %~2
    call :remove_intermediate "%~2"
    exit /b 1
)
exit /b 0

:remove_final_aliases
for %%F in (build\freak.exe build\hangar.exe build\freakc.exe build\freakc_v3.exe) do (
    call :remove_intermediate "%%F"
    if errorlevel 1 exit /b 1
)
exit /b 0

:copy_final_alias
call :require_file "%~1" "final alias source"
if errorlevel 1 (
    call :remove_final_aliases
    exit /b 1
)
call :remove_intermediate "%~2"
if errorlevel 1 (
    call :remove_final_aliases
    exit /b 1
)
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
fc /b "%~1" "%~2" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Final alias %~2 does not match %~1
    call :remove_final_aliases
    exit /b 1
)
exit /b 0
