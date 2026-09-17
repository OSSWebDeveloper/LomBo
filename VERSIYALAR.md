# Versiyalar tarixi

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
