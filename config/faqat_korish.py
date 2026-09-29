# -*- coding: utf-8 -*-
"""ngrok nusxasi — faqat ko'rish uchun (foydalanuvchi qarori, 2026-09-29).

Asosiy sayt PythonAnywhere'da. Bu kompyuterdagi nusxa ma'lumotni undan
oladi (`nusxa_ol.py`) va har yangilanishda bazasi ustiga yoziladi — shu
yerda kiritilgan narsa yo'qolib ketardi. Shuning uchun o'zgartiradigan
so'rovlar (POST) bloklanadi; kirish/chiqish bundan mustasno.
"""
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse

ASOSIY_SAYT = 'https://mrclayd.pythonanywhere.com/'
XABAR = ("Bu nusxa faqat ko'rish uchun — o'zgarish saqlanmadi. "
         "Shartnoma asosiy saytda kiritiladi: " + ASOSIY_SAYT)


class FaqatKorish:
    def __init__(self, get_response):
        self.get_response = get_response
        self.ruxsat = {reverse('login'), reverse('logout')}

    def __call__(self, request):
        if (getattr(settings, 'FAQAT_KORISH', False)
                and request.method not in ('GET', 'HEAD', 'OPTIONS')
                and request.path not in self.ruxsat):
            messages.error(request, XABAR)
            return redirect(request.META.get('HTTP_REFERER') or '/')
        return self.get_response(request)
