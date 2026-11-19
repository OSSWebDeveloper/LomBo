# -*- coding: utf-8 -*-
"""Ichki panelning `stats` buyrug'i — qurilmalar statistikasi matn ko'rinishida.

Konsol monoshriftli, shuning uchun jadval va grafiklar belgilardan (█) yasaladi.
Botlar asosiy raqamlarga qo'shilmaydi, alohida qatorda ko'rsatiladi.
"""
from datetime import datetime, time, timedelta

from django.db.models import Count, Sum
from django.utils import timezone

from .models import Qurilma, QurilmaKun

KENGLIK = 28                       # grafik ustunining eng uzun bo'lagi
HAFTA = ['Du', 'Se', 'Ch', 'Pa', 'Ju', 'Sh', 'Ya']
TUR_NOMI = dict(Qurilma.TURLAR)


def _son(n):
    return f'{n:,}'.replace(',', ' ')


def _ustun(qiymat, eng_kop):
    if not eng_kop or not qiymat:
        return ''
    return '█' * max(1, round(qiymat / eng_kop * KENGLIK))


def _taqsimot(sarlavha, juftlar, jami):
    """[(nom, son), ...] -> foizli gorizontal grafik qatorlari."""
    qatorlar = [sarlavha]
    if not juftlar:
        return qatorlar + ["  (ma'lumot yo'q)"]
    eng = max(s for _, s in juftlar)
    enli = max(len(n) for n, _ in juftlar)
    for nom, s in juftlar:
        foiz = s * 100 / jami if jami else 0
        qatorlar.append(f'  {nom:<{enli}}  {_ustun(s, eng):<{KENGLIK}}  {s:>4}  ({foiz:.0f}%)')
    return qatorlar


def _guruh(qs, maydon):
    return [(r[maydon] or "noma'lum", r['n'])
            for r in qs.values(maydon).annotate(n=Count('id')).order_by('-n', maydon)]


def umumiy(kunlar=14):
    endi = timezone.now()
    bugun = timezone.localdate(endi)
    odam = Qurilma.objects.exclude(turi='bot')
    jami = odam.count()
    botlar = Qurilma.objects.filter(turi='bot').count()

    def faol(kun):
        return odam.filter(kunlar__sana__gt=bugun - timedelta(days=kun)).distinct().count()

    yangi_bugun = odam.filter(
        birinchi__gte=timezone.make_aware(datetime.combine(bugun, time.min))).count()
    onlayn = odam.filter(oxirgi__gte=endi - timedelta(minutes=5)).count()
    sahifa = odam.aggregate(s=Sum('sorov_soni'))['s'] or 0
    bugun_sahifa = QurilmaKun.objects.filter(
        sana=bugun).exclude(qurilma__turi='bot').aggregate(s=Sum('sorov_soni'))['s'] or 0

    q = [
        f'QURILMALAR STATISTIKASI   {timezone.localtime(endi):%d.%m.%Y %H:%M}',
        '─' * 52,
        f'  Jami qurilma .............. {_son(jami):>6}',
        f'  Hozir onlayn (5 daqiqa) ... {_son(onlayn):>6}',
        f'  Bugun faol ................ {_son(faol(1)):>6}   (yangi: {yangi_bugun})',
        f'  Oxirgi 7 kun .............. {_son(faol(7)):>6}',
        f'  Oxirgi 30 kun ............. {_son(faol(30)):>6}',
        f'  Sahifa ochilishi: bugun {_son(bugun_sahifa)}, jami {_son(sahifa)}',
    ]
    if botlar:
        q.append(f'  Bot/skript (hisobga olinmagan): {botlar}')
    if not jami:
        q += ['', "Hali birorta qurilma yozilmagan — saytga kirilgach ko'rinadi.",
              "Kuzatuvdan oldingi kirishlar:  stats --tarix"]
        return '\n'.join(q)

    q.append('')
    q += _taqsimot('Qurilma turi', [(TUR_NOMI.get(n, n), s) for n, s in _guruh(odam, 'turi')], jami)
    q.append('')
    q += _taqsimot('Operatsion tizim', _guruh(odam, 'tizim'), jami)
    q.append('')
    q += _taqsimot('Brauzer', _guruh(odam, 'brauzer'), jami)

    # Kunlik faol qurilmalar
    boshi = bugun - timedelta(days=kunlar - 1)
    kunlik = dict(QurilmaKun.objects.filter(sana__gte=boshi).exclude(qurilma__turi='bot')
                  .values('sana').annotate(n=Count('qurilma', distinct=True))
                  .values_list('sana', 'n'))
    eng = max(kunlik.values(), default=0)
    q += ['', f'Kunlik faol qurilmalar (oxirgi {kunlar} kun)']
    for i in range(kunlar):
        kun = boshi + timedelta(days=i)
        n = kunlik.get(kun, 0)
        belgi = ' ◄ bugun' if kun == bugun else ''
        q.append(f'  {kun:%d.%m} {HAFTA[kun.weekday()]}  {_ustun(n, eng):<{KENGLIK}}  {n:>3}{belgi}')

    # Hisoblar
    hisob = list(odam.exclude(foydalanuvchi='').values('foydalanuvchi')
                 .annotate(n=Count('id')).order_by('-n', 'foydalanuvchi')
                 .values_list('foydalanuvchi', 'n'))
    mehmon = odam.filter(foydalanuvchi='').count()
    q += ['', 'Hisoblar bo\'yicha (nechta qurilmadan kirgan)']
    for nom, n in hisob[:15]:
        q.append(f'  {nom:<20} {n:>3}')
    if mehmon:
        q.append(f'  {"(kirmagan)":<20} {mehmon:>3}')
    q += ['', "Batafsil:  stats --list   ·   stats --days 30   ·   stats --tarix (oldingilar)"]
    return '\n'.join(q)


def royxat(soni=20):
    qs = Qurilma.objects.all()[:soni]
    if not qs:
        return "Hali birorta qurilma yozilmagan."
    q = [f'Oxirgi faol {len(qs)} qurilma (jami {Qurilma.objects.count()})',
         f'  {"#":>4}  {"Qurilma":<30}  {"Hisob":<12}  {"Oxirgi":<11}  {"Sahifa":>6}  IP',
         '  ' + '─' * 72]
    for d in qs:
        nom = ' · '.join(x for x in (TUR_NOMI.get(d.turi, d.turi), d.tizim, d.brauzer) if x)
        q.append(f'  {d.pk:>4}  {nom[:30]:<30}  {(d.foydalanuvchi or "—")[:12]:<12}  '
                 f'{timezone.localtime(d.oxirgi):%d.%m %H:%M}  {d.sorov_soni:>6}  {d.ip}')
    return '\n'.join(q)


def bajar(flaglar):
    """Panel buyrug'i: `stats`, `stats --days N`, `stats --list [--n N]` (`--tarix` — views da)."""
    def butun(nom, std, eng_kop):
        try:
            return max(1, min(int(flaglar.get(nom, std)), eng_kop))
        except (TypeError, ValueError):
            return std

    if flaglar.get('list'):
        return royxat(butun('n', 20, 500))
    return umumiy(butun('days', 14, 90))
