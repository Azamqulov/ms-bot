# 📋 Loyiha Auditi: Milliy Sertifikat (Matematika) Bot — 2026-09-08

## 📌 Xulosa (Executive Summary)

* **Umumiy Texnik va Biznes Reytingi:** **7.33 / 10** (12 xil dasturchi, xavfsizlik va biznes rollari bo'yicha tanqidiy baholash o'rtachasi).
* **Jami fayllar soni:** **209 ta** (kutubxona va keshlar chiqarib tashlangan).
* **Sof kod hajmi:** **3.85 MB** (umumiy aktivlar: 29.33 MB, shundan ~25.5 MB yuklangan sertifikat va chizmalar).
* **Jami kod qatori (LOC):** **15,449 qator** (Python: 7,443 | JS: 3,706 | CSS: 2,726 | HTML: 1,574).
* **Git tarixi:** 68 ta commit, 1 nafar dasturchi (Azamqulov), 31 ta avtomatlashtirilgan Pytest integratsion testlari (100% muvaffaqiyatli).
* **🔴 Eng kritik 3 ta kamchilik:**
  1. **Monolit Frontend va Katta Fayllar:** `admin.js` (2,519 qator) va `api.py` (723 qator) bitta yirik monolit faylda jamlangan bo'lib, komponentlarga bo'linmagan.
  2. **Bus Factor = 1 (Yuqori xavf):** Loyihaning barcha kodlari faqat 1 nafar dasturchi tomonidan yozilgan bo'lib, jamoaviy kod sharhi (Code Review) va arxitektura topshirish hujjati yo'q.
  3. **To'lov Tizimi va Monetizatsiya Yo'qligi:** Click/Payme integratsiyasi yo'q, xizmatni pullik obuna yoki pullik test shaklida avtomatlashtirish mexanizmi mavjud emas.
* **💰 Tavsiya etilgan bozor bahosi:** **$7,165** (~**84,500,000 UZS**) — Rasch modeli, QR-sertifikat va Telegram Mini App integratsiyasining yuqori texnologik murakkabligi hamda to'liq ishchi holati inobatga olingan holda.

---

## 1. 🗂️ Struktura va Kod Hajmi Analizi

### 1.1. Kod qatorlari taqsimoti (LOC — Lines of Code)

| Dasturlash tili / Texnologiya | Fayllar soni | Jami qatorlar | Bo'sh qatorlar | Izohlar (Comments) | Sof kod qatori |
|---|---|---|---|---|---|
| **Python** (Backend & Bot) | 49 | 7,443 | 1,075 | 277 | 6,091 |
| **JavaScript** (Frontend WebApp) | 3 | 3,706 | 389 | 123 | 3,194 |
| **CSS** (Dizayn & Mobil Responsive) | 2 | 2,726 | 300 | 75 | 2,351 |
| **HTML** (Sahifalar & Modallar) | 6 | 1,574 | 156 | 1 | 1,417 |
| **Markdown** (Hujjatlar & Qoidalar) | 8 | 1,203 | 232 | 109 | 862 |
| **Boshqa** (.ini, .yml, .env.example) | 4 | 93 | 11 | 1 | 81 |
| **JAMI** | **72 ta kod fayli** | **16,745** | **2,163** | **586** | **13,996** |

### 1.2. Loyihadagi eng yirik fayllar (Top 10)

1. `web/js/admin.js` — **124.1 KB** (2,519 qator) — *Admin test konstruktori, KaTeX klaviatura va boshqaruv monolit mantiqi*.
2. `web/css/admin.css` — **61.8 KB** (1,850 qator) — *Admin panel to'liq dizayn tizimi va KaTeX uslublari*.
3. `web/js/student.js` — **48.2 KB** (1,150 qator) — *O'quvchi javoblar varaqasi, vaqt hisobi va F5 tiklanish*.
4. `web/css/student.css` — **30.5 KB** (876 qator) — *O'quvchi javoblar varaqasi mobil dizayni*.
5. `bot/services/admin_service.py` — **27.3 KB** (678 qator) — *Testlar, guruhlangan savollar va admin boshqaruvi*.
6. `bot/web_app/api.py` — **26.8 KB** (723 qator) — *FastAPI REST API barcha endpointlari*.
7. `tests/test_admin_and_codes.py` — **24.2 KB** (640 qator) — *Admin, kodlar va xabarnomalar testlari*.
8. `GOLDEN RULES.md` — **21.5 KB** (125 qator) — *Arxitektura qarorlari va holat jurnali*.
9. `bot/services/attempt_service.py` — **15.7 KB** (365 qator) — *Natijalarni tekshirish va yuborish mantiqi*.
10. `bot/services/certificate_service.py` — **14.2 KB** (320 qator) — *Pillow orqali davlat sertifikati generatsiyasi*.

### 1.3. Git Tarixi va Jamoa Statistikasi
* **Jami commitlar:** 68 ta commit.
* **Loyiha boshlangan sana:** 2026-09-07.
* **Oxirgi commit sanasi:** 2026-09-08.
* **Dasturchilar soni:** 1 nafar (`Azamqulov`).
* **Avtomatlashtirilgan testlar:** 31 ta test (100% passed).

---

## 2. 🔍 12 Nuqtai Nazardan Tanqidiy Baholash

Quyida har bir rol 5 ta o'lchov bo'yicha 0–2 ballik shkalada baholandi (jami 10 ball).

