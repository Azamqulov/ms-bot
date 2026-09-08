# 📋 Loyiha Auditi: Milliy Sertifikat (Matematika) Bot — 2026-09-08

## Xulosa (Executive Summary)

- **Loyiha nomi:** Milliy Sertifikat — Matematika (Telegram Bot + Telegram Mini App OMR Test Tizimi)
- **Umumiy Audit Reytingi:** **6.0 / 10.0** (12 xil dasturchi va biznes rollarining qat'iy va tanqidiy o'rtachasi)
- **Hajm ko'rsatkichlari:** 68 ta fayl | Sof dastur kodi: **12 051 qator (LOC)** | Git: 47 commit
- **🔴 Eng kritik 3 ta kamchilik:**
  1. **CI/CD va Avtomatlashtirilgan Deploy yo'qligi:** Docker containerization yo'q, loyiha Windows muhitida `start.py` orqali subprocess sifatida ishlaydi.
  2. **Database Migration (Alembic) yo'qligi:** Ma'lumotlar bazasi o'zgarishlari xom SQL `ALTER TABLE` yoki qo'lda yozilgan skriptlar orqali amalga oshirilgan, rollback mexanizmi yo'q.
  3. **Bus Factor = 1 (Yolg'iz dasturchiga bog'liqlik):** Git tarixida 100% commitlar bitta dasturchiga tegishli, jamoaviy kod ko'rib chiqish (PR review) va SLA yo'q.
