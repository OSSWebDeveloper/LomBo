# Lombard — shartnoma tizimi

"Asia Invest Mikromoliya tashkiloti" MCHJ uchun mikroqarz shartnomalarini avtomatik
tayyorlash tizimi. Operator faqat o'zgaruvchan ma'lumotlarni kiritadi — o'zgarmas
huquqiy matn dastur tomonidan qo'shiladi va tayyor Word hujjat yuklab olinadi.

## Ishga tushirish (lokal)

```bash
pip install -r requirements.txt
python manage.py migrate
python seed_demo.py        # namuna ma'lumotlar (ixtiyoriy)
python manage.py runserver
```

Sayt: http://127.0.0.1:8000/ · Admin panel: http://127.0.0.1:8000/admin/

### Hozirgi hisoblar (sinov uchun)

| Login | Parol | Nima qila oladi |
|---|---|---|
| `boshliq` | `boshliq` | Sayt: barcha boshliq bo'limlari + to'liq tahrirlash + shablonlarni almashtirish |
| `ishchi` | `ishchi` | Sayt: shartnoma qo'shish, o'z shartnomalarini ko'rish |
| `superuser` | `superuser` | Faqat admin panel (`/admin/`) — saytga kirmaydi |

`ishchi` hisobi `boshliq`ga biriktirilgan, ya'ni o'chirish so'rovlari o'shanga boradi.

**Muhim:** bu parollar sinov uchun — login bilan bir xil, ya'ni juda zaif.
Haqiqiy ishga o'tishdan oldin albatta almashtiring: boshliq va ishchi parolini
admin panel yoki saytdan, superuser parolini
`python manage.py changepassword superuser` buyrug'i bilan.

`seed_demo.py` fayli eskirgan (u boshqa hisoblar yaratadi va yangi rol tizimiga
mos emas) — ishlatmang yoki o'chirib tashlang.

## Mijoz kompyuteriga o'rnatish (ORNATISH.bat)

Mijozda Python ham, Git ham bo'lishi shart emas — `ORNATISH.bat` ni ikki marta
bosish kifoya. U administrator huquqini o'zi so'raydi va ketma-ket to'qqiz ishni
bajaradi:

| # | Bosqich | Nima qiladi |
|---|---|---|
| 1 | Python | 3.12+ bormi tekshiradi; bo'lmasa python.org dan yuklab, jimgina o'rnatadi |
| 2 | Server | Ishlab turgan eski serverni to'xtatadi (fayllar band bo'lmasin) |
| 3 | Yuklash | GitHub'dan yangi nusxani oladi; internet yoki ombor yopiq bo'lsa — `.bat` turgan papkadagi nusxani ishlatadi |
| 4 | Fayllar | `C:\lombard` ga ko'chiradi; bazadan zaxira oladi |
| 5 | Kutubxonalar | `.venv` yasab, `requirements.txt` ni o'rnatadi |
| 6 | Ma'lumotlar | **Birinchi o'rnatishda** saytdagi baza va garov suratlarini ko'chirib oladi |
| 7 | Baza | `migrate` va `boshlangich` (maxfiy kalit + kerak bo'lsa birinchi hisob) |
| 8 | Yorliqlar | Ish stoliga ikkita yorliq qo'yadi |
| 9 | Hujjatlar | Word shablonlari joyidami, PDF uchun Word/LibreOffice bormi — tekshiradi |

Oxirida sayt fon rejimida ishga tushadi va Chrome o'zi ochiladi.

**Manzil:** `http://127.0.0.1:8010/` — sayt faqat shu kompyuterda ochiladi,
tarmoqqa chiqarilmaydi.

### Ish stolidagi yorliqlar

| Yorliq | Nima qiladi |
|---|---|
| **Lombard** | Serverni oynasiz ishga tushiradi va Chrome'da saytni ochadi |
| **Lombardni to'xtatish** | Ishlab turgan serverni to'xtatadi |

Server ishlayotganda soat yonida (treyda) oltin belgi turadi: chap tugma —
saytni ochadi, o'ng tugma — «Dasturni yangilash» va «Serverni to'xtatish».
Server to'xtasa belgi o'zi yo'qoladi.

### Birinchi o'rnatishda ma'lumotlar saytdan keladi

Yangi kompyuterda baza bo'm-bo'sh bo'lsa, o'rnatuvchi jonli saytdagi
ma'lumotlarni shu yerga ko'chirib oladi:

```
https://mrclayd.pythonanywhere.com/
```

Ekranda saytning **boshqaruv (superuser) logini va paroli** so'raladi — parol
yozilayotganda ko'rinmaydi va hech qayerda saqlanmaydi. Enter bosilsa qadam
o'tkazib yuboriladi va bo'sh bazadan boshlanadi.

Nima ko'chiriladi:

| Nima | Qayerdan | Qayerga |
|---|---|---|
| `db.sqlite3` — shartnomalar, hisoblar, tarix | Saytning ichki paneli (`/ic-9f4k2m/`) | `C:\lombard\db.sqlite3` |
| Garov suratlari | O'sha panel, `media` papkasi (zip) | `C:\lombard\media\` |

Muhim jihatlar:

* Ma'lumot **faqat bir marta**, birinchi o'rnatishda olinadi. Keyingi
  yangilanishlarda bu qadam o'tkazib yuboriladi — mahalliy bazaning ustiga
  hech qachon yozilmaydi.
* Baza kelgach `migrate` ishlaydi, ya'ni saytdagi baza eskiroq bo'lsa ham
  yangi jadvallar o'z-o'zidan qo'shiladi.
* Ma'lumot kelgan bo'lsa saytdagi loginlar bilan kiriladi (`boshliq`/`boshliq`
  hisobi yaratilmaydi).
* Sayt javob bermasa yoki parol noto'g'ri bo'lsa — o'rnatish to'xtamaydi,
  shunchaki bo'sh bazadan boshlanadi.
* Panelga faqat superuser kira oladi, ya'ni bu yo'l saytdagidan ortiq huquq
  bermaydi. Parol mijozning kompyuterida qolmaydi.

Xohlasangiz qo'lda ham chaqirsa bo'ladi (masalan boshqa saytdan olish uchun):

```bash
set LOMBARD_SAYT_LOGIN=...
set LOMBARD_SAYT_PAROL=...
python bazani_ol.py --manzil https://mrclayd.pythonanywhere.com --nishon C:\lombard --suratlar
```

**O'rnatishda o'tkazib yuborilgan bo'lsa** (Enter bosilgan yoki parol noto'g'ri
kiritilgan), qayta o'rnatish shart emas — `C:\lombard\MALUMOTNI_OL.bat` ni ishga
tushiring. U login/parolni so'raydi, serverni vaqtincha to'xtatadi, eski bazadan
zaxira oladi (`db_zaxira_oxirgi.sqlite3`), saytdagi ma'lumotni qo'yadi va
serverni qaytadan ochadi.

