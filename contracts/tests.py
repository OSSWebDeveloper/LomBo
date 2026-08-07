# -*- coding: utf-8 -*-
"""Hujjat yasash va forma tekshiruvlari."""
import io
import re
from datetime import date

from django.test import TestCase

from docx import Document
from docx.oxml.ns import qn

from .docgen import contract_end_date
from .forms import ContractForm
from .models import Contract, GuarantorInfo, JewelryItem, VehicleInfo
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
            borrower_phone3='93 555-66-77', monthly_income=4_000_000,
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

    def test_hamma_hujjat_bitta_raqam_bilan(self):
        """Shartnoma, garov, dalolatnoma, bayon va farmoyish — bir xil raqamda."""
        c = self.zargarlik()
        matn = re.sub(r'\s+', ' ', hujjat_matni(hujjat_yasa(c, qism='hammasi')))
        for ibora in ('Микрокарз шартномаси №301', 'Гаров шартнома 301',
                      '№301-сонли', 'далолатномаси №301', 'БАЁНИ №301',
                      'ФАРМОЙИШ №301'):
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
            'passport_region': 'Бухоро вилояти', 'passport_org': '61013',
            'passport_date': '2025-04-23', 'passport_number': 'АE№2437494',
            'borrower_address': 'Бухоро шахар, Навоий кўчаси, 5-уй',
            'borrower_phone': '901234567', 'borrower_phone2': '912223344',
            'borrower_phone3': '935556677', 'monthly_income': '4 000 000',
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
