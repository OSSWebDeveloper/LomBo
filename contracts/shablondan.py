# -*- coding: utf-8 -*-
"""Asl shartnoma fayllaridan yasalgan shablonlar asosida hujjat tayyorlash.

O'zgarmas matn va formatlash asl faylning aynan o'zi — faqat `{{ ... }}`
belgilari va zargarlik jadvalidagi `#...#` namunasi almashtiriladi.
"""
import copy
import io
import os

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph
from docxtpl import DocxTemplate

from .docx_ulash import hujjatni_boshiga_qoy
from .formatlash import sana_sozlar
from .num2words_uz import num2words_uz, summa_formatlangan

SHABLONLAR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shablonlar')

# Ma'lumot yo'q bo'lsa hujjatda qo'lda to'ldiriladigan chiziq qoladi.
# Telefon va oylik daromad maydonlari 2026-08 da qo'shilgan — undan oldingi
# shartnomalarda bu qiymatlar bo'lmaydi.
BOSH_CHIZIQ = '____________'

# Asl fayllarda raqamlar ichida uzilmas bo'shliq ishlatilgan
NBSP = ' '


def _pul(n):
    """35000000 -> «35 000 000 (ўттиз беш миллион)» (asl fayldagidek)"""
    return f'{_raqam(n)} ({num2words_uz(n)})'


def _raqam(n):
    """Asl hujjatdagidek: birinchi bo'shliq oddiy, keyingilari uzilmas."""
    s = summa_formatlangan(n)
    boshi, _, qolgani = s.partition(' ')
    return boshi + (' ' + qolgani.replace(' ', NBSP) if qolgani else '')


def _vergul(x):
    return f'{x}'.replace('.', ',')


# --------------------------------------------------------------- jadval

def _jadvallar(doc):
    for el in doc.element.body.iter(qn('w:tbl')):
        yield Table(el, None)


def _katakka_yoz(katak, matn):
    """Katak matnini almashtiradi, birinchi run formatlashini saqlab."""
    p = katak.paragraphs[0]
    if p.runs:
        p.runs[0].text = matn
        for r in p.runs[1:]:
            r.text = ''
    else:
        p.add_run(matn)
    for qoshimcha in katak.paragraphs[1:]:
        for r in qoshimcha.runs:
            r.text = ''


def _buyumlar_jadvali(doc, buyumlar):
    """`#NOMI#` namunali qatorni har bir buyum uchun nusxalaydi."""
    nishon = namuna = None
    for t in _jadvallar(doc):
        for row in t.rows:
            if any('#NOMI#' in c.text for c in row.cells):
                nishon, namuna = t, row
                break
        if nishon:
            break
    if namuna is None:
        return False

    oldingi = namuna._tr
    for i, b in enumerate(buyumlar, start=1):
        yangi_tr = copy.deepcopy(namuna._tr)
        oldingi.addnext(yangi_tr)
        oldingi = yangi_tr
        qator = [r for r in nishon.rows if r._tr is yangi_tr][0]
        qiymatlar = [str(i), b['nomi'], f'{b["soni"]} та',
                     f'{b["ogirligi"]} гр', b['probasi'], b['summasi']]
        for j, katak in enumerate(qator.cells):
            if j < len(qiymatlar):
                _katakka_yoz(katak, qiymatlar[j])

    namuna._tr.getparent().remove(namuna._tr)   # namuna qatorini olib tashlaymiz
    return True


# --------------------------------------------------------------- kontekst

def zargarlik_konteksti(c):
    buyumlar = list(c.jewelry_items.all())
    jami_soni = sum(b.quantity for b in buyumlar)
    jami_ogirligi = sum(b.weight for b in buyumlar)
    ctx = _umumiy(c)
    ctx.update({
        # Garov shartnomasi, bayon, farmoyish va dalolatnoma — hammasi
        # shartnomaning o'sha raqami bilan yuritiladi.
        'garov_raqam': str(c.number),
        'garov_baho': _pul(c.garov_value or 0),
        'garov_baho_raqam': _raqam(c.garov_value or 0),
        'jami_soni': str(jami_soni),
        'jami_ogirligi': _vergul(jami_ogirligi),
        '_buyumlar': [{'nomi': b.name, 'soni': str(b.quantity),
                       'ogirligi': _vergul(b.weight), 'probasi': b.proba,
                       'summasi': _raqam(b.value)} for b in buyumlar],
    })
    return ctx


