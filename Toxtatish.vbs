' ============================================================
'  Lombard - serverni to'xtatish
'  Ish stolidagi "Lombardni to'xtatish" yorlig'i shu faylni chaqiradi.
'  Jimgina ishlaydi: hech qanday tasdiq oynasi chiqmaydi.
'
'  Agar server administrator huquqi bilan ishga tushgan bo'lsa
'  (masalan ORNATISH.bat oxirida), oddiy foydalanuvchi uni to'xtata
'  olmaydi. Shunday holatda skript o'zini administrator huquqi bilan
'  qayta chaqiradi - Windows bir marta ruxsat so'raydi.
' ============================================================
Option Explicit

Dim shell, fso, joy, port, url, adminMi, i

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

adminMi = False
If WScript.Arguments.Count > 0 Then
    If LCase(Trim(WScript.Arguments(0))) = "/admin" Then adminMi = True
End If

joy = fso.GetParentFolderName(WScript.ScriptFullName)
port = PortniOqi(joy)
url = "http://127.0.0.1:" & port & "/"

If Not ServerIshlayapti(url) Then
    WScript.Quit 0          ' allaqachon to'xtagan - jimgina chiqamiz
End If

' Uch marta urinamiz: ba'zan jarayon darrov yopilmaydi
For i = 1 To 3
    JarayonlarniYop port
    WScript.Sleep 600
    If Not ServerIshlayapti(url) Then WScript.Quit 0
Next

' Bu yergacha kelgan bo'lsa - huquq yetmadi
If Not adminMi Then
    If AdminBilanQaytaChaqir() Then WScript.Quit 0
End If

MsgBox "Serverni to'xtatib bo'lmadi." & vbCrLf & vbCrLf & _
       "Vazifalar dispetcherini ochib, python.exe jarayonini yoping.", _
       vbCritical, "Lombard"
WScript.Quit 1


' ------------------------------------------------------------ yordamchilar

Sub JarayonlarniYop(p)
    Dim pidlar, j
    pidlar = TinglayotganPidlar(p)
    For j = 0 To UBound(pidlar)
        If pidlar(j) <> "" Then
            shell.Run "taskkill /PID " & pidlar(j) & " /T /F", 0, True
        End If
    Next
End Sub

Function AdminBilanQaytaChaqir()
    ' O'zini administrator huquqi bilan qayta ishga tushiradi.
    ' Foydalanuvchi ruxsat bermasa - False qaytadi.
    Dim app
    AdminBilanQaytaChaqir = False
    On Error Resume Next
    Set app = CreateObject("Shell.Application")
    If Err.Number <> 0 Then Exit Function
    app.ShellExecute "wscript.exe", _
                     """" & WScript.ScriptFullName & """ /admin", joy, "runas", 0
    If Err.Number = 0 Then AdminBilanQaytaChaqir = True
    On Error GoTo 0
End Function

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

Function ServerIshlayapti(manzil)
    Dim http
    ServerIshlayapti = False
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
    If Err.Number = 0 Then ServerIshlayapti = True
    On Error GoTo 0
End Function

Function TinglayotganPidlar(p)
    ' netstat chiqishidan shu portni tinglayotgan jarayon raqamlarini oladi
    Dim exec, matn, qatorlar, q, bolaklar, j, natija, pid
    natija = Array()
    On Error Resume Next
    Set exec = shell.Exec("cmd /c netstat -ano -p TCP")
    If Err.Number <> 0 Then
        TinglayotganPidlar = natija
        Exit Function
    End If
    matn = exec.StdOut.ReadAll()
    On Error GoTo 0

    qatorlar = Split(matn, vbCrLf)
    For Each q In qatorlar
        If InStr(q, ":" & p & " ") > 0 And InStr(UCase(q), "LISTENING") > 0 Then
            bolaklar = Split(q, " ")
            pid = ""
            For j = UBound(bolaklar) To 0 Step -1
                If Trim(bolaklar(j)) <> "" Then
                    pid = Trim(bolaklar(j))
                    Exit For
                End If
            Next
            If IsNumeric(pid) Then
                ReDim Preserve natija(UBound(natija) + 1)
                natija(UBound(natija)) = pid
            End If
        End If
    Next
    TinglayotganPidlar = natija
End Function
