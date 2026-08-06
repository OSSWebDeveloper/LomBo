# -*- coding: utf-8 -*-
"""Pul summasini o'qish oson ko'rinishda chiqarish.

`{{ contract.amount|pul }}` -> `7 000 000`
"""
from django import template

from ..formatlash import pul_matn

register = template.Library()


@register.filter(name='pul')
def pul(qiymat):
    """Summani har uch raqamdan keyin bo'shliq bilan yozadi. Bo'sh bo'lsa «0»."""
    if qiymat is None or qiymat == '':
        return '0'
    return pul_matn(qiymat)
