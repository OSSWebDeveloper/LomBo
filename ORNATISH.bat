@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul 2>&1
title Lombard - avtomatik o'rnatish

rem ============================================================
rem   SOZLAMALAR - kerak bo'lsa faqat shu qatorlarni o'zgartiring
rem ============================================================
set "GITHUB=https://github.com/OSSWebDeveloper/LomBo"
set "TARMOQ=main"
set "JOY=C:\lombard"
set "PORT=8010"
rem Birinchi o'rnatishda ma'lumotlar shu saytdan ko'chirib olinadi
set "SAYT=https://mrclayd.pythonanywhere.com"
set "YORLIQ=Lombard"
set "YORLIQ2=Lombardni to'xtatish"
set "PY_YUKLASH=https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe"
rem ============================================================

rem --- Administrator huquqi tekshiriladi ---
rem Ish stoli manzili ko'tarilishdan OLDIN aniqlanib, argument sifatida
rem uzatiladi. Sababi: UAC boshqa hisob bilan ko'tarilsa, ko'tarilgan
rem jarayon uchun "ish stoli" o'sha administratorning papkasi bo'lib
rem qoladi va yorliqlar foydalanuvchiga ko'rinmay qolardi.
rem Qavsli blok emas, tekis qatorlar: shunda har bir qadamning natijasini
rem alohida tekshirish mumkin (qavs ichida errorlevel eskirib qoladi).
set "KOTARISH="
net session >nul 2>&1
if errorlevel 1 set "KOTARISH=1"

if defined KOTARISH echo.
if defined KOTARISH echo   Administrator huquqi kerak. Hozir ruxsat oynasi chiqadi -
if defined KOTARISH echo   "Ha" / "Yes" ni bosing. Shu oyna esa yopiladi.
if defined KOTARISH for /f "usebackq delims=" %%D in (`powershell -NoProfile -Command "[Environment]::GetFolderPath('Desktop')"`) do set "LOM_ISHSTOLI=%%D"
rem Oyna `cmd /c` bilan ochiladi va faqat tugmani bosgandan keyin yopiladi:
rem ish oxirida ham, xato chiqqanda ham `pause` turibdi.
rem Yo'l va ism muhit o'zgaruvchisi orqali beriladi (qo'shtirnoq bilan
rem ovora bo'lmaslik uchun), qo'shtirnoqni PowerShell [char]34 dan yasaydi.
rem Diqqat: butun satr YANA bir juft qo'shtirnoqqa olinadi - `cmd /k` birinchi
rem va oxirgi qo'shtirnoqni o'zi olib tashlaydi. Usiz papka nomida bo'shliq
rem bo'lsa yo'l yarmidan kesilib, oyna darrov yopilib ketadi.
set "LOM_BAT=%~f0"
if defined KOTARISH powershell -NoProfile -Command "$q=[char]34; $a='/c '+$q+$q+$env:LOM_BAT+$q+' '+$q+$env:LOM_ISHSTOLI+$q+$q; try { Start-Process -FilePath $env:ComSpec -ArgumentList $a -Verb RunAs -ErrorAction Stop } catch { exit 1 }"
if defined KOTARISH if not errorlevel 1 exit /b 0

rem Bu yergacha kelgan bo'lsa - ruxsat berilmadi yoki oyna ochilmadi.
if defined KOTARISH color 0C
if defined KOTARISH echo.
if defined KOTARISH echo  ============================================================
if defined KOTARISH echo   Administrator huquqi berilmadi - o'rnatib bo'lmaydi.
if defined KOTARISH echo.
if defined KOTARISH echo   Nima qilish kerak:
if defined KOTARISH echo     1^) Shu faylni O'NG tugma bilan bosing
if defined KOTARISH echo     2^) "Run as administrator" ni tanlang
if defined KOTARISH echo        ^(o'zbekcha: "Administrator nomidan ishga tushirish"^)
if defined KOTARISH echo     3^) Chiqqan ruxsat oynasida "Ha" / "Yes" ni bosing
if defined KOTARISH echo  ============================================================
if defined KOTARISH echo.
if defined KOTARISH pause
if defined KOTARISH exit /b 1

