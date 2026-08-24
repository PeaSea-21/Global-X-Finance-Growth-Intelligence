$ErrorActionPreference = "Stop"
$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$repositoryRoot = Split-Path -Parent $scriptDirectory
$pythonPath = Join-Path $repositoryRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw "Project Python not found. Run the demo launcher once before starting X collection."
}

Push-Location -LiteralPath $repositoryRoot
try {
    & $pythonPath "scripts\run_daily_x_collection.py" `
        --database "data\taiwan-demo.db" `
        --accounts "config\x_accounts.csv" `
        --output-root "outputs\x_daily"
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
