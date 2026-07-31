from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class LombardUserManager(UserManager):
    """Yangi superuser saytga kirmaydigan «faqat admin» roli bilan yaratiladi."""

    def create_superuser(self, *args, **kwargs):
        kwargs.setdefault('role', User.ROLE_ADMIN)
        return super().create_superuser(*args, **kwargs)


class User(AbstractUser):
    """Rol saytga kirishni, is_staff esa admin panelga kirishni belgilaydi.

    Ikkalasi bir-biridan mustaqil: «faqat admin» roli bilan saytga kirilmaydi,
    boshliq/ishchi esa admin panelga kirmaydi.
    """

    ROLE_BOSHLIQ = 'boshliq'
    ROLE_ISHCHI = 'ishchi'
    ROLE_ADMIN = 'admin'
    ROLE_CHOICES = [
        (ROLE_BOSHLIQ, 'Boshliq'),
        (ROLE_ISHCHI, 'Ishchi'),
        (ROLE_ADMIN, 'Faqat admin panel (saytga kirmaydi)'),
    ]
    # Saytga kirish huquqi bo'lgan rollar
    SAYT_ROLLARI = (ROLE_BOSHLIQ, ROLE_ISHCHI)

    objects = LombardUserManager()

    role = models.CharField('Rol', max_length=10, choices=ROLE_CHOICES, default=ROLE_ISHCHI)
    added_by = models.ForeignKey(
        'self', verbose_name="Kim qo'shgan (boshliq)",
        null=True, blank=True, on_delete=models.SET_NULL, related_name='workers',
    )
    can_full_edit = models.BooleanField(
        "To'liq tahrirlash vakolati", default=False,
        help_text="Belgilansa, bu boshliq istalgan shartnomani to'liq tahrirlay oladi.",
    )
    can_edit_template = models.BooleanField(
        'Shablonni o‘zgartirish vakolati', default=False,
        help_text='Belgilansa, bu boshliq Word shablonlarini almashtira oladi.',
    )
    # Ishchi qo'shgan shartnomalar soni — shartnoma o'chirilsa ham kamaymaydi.
    contracts_added = models.PositiveIntegerField("Qo'shgan shartnomalari (jami)", default=0)

    class Meta:
        verbose_name = 'Foydalanuvchi'
        verbose_name_plural = 'Foydalanuvchilar'

    @property
    def sayt_foydalanuvchisi(self):
        """Saytga kira oladimi? Superuser bo'lish o'zi huquq bermaydi."""
        return self.role in self.SAYT_ROLLARI

    @property
    def is_boshliq(self):
        return self.role == self.ROLE_BOSHLIQ

    @property
    def is_ishchi(self):
        return self.role == self.ROLE_ISHCHI

    @property
    def shablon_vakolati(self):
        return self.is_boshliq and self.can_edit_template

    def __str__(self):
        full = self.get_full_name()
        return f'{full} ({self.username})' if full else self.username


class BoshliqManager(UserManager):
    """Faqat boshliqlarni ko'rsatadi va yangisini avtomatik boshliq qilib yaratadi."""

    def get_queryset(self):
        return super().get_queryset().filter(role=User.ROLE_BOSHLIQ)

    def create(self, **kwargs):
        kwargs['role'] = User.ROLE_BOSHLIQ
        return super().create(**kwargs)


class Boshliq(User):
    """Boshliqni admin panelda soddaroq qo'shish uchun alohida model.

    Bu — proxy model: baza jadvali User bilan bir xil, alohida jadval yaratilmaydi.
    Shu sababli admin panelda «Boshliqlar» bo'limi paydo bo'ladi va u yerda faqat
    kerakli maydonlar so'raladi (login, ism, parol, vakolat).
    """

    objects = BoshliqManager()

    class Meta:
        proxy = True
        verbose_name = 'Boshliq'
        verbose_name_plural = 'Boshliqlar'

    def save(self, *args, **kwargs):
        self.role = User.ROLE_BOSHLIQ
        super().save(*args, **kwargs)

    @property
    def ishchilar_soni(self):
        return self.workers.count()