set "LOM_ISHSTOLI=%~1"
if not defined LOM_ISHSTOLI (
    for /f "usebackq delims=" %%D in (`powershell -NoProfile -Command "[Environment]::GetFolderPath('Desktop')"`) do set "LOM_ISHSTOLI=%%D"
)

cls
echo ============================================================
echo    LOMBARD - SHARTNOMA TIZIMI
echo    Avtomatik o'rnatish va yangilash
echo ============================================================
echo.
echo    Manba : %GITHUB%
echo    Joy   : %JOY%
echo    Port  : %PORT%
echo.
echo    Ma'lumotlar bazasi hech qachon o'chirilmaydi - faqat dastur
echo    fayllari yangilanadi. Garov suratlari va saytdan yuklangan
echo    shablonlar ham joyida qoladi.
echo.

set "SHUYER=%~dp0"
if "!SHUYER:~-1!"=="\" set "SHUYER=!SHUYER:~0,-1!"

rem --- O'rnatilgan papkaning O'ZIDAN ishga tushirilganmi? ---
rem Treydagi "Dasturni yangilash" aynan shunday chaqiradi. Bunda 4-bosqich
rem shu faylning ustiga yangi versiyani yozib yuborishi mumkin, cmd esa
rem ishlab turgan faylni qatorma-qator o'qiydi va adashib qoladi. Shuning
rem uchun o'zimizdan TEMP ga nusxa olamiz va davomini o'sha nusxa bajaradi
rem (administrator huquqi ham, ish stoli manzili ham o'ziga uzatiladi).
set "OZNUSXA="
if /i "!SHUYER!"=="%JOY%" set "OZNUSXA=1"
if defined OZNUSXA copy /y "%~f0" "%TEMP%\lombard_ornatish.bat" >nul 2>&1
if defined OZNUSXA if not exist "%TEMP%\lombard_ornatish.bat" set "OZNUSXA="
rem `call` siz chaqirilgan .bat boshqaruvni butunlay o'ziga oladi va shu
rem oynada davom etadi (start bo'lsa "cmd /K" bilan ikkinchi oyna ochilib,
rem ish tugagach yopilmay turib qolardi).
if defined OZNUSXA "%TEMP%\lombard_ornatish.bat" "!LOM_ISHSTOLI!"
if defined OZNUSXA exit /b 0

rem ============================================================
echo.
echo  ------------------------------------------------------------
echo   1/9   Python tekshirilmoqda
echo  ------------------------------------------------------------
rem ============================================================
set "PY="
py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1
if not errorlevel 1 set "PY=py -3"
if not defined PY (
    python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1
    if not errorlevel 1 set "PY=python"
)

if not defined PY (
    echo    Mos Python topilmadi. Yuklab olinmoqda, bir necha daqiqa ketadi...
    powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%PY_YUKLASH%' -OutFile '%TEMP%\python_setup.exe'" >nul 2>&1
    if errorlevel 1 goto :xato_internet
    echo    O'rnatilmoqda...
    "%TEMP%\python_setup.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1 Include_launcher=1
    del /q "%TEMP%\python_setup.exe" >nul 2>&1
    py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1
    if not errorlevel 1 set "PY=py -3"
)
if not defined PY goto :xato_python

!PY! -c "import sys;print(sys.version.split()[0])" > "%TEMP%\lom_pyv.txt" 2>nul
set "PYV=?"
if exist "%TEMP%\lom_pyv.txt" set /p PYV=<"%TEMP%\lom_pyv.txt"
del /q "%TEMP%\lom_pyv.txt" >nul 2>&1
echo    Python !PYV! - tayyor.

rem ============================================================
echo.
echo  ------------------------------------------------------------
echo   2/9   Ishlab turgan server to'xtatilmoqda
echo  ------------------------------------------------------------
rem ============================================================
rem Server --noreload rejimida ishlaydi: yangi fayllar faqat u qayta ishga
rem tushgandan keyin kuchga kiradi. Shu sababli avval to'xtatiladi - shunda
rem fayllar ham, ma'lumotlar bazasi ham band bo'lmaydi.
set "PORT_JORIY=%PORT%"
if exist "%JOY%\port.txt" set /p PORT_JORIY=<"%JOY%\port.txt"

set "SERVER_ISHLAGAN="
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /c:":!PORT_JORIY! " ^| findstr /i "LISTENING"') do (
    taskkill /PID %%P /T /F >nul 2>&1
    set "SERVER_ISHLAGAN=1"
)

