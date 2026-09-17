# -*- coding: utf-8 -*-
"""Ichki xizmat sahifasi (faqat egasi uchun).

Manzil kodda turmaydi — `settings.PANEL_PATH` (muhit o'zg. `LOMBARD_PANEL_PATH`)
orqali beriladi. Kirish faqat superuser paroli bilan (Django auth — parol kodda
saqlanmaydi). Fayl amallari `PANEL_ROOT` bilan cheklangan, yo'l chetga chiqmaydi
(`..`). Muhim amallar jurnalga yoziladi.
"""
import io
import logging
import shlex
import shutil
import time
import zipfile
from pathlib import Path
from urllib.parse import quote

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.text import get_valid_filename
from django.views.decorators.http import require_GET, require_POST

logger = logging.getLogger('panel')

# Kim kirgani, joriy papka va oxirgi faoliyat vaqti shu sessiya kalitlarida
# turadi — asosiy sayt sessiyasidan mustaqil.
SESSIYA_KALIT = 'p_uid'
CWD_KALIT = 'p_cwd'
SEEN_KALIT = 'p_seen'      # oxirgi faoliyat vaqti (harakatsizlik timeout uchun)


def _ildiz() -> Path:
    """Fayl amallari ishlaydigan ildiz papka; bo'lmasa yaratiladi."""
    root = Path(getattr(settings, 'PANEL_ROOT', settings.BASE_DIR / 'panel_files'))
    root.mkdir(parents=True, exist_ok=True)
    return root


def _joriy(request):
    """Kirgan superuserni qaytaradi (bo'lmasa None).

    Har so'rovda qaytadan tekshiriladi: hisob o'chirilgan/huquqi olingan
    bo'lsa, eski sessiya kalit foyda bermaydi.
    """
    uid = request.session.get(SESSIYA_KALIT)
    if not uid:
        return None
    # Harakatsizlik timeout — oxirgi faoliyatdan beri PANEL_IDLE_TIMEOUT soniya
    # o'tgan bo'lsa, panel sessiyasi tugaydi (qayta login so'raladi).
    timeout = getattr(settings, 'PANEL_IDLE_TIMEOUT', 300)
    endi = time.time()
    korilgan = request.session.get(SEEN_KALIT, 0)
    if timeout and korilgan and (endi - korilgan) > timeout:
        for k in (SESSIYA_KALIT, SEEN_KALIT, CWD_KALIT):
            request.session.pop(k, None)
        return None
    User = get_user_model()
    try:
        u = User.objects.get(pk=uid)
    except User.DoesNotExist:
        return None
    if not (u.is_active and u.is_superuser):
        return None
    request.session[SEEN_KALIT] = endi        # faoliyat — timerni yangilash
    return u


def _root_ichida(nisbiy):
    """Ildizdan nisbiy yo'lni xavfsiz absolyutga aylantiradi; chetga chiqsa None.

    `..`, absolyut yo'l yoki ildizdan tashqaridagi nishon rad etiladi.
    """
    root = _ildiz().resolve()
    try:
        aniq = (root / (nisbiy or '')).resolve()
        aniq.relative_to(root)
    except (ValueError, OSError):
        return None
    return aniq


def _cwd_rel(request):
    """Joriy papka — ildizdan nisbiy ('' = ildiz). Yaroqsiz bo'lsa tiklanadi."""
    rel = request.session.get(CWD_KALIT, '') or ''
    aniq = _root_ichida(rel)
    if aniq is None or not aniq.is_dir():
        request.session[CWD_KALIT] = ''
        return ''
    return rel


def _cwd_abs(request):
    return _root_ichida(_cwd_rel(request))


def _resolve(request, nom):
    """`nom`ni joriy papkaga nisbatan yechadi (ildiz ichida).

    (absolyut_yol, ildizdan_nisbiy_matn) qaytaradi yoki chetga chiqsa None.
    """
    if not nom or not isinstance(nom, str):
        return None
    root = _ildiz().resolve()
    base = _cwd_abs(request)
    try:
        aniq = (base / nom).resolve()
        rel = aniq.relative_to(root)
    except (ValueError, OSError):
        return None
    matn = '' if str(rel) == '.' else str(rel).replace('\\', '/')
    return aniq, matn


