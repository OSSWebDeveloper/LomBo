# -*- coding: utf-8 -*-
"""Ichki panel testlari — asosan xavfsizlik: login majburiy, papkadan
tashqariga chiqib bo'lmaydi, upload/download faqat PANEL_ROOT ichida.

Diqqat: bu yerdagi parol — shunchaki sinov qiymati, haqiqiy parol emas."""
import contextlib
import io
import shlex
import shutil
import sqlite3
import tempfile
import time
import zipfile
from pathlib import Path

import bazani_ol

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

User = get_user_model()

SINOV_PAROL = 'sinov-parol-123'


class PanelBaza(TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='panel_test_'))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self._ctx = override_settings(PANEL_ROOT=self.root)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)
        self.url_index = reverse('panel_index')
        self.url_run = reverse('panel_run')
        self.url_upload = reverse('panel_upload')
        self.url_download = reverse('panel_download')
        self.ega = User.objects.create_superuser(
            username='ega_test', password=SINOV_PAROL, email='')
        self.ishchi = User.objects.create_user(
            username='ishchi1', password='ishchi123', role='ishchi')

    def run_cmd(self, matn):
        return self.client.post(self.url_run, {'command': matn})

    def login_ega(self):
        r = self.run_cmd(f'login --username ega_test --password {SINOV_PAROL}')
        self.assertIn('Xush kelibsiz', r.json()['output'])


class LoginTest(PanelBaza):
    def test_login_qilinmasa_buyruq_ishlamaydi(self):
        self.assertIn('Avval login qiling', self.run_cmd('ls').json()['output'])

    def test_notogri_parol_rad(self):
        r = self.run_cmd('login --username ega_test --password boshqa-narsa')
        self.assertIn("noto'g'ri", r.json()['output'])
        self.assertNotIn('p_uid', self.client.session)

    def test_togri_parol_kiritadi(self):
        self.login_ega()
        self.assertIn('p_uid', self.client.session)
        self.assertEqual(self.run_cmd('whoami').json()['output'], 'ega_test')

    def test_oddiy_foydalanuvchi_superuser_emas_kira_olmaydi(self):
        r = self.run_cmd('login --username ishchi1 --password ishchi123')
        self.assertIn("noto'g'ri", r.json()['output'])
        self.assertNotIn('p_uid', self.client.session)

    def test_help_yoq(self):
        """`help` buyrug'i yo'q — noma'lum buyruq sifatida qaraladi."""
        self.login_ega()
        self.assertIn("Noma'lum buyruq", self.run_cmd('help').json()['output'])

    def test_logout(self):
        self.login_ega()
        self.run_cmd('logout')
        self.assertNotIn('p_uid', self.client.session)

    def test_harakatsizlik_timeout_chiqaradi(self):
        """Oxirgi faoliyatdan beri PANEL_IDLE_TIMEOUT o'tsa — chiqadi."""
        self.login_ega()
        s = self.client.session
        s['p_seen'] = time.time() - 10000      # ancha oldin (timeout o'tgan)
        s.save()
        r = self.run_cmd('ls')
        self.assertIn('Avval login qiling', r.json()['output'])
        self.assertNotIn('p_uid', self.client.session)

    def test_faoliyat_ichida_kirgan_qoladi(self):
        """Timeout ichida buyruq bersa — kirgan holatда qoladi."""
        self.login_ega()
        self.assertEqual(self.run_cmd('whoami').json()['output'], 'ega_test')
        self.assertEqual(self.run_cmd('whoami').json()['output'], 'ega_test')