if defined SERVER_ISHLAGAN (
    rem fayl qulflari bo'shashi uchun bir-ikki soniya kutamiz
    ping -n 3 127.0.0.1 >nul 2>&1
    echo    Server to'xtatildi - oxirida yangi versiya bilan qayta ochiladi.
) else (
    echo    Ishlab turgan server topilmadi.
)

rem ============================================================
echo.
echo  ------------------------------------------------------------
echo   3/9   Yangi nusxa yuklab olinmoqda
echo  ------------------------------------------------------------
rem ============================================================
set "ESKI_V=o'rnatilmagan"
if exist "%JOY%\versiya.txt" set /p ESKI_V=<"%JOY%\versiya.txt"

set "ZIP=%TEMP%\lombard.zip"
set "VAQT=%TEMP%\lombard_manba"
set "MANBA="
if exist "%ZIP%" del /q "%ZIP%" >nul 2>&1
if exist "%VAQT%" rd /s /q "%VAQT%" >nul 2>&1

rem GitHub fayllarni besh daqiqagacha keshda ushlab turadi. Shuning uchun
rem versiya alohida o'qilmaydi (kesh tufayli eski raqam kelib, yangilanish
rem o'tkazib yuborilar edi) - to'g'ridan-to'g'ri arxiv olinadi, manzilga
rem tasodifiy raqam qo'shilib keshdan emas, serverdan olish so'raladi.
rem
rem Ombor yopiq (private) bo'lsa yuklab bo'lmaydi - u holda shu papkadagi
rem nusxa ishlatiladi. Ya'ni fleshka yoki zip orqali tarqatish ham ishlaydi.
set "CB=%RANDOM%%RANDOM%"
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%GITHUB%/archive/refs/heads/%TARMOQ%.zip?nocache=!CB!' -Headers @{'Cache-Control'='no-cache';'Pragma'='no-cache'} -OutFile '%ZIP%'" >nul 2>&1
if not errorlevel 1 (
    powershell -NoProfile -Command "Expand-Archive -LiteralPath '%ZIP%' -DestinationPath '%VAQT%' -Force" >nul 2>&1
    for /d %%D in ("%VAQT%\*") do set "MANBA=%%D"
)

if defined MANBA (
    echo    Yuklab olindi.
) else (
    if exist "!SHUYER!\manage.py" (
        echo    Internetdan yuklab bo'lmadi - shu papkadagi nusxa ishlatiladi.
        set "MANBA=!SHUYER!"
    )
)
if not defined MANBA (
    if exist "%JOY%\manage.py" (
        echo    Internetdan yuklab bo'lmadi - o'rnatilgan nusxa saqlanib qoladi.
    ) else (
        goto :xato_internet
    )
)

set "YANGI_V=aniqlanmadi"
if defined MANBA (
    pushd "!MANBA!"
    if exist "versiya.txt" set /p YANGI_V=<versiya.txt
    popd
)

echo    Qurilmada : !ESKI_V!
echo    Yangi     : !YANGI_V!

