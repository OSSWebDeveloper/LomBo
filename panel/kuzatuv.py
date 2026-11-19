# -*- coding: utf-8 -*-
"""Saytga kirgan qurilmalarni sanaydigan middleware.

Har bir sahifa ochilishi (brauzer manzil satri/havola orqali GET) qurilmaga
yoziladi. Statik fayllar, media, ichki panel, AJAX/fetch so'rovlari (masalan
/tasdiq/ dagi 30 soniyalik polling) sanalmaydi — aks holda raqamlar shishib
ketardi. Kuzatuvdagi har qanday xato saytni to'xtatmaydi: faqat jurnalga
yoziladi.
"""
import hashlib
import logging
import re
import uuid

from django.conf import settings
from django.db.models import F
from django.utils import timezone

logger = logging.getLogger('panel')

COOKIE = 'lq'
COOKIE_MUDDAT = 2 * 365 * 24 * 3600          # 2 yil

_BOT = re.compile(r'bot|crawl|spider|slurp|curl|wget|python|httpx|go-http|java/|'
                  r'headless|preview|facebookexternalhit|scan|monitor|uptime', re.I)


def ua_tahlil(ua):
    """User-Agent -> (turi, tizim, brauzer). Tashqi kutubxonasiz, taxminiy."""
    ua = ua or ''
    if not ua.strip() or _BOT.search(ua):
        return 'bot', '', ''

    if 'iPad' in ua or 'Tablet' in ua or ('Android' in ua and 'Mobile' not in ua):
        turi = 'planshet'
    elif 'Mobi' in ua or 'iPhone' in ua or 'Android' in ua:
        turi = 'telefon'
    else:
        turi = 'kompyuter'

    if 'Windows' in ua:
        tizim = 'Windows'
    elif m := re.search(r'Android (\d+)', ua):
        tizim = f'Android {m.group(1)}'
    elif m := re.search(r'(?:iPhone|CPU) OS (\d+)', ua):
        tizim = f'iOS {m.group(1)}'
    elif 'CrOS' in ua:
        tizim = 'ChromeOS'
    elif 'Mac OS X' in ua or 'Macintosh' in ua:
        tizim = 'macOS'
    elif 'Linux' in ua:
        tizim = 'Linux'
    else:
        tizim = 'Boshqa'

    for belgi, nom in (('YaBrowser', 'Yandex'), ('Edg', 'Edge'), ('OPR/', 'Opera'),
                       ('Opera', 'Opera'), ('SamsungBrowser', 'Samsung'),
                       ('Firefox', 'Firefox'), ('FxiOS', 'Firefox'),
                       ('CriOS', 'Chrome'), ('Chrome', 'Chrome'), ('Safari', 'Safari')):
        if belgi in ua:
            brauzer = nom
            break
    else:
        brauzer = 'Boshqa'
    return turi, tizim, brauzer


def mijoz_ip(request):
    """Haqiqiy IP: PythonAnywhere va ngrok proksi orqali X-Forwarded-For beradi."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if xff:
        return xff.split(',')[0].strip()[:45]
    return request.META.get('HTTP_X_REAL_IP') or request.META.get('REMOTE_ADDR', '')


def _sanaladimi(request, javob):
    if request.method != 'GET' or javob.status_code >= 400:
        return False
    yol = request.path
    chetda = ('/static/', '/media/', '/favicon', f'/{settings.PANEL_PATH}/')
    if yol.startswith(chetda):
        return False
    # fetch()/XHR va rasm/skript so'rovlari — sahifa ochilishi emas
    if request.headers.get('X-Requested-With'):
        return False
    manzil = request.headers.get('Sec-Fetch-Dest', '')
    if manzil and manzil not in ('document', 'iframe'):
        return False
    return True


class QurilmaKuzatuvi:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        javob = self.get_response(request)
        if not _sanaladimi(request, javob):
            return javob
        try:
            kalit = self._yoz(request)
        except Exception:                           # sayt ishlashi muhimroq
            logger.exception('Qurilma kuzatuvi xatosi')
            return javob
        if kalit and request.COOKIES.get(COOKIE) != kalit:
            javob.set_cookie(COOKIE, kalit, max_age=COOKIE_MUDDAT,
                             httponly=True, samesite='Lax',
                             secure=request.is_secure())
        return javob

    def _yoz(self, request):
        from .models import Qurilma, QurilmaKun

        ua = request.META.get('HTTP_USER_AGENT', '')[:300]
        ip = mijoz_ip(request)
        turi, tizim, brauzer = ua_tahlil(ua)

        kalit = request.COOKIES.get(COOKIE, '')
        if not re.fullmatch(r'[0-9a-f]{32}', kalit):
            # Bot cookie saqlamaydi — har so'rovda yangi qurilma bo'lib ketmasligi
            # uchun IP+UA dan doimiy kalit. Odamlarga — tasodifiy kalit (bir
            # ofisdagi bir xil kompyuterlar bitta bo'lib qolmasin).
            if turi == 'bot':
                kalit = hashlib.sha256(f'{ip}|{ua}'.encode()).hexdigest()[:32]
            else:
                kalit = uuid.uuid4().hex

        endi = timezone.now()
        user = getattr(request, 'user', None)
        hisob = user.get_username() if user is not None and user.is_authenticated else ''

        q, yangi = Qurilma.objects.get_or_create(kalit=kalit, defaults={
            'turi': turi, 'tizim': tizim, 'brauzer': brauzer, 'user_agent': ua,
            'ip': ip, 'foydalanuvchi': hisob, 'birinchi': endi, 'oxirgi': endi,
            'sorov_soni': 1})
        if not yangi:
            ozgar = {'oxirgi': endi, 'ip': ip, 'sorov_soni': F('sorov_soni') + 1,
                     'turi': turi, 'tizim': tizim, 'brauzer': brauzer, 'user_agent': ua}
            if hisob:
                ozgar['foydalanuvchi'] = hisob
            Qurilma.objects.filter(pk=q.pk).update(**ozgar)

        sana = timezone.localdate(endi)
        if not QurilmaKun.objects.filter(qurilma=q, sana=sana).update(
                sorov_soni=F('sorov_soni') + 1):
            QurilmaKun.objects.get_or_create(qurilma=q, sana=sana,
                                             defaults={'sorov_soni': 1})
        return kalit
