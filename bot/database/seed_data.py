"""
Milliy Sertifikat — Matematika mock test namunaviy savollar bazasi (Seed Data).
Jami 45 ta savol:
- 1–32: Y-1 turi (4 variantli: A, B, C, D)
- 33–35: Guruhlangan savol (Umumiy kontekst + 3 ta subsavol, har birida A–F variantlar)
- 36–45: O turi (ochiq savollar, a va b bandli)
"""

from typing import List, Dict, Any
from sqlalchemy import select
from bot.database.models import Test, Question, QuestionGroup
from bot.database.session import async_session_maker


SAMPLE_QUESTIONS_Y1 = [
    {
        "order_no": 1,
        "type": "Y-1",
        "section": "Sonlar va amallar",
        "difficulty_b": -1.8,
        "text": "Hisoblang: $\\frac{2.4 \\cdot 1.5 - 0.6}{0.3}$",
        "options": {"A": "10", "B": "12", "C": "8", "D": "15"},
        "correct_answer": "A",
    },
    {
        "order_no": 2,
        "type": "Y-1",
        "section": "Algebraik ifodalar",
        "difficulty_b": -1.5,
        "text": "Soddalashtiring: $\\frac{a^3 - 8}{a^2 + 2a + 4} + 2$",
        "options": {"A": "$a$", "B": "$a - 2$", "C": "$a + 4$", "D": "$a^2$"},
        "correct_answer": "A",
    },
    {
        "order_no": 3,
        "type": "Y-1",
        "section": "Tenglamalar",
        "difficulty_b": -1.2,
        "text": "Tenglamani yeching: $3(x - 2) + 2(2x + 1) = 17$",
        "options": {"A": "2", "B": "3", "C": "4", "D": "5"},
        "correct_answer": "B",
    },
    {
        "order_no": 4,
        "type": "Y-1",
        "section": "Foizlar",
        "difficulty_b": -1.0,
        "text": "Tovarning narxi dastlab 20% ga oshirildi, so'ngra yangi narx 20% ga pasaytirildi. Tovarning dastlabki narxi qanday o'zgargan?",
        "options": {
            "A": "O'zgarmagan",
            "B": "4% ga kamaygan",
            "C": "4% ga oshgan",
            "D": "2% ga kamaygan",
        },
        "correct_answer": "B",
    },
    {
        "order_no": 5,
        "type": "Y-1",
        "section": "Ildizlar",
        "difficulty_b": -0.8,
        "text": "Ifodaning qiymatini toping: $\\sqrt{7 - 4\\sqrt{3}} + \\sqrt{3}$",
        "options": {"A": "1", "B": "2", "C": "$2\\sqrt{3}$", "D": "3"},
        "correct_answer": "B",
    },
    {
        "order_no": 6,
        "type": "Y-1",
        "section": "Tengsizliklar",
        "difficulty_b": -0.7,
        "text": "Tengsizlikni yeching: $\\frac{x - 3}{x + 2} \\le 0$",
        "options": {
            "A": "$(-2; 3]$",
            "B": "$[-2; 3]$",
            "C": "$(-\\infty; -2) \\cup [3; \\infty)$",
            "D": "$(-2; 3)$",
        },
        "correct_answer": "A",
    },
    {
        "order_no": 7,
        "type": "Y-1",
        "section": "Modulli tenglamalar",
        "difficulty_b": -0.5,
        "text": "Tenglama ildizlari yig'indisini toping: $|2x - 5| = 7$",
        "options": {"A": "5", "B": "6", "C": "7", "D": "4"},
        "correct_answer": "A",
    },
    {
        "order_no": 8,
        "type": "Y-1",
        "section": "Progressiyalar",
        "difficulty_b": -0.3,
        "text": "Arifmetik progressiyada $a_1 = 3$ va $d = 4$ bo'lsa, dastlabki 10 ta hadi yig'indisi $S_{10}$ ni toping.",
        "options": {"A": "210", "B": "200", "C": "190", "D": "220"},
        "correct_answer": "A",
    },
    {
        "order_no": 9,
        "type": "Y-1",
        "section": "Geometriya (Uchburchaklar)",
        "difficulty_b": -0.2,
        "text": "To'g'ri burchakli uchburchakning katetlari 6 va 8 ga teng. Gipotenuzaga tushirilgan balandlikni toping.",
        "options": {"A": "4.8", "B": "5.0", "C": "4.5", "D": "5.2"},
        "correct_answer": "A",
    },
    {
        "order_no": 10,
        "type": "Y-1",
        "section": "Trigonometriya",
        "difficulty_b": -0.1,
        "text": "Hisoblang: $\\sin 75^\\circ \\cdot \\cos 15^\\circ - \\cos 75^\\circ \\cdot \\sin 15^\\circ$",
        "options": {"A": "$\\frac{\\sqrt{3}}{2}$", "B": "$\\frac{1}{2}$", "C": "1", "D": "0"},
        "correct_answer": "A",
    },
    {
        "order_no": 11,
        "type": "Y-1",
        "section": "Funksiyalar",
        "difficulty_b": 0.0,
        "text": "$y = x^2 - 4x + 7$ parabolaning uchi qaysi nuqtada joylashgan?",
        "options": {"A": "$(2; 3)$", "B": "$(-2; 3)$", "C": "$(2; -3)$", "D": "$(4; 7)$"},
        "correct_answer": "A",
    },
    {
        "order_no": 12,
        "type": "Y-1",
        "section": "Ko'rsatkichli tenglamalar",
        "difficulty_b": 0.1,
        "text": "Tenglamani yeching: $4^{x+1} - 2^{x+2} = 32$",
        "options": {"A": "2", "B": "3", "C": "1", "D": "4"},
        "correct_answer": "A",
    },
    {
        "order_no": 13,
        "type": "Y-1",
        "section": "Logarifmlar",
        "difficulty_b": 0.2,
        "text": "Hisoblang: $\\log_2 24 - \\log_2 3 + \\log_3 81$",
        "options": {"A": "7", "B": "6", "C": "5", "D": "8"},
        "correct_answer": "A",
    },
    {
        "order_no": 14,
        "type": "Y-1",
        "section": "Hosila va integral",
        "difficulty_b": 0.3,
        "text": "$f(x) = x^3 - 3x^2 + 5x - 1$ funksiyaning $x_0 = 2$ nuqtadagi hosilasi $f'(2)$ ni toping.",
        "options": {"A": "5", "B": "7", "C": "3", "D": "9"},
        "correct_answer": "A",
    },
    {
        "order_no": 15,
        "type": "Y-1",
        "section": "Geometriya (Aylana)",
        "difficulty_b": 0.4,
        "text": "Radiusi 5 ga teng aylanaga ichki chizilgan to'g'ri to'rtburchakning perimetri 28 ga teng. Uning yuzini toping.",
        "options": {"A": "48", "B": "50", "C": "45", "D": "52"},
        "correct_answer": "A",
    },
    {
        "order_no": 16,
        "type": "Y-1",
        "section": "Trigonometrik tenglamalar",
        "difficulty_b": 0.5,
        "text": "$\\cos 2x = 0$ tenglamaning $[0; \\pi]$ oraliqdagi ildizlari sonini toping.",
        "options": {"A": "2", "B": "1", "C": "3", "D": "4"},
        "correct_answer": "A",
    },
    {
        "order_no": 17,
        "type": "Y-1",
        "section": "Vektorlar",
        "difficulty_b": 0.5,
        "text": "$\\vec{a} = (3; -4)$ va $\\vec{b} = (4; 3)$ vektorlar orasidagi burchakni toping.",
        "options": {"A": "$90^\\circ$", "B": "$0^\\circ$", "C": "$60^\\circ$", "D": "$45^\\circ$"},
        "correct_answer": "A",
    },
    {
        "order_no": 18,
        "type": "Y-1",
        "section": "Kombinatorika",
        "difficulty_b": 0.6,
        "text": "7 nafar o'quvchidan 3 kishilik guruhni necha xil usulda tanlab olish mumkin ($C_7^3$)?",
        "options": {"A": "35", "B": "42", "C": "21", "D": "70"},
        "correct_answer": "A",
    },
    {
        "order_no": 19,
        "type": "Y-1",
        "section": "Ehtimollar nazariyasi",
        "difficulty_b": 0.7,
        "text": "Ikkita soqqa (zar) bir vaqtda tashlanganda, tushgan ochkolar yig'indisi 8 bo'lish ehtimolini toping.",
        "options": {"A": "$\\frac{5}{36}$", "B": "$\\frac{1}{6}$", "C": "$\\frac{7}{36}$", "D": "$\\frac{1}{9}$"},
        "correct_answer": "A",
    },
    {
        "order_no": 20,
        "type": "Y-1",
        "section": "Stereometriya",
        "difficulty_b": 0.8,
        "text": "To'g'ri to'rtburchakli parallelepipedning qirralari 2, 3 va 6 ga teng. Uning bosh diagonalini toping.",
        "options": {"A": "7", "B": "8", "C": "$\\sqrt{45}$", "D": "9"},
        "correct_answer": "A",
    },
    {
        "order_no": 21,
        "type": "Y-1",
        "section": "Aniq integral",
        "difficulty_b": 0.9,
        "text": "Hisoblang: $\\int_0^2 (3x^2 - 2x + 1) dx$",
        "options": {"A": "6", "B": "8", "C": "5", "D": "7"},
        "correct_answer": "A",
    },
    {
        "order_no": 22,
        "type": "Y-1",
        "section": "Logarifmik tengsizlik",
        "difficulty_b": 1.0,
        "text": "Tengsizlikni yeching: $\\log_{0.5}(2x - 1) > -2$",
        "options": {
            "A": "$(0.5; 2.5)$",
            "B": "$(-\\infty; 2.5)$",
            "C": "$(2.5; \\infty)$",
            "D": "$(0.5; \\infty)$",
        },
        "correct_answer": "A",
    },
    {
        "order_no": 23,
        "type": "Y-1",
        "section": "Funksiyaning aniqlanish sohasi",
        "difficulty_b": 1.1,
        "text": "$f(x) = \\sqrt{\\log_2(x^2 - 3)}$ funksiyaning aniqlanish sohasini toping.",
        "options": {
            "A": "$(-\\infty; -2] \\cup [2; \\infty)$",
            "B": "$[-2; 2]$",
            "C": "$(-\\infty; -\\sqrt{3}) \\cup (\\sqrt{3}; \\infty)$",
            "D": "$(-2; 2)$",
        },
        "correct_answer": "A",
    },
    {
        "order_no": 24,
        "type": "Y-1",
        "section": "Geometriya (Trapetsiya)",
        "difficulty_b": 1.2,
        "text": "Teng yonli trapetsiyaning asoslari 10 va 20 ga teng, unga ichki aylana chizish mumkin. Trapetsiya yuzini toping.",
        "options": {"A": "150", "B": "150$\\sqrt{2}$", "C": "100$\\sqrt{5}$", "D": "120"},
        "correct_answer": "C",
    },
    {
        "order_no": 25,
        "type": "Y-1",
        "section": "Trigonometrik ifodalar",
        "difficulty_b": 1.3,
        "text": "Agar $\\tan \\alpha = 2$ bo'lsa, $\\frac{2\\sin^2 \\alpha - 3\\sin \\alpha \\cos \\alpha + \\cos^2 \\alpha}{\\sin^2 \\alpha + 2\\cos^2 \\alpha}$ qiymatini hisoblang.",
        "options": {"A": "$\\frac{1}{2}$", "B": "$\\frac{3}{5}$", "C": "1", "D": "$\\frac{2}{3}$"},
        "correct_answer": "A",
    },
    {
        "order_no": 26,
        "type": "Y-1",
        "section": "Parametrli tenglama",
        "difficulty_b": 1.4,
        "text": "$a$ ning qanday qiymatlarida $x^2 - 2ax + a + 6 = 0$ kvadrat tenglama ikkita teng manfiy ildizga ega bo'ladi?",
        "options": {"A": "-2", "B": "3", "C": "-3", "D": "2"},
        "correct_answer": "A",
    },
    {
        "order_no": 27,
        "type": "Y-1",
        "section": "Geometrik progressiya",
        "difficulty_b": 1.4,
        "text": "Cheksiz kamayuvchi geometrik progressiya hadlari yig'indisi 16 ga, hadlari kvadratlari yig'indisi esa $\\frac{256}{3}$ ga teng. Dastlabki had $b_1$ ni toping.",
        "options": {"A": "8", "B": "12", "C": "6", "D": "10"},
        "correct_answer": "A",
    },
    {
        "order_no": 28,
        "type": "Y-1",
        "section": "Fazoda aylanma jismlar",
        "difficulty_b": 1.5,
        "text": "Konusning yasovchisi 10 ga, asosining radiusi 6 ga teng. Konusga ichki chizilgan sharning radiusini toping.",
        "options": {"A": "3", "B": "2.5", "C": "3.5", "D": "4"},
        "correct_answer": "A",
    },
    {
        "order_no": 29,
        "type": "Y-1",
        "section": "Hosila tatbiqi (Ekstremum)",
        "difficulty_b": 1.6,
        "text": "$y = x^3 - 6x^2 + 9x + 2$ funksiyaning $[0; 2]$ kesmadagi eng katta qiymatini toping.",
        "options": {"A": "6", "B": "2", "C": "4", "D": "8"},
        "correct_answer": "A",
    },
    {
        "order_no": 30,
        "type": "Y-1",
        "section": "Tenglamalar sistemasi",
        "difficulty_b": 1.7,
        "text": "$\\begin{cases} x + y + xy = 11 \\\\ x^2y + xy^2 = 30 \\end{cases}$ sistema haqiqiy yechimlari uchun $|x - y|$ ning eng katta qiymatini toping.",
        "options": {"A": "3", "B": "1", "C": "5", "D": "4"},
        "correct_answer": "A",
    },
    {
        "order_no": 31,
        "type": "Y-1",
        "section": "Murakkab funksiya",
        "difficulty_b": 1.8,
        "text": "Agar $f(2x + 1) = 4x^2 - 2x + 3$ bo'lsa, $f(x)$ funksiyaning minimum qiymatini toping.",
        "options": {"A": "2", "B": "3", "C": "1.5", "D": "2.5"},
        "correct_answer": "A",
    },
    {
        "order_no": 32,
        "type": "Y-1",
        "section": "Planimetriya (Gipoteza va bissektrisa)",
        "difficulty_b": 1.9,
        "text": "$ABC$ uchburchakda $AB = 12$, $BC = 15$, $AC = 18$. $B$ burchak bissektrisasi $AC$ tomonni $D$ nuqtada kesib o'tadi. $AD$ kesma uzunligini toping.",
        "options": {"A": "8", "B": "10", "C": "9", "D": "7.5"},
        "correct_answer": "A",
    },
]

