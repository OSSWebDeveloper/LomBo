# -*- coding: utf-8 -*-
"""Kiritilgan ma'lumotlarni bir xil ko'rinishga keltirish.

Hujjat seriya-raqami turlicha yozilishi mumkin:
    ae5862145 · AE 5862145 · АЕ№5862145 · ae-5862145
Hammasi bitta ko'rinishga keltiriladi:  AE№5862145

Pul summasi esa har uch raqamdan keyin bo'shliq bilan ko'rsatiladi:
    7000000 -> 7 000 000
"""
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

# Kirill va lotin harflari ko'rinishda bir xil, lekin kod jihatdan boshqa.
# Asl shartnomalarda ular aralash yozilgan (kirill «А» + lotin «E»), bu esa
# keyinchalik qidiruvni buzadi. Shuning uchun hammasi lotinga keltiriladi.
KIRILL_LOTIN = str.maketrans({
    'А': 'A', 'В': 'B', 'Е': 'E', 'К': 'K', 'М': 'M', 'Н': 'H',
    'О': 'O', 'Р': 'P', 'С': 'C', 'Т': 'T', 'У': 'Y', 'Х': 'X',
})

AJRATGICH = re.compile(r'[\s\-–—_№]+')
TOLIQ = re.compile(r'^([A-Z]{1,3})(\d{5,9})$')
QISMAN = re.compile(r'^([A-Z]{1,3})(\d{0,9})$')


def hujjat_raqami(qiymat: str) -> str:
    """Seriya va raqamni ajratib, «AE№5862145» ko'rinishiga keltiradi.

    Tanish bo'lmagan format (masalan tug'ilganlik guvohnomasi) o'zgartirilmaydi —
    faqat ortiqcha bo'shliqlar olib tashlanadi.
    """
    if not qiymat:
        return qiymat

    asl = qiymat.strip()
    tozalangan = AJRATGICH.sub('', asl).upper().translate(KIRILL_LOTIN)

    m = TOLIQ.match(tozalangan)
    if m:
        return f'{m.group(1)}№{m.group(2)}'

    # Yarim kiritilgan holat: «AE» yoki «AE5» — seriya baribir ajratiladi
    m = QISMAN.match(tozalangan)
    if m:
        return f'{m.group(1)}№{m.group(2)}' if m.group(2) else m.group(1)

    return asl


# --------------------------------------------------------------- pul summasi

# Foydalanuvchi ham, brauzer ham turli bo'shliqlarni yozib qo'yishi mumkin:
# oddiy, uzilmas (NBSP), ingichka. Hammasi son sifatida e'tiborsiz qoldiriladi.
BOSHLIQLAR = ' \u00a0\u202f\u2009\u2007'


def pul_son(qiymat):
    """«7 000 000» -> «7000000». Matn bo'lmasa o'zgarishsiz qaytadi."""
    if not isinstance(qiymat, str):
        return qiymat
    for b in BOSHLIQLAR:
        qiymat = qiymat.replace(b, '')
    return qiymat


# --------------------------------------------------------------- sana

# Arizada sana so'z bilan yoziladi: «05 август 2026 йил»
OYLAR = ['январ', 'феврал', 'март', 'апрел', 'май', 'июн',
         'июл', 'август', 'сентябр', 'октябр', 'ноябр', 'декабр']


def sana_sozlar(sana):
    """date(2026, 8, 5) -> «05 август 2026»"""
    return f'{sana.day:02d} {OYLAR[sana.month - 1]} {sana.year}'


def pul_matn(qiymat):
    """7000000 -> «7 000 000». Songa aylanmasa qiymatning o'zi qaytadi."""
    if qiymat is None or qiymat == '':
        return qiymat
    try:
        son = Decimal(pul_son(str(qiymat)))
    except (InvalidOperation, ValueError):
        return qiymat
    butun = int(son.to_integral_value(rounding=ROUND_HALF_UP))
    return f'{butun:,}'.replace(',', ' ')
