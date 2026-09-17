' ============================================================
'  Lombard - shartnoma tizimi
'  Ish stolidagi yorliq shu faylni ishga tushiradi:
'    1) server fon rejimida (oynasiz) ishga tushadi
'    2) tayyor bo'lgach Chrome ochiladi
'  Server allaqachon ishlayotgan bo'lsa - faqat Chrome ochiladi.
' ============================================================
Option Explicit

Dim shell, fso, joy, port, url, ishga, i, tayyor
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

joy = fso.GetParentFolderName(WScript.ScriptFullName)
port = PortniOqi(joy)
url = "http://127.0.0.1:" & port & "/"
ishga = joy & "\Server.bat"

If Not fso.FileExists(ishga) Or Not fso.FileExists(joy & "\.venv\Scripts\python.exe") Then
    MsgBox "Dastur to'liq o'rnatilmagan." & vbCrLf & vbCrLf & _
           "Papka: " & joy & vbCrLf & vbCrLf & _
           "ORNATISH.bat faylini administrator nomidan qayta ishga tushiring.", _
           vbCritical, "Lombard"
    WScript.Quit 1
End If

If Not ServerTayyor(url) Then
    shell.CurrentDirectory = joy
    shell.Run """" & ishga & """", 0, False

    tayyor = False
    For i = 1 To 60           ' eng ko'pi bilan 30 soniya kutamiz
        WScript.Sleep 500
        If ServerTayyor(url) Then
            tayyor = True
            Exit For
        End If
    Next

    If Not tayyor Then
        MsgBox "Server ishga tushmadi." & vbCrLf & vbCrLf & _
               "Sababi shu faylda yozilgan:" & vbCrLf & joy & "\server.log" & vbCrLf & vbCrLf & _
               "Yoki papkadagi Tekshirish.bat ni oching - xato oynada ko'rinadi.", _
               vbCritical, "Lombard"
        WScript.Quit 1
    End If
End If

BelginiYoq joy
BrauzerdaOch url
WScript.Quit 0


' ------------------------------------------------------------ yordamchilar

Sub BelginiYoq(papka)
    ' Soat yonidagi (trey) belgi: server ishlayotganini ko'rsatib turadi.
    ' Belgi.ps1 ning o'zi ikkinchi nusxa ochilishiga yo'l qo'ymaydi,
    ' shuning uchun bu yerda tekshirish shart emas.
    Dim belgi
    belgi = papka & "\Belgi.ps1"
    If Not fso.FileExists(belgi) Then Exit Sub
    shell.Run "powershell.exe -NoProfile -ExecutionPolicy Bypass " & _
              "-WindowStyle Hidden -File """ & belgi & """", 0, False
End Sub

Function PortniOqi(papka)
    Dim f
    PortniOqi = "8010"
    If fso.FileExists(papka & "\port.txt") Then
        Set f = fso.OpenTextFile(papka & "\port.txt", 1)
        If Not f.AtEndOfStream Then PortniOqi = Trim(f.ReadLine)
        f.Close
        If Not IsNumeric(PortniOqi) Then PortniOqi = "8010"
    End If
End Function

Function ServerTayyor(manzil)
    Dim http
    ServerTayyor = False
    On Error Resume Next
    Set http = CreateObject("MSXML2.ServerXMLHTTP.6.0")
    If Err.Number <> 0 Then
        Err.Clear
        Set http = CreateObject("MSXML2.XMLHTTP")
    End If
    If Err.Number <> 0 Then Exit Function
    http.setTimeouts 1000, 1000, 2000, 2000
    Err.Clear
    http.Open "GET", manzil, False
    http.Send
    If Err.Number = 0 Then ServerTayyor = True
    On Error GoTo 0
End Function

Sub BrauzerdaOch(manzil)
    Dim chrome
    chrome = ChromeYoli()
    If chrome <> "" Then
        shell.Run """" & chrome & """ --new-window " & manzil, 1, False
    Else
        shell.Run manzil, 1, False       ' standart brauzer
    End If
End Sub

Function ChromeYoli()
    Dim yol, yollar, y
    ChromeYoli = ""

    On Error Resume Next
    yol = shell.RegRead("HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe\")
    On Error GoTo 0
    If yol <> "" Then
        If fso.FileExists(yol) Then
            ChromeYoli = yol
            Exit Function
        End If
    End If

    yollar = Array( _
        shell.ExpandEnvironmentStrings("%ProgramFiles%") & "\Google\Chrome\Application\chrome.exe", _
        shell.ExpandEnvironmentStrings("%ProgramFiles(x86)%") & "\Google\Chrome\Application\chrome.exe", _
        shell.ExpandEnvironmentStrings("%LocalAppData%") & "\Google\Chrome\Application\chrome.exe")

    For Each y In yollar
        If fso.FileExists(y) Then
            ChromeYoli = y
            Exit Function
        End If
    Next
End Function
