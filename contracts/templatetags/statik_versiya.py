# -*- coding: utf-8 -*-
"""CSS/JS fayllari o'zgarganda brauzer keshini avtomatik yangilash.

`{% statik 'css/app.css' %}` -> `/static/css/app.css?v=1769712345`
Raqam — faylning oxirgi o'zgartirilgan vaqti. Fayl o'zgarmasa manzil ham
o'zgarmaydi, ya'ni kesh o'z ishini qilaveradi.
"""
import os

from django import template
from django.conf import settings
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def statik(yol):
    manzil = static(yol)
    papkalar = list(getattr(settings, 'STATICFILES_DIRS', []))
    if getattr(settings, 'STATIC_ROOT', None):
        papkalar.append(settings.STATIC_ROOT)
    for papka in papkalar:
        toliq = os.path.join(str(papka), *yol.split('/'))
        if os.path.exists(toliq):
            return f'{manzil}?v={int(os.path.getmtime(toliq))}'
    return manzil
