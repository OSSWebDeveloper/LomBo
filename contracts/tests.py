# -*- coding: utf-8 -*-
"""Hujjat yasash va forma tekshiruvlari."""
import io
import re
import shutil
import tempfile
from datetime import date

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone

from docx import Document
from docx.oxml.ns import qn

from .docgen import contract_end_date
from .forms import ContractForm
from .models import (HUJJAT_ID_KARTA, HUJJAT_PASPORT, Contract, GuarantorInfo,
                     JewelryItem, VehicleInfo)
from .shablondan import hujjat_yasa


# Suratlar test paytida vaqtinchalik papkaga tushadi — loyihaning media/
# papkasiga axlat qolmasin.
TEST_MEDIA = tempfile.mkdtemp(prefix='lombard-test-media-')


def namuna_rasm(nom='garov.png'):
    """Kichik, haqiqiy PNG — ImageField uni Pillow bilan tekshiradi."""
    from PIL import Image
    buf = io.BytesIO()
    Image.new('RGB', (8, 8), 'red').save(buf, format='PNG')
    return SimpleUploadedFile(nom, buf.getvalue(), content_type='image/png')


def hujjat_matni(baytlar):
    """Yasalgan .docx ichidagi butun matn — jadval kataklari bilan."""
    doc = Document(io.BytesIO(baytlar))
    return '\n'.join(
        ''.join(t.text or '' for t in p.iter(qn('w:t')))
        for p in doc.element.body.iter(qn('w:p'))
    ).replace(' ', ' ')


# Namuna fayllardan qolib ketmasligi kerak bo'lgan qiymatlar
NAMUNA_QOLDIQLARI = [
    'Рахмонова', 'Чогдаре', '2540542',            # m159 (zargarlik) namunasi
    'Содиков', 'Работикалмок', '2751664',         # m199 namunasi
    'Бахшиллоева', 'Express Alligator', 'KRONE',  # transport namunasi
    'Жураев Азизбек',                             # kafillik namunasi
]


