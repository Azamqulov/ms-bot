# 📌 PROJECT DASHBOARD & STATE — Milliy Sertifikat (Matematika) Bot

> Bu fayl loyiha ildizida yashaydi va loyihaning arxitekturaviy qarorlari, hozirgi holati va vazifalar xaritasini yuritadi.
> Umumiy texnik qoidalar global `AGENTS.md` va `skills/` papkasiga tayanadi.

## 🎯 Overall Objective & Current Phase
- **Loyiha:** Milliy Sertifikat — Matematika imtihoniga tayyorlanuvchilar uchun mock test va RASH (IRT — Item Response Theory) modeli asosida avtomatik baholovchi Telegram Bot + Telegram Mini App (Web App).
- **Hozirgi Bosqich:** Phase 4 (Cloud Database Migration: SQLite -> Supabase PostgreSQL Pooler with PgBouncer & TIMESTAMPTZ support).
- **Status:** Production / 19 ta testdan 100% muvaffaqiyatli o'tdi. Server va bot Supabase bulut bazasi bilan faol ishlamoqda.

## 🧠 Architecture Decision Log (ADR)
- **Zero Emoji & 100% Pure SVG Icons:** Foydalanuvchi talabiga ko'ra barcha standart emojilar olib tashlandi va yagona Lucide SVG ikonkalar tizimiga o'tkazildi (`icon-standards`).
- **Dark & Light Mode Theming:** `web/index.html` va `web/admin.html` da to'liq CSS tokenlar orqali Sun/Moon toggle tugmasi, `data-theme="light"` va `data-theme="dark"` qo'llab-quvvatlanadi (`dark-light-mode-theming`). Telegram WebApp rang sxemasi bilan avtomatik sinxronlashadi.
- **Katta Savollar Xaritasi Tugmasi:** `[Oldingi] [Keyingi] [Yakunlash]` tugmalarining **tagiga** to'liq enli (full-width), katta `Savollar xaritasi (1–45)` tugmasi joylashtirildi.
- **Custom Modals & Zero Native Alert/Confirm:** Brauzerning standart `alert()` va `confirm()` dialoglari butunlay olib tashlandi. Testni yakunlashda premium `#finishModal` (Davom ettirish / Ha, yakunlash) oynasi chiqadi, xatoliklar va xabarlar esa maxsus glassmorphic Toast bildirishnomalari orqali ko'rsatiladi.
- **Zero-Flicker Option Selection:** Savol variantlari tanlanganda butun DOM yoki KaTeX qayta yuklanmaydi, faqatgina `.option-item.selected` klassi yangilanadi. Matn sakrashi va shrift o'lchami o'zgarishi butunlay bartaraf etildi.
- **F5 Session Persistence & Recovery:** Foydalanuvchi test davomida F5 (sahifani yangilash) bossa ham barcha belgilangan javoblar, turgan savoli va aniq qolgan vaqt (haqiqiy vaqt asosida hisoblangan) `localStorage` orqali saqlanadi va sahifa yuklanishi bilan avtomatik davom ettiriladi.
- **Tugmalar Dizayni & Balandligi:** `#finishModal` dagi `[ Davom ettirish ]` va `[ Ha, yakunlash ]` tugmalari bir xil 46px balandlikda, 50/50 kenglikda va professional dizaynda bir tekis qilindi.
- **Ixcham Matematik Formula Paneli (Math Formula Toolbar):** Admin panelida test savollari va variantlarini yozishda formulalarni qulay kiritish uchun KaTeX bilan render qilinuvchi toifalangan (Algebra & Kasr, Trig & Log, Geometriya & Belgilar, Hisob & To'plam) ixcham virtual formula paneli qo'shildi. Tugmani bosganda formula kursor turgan joyga bir zumda joylanadi.
- **Zamonaviy Custom Select Komponenti:** Brauzerning standart xunuk ko'k `<select>` menyulari o'rniga premium, glassmorphic, aylanuvchi o'q belgisi, checkmark va A/B/C/D variant nishonlari (badge) bo'lgan zamonaviy maxsus dropdown komponenti joriy etildi.
- **Oddiy Odamlar uchun Intuitiv 3 Qadamli Savol Konstruktori:**
  1. Savol turini tushunarli vizual kartalar orqali tanlash (Variantli yoki Ochiq).
  2. Savol matnini oddiy so'zlar bilan yozish va o'quvchi ekranida qanday ko'rinishini real vaqtda kuzatish.
  3. Har bir variant yonidagi `[✓ To'g'ri javob]` tugmasini bir marta bosish orqali to'g'ri javobni bir zumda belgilash (ortiqcha dropdownlar yo'q qilindi).
- **Cache-Control Headers:** WebApp statik sahifalarida brauzer keshida eski versiya qolib ketishining oldini olish uchun `no-cache, no-store, must-revalidate` sarlavhalari ulandi.
- **Backend & Stack:** Python 3.13, `aiogram 3.31.0`, `FastAPI 0.115.0`, `uvicorn 0.34.0`, `KaTeX 0.16.11`, `SQLAlchemy 2.0.52 (async)`, `Supabase PostgreSQL (asyncpg)`.
- **Supabase Cloud Database & PgBouncer Compatibility:** Barcha ma'lumotlar bazasi lokal SQLite dan Supabase PostgreSQL bulut bazasiga ko'chirildi. PgBouncer pooler bilan `statement_cache_size: 0` va asyncpg bilan datetime nomuvofiqligining oldini olish uchun barcha sana/vaqt ustunlari `TIMESTAMPTZ` (timezone-aware) ga o'tkazildi.

## 🤖 AI Developers & Team Protocol
- Pipeline: Dev → QA-Tester → Team-Lead → Senior-QA → PM
- Barcha o'zgarishlar qat'iy sinovdan o'tkazildi (19 ta Pytest testlari orqali).

## 🔄 Active Task (In Progress)
- [x] 1. Barcha emojilarni toza SVG ikonkalarga almashtirish (0 emoji).
- [x] 2. To'liq Light Mode va Dark Mode theming tizimini joriy qilish.
- [x] 3. "Savollar xaritasi" tugmasini navigatsiya tugmalari tagiga katta qilib joylashtirish.
- [x] 4. Brauzer confirm/alert o'rniga maxsus modal va toast joriy qilish.
- [x] 5. Variant tanlanganda matn sakrashi va qayta yuklanishini bartaraf qilish.
- [x] 6. Modal tugmalari ("Davom ettirish" va "Ha, yakunlash") o'lchami va ko'rinishini bir tekis qilish.
- [x] 7. F5 bosilganda test holati, javoblar va vaqtni avtomatik tiklash (Session Persistence).
- [x] 8. Admin paneliga ixcham matematik formula va belgilarni kiritish paneli qo'shish.
- [x] 9. Barcha selectlarni zamonaviy custom select komponentiga aylantirish.
- [x] 10. Oddiy odamlar (o'qituvchilar) uchun 3 qadamli o'ta qulay va tushunarli interfeys joriy qilish.
- [x] 11. Admin test konstruktorini to'liq foydalanuvchi yuborgan 5 ta skrinshot andazasiga moslab qayta qurish (1-35 yopiq variantlar kaliti [A][B][C][D], 36-45 ochiq savollar a/b, sozlamalar va to'liq virtual matematika klaviaturasi).
- [x] 12. 18 ta testni to'liq tekshirish va tasdiqlash.
- [x] 13. Admin panelining barcha funksiyalarini to'liq ishchi holatga keltirish (Fayl yuklash, Flatpickr sana/vaqt tanlash, Tezkor kalitlarni to'ldirish, KaTeX real vaqtli matematik ko'rinish, 36-45 savollar sharti va chizmasi, Qoralamani avtosaqlash (Draft autosave), Mening testlarim ro'yxati va faollikni boshqarish, Zero native alert/confirm dialoglar).
- [x] 14. Doimiy test tanlanganda pastdagi sana/vaqtlar (Boshlash va Tugash vaqti) hamda "Testga qatnashish turi" (Ochiq/Yopiq test) bloklarini avtomatik yashirish, faqat "Vaqtli test" tanlangandagina ko'rsatish dinamikasi joriy qilindi.
- [x] 15. Ochiq test tanlanganda "Test kodi (Kupon)" maydonini butunlay yashirish, faqat "Yopiq test" tanlangandagina kod kiritish bloki chiqishi to'liq joriy qilindi.
- [x] 17. Loyiha xavfsiz holatda (.env, ma'lumotlar bazasi va ortiqcha binarlar tozalanib) git omboriga commit qilindi va `https://github.com/Azamqulov/ms-bot.git` omborining `main` tarmog'iga muvaffaqiyatli push qilindi.
- [x] 18. GitHub Pages uchun root papkada faqat `index.html` qoldirildi, `admin.html` faqat `web/admin.html` da saqlandi.
- [x] 19. Botda birinchi kirganda Ism-familiya va Telefon raqamini so'rash (onboarding), ushbu shaxsiy ma'lumotlar bilan WebApp da test topshirish va natijani avtomatik ravishda talabgorning Telegram botiga batafsil hisobot ko'rinishida yuborish to'liq joriy qilindi.
- [x] 20. Admin panelida 33-35 kontekstli savollar bloki test tekshirish (OMR) tizimiga moslashtirildi: barcha ortiqcha matn/chizma maydonlari yig'ishtirilib, to'g'ridan-to'g'ri 6 ta variantli (A–F) toza kalit tanlash qatorlari joriy qilindi.
- [x] 21. O'quvchi javoblar varaqasi foydalanuvchi yuborgan andazaga to'liq moslashtirildi: har bir savol alohida kartochkaga olinib (`1-savol` va pastida `[A][B][C][D]` to'rtburchak tugmalar), ko'z ikonkasi yashirildi.
- [x] 22. Test topshirilganda natijalar nafaqat o'quvchiga, balki ushbu testni yaratgan o'qituvchi/muallifning Telegramiga ham to'liq ma'lumotlar bilan (ism, telefon, ball, daraja) avtomatik yuborilishi ta'minlandi.
- [x] 23. Bot bosh menyusidan "Botda topshirish" tugmasi butunlay olib tashlandi va "Test topshirish (Web App)" tugmasi foydalanuvchi talabiga ko'ra "Javobni tekshirish" ga o'zgartirildi.
- [x] 24. `requirements.txt` ga `httpx>=0.27.0` qaramligi qo'shildi (toza klonda testlar to'liq o'tishi uchun).
- [x] 25. Admin API endpointlariga Telegram WebApp `initData` HMAC-SHA256 server-side autentifikatsiyasi va RBAC tekshiruvi joriy qilindi (`bot/web_app/auth.py`).
- [x] 26. `web/admin.html` va `admin.html` fayllaridan `SUPER_ADMIN_ID` fallback olib tashlandi, faqat Telegram ichida ochilishiga cheklov qo'yildi va barcha admin fetch so'rovlariga `X-Telegram-Init-Data` sarlavhasi ulandi.
- [x] 27. Barcha 19 ta Pytest testlari (xavfsizlik va endpointlar integratsiyasi bilan birga) 100% muvaffaqiyatli o'tdi.
- [x] 28. Ism-familiya validatsiyasi kuchaytirildi (faqat '.' yoki placeholder bo'lsa bot `/start` da to'liq ismni so'raydi, Web App da ham profilni tahrirlash va sinxronlash to'liq joriy qilindi).
- [x] 29. Ma'lumotlar bazasi to'liq Supabase (PostgreSQL) bulutiga ko'chirildi: barcha mavjud foydalanuvchilar, testlar, savollar va urinishlar saqlandi, PgBouncer va TIMESTAMPTZ sozlamalari joriy qilindi.
- [x] 30. Admin panelida test javoblari va savollarini tahrirlash (Edit Mode) funksiyasi to'liq joriy qilindi: har bir kartochkaga [Tahrirlash] tugmasi, formaga ma'lumotlarni avtomatik yuklash, kalitlarni o'zgartirish va backendda xavfsiz saqlash (`PUT /api/admin/tests/{test_id}`).
- [x] 31. Testlar bo'yicha to'liq statistika va o'quvchilar natijalari tizimi joriy qilindi: har bir kartochkada [Statistika] tugmasi, KPI kartochkalari (qatnashuvchilar, o'rtacha ball, eng yuqori ball, sertifikat foizi), har bir o'quvchining ismi, telefoni, to'plagan balli, darajasi va vaqti bilan reyting jadvali, o'quvchilarni qidirish qatori va `GET /api/admin/tests/{test_id}/stats` endpointi.
- [x] 32. Rasmiy "Umumta'lim fanini bilish darajasi to'g'risida sertifikat" blankasi asosida avtomatik real sertifikat generatsiya qilish tizimi joriy qilindi: talabgorning shaxsiy kodi, familiyasi, ismi, otasining ismi, to'plagan balli, umumiy ballga nisbatan foizi, sertifikat darajasi (A+..C yoki "Talabga javob bermadi"), test sinovi natijasi ("Sertifikat berilsin" / "Sertifikat berilmadi"), berilgan sanasi, 3 yillik amal qilish muddati, bot havolasi bilan integratsiyalashgan rasmiy QR kod joylanadi. WebApp natijalarida HD rasm va [Yuklab olish (JPG)] tugmasi chiqariladi, shuningdek Telegram bot orqali o'quvchi va o'qituvchiga fotosurat ko'rinishida yuboriladi.
- [x] 33. Testni yakunlashda ikki tomonlama himoya (single-click guard / debounce) va to'liq ekranli premium Glassmorphic yuklash animatsiyasi (spinner, progress bar va tushunarli holat matni) joriy qilindi. Tugma qayta bosilishi bloklandi, foydalanuvchiga test tekshirilishi va sertifikat yaratilishi jarayoni real vaqtda animatsiya bilan ko'rsatilishi ta'minlandi.
- [x] 34. Admin boshqaruv panelidan ortiqcha JSON yuklash va JSON shablon olish tugmalari hamda handlerlari butunlay olib tashlandi. "Mening testlarim" bo'limi interaktiv inline tugmalar tizimiga o'tkazildi: admin o'zi yuklagan testlar nomi va kodi bilan alohida tugmalar bo'lib chiqadi, tugma bosilganda ushbu test bo'yicha to'liq statistika (ishtirokchilar, o'rtacha/eng yuqori ball, sertifikat olganlar soni, har bir talabgorning bali, telefoni va sanasi bilan reyting jadvali) chiroyli Telegram natijalar posti sifatida taqdim etiladi.
- [x] 35. O'quvchi javoblar varaqasida [A] [B] [C] [D] (va 33-35 da A–F) variant tugmalari kartochkaning butun kengligi (100%) bo'yicha teng taqsimlanib, to'liq yoyilishi (`flex: 1`, `width: 100%`) ta'minlandi.
- [x] 36. WebApp natijalar ekranida rasmiy sertifikat rasmining cross-origin (GitHub Pages -> API tunnel) mutlaq URL manzili to'g'rilandi (404 broken image bartaraf etildi), rasm ramkasiga yuklanish spinneri o'rnatildi, "Yuklab olish (JPG)" va "Kattalashtirish" tugmalari 50/50 teng kenglikda bir tekis qilindi va to'g'ridan-to'g'ri Blob orqali telefon xotirasiga .jpg fayl qilib yuklab olish funksiyasi joriy qilindi.
- [x] 37. Test yakunlash interfeysi matnlari foydalanuvchi talabiga ko'ra tabiiy va rasmiy o'zbek tiliga o'tkazildi: suzuvchi panel tugmasi "Testni yakunlash", tasdiqlash modali sarlavhasi "Testni yakunlaysizmi?", bekor qilish "Davom ettirish" va asosiy yakunlash tugmasi "Ha, tugatish" deb qayta nomlandi.
- [x] 38. O'quvchi javoblar varaqasi (Web App) boshlang'ich mavzusi (default theme) foydalanuvchi talabiga asosan Dark rejimidan Light rejimiga o'tkazildi: `:root` tokenlari Light rejimga moslandi, HTML `data-theme="light"` qilindi, quyosh/oy ikonkasi to'g'rilandi va mavzu tanlash xotirasi (`ms_theme_v2`) sinxronlashtirildi.
- [x] 39. Foydalanuvchi talabiga asosan 5 ta muhim biznes logika va interfeys sozlamalari joriy qilindi:
  - 1) "Telegram kanalga majburiy obuna" bloki admin interfeysidan butunlay olib tashlandi.
  - 2) "36–45 savollar uchun javob berish usuli" (Yozish / Rasmga olish) ortiqcha segmenti olib tashlandi, standart faqat 'write' rejimida qoldirildi.
  - 3) "Testga qatnashish turi"da "Ochiq test" noaktiv qilindi, faqat "Yopiq test" faol qoldirildi; "Test kodi (Kupon)" doimiy ko'rinadigan qilib chiqarildi.
  - 4) "Test yakunlangandan keyin natijalarni yashirish" (`hide_answers`) funksiyasi to'liq ulandi: agar bu yoqilgan bo'lsa, o'quvchi testni yakunlaganda bal va to'g'ri javoblar ko'rsatilmaydi, "Test muvaffaqiyatli yakunlandi! Natijalarni ustozingiz e'lon qiladi" xabari beriladi; agar o'chiq bo'lsa natija darhol sertifikat bilan chiqadi. Natijalar ustozga har doim to'liq yetib boradi.
  - 5) Vaqt tugaganda (`remainingSeconds <= 0`) avtomatik testni yakunlash (auto-submit timeout) to'liq ishchi holatga keltirildi.
