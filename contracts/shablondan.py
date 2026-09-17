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

from .docx_ulash import hujjatni_ulash, matnni_oddiy_qil
from .formatlash import sana_sozlar
from .models import pasport_hududi
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

def _dalolatnoma_taraflar(c):
    """Baholash dalolatnomasidagi ishtirokchilar ro'yxati.

    Odatda qarz oluvchi va garovga qo'yuvchi bitta shaxs — asl hujjatdagidek
    bitta ism yoziladi. Boshqa shaxs bo'lsa ikkalasi ham alohida ko'rsatiladi.
    """
    qarz = f'{c.borrower_fio} ({c.passport_full} ,Манзил: {c.borrower_address})'
    if not c.garov_beruvchi_boshqami:
        return f'қарз олувчи ва гаровга куювчи {qarz}'
    garov = (f'{c.garov_beruvchi_fio} ({c.garov_beruvchi_pasport} '
             f',Манзил: {c.garov_beruvchi_manzil})')
    return f'қарз олувчи {qarz} ва гаровга куювчи {garov}'


def zargarlik_konteksti(c):
    buyumlar = list(c.jewelry_items.all())
    jami_soni = sum(b.quantity for b in buyumlar)
    jami_ogirligi = sum(b.weight for b in buyumlar)
    ctx = _umumiy(c)
    boshqa = c.garov_beruvchi_boshqami
    ctx.update({
        # Butun to'plam bitta raqam bilan yuritiladi (xaridor qarori,
        # 2026-08-14 kechqurun — bir kun oldingi «alohida raqam» bekor).
        'garov_raqam': str(c.number),
        # Arizada — qarz oluvchining o'z tilidan, bayonda — uchinchi shaxsda.
        # Garovga qo'yuvchi boshqa bo'lsagina ism aytiladi.
        'ariza_taminot': (
            f'{c.garov_beruvchi_fio}га тегишли заргарлик буюмларини гаровга такдим этаман'
            if boshqa else 'узимга тегишли заргарлик буюмларини гаровга такдим этаман'),
        'garov_mulki': f'{c.garov_beruvchi_fio}га тегишли заргарлик буюмлари',
        'garov_mulki_egalik': (
            f'{c.garov_beruvchi_fio}га тегишли заргарлик буюмлари' if boshqa
            else f'{c.borrower_fio} узига тегишли заргарлик буюмлари'),
        # Garov shartnomasi va dalolatnomada «гаровга қўювчи» qarz oluvchining
        # o'zi bo'lishi shart emas — boshqa shaxs kiritilmagan bo'lsa
        # xossalar qarz oluvchining ma'lumotini qaytaradi.
        'garov_fio': c.garov_beruvchi_fio,
        'garov_pasport': c.garov_beruvchi_pasport,
        'garov_manzil': c.garov_beruvchi_manzil,
        'dalolatnoma_taraflar': _dalolatnoma_taraflar(c),
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
        'ish_joyi': c.borrower_workplace or BOSH_CHIZIQ,
        'daromad': _raqam(c.monthly_income) if c.monthly_income else BOSH_CHIZIQ,
        # Arizada pasport ma'lumoti alohida kataklarga bo'lingan
        'pasport_seriya': c.passport_seriya,
        'pasport_soni': c.passport_soni,
        'pasport_sana': c.passport_date.strftime('%d.%m.%Y'),
        'pasport_viloyat': c.passport_region,
        'pasport_bolim': c.passport_org,
        'pasport_tuman': c.passport_district,
        # «Бухоро вилояти 61013 - сонли» yoki (biometrik pasportda, bo'lim
        # raqami o'rnida tuman turgani uchun) «Бухоро вилояти Когон тумани»
        'pasport_bergan': (f'{c.passport_region} {c.passport_org} - сонли'
                           if c.passport_org
                           else pasport_hududi(c.passport_region, c.passport_district)),
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


def _transport_garovi(c, v):
    """Transport garovida «гаровга қўювчи» kim va qanday imzolaydi.

    Uch xil holat `VehicleInfo.egasi_turi` da turadi:
      tashkilot    — mashina tashkilotniki, uni rahbari buyruq asosida qo'yadi;
      qarz oluvchi — mashina o'zining nomida;
      shaxs        — mashina boshqa kishiniki, uni qarz oluvchi ishonchnoma
                     asosida garovga qo'yadi. Egasi hujjatni imzolamaydi,
                     ismi faqat «... га тегишли» degan joyda turadi
                     (xaridor namunasi: «Давронов Хумоюн — matiz», 2026-08-25).
    """
    mulk = (f'{v.owner}га тегишли, давлат раками {v.state_number} бўлган, '
            f'{v.model} русумли транспорт воситаси')
    tashkilot = v.egasi_turi == v.EGASI_TASHKILOT
    ishonchnoma = v.egasi_turi == v.EGASI_SHAXS
    qarz_oluvchi = (f'{c.borrower_fio} ({c.passport_full}, '
                    f'Манзил: {c.borrower_address})')

    if tashkilot:
        return {
            'garov_mulki': mulk,
            'taminot': f'{mulk} гаровга қўйилади.',
            'garovga_qoyuvchi': (
                f'гаровга кўювчи: {v.owner} номидан буйрук асосида фаолиятини '
                f'амалга оширувчи, жамият рахбари {v.owner_head}'),
            'garov_imzo_sarlavha': 'Гаровга  қўювчи:',
            'garov_imzo_ism': v.owner,
            'garov_imzo_qator': f'директори:_________________{_qisqa_ism(v.owner_head)}',
            'dalolatnoma_taraflar': (
                f'қарз олувчи {c.borrower_fio} ({c.passport_full}, манзили: '
                f'{c.borrower_address}) хамда гаровга қўювчи {v.owner} '
                f'рахбари {v.owner_head}'),
            'garov_dalolat_imzo': f'{v.owner} рахбари :    ___________     {v.owner_head}',
        }

    # Garovga qo'yuvchi — qarz oluvchining o'zi. Mashina boshqa kishiniki
    # bo'lsa u buni ishonchnoma asosida qiladi va shartnoma summasi
    # miqdorida kafillik ham beradi.
    return {
        'garov_mulki': mulk,
        'taminot': (f'{mulk} гарови хамда {c.borrower_fio}нинг {_pul(c.amount)} '
                    'сумлик кафиллиги такдим этилади.'
                    if ishonchnoma else f'{mulk} гаровга қўйилади.'),
        'garovga_qoyuvchi': ('Ишончнома асосида гаровга кўювчи: ' if ishonchnoma
                             else 'гаровга кўювчи: ') + qarz_oluvchi,
        'garov_imzo_sarlavha': ('Ишончнома асосида гаровга  қўювчи:' if ishonchnoma
                                else 'Гаровга  қўювчи:'),
        # Rekvizit blokida uch qator: ism, pasport, manzil
        'garov_imzo_ism': (f'{c.borrower_fio}\n{c.passport_full}\n'
                           f'Манзил: {c.borrower_address}'),
        'garov_imzo_qator': '___________',
        'dalolatnoma_taraflar': f'қарз олувчи ва гаровга куювчи {qarz_oluvchi}',
        'garov_dalolat_imzo': f'___________     {c.borrower_fio}',
    }


def transport_konteksti(c):
    v = c.vehicle
    ctx = _umumiy(c)
    ctx.update({
        # Butun to'plam bitta raqam bilan yuritiladi
        'garov_raqam': str(c.number),
        # Eski belgilar: saytdan yuklangan shablonlarda uchrashi mumkin
        'garov_egasi': v.owner,
        'garov_rahbari': v.owner_head or v.owner,
        'garov_rahbari_qisqa': _qisqa_ism(v.owner_head) if v.owner_head else v.owner,
        'garov_baho': _pul(c.garov_value or 0),
        'summa_raqam_soz': _pul(c.amount),
        'davlat_raqami': v.state_number,
        'rusumi': v.model,
        'rangi': v.color,
        'kuzov': v.body_number or '-',
        'shassi': v.chassis_number or '-',
        'dvigatel': v.engine_number or '-',
        'yili': v.year,
        'texpasport': v.techpassport,
    })
    ctx.update(_transport_garovi(c, v))
    return ctx


# --------------------------------------------------------------- to'lov jadvali

# Ustunlar xaridor namunasidagi tartibda (2026-08-17): kredit qoldig'i
# oldinda (davr boshidagi holat), jami to'lov esa oxirida.
JADVAL_SARLAVHALARI = ['№', 'Тулов санаси', 'Кредит қолдиги',
                       'Асосий карзни қайтариш',
                       'Фоиз тўловларини қайтариш', 'Туловнинг умумий суммаси']

# Jadval ostidagi o'zgarmas eslatmalar — xaridor namunasidan (2026-08-14)
JADVAL_ESLATMALARI = [
    'Кредитга хисобланган фоизлар миқдори кредитнинг хақиқатда чиққан ва '
    'қайтариш санасига қараб ўзгариши мумкин.',
    'Кредит фоизларини ва узини уз вактида кайтаришни унутманг.',
    'Хар бир кечиктирилган кун учун 0,3% микдорда жарима ундирилади.',
]


def _summa_tiyin(qiymat):
    """«664 246,56» — namunadagidek: minglar bo'shliq, tiyin vergul bilan."""
    butun, _, kasr = f'{qiymat:.2f}'.partition('.')
    return f'{int(butun):,}'.replace(',', ' ') + ',' + kasr


# Ilovadagi ustun enlari (sm) — xaridor tahrirlagan `shartnoma_168.docx` dan
# aynan olingan. Jami 16,9 sm — A4 matn maydoniga (17 sm) sig'adi.
JADVAL_USTUN_ENLARI = [0.81, 3.16, 3.19, 3.19, 3.36, 3.19]

ILOVA_MATN_PT = 12     # xatboshilar, sarlavha, «№» va sana ustunlari
ILOVA_SUMMA_PT = 11    # FAQAT pul summalari (2–5-ustunlar)

# Pul summalari turadigan ustunlar: qoldiq, asosiy qarz, foiz, umumiy summa.
# Faqat shular 11 pt — qolgan hamma narsa 12 pt (xaridor talabi, 2026-08-18).
SUMMA_USTUNLARI = (2, 3, 4, 5)


def tolov_jadvalini_qosh(doc, contract, qatorlar, *, yangi_sahifa=True):
    """Shartnoma oxiriga «1-сонли илова» — to'lov jadvalini qo'shadi.

    Ko'rinishi xaridor tahrirlab qaytargan namunadan olingan (2026-08-18,
    `shartnoma_168.docx`) — 2026-08-14 namunasini almashtiradi:
      * ilovadagi BARCHA yozuvlar qalin va 12 pt (eslatmalar ham);
      * sarlavha ikki qatorga bo'lingan — tashkilot/sana, keyin shartnoma raqami;
      * jadval kataklari gorizontal va vertikal markazda; FAQAT pul summalari
        11 pt (SUMMA_USTUNLARI), qolgani 12 pt — sarlavha qatori, «№» va sana
        ustunlari, «Жами» so'zi;
      * ustun enlari qat'iy (JADVAL_USTUN_ENLARI), teng bo'linmaydi;
      * «Жами» qatorida faqat «Жами» so'zi qalin — summalar oddiy.

    `yangi_sahifa=False` — ilova alohida hujjat bo'lganda (grafik
    kalkulyatorining Word yuklamasi): oldiga bo'sh sahifa qo'yilmaydi.
    """
    from django.conf import settings
    from docx.enum.table import WD_ALIGN_VERTICAL
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Cm, Pt

    org = settings.LOMBARD_ORG

    def qator(matn, *, markaz=False, qalin=True, olcham=ILOVA_MATN_PT):
        p = doc.add_paragraph()
        if markaz:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(2)
        if matn:
            r = p.add_run(matn)
            r.bold = qalin
            r.font.size = Pt(olcham)
            r.font.name = 'Times New Roman'
        return p

    def katak(i, j, matn, *, qalin=False, olcham=ILOVA_MATN_PT):
        """Jadval katagi — gorizontal va vertikal markazda."""
        yacheyka = jadval.cell(i, j)
        yacheyka.width = Cm(JADVAL_USTUN_ENLARI[j])
        yacheyka.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        _katakka_yoz(yacheyka, matn)
        p = yacheyka.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.runs[0]
        r.bold = qalin
        r.font.size = Pt(olcham)
        r.font.name = 'Times New Roman'

    if yangi_sahifa:
        doc.add_page_break()
    qator(contract.borrower_fio, markaz=True)
    # Sarlavha ikki qatorda — xaridor hujjatidagidek: birinchi qator tashkilot
    # va sana bilan tugaydi (oxiridagi bo'sh joy ham o'sha yerdan).
    qator(f'{org["name"]}нинг {sana_sozlar(contract.date)}-йилдаги ', markaz=True)
    qator(f'№{contract.number}-сонли микрокарз шартномасига 1-сонли илова',
          markaz=True)
    qator('')

    jadval = doc.add_table(rows=len(qatorlar) + 2, cols=6)
    jadval.style = 'Table Grid'
    jadval.autofit = False
    for j, h in enumerate(JADVAL_SARLAVHALARI):
        katak(0, j, h, qalin=True)

    j_asosiy = j_foiz = j_jami = 0
    for i, (n, sana, jami, asosiy, foiz, qoldiq) in enumerate(qatorlar, start=1):
        qiymatlar = [str(n), sana.strftime('%d.%m.%Y'), _summa_tiyin(qoldiq),
                     _summa_tiyin(asosiy), _summa_tiyin(foiz), _summa_tiyin(jami)]
        for j, q in enumerate(qiymatlar):
            katak(i, j, q, qalin=(j == 0),      # «№» ustuni qalin
                  olcham=ILOVA_SUMMA_PT if j in SUMMA_USTUNLARI else ILOVA_MATN_PT)
        j_asosiy += asosiy
        j_foiz += foiz
        j_jami += jami

    # «Жами» qatorida qoldiq ustuni (2) bo'sh qoladi — namunada ham shunday.
    # Faqat «Жами» so'zi qalin, summalar oddiy (xaridor namunasi, 2026-08-18).
    oxirgi = len(qatorlar) + 1
    jami_qatori = [(0, ''), (1, 'Жами'), (2, ''),
                   (3, _summa_tiyin(j_asosiy)), (4, _summa_tiyin(j_foiz)),
                   (5, _summa_tiyin(j_jami))]
    for j, q in jami_qatori:
        # 2-ustun «Жами» qatorida bo'sh — summa emas, shuning uchun 12 pt
        summami = j in SUMMA_USTUNLARI and q
        katak(oxirgi, j, q, qalin=(j == 1),
              olcham=ILOVA_SUMMA_PT if summami else ILOVA_MATN_PT)

    qator('')
    qator(f'Ижрочи директор :\t\t\t\t\t\t{org["director_short"]}')
    qator('')
    qator(f'Кредит олувчи:\t\t\t\t\t\t{contract.borrower_fio}')
    qator('Илованинг бир нусхасини олдим   \t\t\t ____________________')
    qator(f'Мурожаат учун Тел: {org.get("phone_jadval", org["phone"])}')
    qator('')
    qator('Хурматли кредитор!')
    for eslatma in JADVAL_ESLATMALARI:
        qator(eslatma)


def shablondan_yasa(shablon_nomi, ctx, contract=None, jadval_qatorlari=None):
    """Shablonni to'ldirib, .docx baytlarini qaytaradi."""
    tpl = DocxTemplate(os.path.join(SHABLONLAR, shablon_nomi))
    buyumlar = ctx.pop('_buyumlar', None)
    tpl.render(ctx)

    buf = io.BytesIO()
    tpl.save(buf)
    buf.seek(0)

    doc = Document(buf)
    if buyumlar is not None:
        _buyumlar_jadvali(doc, buyumlar)
    if jadval_qatorlari:
        tolov_jadvalini_qosh(doc, contract, jadval_qatorlari)
    # Ko'rinish shablonda emas, aynan shu yerda tekislanadi: shunda xodim
    # o'zi yuklagan shablon ham oddiy chiqadi, shablon tahrirlash sahifasida
    # esa `{{ }}` belgilari rangi bilan ajralib turaveradi.
    matnni_oddiy_qil(doc)

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


def garov_rasmlarini_qosh(doc, contract):
    """To'plam oxiriga garov suratlarini qo'yadi (muqovadan oldin).

    Bir varaqda ikkita surat (xaridor talabi, 2026-08-14). Har bir surat
    16×11 sm ramkaga sig'diriladi — nisbati saqlanadi, ya'ni tik surat ham,
    yotiq surat ham cho'zilmaydi.

    Fayl diskda topilmasa jimgina o'tkazib yuboriladi: eski shartnoma
    zaxiradan tiklanganda rasm yo'q bo'lishi mumkin.
    """
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Cm, Pt

    RAMKA_EN, RAMKA_BALAND = 16.0, 11.0        # santimetr

    rasmlar = list(contract.garov_rasmlari.all())
    if not rasmlar:
        return 0

    # python-docx faqat shu formatlarni tushunadi. Boshqasi (masalan telefon
    # yoki internetdan olingan .webp) hujjatga qo'yilmasdan oldin PNG'ga
    # o'giriladi — aks holda UnrecognizedImageError bilan yuklab olish uziladi.
    QOLLANADIGAN = {'PNG', 'JPEG', 'GIF', 'BMP', 'TIFF'}

    def tayyorla(yol):
        """(manba, en, balandlik) — manba fayl yo'li yoki xotiradagi oqim.

        Rasm o'lchami ramkaga nisbatini buzmasdan sig'diriladi.
        """
        from PIL import Image
        with Image.open(yol) as im:
            en_px, baland_px = im.size
            turi = (im.format or '').upper()
            manba = yol
            if turi not in QOLLANADIGAN:
                buf = io.BytesIO()
                # Shaffoflik oq fonga tushadi: Word'da PNG shaffofligi
                # ba'zan qora bo'lib chiqadi
                nusxa = im.convert('RGB')
                nusxa.save(buf, 'PNG')
                buf.seek(0)
                manba = buf
        nisbat = min(RAMKA_EN / en_px, RAMKA_BALAND / baland_px)
        return manba, Cm(en_px * nisbat), Cm(baland_px * nisbat)

    def sarlavha(matn, olcham_pt=12):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(4)
        r = p.add_run(matn)
        r.bold = True
        r.font.size = Pt(olcham_pt)
        r.font.name = 'Times New Roman'

    qoshildi = 0
    for rasm in rasmlar:
        try:
            manba, en, baland = tayyorla(rasm.rasm.path)
        except Exception:
            # Fayl yo'q, buzilgan yoki tanib bo'lmaydigan format — bitta surat
            # sababli butun hujjat berilmay qolmasin
            continue
        if qoshildi % 2 == 0:                  # har ikkitadan keyin yangi varaq
            doc.add_page_break()
            sarlavha(f'Гаров суратлари — №{contract.number}')
        if rasm.izoh:
            sarlavha(rasm.izoh, olcham_pt=10)
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(8)
        p.add_run().add_picture(manba, width=en, height=baland)
        qoshildi += 1
    return qoshildi


def muqova_bilan(contract, bayt):
    """To'plam oxiriga muqovani qo'yadi.

    Xaridor talabi (2026-08-14): muqova («Yuzi») eng oxirida tursin — avval
    shartnoma, garov, dalolatnoma, ariza, jadval va suratlar.

    Muqova shartnoma hujjatining ichiga qo'shiladi, teskarisi emas — shunda
    shartnomaning uslublari joyida qoladi (qarang: docx_ulash).
    """
    from .muqova import muqova_hujjati

    doc = Document(io.BytesIO(bayt))
    garov_rasmlarini_qosh(doc, contract)      # suratlar muqovadan oldin
    hujjatni_ulash(doc, muqova_hujjati(contract))
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
