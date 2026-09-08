"""
Tests for the Modular Rasch Evaluation Engine (bot/core/rasch_engine.py)
"""

import os
import sys

# Loyiha ildiz papkasini sys.path ga qo'shish
_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

try:
    import pytest
except ImportError:
    pytest = None

from bot.core.rasch_engine import (
    calculateProbability,
    estimateItemDifficulty,
    convertRaschToScore,
    getCertificateLevel,
    calculateRaschAbility,
    DEFAULT_DIFFICULTY_MAP,
)


def test_calculate_probability_symmetry():
    # Theta == b bo'lganda ehtimollik aniq 0.5 bo'lishi shart
    assert abs(calculateProbability(0.0, 0.0) - 0.5) < 1e-6
    assert abs(calculateProbability(1.2, 1.2) - 0.5) < 1e-6
    assert abs(calculateProbability(-2.0, -2.0) - 0.5) < 1e-6

    # Qobiliyat qiyinlikdan yuqori bo'lsa ehtimollik > 0.5
    assert calculateProbability(1.0, 0.0) > 0.5
    # Qobiliyat qiyinlikdan past bo'lsa ehtimollik < 0.5
    assert calculateProbability(-1.0, 0.0) < 0.5

    # Overflow/underflow himoyasi
    assert calculateProbability(100.0, 0.0) == 1.0
    assert calculateProbability(-100.0, 0.0) == 0.0


def test_estimate_item_difficulty_auto():
    # Auto difficulty ON:
    # 1-15 savollar -> easy (b = -1.0)
    diff_name, b_val, auto_flag = estimateItemDifficulty(1, "Y", auto_difficulty=True)
    assert diff_name == "easy"
    assert b_val == -1.0
    assert auto_flag is True

    diff_name, b_val, auto_flag = estimateItemDifficulty(15, "Y", auto_difficulty=True)
    assert diff_name == "easy"
    assert b_val == -1.0

    # 16-35 savollar -> medium (b = 0.0)
    diff_name, b_val, auto_flag = estimateItemDifficulty(16, "Y", auto_difficulty=True)
    assert diff_name == "medium"
    assert b_val == 0.0

    diff_name, b_val, auto_flag = estimateItemDifficulty(35, "GROUPED", auto_difficulty=True)
    assert diff_name == "medium"
    assert b_val == 0.0

    # 36-45 savollar -> hard (b = +1.0)
    diff_name, b_val, auto_flag = estimateItemDifficulty(36, "O", auto_difficulty=True)
    assert diff_name == "hard"
    assert b_val == 1.0

    diff_name, b_val, auto_flag = estimateItemDifficulty(45, "O", auto_difficulty=True)
    assert diff_name == "hard"
    assert b_val == 1.0


def test_estimate_item_difficulty_manual():
    # Auto difficulty OFF:
    # Admin qo'lda easy, medium, hard yoki float b_i kiritganda
    diff_name, b_val, auto_flag = estimateItemDifficulty(
        order_no=5, question_type="Y", auto_difficulty=False, manual_difficulty="hard"
    )
    assert diff_name == "hard"
    assert b_val == 1.0
    assert auto_flag is False

    # Real float b_i parametri (masalan, empirik b_i = 0.65)
    diff_name, b_val, auto_flag = estimateItemDifficulty(
        order_no=10, question_type="Y", auto_difficulty=False, manual_difficulty=0.65
    )
    assert diff_name == 0.65
    assert b_val == 0.65
    assert auto_flag is False


def test_convert_rasch_to_score_and_calibration():
    # Standart kalibrlash: theta = 0.0 -> 50.0 ball
    assert convertRaschToScore(0.0) == 50.0

    # Yuqori qobiliyat (theta = 2.5) -> 72.0 ball
    score_high = convertRaschToScore(2.5)
    assert score_high >= 70.0

    # Past qobiliyat (theta = -2.5) -> 28.0 ball
    score_low = convertRaschToScore(-2.5)
    assert score_low < 30.0

    # Min va max chegaralari (0.0 va 75.0)
    assert convertRaschToScore(10.0) == 75.0
    assert convertRaschToScore(-10.0) == 0.0


