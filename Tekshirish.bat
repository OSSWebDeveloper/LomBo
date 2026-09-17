@echo off
chcp 65001 >nul 2>&1
title Lombard - tekshirish rejimi
cd /d "%~dp0"

set "PORT=8010"
if exist port.txt set /p PORT=<port.txt

echo.
echo   Server oynali rejimda ishga tushirilmoqda.
echo   Agar xatolik bo'lsa, u shu oynada ko'rinadi.
echo   To'xtatish uchun Ctrl+C bosing.
echo.

if not exist ".venv\Scripts\python.exe" (
    echo   XATO: .venv papkasi topilmadi.
    echo   ORNATISH.bat faylini administrator nomidan qayta ishga tushiring.
    echo.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" manage.py runserver 127.0.0.1:%PORT%
echo.
pause
