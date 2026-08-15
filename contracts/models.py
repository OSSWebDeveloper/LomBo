import math
from datetime import timedelta

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


# Hujjat berilgan hudud — 12 viloyat, Toshkent shahri va Qoraqalpog'iston.
# Qiymatlar kirillda saqlanadi, chunki shartnoma matniga aynan shu ko'rinishda tushadi.
VILOYATLAR = [
    ('Андижон вилояти', 'Андижон вилояти'),
    ('Бухоро вилояти', 'Бухоро вилояти'),
    ('Жиззах вилояти', 'Жиззах вилояти'),
    ('Навоий вилояти', 'Навоий вилояти'),
    ('Наманган вилояти', 'Наманган вилояти'),
    ('Самарқанд вилояти', 'Самарқанд вилояти'),
    ('Сирдарё вилояти', 'Сирдарё вилояти'),
    ('Сурхондарё вилояти', 'Сурхондарё вилояти'),
    ('Тошкент вилояти', 'Тошкент вилояти'),
    ('Фарғона вилояти', 'Фарғона вилояти'),
    ('Хоразм вилояти', 'Хоразм вилояти'),
    ('Қашқадарё вилояти', 'Қашқадарё вилояти'),
    ('Тошкент шаҳри', 'Тошкент шаҳри'),
    ('Қорақалпоғистон Республикаси', 'Қорақалпоғистон Республикаси'),
]


# Shaxsni tasdiqlovchi hujjat ikki xil bo'ladi: yashil biometrik pasport va
# ID karta. Shartnoma matnidagi ibora shu tanlovga qarab yoziladi — qolgan
# hamma narsa (seriya-raqam, IIV bo'limi, sana) ikkalasida bir xil.
HUJJAT_ID_KARTA = 'id_karta'
HUJJAT_PASPORT = 'passport'
HUJJAT_TURLARI = [
    (HUJJAT_ID_KARTA, 'ID karta'),
    (HUJJAT_PASPORT, 'Biometrik pasport (yashil)'),
]

HUJJAT_IBORASI = {
    HUJJAT_ID_KARTA: 'ракамли шахс гувохномаси',
    HUJJAT_PASPORT: 'ракамли паспорти',
}


def pasport_matni(viloyat, bolim, sana, raqam, turi):
    """«Бухоро вилояти, 61013-сонли ИИВ томонидан 23.04.2025-йилда берилган
    АE№2437494 ракамли шахс гувохномаси»

    Qarz oluvchi uchun ham, garovga qo'yuvchi uchun ham shu funksiya ishlaydi.
    Yashil biometrik pasportda IIV bo'lim raqami bo'lmaydi — u holda
    «Бухоро вилояти ИИВ томонидан ...» deb, raqamsiz yoziladi.
    Ma'lumot to'liq bo'lmasa bo'sh matn qaytadi.
    """
    if not (sana and raqam):
        return ''
    hudud = (f'{viloyat}, ' if bolim else f'{viloyat} ') if viloyat else ''
    bolim_matni = f'{bolim}-сонли ' if bolim else ''
    ibora = HUJJAT_IBORASI.get(turi) or HUJJAT_IBORASI[HUJJAT_ID_KARTA]
    return (f'{hudud}{bolim_matni}ИИВ томонидан '
            f'{sana.strftime("%d.%m.%Y")}-йилда берилган {raqam} {ibora}')


def next_contract_number():
    """Avtomatik raqam: bazadagi eng katta raqam + 1, minimal CONTRACT_START_NUMBER."""
    last = Contract.objects.aggregate(m=models.Max('number'))['m'] or 0
    return max(last + 1, settings.CONTRACT_START_NUMBER)


def next_garov_number():
    """Garov shartnomasi o'z hisobida yuritiladi — asosiy raqamdan mustaqil."""
    last = Contract.objects.aggregate(m=models.Max('garov_number'))['m'] or 0
    return max(last + 1, settings.GAROV_START_NUMBER)


