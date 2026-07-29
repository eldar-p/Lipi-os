#Requires -Version 5.0
<#
.SYNOPSIS
  Run Lipi OS Live ISO build via WSL (root) or Docker.

  Always builds on a Linux filesystem (/var/tmp/...), then COPIES the .iso
  back into the Windows project folder: <RepoRoot>\dist\
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
$DistDir = Join-Path $RepoRoot 'dist'
$LogDir = Split-Path -Parent $LogPath
if (-not (Test-Path -LiteralPath $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}
if (-not (Test-Path -LiteralPath $DistDir)) {
    New-Item -ItemType Directory -Path $DistDir -Force | Out-Null
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
    $resolved = & wsl --exec wslpath -a $WindowsPath 2>$null
    if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($resolved)) {
        return ($resolved | Select-Object -Last 1).Trim()
    }
    $drive = $WindowsPath.Substring(0, 1).ToLowerInvariant()
    $rest = $WindowsPath.Substring(2).Replace('\', '/')
    return "/mnt/$drive$rest"
}

function Get-ExpectedIsoNames {
    param([string]$BuildTarget)
    switch -Regex ($BuildTarget.ToLowerInvariant()) {
        '^(desktop|live|normal|full)$' { @('lipi-os-live.iso') }
        '^(server|srv|minimal)$' { @('lipi-os-server.iso') }
        '^(all|both)$' { @('lipi-os-live.iso', 'lipi-os-server.iso') }
        'clean' { @() }
        default { @('lipi-os-live.iso') }
    }
}

function Test-ProjectDistIsos {
    param([string[]]$Names)
    $missing = @()
    foreach ($name in $Names) {
        $path = Join-Path $DistDir $name
        if (-not (Test-Path -LiteralPath $path)) {
            $missing += $name
        }
    }
    return $missing
}

function Show-ProjectDistIsos {
    Write-Output '' | Write-LiveLog
    Write-Output '==== ISO in PROJECT folder (Windows) ====' | Write-LiveLog
    Write-Output "Folder: $DistDir" | Write-LiveLog
    Get-ChildItem -LiteralPath $DistDir -Filter '*.iso' -ErrorAction SilentlyContinue | ForEach-Object {
        Write-Output ("  {0}  ({1:N0} bytes)" -f $_.FullName, $_.Length) | Write-LiveLog
    }
    Get-ChildItem -LiteralPath $DistDir -Filter '*.iso.sha256' -ErrorAction SilentlyContinue | ForEach-Object {
        Write-Output ("  {0}" -f $_.Name) | Write-LiveLog
    }
}

Set-Content -LiteralPath $LogPath -Value ("Lipi OS ISO build log  {0:u}  backend={1} target={2}" -f (Get-Date), $Backend, $Target) -Encoding UTF8
Write-Output "Project folder: $RepoRoot" | Write-LiveLog
Write-Output "ISO output:     $DistDir" | Write-LiveLog

$expected = Get-ExpectedIsoNames -BuildTarget $Target

if ($Backend -eq 'wsl') {
    if ([string]::IsNullOrWhiteSpace($WslRoot)) {
        $WslRoot = ConvertTo-WslPath -WindowsPath $RepoRoot
    }
    $WslLog = ConvertTo-WslPath -WindowsPath $LogPath
    $safeRoot = '/var/tmp/lipi-os-build'

    Write-Output "WSL source path: $WslRoot" | Write-LiveLog
    Write-Output "WSL build path:  $safeRoot (temp; ISO will be copied to project dist\)" | Write-LiveLog

    # $1=src $2=dst $3=target $4=windows log (wsl path)
    $syncAndBuild = @'
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
SRC="$1"
DST="$2"
TARGET="$3"
WINLOG="$4"
mkdir -p "$SRC/dist"
touch "$WINLOG" 2>/dev/null || true
log() { echo "$1" | tee -a "$WINLOG"; }

log "==> Sync $SRC -> $DST"
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
  tar -C "$SRC" --exclude='.git' --exclude='iso/.work' --exclude='dist' -cf - . | tar -C "$DST" -xf -
  mkdir -p "$DST/dist"
fi

cd "$DST"
chmod +x iso/auto-build.sh iso/build.sh iso/*.sh 2>/dev/null || true
# strip CRLF if Windows checkout contaminated scripts
find iso -name '*.sh' -print0 2>/dev/null | xargs -0 -r sed -i 's/\r$//' || true

log "==> Building inside WSL ($TARGET) — ISO will be copied to Windows project dist\\"
./iso/auto-build.sh "$TARGET" 2>&1 | tee -a "$WINLOG"

log "==> Copying ISO artifacts to Windows project: $SRC/dist"
mkdir -p "$SRC/dist"
shopt -s nullglob
ISOS=("$DST"/dist/*.iso)
if ((${#ISOS[@]} == 0)); then
  log "[X] No ISO produced under $DST/dist"
  ls -la "$DST/dist" 2>&1 | tee -a "$WINLOG" || true
  exit 1
fi
cp -f "$DST"/dist/*.iso "$SRC/dist/"
cp -f "$DST"/dist/*.iso.sha256 "$SRC/dist/" 2>/dev/null || true
# force sync to DrvFs
sync || true
log "==> Files in Windows dist:"
ls -lh "$SRC/dist" | tee -a "$WINLOG"
'@

    # Stream live: do not capture; bash tees into the Windows log path.
    $argv = @(
        '-u', 'root', '--exec', 'bash', '-c', $syncAndBuild,
        'lipi-build', $WslRoot, $safeRoot, $Target, $WslLog
    )
    & wsl @argv
    $code = $LASTEXITCODE

    Show-ProjectDistIsos
    $missing = Test-ProjectDistIsos -Names $expected
    if ($code -ne 0 -or ($expected.Count -gt 0 -and $missing.Count -gt 0)) {
        if ($missing.Count -gt 0) {
            Write-Output ("[X] Missing in project dist\: {0}" -f ($missing -join ', ')) | Write-LiveLog
        }
        exit $(if ($code -ne 0) { $code } else { 1 })
    }
    Write-Output '[OK] ISO is in the project dist\ folder (not only inside WSL).' | Write-LiveLog
    exit 0
}

if ($Backend -eq 'docker') {
    Write-Output 'Pulling ubuntu:24.04 ...' | Write-LiveLog
    & docker pull ubuntu:24.04 2>&1 | Write-LiveLog
    if ($LASTEXITCODE -ne 0) {
        Write-Output 'docker pull failed' | Write-LiveLog
        exit $LASTEXITCODE
    }

    # Same pattern as WSL: copy off the Windows mount into container /var/tmp, build, copy ISO back.
    $bash = @'
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
TARGET="$1"
SRC=/lipi-src
DST=/var/tmp/lipi-os-build
echo "==> Sync $SRC -> $DST (Linux FS inside container)"
rm -rf "$DST"
mkdir -p "$DST" /lipi-out
if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete --exclude '.git/' --exclude 'iso/.work/' --exclude 'dist/*.iso' --exclude 'dist/*.iso.sha256' "$SRC"/ "$DST"/
else
  apt-get update -qq && apt-get install -y -qq rsync >/dev/null
  rsync -a --delete --exclude '.git/' --exclude 'iso/.work/' --exclude 'dist/*.iso' "$SRC"/ "$DST"/
fi
cd "$DST"
chmod +x iso/auto-build.sh iso/build.sh
find iso -name '*.sh' -print0 | xargs -0 -r sed -i 's/\r$//' || true
./iso/auto-build.sh "$TARGET"
echo "==> Copy ISO to Windows project mount /lipi-out"
shopt -s nullglob
ISOS=("$DST"/dist/*.iso)
if ((${#ISOS[@]} == 0)); then
  echo "[X] No ISO produced"
  exit 1
fi
cp -f "$DST"/dist/*.iso /lipi-out/
cp -f "$DST"/dist/*.iso.sha256 /lipi-out/ 2>/dev/null || true
ls -lh /lipi-out
'@

    $dockerArgs = @(
        'run', '--rm', '--privileged',
        '-e', 'DEBIAN_FRONTEND=noninteractive',
        '-e', 'NEEDRESTART_MODE=a',
        '-v', "${RepoRoot}:/lipi-src",
        '-v', "${DistDir}:/lipi-out",
        'ubuntu:24.04',
        'bash', '-c', $bash,
        'lipi-build',
        $Target
    )

    & docker @dockerArgs 2>&1 | Write-LiveLog
    $code = $LASTEXITCODE
    Show-ProjectDistIsos
    $missing = Test-ProjectDistIsos -Names $expected
    if ($code -ne 0 -or ($expected.Count -gt 0 -and $missing.Count -gt 0)) {
        if ($missing.Count -gt 0) {
            Write-Output ("[X] Missing in project dist\: {0}" -f ($missing -join ', ')) | Write-LiveLog
        }
        exit $(if ($code -ne 0) { $code } else { 1 })
    }
    Write-Output '[OK] ISO is in the project dist\ folder.' | Write-LiveLog
    exit 0
}

Write-Output "Unknown backend: $Backend" | Write-LiveLog
exit 2
