$ErrorActionPreference = "Stop"
$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$repositoryRoot = Split-Path -Parent $scriptDirectory
$pythonPath = Join-Path $repositoryRoot ".venv\Scripts\python.exe"
$databasePath = Join-Path $repositoryRoot "data\taiwan-demo.db"

if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw "Project Python not found. Run the demo launcher once before starting the radar."
}

$xhotCandidates = @()
if ($env:X_HOTTOPIC_ROOT) {
    $xhotCandidates += $env:X_HOTTOPIC_ROOT
}
$xhotCandidates += (Join-Path $env:USERPROFILE "Desktop\code\X-HotTopic")
$xhotRoot = $xhotCandidates | Where-Object {
    Test-Path -LiteralPath (Join-Path $_ "src\x_hottopic\timeline.py")
} | Select-Object -First 1
if (-not $xhotRoot) {
    throw "NOT_PROVIDED: local xHotTopic source path was not found."
}

Push-Location -LiteralPath $repositoryRoot
$radarExitCode = 1
try {
    & $pythonPath -m global_x_finance.cli radar cycle `
        --db $databasePath `
        --xhot-root $xhotRoot
    $radarExitCode = $LASTEXITCODE
}
finally {
    Pop-Location
}
exit $radarExitCode
