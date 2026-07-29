#Requires -Version 5.0
<#
.SYNOPSIS
  Run Lipi OS Live ISO build via WSL (root) or Docker, with live console + log.

  Paths may contain spaces or characters like ( ) — they are passed as argv /
  properly quoted, never via bare env assignments that bash re-parses.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('wsl', 'docker')]
    [string]$Backend,

    [Parameter(Mandatory = $true)]
    [string]$RepoRoot,

    [Parameter(Mandatory = $true)]
    [string]$Target,

    [Parameter(Mandatory = $true)]
    [string]$LogPath,

    [string]$WslRoot = ''
)

$ErrorActionPreference = 'Continue'
$RepoRoot = [System.IO.Path]::GetFullPath($RepoRoot)
$LogDir = Split-Path -Parent $LogPath
if (-not (Test-Path -LiteralPath $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

function Write-LiveLog {
    param([Parameter(ValueFromPipeline = $true)][string]$Line)
    process {
        if ($null -eq $Line) { return }
        $Line
        Add-Content -LiteralPath $LogPath -Value $Line -Encoding UTF8
    }
}

function ConvertTo-WslPath {
    param([string]$WindowsPath)
    $resolved = & wsl -e wslpath -a $WindowsPath 2>$null
    if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($resolved)) {
        return ($resolved | Select-Object -Last 1).Trim()
    }
    $drive = $WindowsPath.Substring(0, 1).ToLowerInvariant()
    $rest = $WindowsPath.Substring(2).Replace('\', '/')
    return "/mnt/$drive$rest"
}

# Truncate / create log
Set-Content -LiteralPath $LogPath -Value ("Lipi OS ISO build log  {0:u}  backend={1} target={2}" -f (Get-Date), $Backend, $Target) -Encoding UTF8

if ($Backend -eq 'wsl') {
    if ([string]::IsNullOrWhiteSpace($WslRoot)) {
        $WslRoot = ConvertTo-WslPath -WindowsPath $RepoRoot
    }

    Write-Output "WSL root path: $WslRoot" | Write-LiveLog

    # IMPORTANT: pass repo path / target as bash positional args ($1, $2).
    # Do NOT use: env LIPI_WSL_ROOT=/path/with(parens) — bash treats ( as syntax.
    # bash -lc '...' name arg1 arg2  => $0=name, $1=arg1, $2=arg2
    $bash = 'set -euo pipefail; export DEBIAN_FRONTEND=noninteractive; cd "$1"; chmod +x iso/auto-build.sh iso/build.sh; exec ./iso/auto-build.sh "$2"'

    $wslArgs = @(
        '-u', 'root', '--',
        'bash', '-lc', $bash,
        'lipi-build',
        $WslRoot,
        $Target
    )

    & wsl @wslArgs 2>&1 | ForEach-Object {
        if ($_ -is [System.Management.Automation.ErrorRecord]) {
            $_.ToString() | Write-LiveLog
        }
        else {
            "$_" | Write-LiveLog
        }
    }
    exit $LASTEXITCODE
}

if ($Backend -eq 'docker') {
    Write-Output 'Pulling ubuntu:24.04 ...' | Write-LiveLog
    & docker pull ubuntu:24.04 2>&1 | ForEach-Object { "$_" | Write-LiveLog }
    if ($LASTEXITCODE -ne 0) {
        Write-Output 'docker pull failed' | Write-LiveLog
        exit $LASTEXITCODE
    }

    # Target via argv ($1); volume path is handled by Docker API (parens OK).
    $bash = 'set -euo pipefail; chmod +x iso/auto-build.sh iso/build.sh; exec ./iso/auto-build.sh "$1"'
    $dockerArgs = @(
        'run', '--rm', '--privileged',
        '-e', 'DEBIAN_FRONTEND=noninteractive',
        '-e', 'NEEDRESTART_MODE=a',
        '-v', "${RepoRoot}:/lipi",
        '-w', '/lipi',
        'ubuntu:24.04',
        'bash', '-lc', $bash,
        'lipi-build',
        $Target
    )

    & docker @dockerArgs 2>&1 | ForEach-Object {
        if ($_ -is [System.Management.Automation.ErrorRecord]) {
            $_.ToString() | Write-LiveLog
        }
        else {
            "$_" | Write-LiveLog
        }
    }
    exit $LASTEXITCODE
}

Write-Output "Unknown backend: $Backend" | Write-LiveLog
exit 2
