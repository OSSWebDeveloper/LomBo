# -*- coding: utf-8 -*-
"""Saytga kirayotgan qurilmalarni kuzatish (ichki panel `stats` buyrug'i uchun).

Qurilma brauzerdagi uzoq muddatli cookie (`lq`) bilan taniladi: bir kompyuter
yoki telefon — bitta yozuv, kim kirganidan qat'i nazar. Cookie tozalansa yoki
boshqa brauzer ochilsa — yangi qurilma bo'lib sanaladi.
"""
import logging

from django.db import models


class Qurilma(models.Model):
    TURLAR = [
        ('kompyuter', 'Kompyuter'),
        ('telefon', 'Telefon'),
        ('planshet', 'Planshet'),
        ('bot', 'Bot'),
    ]

    kalit = models.CharField(max_length=32, unique=True)
    turi = models.CharField(max_length=10, choices=TURLAR, default='kompyuter')
    tizim = models.CharField(max_length=40, blank=True)
    brauzer = models.CharField(max_length=40, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)
    ip = models.CharField(max_length=45, blank=True)
    foydalanuvchi = models.CharField(max_length=150, blank=True,
                                     help_text='Oxirgi marta kirgan hisob')
    birinchi = models.DateTimeField()
    oxirgi = models.DateTimeField(db_index=True)
    sorov_soni = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-oxirgi']

    def __str__(self):
        return f'#{self.pk} {self.turi} {self.tizim}/{self.brauzer}'


class QurilmaKun(models.Model):
    """Qurilma qaysi kuni necha sahifa ochgani — kunlik grafik uchun."""
    qurilma = models.ForeignKey(Qurilma, on_delete=models.CASCADE, related_name='kunlar')
    sana = models.DateField(db_index=True)
    sorov_soni = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [('qurilma', 'sana')]


class KirishUrinishi(models.Model):
    """Saytga kirish urinishi — kim, qaysi IP, natija (`stats --ishchi` uchun).

    Qurilma jadvali faqat qurilmaning OXIRGI IP sini saqlaydi va ishchi
    bloklangach «mehmon»ga aylanadi — shuning uchun «qaysi ishchi qaysi IP dan
    kirgan/urinayotgan»ini to'liq bermaydi. Bu jurnal esa HAR kirish urinishini
    (ruxsat berilgan yoki rad etilgan) alohida saqlaydi.
    """
    KIRDI = 'kirdi'
    ISHCHI = 'ishchi'
    IP = 'ip'
    PAROL = 'parol'
    NATIJALAR = [
        (KIRDI, 'Kirdi'),
        (ISHCHI, 'Ishchi — rad etildi'),
        (IP, 'Boshliq IP — rad etildi'),
        (PAROL, "Login/parol noto'g'ri"),
    ]

    vaqt = models.DateTimeField(auto_now_add=True, db_index=True)
    login = models.CharField(max_length=150, blank=True, db_index=True,
                             help_text='Kiritilgan login (hisob)')
    ip = models.CharField(max_length=45, blank=True)
    natija = models.CharField(max_length=10, choices=NATIJALAR)
    user_agent = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ['-vaqt']
        indexes = [models.Index(fields=['login', 'ip'])]

    def __str__(self):
        return f'{self.login}@{self.ip} — {self.natija}'

    @classmethod
    def yoz(cls, request, login, natija):
        """Urinishni yozadi. Hech qachon kirishni buzmaydi (xato — faqat jurnalga)."""
        from .kuzatuv import mijoz_ip
        try:
            cls.objects.create(
                login=(login or '')[:150], ip=mijoz_ip(request), natija=natija,
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:300])
        except Exception:
            logging.getLogger('panel').exception('Kirish urinishi yozilmadi')