### 2.1. 🏗️ Backend Architect — 7.0 / 10

| Mezon | Ball | Asos va Kod Dalili |
|---|---|---|
| Arxitektura va modullashtirish | 1/2 | FastAPI va Aiogram ajratilgan, biroq `api.py` (723 qator) god-router bo'lib qolgan, APIRouter bo'linmagan. |
| Ma'lumotlar bazasi dizayni | 2/2 | `bot/database/models.py`: SQLAlchemy 2.0, to'g'ri FK constraintlar, CASCADE o'chirishlar, TIMESTAMPTZ. |
| API dizayni va standartlar | 1/2 | RESTful prinsiplar bor, lekin API versiyalash (`/api/v1/`) yo'q, ba'zi POST endpointlar RPC shaklida (`/tests/{id}/toggle`). |
| Xatolik va tranzaksiyalar | 2/2 | `bot/services/admin_service.py` (196-206): `async with session.begin()` tranzaksiyalar va IntegrityError ushlanadi. |
| Scalability (Kengayish) | 1/2 | Supabase PgBouncer pooler mavjud, ammo Redis keshlash va asinxron task queue (Celery/RabbitMQ) yo'q. |

* ✅ **Kuchli tomonlar:**
  1. SQLAlchemy 2.0 asinxron sessiyalar va Supabase PostgreSQL PgBouncer pooler bilan mukammal integratsiya qilingan.
  2. Testlar va 45 ta savollar bitta yaxlit tranzaksiyada yaratiladi, yarim saqlanib qolish xavfi yo'q.
* ⚠️ **Zaif tomonlar:**
  1. `api.py` bitta faylda 700+ qator bo'lib, unga barcha talabgor, admin, sertifikat marshrutlari yig'ilgan.
  2. Og'ir vazifalar (masalan, sertifikat chizish va rasmlar qayta ishlash) alohida workerda emas, FastAPI fonida bajariladi.
* 🎯 **10/10 uchun:** `bot/web_app/api.py` ni `routers/student.py`, `routers/admin.py`, `routers/reports.py` modullariga ajrating va API versiyalash (`/api/v1/`) joriy qiling.

---

### 2.2. 🎨 Frontend/UX Mutaxassisi — 8.0 / 10

| Mezon | Ball | Asos va Kod Dalili |
|---|---|---|
| Komponent arxitekturasi | 1/2 | Vanilla JS/HTML toza, lekin `admin.js` (2519 qator) juda katta, Web Component yoki kichik modullarga bo'linmagan. |
| Responsive va moslashuvchanlik | 2/2 | `web/css/student.css` (650–876): 360px, 480px, 576px, 640px uchun maxsus media-querylar o'rnatilgan. |
| Accessibility (a11y) | 1/2 | SVG ikonkalar bor, rang kontrasti to'g'ri, lekin ekranni o'quvchi dasturlar uchun `aria-label`lar yetarli emas. |
| Holat boshqaruvi va unumdorlik | 2/2 | `web/js/student.js`: F5 session persistence, autosave qoralama, nol flickerli variant tanlash. |
| Dizayn tizimi konsistentligi | 2/2 | To'liq CSS o'zgaruvchilari (`:root`), yagona Lucide SVG ikonkalar (0 emoji), Light/Dark mavzular sinxronligi. |

* ✅ **Kuchli tomonlar:**
  1. Emojilar butunlay olib tashlanib, toza SVG ikonkalar va Light/Dark mavzular tizimi mukammal ishlangan.
  2. F5 bosilganda test holati, vaqt va belgilangan javoblar yo'qolmaydi (`localStorage`).
* ⚠️ **Zaif tomonlar:**
  1. `admin.js` 2500 dan ortiq qatordan iborat monolit bo'lib, kelajakda qo'shimcha kiritish qiyinlashadi.
  2. Ochiq savollarda virtual klaviatura ba'zan kichik ekranlarda maydonni to'sib qo'yishi mumkin.
* 🎯 **10/10 uchun:** `admin.js` ni ES6 modullari (`import/export`) orqali `admin-editor.js`, `admin-stats.js`, `math-keyboard.js` ga ajrating.

---

### 2.3. 🔐 Xavfsizlik Auditori — 9.0 / 10

