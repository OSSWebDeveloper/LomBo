# -*- coding: utf-8 -*-
"""Eski shartnomalarda mashina egasi kimligini aniqlab qo'yadi.

`egasi_turi` maydoni yangi (2026-08-25). Undan oldingi yozuvlarda egasi
«Egasi» maydoniga qanday yozilganiga qarab aniqlanadi — shunda eski
shartnomalarning hujjati avvalgidek chiqaveradi.
"""
from django.db import migrations


def _toza(ism):
    return ' '.join((ism or '').split()).casefold()


def turini_aniqla(apps, schema_editor):
    VehicleInfo = apps.get_model('contracts', 'VehicleInfo')
    for v in VehicleInfo.objects.select_related('contract'):
        if v.owner_head:
            turi = 'tashkilot'
        elif _toza(v.owner) == _toza(v.contract.borrower_fio):
            turi = 'oz'
        else:
            turi = 'shaxs'
        if v.egasi_turi != turi:
            VehicleInfo.objects.filter(pk=v.pk).update(egasi_turi=turi)


def orqaga(apps, schema_editor):
    """Maydon o'chirilganda hech narsa qilish shart emas."""


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0017_vehicleinfo_egasi_turi_vehicleinfo_owner_address_and_more'),
    ]

    operations = [
        migrations.RunPython(turini_aniqla, orqaga),
    ]
