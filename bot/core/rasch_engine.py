"""
Milliy Sertifikat — Matematika: Rasch Modeli (1PL IRT) Baholash Dvigateli
=======================================================================
Ushbu modul O'zbekiston Milliy sertifikat imtihoni (Matematika) formati
uchun 45 ta topshiriq asosida Rasch o'lchov modelini (1-Parameter Logistic IRT)
amalga oshiradi.

DIQQAT:
Ushbu tizim Milliy sertifikatga o'xshash simulyatsion baholash vositasi bo'lib,
BBA (Bilim va malakalarni baholash agentligi) rasmiy baholash tizimi yoki
rasmiy parametrlari hisoblanmaydi.

Rasch ehtimollik modeli:
P(X_ni = 1 | theta_n, b_i) = exp(theta_n - b_i) / (1 + exp(theta_n - b_i))

Modul funksiyalari:
- calculateProbability(theta, b)
- estimateItemDifficulty(question_info, auto_difficulty)
- calculateRaschAbility(answers_data)
- convertRaschToScore(theta, calibration_params)
- getCertificateLevel(final_score)
"""

from __future__ import annotations
import math
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field


# Boshlang'ich simulyatsion qiyinlik parametrlari (b_i logit)
DEFAULT_DIFFICULTY_MAP: Dict[str, float] = {
    "easy": -1.0,
    "medium": 0.0,
    "hard": 1.0,
}

# Standart kalibrlash parametrlari (logit -> 0-75 ball shkalasi)
DEFAULT_CALIBRATION_PARAMS: Dict[str, float] = {
    "base_score": 50.0,     # theta = 0 bo'lgandagi ball (C+ chegarasi)
    "scale_factor": 8.8,    # 1 logit uchun ball ko'paytuvchisi
    "min_score": 0.0,
    "max_score": 75.0,
}


@dataclass
class QuestionEvaluationItem:
    """Bitta savol ma'lumoti va uning baholash holati"""
    question_id: Union[int, str]
    correct_answer: str
    user_answer: str
    is_correct: bool
    difficulty: Union[str, float]       # 'easy', 'medium', 'hard' yoki float b_i
    numerical_b: float                  # Hisoblashda ishlatiladigan b_i qiymati
    auto_assigned: bool = False         # Qiyinlik avtomatik belgilandimi?


@dataclass
class RaschEvaluationResult:
    """Rasch modeli bo'yicha to'liq baholash natijasi"""
    total_questions: int                # Umumiy savollar soni (masalan, 45)
    correct_count: int                  # To'g'ri javoblar soni (X / 45)
    wrong_count: int                    # Noto'g'ri javoblar soni (X / 45)
    theta: float                        # Rasch ability (qobiliyat) darajasi (logit)
    standard_error: float               # O'lchovning standart xatosi SE(theta)
    final_score: float                  # Kalibrlangan yakuniy ball (0 - 75)
    certificate_level: str              # A+, A, B+, B, C+, C yoki "Sertifikat darajasi yo'q"
    is_certified: bool                  # Sertifikat olganmi (ball >= 46.0)
    items: List[QuestionEvaluationItem] = field(default_factory=list)
    disclaimer: str = (
        "Eslatma: Ushbu baholash Milliy sertifikat metodikasiga o'xshash simulyatsion "
        "model hisoblanadi va BBA rasmiy natijasi deb talqin qilinmaydi."
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_questions": self.total_questions,
            "correct_count": self.correct_count,
            "wrong_count": self.wrong_count,
            "theta": self.theta,
            "standard_error": self.standard_error,
            "final_score": self.final_score,
            "certificate_level": self.certificate_level,
            "is_certified": self.is_certified,
            "disclaimer": self.disclaimer,
            "items": [
                {
                    "questionId": it.question_id,
                    "correctAnswer": it.correct_answer,
                    "userAnswer": it.user_answer,
                    "isCorrect": it.is_correct,
                    "difficulty": it.difficulty,
                    "numericalB": it.numerical_b,
                    "autoAssigned": it.auto_assigned,
                }
                for it in self.items
            ]
        }