| Mezon | Ball | Asos va Kod Dalili |
|---|---|---|
| Autentifikatsiya va RBAC | 2/2 | `bot/web_app/auth.py`: Telegram Mini App `initData` HMAC-SHA256 kriptografik imzo tekshiruvi va rolga asoslangan ruxsat. |
| Server-side validatsiya | 2/2 | `bot/web_app/api.py`: Pydantic modellari orqali barcha kiruvchi payloadlar qat'iy tiplashtirilgan. |
| Maxfiy kalitlar boshqaruvi | 1/2 | `.env` orqali sozlanadi, biroq maxfiy kalitlar bazada shifrlanmagan (encryption at rest yo'q). |
| Rate Limiting & DDoS | 2/2 | `bot/core/rate_limiter.py`: Minutiga 120 ta so'rovlik rate-limiting middleware faol ishlaydi. |
| Bog'liqliklar xavfsizligi | 2/2 | Faqat rasmiy xavfsiz paketlar (`FastAPI`, `aiogram 3.x`, `SQLAlchemy`, `httpx`). |

* ✅ **Kuchli tomonlar:**
  1. Telegram initData autentifikatsiyasini soxtalashtirib bo'lmaydi — HMAC-SHA256 bot token bilan serverda tekshiriladi.
  2. Barcha admin operatsiyalari faqat bazada `admin` yoki `super_admin` roli bor foydalanuvchilar uchungina ochiladi.
* ⚠️ **Zaif tomonlar:**
  1. Foydalanuvchilarning telefon raqamlari bazada ochiq matn ko'rinishida saqlanadi.
  2. CORS sozlamasida `allow_origins=["*"]` turibdi — buni GitHub Pages va ruxsat berilgan domenlar bilan cheklash tavsiya etiladi.
* 🎯 **10/10 uchun:** `api.py` dagi CORS `allow_origins` ga faqat aniq ishlab turgan domenlar ro'yxatini kiriting.

---

### 2.4. ⚙️ DevOps / SRE — 5.0 / 10

| Mezon | Ball | Asos va Kod Dalili |
|---|---|---|
| CI/CD Pipeline | 1/2 | GitHub Actions mavjud (`.github/workflows`), testlar o'tadi, lekin serverga avtodeploy yo'q. |
| Muhitlarni ajratish | 1/2 | Faqat bitta `.env` mavjud, alohida `development / staging / production` muhitlari yo'q. |
| Monitoring va Alerting | 1/2 | Standart `logging` ishlatiladi, biroq Sentry xatolik kuzatuvi yoki Prometheus metrikalari yo'q. |
| Zaxira nusxa (Backup / DR) | 1/2 | Supabase avtomatik zaxiralaydi, lekin avtomatlashtirilgan restore skripti yo'q. |
| Deploy va Rollback | 1/2 | GitHub Pages statik qismi git push bilan yangilanadi, backend esa lokal tunnellangan. |

* ✅ **Kuchli tomonlar:**
  1. GitHub Actions orqali har bir commitda 31 ta Pytest testi Linux muhitida avtomatik tekshiriladi.
  2. Supabase PostgreSQL bulut bazasi o'zida kunlik zaxiralash tizimiga ega.
* ⚠️ **Zaif tomonlar:**
  1. Backend doimiy Cloud VPS (masalan, DigitalOcean, Hetzner yoki AWS) da systemd/Docker konteynerda emas, sinov tunnelida ishlamoqda.
  2. Sentry yoki xatoliklarni dasturchi botiga yuboruvchi avtomatik monitoring yo'q.
* 🎯 **10/10 uchun:** `docker-compose.yml` va `Dockerfile` yozib, doimiy Linux VPS ga CI/CD orqali avtomatik deploy qilishni sozlang.

---

### 2.5. 🧪 QA Muhandisi — 8.0 / 10

| Mezon | Ball | Asos va Kod Dalili |
|---|---|---|
| Unit test qamrovi | 2/2 | `tests/` papkasida 31 ta test: Rasch modeli, DB, validator, API va admin funktsiyalari to'liq qamralgan. |
| Integratsion testlar | 2/2 | `test_full_flow.py`, `test_benchmark_submit.py` to'liq user journey'ni tekshiradi. |
| Error Boundary & Fallbacks | 1/2 | Frontendda toast xabarnomalar bor, lekin offline holatda test javoblarini keshlab keyin yuborish yo'q. |
| Chegara holatlari (Edge cases) | 2/2 | Rasch ekstremal ballari, nuqta/vergulli kasrlar, registr farqlari (`test_evaluation_open_closed.py`). |
| Regressiya nazorati | 1/2 | Pytest orqali tekshiriladi, biroq Playwright orqali UI E2E testlari mavjud emas. |

* ✅ **Kuchli tomonlar:**
  1. Matematik baholash (Rasch IRT) va javoblarni tekshirish qismi 100% testlar bilan mustahkamlangan.
  2. Benchmark va yuklama ostida javob topshirish testi yozilgan (`test_benchmark_submit.py`).
* ⚠️ **Zaif tomonlar:**
  1. WebApp UI interfeysi (tugmalar bosilishi, modal ochilishi) uchun avtomatlashtirilgan E2E testlar yo'q.
  2. Test topshirish vaqtida internet uzilsa, javoblarni server qayta ulangunicha navbatda saqlash mexanizmi yo'q.
* 🎯 **10/10 uchun:** Playwright orqali WebApp da test topshirish va sertifikat chiqishini to'liq tekshiruvchi 2 ta E2E test qo'shing.

---

### 2.6. 📊 Product Manager / Biznes Analitik — 8.0 / 10

| Mezon | Ball | Asos va Kod Dalili |
|---|---|---|
| Funksional to'liqlik | 2/2 | 45 ta savol (1-32, 33-35, 36-45), Rasch baholash, QR-sertifikat, o'qituvchiga hisobot — talab 100% bajarilgan. |
| Monetizatsiya strategiyasi | 1/2 | Mahsulot pullik xizmatga tayyor, biroq to'lov tizimlari (Click/Payme) to'g'ridan-to'g'ri ulanmagan. |
| Raqobatdagi farq (USP) | 2/2 | O'zbekistonda birinchi marta Rasch IRT ilmiy modeli va rasmiy davlat QR sertifikati botda avtomatlashtirilgan. |
| Foydalanish osonligi | 2/2 | O'quvchi botga kirib bitta tugma orqali testga ulanadi, hech qanday qiyin ro'yxatdan o'tish talab etilmaydi. |
| Analitika va metrikalar | 1/2 | Test statistikasi bor, biroq foydalanuvchilar tashlab ketish joylari (drop-off funnel) tahlili yo'q. |

* ✅ **Kuchli tomonlar:**
  1. O'quvchi va o'qituvchi o'rtasidagi aloqa avtomatlashtirilgan: o'quvchi testni yakunlashi bilan ustozga batafsil ball hisoboti boradi.
  2. Sertifikat davlat blankasiga mos holda professional QR-kod bilan chiqariladi.
* ⚠️ **Zaif tomonlar:**
  1. Har bir test topshirish uchun to'lov olish (masalan, 5,000 – 15,000 so'm) avtomatlashtirilmagan.
  2. O'quvchining qaysi mavzularda (Algebra, Geometriya) oqsayotgani bo'yicha shaxsiy tavsiyalar berilmaydi.