- [x] 40. `web/index.html` va `web/admin.html` fayllariga to'liq mobil-first responsive CSS media queries tizimi joriy qilindi:
  - 360px (juda kichik telefon): container padding kichraytirildi, header/timer yozuvlari kichraydi, pufakchali variant tugmalari (`bubble-btn`) kichik o'lchamga tushirildi, diagnostika panjarasida ustun soni 5 dan 4 ga kamaytirildi, modal padding va font-size optimallashtirildi.
  - 480px (kichik telefon): header `flex-wrap:wrap` qilindi (yozuvlar pastga siljishi o'rniga qator bo'yicha joylashadi), stat-row (`span`/`b`) avvalgiday yonma-yon lekin kichraymagan holda chiqadi, sertifikat yuklab olish tugmalari ekranga sig'adi, admin-nav-btn yorliqlari kichrayadi, test kartochalari (`test-card`) va statistika modal KPI bloki 2 ustunli grid formatga o'tadi.
  - 576px: ochiq savol juft kiritish qatorlari (`open-inputs-pair`) 2 ustundan 1 ustunlik to'liq kenglikka o'tadi.
  - 640px: `app-container` 100% kenglikda bo'ladi.

## ✅ Completed Checklist (History)
- [x] [2026-09-07] LaTeX formula tozalash moduli yaratildi.
- [x] [2026-09-07] Super Admin (`1685356708`) va Adminlar boshqaruvi yo'lga qo'yildi.
- [x] [2026-09-07] FastAPI backend (`bot/web_app/api.py`) yaratildi.
- [x] [2026-09-07] `web/index.html` va `web/admin.html` toza SVG ikonkalar va Light/Dark theme bilan yangilandi.
- [x] [2026-09-07] Admin panelidagi barcha funksiyalar (fayl yuklash, sana tanlash, tezkor kalitlar, KaTeX preview, test boshqaruvi) 100% to'liq ishchi holatga keltirildi.
- [x] [2026-09-07] Doimiy test / Vaqtli test selektoriga bog'liq holda vaqt va ochiq/yopiq sozlamalarini dinamik ko'rsatish/yashirish to'liq ulandi.
- [x] [2026-09-07] Ochiq testda "Test kodi"ni yashirish va Yopiq testda ko'rsatish dinamikasi ulandi.
- [x] [2026-09-07] Ortiqcha "Fanni tanlang" menyusi butunlay olib tashlandi.
- [x] [2026-09-07] Loyiha to'liq `https://github.com/Azamqulov/ms-bot.git` ga push qilindi.
- [x] [2026-09-07] Boshqa foydalanuvchilar test topshirganda ularning natijalari admin ID si (1685356708) bilan yozilib ketishi va "Natijalarim"da ko'rinmaslik muammosi to'liq tuzatildi: web/index.html da studentTelegramId, query param va Telegram WebApp user ID dinamik bog'landi, hardcoded admin ID fallback butunlay olib tashlandi.
- [x] [2026-09-07] 20 ta Pytest testlari 100% muvaffaqiyatli o'tdi.
- [x] [2026-09-07] Server va bot parallel holda fonda ishlamoqda.
- [x] [2026-09-08] Admin foydalanuvchilar "Admin panelga o'tish" tugmasini bosganda yuzaga kelgan GitHub Pages 404 (File not found) xatosi to'liq bartaraf etildi: `getAdminPanelUrl` dinamik yo'l aniqlash funksiyasi joriy qilindi, `navigateToAdminPanel` orqali query parametrlar saqlangan holda to'g'ri `web/admin.html` ga yo'naltirildi, root `404.html` va `admin/index.html` redirection ko'priklari qo'shildi, backendda `/web` statik marshruti ta'minlandi.
- [x] [2026-09-08] Admin statistika modalida "Telegramga post qilish" funksiyasi to'liq joriy qilindi: umumiy KPI va har bir talabgorning to'g'ri javoblari soni, to'plagan bali va sertifikat holati (`Ism Familiya ------ 🎯 X ta to'g'ri, ⭐️ Y ball, Daraja (✅ berildi / ❌ berilmadi)`) ko'rinishida Telegramga yuborish (va clipboardga nusxalash) imkoniyati yaratildi; backendda `POST /api/admin/tests/{test_id}/send-telegram-post` endpointi va `format_telegram_stats_post` servisi yaratildi.
- [x] [2026-09-08] GitHub Actions Linux CI fail bo'lishi (`certificate_service.py` shrift yuklashdagi `cannot open resource` xatosi) to'liq tuzatildi: shrift tanlash cross-platform qilindi (Linux DejaVu/Liberation/FreeSans va xavfsiz `load_default()` fallback). Telegramga post yuborish ishonchliligi oshirildi: HTML belgilari `html.escape` qilindi, bot instansiyasi fallback bilan ta'minlandi, kanal username tozalash joriy etildi va Telegram bot chatiga ham "📢 Kanal/Guruhga post qilish" tugmasi ulandi.
- [x] [2026-09-08] Admin statistika va test yaratish bo'yicha 4 ta muhim takomillashtirish to'liq amalga oshirildi:
  1) Ortiqcha modal/URL so'rash dialogi butunlay olib tashlandi: "Telegramga post qilish" bosilganda to'g'ridan-to'g'ri operatsiyani amalga oshirayotgan adminning o'z chatiga chiroyli hisobot yuboriladi.
  2) Statistikada talabgorlar natijasini bosganda ochiluvchi batafsil savolma-savol tahlil modali (`attemptDetailsModal`) yaratildi: 45 ta savolning har biri bo'yicha talabgor qaysi javobni tanlagani, to'g'ri javob nima ekanligi va status nishonlari (✅ To'g'ri, ❌ Noto'g'ri, ⚪️ Yechilmagan) aniq ko'rsatiladi.
  3) Yangi test yaratishda eski test ma'lumotlari (kod, nom, javoblar, qoralama) qolib ketishi butunlay bartaraf etildi (`resetCreateForm`, `confirmResetDraft`, `switchAdminTab` va nashr qilishdan keyin avtomatik tozalash).
  4) Bir xil kodli test yaratishga yo'l qo'ymaslik frontend (`window.myTestsCache` tekshiruvi) va backendda (`func.upper(Test.code) == clean_code` tekshiruvi) qat'iy kafolatlandi. Barcha 28 ta test 100% muvaffaqiyatli o'tdi.
