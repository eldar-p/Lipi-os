#Requires -Version 5.0
<#
.SYNOPSIS
  Run Lipi OS Live ISO build via WSL (root) or Docker, with live console + log.

  WSL note: plain `wsl cmd args` joins args into one shell string, so paths with
  ( ) break bash. We always use `wsl --exec` (real argv) and build on a Linux
  filesystem path under /var/tmp (no DrvFs quirks / special chars).
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
    param([Parameter(ValueFromPipeline = $true)][object]$Line)
    process {
        if ($null -eq $Line) { return }
        $text = if ($Line -is [System.Management.Automation.ErrorRecord]) {
            $Line.ToString()
        } else {
            "$Line"
        }
        $text
        Add-Content -LiteralPath $LogPath -Value $text -Encoding UTF8
    }
}

function ConvertTo-WslPath {
    param([string]$WindowsPath)
    # wslpath via --exec so parentheses in the Windows path are not re-parsed
    $resolved = & wsl --exec wslpath -a $WindowsPath 2>$null
    if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($resolved)) {
        return ($resolved | Select-Object -Last 1).Trim()
    }
    $drive = $WindowsPath.Substring(0, 1).ToLowerInvariant()
    $rest = $WindowsPath.Substring(2).Replace('\', '/')
    return "/mnt/$drive$rest"
}

function Invoke-WslExec {
    param(
        [Parameter(Mandatory = $true)][string]$BashScript,
        [string[]]$BashArgs = @()
    )
    # --exec: pass real argv to bash; do NOT let wsl join into /bin/sh -c "..."
    # bash -c SCRIPT $0 $1 $2 ...  => our SCRIPT uses $1 $2 $3, so $0 is a dummy.
    $argv = @('-u', 'root', '--exec', 'bash', '-c', $BashScript, 'lipi-build') + $BashArgs
    $output = & wsl @argv 2>&1
    $code = $LASTEXITCODE
    $output | Write-LiveLog
    return $code
}

Set-Content -LiteralPath $LogPath -Value ("Lipi OS ISO build log  {0:u}  backend={1} target={2}" -f (Get-Date), $Backend, $Target) -Encoding UTF8

if ($Backend -eq 'wsl') {
    if ([string]::IsNullOrWhiteSpace($WslRoot)) {
        $WslRoot = ConvertTo-WslPath -WindowsPath $RepoRoot
    }

    $safeRoot = '/var/tmp/lipi-os-build'
    Write-Output "Windows/WSL source: $WslRoot" | Write-LiveLog
    Write-Output "Build directory:    $safeRoot  (Linux FS, safe path)" | Write-LiveLog

    # $1 = source on /mnt/..., $2 = safe build dir, $3 = target
    # Copy onto ext4 so debootstrap/chmod work; path has no ( ) from Windows zips.
    $syncAndBuild = @'
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
SRC="$1"
DST="$2"
TARGET="$3"
echo "==> Sync $SRC -> $DST"
rm -rf "$DST"
mkdir -p "$DST"
if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete \
    --exclude '.git/' \
    --exclude 'iso/.work/' \
    --exclude 'dist/*.iso' \
    --exclude 'dist/*.iso.sha256' \
    "$SRC"/ "$DST"/
else
  tar -C "$SRC" \
    --exclude='.git' \
    --exclude='iso/.work' \
    --exclude='dist' \
    -cf - . | tar -C "$DST" -xf -
  mkdir -p "$DST/dist"
fi
cd "$DST"
chmod +x iso/auto-build.sh iso/build.sh
./iso/auto-build.sh "$TARGET"
echo "==> Copy ISO artifacts back to Windows tree"
mkdir -p "$SRC/dist"
cp -f "$DST"/dist/*.iso "$SRC/dist/" 2>/dev/null || true
cp -f "$DST"/dist/*.iso.sha256 "$SRC/dist/" 2>/dev/null || true
ls -lh "$SRC/dist" || true
'@

    $code = Invoke-WslExec -BashScript $syncAndBuild -BashArgs @($WslRoot, $safeRoot, $Target)
    exit $code
}

if ($Backend -eq 'docker') {
    Write-Output 'Pulling ubuntu:24.04 ...' | Write-LiveLog
    & docker pull ubuntu:24.04 2>&1 | Write-LiveLog
    if ($LASTEXITCODE -ne 0) {
        Write-Output 'docker pull failed' | Write-LiveLog
        exit $LASTEXITCODE
    }

    # Target as argv $1; Docker volume API accepts ( ) in Windows paths.
    $bash = 'set -euo pipefail; chmod +x iso/auto-build.sh iso/build.sh; exec ./iso/auto-build.sh "$1"'
    $dockerArgs = @(
        'run', '--rm', '--privileged',
        '-e', 'DEBIAN_FRONTEND=noninteractive',
        '-e', 'NEEDRESTART_MODE=a',
        '-v', "${RepoRoot}:/lipi",
        '-w', '/lipi',
        'ubuntu:24.04',
        'bash', '-c', $bash,
        'lipi-build',
        $Target
    )

    & docker @dockerArgs 2>&1 | Write-LiveLog
    exit $LASTEXITCODE
}

Write-Output "Unknown backend: $Backend" | Write-LiveLog
exit 2