class Contract(models.Model):
    TYPE_ZARGARLIK = 'zargarlik'
    TYPE_TRANSPORT = 'transport'
    TYPE_KAFILLIK = 'kafillik'
    TYPE_CHOICES = [
        (TYPE_ZARGARLIK, 'Zargarlik buyumlari garovi'),
        (TYPE_TRANSPORT, 'Transport vositasi garovi'),
        (TYPE_KAFILLIK, 'Ish haqi kafilligi'),
    ]

    STATUS_ACTIVE = 'active'
    STATUS_PENDING_DELETE = 'pending_delete'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Faol'),
        (STATUS_PENDING_DELETE, "O'chirish so'ralgan"),
    ]

    number = models.PositiveIntegerField('Shartnoma №', unique=True, default=next_contract_number)
    date = models.DateField('Shartnoma sanasi')
    collateral_type = models.CharField("Ta'minot turi", max_length=12, choices=TYPE_CHOICES)

    # Qarz oluvchi
    borrower_fio = models.CharField('Qarz oluvchi F.I.Sh. (kirillda)', max_length=200)
    passport_type = models.CharField('Hujjat turi', max_length=10, choices=HUJJAT_TURLARI,
                                     default=HUJJAT_ID_KARTA)
    passport_region = models.CharField('Hujjat berilgan viloyat', max_length=100, blank=True,
                                       choices=VILOYATLAR)
    # Faqat raqam saqlanadi; hujjatda «-сонли» qo'shimchasi o'zi qo'shiladi.
    # Yashil biometrik pasportda bunday raqam bo'lmaydi — o'shanda bo'sh qoladi.
    passport_org = models.CharField('IIV bo\'lim raqami', max_length=50, blank=True,
                                    validators=[RegexValidator(
                                        r'^\d*$', 'Faqat raqam kiriting.')],
                                    help_text='Faqat raqam. Masalan: 61013')
    passport_date = models.DateField('Hujjat berilgan sana')
    passport_number = models.CharField('Hujjat seriya-raqami', max_length=30,
                                       help_text='Masalan: АE№2437494')
    borrower_address = models.CharField('Manzil (kirillda)', max_length=300)
    # Arizada uchta telefon raqami so'raladi. Birinchisi shartnomaning
    # «Қарз олувчи» rekvizitlariga ham tushadi.
    # Eski shartnomalarda bo'lmagani uchun bazada bo'sh bo'lishi mumkin — yangisida
    # uchalasini ham to'ldirish majburiy (qarang: ContractForm).
    borrower_phone = models.CharField('Telefon raqami 1', max_length=25, blank=True,
                                      help_text='Masalan: 12 345-67-89')
    borrower_phone2 = models.CharField('Telefon raqami 2', max_length=25, blank=True)
    borrower_phone3 = models.CharField('Telefon raqami 3', max_length=25, blank=True)
    # Arizadagi «Менинг иш жойим ва унинг манзили» qatori
    borrower_workplace = models.CharField('Ish joyi va manzili (kirillda)',
                                          max_length=300, blank=True)
    # Arizadagi «Мен ойида ўртача ... сўм даромадларга эга» jumlasi uchun
    monthly_income = models.DecimalField('Oylik daromad (so\'m)', max_digits=15,
                                         decimal_places=0, null=True, blank=True)

    # Kredit shartlari
    amount = models.DecimalField('Kredit summasi (so\'m)', max_digits=15, decimal_places=0)
    term_months = models.PositiveIntegerField('Muddat (oy)', default=12)
    interest_rate = models.PositiveIntegerField('Yillik foiz (%)', default=60)
    end_date = models.DateField('Tugash sanasi')
    # To'lov jadvali shu sanadan boshlanadi va keyin har oy shu kunda davom
    # etadi. Xaridor talabi (2026-08-14): sana qo'ldan belgilanishi kerak —
    # mijoz bilan kelishilgan kun har doim ham «shartnoma + 1 oy» bo'lmaydi.
    # Bo'sh qolsa shartnoma sanasidan bir oy keyin olinadi.
    payment_start_date = models.DateField("Birinchi to'lov sanasi", null=True, blank=True)

    # Garov umumiy
    # Garov shartnomasining raqami asosiy shartnomanikidan mustaqil (mijoz
    # qarori, 2026-08-14) — o'z hisobida boradi va qo'lda ham o'zgartiriladi.
    # Kafillikda garov shartnomasi tuzilmaydi, shuning uchun bo'sh qoladi.
    garov_number = models.PositiveIntegerField('Garov shartnomasi №', unique=True,
                                               null=True, blank=True)
    garov_value = models.DecimalField('Garov bahosi (so\'m)', max_digits=15, decimal_places=0,
                                      null=True, blank=True)

    # Garovga qo'yuvchi qarz oluvchining o'zi bo'lmasligi mumkin — masalan
    # onasining tillasini garovga qo'ysa. Bo'sh bo'lsa qarz oluvchining
    # ma'lumotlari ishlatiladi (garov_beruvchi_* xossalariga qarang).
    # Transportda bu ish `VehicleInfo.owner` orqali qilinadi.
    pledgor_other = models.BooleanField('Garovga qo\'yuvchi boshqa shaxs', default=False)
    pledgor_fio = models.CharField('Garovga qo\'yuvchi F.I.Sh. (kirillda)',
                                   max_length=200, blank=True)
    pledgor_passport_type = models.CharField('Hujjat turi', max_length=10, blank=True,
                                             choices=HUJJAT_TURLARI)
    pledgor_passport_region = models.CharField('Hujjat berilgan viloyat', max_length=100,
                                               blank=True, choices=VILOYATLAR)
    pledgor_passport_org = models.CharField('IIV bo\'lim raqami', max_length=50, blank=True,
                                            validators=[RegexValidator(
                                                r'^\d*$', 'Faqat raqam kiriting.')])
    pledgor_passport_date = models.DateField('Hujjat berilgan sana', null=True, blank=True)
    pledgor_passport_number = models.CharField('Hujjat seriya-raqami', max_length=30, blank=True)
    pledgor_address = models.CharField('Manzil (kirillda)', max_length=300, blank=True)

    status = models.CharField('Holat', max_length=15, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Kim kiritgan',
                                   on_delete=models.SET_NULL, null=True, related_name='contracts')
    created_at = models.DateTimeField('Kiritilgan vaqt', auto_now_add=True)
    updated_at = models.DateTimeField('O\'zgartirilgan vaqt', auto_now=True)

    class Meta:
        verbose_name = 'Shartnoma'
        verbose_name_plural = 'Shartnomalar'
        ordering = ['-number']

    def __str__(self):
        return f'№{self.number} — {self.borrower_fio}'

    @property
    def tahrir_muddati(self):
        """Ishchi uchun tahrirlash oynasi qachon yopiladi.

        Muddat kiritilgan vaqtdan (`created_at`) sanaladi, shuning uchun
        tahrirlash oynani uzaytirmaydi. Saqlanmagan shartnomada — None.
        """
        daqiqa = getattr(settings, 'ISHCHI_TAHRIR_DAQIQA', 0)
        if not self.created_at or daqiqa <= 0:
            return None
        return self.created_at + timedelta(minutes=daqiqa)

    @property
    def tahrir_qoldiq_daqiqa(self):
        """Tahrirlash oynasi yopilishiga necha daqiqa qoldi (o'tgan bo'lsa 0)."""
        muddat = self.tahrir_muddati
        if muddat is None:
            return 0
        return max(0, math.ceil((muddat - timezone.now()).total_seconds() / 60))

    def ishchi_tahrirlay_oladi(self, user):
        """Ishchi faqat o'zi endigina kiritgan shartnomani tuzata oladi.

        O'chirish so'rovi yuborilgan shartnoma tahrirlanmaydi — boshliq
        so'rovni ko'rayotgan shartnoma o'zgarib ketmasligi kerak.
        """
        muddat = self.tahrir_muddati
        return bool(muddat
                    and timezone.now() < muddat
                    and getattr(user, 'is_ishchi', False)
                    and self.created_by_id == user.id
                    and self.status == self.STATUS_ACTIVE)

    @property
    def tolov_boshlanishi(self):
        """Birinchi to'lov sanasi — belgilanmagan bo'lsa shartnomadan bir oy keyin."""
        from .docgen import add_months
        return self.payment_start_date or add_months(self.date, 1)

    @property
    def passport_full(self):
        """«Бухоро вилояти, 61013-сонли ИИВ томонидан 23.04.2025-йилда берилган АE№2437494 ...»"""
        return pasport_matni(self.passport_region, self.passport_org,
                             self.passport_date, self.passport_number,
                             self.passport_type)

    # --------------------------------------------------- garovga qo'yuvchi
    # Alohida shaxs kiritilmagan bo'lsa hamma joyda qarz oluvchining o'zi
    # garovga qo'yuvchi bo'ladi — hujjat matni shu holatga mo'ljallangan.

    @property
    def garov_beruvchi_boshqami(self):
        return bool(self.pledgor_other and self.pledgor_fio)

    @property
    def garov_beruvchi_fio(self):
        return self.pledgor_fio if self.garov_beruvchi_boshqami else self.borrower_fio

    @property
    def garov_beruvchi_pasport(self):
        if not self.garov_beruvchi_boshqami:
            return self.passport_full
        return pasport_matni(self.pledgor_passport_region, self.pledgor_passport_org,
                             self.pledgor_passport_date, self.pledgor_passport_number,
                             self.pledgor_passport_type)

    @property
    def garov_beruvchi_manzil(self):
        return (self.pledgor_address if self.garov_beruvchi_boshqami
                else self.borrower_address)

    @property
    def passport_seriya(self):
        """«АD№2540542» -> «АD». Arizada seriya va raqam alohida kataklarda."""
        return (self.passport_number or '').split('№')[0].strip()

    @property
    def passport_soni(self):
        """«АD№2540542» -> «2540542»"""
        qismlar = (self.passport_number or '').split('№')
        return qismlar[1].strip() if len(qismlar) > 1 else ''


