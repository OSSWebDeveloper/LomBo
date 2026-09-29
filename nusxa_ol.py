# -*- coding: utf-8 -*-
"""ngrok nusxasi uchun: asosiy saytdagi (PythonAnywhere) bazani va garov
suratlarini shu kompyuterga oladi.

    python nusxa_ol.py            bir marta
    python nusxa_ol.py --har 15   har 15 daqiqada (NGROK.bat shunday ishlatadi)

Asosiy sayt — PA (2026-09-29). Bu nusxa faqat ko'rish uchun (LOMBARD_NGROK=1
da o'zgartirish bloklanadi), shuning uchun bazani ustidan yozish xavfsiz.
Baza SQLite'ning backup usuli bilan almashtiriladi — server ishlab turganda
ham fayl buzilmaydi. Kelgan fayl avval tekshiriladi; yaroqsiz bo'lsa
hozirgi baza o'zgarmaydi.

Token: PA_API_TOKEN muhit o'zgaruvchisi yoki `D:\\lambard\\.pa_token`
(yoki shu papkadan bir yuqoridagi `.pa_token`). Faqat kutubxonasiz —
`.venv` da `requests` yo'q.
"""
import argparse
import datetime
import json
import os
import sqlite3
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

ILDIZ = Path(__file__).resolve().parent
USER = 'MRClayd'
API = f'https://www.pythonanywhere.com/api/v0/user/{USER}/files'
UZOQ = f'/home/{USER}/lombard_site'
LOG = ILDIZ / 'nusxa_ol.log'


def yoz(*q):
    qator = f'[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] ' + ' '.join(map(str, q))
    print(qator, flush=True)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(qator + '\n')


def token():
    t = os.environ.get('PA_API_TOKEN', '').strip()
    if t:
        return t
    for yol in (ILDIZ.parent / '.pa_token', Path(r'D:\lambard\.pa_token')):
        if yol.exists():
            return yol.read_text(encoding='utf-8').strip()
    raise SystemExit('PA tokeni topilmadi (PA_API_TOKEN yoki .pa_token).')


def ol(yol, tok):
    url = API + '/path' + urllib.parse.quote(yol)
    so = urllib.request.Request(url, headers={'Authorization': f'Token {tok}'})
    with urllib.request.urlopen(so, timeout=120) as j:
        return j.read()


def bazani_ol(tok):
    baytlar = ol(f'{UZOQ}/db.sqlite3', tok)
    with tempfile.NamedTemporaryFile(suffix='.sqlite3', delete=False) as f:
        f.write(baytlar)
        vaqt = f.name
    try:
        manba = sqlite3.connect(vaqt)
        if manba.execute('pragma integrity_check').fetchone()[0] != 'ok':
            raise ValueError('kelgan baza buzilgan')
        soni = manba.execute('select count(*) from contracts_contract').fetchone()[0]
        nishon = sqlite3.connect(ILDIZ / 'db.sqlite3', timeout=30)
        manba.backup(nishon)            # ishlab turgan server uchun xavfsiz
        nishon.close()
        manba.close()
        return soni
    finally:
        os.unlink(vaqt)


def suratlarni_ol(tok, papka=f'{UZOQ}/media/'):
    """Yo'q fayllarni oladi (garov suratlari o'zgarmaydi — nomi yangi bo'ladi)."""
    royxat = json.loads(ol(papka, tok))
    soni = 0
    for nom, info in royxat.items():
        yol = papka.rstrip('/') + '/' + nom
        if info.get('type') == 'directory':
            soni += suratlarni_ol(tok, yol + '/')
            continue
        joy = ILDIZ / yol[len(UZOQ) + 1:]
        if not joy.exists():
            joy.parent.mkdir(parents=True, exist_ok=True)
            joy.write_bytes(ol(yol, tok))
            soni += 1
    return soni


def bir_marta(tok):
    try:
        soni = bazani_ol(tok)
        yangi = suratlarni_ol(tok)
        yoz(f'Yangilandi: {soni} shartnoma, {yangi} ta yangi surat.')
        return True
    except Exception as e:                   # tarmoq uzilsa — keyingi safar
        yoz('Yangilanmadi:', repr(e))
        return False


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--har', type=int, default=0, help='Har necha daqiqada (0 — bir marta)')
    a = p.parse_args()
    tok = token()
    ok = bir_marta(tok)
    while a.har > 0:
        time.sleep(a.har * 60)
        bir_marta(tok)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