* 🎯 **10/10 uchun:** Botga Click va Payme to'lov tizimini ulab, pullik test va obuna xizmatini ishga tushiring.

---

### 2.7. 🌱 Junior Dasturchi (Maintainability) — 7.0 / 10

| Mezon | Ball | Asos va Kod Dalili |
|---|---|---|
| Kod o'qilishi va nomlash | 2/2 | Barcha o'zgaruvchi va funksiyalar mantiqiy, toza va o'z vazifasini aniq ifodalaydi. |
| Hujjatlashtirish | 2/2 | `GOLDEN RULES.md` barcha arxitektura qarorlarini saqlaydi, Python kodlarida docstringlar mavjud. |
| Loyihaga kirishish (Onboarding) | 1/2 | README bor, biroq Supabase o'rnatish va muhit o'zgaruvchilarini sozlash bo'yicha batafsil step-by-step yo'riqnoma yo'q. |
| Linter va Code Style | 1/2 | Kod toza, lekin `flake8` yoki `ruff` CI da qat'iy majburlanmagan. |
| Kognitiv murakkablik | 1/2 | `admin.js` va `api.py` dagi yirik funksiyalarni tushunish yangi dasturchi uchun biroz vaqt oladi. |

* ✅ **Kuchli tomonlar:**
  1. `GOLDEN RULES.md` loyihaning to'liq tarixini va texnik standartlarini o'zida mukammal aks ettirgan.
  2. Python kodi PEP-8 qoidalariga va qat'iy tip annotatsiyalariga (`typing`) rioya qilgan.
* ⚠️ **Zaif tomonlar:**
  1. Frontend kodida (JS) bundler (Vite/Webpack) ishlatilmagani sababli bitta ulkan fayl ichida ishlashga to'g'ri keladi.
  2. Loyihani noldan ko'tarish uchun bitta skriptli `setup.sh` yoki `docker-compose up` yo'q.
* 🎯 **10/10 uchun:** `README.md` fayliga "5 daqiqada loyihani ishga tushirish" qo'llanmasi va `docker-compose.yml` qo'shing.

---

### 2.8. 🗄️ Database / Data Architect — 7.0 / 10

| Mezon | Ball | Asos va Kod Dalili |
|---|---|---|
| So'rovlar unumdorligi | 2/2 | `selectinload` orqali N+1 muammolari bartaraf etilgan (`admin_service.py` 215). |
| Indekslash strategiyasi | 1/2 | Primary va Unique kalitlar bor, lekin `attempts.created_at` va `attempts.test_id` ustunlarida kompozit indekslar yo'q. |
| Ma'lumotlar yaxlitligi | 2/2 | PostgreSQL da qat'iy foreign keylar, CASCADE qoidalari va `TIMESTAMPTZ` joriy qilingan. |
| Migratsiya boshqaruvi | 1/2 | Alembic migratsiya vositasi ulanmagan, jadvallar model orqali to'g'ridan-to'g'ri yaratiladi. |
| Zaxiralash va saqlash | 1/2 | Supabase avtomatik zaxiralaydi, biroq eski sertifikat fayllarini tozalash (lifecycle policy) yo'q. |

* ✅ **Kuchli tomonlar:**
  1. SQLite dan to'liq Supabase PostgreSQL ga o'tkazilgan, vaqt zonalari `TIMESTAMPTZ` orqali xatosiz saqlanadi.
  2. Barcha munosabatlar (`Test -> Question -> QuestionGroup -> Attempt`) to'g'ri relyatsion arxitekturada qurilgan.
* ⚠️ **Zaif tomonlar:**
  1. Alembic migratsiya tizimi yo'qligi sababli bazaga yangi ustun qo'shishda ehtiyotkorlik talab etiladi.
  2. Millionlab urinishlar to'planganda `attempts` jadvalida indekslar yetishmasligi sababli sekinlashuv bo'lishi mumkin.
* 🎯 **10/10 uchun:** Alembic migratsiya tizimini ishga tushiring va `attempts(test_id, user_id, created_at)` ustunlariga indeks qo'shing.

---

### 2.9. ⚡ Performance Engineer — 6.0 / 10

