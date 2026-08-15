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
from docx.shared import RGBColor
from docx.text.run import Run

QORA = '000000'
OQ = 'FFFFFF'


def matnni_oddiy_qil(doc):
    """Ajratib ko'rsatilgan joylarni oddiy ko'rinishga keltiradi.

    Asl shartnoma fayllarida o'zgaruvchan joylar (ism, summa, sana) qizil
    rangda, ko'pincha qalin/kursiv/tagchiziqli yozilgan edi. Xaridor talabiga
    ko'ra tayyor hujjatda ular boshqa matndan farq qilmasligi kerak:
      * 2026-08-14 — hamma harf qora bo'lsin;
      * 2026-08-15 — qalin, kursiv va tagchiziq ham olib tashlansin.

    Aynan **rangi bo'lgan** run'largina oddiylashtiriladi. Sarlavhalar va
    «Қарз олувчи» kabi atamalar asl faylda qora holda qalin — ular o'z
    ko'rinishida qoladi, aks holda hujjat tuzilishi yo'qolardi.

    Oq rangga tegilmaydi: asl faylda u ko'rinmas to'ldirgich sifatida
    ishlatilgan, qora qilinsa hujjatda avval bo'lmagan chiziq paydo bo'lardi.

    Nechta run o'zgargani qaytadi.
    """
    ozgardi = 0
    for qism in _rang_beriladigan_qismlar(doc):
        for el in qism.iter(qn('w:r')):
            if not el.findall(qn('w:t')):
                continue                      # matnsiz run (rasm, uzilish)
            run = Run(el, None)
            try:
                joriy = run.font.color.rgb
            except (AttributeError, TypeError, ValueError):
                joriy = None
            if joriy is not None and str(joriy).upper() == OQ:
                continue
            ajratilgan = joriy is not None and str(joriy).upper() != QORA
            run.font.color.rgb = RGBColor(0, 0, 0)
            # Mavzu rangi (themeColor) qo'yilgan bo'lsa w:val'dan ustun turadi
            rang = el.find(qn('w:rPr')).find(qn('w:color'))
            for atr in ('w:themeColor', 'w:themeTint', 'w:themeShade'):
                rang.attrib.pop(qn(atr), None)
            if ajratilgan:
                run.font.bold = False
                run.font.italic = False
                run.font.underline = False
                ozgardi += 1
            elif joriy is None:
                ozgardi += 1
    return ozgardi


# Eski nom — tashqi kod buzilmasligi uchun
qora_qil = matnni_oddiy_qil


def _rang_beriladigan_qismlar(doc):
    """Hujjat tanasi va haqiqatda mavjud kolontitullar.

    `is_linked_to_previous` tekshiruvi shart: yo'q kolontitulning `_element`iga
    murojaat qilinsa python-docx uni o'zi yaratib qo'yadi, bu esa sahifada
    joy egallab, matnni pastga suradi va hujjat sahifasi ortib ketadi.
    """
    yield doc.element.body
    for bolim in doc.sections:
        for qism in (bolim.header, bolim.footer,
                     bolim.first_page_header, bolim.first_page_footer,
                     bolim.even_page_header, bolim.even_page_footer):
            if qism is not None and not qism.is_linked_to_previous:
                yield qism._element


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


def hujjatni_boshiga_qoy(nishon, manba):
    """`nishon` hujjat boshiga `manba` hujjatni qo'yadi.

    Yo'nalish muhim: uslublar (styles.xml) faqat `nishon` hujjatniki bo'lib
    qoladi, `manba`niki tashlab yuboriladi. Shuning uchun muqovani muqova
    hujjatiga shartnomani qo'shish bilan emas, aynan shu yo'l bilan qo'yish
    kerak — aks holda shartnomaning jadval va xatboshi uslublari yo'qolib,
    matn tor ustunga siqilib qoladi.

    `manba` (muqova) butun formatlashini bevosita belgilarda olib yuradi,
    shuning uchun uslublarsiz ham o'z ko'rinishida qoladi.
    """
    n_body = nishon.element.body
    m_body = manba.element.body

    birinchi = n_body[0]
    for el in m_body:
        if el.tag == qn('w:sectPr'):
            continue                   # bo'lim sozlamasi pastda biriktiriladi
        birinchi.addprevious(copy.deepcopy(el))

    # Manba hujjatning sahifa sozlamasi alohida bo'lim bo'lib qoladi
    chegara = OxmlElement('w:p')
    manba_sect = m_body.find(qn('w:sectPr'))
    if manba_sect is not None:
        pPr = OxmlElement('w:pPr')
        pPr.append(copy.deepcopy(manba_sect))
        chegara.append(pPr)
    birinchi.addprevious(chegara)
    return nishon
