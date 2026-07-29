@echo off
rem Удобный ярлык из корня репозитория → iso\build.bat
cd /d "%~dp0"
call "%~dp0iso\build.bat" %*