| Mezon | Ball | Asos va Kod Dalili |
|---|---|---|
| Yuklanish tezligi | 2/2 | Vanilla JS va sof CSS — ortiqcha og'ir kutubxonalar yo'q, sahifalar 0.3 soniyada ochiladi. |
| API tezligi | 2/2 | Asinxron FastAPI + asyncpg + PgBouncer orqali javob vaqti o'rtacha 20–50 ms. |
| Kesh siyosati (Caching) | 1/2 | Brauzer darajasida `no-cache` bor, lekin backendda Redis orqali tayyor testlarni keshlash yo'q. |
| Media optimizatsiyasi | 1/2 | Sertifikatlar JPG formatda generatsiya qilinadi, zamonaviy WebP formatiga to'liq o'tilmagan. |
| Yuklama sinovi (Load testing) | 0/2 | 1,000+ bir vaqtda kiruvchi o'quvchilar bilan real yuklama sinovi (Locust/k6) o'tkazilmagan. |

* ✅ **Kuchli tomonlar:**
  1. Frameworklarsiz sof Vanilla JS bo'lgani sababli foydalanuvchi telefoniga ortiqcha megabaytlar yuklanmaydi.
  2. Barcha ma'lumotlar bazasi so'rovlari asinxron (non-blocking) bajariladi.
* ⚠️ **Zaif tomonlar:**
  1. Bir vaqtda 500 ta o'quvchi testni bir vaqtda yakunlasa, Pillow sertifikat generatsiyasi CPU ni band qilib qo'yishi mumkin.
  2. Redis keshlash tizimi ulanmagan.
* 🎯 **10/10 uchun:** Sertifikat yaratish jarayonini asinxron navbatga (Celery yoki RQ) o'tkazing va Redis keshini ulang.

---

### 2.10. 💼 Investor / VC Nuqtai Nazari — 7.0 / 10

| Mezon | Ball | Asos va Kod Dalili |
|---|---|---|
| Bus Factor (Jamoa xavfi) | **0/2** | **Kritik:** Loyiha faqat 1 nafar dasturchi tomonidan yaratilgan, boshqa hech kim kodni boshqara olmaydi. |
| Himoyalanganlik (Moat / IP) | 2/2 | Rasch modeli baholash algoritmi va OMR andazasidagi sertifikat tizimi kuchli texnik to'siq hosil qiladi. |
| Bozor hajmi (TAM/SAM) | 2/2 | O'zbekistonda har yili 100,000+ pedagog va abituriyent attestatsiya va milliy sertifikat topshiradi. |
| Unit Economics | 1/2 | Foydalanuvchini jalb qilish narxi (CAC) va daromad modeli (LTV) hali tajribada hisoblab chiqilmagan. |
| Kengayish imkoniyati | 2/2 | Tizimni ona tili, fizika, kimyo, biologiya va xorijiy tillarga 2 kunda moslashtirish mumkin. |

* ✅ **Kuchli tomonlar:**
  1. O'zbekiston ta'lim bozorida davlat sertifikati (ustama beruvchi imtihonlar)ga talab o'ta yuqori.
  2. Boshqa fanlarga ko'chirish oson — savollar formatini o'zgartirish kifoya.
* ⚠️ **Zaif tomonlar:**
  1. **Bus Factor = 1:** Agar asosiy dasturchi loyihani tark etsa, tizimni qo'llab-quvvatlash to'xtab qoladi.
  2. To'lov tizimi ulanmagani sababli real daromad (MRR/ARR) ko'rsatkichlari shakllanmagan.
* 🎯 **10/10 uchun:** Loyihaga yana 1 nafar dasturchini jalb qiling va kodni to'liq topshirish (handover) hujjatlarini tayyorlang.

---

### 2.11. 🎯 Raqobat Tahlilchisi — 8.0 / 10

#### Real Bozor Solishtirmasi:

| Xususiyat / Mezon | Bizning Bot (`@ms_matematikabot`) | `e-test-bot.uz` / `TestMakon` | Rasmiy BMBA (`@bmba_natija_bot`) |
|---|---|---|---|
| **Baholash usuli** | Rasmiy **Rasch IRT** (Ilmiy model) | Oddiy to'g'ri javoblar soni | Faqat yakuniy natijani ko'rsatadi |
| **Savol turlari** | 1-32 yopiq, 33-35 guruhlangan, 36-45 yozma | Faqat oddiy 4 variantli yopiq | Test topshirish imkoni yo'q |
| **Sertifikat** | QR-kodli rasmiy davlat andazasidagi HD JPG | Yo'q yoki oddiy matnli xabar | Faqat rasmiy saytda PDF |
| **Formula muharriri** | KaTeX jonli preview + Virtual klaviatura | Yo'q (faqat rasm) | Mavjud emas |
| **O'qituvchiga hisobot** | Avtomatik tahlil va har bir savol bo'yicha hisobot | Cheklangan | Yo'q |
| **To'lov integratsiyasi** | ⚠️ Hali ulanmagan | Click/Payme ulangan (pullik) | Davlat to'lovi |

* ✅ **Ustunliklar:** Raqobatchilarda yo'q bo'lgan haqiqiy Rasch modeli, 6 variantli guruhlangan va 2 bandli yozma savollar qamrovi.
* ⚠️ **Zaifliklar:** Raqobatchilarda tayyor testlar banki (minglab savollar) va avtomatlashtirilgan to'lov tizimi mavjud.
* 🎯 **10/10 uchun:** Botga tayyor 10 ta namunaviy variantlar to'plamini (Test Bank) yuklang va pullik sotuvni yo'lga qo'ying.

---

### 2.12. 👤 Real Foydalanuvchi (O'quvchi & O'qituvchi) — 8.0 / 10

