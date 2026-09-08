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
    get_admin_tests,
    get_test_participants_stats,
)
from bot.services.test_service import get_or_create_user, get_user_by_telegram_id
from bot.keyboards.admin import (
    get_admin_dashboard_keyboard,
    get_admin_back_keyboard,
    get_admin_my_tests_keyboard,
    get_admin_test_stats_keyboard,
)
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
    user = await get_user_by_telegram_id(callback.from_user.id)
    await callback.message.answer("Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu_keyboard(is_adm, user=user))


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
    user = await get_user_by_telegram_id(message.from_user.id)
    await message.answer(f"{'✅' if success else '❌'} {msg}", reply_markup=get_main_menu_keyboard(True, user=user))


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
    user = await get_user_by_telegram_id(message.from_user.id)
    await message.answer(f"{'✅' if success else '❌'} {msg}", reply_markup=get_main_menu_keyboard(True, user=user))


# ==================== MENING TESTLARIM VA STATISTIKA ====================

@router.callback_query(F.data == "adm_my_tests")
async def handle_my_tests(callback: CallbackQuery):
    """Admin yaratgan testlarni inline tugmalar ro'yxati shaklida chiqarish"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan.", show_alert=True)
        return

    admin_user = await get_or_create_user(callback.from_user.id, callback.from_user.full_name)
    tests = await get_admin_tests(admin_user.id)

    if not tests:
        text = (
            "📭 <b>Siz hali birorta ham test yuklamagansiz.</b>\n\n"
            "Yangi test yaratish uchun <b>'🌐 Veb Konstruktorni ochish'</b> tugmasidan foydalaning."
        )
        await callback.answer()
        await callback.message.edit_text(text, reply_markup=get_admin_back_keyboard())
        return

    text = (
        f"📋 <b>SIZ YUKLAGAN TESTLAR ({len(tests)} ta):</b>\n\n"
        f"Statistikasini ko'rish uchun quyidagi test tugmalaridan birini bosing:"
    )
    await callback.answer()
    await callback.message.edit_text(text, reply_markup=get_admin_my_tests_keyboard(tests))


@router.callback_query(F.data.startswith("adm_tstats_"))
async def handle_test_stats(callback: CallbackQuery):
    """Tanlangan testning to'liq natijalari va statistikasini Telegram posti shaklida chiqarish"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan.", show_alert=True)
        return

    try:
        test_id = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer("Noto'g'ri test tanlandi!", show_alert=True)
        return

    admin_user = await get_or_create_user(callback.from_user.id, callback.from_user.full_name)
    stats = await get_test_participants_stats(test_id, admin_user.id)

    if not stats:
        await callback.answer("Test statistikasi topilmadi yoki ruxsat yo'q!", show_alert=True)
        return

    total_part = stats.get("total_participants", 0)
    completed_cnt = stats.get("completed_count", 0)
    cert_cnt = stats.get("certified_count", 0)
    cert_pct = round((cert_cnt / completed_cnt * 100), 1) if completed_cnt > 0 else 0.0

    post_lines = [
        f"📊 <b>NATIJALAR: {stats['test_title']}</b>",
        f"🔑 <b>Test kodi:</b> <code>#{stats['test_code']}</code>",
        f"❓ <b>Savollar:</b> {stats['question_count']} ta | ⏱ <b>Vaqt:</b> {stats['time_limit_min']} daqiqa\n",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"👥 <b>Jami qatnashuvchilar:</b> {total_part} nafar",
        f"✅ <b>Tugatganlar:</b> {completed_cnt} nafar",
        f"📈 <b>O'rtacha ball:</b> {stats['avg_score']:.1f} / 70 ball",
        f"🏆 <b>Eng yuqori ball:</b> {stats['highest_score']:.1f} ball",
        f"🎖 <b>Sertifikat olganlar:</b> {cert_cnt} nafar ({cert_pct}%)",
        f"━━━━━━━━━━━━━━━━━━━━\n",
    ]

    participants = stats.get("participants", [])
    if not participants:
        post_lines.append("ℹ️ <i>Ushbu testni hali birorta ham talabgor topshirmagan.</i>")
    else:
        post_lines.append("🏆 <b>TALABGORLAR NATIJALARI VA REYTINGI:</b>\n")
        # Telegram xabar limiti (4096 belgi) dan oshib ketmasligi uchun top 25 ta chiqariladi
        for p in participants[:25]:
            status_mark = "✅ Sertifikat berildi" if p.get("is_certified") else "❌ Sertifikat berilmadi"
            grade_str = f"({p['grade']})" if p.get('grade') else ""
            phone_str = f" | 📞 {p['phone_number']}" if p.get('phone_number') else ""
            date_str = f" | 📅 {p['finished_at']}" if p.get('finished_at') else ""
            post_lines.append(
                f"<b>{p['rank']}. {p['full_name']}</b> — <b>{p['final_score']:.1f} ball</b> {grade_str}\n"
                f"   └ {status_mark}{phone_str}{date_str}\n"
            )
        if len(participants) > 25:
            post_lines.append(f"<i>...va yana {len(participants) - 25} nafar talabgor (to'liq ro'yxat Veb Konstruktorda).</i>")

    post_text = "\n".join(post_lines)

    await callback.answer()
    await callback.message.edit_text(
        post_text,
        reply_markup=get_admin_test_stats_keyboard(test_id),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("adm_poststats_"))
async def handle_post_stats_to_chat(callback: CallbackQuery, state: FSMContext):
    """Statistika xabarini kanal yoki guruhga post qilish uchun so'rov"""
    test_id = int(callback.data.replace("adm_poststats_", ""))
    await state.update_data(stats_post_test_id=test_id)
    await state.set_state(AdminState.waiting_stats_channel)
    await callback.message.answer(
        "📢 <b>Ushbu test statistikasini qaysi kanal yoki guruhga yubormoqchisiz?</b>\n\n"
        "Kanal/guruh usernamesini kiriting (masalan <code>@kanal_nomi</code> yoki <code>-100...</code>):\n\n"
        "<i>Eslatma: Bot ushbu kanalda xabar yozish huquqiga (adminlikka) ega bo'lishi kerak.</i>\n\n"
        "Bekor qilish uchun /cancel deb yozing.",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AdminState.waiting_stats_channel)
async def process_stats_chat_target(message: Message, state: FSMContext):
    if message.text and message.text.startswith("/cancel"):
        await state.clear()
        await message.answer("Bekor qilindi.")
        return

    data = await state.get_data()
    test_id = data.get("stats_post_test_id")
    target_chat = message.text.strip()
    for prefix in ["https://t.me/", "http://t.me/", "t.me/"]:
        if target_chat.lower().startswith(prefix):
            target_chat = target_chat[len(prefix):]
    if not target_chat.startswith("@") and not target_chat.lstrip("-").isdigit():
        target_chat = f"@{target_chat}"
    if target_chat.lstrip("-").isdigit():
        target_chat = int(target_chat)

    admin_user = await get_or_create_user(message.from_user.id, message.from_user.full_name or "Admin")
    stats = await get_test_participants_stats(test_id, admin_user.id)
    if not stats:
        await message.answer("❌ Test topilmadi yoki statistikani yuborishga ruxsat yo'q.")
        await state.clear()
        return

    from bot.services.report_service import format_telegram_stats_post
    messages = format_telegram_stats_post(stats)
    try:
        for msg in messages:
            await message.bot.send_message(chat_id=target_chat, text=msg, parse_mode="HTML")
        await message.answer(f"✅ Statistika posti muvaffaqiyatli <b>{target_chat}</b> kanaliga yuborildi!", parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❌ Telegramga yuborishda xatolik: {e}\n\nBot ushbu kanalda admin ekanligiga ishonch hosil qiling.")
    finally:
        await state.clear()


