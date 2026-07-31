# -*- coding: utf-8 -*-
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class SaytKirishFormasi(AuthenticationForm):
    """Saytga faqat boshliq va ishchi kiradi — admin hisobi kirmaydi."""

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.sayt_foydalanuvchisi:
            raise forms.ValidationError(
                'Bu hisob faqat admin panel uchun. Saytga boshliq yoki ishchi '
                'hisobi bilan kiring.',
                code='faqat_admin',
            )


class WorkerCreateForm(UserCreationForm):
    """Boshliq ishchi qo'shadi."""

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name']
        labels = {
            'username': 'Login',
            'first_name': 'Ismi',
            'last_name': 'Familiyasi',
        }

    def __init__(self, *args, boss=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.boss = boss
        self.fields['password1'].label = 'Parol'
        self.fields['password2'].label = 'Parolni takrorlang'
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.ROLE_ISHCHI
        user.added_by = self.boss
        if commit:
            user.save()
        return user


class WorkerEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'is_active']
        labels = {
            'first_name': 'Ismi',
            'last_name': 'Familiyasi',
            'is_active': 'Faol (belgini olib tashlasangiz — kirolmaydi)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = 'form-check-input' if name == 'is_active' else 'form-control'
            field.widget.attrs.setdefault('class', css)


class SetPasswordSimpleForm(forms.Form):
    password1 = forms.CharField(label='Yangi parol', widget=forms.PasswordInput(
        attrs={'class': 'form-control'}))
    password2 = forms.CharField(label='Parolni takrorlang', widget=forms.PasswordInput(
        attrs={'class': 'form-control'}))

    def clean(self):
        data = super().clean()
        if data.get('password1') != data.get('password2'):
            raise forms.ValidationError('Parollar mos kelmadi.')
        if len(data.get('password1') or '') < 4:
            raise forms.ValidationError('Parol kamida 4 belgidan iborat bo\'lsin.')
        return data