Shu ikki o'zgaruvchi `ORNATISH.bat` dan oldin berilsa, o'rnatuvchi hech nima
so'ramaydi — bir nechta kompyuterga ketma-ket o'rnatishda qulay.

### Birinchi hisob

Saytdan ma'lumot olinmagan bo'lsa (yuqoridagi qadam o'tkazib yuborilgan),
`boshlangich` buyrug'i bitta boshliq hisobini ochadi:
login `boshliq`, parol `boshliq` (to'liq tahrirlash va shablon vakolatlari
bilan). **Saytga kirgach parolni almashtirish shart.** Hisoblar allaqachon bor
bo'lsa buyruq hech nimaga tegmaydi — yangilashda parollar saqlanib qoladi.

Admin panel (`/admin/`) uchun alohida hisob kerak bo'lsa:

```bash
python manage.py boshlangich --admin        # faqat bo'sh bazada
python manage.py panel_admin --username ...  # istalgan vaqtda
```

### Yangilash

Shu `ORNATISH.bat` ni qayta ishga tushirish kifoya (yoki treydagi belgidan
«Dasturni yangilash»). Ma'lumotlar bazasi, garov suratlari va saytdan
yuklangan shablonlar **hech qachon o'chirilmaydi** — yangilanishdan oldin
bazadan `db_zaxira_oxirgi.sqlite3` nusxasi olinadi.

Ombor (`OSSWebDeveloper/LomBo`) yopiq bo'lgani uchun hozir GitHub'dan yuklash
ishlamaydi: o'rnatuvchi loyiha papkasining o'zidan nusxa oladi. Ya'ni mijozga
butun papkani (zip yoki fleshka bilan) berib, ichidagi `ORNATISH.bat` ni
bostirish kerak. Omborni ochiq qilsangiz — yangilanish internet orqali o'zi
keladi, boshqa hech nima o'zgartirilmaydi.

### O'rnatuvchi fayllar

| Fayl | Vazifasi |
|---|---|
| `ORNATISH.bat` | O'rnatish va yangilash (to'qqiz bosqich) |
| `Ishga_tushirish.vbs` | Serverni fonda ochadi, Chrome'ni chaqiradi (yorliq shuni bosadi) |
| `Toxtatish.vbs` | Serverni jimgina to'xtatadi |
| `Server.bat` | `runserver --noreload`, chiqishini `server.log` ga yozadi |
| `MALUMOTNI_OL.bat` | Saytdagi ma'lumotlarni keyin ham olib keladi (qayta o'rnatmasdan) |
| `bazani_ol.py` | Saytdagi baza va suratlarni ko'chirib oladi (birinchi o'rnatish) |
| `Belgi.ps1` | Treydagi belgi va uning menyusi |
| `yorliqlar.ps1` | Ish stoli yorliqlarini yasaydi |
| `Yorliqlarni_tiklash.bat` | Yorliqlar ko'rinmay qolsa — faqat ularni qayta yasaydi |
| `Tekshirish.bat` | Serverni oynali rejimda ochadi — xato ekranda ko'rinadi |
| `Toxtatish.bat` | Portni band qilgan jarayonni yopadi (zaxira usul) |
| `versiya.txt` | O'rnatilgan versiya; yangilashda shu raqam solishtiriladi |
| `lombard.ico`, `lombard_stop.ico` | Yorliq va trey belgilari |

