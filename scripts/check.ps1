$ErrorActionPreference = "Stop"
$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$repositoryRoot = Split-Path -Parent $scriptDirectory
$projectPython = Join-Path $repositoryRoot ".venv\Scripts\python.exe"
$pythonPath = if (Test-Path -LiteralPath $projectPython) { $projectPython } else { "python" }

Push-Location -LiteralPath $repositoryRoot
try {
    & $pythonPath -m pytest
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }

    & $pythonPath -m global_x_finance.cli security scan --root .
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}
finally {
    Pop-Location
}