# --------------------------------------------------------------- asosiy

def _umumiy(c):
    """Uchala turga ham tegishli qiymatlar."""
    return {
        'raqam': str(c.number),
        'sana': c.date.strftime('%d.%m.%Y'),
        'sana_soz': sana_sozlar(c.date),        # arizada: «05 август 2026»
        'tugash': c.end_date.strftime('%d.%m.%Y'),
        'muddat': str(c.term_months),
        'muddat_soz': num2words_uz(c.term_months),
        'foiz': str(c.interest_rate),
        'foiz_soz': num2words_uz(c.interest_rate),
        'summa': _pul(c.amount),
        'fio': c.borrower_fio,
        'pasport': c.passport_full,
        'manzil': c.borrower_address,
        # Arizada uchta raqam, shartnoma rekvizitlarida birinchisi
        'telefon': c.borrower_phone or BOSH_CHIZIQ,
        'telefon2': c.borrower_phone2 or BOSH_CHIZIQ,
        'telefon3': c.borrower_phone3 or BOSH_CHIZIQ,
        'daromad': _raqam(c.monthly_income) if c.monthly_income else BOSH_CHIZIQ,
        # Arizada pasport ma'lumoti alohida kataklarga bo'lingan
        'pasport_seriya': c.passport_seriya,
        'pasport_soni': c.passport_soni,
        'pasport_sana': c.passport_date.strftime('%d.%m.%Y'),
        'pasport_viloyat': c.passport_region,
        'pasport_bolim': c.passport_org,
    }


def kafillik_konteksti(c):
    g = c.guarantor
    ctx = _umumiy(c)
    ctx.update({'kafil': g.fio, 'kafillik_summa': _pul(g.amount)})
    return ctx


def _qisqa_ism(toliq):
    """«Бахшиллоева Дилноза Бахтиёровна» -> «Д.Б.Бахшиллоева» (imzo qatori uchun)."""
    qismlar = (toliq or '').split()
    if len(qismlar) >= 3:
        return f'{qismlar[1][0]}.{qismlar[2][0]}.{qismlar[0]}'
    if len(qismlar) == 2:
        return f'{qismlar[1][0]}.{qismlar[0]}'
    return toliq


def transport_konteksti(c):
    v = c.vehicle
    mulk = (f'{v.owner}га тегишли, давлат раками {v.state_number} бўлган, '
            f'{v.model} русумли транспорт воситаси')
    ctx = _umumiy(c)
    ctx.update({
        # Garov shartnomasi, bayon, farmoyish va dalolatnoma — hammasi
        # shartnomaning o'sha raqami bilan yuritiladi.
        'garov_raqam': str(c.number),
        'garov_mulki': mulk,
        'garov_egasi': v.owner,
        'garov_rahbari': v.owner_head or v.owner,
        'garov_rahbari_qisqa': _qisqa_ism(v.owner_head) if v.owner_head else v.owner,
        'garov_baho': _pul(c.garov_value or 0),
        'summa_raqam_soz': _pul(c.amount),
        'davlat_raqami': v.state_number,
        'rusumi': v.model,
        'rangi': v.color,
        'shassi': v.chassis_number,
        'yili': v.year,
        'texpasport': v.techpassport,
    })
    return ctx


# --------------------------------------------------------------- to'lov jadvali

