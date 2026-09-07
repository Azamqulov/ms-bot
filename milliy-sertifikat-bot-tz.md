# TEXNIK TOPSHIRIQ (TZ)
## "Milliy Sertifikat — Matematika" Telegram Bot

**Loyiha turi:** Yangi mustaqil loyiha
**Sana:** 2026-yil sentyabr
**Analog:** @MilliySertifikatMatematika_bot

---

## 1. Loyihaning maqsadi

Matematikadan Milliy Sertifikat imtihoniga tayyorlanayotgan talabgorlar uchun mock (sinov) testlarni onlayn topshirish va natijalarni **RASH modeli (IRT — Item Response Theory)** asosida baholaydigan Telegram bot yaratish.

Bot foydalanuvchiga:
- Real imtihon formatiga yaqin mock test taqdim etadi
- Har bir savolga javob yig'adi
- Rasmiy metodikaga yaqin tarzda ball va daraja (C, C+, B, B+, A, A+) hisoblab beradi
- Natijalar tarixini saqlaydi

---

## 2. Auditoriya va til

- Auditoriya: Milliy Sertifikatga tayyorlanayotgan o'zbek talabgorlari
- Bot interfeysi: **o'zbek tilida** (lotin, kerak bo'lsa keyinchalik rus/kirill qo'shilishi mumkin)
- Formula va matematik belgilar to'g'ri render bo'lishi kerak (LaTeX/rasm formatida savollar bo'lishi mumkin)

---

## 3. Texnik stack

