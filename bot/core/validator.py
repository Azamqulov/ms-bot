"""
Ochiq savollar (O turi, 36-45) javoblarini normalizatsiya qilish va tekshirish.

Foydalanuvchi javoblari turli shakllarda kiritilishi mumkin:
- Butun son: "12", " 12 ", "+12"
- Manfiy son: "-5", "- 5", "-5.0"
- O'nli kasr: "3.5", "3,5", " 3,5 "
- Oddiy kasr: "1/2", " 3/4 "
- Bir nechta qismli xabar: "a) 12 b) -3.5" yoki "a: 4, b: 9"
"""

import re
from fractions import Fraction
from typing import Optional, Dict, Tuple


def parse_numeric_value(raw: str) -> Optional[float]:
    """
    Kiritilgan matndan sonli qiymatni ajratib olishga harakat qiladi.
    Vergulni nuqtaga almashtiradi, oddiy kasrlarni ('3/4') hisoblaydi.
    """
    cleaned = raw.strip().replace(" ", "").replace(",", ".")

    # 1. Oddiy kasr formati (masalan '3/4', '-1/2')
    if "/" in cleaned:
        try:
            frac = Fraction(cleaned)
            return float(frac)
        except (ValueError, ZeroDivisionError):
            pass

    # 2. Oddiy float/int formati
    try:
        return float(cleaned)
    except ValueError:
        return None


def normalize_text_answer(raw: str) -> str:
    """Matnli javobni standart ko'rinishga keltirish"""
    # Kichik harfga o'tkazish, probellarni qisqartirish
    text = raw.strip().lower()
    text = re.sub(r"\s+", " ", text)
    text = text.replace(",", ".")
    return text


def check_open_answer(user_ans: str, correct_ans: str, tolerance: float = 1e-3) -> bool:
    """
    Foydalanuvchi javobini to'g'ri javob bilan solishtirish.
    Sonli qiymat bo'lsa - tolerantlik bilan solishtiriladi (masalan 0.5 == 1/2).
    Aks holda - tozalangan matn bo'yicha solishtiriladi.
    """
    if not user_ans or not correct_ans:
        return False

    u_clean = user_ans.strip()
    c_clean = correct_ans.strip()

    # Bir nechta muqobil to'g'ri javoblar bo'lsa (masalan "3.5; 7/2")
    correct_variants = [v.strip() for v in c_clean.split(";") if v.strip()]
    if not correct_variants:
        correct_variants = [c_clean]

    u_num = parse_numeric_value(u_clean)

    for variant in correct_variants:
        c_num = parse_numeric_value(variant)

        if u_num is not None and c_num is not None:
            # Ikkalasi ham son bo'lsa
            if abs(u_num - c_num) <= tolerance:
                return True
        else:
            # Matnli solishtirish
            if normalize_text_answer(u_clean) == normalize_text_answer(variant):
                return True

    return False


def parse_subparts_input(raw_text: str) -> Dict[str, str]:
    """
    Foydalanuvchi bitta xabarda 'a' va 'b' bandlariga birdan javob bersa:
    Masalan:
      "a) 12 b) 3.5"
      "a: 12\nb: 3.5"
      "a = 12, b = 3.5"
    
    Qaytaradi:
      {'a': '12', 'b': '3.5'}
    Agar format topilmasa, butun matnni bitta javob deb qabul qiladi.
    """
    result: Dict[str, str] = {}
    cleaned = raw_text.strip()

    # a) va b) naqshini qidirish
    pattern = r"(?:^|\s|\n)(?:a[\)\:\=]|\(a\))\s*([^\n\,bB]+?)(?=(?:\s|\n)+(?:b[\)\:\=]|\(b\))|$)"
    match_a = re.search(pattern, cleaned, flags=re.IGNORECASE)

    pattern_b = r"(?:^|\s|\n)(?:b[\)\:\=]|\(b\))\s*([^\n\,]+)"
    match_b = re.search(pattern_b, cleaned, flags=re.IGNORECASE)

    if match_a:
        result["a"] = match_a.group(1).strip()
    if match_b:
        result["b"] = match_b.group(1).strip()

    return result
