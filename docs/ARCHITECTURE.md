# 🏛️ MSBot Tizim Arxitekturasi (System Architecture)

Ushbu hujjat Milliy Sertifikat Matematika (MSBot) platformasining to'liq texnik me'morchiligi, ma'lumotlar oqimi, kiberxavfsizlik choralari va komponentlar o'rtasidagi munosabatlarni vizual diagrammalar (Mermaid) bilan tushuntiradi.

---

## 1. Yuqori Darajadagi C4 Konteyner Diagrammasi (High-Level Architecture)

```mermaid
C4Context
    title MSBot Tizim Konteksti
    Person(student, "Talaba (O'quvchi)", "Telegram orqali test topshiradi va sertifikat oladi")
    Person(teacher, "O'qituvchi / Admin", "Web orqali test tuzadi va natijalarni tahlil qiladi")

    System_Boundary(msbot_system, "MSBot Platformasi") {
        System(bot_polling, "Telegram Bot (Aiogram 3)", "Foydalanuvchilar bilan muloqot, buyruqlar, PDF va rasm sertifikat yuborish")
        System(web_app, "FastAPI REST API", "Web konstruktor, TMA interfeysi, Rate limiting va xavfsizlik")
        System(scoring_engine, "Rasch IRT Modeli", "Item Response Theory asosida qiyinlik va qobiliyat parametrlarini hisoblash")
    }

    System_Ext(telegram_api, "Telegram Bot API", "Xabarlar va WebApp ma'lumotlari uzatish")
    SystemDb_Ext(supabase_db, "Supabase PostgreSQL", "Foydalanuvchilar, testlar, savollar va urinishlar bazasi")

    Rel(student, telegram_api, "Bot buyruqlaridan foydalanadi")
    Rel(student, web_app, "Test topshirish uchun TMA ochadi (HTTPS)")
    Rel(teacher, web_app, "Admin panel orqali test yaratadi")
    Rel(telegram_api, bot_polling, "Updates (Polling / Webhook)")
    Rel(web_app, scoring_engine, "Javoblarni baholashga yuboradi")
    Rel(web_app, supabase_db, "SQLAlchemy Async ORM orqali so'rovlar")
    Rel(bot_polling, supabase_db, "Foydalanuvchi va test holatini tekshiradi")
    Rel(web_app, bot_polling, "Sertifikat va xabarnomalarni yuborishga uzatadi")
```

---

## 2. Ma'lumotlar Bazasi Sxemasi (Entity-Relationship Diagram)

```mermaid
erDiagram
    USERS ||--o{ TESTS : "yaratadi (creator)"
    USERS ||--o{ ATTEMPTS : "topshiradi (student)"
    TESTS ||--o{ QUESTIONS : "o'z ichiga oladi (45 ta)"
    TESTS ||--o{ QUESTION_GROUPS : "guruhlangan kontekst"
    QUESTION_GROUPS ||--o{ QUESTIONS : "biriktiriladi"
    ATTEMPTS ||--o{ ATTEMPT_ANSWERS : "javoblar ro'yxati"
    QUESTIONS ||--o{ ATTEMPT_ANSWERS : "savolga javob"

    USERS {
        int id PK
        bigint telegram_id UK
        string full_name
        string username
        string phone_number
        string role
        timestamp registered_at
    }

    TESTS {
        int id PK
        int creator_user_id FK
        string code UK
        string title
        int time_limit_min
        boolean is_active
        boolean hide_answers
        int question_count
    }

    QUESTION_GROUPS {
        int id PK
        int test_id FK
        text shared_context_text
        string shared_image_url
        json shared_options
    }

    QUESTIONS {
        int id PK
        int test_id FK
        int group_id FK
        int order_no
        string type
        string section
        float difficulty_b
        text text
        string image_url
        json options
        string correct_answer
    }

    ATTEMPTS {
        int id PK
        int user_id FK
        int test_id FK
        timestamp start_time
        timestamp finished_at
        float raw_score
        float scaled_score
        float theta
        float sem
        string grade
        boolean is_finished
    }

    ATTEMPT_ANSWERS {
        int id PK
        int attempt_id FK
        int question_id FK
        string user_answer
        boolean is_correct
        string sub_part_label
    }
```

---

## 3. Test Topshirish va Baholash Oqimi (Sequence Flow)

```mermaid
sequenceDiagram
    autonumber
    actor Talaba as O'quvchi (TMA)
    participant API as FastAPI Web App
    participant RateLimit as RateLimiter Middleware
    participant Security as Security Service (HMAC)
    participant AttemptSvc as Attempt Service
    participant Rasch as Rasch IRT Engine
    participant CertSvc as Certificate Generator
    participant DB as PostgreSQL (Supabase)
    participant Bot as Aiogram Bot

    Talaba->>RateLimit: GET /api/test/STANDART
    RateLimit->>API: Ruxsat berildi
    API->>DB: Savollarni yuklash
    DB-->>API: 45 ta savol (LaTeX + SVG/PNG)
    API-->>Talaba: JSON savollar ro'yxati

    Note over Talaba: O'quvchi testni ishlaydi...

    Talaba->>API: POST /api/test/session (tg_id, test_id)
    API->>Security: HMAC-SHA256 Sessiya tokeni yaratish
    Security-->>API: session_token
    API-->>Talaba: session_token (5 soat amal qiladi)

    Talaba->>RateLimit: POST /api/test/submit (token, javoblar)
    RateLimit->>API: Ruxsat berildi
    API->>Security: Sessiya tokenini tekshirish
    Security-->>API: Token tasdiqlandi (anti-spoofing OK)

    API->>AttemptSvc: process_test_submission()
    AttemptSvc->>DB: Urinish va javoblarni saqlash
    AttemptSvc->>Rasch: evaluate_attempt(savollar, javoblar)
    Rasch-->>AttemptSvc: {theta, score: 72.5, grade: 'A'}
    AttemptSvc->>CertSvc: generate_certificate_image()
    CertSvc-->>AttemptSvc: cert_123.jpg (Ultra-HD blanka)
    AttemptSvc->>Bot: send_photo(talaba_id, cert) + send_message(ustoz_id)
    AttemptSvc-->>API: To'liq natijalar
    API-->>Talaba: 200 OK {final_score, grade, cert_url}
```

---

## 4. Xavfsizlik Modeli (Security Architecture)

1. **Kirish Nazorati (Authentication & RBAC):**
   * Admin paneli faqat Telegram tomonidan imzolangan `X-Telegram-Init-Data` sarlavhasi bilan ochiladi.
   * `is_admin()` tekshiruvi orqali Super Admin va Admin rollari ajratiladi.
2. **Anti-Spoofing (Talaba Sessiyasi):**
   * Har bir test topshirish sessiyasi uchun unikal HMAC tokeni ishlatiladi, birov boshqa birovning `telegram_id` sini qo'lda yubora olmaydi.
3. **DDoS va Spam Himoyasi (Sliding Window Rate Limiter):**
   * Barcha API yo'llari IP va foydalanuvchi bo'yicha 60 soniyada 120 ta so'rov bilan cheklangan.
4. **Xavfsiz Muhit (Docker Non-Root):**
   * Docker konteyneri root huquqlarisiz (`appuser`, UID 1000) ishga tushadi.
