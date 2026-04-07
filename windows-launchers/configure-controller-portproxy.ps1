[CmdletBinding()]
param(
    [string]$Distro = "Ubuntu",
    [int]$Port = 8780,
    [switch]$ShowOnly,
    [switch]$Remove
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Require-Admin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "관리자 PowerShell로 실행해 주세요."
    }
}

function Get-WslIPv4([string]$TargetDistro) {
    $raw = & wsl.exe -d $TargetDistro -- hostname -I
    if ($LASTEXITCODE -ne 0 -or -not $raw) {
        throw "WSL distro '$TargetDistro'의 IP를 가져오지 못했습니다."
    }
    $ip = ($raw -split "\s+" | Where-Object { $_ -match '^\d{1,3}(\.\d{1,3}){3}$' } | Select-Object -First 1)
    if (-not $ip) {
        throw "유효한 WSL IPv4 주소를 찾지 못했습니다."
    }
    return $ip
}

function Remove-PortProxy([string]$ListenAddress, [int]$ListenPort) {
    & netsh interface portproxy delete v4tov4 listenaddress=$ListenAddress listenport=$ListenPort | Out-Null
}

function Add-PortProxy([string]$ListenAddress, [int]$ListenPort, [string]$ConnectAddress, [int]$ConnectPort) {
    & netsh interface portproxy add v4tov4 listenaddress=$ListenAddress listenport=$ListenPort connectaddress=$ConnectAddress connectport=$ConnectPort | Out-Null
}

$wslIp = Get-WslIPv4 -TargetDistro $Distro

Write-Host "WSL distro : $Distro"
Write-Host "WSL IPv4   : $wslIp"
Write-Host "Port       : $Port"

if ($ShowOnly) {
    Write-Host ""
    Write-Host "Run as Administrator:"
    Write-Host "  netsh interface portproxy delete v4tov4 listenaddress=127.0.0.1 listenport=$Port"
    Write-Host "  netsh interface portproxy delete v4tov4 listenaddress=0.0.0.0 listenport=$Port"
    if (-not $Remove) {
        Write-Host "  netsh interface portproxy add v4tov4 listenaddress=127.0.0.1 listenport=$Port connectaddress=$wslIp connectport=$Port"
        Write-Host "  netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=$Port connectaddress=$wslIp connectport=$Port"
    }
    exit 0
}

Require-Admin

Remove-PortProxy -ListenAddress "127.0.0.1" -ListenPort $Port
Remove-PortProxy -ListenAddress "0.0.0.0" -ListenPort $Port

if (-not $Remove) {
    Add-PortProxy -ListenAddress "127.0.0.1" -ListenPort $Port -ConnectAddress $wslIp -ConnectPort $Port
    Add-PortProxy -ListenAddress "0.0.0.0" -ListenPort $Port -ConnectAddress $wslIp -ConnectPort $Port
}

Write-Host ""
Write-Host "Current portproxy rules:"
& netsh interface portproxy show all

    Write-Host ""
if ($Remove) {
    Write-Host "Removed localhost portproxy for port $Port."
} else {
    Write-Host "Configured localhost portproxy:"
    Write-Host "  http://127.0.0.1:$Port/controller"
    Write-Host "  -> ${wslIp}:$Port"
}
