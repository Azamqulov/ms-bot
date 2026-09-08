try:
    import pytest
except ImportError:
    pytest = None
from bot.core.rasch import (
    RaschItem,
    probability,
    estimate_theta_mle,
    convert_theta_to_score,
    determine_grade,
    evaluate_attempt,
)


def test_probability_symmetry():
    # Theta == b bo'lganda ehtimollik 0.5 bo'lishi kerak
    assert abs(probability(0.0, 0.0) - 0.5) < 1e-6
    assert abs(probability(1.5, 1.5) - 0.5) < 1e-6
    # Theta > b bo'lganda ehtimollik > 0.5
    assert probability(1.0, 0.0) > 0.5
    # Theta < b bo'lganda ehtimollik < 0.5
    assert probability(-1.0, 0.0) < 0.5


def test_estimate_theta_mle_average():
    # 10 ta o'rtacha savol (b = 0)
    items = [RaschItem(item_id=str(i), difficulty_b=0.0) for i in range(10)]
    # 5 ta to'g'ri, 5 ta xato (aniq yarmi)
    correct_flags = [True] * 5 + [False] * 5
    theta, se = estimate_theta_mle(items, correct_flags)
    # Theta 0.0 ga juda yaqin bo'lishi kerak
    assert abs(theta - 0.0) < 0.1
    assert se > 0.0


def test_estimate_theta_extreme_cases():
    # Hech qanday to'g'ri javob yo'q (0 ta to'g'ri)
    items = [RaschItem(item_id=str(i), difficulty_b=0.0) for i in range(10)]
    all_wrong = [False] * 10
    theta_wrong, _ = estimate_theta_mle(items, all_wrong)
    assert theta_wrong < -2.0  # Aniq past qobiliyat

    # Barcha javoblar to'g'ri (10 ta to'g'ri)
    all_right = [True] * 10
    theta_right, _ = estimate_theta_mle(items, all_right)
    assert theta_right > 2.0  # Aniq yuqori qobiliyat


def test_convert_theta_to_score():
    assert convert_theta_to_score(0.0) == 50.0
    assert convert_theta_to_score(2.5) >= 70.0
    assert convert_theta_to_score(-3.0) < 30.0
    # Clamping tekshiruvi (0 va 75 chegaralari)
    assert convert_theta_to_score(10.0) == 75.0
    assert convert_theta_to_score(-10.0) == 0.0


def test_determine_grade():
    assert determine_grade(72.5) == ("A+", True)
    assert determine_grade(67.0) == ("A", True)
    assert determine_grade(62.0) == ("B+", True)
    assert determine_grade(56.0) == ("B", True)
    assert determine_grade(51.0) == ("C+", True)
    assert determine_grade(47.0) == ("C", True)
    assert determine_grade(45.5) == ("Sertifikat berilmaydi", False)


def test_evaluate_attempt_55_items():
    # 55 ta bandli real test simulyatsiyasi
    items = [
        RaschItem(item_id=f"q_{i}", difficulty_b=(i - 27) * 0.1)
        for i in range(55)
    ]
    # 45 ta to'g'ri javob (yaxshi natija)
    user_answers = [True] * 45 + [False] * 10
    result = evaluate_attempt(items, user_answers)

    assert result.raw_score == 45
    assert result.total_items == 55
    assert result.theta > 0.5
    assert result.final_score >= 55.0
    assert result.is_certified is True