| Qism | Tanlov | Izoh |
|---|---|---|
| Bot backend | **Python + aiogram 3.x** | Test/ta'lim botlarida ishonchli, async, keng community |
| Baza | **Supabase (PostgreSQL)** | Standart stack, RLS bilan xavfsiz |
| Hosting | VPS yoki Supabase Edge Function + webhook, yoki polling rejimida oddiy VPS/Railway | MVP bosqichida polling + arzon VPS tavsiya etiladi |
| Rasm/formula saqlash | Supabase Storage | Savol rasmlari (agar formulalar rasm sifatida bo'lsa) |
| Admin panel | Alohida veb-panel (Vue 3 + Tailwind) — Faza 3 da | MVP da admin ishlari to'g'ridan-to'g'ri DB orqali yoki oddiy Telegram admin-komandalar bilan |

---

## 4. RASH (IRT) modeli — tavsiya etilgan yondashuv

Ikki bosqichli strategiya tavsiya etiladi:

**Faza 1 (MVP) — "Fixed-parameter Rasch"**
Har bir savolga oldindan **qiyinlik darajasi (b-parametr)** admin tomonidan kiritiladi (masalan rasmiy DTM statistikasi yoki ekspert bahosi asosida, -3 dan +3 gacha shkala). Foydalanuvchi qobiliyati (θ — theta) quyidagi formulaga asosan hisoblanadi:

```
P(to'g'ri javob) = e^(θ - b) / (1 + e^(θ - b))
```

Foydalanuvchining θ qiymati **Maximum Likelihood Estimation (MLE)** yoki soddalashtirilgan iterativ usul bilan hisoblanadi (barcha savollar javoblari asosida), keyin θ → xom ball → 0-75 ball shkalasiga va rasmiy darajalarga (C=46-49.9, C+=50-54.9, B=55-59.9, B+=60-64.9, A=65-69.9, A+=70+) o'giriladi.

**Faza 2 (keyingi bosqich) — "Dinamik kalibrlash"**
Yetarlicha foydalanuvchi javoblari to'plangach (masalan 200+ urinish/savol), savol qiyinlik darajalari haqiqiy javoblar statistikasidan avtomatik qayta hisoblanadi (item calibration), bot vaqt o'tishi bilan aniqroq bo'lib boradi.

*Tavsiya: MVP uchun Faza 1 bilan boshlash — tezroq ishga tushirish, keyin Faza 2 qo'shish.*

---

## 5. Funksional talablar — fazalarga bo'lingan

### FAZA 1 — MVP (asosiy oqim)

**Real mock test namunasi asosida aniqlangan format** (super_matematika kanali, 4-mock test):

- **45 ta savol, 150 daqiqa** (2 soat 30 daqiqa) — umumiy vaqt chegarasi butun test uchun
- **1-32-savollar — Y-1 turi**: 4 variantli (A-D) yopiq savol, tugmalar orqali javob
- **33-35-savollar — guruhlangan savol (umumiy shart + umumiy javob to'plami)**: bitta umumiy matn/rasm (masalan geometrik jism tavsifi) asosida 3 ta bog'liq subsavol beriladi, va barchasi uchun umumiy 6 ta javob varianti (A-F) taqdim etiladi — har bir subsavol shu 6 tadan birini tanlaydi
- **36-45-savollar — O turi (ochiq savol)**: ko'pchiligi ikki qismli (a, b), javob matn/son sifatida kiritiladi (masalan "Javob: ___")

Demak savol turlari 3 xil UI oqimini talab qiladi:
1. Oddiy tugmali (Y-1)
2. Guruhlangan — bitta kontekst + bir nechta subsavol, umumiy variant to'plami (33-35 kabi)
3. Ochiq matn/son kiritish, ko'pincha ikki qismli (36-45 kabi)

**Bot oqimi:**
1. `/start` — foydalanuvchini ro'yxatdan o'tkazish (Telegram ID, ism)
2. Mock test tanlash (agar bir nechta variant bo'lsa) yoki bitta standart test bilan boshlash
3. Umumiy 150 daqiqalik taymer boshlanadi (test boshida ogohlantirish bilan)
4. Savollar yuqoridagi 3 turga mos UI bilan ketma-ket yuboriladi (rasm/formula bo'lsa — rasm sifatida yoki LaTeX render qilingan holda)
5. Test tugagach (vaqt tugashi yoki foydalanuvchi yakunlashi bilan): xom ball, θ (qobiliyat darajasi), yakuniy ball (0-75 shkala) va daraja (C...A+) ko'rsatiladi
6. Natijalar tarixi — `/natijalarim` komandasi orqali oldingi urinishlar ro'yxati

### FAZA 2 — Kengaytirilgan funksiyalar
1. Bo'limlar bo'yicha statistika (qaysi mavzuda ko'proq xato qilingani)
2. Xato qilingan savollar uchun video/matn tushuntirish havolasi
3. Reyting/leaderboard (ixtiyoriy, foydalanuvchi roziligi bilan)
4. Dinamik RASH kalibrlash (yuqoridagi Faza 2)

### FAZA 3 — Admin va boshqaruv
1. Veb-admin panel: savol qo'shish/tahrirlash, qiyinlik darajasini sozlash
2. Statistika dashboard (nechta foydalanuvchi, o'rtacha ball, savol bo'yicha to'g'ri javob %)
3. Yangi test variantlarini yaratish

---

## 6. Ma'lumotlar bazasi (Supabase) — asosiy jadvallar

```
users            (id, telegram_id, full_name, created_at)
tests            (id, title, description, question_count, time_limit_min)

question_groups  (id, test_id, shared_context_text, shared_image_url,
                  shared_options JSONB)   -- 33-35 kabi guruhlangan savollar uchun,
                                          -- oddiy Y-1/O savollarda NULL group

questions        (id, test_id, group_id NULLABLE, order_no,
                  type[Y-1 / GROUPED / O],
                  text, image_url,
                  options JSONB,          -- Y-1 uchun A-D variantlar
                  sub_parts JSONB,        -- O turi uchun: [{label:"a", correct_answer:...}, {label:"b", ...}]
                  correct_answer,         -- Y-1 va GROUPED uchun
                  difficulty_b, section)

attempts         (id, user_id, test_id, started_at, finished_at,
                  raw_score, theta, final_score, grade)
attempt_answers  (id, attempt_id, question_id, sub_part_label NULLABLE,
                  user_answer, is_correct, answered_at)
```

**Izoh:** `sub_parts` — 36-45 kabi ikki qismli (a, b) ochiq savollar uchun; har bir qism alohida to'g'ri javobga va alohida Rasch difficulty-ga ega bo'lishi mumkin (chunki b-qism odatda a-qismga qaraganda qiyinroq). `attempt_answers.sub_part_label` shu qismni belgilaydi.

---

## 7. Foydalanuvchi oqimi (user flow)

```
/start → Ro'yxatdan o'tish → Test tanlash → Savol 1 → Savol 2 → ... → Savol N
       → Natija hisoblash (RASH) → Natijani ko'rsatish → Tarixga saqlash
       → "Yana test topshirish" / "Natijalarim" / "Bosh menyu"
```

---

## 8. Monetizatsiya

Hozirgi bosqichda **to'liq bepul**. Kelajakda kerak bo'lsa (masalan ko'proq mock test yoki batafsil tahlil uchun) Payme/Click orqali freemium qo'shish mumkin — bu alohida modul sifatida keyinroq loyihalashtiriladi.

---

## 9. Muvaffaqiyat mezonlari (MVP uchun)

- Foydalanuvchi to'liq testni xatosiz topshira olishi
- Ball va daraja rasmiy metodikaga (Rasch asosida, 0-75 shkala) mos hisoblanishi
- Natijalar tarixi saqlanishi va qayta ko'rish mumkinligi
- Bot 100+ bir vaqtdagi foydalanuvchini muammosiz ko'tara olishi (asinxron aiogram tufayli)

---

## 10. Ochiq savollar (keyingi muhokama uchun)

- Savollar bazasi qayerdan olinadi — o'zingiz tuzasizmi yoki mavjud DTM/oliygoh.uz/super_matematika kabi manbalardan (ruxsat bilan) foydalanasizmi?
- Nechta mock test variant kerak (bitta umumiy yoki bir nechta, masalan har hafta yangi mock)?
- 36-45 (O turi) javoblarni tekshirishda **aniq mos kelish** (exact match) yetarlimi, yoki sonli javoblarda formatlash farqlariga (masalan "3" vs "3.0" vs "3,0") tolerantlik kerakmi?
- 33-35 kabi guruhlangan savollarda rasm/chizma bo'lsa, bot foydalanuvchiga rasmni qanday yuboradi — bitta rasm barcha 3 subsavol uchun bir marta yuboriladimi?