def tolov_jadvalini_qosh(doc, contract, qatorlar):
    """Shablon oxiriga «1-илова» — to'lov jadvalini qo'shadi."""
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Pt

    def sarlavha(matn, olcham=12, qalin=True):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(matn)
        r.bold = qalin
        r.font.size = Pt(olcham)
        r.font.name = 'Times New Roman'
        return p

    doc.add_page_break()
    sarlavha(f'Микрокарз шартномаси №{contract.number}га 1-илова')
    sarlavha('Кредит фоизларини тўлаш ва асосий қарз суммасини қайтариш ЖАДВАЛИ')

    p = doc.add_paragraph()
    r = p.add_run(f'Қарз олувчи: {contract.borrower_fio}. '
                  f'Кредит суммаси: {_pul(contract.amount)} сўм. '
                  f'Муддат: {contract.term_months} ой. '
                  f'Йиллик фоиз: {contract.interest_rate}%.')
    r.font.size = Pt(12)
    r.font.name = 'Times New Roman'

    jadval = doc.add_table(rows=len(qatorlar) + 2, cols=6)
    jadval.style = 'Table Grid'
    sarlavhalar = ['№', 'Тўлов санаси', 'Асосий қарз (сўм)', 'Фоиз (сўм)',
                   'Жами тўлов (сўм)', 'Қолдиқ (сўм)']
    for j, h in enumerate(sarlavhalar):
        _katakka_yoz(jadval.cell(0, j), h)
        jadval.cell(0, j).paragraphs[0].runs[0].bold = True

    j_asosiy = j_foiz = j_jami = 0
    for i, (n, sana, asosiy, foiz, jami, qoldiq) in enumerate(qatorlar, start=1):
        qiymatlar = [str(n), sana.strftime('%d.%m.%Y'), _raqam(asosiy),
                     _raqam(foiz), _raqam(jami), _raqam(qoldiq)]
        for j, q in enumerate(qiymatlar):
            _katakka_yoz(jadval.cell(i, j), q)
        j_asosiy += asosiy
        j_foiz += foiz
        j_jami += jami

    oxirgi = len(qatorlar) + 1
    for j, q in [(1, 'Жами'), (2, _raqam(j_asosiy)), (3, _raqam(j_foiz)),
                 (4, _raqam(j_jami))]:
        _katakka_yoz(jadval.cell(oxirgi, j), q)
        jadval.cell(oxirgi, j).paragraphs[0].runs[0].bold = True

    doc.add_paragraph()
    from django.conf import settings
    org = settings.LOMBARD_ORG
    for matn in [f'«Микромолия ташкилоти»: ___________ {org["director_short"]}',
                 f'«Қарз олувчи»: ___________ {contract.borrower_fio}']:
        p = doc.add_paragraph()
        r = p.add_run(matn)
        r.font.size = Pt(12)
        r.font.name = 'Times New Roman'


def shablondan_yasa(shablon_nomi, ctx, contract=None, jadval_qatorlari=None):
    """Shablonni to'ldirib, .docx baytlarini qaytaradi."""
    tpl = DocxTemplate(os.path.join(SHABLONLAR, shablon_nomi))
    buyumlar = ctx.pop('_buyumlar', None)
    tpl.render(ctx)

    buf = io.BytesIO()
    tpl.save(buf)
    buf.seek(0)

    if buyumlar is not None or jadval_qatorlari:
        doc = Document(buf)
        if buyumlar is not None:
            _buyumlar_jadvali(doc, buyumlar)
        if jadval_qatorlari:
            tolov_jadvalini_qosh(doc, contract, jadval_qatorlari)
        buf = io.BytesIO()
        doc.save(buf)

    return buf.getvalue()


def _garov_jadvalini_top(doc):
    """Garov shartnomasi va dalolatnoma joylashgan jadvalni topadi."""
    body = doc.element.body
    for el in body.iter(qn('w:tbl')):
        if el.getparent() is not body:
            continue                      # faqat eng yuqori darajadagi jadval
        matn = ''.join(t.text or '' for t in el.iter(qn('w:t')))
        if 'аров шартнома' in matn and 'ШАРТНОМА  ПРЕДМЕТИ' in matn:
            return el
    return None