- **💰 Tavsiya etilgan bozor narxi:** **$3,500 (taxminan 41 260 000 UZS)** (O'zbekiston bozori uchun) | **$9,200** (Jahon bozori uchun).
  *Asos:* Loyihada rasmiy RASH (IRT) baholash modeli, toza KaTeX formula klaviaturasi va WebApp OMR varaqasi mukammal joriy etilgan, biroq to'lov tizimi, avtomatik test deployi va migratsiya mexanizmlari yetishmasligi narxni o'rta-yuqori diapazonda ushlab turadi.

---

## 1. Struktura va Hajm Tahlili

### Fayllar va Kod Qatorlari (LOC)
| Kengaytma / Til | Fayllar soni | Kod qatorlari (LOC) | Vazifasi |
|---|---|---|---|
| **Python (.py)** | 43 | 5 756 | Aiogram bot, FastAPI backend, Rasch modeli, DB sessiyalari |
| **JavaScript (.js)** | 3 | 3 049 | TMA o'quvchi javoblar varaqasi, Admin test konstruktori, API config |
| **CSS (.css)** | 2 | 2 383 | Dark/Light mavzular, javob kartochkalari, responsive media queries |
| **HTML (.html)** | 4 | 863 | Semantik sahifalar va avto-yo'naltiruvchi ko'priklar |
| **Boshqa (md, txt, ini)** | 16 | 450 | Hujjatlar, konfiguratsiyalar |
| **JAMI SOF KOD** | **68** | **12 051** | **To'liq ishlab turgan modulli kod bazasi** |

### Git Tarixi
- **Jami commitlar:** 47 ta
- **Boshlanish sanasi:** 2026-09-07
- **So'nggi commit:** 2026-09-08
- **Mualliflar soni:** 1 nafar (`Azamqulov`)
- **Bus factor:** 1 (Yuqori xavf darajasi)

---

## 2. 12 Nuqtai Nazardan Tanqidiy Baholash

### 1. 🏗️ Backend Architect — 6 / 10
| Mezon | Ball | Asos va Dalil (Fayl / Qator) |
|---|---|---|
| Arxitektura/modullashtirish | 2/2 | `bot/core`, `bot/database`, `bot/services`, `bot/web_app` qatlamlari to'liq ajratilgan. |
| DB dizayni | 1/2 | Normalizatsiya qilingan, ammo `attempts(user_id, status)` bo'yicha kompozit index yo'q (`models.py:91-100`). |
| API dizayni | 1/2 | RESTful endpointlar bor, ammo versiyalash (`/api/v1/`) yo'q, xato javoblari noizchil (`api.py:145-200`). |
| Xatolik/tranzaksiya | 1/2 | Test submitda tranzaksiya bor, lekin test yaratishda concurrent race condition himoyasi yo'q (`admin_service.py:118`). |
| Scalability | 1/2 | Redis kesh yo'q, har bir savol so'rovi to'g'ridan-to'g'ri Supabase PostgreSQL bazasiga boradi. |

- ✅ **Kuchli tomonlar:** FastAPI va Aiogram bir xil asinxron hodisalar siklida (`asyncio.gather`) uyg'un ishlaydi (`bot/main.py:90-95`). Supabase PgBouncer pooler bilan `statement_cache_size=0` xavfsiz sozlangan (`session.py:23`).
- ⚠️ **Zaif tomonlar:** API versiyalash yo'q; kesh qatlami (masalan, test savollari uchun Redis/in-memory cache) yo'qligi sababli bazaga yuklama ortishi mumkin.
- 🎯 **10/10 uchun:** `attempts` va `questions` jadvallariga kompozit indexlar qo'shing; API ni `/api/v1/` prefiksi bilan versiyalang; Redis keshini ulab test savollarini xotiradan bering.

---

### 2. 🎨 Frontend/UX Mutaxassisi — 6 / 10
| Mezon | Ball | Asos va Dalil (Fayl / Qator) |
|---|---|---|
| Komponent arxitekturasi | 1/2 | Vanilla JS/CSS modullariga ajratildi (`web/js/student.js`, `web/js/admin.js`), lekin string HTML template orqali yig'iladi. |
| Responsive/cross-device | 2/2 | 360px, 480px, 576px, 640px media querylari to'liq kiritilgan (`web/css/student.css:650-750`). |
| Accessibility (a11y) | 0/2 | ARIA atributlari, screen reader yorliqlari va to'liq keyboard navigatsiyasi deyarli yo'q. |
| State/performance | 1/2 | Holat global o'zgaruvchilarda (`currentTest`, `answers`) saqlanadi, re-render DOM tozalash bilan bo'ladi. |
| Dizayn tizimi | 2/2 | `:root` va `[data-theme="dark"]` CSS tokenlar tizimi to'liq, Lucide SVG ikonkalar yagona o'lchamda. |

- ✅ **Kuchli tomonlar:** F5 bosilganda javoblar va vaqt saqlanib qoladi (Session Recovery); Dark/Light rejim sinxronlashgan.
- ⚠️ **Zaif tomonlar:** A11y (Accessibility) standartlari qo'llanilmagan; `web/js/admin.js` 1800 qatordan iborat bo'lib, DOM manipulyatsiyasi qo'lda bajariladi.
- 🎯 **10/10 uchun:** Barcha tugma va inputlarga `aria-label` va klaviatura fokus halqalarini (`:focus-visible`) qo'shing; kelgusida admin panelini Vue 3 yoki Svelte komponentlariga o'tkazing.

---

### 3. 🔐 Xavfsizlik Auditori — 6 / 10
| Mezon | Ball | Asos va Dalil (Fayl / Qator) |
|---|---|---|
| Auth/Authorization | 2/2 | Admin API da Telegram WebApp `initData` HMAC-SHA256 tekshiruvi va RBAC bor (`bot/web_app/auth.py:20-65`). |
| Input validation | 1/2 | Pydantic modellar bor, lekin savol matnlari va formulalarda XSS sanitize filtri yo'q (`api.py:103-131`). |
| Secret management | 1/2 | `.env` mavjud, lekin ishlab turgan bazaning paroli `.env` da ochiq holda saqlanadi. |
| Rate limiting/brute-force | 0/2 | Hech qanday rate-limiting yo'q, `/api/test/submit` yoki `/api/test/{code}` ochiq turibdi. |
| Dependency zaifliklari | 2/2 | Kutubxonalar zamonaviy va xavfsiz versiyalarda (`fastapi 0.115`, `aiogram 3.31`). |

- ✅ **Kuchli tomonlar:** Telegram Mini App kriptografik HMAC-SHA256 xeshi serverda tekshiriladi, begonalar admin bo'la olmaydi.
- ⚠️ **Zaif tomonlar:** Rate limiting yo'qligi sababli bot va backend osongina spam qilinishi mumkin; foydalanuvchi kiritgan matnlarda sanitizatsiya yo'q.
- 🎯 **10/10 uchun:** `slowapi` yoki Nginx darajasida IP bo'yicha rate limit (masalan, 60 req/min) o'rnating; foydalanuvchi kiritgan matnlarga HTML sanitizatsiya qo'shing.

---

### 4. ⚙️ DevOps/SRE — 3 / 10
| Mezon | Ball | Asos va Dalil (Fayl / Qator) |
|---|---|---|
| CI/CD | 0/2 | GitHub Actions yoki avtomatik pipeline umuman yo'q. |
| Environment separation | 1/2 | Faqat bitta muhit mavjud (dev va prod aralash holda Supabase ga ulanadi). |
| Monitoring/logging | 1/2 | Faqat stdout konsol logi (`bot/main.py:25-31`), Sentry yoki markazlashgan log yo'q. |
| Backup/DR | 1/2 | Supabase avtomatik zaxiralaydi, lekin mustaqil zaxiralash skripti mavjud emas. |
| Deploy avtomatlashtirilgan | 0/2 | Dockerfile yoki docker-compose yo'q; Windows `start.py` orqali qo'lda ishga tushiriladi. |

- ✅ **Kuchli tomonlar:** `start.py` orqali Cloudflare tunnel va botni avtomatik bir buyruq bilan yoqish mexanizmi mavjud.
- ⚠️ **Zaif tomonlar:** Docker yo'qligi sababli loyihani Linux VPS yoki Kubernetes klasteriga deploy qilish qiyin; CI/CD yo'qligi xatolarni faqat ishlab turganda aniqlashga olib keladi.
- 🎯 **10/10 uchun:** `Dockerfile` va `docker-compose.yml` fayllarini yarating; GitHub Actions orqali testlarni har pushda avtomatik tekshiradigan pipeline o'rnating.

---

### 5. 🧪 QA Muhandisi — 7 / 10
| Mezon | Ball | Asos va Dalil (Fayl / Qator) |
|---|---|---|
| Unit test qamrovi | 1/2 | 20 ta Pytest testlari mavjud (`tests/`), biroq umumiy qamrov 50% atrofida. |
| Integration/E2E | 1/2 | API va full flow sinovlari bor, ammo brauzer darajasidagi E2E testlar yo'q. |
| Error boundary | 2/2 | `apiFetch` o'z-o'zini tiklovchi avto-fallback mexanizmiga ega (`config.js:46-65`). |
| Edge case handling | 2/2 | Matematik ifodalar, kasrlar va Rasch haddan tashqari holatlari (`test_rasch.py:18-35`) to'liq qamralgan. |
| Regression jarayoni | 1/2 | Qo'lda tekshirish, avtomatlashtirilgan regression pipeline yo'q. |

- ✅ **Kuchli tomonlar:** Rasch IRT algoritmi, LaTeX tozalash va ochiq savollar validatsiyasi unit testlar bilan qat'iy himoyalangan (20/20 test o'tmoqda).
- ⚠️ **Zaif tomonlar:** Frontend interfeysi (UI/UX) uchun avtomatik E2E testlar (masalan, Playwright) mavjud emas.
- 🎯 **10/10 uchun:** `pytest-cov` ulab test coverage ni 80%+ ga chiqaring; Playwright bilan test topshirish jarayonini avtomatlashtirilgan E2E testga aylantiring.

