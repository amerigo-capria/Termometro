@echo off
setlocal
cd /d "%~dp0"

echo Building TermometroXiaomi (cartella portatile)...
python -m PyInstaller --noconfirm --clean termometro.spec
if errorlevel 1 exit /b 1

echo.
echo OK: dist\TermometroXiaomi\
echo Avvio: dist\TermometroXiaomi\TermometroXiaomi.exe
echo Per distribuire: comprimi la cartella dist\TermometroXiaomi in uno ZIP.
