@echo off
rem Двойной клик = авто-сборка обеих ISO (desktop + server) через WSL/Docker.
cd /d "%~dp0"
call "%~dp0iso\build.bat" %*