---

### 6. 📊 Product Manager / Biznes Analitik — 7 / 10
| Mezon | Ball | Asos va Dalil (Fayl / Qator) |
|---|---|---|
| Funksional to'liqlik | 2/2 | 45 talik mock, RASH modeli, A+-C daraja, sertifikat generatsiyasi mavjud. |
| Monetizatsiya | 1/2 | Click / Payme to'lov shlyuzlari ulanmagan; faqat bepul yoki qo'lda boshqariladi. |
| Raqobatdan farqi (USP) | 2/2 | Rasmiy RASH (IRT) baholash modeli va qulay formula klaviaturasi. |
| Onboarding/friction | 2/2 | Telegram botga kirish bilan darhol ism-familiya so'raladi va WebApp ochiladi. |
| Analytics/metrikalar | 0/2 | Foydalanuvchilar qayerda chiqib ketayotganini ko'rsatuvchi analitika (Mixpanel/PostHog) yo'q. |

- ✅ **Kuchli tomonlar:** O'quvchi va o'qituvchilar uchun juda aniq va foydali mahsulot; sertifikat darhol rasm ko'rinishida taqdim etiladi.
- ⚠️ **Zaif tomonlar:** To'lov tizimi yo'qligi biznesdan pul ishlab olishni cheklaydi; analitika yo'qligi sababli qaysi savollarda o'quvchilar ko'p xato qilayotgani tahlil qilinmaydi.
- 🎯 **10/10 uchun:** Payme / Click Billing integratsiyasini qiling; bot va webapp ichiga PostHog yoki Yandex Metrika hodisalarini o'rnating.