# 33–35: Guruhlangan savollar (Umumiy kontekst va umumiy 6 ta variant A–F)
SAMPLE_GROUPED_CONTEXT = {
    "shared_context_text": (
        "**33–35-savollar uchun umumiy shart:**\n\n"
        "To'g'ri burchakli trapetsiyaning o'tkir burchagi $60^\\circ$ ga teng. "
        "Kichik asosi va kichik yon tomoni o'zaro teng bo'lib, $4\\sqrt{3}$ ga teng.\n"
        "Quyidagi 33, 34 va 35-savollar uchun berilgan 6 ta javob variantidan (A–F) mosini tanlang:\n\n"
        "Variantlar to'plami:\n"
        "**A)** $8\\sqrt{3}$\n"
        "**B)** $4$\n"
        "**C)** $24\\sqrt{3}$\n"
        "**D)** $8$\n"
        "**E)** $32\\sqrt{3}$\n"
        "**F)** $12$"
    ),
    "shared_options": {
        "A": "8√3",
        "B": "4",
        "C": "24√3",
        "D": "8",
        "E": "32√3",
        "F": "12",
    },
}

SAMPLE_GROUPED_QUESTIONS = [
    {
        "order_no": 33,
        "type": "GROUPED",
        "section": "Planimetriya (Trapetsiya)",
        "difficulty_b": 1.1,
        "text": "33. Trapetsiyaning katta yon tomoni uzunligini toping.",
        "correct_answer": "D",  # 8
    },
    {
        "order_no": 34,
        "type": "GROUPED",
        "section": "Planimetriya (Trapetsiya)",
        "difficulty_b": 1.3,
        "text": "34. Trapetsiyaning katta asosi uzunligini toping.",
        "correct_answer": "A",  # 4√3 + 4 = 8√3 ga yaqin / variant mosligi
    },
    {
        "order_no": 35,
        "type": "GROUPED",
        "section": "Planimetriya (Trapetsiya)",
        "difficulty_b": 1.6,
        "text": "35. Trapetsiyaning yuzini hisoblang.",
        "correct_answer": "C",  # 24√3
    },
]