O'rnatilgan kompyuterda qo'shimcha yasaladigan fayllar: `db.sqlite3`,
`db_zaxira_oxirgi.sqlite3`, `.secret_key`, `port.txt`, `server.log`,
`media/garov/…` — ular git'ga tushmaydi va yangilashda ko'chirilmaydi.

### Nimadir ishlamasa

* **Sayt ochilmadi** — `C:\lombard\Tekshirish.bat`: server oynada ishga tushadi
  va xato ko'rinib turadi. Batafsil yozuv: `C:\lombard\server.log`.
* **Yorliqlar yo'q** — `C:\lombard\Yorliqlarni_tiklash.bat` (yoki papkadagi
  tayyor `.lnk` fayllarini qo'lda ish stoliga ko'chiring).
* **Port band** — `port.txt` dagi raqamni o'zgartiring va `ORNATISH.bat` dagi
  `set "PORT=8010"` qatorini ham shunga moslang.
* **PDF tugmasi yo'q** — kompyuterda Microsoft Word ham, LibreOffice ham yo'q.
  Word hujjat baribir yuklab olinadi.

## Rollar va huquqlar

### Admin panel va sayt — alohida kirish

Ikkisi bir-biridan mustaqil:

| Hisob turi | Saytga kiradi | Admin panelga kiradi |
|---|:---:|:---:|
| Rol = Boshliq / Ishchi | ✅ | ❌ |
| Rol = «Faqat admin panel» (superuser) | ❌ | ✅ |

`createsuperuser` bilan yaratilgan yangi hisob avtomatik «Faqat admin panel»
roliga tushadi — u bilan saytga kirilmaydi. Admin panelga kirgan holda saytga
o'tishga urinsa, tushuntirish sahifasi chiqadi. Agar administratorning o'ziga
sayt kerak bo'lsa, unga alohida boshliq hisobi yarating.

| Amal | Ishchi | Boshliq | Vakolatli boshliq |
|---|:---:|:---:|:---:|
| Shartnoma qo'shish | ✅ | ✅ | ✅ |
| O'z shartnomasini ko'rish | ✅ | ✅ | ✅ |
| Barcha shartnomalarni ko'rish | ❌ | ✅ | ✅ |
| Word yuklab olish | ✅ | ✅ | ✅ |
| PDF yuklab olish | ✅ | ✅ | ✅ |
| Shartnomani to'liq tahrirlash | ❌ | ❌ | ✅ |
| O'zi kiritgan shartnomani tuzatish | ✅ (60 daqiqa ichida) | ❌ | ✅ (muddatsiz) |
| Shartnomani o'chirish | so'rov orqali | ✅ | ✅ |
| Ishchi qo'shish/bo'shatish | ❌ | ✅ | ✅ |
| Monitoring | ❌ | ✅ | ✅ |
| **Word shablonlarini almashtirish** | ❌ | ❌ | ✅ (alohida vakolat) |

### Boshliq qo'shish

Admin panelda **Boshliqlar → Qo'shish** bo'limiga kiring. Forma faqat 5 ta maydondan
iborat:

| Maydon | Izoh |
|---|---|
| Login | Boshliq shu login bilan saytga kiradi |
| Parol / Parolni takrorlang | |
| Ismi, Familiyasi | |
| To'liq tahrirlash vakolati | Belgilansa — mavjud shartnomalarni tahrirlay oladi |

Rol avtomatik "Boshliq" qilib qo'yiladi — qo'lda tanlash shart emas. Vakolatni keyin
ham o'zgartirish mumkin: Boshliqlar ro'yxatidan tanlab, belgini qo'ying yoki oling.

**Parolni almashtirish.** Boshliqni tahrirlash sahifasida "Parolni almashtirish"
bo'limi bor: yangi parolni ikki marta yozing va saqlang. Eski parolni bilish shart
emas. Bo'sh qoldirsangiz parol o'zgarmaydi — boshqa maydonlarni parolga tegmasdan
tahrirlash mumkin.

Boshliqni **bo'shatish** uchun uni o'chirish shart emas — tahrirlash sahifasida
`Faol` belgisini olib tashlang, u saytga kira olmaydi, ma'lumotlari esa saqlanadi.

Texnik jihatdan `Boshliq` — `User` modelining proxy'si (`accounts/models.py`),
ya'ni bazada alohida jadval yaratilmaydi. Barcha foydalanuvchilarni bir joyda
ko'rish kerak bo'lsa, admin paneldagi **Foydalanuvchilar** bo'limi o'sha-o'sha turadi.

**Ishchilarni** boshliq saytning o'zidan qo'shadi (admin panel kerak emas); qo'shgan
boshliq avtomatik biriktiriladi va o'chirish so'rovlari o'shanga boradi.