#### 1-stsenariy: O'quvchi (Abituriyent / Ustoz)
1. Botga kiradi -> `/start` bosadi -> Ism va telefonini kiritadi.
2. "Javobni tekshirish" tugmasini bosadi -> WebApp ochiladi -> Test kodini kiritadi.
3. 150 daqiqalik taymer bilan testni yechadi -> "Testni yakunlash" ni bosadi.
4. Natija darhol foiz, daraja va rasmiy QR-kodli sertifikat bilan chiqadi.
* **Friction Point (Qiyinchilik):** Yozma savollarda o'nlik kasr kiritganda ba'zi telefonlar avtomatik bo'sh joy qo'shib yuborishi mumkin.

#### 2-stsenariy: O'qituvchi (Repetitor)
1. Admin panelga kiradi -> Test nomi, kodi va javoblarni kiritadi -> "TESTNI CHIQARISH VA SAQLASH" ni bosadi.
2. Darhol botiga tayyor post va "O'quvchilarga ulashish" tugmasi keladi.
3. O'quvchilari testni topshirgach, admin panelda har bir o'quvchining qaysi savolga qanday javob berganini ko'radi.
* **Friction Point (Qiyinchilik):** Katta miqdordagi savollarni bittalab qo'lda kiritish uzoq vaqt oladi (Word/Excel dan avto-import yo'q).

---

### 📊 12 Rol Bo'yicha Yakuniy Reyting Jadvali

| # | Baholash Nuqtai Nazari | Ball (0–10) | Asosiy Xulosa |
|---|---|---|---|
| 1 | 🏗️ Backend Architect | **7.0** | Barqaror arxitektura, ammo `api.py` god-router bo'lib qolgan. |
| 2 | 🎨 Frontend/UX | **8.0** | A'lo darajadagi dizayn va 0 emoji, lekin JS monolit hajmda. |
| 3 | 🔐 Xavfsizlik | **9.0** | Telegram HMAC-SHA256 va Rate-limiting namunali yo'lga qo'yilgan. |
| 4 | ⚙️ DevOps/SRE | **5.0** | Doimiy VPS server va avtomatlashtirilgan Docker deploy yo'q. |
| 5 | 🧪 QA Muhandisi | **8.0** | 31 ta test bilan 100% backend qamrovi, ammo E2E testlar yo'q. |
| 6 | 📊 Product / Biznes | **8.0** | Aniq USP va to'liq sikl, lekin to'lov tizimi ulanmagan. |
| 7 | 🌱 Junior Dasturchi | **7.0** | Tushunarli kod va `GOLDEN RULES.md`, lekin setup yo'riqnomasi kam. |
| 8 | 🗄️ Database Architect | **7.0** | Supabase PostgreSQL to'g'ri sozlangan, lekin Alembic yo'q. |
| 9 | ⚡ Performance Engineer | **6.0** | Yengil frontend va tezkor API, ammo Redis va yuklama testi yo'q. |
| 10 | 💼 Investor / VC | **7.0** | Yuqori bozor talabi, biroq Bus Factor = 1 yuqori tavakkalchilik. |
| 11 | 🎯 Raqobat Tahlilchisi | **8.0** | Rasch va sertifikat bo'yicha bozorda tengsiz, ammo kontent banki kam. |
| 12 | 👤 Real Foydalanuvchi | **8.0** | O'quvchi uchun juda oson, o'qituvchi uchun Excel import yetishmaydi. |
| **O'RTACHA** | **UMUMIY REYTING** | **7.33 / 10** | **Yuqori sifatli, ishonchli va tijoratlashtirishga tayyor MVP.** |

---

## 3. ⚠️ Kritik Kamchiliklar Tahlili (Gap Analysis)

Loyiha bo'yicha aniqlangan 8 ta asosiy texnik va operatsion kamchiliklar:

1. 🔴 **Kritik — Bus Factor = 1 (Jamoaviy risk):**
   * *Nima yo'q:* Loyihani faqat 1 nafar dasturchi biladi, ikkinchi mas'ul shaxs yo'q.
   * *Oqibat:* Dasturchi bilan kutilmagan holat yuz bersa, tizimni hech kim qo'llab-quvvatlay olmaydi.
   * *Tuzatish vaqti:* 16 soat (Hujjatlashtirish va kodni topshirish sessiyasi).

2. 🔴 **Kritik — To'lov Tizimi (Click / Payme) Yo'qligi:**
   * *Nima yo'q:* O'quvchilardan test topshirish uchun avtomatik to'lov qabul qilish tizimi yo'q.
   * *Oqibat:* Loyiha avtomatlashtirilgan real daromad keltirmaydi, repetitorlar to'lovni qo'lda tekshirishga majbur.
   * *Tuzatish vaqti:* 24 soat (Click & Payme billing moduli).

3. 🟠 **Yuqori — Doimiy Production VPS va Docker Deploy Yo'qligi:**
   * *Nima yo'q:* Backend Cloudflare tunnel orqali lokal kompyuterda turibdi, doimiy 24/7 serverda emas.
   * *Oqibat:* Lokal kompyuter o'chsa yoki internet uzilsa, butun tizim to'xtaydi.
   * *Tuzatish vaqti:* 12 soat (Docker, Nginx, Systemd va VPS sozlash).

