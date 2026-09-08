# TEXNIK TOPSHIRIQ (TZ)
## Loyiha: Milliy Sertifikat Matematika (MSBot)
### Modul: Backend Arxitekturasi, Kiberxavfsizlik, DevOps CI/CD va Tizim Hujjatlashtirish (Audit: 1, 3, 4, 7)

---

## 1. Maqsad va qamrov (Purpose & Scope)
Ushbu texnik topshiriq audit natijalarida eng zaif va muhim deb topilgan to'rtta yo'nalishni (Audit 1: Backend Architecture, Audit 3: Security & Auth, Audit 4: DevOps & CI/CD, Audit 7: Junior Onboarding & Architecture) jahon va korporativ standartlariga ko'tarishga qaratilgan.
Tizim O'zbekiston Milliy sertifikatiga tayyorlanayotgan 100,000+ abituriyent va repetitorlarga xizmat ko'rsatuvchi Telegram Mini App (TMA) va REST API bo'lib, uning uzluksizligi, hujumlardan himoyasi (anti-DDoS, anti-spoofing), avtomatlashtirilgan konteynerizatsiyasi va yangi dasturchilarning 15 daqiqada loyihaga kirishib keta olishi (onboarding) kafolatlanadi.

---

## 2. Foydalanuvchi rollari (User Roles)

