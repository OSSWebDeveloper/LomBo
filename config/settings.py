"""
Django settings — Lombard shartnoma tizimi.
PythonAnywhere bepul tarifiga mos (SQLite, WhiteNoise'siz oddiy static).
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# ============ ISHGA TUSHIRISH REJIMI ============
DEBUG = os.environ.get('LOMBARD_DEBUG', '1') == '1'

# Maxfiy kalit kodda saqlanmaydi — muhit o'zgaruvchisidan olinadi.
# Serverda (PythonAnywhere WSGI faylida) shunday beriladi:
#     os.environ['LOMBARD_SECRET_KEY'] = '<tasodifiy kalit>'
# Lokal ishlashda o'zgaruvchi berilmasa, kalit `.secret_key` faylida
# yasaladi va saqlanadi (bu fayl git'ga tushmaydi).
SECRET_KEY = os.environ.get('LOMBARD_SECRET_KEY', '').strip()

if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured(
            "LOMBARD_SECRET_KEY muhit o'zgaruvchisi berilmagan. "
            "Ishlab chiqarish rejimida (LOMBARD_DEBUG=0) maxfiy kalit majburiy — "
            "WSGI faylida os.environ['LOMBARD_SECRET_KEY'] = '...' deb bering.")
    _kalit_fayl = BASE_DIR / '.secret_key'
    if _kalit_fayl.exists():
        SECRET_KEY = _kalit_fayl.read_text(encoding='utf-8').strip()
    else:
        from django.core.management.utils import get_random_secret_key
        SECRET_KEY = get_random_secret_key()
        _kalit_fayl.write_text(SECRET_KEY, encoding='utf-8')

# Masalan: ['foydalanuvchi.pythonanywhere.com']
ALLOWED_HOSTS = os.environ.get('LOMBARD_HOSTS', '*').split(',')

if not DEBUG:
    # Ishlab chiqarish rejimida himoya avtomatik yoqiladi
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    CSRF_TRUSTED_ORIGINS = [f'https://{h}' for h in ALLOWED_HOSTS if h != '*']

# ============ LOMBARD SOZLAMALARI ============
# Shartnoma avtomatik raqamlash shu raqamdan boshlanadi.
# Bazada bundan katta raqam bo'lsa, eng kattasidan davom etadi.
CONTRACT_START_NUMBER = 200

# Garov shartnomasi o'z hisobida yuritiladi (asosiy shartnoma raqamidan
# mustaqil). Avtomatik raqamlash shu sondan boshlanadi; bazada bundan katta
# raqam bo'lsa, eng kattasidan davom etadi.
GAROV_START_NUMBER = 1

# Ishchi o'zi kiritgan shartnomani necha daqiqa ichida tuzata oladi?
# Shartnoma kiritilgach shu vaqt ichida ishchi xatosini o'zi to'g'rilaydi
# (masalan, ism yoki summani noto'g'ri yozgan bo'lsa). Muddat o'tgach
# tahrirlash faqat vakolatli boshliqda qoladi.
# 0 qo'yilsa ishchi umuman tahrirlay olmaydi.
ISHCHI_TAHRIR_DAQIQA = 60

# To'lov jadvali («1-илова») Word hujjatga qo'shilsinmi?
# 2026-07-30 da vaqtincha o'chirilgan edi; 2026-08-14 da xaridor «Grafik» deb
# aynan shuni so'ragani aniqlandi va qaytarildi.
# Eslatma: shartnoma matnida ilovaga havola bor («1-иловасидаги ... Жадвали»да).
TOLOV_JADVALI_QOSHILSIN = True

# Tashkilot rekvizitlari — Word hujjatlarga shu yerdan qo'yiladi.
LOMBARD_ORG = {
    'name': '“Asia Invest Mikromoliya tashkiloti” МЧЖ',
    'name_short': '“Asia Invest Mikromoliya tashkiloti” МЧЖ',
    # Muqovaning yirik sarlavhasi — «МЧЖ»siz, chunki uning tagida
    # «масъулияти чекланган жамияти» deb yoziladi.
    'title_latin': 'Asia Invest Mikromoliya tashkiloti',
    'director_full': 'Самиев Бахриддин Баходирович',
    'director_short': 'Б.Б.Самиев',
    'employee_short': 'Б.Т.Хўжаев',
    'stir': '309268086',
    'oked': '65220',
    'account': '20216000005489627001',
    'bank': '«ASIA ALLIANCE BANK» Бухоро филиали',
    'bank_name_full': '“Asia Alliance Bank” банкининг Бухоро вилоят филиали',
    'bank_code': '01095',
    # Garov shartnomasida boshqa hisob raqami ko'rsatiladi (2026-08 dagi
    # yurist tahriridan) — mikroqarz shartnomasining 9-bandidagisi o'zgarmagan.
    'garov_account': '20216000405489627001',
    'garov_bank_code': '01137',
    'address': 'Бухоро шахар Б.Накшбанд кўчаси 153-уй',
    'phone': '55 310 00 87, 91 415-00-87',
    # To'lov jadvalining pastidagi murojaat raqamlari (xaridor namunasidan)
    'phone_jadval': '55-310-00-87   91-415-00-87  93-685-21-10',
    'city': 'Бухоро шаҳри',
}

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'contracts',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'accounts.middleware.SaytKirishNazorati',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 4}},
]

LANGUAGE_CODE = 'uz'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
