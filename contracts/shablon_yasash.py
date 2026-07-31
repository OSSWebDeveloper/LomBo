# -*- coding: utf-8 -*-
"""Asl .doc shartnomalaridan docxtpl shablonlarini yasaydi.

Asl fayldagi o'zgaruvchan qiymatlar (mijoz ismi, summa, sana...) o'rniga
`{{ nom }}` shaklidagi belgilar qo'yiladi. O'zgarmas matn va butun formatlash
asl faylning aynan o'zi bo'lib qoladi.

Ishga tushirish:  python contracts/shablon_yasash.py
"""
import copy
import os
import sys

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

PAPKA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shablonlar')


# --------------------------------------------------------------- yurish

def xatboshilar(doc):
    """Hujjatdagi barcha xatboshilar — jadval ichidagilari ham.

    XML daraxtining o'zidan yuriladi: birlashtirilgan (merged) kataklar
    sababli bir element bir necha marta qaytishining oldi olinadi.
    """
    for el in doc.element.body.iter(qn('w:p')):
        yield Paragraph(el, None)


def jadvallar(doc):
    """Barcha jadvallar — ichma-ichlari bilan, takrorlanmasdan."""
    for el in doc.element.body.iter(qn('w:tbl')):
        yield Table(el, None)


# --------------------------------------------------------------- almashtirish

def xatboshida_almashtir(p, eski, yangi):
    """Run'lar orasiga bo'lingan matnni ham almashtiradi.

    Topilgan joyning birinchi run'i formatlashi saqlanadi — ya'ni asl faylda
    qizil bo'lgan qism qizilligicha qoladi.
    """
    almashdi = 0
    while True:
        runs = p.runs
        toliq = ''.join(r.text for r in runs)
        # Asl faylda raqamlar ichida uzilmas bo'shliq (U+00A0) ishlatilgan.
        # Uzunligi bir xil bo'lgani uchun indekslar buzilmaydi.
        boshi = toliq.replace(' ', ' ').find(eski)
        if boshi < 0:
            return almashdi
        oxiri = boshi + len(eski)

        # Har bir run qaysi belgilarni egallaganini hisoblaymiz
        chegara = []
        joriy = 0
        for r in runs:
            chegara.append((joriy, joriy + len(r.text)))
            joriy += len(r.text)

        birinchi = None
        for i, (a, b) in enumerate(chegara):
            if b <= boshi or a >= oxiri:
                continue          # bu run tegishli emas
            kes_a = max(boshi, a) - a
            kes_b = min(oxiri, b) - a
            matn = runs[i].text
            if birinchi is None:
                birinchi = i
                runs[i].text = matn[:kes_a] + yangi + matn[kes_b:]
            else:
                runs[i].text = matn[:kes_a] + matn[kes_b:]
        almashdi += 1


def hujjatda_almashtir(doc, juftlar):
    """juftlar: [(eski_matn, yangi_matn), ...] — tartib muhim."""
    hisob = {eski: 0 for eski, _ in juftlar}
    for p in xatboshilar(doc):
        for eski, yangi in juftlar:
            hisob[eski] += xatboshida_almashtir(p, eski, yangi)
    return hisob


# --------------------------------------------------------------- zargarlik jadvali

def zargarlik_jadvalini_shablonla(doc):
    """4 ta namuna qatorini bitta takrorlanuvchi qatorga aylantiradi."""
    # Aynan buyumlar jadvali: kamida 5 ustun va sarlavhasida «Кимматликлар»
    # bo'lgan qisqa katak (uni o'rab turgan katta jadvaldan farqlash uchun).
    nishon = None
    for t in jadvallar(doc):
        if len(t.columns) < 5:
            continue
        sarlavha = [c.text.strip() for c in t.rows[0].cells]
        if any('имматликлар' in s and len(s) < 40 for s in sarlavha):
            nishon = t
            break
    if nishon is None:
        return False, 'zargarlik jadvali topilmadi'

    qatorlar = nishon.rows
    if len(qatorlar) < 3:
        return False, f'jadvalda atigi {len(qatorlar)} qator bor'

    # 0 — sarlavha, 1..n-2 — buyumlar, oxirgisi — «Жами»
    birinchi_buyum = qatorlar[1]
    jami_qatori = qatorlar[-1]

    # Birinchi buyum qatorini namuna qatoriga aylantiramiz.
    # Bu qator docxtpl'ga tegishli emas — u render'dan keyin har bir buyum
    # uchun nusxalanadi (docgen.py dagi _buyumlar_jadvali).
    qiymatlar = ['#IDX#', '#NOMI#', '#SONI# та', '#OGIR# гр', '#PROBA#', '#SUMMA#']
    kataklar = birinchi_buyum.cells
    for i, katak in enumerate(kataklar):
        if i >= len(qiymatlar):
            break
        p = katak.paragraphs[0]
        if p.runs:
            p.runs[0].text = qiymatlar[i]
            for r in p.runs[1:]:
                r.text = ''
        else:
            p.add_run(qiymatlar[i])
        for qoshimcha in katak.paragraphs[1:]:
            for r in qoshimcha.runs:
                r.text = ''

    # Ortiqcha namuna qatorlarini o'chiramiz (jami qatoridan tashqari)
    for qator in list(qatorlar[2:-1]):
        qator._element.getparent().remove(qator._element)

    return True, f'jadval shablonlandi, {len(qatorlar) - 3} ta ortiqcha qator olindi'