- [x] [2026-09-08] Yozma (36-45) va yopiq (1-35) savollarni hisoblashdagi barcha muammolar to'liq bartaraf etildi:
  1) `web/js/admin.js` da yozma savollar `type: "O-1"` deb generatsiya qilinayotgani sababli backendda (`if q.type == "O"`) tekshiruvidan o'tmay qolayotgan edi. Backend `attempt_service.py`, `test_service.py` va `admin_service.py` da `is_open = q.type in ("O", "O-1") or (q.sub_parts and len(q.sub_parts) > 0) or q.order_no >= 36` mustahkam tekshiruvi o'rnatildi va `admin.js` da standart `type: "O"` ga keltirildi; mavjud bazadagi `O-1` savollar migratsiya qilindi.
  2) Yozma savollarning `alternative_answers` (nuqta/vergul: `12.0` va `12,0`, kasr va o'nlik) hisobga olinmayotgani to'g'rilandi.
  3) Yopiq savollarda registr (kichik/katta harflar `a` vs `A`) va probellar (`" A "`) `.strip().upper()` bilan to'liq normallashtirildi.
  4) Yangi test `tests/test_evaluation_open_closed.py` qo'shildi va barcha 30 ta test 100% muvaffaqiyatli o'tdi.

## 📋 Roadmap & Upcoming Tasks (Backlog)
- [ ] Faza 2: Savollar uchun video/matnli yechimlar havolasi.
- [ ] Faza 2: Mavzular (bo'limlar) bo'yicha tahlil.
- [ ] Faza 2: Leaderboard (Umumiy reyting jadvali).
