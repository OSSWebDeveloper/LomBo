from django import forms
from django.contrib import admin
from django.contrib.auth import password_validation
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm

from .models import Boshliq, User


# =====================================================================
#  BOSHLIQLAR — sodda forma
# =====================================================================

class BoshliqCreationForm(UserCreationForm):
    """Boshliq qo'shish: faqat 5 ta maydon."""

    class Meta:
        model = Boshliq
        fields = ('username', 'first_name', 'last_name')
        labels = {
            'username': 'Login',
            'first_name': 'Ismi',
            'last_name': 'Familiyasi',
        }
        help_texts = {
            'username': 'Boshliq shu login bilan saytga kiradi.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].label = 'Parol'
        self.fields['password2'].label = 'Parolni takrorlang'
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True


class BoshliqChangeForm(forms.ModelForm):
    """Tahrirlash: parolni shu yerning o'zida almashtirish mumkin."""

    yangi_parol = forms.CharField(
        label='Yangi parol',
        required=False,
        widget=forms.PasswordInput(render_value=False, attrs={'autocomplete': 'new-password'}),
        help_text="Parolni almashtirmoqchi bo'lsangizgina to'ldiring. "
                  "Bo'sh qoldirsangiz eski parol o'zgarishsiz qoladi.",
    )
    yangi_parol_takror = forms.CharField(
        label='Yangi parolni takrorlang',
        required=False,
        widget=forms.PasswordInput(render_value=False, attrs={'autocomplete': 'new-password'}),
    )

    class Meta:
        model = Boshliq
        fields = ('username', 'first_name', 'last_name', 'can_full_edit',
                  'can_edit_template', 'is_active')
        labels = {
            'username': 'Login',
            'first_name': 'Ismi',
            'last_name': 'Familiyasi',
            'is_active': 'Faol',
        }

    def clean(self):
        data = super().clean()
        p1 = data.get('yangi_parol')
        p2 = data.get('yangi_parol_takror')
        if p1 or p2:
            if p1 != p2:
                raise forms.ValidationError('Parollar mos kelmadi — ikkalasini bir xil yozing.')
            password_validation.validate_password(p1, self.instance)
        return data

    def save(self, commit=True):
        boshliq = super().save(commit=False)
        yangi = self.cleaned_data.get('yangi_parol')
        if yangi:
            boshliq.set_password(yangi)
        if commit:
            boshliq.save()
        return boshliq


@admin.register(Boshliq)
class BoshliqAdmin(UserAdmin):
    """Boshliq qo'shish/tahrirlash — ortiqcha maydonlarsiz."""

    add_form = BoshliqCreationForm
    form = BoshliqChangeForm

    list_display = ('username', 'get_full_name', 'can_full_edit',
                    'can_edit_template', 'ishchilar_soni', 'is_active')
    list_filter = ('can_full_edit', 'can_edit_template', 'is_active')
    search_fields = ('username', 'first_name', 'last_name')
    ordering = ('username',)
    filter_horizontal = ()

    # Yangi boshliq qo'shish formasi
    add_fieldsets = (
        ('Kirish ma\'lumotlari', {
            'fields': ('username', 'password1', 'password2'),
        }),
        ('Shaxsiy ma\'lumotlar', {
            'fields': ('first_name', 'last_name'),
        }),
        ('Vakolatlar', {
            'fields': ('can_full_edit', 'can_edit_template'),
            'description': "«To'liq tahrirlash» — mavjud shartnomalarni o'zgartirish. "
                           "«Shablonni o'zgartirish» — Word shablonlarini almashtirish. "
                           "Ikkalasi ham belgilanmasa, boshliq faqat ko'radi, ishchi "
                           "boshqaradi va o'chirish so'rovlarini tasdiqlaydi.",
        }),
    )

    # Mavjud boshliqni tahrirlash formasi
    fieldsets = (
        ('Kirish ma\'lumotlari', {'fields': ('username',)}),
        ('Parolni almashtirish', {
            'fields': ('yangi_parol', 'yangi_parol_takror'),
            'description': "Bu bo'limni faqat parolni almashtirmoqchi bo'lsangiz "
                           "to'ldiring. Eski parolni bilish shart emas.",
        }),
        ('Shaxsiy ma\'lumotlar', {'fields': ('first_name', 'last_name')}),
        ('Vakolatlar', {
            'fields': ('can_full_edit', 'can_edit_template', 'is_active'),
            'description': "Faol belgisini olib tashlasangiz — boshliq saytga "
                           "kira olmaydi, lekin ma'lumotlari saqlanib qoladi.",
        }),
    )

    @admin.display(description='F.I.Sh.')
    def get_full_name(self, obj):
        return obj.get_full_name() or '—'

    @admin.display(description='Ishchilari')
    def ishchilar_soni(self, obj):
        return obj.workers.count()


# =====================================================================
#  BARCHA FOYDALANUVCHILAR — to'liq boshqaruv (kerak bo'lganda)
# =====================================================================

@admin.register(User)
class LombardUserAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'role',
                    'can_full_edit', 'contracts_added', 'added_by', 'is_active')
    list_filter = ('role', 'can_full_edit', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Lombard sozlamalari', {
            'fields': ('role', 'added_by', 'can_full_edit', 'can_edit_template',
                       'contracts_added'),
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Lombard sozlamalari', {
            'fields': ('role', 'first_name', 'last_name', 'can_full_edit'),
        }),
    )
