import re
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.services.test_service import get_or_create_user, get_user_by_telegram_id, update_user_profile
from bot.services.admin_service import is_admin
from bot.keyboards.reply import get_main_menu_keyboard, get_phone_request_keyboard
from bot.states.registration_state import RegistrationState

router = Router(name="common")


def is_valid_name(name: str | None) -> bool:
    if not name:
        return False
    if name.strip().lower() in ("talabgor", ".", "-", "none"):
        return False
    clean = re.sub(r"[^a-zA-Zа-яА-ЯўқғҳЎҚҒҲ\s\']", "", name).strip()
    return len(clean) >= 3


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        full_name=message.from_user.full_name or "Talabgor",
        username=message.from_user.username,
    )
    is_adm = await is_admin(message.from_user.id)

    # Agar foydalanuvchi hali telefon raqami bilan ro'yxatdan o'tmagan bo'lsa
    # yoki ismi yaroqsiz bo'lsa (masalan '.' yoki 3 ta harfdan kam bo'lsa)
    if not user.phone_number or not is_valid_name(user.full_name):
        ask_name_text = (
            "Assalomu alaykum! 🎓 <b>Milliy Sertifikat — Matematika</b> sinov botiga xush kelibsiz!\n\n"
            "Test natijalaringizni rasmiy hisoblash va sertifikat ballingizni to'g'ri qayd etish uchun, "
            "iltimos, to'liq <b>Ism va Familiyangizni</b> kiriting:\n\n"
            "<i>(Masalan: Rustamov Jasur)</i>"
        )
        await state.set_state(RegistrationState.waiting_for_full_name)
        await message.answer(ask_name_text)
        return

    welcome_text = (
        f"Assalomu alaykum, <b>{user.full_name}</b>!\n\n"
        f"🎓 <b>'Milliy Sertifikat — Matematika'</b> sinov botiga xush kelibsiz!\n\n"
        f"Ushbu bot orqali siz:\n"
        f"• Real imtihon formatidagi <b>45 ta savoldan</b> iborat mock test topshirasiz;\n"
        f"• Natijangiz rasmiy <b>RASH (IRT) modeli</b> asosida baholanadi;\n"
        f"• <b>0 dan 75 gacha</b> aniq ball hamda rasmiy darajangizni (<b>A+, A, B+, B, C+, C</b>) olasiz;\n"
        f"• O'z bilimingizni sinab, imtihonga 100% tayyorlanasiz.\n\n"
        f"Boshlash uchun pastdagi <b>'🚀 Javobni tekshirish'</b> tugmasini bosing!"
    )
    await message.answer(welcome_text, reply_markup=get_main_menu_keyboard(is_adm, user=user))


@router.message(Command("ism"))
@router.message(Command("profil"))
async def cmd_edit_profile(message: Message, state: FSMContext):
    """Ism va familiyani tahrirlash komandasi"""
    await state.set_state(RegistrationState.waiting_for_full_name)
    await message.answer(
        "Iltimos, to'liq <b>Ism va Familiyangizni</b> kiriting:\n\n"
        "<i>(Masalan: Rustamov Jasur)</i>"
    )


@router.message(RegistrationState.waiting_for_full_name)
async def process_full_name(message: Message, state: FSMContext):
    name_text = (message.text or "").strip()
    if not is_valid_name(name_text):
        await message.answer(
            "⚠️ Iltimos, haqiqiy ism va familiyangizni to'liq kiriting (kamida 3 ta harf).\n"
            "<i>Masalan: Rustamov Jasur</i>"
        )
        return

    # Agar foydalanuvchining telefon raqami allaqachon bazada bo'lsa,
    # to'g'ridan-to'g'ri ismni yangilab asosiy menyuga o'tkazamiz
    user = await get_user_by_telegram_id(message.from_user.id)
    if user and user.phone_number:
        await update_user_profile(
            telegram_id=message.from_user.id,
            full_name=name_text,
            phone_number=user.phone_number,
            username=message.from_user.username,
        )
        await state.clear()
        is_adm = await is_admin(message.from_user.id)
        db_user = await get_user_by_telegram_id(message.from_user.id)
        await message.answer(
            f"✅ Ism va familiyangiz muvaffaqiyatli saqlandi: <b>{name_text}</b>\n\n"
            f"Pastdagi <b>'🚀 Javobni tekshirish'</b> tugmasini bosib testni topshirishingiz mumkin!",
            reply_markup=get_main_menu_keyboard(is_adm, user=db_user)
        )
        return

    await state.update_data(full_name=name_text)
    await state.set_state(RegistrationState.waiting_for_phone)

    await message.answer(
        f"Ajoyib, <b>{name_text}</b>!\n\n"
        "Endi ro'yxatdan o'tishni yakunlash uchun <b>telefon raqamingizni</b> yuboring:\n\n"
        "<i>(Pastdagi '📱 Telefon raqamimni yuborish' tugmasini bosing yoki +998901234567 shaklida yozing)</i>",
        reply_markup=get_phone_request_keyboard()
    )


