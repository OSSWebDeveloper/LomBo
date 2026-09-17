# ============================================================
#  Lombard - soat yonidagi (trey) belgi
#
#  Belgi turgan bo'lsa - server ishlayapti, yo'q bo'lsa - ishlamayapti.
#    chap tugma  - saytni Chrome'da ochadi
#    o'ng tugma  - "Dasturni yangilash" va "Serverni to'xtatish"
#
#  Tashqi kutubxona kerak emas - Windows'ning o'z .NET shakllari
#  ishlatiladi. Ishga_tushirish.vbs uni ko'rinmas rejimda chaqiradi.
# ============================================================
$ErrorActionPreference = 'SilentlyContinue'

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# --- ikkita belgi paydo bo'lib qolmasin ---
$yangimi = $false
$muteks = New-Object System.Threading.Mutex($true, 'LombardBelgisi', [ref]$yangimi)
if (-not $yangimi) { return }

$joy = Split-Path -Parent $PSCommandPath

# --- port va manzil ---
$port = '8010'
$portFayli = Join-Path $joy 'port.txt'
if (Test-Path -LiteralPath $portFayli) {
    $oqilgan = (Get-Content -LiteralPath $portFayli -TotalCount 1)
    if ($oqilgan) { $oqilgan = $oqilgan.Trim() }
    if ($oqilgan -match '^\d+$') { $port = $oqilgan }
}
$manzil = "http://127.0.0.1:$port/"

# Server uzoq vaqt ishlamasa, belgi o'zini yopadi (bekorga turmasligi uchun).
# Yangilash paytida server bir necha daqiqaga to'xtaydi - shuni hisobga olamiz.
$tekshirishOraligi = 3000          # millisekund
$yopishChegarasi = 100             # 100 x 3 sekund = 5 daqiqa


function ServerIshlayaptimi {
    $ulandi = $false
    try {
        $mijoz = New-Object System.Net.Sockets.TcpClient
        $natija = $mijoz.BeginConnect('127.0.0.1', [int]$port, $null, $null)
        $ulandi = $natija.AsyncWaitHandle.WaitOne(500, $false)
        if ($ulandi) {
            try { $mijoz.EndConnect($natija) } catch { $ulandi = $false }
        }
        $mijoz.Close()
    } catch { $ulandi = $false }
    return $ulandi
}


function ChromeYoli {
    $kalit = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe'
    $yol = (Get-ItemProperty -Path $kalit -EA 0).'(default)'
    if ($yol -and (Test-Path -LiteralPath $yol)) { return $yol }

    foreach ($y in @(
        (Join-Path $env:ProgramFiles 'Google\Chrome\Application\chrome.exe'),
        (Join-Path ${env:ProgramFiles(x86)} 'Google\Chrome\Application\chrome.exe'),
        (Join-Path $env:LocalAppData 'Google\Chrome\Application\chrome.exe'))) {
        if ($y -and (Test-Path -LiteralPath $y)) { return $y }
    }
    return $null
}


function SaytniOch {
    $chrome = ChromeYoli
    if ($chrome) {
        Start-Process -FilePath $chrome -ArgumentList '--new-window', $manzil
    } else {
        Start-Process $manzil          # standart brauzer
    }
}


# --- belgi va menyu ---
$belgi = New-Object System.Windows.Forms.NotifyIcon
$belgiFayli = Join-Path $joy 'lombard.ico'
if (Test-Path -LiteralPath $belgiFayli) {
    $belgi.Icon = New-Object System.Drawing.Icon($belgiFayli)
} else {
    $belgi.Icon = [System.Drawing.SystemIcons]::Application
}
$belgi.Text = "Lombard"
$belgi.Visible = $false

$menyu = New-Object System.Windows.Forms.ContextMenuStrip
$bandYangilash = $menyu.Items.Add("Dasturni yangilash")
$bandToxtatish = $menyu.Items.Add("Serverni to'xtatish")
$belgi.ContextMenuStrip = $menyu

$taymer = New-Object System.Windows.Forms.Timer
$taymer.Interval = $tekshirishOraligi

$kontekst = New-Object System.Windows.Forms.ApplicationContext
$script:ochmagan = 0


function Yopilsin {
    $taymer.Stop()
    $belgi.Visible = $false
    $belgi.Dispose()
    $kontekst.ExitThread()
}


# --- hodisalar ---
$belgi.add_MouseClick({
    param($yuboruvchi, $hodisa)
    if ($hodisa.Button -eq [System.Windows.Forms.MouseButtons]::Left) { SaytniOch }
})

$bandYangilash.add_Click({
    $ornatuvchi = Join-Path $joy 'ORNATISH.bat'
    if (Test-Path -LiteralPath $ornatuvchi) {
        # Administrator huquqini ORNATISH.bat o'zi so'raydi
        Start-Process -FilePath $ornatuvchi -WorkingDirectory $joy
    } else {
        [System.Windows.Forms.MessageBox]::Show(
            "ORNATISH.bat topilmadi:`n$joy", "Lombard",
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Warning) | Out-Null
    }
})

$bandToxtatish.add_Click({
    $toxtatuvchi = Join-Path $joy 'Toxtatish.vbs'
    if (Test-Path -LiteralPath $toxtatuvchi) {
        Start-Process -FilePath 'wscript.exe' -ArgumentList "`"$toxtatuvchi`"" -WindowStyle Hidden
    }
    Yopilsin
})

$taymer.add_Tick({
    if (ServerIshlayaptimi) {
        $script:ochmagan = 0
        if (-not $belgi.Visible) { $belgi.Visible = $true }
    } else {
        if ($belgi.Visible) { $belgi.Visible = $false }
        $script:ochmagan = $script:ochmagan + 1
        if ($script:ochmagan -ge $yopishChegarasi) { Yopilsin }
    }
})

# Birinchi tekshiruvni kutib o'tirmaymiz
if (ServerIshlayaptimi) { $belgi.Visible = $true }
$taymer.Start()

try {
    [System.Windows.Forms.Application]::Run($kontekst)
} finally {
    # Belgi ekranda "arvoh" bo'lib qolmasin
    $belgi.Visible = $false
    $belgi.Dispose()
    $muteks.ReleaseMutex()
    $muteks.Dispose()
}