rem ============================================================
echo.
echo  ------------------------------------------------------------
echo   4/9   Fayllar yangilanmoqda
echo  ------------------------------------------------------------
rem ============================================================
if not exist "%JOY%" mkdir "%JOY%"

rem Versiyalar teng bo'lsa ham nusxa ko'chiriladi: robocopy o'zgarmagan
rem fayllarni o'tkazib yuboradi, shu bilan "yangilandi deydi-yu, aslida
rem eski fayl qolib ketadi" degan holat butunlay yo'qoladi.
set "KOCHIR=1"
if not defined MANBA set "KOCHIR="
if defined MANBA if /i "!MANBA!"=="%JOY%" set "KOCHIR="

if not defined MANBA echo    Yangi fayllar yo'q - o'tkazib yuborildi.
if defined MANBA if /i "!MANBA!"=="%JOY%" echo    Dastur allaqachon shu papkada - ko'chirish shart emas.

if defined KOCHIR (
    if exist "%JOY%\db.sqlite3" (
        copy /y "%JOY%\db.sqlite3" "%JOY%\db_zaxira_oxirgi.sqlite3" >nul 2>&1
        echo    Bazadan zaxira olindi: db_zaxira_oxirgi.sqlite3
    )
    robocopy "!MANBA!" "%JOY%" /E /NFL /NDL /NJH /NJS /NP /XD ".venv" "__pycache__" ".git" ".claude" "staticfiles" "media" "panel_files" "zaxira" /XF "db.sqlite3" "db_zaxira_oxirgi.sqlite3" "db.sqlite3.zaxira-*" ".secret_key" "port.txt" "server.log" "ngrok.exe" >nul
    if errorlevel 8 goto :xato_nusxa
    echo    Dastur fayllari yangilandi; bazaga, garov suratlariga va
    echo    yuklangan shablonlarga tegilmadi.
)

icacls "%JOY%" /grant "*S-1-5-32-545:(OI)(CI)M" /T /C /Q >nul 2>&1
echo    Yozish huquqi berildi.

rem ============================================================
echo.
echo  ------------------------------------------------------------
echo   5/9   Kutubxonalar tekshirilmoqda
echo  ------------------------------------------------------------
rem ============================================================
if not exist "%JOY%\manage.py" goto :xato_nusxa
set "VPY=%JOY%\.venv\Scripts\python.exe"
if not exist "!VPY!" (
    echo    Virtual muhit yaratilmoqda...
    !PY! -m venv "%JOY%\.venv"
)
if not exist "!VPY!" goto :xato_venv

"!VPY!" -m pip install --upgrade pip --disable-pip-version-check -q >nul 2>&1
"!VPY!" -m pip install -r "%JOY%\requirements.txt" --disable-pip-version-check -q
if errorlevel 1 (
    "!VPY!" -c "import django, docx, docxtpl" >nul 2>&1
    if errorlevel 1 goto :xato_kutubxona
    echo    Internet yo'q, lekin kerakli kutubxonalar allaqachon o'rnatilgan.
)

"!VPY!" -c "import django;print(django.get_version())" > "%TEMP%\lom_djv.txt" 2>nul
set "DJV=?"
if exist "%TEMP%\lom_djv.txt" set /p DJV=<"%TEMP%\lom_djv.txt"
del /q "%TEMP%\lom_djv.txt" >nul 2>&1
echo    Django !DJV! - tayyor.

