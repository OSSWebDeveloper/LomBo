# -*- coding: utf-8 -*-
"""Dastur versiyasini yangilaydi — yagona joydan.

    python versiya.py                      hozirgi versiyani ko'rsatadi
    python versiya.py 1.2.0 "Qisqa izoh"   versiyani oshiradi
    python versiya.py 1.2.0 "Izoh" --push  + GitHub'ga yuboradi

Nima qiladi:
  * `versiya.txt` ni yangilaydi — uni sayt ham (sahifa pastida), ORNATISH.bat
    ham (yangilanish kerakmi yoki yo'qmi) o'qiydi;
  * `VERSIYALAR.md` ga yangi qatorni sana bilan qo'shadi;
  * shu ikki faylni commit qiladi va `v1.2.0` degan teg qo'yadi;
  * `--push` berilsa — commit va tegni GitHub'ga yuboradi.

Boshqa o'zgargan fayllar bor bo'lsa ular commitga TUSHMAYDI (avval ularni
o'zingiz commit qiling) — `--hammasi` bayrog'i bilan majburlash mumkin.
"""
import argparse
import datetime
import re
import subprocess
import sys
from pathlib import Path

ILDIZ = Path(__file__).resolve().parent
VERSIYA_FAYL = ILDIZ / 'versiya.txt'
TARIX_FAYL = ILDIZ / 'VERSIYALAR.md'
KOLIP = re.compile(r'^\d+\.\d+\.\d+$')


def hozirgi():
    if not VERSIYA_FAYL.exists():
        return '0.0.0'
    return VERSIYA_FAYL.read_text(encoding='utf-8').strip()


def raqamlar(v):
    return tuple(int(q) for q in v.split('.'))


def git(*argv, tekshir=True):
    natija = subprocess.run(['git'] + list(argv), cwd=ILDIZ,
                            capture_output=True, text=True, encoding='utf-8')
    if tekshir and natija.returncode != 0:
        chiqish = (natija.stderr or natija.stdout or '').strip()
        raise SystemExit("XATO (git %s): %s" % (' '.join(argv), chiqish))
    return (natija.stdout or '').strip()


def tarixga_yoz(yangi, izoh):
    """Yangi versiyani VERSIYALAR.md ning tepasiga qo'shadi."""
    sana = datetime.date.today().isoformat()
    yozuv = '## %s — %s\n\n%s\n\n' % (yangi, sana, izoh)
    if not TARIX_FAYL.exists():
        TARIX_FAYL.write_text('# Versiyalar tarixi\n\n' + yozuv, encoding='utf-8')
        return
    matn = TARIX_FAYL.read_text(encoding='utf-8')
    sarlavha = '# Versiyalar tarixi\n\n'
    if matn.startswith(sarlavha):
        matn = sarlavha + yozuv + matn[len(sarlavha):]
    else:
        matn = sarlavha + yozuv + matn
    TARIX_FAYL.write_text(matn, encoding='utf-8')


def main(argv=None):
    p = argparse.ArgumentParser(description='Dastur versiyasini yangilaydi.')
    p.add_argument('yangi', nargs='?', help='Yangi versiya, masalan 1.2.0')
    p.add_argument('izoh', nargs='?', help='Nima o\'zgardi (bir-ikki jumla)')
    p.add_argument('--push', action='store_true', help='GitHub\'ga yuborilsin')
    p.add_argument('--hammasi', action='store_true',
                   help='Boshqa o\'zgarishlar ham shu commitga qo\'shilsin')
    a = p.parse_args(argv)

    eski = hozirgi()
    if not a.yangi:
        print('Hozirgi versiya: %s' % eski)
        return 0

    if not KOLIP.match(a.yangi):
        raise SystemExit('XATO: versiya "1.2.0" ko\'rinishida bo\'lsin.')
    if raqamlar(a.yangi) <= raqamlar(eski):
        raise SystemExit('XATO: %s -> %s. Yangi versiya kattaroq bo\'lishi kerak.'
                         % (eski, a.yangi))
    if not a.izoh:
        raise SystemExit('XATO: izoh yozing — u VERSIYALAR.md ga tushadi.')

    VERSIYA_FAYL.write_text(a.yangi, encoding='utf-8')
    tarixga_yoz(a.yangi, a.izoh)
    print('%s -> %s' % (eski, a.yangi))

    if a.hammasi:
        git('add', '-A')
    else:
        git('add', str(VERSIYA_FAYL.name), str(TARIX_FAYL.name))
        qolgan = git('diff', '--name-only')
        if qolgan:
            print('Eslatma: commitga tushmagan o\'zgarishlar bor:')
            for q in qolgan.splitlines():
                print('   ', q)

    git('commit', '-m', 'Versiya %s — %s' % (a.yangi, a.izoh))
    git('tag', '-a', 'v%s' % a.yangi, '-m', a.izoh)
    print('Commit va teg tayyor: v%s' % a.yangi)

    if a.push:
        git('push', 'origin', 'HEAD')
        git('push', 'origin', 'v%s' % a.yangi)
        print('GitHub\'ga yuborildi.')
    else:
        print('Yuborish uchun:  git push origin HEAD && git push origin v%s' % a.yangi)
    return 0


if __name__ == '__main__':
    sys.exit(main())
