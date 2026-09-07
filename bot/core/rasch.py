"""
RASH (Item Response Theory - IRT) Baholash Dvigateli
Milliy Sertifikat — Matematika formati uchun.

1PL (Bir parametrli logistik) Rasch modeli:
P(X_ni = 1 | theta_n, b_i) = 1 / (1 + exp(-(theta_n - b_i)))

Bu yerda:
- theta_n: Talabgorning matematik qobiliyat darajasi (latent trait)
- b_i: Savol (yoki subsavol)ning qiyinlik parametri (difficulty)
- r: To'g'ri javoblar soni (xom ball)
"""

from dataclasses import dataclass
from typing import List, Optional
import math


@dataclass
class RaschItem:
    """Bitta baholash bandi (savol yoki ochiq savolning alohida qismi)"""
    item_id: str
    difficulty_b: float  # Odatda -3.0 dan +3.0 gacha


@dataclass
class RaschResult:
    """Rasch baholash natijasi"""
    raw_score: int          # To'g'ri javoblar soni
    total_items: int        # Umumiy baholanadigan bandlar soni
    theta: float            # Qobiliyat darajasi (logislarda, odatda -3.5 dan +3.5 gacha)
    standard_error: float   # Baholashning standart xatosi SE(theta)
    final_score: float      # Rasmiy 0-75 ball shkalasidagi yakuniy ball
    grade: str              # Rasmiy daraja: A+, A, B+, B, C+, C yoki "Sertifikat berilmaydi"
    is_certified: bool      # Sertifikat olgan/olmaganligi (ball >= 46.0)


def probability(theta: float, b: float) -> float:
    """Rasch logistik ehtimollik funksiyasi: P(correct | theta, b)"""
    diff = theta - b
    # Overflow/underflow himoyasi
    if diff > 30.0:
        return 1.0
    if diff < -30.0:
        return 0.0
    return 1.0 / (1.0 + math.exp(-diff))


def estimate_theta_mle(
    items: List[RaschItem],
    correct_flags: List[bool],
    max_iter: int = 50,
    tolerance: float = 1e-5
) -> tuple[float, float]:
    """
    Maximum Likelihood Estimation (MLE) orqali theta (qobiliyat) ni hisoblash.
    Newton-Raphson algoritmi qo'llaniladi.
    Ekstremal natijalar (barchasi to'g'ri yoki barchasi xato) uchun Bayes tuzatishi beriladi.
    
    Qaytaradi:
        (theta, standard_error)
    """
    n_items = len(items)
    if n_items == 0:
        return 0.0, 1.0

    raw_score = sum(1 for c in correct_flags if c)

    # Ekstremal ballarni qayta ishlash (Bayes/Winsorized smoothing)
    # Agar barchasi xato bo'lsa (r=0) yoki barchasi to'g'ri bo'lsa (r=n_items),
    # sof MLE cheksizlikka ketadi (+inf yoki -inf).
    adjusted_score = float(raw_score)
    if raw_score == 0:
        adjusted_score = 0.3
    elif raw_score == n_items:
        adjusted_score = n_items - 0.3

    # Boshlang'ich theta qiymati (oddiy logit xom ball asosida)
    proportion = adjusted_score / n_items
    initial_theta = math.log(proportion / (1.0 - proportion))
    theta = max(min(initial_theta, 4.0), -4.0)

    # Newton-Raphson iteratsiyasi
    for _ in range(max_iter):
        f_theta = 0.0   # Sum(P_i) - r
        info_theta = 0.0 # Sum(P_i * (1 - P_i)) = f'(theta) = Fisher Information

        for item in items:
            p_i = probability(theta, item.difficulty_b)
            f_theta += p_i
            info_theta += p_i * (1.0 - p_i)

        f_theta -= adjusted_score

        # Yaqinlashish sharti
        if abs(f_theta) < tolerance:
            break

        if info_theta < 1e-7:
            # Agar axborot juda kichik bo'lsa, qadamni cheklaymiz
            break

        delta = f_theta / info_theta
        # Qadamni haddan tashqari sakrab ketishdan himoyalash
        delta = max(min(delta, 1.0), -1.0)
        theta -= delta

        # Chegaralarni nazorat qilish
        theta = max(min(theta, 5.0), -5.0)

    # Standart xato SE(theta) = 1 / sqrt(I(theta))
    final_info = sum(
        probability(theta, item.difficulty_b) * (1.0 - probability(theta, item.difficulty_b))
        for item in items
    )
    se = 1.0 / math.sqrt(final_info) if final_info > 1e-7 else 1.0

    return round(theta, 3), round(se, 3)


def convert_theta_to_score(theta: float) -> float:
    """
    Theta (-3.5 dan +3.5 gacha) qiymatini rasmiy 0-75 ball shkalasiga o'tkazish.
    
    Standartlashtirish qoidasi:
    - O'rtacha qobiliyat (theta = 0.0) -> ~50.0 ball (C+ daraja chegarasi)
    - Yuqori qobiliyat (theta = +2.5) -> ~72.0 ball (A+ daraja)
    - Past qobiliyat (theta = -2.5) -> ~28.0 ball
    - Maksimal: 75.0 ball, Minimal: 0.0 ball
    """
    # Chiziqli konvertatsiya: Score = 50.0 + 8.8 * theta
    score = 50.0 + 8.8 * theta
    # 0.0 va 75.0 oralig'ida cheklash
    score = max(0.0, min(75.0, score))
    return round(score, 1)


def determine_grade(score: float) -> tuple[str, bool]:
    """
    75 ballik shkala asosida Milliy Sertifikat darajasini aniqlash:
    - A+: 70.0 - 75.0
    - A : 65.0 - 69.9
    - B+: 60.0 - 64.9
    - B : 55.0 - 59.9
    - C+: 50.0 - 54.9
    - C : 46.0 - 49.9
    - Sertifikat berilmaydi: < 46.0
    
    Qaytaradi:
        (grade_str, is_certified)
    """
    if score >= 70.0:
        return "A+", True
    elif score >= 65.0:
        return "A", True
    elif score >= 60.0:
        return "B+", True
    elif score >= 55.0:
        return "B", True
    elif score >= 50.0:
        return "C+", True
    elif score >= 46.0:
        return "C", True
    else:
        return "Sertifikat berilmaydi", False


def evaluate_attempt(
    items: List[RaschItem],
    user_answers_correct: List[bool]
) -> RaschResult:
    """
    Foydalanuvchining butun test urinishini RASH modeli asosida to'liq baholash.
    """
    raw_score = sum(1 for c in user_answers_correct if c)
    total_items = len(items)

    theta, se = estimate_theta_mle(items, user_answers_correct)
    final_score = convert_theta_to_score(theta)
    grade, is_certified = determine_grade(final_score)

    return RaschResult(
        raw_score=raw_score,
        total_items=total_items,
        theta=theta,
        standard_error=se,
        final_score=final_score,
        grade=grade,
        is_certified=is_certified
    )