class FaylTest(PanelBaza):
    def test_upload_saqlaydi(self):
        self.login_ega()
        fayl = SimpleUploadedFile('hisobot.txt', b'salom dunyo')
        r = self.client.post(self.url_upload, {'file': fayl})
        self.assertIn('Yuklandi', r.json()['output'])
        self.assertTrue((self.root / 'hisobot.txt').exists())

    def test_upload_login_talab_qiladi(self):
        fayl = SimpleUploadedFile('x.txt', b'x')
        r = self.client.post(self.url_upload, {'file': fayl})
        self.assertEqual(r.status_code, 403)
        self.assertFalse((self.root / 'x.txt').exists())

    def test_download_file(self):
        (self.root / 'hujjat.txt').write_text('mazmun', encoding='utf-8')
        self.login_ega()
        url = self.run_cmd("download --file 'hujjat.txt'").json()['action']['download']
        yuk = self.client.get(url)
        self.assertEqual(yuk.status_code, 200)
        self.assertEqual(b''.join(yuk.streaming_content), 'mazmun'.encode())

    def test_download_all_zip(self):
        (self.root / 'a.txt').write_text('a', encoding='utf-8')
        self.login_ega()
        url = self.run_cmd('download --all').json()['action']['download']
        yuk = self.client.get(url)
        self.assertEqual(yuk.status_code, 200)
        self.assertEqual(yuk['Content-Type'], 'application/zip')

    def test_papkadan_tashqariga_chiqib_bolmaydi(self):
        """Papka tashqarisidagi faylga `..` orqali murojaat bloklanadi."""
        tashqi = self.root.parent / 'tashqaridagi_fayl.txt'
        tashqi.write_text('maxfiy', encoding='utf-8')
        self.addCleanup(tashqi.unlink, missing_ok=True)
        self.login_ega()
        r = self.run_cmd("download --file '../tashqaridagi_fayl.txt'")
        self.assertIn('topilmadi', r.json()['output'])
        self.assertIsNone(r.json()['action'])

    def test_download_endpoint_login_talab_qiladi(self):
        (self.root / 'fayl.txt').write_text('x', encoding='utf-8')
        r = self.client.get(reverse('panel_download') + '?file=fayl.txt')
        self.assertEqual(r.status_code, 404)

    def test_tashqariga_chiqish_endpointda_ham_bloklanadi(self):
        self.login_ega()
        r = self.client.get(reverse('panel_download') + '?file=../tashqaridagi_fayl.txt')
        self.assertEqual(r.status_code, 404)


class NavigatsiyaTest(PanelBaza):
    def test_dir_ls_bilan_bir_xil(self):
        (self.root / 'a.txt').write_text('a', encoding='utf-8')
        self.login_ega()
        self.assertEqual(self.run_cmd('dir').json()['output'],
                         self.run_cmd('ls').json()['output'])

    def test_cd_va_pwd(self):
        (self.root / 'ichki').mkdir()
        (self.root / 'ichki' / 'hujjat.txt').write_text('x', encoding='utf-8')
        self.login_ega()
        self.assertEqual(self.run_cmd('cd ichki').json()['cwd'], '/ichki')
        self.assertEqual(self.run_cmd('pwd').json()['output'], '/ichki')
        self.assertIn('hujjat.txt', self.run_cmd('ls').json()['output'])

    def test_cd_ortga_qaytadi(self):
        (self.root / 'ichki').mkdir()
        self.login_ega()
        self.run_cmd('cd ichki')
        self.assertEqual(self.run_cmd('cd ..').json()['cwd'], '/')

    def test_cd_tashqariga_chiqib_bolmaydi(self):
        self.login_ega()
        r = self.run_cmd('cd ..')
        self.assertIn('tashqariga', r.json()['output'])
        self.assertEqual(self.run_cmd('pwd').json()['output'], '/')

    def test_cd_yoq_papka(self):
        self.login_ega()
        self.assertIn('topilmadi', self.run_cmd('cd yoq_papka').json()['output'])

    def test_download_ichki_papkadan(self):
        (self.root / 'ichki').mkdir()
        (self.root / 'ichki' / 'hujjat.txt').write_text('mazmun', encoding='utf-8')
        self.login_ega()
        self.run_cmd('cd ichki')
        url = self.run_cmd("download --file 'hujjat.txt'").json()['action']['download']
        yuk = self.client.get(url)
        self.assertEqual(yuk.status_code, 200)
        self.assertEqual(b''.join(yuk.streaming_content), 'mazmun'.encode())

    def test_upload_joriy_papkaga_tushadi(self):
        (self.root / 'ichki').mkdir()
        self.login_ega()
        self.run_cmd('cd ichki')
        self.client.post(self.url_upload, {'file': SimpleUploadedFile('yangi.txt', b'salom')})
        self.assertTrue((self.root / 'ichki' / 'yangi.txt').exists())
        self.assertFalse((self.root / 'yangi.txt').exists())


