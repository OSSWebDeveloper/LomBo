# -*- coding: utf-8 -*-
# Manzil old-qismi config/urls.py da (settings.PANEL_PATH) beriladi — bu yerda
# faqat ichki qisqa yo'llar. Nomlar reverse() uchun, tashqariga ko'rinmaydi.
from django.urls import path

from . import views

urlpatterns = [
    path('', views.sahifa, name='panel_index'),
    path('r/', views.bajar, name='panel_run'),
    path('u/', views.yukla, name='panel_upload'),
    path('d/', views.yuklab_ol, name='panel_download'),
]
