# -*- coding: utf-8 -*-
"""Word hujjatini PDF'ga aylantirish.

Ikki usul ketma-ket sinaladi:
  1. LibreOffice (`soffice`) — Linux serverlarda va o'rnatilgan bo'lsa Windows'da
  2. Microsoft Word — faqat Windows'da, PowerShell orqali (qo'shimcha kutubxona kerak emas)

Ikkalasi ham topilmasa PdfImkoniYoq xatosi ko'tariladi — bunda foydalanuvchiga
Word faylni yuklab olish taklif qilinadi.
"""
import os
import shutil
import subprocess
import tempfile

# Windows'da Word'ni PowerShell orqali chaqirish uchun buyruq
_PS_BUYRUQ = r'''
$ErrorActionPreference = 'Stop'
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {{
    $doc = $word.Documents.Open('{kirish}', $false, $true)
    $doc.SaveAs([ref]'{chiqish}', [ref]17)
    $doc.Close($false)
}} finally {{
    $word.Quit()
}}
'''


class PdfImkoniYoq(RuntimeError):
    """Bu serverda PDF yasash imkoni yo'q."""


def _soffice_yoli():
    yol = shutil.which('soffice') or shutil.which('libreoffice')
    if yol:
        return yol
    # Windows'da PATH'da bo'lmasligi mumkin
    for taxmin in (r'C:\Program Files\LibreOffice\program\soffice.exe',
                   r'C:\Program Files (x86)\LibreOffice\program\soffice.exe'):
        if os.path.exists(taxmin):
            return taxmin
    return None


def _libreoffice_bilan(kirish, papka):
    soffice = _soffice_yoli()
    if not soffice:
        return None
    try:
        subprocess.run(
            [soffice, '--headless', '--convert-to', 'pdf', '--outdir', papka, kirish],
            check=True, capture_output=True, timeout=120,
        )
    except (subprocess.SubprocessError, OSError):
        return None
    natija = os.path.join(papka, os.path.splitext(os.path.basename(kirish))[0] + '.pdf')
    return natija if os.path.exists(natija) else None


def _word_bilan(kirish, papka):
    if os.name != 'nt':
        return None
    powershell = shutil.which('powershell') or shutil.which('pwsh')
    if not powershell:
        return None
    natija = os.path.join(papka, 'natija.pdf')
    buyruq = _PS_BUYRUQ.format(kirish=kirish.replace("'", "''"),
                               chiqish=natija.replace("'", "''"))
    try:
        subprocess.run([powershell, '-NoProfile', '-NonInteractive', '-Command', buyruq],
                       check=True, capture_output=True, timeout=180)
    except (subprocess.SubprocessError, OSError):
        return None
    return natija if os.path.exists(natija) else None


def pdf_imkoni_bor():
    """Sahifada PDF tugmasini ko'rsatish kerakmi?"""
    if _soffice_yoli():
        return True
    return os.name == 'nt' and bool(shutil.which('powershell') or shutil.which('pwsh'))


def docx_dan_pdf(docx_baytlari: bytes) -> bytes:
    """Word baytlarini PDF baytlariga aylantiradi."""
    with tempfile.TemporaryDirectory() as papka:
        kirish = os.path.join(papka, 'hujjat.docx')
        with open(kirish, 'wb') as f:
            f.write(docx_baytlari)

        for usul in (_libreoffice_bilan, _word_bilan):
            natija = usul(kirish, papka)
            if natija:
                with open(natija, 'rb') as f:
                    return f.read()

    raise PdfImkoniYoq(
        'Bu serverda PDF yasash imkoni yo‘q. PDF uchun LibreOffice o‘rnatilishi '
        'kerak. Hozircha Word faylni yuklab olib, o‘zingiz PDF qilib saqlashingiz mumkin.'
    )
