@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
title Lipi OS ISO build

rem =============================================================================
rem  Lipi OS ISO - one/two-click build on Windows
rem
rem  Double-click  -> after 5 sec builds BOTH editions (Ctrl+C to cancel)
rem  build.bat desktop | server | all | clean | menu
rem
rem  Backends (in order):
rem    1) WSL as root (no sudo password) + auto apt
rem    2) Docker Desktop (everything inside the container)
rem
rem  Actual build runs via iso\build-windows.ps1 (avoids cmd quoting bugs).
rem =============================================================================

cd /d "%~dp0.."
set "REPO_ROOT=%CD%"
set "TARGET=%~1"
set "LOG=%REPO_ROOT%\dist\build-windows.log"
set "PS1=%REPO_ROOT%\iso\build-windows.ps1"
set "SKIP_PAUSE=%LIPI_NOPAUSE%"

if not exist "%REPO_ROOT%\dist" mkdir "%REPO_ROOT%\dist" >nul 2>&1

echo.
echo  ============================================================
echo   Lipi OS  ^|  Live ISO auto-build for Windows
echo  ============================================================
echo   Folder: %REPO_ROOT%
echo.

if not exist "%REPO_ROOT%\iso\build.sh" (
  echo [X] Missing iso\build.sh - run from the Lipi-os repository.
  goto :fail
)
if not exist "%REPO_ROOT%\iso\auto-build.sh" (
  echo [X] Missing iso\auto-build.sh
  goto :fail
)
if not exist "%PS1%" (
  echo [X] Missing iso\build-windows.ps1
  goto :fail
)

if "%TARGET%"=="" goto :autostart
goto :normalize

:autostart
echo   Double-click: building DESKTOP + SERVER automatically.
echo   Manual target example:
echo     build-iso.bat desktop
echo.
echo   Starting in 5 seconds...  ^(Ctrl+C = cancel^)
timeout /t 5 /nobreak >nul 2>&1
if errorlevel 1 (
  echo Cancelled.
  goto :fail
)
set "TARGET=all"
echo.
goto :normalize

:normalize
if /i "%TARGET%"=="live" set "TARGET=desktop"
if /i "%TARGET%"=="normal" set "TARGET=desktop"
if /i "%TARGET%"=="full" set "TARGET=desktop"
if /i "%TARGET%"=="menu" goto :menu
if /i "%TARGET%"=="srv" set "TARGET=server"
if /i "%TARGET%"=="minimal" set "TARGET=server"
if /i "%TARGET%"=="both" set "TARGET=all"

echo   Target: %TARGET%
echo   Log:    dist\build-windows.log
echo.

rem Prefer WSL root (no sudo password)
where wsl >nul 2>&1
if errorlevel 1 goto :try_docker

wsl -e true >nul 2>&1
if errorlevel 1 (
  echo [WARN] WSL found, but distro is not ready.
  echo        Trying to install Ubuntu...
  call :offer_wsl_install
  wsl -e true >nul 2>&1
  if errorlevel 1 goto :try_docker
)

echo [1/3] WSL found - building as root ^(no sudo password^)...
echo [2/3] apt: dependencies will be installed automatically if needed
echo [3/3] building %TARGET% ...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%PS1%" -Backend wsl -RepoRoot "%REPO_ROOT%" -Target "%TARGET%" -LogPath "%LOG%"
set "ERR=!ERRORLEVEL!"
if not "!ERR!"=="0" (
  echo.
  echo [WARN] WSL build failed ^(exit code !ERR!^). Trying Docker...
  goto :try_docker
)
goto :success

:menu
echo  1^) desktop   2^) server   3^) all   4^) clean   0^) exit
set /p "CHOICE=Number: "
if "%CHOICE%"=="1" set "TARGET=desktop" & goto :normalize
if "%CHOICE%"=="2" set "TARGET=server" & goto :normalize
if "%CHOICE%"=="3" set "TARGET=all" & goto :normalize
if "%CHOICE%"=="4" set "TARGET=clean" & goto :normalize
if "%CHOICE%"=="0" exit /b 0
echo Invalid choice.
goto :fail

