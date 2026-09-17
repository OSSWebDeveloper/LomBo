@echo off
rem ============================================================
rem   Lombard - ish stoli yorliqlarini tiklash
rem
rem   Agar o'rnatishdan keyin ish stolida yorliqlar ko'rinmasa,
rem   shu faylni ishga tushiring. Dastur qayta o'rnatilmaydi,
rem   ma'lumotlar bazasiga ham tegilmaydi - faqat yorliqlar
rem   qaytadan yaratiladi.
rem ============================================================
setlocal EnableExtensions EnableDelayedExpansion
title Lombard - yorliqlarni tiklash

rem --- Administrator huquqi: umumiy ish stoliga yozish uchun kerak ---
rem Ish stoli manzili ko'tarilishdan oldin olinadi - UAC boshqa hisob
rem bilan ko'tarilsa, yorliq o'sha hisobning ish stoliga tushib qolmasin.
net session >nul 2>&1
if errorlevel 1 (
    echo.
    echo   Administrator huquqi so'raladi...
    for /f "usebackq delims=" %%D in (`powershell -NoProfile -Command "[Environment]::GetFolderPath('Desktop')"`) do set "LOM_ISHSTOLI=%%D"
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -ArgumentList '\"!LOM_ISHSTOLI!\"' -Verb RunAs" >nul 2>&1
    exit /b
)

set "LOM_ISHSTOLI=%~1"
if not defined LOM_ISHSTOLI (
    for /f "usebackq delims=" %%D in (`powershell -NoProfile -Command "[Environment]::GetFolderPath('Desktop')"`) do set "LOM_ISHSTOLI=%%D"
)

set "JOY=%~dp0"
if "%JOY:~-1%"=="\" set "JOY=%JOY:~0,-1%"

set "LOM_JOY=%JOY%"
set "LOM_YORLIQ1=Lombard"
set "LOM_YORLIQ2=Lombardni to'xtatish"

echo.
echo   Yorliqlar tiklanmoqda...
echo   Dastur papkasi : !LOM_JOY!
echo   Ish stoli      : !LOM_ISHSTOLI!
echo.

if not exist "%JOY%\yorliqlar.ps1" (
    echo   XATO: yorliqlar.ps1 topilmadi.
    echo   ORNATISH.bat orqali dasturni yangilang.
    echo.
    pause
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%JOY%\yorliqlar.ps1"
set "NATIJA=%ERRORLEVEL%"

echo.
if "%NATIJA%"=="0" (
    echo   Tayyor. Ish stolini bir marta yangilang ^(F5^).
) else (
    echo   Ba'zi yorliqlar yaratilmadi.
    echo   "%LOM_JOY%" papkasidagi .lnk fayllarini o'zingiz
    echo   ish stoliga ko'chirib qo'ying.
)
echo.
pause
endlocal