class HujjatYasashTest(TestCase):
    """Uchala tur uchun ham shartnoma + ariza + bayon bitta faylda chiqadi."""

    def _shartnoma(self, tur, **qoshimcha):
        sana = date(2026, 8, 5)
        c = Contract.objects.create(
            number=301, date=sana, collateral_type=tur,
            borrower_fio='Каримова Нилуфар Аскаровна',
            passport_region='Бухоро вилояти', passport_org='61013',
            passport_date=date(2025, 4, 23), passport_number='АE№2437494',
            borrower_address='Бухоро шахар, Навоий кўчаси, 5-уй',
            borrower_phone='90 123-45-67', borrower_phone2='91 222-33-44',
            borrower_phone3='93 555-66-77', borrower_workplace='Бухоро тикув фабрикаси',
            monthly_income=4_000_000,
            amount=8_000_000, term_months=12, interest_rate=60,
            end_date=contract_end_date(sana, 12),
            **qoshimcha)
        return c

    def zargarlik(self):
        c = self._shartnoma(Contract.TYPE_ZARGARLIK, garov_value=9_000_000)
        JewelryItem.objects.create(contract=c, name='Тилла узук', quantity=1,
                                   weight=3, proba='585', value=4_000_000)
        JewelryItem.objects.create(contract=c, name='Тилла халка', quantity=2,
                                   weight='4.5', proba='585', value=5_000_000)
        return c

    def transport(self):
        c = self._shartnoma(Contract.TYPE_TRANSPORT, garov_value=90_000_000)
        VehicleInfo.objects.create(
            contract=c, egasi_turi=VehicleInfo.EGASI_TASHKILOT,
            owner='“Test Trans” МЧЖ', owner_head='Азизов Акмал Шухратович',
            state_number='01 A123AA', model='ISUZU NQR', color='ОК',
            body_number='-', chassis_number='XYZ123', engine_number='-',
            year='2019-yil', techpassport='AAF 1112223 / 01.02.2024 йил')
        return c

    def kafillik(self):
        c = self._shartnoma(Contract.TYPE_KAFILLIK)
        GuarantorInfo.objects.create(contract=c, fio='Салимов Жасур Анварович',
                                     amount=6_000_000)
        return c

    # ------------------------------------------------------------------ testlar

    def test_uchala_turda_ariza_va_bayon_bor(self):
        for yasovchi in (self.zargarlik, self.transport, self.kafillik):
            with self.subTest(tur=yasovchi.__name__):
                c = yasovchi()
                matn = hujjat_matni(hujjat_yasa(c, qism='hammasi'))
                self.assertIn('АРИЗА', matn)
                self.assertIn('кредит кумитаси йигилиш', matn)
                self.assertIn('ФАРМОЙИШ', matn)
                self.assertIn('ҚАРОР КИЛИНДИ', matn)
                Contract.objects.all().delete()

    def test_namuna_qiymatlari_qolmaydi(self):
        for yasovchi in (self.zargarlik, self.transport, self.kafillik):
            with self.subTest(tur=yasovchi.__name__):
                c = yasovchi()
                matn = hujjat_matni(hujjat_yasa(c, qism='hammasi'))
                for soz in NAMUNA_QOLDIQLARI:
                    self.assertNotIn(soz, matn)
                Contract.objects.all().delete()

    def test_mijoz_malumoti_hujjatga_tushadi(self):
        c = self.zargarlik()
        matn = hujjat_matni(hujjat_yasa(c, qism='hammasi'))
        self.assertIn('Каримова Нилуфар Аскаровна', matn)
        self.assertIn('Бухоро шахар, Навоий кўчаси, 5-уй', matn)
        self.assertIn('№301', matn)
        self.assertIn('8 000 000 (саккиз миллион)', matn)

    def test_uchala_telefon_arizaga_tushadi(self):
        for yasovchi in (self.zargarlik, self.transport, self.kafillik):
            with self.subTest(tur=yasovchi.__name__):
                c = yasovchi()
                matn = re.sub(r'\s+', ' ', hujjat_matni(hujjat_yasa(c, qism='hammasi')))
                self.assertIn('Телефон ракам 1) 90 123-45-67 2) 91 222-33-44 '
                              '3) 93 555-66-77', matn)
                # Birinchi raqam shartnomaning 9-bandiga ham tushadi
                self.assertEqual(matn.count('90 123-45-67'), 2)
                self.assertEqual(matn.count('91 222-33-44'), 1)
                self.assertEqual(matn.count('93 555-66-77'), 1)
                Contract.objects.all().delete()

    def test_arizada_daromad_va_pasport_qismlari(self):
        c = self.zargarlik()
        matn = hujjat_matni(hujjat_yasa(c, qism='hammasi'))
        self.assertIn('ойида ўртача 4 000 000 сўм', matn)
        self.assertIn('23.04.2025-йилда, Бухоро вилояти 61013 - сонли', matn)
        self.assertIn('05 август 2026 йил', matn)
        self.assertIn('Менинг иш жойим ва унинг манзили: Бухоро тикув фабрикаси',
                      matn)

    def test_telefon_yoq_bolsa_chiziq_qoladi(self):
        """Eski shartnomalarda telefon va daromad yo'q — joyi bo'sh qolmaydi."""
        c = self.zargarlik()
        Contract.objects.filter(pk=c.pk).update(
            borrower_phone='', borrower_phone2='', borrower_phone3='',
            monthly_income=None)
        c.refresh_from_db()
        matn = re.sub(r'\s+', ' ', hujjat_matni(hujjat_yasa(c, qism='hammasi')))
        self.assertIn('Телефон ракам 1) ____________ 2) ____________ '
                      '3) ____________', matn)
        self.assertIn('ойида ўртача ____________ сўм', matn)

    def test_yurist_tuzatishi_uchala_turda(self):
        """5.2-band: nizolar notarial ijro xati orqali ham hal qilinadi."""
        for yasovchi in (self.zargarlik, self.transport, self.kafillik):
            with self.subTest(tur=yasovchi.__name__):
                c = yasovchi()
                matn = hujjat_matni(hujjat_yasa(c, qism='hammasi'))
                self.assertIn('Нотариал идоранинг Ижро хати хамда Суд тартибида', matn)
                self.assertIn('55 310 00 87, 91 415-00-87', matn)
                Contract.objects.all().delete()

    def test_garov_rekvizitlari_yangilangan(self):
        for yasovchi in (self.zargarlik, self.transport):
            with self.subTest(tur=yasovchi.__name__):
                c = yasovchi()
                matn = hujjat_matni(hujjat_yasa(c, qism='hammasi'))
                self.assertIn('20216000405489627001', matn)
                self.assertIn('01137', matn)
                Contract.objects.all().delete()

    def test_muqova_toplamning_oxirgi_sahifasi(self):
        c = self.zargarlik()
        matn = hujjat_matni(hujjat_yasa(c, qism='hammasi'))
        self.assertIn('Кредит №', matn)
        self.assertIn('Сана / Муддати', matn)
        self.assertIn('8 000 000,00', matn)
        self.assertIn('Заргарлик буюмлари', matn)
        self.assertIn('Бухоро шаҳри 2026 йил', matn)
        # Xaridor talabi (2026-08-14): muqova («Yuzi») eng oxirida
        self.assertGreater(matn.index('Кредит №'),
                           matn.index('Микрокарз шартномаси'))
        self.assertGreater(matn.index('Кредит №'), matn.index('АРИЗА'))

    def test_muqovada_garov_turi_yoziladi(self):
        for yasovchi, kutilgan in ((self.zargarlik, 'Заргарлик буюмлари'),
                                   (self.transport, 'Транспорт воситаси'),
                                   (self.kafillik, 'Иш хаки кафиллиги')):
            with self.subTest(tur=yasovchi.__name__):
                c = yasovchi()
                matn = hujjat_matni(hujjat_yasa(c, qism='hammasi'))
                self.assertIn(kutilgan, matn)
                Contract.objects.all().delete()

    def test_hamma_hujjat_bitta_raqam_bilan(self):
        """Xaridor qarori: butun to'plam bitta shartnoma raqamida."""
        c = self.zargarlik()
        matn = re.sub(r'\s+', ' ', hujjat_matni(hujjat_yasa(c, qism='hammasi')))
        for ibora in ('Микрокарз шартномаси №301', '№301-сонли',
                      'далолатномаси №301', 'БАЁНИ №301', 'ФАРМОЙИШ №301',
                      'Гаров шартнома 301'):
            self.assertIn(ibora, matn)

    def test_zargarlik_jadvali_barcha_buyumni_chiqaradi(self):
        c = self.zargarlik()
        matn = hujjat_matni(hujjat_yasa(c, qism='hammasi'))
        self.assertIn('Тилла узук', matn)
        self.assertIn('Тилла халка', matn)
        self.assertIn('9 000 000', matn)      # garov bahosi = jami

    def test_garov_qismi_alohida_ajraladi(self):
        c = self.zargarlik()
        asosiy = hujjat_matni(hujjat_yasa(c, qism='asosiy'))
        garov = hujjat_matni(hujjat_yasa(c, qism='garov'))
        self.assertIn('ШАРТНОМА  ПРЕДМЕТИ', garov)
        self.assertNotIn('ШАРТНОМА  ПРЕДМЕТИ', asosiy)
        # Ariza va bayon asosiy hujjat bilan birga qoladi
        self.assertIn('АРИЗА', asosiy)
        self.assertIn('ФАРМОЙИШ', asosiy)

    def test_kafillikda_garov_hujjati_yoq(self):
        c = self.kafillik()
        matn = hujjat_matni(hujjat_yasa(c, qism='hammasi'))
        self.assertNotIn('ШАРТНОМА  ПРЕДМЕТИ', matn)
        self.assertIn('Салимов Жасур Анварович', matn)
        self.assertIn('6 000 000 (олти миллион) сўмлик иш хакки кафиллиги', matn)

    # ------------------------------------------------------- pasport turi

    def test_biometrik_pasportda_iiv_raqami_yozilmaydi(self):
        """Yashil pasportda IIV bo'lim raqami yo'q — matn raqamsiz tuziladi."""
        c = self.zargarlik()
        Contract.objects.filter(pk=c.pk).update(
            passport_type=HUJJAT_PASPORT, passport_org='')
        c.refresh_from_db()
        self.assertEqual(
            c.passport_full,
            'Бухоро вилояти ИИВ томонидан 23.04.2025-йилда берилган '
            'АE№2437494 ракамли паспорти')
        matn = re.sub(r'\s+', ' ', hujjat_matni(hujjat_yasa(c, qism='hammasi')))
        self.assertIn('Бухоро вилояти ИИВ томонидан 23.04.2025-йилда берилган', matn)
        self.assertNotIn('- сонли', matn)          # arizadagi joyi ham toza
        self.assertNotIn('-сонли ИИВ', matn)

    def test_pasport_turi_hujjatdagi_iborani_belgilaydi(self):
        for turi, kutilgan, kutilmagan in (
                (HUJJAT_ID_KARTA, 'ракамли шахс гувохномаси',
                 'ракамли паспорти'),
                (HUJJAT_PASPORT, 'ракамли паспорти',
                 'ракамли шахс гувохномаси')):
            with self.subTest(turi=turi):
                Contract.objects.all().delete()
                c = self.zargarlik()
                Contract.objects.filter(pk=c.pk).update(passport_type=turi)
                c.refresh_from_db()
                matn = hujjat_matni(hujjat_yasa(c, qism='hammasi'))
                self.assertIn(f'АE№2437494 {kutilgan}', matn)
                self.assertNotIn(kutilmagan, matn)

    # ------------------------------------------------- garovga qo'yuvchi

    def _garov_beruvchili(self):
        c = self.zargarlik()
        Contract.objects.filter(pk=c.pk).update(
            pledgor_other=True, pledgor_fio='Юсупова Гулнора Рахимовна',
            pledgor_passport_type=HUJJAT_PASPORT,
            pledgor_passport_region='Бухоро вилояти', pledgor_passport_org='61020',
            pledgor_passport_date=date(2024, 3, 15),
            pledgor_passport_number='АА№1112223',
            pledgor_address='Бухоро шахар, Гиждувон кўчаси, 12-уй')
        c.refresh_from_db()
        return c

    def test_garovga_qoyuvchi_boshqa_shaxs_hujjatga_tushadi(self):
        c = self._garov_beruvchili()
        garov = re.sub(r'\s+', ' ', hujjat_matni(hujjat_yasa(c, qism='garov')))
        # Garov shartnomasi va dalolatnomada — garovga qo'yuvchi
        self.assertIn('гаровга кўювчи: Юсупова Гулнора Рахимовна', garov)
        self.assertIn('АА№1112223 ракамли паспорти', garov)
        self.assertIn('Бухоро шахар, Гиждувон кўчаси, 12-уй', garov)
        # Qarz oluvchi ham o'z o'rnida qoladi
        self.assertIn('Каримова Нилуфар Аскаровна', garov)
        self.assertIn('қарз олувчи Каримова Нилуфар Аскаровна', garov)
        self.assertIn('ва гаровга куювчи Юсупова Гулнора Рахимовна', garov)

    def test_garovga_qoyuvchi_asosiy_shartnomaga_tegmaydi(self):
        """Mikroqarz shartnomasida faqat qarz oluvchi bo'ladi."""
        c = self._garov_beruvchili()
        asosiy = hujjat_matni(hujjat_yasa(c, qism='asosiy'))
        self.assertIn('«Қарз олувчи»: Каримова Нилуфар Аскаровна', asosiy)
        # Arizada esa kimning mulki gaovga qo'yilayotgani aytiladi
        self.assertIn('Юсупова Гулнора Рахимовнага тегишли заргарлик буюмларини',
                      asosiy)

    def test_garovga_qoyuvchi_kiritilmasa_qarz_oluvchi_qoladi(self):
        """Belgi qo'yilmagan bo'lsa hujjat avvalgidek chiqadi."""
        c = self.zargarlik()
        garov = re.sub(r'\s+', ' ', hujjat_matni(hujjat_yasa(c, qism='garov')))
        self.assertIn('гаровга кўювчи: Каримова Нилуфар Аскаровна', garov)
        self.assertIn('қарз олувчи ва гаровга куювчи Каримова Нилуфар Аскаровна',
                      garov)
        asosiy = hujjat_matni(hujjat_yasa(c, qism='asosiy'))
        self.assertIn('узимга тегишли заргарлик буюмларини', asosiy)

    # ------------------------------------------- transport: mashina egasi

    def transport_shaxsiy(self, egasi=None):
        """Mashina jismoniy shaxsniki — tashkilot emas.

        `egasi` berilmasa mashina qarz oluvchining o'z nomida bo'ladi.
        """
        c = self._shartnoma(Contract.TYPE_TRANSPORT, garov_value=23_000_000)
        VehicleInfo.objects.create(
            contract=c, owner=egasi or '', owner_head='',
            egasi_turi=(VehicleInfo.EGASI_SHAXS if egasi else VehicleInfo.EGASI_OZI),
            owner_passport_type=(HUJJAT_ID_KARTA if egasi else ''),
            owner_passport_region=('Бухоро вилояти' if egasi else ''),
            owner_passport_org=('61020' if egasi else ''),
            owner_passport_date=(date(2021, 5, 12) if egasi else None),
            owner_passport_number=('АД№1234567' if egasi else ''),
            owner_address=('Бухоро шахар, Гиждувон кўчаси, 3-уй' if egasi else ''),
            state_number='80 J 852 XA', model='MATIZ', color='KULRANG SEREBRISTIY',
            body_number='XWB4A11ADBA570223', chassis_number='RAQAMSIZ',
            engine_number='F8CV793145', year='2011-yil',
            techpassport='AAG 2620541 / 18.10.2023 йил')
        return c

    def test_mashina_egasi_boshqa_kishi_ishonchnoma_bilan_chiqadi(self):
        """Egasi imzolamaydi — qarz oluvchi ishonchnoma asosida garovga qo'yadi."""
        c = self.transport_shaxsiy('Бафоев Шахриёр Бахтиёрович')
        garov = re.sub(r'\s+', ' ', hujjat_matni(hujjat_yasa(c, qism='garov')))
        self.assertIn('Ишончнома асосида гаровга кўювчи: '
                      'Каримова Нилуфар Аскаровна', garov)
        self.assertIn('Ишончнома асосида гаровга қўювчи:', garov)
        # Mashina egasining ismi faqat mulk tavsifida turadi
        self.assertIn('Бафоев Шахриёр Бахтиёровичга тегишли', garov)
        self.assertIn('қарз олувчи ва гаровга куювчи Каримова Нилуфар Аскаровна',
                      garov)
        # Mikroqarz shartnomasining 1.1-bandi: garov + qarz oluvchining kafilligi
        asosiy = re.sub(r'\s+', ' ', hujjat_matni(hujjat_yasa(c, qism='asosiy')))
        self.assertIn('Бафоев Шахриёр Бахтиёровичга тегишли', asosiy)
        self.assertIn('Каримова Нилуфар Аскаровнанинг 8 000 000 (саккиз миллион) '
                      'сумлик кафиллиги такдим этилади', asosiy)

    def test_mashina_qarz_oluvchining_ozida_bolsa_ishonchnoma_yozilmaydi(self):
        c = self.transport_shaxsiy()
        garov = re.sub(r'\s+', ' ', hujjat_matni(hujjat_yasa(c, qism='garov')))
        self.assertIn('гаровга кўювчи: Каримова Нилуфар Аскаровна', garov)
        self.assertNotIn('Ишончнома', garov)
        asosiy = re.sub(r'\s+', ' ', hujjat_matni(hujjat_yasa(c, qism='asosiy')))
        self.assertIn('транспорт воситаси гаровга қўйилади', asosiy)
        self.assertNotIn('кафиллиги такдим этилади', asosiy)

    def test_mashina_tashkilotniki_bolsa_rahbari_imzolaydi(self):
        c = self.transport()
        garov = re.sub(r'\s+', ' ', hujjat_matni(hujjat_yasa(c, qism='garov')))
        self.assertIn('гаровга кўювчи: “Test Trans” МЧЖ номидан буйрук асосида',
                      garov)
        self.assertIn('жамият рахбари Азизов Акмал Шухратович', garov)
        self.assertIn('хамда гаровга қўювчи “Test Trans” МЧЖ рахбари '
                      'Азизов Акмал Шухратович', garov)
        self.assertNotIn('Ишончнома', garov)

    def test_dalolatnomada_mashina_raqamlari_toliq_boladi(self):
        """Kuzov, shassi va dvigatel raqamlari formadan hujjatga tushadi."""
        c = self.transport_shaxsiy('Бафоев Шахриёр Бахтиёрович')
        garov = re.sub(r'\s+', ' ', hujjat_matni(hujjat_yasa(c, qism='garov')))
        self.assertIn('XWB4A11ADBA570223 / RAQAMSIZ', garov)
        self.assertIn('F8CV793145', garov)
        # Baho — shartnomadagi qiymat, namunadagi 70 000 000 emas
        self.assertIn('23 000 000 (йигирма уч миллион)', garov)
        self.assertNotIn('70 000 000', garov)

    # -------------------------------------------------- garov suratlari

    def _rasm(self, contract, nom, fmt):
        from django.core.files.base import ContentFile
        from PIL import Image
        from .models import GarovRasm
        b = io.BytesIO()
        Image.new('RGB', (900, 600), (150, 80, 60)).save(b, fmt)
        return GarovRasm.objects.create(contract=contract,
                                        rasm=ContentFile(b.getvalue(), nom))

    def test_qollanmaydigan_format_hujjatni_buzmaydi(self):
        """`.webp` python-docx uchun notanish — PNG'ga o'girilib qo'yiladi.

        Bu haqiqiy nosozlik edi: mijoz telefondan .webp yuklagach shartnomani
        yuklab olish 500 xato bilan uzilardi (UnrecognizedImageError).
        """
        c = self.zargarlik()
        for nom, fmt in (('a.webp', 'WEBP'), ('b.png', 'PNG'), ('c.gif', 'GIF')):
            self._rasm(c, nom, fmt)
        doc = Document(io.BytesIO(hujjat_yasa(c, qism='hammasi')))
        self.assertEqual(sum(1 for _ in doc.element.body.iter(qn('w:drawing'))), 3)

    def test_buzilgan_surat_otkazib_yuboriladi(self):
        """Bitta yaroqsiz fayl sababli butun hujjat berilmay qolmasin."""
        from django.core.files.base import ContentFile
        from .models import GarovRasm
        c = self.zargarlik()
        self._rasm(c, 'yaxshi.png', 'PNG')
        GarovRasm.objects.create(contract=c,
                                 rasm=ContentFile(b'buzilgan', 'yomon.png'))
        doc = Document(io.BytesIO(hujjat_yasa(c, qism='hammasi')))
        self.assertEqual(sum(1 for _ in doc.element.body.iter(qn('w:drawing'))), 1)

    def test_bir_varaqda_ikkita_surat(self):
        c = self.zargarlik()
        for i in range(5):
            self._rasm(c, f'r{i}.png', 'PNG')
        doc = Document(io.BytesIO(hujjat_yasa(c, qism='hammasi')))
        uzilish, sahifa = 0, {}
        for el in doc.element.body.iter():
            if el.tag == qn('w:br') and el.get(qn('w:type')) == 'page':
                uzilish += 1
            elif el.tag == qn('w:drawing'):
                sahifa[uzilish] = sahifa.get(uzilish, 0) + 1
        self.assertEqual(sum(sahifa.values()), 5)
        self.assertTrue(all(v <= 2 for v in sahifa.values()), sahifa)

    # ------------------------------------------------------ ko'rinishi

    def test_hujjatda_qora_bolmagan_harf_qolmaydi(self):
        """Asl faylda qizil bo'lgan joylar ham qora chiqadi."""
        for yasovchi in (self.zargarlik, self.transport, self.kafillik):
            with self.subTest(tur=yasovchi.__name__):
                Contract.objects.all().delete()
                doc = Document(io.BytesIO(hujjat_yasa(yasovchi(), qism='hammasi')))
                uchragan = set()
                for run in doc.element.body.iter(qn('w:r')):
                    if not ''.join(t.text or '' for t in run.iter(qn('w:t'))).strip():
                        continue
                    rPr = run.find(qn('w:rPr'))
                    rang = rPr.find(qn('w:color')) if rPr is not None else None
                    uchragan.add(rang.get(qn('w:val')) if rang is not None else None)
                # Qora, oq (ko'rinmas to'ldirgich) va rangsiz — boshqasi bo'lmasin.
                # Rangsiz run Word'da baribir qora chiqadi (muqova shunday yasaladi).
                self.assertEqual(uchragan - {'FFFFFF', None}, {'000000'})

    def test_telefondan_keyin_bosh_qator_qoladi(self):
        """9-band: telefon raqami imzo jadvaliga yopishib qolmaydi."""
        for yasovchi in (self.zargarlik, self.transport, self.kafillik):
            with self.subTest(tur=yasovchi.__name__):
                Contract.objects.all().delete()
                doc = Document(io.BytesIO(hujjat_yasa(yasovchi(), qism='hammasi')))
                pars = [''.join(t.text or '' for t in p.iter(qn('w:t')))
                        for p in doc.element.body.iter(qn('w:p'))]
                i = next(n for n, t in enumerate(pars)
                         if t.strip().endswith('Телефон: 90 123-45-67'))
                self.assertEqual(pars[i + 1].strip(), '')
                self.assertEqual(pars[i + 2].strip(), '')


