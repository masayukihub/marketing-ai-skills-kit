$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
if (Get-Command python -ErrorAction SilentlyContinue) { $Python = 'python'; $PyArgs = @() }
elseif (Get-Command py -ErrorAction SilentlyContinue) { $Python = 'py'; $PyArgs = @('-3') }
else { throw 'Install Python 3.10+ first.' }
foreach ($Script in @('install.py','doctor.py','demo.py')) {
  & $Python @PyArgs (Join-Path $Root "scripts/$Script")
  if ($LASTEXITCODE -ne 0) { throw "$Script failed with $LASTEXITCODE" }
}