# --------------------------------------------------------------- 196 -> zargarlik

ZARGARLIK_JUFTLAR = [
    # Uzunroq va aniqroqlari birinchi
    ('Бухоро вилояти, 61013-сонли ИИВ томонидан 23.04.2025-йилда берилган '
     'АE№2437494 ракамли шахс гувохномаси', '{{ pasport }}'),
    ('Бухоро шахар, Имом Ал-Бухорий МФЙ, Тагбанбафон  кўчаси, 22-уй', '{{ manzil }}'),
    ('43 750 000 (кирк уч миллион етти юз эллик минг)', '{{ garov_baho }}'),
    ('35 000 000 (Ўттиз беш миллион)', '{{ summa }}'),
    ('Микрокарз шартномаси №196', 'Микрокарз шартномаси №{{ raqam }}'),
    ('Гаров шартнома 196', 'Гаров шартнома {{ garov_raqam }}'),
    ('№196-сонли', '№{{ raqam }}-сонли'),
    ('Джураева Майсара Ахмедовнага', '{{ fio }}га'),
    ('Джураева Майсара Ахмедовна', '{{ fio }}'),
    ('02.11.2026', '{{ tugash }}'),
    ('03.11.2025', '{{ sana }}'),
    ('12(ўн икки)', '{{ muddat }}({{ muddat_soz }})'),
    ('60% (олтмиш)', '{{ foiz }}% ({{ foiz_soz }})'),
    # Jadval jami qatori
    ('11 та', '{{ jami_soni }} та'),
    ('46,10 гр', '{{ jami_ogirligi }} гр'),
    ('43 750 000', '{{ garov_baho_raqam }}'),
]


def zargarlik_shabloni():
    manba = os.path.join(PAPKA, 'm196.docx')
    doc = Document(manba)

    ok, xabar = zargarlik_jadvalini_shablonla(doc)
    print(f'  jadval: {xabar}')

    hisob = hujjatda_almashtir(doc, ZARGARLIK_JUFTLAR)
    for eski, n in hisob.items():
        belgi = 'OK ' if n else 'YO\'Q'
        print(f'  [{belgi}] {n:2} marta: {eski[:60]}')

    chiqish = os.path.join(PAPKA, 'zargarlik.docx')
    doc.save(chiqish)
    print(f'  -> {chiqish}')
    return all(hisob.values())


# --------------------------------------------------------------- 199 -> kafillik / transport

# 199-faylning mikroqarz qismidagi umumiy qiymatlar
Q199_UMUMIY = [
    ('61013-сонли ИИВ томонидан 20.05.2025-йилда берилган АE№2751664 '
     'ракамли шахс гувохномаси', '{{ pasport }}'),
    ('Бухоро вилояти, Бухоро  туман, Работикалмок МФЙ,Тикончи кўчаси', '{{ manzil }}'),
    ('7 000 000 (етти миллион)', '{{ summa }}'),
    ('Микрокарз шартномаси №199', 'Микрокарз шартномаси №{{ raqam }}'),
    ('Содиков Ботир Нусратович', '{{ fio }}'),
    ('30.10.2026', '{{ tugash }}'),
    ('31.10.2025', '{{ sana }}'),
    ('12(ўн икки)', '{{ muddat }}({{ muddat_soz }})'),
    ('60% (олтмиш )', '{{ foiz }}% ({{ foiz_soz }})'),
]

# 1.1-banddagi ta'minot jumlasi — turga qarab boshqacha
KAFILLIK_TAMINOT = (
    'Жураев Азизбек Носировичнинг  10 000 000 (ўн миллион) сўмлик '
    'иш хакки кафиллиги  такдим килинади.')
