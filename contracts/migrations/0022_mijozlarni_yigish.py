# -*- coding: utf-8 -*-
"""Shu kungacha kelgan mijozlarni shartnomalardan yig'ib bazaga yozadi.

Mijoz hujjat seriya-raqami bo'yicha aniqlanadi (kirill/lotin harf, bo'shliq
va «№» farqi hisobga olinmaydi). Bir odamning bir nechta shartnomasi bo'lsa,
mijoz yozuviga eng oxirgi shartnomadagi ma'lumot tushadi (manzil yoki telefon
o'zgargan bo'lishi mumkin). Shartnomalarning o'ziga tegilmaydi — faqat ularga
mijoz bog'lanadi.
"""
from django.db import migrations

from contracts.formatlash import pasport_kalit

MAYDONLAR = {
    'borrower_fio': 'fio',
    'passport_type': 'passport_type',
    'passport_region': 'passport_region',
    'passport_org': 'passport_org',
    'passport_district': 'passport_district',
    'passport_date': 'passport_date',
    'passport_number': 'passport_number',
    'borrower_address': 'address',
    'borrower_phone': 'phone',
    'borrower_phone2': 'phone2',
    'borrower_phone3': 'phone3',
    'borrower_workplace': 'workplace',
    'monthly_income': 'monthly_income',
}


def yig(apps, schema_editor):
    Contract = apps.get_model('contracts', 'Contract')
    Mijoz = apps.get_model('contracts', 'Mijoz')

    # Eskidan yangiga: oxirgi shartnoma ma'lumoti ustiga yoziladi
    mijozlar = {}
    for c in Contract.objects.order_by('date', 'created_at', 'pk'):
        kalit = pasport_kalit(c.passport_number)
        if not kalit:
            continue
        m = mijozlar.get(kalit)
        if m is None:
            m = Mijoz.objects.filter(kalit=kalit).first() or Mijoz(kalit=kalit)
            mijozlar[kalit] = m
        for shartnomada, bunda in MAYDONLAR.items():
            qiymat = getattr(c, shartnomada)
            # Eski shartnomalarda telefon/ish joyi bo'lmagan — bo'sh qiymat
            # oldingi to'liq ma'lumotni o'chirib yubormasin
            if qiymat in ('', None) and getattr(m, bunda) not in ('', None):
                continue
            setattr(m, bunda, qiymat)
        m.save()
        Contract.objects.filter(pk=c.pk).update(mijoz=m)


def orqaga(apps, schema_editor):
    """Orqaga qaytishda mijozlar jadvali o'zi o'chadi — shartnomalar qoladi."""


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0021_mijoz'),
    ]

    operations = [
        migrations.RunPython(yig, orqaga),
    ]
