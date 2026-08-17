# -*- coding: utf-8 -*-
"""Admin panel va sayt kirishini ajratib turadi.

Django'da sessiya bitta bo'lgani uchun admin panelga kirgan hisob avtomatik
saytga ham kirgan hisoblanadi. Bu middleware shuni to'xtatadi: saytga faqat
boshliq va ishchi rolidagi hisoblar kiradi.
"""
from django.conf import settings
from django.shortcuts import render

# Bu manzillar nazoratdan tashqarida
OCHIQ_YOLLAR = ('/admin/', '/static/', '/media/', '/kirish/', '/chiqish/')


class SaytKirishNazorati:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        foydalanuvchi = getattr(request, 'user', None)
        # Ichki xizmat — sayt rol nazoratidan chetda; manzili sozlamadan.
        ochiq = OCHIQ_YOLLAR + (f'/{settings.PANEL_PATH}',)
        if (foydalanuvchi is not None
                and foydalanuvchi.is_authenticated
                and not request.path.startswith(ochiq)
                and not foydalanuvchi.sayt_foydalanuvchisi):
            return render(request, 'faqat_admin.html', status=403)
        return self.get_response(request)