KAFILLIK_YANGI = '{{ kafil }}нинг {{ kafillik_summa }} сўмлик иш хакки кафиллиги такдим килинади.'
TRANSPORT_YANGI = ('{{ garov_egasi }}га тегишли, давлат раками {{ davlat_raqami }} бўлган, '
                   '{{ rusumi }} русумли транспорт воситаси гаровга қўйилади.')

# Garov shartnomasi va dalolatnomadagi transport qiymatlari
TRANSPORT_JUFTLAR = [
    ('“Express Alligator Bukhara” МЧЖга тегишли, давлат раками 80 9511АA бўлган, '
     'KRONE SDR27 русумли YARIM TIRKAMA REFRIJERATOR', '{{ garov_mulki }}'),
    ('“Express Alligator Bukhara” МЧЖга тегишли, давлат раками 80 9511 АA бўлган, '
     'KRONE SDR27 русумли YARIM TIRKAMA REFRIJERATOR', '{{ garov_mulki }}'),
    ('70 000 000 (етмиш миллион)', '{{ garov_baho }}'),
    ('50 000 000(эллик миллион)', '{{ summa_raqam_soz }}'),
    ('Гаров шартнома 34', 'Гаров шартнома {{ garov_raqam }}'),
    ('№34-сонли', '№{{ raqam }}-сонли'),
    ('04.04.2025', '{{ sana }}'),
    ('Бахшиллоева Нозима Бахтиёровна', '{{ fio }}'),
    ('Бахшиллоева Дилноза Бахтиёровна', '{{ garov_rahbari }}'),
    ('Д.Б.Бахшиллоева', '{{ garov_rahbari_qisqa }}'),   # imzo qatoridagi qisqartma
    ('“Express Alligator Bukhara” МЧЖ', '{{ garov_egasi }}'),
    ('Бухоро шахар 6206-сонли ИИВ томонидан 08.04.2021 йилда берилган '
     'АD 0301390 ракамли шахсни тасдикловчи хужжат', '{{ pasport }}'),
    ('Бухоро шахар, Шайхон кучаси, 156 – уй', '{{ manzil }}'),
    ('80 9511 АА', '{{ davlat_raqami }}'),
    ('KRONE SDR27', '{{ rusumi }}'),
    ('QORA CHERNIY', '{{ rangi }}'),
    ('WKESD000000713326', '{{ shassi }}'),
    ('2016-yil', '{{ yili }}'),
    ('AAG 0949387 / 14.02.2023 йил', '{{ texpasport }}'),
]


def _garov_qismini_ochir(doc):
    """Kafillik uchun garov shartnomasi va dalolatnomani olib tashlaydi."""
    body = doc.element.body
    ochirildi = 0
    for el in list(body):
        if el.tag != qn('w:tbl'):
            continue
        matn = ''.join(t.text or '' for t in el.iter(qn('w:t')))
        if 'аров шартнома' in matn and 'ШАРТНОМА  ПРЕДМЕТИ' in matn:
            body.remove(el)
            ochirildi += 1
    return ochirildi


def _shablon_yasa(nomi, juftlar, taminot_yangi, garovni_ochir=False):
    doc = Document(os.path.join(PAPKA, 'm199.docx'))

    if garovni_ochir:
        n = _garov_qismini_ochir(doc)
        print(f'  garov qismi olib tashlandi: {n} ta blok')

    juftlar = [(KAFILLIK_TAMINOT, taminot_yangi)] + juftlar
    hisob = hujjatda_almashtir(doc, juftlar)
    for eski, n in hisob.items():
        belgi = 'OK ' if n else 'YO\'Q'
        print(f'  [{belgi}] {n:2} marta: {eski[:58]}')

    chiqish = os.path.join(PAPKA, nomi)
    doc.save(chiqish)
    print(f'  -> {chiqish}')
    return all(hisob.values())


def kafillik_shabloni():
    return _shablon_yasa('kafillik.docx', list(Q199_UMUMIY),
                         KAFILLIK_YANGI, garovni_ochir=True)


def transport_shabloni():
    return _shablon_yasa('transport.docx', list(Q199_UMUMIY) + TRANSPORT_JUFTLAR,
                         TRANSPORT_YANGI)


if __name__ == '__main__':
    natijalar = []
    print('ZARGARLIK shabloni:')
    natijalar.append(zargarlik_shabloni())
    print('\nKAFILLIK shabloni:')
    natijalar.append(kafillik_shabloni())
    print('\nTRANSPORT shabloni:')
    natijalar.append(transport_shabloni())
    sys.exit(0 if all(natijalar) else 1)
