@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul 2>&1
title Lombard - saytdagi ma'lumotlarni olish
cd /d "%~dp0"

rem ============================================================
rem   Saytdagi shartnomalar va garov suratlarini shu kompyuterga
rem   ko'chirib oladi. O'rnatish paytida bu qadam o'tkazib
rem   yuborilgan bo'lsa yoki parol noto'g'ri kiritilgan bo'lsa -
rem   qayta o'rnatmasdan shu faylni ishga tushirish kifoya.
rem ============================================================
set "SAYT=https://mrclayd.pythonanywhere.com"
set "VPY=%~dp0.venv\Scripts\python.exe"
rem Papka manzili oxiridagi teskari chiziq qo'shtirnoqni "qochiradi"
rem ("C:\lombard\" -> keyingi buyruq bo'laklari manzilga yopishib ketadi),
rem shuning uchun uni olib tashlaymiz.
set "JOY_BU=%~dp0"
if "!JOY_BU:~-1!"=="\" set "JOY_BU=!JOY_BU:~0,-1!"
set "PORT=8010"
if exist port.txt set /p PORT=<port.txt

echo.
echo ============================================================
echo    SAYTDAGI MA'LUMOTLARNI KO'CHIRIB OLISH
echo ============================================================
echo.
echo    Sayt : %SAYT%
echo    Joy  : !JOY_BU!
echo.
echo    Saytdagi baza va garov suratlari shu kompyuterga tushadi.
echo    Hozirgi baza o'chmaydi - zaxira nusxasi saqlanadi.
echo.

if not exist "!VPY!" echo    XATO: .venv topilmadi - avval ORNATISH.bat ni ishga tushiring.
if not exist "!VPY!" echo.
if not exist "!VPY!" pause
if not exist "!VPY!" exit /b 1

rem --- Login va parol (hech qayerda saqlanmaydi) ---
rem Oldindan berilgan bo'lsa (set LOMBARD_SAYT_LOGIN=...) so'ralmaydi.
if not defined LOMBARD_SAYT_LOGIN echo    Saytning boshqaruv (superuser) logini kerak.
if not defined LOMBARD_SAYT_LOGIN echo    Bekor qilish uchun - Enter.
if not defined LOMBARD_SAYT_LOGIN echo.
if not defined LOMBARD_SAYT_LOGIN set /p "LOMBARD_SAYT_LOGIN=   Sayt logini: "

rem Parol ekranda ko'rinmaydi: PowerShell uni yopiq o'qiydi, so'rov matni
rem Write-Host bilan ekranga chiqadi (for /f faqat parolning o'zini oladi).
if not defined LOMBARD_SAYT_PAROL if defined LOMBARD_SAYT_LOGIN for /f "usebackq delims=" %%P in (`powershell -NoProfile -Command "Write-Host '   Sayt paroli: ' -NoNewline; $s = $Host.UI.ReadLineAsSecureString(); [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s))"`) do set "LOMBARD_SAYT_PAROL=%%P"
echo.

set "DAVOM=1"
if not defined LOMBARD_SAYT_LOGIN set "DAVOM="
if not defined LOMBARD_SAYT_PAROL set "DAVOM="

if not defined DAVOM echo    Bekor qilindi - hech narsa o'zgarmadi.
if not defined DAVOM echo.
if not defined DAVOM pause
if not defined DAVOM exit /b 0

rem --- Server to'xtatiladi: baza fayli band bo'lmasligi kerak ---
set "SERVER_ISHLAGAN="
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /c:":!PORT! " ^| findstr /i "LISTENING"') do (
    taskkill /PID %%P /T /F >nul 2>&1
    set "SERVER_ISHLAGAN=1"
)
if defined SERVER_ISHLAGAN ping -n 3 127.0.0.1 >nul 2>&1
if defined SERVER_ISHLAGAN echo    Server vaqtincha to'xtatildi.

rem --- Eski bazadan zaxira ---
if exist db.sqlite3 copy /y db.sqlite3 "db_zaxira_oxirgi.sqlite3" >nul 2>&1
if exist db.sqlite3 echo    Eski baza saqlandi: db_zaxira_oxirgi.sqlite3
echo.

"!VPY!" "%~dp0bazani_ol.py" --manzil "%SAYT%" --nishon "!JOY_BU!" --suratlar --majburiy
set "NATIJA=%ERRORLEVEL%"
set "LOMBARD_SAYT_PAROL="

if not "%NATIJA%"=="0" echo.
if not "%NATIJA%"=="0" echo    Ma'lumot ko'chirilmadi. Eski baza joyida qoldi.
if not "%NATIJA%"=="0" echo.
if not "%NATIJA%"=="0" pause
if not "%NATIJA%"=="0" exit /b 1

rem --- Saytdagi baza eskiroq bo'lsa, yetishmagan jadvallar qo'shiladi ---
echo.
echo    Baza tekshirilmoqda...
"!VPY!" manage.py migrate --noinput

echo.
echo ============================================================
echo    TAYYOR - saytdagi ma'lumotlar shu kompyuterda.
echo ============================================================
echo.
echo    Endi saytga O'ZINGIZNING sayt logini va paroli bilan
echo    kirasiz (mahalliy "boshliq" hisobi o'rniga).
echo.

if defined SERVER_ISHLAGAN echo    Server qayta ishga tushirilmoqda...
if defined SERVER_ISHLAGAN explorer.exe "%~dp0Ishga_tushirish.vbs"
if not defined SERVER_ISHLAGAN echo    Saytni ochish uchun ish stolidagi "Lombard" yorlig'ini bosing.
echo.
pause
endlocal
exit /b 0
