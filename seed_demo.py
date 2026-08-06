# -*- coding: utf-8 -*-
"""Namuna ma'lumotlar: 1 boshliq, 2 ishchi, 3 xil shartnoma.
Ishga tushirish:  python seed_demo.py
"""
import os
from datetime import date
from decimal import Decimal

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import User                                    # noqa: E402
from contracts.docgen import add_months                             # noqa: E402
from contracts.models import (Contract, GuarantorInfo, JewelryItem,  # noqa: E402
                              VehicleInfo)


def main():
    admin, created = User.objects.get_or_create(
        username='admin', defaults={'is_superuser': True, 'is_staff': True,
                                    'role': User.ROLE_BOSHLIQ, 'first_name': 'Bosh',
                                    'last_name': 'Administrator', 'can_full_edit': True})
    if created:
        admin.set_password('admin123')
        admin.save()
        print('admin / admin123 yaratildi')

    boss, created = User.objects.get_or_create(
        username='boshliq', defaults={'role': User.ROLE_BOSHLIQ, 'is_staff': False,
                                      'first_name': 'Бахриддин', 'last_name': 'Самиев',
                                      'can_full_edit': True})
    if created:
        boss.set_password('boshliq123')
        boss.save()
        print('boshliq / boshliq123 yaratildi (to\'liq tahrirlash vakolati bor)')

    boss2, created = User.objects.get_or_create(
        username='boshliq2', defaults={'role': User.ROLE_BOSHLIQ,
                                       'first_name': 'Бобур', 'last_name': 'Хўжаев',
                                       'can_full_edit': False})
    if created:
        boss2.set_password('boshliq123')
        boss2.save()
        print('boshliq2 / boshliq123 yaratildi (vakolatsiz)')

    w1, created = User.objects.get_or_create(
        username='ishchi1', defaults={'role': User.ROLE_ISHCHI, 'added_by': boss,
                                      'first_name': 'Азиз', 'last_name': 'Каримов'})
    if created:
        w1.set_password('ishchi123')
        w1.save()
        print('ishchi1 / ishchi123 yaratildi')

    w2, created = User.objects.get_or_create(
        username='ishchi2', defaults={'role': User.ROLE_ISHCHI, 'added_by': boss,
                                      'first_name': 'Дилноза', 'last_name': 'Рахимова'})
    if created:
        w2.set_password('ishchi123')
        w2.save()
        print('ishchi2 / ishchi123 yaratildi')

    if Contract.objects.exists():
        print('Shartnomalar allaqachon mavjud, qayta yaratilmadi.')
        return

    # 1) Zargarlik (196-namuna asosida)
    c1 = Contract.objects.create(
        number=200, date=date(2025, 11, 3), collateral_type=Contract.TYPE_ZARGARLIK,
        borrower_fio='Джураева Майсара Ахмедовна',
        passport_region='Бухоро вилояти', passport_org='61013-сонли',
        passport_date=date(2025, 4, 23), passport_number='АE№2437494',
        borrower_address='Бухоро шахар, Имом Ал-Бухорий МФЙ, Тагбанбафон кўчаси, 22-уй',
        borrower_phone='91 415-00-87', monthly_income=Decimal('6000000'),
        amount=Decimal('35000000'), term_months=12, interest_rate=60,
        end_date=add_months(date(2025, 11, 3), 12),
        garov_number=200, garov_value=Decimal('43750000'), created_by=w1)
    for name, qty, wt, val in [
        ('Тилла комплект (халка узук)', 2, '21.95', 24750000),
        ('Тилла узук', 6, '12.50', 10000000),
        ('Тилла халка', 2, '3.70', 3000000),
        ('Тилла занжир', 2, '7.95', 6000000),
    ]:
        JewelryItem.objects.create(contract=c1, name=name, quantity=qty,
                                   weight=Decimal(wt), proba='585', value=Decimal(val))

    # 2) Transport (199-namuna ilovasi asosida)
    c2 = Contract.objects.create(
        number=201, date=date(2025, 11, 10), collateral_type=Contract.TYPE_TRANSPORT,
        borrower_fio='Бахшиллоева Нозима Бахтиёровна',
        passport_region='Бухоро шахар', passport_org='6206-сонли',
        passport_date=date(2021, 4, 8), passport_number='АD 0301390',
        borrower_address='Бухоро шахар, Шайхон кучаси, 156-уй',
        borrower_phone='90 220-11-33', monthly_income=Decimal('12000000'),
        amount=Decimal('50000000'), term_months=12, interest_rate=60,
        end_date=add_months(date(2025, 11, 10), 12),
        garov_number=201, garov_value=Decimal('70000000'), created_by=w1)
    VehicleInfo.objects.create(
        contract=c2, owner='“Express Alligator Bukhara” МЧЖ',
        owner_head='Бахшиллоева Дилноза Бахтиёровна',
        state_number='80 9511 АA', model='KRONE SDR27', color='QORA CHERNIY',
        body_number='-', chassis_number='WKESD000000713326', engine_number='-',
        year='2016-yil', techpassport='AAG 0949387 / 14.02.2023 йил')

    # 3) Kafillik (199-namuna asosida)
    c3 = Contract.objects.create(
        number=202, date=date(2025, 10, 31), collateral_type=Contract.TYPE_KAFILLIK,
        borrower_fio='Содиков Ботир Нусратович',
        passport_region='', passport_org='61013-сонли',
        passport_date=date(2025, 5, 20), passport_number='АE№2751664',
        borrower_address='Бухоро вилояти, Бухоро тумани, Работикалмок МФЙ, Тикончи кўчаси',
        borrower_phone='93 777-05-14', monthly_income=Decimal('4500000'),
        amount=Decimal('7000000'), term_months=12, interest_rate=60,
        end_date=add_months(date(2025, 10, 31), 12), created_by=w2)
    GuarantorInfo.objects.create(contract=c3, fio='Жураев Азизбек Носирович',
                                 amount=Decimal('10000000'))

    User.objects.filter(pk=w1.pk).update(contracts_added=2)
    User.objects.filter(pk=w2.pk).update(contracts_added=1)
    print('3 ta namuna shartnoma yaratildi:', c1.number, c2.number, c3.number)


if __name__ == '__main__':
    main()
