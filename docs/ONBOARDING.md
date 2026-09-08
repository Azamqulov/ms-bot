# 🚀 MSBot Dasturchilar uchun Onboarding Qo'llanmasi (Junior & Middle Runbook)

MSBot — Milliy Sertifikat (Matematika) bo'yicha test topshirish, Rasch (IRT) modeli yordamida ilmiy baholash va Telegram orqali rasmiy sertifikat taqdim etish platformasi.
Ushbu qo'llanma loyihaga yangi qo'shilgan dasturchi uchun 15 daqiqada muhitni to'liq sozlash va birinchi commitni amalga oshirish imkonini beradi.

---

## 1. ⚙️ Kerakli Texnologiyalar (Prerequisites)
* **Python:** 3.11 yoki 3.13+
* **Git:** 2.30+
* **Docker & Docker Compose:** (Ixtiyoriy, konteynerda ishlatish uchun)
* **Telegram Hisob:** BotFather orqali yaratilgan bot tokeni

---

## 2. ⚡ 3 Qadamda Ishga Tushirish (Quickstart)

### 1-qadam: Repozitoriyni yuklab olish va virtual muhit yaratish
```bash
git clone https://github.com/Azamqulov/ms-bot.git
cd ms-bot

# Virtual muhit yaratish
python -m venv .venv

# Windows Powershell:
.\.venv\Scripts\Activate.ps1
# Linux/MacOS:
source .venv/bin/activate

# Kutubxonalarni o'rnatish
pip install -r requirements.txt
```

### 2-qadam: Muhit o'zgaruvchilarini sozlash (`.env`)
Loyiha ildizida `.env` faylini yarating:
```env
BOT_TOKEN=8811201137:AAGxxxxxxxxxxxxxxxxxxxxxxxxxxx
SUPER_ADMIN_ID=1685356708
DATABASE_URL=postgresql+asyncpg://postgres.xxxx:pass@aws-0-eu-central-1.pooler.supabase.com:6543/postgres
WEB_APP_URL=http://localhost:8000
```
> 💡 *Eslatma: Agar lokal test qilayotgan bo'lsangiz, `DATABASE_URL=sqlite+aiosqlite:///./data/local.db` qilib ishlatishingiz ham mumkin.*

### 3-qadam: Ishga tushirish
```bash
# Server va botni birgalikda ishga tushirish:
python start.py

# Yoki to'g'ridan-to'g'ri modul sifatida:
python -m bot.main
```
Brauzerda tekshiring:
* Web ilova: `http://localhost:8000/`
* Admin panel: `http://localhost:8000/admin`
* Salomatlik tekshiruvi: `http://localhost:8000/healthz`

---

## 3. 🐳 Docker orqali ishga tushirish
Hech qanday Python kutubxonalarini lokal o'rnatmasdan, konteynerda ishlatish uchun:
```bash
docker compose up -d --build
```
Loglarni kuzatish:
```bash
docker compose logs -f app
```

---

## 4. 🧪 Avtomatik Testlarni Yurgizish
Har qanday kod o'zgarishidan so'ng barcha testlar yashil bo'lishi shart:
```bash
pytest tests/ -v
```
Hozirda tizimda **24 ta integratsion va birlik testlar** mavjud (Rasch baholash, LaTeX formulalar, Web API, Kiberxavfsizlik va DevOps).

---

## 5. 📂 Papkalar Tuzilmasi (Folder Structure)

```
MSBot/
├── bot/                     # Asosiy Python backend paketi
│   ├── config.py            # Pydantic Settings & Env o'qish
│   ├── main.py              # Bot va FastAPI ulanish nuqtasi
│   ├── core/                # Yadrolar: Rasch modeli, Rate limiter, Xavfsizlik
│   ├── database/            # SQLAlchemy modellar, sessiya va seed
│   ├── handlers/            # Aiogram Telegram buyruqlari
│   ├── services/            # Biznes servislar: Attempt, Admin, Report, Certificate
│   └── web_app/             # FastAPI marshrutlari va Telegram WebApp auth
├── web/                     # Frontend aktivlari
│   ├── css/                 # student.css, admin.css
│   ├── js/                  # config.js, student.js, admin.js
│   ├── index.html           # Talaba test topshirish interfeysi
│   └── admin.html           # Admin konstruktori
├── tests/                   # 24 ta Pytest testlari
├── docs/                    # Arxitektura, auditlar va TZ hujjatlari
├── Dockerfile               # Production multi-stage Docker konteyneri
├── docker-compose.yml       # Konteynerlarni boshqarish
└── .github/workflows/ci.yml # Avtomatik CI/CD pipeline
```

---

## 6. ⚠️ Ko'p Uchraydigan Muammolar (Gotchas & FAQ)

1. **LaTeX Formulalar buzilishi:**
   * Savol matnida `\` belgisini yozganda doim `\\` yoki Python raw-string (`r"..."`) ishlating. Masalan: `$x = \\frac{a}{b}$`.
2. **Supabase Pooler Port 6543:**
   * Supabase'da doim Transaction Pooler porti `6543` dan foydalaning (5432 to'g'ridan-to'g'ri ulanish IPv6 talab qilishi mumkin).
3. **Admin ruxsati berilmasligi:**
   * Admin bo'lish uchun Telegram ID `.env` faylidagi `SUPER_ADMIN_ID` ga yozilishi yoki botda `/add_admin` orqali qo'shilishi kerak.
