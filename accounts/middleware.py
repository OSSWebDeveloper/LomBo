# -*- coding: utf-8 -*-
"""Admin panel va sayt kirishini ajratib turadi + kirish cheklovini ta'minlaydi.

Django'da sessiya bitta bo'lgani uchun admin panelga kirgan hisob avtomatik
saytga ham kirgan hisoblanadi. Bu middleware shuni to'xtatadi: saytga faqat
boshliq va ishchi rolidagi hisoblar kiradi.

Shuningdek, kirish cheklovi (ishchi bloklangan / boshliq faqat ruxsat etilgan
IP'dan) HAR SO'ROVDA shu yerda tekshiriladi. Shu sabab cheklov qo'yilgunча ochiq
sessiya bilan ichkarida qolgan hisob ham chiqariladi: jimgina logout qilinib
kirish sahifasiga qaytariladi (hech qanday xato/xabar ko'rinmaydi, cheksiz
aylanaveradi), chunki form_valid dagi tekshiruv faqat yangi login paytida ishlaydi.
"""
from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect, render

from .kirish import kirish_ruxsati

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
                and not request.path.startswith(ochiq)):
            # 1) Rol nazorati: faqat sayt foydalanuvchilari (admin bo'lsa to'xtatiladi)
            if not foydalanuvchi.sayt_foydalanuvchisi:
                return render(request, 'faqat_admin.html', status=403)
            # 2) Kirish cheklovi: ruxsatsiz rol/IP — ochiq sessiya bo'lsa ham
            #    jimgina chiqariladi va kirish sahifasiga qaytariladi.
            if not kirish_ruxsati(foydalanuvchi, request):
                logout(request)
                return redirect('login')
        return self.get_response(request)
