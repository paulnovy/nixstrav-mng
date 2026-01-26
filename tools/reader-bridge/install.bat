@echo off
setlocal

REM UHF Reader Bridge installer (Windows)

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python not found. Install Python 3.10+ and retry.
  echo https://www.python.org/downloads/
  exit /b 1
)

cd /d %~dp0

if not exist .venv (
  echo [INFO] Creating venv...
  python -m venv .venv
)

call .venv\Scripts\activate

echo [INFO] Installing requirements...
pip install -r requirements.txt

if not exist UHFPrimeReader.dll (
  echo [WARN] UHFPrimeReader.dll missing.
  echo Copy it from SDK to this folder and run again.
)

echo [DONE] Install completed.
pause
