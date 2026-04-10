Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Copy-TreeItem {
    param(
        [Parameter(Mandatory = $true)][string]$SourceRoot,
        [Parameter(Mandatory = $true)][string]$DestinationRoot,
        [Parameter(Mandatory = $true)][string]$RelativePath
    )

    $sourcePath = Join-Path $SourceRoot $RelativePath
    if (-not (Test-Path -LiteralPath $sourcePath)) {
        throw "Missing required source path: $RelativePath"
    }

    $destinationPath = Join-Path $DestinationRoot $RelativePath
    $destinationParent = Split-Path -Parent $destinationPath
    if ($destinationParent) {
        New-Item -ItemType Directory -Force -Path $destinationParent | Out-Null
    }

    Copy-Item -LiteralPath $sourcePath -Destination $destinationPath -Recurse -Force
}

$RepoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$StageRoot = Join-Path $env:TEMP "pipeline-gui-build"
$SourceRoot = Join-Path $StageRoot "src"
$StageDist = Join-Path $SourceRoot "dist"
$RepoDistDir = Join-Path $RepoRoot "dist"
$MirrorDistDir = Join-Path $RepoRoot "windows-launchers\dist"
$DesktopDir = [Environment]::GetFolderPath("Desktop")
$RepoExe = Join-Path $RepoDistDir "pipeline-gui.exe"
$MirrorExe = Join-Path $MirrorDistDir "pipeline-gui.exe"
$DesktopExe = Join-Path $DesktopDir "pipeline-gui.exe"

$CopyItems = @(
    "pipeline-gui.py",
    "start-pipeline.sh",
    "stop-pipeline.sh",
    "watcher_core.py",
    "pipeline_gui",
    "storage",
    "_data",
    "schemas",
    ".pipeline\README.md"
)

Write-Step "Project root"
Write-Host $RepoRoot

Write-Step "Prepare Windows-local staging directory"
if (Test-Path -LiteralPath $StageRoot) {
    Remove-Item -LiteralPath $StageRoot -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $SourceRoot | Out-Null

Write-Step "Copy source tree from repo to staging"
foreach ($item in $CopyItems) {
    Copy-TreeItem -SourceRoot $RepoRoot -DestinationRoot $SourceRoot -RelativePath $item
}

Write-Step "Remove stale __pycache__ from staging"
Get-ChildItem -Path $SourceRoot -Filter "__pycache__" -Recurse -Directory -ErrorAction SilentlyContinue |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

$ExpectedPaths = @(
    "pipeline-gui.py",
    "pipeline_gui\app.py",
    "pipeline_gui\agents.py",
    "pipeline_gui\backend.py",
    "storage\json_store_base.py",
    "start-pipeline.sh",
    "stop-pipeline.sh",
    "watcher_core.py",
    "_data\token_collector.py",
    "_data\token_store.py",
    "schemas\agent_manifest.schema.json",
    "schemas\job_state.schema.json",
    ".pipeline\README.md"
)

Write-Step "Validate staged source snapshot"
foreach ($relativePath in $ExpectedPaths) {
    $fullPath = Join-Path $SourceRoot $relativePath
    if (-not (Test-Path -LiteralPath $fullPath)) {
        throw "Staged snapshot is missing required file: $relativePath"
    }
}

$PyInstallerArgs = @(
    "--clean",
    "-y",
    "--onefile",
    "--noconsole",
    "--name",
    "pipeline-gui",
    "--paths",
    ".",
    "--add-data",
    "start-pipeline.sh;_data",
    "--add-data",
    "stop-pipeline.sh;_data",
    "--add-data",
    "watcher_core.py;_data",
    "--add-data",
    "pipeline_gui/token_usage_shared.py;_data",
    "--add-data",
    "pipeline_gui/token_dashboard_shared.py;_data",
    "--add-data",
    "_data;_data",
    "--add-data",
    "schemas/agent_manifest.schema.json;_data/schemas",
    "--add-data",
    "schemas/job_state.schema.json;_data/schemas",
    "--add-data",
    ".pipeline/README.md;_data/.pipeline",
    "pipeline-gui.py"
)

Write-Step "Run PyInstaller from the staged local copy"
Push-Location $SourceRoot
try {
    & py -3 -m PyInstaller @PyInstallerArgs
}
finally {
    Pop-Location
}

$BuiltExe = Join-Path $StageDist "pipeline-gui.exe"
if (-not (Test-Path -LiteralPath $BuiltExe)) {
    throw "PyInstaller did not produce: $BuiltExe"
}

Write-Step "Copy built exe back to repo output locations"
New-Item -ItemType Directory -Force -Path $RepoDistDir | Out-Null
New-Item -ItemType Directory -Force -Path $MirrorDistDir | Out-Null
Copy-Item -LiteralPath $BuiltExe -Destination $RepoExe -Force
Copy-Item -LiteralPath $BuiltExe -Destination $MirrorExe -Force

if ([string]::IsNullOrWhiteSpace($DesktopDir)) {
    throw "Desktop path could not be resolved."
}

Write-Step "Overwrite Desktop exe copy"
Copy-Item -LiteralPath $BuiltExe -Destination $DesktopExe -Force

$RepoHash = (Get-FileHash -LiteralPath $RepoExe -Algorithm SHA256).Hash
$MirrorHash = (Get-FileHash -LiteralPath $MirrorExe -Algorithm SHA256).Hash
$DesktopHash = (Get-FileHash -LiteralPath $DesktopExe -Algorithm SHA256).Hash
$RepoInfo = Get-Item -LiteralPath $RepoExe
$MirrorInfo = Get-Item -LiteralPath $MirrorExe
$DesktopInfo = Get-Item -LiteralPath $DesktopExe

Write-Step "Build result"
Write-Host "dist exe   : $RepoExe"
Write-Host "mirror exe : $MirrorExe"
Write-Host "desktop exe: $DesktopExe"
Write-Host "dist size  : $($RepoInfo.Length)"
Write-Host "mirror size: $($MirrorInfo.Length)"
Write-Host "desktop size: $($DesktopInfo.Length)"
Write-Host "dist hash  : $RepoHash"
Write-Host "mirror hash: $MirrorHash"
Write-Host "desktop hash: $DesktopHash"

if ($RepoHash -ne $MirrorHash) {
    throw "Mirrored exe hash mismatch after copy-back."
}

if ($RepoHash -ne $DesktopHash) {
    throw "Desktop exe hash mismatch after copy-back."
}

Write-Step "Done"
Write-Host "Desktop exe was overwritten with the latest build."
