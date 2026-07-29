@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
title Lipi OS — сборка ISO

rem =============================================================================
rem  Lipi OS ISO — сборка в 1–2 клика (Windows)
rem
rem  Двойной клик  →  через 5 сек соберёт ОБЕ редакции (можно отменить)
rem  build.bat desktop | server | all | clean
rem
rem  Порядок бэкендов:
rem    1) WSL как root  (без пароля sudo) + авто-apt
rem    2) Docker Desktop (всё внутри контейнера)
rem =============================================================================

cd /d "%~dp0.."
set "REPO_ROOT=%CD%"
set "TARGET=%~1"
set "LOG=%REPO_ROOT%\dist\build-windows.log"
set "SKIP_PAUSE=%LIPI_NOPAUSE%"

if not exist "%REPO_ROOT%\dist" mkdir "%REPO_ROOT%\dist" >nul 2>&1

echo.
echo  ============================================================
echo   Lipi OS  ^|  авто-сборка Live ISO под Windows
echo  ============================================================
echo   Папка: %REPO_ROOT%
echo.

if not exist "%REPO_ROOT%\iso\build.sh" (
  echo [X] Не найден iso\build.sh — запускайте из репозитория Lipi-os.
  goto :fail
)
if not exist "%REPO_ROOT%\iso\auto-build.sh" (
  echo [X] Не найден iso\auto-build.sh
  goto :fail
)

if "%TARGET%"=="" goto :autostart
goto :normalize

:autostart
echo   Двойной клик: соберём DESKTOP + SERVER автоматически.
echo   Чтобы выбрать вручную — закройте окно и запустите:
echo     build-iso.bat desktop
echo.
echo   Старт через 5 секунд...  ^(Ctrl+C = отмена^)
timeout /t 5 /nobreak >nul 2>&1
if errorlevel 1 (
  echo Отменено.
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

echo   Цель: %TARGET%
echo   Лог:  dist\build-windows.log
echo.

rem Prefer WSL root (no sudo password)
where wsl >nul 2>&1
if errorlevel 1 goto :try_docker

wsl -e true >nul 2>&1
if errorlevel 1 (
  echo [!] WSL есть, но дистрибутив не готов.
  echo     Пробую установить Ubuntu...
  call :offer_wsl_install
  wsl -e true >nul 2>&1
  if errorlevel 1 goto :try_docker
)

echo [1/3] WSL найден — сборка от root ^(без пароля^)...
for /f "delims=" %%i in ('wsl -e wslpath -a "%REPO_ROOT%" 2^>nul') do set "WSL_ROOT=%%i"
if not defined WSL_ROOT (
  set "WSL_ROOT=%REPO_ROOT%"
  set "WSL_ROOT=!WSL_ROOT:\=/!"
  set "WSL_ROOT=!WSL_ROOT::=!"
  set "WSL_ROOT=/mnt/!WSL_ROOT!"
  call :tolower_drive
)
echo       путь: !WSL_ROOT!
echo [2/3] apt: зависимости скачаются сами при необходимости
echo [3/3] сборка %TARGET% ...
echo.

rem Live output + log (PowerShell Tee-Object)
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Continue';" ^
  "wsl -u root -- bash -lc \"export DEBIAN_FRONTEND=noninteractive; cd '!WSL_ROOT!' && chmod +x iso/auto-build.sh iso/build.sh && ./iso/auto-build.sh %TARGET%\" 2>&1 |" ^
  "Tee-Object -FilePath '%LOG%'; exit $LASTEXITCODE"
set "ERR=!ERRORLEVEL!"
if not "!ERR!"=="0" (
  echo.
  echo [!] WSL-сборка не удалась ^(код !ERR!^). Пробую Docker...
  goto :try_docker
)
goto :success

:menu
echo  1^) desktop   2^) server   3^) all   4^) clean   0^) выход
set /p "CHOICE=Номер: "
if "%CHOICE%"=="1" set "TARGET=desktop" & goto :normalize
if "%CHOICE%"=="2" set "TARGET=server" & goto :normalize
if "%CHOICE%"=="3" set "TARGET=all" & goto :normalize
if "%CHOICE%"=="4" set "TARGET=clean" & goto :normalize
if "%CHOICE%"=="0" exit /b 0
echo Неверный выбор.
goto :fail

:try_docker
where docker >nul 2>&1
if errorlevel 1 goto :no_backend

docker info >nul 2>&1
if errorlevel 1 (
  echo [!] Docker установлен, но не запущен.
  echo     Запустите Docker Desktop и подождите зелёный индикатор…
  echo     Жду до 90 секунд…
  set /a _n=0
  :wait_docker
  timeout /t 5 /nobreak >nul
  docker info >nul 2>&1
  if not errorlevel 1 goto :docker_ready
  set /a _n+=5
  if !_n! GEQ 90 (
    echo [X] Docker так и не ответил.
    goto :no_backend
  )
  echo     … !_n!/90 с
  goto :wait_docker
)

