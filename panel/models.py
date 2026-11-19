# -*- coding: utf-8 -*-
"""Saytga kirayotgan qurilmalarni kuzatish (ichki panel `stats` buyrug'i uchun).

Qurilma brauzerdagi uzoq muddatli cookie (`lq`) bilan taniladi: bir kompyuter
yoki telefon — bitta yozuv, kim kirganidan qat'i nazar. Cookie tozalansa yoki
boshqa brauzer ochilsa — yangi qurilma bo'lib sanaladi.
"""
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
