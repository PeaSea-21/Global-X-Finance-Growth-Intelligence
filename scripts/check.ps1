$ErrorActionPreference = "Stop"
$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$repositoryRoot = Split-Path -Parent $scriptDirectory

Push-Location -LiteralPath $repositoryRoot
try {
    python -m pytest
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }

    python -m global_x_finance.cli security scan --root .
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}
finally {
    Pop-Location
}

