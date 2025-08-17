@echo off
REM Clean previous build
rmdir /s /q EXE
del /q log.log

REM Build with assets folder included and capture ALL output (stdout + stderr)
echo Exporting... (this may take looooong)
pyinstaller --noconsole --onefile --add-data "assets;assets" --icon=assets/logo.ico stopwatch.py > log.log 2>&1
echo Done!
REM Check if build succeeded by verifying EXE exists
if exist dist\stopwatch.exe (
    echo Build succeeded!
    rename dist EXE
) else (
    echo Build failed!
    rmdir /s /q dist
)

REM Cleanup temp build artifacts
rmdir /s /q build
del /q stopwatch.spec

pause