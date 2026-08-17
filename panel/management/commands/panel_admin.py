# -*- coding: utf-8 -*-
"""Panel uchun superuser yaratadi yoki parolini yangilaydi.

Parol kodda saqlanmaydi — argumentdan yoki yashirin so'rov orqali olinadi:
    python manage.py panel_admin --username MR_Clayd --password '...'
    python manage.py panel_admin                  # parolni yashirin so'raydi
"""
from getpass import getpass

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Panel uchun superuser yaratadi yoki parolini yangilaydi."

    def add_arguments(self, parser):
        parser.add_argument('--username', default='MR_Clayd')
        parser.add_argument('--password', default=None,
                            help="Berilmasa yashirin so'raladi.")

    def handle(self, *args, **options):
        User = get_user_model()
        username = options['username']
        password = options['password'] or getpass('Yangi parol: ')
        if not password:
            raise CommandError("Parol bo'sh bo'lishi mumkin emas.")

        user, yangi = User.objects.get_or_create(username=username)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        if hasattr(user, 'role'):
            user.role = 'admin'          # saytga emas, faqat panelga
        user.set_password(password)
        user.save()

        holat = 'yaratildi' if yangi else 'yangilandi'
        self.stdout.write(self.style.SUCCESS(f'{username} superuser {holat}.'))
