from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.config import settings


def get_admin_dashboard_keyboard(is_super: bool) -> InlineKeyboardMarkup:
    """Admin boshqaruv paneli klaviaturasi"""
    builder = InlineKeyboardBuilder()

    # Veb Konstruktorni ochish tugmasi
    builder.row(
        InlineKeyboardButton(
            text="🌐 Veb Konstruktorni ochish (TMA)",
            web_app=WebAppInfo(url=f"{settings.WEB_APP_URL}/admin")
        )
    )

    if is_super:
        builder.row(
            InlineKeyboardButton(text="👥 Adminlar ro'yxati", callback_data="adm_list_admins"),
            InlineKeyboardButton(text="➕ Admin qo'shish", callback_data="adm_add_admin_prompt"),
        )
        builder.row(
            InlineKeyboardButton(text="➖ Adminni o'chirish", callback_data="adm_remove_admin_prompt"),
        )

    builder.row(
        InlineKeyboardButton(text="📤 Yangi test yuklash (JSON)", callback_data="adm_upload_test_prompt"),
        InlineKeyboardButton(text="📄 Shablon fayl (JSON)", callback_data="adm_get_template"),
    )
    builder.row(
        InlineKeyboardButton(text="📋 Mening testlarim", callback_data="adm_my_tests"),
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Bosh menyu", callback_data="adm_close_panel"),
    )

    return builder.as_markup()


def get_admin_back_keyboard() -> InlineKeyboardMarkup:
    """Admin paneliga qaytish tugmasi"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙 Admin panelga qaytish", callback_data="adm_open_panel"))
    return builder.as_markup()
