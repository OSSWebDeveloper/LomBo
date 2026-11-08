# -*- coding: utf-8 -*-
"""Har bir sahifaga qo'shiladigan umumiy qiymatlar.

Hozircha bittasi — dastur versiyasi (`versiya.txt`). U sahifaning pastida
ko'rinib turadi: mijoz «qaysi versiya ishlayapti?» deganda aytishi oson
bo'ladi, o'rnatuvchi ham xuddi shu raqamni solishtiradi.
"""
from django.conf import settings


def tasdiq(request):
    """Boshliq menyusidagi «Tasdiqlash» yonidagi son."""
    user = getattr(request, 'user', None)
    if not (user and user.is_authenticated and getattr(user, 'is_boshliq', False)):
        return {}
    from contracts.models import tasdiq_kutayotganlar
    return {'tasdiq_soni': tasdiq_kutayotganlar(user).count()}


def versiya(request):
    return {'versiya': getattr(settings, 'VERSIYA', ''),
            # ngrok nusxasi: sahifa tepasida «faqat ko'rish uchun» yozuvi
            'faqat_korish': getattr(settings, 'FAQAT_KORISH', False)}