---

### 7. 🌱 Junior Dasturchi (Maintainability) — 7 / 10
| Mezon | Ball | Asos va Dalil (Fayl / Qator) |
|---|---|---|
| Nomlash/o'qilishi | 2/2 | Python va JS kodlari PEP8 va Clean Code qoidalariga mos yozilgan. |
| Documentation | 2/2 | `GOLDEN RULES.md` va fayllardagi docstringlar to'liq va tushunarli. |
| Onboarding | 2/2 | `README.md` mavjud, virtualenv yaratish va ishga tushirish oson. |
| Linter/formatter | 0/2 | Pre-commit hook, Ruff yoki Black konfiguratsiyasi o'rnatilmagan. |
| Kognitiv murakkablik | 1/2 | `web/js/admin.js` (86 KB) va `web/js/student.js` (41 KB) juda katta va ichma-ich kodlarga ega. |

- ✅ **Kuchli tomonlar:** Loyiha arxitekturasi va mantiqiy bo'linishi har qanday yangi dasturchi tez tushunadigan darajada izchil.
- ⚠️ **Zaif tomonlar:** Katta frontend JS fayllari kichikroq komponentlarga ajratilmagan; linter nazorati yo'q.
- 🎯 **10/10 uchun:** `pyproject.toml` ga `ruff` sozlamasini kiriting; `admin.js` ni 3-4 ta alohida modulga (keyboard, editor, stats) bo'ling.

---

### 8. 🗄️ Database/Data Architect — 6 / 10
| Mezon | Ball | Asos va Dalil (Fayl / Qator) |
|---|---|---|
| Query performance | 2/2 | `selectinload` orqali N+1 muammosi to'liq bartaraf etilgan. |
| Index strategiyasi | 1/2 | Asosiy PK va UK lar bor, biroq statistika uchun kerakli kompozit indexlar yetishmaydi. |
| Data integrity | 2/2 | `CASCADE` va `SET NULL` qoidalari to'liq joriy qilingan (`models.py:44,58,71`). |
| Migration strategiyasi | 0/2 | Alembic yo'q! Bazaga o'zgartirishlar xom SQL orqali qilinadi (`session.py:45-59`). |
| Backup/Restore | 1/2 | Supabase avtomatik backup qiladi, lekin lokal dump skriptlari mavjud emas. |

- ✅ **Kuchli tomonlar:** Supabase bulut bazasi bilan PgBouncer va TIMESTAMPTZ vaqt mintaqalari to'g'ri sozlangan.
- ⚠️ **Zaif tomonlar:** Alembic migratsiyasi yo'qligi — production bazani yangilashda jiddiy data yo'qotish xavfini tug'diradi.
- 🎯 **10/10 uchun:** Alembic kutubxonasini o'rnating (`alembic init`) va barcha jadvallarni rasmiy versiyalangan migratsiyalarga o'tkazing.

---

### 9. ⚡ Performance Engineer — 6 / 10
| Mezon | Ball | Asos va Dalil (Fayl / Qator) |
|---|---|---|
| Algoritmik murakkablik | 2/2 | Rasch baholash algoritmi Newton-Raphson iteratsiyasi bilan o'ta tez ishlaydi. |
| Asset yuklanishi | 1/2 | Sertifikat shablon rasmi (`certificate_template.jpg`) 433 KB — siqilmagan. |
| Async I/O | 2/2 | Barcha DB va Web so'rovlari 100% async (`asyncpg`, `aiosqlite`, `FastAPI`). |
| Connection pool | 1/2 | SQLAlchemy connection pool max_overflow va pool_size aniq cheklanmagan. |
| Load testing | 0/2 | Bir vaqtda 500+ talaba kirgandagi yuklama sinovlari o'tkazilmagan. |

- ✅ **Kuchli tomonlar:** Butun tizim asinxron (non-blocking I/O) asosida qurilgan, bu ko'p sonli bir vaqtda kiruvchi so'rovlarni oson ko'taradi.
- ⚠️ **Zaif tomonlar:** Rasm aktivlari (sertifikat shablonlari) WebP formatiga o'tkazilmagan; load test natijalari mavjud emas.
- 🎯 **10/10 uchun:** Sertifikat rasmini WebP formatiga o'tkazib hajmini 80 KB ga tushiring; `locust` orqali 1000 user yuklama testini o'tkazing.

