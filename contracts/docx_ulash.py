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


def _sarlavhami(p_el):
    """Xatboshi sarlavhami? Asl shartnomada sarlavhalar markazga tekislangan.

    Band nomlari («1.Шартноманинг предмети.»), hujjat nomlari («АРИЗА»,
    «Гаров шартнома 301») va jadval ustun nomlari — hammasi markazda.
    Oddiy matn esa eniga tekislangan yoki chapda.
    """
    pPr = p_el.find(qn('w:pPr'))
    if pPr is None:
        return False
    jc = pPr.find(qn('w:jc'))
    return jc is not None and jc.get(qn('w:val')) in ('center', 'centre')


def matnni_oddiy_qil(doc):
    """Shartnoma matnini bir xil ko'rinishga keltiradi.

    Xaridor talabi: hujjatdagi barcha matn bir xil uslubda bo'lsin, faqat
    bandlar sarlavhasi ajralib tursin.
      * 2026-08-14 — hamma harf qora (asl faylda o'zgaruvchan joylar qizil edi);
      * 2026-08-15 — qalin, kursiv va tagchiziq olib tashlanadi.

    Sarlavhalarga tegilmaydi: ular markazga tekislangani bilan tanib olinadi
    (band nomlari, hujjat nomlari, jadval ustun nomlari). Aks holda hujjatning
    tuzilishi yo'qolib, bandlar bir-biridan ajralmay qolardi.

    Oq rangga tegilmaydi: asl faylda u ko'rinmas to'ldirgich sifatida
    ishlatilgan, qora qilinsa hujjatda avval bo'lmagan chiziq paydo bo'lardi.

    Nechta run o'zgargani qaytadi.
    """
    ozgardi = 0
    for qism in _rang_beriladigan_qismlar(doc):
        for p_el in qism.iter(qn('w:p')):
            sarlavha = _sarlavhami(p_el)
            for el in p_el.iter(qn('w:r')):
                if not el.findall(qn('w:t')):
                    continue                  # matnsiz run (rasm, uzilish)
                run = Run(el, None)
                try:
                    joriy = run.font.color.rgb
                except (AttributeError, TypeError, ValueError):
                    joriy = None
                if joriy is not None and str(joriy).upper() == OQ:
                    continue
                run.font.color.rgb = RGBColor(0, 0, 0)
                # Mavzu rangi (themeColor) qo'yilgan bo'lsa w:val'dan ustun turadi
                rang = el.find(qn('w:rPr')).find(qn('w:color'))
                for atr in ('w:themeColor', 'w:themeTint', 'w:themeShade'):
                    rang.attrib.pop(qn(atr), None)
                if not sarlavha:
                    run.font.bold = False
                    run.font.italic = False
                    run.font.underline = False
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
