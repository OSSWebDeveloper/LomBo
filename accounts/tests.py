# -*- coding: utf-8 -*-
"""Hisob-rol tekshiruvlari va o'rnatishdagi `boshlangich` buyrug'i."""
import tempfile
from io import StringIO
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings

User = get_user_model()


class BoshlangichTest(TestCase):
    """ORNATISH.bat birinchi o'rnatishda shu buyruqni chaqiradi."""

    def setUp(self):
        self.papka = Path(tempfile.mkdtemp(prefix='lombard-test-kalit-'))

    def bajar(self, *argv):
        chiqish = StringIO()
        with override_settings(BASE_DIR=self.papka):
            call_command('boshlangich', *argv, stdout=chiqish)
        return chiqish.getvalue()

    def test_kalit_yaratiladi_va_saqlanib_qoladi(self):
        self.bajar()
        kalit_fayl = self.papka / '.secret_key'
        kalit = kalit_fayl.read_text(encoding='utf-8')
        self.assertTrue(kalit.strip())

        # Ikkinchi chaqiruv kalitni almashtirib yubormasligi kerak — aks holda
        # yangilangandan keyin hamma sessiya uzilib ketardi.
        self.bajar()
        self.assertEqual(kalit_fayl.read_text(encoding='utf-8'), kalit)

    def test_birinchi_hisob_boshliq_boladi(self):
        self.bajar()
        boshliq = User.objects.get(username='boshliq')
        self.assertEqual(boshliq.role, User.ROLE_BOSHLIQ)
        self.assertTrue(boshliq.sayt_foydalanuvchisi)
        self.assertTrue(boshliq.can_full_edit)
        self.assertTrue(boshliq.can_edit_template)
        self.assertTrue(boshliq.check_password('boshliq'))

    def test_mavjud_hisoblarga_tegilmaydi(self):
        User.objects.create_user(username='boshliq', password='maxfiy-parol',
                                 role=User.ROLE_BOSHLIQ)
        chiqish = self.bajar()

        self.assertEqual(User.objects.count(), 1)
        self.assertTrue(User.objects.get(username='boshliq').check_password('maxfiy-parol'))
        self.assertIn('boshliq', chiqish)

    def test_admin_bayrogi_panel_hisobini_ochadi(self):
        self.bajar('--admin')
        admin = User.objects.get(username='superuser')
        self.assertTrue(admin.is_superuser)
        # Admin panel hisobi saytga kirmaydi — rollar aralashib ketmasin.
        self.assertFalse(admin.sayt_foydalanuvchisi)

    def test_boshqa_login_va_parol_berish_mumkin(self):
        self.bajar('--login', 'rahbar', '--parol', 'Kuchli!parol9')
        rahbar = User.objects.get(username='rahbar')
        self.assertTrue(rahbar.check_password('Kuchli!parol9'))


class VersiyaTest(TestCase):
    """`versiya.txt` — yagona manba: sayt ham, o'rnatuvchi ham shuni o'qiydi."""

    def test_sozlamadagi_versiya_fayldan_olinadi(self):
        from django.conf import settings
        fayl = settings.BASE_DIR / 'versiya.txt'
        self.assertEqual(settings.VERSIYA, fayl.read_text(encoding='utf-8').strip())

    def test_versiya_sahifa_pastida_korinadi(self):
        from django.conf import settings
        User.objects.create_user(username='boshliq1', password='sinov-parol',
                                 role=User.ROLE_BOSHLIQ)
        self.client.login(username='boshliq1', password='sinov-parol')
        javob = self.client.get('/')
        self.assertContains(javob, settings.VERSIYA)

    def test_versiya_raqamlari_solishtiriladi(self):
        import versiya
        self.assertGreater(versiya.raqamlar('1.10.0'), versiya.raqamlar('1.9.9'))
        self.assertGreater(versiya.raqamlar('2.0.0'), versiya.raqamlar('1.99.99'))

    def test_notogri_versiya_shakli_rad_etiladi(self):
        import versiya
        for yaroqli in ('1.0.0', '10.2.35'):
            self.assertTrue(versiya.KOLIP.match(yaroqli))
        for yaroqsiz in ('1.0', 'v1.0.0', '1.0.0-beta', 'bir'):
            self.assertFalse(versiya.KOLIP.match(yaroqsiz))

    def test_tarixga_yangi_yozuv_tepaga_qoshiladi(self):
        import tempfile
        import versiya
        from pathlib import Path
        eski_fayl = versiya.TARIX_FAYL
        vaqt = Path(tempfile.mkdtemp(prefix='versiya-test-')) / 'VERSIYALAR.md'
        vaqt.write_text('# Versiyalar tarixi\n\n## 1.0.0 — 2026-01-01\n\nEski.\n',
                        encoding='utf-8')
        versiya.TARIX_FAYL = vaqt
        try:
            versiya.tarixga_yoz('1.1.0', 'Yangi narsa')
        finally:
            versiya.TARIX_FAYL = eski_fayl
        matn = vaqt.read_text(encoding='utf-8')
        self.assertLess(matn.index('1.1.0'), matn.index('1.0.0'))
        self.assertIn('Yangi narsa', matn)
