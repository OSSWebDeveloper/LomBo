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


from django.urls import reverse  # noqa: E402


@override_settings(LOMBARD_BOSS_IP=['198.163.193.78'], LOMBARD_ISHCHI_KIRISHI=False)
class KirishChekloviTest(TestCase):
    """Ishchi kira olmaydi (jim rad), boshliq faqat ruxsat etilgan IP dan kiradi."""
    PAROL = 'sinov-parol-123'
    BOSS_IP = '198.163.193.78'

    def setUp(self):
        self.url = reverse('login')
        self.boshliq = User.objects.create_user(
            username='boss1', password=self.PAROL, role=User.ROLE_BOSHLIQ)
        self.ishchi = User.objects.create_user(
            username='worker1', password=self.PAROL, role=User.ROLE_ISHCHI)

    def kir(self, username, ip=None, **extra):
        if ip:
            extra['HTTP_X_FORWARDED_FOR'] = ip
        return self.client.post(
            self.url, {'username': username, 'password': self.PAROL}, **extra)

    def kirganmi(self):
        return '_auth_user_id' in self.client.session

    # --- Ishchi ---
    def test_ishchi_jim_rad(self):
        r = self.kir('worker1', ip=self.BOSS_IP)
        self.assertEqual(r.status_code, 302)                 # qayta kirish sahifasiga
        self.assertEqual(r.url, self.url)
        self.assertFalse(self.kirganmi())

    def test_ishchi_rad_etilganda_xabar_yoq(self):
        """Hech qanday visual ta'sir bo'lmasin — redirectdan keyin sahifada xato yo'q."""
        r = self.client.post(self.url, {'username': 'worker1', 'password': self.PAROL},
                             follow=True, HTTP_X_FORWARDED_FOR=self.BOSS_IP)
        self.assertNotContains(r, 'noto', status_code=200)   # «noto'g'ri» chiqmaydi
        self.assertNotContains(r, 'xato')
        self.assertFalse(self.kirganmi())

    @override_settings(LOMBARD_ISHCHI_KIRISHI=True)
    def test_ishchi_qayta_yoqilsa_kiradi(self):
        self.assertFalse(self.kirganmi())
        self.kir('worker1', ip=self.BOSS_IP)
        self.assertTrue(self.kirganmi())

    # --- Boshliq ---
    def test_boshliq_ruxsat_ip_dan_kiradi(self):
        self.kir('boss1', ip=self.BOSS_IP)
        self.assertTrue(self.kirganmi())

    def test_boshliq_boshqa_ip_dan_jim_rad(self):
        r = self.kir('boss1', ip='5.6.7.8')
        self.assertEqual(r.status_code, 302)
        self.assertFalse(self.kirganmi())

    def test_boshliq_xff_birinchi_ip_hisobga_olinadi(self):
        # Proksi zanjiri: haqiqiy mijoz — birinchi IP
        self.kir('boss1', ip=f'{self.BOSS_IP}, 10.0.0.1')
        self.assertTrue(self.kirganmi())

    @override_settings(LOMBARD_BOSS_IP=[])
    def test_boss_ip_bosh_bolsa_hamma_ip_dan_kiradi(self):
        self.kir('boss1', ip='5.6.7.8')
        self.assertTrue(self.kirganmi())

    def test_notogri_parol_odatdagidek(self):
        # Noto'g'ri parol — bu cheklov emas, odatdagi xato ko'rinadi
        r = self.client.post(self.url, {'username': 'boss1', 'password': 'boshqa'},
                             HTTP_X_FORWARDED_FOR=self.BOSS_IP)
        self.assertEqual(r.status_code, 200)
        self.assertFalse(self.kirganmi())

    # --- Ochiq sessiya: cheklov qo'yilguncha kirgan hisob (middleware) ---
    # form_valid faqat yangi login paytida ishlaydi; cheklovdan OLDIN kirgan
    # hisobning sessiyasi esa amal qilaverardi. Shu teshikni middleware yopadi:
    # har so'rovda tekshirib, ruxsatsiz hisobni jimgina chiqaradi.
    def test_ochiq_sessiyali_ishchi_chiqariladi(self):
        self.client.force_login(self.ishchi)      # login view'ni chetlab sessiya ochish
        self.assertTrue(self.kirganmi())
        r = self.client.get('/', HTTP_X_FORWARDED_FOR=self.BOSS_IP)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.url, self.url)
        self.assertFalse(self.kirganmi())          # sessiya uzildi — kira olmaydi

    def test_ochiq_sessiyali_boshliq_notogri_ip_chiqariladi(self):
        self.client.force_login(self.boshliq)
        r = self.client.get('/', HTTP_X_FORWARDED_FOR='5.6.7.8')
        self.assertEqual(r.status_code, 302)
        self.assertFalse(self.kirganmi())

    def test_ochiq_sessiyali_boshliq_togri_ip_qoladi(self):
        self.client.force_login(self.boshliq)
        r = self.client.get('/', HTTP_X_FORWARDED_FOR=self.BOSS_IP)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(self.kirganmi())


