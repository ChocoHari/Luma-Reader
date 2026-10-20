param([string]$PythonExe = '')
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath '.venv313\Scripts\python.exe')) {
    if ($PythonExe) { & $PythonExe -m venv .venv313 } else { & py -3.13 -m venv .venv313 }
    if ($LASTEXITCODE -ne 0) { throw 'Install Python 3.13 (64-bit), or provide -PythonExe with its full path, then run setup again.' }
}
$requirements = if (Test-Path -LiteralPath 'requirements-lock.txt') { 'requirements-lock.txt' } else { 'requirements.txt' }
& '.\.venv313\Scripts\python.exe' -m pip install --disable-pip-version-check -r $requirements
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed. Check the internet connection and the error above.' }
& '.\.venv313\Scripts\python.exe' tools/fetch_ocr_models.py
if ($LASTEXITCODE -ne 0) { throw 'Reviewed OCR model setup failed. Existing files were not overwritten.' }
Write-Host 'Setup complete. Double-click Launch Luma Reader.vbs.'
