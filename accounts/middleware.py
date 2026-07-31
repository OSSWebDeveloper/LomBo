# -*- coding: utf-8 -*-
"""Admin panel va sayt kirishini ajratib turadi.

Django'da sessiya bitta bo'lgani uchun admin panelga kirgan hisob avtomatik
saytga ham kirgan hisoblanadi. Bu middleware shuni to'xtatadi: saytga faqat
boshliq va ishchi rolidagi hisoblar kiradi.
"""
from django.shortcuts import render

# Bu manzillar nazoratdan tashqarida
OCHIQ_YOLLAR = ('/admin/', '/static/', '/media/', '/kirish/', '/chiqish/')


class SaytKirishNazorati:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        foydalanuvchi = getattr(request, 'user', None)
        if (foydalanuvchi is not None
                and foydalanuvchi.is_authenticated
                and not request.path.startswith(OCHIQ_YOLLAR)
                and not foydalanuvchi.sayt_foydalanuvchisi):
            return render(request, 'faqat_admin.html', status=403)
        return self.get_response(request)