class OchirishTest(PanelBaza):
    def test_delete_file(self):
        (self.root / 'a.txt').write_text('a', encoding='utf-8')
        self.login_ega()
        r = self.run_cmd("delete --file 'a.txt'")
        self.assertIn("O'chirildi", r.json()['output'])
        self.assertFalse((self.root / 'a.txt').exists())

    def test_delete_file_topilmadi(self):
        self.login_ega()
        self.assertIn('Topilmadi', self.run_cmd("delete --file 'yoq.txt'").json()['output'])

    def test_delete_all_tasdiqsiz_ochirmaydi(self):
        (self.root / 'a.txt').write_text('a', encoding='utf-8')
        self.login_ega()
        r = self.run_cmd('delete --all')
        self.assertIn('Tasdiqlang', r.json()['output'])
        self.assertTrue((self.root / 'a.txt').exists())     # hali turibdi

    def test_delete_all_yes_tozalaydi(self):
        (self.root / 'a.txt').write_text('a', encoding='utf-8')
        (self.root / 'ichki').mkdir()
        (self.root / 'ichki' / 'b.txt').write_text('b', encoding='utf-8')
        self.login_ega()
        r = self.run_cmd('delete --all --yes')
        self.assertIn("O'chirildi", r.json()['output'])
        self.assertEqual(list(self.root.iterdir()), [])

    def test_delete_all_faqat_joriy_papka(self):
        """`cd` ichida `delete --all --yes` faqat o'sha papkani tozalaydi."""
        (self.root / 'tashqi.txt').write_text('x', encoding='utf-8')
        (self.root / 'ichki').mkdir()
        (self.root / 'ichki' / 'b.txt').write_text('b', encoding='utf-8')
        self.login_ega()
        self.run_cmd('cd ichki')
        self.run_cmd('delete --all --yes')
        self.assertFalse((self.root / 'ichki' / 'b.txt').exists())
        self.assertTrue((self.root / 'tashqi.txt').exists())     # tegilmagan

    def test_delete_tashqariga_chiqib_bolmaydi(self):
        tashqi = self.root.parent / 'tashqaridagi_fayl.txt'
        tashqi.write_text('maxfiy', encoding='utf-8')
        self.addCleanup(tashqi.unlink, missing_ok=True)
        self.login_ega()
        r = self.run_cmd("delete --file '../tashqaridagi_fayl.txt'")
        self.assertIn('Topilmadi', r.json()['output'])
        self.assertTrue(tashqi.exists())                         # o'chmagan


class AdduserTest(PanelBaza):
    def test_adduser_yaratadi(self):
        self.login_ega()
        r = self.run_cmd('adduser --username yangi_admin --password parol123')
        self.assertIn('Superuser yaratildi', r.json()['output'])
        u = User.objects.get(username='yangi_admin')
        self.assertTrue(u.is_superuser and u.is_active)

    def test_adduser_login_talab_qiladi(self):
        r = self.run_cmd('adduser --username x --password parol123')
        self.assertIn('Avval login qiling', r.json()['output'])
        self.assertFalse(User.objects.filter(username='x').exists())

    def test_adduser_dubl_rad(self):
        self.login_ega()
        r = self.run_cmd('adduser --username ega_test --password parol123')
        self.assertIn('Allaqachon mavjud', r.json()['output'])

    def test_adduser_qisqa_parol_rad(self):
        self.login_ega()
        r = self.run_cmd('adduser --username yangi --password 12')
        self.assertIn('kamida 4', r.json()['output'])
        self.assertFalse(User.objects.filter(username='yangi').exists())

    def test_yaratilgan_admin_kira_oladi(self):
        self.login_ega()
        self.run_cmd('adduser --username admin2 --password parol123')
        self.run_cmd('logout')
        r = self.run_cmd('login --username admin2 --password parol123')
        self.assertIn('Xush kelibsiz', r.json()['output'])


class SahifaTest(PanelBaza):
    def test_sahifa_ochiladi(self):
        r = self.client.get(self.url_index)
        self.assertEqual(r.status_code, 200)


# ---------------------------------------------------------------- o'rnatuvchi

class OrnatuvchiYoliTest(PanelBaza):
    """`bazani_ol.py` aynan shu yo'ldan yuradi: login -> db.sqlite3 -> media.zip.

    Ya'ni bu testlar buzilsa — yangi kompyuterga o'rnatishda saytdagi
    ma'lumotlar ko'chirilmay qoladi.
    """

    def setUp(self):
        super().setUp()
        (self.root / 'db.sqlite3').write_bytes(b'SQLite format 3\x00soxta-baza')
        (self.root / 'media' / 'garov').mkdir(parents=True)
        (self.root / 'media' / 'garov' / 'surat.bin').write_bytes(b'rasm')

    def test_bazani_yuklab_olish_login_talab_qiladi(self):
        r = self.client.get(self.url_download, {'file': 'db.sqlite3'})
        self.assertEqual(r.status_code, 404)

    def test_kirgan_superuser_bazani_oladi(self):
        self.login_ega()
        r = self.client.get(self.url_download, {'file': 'db.sqlite3'})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(b''.join(r.streaming_content).startswith(b'SQLite format 3\x00'))

    def test_media_papkasi_zip_bolib_keladi(self):
        self.login_ega()
        r = self.client.get(self.url_download, {'all': '1', 'dir': 'media'})
        self.assertEqual(r.status_code, 200)
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            self.assertEqual(z.namelist(), ['garov/surat.bin'])

    def test_skript_yasagan_login_buyrugi_ishlaydi(self):
        """Parolda bo'shliq va apostrof bo'lsa ham login o'tishi kerak."""
        murakkab = "pa rol'ata\\shi"
        self.ega.set_password(murakkab)
        self.ega.save()
        buyruq = 'login --username %s --password %s' % (
            bazani_ol.tirnoqla('ega_test'), bazani_ol.tirnoqla(murakkab))
        self.assertIn('Xush kelibsiz', self.run_cmd(buyruq).json()['output'])


