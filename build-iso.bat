@echo off
rem Double-click = auto-build both ISOs (desktop + server) via WSL/Docker.
cd /d "%~dp0"
call "%~dp0iso\build.bat" %*