## Ishchining tuzatish muddati

Ishchi shartnomani kiritgach, **60 daqiqa** ichida uni o'zi to'g'rilay oladi:
shartnoma sahifasida "✏️ Tuzatish" tugmasi turadi va yonida qancha vaqt
qolgani yozib turiladi. Bu — yangi kiritilgan shartnomadagi xatoni (ism,
summa, hujjat raqami) darrov tuzatish uchun.

- Muddat **kiritilgan vaqtdan** sanaladi — tuzatish uni cho'zmaydi.
- Muddat o'tgach tugma yo'qoladi, tahrirlash faqat vakolatli boshliqda qoladi.
- Ishchi faqat **o'zi kiritgan** shartnomani va faqat u `faol` holatda
  bo'lgandagina tuzata oladi (o'chirish so'rovi yuborilgani tahrirlanmaydi).
- Tugash sanasi baribir qulflangan — u avtomatik hisoblanadi.
- Har bir tuzatish "Tarix" bo'limiga yoziladi (`Shartnomani o'zgartirdi`,
  izohda "kiritgandan keyingi tuzatish").

Muddatni `config/settings.py` dagi `ISHCHI_TAHRIR_DAQIQA` o'zgartiradi;
`0` qo'yilsa ishchi umuman tahrirlay olmaydi.

## O'chirish oqimi

Boshliq shartnoma sahifasidagi qizil **"🗑 O'chirish"** tugmasi orqali
istalgan shartnomani o'zi o'chiradi — tasdiqlash sahifasi chiqadi, "Ha,
o'chirilsin" bosilgach shartnoma butunlay o'chadi va amal tarixga yoziladi.

Ishchida bu tugma yo'q. Uning uchun so'rov oqimi mo'ljallangan (kodda to'liq
ishlaydi, lekin hozir shartnoma sahifasida "O'chirishni so'rash" tugmasi
ko'rsatilmayapti — kerak bo'lsa tugmani qaytarish bir necha qatorlik ish):

1. Ishchi shartnoma sahifasida "O'chirishni so'rash" tugmasini bosadi va sabab yozadi.
2. Shartnoma `o'chirish so'ralgan` holatiga o'tadi, lekin **o'chirilmaydi**.
3. So'rov aynan **o'sha ishchini qo'shgan boshliqqa** boradi (boshqa boshliq ko'ra olmaydi).
4. Boshliq "So'rovlar" bo'limida tasdiqlaydi yoki rad etadi.
   - Tasdiqlansa — shartnoma o'chiriladi, so'rov tarixi bazada qoladi.
   - Rad etilsa — shartnoma faol holatiga qaytadi.

Ishchining `Qo'shgan shartnomalari (jami)` hisoblagichi shartnoma o'chirilsa ham
**kamaymaydi** — bu uning umumiy mehnat ko'rsatkichi.

## Hujjatlar — ikkita alohida fayl

Har bir shartnoma bo'yicha **ikkita mustaqil hujjat** chiqadi:

| Fayl | Tarkibi | Kimda bor |
|---|---|---|
| `shartnoma_<shartnoma №>.docx` | Mikroqarz shartnomasi | Barcha turlarda |
| `garov_<garov №>.docx` | Garov shartnomasi + Baholash dalolatnomasi | Zargarlik va transportda |

Garov faylining nomida **garov shartnomasining o'z raqami** turadi — hujjat
sarlavhasidagi raqam bilan bir xil bo'lishi uchun.

Ish haqi kafilligida garov hujjati tuzilmaydi — faqat mikroqarz shartnomasi.

Shartnoma sahifasidagi **Hujjatlar** bo'limida ikkalasi alohida guruh bo'lib
turadi, har biri uchun Word va PDF tugmasi. Ro'yxatda esa «Shartnoma» va
«Garov» tugmalari (garovi yo'q shartnomada ikkinchisi ko'rinmaydi).

Texnik jihatdan shablon bitta bo'lib qolaveradi — tayyor hujjat garov jadvali
chegarasidan ikkiga bo'linadi (`contracts/shablondan.py` dagi `qismlarga_ajrat`).

Summalar avtomatik so'z bilan yoziladi (kirill-o'zbekcha):
`35 000 000` → `35 000 000 (ўттиз беш миллион)`.

To'lov jadvali differensial usulda hisoblanadi: asosiy qarz oylarga teng bo'linadi,
foiz qolgan qoldiqqa hisoblanadi.

Ikki nozik qoida bor — ikkalasi ham lombardning bosma grafiklaridan aniqlangan
va `TolovJadvaliTest` da qat'iy yozib qo'yilgan:

- **Asosiy ulush** eng yaqin butun so'mga yaxlitlanadi (yarmi yuqoriga):
  `5 000 000 / 12 = 416 666,67` → `416 667,00`. Bo'linishdan qolgani oxirgi
  to'lovga qo'shiladi (`416 663,00`). Pastga yaxlitlansa butun jadval bir
  so'mdan surilib ketadi — qoldiq foiz bazasi bo'lgani uchun xato har oyda
  o'sadi.