class ShablonTekshiruviTest(TestCase):
    """Shablonlar sayt orqali tahrirlash/almashtirish tekshiruvidan o'tadi."""

    def test_har_bir_shablon_sinov_konteksti_bilan_toladi(self):
        import os

        from .shablondan import SHABLONLAR
        from .views import SHABLON_TURLARI, _shablonni_tekshir

        for turi in SHABLON_TURLARI:
            with self.subTest(turi=turi):
                yol = os.path.join(SHABLONLAR, SHABLON_TURLARI[turi][0])
                self.assertIsNone(_shablonni_tekshir(yol, turi))


@override_settings(MEDIA_ROOT=TEST_MEDIA)
class FormaSahifasiTest(TestCase):
    """«Yangi shartnoma» formasida telefon va daromad maydonlari bor."""

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_MEDIA, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        from accounts.models import User
        self.ishchi = User.objects.create_user(
            username='ishchi1', password='ishchi123', role=User.ROLE_ISHCHI)
        self.client.force_login(self.ishchi)

    def test_maydonlar_formada_korinadi(self):
        javob = self.client.get('/shartnoma/yangi/')
        self.assertEqual(javob.status_code, 200)
        matn = javob.content.decode()
        for nom in ('id_borrower_phone', 'id_borrower_phone2',
                    'id_borrower_phone3', 'id_monthly_income'):
            self.assertIn(nom, matn)
        # Qarz oluvchi bo'limida — manzildan keyin
        self.assertLess(matn.index('id_borrower_address'), matn.index('id_borrower_phone'))
        self.assertLess(matn.index('id_borrower_phone'), matn.index("3. Kredit shartlari"))

    def test_kimniki_almashtirgichi_formada_boladi(self):
        """«Qarz oluvchiniki / boshqa» tanlovi ikkala garov turida ham bor."""
        matn = self.client.get('/shartnoma/yangi/').content.decode()
        self.assertIn('id="pledgor-tanlov"', matn)      # zargarlik
        self.assertIn('id="egasi-tanlov"', matn)        # transport
        # Transportda uchta tugma bo'ladi, zargarlikda — ikkita
        self.assertIn('vehicle-egasi_turi', matn)
        for qiymat in ('value="oz"', 'value="shaxs"', 'value="tashkilot"'):
            self.assertIn(qiymat, matn)
        # Egasining maydonlari almashadigan bloklar ichida turadi
        self.assertLess(matn.index('id="egasi-nomi"'), matn.index('vehicle-owner"'))
        self.assertLess(matn.index('id="egasi-hujjati"'),
                        matn.index('vehicle-owner_passport_number'))
        self.assertLess(matn.index('vehicle-owner_address'),
                        matn.index('vehicle-state_number'))
        # Shablon izohi sahifaga chiqib qolmasin: `{# ... #}` faqat bitta
        # qatorda ishlaydi, ko'p qatorlisi oddiy matn bo'lib ko'rinib qoladi.
        self.assertNotIn('{#', matn)
        self.assertNotIn('{%', matn)

    def test_telefonsiz_saqlab_bolmaydi(self):
        javob = self.client.post('/shartnoma/yangi/', self._malumot(telefonsiz=True))
        self.assertEqual(javob.status_code, 200)          # forma qayta ko'rsatiladi
        self.assertFalse(Contract.objects.exists())

    def test_toldirilgan_forma_saqlanadi(self):
        javob = self.client.post('/shartnoma/yangi/', self._malumot())
        self.assertEqual(javob.status_code, 302)
        c = Contract.objects.get()
        self.assertEqual(c.borrower_phone, '90 123-45-67')
        self.assertEqual(c.borrower_phone2, '91 222-33-44')
        self.assertEqual(c.borrower_phone3, '93 555-66-77')
        self.assertEqual(int(c.monthly_income), 4_000_000)

    def _malumot(self, telefonsiz=False, rasmsiz=False):
        """Formani to'ldirish uchun namuna ma'lumot.

        Kamida bitta garov surati majburiy (xaridor talabi, 2026-08-18) —
        shuning uchun surat formseti ham har doim qo'shiladi.
        """
        malumot = {
            'date': '2026-08-05', 'collateral_type': Contract.TYPE_ZARGARLIK,
            'borrower_fio': 'Каримова Нилуфар Аскаровна',
            'passport_type': HUJJAT_ID_KARTA,
            'passport_region': 'Бухоро вилояти', 'passport_org': '61013',
            'passport_date': '2025-04-23', 'passport_number': 'АE№2437494',
            'borrower_address': 'Бухоро шахар, Навоий кўчаси, 5-уй',
            'borrower_phone': '901234567', 'borrower_phone2': '912223344',
            'borrower_phone3': '935556677',
            'borrower_workplace': 'Бухоро тикув фабрикаси',
            'monthly_income': '4 000 000',
            'amount': '8 000 000', 'term_months': '12', 'interest_rate': '60',
            'jewelry-TOTAL_FORMS': '1', 'jewelry-INITIAL_FORMS': '0',
            'jewelry-MIN_NUM_FORMS': '0', 'jewelry-MAX_NUM_FORMS': '1000',
            'jewelry-0-name': 'Тилла узук', 'jewelry-0-quantity': '1',
            'jewelry-0-weight': '3', 'jewelry-0-proba': '585',
            'jewelry-0-value': '8 000 000',
            'rasm-TOTAL_FORMS': '1', 'rasm-INITIAL_FORMS': '0',
            'rasm-MIN_NUM_FORMS': '0', 'rasm-MAX_NUM_FORMS': '1000',
        }
        if not rasmsiz:
            malumot['rasm-0-rasm'] = namuna_rasm()
        if telefonsiz:
            malumot['borrower_phone'] = ''
        return malumot

    # ---------------------------------------------------- mashina egasi

    def _transport_malumoti(self, **qoshimcha):
        """Transport shartnomasi uchun to'liq forma ma'lumoti."""
        malumot = self._malumot()
        malumot['collateral_type'] = Contract.TYPE_TRANSPORT
        malumot.update({
            'vehicle-egasi_turi': VehicleInfo.EGASI_OZI,
            'vehicle-owner': '', 'vehicle-owner_head': '',
            'vehicle-state_number': '80 J 852 XA', 'vehicle-model': 'MATIZ',
            'vehicle-color': 'KULRANG', 'vehicle-body_number': 'XWB4A11ADBA570223',
            'vehicle-chassis_number': 'RAQAMSIZ',
            'vehicle-engine_number': 'F8CV793145', 'vehicle-year': '2011-yil',
            'vehicle-techpassport': 'AAG 2620541 / 18.10.2023 йил',
            'garov_value': '23 000 000',
        })
        malumot.update(qoshimcha)
        return malumot

    def test_mashina_qarz_oluvchiniki_bolsa_egasi_ozi_toladi(self):
        javob = self.client.post('/shartnoma/yangi/', self._transport_malumoti())
        self.assertEqual(javob.status_code, 302)
        v = Contract.objects.get().vehicle
        self.assertEqual(v.egasi_turi, VehicleInfo.EGASI_OZI)
        self.assertEqual(v.owner, 'Каримова Нилуфар Аскаровна')

    def test_boshqa_shaxs_bolsa_hujjati_soraladi(self):
        malumot = self._transport_malumoti(**{
            'vehicle-egasi_turi': VehicleInfo.EGASI_SHAXS,
            'vehicle-owner': 'Бафоев Шахриёр Бахтиёрович'})
        javob = self.client.post('/shartnoma/yangi/', malumot)
        self.assertEqual(javob.status_code, 200)          # hujjatsiz saqlanmaydi
        self.assertFalse(Contract.objects.exists())

        malumot.update({
            'vehicle-owner_passport_type': HUJJAT_ID_KARTA,
            'vehicle-owner_passport_region': 'Бухоро вилояти',
            'vehicle-owner_passport_org': '61020',
            'vehicle-owner_passport_date': '2021-05-12',
            'vehicle-owner_passport_number': 'ad1234567',
            'vehicle-owner_address': 'Бухоро шахар, Гиждувон кўчаси, 3-уй',
            'rasm-0-rasm': namuna_rasm(),
        })
        javob = self.client.post('/shartnoma/yangi/', malumot)
        self.assertEqual(javob.status_code, 302)
        v = Contract.objects.get().vehicle
        self.assertEqual(v.owner, 'Бафоев Шахриёр Бахтиёрович')
        self.assertEqual(v.owner_passport_number, 'AD№1234567')
        self.assertIn('ракамли шахс гувохномаси', v.egasi_pasporti)

    def test_tashkilot_bolsa_rahbari_soraladi(self):
        malumot = self._transport_malumoti(**{
            'vehicle-egasi_turi': VehicleInfo.EGASI_TASHKILOT,
            'vehicle-owner': '“Test Trans” МЧЖ'})
        javob = self.client.post('/shartnoma/yangi/', malumot)
        self.assertEqual(javob.status_code, 200)          # rahbarisiz saqlanmaydi
        self.assertFalse(Contract.objects.exists())

        malumot['vehicle-owner_head'] = 'Азизов Акмал Шухратович'
        malumot['rasm-0-rasm'] = namuna_rasm()
        javob = self.client.post('/shartnoma/yangi/', malumot)
        self.assertEqual(javob.status_code, 302)
        v = Contract.objects.get().vehicle
        self.assertEqual(v.owner_head, 'Азизов Акмал Шухратович')
        self.assertEqual(v.owner_passport_number, '')     # tashkilotda so'ralmaydi

    def test_royxatda_kiritilgan_vaqt_korinadi(self):
        self.client.post('/shartnoma/yangi/', self._malumot())
        c = Contract.objects.get()
        matn = self.client.get('/shartnomalar/').content.decode()
        self.assertIn('Kiritilgan', matn)
        self.assertIn(timezone.localtime(c.created_at).strftime('%d.%m.%Y %H:%M'), matn)

    # -------------------------------------------------------------- suratlar

    def test_suratsiz_saqlab_bolmaydi(self):
        """Kamida bitta garov surati majburiy (xaridor talabi, 2026-08-18)."""
        javob = self.client.post('/shartnoma/yangi/', self._malumot(rasmsiz=True))
        self.assertEqual(javob.status_code, 200)          # forma qayta ochiladi
        self.assertFalse(Contract.objects.exists())
        self.assertIn('Kamida 1 ta garov surati', javob.content.decode())

    def test_surat_bilan_saqlanadi(self):
        javob = self.client.post('/shartnoma/yangi/', self._malumot())
        self.assertEqual(javob.status_code, 302)
        self.assertEqual(Contract.objects.get().garov_rasmlari.count(), 1)

    def test_uchinchi_telefonsiz_ham_saqlab_bolmaydi(self):
        """Arizada uchta raqam so'ralgani uchun uchalasi ham majburiy."""
        malumot = self._malumot()
        malumot['borrower_phone3'] = ''
        javob = self.client.post('/shartnoma/yangi/', malumot)
        self.assertEqual(javob.status_code, 200)
        self.assertFalse(Contract.objects.exists())

    # -------------------------------------------------------------- raqamlar

    def test_raqam_maydoni_ochiq_va_toldirilgan(self):
        """Raqam avtomat taklif qilinadi, lekin qulflanmaydi."""
        matn = self.client.get('/shartnoma/yangi/').content.decode()
        maydon = re.search(r'<input[^>]*id="id_number"[^>]*>', matn).group(0)
        self.assertNotIn('disabled', maydon)
        self.assertIn(f'value="{settings.CONTRACT_START_NUMBER}"', maydon)

    def test_raqamni_qolda_kiritish(self):
        malumot = self._malumot()
        malumot['number'] = '777'
        self.assertEqual(self.client.post('/shartnoma/yangi/', malumot).status_code, 302)
        c = Contract.objects.get()
        self.assertEqual(c.number, 777)

    def test_band_raqam_xato_beradi(self):
        self.client.post('/shartnoma/yangi/', self._malumot())
        bor = Contract.objects.get()

        malumot = self._malumot()
        malumot['number'] = str(bor.number)
        javob = self.client.post('/shartnoma/yangi/', malumot)
        self.assertEqual(javob.status_code, 200)
        self.assertEqual(Contract.objects.count(), 1)
        self.assertIn('allaqachon mavjud', javob.content.decode())

    def test_raqamlar_bosh_qoldirilsa_avtomat_beriladi(self):
        """Ikki shartnoma ketma-ket: raqamlar o'z hisobida oshib boradi."""
        for _ in range(2):
            self.assertEqual(
                self.client.post('/shartnoma/yangi/', self._malumot()).status_code, 302)
        raqamlar = list(Contract.objects.order_by('number')
                        .values_list('number', flat=True))
        self.assertEqual(raqamlar, [settings.CONTRACT_START_NUMBER,
                                    settings.CONTRACT_START_NUMBER + 1])

    # ------------------------------------------------------ garovga qo'yuvchi

    def _garov_beruvchi_malumoti(self):
        return {
            'pledgor_other': 'on',
            'pledgor_fio': 'Юсупова Гулнора Рахимовна',
            'pledgor_passport_type': HUJJAT_PASPORT,
            'pledgor_passport_region': 'Бухоро вилояти',
            'pledgor_passport_org': '',
            'pledgor_passport_district': 'Ромитан тумани',
            'pledgor_passport_date': '2024-03-15',
            'pledgor_passport_number': 'aa1112223',
            'pledgor_address': 'Бухоро шахар, Гиждувон кўчаси, 12-уй',
        }

    def test_garovga_qoyuvchi_saqlanadi(self):
        malumot = self._malumot()
        malumot.update(self._garov_beruvchi_malumoti())
        self.assertEqual(self.client.post('/shartnoma/yangi/', malumot).status_code, 302)
        c = Contract.objects.get()
        self.assertTrue(c.garov_beruvchi_boshqami)
        self.assertEqual(c.garov_beruvchi_fio, 'Юсупова Гулнора Рахимовна')
        # Hujjat raqami qarz oluvchinikidek bir ko'rinishga keltiriladi
        self.assertEqual(c.pledgor_passport_number, 'AA№1112223')
        self.assertIn('ракамли паспорти', c.garov_beruvchi_pasport)

    def test_biometrik_pasportda_iiv_raqami_sorlmaydi(self):
        """Yashil pasportda IIV o'rniga tuman so'raladi, raqam bo'sh saqlanadi."""
        malumot = self._malumot()
        malumot['passport_type'] = HUJJAT_PASPORT
        malumot['passport_org'] = ''
        malumot['passport_district'] = 'Когон тумани'
        self.assertEqual(self.client.post('/shartnoma/yangi/', malumot).status_code, 302)
        c = Contract.objects.get()
        self.assertEqual(c.passport_org, '')
        self.assertIn('Бухоро вилояти Когон тумани ИИВ томонидан', c.passport_full)

    def test_biometrik_pasportda_tuman_majburiy(self):
        """Yashil pasport tanlanib tuman bo'sh qolsa saqlanmaydi."""
        malumot = self._malumot()
        malumot['passport_type'] = HUJJAT_PASPORT
        malumot['passport_org'] = ''
        malumot['passport_district'] = ''
        javob = self.client.post('/shartnoma/yangi/', malumot)
        self.assertEqual(javob.status_code, 200)
        self.assertFalse(Contract.objects.exists())
        self.assertIn('Tumanni kirillcha kiriting', javob.content.decode())

    def test_tuman_qoshimchasi_ozi_qoshiladi(self):
        """«Когон» yozilsa «Когон тумани» bo'lib saqlanadi."""
        malumot = self._malumot()
        malumot['passport_type'] = HUJJAT_PASPORT
        malumot['passport_org'] = ''
        malumot['passport_district'] = 'Когон'
        self.assertEqual(self.client.post('/shartnoma/yangi/', malumot).status_code, 302)
        self.assertEqual(Contract.objects.get().passport_district, 'Когон тумани')

    def test_tuman_lotincha_ham_boladi(self):
        """Lotin harflar ham qabul qilinadi; qo'shimcha lotincha qo'shiladi."""
        malumot = self._malumot()
        malumot['passport_type'] = HUJJAT_PASPORT
        malumot['passport_org'] = ''
        malumot['passport_district'] = 'Kogon'
        self.assertEqual(self.client.post('/shartnoma/yangi/', malumot).status_code, 302)
        self.assertEqual(Contract.objects.get().passport_district, 'Kogon tumani')

    def test_biometrik_pasportda_eski_iiv_raqami_tozalanadi(self):
        """Turi almashtirilsa eski raqam hujjatda qolib ketmasin."""
        malumot = self._malumot()
        malumot['passport_type'] = HUJJAT_PASPORT      # raqam esa yozilib qolgan
        malumot['passport_district'] = 'Когон тумани'
        self.assertEqual(self.client.post('/shartnoma/yangi/', malumot).status_code, 302)
        self.assertEqual(Contract.objects.get().passport_org, '')

    def test_id_kartada_tuman_tozalanadi(self):
        """ID karta tanlansa tuman bo'sh bo'lib qoladi (biometrikdan qolmasin)."""
        malumot = self._malumot()                       # ID karta, IIV raqami bor
        malumot['passport_district'] = 'Когон тумани'    # xatoan yozilib qolgan
        self.assertEqual(self.client.post('/shartnoma/yangi/', malumot).status_code, 302)
        self.assertEqual(Contract.objects.get().passport_district, '')

    def test_id_kartada_iiv_raqami_majburiy(self):
        malumot = self._malumot()
        malumot['passport_org'] = ''
        javob = self.client.post('/shartnoma/yangi/', malumot)
        self.assertEqual(javob.status_code, 200)
        self.assertFalse(Contract.objects.exists())
        self.assertIn('IIV bo‘lim raqamini kiriting', javob.content.decode())

    def test_garovga_qoyuvchi_biometrik_pasporti_iivsiz(self):
        malumot = self._malumot()
        malumot.update(self._garov_beruvchi_malumoti())
        malumot['pledgor_passport_org'] = ''       # yashil pasport tanlangan
        self.assertEqual(self.client.post('/shartnoma/yangi/', malumot).status_code, 302)
        c = Contract.objects.get()
        self.assertEqual(c.pledgor_passport_org, '')
        self.assertIn('Бухоро вилояти Ромитан тумани ИИВ томонидан',
                      c.garov_beruvchi_pasport)

    def test_garovga_qoyuvchi_id_kartasida_iiv_majburiy(self):
        malumot = self._malumot()
        malumot.update(self._garov_beruvchi_malumoti())
        malumot['pledgor_passport_type'] = HUJJAT_ID_KARTA
        malumot['pledgor_passport_org'] = ''
        malumot['pledgor_passport_district'] = ''
        javob = self.client.post('/shartnoma/yangi/', malumot)
        self.assertEqual(javob.status_code, 200)
        self.assertFalse(Contract.objects.exists())

    def test_garovga_qoyuvchi_yarim_toldirilsa_saqlanmaydi(self):
        malumot = self._malumot()
        malumot.update(self._garov_beruvchi_malumoti())
        malumot['pledgor_address'] = ''
        javob = self.client.post('/shartnoma/yangi/', malumot)
        self.assertEqual(javob.status_code, 200)
        self.assertFalse(Contract.objects.exists())

    def test_belgi_qoyilmasa_maydonlar_tozalanadi(self):
        """Belgi olib tashlansa eski shaxs hujjatda qolib ketmaydi."""
        malumot = self._malumot()
        malumot.update(self._garov_beruvchi_malumoti())
        malumot.pop('pledgor_other')
        self.assertEqual(self.client.post('/shartnoma/yangi/', malumot).status_code, 302)
        c = Contract.objects.get()
        self.assertFalse(c.garov_beruvchi_boshqami)
        self.assertEqual(c.pledgor_fio, '')
        self.assertEqual(c.garov_beruvchi_fio, c.borrower_fio)


