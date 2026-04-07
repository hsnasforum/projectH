[CmdletBinding()]
param(
    [string]$Distro = "Ubuntu",
    [int]$Port = 8780,
    [switch]$ShowOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$raw = & wsl.exe -d $Distro -- hostname -I
if ($LASTEXITCODE -ne 0 -or -not $raw) {
    throw "WSL distro '$Distro'의 IPv4 주소를 가져오지 못했습니다."
}

$wslIp = ($raw -split "\s+" | Where-Object { $_ -match '^\d{1,3}(\.\d{1,3}){3}$' } | Select-Object -First 1)
if (-not $wslIp) {
    throw "유효한 WSL IPv4 주소를 찾지 못했습니다."
}

$url = "http://${wslIp}:$Port/controller"

Write-Host "WSL distro : $Distro"
Write-Host "WSL IPv4   : $wslIp"
Write-Host "Controller : $url"

if (-not $ShowOnly) {
    Start-Process $url | Out-Null
}
