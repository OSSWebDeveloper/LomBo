# -*- coding: utf-8 -*-
"""Birinchi o'rnatishdan keyingi tayyorgarlik — ORNATISH.bat shuni chaqiradi.

Bir necha marta ishga tushirilsa ham xavfsiz:
  * maxfiy kalit fayli bo'lmasa — yaratadi;
  * bazada birorta ham hisob bo'lmasa — boshliq hisobini ochadi;
  * hisoblar allaqachon bor bo'lsa — hech nimaga tegmaydi.

Admin panel (/admin/) uchun superuser kerak bo'lsa — `--admin` bayrog'i
bilan chaqiriladi yoki keyin `python manage.py panel_admin` ishlatiladi.
"""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.core.management.utils import get_random_secret_key


class Command(BaseCommand):
    help = "Birinchi ishga tushirish uchun maxfiy kalit va boshliq hisobini tayyorlaydi."

    def add_arguments(self, parser):
        parser.add_argument('--login', default='boshliq', help='Boshliq logini')
        parser.add_argument('--parol', default='boshliq', help='Boshliq paroli')
        parser.add_argument('--admin', action='store_true',
                            help="Admin panel uchun ham hisob ochilsin (login: superuser)")

    def handle(self, *args, **options):
        self._kalit()
        self._hisoblar(options['login'], options['parol'], options['admin'])

    def _kalit(self):
        """Maxfiy kalit `.secret_key` faylida — bazadan mustaqil saqlanadi."""
        fayl = settings.BASE_DIR / '.secret_key'
        if fayl.exists() and fayl.read_text(encoding='utf-8').strip():
            self.stdout.write('Maxfiy kalit joyida.')
            return
        fayl.write_text(get_random_secret_key(), encoding='utf-8')
        self.stdout.write(self.style.SUCCESS('Yangi maxfiy kalit yaratildi.'))

    def _hisoblar(self, login, parol, admin_ham):
        User = get_user_model()

        if User.objects.exists():
            nomlar = ', '.join(
                User.objects.filter(role=User.ROLE_BOSHLIQ, is_active=True)
                .values_list('username', flat=True)
            )
            self.stdout.write("Hisoblar mavjud — o'zgartirilmadi.")
            self.stdout.write('    Boshliq logini: ' + (nomlar or "yo'q"))
            return

        User.objects.create_user(
            username=login, password=parol,
            role=User.ROLE_BOSHLIQ,
            can_full_edit=True,      # birinchi boshliq — to'liq vakolatli
            can_edit_template=True,
        )
        self.stdout.write(self.style.SUCCESS('Boshliq hisobi yaratildi.'))
        self.stdout.write(self.style.WARNING('    login: ' + login))
        self.stdout.write(self.style.WARNING('    parol: ' + parol))
        self.stdout.write(self.style.WARNING(
            "    Saytga kirgach parolni albatta almashtiring!"))

        if admin_ham:
            admin = User.objects.create_superuser(
                username='superuser', password='superuser')
            self.stdout.write(self.style.SUCCESS(
                'Admin panel hisobi yaratildi: ' + admin.username + ' / superuser'))