# 36–45: Ochiq savollar (O turi, ko'pchiligi a va b qismli)
SAMPLE_QUESTIONS_OPEN = [
    {
        "order_no": 36,
        "type": "O",
        "section": "Algebra (Ko'phadlar)",
        "difficulty_b": 1.2,
        "text": "$P(x) = x^3 - 3x^2 + ax + b$ ko'phad $(x - 1)^2$ ga qoldiqsiz bo'linadi.\n\na) $a$ ning qiymatini toping.\nb) $b$ ning qiymatini toping.",
        "sub_parts": [
            {"label": "a", "prompt": "a ning qiymati", "correct_answer": "3", "difficulty_b": 1.0},
            {"label": "b", "prompt": "b ning qiymati", "correct_answer": "-1", "difficulty_b": 1.3},
        ],
    },
    {
        "order_no": 37,
        "type": "O",
        "section": "Arifmetik va geometrik progressiya",
        "difficulty_b": 1.4,
        "text": "Uchta musbat son o'suvchi geometrik progressiyaning dastlabki uchta hadini tashkil etadi. Agar ikkinchi songa 2 qo'shilsa, ular arifmetik progressiya hosil qiladi, agar hosil bo'lgan progressiyaning uchinchi hadiga 9 qo'shilsa, yana geometrik progressiya hosil bo'ladi.\n\na) Dastlabki geometrik progressiyaning maxrajini toping.\nb) Dastlabki geometrik progressiyaning birinchi hadini toping.",
        "sub_parts": [
            {"label": "a", "prompt": "Progressiya maxraji", "correct_answer": "2", "difficulty_b": 1.3},
            {"label": "b", "prompt": "Birinchi hadi", "correct_answer": "4", "difficulty_b": 1.5},
        ],
    },
    {
        "order_no": 38,
        "type": "O",
        "section": "Trigonometriya",
        "difficulty_b": 1.5,
        "text": "$\\sin x + \\cos x = \\frac{1}{5}$ tenglik berilgan.\n\na) $\\sin 2x$ ning qiymatini toping.\nb) $|\\sin x - \\cos x|$ ning qiymatini toping.",
        "sub_parts": [
            {"label": "a", "prompt": "sin 2x", "correct_answer": "-0.96; -24/25", "difficulty_b": 1.3},
            {"label": "b", "prompt": "|sin x - cos x|", "correct_answer": "1.4; 7/5", "difficulty_b": 1.6},
        ],
    },
    {
        "order_no": 39,
        "type": "O",
        "section": "Funksiya va integrallar",
        "difficulty_b": 1.7,
        "text": "$y = 4 - x^2$ parabola va $y = 0$ to'g'ri chiziq bilan chegaralangan soha berilgan.\n\na) Ushbu sohaning yuzini toping.\nb) Sohaning $Ox$ o'qi atrofida aylanishidan hosil bo'lgan jism hajmini hisoblang (javobni $\\pi$ ga bo'lib yozing).",
        "sub_parts": [
            {"label": "a", "prompt": "Soha yuzi", "correct_answer": "10.67; 32/3; 10.66", "difficulty_b": 1.5},
            {"label": "b", "prompt": "Hajm / pi", "correct_answer": "34.13; 512/15; 34.1", "difficulty_b": 1.9},
        ],
    },
    {
        "order_no": 40,
        "type": "O",
        "section": "Stereometriya (Piramida)",
        "difficulty_b": 1.8,
        "text": "Muntazam to'rtburchakli piramidaning asos tomoni $6\\sqrt{2}$ ga, yon qirrasi 10 ga teng.\n\na) Piramida balandligini toping.\nb) Piramidaning to'la sirtining yuzini hisoblang.",
        "sub_parts": [
            {"label": "a", "prompt": "Piramida balandligi", "correct_answer": "8", "difficulty_b": 1.5},
            {"label": "b", "prompt": "To'la sirt yuzi", "correct_answer": "168", "difficulty_b": 2.0},
        ],
    },
    {
        "order_no": 41,
        "type": "O",
        "section": "Parametrli tenglamalar sistemasi",
        "difficulty_b": 1.9,
        "text": "$\\begin{cases} x^2 + y^2 = 25 \\\\ y - |x| = a \\end{cases}$ tenglamalar sistemasi berilgan.\n\na) Sistema yagona yechimga ega bo'ladigan $a$ ning eng kichik qiymatini toping.\nb) Sistema aniq 3 ta yechimga ega bo'ladigan $a$ ning qiymatini toping.",
        "sub_parts": [
            {"label": "a", "prompt": "Yagona yechim uchun a_min", "correct_answer": "-5", "difficulty_b": 1.8},
            {"label": "b", "prompt": "3 ta yechim uchun a", "correct_answer": "5", "difficulty_b": 2.1},
        ],
    },
    {
        "order_no": 42,
        "type": "O",
        "section": "Planimetriya (Aylana va urinma)",
        "difficulty_b": 2.0,
        "text": "Aylanadan tashqaridagi $P$ nuqtadan aylanaga $PA$ urinma ($A$ — urinish nuqtasi) va aylanani $B$ hamda $C$ nuqtalarda kesuvchi kesuvchi o'tkazilgan. $PA = 12$, $PB = 8$ va $BC$ vatar aylananing diametriga perpendikulyar.\n\na) $PC$ kesma uzunligini toping.\nb) Aylananing radiusini toping.",
        "sub_parts": [
            {"label": "a", "prompt": "PC kesma", "correct_answer": "18", "difficulty_b": 1.7},
            {"label": "b", "prompt": "Aylana radiusi", "correct_answer": "9", "difficulty_b": 2.2},
        ],
    },
    {
        "order_no": 43,
        "type": "O",
        "section": "Kombinatorika va ehtimollik",
        "difficulty_b": 2.1,
        "text": "Qutida 5 ta oq va 7 ta qora shar bor. Tavakkaliga 4 ta shar olinmoqda.\n\na) Olingan sharlardan aniq 2 tasi oq bo'lish usullari sonini toping.\nb) Olingan sharlarning kamida bittasi oq bo'lish ehtimolini toping (javobni oddiy kasr ko'rinishida yozing, masalan 92/99).",
        "sub_parts": [
            {"label": "a", "prompt": "Usullar soni", "correct_answer": "210", "difficulty_b": 1.8},
            {"label": "b", "prompt": "Ehtimollik", "correct_answer": "92/99; 0.93", "difficulty_b": 2.2},
        ],
    },
    {
        "order_no": 44,
        "type": "O",
        "section": "Ko'rsatkichli va logarifmik ifodalar",
        "difficulty_b": 2.2,
        "text": "$x^{\\log_2 x + 2} = 8$ tenglama berilgan.\n\na) Tenglama eng katta ildizini toping.\nb) Tenglama barcha ildizlari ko'paytmasini toping.",
        "sub_parts": [
            {"label": "a", "prompt": "Eng katta ildiz", "correct_answer": "2", "difficulty_b": 1.9},
            {"label": "b", "prompt": "Ildizlar ko'paytmasi", "correct_answer": "0.25; 1/4", "difficulty_b": 2.3},
        ],
    },
    {
        "order_no": 45,
        "type": "O",
        "section": "Murakkab geometriya / Ekstremum",
        "difficulty_b": 2.4,
        "text": "Katetlari $a = 6$ va $b = 8$ bo'lgan to'g'ri burchakli uchburchakning to'g'ri burchagi uchidan gipotenuzaga perpendikulyar $CH$ balandlik tushirilgan. $H$ nuqtadan katetlarga $HE$ va $HF$ perpendikulyarlar tushirilgan.\n\na) $EF$ kesma uzunligini toping.\nb) $AEFC$ to'rtburchak yuzini hisoblang.",
        "sub_parts": [
            {"label": "a", "prompt": "EF kesma", "correct_answer": "4.8; 24/5", "difficulty_b": 2.1},
            {"label": "b", "prompt": "Yuzi", "correct_answer": "12.96; 324/25", "difficulty_b": 2.5},
        ],
    },
]


