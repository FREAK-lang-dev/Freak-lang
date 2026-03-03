@echo off
setlocal

if "%~1"=="" (
    echo Usage: run.bat ^<source.fk^> [--keep-c]
    exit /b 1
)

python -m freakc %*