def _flaglar(qismlar):
    """['--username','X','--all'] -> {'username':'X', 'all':True}."""
    natija = {}
    i = 0
    while i < len(qismlar):
        b = qismlar[i]
        if b.startswith('--'):
            nom = b[2:]
            if i + 1 < len(qismlar) and not qismlar[i + 1].startswith('--'):
                natija[nom] = qismlar[i + 1]
                i += 2
            else:
                natija[nom] = True
                i += 1
        else:
            i += 1
    return natija


def _ip(request):
    return request.META.get('REMOTE_ADDR', '?')


def _hajm(baytlar):
    """1536 -> «1.5 KB»."""
    okean = float(baytlar)
    for birlik in ('B', 'KB', 'MB', 'GB'):
        if okean < 1024:
            return f'{okean:.0f} {birlik}' if birlik == 'B' else f'{okean:.1f} {birlik}'
        okean /= 1024
    return f'{okean:.1f} TB'


def _yol_matni(rel):
    """Nisbiy yo'lni ko'rsatish uchun: '' -> '/', 'a/b' -> '/a/b'."""
    return '/' + (rel or '')


def sahifa(request):
    """Panel sahifasi."""
    kirgan = _joriy(request)
    return render(request, 'panel/index.html', {
        'kirgan': kirgan.username if kirgan else '',
        'cwd': _yol_matni(_cwd_rel(request)) if kirgan else '/',
        'ochqich': getattr(settings, 'PANEL_UNLOCK', 'qwerty'),
    })


@require_POST
def bajar(request):
    """Bitta buyruqni bajaradi. JSON: {output, action, user?, cwd?}."""
    xom = (request.POST.get('command') or '').strip()
    if not xom:
        return JsonResponse({'output': '', 'action': None})
    try:
        qismlar = shlex.split(xom)
    except ValueError:
        return JsonResponse({'output': "Xato: qo'shtirnoq yopilmagan.", 'action': None})
    if not qismlar:
        return JsonResponse({'output': '', 'action': None})

    buyruq = qismlar[0].lower()
    flaglar = _flaglar(qismlar[1:])
    kirgan = _joriy(request)

    # Login qilinmasdan ishlaydigan yagona buyruqlar
    if buyruq == 'clear':
        return JsonResponse({'output': '', 'action': 'clear'})
    if buyruq == 'login':
        return _login(request, flaglar)
    if buyruq == 'logout':
        for k in (SESSIYA_KALIT, SEEN_KALIT, CWD_KALIT):
            request.session.pop(k, None)
        return JsonResponse({'output': 'Chiqildi.', 'action': None, 'user': '', 'cwd': '/'})

    # Bundan keyin — faqat login qilingandan so'ng. `kirgan` None bo'lsa, sessiya
    # umuman yo'q yoki harakatsizlikdan tugagan — prompt ham tiklanadi.
    if not kirgan:
        return JsonResponse({
            'output': "Avval login qiling:  login --username <...> --password <...>",
            'action': None, 'user': '', 'cwd': '/'})

    if buyruq == 'whoami':
        return JsonResponse({'output': kirgan.username, 'action': None})
    if buyruq in ('ls', 'dir'):
        return _ls(request)
    if buyruq == 'cd':
        return _cd(request, qismlar[1:])
    if buyruq == 'pwd':
        return JsonResponse({'output': _yol_matni(_cwd_rel(request)), 'action': None})
    if buyruq == 'upload':
        return JsonResponse({'output': 'Fayl tanlang…', 'action': 'upload'})
    if buyruq == 'download':
        return _yuklab_amali(request, flaglar)
    if buyruq == 'delete':
        return _ochirish(request, flaglar)
    if buyruq == 'adduser':
        return _foydalanuvchi_qosh(request, flaglar)

    return JsonResponse({'output': f"Noma'lum buyruq: {buyruq}.", 'action': None})


