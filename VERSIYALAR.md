# Versiyalar tarixi

## 1.2.6 — 2026-09-29

Almashtirgich tugmalari (mijoz, kimniki, mashina egasi) kengligi 85%, telefonda 100%.

## 1.2.5 — 2026-09-29

ngrok nusxasida saqlash/tahrirlash/o'chirish tugmalari boshidanoq o'chiq (formani to'ldirib bo'lgach bloklanmasin).

## 1.2.4 — 2026-09-29

Asosiy sayt — PythonAnywhere. ngrok nusxasi faqat ko'rish uchun va ma'lumotni PA'dan o'zi yangilab turadi.

## 1.2.3 — 2026-09-29

«Oldingi mijoz» maydoni bosilishi bilan (hech narsa yozilmasa ham) mijozlar ro'yxati chiqadi; tartib oxirgi shartnoma sanasi bo'yicha, yangisi tepada.

## 1.2.2 — 2026-09-29

ngrok orqali ochish: NGROK.bat (doimiy domen, alohida 8011-port, DEBUG o'chiq).

## 1.2.1 — 2026-09-29

Joylash paytida mijozlar qayta yig'iladi: 0022 dan keyin tuzilgan shartnomalar ham mijozga bog'lanadi.

## 1.2.0 — 2026-09-29

Mijozlar bazasi: qayta kelgan mijoz pasport seriya-raqami bo'yicha ro'yxatdan tanlanadi, ma'lumotlari o'zi to'ldiriladi. Eski shartnomalardagi mijozlar avtomatik bazaga yozildi.

## 1.1.1 — 2026-09-17

Ombor ochiq: ORNATISH.bat yolg'iz o'zi ham ishlaydi, fayllarni GitHub'dan oladi

## 1.1.0 — 2026-09-17

Birinchi o'rnatishda ma'lumotlar jonli saytdan (`mrclayd.pythonanywhere.com`)
ko'chirib olinadi: baza va garov suratlari. Login/parol o'rnatish paytida
so'raladi va hech qayerda saqlanmaydi.

- `bazani_ol.py` — saytning ichki paneli orqali `db.sqlite3` va `media/` ni oladi;
  kelgan fayl haqiqiy baza ekani tekshiriladi.
- `MALUMOTNI_OL.bat` — o'rnatishda o'tkazib yuborilgan bo'lsa, keyin ham
  qayta o'rnatmasdan olib keladi (eski bazadan zaxira oladi).
- Sahifa pastida dastur versiyasi ko'rinadi; `versiya.py` bilan yangilanadi.
- Tuzatildi: administrator huquqi berilmasa oyna jimgina yopilib ketardi;
  papka nomida bo'shliq bo'lsa yo'l yarmidan kesilardi.
- `requirements.txt` ga Pillow qo'shildi — usiz toza kompyuterda `migrate`
  to'xtab qolardi (garov surati uchun `ImageField`).

## 1.0.0 — 2026-09-17

Mijoz kompyuteriga o'rnatish to'plami: `ORNATISH.bat` (Python tekshiruvi,
`.venv`, `migrate`, ish stoli yorliqlari, trey belgisi), `Ishga_tushirish.vbs`,
`Toxtatish.vbs`, `Belgi.ps1`, `Tekshirish.bat` va `boshlangich` buyrug'i.