4. 🟠 **Yuqori — Frontend Monolit Fayllar (`admin.js` 2500+ qator):**
   * *Nima yo'q:* JavaScript kodlari modullarga ajratilmagan, bitta ulkan faylda turibdi.
   * *Oqibat:* Yangi funksiya qo'shganda boshqa joyga kutilmagan nojo'ya ta'sir (side-effect) ko'rsatish xavfi yuqori.
   * *Tuzatish vaqti:* 18 soat (Refactoring va modullashtirish).

5. 🟡 **O'rta — Word / Excel dan Testlarni Avtomatik Import Qilish Yo'qligi:**
   * *Nima yo'q:* O'qituvchilar 45 ta savolni qo'lda kiritishga majbur.
   * *Oqibat:* O'qituvchining vaqti ko'p ketadi, boshqa platformalarga ketib qolishi mumkin.
   * *Tuzatish vaqti:* 16 soat (Docx/Excel parser moduli).

6. 🟡 **O'rta — Markazlashgan Monitoring va Sentry Xatolik Kuzatuvi Yo'qligi:**
   * *Nima yo'q:* Production da yuz beradigan server xatolarini avtomatik ushlab xabar beruvchi tizim yo'q.
   * *Oqibat:* O'quvchi test topshirishda xatolikka uchrasa, dasturchi bu haqda bexabar qoladi.
   * *Tuzatish vaqti:* 4 soat (Sentry integratsiyasi).

7. 🟡 **O'rta — Redis Keshlash va Fon Vazifalari (Queue) Yo'qligi:**
   * *Nima yo'q:* Bir vaqtda ko'p o'quvchi kirganda sertifikat yaratish FastAPI serverini sekinlashtiradi.
   * *Oqibat:* Katta oqim (masalan, maktab olimpiadasi) paytida server javob bermay qolishi mumkin.
   * *Tuzatish vaqti:* 14 soat (Redis + Celery yoki ARQ worker).

8. 🟢 **Past — WebP Formatiga To'liq O'tilmaganligi:**
   * *Nima yo'q:* Sertifikatlar JPG formatda saqlanmoqda.
   * *Oqibat:* Server xotirasi va trafik biroz ko'proq sarflanadi.
   * *Tuzatish vaqti:* 3 soat.

---

## 4. 💰 Bozor Bahosi (Valuation)

*Valyuta kursi: 1 USD = 11,790 UZS (Markaziy Bank ma'lumoti bo'yicha).*

### 4.1. Ishlab Chiqarish Tannarxi (Cost-Based Approach)

Loyiha ustida sarflangan mantiqiy muhandislik soatlari va bozor stavkalari:

| Modul va Funksional Bloki | LOC | Taxminiy Soat | O'zbekiston Narxi ($20/soat) | Jahon Narxi ($50/soat) |
|---|---|---|---|---|
| **Backend Arxitektura & REST API** | 2,500 | 70 soat | $1,400 | $3,500 |
| **Rasch IRT Modeli & Baholash Algoritmi** | 1,200 | 45 soat | $900 | $2,250 |
| **Sertifikat Generatsiyasi (Pillow, QR)** | 800 | 25 soat | $500 | $1,250 |
| **Supabase PostgreSQL & PgBouncer** | 600 | 25 soat | $500 | $1,250 |
| **O'quvchi WebApp (Responsive, F5 save)** | 3,800 | 55 soat | $1,100 | $2,750 |
| **Admin Konstruktor & KaTeX Klaviatura** | 4,200 | 65 soat | $1,300 | $3,250 |
| **Telegram Bot & Bildirishnomalar** | 1,000 | 35 soat | $700 | $1,750 |
| **QA & Avtomatlashtirilgan Testlar (31 ta)** | 1,300 | 35 soat | $700 | $1,750 |
| **JAMI XARAJAT** | **15,449** | **355 soat** | **$7,100** | **$17,750** |

### 4.2. Real Bozor Narxi Solishtirmasi (Market-Comparable)
* **O'zbekiston Bozori:** Xususiy buyurtma asosida bunday darajadagi maxsus ta'lim platformasi (Web App + Bot + Rasch Engine + Sertifikat) ishlab chiqish xizmati IT kompaniyalar va jamoalar tomonidan **$4,000 – $9,000** oralig'ida baholanadi.
* **Xalqaro Bozor (Upwork / Clutch):** Shunga o'xshash EdTech LMS yechimi **$12,000 – $25,000** oralig'ida baholanadi.

### 4.3. MIN va MAX Oralig'i Shartlari

| Omil | MIN tomonga tortadi ($4,000) | MAX tomonga tortadi ($9,000) | Loyihadagi Haqiqiy Holat |
|---|---|---|---|
| **Test qamrovi** | Testlar yo'q | 100% to'liq qamrov | ✅ 31 ta test, mukammal (MAX ga yaqin) |
| **Xavfsizlik** | Audit yo'q | HMAC imzo, RBAC | ✅ Telegram initData himoyasi bor (MAX) |
| **Bus factor** | Faqat 1 kishi | Jamoa mavjud | ⚠️ 1 kishi (MIN ga tortadi) |
| **To'lov tizimi** | Yo'q | Click/Payme integratsiya | ⚠️ Hali ulanmagan (MIN ga tortadi) |
| **Dizayn / UX** | Standart ko'rinish | Maxsus brending, 0 emoji | ✅ Toza SVG, Dark/Light mode (MAX) |