:docker_ready
echo [1/3] Docker готов
echo [2/3] Тянем ubuntu:24.04 и ставим пакеты автоматически…
echo [3/3] Сборка %TARGET% в привилегированном контейнере…
echo.

rem No -it : works on double-click (no TTY). Log to file + console via powershell tee alternative.
docker pull ubuntu:24.04
if errorlevel 1 (
  echo [X] Не удалось скачать ubuntu:24.04 — проверьте интернет.
  goto :fail
)

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Continue';" ^
  "docker run --rm --privileged " ^
  "-e DEBIAN_FRONTEND=noninteractive -e NEEDRESTART_MODE=a " ^
  "-v '%REPO_ROOT%:/lipi' -w /lipi ubuntu:24.04 " ^
  "bash -lc 'chmod +x iso/auto-build.sh iso/build.sh && ./iso/auto-build.sh %TARGET%' 2>&1 |" ^
  "Tee-Object -FilePath '%LOG%'; exit $LASTEXITCODE"

set "ERR=!ERRORLEVEL!"
if not "!ERR!"=="0" (
  echo.
  echo [X] Docker-сборка упала ^(код !ERR!^). См. dist\build-windows.log
  goto :fail
)
goto :success

:offer_wsl_install
echo.
echo  Установить Ubuntu в WSL сейчас? Потребуются права администратора.
echo  После установки Windows может попросить ПЕРЕЗАГРУЗКУ.
set /p "WI=Ставить WSL+Ubuntu? [Y/N]: "
if /i not "%WI%"=="Y" if /i not "%WI%"=="Д" if /i not "%WI%"=="y" goto :eof
powershell -NoProfile -Command "Start-Process wsl -ArgumentList '--install','-d','Ubuntu' -Verb RunAs -Wait"
echo  Если просили reboot — перезагрузите ПК и снова запустите build-iso.bat
goto :eof

:no_backend
echo.
echo [X] Нет готового Linux-бэкенда.
echo.
echo  Сделайте ОДИН раз ^(далее всё будет в 1–2 клика^):
echo.
echo  A^) WSL2 + Ubuntu  ^(рекомендуется^)
echo       в PowerShell от Администратора:
echo         wsl --install -d Ubuntu
echo       перезагрузка → снова build-iso.bat
echo.
echo  B^) Docker Desktop
echo       https://www.docker.com/products/docker-desktop/
echo       установить, запустить, снова build-iso.bat
echo.
echo  Этот скрипт сам скачает зависимости и соберёт ISO.
goto :fail

:success
echo.
echo  ============================================================
echo   ГОТОВО
echo  ============================================================
set "ANY="
if exist "%REPO_ROOT%\dist\lipi-os-live.iso" (
  set "ANY=1"
  for %%F in ("%REPO_ROOT%\dist\lipi-os-live.iso") do (
    echo   Desktop:  dist\lipi-os-live.iso
    echo             %%~zF байт
  )
  if exist "%REPO_ROOT%\dist\lipi-os-live.iso.sha256" type "%REPO_ROOT%\dist\lipi-os-live.iso.sha256"
)
if exist "%REPO_ROOT%\dist\lipi-os-server.iso" (
  set "ANY=1"
  for %%F in ("%REPO_ROOT%\dist\lipi-os-server.iso") do (
    echo   Server:   dist\lipi-os-server.iso
    echo             %%~zF байт
  )
  if exist "%REPO_ROOT%\dist\lipi-os-server.iso.sha256" type "%REPO_ROOT%\dist\lipi-os-server.iso.sha256"
)
if not defined ANY (
  if /i "%TARGET%"=="clean" (
    echo   Кэш iso\.work очищен.
  ) else (
    echo   [?] ISO-файлы не найдены в dist\ — смотрите лог.
  )
)
echo.
echo   Запись на флешку: Rufus → режим DD / Image mode
echo   Лог сборки: dist\build-windows.log
echo.

rem Open dist folder for convenience (second "click" result)
if defined ANY (
  echo   Открываю папку dist…
  start "" explorer "%REPO_ROOT%\dist"
)

if /i "%SKIP_PAUSE%"=="1" exit /b 0
pause
exit /b 0

:fail
echo.
if /i not "%SKIP_PAUSE%"=="1" pause
exit /b 1

:tolower_drive
set "WSL_ROOT=%WSL_ROOT:/mnt/A=/mnt/a%"
set "WSL_ROOT=%WSL_ROOT:/mnt/B=/mnt/b%"
set "WSL_ROOT=%WSL_ROOT:/mnt/C=/mnt/c%"
set "WSL_ROOT=%WSL_ROOT:/mnt/D=/mnt/d%"
set "WSL_ROOT=%WSL_ROOT:/mnt/E=/mnt/e%"
set "WSL_ROOT=%WSL_ROOT:/mnt/F=/mnt/f%"
set "WSL_ROOT=%WSL_ROOT:/mnt/G=/mnt/g%"
set "WSL_ROOT=%WSL_ROOT:/mnt/H=/mnt/h%"
goto :eof
