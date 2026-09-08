# 🛠️ TEXNIK KO'NIKMA VA OPERATSION QO'LLANMA
## Milliy Sertifikat Matematika (MSBot) Tizimi uchun Keng Qamrovli Yo'riqnoma

Ushbu ko'nikma hujjati loyihani boshqarish, xavfsizlikni ta'minlash, DevOps amaliyotlari va backend xizmatlarini kengaytirish bo'yicha to'liq texnik bilimlarni o'z ichiga oladi.

---

## 1. 🐳 DevOps va Konteynerizatsiya Ko'nikmasi

### 1.1. Dockerfile Arxitekturasi
Loyihamiz `python:3.13-slim` bazasida multi-stage prinsipi va xavfsiz `appuser` (non-root) profilida ishlaydi.
* **Kesh optimizatsiyasi:** Avval `requirements.txt` ko'chiriladi va kutubxonalar o'rnatiladi, shunda kod o'zgarganda dependency'lar qayta yuklanmaydi.
* **Salomatlik tekshiruvi (Healthcheck):** Har 30 soniyada `curl -f http://localhost:8000/healthz` orqali konteyner monitoring qilinadi.

### 1.2. Docker Compose bilan Boshqarish
```bash
# 1. Konteynerni build qilish va fonda ishga tushirish
docker compose up -d --build

# 2. Loglarni jonli kuzatish
docker compose logs -f app

# 3. Konteynerni to'xtatish
docker compose down
```

### 1.3. GitHub Actions CI/CD Pipeline
`.github/workflows/ci.yml` orqali har bir `git push` va Pull Request'da:
1. Python muhiti ko'tariladi.
2. `requirements.txt` o'rnatiladi.
3. Sintaktik va xatoliklar tekshiruvi (`flake8` orqali kritik syntax errorlar) bajariladi.
4. Barcha 20+ ta Pytest birlik va integratsion testlari ishga tushiriladi.
5. Agar birorta test yiqilsa, PR merge qilinishiga ruxsat berilmaydi.

---

## 2. 🔐 Kiberxavfsizlik va Anti-Spoofing Ko'nikmasi

### 2.1. In-Memory Sliding-Window Rate Limiting
API endpointlarini DDoS, scraping va brute-force hujumlaridan himoya qilish uchun `FastAPI` middleware darajasida so'rovlar hisoblab boriladi:
* **Mantiq:** Har bir mijoz IP'si (yoki `X-Forwarded-For`) uchun vaqt belgilari (timestamps) ro'yxati saqlanadi. 60 soniyadan eski vaqtlar tozalanadi.
* **Limit:** Bir daqiqada maksimum 60 ta so'rov (Admin va o'quvchi oddiy foydalanishi uchun 1 soniyada 1 so'rov ideal me'yor).
* **Limit oshganda:** Server yuklanmasdan `429 Too Many Requests` va `Retry-After: 60` sarlavhasini qaytaradi.

### 2.2. HMAC-SHA256 Sessiya Tokenlari (Anti-Spoofing)
Oldingi zaiflik: Har qanday shaxs `/api/test/submit` ga istalgan `telegram_id` ni yuborishi mumkin edi.
* **Yangi yechim:** Test boshlanayotganda talaba uchun `HMAC_SHA256(bot_token, f"{test_id}:{telegram_id}:{timestamp}")` imzosi yaratiladi.
* Submit vaqtida talabaning so'rovi imzoga mosligi tekshiriladi, bu esa boshqa birovning nomidan soxta ball topshirishni 100% bartaraf etadi.

---

## 3. 🏛️ Backend Arxitekturasi va Service Qatlami

Tizim uch qatlamli (Layered Architecture) me'morchilikka asoslangan:
```
[ Client: TMA / Web / Telegram ]
             │
             ▼
[ 1. Transport Qatlami: FastAPI Routes & Aiogram Handlers ]
             │  (Faqat HTTP/Telegram I/O, DTO validatsiya)
             ▼
[ 2. Biznes Xizmat Qatlami: Service Layer ]
     ├── AuthService (InitData verify, Token generation)
     ├── AttemptService (Rasch grading, Answer matching)
     ├── TestService (Test CRUD, Question grouping)
     └── ReportService & CertificateService (PDF/Image)
             │
             ▼
[ 3. Ma'lumotlar Qatlami: SQLAlchemy Async Engine & Models ]
             │
             ▼
[ Supabase PostgreSQL 6543 Pooler ]
```

---

## 4. 🚀 Yangi Xususiyatlar Qo'shish Qoidalari
1. Yangi API qo'shayotganda doim Pydantic model (`BaseModel`) orqali kiruvchi maydonlarni validatsiya qiling.
2. Ma'lumotlar bazasiga to'g'ridan-to'g'ri `api.py` ichida so'rov yozmang — barcha mantiqni `bot/services/` ichidagi mos servisga joylashtiring.
3. Yangi funksiya uchun albatta `tests/` papkasiga Pytest testini yozing.
