import json
import io
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext

from bot.services.admin_service import (
    is_admin,
    is_super_admin,
    add_admin,
    remove_admin,
    get_all_admins,
    create_test_with_questions,
    get_admin_tests,
    get_sample_test_template,
)
from bot.services.test_service import get_or_create_user
from bot.keyboards.admin import get_admin_dashboard_keyboard, get_admin_back_keyboard
from bot.keyboards.reply import get_main_menu_keyboard
from bot.states.admin_state import AdminState

router = Router(name="admin")


@router.message(F.text == "👑 Admin Panel")
@router.message(Command("admin"))
async def open_admin_panel(message: Message, state: FSMContext):
    await state.clear()
    telegram_id = message.from_user.id
    if not await is_admin(telegram_id):
        await message.answer("⛔ <b>Kechirasiz, sizda Admin huquqi yo'q!</b>")
        return

    is_super = is_super_admin(telegram_id)
    role_title = "Super Admin" if is_super else "Admin"

    text = (
        f"👑 <b>BOSHQARUV PANELI ({role_title})</b>\n\n"
        f"Xush kelibsiz, <b>{message.from_user.full_name}</b>!\n"
        f"Quyidagi bo'limlardan birini tanlang:"
    )
    await message.answer(text, reply_markup=get_admin_dashboard_keyboard(is_super))


@router.callback_query(F.data == "adm_open_panel")
async def callback_admin_panel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    telegram_id = callback.from_user.id
    if not await is_admin(telegram_id):
        await callback.answer("Ruxsat berilmagan.", show_alert=True)
        return

    is_super = is_super_admin(telegram_id)
    text = (
        f"👑 <b>BOSHQARUV PANELI</b>\n\n"
        f"Quyidagi bo'limlardan birini tanlang:"
    )
    await callback.answer()
    await callback.message.edit_text(text, reply_markup=get_admin_dashboard_keyboard(is_super))