class RoyxatSahifasiTest(TestCase):
    """Shartnomalar ro'yxatidagi tugmalar."""

    def setUp(self):
        from accounts.models import User
        self.boshliq = User.objects.create_user(
            username='boshliq1', password='x', role=User.ROLE_BOSHLIQ)
        self.ishchi = User.objects.create_user(
            username='ishchi1', password='x', role=User.ROLE_ISHCHI, added_by=self.boshliq)
        sana = date(2026, 8, 5)
        self.c = Contract.objects.create(
            number=301, garov_number=55, date=sana,
            collateral_type=Contract.TYPE_ZARGARLIK,
            borrower_fio='Каримова Нилуфар Аскаровна',
            passport_region='Бухоро вилояти', passport_org='61013',
            passport_date=date(2025, 4, 23), passport_number='АE№2437494',
            borrower_address='Бухоро шахар', borrower_phone='90 123-45-67',
            borrower_phone2='91 222-33-44', borrower_phone3='93 555-66-77',
            borrower_workplace='—', monthly_income=4_000_000, amount=8_000_000,
            term_months=12, interest_rate=60, end_date=contract_end_date(sana, 12),
            garov_value=8_000_000, created_by=self.ishchi)

    def _royxat(self, user):
        self.client.force_login(user)
        javob = self.client.get('/shartnomalar/')
        self.assertEqual(javob.status_code, 200)
        return javob.content.decode()

    def test_boshliqda_ochirish_tugmasi_bor(self):
        matn = self._royxat(self.boshliq)
        self.assertIn(f'/shartnoma/{self.c.pk}/ochirish/', matn)
        self.assertIn('btn-danger', matn)

    def test_ishchida_ochirish_tugmasi_yoq(self):
        """Ishchining o'chirish oqimi ataylab yopiq (qarang: contract_delete)."""
        matn = self._royxat(self.ishchi)
        self.assertNotIn('ochirish', matn)
        self.assertNotIn('btn-danger', matn)

    def test_shablon_izohlari_sahifaga_chiqmaydi(self):
        """`{# #}` ko'p qatorli bo'lolmaydi — izoh matn bo'lib chiqib ketmasin."""
        for user in (self.boshliq, self.ishchi):
            with self.subTest(user=user.username):
                matn = self._royxat(user)
                self.assertNotIn('{#', matn)
                self.assertNotIn('{%', matn)


