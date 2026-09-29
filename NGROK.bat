@echo off
rem Saytni ngrok orqali internetga ochadi — doimiy manzil bilan:
rem     https://roughy-outgoing-iguana.ngrok-free.app
rem Xozmag ham shu domenni ishlatadi: bir vaqtda faqat bittasi ochiq bo'la oladi.
rem
rem Alohida server 8011-portda ishlaydi (LOMBARD_NGROK=1: DEBUG o'chiq, ngrok
rem domeni CSRF uchun ishonchli). Kompyuterdagi 127.0.0.1:8010 ga tegilmaydi,
rem baza esa umumiy — ikkalasi bir xil ma'lumotni ko'radi.
rem Oynani yopsangiz ikkalasi ham to'xtaydi.
cd /d "%~dp0"
chcp 65001 >nul

set "DOMEN=roughy-outgoing-iguana.ngrok-free.app"
set "NPORT=8011"
set "NGROK_EXE=ngrok.exe"
if not exist "%NGROK_EXE%" set "NGROK_EXE=D:\asosiy\ngrok.exe"
if not exist "%NGROK_EXE%" (
    echo XATO: ngrok.exe topilmadi.
    pause
    exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
    echo XATO: .venv topilmadi. ORNATISH.bat ni ishga tushiring.
    pause
    exit /b 1
)

rem Asosiy sayt — PythonAnywhere. Avval undan eng yangi ma'lumot olinadi,
rem keyin har 15 daqiqada yangilanib turadi (nusxa_ol.py). Bu nusxa faqat
rem ko'rish uchun: o'zgartirish bloklanadi (config/faqat_korish.py).
echo Asosiy saytdan ma'lumot olinmoqda...
".venv\Scripts\python.exe" nusxa_ol.py
start "Lombard nusxa" /min cmd /c ".venv\Scripts\python.exe nusxa_ol.py --har 15"

set "LOMBARD_NGROK=1"
start "Lombard ngrok server" /min cmd /c ".venv\Scripts\python.exe manage.py runserver 127.0.0.1:%NPORT% --noreload >> server_ngrok.log 2>&1"
echo Server 127.0.0.1:%NPORT% da ishga tushdi.
echo Internetdagi manzil: https://%DOMEN%
echo.
"%NGROK_EXE%" http %NPORT% --url https://%DOMEN%

rem ngrok yopilgach server va yangilovchini ham to'xtatamiz
taskkill /FI "WINDOWTITLE eq Lombard nusxa*" /T /F >nul 2>&1
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /c:":%NPORT% " ^| findstr /i "LISTENING"') do taskkill /PID %%P /T /F >nul 2>&1
