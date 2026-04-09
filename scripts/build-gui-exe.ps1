# ============================================================
# build-gui-exe.ps1 - WSL 소스를 Windows 임시 경로로 복사 후 exe 빌드
# ============================================================
#
# 문제:
#   Windows Python이 WSL 파일시스템(\\wsl.localhost\...)을 직접 읽으면
#   mtime 비교가 깨져 이전 bytecode를 재사용합니다.
#   결과: 소스를 수정해도 exe에 반영되지 않음.
#
# 해결:
#   1. WSL 소스를 Windows %TEMP% 아래로 복사
#   2. Windows Python + PyInstaller로 빌드
#   3. 결과물을 WSL 원본 위치로 복사
#
# 사용법 (PowerShell):
#   cd \\wsl.localhost\Ubuntu\home\xpdlqj\code\projectH
#   .\scripts\build-gui-exe.ps1
#
# 사전 조건:
#   pip install pyinstaller
# ============================================================

$ErrorActionPreference = "Stop"

# ── WSL 소스 경로 감지 ──
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$WslProjectRoot = Split-Path -Parent $ScriptDir

Write-Host "Pipeline GUI exe builder (Windows safe-copy)" -ForegroundColor Cyan
Write-Host "============================================="
Write-Host "Source : $WslProjectRoot"
Write-Host ""

# ── PyInstaller 확인 ──
try {
    $pyVer = & py -3 -m PyInstaller --version 2>&1
    if ($LASTEXITCODE -ne 0) { throw "not found" }
    Write-Host "[OK] PyInstaller $pyVer" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] PyInstaller not found. Run: pip install pyinstaller" -ForegroundColor Red
    exit 1
}

# ── Windows 임시 빌드 디렉토리 ──
$BuildTemp = Join-Path $env:TEMP "pipeline-gui-build"
if (Test-Path $BuildTemp) {
    Write-Host "Cleaning previous build temp..."
    Remove-Item -Recurse -Force $BuildTemp
}
New-Item -ItemType Directory -Path $BuildTemp | Out-Null
Write-Host "Build temp: $BuildTemp"
Write-Host ""

# ── 필요한 소스 복사 ──
Write-Host "Copying source to Windows local path..." -ForegroundColor Yellow

# Python 패키지 + 진입점
$CopyItems = @(
    "pipeline-gui.py",
    "pipeline-gui.spec",
    "pipeline_gui",
    "storage",
    "start-pipeline.sh",
    "stop-pipeline.sh",
    "watcher_core.py",
    "_data",
    "schemas",
    ".pipeline\README.md"
)

foreach ($item in $CopyItems) {
    $src = Join-Path $WslProjectRoot $item
    $dst = Join-Path $BuildTemp $item
    if (Test-Path $src) {
        if ((Get-Item $src).PSIsContainer) {
            Copy-Item -Recurse -Force $src $dst
            Write-Host "  [DIR]  $item" -ForegroundColor Gray
        } else {
            $dstParent = Split-Path -Parent $dst
            if (-not (Test-Path $dstParent)) {
                New-Item -ItemType Directory -Path $dstParent -Force | Out-Null
            }
            Copy-Item -Force $src $dst
            Write-Host "  [FILE] $item" -ForegroundColor Gray
        }
    } else {
        Write-Host "  [SKIP] $item (not found)" -ForegroundColor DarkYellow
    }
}

# .pipeline/README.md 특수 처리 (중첩 경로)
$pipelineReadmeSrc = Join-Path $WslProjectRoot ".pipeline\README.md"
$pipelineReadmeDst = Join-Path $BuildTemp ".pipeline\README.md"
if (Test-Path $pipelineReadmeSrc) {
    $pipelineDir = Split-Path -Parent $pipelineReadmeDst
    if (-not (Test-Path $pipelineDir)) {
        New-Item -ItemType Directory -Path $pipelineDir -Force | Out-Null
    }
    Copy-Item -Force $pipelineReadmeSrc $pipelineReadmeDst
}

# __pycache__ 삭제 (혼선 방지)
Get-ChildItem -Path $BuildTemp -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Write-Host ""
Write-Host "Cleaned __pycache__ from build temp" -ForegroundColor Gray