| Rol nomi | Ko'ra oladi / Bajara oladi | Cheklovlar / Bajarolmaydi |
|---|---|---|
| **Super Admin** | Barcha testlar, statistikalar, admin tayinlash/o'chirish, tizim salomatligi (`/healthz`), rasm yuklash, test kalitlarini ko'rish. | Faqat o'z telegram_id va imzolangan HMAC initData bilan kira oladi. |
| **Admin (O'qituvchi)** | O'z testlarini yaratish (Y-1, Guruhlangan, Ochiq), tahrirlash, o'z test qatnashchilari natijalarini ko'rish. | Boshqa adminlarning testlarini o'chira/tahrirlay olmaydi; Super admin huquqlarini bera olmaydi. |
| **O'quvchi (Student)** | Test topshirish, Telegram orqali natija va sertifikat olish, profilingni yangilash. | Boshqa o'quvchining nomidan soxta javob yubora olmaydi (HMAC imzolangan sessiya tokeni talab etiladi); Admin panelga kira olmaydi. |
| **DevOps / CI Runner** | Docker orqali build qilish, GitHub Actions'da linting va testlarni avtomatik yurgizish, `/healthz` monitoring qilish. | Ishlab chiqarish ma'lumotlar bazasini to'g'ridan-to'g'ri o'zgartirmaydi; `.env` sirlari himoyalangan. |

---

## 3. Ma'lumotlar bazasi sxemasi (DB Schema)
Mavjud Supabase PostgreSQL sxemasi to'liq saqlangan holda, sessiya va so'rovlar xavfsizligini ta'minlash uchun tranzaksiya yaxlitligi va unumdor indekslar mustahkamlanadi:

```sql
-- Foydalanuvchilar jadvali
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    username VARCHAR(255),
    phone_number VARCHAR(64),
    role VARCHAR(32) NOT NULL DEFAULT 'user', -- 'user', 'admin', 'super_admin'
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Testlar jadvali
CREATE TABLE IF NOT EXISTS tests (
    id SERIAL PRIMARY KEY,
    creator_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    code VARCHAR(64) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    time_limit_min INTEGER NOT NULL DEFAULT 150,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    hide_answers BOOLEAN NOT NULL DEFAULT FALSE,
    question_count INTEGER NOT NULL DEFAULT 45,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_tests_code ON tests(code);
CREATE INDEX IF NOT EXISTS idx_tests_creator ON tests(creator_user_id);

-- Test urinishlari (Attempts)
CREATE TABLE IF NOT EXISTS attempts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    test_id INTEGER REFERENCES tests(id) ON DELETE CASCADE,
    start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    end_time TIMESTAMP WITH TIME ZONE,
    is_finished BOOLEAN NOT NULL DEFAULT FALSE,
    raw_score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    scaled_score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    theta DOUBLE PRECISION,
    sem DOUBLE PRECISION,
    grade VARCHAR(16)
);
CREATE INDEX IF NOT EXISTS idx_attempts_user_test ON attempts(user_id, test_id);
```

---

## 4. API Jadvali (API Table)

| Method | Path | Auth Required? | Request Body | Response (JSON) | Error Cases |
|---|---|:---:|---|---|---|
| **GET** | `/healthz` | Yo'q | Bo'sh | `{"status":"ok","database":"connected","timestamp":172578...}` | `503 Service Unavailable` (DB uzilganda) |
| **GET** | `/api/test/{code}` | Yo'q (Public) | Bo'sh | `{"id":1,"code":"STANDART","questions":[...]}` | `404 Not Found`, `429 Too Many Requests` |
| **POST** | `/api/test/start-session` | Telegram initData | `{"test_id": 1, "telegram_id": 123}` | `{"session_token": "hmac_jwt...", "expires_at": ...}` | `401 Unauthorized`, `404 Not Found` |
| **POST** | `/api/test/submit` | Sessiya Tokeni / Header | `{"test_id":1,"telegram_id":123,"answers":[...]}` | `{"raw_score":42,"final_score":72.5,"grade":"A",...}` | `400 Bad Request`, `401 Unauthorized`, `429 Rate Limit` |
| **POST** | `/api/admin/create-test` | `X-Telegram-Init-Data` (Admin) | `CreateTestPayload` (45 ta savol) | `{"success":true,"code":"MATH-1","question_count":45}` | `400 Validation Error`, `401 Unauthorized`, `403 Forbidden` |
| **POST** | `/api/admin/upload-image`| `X-Telegram-Init-Data` (Admin) | `multipart/form-data (file)` | `{"url":"/uploads/uuid.png","filename":"..."}` | `400 Invalid File`, `413 File Too Large`, `401 Unauthorized` |
| **GET** | `/api/admin/tests/{tg_id}`| `X-Telegram-Init-Data` (Admin) | Bo'sh | `[{"id":1,"code":"...","title":"..."}]` | `401 Unauthorized`, `403 Forbidden` |

---

## 5. Ekranlar va Komponentlar Ro'yxati (Screens & Components)
1. **O'quvchi Test Interfeysi (`web/index.html`):** Formula va chizmalar bilan 45 ta savol, real-time javob varaqasi, orqaga hisoblovchi taymer, yakunlash modali.
2. **Admin Konstruktor (`web/admin.html`):** 3 blokli (Y-1, Guruhlangan, Ochiq) savol generatori, formula klaviaturasi, rasm yuklash paneli, test faolligini boshqarish.
3. **Sertifikat va Natijalar Ko'rinishi:** Rasch modeli bo'yicha hisoblangan ball, daraja (A+, A, B+, B, C+, C), ballar taqsimoti va grafik sertifikat generatsiyasi.
4. **DevOps Monitoring Dashboard:** `/healthz` orqali server holati va Cloudflare tunnel ping statusi.

---

## 6. Qabul Qilish Mezonlari (Acceptance Criteria)
- [x] **AC-1 (DevOps):** `Dockerfile` multi-stage orqali Python 3.13-slim bazasida xavfsiz (non-root) yaratilishi va `docker-compose up --build` orqali barcha servislar xatosiz ko'tarilishi.
- [x] **AC-2 (DevOps CI/CD):** `.github/workflows/ci.yml` fayli mavjud bo'lib, har bir commit va PR'da syntax-check, flake8 va pytest testlarini avtomatik yurgizishi.
- [x] **AC-3 (Kiberxavfsizlik):** FastAPI middleware darajasida In-Memory Sliding-Window Rate Limiter (IP va Telegram ID bo'yicha 60 soniyada 60 ta so'rov chegarasi) ishlab turishi, limit oshganda `429 Too Many Requests` qaytarishi.
- [x] **AC-4 (Anti-Spoofing):** Talaba sessiyasi tokeni (HMAC imzolangan) orqali boshqa foydalanuvchining ID sini soxtalashtirib javob yuborishning oldi olinishi.
- [x] **AC-5 (Arxitektura & Services):** `bot/web_app/api.py` dagi murakkab DB so'rovlari va mantiqiy hisob-kitoblar alohida xizmat qatlamiga (`AttemptService`, `SecurityService`) chiqarilishi.
- [x] **AC-6 (Hujjatlashtirish):** Yangi kelgan dasturchi 15 daqiqada loyihani ishga tushirishi uchun `docs/ARCHITECTURE.md` (Mermaid diagrammalari bilan) va `docs/ONBOARDING.md` qo'llanmalari to'liq yozilishi.
- [x] **AC-7 (Testlar):** Mavjud 20 ta test va qo'shilgan yangi xavfsizlik/healthz testlari (100%) muvaffaqiyatli o'tishi.

---

## 7. Chetga Chiqish Holatlari (Edge Cases to Handle)
1. **DDoS va API Spam:** Bir vaqtning o'zida bir IP dan sekundiga 20+ so'rov kelsa — Rate Limiter 429 xatosi beradi va bazani yuklamadan asraydi.
2. **Soxta initData yoki Muddati o'tgan Token:** 24 soatdan eski Telegram initData yoki o'zgartirilgan hash darhol `401 Unauthorized` bilan qaytariladi.
3. **Ma'lumotlar bazasi uzilishi:** Agar Supabase vaqtincha javob bermasa — `/healthz` `503 Service Unavailable` qaytaradi, bot esa foydalanuvchiga tushunarli o'zbekcha "Baza bilan aloqa vaqtincha uzildi, qayta urining" xabarini beradi.
4. **Katta hajmdagi rasmlar:** 10MB dan katta fayllar yoki buzilgan grafik fayllar yuklanganda server qulamasdan `400 Bad Request` qaytaradi.

---

## 8. Taxminlar va Ochiq Savollar (Assumptions)
- `[ASSUMPTION]` Bot va Web App Supabase PostgreSQL connection pooler (port 6543) orqali ishlaydi.
- `[ASSUMPTION]` Rate limiting Redis serveri talab qilinmasdan in-memory sliding window orqali yengil va tezkor ishlaydi, kelgusida Redis'ga oson ulanadi.
- `[ASSUMPTION]` GitHub Actions workflows bepul public repository limitlari doirasida `ubuntu-latest` da bajariladi.