---

### 10. 💼 Investor / VC — 6 / 10
| Mezon | Ball | Asos va Dalil (Fayl / Qator) |
|---|---|---|
| Bozor hajmi | 2/2 | O'zbekistonda Milliy Sertifikat topshiruvchilar bozori har yili 150 000+ kishini tashkil etadi. |
| Bus factor | 0/2 | Loyiha faqat 1 ta dasturchiga bog'liq (Azamqulov). |
| IP va kod mustaqilligi | 1/2 | Kod ochiq repository'da turibdi, maxfiy tijorat litsenziyasi belgilanmagan. |
| Unit economics | 2/2 | Server infratuzilmasi xarajati deyarli $0 (bepul tariflar), marja 90%+. |
| Traction/metrikalar | 1/2 | Hali ommaviy marketing kampaniyasi o'tkazilmagan. |

- ✅ **Kuchli tomonlar:** Unit-ekonomika ajoyib: server tannarxi minimal, har bir test topshirish narxidan yuqori sof foyda olish mumkin.
- ⚠️ **Zaif tomonlar:** 1 dasturchi ketib qolsa tizim to'xtashi mumkin (Bus Factor); intellektual mulk himoyalanmagan.
- 🎯 **10/10 uchun:** Kod bazasini ikkinchi dasturchiga topshirish (onboarding) hujjatlarini yarating; loyihaga tijorat litsenziyasini belgilang.

---

### 11. 🎯 Raqobat Tahlilchisi — 7 / 10
| Mezon | Ball | Asos va Dalil (Fayl / Qator) |
|---|---|---|
| Raqobatchilardan ustunlik | 2/2 | OMR javoblar varaqasi va Rasch IRT formulasi bo'yicha baholashda O'zbekistonda yetakchi. |
| Xususiyatlar tengligi | 1/2 | Hozirda faqat bitta fan (Matematika). Raqobatchilar barcha fanlarni qamragan. |
| Narx raqobatbardoshligi | 2/2 | O'qituvchilar o'z testlarini bepul yaratishi mumkinligi tez tarqalishga yordam beradi. |
| Retention (Mijozni ushlab qolish) | 1/2 | Xatolar tahlili va mavzuli video darslar yo'qligi qayta kirishni pasaytiradi. |
| Brend va ishonch | 1/2 | Rasmiy DTM blankiga 100% o'xshash professional sertifikat ishonch uyg'otadi. |

- ✅ **Kuchli tomonlar:** `e-test-bot.uz` va `testmakon.uz` dan farqli ravishda, o'qituvchining o'zi bir necha daqiqada yangi test yaratishi va statistikasini ko'rishi mumkin.
- ⚠️ **Zaif tomonlar:** Boshqa fanlar (Fizika, Kimyo, Ona tili) qo'shilmagan; tahliliy darslar yo'q.
- 🎯 **10/10 uchun:** Fizika va Kimyo fanlari uchun ham standart mock shablonlarini joriy eting; test yakunida tavsiya etilgan video darslar havolasini qo'shing.

---

### 12. 👤 Real Foydalanuvchi — 8 / 10
| Mezon | Ball | Asos va Dalil (Fayl / Qator) |
|---|---|---|
| Usability (Qulaylik) | 2/2 | Katta variant tugmalari `[A][B][C][D]`, savollar xaritasi, F5 session tiklash. |
| Tezlik va javob berish | 2/2 | Tugma bosilganda sahifa sakramaydi, KaTeX tez render bo'ladi. |
| Natijalar shaffofligi | 1/2 | Ball va daraja aniq chiqadi, lekin har bir savolning to'g'ri yechimi ko'rsatilmaydi. |
| Oflayn / yomon internet | 1/2 | Brauzer oflayn bo'lsa ogohlantirish yo'q, PWA xususiyatlari yetishmaydi. |
| Qoniqish (NPS) | 2/2 | Rasmiy QR kodli HD sertifikat olish imkoniyati o'quvchilarda katta qoniqish hosil qiladi. |