@router.message(RegistrationState.waiting_for_phone, F.contact)
@router.message(RegistrationState.waiting_for_phone, F.text)
async def process_phone(message: Message, state: FSMContext):
    data = await state.get_data()
    full_name = data.get("full_name") or message.from_user.full_name or "Talabgor"

    phone = None
    if message.contact and message.contact.phone_number:
        phone = message.contact.phone_number
        if not phone.startswith("+"):
            phone = "+" + phone
    elif message.text:
        raw = message.text.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        # O'zbekiston yoki xalqaro raqam formati
        if re.match(r"^\+?\d{9,15}$", raw):
            phone = raw if raw.startswith("+") else ("+" + raw)

    if not phone:
        await message.answer(
            "⚠️ Telefon raqami noto'g'ri kiritildi. Iltimos, pastdagi tugmani bosing yoki raqamingizni quyidagicha yozing:\n"
            "<code>+998901234567</code>",
            reply_markup=get_phone_request_keyboard()
        )
        return

    # Bazaga profilni saqlash
    await update_user_profile(
        telegram_id=message.from_user.id,
        full_name=full_name,
        phone_number=phone,
        username=message.from_user.username,
    )
    await state.clear()

    is_adm = await is_admin(message.from_user.id)
    success_text = (
        f"🎉 <b>Tabriklaymiz, {full_name}!</b>\n\n"
        f"Siz muvaffaqiyatli ro'yxatdan o'tdingiz.\n"
        f"👤 <b>Talabgor:</b> {full_name}\n"
        f"📱 <b>Telefon:</b> {phone}\n\n"
        "Endi pastdagi <b>'🚀 Javobni tekshirish'</b> tugmasini bosib, to'g'ridan-to'g'ri Milliy Sertifikat javoblar varaqasini tekshirishingiz mumkin!\n"
        "Test natijalaringiz avtomatik hisoblanib, ushbu botga batafsil hisobot sifatida keladi."
    )
    db_user = await get_user_by_telegram_id(message.from_user.id)
    await message.answer(success_text, reply_markup=get_main_menu_keyboard(is_adm, user=db_user))


@router.message(F.text == "ℹ️ RASH modeli haqida")
@router.message(Command("rasch"))
async def show_rasch_info(message: Message):
    text = (
        "📐 <b>RASH (Item Response Theory — IRT) MODELI HAQIDA</b>\n\n"
        "Milliy Sertifikat imtihonlarida ballar oddiy to'g'ri javoblar soni bilan emas, "
        "balki <b>RASH ilmiy modeli</b> orqali hisoblanadi.\n\n"
        "<b>Bu qanday ishlaydi?</b>\n"
        "1. Har bir savol o'zining qiyinlik darajasiga (<b>b-parametr</b>) ega.\n"
        "2. Qiyin savolga to'g'ri javob berish talabgorning qobiliyati (<b>θ — theta</b>) yuqori ekanini ko'rsatadi.\n"
        "3. Formula: <code>P(to'g'ri) = 1 / (1 + e^(-(θ - b)))</code>\n"
        "4. Maximum Likelihood Estimation (MLE) orqali barcha javoblar majmuasidan sizning aniq qobiliyatingiz aniqlanadi.\n"
        "5. Yakunda qobiliyat ko'rsatkichi <b>0–75 ballik rasmiy shkalaga</b> o'giriladi.\n\n"
        "🎖 <b>Rasmiy darajalar:</b>\n"
        "• <b>A+</b>: 70.0 — 75.0 ball (100% imtiyoz)\n"
        "• <b>A</b>: 65.0 — 69.9 ball (Maksimal ball)\n"
        "• <b>B+</b>: 60.0 — 64.9 ball\n"
        "• <b>B</b>: 55.0 — 59.9 ball\n"
        "• <b>C+</b>: 50.0 — 54.9 ball\n"
        "• <b>C</b>: 46.0 — 49.9 ball (Minimal o'tish)\n"
        "• <b>Sertifikat berilmaydi</b>: 46.0 balldan past."
    )
    await message.answer(text)


