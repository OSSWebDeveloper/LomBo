# -*- coding: utf-8 -*-
import re

from django import forms
from django.forms import inlineformset_factory

from .docgen import contract_end_date
from .formatlash import hujjat_raqami, pul_matn, pul_son
from .models import (HUJJAT_PASPORT, HUJJAT_TURLARI, VILOYATLAR, Contract,
                     GarovRasm, GuarantorInfo, JewelryItem, VehicleInfo,
                     next_contract_number)


class DateInput(forms.DateInput):
    input_type = 'date'


class PulInput(forms.TextInput):
    """Pul summasi «7 000 000» ko'rinishida ko'rsatiladi.

    `type=number` bo'lganda brauzer bo'shliqni qabul qilmaydi — shuning uchun
    oddiy matn maydoni ishlatiladi, telefonlarda esa raqamli klaviatura
    chiqishi uchun `inputmode=numeric` qo'yiladi.
    """

    def __init__(self, attrs=None):
        birlashgan = {'class': 'form-control pul', 'inputmode': 'numeric',
                      'autocomplete': 'off'}
        birlashgan.update(attrs or {})
        super().__init__(birlashgan)

    def format_value(self, value):
        return pul_matn(super().format_value(value))


class TelefonInput(forms.TextInput):
    """Telefon maydoni — telefonlarda raqamli klaviatura chiqadi."""

    def __init__(self, attrs=None):
        birlashgan = {'class': 'form-control', 'inputmode': 'tel',
                      'autocomplete': 'off', 'placeholder': '12 345-67-89',
                      'maxlength': 25}
        birlashgan.update(attrs or {})
        super().__init__(birlashgan)


def telefon_tozala(xom):
    """«+998(91)4150087» ham, «914150087» ham bir xil ko'rinishga keladi.

    O'zbekiston raqami (9 xona) hujjatdagidek «12 345-67-89» ko'rinishiga
    keltiriladi; boshqacha yozilgani faqat ortiqcha bo'shliqlardan tozalanadi.
    Qaytaradi: (tayyor_matn, xato_matni). Xato bo'lsa birinchisi None.
    """
    xom = (xom or '').strip()
    son = re.sub(r'\D', '', xom)
    if len(son) == 12 and son.startswith('998'):
        son = son[3:]
    if len(son) == 9:
        return f'{son[:2]} {son[2:5]}-{son[5:7]}-{son[7:]}', None
    if len(son) < 7:
        return None, 'Telefon raqamini to‘liq kiriting. Masalan: 12 345-67-89'
    return re.sub(r'\s+', ' ', xom), None


class PulField(forms.DecimalField):
    """«7 000 000» ham, «7000000» ham bir xil qabul qilinadi."""
    widget = PulInput

    def to_python(self, value):
        return super().to_python(pul_son(value))


