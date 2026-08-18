$ErrorActionPreference = "Stop"
$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$repositoryRoot = Split-Path -Parent $scriptDirectory
$virtualEnvironment = Join-Path $repositoryRoot ".venv"
$virtualPython = Join-Path $virtualEnvironment "Scripts\python.exe"
$databasePath = Join-Path $repositoryRoot "data\taiwan-demo.db"

function Test-TcpPort {
    param([int]$Port)
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $client.Connect("127.0.0.1", $Port)
        return $true
    }
    catch {
        return $false
    }
    finally {
        $client.Dispose()
    }
}

function Test-CurrentRadar {
    param([int]$Port)
    try {
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/health" -TimeoutSec 2
        $radar = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$Port/stock-radar" -TimeoutSec 5
        return (
            $health.status -eq "ok" -and
            $health.market -eq "TW" -and
            $radar.StatusCode -eq 200 -and
            $radar.Content.Contains("ben-stock-radar.topic-queue.v1")
        )
    }
    catch {
        return $false
    }
}

Push-Location -LiteralPath $repositoryRoot
try {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCommand) {
        throw "找不到 Python。請先從 https://www.python.org/downloads/ 安裝 Python 3.11 或更新版本，安裝時勾選 Add Python to PATH。"
    }

    $versionOk = & python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"
    if ($LASTEXITCODE -ne 0) {
        throw "Python 版本太舊。本 Demo 需要 Python 3.11 或更新版本。"
    }

    if (-not (Test-Path -LiteralPath $virtualPython)) {
        Write-Host "[1/9] 第一次啟動：建立獨立執行環境…" -ForegroundColor Cyan
        & python -m venv $virtualEnvironment
        if ($LASTEXITCODE -ne 0) { throw "建立執行環境失敗。" }
    }
    else {
        Write-Host "[1/9] 使用既有執行環境。" -ForegroundColor Cyan
    }

    Write-Host "[2/9] 安裝或確認必要元件…" -ForegroundColor Cyan
    & $virtualPython -m pip install --disable-pip-version-check -e $repositoryRoot
    if ($LASTEXITCODE -ne 0) { throw "安裝必要元件失敗，請確認網路後再試。" }

    Write-Host "[3/9] 確認資料庫與台灣／美國 Market Pack…" -ForegroundColor Cyan
    & $virtualPython -m global_x_finance.cli db init `
        --db $databasePath `
        --market-pack "codex_mvp_inputs/taiwan.market-pack.yaml" `
        --market-pack "codex_mvp_inputs/us.market-pack.template.yaml"
    if ($LASTEXITCODE -ne 0) { throw "資料庫初始化失敗。" }

    Write-Host "[4/9] 校驗並登記已驗證來源…" -ForegroundColor Cyan
    & $virtualPython -m global_x_finance.cli sources import `
        --db $databasePath `
        --registry "codex_mvp_inputs/verified_source_registry.csv"
    if ($LASTEXITCODE -ne 0) { throw "來源註冊表校驗或匯入失敗。" }

    Write-Host "[5/9] 匯入即時雷達來源治理狀態…" -ForegroundColor Cyan
    & $virtualPython -m global_x_finance.cli radar registry-import `
        --db $databasePath `
        --registry "config/taiwan_realtime_sources.csv"
    if ($LASTEXITCODE -ne 0) { throw "即時雷達來源註冊表校驗或匯入失敗。" }

    Write-Host "[6/9] 匯入 Ben X 監測帳號…" -ForegroundColor Cyan
    & $virtualPython -m global_x_finance.cli ben-radar x-import `
        --db $databasePath `
        --accounts "config/x_accounts.csv"
    if ($LASTEXITCODE -ne 0) { throw "Ben X 帳號清單匯入失敗。" }

    Write-Host "[7/9] 執行到期的 X 增量監測…" -ForegroundColor Cyan
    & $virtualPython -m global_x_finance.cli ben-radar x-sync `
        --db $databasePath `
        --accounts "config/x_accounts.csv"
    if ($LASTEXITCODE -ne 0) { throw "Ben X 增量監測失敗。" }

    Write-Host "[8/9] 標準化既有官方 Evidence 並建立規則卡…" -ForegroundColor Cyan
    & $virtualPython -m global_x_finance.cli normalize twse `
        --db $databasePath `
        --dataset-config "config/twse_openapi.datasets.json"
    if ($LASTEXITCODE -ne 0) { throw "官方 Evidence 標準化失敗。" }

    $launchPort = $null
    foreach ($candidatePort in 8765, 8766, 8767) {
        if (Test-CurrentRadar -Port $candidatePort) {
            $demoUrl = "http://127.0.0.1:$candidatePort/stock-radar"
            Write-Host "目前版本已在 $candidatePort 執行，正在開啟 BEN 財經熱點雷達。" -ForegroundColor Green
            Start-Process $demoUrl
            exit 0
        }
        if (-not (Test-TcpPort -Port $candidatePort)) {
            $launchPort = $candidatePort
            break
        }
        Write-Host "連接埠 $candidatePort 已被舊版或其他服務占用，改試下一個連接埠。" -ForegroundColor Yellow
    }
    if ($null -eq $launchPort) {
        throw "8765、8766、8767 都已被其他服務占用，請先關閉舊 Demo 後再試。"
    }

    Write-Host "[9/9] 將在 $launchPort 啟動目前版本；瀏覽器即將開啟。關閉方式：回到此視窗按 Ctrl+C。" -ForegroundColor Green
    & $virtualPython -m global_x_finance.webapp --db $databasePath --port $launchPort --open-browser
    if ($LASTEXITCODE -ne 0) { throw "本地網頁服務異常結束。" }
}
catch {
    Write-Host ""
    Write-Host "啟動失敗：$($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
finally {
    Pop-Location
}
