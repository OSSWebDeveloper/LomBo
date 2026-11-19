# -*- coding: utf-8 -*-
"""`stats --tarix` — qurilma kuzatuvi yoqilishidan OLDINGI kirishlar.

Manba — veb-serverning access log'lari (PythonAnywhere ularni
`/var/log/<domen>.access.log`, `.1`, `.2.gz` … ko'rinishida bir necha oy saqlaydi).
Log'da cookie yo'q, shuning uchun qurilma brauzer «oilasi» (tur · tizim ·
brauzer, versiyasiz) bo'yicha guruhlanadi: bir xil brauzerli ikki kompyuter bitta
qator bo'lib qoladi — natija «kamida N qurilma» ma'nosida, taxminiy.
"""
import glob
import gzip
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone

from .kuzatuv import ua_tahlil

QATOR = re.compile(r'^(\S+) \S+ \S+ \[([^\]]+)\] "(\S+) (\S+)[^"]*" (\d{3}) \S+ '
                   r'"[^"]*" "([^"]*)"')
# Sahifa ochilishi emas — fon so'rovlari (polling, AJAX qidiruv) va fayllar
FON = ('/static/', '/media/', '/favicon', '/tasdiq/holat/', '/xabarlar/', '/mijozlar/qidir/')
TUR_NOMI = {'kompyuter': 'Kompyuter', 'telefon': 'Telefon', 'planshet': 'Planshet'}
KENGLIK = 28


def log_fayllari(host):
    """Log fayllari ro'yxati. Sozlamada `PANEL_ACCESS_LOG` (glob) bo'lsa — o'sha."""
    andoza = getattr(settings, 'PANEL_ACCESS_LOG', '') or f'/var/log/{host}.access.log*'
    return sorted(glob.glob(andoza))


def _qatorlar(yol):
    ochuvchi = gzip.open if yol.endswith('.gz') else open
    try:
        with ochuvchi(yol, 'rt', encoding='utf-8', errors='replace') as f:
            yield from f
    except OSError:
        return


def _ustun(n, eng):
    return '█' * max(1, round(n / eng * KENGLIK)) if n and eng else ''


def hisobot(host):
    fayllar = log_fayllari(host)
    if not fayllar:
        return ("Access log topilmadi (serverda /var/log/<domen>.access.log). "
                "Bu buyruq faqat PythonAnywhere'dagi saytda ishlaydi.")

    panel = f'/{settings.PANEL_PATH}/'
    qurilma = defaultdict(lambda: {'bir': None, 'oxir': None, 'sahifa': 0,
                                   'ip': set(), 'kun': set()})
    kunlik = defaultdict(set)
    ip_hammasi = set()
    botlar = 0
    jami = 0
    for yol in fayllar:
        for q in _qatorlar(yol):
            m = QATOR.match(q)
            if not m:
                continue
            ip, vaqt, usul, manzil, kod, ua = m.groups()
            manzil = manzil.split('?')[0]
            if usul != 'GET' or int(kod) >= 400 or manzil.startswith(FON + (panel,)):
                continue
            try:
                t = timezone.localtime(datetime.strptime(vaqt, '%d/%b/%Y:%H:%M:%S %z'))
            except ValueError:
                continue
            turi, tizim, brauzer = ua_tahlil(ua)
            if turi == 'bot':
                botlar += 1
                continue
            kalit = f'{TUR_NOMI.get(turi, turi)} · {tizim} · {brauzer}'
            d = qurilma[kalit]
            d['bir'] = min(d['bir'] or t, t)
            d['oxir'] = max(d['oxir'] or t, t)
            d['sahifa'] += 1
            d['ip'].add(ip)
            d['kun'].add(t.date())
            kunlik[t.date()].add(kalit)
            ip_hammasi.add(ip)
            jami += 1

    if not qurilma:
        return "Log'da sahifa ochilishi topilmadi."

    bosh = min(d['bir'] for d in qurilma.values())
    oxir = max(d['oxir'] for d in qurilma.values())
    q = [f"OLDINGI KIRISHLAR (server log'laridan, taxminiy)   {bosh:%d.%m.%Y} — {oxir:%d.%m.%Y}",
         '─' * 60,
         f'  Turli qurilma/brauzer ........ {len(qurilma):>5}   (kamida)',
         f'  Turli IP manzil .............. {len(ip_hammasi):>5}',
         f'  Saytga kirilgan kunlar ....... {len(kunlik):>5}',
         f'  Sahifa ochilishi ............. {jami:>5}',
         f"  Bot/skript so'rovlari (hisobga olinmagan): {botlar}"]

    haftalar = defaultdict(set)
    for kun, ks in kunlik.items():
        haftalar[kun - timedelta(days=kun.weekday())] |= ks
    eng = max(len(v) for v in haftalar.values())
    q += ['', 'Haftalik faol qurilmalar (hafta boshi — dushanba)']
    h, oxirgi = min(haftalar), max(haftalar)
    while h <= oxirgi:
        n = len(haftalar.get(h, ()))
        q.append(f'  {h:%d.%m}  {_ustun(n, eng):<{KENGLIK}}  {n:>2}')
        h += timedelta(days=7)

    q += ['', 'Qurilmalar',
          f'  {"Qurilma":<34} {"Birinchi":<10} {"Oxirgi":<10} {"Kun":>4} {"Sahifa":>6} {"IP":>3}',
          '  ' + '─' * 72]
    for k, d in sorted(qurilma.items(), key=lambda x: -x[1]['sahifa']):
        q.append(f'  {k[:34]:<34} {d["bir"]:%d.%m.%Y} {d["oxir"]:%d.%m.%Y} '
                 f'{len(d["kun"]):>4} {d["sahifa"]:>6} {len(d["ip"]):>3}')
    q += ['', "Izoh: qurilma brauzer turi bo'yicha ajratiladi (log'da cookie yo'q) — "
              "bir xil brauzerli kompyuterlar bitta qator. IP provayder tomonidan "
              "o'zgarib turadi, IP soni qurilma soni emas."]
    return '\n'.join(q)
