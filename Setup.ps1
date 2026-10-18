$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    & py -3.11 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Install Python 3.11 (64-bit), then run setup again.' }
}
$requirements = if (Test-Path -LiteralPath 'requirements-lock.txt') { 'requirements-lock.txt' } else { 'requirements.txt' }
& '.\.venv\Scripts\python.exe' -m pip install --disable-pip-version-check -r $requirements
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed. Check the internet connection and the error above.' }
Write-Host 'Setup complete. Double-click Launch Luma Reader.vbs.'