class JewelryItem(models.Model):
    """Zargarlik garovi jadvali qatori."""
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='jewelry_items')
    name = models.CharField('Nomi (kirillda)', max_length=200)
    quantity = models.PositiveIntegerField('Soni (dona)')
    weight = models.DecimalField('Og\'irligi (gr)', max_digits=8, decimal_places=2)
    proba = models.CharField('Probasi', max_length=10, default='585')
    value = models.DecimalField('Summasi (so\'m)', max_digits=15, decimal_places=0)

    class Meta:
        verbose_name = 'Zargarlik buyumi'
        verbose_name_plural = 'Zargarlik buyumlari'

    def __str__(self):
        return f'{self.name} x{self.quantity}'


class VehicleInfo(models.Model):
    """Transport garovi ma'lumotlari."""
    contract = models.OneToOneField(Contract, on_delete=models.CASCADE, related_name='vehicle')
    owner = models.CharField('Egasi (garovga qo\'yuvchi)', max_length=250,
                             help_text='Masalan: “Express Alligator Bukhara” МЧЖ yoki F.I.Sh.')
    owner_head = models.CharField('Tashkilot rahbari (bo\'lsa)', max_length=200, blank=True)
    state_number = models.CharField('Davlat raqami', max_length=20)
    model = models.CharField('Rusumi', max_length=100)
    color = models.CharField('Rangi', max_length=50)
    body_number = models.CharField('Kuzov raqami', max_length=50, blank=True, default='-')
    chassis_number = models.CharField('Shassi raqami', max_length=50, blank=True, default='-')
    engine_number = models.CharField('Dvigatel raqami', max_length=50, blank=True, default='-')
    year = models.CharField('Ishlab chiqarilgan yili', max_length=10)
    techpassport = models.CharField('Texpasport raqami va sanasi', max_length=100,
                                    help_text='Masalan: AAG 0949387 / 14.02.2023')

    class Meta:
        verbose_name = 'Transport vositasi'
        verbose_name_plural = 'Transport vositalari'

    def __str__(self):
        return f'{self.model} {self.state_number}'


