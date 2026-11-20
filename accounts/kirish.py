# -*- coding: utf-8 -*-
"""Saytga kirish ruxsati — rol/IP cheklovi.

`KirishView` (kirish formasi) ham, `SaytKirishNazorati` middleware (har so'rov)
ham shu bitta funksiyadan foydalanadi. Shuning uchun cheklov faqat login
payti emas, OCHIQ SESSIYA bilan ichkarida qolganlarga ham qo'llanadi:
ruxsatsiz hisob har so'rovda jimgina kirish sahifasiga qaytariladi.

Foydalanuvchi talabi (2026-11-19):
  - Ishchilar saytga kira olmaydi (LOMBARD_ISHCHI_KIRISHI=1 bo'lmaguncha).
  - Boshliq faqat settings.LOMBARD_BOSS_IP ro'yxatidagi IP(lar)dan kiradi
    (ro'yxat bo'sh bo'lsa — IP cheklovi yo'q).
IP haqiqiy manzildan olinadi (proksi orqali X-Forwarded-For) — kuzatuv bilan bir xil.
"""
from django.conf import settings

from panel.kuzatuv import mijoz_ip


def kirish_ruxsati(user, request):
    """Saytga kirishga ruxsatmi. False bo'lsa kirish JIM rad etiladi."""
    if getattr(user, 'is_ishchi', False) and not getattr(settings, 'LOMBARD_ISHCHI_KIRISHI', False):
        return False
    if getattr(user, 'is_boshliq', False):
        ruxsat = getattr(settings, 'LOMBARD_BOSS_IP', []) or []
        if ruxsat and mijoz_ip(request) not in ruxsat:
            return False
    return True
