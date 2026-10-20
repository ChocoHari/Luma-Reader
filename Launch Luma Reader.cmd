@echo off
cd /d "%~dp0"
set "luma_python=.venv313\Scripts\pythonw.exe"
if not exist "%luma_python%" set "luma_python=.venv\Scripts\pythonw.exe"
if not exist "%luma_python%" (
  echo Luma Reader needs its local Python environment. Run Setup.ps1 first.
  pause
  exit /b 1
)
start "Luma Reader" "%luma_python%" "app.py" %*