- ✅ **Kuchli tomonlar:** Real imtihon muhiti 100% aks ettirilgan; suzuvchi taymer va javoblar varaqasi o'quvchiga ortiqcha noqulaylik tug'dirmaydi.
- ⚠️ **Zaif tomonlar:** O'quvchi xato qilgan savolining to'g'ri yechimini ko'ra olmaydi (faqat to'g'ri/noto'g'ri xulosasi beriladi).
- 🎯 **10/10 uchun:** Test yakunida "Yechimlarni ko'rish" oynasini oching va har bir savolga tushuntirish matnini qo'shing.

---

## 3. Kritik Kamchiliklar Tahlili (Gap Analysis)

| № | Kamchilik nomi | Jiddiylik | Nega muhim (Real oqibat) | Tuzatish vaqti |
|---|---|---|---|---|
| 1 | **Alembic migratsiyasi yo'qligi** | 🔴 Kritik | Schema o'zgarganda jadval buzilishi yoki ma'lumotlar o'chib ketishi xavfi bor. | 8 soat |
| 2 | **CI/CD va Docker yo'qligi** | 🔴 Kritik | Faqat Windows da qo'lda yuradi; server o'chib qolsa avtomatik tiklanmaydi. | 12 soat |
| 3 | **Rate Limiting yo'qligi** | 🟠 Yuqori | Har qanday yovuz niyatli foydalanuvchi script bilan serverni to'xtatib qo'yishi mumkin. | 6 soat |
| 4 | **To'lov integratsiyasi yo'qligi** | 🟠 Yuqori | Pul ishlab olish va tizimni tijoratlashtirish jarayoni butunlay qo'lda qolmoqda. | 16 soat |
| 5 | **Avtomatlashtirilgan E2E testlar yo'qligi** | 🟡 O'rta | Frontendda biror CSS/JS o'zgarsa, o'quvchi test topshirolmay qolishi mumkin. | 10 soat |
| 6 | **Xatolar ustida ishlash (Yechimlar) yo'qligi** | 🟡 O'rta | O'quvchi nega xato qilganini bilmaydi va botga qayta kirish qiziqishi pasayadi. | 18 soat |
| 7 | **Faqat bitta fan (Matematika) borligi** | 🟡 O'rta | Bozorning 70% dan ortiq boshqa fanlar bo'yicha talabgorlari qamrab olinmagan. | 24 soat |
| 8 | **Bus Factor = 1 (1 ta dasturchi)** | 🟡 O'rta | Dasturchi betob bo'lsa yoki loyihani tark etsa, tizim rivojlanishdan to'xtaydi. | — |

---

## 4. Bozor Bahosi va Daromad Potensiali (Valuation)

### A) Ishlab Chiqish Tannarxi (Cost-Based)
Loyihani noldan xuddi shu sifat va funksional darajada qayta yaratish uchun talab etiladigan resurslar:

| Modul | Murakkablik | Sarflanadigan soat | O'zbekiston ($10–18/soat) | Jahon bozori ($35–60/soat) |
|---|---|---|---|---|
| Telegram Bot & State Engine (Aiogram 3) | O'rta | 25 soat | $250 – $450 | $875 – $1,500 |
| Rasch IRT Matematik Baholash Dvigateli | Yuqori | 35 soat | $350 – $630 | $1,225 – $2,100 |
| WebApp OMR Varaqasi (KaTeX, SVG, F5) | Yuqori | 45 soat | $450 – $810 | $1,575 – $2,700 |
| Admin Test Konstruktori & Formula Keyboard | Yuqori | 50 soat | $500 – $900 | $1,750 – $3,000 |
| REST API Backend (FastAPI, Auth HMAC) | O'rta | 30 soat | $300 – $540 | $1,050 – $1,800 |
| PostgreSQL Supabase & Data modeling | O'rta | 20 soat | $200 – $360 | $700 – $1,200 |
| Sertifikat Generatsiyasi (Pillow HD + QR) | O'rta | 15 soat | $150 – $270 | $525 – $900 |
| Unit & Integration Testlar (Pytest 20 ta) | O'rta | 20 soat | $200 – $360 | $700 – $1,200 |
| **JAMI** | | **240 soat** | **$2,400 – $4,320** | **$8,400 – $14,400** |

