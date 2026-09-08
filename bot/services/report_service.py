"""
Test natijalarini chiroyli formatda taqdim etish servisi (Report Service).
"""

import html
from datetime import datetime
from typing import List, Dict, Any, Optional
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
            "Sinovdan o'tish uchun asosiy menyudan <b>'🚀 Javobni tekshirish'</b> tugmasini bosing!"
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


def format_telegram_stats_post(stats: Dict[str, Any]) -> List[str]:
    """
    Test statistikasi va qatnashuvchilar ro'yxatini Telegram post xabarlari formatida tayyorlaydi.
    Format talabi:
    Ism Familiya ------ nechta to'g'ri topgani, to'plagan bali va darajasi (✅ berildi / ❌ berilmadi)
    Telegram 4096 belgi chegarasi xavfsiz hisobga olingan.
    """
    total_part = stats.get("total_participants", 0)
    completed_cnt = stats.get("completed_count", 0)
    cert_cnt = stats.get("certified_count", 0)
    cert_pct = round((cert_cnt / completed_cnt * 100), 1) if completed_cnt > 0 else 0.0

    test_title = html.escape(str(stats.get("test_title", "Milliy Sertifikat Testi")))
    test_code = html.escape(str(stats.get("test_code", "")))
    q_count = stats.get("question_count", 45)
    time_limit = stats.get("time_limit_min", 150)
    avg_score = stats.get("avg_score", 0.0)
    highest_score = stats.get("highest_score", 0.0)

    header = (
        f"📊 <b>TEST NATIJALARI VA STATISTIKASI</b>\n\n"
        f"🏷 <b>Test:</b> {test_title}\n"
        f"🔑 <b>Test kodi:</b> <code>#{test_code}</code>\n"
        f"❓ <b>Savollar soni:</b> {q_count} ta | ⏱ <b>Vaqt:</b> {time_limit} daqiqa\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 <b>Qatnashuvchilar:</b> {total_part} ta\n"
        f"📈 <b>O'rtacha ball:</b> {avg_score:.1f} / 75 ball\n"
        f"🏆 <b>Eng yuqori ball:</b> {highest_score:.1f} ball\n"
        f"📜 <b>Sertifikat olganlar:</b> {cert_cnt} ta ({cert_pct}%)\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🏆 <b>TALABGORLAR VA NATIJALAR:</b>\n\n"
    )

    participants = stats.get("participants", [])
    if not participants:
        return [header + "ℹ️ <i>Ushbu testni hali birorta ham talabgor topshirmagan.</i>"]

    lines = []
    for p in participants:
        rank = p.get("rank", 1)
        name = html.escape(str(p.get("full_name", "Noma'lum")))
        raw_score = p.get("raw_score", 0)
        final_score = p.get("final_score", 0.0)
        is_cert = p.get("is_certified", False)
        grade = html.escape(str(p.get("grade", ""))) if p.get("grade") else ""

        if is_cert:
            grade_label = f"{grade} (✅ Sertifikat berildi)" if grade else "✅ Sertifikat berildi"
        else:
            grade_label = "❌ Sertifikat berilmadi"

        line = f"<b>{rank}. {name}</b> ------ 🎯 {raw_score} ta to'g'ri, ⭐️ {final_score:.1f} ball, {grade_label}"
        lines.append(line)

    messages = []
    current_chunk = header
    for line in lines:
        if len(current_chunk) + len(line) + 2 > 3900:
            messages.append(current_chunk.strip())
            current_chunk = line + "\n"
        else:
            current_chunk += line + "\n"

    if current_chunk.strip():
        messages.append(current_chunk.strip())

    return messages

