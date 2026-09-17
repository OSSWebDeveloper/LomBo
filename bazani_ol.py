# -*- coding: utf-8 -*-
"""Saytdagi ma'lumotlarni shu kompyuterga ko'chirib oladi.

ORNATISH.bat buni faqat BIRINCHI o'rnatishda — kompyuterda baza hali
yo'q bo'lganda — chaqiradi:

    python bazani_ol.py --manzil https://mrclayd.pythonanywhere.com \\
                        --nishon C:\\lombard --suratlar

Login va parol buyruq satrida emas, muhit o'zgaruvchilarida keladi
(`LOMBARD_SAYT_LOGIN`, `LOMBARD_SAYT_PAROL`) — shunda parol jarayonlar
ro'yxatida ko'rinib qolmaydi.

Ma'lumot saytning ichki paneli orqali olinadi (`panel/views.py`): avval
`login`, so'ng `d/?file=db.sqlite3`. Panelga faqat superuser kira oladi,
ya'ni bu yerda saytdagidan ortiq huquq berilmaydi.

Tashqi kutubxona kerak emas — hammasi standart Python bilan.
"""
import argparse
import http.cookiejar
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

PANEL_STANDART = 'ic-9f4k2m'
SQLITE_BELGISI = b'SQLite format 3\x00'
KUTISH = 60                      # soniya
BOLAK = 256 * 1024               # o'qish bo'lagi


class Xato(Exception):
    """Foydalanuvchiga ko'rsatiladigan tushunarli xato."""


# --------------------------------------------------------------- aloqa

def ulanish():
    """Cookie saqlaydigan ochuvchi — panel sessiyasi shu orqali ushlanadi."""
    jar = http.cookiejar.CookieJar()
    ochuvchi = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    ochuvchi.addheaders = [('User-Agent', 'lombard-ornatuvchi/1.0')]
    return ochuvchi


def csrf_token(html):
    """Panel sahifasidagi yashirin csrf maydonini oladi."""
    moslik = re.search(r'name=["\']csrfmiddlewaretoken["\']\s+value=["\']([^"\']+)', html)
    return moslik.group(1) if moslik else ''


def kir(ochuvchi, panel_url, login, parol):
    """Panelga kiradi. Muvaffaqiyatsiz bo'lsa — Xato."""
    try:
        with ochuvchi.open(panel_url, timeout=KUTISH) as javob:
            html = javob.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as x:
        raise Xato('Sayt panelini ochib bo\'lmadi (%s). Manzilni tekshiring.' % x.code)
    except OSError as x:
        raise Xato('Saytga ulanib bo\'lmadi: %s' % x)

    token = csrf_token(html)
    if not token:
        raise Xato('Sayt panelidan xavfsizlik kaliti olinmadi — manzil to\'g\'rimi?')

    # Panel buyruqni shlex bilan bo'laklarga ajratadi: parolda bo'shliq yoki
    # tirnoq bo'lsa ham bitta bo'lak bo'lib qolishi uchun tirnoqqa olamiz.
    buyruq = 'login --username %s --password %s' % (tirnoqla(login), tirnoqla(parol))

    malumot = urllib.parse.urlencode({'command': buyruq}).encode()
    soorov = urllib.request.Request(panel_url + 'r/', data=malumot, headers={
        'X-CSRFToken': token,
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': panel_url,
    })
    try:
        with ochuvchi.open(soorov, timeout=KUTISH) as javob:
            natija = json.loads(javob.read().decode('utf-8', 'replace'))
    except (urllib.error.HTTPError, OSError, ValueError) as x:
        raise Xato('Panelga kirishda xatolik: %s' % x)

    if not natija.get('user'):
        raise Xato(natija.get('output') or 'Login yoki parol noto\'g\'ri.')
    return natija['user']


def tirnoqla(matn):
    """shlex uchun: bo'shliq yoki tirnoq bo'lsa ham bir bo'lak bo'lib qolsin."""
    return "'" + matn.replace("'", "'\\''") + "'"