### B) Real Bozor Solishtirmasi (Market-Comparable)
- O'zbekistonda tayyor Telegram Bot + WebApp buyurtma narxi: **$2,000 – $4,500**.
- Upwork / Fiverr platformalarida shunga o'xshash xalqaro loyiha: **$5,000 – $12,000**.

### C) Tavsiya Etilgan Bozor Narxi (Bitta Aniq Raqam)
Formula: `Tavsiya narx = Min + (Audit Reytingi / 10) * (Max - Min)`

- **O'zbekiston bozori uchun:**
  `$2,000 + (6.0 / 10) * ($4,500 - $2,000) = $3,500` (**41 260 000 UZS**)
  *(1 USD = 11 789.33 UZS kursi bo'yicha)*
- **Jahon bozori uchun:**
  `$5,000 + (6.0 / 10) * ($12,000 - $5,000) = $9,200`.

---

### D) SaaS / Obuna Modeli (O'qituvchilar va Markazlar uchun)

| Tarif rejasi | Oylik narxi (UZS) | Oylik narxi (USD) | Imkoniyatlar |
|---|---|---|---|
| **Boshlang'ich (Start)** | 99 000 so'm | $8.4 | Oyiga 3 tagacha test, 100 tagacha o'quvchi tekshirish |
| **Professional (Pro)** | 249 000 so'm | $21.1 | Cheksiz testlar, 500 tagacha o'quvchi, avtomatik sertifikat, statistika |
| **Enterprise (Markaz)** | 690 000 so'm | $58.5 | O'z logotipi bilan sertifikat, Excel export, cheksiz o'quvchi, SLA |

**Breakeven tahlili:**
- O'rtacha 25 ta Pro obunachi jalb qilinsa: `25 × 249 000 = 6 225 000 so'm/oy` (~$528/oy sof passiv daromad).
- Tizim o'z ishlab chiqarish tannarxini 6–8 oy ichida to'liq qoplaydi.

---

## 5. Raqobatdan Ajralib Turish Uchun Funksiya Takliflari

| № | Funksiya / Imkoniyat | Soat | O'zbekiston narxi | Jahon narxi | Tavsiya narx |
|---|---|---|---|---|---|
| 1 | **Click / Payme Avtomatik To'lov Tizimi** | 18 | $180 – $320 | $630 – $1,080 | **$250 / 2.9 mln UZS** |
| 2 | **Xatolar ustida ishlash & Video/Matnli Yechimlar** | 24 | $240 – $430 | $840 – $1,440 | **$350 / 4.1 mln UZS** |
| 3 | **Mavzuli Diagnostika (Algebra/Geometriya Radar)** | 16 | $160 – $290 | $560 – $960 | **$220 / 2.6 mln UZS** |
| 4 | **Excel / PDF Natijalarini Eksport Qilish** | 12 | $120 – $220 | $420 – $720 | **$160 / 1.9 mln UZS** |
| 5 | **Docker & GitHub Actions CI/CD Avtomatizatsiyasi** | 14 | $140 – $250 | $490 – $840 | **$190 / 2.2 mln UZS** |
| 6 | **Alembic Database Versiyalangan Migratsiyasi** | 10 | $100 – $180 | $350 – $600 | **$140 / 1.6 mln UZS** |

---

## 6. Keyingi 3 Oylik Yo'l Xaritasi (Roadmap)

### 1-Oy: Xavfsizlik va Barqarorlik (Infratuzilma)
1. **Alembic** ulab barcha DB migratsiyalarni versiyalash (Xarajat: $140).
2. **Dockerfile & docker-compose** yaratish va Linux VPS ga deploy qilish (Xarajat: $190).
3. **SlowAPI** orqali rate limiting va input sanitization o'rnatish (Xarajat: $100).

### 2-Oy: Monetizatsiya va Savdo
1. **Payme / Click** to'lov tizimini ulash (Xarajat: $250).
2. O'quvchilar va o'qituvchilar uchun 3 ta obuna tarifini ochish.
3. Excel va PDF eksport funksiyasini joriy etish (Xarajat: $160).

### 3-Oy: Foydalanuvchi Qoniqishi va O'sish
1. Test yakunlangach **Xatolar ustida ishlash va savollar yechimi** modulini chiqarish (Xarajat: $350).
2. O'quv markazlari uchun White-Label (o'z brendi bilan sertifikat chiqarish) rejimini yoqish.
3. Fizika va Kimyo fanlari uchun qo'shimcha shablonlarni kiritish.
