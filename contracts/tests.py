# -*- coding: utf-8 -*-
"""Hujjat yasash va forma tekshiruvlari."""
import io
import re
from datetime import date

from django.conf import settings
from django.test import TestCase

from docx import Document
from docx.oxml.ns import qn

from .docgen import contract_end_date
from .forms import ContractForm
from .models import (HUJJAT_ID_KARTA, HUJJAT_PASPORT, Contract, GuarantorInfo,
                     JewelryItem, VehicleInfo)
from .shablondan import hujjat_yasa


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
        c = self._shartnoma(Contract.TYPE_ZARGARLIK, garov_value=9_000_000,
                            garov_number=55)
        JewelryItem.objects.create(contract=c, name='Тилла узук', quantity=1,
                                   weight=3, proba='585', value=4_000_000)
        JewelryItem.objects.create(contract=c, name='Тилла халка', quantity=2,
                                   weight='4.5', proba='585', value=5_000_000)
        return c

    def transport(self):
        c = self._shartnoma(Contract.TYPE_TRANSPORT, garov_value=90_000_000,
                            garov_number=55)
        VehicleInfo.objects.create(
            contract=c, owner='“Test Trans” МЧЖ', owner_head='Азизов Акмал Шухратович',
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

    def test_muqova_toplamning_birinchi_sahifasi(self):
        c = self.zargarlik()
        matn = hujjat_matni(hujjat_yasa(c, qism='hammasi'))
        self.assertIn('Кредит №', matn)
        self.assertIn('Сана / Муддати', matn)
        self.assertIn('8 000 000,00', matn)
        self.assertIn('Заргарлик буюмлари', matn)
        self.assertIn('Бухоро шаҳри 2026 йил', matn)
        # Muqova shartnomadan oldin turishi kerak
        self.assertLess(matn.index('Кредит №'),
                        matn.index('Микрокарз шартномаси'))

    def test_muqovada_garov_turi_yoziladi(self):
        for yasovchi, kutilgan in ((self.zargarlik, 'Заргарлик буюмлари'),
                                   (self.transport, 'Транспорт воситаси'),
                                   (self.kafillik, 'Иш хаки кафиллиги')):
            with self.subTest(tur=yasovchi.__name__):
                c = yasovchi()
                matn = hujjat_matni(hujjat_yasa(c, qism='hammasi'))
                self.assertIn(kutilgan, matn)
                Contract.objects.all().delete()

    def test_garov_shartnomasi_oz_raqamida(self):
        """Garov shartnomasi alohida raqamda, qolgan hujjatlar asosiy raqamda."""
        c = self.zargarlik()
        matn = re.sub(r'\s+', ' ', hujjat_matni(hujjat_yasa(c, qism='hammasi')))
        for ibora in ('Микрокарз шартномаси №301', '№301-сонли',
                      'далолатномаси №301', 'БАЁНИ №301', 'ФАРМОЙИШ №301'):
            self.assertIn(ibora, matn)
        self.assertIn('Гаров шартнома 55', matn)
        self.assertNotIn('Гаров шартнома 301', matn)

    def test_garov_raqami_yoq_bolsa_asosiysi_ishlatiladi(self):
        """Eski shartnomalarda garov raqami yo'q — hujjat baribir chiqadi."""
        c = self.zargarlik()
        Contract.objects.filter(pk=c.pk).update(garov_number=None)
        c.refresh_from_db()
        matn = re.sub(r'\s+', ' ', hujjat_matni(hujjat_yasa(c, qism='hammasi')))
        self.assertIn('Гаров шартнома 301', matn)

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


class FormaSahifasiTest(TestCase):
    """«Yangi shartnoma» formasida telefon va daromad maydonlari bor."""

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

    def _malumot(self, telefonsiz=False):
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
        }
        if telefonsiz:
            malumot['borrower_phone'] = ''
        return malumot

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
        malumot['garov_number'] = '42'
        self.assertEqual(self.client.post('/shartnoma/yangi/', malumot).status_code, 302)
        c = Contract.objects.get()
        self.assertEqual(c.number, 777)
        self.assertEqual(c.garov_number, 42)

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
                        .values_list('number', 'garov_number'))
        self.assertEqual(raqamlar, [(settings.CONTRACT_START_NUMBER,
                                     settings.GAROV_START_NUMBER),
                                    (settings.CONTRACT_START_NUMBER + 1,
                                     settings.GAROV_START_NUMBER + 1)])

    def test_kafillikda_garov_raqami_bolmaydi(self):
        malumot = {k: v for k, v in self._malumot().items()
                   if not k.startswith('jewelry')}
        malumot['collateral_type'] = Contract.TYPE_KAFILLIK
        malumot['garov_number'] = '42'
        malumot.update({'guarantor-fio': 'Салимов Жасур Анварович',
                        'guarantor-amount': '6 000 000'})
        self.assertEqual(self.client.post('/shartnoma/yangi/', malumot).status_code, 302)
        self.assertIsNone(Contract.objects.get().garov_number)

    # ------------------------------------------------------ garovga qo'yuvchi

    def _garov_beruvchi_malumoti(self):
        return {
            'pledgor_other': 'on',
            'pledgor_fio': 'Юсупова Гулнора Рахимовна',
            'pledgor_passport_type': HUJJAT_PASPORT,
            'pledgor_passport_region': 'Бухоро вилояти',
            'pledgor_passport_org': '61020',
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
        """Yashil pasport tanlansa IIV maydoni bo'sh bo'lsa ham saqlanadi."""
        malumot = self._malumot()
        malumot['passport_type'] = HUJJAT_PASPORT
        malumot['passport_org'] = ''
        self.assertEqual(self.client.post('/shartnoma/yangi/', malumot).status_code, 302)
        self.assertEqual(Contract.objects.get().passport_org, '')

    def test_biometrik_pasportda_eski_iiv_raqami_tozalanadi(self):
        """Turi almashtirilsa eski raqam hujjatda qolib ketmasin."""
        malumot = self._malumot()
        malumot['passport_type'] = HUJJAT_PASPORT      # raqam esa yozilib qolgan
        self.assertEqual(self.client.post('/shartnoma/yangi/', malumot).status_code, 302)
        self.assertEqual(Contract.objects.get().passport_org, '')

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
        self.assertIn('Бухоро вилояти ИИВ томонидан', c.garov_beruvchi_pasport)

    def test_garovga_qoyuvchi_id_kartasida_iiv_majburiy(self):
        malumot = self._malumot()
        malumot.update(self._garov_beruvchi_malumoti())
        malumot['pledgor_passport_type'] = HUJJAT_ID_KARTA
        malumot['pledgor_passport_org'] = ''
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

