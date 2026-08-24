[CmdletBinding()]
param(
    [string]$ProjectRoot = "",
    [string]$TradeDate = "",
    [switch]$ValidateOnly
)

$ErrorActionPreference = "Stop"

function Invoke-Git {
    param(
        [Parameter(Mandatory = $true)][string]$WorkingDirectory,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )
    Push-Location -LiteralPath $WorkingDirectory
    try {
        & git @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "git $($Arguments -join ' ') failed with exit code $LASTEXITCODE"
        }
    }
    finally {
        Pop-Location
    }
}

function Read-JsonFile {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Required file is missing: $Path"
    }
    return Get-Content -Raw -Encoding UTF8 -LiteralPath $Path | ConvertFrom-Json
}

if (-not $ProjectRoot) {
    $ProjectRoot = Split-Path -Parent $PSScriptRoot
}
$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)
if (-not $TradeDate) {
    $taipei = [System.TimeZoneInfo]::ConvertTimeBySystemTimeZoneId(
        [DateTimeOffset]::UtcNow,
        "Taipei Standard Time"
    )
    $TradeDate = $taipei.ToString("yyyy-MM-dd")
}

$dayRoot = Join-Path $ProjectRoot "outputs\ben_channel_daily\$TradeDate"
$summaryPath = Join-Path $dayRoot "run_summary.json"
$auditPath = Join-Path $dayRoot "audit.json"
$briefPath = Join-Path $ProjectRoot "sites\ben-channel-review\brief.json"
$studioDataPath = Join-Path $ProjectRoot "sites\ben-content-studio\data.json"

$summary = Read-JsonFile -Path $summaryPath
$audit = Read-JsonFile -Path $auditPath
$brief = Read-JsonFile -Path $briefPath
$studioData = Read-JsonFile -Path $studioDataPath
$channelWorkbench = $studioData.channel_workbench
if ($null -eq $channelWorkbench) { throw "all-20 channel workbench is missing" }
$sourceSnapshotDate = [string]$channelWorkbench.source_snapshot_date
$channelAuditPath = Join-Path $ProjectRoot "outputs\ben_all20_editorial\$sourceSnapshotDate\all20_editorial_audit.json"
$channelAudit = Read-JsonFile -Path $channelAuditPath

