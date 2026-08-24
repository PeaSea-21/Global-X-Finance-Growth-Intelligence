$ErrorActionPreference = "Stop"
$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$repositoryRoot = Split-Path -Parent $scriptDirectory
$runner = Join-Path $scriptDirectory "run_daily_x_collection.ps1"
$taskName = "Global X Finance - Daily X Collection"

if (-not (Test-Path -LiteralPath (Join-Path $repositoryRoot ".venv\Scripts\python.exe"))) {
    throw "Project Python not found. Run the demo launcher once before installing the task."
}

$taskArguments = '-NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "{0}"' -f $runner
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument $taskArguments `
    -WorkingDirectory $repositoryRoot
$trigger = New-ScheduledTaskTrigger `
    -Weekly `
    -WeeksInterval 1 `
    -DaysOfWeek Sunday, Monday, Tuesday, Wednesday, Thursday, Friday `
    -At "13:05"
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Daily read-only collection of the configured X account pool through FxTwitter; no posting." `
    -Force | Out-Null

Write-Host "Windows scheduled task installed: $taskName" -ForegroundColor Green
Write-Host "Runs Sunday through Friday at 13:05 Asia/Taipei; Saturday is excluded." -ForegroundColor Cyan
Write-Host "Writes outputs/x_daily/<date>/run_summary.json." -ForegroundColor Cyan
