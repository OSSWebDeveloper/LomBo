# -*- coding: utf-8 -*-
"""Kiritilgan ma'lumotlarni bir xil ko'rinishga keltirish.

Hujjat seriya-raqami turlicha yozilishi mumkin:
    ae5862145 · AE 5862145 · АЕ№5862145 · ae-5862145
Hammasi bitta ko'rinishga keltiriladi:  AE№5862145
"""
import re

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