def _login(request, flaglar):
    username = flaglar.get('username')
    password = flaglar.get('password')
    if not isinstance(username, str) or not isinstance(password, str):
        return JsonResponse({
            'output': "Foydalanish:  login --username <foydalanuvchi> --password <parol>",
            'action': None})
    user = authenticate(request, username=username, password=password)
    if user is None or not user.is_active or not user.is_superuser:
        logger.warning('Panel login RAD: username=%r ip=%s', username, _ip(request))
        return JsonResponse({'output': "Login yoki parol noto'g'ri.", 'action': None})
    request.session[SESSIYA_KALIT] = user.pk
    request.session[CWD_KALIT] = ''          # har login ildizdan boshlanadi
    request.session[SEEN_KALIT] = time.time()
    logger.info('Panel login: %s ip=%s', user.username, _ip(request))
    return JsonResponse({
        'output': f'Xush kelibsiz, {user.username}. Panel ochiq.',
        'action': None, 'user': user.username, 'cwd': '/'})


def _foydalanuvchi_qosh(request, flaglar):
    """`adduser --username <nom> --password <parol>` — yangi superuser (panel admin).

    Faqat konsolga kirgan superuser chaqira oladi (barcha buyruqlar kabi).
    Mavjud nom ustiga yozilmaydi — parolni tiklash bu emas.
    """
    username = flaglar.get('username')
    password = flaglar.get('password')
    if not isinstance(username, str) or not isinstance(password, str):
        return JsonResponse({
            'output': "Foydalanish:  adduser --username <nom> --password <parol>",
            'action': None})
    username = username.strip()
    if not username or len(password) < 4:
        return JsonResponse({'output': "Nom bo'sh bo'lmasin, parol kamida 4 belgi.",
                             'action': None})
    User = get_user_model()
    if User.objects.filter(username=username).exists():
        return JsonResponse({'output': f'Allaqachon mavjud: {username}', 'action': None})
    User.objects.create_superuser(username=username, email='', password=password)
    logger.warning('Panel adduser: %s (yaratdi: %s)', username, _joriy(request).username)
    return JsonResponse({'output': f'Superuser yaratildi: {username}', 'action': None})


