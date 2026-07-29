#Requires -Version 5.0
<#
.SYNOPSIS
  Run Lipi OS Live ISO build via WSL (root) or Docker.

  Builds on Linux FS (/var/tmp/...), then COPIES .iso into <RepoRoot>\dist\
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
        try {
            Add-Content -LiteralPath $LogPath -Value $text -Encoding UTF8 -ErrorAction SilentlyContinue
        } catch {}
    }
}

function ConvertTo-WslPath {
    param([string]$WindowsPath)
    # Prefer wslpath; fall back to /mnt/<drive>/...
    $resolved = & wsl -u root --exec wslpath -a $WindowsPath 2>$null
    if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($resolved)) {
        return ($resolved | Select-Object -Last 1).Trim()
    }
    $resolved = & wsl --exec wslpath -a $WindowsPath 2>$null
    if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($resolved)) {
        return ($resolved | Select-Object -Last 1).Trim()
    }
    $drive = $WindowsPath.Substring(0, 1).ToLowerInvariant()
    $rest = $WindowsPath.Substring(2).Replace('\', '/')
    return "/mnt/$drive$rest"
}

function Write-UnixFile {
    param([string]$Path, [string]$Content)
    $lf = $Content -replace "`r`n", "`n" -replace "`r", "`n"
    if (-not $lf.EndsWith("`n")) { $lf += "`n" }
    [System.IO.File]::WriteAllText($Path, $lf, [System.Text.UTF8Encoding]::new($false))
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
}

Set-Content -LiteralPath $LogPath -Value ("Lipi OS ISO build log  {0:u}  backend={1} target={2}" -f (Get-Date), $Backend, $Target) -Encoding UTF8
Write-Output "Project folder: $RepoRoot" | Write-LiveLog
Write-Output "ISO output:     $DistDir" | Write-LiveLog

$expected = Get-ExpectedIsoNames -BuildTarget $Target
$innerSrc = Join-Path $RepoRoot 'iso\wsl-build-inner.sh'
$dockerInnerSrc = Join-Path $RepoRoot 'iso\docker-build-inner.sh'

if ($Backend -eq 'wsl') {
    if (-not (Test-Path -LiteralPath $innerSrc)) {
        Write-Output "[X] Missing iso\wsl-build-inner.sh" | Write-LiveLog
        exit 1
    }

    # Preflight: can we run as root?
    $probe = & wsl -u root --exec /bin/bash -c 'echo LIPI_WSL_ROOT_OK; id -u' 2>&1
    $probeCode = $LASTEXITCODE
    $probe | Write-LiveLog
    if ($probeCode -ne 0) {
        Write-Output "[X] wsl -u root --exec failed (exit $probeCode). Is your default distro Ubuntu and root enabled?" | Write-LiveLog
        exit $probeCode
    }

    if ([string]::IsNullOrWhiteSpace($WslRoot)) {
        $WslRoot = ConvertTo-WslPath -WindowsPath $RepoRoot
    }
    $WslLog = ConvertTo-WslPath -WindowsPath $LogPath
    $safeRoot = '/var/tmp/lipi-os-build'
    $innerWsl = ConvertTo-WslPath -WindowsPath $innerSrc

    Write-Output "WSL source path: $WslRoot" | Write-LiveLog
    Write-Output "WSL build path:  $safeRoot" | Write-LiveLog
    Write-Output "Inner script:    $innerWsl" | Write-LiveLog

    # Install inner script onto Linux FS (strip CRLF only — NOT tr -d "\r", which deletes letter r!)
    $stageCmd = 'sed "s/\r$//" < "$1" > /var/tmp/lipi-wsl-build-inner.sh && chmod +x /var/tmp/lipi-wsl-build-inner.sh && head -n 6 /var/tmp/lipi-wsl-build-inner.sh && echo STAGED_OK'
    Write-Output "==> Staging inner build script into WSL /var/tmp ..." | Write-LiveLog
    $stageOut = & wsl -u root --exec /bin/bash -c $stageCmd -- $innerWsl 2>&1
    $stageCode = $LASTEXITCODE
    $stageOut | Write-LiveLog
    if ($stageCode -ne 0) {
        Write-Output "[X] Failed to stage inner script (exit $stageCode)" | Write-LiveLog
        exit $stageCode
    }
    # Sanity: staged file must contain a real 'export' (guards against the old tr bug)
    $check = & wsl -u root --exec /bin/bash -c 'grep -n "^export " /var/tmp/lipi-wsl-build-inner.sh | head -n 2' 2>&1
    $check | Write-LiveLog
    if ("$check" -notmatch 'export ') {
        Write-Output "[X] Staged script looks corrupted (no export lines). Aborting." | Write-LiveLog
        exit 1
    }

    Write-Output "==> Starting WSL build (live output below) ..." | Write-LiveLog
    # Run staged script with real argv (paths may contain parentheses).
    $argv = @(
        '-u', 'root', '--exec', '/bin/bash',
        '/var/tmp/lipi-wsl-build-inner.sh',
        $WslRoot, $safeRoot, $Target, $WslLog
    )
    # Live console + also keep exit code
    & wsl @argv
    $code = $LASTEXITCODE
    Write-Output ("==> WSL inner exit code: {0}" -f $code) | Write-LiveLog

    Show-ProjectDistIsos
    $missing = Test-ProjectDistIsos -Names $expected
    if ($code -ne 0 -or ($expected.Count -gt 0 -and $missing.Count -gt 0)) {
        if ($missing.Count -gt 0) {
            Write-Output ("[X] Missing in project dist\: {0}" -f ($missing -join ', ')) | Write-LiveLog
            Write-Output '    Open dist\build-windows.log for the full WSL output.' | Write-LiveLog
        }
        exit $(if ($code -ne 0) { $code } else { 1 })
    }
    Write-Output '[OK] ISO is in the project dist\ folder (Windows).' | Write-LiveLog
    exit 0
}

if ($Backend -eq 'docker') {
    if (-not (Test-Path -LiteralPath $dockerInnerSrc)) {
        Write-Output "[X] Missing iso\docker-build-inner.sh" | Write-LiveLog
        exit 1
    }

    Write-Output 'Pulling ubuntu:24.04 ...' | Write-LiveLog
    & docker pull ubuntu:24.04 2>&1 | Write-LiveLog
    if ($LASTEXITCODE -ne 0) {
        Write-Output 'docker pull failed' | Write-LiveLog
        exit $LASTEXITCODE
    }

    # Normalize inner script to LF in dist so container can run it reliably
    $dockerRunSh = Join-Path $DistDir '_docker-build-inner.sh'
    $raw = [System.IO.File]::ReadAllText($dockerInnerSrc)
    Write-UnixFile -Path $dockerRunSh -Content $raw

    $dockerArgs = @(
        'run', '--rm', '--privileged',
        '-e', 'DEBIAN_FRONTEND=noninteractive',
        '-e', 'NEEDRESTART_MODE=a',
        '-v', "${RepoRoot}:/lipi-src",
        '-v', "${DistDir}:/lipi-out",
        'ubuntu:24.04',
        'bash', '/lipi-out/_docker-build-inner.sh',
        $Target
    )

    & docker @dockerArgs 2>&1 | Write-LiveLog
    $code = $LASTEXITCODE
    Remove-Item -LiteralPath $dockerRunSh -Force -ErrorAction SilentlyContinue

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
