#Requires -Version 5.0
<#
.SYNOPSIS
  Run Lipi OS Live ISO build via WSL (root) or Docker, with live console + log.
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

# Truncate / create log
Set-Content -LiteralPath $LogPath -Value ("Lipi OS ISO build log  {0:u}  backend={1} target={2}" -f (Get-Date), $Backend, $Target) -Encoding UTF8

if ($Backend -eq 'wsl') {
    if ([string]::IsNullOrWhiteSpace($WslRoot)) {
        $resolved = & wsl -e wslpath -a $RepoRoot 2>$null
        if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($resolved)) {
            $WslRoot = ($resolved | Select-Object -Last 1).Trim()
        }
        else {
            $drive = $RepoRoot.Substring(0, 1).ToLowerInvariant()
            $rest = $RepoRoot.Substring(2).Replace('\', '/')
            $WslRoot = "/mnt/$drive$rest"
        }
    }

    Write-Output "WSL root path: $WslRoot" | Write-LiveLog

    # Pass path/target as env vars so bash quoting stays simple (no nested quotes from cmd).
    $bash = 'set -e; export DEBIAN_FRONTEND=noninteractive; cd "$LIPI_WSL_ROOT"; chmod +x iso/auto-build.sh iso/build.sh; exec ./iso/auto-build.sh "$LIPI_TARGET"'

    $wslArgs = @(
        '-u', 'root', '--',
        'env',
        ("LIPI_WSL_ROOT={0}" -f $WslRoot),
        ("LIPI_TARGET={0}" -f $Target),
        'bash', '-lc', $bash
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

    $bash = 'chmod +x iso/auto-build.sh iso/build.sh && ./iso/auto-build.sh "$LIPI_TARGET"'
    $dockerArgs = @(
        'run', '--rm', '--privileged',
        '-e', 'DEBIAN_FRONTEND=noninteractive',
        '-e', 'NEEDRESTART_MODE=a',
        '-e', ("LIPI_TARGET={0}" -f $Target),
        '-v', ("{0}:/lipi" -f $RepoRoot),
        '-w', '/lipi',
        'ubuntu:24.04',
        'bash', '-lc', $bash
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