if ($summary.status -ne "PASS") { throw "run_summary status is not PASS" }
if ($summary.market_session_date -ne $TradeDate) { throw "run_summary date mismatch" }
if ($summary.replay_mode -ne $false) { throw "run_summary is a replay" }
if ([int]$summary.violation_count -ne 0) { throw "run_summary has audit violations" }
if (@($audit.violations).Count -ne 0) { throw "audit.json has violations" }
if ($brief.market_session_date -ne $TradeDate) { throw "brief date mismatch" }
if ($brief.replay_mode -ne $false) { throw "brief is a replay" }
if ($studioData.market_session_date -ne $TradeDate) { throw "studio data date mismatch" }
if ($studioData.studio_artifact -ne "BEN_CONTENT_STUDIO_DAILY") { throw "studio artifact mismatch" }
if (@($studioData.weight_topics).Count -ne 5) { throw "weight channel does not have five topics" }
if (@($studioData.briefs).Count -ne 3) { throw "pilot brief count is not three" }
if ([int]$channelWorkbench.channel_count -ne 20) { throw "channel count is not twenty" }
if ([int]$channelWorkbench.draft_ready_channel_count -ne 11) { throw "ready count is not eleven" }
if ([int]$channelWorkbench.waiting_sample_channel_count -ne 9) { throw "waiting count is not nine" }
if ([int]$channelWorkbench.public_visible_channel_count -ne 11) { throw "public visible count is not eleven" }
if ([int]$channelWorkbench.hidden_waiting_channel_count -ne 9) { throw "hidden waiting count is not nine" }
if ([int]$channelWorkbench.news_source_success_count -lt 9) { throw "base news source coverage is incomplete" }
if (@($channelWorkbench.channels).Count -ne 20) { throw "all-20 channel payload is incomplete" }
$historyEntries = @($channelWorkbench.channel_history_index)
if ($historyEntries.Count -lt 11) { throw "channel history does not cover the visible channels" }
$historySourceRoot = Join-Path $ProjectRoot "sites\ben-content-studio\history"
foreach ($entry in $historyEntries) {
    $relativeHistoryPath = ([string]$entry.path).Replace('/', [System.IO.Path]::DirectorySeparatorChar)
    $historyPath = Join-Path (Join-Path $ProjectRoot "sites\ben-content-studio") $relativeHistoryPath
    $resolvedHistoryPath = [System.IO.Path]::GetFullPath($historyPath)
    if (-not $resolvedHistoryPath.StartsWith([System.IO.Path]::GetFullPath($historySourceRoot), [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "history index points outside the content studio history directory"
    }
    $historyArtifact = Read-JsonFile -Path $resolvedHistoryPath
    if ($historyArtifact.snapshot_fingerprint -ne $entry.snapshot_fingerprint) {
        throw "history snapshot fingerprint mismatch"
    }
    foreach ($reviewEvent in @($historyArtifact.review_events)) {
        if ($null -eq $reviewEvent) { continue }
        if ($reviewEvent.status -ne "PENDING_DATA") {
            if (-not $reviewEvent.observation_date) {
                throw "resolved history review is missing observation date"
            }
            if (@($reviewEvent.evidence).Count -eq 0) {
                throw "resolved history review is missing Evidence"
            }
            foreach ($reviewEvidence in @($reviewEvent.evidence)) {
                $reviewUrl = [string]$reviewEvidence.human_verification_url
                if (-not $reviewUrl) { $reviewUrl = [string]$reviewEvidence.url }
                if (-not ($reviewUrl.StartsWith("https://") -or $reviewUrl.StartsWith("http://"))) {
                    throw "resolved history review has invalid Evidence URL"
                }
            }
        }
    }
}
if ($channelWorkbench.last_market_session_date -ne $TradeDate) {
    throw "channel workbench close-talk date mismatch"
}
$closeTalkChannel = @($channelWorkbench.channels | Where-Object { $_.channel_id -eq "ch-02-tw-close-night-talk" })
if ($closeTalkChannel.Count -ne 1) { throw "close-talk channel is missing or duplicated" }
if ($closeTalkChannel[0].content_date -ne $TradeDate) { throw "close-talk channel content is stale" }
if (@($closeTalkChannel[0].topics).Count -ne 5) { throw "close-talk channel does not have five topics" }
foreach ($topic in @($closeTalkChannel[0].topics)) {
    if (-not $topic.script_text) { throw "close-talk topic is missing a complete manuscript" }
    if ([int]$topic.script_character_count -lt 3000) {
        throw "close-talk manuscript is below the 15-minute duration gate"
    }
    if ($topic.script_meets_target -ne $true) { throw "close-talk manuscript target flag is false" }
}
$closeTalkEditorial = $studioData.close_talk_editorial
if ($null -eq $closeTalkEditorial) { throw "close-talk editorial is missing" }
if ($closeTalkEditorial.market_session_date -ne $TradeDate) {
    throw "close-talk editorial date mismatch"
}
if (@($closeTalkEditorial.angles).Count -ne 5) { throw "close-talk editorial does not have five angles" }
foreach ($angle in @($closeTalkEditorial.angles)) {
    $fullText = [string]$angle.script.full_text
    if (-not $fullText) { throw "close-talk editorial angle is missing a complete manuscript" }
    $actualCount = ($fullText -replace '\s', '').Length
    if ($actualCount -lt 3000) { throw "close-talk editorial manuscript is below 3000 characters" }
    if ([int]$angle.script.character_count -ne $actualCount) {
        throw "close-talk editorial manuscript character count is incorrect"
    }
}
if ($channelAudit.status -ne "PASS") { throw "all-20 editorial audit did not pass" }
if ([int]$channelAudit.violation_count -ne 0) { throw "all-20 editorial audit has violations" }
if (-not $channelAudit.input_sha256) { throw "all-20 editorial audit fingerprint is missing" }
if ([int]$channelAudit.topic_count -ne 55) { throw "public channel topic count is not fifty-five" }
if ([int]$channelAudit.full_script_count -ne 55) { throw "complete manuscript count is not fifty-five" }
if ([int]$channelAudit.unique_script_count -ne 55) { throw "complete manuscript bodies are not unique" }
foreach ($channelName in @($channelAudit.channel_length_stats.PSObject.Properties.Name)) {
    $lengthStats = $channelAudit.channel_length_stats.$channelName
    if ([int]$lengthStats.minimum_actual -lt [int]$lengthStats.minimum_required) {
        throw "channel $channelName contains a manuscript below its duration target"
    }
}
foreach ($channel in @($studioData.briefs)) {
    if (@($channel.assignments).Count -lt 5) {
        throw "channel $($channel.channel_name) has fewer than five assignments"
    }
}

$validation = [ordered]@{
    status = "PASS"
    market_session_date = $TradeDate
    violation_count = 0
    pilot_channels = 3
    weight_topics = 5
    channels = 20
    public_channels = 11
    topics = 55
    full_scripts = 55
    draft_ready = 11
    waiting_samples = 9
}
if ($ValidateOnly) {
    $validation | ConvertTo-Json -Compress
    exit 0
}

$tempRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
$worktreePath = Join-Path $tempRoot ("ben-content-studio-pages-" + [guid]::NewGuid().ToString("N"))
$worktreePath = [System.IO.Path]::GetFullPath($worktreePath)
if (-not $worktreePath.StartsWith($tempRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Publication worktree is outside TEMP"
}

try {
    Invoke-Git -WorkingDirectory $ProjectRoot -Arguments @("fetch", "origin", "gh-pages")
    Invoke-Git -WorkingDirectory $ProjectRoot -Arguments @(
        "worktree", "add", "--detach", $worktreePath, "origin/gh-pages"
    )

    $studioTarget = Join-Path $worktreePath "ben-content-studio"
    $reviewTarget = Join-Path $worktreePath "ben-channel-review"
    New-Item -ItemType Directory -Force -Path $studioTarget | Out-Null
    New-Item -ItemType Directory -Force -Path $reviewTarget | Out-Null

    foreach ($name in @("index.html", "styles.css", "app.js", "data.json", "favicon.svg")) {
        Copy-Item -LiteralPath (Join-Path $ProjectRoot "sites\ben-content-studio\$name") `
            -Destination (Join-Path $studioTarget $name)
    }
    $historyTarget = Join-Path $studioTarget "history"
    New-Item -ItemType Directory -Force -Path $historyTarget | Out-Null
    if (Test-Path -LiteralPath $historySourceRoot -PathType Container) {
        Copy-Item -Path (Join-Path $historySourceRoot "*") -Destination $historyTarget -Recurse -Force
    }
    Copy-Item -LiteralPath $briefPath -Destination (Join-Path $worktreePath "brief.json")
    Copy-Item -LiteralPath $briefPath -Destination (Join-Path $reviewTarget "brief.json")
    Copy-Item -LiteralPath (Join-Path $ProjectRoot "sites\ben-channel-review\favicon.svg") `
        -Destination (Join-Path $reviewTarget "favicon.svg")

    $publishFiles = @(
        "brief.json",
        "ben-channel-review/brief.json",
        "ben-channel-review/favicon.svg",
        "ben-content-studio/index.html",
        "ben-content-studio/styles.css",
        "ben-content-studio/app.js",
        "ben-content-studio/data.json",
        "ben-content-studio/favicon.svg",
        "ben-content-studio/history"
    )
    Invoke-Git -WorkingDirectory $worktreePath -Arguments (@("add", "--") + $publishFiles)
    Invoke-Git -WorkingDirectory $worktreePath -Arguments @("diff", "--cached", "--check")

    Push-Location -LiteralPath $worktreePath
    try {
        & git diff --cached --quiet
        $hasChanges = $LASTEXITCODE -ne 0
    }
    finally {
        Pop-Location
    }
    if (-not $hasChanges) {
        ([ordered]@{ status = "NO_CHANGES"; market_session_date = $TradeDate }) |
            ConvertTo-Json -Compress
        exit 0
    }

    Invoke-Git -WorkingDirectory $worktreePath -Arguments @(
        "commit", "-m", "chore: publish $TradeDate BEN content studio"
    )
    Invoke-Git -WorkingDirectory $worktreePath -Arguments @("push", "origin", "HEAD:gh-pages")
    $commit = (& git -C $worktreePath rev-parse HEAD).Trim()
    ([ordered]@{
        status = "PUBLISHED"
        market_session_date = $TradeDate
        commit = $commit
    }) | ConvertTo-Json -Compress
}
finally {
    if (Test-Path -LiteralPath $worktreePath) {
        if (-not $worktreePath.StartsWith($tempRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to remove publication worktree outside TEMP"
        }
        & git -C $ProjectRoot worktree remove --force $worktreePath
    }
}
