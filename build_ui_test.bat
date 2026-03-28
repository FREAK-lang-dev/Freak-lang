@echo off
setlocal
REM Build freak-ui visual test
REM Concatenates std::ui + freak-ui sources + test program, compiles to native binary

echo [1/3] Combining source files...

REM Create combined .fk file (strip use lines since everything is in one file)
(
    echo -- Combined freak-ui build [auto-generated]
    echo.

    REM std::ui types and wrappers
    findstr /v /b "use " std\ui\window.fk

    echo.

    REM freak-ui: layout engine
    findstr /v /b "use " packages\freak-ui\src\layout.fk

    echo.

    REM freak-ui: theme
    findstr /v /b "use " packages\freak-ui\src\theme.fk

    echo.

    REM freak-ui: widget drawing helpers
    findstr /v /b "use " packages\freak-ui\src\widgets.fk

    echo.

    REM freak-ui: main UI (widgets + animation)
    findstr /v /b "use " packages\freak-ui\src\ui.fk

    echo.

    REM Test program
    findstr /v /b "use " tests\ui_showcase_test.fk
) > build\ui_test_combined.fk

echo [2/3] Transpiling to C...
python -m freakc build build\ui_test_combined.fk 2> build\ui_test_errors.txt
if errorlevel 1 (
    echo TRANSPILE FAILED:
    type build\ui_test_errors.txt
    exit /b 1
)

echo [3/3] Compiling with clang...
clang build\ui_test_combined.fk.c ^
    freakc\runtime\freak_runtime.c ^
    freakc\runtime\ui\win32_backend.c ^
    -Ifreakc\runtime -Ifreakc\runtime\ui ^
    -luser32 -lgdi32 ^
    -D_CRT_SECURE_NO_WARNINGS ^
    -o build\ui_test.exe -O2 -w

if errorlevel 1 (
    echo CLANG FAILED
    exit /b 1
)

echo.
echo BUILD OK: build\ui_test.exe
echo Running...
build\ui_test.exe
