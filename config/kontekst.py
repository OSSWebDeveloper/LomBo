# -*- coding: utf-8 -*-
"""Har bir sahifaga qo'shiladigan umumiy qiymatlar.

Hozircha bittasi — dastur versiyasi (`versiya.txt`). U sahifaning pastida
ko'rinib turadi: mijoz «qaysi versiya ishlayapti?» deganda aytishi oson
bo'ladi, o'rnatuvchi ham xuddi shu raqamni solishtiradi.
"""
from django.conf import settings


def versiya(request):
    return {'versiya': getattr(settings, 'VERSIYA', '')}
