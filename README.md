# 🎓 Milliy Sertifikat — Matematika Telegram Bot

Matematikadan O'zbekiston Milliy Sertifikat imtihoniga tayyorlanayotgan talabgorlar uchun mock (sinov) testlarni topshirish va natijalarni **RASH modeli (IRT — Item Response Theory)** asosida aniq baholaydigan zamonaviy Telegram bot.

Analog: `@MilliySertifikatMatematika_bot`

---

## 🌟 Asosiy imkoniyatlar

1. **Haqiqiy Milliy Sertifikat imtihon formati:**
   - **45 ta savol**, umumiy **150 daqiqa** (2 soat 30 daqiqa) vaqt limiti.
   - **1–32-savollar (Y-1 turi):** 4 variantli yopiq test (A, B, C, D) — bir marta bosish orqali javob berish.
   - **33–35-savollar (Guruhlangan):** Bitta umumiy amaliy/fazoviy masala va umumiy 6 ta variant (A–F) to'plami.
   - **36–45-savollar (O turi):** Ochiq savollar (matn yoki son kiritish), har biri `a)` va `b)` mustaqil bandlariga ega.
2. **RASH (IRT — Item Response Theory) ilmiy baholash tizimi:**
   - Har bir savol va topshiriq bandi o'zining qiyinlik parametri ($b \in [-3.0, +3.0]$)ga ega.
   - Talabgorning matematik qobiliyati ($\theta$ — theta) **Maximum Likelihood Estimation (MLE)** / Newton-Raphson iteratsiyasi yordamida hisoblanadi.
   - Ekstremal holatlar (barchasi xato yoki barchasi to'g'ri) uchun Bayes tuzatishi qo'llaniladi.
   - Natija rasmiy **0–75 ball** shkalasiga o'tkazilib, rasmiy darajalar belgilanadi:
     - 🏆 **A+**: 70.0 — 75.0 ball (100% maksimal imtiyoz)
     - 🥇 **A**: 65.0 — 69.9 ball
     - 🥈 **B+**: 60.0 — 64.9 ball
     - 🥉 **B**: 55.0 — 59.9 ball
     - 🎖 **C+**: 50.0 — 54.9 ball
     - 🎗 **C**: 46.0 — 49.9 ball (Minimal o'tish)
     - ❌ **Sertifikat berilmaydi**: < 46.0 ball
3. **Ergonomik Telegram UX va Navigatsiya:**
   - 45 ta savol xaritasi (Grid 1–45) orqali istalgan savolga bir zumda o'tish va javobni yangilash.
   - Ochiq savollar (36–45) uchun aqlli parser: matndan raqam, manfiy son, oddiy kasr (`1/2`) va o'nli kasr (`3,5` yoki `3.5`) turlarini tushunadi.
   - Natijalar tarixi (`/natijalarim`) va rivojlanish statistikasi.
4. **Mustahkam Texnologik Stack:**
   - **Python 3.13 + aiogram 3.x** (asinxron, yuqori yuklamalarga chidamli).
   - **SQLAlchemy 2.0 (async)**: Ham Supabase (PostgreSQL), ham lokal sinovlar uchun SQLite qo'llab-quvvatlaydi.

---

## 🚀 O'rnatish va ishga tushirish

### 1. Talablar
- Python 3.11+ (Python 3.13 tavsiya etiladi)
- Telegram Bot Token ([@BotFather](https://t.me/BotFather) dan olinadi)

### 2. Virtual muhit va kutubxonalar
```bash
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Muhit o'zgaruvchilari (.env)
`.env` faylini oching va bot tokeningizni kiriting:
```env
BOT_TOKEN=123456789:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxx
DATABASE_URL=sqlite+aiosqlite:///./data/msbot.db
DEFAULT_TEST_TIME_LIMIT_MIN=150
```

> **Supabase / PostgreSQL ulash:**
> Agar Supabase bazasiga ulamoqchi bo'lsangiz:
> `DATABASE_URL=postgresql+asyncpg://postgres:parol@db.your-id.supabase.co:5432/postgres`

### 4. Testlarni ishga tushirish
```bash
pytest -v
```

### 5. Botni ishga tushirish
```bash
python -m bot.main
```

---

## 📁 Loyiha tuzilishi

```
MSBot/
├── bot/
│   ├── core/
│   │   ├── rasch.py          # 1PL Rasch IRT baholash dvigateli (MLE, Theta, 0-75 shkala)
│   │   └── validator.py      # Ochiq javoblar normalizatori va tekshirgichi
│   ├── database/
│   │   ├── models.py         # SQLAlchemy modellari (User, Test, Question, Attempt...)
│   │   ├── session.py        # Asinxron DB sessiya boshqaruvi
│   │   └── seed_data.py      # 45 ta namunaviy savollar bazasi (Y-1, Guruhlangan, Ochiq)
│   ├── handlers/
│   │   ├── common.py         # /start, /help, RASH modeli tushuntirishi
│   │   ├── test_runner.py    # Test oqimi, inline klaviaturalar, navigatsiya, yakunlash
│   │   ├── open_question.py  # 36-45 ochiq savollarga javob qabul qilish
│   │   └── history.py        # /natijalarim va tarix ko'rsatish
│   ├── keyboards/
│   │   ├── inline.py         # Variantlar (A-D, A-F), navigatsiya, grid xarita
│   │   └── reply.py          # Asosiy menyu
│   ├── services/
│   │   ├── test_service.py   # Asosiy biznes mantiq va urinishlarni boshqarish
│   │   └── report_service.py # Chiroyli natija hisoboti va statistika
│   ├── states/
│   │   └── test_state.py     # aiogram FSM holatlari
│   ├── config.py             # Pydantic Settings
│   └── main.py               # Botni ishga tushiruvchi kirish nuqtasi
├── tests/
│   ├── test_rasch.py         # Rasch matematik modeli testlari
│   ├── test_validator.py     # Javoblarni tekshirish testlari
│   ├── test_database.py      # Baza va savollar yuklanishi testi
│   └── test_full_flow.py     # End-to-end to'liq test topshirish testi
├── requirements.txt
├── .env.example
├── .gitignore
├── GOLDEN RULES.md
└── README.md
```