# ==============================================================================
# 1. RASCH LOGISTIK EHTIMOLLIK FUNKSIYASI
# ==============================================================================
def calculateProbability(theta: float, b: float) -> float:
    """
    Rasch modelining asosiy matematik ehtimolligi:
    P(X_ni = 1 | theta_n, b_i) = exp(theta_n - b_i) / (1 + exp(theta_n - b_i))

    Bu yerda:
    - theta: talabgorning qobiliyat parametri (ability)
    - b: savolning qiyinlik parametri (difficulty)
    """
    diff = theta - b
    # Overflow va underflow'ga qarshi xavfsizlik chegaralari
    if diff > 35.0:
        return 1.0
    if diff < -35.0:
        return 0.0

    exp_val = math.exp(diff)
    return exp_val / (1.0 + exp_val)


# Snake_case alias
calculate_probability = calculateProbability


# ==============================================================================
# 2. SAVOLNING QIYINLIK PARAMETRINI ANIQLASH (AUTO DIFFICULTY / MANUAL)
# ==============================================================================
def estimateItemDifficulty(
    order_no: int,
    question_type: Optional[str] = None,
    auto_difficulty: bool = True,
    manual_difficulty: Optional[Union[str, float]] = None,
    custom_difficulty_map: Optional[Dict[str, float]] = None,
) -> Tuple[Union[str, float], float, bool]:
    """
    Savolning qiyinlik darajasi va unga mos numerical b_i parametrini aniqlaydi.

    Qoidalar:
    - Agar auto_difficulty == True bo'lsa:
      Tizim savolning tartib raqami (1-45) va murakkabligi asosida avtomatik belgilaydi:
        * 1-15 (oddiy yopiq test): "easy" (b = -1.0)
        * 16-35 (o'rta darajali yopiq va kontekstli savollar): "medium" (b = 0.0)
        * 36-45 (murakkab ochiq / yozma savollar): "hard" (b = +1.0)
    - Agar auto_difficulty == False bo'lsa:
      Admin qo'lda kiritgan "easy", "medium", "hard" yoki to'g'ridan-to'g'ri real
      float b_i parametri ishlatiladi.

    Qaytaradi:
        (difficulty_name_or_value, numerical_b, auto_assigned_flag)
    """
    diff_map = custom_difficulty_map or DEFAULT_DIFFICULTY_MAP

    if not auto_difficulty and manual_difficulty is not None:
        # Qo'lda berilgan qiymat
        if isinstance(manual_difficulty, (int, float)):
            # Real b_i parametri berilgan (masalan, 0.45)
            val = float(manual_difficulty)
            return val, val, False

        diff_str = str(manual_difficulty).strip().lower()
        if diff_str in diff_map:
            return diff_str, diff_map[diff_str], False
        try:
            val = float(diff_str)
            return val, val, False
        except ValueError:
            return "medium", diff_map["medium"], False

    # Auto difficulty ON: matematika Milliy sertifikat strukturasiga mos
    q_type = str(question_type or "").upper()
    is_open = q_type.startswith("O") or order_no >= 36

    if is_open or order_no >= 36:
        label = "hard"
    elif order_no <= 15:
        label = "easy"
    else:
        label = "medium"

    return label, diff_map.get(label, 0.0), True


# Snake_case alias
estimate_item_difficulty = estimateItemDifficulty