:try_docker
where docker >nul 2>&1
if errorlevel 1 goto :no_backend

docker info >nul 2>&1
if errorlevel 1 (
  echo [WARN] Docker is installed but not running.
  echo        Start Docker Desktop and wait for the green indicator.
  echo        Waiting up to 90 seconds...
  set /a _n=0
  :wait_docker
  timeout /t 5 /nobreak >nul
  docker info >nul 2>&1
  if not errorlevel 1 goto :docker_ready
  set /a _n+=5
  if !_n! GEQ 90 (
    echo [X] Docker did not respond.
    goto :no_backend
  )
  echo        ... !_n!/90 s
  goto :wait_docker
)

:docker_ready
echo [1/3] Docker ready
echo [2/3] Pulling ubuntu:24.04 and installing packages automatically...
echo [3/3] Building %TARGET% in a privileged container...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%PS1%" -Backend docker -RepoRoot "%REPO_ROOT%" -Target "%TARGET%" -LogPath "%LOG%"
set "ERR=!ERRORLEVEL!"
if not "!ERR!"=="0" (
  echo.
  echo [X] Docker build failed ^(exit code !ERR!^). See dist\build-windows.log
  goto :fail
)
goto :success

:offer_wsl_install
echo.
echo  Install Ubuntu in WSL now? Administrator rights required.
echo  Windows may ask you to REBOOT after install.
set /p "WI=Install WSL+Ubuntu? [Y/N]: "
if /i not "%WI%"=="Y" if /i not "%WI%"=="y" goto :eof
powershell -NoProfile -Command "Start-Process wsl -ArgumentList '--install','-d','Ubuntu' -Verb RunAs -Wait"
echo  If reboot was requested - reboot, then run build-iso.bat again.
goto :eof

:no_backend
echo.
echo [X] No ready Linux backend found.
echo.
echo  Do this ONCE (then builds are 1-2 clicks):
echo.
echo  A^) WSL2 + Ubuntu  ^(recommended^)
echo       In PowerShell as Administrator:
echo         wsl --install -d Ubuntu
echo       Reboot, then run build-iso.bat again.
echo.
echo  B^) Docker Desktop
echo       https://www.docker.com/products/docker-desktop/
echo       Install, start it, then run build-iso.bat again.
echo.
echo  This script downloads dependencies and builds the ISO itself.
goto :fail

:success
echo.
echo  ============================================================
echo   DONE
echo  ============================================================
set "ANY="
if exist "%REPO_ROOT%\dist\lipi-os-live.iso" (
  set "ANY=1"
  for %%F in ("%REPO_ROOT%\dist\lipi-os-live.iso") do (
    echo   Desktop:  dist\lipi-os-live.iso
    echo             %%~zF bytes
  )
  if exist "%REPO_ROOT%\dist\lipi-os-live.iso.sha256" type "%REPO_ROOT%\dist\lipi-os-live.iso.sha256"
)
if exist "%REPO_ROOT%\dist\lipi-os-server.iso" (
  set "ANY=1"
  for %%F in ("%REPO_ROOT%\dist\lipi-os-server.iso") do (
    echo   Server:   dist\lipi-os-server.iso
    echo             %%~zF bytes
  )
  if exist "%REPO_ROOT%\dist\lipi-os-server.iso.sha256" type "%REPO_ROOT%\dist\lipi-os-server.iso.sha256"
)
if not defined ANY (
  if /i "%TARGET%"=="clean" (
    echo   Cache iso\.work cleaned.
  ) else (
    echo   [?] ISO files not found in dist\ - see the log.
  )
)
echo.
echo   Flash with Rufus - DD / Image mode
echo   Build log: dist\build-windows.log
echo.

if defined ANY (
  echo   Opening dist folder...
  start "" explorer "%REPO_ROOT%\dist"
)

if /i "%SKIP_PAUSE%"=="1" exit /b 0
pause
exit /b 0

:fail
echo.
if /i not "%SKIP_PAUSE%"=="1" pause
exit /b 1
