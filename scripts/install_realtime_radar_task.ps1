$ErrorActionPreference = "Stop"
$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$repositoryRoot = Split-Path -Parent $scriptDirectory
$runner = Join-Path $scriptDirectory "run_realtime_radar.ps1"
$taskName = "Global X Finance - Taiwan Realtime Radar"

if (-not (Test-Path -LiteralPath (Join-Path $repositoryRoot ".venv\Scripts\python.exe"))) {
    throw "Project Python not found. Run the demo launcher once before installing the task."
}

$taskArguments = '-NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "{0}"' -f $runner
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument $taskArguments `
    -WorkingDirectory $repositoryRoot
$trigger = New-ScheduledTaskTrigger `
    -Once `
    -At (Get-Date).AddMinutes(1) `
    -RepetitionInterval (New-TimeSpan -Minutes 10) `
    -RepetitionDuration (New-TimeSpan -Days 3650)
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 8)

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Taiwan X 10-minute and YouTube 30-minute read-only radar; no posting." `
    -Force | Out-Null

Write-Host "Windows scheduled task installed: $taskName" -ForegroundColor Green
Write-Host "Dispatcher: 10 minutes. X: 10 minutes. YouTube: 30 minutes." -ForegroundColor Cyan