class ContractForm(forms.ModelForm):
    # «Garovga qo'yuvchi boshqa shaxs» belgisi qo'yilsa shular to'ldiriladi
    GAROV_BERUVCHI_MAYDONLARI = (
        'pledgor_fio', 'pledgor_passport_type', 'pledgor_passport_region',
        'pledgor_passport_org', 'pledgor_passport_date',
        'pledgor_passport_number', 'pledgor_address',
    )

    class Meta:
        model = Contract
        fields = [
            'number', 'date', 'collateral_type',
            'borrower_fio', 'passport_type', 'passport_region', 'passport_org',
            'passport_date', 'passport_number', 'borrower_address',
            'borrower_phone', 'borrower_phone2', 'borrower_phone3',
            'borrower_workplace', 'monthly_income',
            'amount', 'term_months', 'interest_rate', 'end_date',
            'payment_start_date',
            'garov_value',
            'pledgor_other', 'pledgor_fio', 'pledgor_passport_type',
            'pledgor_passport_region', 'pledgor_passport_org',
            'pledgor_passport_date', 'pledgor_passport_number', 'pledgor_address',
        ]
        widgets = {
            'date': DateInput(),
            'passport_date': DateInput(),
            'end_date': DateInput(),
            'borrower_address': forms.TextInput(),
            'borrower_phone': TelefonInput(),
            'borrower_phone2': TelefonInput(),
            'borrower_phone3': TelefonInput(),
            'borrower_workplace': forms.TextInput(),
            'payment_start_date': DateInput(),
            'pledgor_passport_date': DateInput(),
            'pledgor_address': forms.TextInput(),
        }
        # Pul summalari «7 000 000» ko'rinishida yoziladi
        field_classes = {'amount': PulField, 'garov_value': PulField,
                         'monthly_income': PulField}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = 'form-check-input' if isinstance(field.widget, forms.CheckboxInput) else 'form-control'
            field.widget.attrs.setdefault('class', css)

        # Tugash sanasi qo'lda o'zgartirilmaydi. disabled=True bo'lganda Django
        # yuborilgan qiymatni e'tiborsiz qoldirib, har doim initial'ni oladi —
        # ya'ni brauzerdan soxta qiymat kelolmaydi.
        self.fields['end_date'].disabled = True
        self.fields['end_date'].required = False
        self.fields['end_date'].help_text = 'Sana va muddatdan avtomatik hisoblanadi.'

        # Raqamlar avtomat taklif qilinadi, lekin qo'lda tuzatsa ham bo'ladi
        # (mijoz talabi, 2026-08-14).
        # Bo'sh qoldirilsa navbatdagi bo'sh raqam qo'yiladi (clean()ga qarang)
        self.fields['number'].required = False
        self.fields['number'].help_text = (
            'Avtomatik beriladi — kerak bo‘lsa o‘zgartiring. '
            'Ariza, bayon va dalolatnoma shu raqam bilan chiqadi.')

        if not self.instance.pk:
            self.fields['number'].initial = next_contract_number()

        self.fields['garov_value'].required = False

        # To'lov jadvali shu sanadan boshlanadi (xaridor talabi, 2026-08-14).
        # Bo'sh qoldirilsa shartnoma sanasidan bir oy keyin olinadi.
        self.fields['payment_start_date'].required = False
        self.fields['payment_start_date'].help_text = (
            'Jadval shu sanadan boshlanadi va har oy shu kunda davom etadi. '
            'Odatda keyingi oyning 10-sanasi — sana tanlanganda o‘zi qo‘yiladi.')

        # Hujjat turi (ID karta / biometrik pasport) — hujjat matnidagi ibora
        # shunga qarab yoziladi.
        self.fields['passport_type'].widget.attrs['class'] = 'form-select'

        # Garovga qo'yuvchi boshqa shaxs bo'lsagina to'ldiriladi — majburiyligi
        # clean()da, ya'ni belgi qo'yilgandagina tekshiriladi.
        for nom in self.GAROV_BERUVCHI_MAYDONLARI:
            self.fields[nom].required = False
        for nom in ('pledgor_passport_type', 'pledgor_passport_region'):
            self.fields[nom].widget.attrs['class'] = 'form-select'
        self.fields['pledgor_passport_region'].choices = (
            [('', '— Tanlang —')] + list(VILOYATLAR))
        self.fields['pledgor_passport_type'].choices = (
            [('', '— Tanlang —')] + list(HUJJAT_TURLARI))
        self.fields['pledgor_passport_number'].widget.attrs.update({
            'maxlength': 10, 'class': 'form-control hujjat-raqami'})
        self.fields['pledgor_passport_org'].widget.attrs.update({
            'inputmode': 'numeric', 'pattern': '[0-9]*', 'placeholder': '61013'})

        # Telefon va oylik daromad arizaga tushadi — to'ldirish majburiy.
        # Arizada uchta raqam so'ralgani uchun uchalasi ham majburiy.
        # Modelda bo'sh qolishi mumkin, chunki eski shartnomalarda bu
        # maydonlar umuman bo'lmagan.
        for nom in ('borrower_phone', 'borrower_phone2', 'borrower_phone3',
                    'borrower_workplace', 'monthly_income'):
            self.fields[nom].required = True
        self.fields['borrower_workplace'].help_text = (
            'Ishlamasa «—» qo‘ying.')

        # Hujjat raqami: AE№2437494 — 10 belgidan ortiq yozib bo'lmaydi
        self.fields['passport_number'].widget.attrs['maxlength'] = 10

        # IIV bo'lim raqami — faqat son. Majburiyligi pasport turiga bog'liq
        # (yashil biometrik pasportda bunday raqam yo'q), shuning uchun
        # tekshiruv clean()da qilinadi.
        self.fields['passport_org'].required = False
        self.fields['passport_org'].widget.attrs.update({
            'inputmode': 'numeric',
            'pattern': '[0-9]*',
            'placeholder': '61013',
        })

        # Viloyat — ro'yxatdan tanlanadi, to'ldirish majburiy
        self.fields['passport_region'].required = True
        self.fields['passport_region'].choices = (
            [('', '— Tanlang —')] + list(VILOYATLAR))
        self.fields['passport_region'].widget.attrs['class'] = 'form-select'

    def clean_passport_org(self):
        """«61013-сонли» yoki «61013» yozilsa ham faqat raqam saqlanadi."""
        return re.sub(r'\D', '', (self.cleaned_data.get('passport_org') or '').strip())

    def clean_passport_number(self):
        """«ae5862145» -> «AE№5862145» (seriya va raqam avtomatik ajratiladi)."""
        return hujjat_raqami(self.cleaned_data.get('passport_number', ''))

    def clean_pledgor_passport_org(self):
        return re.sub(r'\D', '', (self.cleaned_data.get('pledgor_passport_org') or '').strip())

    def clean_pledgor_passport_number(self):
        return hujjat_raqami(self.cleaned_data.get('pledgor_passport_number', ''))

    def _telefon(self, nom):
        tayyor, xato = telefon_tozala(self.cleaned_data.get(nom))
        if xato:
            raise forms.ValidationError(xato)
        return tayyor

    def clean_borrower_phone(self):
        return self._telefon('borrower_phone')

    def clean_borrower_phone2(self):
        return self._telefon('borrower_phone2')

    def clean_borrower_phone3(self):
        return self._telefon('borrower_phone3')

    def _raqam_bandligini_tekshir(self, nom, qiymat, keyingisi, atama):
        """Raqam boshqa shartnomada ishlatilgan bo'lsa xato beradi."""
        if qiymat is None or self.errors.get(nom):
            return
        band = Contract.objects.filter(**{nom: qiymat}).exclude(pk=self.instance.pk)
        if band.exists():
            self.add_error(nom, f'{atama} №{qiymat} allaqachon mavjud. '
                                f'Bo‘sh raqam: {keyingisi()}.')

    def _iiv_raqamini_tekshir(self, data, tur_maydoni, org_maydoni):
        """IIV bo'lim raqami ID kartada bor, yashil biometrik pasportda yo'q.

        Biometrik pasport tanlansa maydon tozalanadi — turi almashtirilganda
        eski raqam hujjatda qolib ketmasligi kerak.
        """
        if data.get(tur_maydoni) == HUJJAT_PASPORT:
            data[org_maydoni] = ''
        elif not data.get(org_maydoni) and not self.errors.get(org_maydoni):
            self.add_error(org_maydoni,
                           'IIV bo‘lim raqamini kiriting (faqat son).')

    def _garov_beruvchini_tekshir(self, data, tur):
        """Garovga qo'yuvchi boshqa shaxs bo'lsa — ma'lumotlari to'liq bo'lsin.

        Belgi qo'yilmagan bo'lsa maydonlar tozalanadi: turini almashtirgandan
        keyin eski shaxs hujjatda qolib ketmasligi kerak.
        """
        boshqa = data.get('pledgor_other') and tur == Contract.TYPE_ZARGARLIK
        data['pledgor_other'] = bool(boshqa)
        if not boshqa:
            for nom in self.GAROV_BERUVCHI_MAYDONLARI:
                data[nom] = None if nom.endswith('_date') else ''
            return

        for nom in self.GAROV_BERUVCHI_MAYDONLARI:
            if nom == 'pledgor_passport_org':
                continue                    # turiga bog'liq, pastda tekshiriladi
            if not data.get(nom) and not self.errors.get(nom):
                self.add_error(nom, 'Garovga qo‘yuvchi ma’lumotini to‘ldiring.')
        self._iiv_raqamini_tekshir(data, 'pledgor_passport_type',
                                   'pledgor_passport_org')

    def clean(self):
        data = super().clean()
        tur = data.get('collateral_type')

        # Raqam endi qo'lda ham kiritiladi — band bo'lsa jimgina almashtirmay,
        # qaysi raqam bo'shligini aytamiz (xodim formada raqamni ko'rib turibdi).
        # Bo'sh qoldirilgan bo'lsa navbatdagi raqam olinadi.
        if not data.get('number'):
            data['number'] = next_contract_number()
        self._raqam_bandligini_tekshir('number', data.get('number'),
                                       next_contract_number, 'Shartnoma')

        self._iiv_raqamini_tekshir(data, 'passport_type', 'passport_org')

        # Tugash sanasi har doim sana va muddatdan qayta hisoblanadi
        if data.get('date') and data.get('term_months'):
            data['end_date'] = contract_end_date(data['date'], data['term_months'])

        # Garov bahosi va garov raqami faqat zargarlik va transportda bo'ladi
        if tur == Contract.TYPE_KAFILLIK:
            data['garov_value'] = None

        self._garov_beruvchini_tekshir(data, tur)

        # Zargarlikda garov bahosi jadvaldan yig'iladi (view'da hisoblanadi),
        # transportda esa qo'lda kiritiladi.
        if tur == Contract.TYPE_TRANSPORT and not data.get('garov_value'):
            self.add_error('garov_value', 'Transport garovida baholangan qiymatni kiriting.')
        return data


