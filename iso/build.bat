@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

rem =============================================================================
rem  Lipi OS — сборка Live ISO из Windows
rem  Запускает iso/build.sh через WSL (предпочтительно) или Docker.
rem
rem  Использование:
rem    build.bat                 — меню
rem    build.bat desktop         — обычная (полная)
rem    build.bat server          — серверная (урезанная)
rem    build.bat all             — обе
rem    build.bat clean           — очистить сборочный кэш
rem =============================================================================

cd /d "%~dp0.."
set "REPO_ROOT=%CD%"
set "TARGET=%~1"

echo.
echo  ========================================
echo   Lipi OS ISO Builder  (Windows)
echo  ========================================
echo   Каталог: %REPO_ROOT%
echo.

if not exist "%REPO_ROOT%\iso\build.sh" (
  echo [ОШИБКА] Не найден iso\build.sh
  echo Запускайте bat из репозитория Lipi-os.
  goto :fail
)

if "%TARGET%"=="" goto :menu
goto :dispatch

:menu
echo  Выберите сборку:
echo    1^) desktop   — обычная  ^(lipi-os-live.iso^)
echo    2^) server    — серверная ^(lipi-os-server.iso^)
echo    3^) all       — обе редакции
echo    4^) clean     — удалить iso\.work
echo    0^) выход
echo.
set /p "CHOICE=Номер: "
if "%CHOICE%"=="1" set "TARGET=desktop"
if "%CHOICE%"=="2" set "TARGET=server"
if "%CHOICE%"=="3" set "TARGET=all"
if "%CHOICE%"=="4" set "TARGET=clean"
if "%CHOICE%"=="0" goto :eof
if "%TARGET%"=="" (
  echo Неверный выбор.
  goto :fail
)

:dispatch
if /i "%TARGET%"=="live" set "TARGET=desktop"
if /i "%TARGET%"=="normal" set "TARGET=desktop"
if /i "%TARGET%"=="full" set "TARGET=desktop"
if /i "%TARGET%"=="srv" set "TARGET=server"
if /i "%TARGET%"=="minimal" set "TARGET=server"
if /i "%TARGET%"=="both" set "TARGET=all"

echo  Цель: %TARGET%
echo.

rem --- Prefer WSL -------------------------------------------------------------
where wsl >nul 2>&1
if errorlevel 1 goto :try_docker

echo [1/2] Найден WSL — сборка через Linux...
wsl -e true >nul 2>&1
if errorlevel 1 (
  echo [ОШИБКА] WSL установлен, но не запускается.
  echo Установите дистрибутив:  wsl --install -d Ubuntu
  goto :try_docker
)

for /f "delims=" %%i in ('wsl -e wslpath -a "%REPO_ROOT%" 2^>nul') do set "WSL_ROOT=%%i"
if not defined WSL_ROOT (
  rem Fallback: C:\foo\bar -> /mnt/c/foo/bar
  set "WSL_ROOT=%REPO_ROOT%"
  set "WSL_ROOT=!WSL_ROOT:\=/!"
  set "WSL_ROOT=!WSL_ROOT::=!"
  set "WSL_ROOT=/mnt/!WSL_ROOT!"
  call :tolower_drive
)

echo      WSL path: %WSL_ROOT%
echo [2/2] Запуск sudo ./iso/build.sh %TARGET%
echo      ^(потребуется пароль sudo внутри WSL, если настроен^)
echo.

wsl -e bash -lc "cd '%WSL_ROOT%' && chmod +x iso/build.sh && sudo ./iso/build.sh %TARGET%"
set "ERR=!ERRORLEVEL!"
if not "!ERR!"=="0" (
  echo.
  echo [ОШИБКА] Сборка завершилась с кодом !ERR!
  echo Проверьте: sudo в WSL, интернет, место на диске.
  goto :fail
)
goto :success

:try_docker
echo [!] WSL недоступен — пробуем Docker...
where docker >nul 2>&1
if errorlevel 1 goto :no_backend

docker version >nul 2>&1
if errorlevel 1 (
  echo [ОШИБКА] Docker найден, но не отвечает. Запустите Docker Desktop.
  goto :fail
)

echo [1/2] Docker OK. Собираем в контейнере Ubuntu 24.04...
echo [2/2] Это может занять много времени при первой сборке.
echo.

rem Map repo into container; privileged needed for chroot/mounts
docker run --rm -it --privileged ^
  -v "%REPO_ROOT%:/lipi" ^
  -w /lipi ^
  ubuntu:24.04 ^
  bash -lc "apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq sudo debootstrap squashfs-tools xorriso grub-pc-bin grub-efi-amd64-bin mtools dosfstools rsync ca-certificates && chmod +x iso/build.sh && ./iso/build.sh %TARGET%"

set "ERR=!ERRORLEVEL!"
if not "!ERR!"=="0" (
  echo.
  echo [ОШИБКА] Docker-сборка завершилась с кодом !ERR!
  goto :fail
)
goto :success

:no_backend
echo [ОШИБКА] Нужен WSL2 ^(Ubuntu^) или Docker Desktop.
echo.
echo  Вариант A — WSL:
echo    wsl --install -d Ubuntu
echo    ^(перезагрузка^)
echo    затем снова:  iso\build.bat desktop
echo.
echo  Вариант B — Docker Desktop:
echo    https://www.docker.com/products/docker-desktop/
echo    затем снова:  iso\build.bat desktop
echo.
goto :fail

:success
echo.
echo  ========================================
echo   Готово.
echo  ========================================
if exist "%REPO_ROOT%\dist\lipi-os-live.iso" (
  echo   Desktop:  dist\lipi-os-live.iso
  for %%F in ("%REPO_ROOT%\dist\lipi-os-live.iso") do echo            %%~zF bytes
)
if exist "%REPO_ROOT%\dist\lipi-os-server.iso" (
  echo   Server:   dist\lipi-os-server.iso
  for %%F in ("%REPO_ROOT%\dist\lipi-os-server.iso") do echo            %%~zF bytes
)
echo.
echo   Запись на флешку ^(Rufus^): режим DD / Image mode
echo   или в PowerShell ^(осторожно с номером диска^):
echo     Write-Output ... см. iso\README.md
echo.
pause
exit /b 0

:fail
echo.
pause
exit /b 1

rem --- helpers ----------------------------------------------------------------
:tolower_drive
rem Convert /mnt/C/... to /mnt/c/...
set "WSL_ROOT=%WSL_ROOT:/mnt/A=/mnt/a%"
set "WSL_ROOT=%WSL_ROOT:/mnt/B=/mnt/b%"
set "WSL_ROOT=%WSL_ROOT:/mnt/C=/mnt/c%"
set "WSL_ROOT=%WSL_ROOT:/mnt/D=/mnt/d%"
set "WSL_ROOT=%WSL_ROOT:/mnt/E=/mnt/e%"
set "WSL_ROOT=%WSL_ROOT:/mnt/F=/mnt/f%"
set "WSL_ROOT=%WSL_ROOT:/mnt/G=/mnt/g%"
set "WSL_ROOT=%WSL_ROOT:/mnt/H=/mnt/h%"
goto :eof