@router.message(F.text == "❓ Yordam")
@router.message(Command("help"))
async def show_help(message: Message):
    text = (
        "🎓 <b>MILLIY SERTIFIKAT (MATEMATIKA) SINOV BOTI</b>\n\n"
        "Ushbu bot Bilim va malakalarni baholash agentligi (DTM) standarti asosida "
        "Matematika fanidan Milliy Sertifikat imtihoniga tayyorgarlik ko'rish, bilimingizni "
        "real sinovdan o'tkazish va aniq natijangizni bilish uchun yaratilgan.\n\n"
        "📐 <b>Baholash tizimi (RASH IRT modeli):</b>\n"
        "• Ballar shunchaki to'g'ri javoblar soniga qarab emas, balki xalqaro <b>RASH (Item Response Theory)</b> modeli asosida hisoblanadi;\n"
        "• Har bir savol o'z qiyinlik darajasiga (b-parametr) ega bo'lib, natija <b>0 dan 75 gacha</b> bo'lgan rasmiy shkalada aniqlanadi;\n"
        "• Natijaga ko'ra rasmiy darajalar belgilanadi: <b>A+, A, B+, B, C+, C</b>.\n\n"
        "📋 <b>Test formati va tuzilishi:</b>\n"
        "⏳ <b>Umumiy vaqt:</b> 150 daqiqa (2 soat 30 daqiqa);\n"
        "• <b>1–32-savollar (Y-1):</b> 4 variantli yopiq testlar (A, B, C, D);\n"
        "• <b>33–35-savollar:</b> Bitta umumiy kontekst/chizma asosidagi 3 ta guruhlangan savol (A–F variantlar);\n"
        "• <b>36–45-savollar:</b> Ochiq yozma savollar (a va b bandlari).\n\n"
        "🎖 <b>Rasmiy QR-kodli elektron sertifikat:</b>\n"
        "Testni topshirib yakunlashingiz bilanoq, bot sizga to'plagan balingiz, umumiy foiz va "
        "darajangiz ko'rsatilgan <b>rasmiy elektron sertifikat blankasini (QR-kod bilan)</b> darhol taqdim etadi!\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "👨‍🏫 <b>USTOZLAR VA REPETITORLAR DIQQATIGA:</b>\n"
        "Agar siz o'z o'quvchilaringiz uchun milliy sertifikat formatida <b>yangi test javoblarini yaratish</b>, "
        "maxsus kod orqali test o'tkazish hamda barcha o'quvchilar natijalari statistikasini olishni istasangiz, "
        "botda <b>Admin huquqi</b> talab qilinadi.\n\n"
        "👨‍💻 <b>SHAXSIY YORDAM VA ADMIN BILAN BOG'LANISH:</b>\n"
        "• Bot bo'yicha har qanday savol va takliflar;\n"
        "• Yangi test javoblarini yaratish (Admin huquqi olish);\n"
        "• Shaxsiy maslahat va yordam uchun:\n\n"
        "👉 <b>Bosh admin:</b> @ITCenter_01"
    )
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="💬 Shaxsiy yordam / Admin (@ITCenter_01)",
            url="https://t.me/ITCenter_01"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="ℹ️ RASH modeli haqida batafsil",
            callback_data="help_rasch_info"
        )
    )
    await message.answer(text, reply_markup=builder.as_markup())


@router.callback_query(F.data == "help_rasch_info")
async def callback_help_rasch_info(callback: CallbackQuery):
    await callback.answer()
    text = (
        "📐 <b>RASH (Item Response Theory — IRT) MODELI HAQIDA</b>\n\n"
        "Milliy Sertifikat imtihonlarida ballar oddiy to'g'ri javoblar soni bilan emas, "
        "balki <b>RASH ilmiy modeli</b> orqali hisoblanadi.\n\n"
        "<b>Bu qanday ishlaydi?</b>\n"
        "1. Har bir savol o'zining qiyinlik darajasiga (<b>b-parametr</b>) ega.\n"
        "2. Qiyin savolga to'g'ri javob berish talabgorning qobiliyati (<b>θ — theta</b>) yuqori ekanini ko'rsatadi.\n"
        "3. Formula: <code>P(to'g'ri) = 1 / (1 + e^(-(θ - b)))</code>\n"
        "4. Maximum Likelihood Estimation (MLE) orqali barcha javoblar majmuasidan sizning aniq qobiliyatingiz aniqlanadi.\n"
        "5. Yakunda qobiliyat ko'rsatkichi <b>0–75 ballik rasmiy shkalaga</b> o'giriladi.\n\n"
        "🎖 <b>Rasmiy darajalar:</b>\n"
        "• <b>A+</b>: 70.0 — 75.0 ball (100% imtiyoz)\n"
        "• <b>A</b>: 65.0 — 69.9 ball (Maksimal ball)\n"
        "• <b>B+</b>: 60.0 — 64.9 ball\n"
        "• <b>B</b>: 55.0 — 59.9 ball\n"
        "• <b>C+</b>: 50.0 — 54.9 ball\n"
        "• <b>C</b>: 46.0 — 49.9 ball (Minimal o'tish)\n"
        "• <b>Sertifikat berilmaydi</b>: 46.0 balldan past."
    )
    await callback.message.answer(text)