def test_get_certificate_level():
    # Rasmiy Milliy sertifikat darajalari:
    # 70+ -> A+
    assert getCertificateLevel(72.5) == ("A+", True)
    assert getCertificateLevel(70.0) == ("A+", True)

    # 65–69.9 -> A
    assert getCertificateLevel(69.9) == ("A", True)
    assert getCertificateLevel(65.0) == ("A", True)

    # 60–64.9 -> B+
    assert getCertificateLevel(64.5) == ("B+", True)
    assert getCertificateLevel(60.0) == ("B+", True)

    # 55–59.9 -> B
    assert getCertificateLevel(58.0) == ("B", True)
    assert getCertificateLevel(55.0) == ("B", True)

    # 50–54.9 -> C+
    assert getCertificateLevel(54.0) == ("C+", True)
    assert getCertificateLevel(50.0) == ("C+", True)

    # 46–49.9 -> C
    assert getCertificateLevel(49.0) == ("C", True)
    assert getCertificateLevel(46.0) == ("C", True)

    # < 46 -> Sertifikat darajasi yo'q
    assert getCertificateLevel(45.9) == ("Sertifikat darajasi yo'q", False)
    assert getCertificateLevel(20.0) == ("Sertifikat darajasi yo'q", False)


def test_calculate_rasch_ability_45_questions():
    # 45 ta savol uchun simulyatsiya:
    # 1 dan 45 gacha savollar
    answers_data = []
    for i in range(1, 46):
        # 30 ta to'g'ri javob
        is_corr = (i <= 30)
        answers_data.append({
            "questionId": i,
            "correctAnswer": "A",
            "userAnswer": "A" if is_corr else "B",
            "isCorrect": is_corr,
            "difficulty": "easy" if i <= 15 else ("medium" if i <= 35 else "hard")
        })

    res = calculateRaschAbility(answers_data, auto_difficulty=True)

    assert res.total_questions == 45
    assert res.correct_count == 30
    assert res.wrong_count == 15
    assert res.theta > 0.0  # 30/45 > 50% bo'lgani uchun qobiliyat o'rtachadan yuqori
    assert res.final_score > 50.0
    assert res.is_certified is True
    assert "simulyatsion" in res.disclaimer.lower()


def test_rasch_difficulty_sensitivity():
    """
    Rasch modelining muhim xossasi:
    1) Oddiy chiziqli proporsiya (30 * 70 / 45 = 46.67) bilan hisoblanmaydi.
       Rasch logistik konvertatsiyasi orqali 30/45 balli ~56+ ball (B daraja) beradi.
    2) Agar topshiruvchiga berilgan savollar qiyinroq bo'lsa (masalan qiyin variant),
       bir xil 20 ta to'g'ri javob uchun qiyinroq testdagi theta yuqoriroq bo'ladi.
    """
    # Oddiy proporsiyadan farqi:
    res30 = calculateRaschAbility([
        {"questionId": i, "isCorrect": (i <= 30)} for i in range(1, 46)
    ])
    simple_linear_score = 30.0 * 70.0 / 45.0  # 46.67
    # Rasch modelida 30/45 to'plagan talabgorning bali oddiy 46.67 emas, ancha yuqori bo'ladi
    assert res30.final_score > simple_linear_score

    # Qiyinroq savollar to'plami vs Osonroq savollar to'plami:
    # 1-topshiruvchi qiyin savollar to'plamini (b = +1.0) yechdi, 20 ta to'g'ri
    items_hard = [
        {"questionId": i, "isCorrect": (i <= 20), "difficulty": 1.0}
        for i in range(1, 46)
    ]
    # 2-topshiruvchi oson savollar to'plamini (b = -1.0) yechdi, 20 ta to'g'ri
    items_easy = [
        {"questionId": i, "isCorrect": (i <= 20), "difficulty": -1.0}
        for i in range(1, 46)
    ]

    res_hard = calculateRaschAbility(items_hard, auto_difficulty=False)
    res_easy = calculateRaschAbility(items_easy, auto_difficulty=False)

    assert res_hard.correct_count == 20
    assert res_easy.correct_count == 20
    # Qiyin testda 20 ta to'g'ri topgan talabgorning qobiliyati oson testdagidan ancha yuqori
    assert res_hard.theta > res_easy.theta
    assert res_hard.final_score > res_easy.final_score


if __name__ == "__main__":
    print("Running Rasch Engine tests...")
    test_calculate_probability_symmetry()
    print("  [OK] test_calculate_probability_symmetry")
    test_estimate_item_difficulty_auto()
    print("  [OK] test_estimate_item_difficulty_auto")
    test_estimate_item_difficulty_manual()
    print("  [OK] test_estimate_item_difficulty_manual")
    test_convert_rasch_to_score_and_calibration()
    print("  [OK] test_convert_rasch_to_score_and_calibration")
    test_get_certificate_level()
    print("  [OK] test_get_certificate_level")
    test_calculate_rasch_ability_45_questions()
    print("  [OK] test_calculate_rasch_ability_45_questions")
    test_rasch_difficulty_sensitivity()
    print("  [OK] test_rasch_difficulty_sensitivity")
    print("\n>>> ALL 7 RASCH ENGINE TEST SUITES PASSED 100%! <<<")

