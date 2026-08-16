[CmdletBinding()]
param(
    [int]$MaxMemoryFileBytes = 65536
)

$ErrorActionPreference = "Stop"
$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$repositoryRoot = Split-Path -Parent $scriptDirectory
$repositoryRootFull = [System.IO.Path]::GetFullPath($repositoryRoot).TrimEnd('\', '/')

function Get-RepositoryRelativePath {
    param([Parameter(Mandatory = $true)][string]$FullPath)

    $normalized = [System.IO.Path]::GetFullPath($FullPath)
    if (-not $normalized.StartsWith($repositoryRootFull, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Path is outside repository root: $FullPath"
    }
    return $normalized.Substring($repositoryRootFull.Length).TrimStart('\', '/')
}

$requiredFiles = @(
    "AGENTS.md",
    "docs/PROJECT_CONTEXT.md",
    "docs/DECISIONS.md",
    "docs/TASKS.md",
    "docs/CHANGELOG_WORK.md",
    "docs/HANDOFF.md",
    ".agents/skills/project-memory/SKILL.md"
)

$memoryFiles = @(
    "AGENTS.md",
    "docs/PROJECT_CONTEXT.md",
    "docs/DECISIONS.md",
    "docs/TASKS.md",
    "docs/CHANGELOG_WORK.md",
    "docs/HANDOFF.md"
)

$failures = [System.Collections.Generic.List[string]]::new()

Push-Location -LiteralPath $repositoryRoot
try {
    foreach ($relativePath in $requiredFiles) {
        if (-not (Test-Path -LiteralPath $relativePath -PathType Leaf)) {
            $failures.Add("Missing required file: $relativePath")
        }
    }

    foreach ($relativePath in $memoryFiles) {
        if (-not (Test-Path -LiteralPath $relativePath -PathType Leaf)) {
            continue
        }
        $size = (Get-Item -LiteralPath $relativePath).Length
        if ($size -gt $MaxMemoryFileBytes) {
            $failures.Add("Memory file is too large: $relativePath ($size bytes; limit $MaxMemoryFileBytes)")
        }
    }

    if (Test-Path -LiteralPath "docs/HANDOFF.md" -PathType Leaf) {
        $handoff = Get-Content -Raw -Encoding UTF8 -LiteralPath "docs/HANDOFF.md"
        $updatedLabel = ([char]0x66F4).ToString() + [char]0x65B0 + [char]0x65F6 + [char]0x95F4 + [char]0xFF1A
        $updatedPattern = '(?m)^- ' + [regex]::Escape($updatedLabel) + '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} [+-]\d{2}:\d{2}\s*$'
        if ($handoff -notmatch $updatedPattern) {
            $failures.Add("HANDOFF.md does not contain a valid updated-at timestamp")
        }
    }

    if (Test-Path -LiteralPath "AGENTS.md" -PathType Leaf) {
        $agents = Get-Content -Raw -Encoding UTF8 -LiteralPath "AGENTS.md"
        $startProtocolPresent = $agents -match 'Task Start Protocol' -and
            $agents -match 'git status --short --branch' -and
            $agents -match 'no more than 10 lines'
        $endProtocolPresent = $agents -match 'Task End Protocol' -and
            $agents -match 'docs/TASKS\.md' -and
            $agents -match 'docs/DECISIONS\.md' -and
            $agents -match 'docs/CHANGELOG_WORK\.md' -and
            $agents -match 'docs/HANDOFF\.md'
        if (-not $startProtocolPresent) {
            $failures.Add("AGENTS.md is missing the required task-start protocol")
        }
        if (-not $endProtocolPresent) {
            $failures.Add("AGENTS.md is missing the required task-end protocol")
        }
    }

    $skipDirectories = @(
        ".git", ".venv", "__pycache__", ".pytest_cache", ".pytest-tmp",
        "node_modules", "build", "dist", "data", "logs"
    )
    $textExtensions = @(
        ".py", ".toml", ".yaml", ".yml", ".json", ".md", ".txt",
        ".csv", ".ini", ".cfg", ".conf", ".env", ".sql", ".sh",
        ".ps1", ".bat"
    )
    $knownTokenPatterns = @(
        @{ Name = "OpenAI-style key"; Regex = '\bsk-[A-Za-z0-9_-]{20,}\b' },
        @{ Name = "GitHub token"; Regex = '\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b' },
        @{ Name = "GitHub fine-grained token"; Regex = '\bgithub_pat_[A-Za-z0-9_]{20,}\b' },
        @{ Name = "Slack token"; Regex = '\bxox[baprs]-[A-Za-z0-9-]{15,}\b' },
        @{ Name = "AWS access key"; Regex = '\b(?:AKIA|ASIA)[A-Z0-9]{16}\b' }
    )
    $assignmentPattern = '(?i)\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|passwd|cookie|secret)\b\s*[:=]\s*["'']([^"'']{8,})["'']'
    $placeholderWords = @("example", "placeholder", "changeme", "redacted", "dummy", "synthetic")

    $candidateFiles = Get-ChildItem -LiteralPath $repositoryRoot -Recurse -File -Force | Where-Object {
        $relative = Get-RepositoryRelativePath -FullPath $_.FullName
        $parts = $relative -split '[\\/]'
        $directoryParts = if ($parts.Length -gt 1) { $parts[0..($parts.Length - 2)] } else { @() }
        $notSkipped = -not ($directoryParts | Where-Object { $_ -in $skipDirectories })
        $isText = $_.Name.StartsWith(".env") -or $_.Extension.ToLowerInvariant() -in $textExtensions
        $notSkipped -and $isText
    }

    foreach ($file in $candidateFiles) {
        $relative = Get-RepositoryRelativePath -FullPath $file.FullName
        try {
            $lines = Get-Content -Encoding UTF8 -LiteralPath $file.FullName
        }
        catch {
            continue
        }

        for ($index = 0; $index -lt $lines.Count; $index++) {
            $line = $lines[$index]
            foreach ($pattern in $knownTokenPatterns) {
                if ($line -match $pattern.Regex) {
                    $failures.Add("Possible $($pattern.Name): ${relative}:$($index + 1)")
                }
            }

            $assignment = [regex]::Match($line, $assignmentPattern)
            if ($assignment.Success) {
                $candidate = $assignment.Groups[1].Value.ToLowerInvariant()
                $isPlaceholder = $false
                foreach ($word in $placeholderWords) {
                    if ($candidate.Contains($word)) {
                        $isPlaceholder = $true
                        break
                    }
                }
                if (-not $isPlaceholder) {
                    $failures.Add("Possible credential assignment: ${relative}:$($index + 1)")
                }
            }
        }
    }
}
finally {
    Pop-Location
}

if ($failures.Count -gt 0) {
    Write-Host "Project Memory check failed:" -ForegroundColor Red
    foreach ($failure in $failures) {
        Write-Host "- $failure" -ForegroundColor Red
    }
    exit 1
}

Write-Host "Project Memory check passed." -ForegroundColor Green
Write-Host "Required files: $($requiredFiles.Count); maximum memory file size: $MaxMemoryFileBytes bytes."
