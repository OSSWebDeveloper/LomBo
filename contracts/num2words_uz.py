# -*- coding: utf-8 -*-
"""Sonni kirill-o'zbek tilida so'z bilan yozish.
35_000_000 -> «ўттиз беш миллион»
43_750_000 -> «қирқ уч миллион етти юз эллик минг»
"""

BIRLIK = ['', 'бир', 'икки', 'уч', 'тўрт', 'беш', 'олти', 'етти', 'саккиз', 'тўққиз']
ONLIK = ['', 'ўн', 'йигирма', 'ўттиз', 'қирқ', 'эллик', 'олтмиш', 'етмиш', 'саксон', 'тўқсон']
DARAJA = ['', 'минг', 'миллион', 'миллиард', 'триллион']


def _uch_xona(n: int) -> str:
    """0..999 ni so'zga aylantiradi."""
    parts = []
    yuz, qoldiq = divmod(n, 100)
    if yuz:
        parts.append(f'{BIRLIK[yuz]} юз'.strip())
    on, bir = divmod(qoldiq, 10)
    if on:
        parts.append(ONLIK[on])
    if bir:
        parts.append(BIRLIK[bir])
    return ' '.join(parts)


def num2words_uz(n) -> str:
    """Butun sonni kirill-o'zbekcha so'zga aylantiradi."""
    n = int(n)
    if n == 0:
        return 'нол'
    if n < 0:
        return 'минус ' + num2words_uz(-n)

    guruhlar = []
    while n:
        n, g = divmod(n, 1000)
        guruhlar.append(g)

    parts = []
    for i in range(len(guruhlar) - 1, -1, -1):
        g = guruhlar[i]
        if not g:
            continue
        soz = _uch_xona(g)
        if DARAJA[i]:
            soz = f'{soz} {DARAJA[i]}'.strip()
        parts.append(soz)
    return ' '.join(parts)


def summa_soz_bilan(n) -> str:
    """«35 000 000 (ўттиз беш миллион)» ko'rinishdagi so'z qismi."""
    return num2words_uz(n)


def summa_formatlangan(n) -> str:
    """35000000 -> «35 000 000»"""
    return f'{int(n):,}'.replace(',', ' ')