- **Foiz** avval kunlik summaga yaxlitlanadi, keyin kunlarga ko'paytiriladi:
  `yaxlit(qoldiq × yillik/365, 2 xona) × kunlar`. Kabisa yilida 365 emas, 366.

## Grafik bo'limi — shartnoma tuzmasdan hisoblash

Yuqori menyudagi **Grafik** — to'lov jadvali kalkulyatori (`/grafik/`). Mijoz
«qancha to'layman?» deb so'raganda shartnoma ochmasdan javob berish uchun.

Majburiy to'rt maydon: qarz summasi, yillik foiz, shartnoma sanasi, muddat.
«Qo'shimcha» bo'limida to'rttasi ixtiyoriy:

| Maydon | Bo'sh qolsa |
|---|---|
| Birinchi to'lov sanasi | Keyingi oyning 10-sanasi |
| Oxirgi to'lov sanasi | Shartnoma sanasi + muddat − 1 kun |
| Qarz oluvchi F.I.Sh. | Word hujjatida bo'sh qoladi |
| Shartnoma № | Word hujjatida bo'sh qoladi |

Hisob shartnomadagi bilan **bitta funksiya** (`payment_schedule`) orqali
yuritiladi — forma faqat saqlanmaydigan `Contract` yig'ib beradi. Shuning uchun
kalkulyator natijasi bosma 1-ilova bilan tiyingacha bir xil bo'ladi; buni
`GrafikSahifasiTest` tekshirib turadi.

Ma'lumot GET orqali yuriladi: sahifani yangilash natijani yo'qotmaydi, havolani
nusxalab yuborsa ham o'sha jadval ochiladi.

Sahifada faqat jadvalning o'zi chiqadi — xulosa kartalari yo'q (xaridor
qarori, 2026-08-24). Jadval ustida **Word** (faqat 1-ilovaning o'zi, alohida
fayl) va **Chop etish** tugmalari. Chop etishda menyu, forma va tugmalar chiqmaydi — faqat jadval
(`app.css` dagi `@media print`).

## Ko'rinish: 3 stil × 2 rejim

Yuqori paneldagi ro'yxatdan stil tanlanadi, yonidagi ☀️ / 🌙 tugmasi kunduzgi va
tungi rejimni almashtiradi. Tanlov brauzerda saqlanadi — har bir xodim o'ziga
qulayini tanlab qo'yadi. Rejim soatga bog'liq emas, faqat tugma orqali o'zgaradi.

| Stil | Ko'rinishi |
|---|---|
| **Klassik** | Jiddiy, korporativ: ko'k rang, serif sarlavhalar, yuqori panel |
| **Zamonaviy** | Yumshoq va keng: siyohrang, yumaloq burchaklar, chap yon panel |
| **Ixcham** | Zich: yashil rang, o'tkir burchaklar, kichik shrift — ko'p ma'lumot bir ekranda |

Ranglarni o'zgartirish uchun `static/css/app.css` faylining boshidagi token
bloklarini tahrirlang — qolgan barcha uslublar shu tokenlardan foydalanadi.

## Sozlamalar

`config/settings.py` fayli oxiridagi ikki blok:

- `CONTRACT_START_NUMBER = 200` — shartnoma raqamlash shu raqamdan boshlanadi.
- `GAROV_START_NUMBER = 1` — garov shartnomasi o'z alohida raqamlanishiga ega.

  Ikkalasi ham bazadagi eng katta raqamdan davom etadi. Raqamni boshqa joydan
  boshlash kerak bo'lsa, birinchi shartnoma kiritilishidan **oldin** o'zgartiring.

- `ISHCHI_TAHRIR_DAQIQA = 60` — ishchi o'zi kiritgan shartnomani necha daqiqa
  ichida tuzata oladi (qarang: "Ishchining tuzatish muddati"). `0` — o'chiradi.

### Avtomatik to'ldiriladigan maydonlar

Formada quyidagilar o'zi hisoblanadi:

| Maydon | Qanday hisoblanadi | Qo'lda o'zgartirsa bo'ladimi |
|---|---|---|
| Shartnoma № | Ketma-ket, `CONTRACT_START_NUMBER` dan | Ha |
| Garov shartnomasi № | Ketma-ket, `GAROV_START_NUMBER` dan. Kafillikda berilmaydi | Ha |
| Tugash sanasi | Shartnoma sanasi + muddat − 1 kun | Yo'q, qulflangan |
| Garov bahosi | Zargarlikda — jadvaldagi summalar yig'indisi. Transportda qo'lda kiritiladi | Zargarlikda yo'q |

Raqamlar avtomat taklif qilinadi, lekin xodim ularni o'zgartira oladi. Kiritilgan
raqam boshqa shartnomada band bo'lsa forma saqlanmaydi va qaysi raqam bo'shligini
aytadi. Maydon bo'sh qoldirilsa navbatdagi bo'sh raqam qo'yiladi.