# ── 빌드 검증: 수정 코드 반영 확인 ──
Write-Host ""
Write-Host "Verifying source freshness..." -ForegroundColor Yellow
$appPy = Join-Path $BuildTemp "pipeline_gui\app.py"
$executorPy = Join-Path $BuildTemp "pipeline_gui\setup_executor.py"
$hasOnComplete = Select-String -Path $executorPy -Pattern "on_complete" -Quiet
$hasScheduleRefresh = Select-String -Path $appPy -Pattern "_schedule_refresh_setup_mode_state" -Quiet
if ($hasOnComplete -and $hasScheduleRefresh) {
    Write-Host "  [OK] on_complete callback present in copied source" -ForegroundColor Green
} else {
    Write-Host "  [WARN] Expected code changes not found in copied source!" -ForegroundColor Red
    Write-Host "         on_complete: $hasOnComplete" -ForegroundColor Red
    Write-Host "         schedule_refresh: $hasScheduleRefresh" -ForegroundColor Red
    Write-Host "         The exe may not contain your latest fixes." -ForegroundColor Red
}

# ── PyInstaller 빌드 ──
Write-Host ""
Write-Host "Building exe..." -ForegroundColor Cyan
Write-Host ""

Push-Location $BuildTemp
try {
    & py -3 -m PyInstaller --clean -y --onefile --noconsole --name "pipeline-gui" `
        --paths "." `
        --add-data "start-pipeline.sh;_data" `
        --add-data "stop-pipeline.sh;_data" `
        --add-data "watcher_core.py;_data" `
        --add-data "pipeline_gui\token_usage_shared.py;_data" `
        --add-data "pipeline_gui\token_dashboard_shared.py;_data" `
        --add-data "_data;_data" `
        --add-data "schemas\agent_manifest.schema.json;_data\schemas" `
        --add-data "schemas\job_state.schema.json;_data\schemas" `
        --add-data ".pipeline\README.md;_data\.pipeline" `
        pipeline-gui.py

    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] PyInstaller build failed" -ForegroundColor Red
        exit 1
    }
} finally {
    Pop-Location
}

# ── 결과물 복사 ──
$ExeSrc = Join-Path $BuildTemp "dist\pipeline-gui.exe"
if (-not (Test-Path $ExeSrc)) {
    Write-Host "[ERROR] Build output not found: $ExeSrc" -ForegroundColor Red
    exit 1
}

# WSL 원본 dist/
$DistDst = Join-Path $WslProjectRoot "dist"
if (-not (Test-Path $DistDst)) {
    New-Item -ItemType Directory -Path $DistDst | Out-Null
}
Copy-Item -Force $ExeSrc (Join-Path $DistDst "pipeline-gui.exe")
Write-Host ""
Write-Host "[OK] Copied to: $DistDst\pipeline-gui.exe" -ForegroundColor Green

# windows-launchers/dist/ 미러
$MirrorDst = Join-Path $WslProjectRoot "windows-launchers\dist"
if (-not (Test-Path $MirrorDst)) {
    New-Item -ItemType Directory -Path $MirrorDst | Out-Null
}
Copy-Item -Force $ExeSrc (Join-Path $MirrorDst "pipeline-gui.exe")
Write-Host "[OK] Mirrored to: $MirrorDst\pipeline-gui.exe" -ForegroundColor Green

# ── 빌드 후 검증 ──
Write-Host ""
Write-Host "Verifying exe content..." -ForegroundColor Yellow
$exeBytes = [System.IO.File]::ReadAllBytes((Join-Path $DistDst "pipeline-gui.exe"))
$exeText = [System.Text.Encoding]::UTF8.GetString($exeBytes)
if ($exeText.Contains("_schedule_refresh_setup_mode_state")) {
    Write-Host "  [OK] on_complete fix verified in exe" -ForegroundColor Green
} else {
    Write-Host "  [WARN] on_complete fix NOT found in exe!" -ForegroundColor Red
}

# ── 정리 ──
Write-Host ""
$cleanup = Read-Host "Delete build temp ($BuildTemp)? [Y/n]"
if ($cleanup -ne "n") {
    Remove-Item -Recurse -Force $BuildTemp
    Write-Host "Build temp cleaned." -ForegroundColor Gray
}

Write-Host ""
Write-Host "Build complete." -ForegroundColor Green
Write-Host "exe: $DistDst\pipeline-gui.exe"
Write-Host ""