class SahifalashTest(TestCase):
    """Ro'yxat 10 tadan sahifalarga bo'linadi (xaridor talabi, 2026-08-18)."""

    def setUp(self):
        from accounts.models import User
        self.boshliq = User.objects.create_user(
            username='boshliq2', password='x', role=User.ROLE_BOSHLIQ)
        sana = date(2026, 8, 5)
        # 12 ta shartnoma — 10 + 2 bo'lib ikki sahifaga tushadi
        for raqam in range(401, 413):
            Contract.objects.create(
                number=raqam, date=sana,
                collateral_type=Contract.TYPE_ZARGARLIK,
                borrower_fio='Каримова Нилуфар Аскаровна',
                passport_region='Бухоро вилояти', passport_org='61013',
                passport_date=date(2025, 4, 23), passport_number='АE№2437494',
                borrower_address='Бухоро шахар', amount=8_000_000,
                term_months=12, interest_rate=60,
                end_date=contract_end_date(sana, 12),
                created_by=self.boshliq)

    def _raqamlar(self, manzil):
        self.client.force_login(self.boshliq)
        javob = self.client.get(manzil)
        self.assertEqual(javob.status_code, 200)
        return [int(r) for r in
                re.findall(r'<td><b>(\d+)</b></td>', javob.content.decode())]

    def test_birinchi_sahifada_on_ta(self):
        self.assertEqual(self._raqamlar('/shartnomalar/'),
                         list(range(412, 402, -1)))

    def test_ikkinchi_sahifada_qolgani(self):
        self.assertEqual(self._raqamlar('/shartnomalar/?page=2'), [402, 401])

    def test_tartib_raqam_boyicha_kamayadi(self):
        """410, 409, 408 ... — eng yangisi tepada."""
        raqamlar = self._raqamlar('/shartnomalar/')
        self.assertEqual(raqamlar, sorted(raqamlar, reverse=True))

    def test_yoq_sahifa_soralganda_oxirgisi_beriladi(self):
        """`?page=99` xato bermasin — get_page oxirgi sahifani qaytaradi."""
        self.assertEqual(self._raqamlar('/shartnomalar/?page=99'), [402, 401])

    def test_havolalarda_qidiruv_shartlari_saqlanadi(self):
        self.client.force_login(self.boshliq)
        matn = self.client.get('/shartnomalar/?q=Каримова').content.decode()
        self.assertIn('q=%D0%9A', matn)      # qidiruv so'zi havolada qoladi
        self.assertIn('page=2', matn)


