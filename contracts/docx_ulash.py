# -*- coding: utf-8 -*-
"""Ikki Word hujjatini bir faylga ulash.

Alohida modulda turibdi, chunki ikki joyda kerak: shablon yasashda
(`shablon_yasash.py`, skript sifatida ishlaydi) va hujjat berishda
(`shablondan.py`, Django ichida). Shu sababli bu modul Django'ga ham,
loyihaning boshqa modullariga ham bog'liq emas.
"""
import copy

from docx.oxml import OxmlElement
from docx.oxml.ns import qn


def hujjatni_ulash(nishon, manba):
    """`nishon` hujjat oxiriga `manba` hujjatni qo'shadi.

    Har bir hujjat o'z sahifa sozlamalarini (chekkalar, yo'nalish) saqlab
    qoladi: joriy bo'lim sozlamasi oxirgi xatboshiga biriktiriladi, manba
    hujjatniki esa yangi bo'lim bo'lib qo'shiladi. Bo'lim uzilishi o'zi yangi
    sahifadan boshlanadi, shuning uchun alohida sahifa uzilishi kerak emas.
    """
    n_body = nishon.element.body
    m_body = manba.element.body

    joriy_sect = n_body.find(qn('w:sectPr'))
    if joriy_sect is not None:
        n_body.remove(joriy_sect)
        chegara = OxmlElement('w:p')
        pPr = OxmlElement('w:pPr')
        pPr.append(copy.deepcopy(joriy_sect))
        chegara.append(pPr)
        n_body.append(chegara)

    for el in list(m_body):
        n_body.append(copy.deepcopy(el))
    return nishon