rem ============================================================
echo.
echo  ------------------------------------------------------------
echo   6/9   Saytdagi ma'lumotlar
echo  ------------------------------------------------------------
rem ============================================================
rem Faqat BIRINCHI o'rnatishda: kompyuterda baza bo'lmasa, saytdagi
rem shartnomalar va garov suratlari shu yerga ko'chiriladi. Login va parol
rem hech qayerda saqlanmaydi - shu oynada so'raladi va muhit o'zgaruvchisi
rem orqali skriptga uzatiladi (buyruq satrida ko'rinmasin uchun).
rem
rem Avtomatik o'rnatish kerak bo'lsa, ORNATISH.bat dan OLDIN shu ikki
rem o'zgaruvchini berib qo'ysangiz - hech narsa so'ralmaydi:
rem     set LOMBARD_SAYT_LOGIN=...
rem     set LOMBARD_SAYT_PAROL=...
set "BAZA_OL="
if not exist "%JOY%\db.sqlite3" set "BAZA_OL=1"
if not defined BAZA_OL echo    Bu kompyuterda baza bor - saytdan olish shart emas.

set "SORALSIN="
if defined BAZA_OL if not defined LOMBARD_SAYT_LOGIN set "SORALSIN=1"

if defined SORALSIN echo    Bu kompyuterda baza hali yo'q. Saytdagi ma'lumotlarni
if defined SORALSIN echo    shu yerga ko'chirib olish mumkin:
if defined SORALSIN echo        %SAYT%
if defined SORALSIN echo.
if defined SORALSIN echo    Buning uchun saytning boshqaruv (superuser) logini kerak.
if defined SORALSIN echo    Kerak bo'lmasa - Enter bosing, bo'sh bazadan boshlanadi.
if defined SORALSIN echo.
if defined SORALSIN set /p "LOMBARD_SAYT_LOGIN=   Sayt logini: "
rem Parol ekranda ko'rinmasin: PowerShell uni yulduzchasiz, yopiq o'qiydi.
rem So'rov matni Write-Host bilan chiqadi - u ekranga boradi, for /f esa
rem faqat parolning o'zini oladi.
if defined SORALSIN if defined LOMBARD_SAYT_LOGIN for /f "usebackq delims=" %%P in (`powershell -NoProfile -Command "Write-Host '   Sayt paroli: ' -NoNewline; $s = $Host.UI.ReadLineAsSecureString(); [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s))"`) do set "LOMBARD_SAYT_PAROL=%%P"

if not defined LOMBARD_SAYT_LOGIN set "BAZA_OL="
if not defined LOMBARD_SAYT_PAROL set "BAZA_OL="
if defined SORALSIN if not defined BAZA_OL echo    O'tkazib yuborildi - bo'sh bazadan boshlanadi.

if defined BAZA_OL echo.
if defined BAZA_OL "!VPY!" "%JOY%\bazani_ol.py" --manzil "%SAYT%" --nishon "%JOY%" --suratlar
if defined BAZA_OL if errorlevel 1 echo    Ma'lumot ko'chirilmadi - bo'sh bazadan davom etamiz.

rem Parol muhitda qolib ketmasin
set "LOMBARD_SAYT_PAROL="

rem ============================================================
echo.
echo  ------------------------------------------------------------
echo   7/9   Ma'lumotlar bazasi tekshirilmoqda
echo  ------------------------------------------------------------
rem ============================================================
pushd "%JOY%"
> "%JOY%\port.txt" echo %PORT%
"!VPY!" manage.py migrate --noinput
if errorlevel 1 (
    popd
    goto :xato_baza
)
rem Birinchi o'rnatishda maxfiy kalit va boshliq hisobini ochadi.
rem Hisoblar allaqachon bor bo'lsa hech nimaga tegmaydi.
"!VPY!" manage.py boshlangich
popd

rem ============================================================
echo.
echo  ------------------------------------------------------------
echo   8/9   Ish stoliga yorliqlar qo'yilmoqda
echo  ------------------------------------------------------------
rem ============================================================
rem Nomlar muhit o'zgaruvchisi orqali uzatiladi - buyruq satridagi
rem apostrof turli kompyuterlarda turlicha o'qilib ketmasligi uchun
set "LOM_JOY=%JOY%"
set "LOM_YORLIQ1=%YORLIQ%"
set "LOM_YORLIQ2=%YORLIQ2%"
powershell -NoProfile -ExecutionPolicy Bypass -File "%JOY%\yorliqlar.ps1"
if errorlevel 1 (
    echo    Ogohlantirish: yorliqlarni yaratib bo'lmadi.
    echo    "%JOY%" papkasidagi .lnk fayllarini o'zingiz ish stoliga ko'chiring
    echo    yoki "%JOY%\Yorliqlarni_tiklash.bat" faylini ishga tushiring.
) else (
    echo    Ko'rinmasa - ish stolida bir marta F5 bosing.
)

rem ============================================================
echo.
echo  ------------------------------------------------------------
echo   9/9   Hujjatlar uchun tekshiruv
echo  ------------------------------------------------------------
rem ============================================================
call :hujjatlar

if exist "%ZIP%" del /q "%ZIP%" >nul 2>&1
if exist "%VAQT%" rd /s /q "%VAQT%" >nul 2>&1

set "HOZIRGI_V=?"
if exist "%JOY%\versiya.txt" set /p HOZIRGI_V=<"%JOY%\versiya.txt"

echo.
echo ============================================================
echo    TAYYOR - o'rnatilgan versiya: !HOZIRGI_V!
echo ============================================================
echo.
echo    Ish stolida ikkita yorliq paydo bo'ldi:
echo      "%YORLIQ%"  - sayt fon rejimida ishga tushadi va Chrome'da ochiladi
echo      "%YORLIQ2%"  - ishlab turgan serverni to'xtatadi
echo.
echo    Server ishlayotganda soat yonida (treyda) belgi turadi:
echo      chap tugma - saytni ochadi, o'ng tugma - yangilash va to'xtatish.
echo    Belgi ko'rinmasa, soat yonidagi "^" strelkasini bosib, uni
echo    sichqoncha bilan panelga tortib chiqaring.
echo.
echo    Manzil         : http://127.0.0.1:%PORT%/
echo    Dastur papkasi : %JOY%
echo    Xato izlash    : %JOY%\Tekshirish.bat
echo.
echo    Birinchi o'rnatishda hisob ochiladi - login va paroli yuqorida,
echo    "7/9" bo'limida yozilgan. Saytga kirgach parolni albatta
echo    almashtiring.
echo.
echo    Yangilanish chiqqanda shu faylni yana ishga tushiring -
echo    baza saqlanib qoladi, server esa o'zi qayta ishga tushadi.
echo.

rem Explorer orqali ochamiz. Sabab: ORNATISH.bat administrator huquqi bilan
rem ishlaydi, "start" esa shu huquqni dasturga ham beradi - keyin oddiy
rem to'xtatish yorlig'i uni to'xtata olmaydi. Explorer dasturni
rem foydalanuvchining odatdagi huquqi bilan ochadi.
rem
rem Bu yerda "Ishga tushirilsinmi? [Y/N]" savoli yo'q: "choice" buyrug'i
rem bosilgan TUGMANI emas, chiqqan HARFNI tekshiradi. Klaviatura tili rus
rem yoki o'zbek kirillchasida tursa, Y tugmasi boshqa harf beradi - choice
rem uni qabul qilmay faqat ovoz chiqaradi va oyna qotib qolgandek ko'rinadi.
if defined SERVER_ISHLAGAN (
    echo    Server yangi versiya bilan qayta ishga tushirilmoqda...
) else (
    echo    Dastur ishga tushirilmoqda - Chrome o'zi ochiladi...
)
explorer.exe "%JOY%\Ishga_tushirish.vbs"

echo.
echo    Keyingi safar ochish uchun ish stolidagi "%YORLIQ%" yorlig'ini bosing.
echo    To'xtatish uchun - "%YORLIQ2%".
echo.
pause
goto :tamom


rem ============================================================
rem  Yordamchi bo'limlar
rem
rem  Diqqat: bosqich sarlavhalari shu yerda emas, o'z joyida uchta
rem  echo bilan yoziladi. Avval `call :sarlavha "..."` bor edi, lekin
rem  cmd.exe metkani fayl ichidagi joyiga qarab ba'zan topa olmaydi
rem  ("cannot find the batch label specified") - 5/8 bosqichida aynan
rem  shunday bo'ldi. Shuning uchun sarlavhaga chaqiruv ishlatilmaydi.
rem  Shu sababdan fayl butunlay ASCII: chcp 65001 bilan ko'p baytli
rem  harflar ham metka qidirishni chalg'itishi mumkin.
rem ============================================================

rem ------------------------------------------------------------
rem  Word shablonlari va PDF imkoniyati tekshiriladi.
rem  PDF uchun alohida paket kerak emas: Word hujjat LibreOffice yoki
rem  Microsoft Word orqali PDF'ga aylantiriladi. Ikkalasi ham bo'lmasa
rem  sayt ishlayveradi, faqat PDF tugmasi ko'rinmaydi.
rem
rem  Diqqat: bu bo'lim qavs ichida emas - "Program Files (x86)" dagi
rem  yopiq qavs qavs ichidagi blokni buzib yuborardi.
rem ------------------------------------------------------------
:hujjatlar
set "SHAB=0"
for /f %%N in ('dir /b "%JOY%\contracts\shablonlar\*.docx" 2^>nul ^| find /c /v ""') do set "SHAB=%%N"
if "!SHAB!"=="0" (
    echo    OGOHLANTIRISH: Word shablonlari topilmadi - hujjat yasalmaydi.
    echo    Dasturni qayta o'rnating.
) else (
    echo    Word shablonlari: !SHAB! ta - joyida.
)

set "PF86=%ProgramFiles(x86)%"
set "PDF="
if exist "%ProgramFiles%\LibreOffice\program\soffice.exe" set "PDF=LibreOffice"
if not defined PDF if exist "!PF86!\LibreOffice\program\soffice.exe" set "PDF=LibreOffice"
if not defined PDF (
    reg query "HKCR\Word.Application" >nul 2>&1
    if not errorlevel 1 set "PDF=Microsoft Word"
)

if defined PDF (
    echo    PDF: !PDF! topildi - PDF tugmasi ishlaydi.
) else (
    echo    PDF: Microsoft Word ham, LibreOffice ham topilmadi.
    echo    Sayt ishlayveradi - hujjatlar Word ^(.docx^) holida yuklanadi.
)
exit /b 0

:xato
color 0C
echo.
echo  ============================================================
echo   XATO: %~1
if not "%~2"=="" echo         %~2
echo  ============================================================
echo.
pause
exit /b 1

:xato_internet
call :xato "Dastur fayllarini olib bo'lmadi." "Internetni tekshiring - fayllar %GITHUB% dan yuklanadi. Internet bo'lmasa, ORNATISH.bat ni manage.py turgan papka ichidan ishga tushiring."
goto :tamom

:xato_python
call :xato "Python o'rnatilmadi." "python.org saytidan 3.12 yoki undan yangi versiyani qo'lda o'rnating."
goto :tamom

:xato_nusxa
call :xato "Dastur fayllari joyiga tushmadi." "%JOY% papkasini tekshiring."
goto :tamom

:xato_venv
call :xato "Virtual muhit yaratilmadi." "%JOY%\.venv papkasini o'chirib, qaytadan urinib ko'ring."
goto :tamom

:xato_kutubxona
call :xato "Kutubxonalarni o'rnatib bo'lmadi." "Internet aloqasini tekshiring."
goto :tamom

:xato_baza
call :xato "Ma'lumotlar bazasini tekshirib bo'lmadi." "Tekshirish.bat orqali batafsil xatoni ko'ring."
goto :tamom

:tamom
endlocal
exit /b 0