class TolovJadvaliTest(TestCase):
    """Grafik yaxlitlanmaydi — summalar tiyini bilan (xaridor talabi, 2026-08-18)."""

    def setUp(self):
        sana = date(2026, 8, 17)
        self.c = Contract(
            number=168, date=sana, collateral_type=Contract.TYPE_ZARGARLIK,
            borrower_fio='Каюмов Санжар Тошмуродович',
            passport_region='Бухоро вилояти', passport_org='61013',
            passport_date=date(2025, 4, 23), passport_number='АE№2437494',
            borrower_address='Бухоро шахар', amount=4_000_000,
            term_months=12, interest_rate=60,
            end_date=contract_end_date(sana, 12))

    def test_asosiy_qarz_butun_somga_bolinadi(self):
        """Lombard grafigi butun so'mda (xaridor qarori, 2026-08-19)."""
        from .docgen import payment_schedule
        qatorlar = payment_schedule(self.c)
        self.assertEqual(str(qatorlar[0][3]), '333333')
        # bo'linishdan qolgani oxirgi to'lovga qo'shiladi
        self.assertEqual(str(qatorlar[-1][3]), '333337')

    def test_jami_aynan_kredit_summasiga_teng(self):
        """Oxirgi to'lov bo'linishdan qolgan tiyinlarni yopadi."""
        from .docgen import payment_schedule
        jami = sum(q[3] for q in payment_schedule(self.c))
        self.assertEqual(jami, self.c.amount)

    def test_summalar_tiyin_bilan_yoziladi(self):
        """Asosiy qarz butun bo'lsa ham, ustunlar tiyin bilan ko'rsatiladi."""
        from .docgen import payment_schedule
        from .shablondan import _summa_tiyin
        qatorlar = payment_schedule(self.c)
        self.assertEqual(_summa_tiyin(qatorlar[1][5]), '3 666 667,00')   # qoldiq
        self.assertIn(',', _summa_tiyin(qatorlar[0][4]))                 # foiz

    def test_36_oylik_namuna_bilan_mos(self):
        """36 oylik namuna — xaridorning `kk.xml` («тугриси» varag'i, 2026-08-19).

        Shartnoma №162: 9 000 000 so'm, 36 oy, 60%, 13.08.2026, 1-to'lov
        10.09.2026, oxirgisi 12.08.2029. Asosiy qarz aynan 250 000,00 ga
        bo'linadi; quyida har oyning foizi — namunadagi qiymatlar.
        """
        from decimal import Decimal

        from .docgen import contract_end_date, payment_schedule
        kutilgan_foiz = [
        '414246.56', '431506.80', '433150.60', '406849.20',
        '407671.08', '394931.63', '345205.56', '369452.11',
        '345205.50', '343972.59', '320547.90', '318493.07',
        '305753.31', '283561.50', '280274.10', '258904.20',
        '254098.32', '241393.59', '213934.45', '215983.51',
        '196721.40', '190573.74', '172131.00', '165163.97',
        '152458.93', '135246.00', '127049.16', '110655.60',
        '101917.77', '89178.01', '69041.00', '63698.49',
        '49315.20', '38219.28', '24657.60', '13561.68',
        ]
        sana = date(2026, 8, 13)
        c = Contract(number=162, date=sana,
                     end_date=contract_end_date(sana, 36),
                     collateral_type=Contract.TYPE_ZARGARLIK,
                     borrower_fio='Баходуров Камолиддин Дилшод угли',
                     amount=9_000_000, term_months=36, interest_rate=60,
                     payment_start_date=date(2026, 9, 10))
        qatorlar = payment_schedule(c)
        self.assertEqual(len(qatorlar), 36)
        self.assertEqual(qatorlar[-1][1], date(2029, 8, 12))
        for (n, d, jami, asosiy, foiz, qoldiq), kutilgan in zip(qatorlar,
                                                               kutilgan_foiz):
            self.assertEqual(asosiy, Decimal(250_000), f'{n}-qator asosiy')
            self.assertEqual(foiz, Decimal(kutilgan), f'{n}-qator foiz')
            self.assertEqual(jami, asosiy + foiz, f'{n}-qator jami')
        self.assertEqual(sum(q[4] for q in qatorlar), Decimal('8284724.41'))
        self.assertEqual(sum(q[2] for q in qatorlar), Decimal('17284724.41'))

    # ---------------------------------------- lombardning bosma grafigi

    # Xaridor 2026-08-19 da №169 shartnomaning bosma grafigini ko'rsatdi
    # (7 000 000 so'm, 12 oy, 60%, shartnoma 19.08.2026, 1-to'lov 10.09.2026).
    # Bizning hisob o'sha qog'oz bilan tiyingacha mos tushishi kerak — shu
    # yerda o'sha jadval aynan yozib qo'yilgan.
    BOSMA_169 = [
        ('10.09.2026', '7 000 000,00', '583 333,00', '253 150,70', '836 483,70'),
        ('10.10.2026', '6 416 667,00', '583 333,00', '316 438,50', '899 771,50'),
        ('10.11.2026', '5 833 334,00', '583 333,00', '297 260,24', '880 593,24'),
        ('10.12.2026', '5 250 001,00', '583 333,00', '258 904,20', '842 237,20'),
        ('10.01.2027', '4 666 668,00', '583 333,00', '237 808,44', '821 141,44'),
        ('10.02.2027', '4 083 335,00', '583 333,00', '208 082,23', '791 415,23'),
        ('10.03.2027', '3 500 002,00', '583 333,00', '161 096,04', '744 429,04'),
        ('10.04.2027', '2 916 669,00', '583 333,00', '148 630,12', '731 963,12'),
        ('10.05.2027', '2 333 336,00', '583 333,00', '115 068,60', '698 401,60'),
        ('10.06.2027', '1 750 003,00', '583 333,00', '89 178,32', '672 511,32'),
        ('10.07.2027', '1 166 670,00', '583 333,00', '57 534,30', '640 867,30'),
        ('18.08.2027', '583 337,00', '583 337,00', '37 397,49', '620 734,49'),
    ]

    def test_bosma_grafik_bilan_tiyingacha_mos(self):
        from .docgen import contract_end_date, payment_schedule
        from .shablondan import _summa_tiyin
        sana = date(2026, 8, 19)
        c = Contract(number=169, date=sana,
                     end_date=contract_end_date(sana, 12),
                     collateral_type=Contract.TYPE_ZARGARLIK,
                     borrower_fio='Хакназарова Латоф Туймуродовна',
                     amount=7_000_000, term_months=12, interest_rate=60,
                     payment_start_date=date(2026, 9, 10))
        qatorlar = payment_schedule(c)
        self.assertEqual(len(qatorlar), len(self.BOSMA_169))
        for (n, d, jami, asosiy, foiz, qoldiq), kutilgan in zip(qatorlar,
                                                               self.BOSMA_169):
            bizniki = (d.strftime('%d.%m.%Y'), _summa_tiyin(qoldiq),
                       _summa_tiyin(asosiy), _summa_tiyin(foiz),
                       _summa_tiyin(jami))
            self.assertEqual(bizniki, kutilgan, f'{n}-qator')
        self.assertEqual(_summa_tiyin(sum(q[4] for q in qatorlar)),
                         '2 180 549,18')          # jami foiz
        self.assertEqual(_summa_tiyin(sum(q[2] for q in qatorlar)),
                         '9 180 549,18')          # jami umumiy

    # Xaridor 2026-08-24 da №170 shartnomaning bosma grafigini ko'rsatdi
    # (5 000 000 so'm, 12 oy, 60%, shartnoma 24.08.2026, 1-to'lov 10.09.2026).
    # Aynan shu jadval asosiy ulushni PASTGA emas, ENG YAQIN butun so'mga
    # yaxlitlash kerakligini ko'rsatdi: 416 666,67 -> 416 667,00.
    BOSMA_170 = [
        ('10.09.2026', '5 000 000,00', '416 667,00', '139 726,06', '556 393,06'),
        ('10.10.2026', '4 583 333,00', '416 667,00', '226 027,50', '642 694,50'),
        ('10.11.2026', '4 166 666,00', '416 667,00', '212 328,61', '628 995,61'),
        ('10.12.2026', '3 749 999,00', '416 667,00', '184 931,40', '601 598,40'),
        ('10.01.2027', '3 333 332,00', '416 667,00', '169 862,95', '586 529,95'),
        ('10.02.2027', '2 916 665,00', '416 667,00', '148 630,12', '565 297,12'),
        ('10.03.2027', '2 499 998,00', '416 667,00', '115 068,52', '531 735,52'),
        ('10.04.2027', '2 083 331,00', '416 667,00', '106 164,15', '522 831,15'),
        ('10.05.2027', '1 666 664,00', '416 667,00', '82 191,60', '498 858,60'),
        ('10.06.2027', '1 249 997,00', '416 667,00', '63 698,49', '480 365,49'),
        ('10.07.2027', '833 330,00', '416 667,00', '41 095,80', '457 762,80'),
        ('23.08.2027', '416 663,00', '416 663,00', '30 136,92', '446 799,92'),
    ]

    def test_bosma_grafik_170_bilan_tiyingacha_mos(self):
        from .docgen import contract_end_date, payment_schedule
        from .shablondan import _summa_tiyin
        sana = date(2026, 8, 24)
        c = Contract(number=170, date=sana,
                     end_date=contract_end_date(sana, 12),
                     collateral_type=Contract.TYPE_ZARGARLIK,
                     borrower_fio='Муратова Зарина Олимджоновна',
                     amount=5_000_000, term_months=12, interest_rate=60,
                     payment_start_date=date(2026, 9, 10))
        qatorlar = payment_schedule(c)
        self.assertEqual(len(qatorlar), len(self.BOSMA_170))
        for (n, d, jami, asosiy, foiz, qoldiq), kutilgan in zip(qatorlar,
                                                               self.BOSMA_170):
            bizniki = (d.strftime('%d.%m.%Y'), _summa_tiyin(qoldiq),
                       _summa_tiyin(asosiy), _summa_tiyin(foiz),
                       _summa_tiyin(jami))
            self.assertEqual(bizniki, kutilgan, f'{n}-qator')
        self.assertEqual(_summa_tiyin(sum(q[4] for q in qatorlar)),
                         '1 519 862,12')          # jami foiz
        self.assertEqual(_summa_tiyin(sum(q[2] for q in qatorlar)),
                         '6 519 862,12')          # jami umumiy

    def test_asosiy_ulush_eng_yaqin_butun_somga(self):
        """416 666,67 pastga emas, yuqoriga — 416 667,00 (№170, 2026-08-24)."""
        from .docgen import payment_schedule
        c = Contract(number=170, date=date(2026, 8, 24),
                     end_date=contract_end_date(date(2026, 8, 24), 12),
                     collateral_type=Contract.TYPE_ZARGARLIK,
                     borrower_fio='Муратова Зарина Олимджоновна',
                     amount=5_000_000, term_months=12, interest_rate=60,
                     payment_start_date=date(2026, 9, 10))
        qatorlar = payment_schedule(c)
        self.assertEqual(str(qatorlar[0][3]), '416667')
        self.assertEqual(str(qatorlar[-1][3]), '416663')
        self.assertEqual(sum(q[3] for q in qatorlar), c.amount)

    # ------------------------------------------------- ilovaning ko'rinishi

    def _ilova(self):
        """1-ilovani alohida hujjatda yasab, jadvalini qaytaradi."""
        from docx import Document
        from .docgen import payment_schedule
        from .shablondan import tolov_jadvalini_qosh
        doc = Document()
        tolov_jadvalini_qosh(doc, self.c, payment_schedule(self.c))
        return doc

    @staticmethod
    def _katak(jadval, i, j):
        run = jadval.cell(i, j).paragraphs[0].runs[0]
        return (run.font.size.pt, bool(run.bold))

    def test_faqat_summalar_11_pt(self):
        """Xaridor talabi (2026-08-18): FAQAT pul summalari 11 pt.

        Sarlavha qatori, «№» va sana ustunlari, «Жами» so'zi — 12 pt.
        """
        jadval = self._ilova().tables[0]
        for j in range(6):
            self.assertEqual(self._katak(jadval, 0, j), (12.0, True), f'sarlavha {j}')
        self.assertEqual(self._katak(jadval, 1, 0), (12.0, True))      # «№»
        self.assertEqual(self._katak(jadval, 1, 1), (12.0, False))     # sana
        for j in (2, 3, 4, 5):                                          # summalar
            self.assertEqual(self._katak(jadval, 1, j), (11.0, False), f'summa {j}')
        oxirgi = len(jadval.rows) - 1
        self.assertEqual(self._katak(jadval, oxirgi, 1), (12.0, True))  # «Жами»
        for j in (3, 4, 5):
            self.assertEqual(self._katak(jadval, oxirgi, j), (11.0, False), f'jami {j}')

    def test_ustun_enlari_qatiy(self):
        from .shablondan import JADVAL_USTUN_ENLARI
        jadval = self._ilova().tables[0]
        enlar = [round(c.width.cm, 2) for c in jadval.rows[0].cells]
        self.assertEqual(enlar, JADVAL_USTUN_ENLARI)

    def test_xatboshilar_qalin_va_12_pt(self):
        """Ilovadagi barcha yozuvlar qalin, 12 pt (eslatmalar ham)."""
        xatboshilar = [p for p in self._ilova().paragraphs if p.text.strip()]
        self.assertEqual(len(xatboshilar), 11)
        for p in xatboshilar:
            run = p.runs[0]
            self.assertTrue(run.bold, p.text[:40])
            self.assertEqual(run.font.size.pt, 12.0, p.text[:40])

    def test_sarlavha_ikki_qatorda(self):
        matnlar = [p.text.strip() for p in self._ilova().paragraphs if p.text.strip()]
        self.assertTrue(matnlar[1].endswith('-йилдаги'), matnlar[1])
        self.assertTrue(matnlar[2].startswith('№168-сонли'), matnlar[2])