# ==============================================================================
# 3. YAKUNIY BALLNI KALIBRLASH (CONVERSION/CALIBRATION)
# ==============================================================================
def convertRaschToScore(
    theta: float,
    calibration_params: Optional[Dict[str, float]] = None
) -> float:
    """
    Rasch logit natijasi theta'ni Milliy sertifikatga o'xshash
    0-70+ (aniqrog'i 0-75) shkalasiga konvertatsiya qiladi.

    Standart kalibrlash qoidasi:
    - O'rtacha qobiliyat (theta = 0.0) -> 50.0 ball (C+ chegarasi)
    - Yuqori qobiliyat (theta = +2.5) -> 72.0 ball (A+ darajasi)
    - Past qobiliyat (theta = -2.5) -> 28.0 ball
    - 0.0 va 75.0 oralig'ida chegaralanadi.
    """
    params = DEFAULT_CALIBRATION_PARAMS.copy()
    if calibration_params:
        params.update(calibration_params)

    base_score = params["base_score"]
    scale_factor = params["scale_factor"]
    min_score = params["min_score"]
    max_score = params["max_score"]

    raw_calc = base_score + (scale_factor * theta)
    clamped = max(min_score, min(max_score, raw_calc))
    return round(clamped, 1)


# Snake_case alias
convert_rasch_to_score = convertRaschToScore


# ==============================================================================
# 4. SERTIFIKAT DARAJASINI ANIQLASH (GRADING SCALE)
# ==============================================================================
def getCertificateLevel(final_score: float) -> Tuple[str, bool]:
    """
    Milliy sertifikat darajalari:
    - 70+       -> A+
    - 65–69.9   -> A
    - 60–64.9   -> B+
    - 55–59.9   -> B
    - 50–54.9   -> C+
    - 46–49.9   -> C
    - < 46      -> Sertifikat darajasi yo'q

    Qaytaradi:
        (daraja_matni, is_certified)
    """
    if final_score >= 70.0:
        return "A+", True
    if final_score >= 65.0:
        return "A", True
    if final_score >= 60.0:
        return "B+", True
    if final_score >= 55.0:
        return "B", True
    if final_score >= 50.0:
        return "C+", True
    if final_score >= 46.0:
        return "C", True
    return "Sertifikat darajasi yo'q", False


# Snake_case alias
get_certificate_level = getCertificateLevel