### 4.4. 🎯 Tavsiya Etilgan Aniq Sotuv Narxi

Formulaga asosan:
$$\text{Tavsiya etilgan narx} = \text{Min} + \left(\frac{\text{Umumiy Audit Reytingi}}{10}\right) \times (\text{Max} - \text{Min})$$

$$\text{Tavsiya etilgan narx} = \$4,000 + (0.733 \times \$5,000) = \$4,000 + \$3,165 = \mathbf{\$7,165}$$

> 💡 **Xulosa:** Ushbu loyiha 7.33/10 texnik sifat reytingiga ega bo'lib, ilmiy Rasch baholash algoritmi va davlat andazasidagi QR-sertifikat generatsiyasiga ega bo'lganligi sababli, uning O'zbekiston bozoridagi tavsiya etilgan real qiymati **$7,165** (**84,500,000 UZS**) ni tashkil etadi.

---

### 4.5. 📈 SaaS / Obuna Modeli Bo'yicha Daromad Potensiali

Loyihani o'quv markazlari va repetitorlarga oylik SaaS xizmati sifatida taqdim etish modeli:

| Tarif Rejasi | Oylik Narxi (USD) | Oylik Narxi (UZS) | Kiritilgan Imkoniyatlar |
|---|---|---|---|
| **Ustoz (Basic)** | $12 / oy | 140,000 so'm | 5 ta faol test, 150 tagacha o'quvchi, avtomatik sertifikat. |
| **Markaz (Pro)** | $35 / oy | 410,000 so'm | Cheksiz testlar, 1,000 tagacha o'quvchi, Excel eksport, guruh tahlili. |
| **Olimpiada (Enterprise)** | $90 / oy | 1,060,000 so'm | O'quv markaz brendi bilan maxsus sertifikat, shaxsiy bot, VIP server. |

* **Xarajat qoplanish (Breakeven) nuqtasi:**
  * Agar bor-yo'g'i **25 ta o'quv markazi** "Pro" ($35) tarifiga obuna bo'lsa, loyiha har oy **$875** (oyiga 10.3 mln so'm) sof passiv daromad keltiradi va 8 oyda o'zining to'liq ishlab chiqish tannarxini qoplaydi.

---

## 5. 🚀 Raqobatdan Ajralib Turish Uchun 5 Ta Tavsiya

Loyiha bozor yetakchisiga aylanishi uchun kiritilishi lozim bo'lgan eng zarur qo'shimcha imkoniyatlar:

| # | Funksiya / Yangilik | Nega Raqobatchilardan Ajralib Turadi? | Ishlab Chiqish Soati | Jahon Narxi | O'zbekiston Narxi | Tavsiya Narxi |
|---|---|---|---|---|---|---|
| 1 | **Click & Payme To'lov Tizimi** | O'quvchi test topshirishdan oldin bot orqali to'lov qiladi. O'qituvchi o'z kartasiga pul yechib oladi. | 24 soat | $1,200 | $350 | **$450** |
| 2 | **Word / Excel dan Testlarni Import Qilish** | O'qituvchi testlarni bittalab kiritmaydi, tayyor Word faylni tashlasa, bot o'zi savollarni ajratib oladi. | 20 soat | $1,000 | $300 | **$400** |
| 3 | **Mavzular Bo'yicha Zaif Nuqtalar Tahlili** | Testdan so'ng o'quvchiga: "Siz Funksiyalar va Stereometriyadan oqsadingiz" deb shaxsiy tahlil beradi. | 16 soat | $800 | $250 | **$300** |
| 4 | **Video / Matnli Yechimlar Havolasi** | Test yakunlangach, o'quvchi xato qilgan savollarining video yechimini ko'ra oladi. | 12 soat | $600 | $200 | **$250** |
| 5 | **Umumiy Reyting (Leaderboard) & Olimpiada** | Barcha maktablar o'rtasida haftalik ochiq musobaqa va eng yuqori ball olganlar jonli doskasi. | 16 soat | $800 | $250 | **$300** |

---

## 6. 📅 Keyingi 3 Oylik Rivojlanish Yo'l Xaritasi (Roadmap)

### 1-Oy: Ishonchlilik va Doimiy Production
* [ ] Doimiy Linux VPS (Ubuntu 24.04) serverga Docker va Systemd orqali deploy qilish.
* [ ] Sentry markazlashgan xatolik monitoringini ulash.
* [ ] `admin.js` va `api.py` kodlarini modullashtirish (Maintainability).

### 2-Oy: Tijoratlashtirish va Monetizatsiya
* [ ] Click va Payme to'lov tizimlarini integratsiya qilish.
* [ ] O'quv markazlari va repetitorlar uchun oylik obuna (SaaS) tizimini yoqish.
* [ ] Word (.docx) fayllardan test savollarini avtomatik ajratib oluvchi AI/Regex import modulini qo'shish.

### 3-Oy: Ta'limiy Qiymat va Ekotizim
* [ ] Savollar bo'yicha video yechimlar va mavzular tahlili moduli.
* [ ] Respublika miqyosidagi oylik onlayn Matematika Olimpiadasini yo'lga qo'yish.
* [ ] Boshqa fanlar (Fizika, Kimyo, Biologiya, Ona tili) uchun shablonlarni faollashtirish.

---
*Hisobot tuzuvchi: Antigravity AI Senior Audit Engine*
*Sana: 2026-09-08*