class SanaMaydoniTest(TestCase):
    """`DateInput` — brauzerning sana tanlagichi ISO qiymat kutadi.

    Bu shartnoma formasiga ham tegishli: tuzatishdan oldin bazadagi sanalar
    tahrirlash sahifasida bo'sh ko'rinardi.
    """

    def test_shartnoma_formasida_sanalar_iso(self):
        sana = date(2026, 8, 24)
        c = Contract(number=170, date=sana, end_date=contract_end_date(sana, 12),
                     payment_start_date=date(2026, 9, 10),
                     collateral_type=Contract.TYPE_ZARGARLIK,
                     borrower_fio='Муратова Зарина Олимджоновна',
                     amount=5_000_000, term_months=12, interest_rate=60)
        forma = ContractForm(instance=c)
        self.assertIn('value="2026-08-24"', str(forma['date']))
        self.assertIn('value="2026-09-10"', str(forma['payment_start_date']))
        self.assertIn('value="2027-08-23"', str(forma['end_date']))

    def test_ikkala_korinishdagi_sana_ham_oqiladi(self):
        """ISO ham, `24.08.2026` ham qabul qilinaveradi."""
        from .forms import GrafikFormasi
        for yozuv in ('2026-08-24', '24.08.2026'):
            with self.subTest(yozuv=yozuv):
                forma = GrafikFormasi({'amount': '5 000 000', 'interest_rate': '60',
                                       'date': yozuv, 'term_months': '12'})
                self.assertTrue(forma.is_valid(), forma.errors)
                self.assertEqual(forma.cleaned_data['date'], date(2026, 8, 24))


