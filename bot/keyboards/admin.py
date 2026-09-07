from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.config import settings


def get_admin_dashboard_keyboard(is_super: bool) -> InlineKeyboardMarkup:
    """Admin boshqaruv paneli klaviaturasi"""
    builder = InlineKeyboardBuilder()

    # Admin URL: GitHub Pages dan HTML, API so'rovlari esa API_SERVER_URL ga
    base_admin_url = (
        f"{settings.WEB_APP_URL.rstrip('/')}/web/admin.html"
        if "github.io" in settings.WEB_APP_URL
        else f"{settings.WEB_APP_URL.rstrip('/')}/admin"
    )

    # Agar API_SERVER_URL belgilangan bo'lsa, ?api= parametrini qo'shamiz
    if settings.API_SERVER_URL and "github.io" in settings.WEB_APP_URL:
        import urllib.parse
        api_clean = settings.API_SERVER_URL.rstrip('/')
        delimiter = "&" if "?" in base_admin_url else "?"
        admin_url = f"{base_admin_url}{delimiter}api={urllib.parse.quote(api_clean, safe=':/')}"
    else:
        admin_url = base_admin_url

    builder.row(
        InlineKeyboardButton(
            text="🌐 Veb Konstruktorni ochish (TMA)",
            web_app=WebAppInfo(url=admin_url)
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