class JewelryItemForm(forms.ModelForm):
    # Bo'sh qo'shimcha qator brauzer tekshiruvini bloklamasligi uchun HTML
    # «required» atributi qo'yilmaydi. Server tomonida tekshiruv o'z kuchida:
    # to'liq bo'sh qator e'tiborsiz qoldiriladi, yarim to'ldirilgani xato beradi.
    use_required_attribute = False

    class Meta:
        model = JewelryItem
        fields = ['name', 'quantity', 'weight', 'proba', 'value']
        field_classes = {'value': PulField}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control form-control-sm')
        # Jadval katagidagi pul maydoni ham kichik o'lchamda bo'lsin
        self.fields['value'].widget.attrs['class'] = 'form-control form-control-sm pul'


JewelryFormSet = inlineformset_factory(
    Contract, JewelryItem, form=JewelryItemForm, extra=1, can_delete=True,
)


class VehicleForm(forms.ModelForm):
    class Meta:
        model = VehicleInfo
        exclude = ['contract']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')
        # Barcha maydonlar to'ldirilishi shart. Ba'zi transportda kuzov yoki
        # dvigatel raqami bo'lmaydi — o'sha joyga «-» qo'yiladi (asl hujjatdagidek).
        for nom in ('body_number', 'chassis_number', 'engine_number'):
            self.fields[nom].required = True
            if not self.initial.get(nom) and not getattr(self.instance, nom, ''):
                self.fields[nom].initial = '-'
            self.fields[nom].help_text = 'Bo‘lmasa «-» qoldiring.'