Tugash sanasining qulflanishi faqat ekranda emas, server tomonida ham amal qiladi:
brauzerdan boshqa qiymat yuborilsa ham e'tiborga olinmaydi.

Forma «2. Qarz oluvchi» bo'limi ajratgich bilan ikkiga bo'lingan: yuqorida
shaxsning o'zi (F.I.Sh., manzil, telefonlar, ish joyi, daromad), pastda
**Shaxsni tasdiqlovchi hujjat**.

**Hujjat turi** ro'yxatdan tanlanadi: *ID karta* yoki *Biometrik pasport (yashil)*.
Tanlov ikki narsani belgilaydi:

1. Shartnoma matnidagi ibora — `... ракамли шахс гувохномаси` yoki
   `... ракамли паспорти`.
2. **IIV bo'lim raqami** maydoni. Yashil biometrik pasportda bunday raqam
   bo'lmaydi — maydon yashiriladi va tozalanadi, hujjatda esa
   `Бухоро вилояти ИИВ томонидан ...` deb, raqamsiz yoziladi (ID kartada
   avvalgidek `Бухоро вилояти, 61013-сонли ИИВ томонидан ...`).

Bu ikki qoida garovga qo'yuvchining hujjatiga ham aynan shunday qo'llanadi.

**Hujjat berilgan viloyat** ro'yxatdan tanlanadi: 12 ta viloyat, Toshkent shahri va
Qoraqalpog'iston Respublikasi. Ro'yxat `contracts/models.py` dagi `VILOYATLAR`
o'zgaruvchisida — o'zgartirish kerak bo'lsa shu yerni tahrirlab, `makemigrations`
va `migrate` buyruqlarini ishga tushiring.

**Hujjat seriya-raqami** yozilishidan qat'i nazar bir ko'rinishga keltiriladi:
`ae5862145`, `AE 5862145`, `АЕ№5862145` — hammasi `AE№5862145` bo'ladi. Kirill
harflari lotinga o'giriladi, chunki asl shartnomalarda ular aralash yozilgan
(ko'rinishda bir xil, lekin qidiruvda topilmaydigan) edi.

### Garovga qo'yuvchi boshqa shaxs bo'lsa

Formada «Qarz oluvchiniki | Boshqa shaxsniki» degan almashtirgich turadi
(ikkita tugma bitta qutida — `static/css/app.css` dagi `.almashtirgich`).
Zargarlikda «Boshqa shaxsniki» tanlansa — masalan mijoz onasining tillasini
garovga qo'ysa — F.I.Sh., hujjat (turi, viloyat, IIV bo'limi, sana,
seriya-raqam) va manzil so'raladi.

Bu ma'lumot faqat **garov shartnomasi** va **baholash dalolatnomasi**ga tushadi —
mikroqarz shartnomasida qarz oluvchi o'z o'rnida qoladi. «Qarz oluvchiniki»
tanlangan bo'lsa hujjat avvalgidek, ya'ni garovga qo'yuvchi sifatida qarz
oluvchining o'zi chiqadi.

Transportda almashtirgich **uch tugmali** (`VehicleInfo.egasi_turi`) — mashina
faqat shu uch holatda bo'ladi:

| Tanlov | Formada so'raladi | Hujjatda garovga qo'yuvchi |
|---|---|---|
| **Qarz oluvchiniki** | hech narsa — «Egasi» maydoniga saqlashda qarz oluvchining ismi yoziladi | qarz oluvchi (pasporti va manzili bilan) |
| **Boshqa (jismoniy shaxs)** | egasining ismi, hujjati (turi, viloyat, IIV bo'limi/tuman, sana, seriya-raqam) va manzili | qarz oluvchi — **ishonchnoma asosida**; egasining ismi «...га тегишли» degan joyda turadi, u hujjatni imzolamaydi |
| **Boshqa (tashkilot)** | tashkilot nomi va rahbari | tashkilot — buyruq asosida rahbari imzolaydi |

Turi almashtirilsa keraksiz maydonlar tozalanadi — formada ham
(`VehicleForm.clean`), saqlashda ham (`VehicleInfo.save`), shunda eski
egasining ma'lumoti bazada ham, hujjatda ham qolib ketmaydi. Eski
shartnomalarda turi `0018_egasi_turini_aniqlash` migratsiyasi bilan
«Egasi» maydoniga qarab aniqlangan.

«Boshqa (jismoniy shaxs)» holatida mikroqarz shartnomasining 1.1-bandiga qarz
oluvchining shartnoma summasi miqdoridagi kafilligi ham qo'shiladi — xaridor
bergan namuna hujjatdagidek («Давронов Хумоюн — matiz», 2026-08-25).

Shartnoma qachon kiritilgani ro'yxatda «Kiritilgan» ustunida va shartnoma
sahifasida «Kiritilgan vaqti» qatorida turadi (soati bilan, Toshkent vaqti).

### Hujjatdagi harflar rangi

Asl shartnoma fayllarida o'zgaruvchan joylar (ism, summa, sana) qizil rangda
yozilgan edi. Tayyor hujjatda hammasi **qora** qilinadi — buni
`contracts/docx_ulash.py` dagi `qora_qil()` bajaradi, hujjat berilayotgan paytda.
Shablonda ranglar o'z holicha qoladi, shuning uchun shablon tahrirlash sahifasida
`{{ ... }}` belgilari ajralib turaveradi. Xodim o'zi yuklagan shablon ham qora
chiqadi.

Oq rangga tegilmaydi: asl faylda u ko'rinmas to'ldirgich sifatida ishlatilgan.
- `LOMBARD_ORG = {...}` — tashkilot rekvizitlari (nomi, direktor, STIR, bank, manzil).
  Hujjatlarga shu yerdan qo'yiladi, o'zgarsa faqat shu joyni tahrirlang.

## PythonAnywhere'ga joylash (bepul tarif)

1. **Fayllarni yuklash** — `lombard_site` papkasini ZIP qilib Files bo'limiga yuklang
   va Bash konsolda oching:
   ```bash
   unzip lombard_site.zip
   ```

2. **Virtual muhit** (Python 3.13 tanlang — Django 6 uchun kerak):
   ```bash
   mkvirtualenv --python=/usr/bin/python3.13 lombard
   pip install -r lombard_site/requirements.txt
   ```
   Agar 3.13 mavjud bo'lmasa, `requirements.txt` da `Django>=5.2,<6` deb yozing va
   Python 3.10+ ishlatavering — kod ikkalasida ham ishlaydi.

3. **Web ilova** — Web → Add a new web app → Manual configuration → o'sha Python versiyasi.

4. **WSGI fayl** (Web bo'limidagi havoladan tahrirlang), butun mazmunini almashtiring:
   ```python
   import os, sys
   path = '/home/FOYDALANUVCHI/lombard_site'
   if path not in sys.path:
       sys.path.insert(0, path)
   os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
   from django.core.wsgi import get_wsgi_application
   application = get_wsgi_application()
   ```

5. **Virtualenv yo'li** — Web bo'limida `/home/FOYDALANUVCHI/.virtualenvs/lombard`.

6. **Static fayllar** — Web bo'limidagi Static files jadvaliga qo'shing:
   - URL: `/static/` → Directory: `/home/FOYDALANUVCHI/lombard_site/staticfiles`

   So'ng konsolda:
   ```bash
   python manage.py collectstatic
   ```

7. **Xavfsizlik sozlamalari** — WSGI faylida `get_wsgi_application()` dan **oldin**
   quyidagilarni qo'shing:
   ```python
   os.environ['LOMBARD_DEBUG'] = '0'
   os.environ['LOMBARD_HOSTS'] = 'FOYDALANUVCHI.pythonanywhere.com'
   os.environ['LOMBARD_SECRET_KEY'] = '<yangi tasodifiy kalit>'
   ```
   `LOMBARD_DEBUG=0` bo'lganda HTTPS-cookie va boshqa himoya sozlamalari
   avtomatik yoqiladi. Yangi kalitni **serverning o'zida** yasang (shunda kalit
   biror joyda nusxalanib qolmaydi):
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

   **Maxfiy kalit kodda saqlanmaydi.** `LOMBARD_DEBUG=0` bo'lib
   `LOMBARD_SECRET_KEY` berilmasa, sayt ataylab ishga tushmaydi va
   `ImproperlyConfigured` xatosi chiqadi — ya'ni serverda tasodifan zaif kalit
   bilan ishlab ketish mumkin emas. Lokal ishlashda (`LOMBARD_DEBUG=1`)
   o'zgaruvchi shart emas: kalit birinchi ishga tushirishda `.secret_key`
   faylida yasalib saqlanadi, bu fayl `.gitignore` da — git'ga tushmaydi.
   Kalitni almashtirish kerak bo'lsa, `.secret_key` ni o'chirsangiz yangisi
   yasaladi (mavjud sessiyalar bekor bo'ladi, qaytadan kirish talab qilinadi).

8. **Baza va admin**:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

9. Web bo'limida **Reload** tugmasini bosing.

**Eslatma:** bepul tarifda SQLite bazasi ishlatiladi — kichik lombard uchun yetarli.
Bazani (`db.sqlite3`) vaqti-vaqti bilan Files bo'limidan yuklab olib zaxiralang.

## Loyiha tuzilishi

```
lombard_site/
├── accounts/           # foydalanuvchilar, rollar, ishchi boshqaruvi
├── contracts/
│   ├── models.py       # Contract, JewelryItem, VehicleInfo, GuarantorInfo, DeleteRequest
│   ├── docgen.py       # Word hujjat generatori (shartnoma matnlari shu yerda)
│   ├── num2words_uz.py # sonni kirill-o'zbekcha so'zga aylantirish
│   ├── forms.py
│   └── views.py
├── config/settings.py  # sozlamalar (tashkilot rekvizitlari shu yerda)
├── templates/
├── static/css/app.css
├── static/js/pul.js    # pul maydonini yozayotganda «7 000 000» qilib bo'lish
└── seed_demo.py        # namuna ma'lumotlar
```

## Word hujjatlar qanday yasaladi

Hujjatlar **asl shartnoma fayllarining o'zidan** yasalgan shablonlar asosida
tayyorlanadi — ya'ni o'zgarmas matn va butun formatlash asl faylning aynan o'zi.

```
contracts/shablonlar/
├── asl_196.docx, asl_199.docx   # asl fayllar (tegilmaydi)
├── m196.docx, m199.docx         # run'lari birlashtirilgan oraliq nusxa
├── zargarlik.docx               # 196 dan yasalgan shablon
├── transport.docx               # 199 dan yasalgan shablon
└── kafillik.docx                # 199 dan (garov qismisiz)
```

Shablonlarda o'zgaruvchan qiymatlar `{{ nom }}` ko'rinishida, zargarlik jadvalidagi
namuna qatori esa `#NOMI#`, `#SONI#` kabi belgilar bilan turadi.

**Shablonni qayta yasash** (asl fayl o'zgarsa yoki yangi qiymat qo'shilsa):

```bash
python contracts/shablon_yasash.py
```

Bu buyruq har bir almashtirish topilgan-topilmaganini ko'rsatadi — `YO'Q` chiqsa,
o'sha matn asl faylda o'zgargan degani.

**Muhim:** kafillik (oylik) turida garov shartnomasi va baholash dalolatnomasi
tuzilmaydi — faqat mikroqarz shartnomasi va to'lov jadvali chiqadi.

### Shablonni saytdan o'zgartirish

Maxsus vakolatli boshliq **Shablonlar** bo'limida har bir qator uchun ro'yxatdan
usul tanlaydi:

| Usul | Nima qiladi |
|---|---|
| **Ochish** | Matnni to'g'ridan-to'g'ri brauzerda tahrirlash |
| **Word faylni yuklab olish** | Shablonni kompyuterga olish |
| **Fayl bilan almashtirish** | Word'da tahrirlangan faylni qaytarib yuklash |

Onlayn tahrirlashda:

Sahifada har bir xatboshi alohida qator bo'lib chiqadi:

- **oq fonli matn** — bosib o'zgartiriladi;
- **rangli belgilar** (`{{ fio }}`, `#NOMI#`) — qulflangan, tahrirlab bo'lmaydi.
  Bu joylarga mijoz ma'lumotlari yoziladi.

O'zgartirilgan qatorlar chap chetida sariq chiziq bilan belgilanadi, pastdagi
panelda nechta qism o'zgargani ko'rinadi. Saqlashdan oldin tizim shablonni
tekshiradi (kerakli belgilar joyidami, sinov to'ldirish o'tadimi) — xato bo'lsa
saqlanmaydi va joriy shablon buzilmaydi.

Agar biror belgi soni kamayib qolsa (masalan `{{ fio }}` 7 joydan 6 ta bo'lib
qolsa), saqlanadi, lekin **ogohlantirish** chiqadi va qaysi belgi kamayganini
aytadi. Har saqlashdan oldin eski nusxa `contracts/shablonlar/zaxira/` papkasiga
sana-vaqt bilan saqlanadi.

### Amallar tarixi

**Tarix** bo'limi (boshliqlar uchun) kim, qachon, nima qilganini ko'rsatadi:

- shartnoma yaratildi / o'zgartirildi / o'chirildi;
- o'chirish so'rovi yuborildi / tasdiqlandi / rad etildi;
- ishchi qo'shildi / bo'shatildi / o'chirildi, paroli o'zgartirildi;
- shablon o'zgartirildi (onlayn yoki fayl bilan).

Shartnoma va shablon o'zgarishida **faqat nechta qism o'zgargani** yoziladi —
qaysi maydon ekani saqlanmaydi.

Ism va obyekt nomi matn sifatida nusxalanadi, shuning uchun foydalanuvchi yoki
shartnoma o'chirilsa ham tarix yozuvi o'qilishli qoladi. Kim, amal turi va sana
oralig'i bo'yicha filtrlash mumkin. Tarix qo'lda tahrirlanmaydi — admin panelda
ham faqat o'qish uchun ochiq.

### PDF

Shartnomani PDF ko'rinishida ham yuklab olish mumkin. PDF Word faylidan
aylantiriladi, shuning uchun serverda **LibreOffice** (Linux) yoki **MS Word**
(Windows) bo'lishi kerak. Ikkalasi ham bo'lmasa PDF tugmasi ko'rinmaydi va
faqat Word yuklab olinadi.

**PythonAnywhere bepul tarifida LibreOffice yo'q** — u yerda PDF ishlamaydi.
Kerak bo'lsa pullik tarifga o'tib LibreOffice o'rnatiladi, yoki xodimlar Word
faylni ochib «PDF sifatida saqlash» qiladi.

`contracts/docgen.py` dagi eski usul (matn koddan yoziladigan) `build_contract_docx_eski`
nomi bilan zaxira sifatida qolgan — hozir ishlatilmaydi.