class GuarantorInfo(models.Model):
    """Ish haqi kafilligi ma'lumotlari."""
    contract = models.OneToOneField(Contract, on_delete=models.CASCADE, related_name='guarantor')
    fio = models.CharField('Kafil F.I.Sh. (kirillda)', max_length=200)
    amount = models.DecimalField('Kafillik summasi (so\'m)', max_digits=15, decimal_places=0)

    class Meta:
        verbose_name = 'Kafil'
        verbose_name_plural = 'Kafillar'

    def __str__(self):
        return self.fio


class DeleteRequest(models.Model):
    """Ishchi shartnomani o'chirishni so'raydi — uni qo'shgan boshliq tasdiqlaydi."""
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Kutilmoqda'),
        (STATUS_APPROVED, 'Tasdiqlangan'),
        (STATUS_REJECTED, 'Rad etilgan'),
    ]

    contract = models.ForeignKey(Contract, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='delete_requests')
    # Shartnoma o'chirilgach ma'lumot saqlanib qolishi uchun nusxa maydonlar:
    contract_number = models.PositiveIntegerField('Shartnoma №')
    contract_info = models.CharField('Shartnoma haqida', max_length=300, blank=True)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                     related_name='delete_requests', verbose_name='So\'ragan ishchi')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                    related_name='delete_approvals', verbose_name='Tasdiqlashi kerak')
    reason = models.CharField('Sabab', max_length=500, blank=True)
    status = models.CharField('Holat', max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField('So\'ralgan vaqt', auto_now_add=True)
    decided_at = models.DateTimeField('Ko\'rilgan vaqt', null=True, blank=True)

    class Meta:
        verbose_name = "O'chirish so'rovi"
        verbose_name_plural = "O'chirish so'rovlari"
        ordering = ['-created_at']

    def __str__(self):
        return f'№{self.contract_number} — {self.get_status_display()}'


class Amal(models.Model):
    """Kim, qachon, nima qilgani — tizim tarixi.

    Foydalanuvchi yoki shartnoma o'chirilsa ham yozuv qoladi, shuning uchun
    ism va obyekt nomi matn sifatida nusxalab saqlanadi.
    """

    YARATDI = 'shartnoma_yaratdi'
    OZGARTIRDI = 'shartnoma_ozgartirdi'
    OCHIRDI = 'shartnoma_ochirdi'
    SOROV_YUBORDI = 'sorov_yubordi'
    SOROV_TASDIQLADI = 'sorov_tasdiqladi'
    SOROV_RAD_ETDI = 'sorov_rad_etdi'
    ISHCHI_QOSHDI = 'ishchi_qoshdi'
    ISHCHI_BOSHATDI = 'ishchi_boshatdi'
    ISHCHI_OCHIRDI = 'ishchi_ochirdi'
    PAROL_OZGARTIRDI = 'parol_ozgartirdi'
    SHABLON_OZGARTIRDI = 'shablon_ozgartirdi'
    HUJJAT_OLDI = 'hujjat_oldi'

    AMAL_CHOICES = [
        (YARATDI, 'Shartnoma yaratdi'),
        (OZGARTIRDI, 'Shartnomani o‘zgartirdi'),
        (OCHIRDI, 'Shartnomani o‘chirdi'),
        (SOROV_YUBORDI, 'O‘chirish so‘rovi yubordi'),
        (SOROV_TASDIQLADI, 'O‘chirish so‘rovini tasdiqladi'),
        (SOROV_RAD_ETDI, 'O‘chirish so‘rovini rad etdi'),
        (ISHCHI_QOSHDI, 'Ishchi qo‘shdi'),
        (ISHCHI_BOSHATDI, 'Ishchini bo‘shatdi'),
        (ISHCHI_OCHIRDI, 'Ishchini o‘chirdi'),
        (PAROL_OZGARTIRDI, 'Parolni o‘zgartirdi'),
        (SHABLON_OZGARTIRDI, 'Shablonni o‘zgartirdi'),
        (HUJJAT_OLDI, 'Hujjatni yuklab oldi'),
    ]

    vaqt = models.DateTimeField('Vaqt', auto_now_add=True, db_index=True)
    kim = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Kim',
                            null=True, blank=True, on_delete=models.SET_NULL,
                            related_name='amallar')
    kim_nomi = models.CharField('Kim (nusxa)', max_length=150)
    kim_roli = models.CharField('Roli', max_length=10, blank=True)
    amal = models.CharField('Amal', max_length=25, choices=AMAL_CHOICES, db_index=True)
    obyekt = models.CharField('Nimaga', max_length=200, blank=True)
    izoh = models.CharField('Izoh', max_length=500, blank=True)

    class Meta:
        verbose_name = 'Amal'
        verbose_name_plural = 'Amallar tarixi'
        ordering = ['-vaqt']

    def __str__(self):
        return f'{self.vaqt:%d.%m.%Y %H:%M} · {self.kim_nomi} · {self.get_amal_display()}'


def amal_yoz(user, amal, obyekt='', izoh=''):
    """Tarixga yozuv qo'shadi. Xato bo'lsa asosiy ishni to'xtatmaydi."""
    try:
        Amal.objects.create(
            kim=user if getattr(user, 'pk', None) else None,
            kim_nomi=str(user) if user else '—',
            kim_roli=getattr(user, 'role', '') or '',
            amal=amal, obyekt=obyekt[:200], izoh=izoh[:500],
        )
    except Exception:      # tarix yozilmasa ham dastur ishlashda davom etsin
        pass
