@echo off
echo ==========================================
echo  FREAK Self-Hosted Compiler Bootstrap v2
echo ==========================================
echo.

echo [Stage 0] Compiling main.fk with Python freakc...
python -m freakc build self_hosted/main.fk -o self_hosted/freakc_self.exe --keep-c
if errorlevel 1 (
    echo FAILED: Could not compile main.fk Stage 0
    exit /b 1
)
echo.

echo [Stage 1] Using freakc_self.exe to compile itself (main.fk -^> main.c)...
self_hosted\freakc_self.exe self_hosted\main.fk
if errorlevel 1 (
    echo FAILED: Stage 1 crashed
    exit /b 1
)
echo [Stage 1] Compiling Stage 1 C output with clang...
clang -o self_hosted/freakc_self2.exe self_hosted/main.fk.c freakc/runtime/freak_runtime.c -Ifreakc/runtime -w -O3
if errorlevel 1 (
    echo FAILED: Could not compile Stage 1 regenerated C
    exit /b 1
)
echo.

echo [Stage 2] Using freakc_self2.exe to compile tests/hello.fk...
self_hosted\freakc_self2.exe tests\hello.fk
if errorlevel 1 (
    echo FAILED: Stage 2 crashed
    exit /b 1
)
echo [Stage 2] Compiling Stage 2 C output with clang...
clang -o tests/hello_self.exe tests/hello.fk.c freakc/runtime/freak_runtime.c -Ifreakc/runtime -w
if errorlevel 1 (
    echo FAILED: Could not compile Stage 2 regenerated C
    exit /b 1
)
echo.

echo [Stage 3] Running hello_self.exe...
echo ------------------------------------------
tests\hello_self.exe
echo ------------------------------------------
echo Bootstrap Level 2 complete! Self-hosted compiler can compile itself.
