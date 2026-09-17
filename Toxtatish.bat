@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul 2>&1
title Lombard - serverni to'xtatish

set "PORT=8010"
if exist "%~dp0port.txt" set /p PORT=<"%~dp0port.txt"

echo.
echo   Port !PORT! dagi server to'xtatilmoqda...
echo.

set "TOPILDI="
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /c:":!PORT! " ^| findstr /i "LISTENING"') do (
    taskkill /PID %%P /F >nul 2>&1
    set "TOPILDI=1"
)

if defined TOPILDI (
    echo   Server to'xtatildi.
) else (
    echo   Ishlab turgan server topilmadi.
)
echo.
timeout /t 3 >nul
endlocal
