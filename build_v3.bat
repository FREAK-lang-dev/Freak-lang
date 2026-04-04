@echo off
echo ===== FREAK v3 Compiler Build =====
echo.

echo [1/4] Concatenating v3 source files...
copy /b /y ^
  src\compiler\v3\globals.fk ^
  + src\compiler\v3\helpers.fk ^
  + src\compiler\v3\lexer.fk ^
  + src\compiler\v3\parser.fk ^
  + src\compiler\v3\emit_c.fk ^
  + src\compiler\v3\emit_llvm.fk ^
  + src\compiler\v3\main.fk ^
  build\freakc_v3.fk > nul

echo [2/4] Compiling v3 with v2 compiler (C backend)...
build\freakc_v2.exe build\freakc_v3.fk --c
if %errorlevel% neq 0 (
    echo ERROR: v2 compiler failed to compile v3 source
    exit /b 1
)

echo [3/4] Building v3 binary with clang...
clang -O2 -o build\freakc_v3.exe build\freakc_v3.fk.c freakc\runtime\freak_runtime.c freakc\runtime\freak_llvm_runtime.c -Ifreakc\runtime -w -D_CRT_SECURE_NO_WARNINGS -lws2_32
if %errorlevel% neq 0 (
    echo ERROR: clang failed to build v3 binary
    exit /b 1
)

echo [4/4] Testing v3 on hello.fk...
build\freakc_v3.exe tests\hello.fk --llvm
if %errorlevel% neq 0 (
    echo ERROR: v3 failed to compile hello.fk
    exit /b 1
)

echo.
echo ===== v3 Build Complete =====
echo Binary: build\freakc_v3.exe
echo.
echo Next steps:
echo   1. Test: build\freakc_v3.exe tests\hello.fk --llvm
echo   2. Compile hello: clang -o build\hello_v3.exe tests\hello.fk.ll freakc\runtime\freak_llvm_runtime.c freakc\runtime\freak_runtime.c -Ifreakc\runtime -w
echo   3. Run: build\hello_v3.exe
