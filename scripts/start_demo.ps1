$ErrorActionPreference = "Stop"
$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$repositoryRoot = Split-Path -Parent $scriptDirectory
$virtualEnvironment = Join-Path $repositoryRoot ".venv"
$virtualPython = Join-Path $virtualEnvironment "Scripts\python.exe"
$databasePath = Join-Path $repositoryRoot "data\taiwan-demo.db"
$demoUrl = "http://127.0.0.1:8765/"

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
        Write-Host "[1/7] 第一次啟動：建立獨立執行環境…" -ForegroundColor Cyan
        & python -m venv $virtualEnvironment
        if ($LASTEXITCODE -ne 0) { throw "建立執行環境失敗。" }
    }
    else {
        Write-Host "[1/7] 使用既有執行環境。" -ForegroundColor Cyan
    }

    Write-Host "[2/7] 安裝或確認必要元件…" -ForegroundColor Cyan
    & $virtualPython -m pip install --disable-pip-version-check -e $repositoryRoot
    if ($LASTEXITCODE -ne 0) { throw "安裝必要元件失敗，請確認網路後再試。" }

    Write-Host "[3/7] 確認資料庫與台灣／美國 Market Pack…" -ForegroundColor Cyan
    & $virtualPython -m global_x_finance.cli db init `
        --db $databasePath `
        --market-pack "codex_mvp_inputs/taiwan.market-pack.yaml" `
        --market-pack "codex_mvp_inputs/us.market-pack.template.yaml"
    if ($LASTEXITCODE -ne 0) { throw "資料庫初始化失敗。" }

    Write-Host "[4/7] 校驗並登記已驗證來源…" -ForegroundColor Cyan
    & $virtualPython -m global_x_finance.cli sources import `
        --db $databasePath `
        --registry "codex_mvp_inputs/verified_source_registry.csv"
    if ($LASTEXITCODE -ne 0) { throw "來源註冊表校驗或匯入失敗。" }

    Write-Host "[5/7] 匯入即時雷達來源治理狀態…" -ForegroundColor Cyan
    & $virtualPython -m global_x_finance.cli radar registry-import `
        --db $databasePath `
        --registry "config/taiwan_realtime_sources.csv"
    if ($LASTEXITCODE -ne 0) { throw "即時雷達來源註冊表校驗或匯入失敗。" }

    Write-Host "[6/7] 標準化既有官方 Evidence 並建立規則卡…" -ForegroundColor Cyan
    & $virtualPython -m global_x_finance.cli normalize twse `
        --db $databasePath `
        --dataset-config "config/twse_openapi.datasets.json"
    if ($LASTEXITCODE -ne 0) { throw "官方 Evidence 標準化失敗。" }

    try {
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:8765/health" -TimeoutSec 2
        if ($health.status -eq "ok" -and $health.market -eq "TW") {
            Write-Host "Demo 已在執行，正在開啟瀏覽器。" -ForegroundColor Green
            Start-Process $demoUrl
            exit 0
        }
    }
    catch {
        # 8765 尚未有本 Demo 執行，繼續正常啟動。
    }

    Write-Host "[7/7] 啟動完成；瀏覽器即將開啟。關閉方式：回到此視窗按 Ctrl+C。" -ForegroundColor Green
    & $virtualPython -m global_x_finance.webapp --db $databasePath --open-browser
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