class BazaniOlTest(TestCase):
    """`bazani_ol.py` ning tarmoqsiz qismlari."""

    def setUp(self):
        self.papka = Path(tempfile.mkdtemp(prefix='bazani_ol_test_'))
        self.addCleanup(shutil.rmtree, self.papka, ignore_errors=True)

    def sqlite_yasa(self, nom, jadval='contracts_contract', qatorlar=3):
        yol = self.papka / nom
        u = sqlite3.connect(yol)
        u.execute('CREATE TABLE %s (id INTEGER PRIMARY KEY)' % jadval)
        u.executemany('INSERT INTO %s (id) VALUES (?)' % jadval,
                      [(i,) for i in range(1, qatorlar + 1)])
        u.commit()
        u.close()
        return yol

    def test_csrf_token_ajratiladi(self):
        html = '<input type="hidden" name="csrfmiddlewaretoken" value="ABC123">'
        self.assertEqual(bazani_ol.csrf_token(html), 'ABC123')
        self.assertEqual(bazani_ol.csrf_token('<p>panel</p>'), '')

    def test_tirnoqla_shlex_bilan_qaytib_ochiladi(self):
        for matn in ("oddiy", "bo shliq", "apostrof'li", "ikkala' va \"qo'sh\""):
            self.assertEqual(shlex.split(bazani_ol.tirnoqla(matn)), [matn])

    def test_baza_tekshir_shartnomalarni_sanaydi(self):
        self.assertEqual(bazani_ol.baza_tekshir(self.sqlite_yasa('ok.sqlite3')), 3)

    def test_html_sahifa_baza_deb_qabul_qilinmaydi(self):
        """Sessiya tugasa panel HTML qaytarishi mumkin — u joyiga tushmasin."""
        soxta = self.papka / 'javob.html'
        soxta.write_bytes(b'<!doctype html><title>Kirish</title>')
        with self.assertRaises(bazani_ol.Xato):
            bazani_ol.baza_tekshir(soxta)

    def test_begona_baza_rad_etiladi(self):
        yol = self.sqlite_yasa('begona.sqlite3', jadval='boshqa_jadval')
        with self.assertRaises(bazani_ol.Xato):
            bazani_ol.baza_tekshir(yol)

    def test_zip_papkadan_tashqariga_chiqa_olmaydi(self):
        zip_yol = self.papka / 'media.zip'
        with zipfile.ZipFile(zip_yol, 'w') as z:
            z.writestr('garov/surat.bin', b'rasm')
            z.writestr('../tashqari.txt', b'yomon niyat')
            z.writestr('/ildiz.txt', b'yomon niyat')
        nishon = self.papka / 'media'
        self.assertEqual(bazani_ol.xavfsiz_chiqar(zip_yol, nishon), 1)
        self.assertTrue((nishon / 'garov' / 'surat.bin').exists())
        self.assertFalse((self.papka / 'tashqari.txt').exists())

    def test_hajm_matni(self):
        self.assertEqual(bazani_ol.hajm(512), '512 B')
        self.assertEqual(bazani_ol.hajm(1536), '1.5 KB')

    def test_mavjud_bazaning_ustiga_yozilmaydi(self):
        (self.papka / 'db.sqlite3').write_bytes(b'eski baza')
        # Skript xatoni ekranga yozadi — test chiqishini ifloslantirmasin
        with contextlib.redirect_stdout(io.StringIO()):
            natija = bazani_ol.main(['--manzil', 'http://mavjud-emas.local',
                                     '--nishon', str(self.papka)])
        self.assertEqual(natija, 1)
        self.assertEqual((self.papka / 'db.sqlite3').read_bytes(), b'eski baza')
