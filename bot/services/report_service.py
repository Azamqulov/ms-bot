"""
Test natijalarini chiroyli formatda taqdim etish servisi (Report Service).
"""

from datetime import datetime
from typing import List
from bot.database.models import Attempt, User
from bot.core.rasch import RaschResult


def format_duration(seconds: int) -> str:
    """Soniyalarni soat va daqiqaga o'tkazish"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours} soat {minutes} daqiqa"
    elif minutes > 0:
        return f"{minutes} daqiqa {secs} soniya"
    else:
        return f"{secs} soniya"


def get_grade_badge(grade: str) -> str:
    badges = {
        "A+": "🏆 A+ (Eng yuqori daraja — 100% imtiyoz)",
        "A": "🥇 A (A'lo daraja — maksimal ball)",
        "B+": "🥈 B+ (Juda yaxshi daraja)",
        "B": "🥉 B (Yaxshi daraja)",
        "C+": "🎖 C+ (Qoniqarli daraja)",
        "C": "🎗 C (Minimal o'tish darajasi)",
        "Sertifikat berilmaydi": "❌ Sertifikat berilmaydi (Minimal 46 ball)",
    }
    return badges.get(grade, grade)


def generate_result_report(user: User, attempt: Attempt, rasch_result: RaschResult) -> str:
    """Yakunlangan test uchun batafsil hisobot matni"""
    duration_sec = 0
    if attempt.finished_at and attempt.started_at:
        duration_sec = int((attempt.finished_at - attempt.started_at).total_seconds())

    duration_str = format_duration(max(1, duration_sec))
    grade_badge = get_grade_badge(rasch_result.grade)

    status_icon = "🎉" if rasch_result.is_certified else "⚠️"
    status_text = (
        "<b>TABRIKLAYMIZ!</b> Siz Milliy Sertifikat darajasini qo'lga kiritdingiz!"
        if rasch_result.is_certified
        else "Afsuski, bu safar sertifikat olish uchun ball yetarli bo'lmadi. O'rganishda davom eting!"
    )

    report = (
        f"{status_icon} <b>MILLIY SERTIFIKAT (MATEMATIKA) MOCK TEST NATIJASI</b>\n\n"
        f"👤 <b>Talabgor:</b> {user.full_name}\n"
        f"📅 <b>Sana:</b> {attempt.finished_at.strftime('%Y-%m-%d %H:%M') if attempt.finished_at else 'Hozir'}\n"
        f"⏱ <b>Sarflangan vaqt:</b> {duration_str}\n\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"🎯 <b>YAKUNIY BALL:</b> <code>{rasch_result.final_score:.1f} / 75.0</code>\n"
        f"🎖 <b>DARAJA:</b> <b>{grade_badge}</b>\n"
        f"📊 <b>Xom ball (To'g'ri bandlar):</b> <code>{rasch_result.raw_score} / {rasch_result.total_items}</code>\n"
        f"🧠 <b>Qobiliyat ko'rsatkichi (θ):</b> <code>{rasch_result.theta:+.2f} logit</code> (SE: ±{rasch_result.standard_error:.2f})\n"
        f"➖➖➖➖➖➖➖➖➖➖\n\n"
        f"{status_text}\n\n"
        f"💡 <i>Natijalar rasmiy DTM RASH (IRT — Item Response Theory) 1PL modeli asosida hisoblandi.</i>\n"
        f"Qayta urinish uchun pastdagi tugmani bosing!"
    )
    return report


def generate_history_report(attempts: List[Attempt]) -> str:
    """Foydalanuvchining o'tgan barcha natijalari ro'yxati"""
    if not attempts:
        return (
            "📭 <b>Siz hali hech qaysi testni yakunlamagansiz.</b>\n\n"
            "Sinovdan o'tish uchun asosiy menyudan <b>'📝 Test topshirish'</b> tugmasini bosing!"
        )

    lines = ["📊 <b>SIZNING NATIJALARINGIZ TARIXI:</b>\n"]
    for idx, att in enumerate(attempts[:10], start=1):
        dt_str = att.finished_at.strftime("%d.%m.%Y") if att.finished_at else "-"
        score = att.final_score if att.final_score is not None else 0.0
        grade = att.grade or "Noma'lum"
        raw = att.raw_score

        icon = "🟢" if att.is_certified else "🔴"
        lines.append(
            f"{idx}. {icon} <b>{dt_str}</b> — Ball: <code>{score:.1f}/75</code> | Daraja: <b>{grade}</b> ({raw} to'g'ri)"
        )

    lines.append("\n💡 <i>Har bir test sizning bilim darajangizni oshirishga xizmat qiladi.</i>")
    return "\n".join(lines)


def generate_teacher_notification(
    student: User,
    test_title: str,
    test_code: str,
    attempt: Attempt,
    rasch_result: RaschResult
) -> str:
    """Test yaratgan o'qituvchi/muallif uchun yangi natija haqida bildirishnoma matni"""
    duration_sec = 0
    if attempt.finished_at and attempt.started_at:
        duration_sec = int((attempt.finished_at - attempt.started_at).total_seconds())

    duration_str = format_duration(max(1, duration_sec))
    grade_badge = get_grade_badge(rasch_result.grade)

    user_tg = f"@{student.username}" if student.username else f"ID: {student.telegram_id}"
    phone = student.phone_number or "Kiritilmagan"

    return (
        f"📬 <b>YANGI TEST NATIJASI QABUL QILINDI!</b>\n\n"
        f"📝 <b>Test:</b> {test_title} (Kod: <code>{test_code}</code>)\n"
        f"👤 <b>Talabgor (O'quvchi):</b> {student.full_name}\n"
        f"📱 <b>Telefon raqami:</b> <code>{phone}</code>\n"
        f"🆔 <b>Telegram:</b> {user_tg}\n"
        f"⏱ <b>Sarflangan vaqt:</b> {duration_str}\n"
        f"📅 <b>Sana:</b> {attempt.finished_at.strftime('%Y-%m-%d %H:%M') if attempt.finished_at else datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"🎯 <b>YAKUNIY BALL:</b> <code>{rasch_result.final_score:.1f} / 75.0</code>\n"
        f"🎖 <b>DARAJA:</b> <b>{grade_badge}</b>\n"
        f"📊 <b>To'g'ri javoblar:</b> <code>{rasch_result.raw_score} / {rasch_result.total_items}</code> ta\n"
        f"🧠 <b>Qobiliyat (θ):</b> <code>{rasch_result.theta:+.2f} logit</code>\n"
        f"➖➖➖➖➖➖➖➖➖➖\n\n"
        f"💡 <i>Ushbu testni siz yaratganingiz uchun talabgorning to'liq natijasi sizga yuborildi.</i>"
    )