class GrafikSahifasiTest(TestCase):
    """«Grafik» bo'limi — shartnoma tuzmasdan to'lov jadvalini hisoblash."""

    SORAV = {'amount': '5 000 000', 'interest_rate': '60',
             'date': '2026-08-24', 'term_months': '12'}

    def setUp(self):
        from accounts.models import User
        self.ishchi = User.objects.create_user(
            username='grafikchi', password='ishchi123', role=User.ROLE_ISHCHI)
        self.client.force_login(self.ishchi)

    def test_kirmagan_foydalanuvchi_kiritilmaydi(self):
        self.client.logout()
        javob = self.client.get('/grafik/')
        self.assertEqual(javob.status_code, 302)
        self.assertIn('/kirish/', javob['Location'])

    def test_bosh_sahifada_forma_chiqadi_jadval_chiqmaydi(self):
        javob = self.client.get('/grafik/')
        self.assertEqual(javob.status_code, 200)
        self.assertIsNone(javob.context['natija'])
        self.assertContains(javob, 'Hisoblash')

    def test_menyuda_havola_bor(self):
        javob = self.client.get('/grafik/')
        self.assertContains(javob, 'href="/grafik/"')

    def test_hisob_bosma_grafik_bilan_bir_xil(self):
        """Kalkulyator natijasi №170 bosma ilovasi bilan tiyingacha mos."""
        from .shablondan import _summa_tiyin
        javob = self.client.get('/grafik/', self.SORAV)
        self.assertEqual(javob.status_code, 200)
        qatorlar = javob.context['natija']['qatorlar']
        self.assertEqual(len(qatorlar), 12)
        for (n, d, jami, asosiy, foiz, qoldiq), kutilgan in zip(
                qatorlar, TolovJadvaliTest.BOSMA_170):
            bizniki = (d.strftime('%d.%m.%Y'), _summa_tiyin(qoldiq),
                       _summa_tiyin(asosiy), _summa_tiyin(foiz),
                       _summa_tiyin(jami))
            self.assertEqual(bizniki, kutilgan, f'{n}-qator')

    def test_yakuniy_summalar(self):
        from .shablondan import _summa_tiyin
        natija = self.client.get('/grafik/', self.SORAV).context['natija']
        self.assertEqual(_summa_tiyin(natija['jami_asosiy']), '5 000 000,00')
        self.assertEqual(_summa_tiyin(natija['jami_foiz']), '1 519 862,12')
        self.assertEqual(_summa_tiyin(natija['jami']), '6 519 862,12')

    def test_sanalar_bosh_qolsa_shartnomadagidek_hisoblanadi(self):
        """1-to'lov — keyingi oyning 10-si, oxirgisi — muddat tugagan kun."""
        natija = self.client.get('/grafik/', self.SORAV).context['natija']
        c = natija['contract']
        self.assertEqual(c.payment_start_date, date(2026, 9, 10))
        self.assertEqual(c.end_date, date(2027, 8, 23))

    def test_qolga_kiritilgan_sanalar_ustun_turadi(self):
        sorov = dict(self.SORAV, payment_start_date='2026-09-05',
                     end_date='2027-08-20')
        natija = self.client.get('/grafik/', sorov).context['natija']
        qatorlar = natija['qatorlar']
        self.assertEqual(qatorlar[0][1], date(2026, 9, 5))
        self.assertEqual(qatorlar[-1][1], date(2027, 8, 20))

    def test_summa_bosliq_bilan_yozilsa_ham_qabul_qilinadi(self):
        """«5 000 000» ham, «5000000» ham bir xil natija beradi."""
        a = self.client.get('/grafik/', self.SORAV).context['natija']
        b = self.client.get('/grafik/', dict(self.SORAV, amount='5000000'))
        self.assertEqual(a['jami'], b.context['natija']['jami'])

    def test_birinchi_tolov_shartnomadan_oldin_bolsa_xato(self):
        sorov = dict(self.SORAV, payment_start_date='2026-08-20')
        javob = self.client.get('/grafik/', sorov)
        self.assertIsNone(javob.context['natija'])
        self.assertIn('payment_start_date', javob.context['form'].errors)

    def test_oxirgi_tolov_oldingisidan_oldin_bolsa_xato(self):
        sorov = dict(self.SORAV, end_date='2027-01-01')
        javob = self.client.get('/grafik/', sorov)
        self.assertIsNone(javob.context['natija'])
        self.assertIn('end_date', javob.context['form'].errors)

    def test_toldirilmagan_forma_jadval_bermaydi(self):
        javob = self.client.get('/grafik/', {'amount': '5000000'})
        self.assertEqual(javob.status_code, 200)
        self.assertIsNone(javob.context['natija'])

    def test_manfiy_summa_qabul_qilinmaydi(self):
        javob = self.client.get('/grafik/', dict(self.SORAV, amount='0'))
        self.assertIsNone(javob.context['natija'])
        self.assertIn('amount', javob.context['form'].errors)

    # ------------------------------------------------------ maydonlarning ko'rinishi

    def test_sana_maydoni_iso_korinishida_chiqadi(self):
        """`<input type="date">` faqat ISO qiymatni o'qiydi.

        `LANGUAGE_CODE = 'uz'` da Django `24.08.2026` deb yozardi — brauzer
        bunday qiymatni tushunmay, maydonni bo'sh ko'rsatardi.
        """
        javob = self.client.get('/grafik/', self.SORAV)
        self.assertContains(javob, 'name="date" value="2026-08-24"')

    def test_bosh_formada_bugungi_sana_turadi(self):
        from django.utils import timezone
        javob = self.client.get('/grafik/')
        bugun = timezone.localdate().strftime('%Y-%m-%d')
        self.assertContains(javob, f'name="date" value="{bugun}"')

    def test_summa_maydoni_pul_klassi_bilan(self):
        """`pul` klassi bo'lgani uchun raqamlar yozilayotganda bo'linadi."""
        javob = self.client.get('/grafik/')
        self.assertContains(javob, 'class="form-control pul"')

    def test_pul_js_sahifaga_ulangan(self):
        javob = self.client.get('/grafik/')
        self.assertContains(javob, 'js/pul.js')

    # ------------------------------------------------------ Word yuklamasi

    def test_word_yuklanadi(self):
        sorov = dict(self.SORAV, borrower_fio='Муратова Зарина Олимджоновна',
                     number='170')
        javob = self.client.get('/grafik/word/', sorov)
        self.assertEqual(javob.status_code, 200)
        self.assertIn('wordprocessingml', javob['Content-Type'])
        self.assertIn('grafik_170.docx', javob['Content-Disposition'])

    def test_word_jadvali_sahifadagi_bilan_bir_xil(self):
        from .shablondan import _summa_tiyin
        sorov = dict(self.SORAV, borrower_fio='Муратова Зарина Олимджоновна',
                     number='170')
        javob = self.client.get('/grafik/word/', sorov)
        doc = Document(io.BytesIO(javob.content))
        jadval = doc.tables[0]
        # sarlavha + 12 qator + «Жами»
        self.assertEqual(len(jadval.rows), 14)
        for i, kutilgan in enumerate(TolovJadvaliTest.BOSMA_170, start=1):
            qator = tuple(jadval.cell(i, j).text for j in range(1, 6))
            self.assertEqual(qator, kutilgan, f'{i}-qator')
        self.assertEqual(jadval.cell(13, 1).text, 'Жами')
        self.assertEqual(jadval.cell(13, 5).text, _summa_tiyin(6519862.12))

    def test_word_bosh_sahifadan_boshlanmaydi(self):
        """Alohida hujjatda oldida bo'sh sahifa bo'lmaydi."""
        javob = self.client.get('/grafik/word/', self.SORAV)
        doc = Document(io.BytesIO(javob.content))
        self.assertNotIn('w:br', doc.paragraphs[0]._p.xml)

    def test_word_malumotsiz_grafikka_qaytaradi(self):
        javob = self.client.get('/grafik/word/')
        self.assertEqual(javob.status_code, 302)
        self.assertIn('/grafik/', javob['Location'])


class TelefonFormatiTest(TestCase):
    """Telefon raqami turlicha yozilsa ham bir ko'rinishga keltiriladi."""

    def _tozala(self, qiymat):
        forma = ContractForm(data={'borrower_phone': qiymat})
        forma.is_valid()          # boshqa maydonlar xato bo'lsa ham bunisi tozalanadi
        return forma.cleaned_data.get('borrower_phone')

    def test_turli_korinishlar(self):
        for kiritilgan in ['914150087', '91 415 00 87', '+998914150087',
                           '+998 (91) 415-00-87', '91-415-00-87']:
            with self.subTest(kiritilgan=kiritilgan):
                self.assertEqual(self._tozala(kiritilgan), '91 415-00-87')

    def test_qisqa_raqam_qabul_qilinmaydi(self):
        forma = ContractForm(data={'borrower_phone': '12345'})
        forma.is_valid()
        self.assertIn('borrower_phone', forma.errors)

    def test_boshqa_format_ozgarmaydi(self):
        self.assertEqual(self._tozala('8 (495) 123-45-67'), '8 (495) 123-45-67')