def yuklab_ol(ochuvchi, url, nishon_fayl, nomi):
    """Faylni oqim bilan yuklaydi (katta fayl xotiraga sig'masligi mumkin)."""
    try:
        with ochuvchi.open(url, timeout=KUTISH) as javob:
            jami = 0
            keyingi_belgi = 2 * 1024 * 1024
            with open(nishon_fayl, 'wb') as f:
                while True:
                    bolak = javob.read(BOLAK)
                    if not bolak:
                        break
                    f.write(bolak)
                    jami += len(bolak)
                    if jami >= keyingi_belgi:
                        print('       ... %s' % hajm(jami), flush=True)
                        keyingi_belgi += 2 * 1024 * 1024
    except urllib.error.HTTPError as x:
        if x.code == 404:
            raise Xato('%s saytda topilmadi.' % nomi)
        raise Xato('%s yuklanmadi (%s).' % (nomi, x.code))
    except OSError as x:
        raise Xato('%s yuklanmadi: %s' % (nomi, x))
    return jami


def hajm(baytlar):
    """1536 -> «1.5 KB» (panel bilan bir xil ko'rinish)."""
    okean = float(baytlar)
    for birlik in ('B', 'KB', 'MB', 'GB'):
        if okean < 1024:
            return '%.0f %s' % (okean, birlik) if birlik == 'B' else '%.1f %s' % (okean, birlik)
        okean /= 1024
    return '%.1f TB' % okean


# --------------------------------------------------------------- baza

