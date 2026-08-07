# -*- coding: utf-8 -*-
import re

from django import forms
from django.forms import inlineformset_factory

from .docgen import contract_end_date
from .formatlash import hujjat_raqami, pul_matn, pul_son
from .models import (VILOYATLAR, Contract, GuarantorInfo, JewelryItem, VehicleInfo,
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


class PulField(forms.DecimalField):
    """«7 000 000» ham, «7000000» ham bir xil qabul qilinadi."""
    widget = PulInput

    def to_python(self, value):
        return super().to_python(pul_son(value))


class ContractForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = [
            'number', 'date', 'collateral_type',
            'borrower_fio', 'passport_region', 'passport_org', 'passport_date',
            'passport_number', 'borrower_address', 'borrower_phone', 'monthly_income',
            'amount', 'term_months', 'interest_rate', 'end_date',
            'garov_value',
        ]
        widgets = {
            'date': DateInput(),
            'passport_date': DateInput(),
            'end_date': DateInput(),
            'borrower_address': forms.TextInput(),
            'borrower_phone': forms.TextInput(attrs={
                'inputmode': 'tel', 'autocomplete': 'off',
                'placeholder': '91 415-00-87', 'maxlength': 25}),
        }
        # Pul summalari «7 000 000» ko'rinishida yoziladi
        field_classes = {'amount': PulField, 'garov_value': PulField,
                         'monthly_income': PulField}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = 'form-check-input' if isinstance(field.widget, forms.CheckboxInput) else 'form-control'
            field.widget.attrs.setdefault('class', css)

        # Avtomatik to'ldiriladigan maydonlar qo'lda o'zgartirilmaydi.
        # disabled=True bo'lganda Django yuborilgan qiymatni e'tiborsiz qoldirib,
        # har doim initial'ni oladi — ya'ni brauzerdan soxta qiymat kelolmaydi.
        for nom in ('number', 'end_date'):
            self.fields[nom].disabled = True
            self.fields[nom].required = False

        self.fields['number'].help_text = (
            'Tizim tomonidan avtomatik beriladi. Garov shartnomasi, ariza, '
            'bayon va dalolatnoma ham shu raqam bilan chiqadi.')
        self.fields['end_date'].help_text = 'Sana va muddatdan avtomatik hisoblanadi.'

        if not self.instance.pk:
            self.fields['number'].initial = next_contract_number()

        self.fields['garov_value'].required = False

        # Telefon va oylik daromad arizaga tushadi — to'ldirish majburiy.
        # Modelda bo'sh qolishi mumkin, chunki eski shartnomalarda bu
        # maydonlar umuman bo'lmagan.
        self.fields['borrower_phone'].required = True
        self.fields['monthly_income'].required = True

        # Hujjat raqami: AE№2437494 — 10 belgidan ortiq yozib bo'lmaydi
        self.fields['passport_number'].widget.attrs['maxlength'] = 10

        # IIV bo'lim raqami — faqat son
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
        qiymat = (self.cleaned_data.get('passport_org') or '').strip()
        faqat_son = re.sub(r'\D', '', qiymat)
        if not faqat_son:
            raise forms.ValidationError('IIV bo‘lim raqamini kiriting (faqat son).')
        return faqat_son

    def clean_passport_number(self):
        """«ae5862145» -> «AE№5862145» (seriya va raqam avtomatik ajratiladi)."""
        return hujjat_raqami(self.cleaned_data.get('passport_number', ''))

    def clean_borrower_phone(self):
        """«+998(91)4150087» ham, «914150087» ham bir xil qabul qilinadi.

        O'zbekiston raqami (9 xona) hujjatdagidek «91 415-00-87» ko'rinishiga
        keltiriladi; boshqacha yozilgani faqat ortiqcha bo'shliqlardan tozalanadi.
        """
        xom = (self.cleaned_data.get('borrower_phone') or '').strip()
        son = re.sub(r'\D', '', xom)
        if len(son) == 12 and son.startswith('998'):
            son = son[3:]
        if len(son) == 9:
            return f'{son[:2]} {son[2:5]}-{son[5:7]}-{son[7:]}'
        if len(son) < 7:
            raise forms.ValidationError(
                'Telefon raqamini to‘liq kiriting. Masalan: 91 415-00-87')
        return re.sub(r'\s+', ' ', xom)

    def clean(self):
        data = super().clean()
        tur = data.get('collateral_type')

        # Ikki xodim bir vaqtda forma ochsa ikkalasiga ham bir xil raqam taklif
        # qilinadi. Saqlash paytida band bo'lib qolgan bo'lsa — keyingisini olamiz.
        num = data.get('number')
        if num is not None and Contract.objects.filter(
                number=num).exclude(pk=self.instance.pk).exists():
            data['number'] = next_contract_number()

        # Tugash sanasi har doim sana va muddatdan qayta hisoblanadi
        if data.get('date') and data.get('term_months'):
            data['end_date'] = contract_end_date(data['date'], data['term_months'])

        # Garov bahosi faqat zargarlik va transportda bo'ladi
        if tur == Contract.TYPE_KAFILLIK:
            data['garov_value'] = None

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