def _oxiridagi_boshliqni_tozala(doc):
    """Garov olib tashlangach oxirida qolgan bo'sh xatboshilarni olib tashlaydi."""
    body = doc.element.body
    for el in reversed(list(body)):
        if el.tag == qn('w:sectPr'):
            continue
        if el.tag == qn('w:p') and not ''.join(
                t.text or '' for t in el.iter(qn('w:t'))).strip():
            body.remove(el)
        else:
            break


def qismlarga_ajrat(bayt):
    """To'liq hujjatni ikkiga bo'ladi: (asosiy shartnoma, garov qismi).

    Garov qismi bo'lmasa (kafillik) ikkinchisi None bo'ladi.
    """
    tekshir = Document(io.BytesIO(bayt))
    if _garov_jadvalini_top(tekshir) is None:
        return bayt, None

    # 1) Asosiy shartnoma — garov jadvalisiz
    asosiy = Document(io.BytesIO(bayt))
    nishon = _garov_jadvalini_top(asosiy)
    nishon.getparent().remove(nishon)
    _oxiridagi_boshliqni_tozala(asosiy)
    b1 = io.BytesIO()
    asosiy.save(b1)

    # 2) Garov qismi — faqat o'sha jadval qoladi
    garov = Document(io.BytesIO(bayt))
    nishon = _garov_jadvalini_top(garov)
    body = garov.element.body
    for el in list(body):
        if el is nishon or el.tag == qn('w:sectPr'):
            continue
        body.remove(el)
    b2 = io.BytesIO()
    garov.save(b2)

    return b1.getvalue(), b2.getvalue()


def muqova_bilan(contract, bayt):
    """Hujjat oldiga muqovani (to'plamning 1-sahifasi) qo'yadi.

    Muqova shartnoma hujjatining ichiga qo'yiladi, teskarisi emas — shunda
    shartnomaning uslublari joyida qoladi (qarang: hujjatni_boshiga_qoy).
    """
    from .muqova import muqova_hujjati

    doc = Document(io.BytesIO(bayt))
    hujjatni_boshiga_qoy(doc, muqova_hujjati(contract))
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def hujjat_yasa(contract, qism='asosiy'):
    """Shartnoma turiga qarab hujjat yasaydi.

    qism='asosiy'   — muqova + mikroqarz shartnomasi (garovsiz)
    qism='garov'    — garov shartnomasi + baholash dalolatnomasi (yo'q bo'lsa None)
    qism='hammasi'  — bitta faylda barchasi, muqovadan boshlab
    """
    from django.conf import settings

    from .docgen import payment_schedule

    turlar = {
        contract.TYPE_ZARGARLIK: ('zargarlik.docx', zargarlik_konteksti),
        contract.TYPE_TRANSPORT: ('transport.docx', transport_konteksti),
        contract.TYPE_KAFILLIK: ('kafillik.docx', kafillik_konteksti),
    }
    shablon, kontekst_fn = turlar[contract.collateral_type]
    # To'lov jadvali sozlamada yoqilgan bo'lsagina qo'shiladi
    qatorlar = (payment_schedule(contract)
                if getattr(settings, 'TOLOV_JADVALI_QOSHILSIN', False) else None)
    toliq = shablondan_yasa(shablon, kontekst_fn(contract),
                            contract=contract, jadval_qatorlari=qatorlar)
    if qism == 'hammasi':
        return muqova_bilan(contract, toliq)

    asosiy, garov = qismlarga_ajrat(toliq)
    # Garov hujjati alohida olinganda muqova kerak emas — u to'plamniki
    return garov if qism == 'garov' else muqova_bilan(contract, asosiy)


def garovi_bormi(contract):
    """Bu shartnomada garov hujjati tuziladimi?"""
    return contract.collateral_type in (contract.TYPE_ZARGARLIK,
                                        contract.TYPE_TRANSPORT)