@override_settings(LOMBARD_BOSS_IP=['198.163.193.78'], LOMBARD_ISHCHI_KIRISHI=False)
class KirishJurnaliTest(TestCase):
    """Har kirish urinishi KirishUrinishi jurnaliga yoziladi; stats --ishchi ko'rsatadi."""
    PAROL = 'sinov-parol-123'
    BOSS_IP = '198.163.193.78'

    def setUp(self):
        from django.urls import reverse
        self.url = reverse('login')
        self.boshliq = User.objects.create_user(
            username='boss1', password=self.PAROL, role=User.ROLE_BOSHLIQ)
        self.ishchi = User.objects.create_user(
            username='worker1', password=self.PAROL, role=User.ROLE_ISHCHI,
            first_name='Ali', last_name='Valiyev')

    def post(self, username, password, ip):
        return self.client.post(self.url, {'username': username, 'password': password},
                                HTTP_X_FORWARDED_FOR=ip)

    def test_ishchi_rad_urinishi_yoziladi(self):
        from panel.models import KirishUrinishi
        self.post('worker1', self.PAROL, '77.88.99.11')
        u = KirishUrinishi.objects.get()
        self.assertEqual(u.login, 'worker1')
        self.assertEqual(u.natija, KirishUrinishi.ISHCHI)
        self.assertEqual(u.ip, '77.88.99.11')

    def test_boshliq_kirdi_yoziladi(self):
        from panel.models import KirishUrinishi
        self.post('boss1', self.PAROL, self.BOSS_IP)
        u = KirishUrinishi.objects.get()
        self.assertEqual(u.natija, KirishUrinishi.KIRDI)

    def test_boshliq_notogri_ip_rad_yoziladi(self):
        from panel.models import KirishUrinishi
        self.post('boss1', self.PAROL, '5.6.7.8')
        self.assertEqual(KirishUrinishi.objects.get().natija, KirishUrinishi.IP)

    def test_notogri_parol_yoziladi(self):
        from panel.models import KirishUrinishi
        self.post('worker1', 'boshqa-parol', '1.2.3.4')
        u = KirishUrinishi.objects.get()
        self.assertEqual(u.login, 'worker1')
        self.assertEqual(u.natija, KirishUrinishi.PAROL)

    def test_stats_ishchi_ip_ni_korsatadi(self):
        from panel.statistika import ishchilar
        self.post('worker1', self.PAROL, '77.88.99.11')   # rad
        self.post('worker1', self.PAROL, '77.88.99.11')   # yana rad
        matn = ishchilar()
        self.assertIn('worker1', matn)
        self.assertIn('Ali Valiyev', matn)
        self.assertIn('77.88.99.11', matn)
