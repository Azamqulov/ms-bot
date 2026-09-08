"""
Milliy Sertifikat (Matematika) rasmiy sertifikat generatori.
Talabgor testni yakunlaganida rasmiy Agentlik blankasi asosida
to'liq to'ldirilgan va QR-kodli rasmiy sertifikat rasmini generatsiya qiladi.
"""

import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from PIL import Image, ImageDraw, ImageFont
import qrcode

CERT_TEMPLATE_PATH = Path("bot/assets/certificate_template.jpg")
CERT_OUTPUT_DIR = Path("uploads/certificates")
CERT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def generate_certificate_image(
    attempt_id: int,
    telegram_id: int,
    full_name: str,
    final_score: float,
    grade: Optional[str],
    is_certified: bool,
    subject: str = "Matematika",
    finished_at: Optional[datetime] = None,
    bot_username: str = "ms_matematikabot"
) -> str:
    """
    Rasmiy sertifikat blankasi ustiga barcha ma'lumotlarni joylab
    JPEG rasm fayli sifatida saqlaydi va fayl yo'lini qaytaradi.
    """
    if not CERT_TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Sertifikat shabloni topilmadi: {CERT_TEMPLATE_PATH}")

    base_img = Image.open(CERT_TEMPLATE_PATH).convert("RGBA")
    draw = ImageDraw.Draw(base_img)

    # Shriftlarni cross-platform xavfsiz tanlash (Windows, Linux, Docker, GitHub Actions CI)
    font_candidates = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]
    font_path = next((f for f in font_candidates if os.path.exists(f)), None)

    font_title = None
    font_field = None
    font_meta = None

    if font_path:
        try:
            font_title = ImageFont.truetype(font_path, 18)
            font_field = ImageFont.truetype(font_path, 15)
            font_meta = ImageFont.truetype(font_path, 13)
        except Exception:
            pass

    if not font_title:
        try:
            font_title = ImageFont.truetype("DejaVuSans", 18)
            font_field = ImageFont.truetype("DejaVuSans", 15)
            font_meta = ImageFont.truetype("DejaVuSans", 13)
        except Exception:
            default_font = ImageFont.load_default()
            font_title = default_font
            font_field = default_font
            font_meta = default_font

    # Rasmiy to'q ko'k-qora rang
    text_color = (15, 30, 70, 255)

    # 1. Sertifikat raqami: masalan "MS 001248"
    cert_number = f"MS {attempt_id:06d}"
    draw.text((200, 277), cert_number, fill=text_color, font=font_title)

    # 2. Talabgorning shaxsiy kodi
    personal_code = str(telegram_id)
    draw.text((265, 321), personal_code, fill=text_color, font=font_field)

    # Ism-familiyani ajratish
    parts = [p for p in full_name.strip().split() if p]
    last_name = parts[0].upper() if len(parts) > 0 else ""
    first_name = parts[1].upper() if len(parts) > 1 else ""
    middle_name = " ".join(parts[2:]).upper() if len(parts) > 2 else ""

    # 3. Familiyasi:
    draw.text((265, 356), last_name, fill=text_color, font=font_field)

    # 4. Ismi:
    draw.text((265, 391), first_name, fill=text_color, font=font_field)

    # 5. Otasining ismi:
    draw.text((265, 426), middle_name, fill=text_color, font=font_field)

    # 6. Umumta'lim fani:
    draw.text((265, 488), subject, fill=text_color, font=font_field)

    # 7. Umumiy to'plagan ball:
    score_val = float(final_score or 0.0)
    score_str = f"{score_val:.1f} ball"
    draw.text((265, 523), score_str, fill=text_color, font=font_field)

    # 8. Umumiy ballga nisbatan foiz ko'rsatkichi: (Matematika maksimal 70 ball)
    percent_val = min(100.0, max(0.0, (score_val / 70.0) * 100.0))
    percent_str = f"{percent_val:.1f} %"
    draw.text((380, 558), percent_str, fill=text_color, font=font_field)

    # 9. Sertifikat darajasi:
    grade_str = grade if is_certified and grade else "Talabga javob bermadi"
    draw.text((265, 592), grade_str, fill=text_color, font=font_field)

    # 10. Test sinovi natijasi:
    result_str = "Sertifikat berilsin" if is_certified else "Sertifikat berilmadi"
    draw.text((265, 649), result_str, fill=text_color, font=font_field)

    # 11. Sanalar
    now = finished_at or datetime.now()
    issue_date = now.strftime("%d.%m.%Y")
    if is_certified:
        try:
            exp_date = (now + timedelta(days=365 * 3)).strftime("%d.%m.%Y")
        except Exception:
            exp_date = "3 yil"
    else:
        exp_date = "—"

    draw.text((180, 767), issue_date, fill=text_color, font=font_meta)
    draw.text((600, 767), exp_date, fill=text_color, font=font_meta)

    # 12. QR Code (kulrang qutichaga 100% mos: x=312, y=813, 100x100px)
    qr_data = f"https://t.me/{bot_username}?start=cert_{attempt_id}"
    qr = qrcode.QRCode(box_size=3, border=1)
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
    qr_img = qr_img.resize((100, 100), Image.Resampling.LANCZOS)
    base_img.paste(qr_img, (312, 813))

    # Saqlash
    output_filename = f"cert_{attempt_id}.jpg"
    output_file_path = CERT_OUTPUT_DIR / output_filename
    base_img.convert("RGB").save(str(output_file_path), quality=95)

    return str(output_file_path)