def baza_tekshir(fayl):
    """Kelgan fayl haqiqiy SQLite bazami? Shartnomalar sonini qaytaradi.

    Sessiya tugab qolsa panel HTML sahifa qaytarishi mumkin — shu tekshiruv
    aynan shunday "baza"ni joyiga qo'yib yuborishning oldini oladi.
    """
    with open(fayl, 'rb') as f:
        if f.read(16) != SQLITE_BELGISI:
            raise Xato('Saytdan kelgan fayl ma\'lumotlar bazasi emas.')

    ulanma = sqlite3.connect('file:%s?mode=ro' % fayl.as_posix(), uri=True)
    try:
        jadvallar = {q[0] for q in ulanma.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        if 'contracts_contract' not in jadvallar:
            raise Xato('Bazada shartnomalar jadvali yo\'q — noto\'g\'ri fayl kelgan.')
        return ulanma.execute('SELECT COUNT(*) FROM contracts_contract').fetchone()[0]
    except sqlite3.DatabaseError as x:
        raise Xato('Baza o\'qilmadi: %s' % x)
    finally:
        ulanma.close()


# --------------------------------------------------------------- suratlar

def xavfsiz_chiqar(zip_fayl, nishon_papka):
    """Zip'ni papkaga ochadi; papkadan tashqariga chiqadigan yo'llar tashlanadi."""
    nishon_papka.mkdir(parents=True, exist_ok=True)
    ildiz = nishon_papka.resolve()
    soni = 0
    with zipfile.ZipFile(zip_fayl) as z:
        for yozuv in z.infolist():
            if yozuv.is_dir():
                continue
            nom = yozuv.filename.replace('\\', '/')
            if nom.startswith('/') or '..' in nom.split('/'):
                continue                      # yo'l chetga chiqmoqchi — tashlaymiz
            manzil = (ildiz / nom).resolve()
            try:
                manzil.relative_to(ildiz)
            except ValueError:
                continue
            manzil.parent.mkdir(parents=True, exist_ok=True)
            with z.open(yozuv) as manba, open(manzil, 'wb') as f:
                while True:
                    bolak = manba.read(BOLAK)
                    if not bolak:
                        break
                    f.write(bolak)
            soni += 1
    return soni


# --------------------------------------------------------------- asosiy ish

def ishla(manzil, nishon, panel, suratlar_ham, majburiy):
    ochuvchi = ulanish()
    manzil = manzil.rstrip('/')
    panel_url = '%s/%s/' % (manzil, panel.strip('/'))
    nishon = Path(nishon).resolve()
    baza_fayl = nishon / 'db.sqlite3'

    if baza_fayl.exists() and not majburiy:
        raise Xato('Bu kompyuterda baza allaqachon bor — ustiga yozilmadi.')

    login = os.environ.get('LOMBARD_SAYT_LOGIN', '').strip()
    parol = os.environ.get('LOMBARD_SAYT_PAROL', '')
    if not login or not parol:
        raise Xato('Login yoki parol berilmadi.')

    print('   Saytga ulanilmoqda: %s' % manzil, flush=True)
    kim = kir(ochuvchi, panel_url, login, parol)
    print('   Kirildi: %s' % kim, flush=True)

    # Avval vaqtinchalik faylga — yarim yuklangan baza joyiga tushmasin
    vaqtinchalik = Path(tempfile.mkdtemp(prefix='lombard-baza-'))
    try:
        xom = vaqtinchalik / 'db.sqlite3'
        print('   Baza yuklanmoqda...', flush=True)
        olingan = yuklab_ol(ochuvchi, panel_url + 'd/?file=db.sqlite3',
                            xom, 'Ma\'lumotlar bazasi')
        soni = baza_tekshir(xom)
        nishon.mkdir(parents=True, exist_ok=True)
        if baza_fayl.exists():
            baza_fayl.unlink()
        xom.replace(baza_fayl)
        print('   Baza ko\'chirildi: %s, %d ta shartnoma.' % (hajm(olingan), soni),
              flush=True)

        if suratlar_ham:
            suratlarni_ol(ochuvchi, panel_url, nishon, vaqtinchalik)
    finally:
        tozala(vaqtinchalik)
    return 0


def suratlarni_ol(ochuvchi, panel_url, nishon, vaqtinchalik):
    """Garov suratlari (media papkasi) — bo'lmasa ish to'xtamaydi."""
    zip_fayl = vaqtinchalik / 'media.zip'
    print('   Suratlar yuklanmoqda...', flush=True)
    try:
        olingan = yuklab_ol(ochuvchi, panel_url + 'd/?all=1&dir=media',
                            zip_fayl, 'Suratlar')
    except Xato as x:
        print('   Suratlar olinmadi: %s' % x)
        print('   Shartnomalar to\'liq ishlaydi, faqat surat ko\'rinmaydi.')
        return
    try:
        soni = xavfsiz_chiqar(zip_fayl, nishon / 'media')
    except (zipfile.BadZipFile, OSError) as x:
        print('   Suratlar ochilmadi: %s' % x)
        return
    print('   Suratlar ko\'chirildi: %d ta fayl (%s).' % (soni, hajm(olingan)))


def tozala(papka):
    shutil.rmtree(papka, ignore_errors=True)



def main(argv=None):
    p = argparse.ArgumentParser(
        description='Saytdagi ma\'lumotlarni shu kompyuterga ko\'chirib oladi.')
    p.add_argument('--manzil', required=True, help='Sayt manzili (https://...)')
    p.add_argument('--nishon', default=str(Path(__file__).resolve().parent),
                   help='Dastur papkasi (db.sqlite3 shu yerga tushadi)')
    p.add_argument('--panel', default=os.environ.get('LOMBARD_PANEL_PATH', PANEL_STANDART),
                   help='Ichki panel manzili')
    p.add_argument('--suratlar', action='store_true', help='Garov suratlari ham olinsin')
    p.add_argument('--majburiy', action='store_true',
                   help='Mavjud bazaning ustiga yozilsin (ehtiyot bo\'ling)')
    a = p.parse_args(argv)

    try:
        return ishla(a.manzil, a.nishon, a.panel, a.suratlar, a.majburiy)
    except Xato as x:
        print('   XATO: %s' % x)
        return 1
    except KeyboardInterrupt:
        print('   To\'xtatildi.')
        return 1
    except OSError as x:
        # Masalan papka manzili noto'g'ri yoki diskda joy qolmagan —
        # foydalanuvchiga uzun traceback emas, bitta qator ko'rinsin.
        print('   XATO: %s' % x)
        return 1


if __name__ == '__main__':
    sys.exit(main())