@router.callback_query(F.data == "adm_close_panel")
async def callback_close_panel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    await callback.message.delete()
    is_adm = await is_admin(callback.from_user.id)
    await callback.message.answer("Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu_keyboard(is_adm))


# ==================== SUPER ADMIN: ADMINLARNI BOSHQARISH ====================

@router.callback_query(F.data == "adm_list_admins")
async def handle_list_admins(callback: CallbackQuery):
    if not is_super_admin(callback.from_user.id):
        await callback.answer("Faqat Super Admin uchun!", show_alert=True)
        return

    admins = await get_all_admins()
    lines = ["👥 <b>RO'YXATDAN O'TGAN ADMINLAR:</b>\n"]
    for idx, adm in enumerate(admins, start=1):
        tag = "⭐ Super Admin" if adm.role == "super_admin" or adm.telegram_id == callback.from_user.id else "👤 Admin"
        name = adm.full_name or "Noma'lum"
        username = f"@{adm.username}" if adm.username else "yo'q"
        lines.append(f"{idx}. {tag}: <b>{name}</b> ({username}) | ID: <code>{adm.telegram_id}</code>")

    lines.append("\n<i>Yangi admin qo'shish yoki o'chirish uchun panel tugmalaridan foydalaning.</i>")
    await callback.answer()
    await callback.message.edit_text("\n".join(lines), reply_markup=get_admin_back_keyboard())


@router.callback_query(F.data == "adm_add_admin_prompt")
async def handle_add_admin_prompt(callback: CallbackQuery, state: FSMContext):
    if not is_super_admin(callback.from_user.id):
        await callback.answer("Faqat Super Admin uchun!", show_alert=True)
        return

    await state.set_state(AdminState.waiting_add_admin_id)
    await callback.answer()
    await callback.message.edit_text(
        "➕ <b>YANGI ADMIN QO'SHISH</b>\n\n"
        "Iltimos, yangi admin bo'ladigan foydalanuvchining <b>Telegram ID</b> raqamini kiriting (masalan: <code>987654321</code>):\n\n"
        "<i>Foydalanuvchi o'z ID sini @userinfobot kabi botlar orqali bilib olishi mumkin.</i>",
        reply_markup=get_admin_back_keyboard()
    )


@router.message(AdminState.waiting_add_admin_id)
async def process_add_admin_id(message: Message, state: FSMContext):
    raw_id = message.text.strip()
    if not raw_id.isdigit():
        await message.answer("⚠️ Iltimos, faqat sonlardan iborat to'g'ri Telegram ID kiriting:")
        return

    target_id = int(raw_id)
    success, msg = await add_admin(target_id)
    await state.clear()
    await message.answer(f"{'✅' if success else '❌'} {msg}", reply_markup=get_main_menu_keyboard(True))


@router.callback_query(F.data == "adm_remove_admin_prompt")
async def handle_remove_admin_prompt(callback: CallbackQuery, state: FSMContext):
    if not is_super_admin(callback.from_user.id):
        await callback.answer("Faqat Super Admin uchun!", show_alert=True)
        return

    await state.set_state(AdminState.waiting_remove_admin_id)
    await callback.answer()
    await callback.message.edit_text(
        "➖ <b>ADMINNI O'CHIRISH</b>\n\n"
        "Adminlikdan o'chirmoqchi bo'lgan foydalanuvchining <b>Telegram ID</b> raqamini kiriting:",
        reply_markup=get_admin_back_keyboard()
    )


@router.message(AdminState.waiting_remove_admin_id)
async def process_remove_admin_id(message: Message, state: FSMContext):
    raw_id = message.text.strip()
    if not raw_id.isdigit():
        await message.answer("⚠️ Iltimos, to'g'ri Telegram ID kiriting:")
        return

    target_id = int(raw_id)
    success, msg = await remove_admin(target_id)
    await state.clear()
    await message.answer(f"{'✅' if success else '❌'} {msg}", reply_markup=get_main_menu_keyboard(True))


# ==================== TEST YUKLASH VA TEST SHABLONI ====================

@router.callback_query(F.data == "adm_get_template")
async def handle_get_template(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q.", show_alert=True)
        return

    template_str = get_sample_test_template()
    file_data = template_str.encode("utf-8")
    input_file = BufferedInputFile(file_data, filename="test_shablon.json")

    caption = (
        "📄 <b>TEST YUKLASH SHABLONI (JSON)</b>\n\n"
        "1. Ushbu JSON faylni yuklab oling va kompyuter yoki telefonda tahrirlang;\n"
        "2. Unda test kodi (<code>code</code>), nomi (<code>title</code>), vaqt chegarasi (<code>time_limit_min</code>) va savollar ro'yxatini yozing;\n"
        "3. Savol turlari:\n"
        "   • <code>Y-1</code> — 4 variantli yopiq savol (options: A, B, C, D)\n"
        "   • <code>O</code> — ochiq savol (sub_parts: a va b qismlari)\n"
        "4. Tayyor faylni botga <b>'📤 Yangi test yuklash'</b> bo'limida yuboring!"
    )
    await callback.answer()
    await callback.message.answer_document(input_file, caption=caption)


@router.callback_query(F.data == "adm_upload_test_prompt")
async def handle_upload_test_prompt(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q.", show_alert=True)
        return

    await state.set_state(AdminState.waiting_test_file)
    await callback.answer()
    await callback.message.edit_text(
        "📤 <b>YANGI TEST YUKLASH</b>\n\n"
        "Iltimos, to'ldirilgan <b>.json</b> shablon faylingizni hujjat (document) sifatida yuboring, "
        "yoki to'g'ridan-to'g'ri JSON matnini shu yerga xabar sifatida yozing.\n\n"
        "<i>(Shablon yo'q bo'lsa, '📄 Shablon fayl' tugmasi orqali oling)</i>",
        reply_markup=get_admin_back_keyboard()
    )


@router.message(AdminState.waiting_test_file, F.document)
async def process_test_file_doc(message: Message, state: FSMContext):
    doc = message.document
    if not doc.file_name.endswith(".json"):
        await message.answer("⚠️ Iltimos, faqat <b>.json</b> formatidagi fayl yuboring:")
        return

    # Faylni yuklab olish
    bot = message.bot
    file_io = io.BytesIO()
    await bot.download(doc, destination=file_io)
    content = file_io.getvalue().decode("utf-8")

    await parse_and_save_test(message, state, content)


@router.message(AdminState.waiting_test_file, F.text)
async def process_test_file_text(message: Message, state: FSMContext):
    await parse_and_save_test(message, state, message.text)


async def parse_and_save_test(message: Message, state: FSMContext, content_str: str):
    """JSON matnni parse qilib bazaga saqlash"""
    try:
        data = json.loads(content_str)
    except Exception as e:
        await message.answer(f"❌ <b>JSON formatida xatolik bor:</b>\n<code>{str(e)}</code>\n\nIltimos, faylni tekshirib qayta yuboring:")
        return

    code = data.get("code")
    title = data.get("title")
    description = data.get("description", "")
    time_limit = int(data.get("time_limit_min", 150))
    questions = data.get("questions", [])
    grouped_ctx = data.get("grouped_context")

    if not code or not title or not questions:
        await message.answer("❌ Faylda <code>code</code>, <code>title</code> yoki <code>questions</code> maydonlari topilmadi!")
        return

    admin_user = await get_or_create_user(message.from_user.id, message.from_user.full_name)

    success, msg, test_obj = await create_test_with_questions(
        creator_user_id=admin_user.id,
        code=code,
        title=title,
        description=description,
        time_limit_min=time_limit,
        questions_data=questions,
        grouped_context=grouped_ctx,
    )

    if success and test_obj:
        await state.clear()
        reply_text = (
            f"🎉 <b>TEST MUVAFFAQIYATLI YUKLANDI!</b>\n\n"
            f"📌 <b>Test Kodi:</b> <code>{test_obj.code}</code>\n"
            f"📝 <b>Nomi:</b> {test_obj.title}\n"
            f"❓ <b>Savollar soni:</b> {test_obj.question_count} ta\n"
            f"⏱ <b>Vaqt chegarasi:</b> {test_obj.time_limit_min} daqiqa\n\n"
            f"💡 <i>Talabgorlar botda '📝 Test topshirish' bosgach <code>{test_obj.code}</code> kodini kiritib testni boshlashlari mumkin!</i>"
        )
        await message.answer(reply_text, reply_markup=get_main_menu_keyboard(True))
    else:
        await message.answer(f"❌ {msg}\n\nIltimos, qayta urinib ko'ring:")


@router.callback_query(F.data == "adm_my_tests")
async def handle_my_tests(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q.", show_alert=True)
        return

    admin_user = await get_or_create_user(callback.from_user.id, callback.from_user.full_name)
    tests = await get_admin_tests(admin_user.id)

    if not tests:
        text = (
            "📭 <b>Siz hali birorta ham test yuklamagansiz.</b>\n\n"
            "Yangi test yuklash uchun <b>'📤 Yangi test yuklash'</b> tugmasini bosing."
        )
    else:
        lines = ["📋 <b>SIZ YUKLAGAN TESTLAR:</b>\n"]
        for idx, t in enumerate(tests, start=1):
            lines.append(
                f"{idx}. <b>{t['title']}</b>\n"
                f"   🔑 Kodi: <code>{t['code']}</code> | Savollar: {t['question_count']} ta\n"
                f"   👥 Talabgorlar: {t['attempts_count']} nafar | O'rtacha ball: {t['avg_score']}/75\n"
            )
        text = "\n".join(lines)

    await callback.answer()
    await callback.message.edit_text(text, reply_markup=get_admin_back_keyboard())
