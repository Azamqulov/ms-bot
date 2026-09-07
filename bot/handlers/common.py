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
    if not user.phone_number:
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
        f"Boshlash uchun pastdagi <b>'🚀 Test topshirish (Web App)'</b> tugmasini bosing!"
    )
    await message.answer(welcome_text, reply_markup=get_main_menu_keyboard(is_adm, user=user))


@router.message(RegistrationState.waiting_for_full_name)
async def process_full_name(message: Message, state: FSMContext):
    name_text = (message.text or "").strip()
    if len(name_text) < 3 or len(name_text) > 100:
        await message.answer(
            "⚠️ Iltimos, haqiqiy ism va familiyangizni to'liq kiriting (kamida 3 ta harf).\n"
            "<i>Masalan: Rustamov Jasur</i>"
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
        "Endi pastdagi <b>'🚀 Test topshirish (Web App)'</b> tugmasini bosib, to'g'ridan-to'g'ri Milliy Sertifikat mock testini topshirishingiz mumkin!\n"
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
        "📖 <b>BOTDAN FOYDALANISH BO'YICHA QO'LLANMA:</b>\n\n"
        "1️⃣ <b>Vaqt:</b> Butun test uchun umumiy <b>150 daqiqa</b> (2 soat 30 daqiqa) beriladi.\n"
        "2️⃣ <b>Savollar formati:</b>\n"
        "  • <b>1–32-savollar (Y-1):</b> 4 variantli yopiq test (A, B, C, D)\n"
        "  • <b>33–35-savollar (Guruhlangan):</b> Bitta umumiy chizma/matn asosida 3 ta savol va 6 ta umumiy variant (A–F)\n"
        "  • <b>36–45-savollar (Ochiq):</b> Javobni matn yoki son sifatida yozish (a va b qismlar)\n"
        "3️⃣ <b>Navigatsiya:</b> Test davomida savollar orasida bemalol oldinga-orqaga harakatlanishingiz va javoblarni o'zgartirishingiz mumkin.\n"
        "4️⃣ <b>Yakunlash:</b> Barcha savollarga javob bergach yoki vaqtingiz yetganda '🏁 Testni yakunlash' tugmasini bosing."
    )
    await message.answer(text)