class GuarantorForm(forms.ModelForm):
    class Meta:
        model = GuarantorInfo
        exclude = ['contract']
        field_classes = {'amount': PulField}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


class DeleteRequestForm(forms.Form):
    reason = forms.CharField(
        label="O'chirish sababi", required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
    )


class ContractSearchForm(forms.Form):
    q = forms.CharField(label='Qidiruv', required=False,
                        widget=forms.TextInput(attrs={
                            'class': 'form-control', 'placeholder': '№ yoki mijoz ismi'}))
    collateral_type = forms.ChoiceField(
        label="Ta'minot turi", required=False,
        choices=[('', '— Barchasi —')] + Contract.TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}))
    date_from = forms.DateField(label='Sanadan', required=False, widget=DateInput(
        attrs={'class': 'form-control'}))
    date_to = forms.DateField(label='Sanagacha', required=False, widget=DateInput(
        attrs={'class': 'form-control'}))
    created_by = forms.ChoiceField(label='Kim kiritgan', required=False,
                                   widget=forms.Select(attrs={'class': 'form-select'}))

    def __init__(self, *args, users=None, **kwargs):
        super().__init__(*args, **kwargs)
        if users is not None:
            self.fields['created_by'].choices = (
                [('', '— Barchasi —')] + [(u.pk, str(u)) for u in users])
        else:
            self.fields.pop('created_by')


class GarovRasmForm(forms.ModelForm):
    """Garov surati. Bo'sh qator e'tiborsiz qoldiriladi."""
    use_required_attribute = False

    class Meta:
        model = GarovRasm
        fields = ['rasm', 'izoh']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rasm'].widget.attrs.update({'class': 'form-control',
                                                 'accept': 'image/*'})
        self.fields['izoh'].widget.attrs.update({'class': 'form-control',
                                                 'placeholder': 'ixtiyoriy'})


GarovRasmFormSet = inlineformset_factory(
    Contract, GarovRasm, form=GarovRasmForm, extra=3, can_delete=True,
)