# ==============================================================================
# 5. RASCH ABILITY THETA'NI BAHOLASH (NEWTON-RAPHSON MLE)
# ==============================================================================
def calculateRaschAbility(
    answers_data: List[Union[Dict[str, Any], QuestionEvaluationItem]],
    max_iter: int = 60,
    tolerance: float = 1e-5,
    auto_difficulty: bool = True,
    custom_difficulty_map: Optional[Dict[str, float]] = None,
    calibration_params: Optional[Dict[str, float]] = None,
) -> RaschEvaluationResult:
    """
    45 ta savol bo'yicha foydalanuvchi javoblarini qabul qilib, Rasch modeli
    orqali iterativ Maximum Likelihood Estimation (MLE) usulida qobiliyat
    darajasi (theta), yakuniy ball va darajani hisoblaydi.

    Har bir savol strukturasi:
    {
        "questionId": 1,
        "correctAnswer": "A",
        "userAnswer": "A",
        "isCorrect": True,      # yoki hisoblanadi: userAnswer == correctAnswer
        "difficulty": "easy"    # 'easy', 'medium', 'hard' yoki float b_i
    }
    """
    parsed_items: List[QuestionEvaluationItem] = []
    diff_map = custom_difficulty_map or DEFAULT_DIFFICULTY_MAP

    for idx, raw in enumerate(answers_data, start=1):
        if isinstance(raw, QuestionEvaluationItem):
            parsed_items.append(raw)
            continue

        q_id = raw.get("questionId", raw.get("question_id", idx))
        c_ans = str(raw.get("correctAnswer", raw.get("correct_answer", ""))).strip()
        u_ans = str(raw.get("userAnswer", raw.get("user_answer", ""))).strip()

        # isCorrect tekshiruvi (agar oldindan berilgan bo'lsa, aks holda taqqoslanadi)
        if "isCorrect" in raw:
            is_corr = bool(raw["isCorrect"])
        elif "is_correct" in raw:
            is_corr = bool(raw["is_correct"])
        else:
            is_corr = (u_ans.upper() == c_ans.upper()) if (u_ans and c_ans) else False

        order_no = int(q_id) if str(q_id).isdigit() else idx
        raw_diff = raw.get("difficulty")
        q_type = raw.get("type", "O" if order_no >= 36 else "Y")

        diff_name_or_val, num_b, auto_flag = estimateItemDifficulty(
            order_no=order_no,
            question_type=q_type,
            auto_difficulty=auto_difficulty,
            manual_difficulty=raw_diff,
            custom_difficulty_map=diff_map,
        )

        parsed_items.append(QuestionEvaluationItem(
            question_id=q_id,
            correct_answer=c_ans,
            user_answer=u_ans,
            is_correct=is_corr,
            difficulty=diff_name_or_val,
            numerical_b=num_b,
            auto_assigned=auto_flag,
        ))

    total_count = len(parsed_items)
    if total_count == 0:
        return RaschEvaluationResult(
            total_questions=0,
            correct_count=0,
            wrong_count=0,
            theta=0.0,
            standard_error=1.0,
            final_score=0.0,
            certificate_level="Sertifikat darajasi yo'q",
            is_certified=False,
            items=[]
        )

    correct_count = sum(1 for it in parsed_items if it.is_correct)
    wrong_count = total_count - correct_count

    # Ekstremal holatlarni qayta ishlash (Bayes / Winsorized smoothing)
    # Agar barchasi to'g'ri (r = total) yoki barchasi xato (r = 0) bo'lsa,
    # sof MLE cheksizlikka (+inf/-inf) ketmasligi uchun 0.3 qadamli korreksiya kiritiladi.
    adjusted_score = float(correct_count)
    if correct_count == 0:
        adjusted_score = 0.3
    elif correct_count == total_count:
        adjusted_score = total_count - 0.3

    # Boshlang'ich logit qobiliyat (oddiy p / (1-p) nisbati)
    prop = adjusted_score / total_count
    prop = max(0.001, min(0.999, prop))
    initial_theta = math.log(prop / (1.0 - prop))
    theta = max(-4.5, min(4.5, initial_theta))

    # Newton-Raphson iterativ yechimi
    for _ in range(max_iter):
        f_val = 0.0     # Sum(P_i) - r
        info_val = 0.0  # Sum(P_i * (1 - P_i)) = Fisher Information

        for it in parsed_items:
            p_i = calculateProbability(theta, it.numerical_b)
            f_val += p_i
            info_val += p_i * (1.0 - p_i)

        f_val -= adjusted_score

        # Yaqinlashish (konvergentsiya) sharti
        if abs(f_val) < tolerance:
            break

        if info_val < 1e-7:
            break

        delta = f_val / info_val
        # O'qdan chetga sakrab ketmasligi uchun qadamni cheklash
        delta = max(-1.0, min(1.0, delta))
        theta -= delta
        theta = max(-5.5, min(5.5, theta))

    # Standart xatolik SE(theta) = 1 / sqrt(I(theta))
    final_info = sum(
        calculateProbability(theta, it.numerical_b) * (1.0 - calculateProbability(theta, it.numerical_b))
        for it in parsed_items
    )
    se = (1.0 / math.sqrt(final_info)) if final_info > 1e-7 else 1.0

    rounded_theta = round(theta, 3)
    rounded_se = round(se, 3)

    # Ball va daraja
    final_score = convertRaschToScore(rounded_theta, calibration_params)
    grade, is_certified = getCertificateLevel(final_score)

    return RaschEvaluationResult(
        total_questions=total_count,
        correct_count=correct_count,
        wrong_count=wrong_count,
        theta=rounded_theta,
        standard_error=rounded_se,
        final_score=final_score,
        certificate_level=grade,
        is_certified=is_certified,
        items=parsed_items,
    )


# Snake_case alias
calculate_rasch_ability = calculateRaschAbility
