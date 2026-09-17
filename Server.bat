@echo off
rem Serverni fon rejimida ishga tushiradi. Ishga_tushirish.vbs shuni chaqiradi.
rem Bevosita ishga tushirilsa ham ishlaydi - oyna ochiq qoladi.
rem Sayt faqat shu kompyuterda ochiladi (127.0.0.1) - tarmoqqa chiqmaydi.
cd /d "%~dp0"

set "PORT=8010"
if exist port.txt set /p PORT=<port.txt

if not exist ".venv\Scripts\python.exe" (
    echo XATO: .venv topilmadi. ORNATISH.bat ni qayta ishga tushiring.>> "server.log"
    exit /b 1
)

echo.>> "server.log"
echo ===== %DATE% %TIME% - server ishga tushmoqda, 127.0.0.1:%PORT% =====>> "server.log"
".venv\Scripts\python.exe" manage.py runserver 127.0.0.1:%PORT% --noreload >> "server.log" 2>&1