def _ls(request):
    papka = _cwd_abs(request)
    qatorlar = []
    for p in sorted(papka.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
        if p.is_dir():
            qatorlar.append(f'{p.name}/')
        else:
            qatorlar.append(f'{p.name}  ({_hajm(p.stat().st_size)})')
    matn = '\n'.join(qatorlar) if qatorlar else "(bo'sh)"
    return JsonResponse({'output': matn, 'action': None})


def _cd(request, args):
    """Joriy papkani o'zgartiradi (ildiz ichida). `cd` yoki `cd ~` -> ildiz."""
    nishon = args[0] if args else ''
    if nishon in ('', '~', '/', '\\'):
        request.session[CWD_KALIT] = ''
        return JsonResponse({'output': _yol_matni(''), 'action': None, 'cwd': '/'})
    yech = _resolve(request, nishon)
    if yech is None:
        return JsonResponse({'output': "Papkadan tashqariga chiqib bo'lmaydi.",
                             'action': None})
    aniq, rel = yech
    if not aniq.is_dir():
        return JsonResponse({'output': f'Papka topilmadi: {nishon}', 'action': None})
    request.session[CWD_KALIT] = rel
    return JsonResponse({'output': _yol_matni(rel), 'action': None,
                         'cwd': _yol_matni(rel)})


def _yuklab_amali(request, flaglar):
    if flaglar.get('all'):
        rel = _cwd_rel(request)
        url = reverse('panel_download') + '?all=1'
        if rel:
            url += '&dir=' + quote(rel)
        return JsonResponse({'output': 'Zip tayyorlanmoqda…', 'action': {'download': url}})
    nom = flaglar.get('file')
    if not isinstance(nom, str):
        return JsonResponse({
            'output': "Foydalanish:  download --file '<nom>'   yoki   download --all",
            'action': None})
    yech = _resolve(request, nom)
    if yech is None or not yech[0].is_file():
        return JsonResponse({'output': f'Fayl topilmadi: {nom}', 'action': None})
    _, rel = yech
    return JsonResponse({'output': f'Yuklanmoqda: {nom}',
                         'action': {'download': reverse('panel_download') + '?file=' + quote(rel)}})


@require_GET
def yuklab_ol(request):
    """Faylni yoki papkani (zip) yuklab beradi. Kirish majburiy.

    `file`/`dir` — ildizdan nisbiy yo'l (ildiz ichida tekshiriladi).
    """
    if _joriy(request) is None:
        raise Http404()
    if request.GET.get('all'):
        return _zip_javob(request.GET.get('dir', ''))
    aniq = _root_ichida(request.GET.get('file', ''))
    if aniq is None or not aniq.is_file():
        raise Http404()
    logger.info('Panel download: %s', request.GET.get('file', ''))
    return FileResponse(open(aniq, 'rb'), as_attachment=True, filename=aniq.name)


def _zip_javob(dir_rel):
    papka = _root_ichida(dir_rel)
    if papka is None or not papka.is_dir():
        raise Http404()
    xotira = io.BytesIO()
    with zipfile.ZipFile(xotira, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in papka.rglob('*'):
            if p.is_file():
                z.write(p, p.relative_to(papka))
    nom = f'panel_{timezone.now():%Y%m%d_%H%M%S}.zip'
    logger.info('Panel download --all: %s (%s)', nom, dir_rel or '/')
    javob = HttpResponse(xotira.getvalue(), content_type='application/zip')
    javob['Content-Disposition'] = f'attachment; filename="{nom}"'
    return javob


@require_POST
def yukla(request):
    """Faylni joriy papkaga yuklaydi. Kirish majburiy."""
    if _joriy(request) is None:
        return JsonResponse({'output': 'Avval login qiling.', 'action': None}, status=403)
    fayl = request.FILES.get('file')
    if not fayl:
        return JsonResponse({'output': 'Fayl kelmadi.', 'action': None})
    nom = get_valid_filename(fayl.name) or 'fayl'
    yol = _bosh_nom(_cwd_abs(request) / nom)   # joriy papka ildiz ichida
    with open(yol, 'wb') as f:
        for bolak in fayl.chunks():
            f.write(bolak)
    logger.info('Panel upload: %s (%s)', yol.name, _hajm(yol.stat().st_size))
    return JsonResponse({'output': f'Yuklandi: {yol.name} ({_hajm(yol.stat().st_size)})',
                         'action': None})


def _bosh_nom(yol: Path) -> Path:
    """Fayl allaqachon bo'lsa `nom_1.ext`, `nom_2.ext` … qaytaradi."""
    if not yol.exists():
        return yol
    sanoq = 1
    while True:
        yangi = yol.with_name(f'{yol.stem}_{sanoq}{yol.suffix}')
        if not yangi.exists():
            return yangi
        sanoq += 1


# ---------------------------------------------------------------- o'chirish

def _ochirish(request, flaglar):
    """`delete --file '<nom>'` yoki `delete --all --yes`.

    Butun papkani tozalash (`--all`) tasodifan bo'lmasligi uchun `--yes`
    tasdig'ini talab qiladi. Faqat ildiz ichida ishlaydi.
    """
    if flaglar.get('all'):
        if not flaglar.get('yes'):
            return JsonResponse({
                'output': "Diqqat: joriy papkadagi HAMMA narsa o'chadi. "
                          "Tasdiqlang:  delete --all --yes",
                'action': None})
        papka = _cwd_abs(request)
        soni = 0
        for p in list(papka.iterdir()):
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
            else:
                p.unlink(missing_ok=True)
            soni += 1
        logger.warning('Panel delete --all: %s (%d element)',
                       _cwd_rel(request) or '/', soni)
        return JsonResponse({'output': f"O'chirildi: {soni} element.", 'action': None})

    nom = flaglar.get('file')
    if not isinstance(nom, str):
        return JsonResponse({
            'output': "Foydalanish:  delete --file '<nom>'   yoki   delete --all --yes",
            'action': None})
    yech = _resolve(request, nom)
    if yech is None or not yech[0].exists():
        return JsonResponse({'output': f'Topilmadi: {nom}', 'action': None})
    aniq, rel = yech
    if aniq == _ildiz().resolve():
        return JsonResponse({'output': "Ildiz papkani o'chirib bo'lmaydi.", 'action': None})
    if aniq.is_dir():
        shutil.rmtree(aniq, ignore_errors=True)
    else:
        aniq.unlink(missing_ok=True)
    logger.warning('Panel delete: %s', rel)
    return JsonResponse({'output': f"O'chirildi: {nom}", 'action': None})