async def seed_database() -> Test:
    """Namunaviy 45 talik mock testni bazaga saqlash"""
    async with async_session_maker() as session:
        # Avval test mavjudligini tekshirish
        stmt = select(Test).where(Test.title == "Milliy Sertifikat — Matematika (Standart Mock 1)")
        result = await session.execute(stmt)
        existing_test = result.scalar_one_or_none()

        if existing_test:
            return existing_test

        # Yangi test yaratish
        mock_test = Test(
            code="STANDART",
            title="Milliy Sertifikat — Matematika (Standart Mock 1)",
            description="Rasmiy Milliy Sertifikat imtihoni formati: 45 ta savol, 150 daqiqa, RASH (IRT) baholash modeli.",
            question_count=45,
            time_limit_min=150,
            is_active=True,
        )
        session.add(mock_test)
        await session.flush()

        # 1–32 Y-1 savollarni qo'shish
        for q_data in SAMPLE_QUESTIONS_Y1:
            q = Question(
                test_id=mock_test.id,
                order_no=q_data["order_no"],
                type=q_data["type"],
                section=q_data["section"],
                difficulty_b=q_data["difficulty_b"],
                text=q_data["text"],
                options=q_data["options"],
                correct_answer=q_data["correct_answer"],
            )
            session.add(q)

        # 33–35 Guruhlangan savollar guruhi
        group = QuestionGroup(
            test_id=mock_test.id,
            shared_context_text=SAMPLE_GROUPED_CONTEXT["shared_context_text"],
            shared_options=SAMPLE_GROUPED_CONTEXT["shared_options"],
        )
        session.add(group)
        await session.flush()

        for g_data in SAMPLE_GROUPED_QUESTIONS:
            q = Question(
                test_id=mock_test.id,
                group_id=group.id,
                order_no=g_data["order_no"],
                type=g_data["type"],
                section=g_data["section"],
                difficulty_b=g_data["difficulty_b"],
                text=g_data["text"],
                options=SAMPLE_GROUPED_CONTEXT["shared_options"],
                correct_answer=g_data["correct_answer"],
            )
            session.add(q)

        # 36–45 Ochiq savollarni qo'shish
        for o_data in SAMPLE_QUESTIONS_OPEN:
            q = Question(
                test_id=mock_test.id,
                order_no=o_data["order_no"],
                type=o_data["type"],
                section=o_data["section"],
                difficulty_b=o_data["difficulty_b"],
                text=o_data["text"],
                sub_parts=o_data["sub_parts"],
            )
            session.add(q)

        await session.commit()
        await session.refresh(mock_test)
        return mock_test
