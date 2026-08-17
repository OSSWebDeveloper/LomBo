# -*- coding: utf-8 -*-
"""Pul summasini o'qish oson ko'rinishda chiqarish.

`{{ contract.amount|pul }}` -> `7 000 000`
`{{ qator.foiz|pul_tiyin }}` -> `664 246,56`
"""
from django import template

from ..formatlash import pul_matn, pul_tiyin_matn

register = template.Library()


@register.filter(name='pul')
def pul(qiymat):
    """Summani har uch raqamdan keyin bo'shliq bilan yozadi. Bo'sh bo'lsa «0»."""
    if qiymat is None or qiymat == '':
        return '0'
    return pul_matn(qiymat)


@register.filter(name='pul_tiyin')
def pul_tiyin(qiymat):
    """To'lov jadvali uchun — tiyinlari bilan. Bo'sh bo'lsa «0,00»."""
    if qiymat is None or qiymat == '':
        return '0,00'
    return pul_tiyin_matn(qiymat)
