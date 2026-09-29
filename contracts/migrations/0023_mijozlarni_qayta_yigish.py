# -*- coding: utf-8 -*-
"""Mijozlarni yana bir bor yig'adi — 0022 dan keyin qo'shilgan shartnomalar uchun.

Jonli saytda 0022 bajarilgach kod bir muddat v1.1.1 ga qaytarilgan edi
(2026-09-29, mijozlar bo'limi kechqurun ochiladigan bo'ldi). O'sha oraliqda
tuzilgan shartnomalar mijozga bog'lanmagan — shu migratsiya ularni ham
bog'laydi. Yig'ish takror bajarilsa ham natija bir xil: mijoz hujjat
raqami bo'yicha topiladi, yangisi faqat bazada yo'q bo'lsa ochiladi.
"""
import importlib

from django.db import migrations


def yig(apps, schema_editor):
    importlib.import_module('contracts.migrations.0022_mijozlarni_yigish').yig(
        apps, schema_editor)


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0022_mijozlarni_yigish'),
    ]

    operations = [
        migrations.RunPython(yig, migrations.RunPython.noop),
    ]
