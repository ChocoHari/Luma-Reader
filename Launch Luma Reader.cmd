@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
  echo Luma Reader needs its local Python environment. Run Setup.ps1 first.
  pause
  exit /b 1
)
start "Luma Reader" ".venv\Scripts\pythonw.exe" "app.py" %*
