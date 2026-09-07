"""
LaTeX formulalarini Telegram uchun toza va o'qishli Unicode/matn ko'rinishiga keltirish moduli.
Masalan:
  '$\\frac{5}{36}$' -> '5/36'
  '$\\sqrt{7 - 4\\sqrt{3}}$' -> '√(7 - 4√3)'
  'x^2 + 2ax + a' -> 'x² + 2ax + a'
  '\\sin 75^\\circ' -> 'sin 75°'
"""

import re

SUPERSCRIPTS = {
    "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
    "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹",
    "+": "⁺", "-": "⁻", "=": "⁼", "(": "⁽", ")": "⁾",
    "n": "ⁿ", "x": "ˣ",
}

SUBSCRIPTS = {
    "0": "₀", "1": "₁", "2": "₂", "3": "₃", "4": "₄",
    "5": "₅", "6": "₆", "7": "₇", "8": "₈", "9": "₉",
    "+": "₊", "-": "₋", "=": "₌", "(": "₍", ")": "₎",
}


def clean_latex(text: str) -> str:
    """
    LaTeX formulalari mavjud matnni Telegramda chiroyli ko'rinadigan qilib tozalash.
    """
    if not text:
        return ""

    s = text

    # 1. Kasrlar: \frac{a}{b} -> (a)/(b) yoki a/b
    # Takroriy \frac larni ham tozalash
    for _ in range(5):
        s = re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"\1/\2", s)

    # 2. Ildizlar: \sqrt[n]{x} -> n√x, \sqrt{x} -> √x
    s = re.sub(r"\\sqrt\[([^{}]+)\]\{([^{}]+)\}", r"\1√(\2)", s)
    for _ in range(3):
        s = re.sub(r"\\sqrt\{([^{}]+)\}", r"√(\1)", s)
    s = s.replace(r"\sqrt", "√")

    # 3. Trigonometrik va standart funksiyalar
    func_map = {
        r"\sin": "sin",
        r"\cos": "cos",
        r"\tan": "tan",
        r"\cot": "cot",
        r"\tg": "tg",
        r"\ctg": "ctg",
        r"\log": "log",
        r"\ln": "ln",
        r"\lim": "lim",
        r"\int": "∫",
        r"\sum": "∑",
    }
    for latex_func, plain in func_map.items():
        s = re.sub(re.escape(latex_func) + r"(?![a-zA-Z])", plain, s)

    # 4. Matematik belgilar
    symbols_map = {
        r"\cdot": "·",
        r"\times": "×",
        r"\div": "÷",
        r"\pm": "±",
        r"\mp": "∓",
        r"\le": "≤",
        r"\ge": "≥",
        r"\ne": "≠",
        r"\approx": "≈",
        r"\infty": "∞",
        r"\circ": "°",
        r"^\circ": "°",
        r"^{\circ}": "°",
        r"\alpha": "α",
        r"\beta": "β",
        r"\gamma": "γ",
        r"\delta": "δ",
        r"\pi": "π",
        r"\theta": "θ",
        r"\lambda": "λ",
        r"\mu": "μ",
        r"\sigma": "σ",
        r"\phi": "φ",
        r"\omega": "ω",
        r"\vec": "",
        r"\triangle": "△",
        r"\angle": "∠",
        r"\cup": "∪",
        r"\cap": "∩",
        r"\in": "∈",
        r"\subset": "⊂",
    }
    # 4. Daraja va belgilar
    s = s.replace(r"^{\circ}", "°").replace(r"^\circ", "°")
    for latex_sym, plain in symbols_map.items():
        s = s.replace(latex_sym, plain)
    s = s.replace("^°", "°")

    # 5. Darajalar (Superscript): x^2 -> x², x^{10} -> x¹⁰
    def replace_super(m):
        content = m.group(1)
        res = "".join(SUPERSCRIPTS.get(c, c) for c in content)
        return res

    s = re.sub(r"\^{([0-9\+\-\(\)nx]+)}", replace_super, s)
    s = re.sub(r"\^([0-9nx])", replace_super, s)

    # 6. Indekslar (Subscript): a_1 -> a₁, a_{10} -> a₁₀
    def replace_sub(m):
        content = m.group(1)
        res = "".join(SUBSCRIPTS.get(c, c) for c in content)
        return res

    s = re.sub(r"_{([0-9\+\-\(\)]+)}", replace_sub, s)
    s = re.sub(r"_([0-9])", replace_sub, s)

    # 7. Qavslar: \left( \right) -> ( )
    s = re.sub(r"\\left([(\[{|])", r"\1", s)
    s = re.sub(r"\\right([)\]}|])", r"\1", s)

    # 8. Tizimlar: \begin{cases} ... \end{cases}
    s = s.replace(r"\begin{cases}", "{\n").replace(r"\end{cases}", "\n}")
    s = s.replace(r"\\", "\n")

    # 9. Qolgan ortiqcha LaTeX teglari va dollar belgilari ($)
    s = s.replace("$$", "")
    s = s.replace("$", "")
    s = s.replace(r"\{", "{").replace(r"\}", "}")
    s = re.sub(r"\\text\{([^{}]+)\}", r"\1", s)

    # Ortiqcha bo'shliqlarni tozalash
    s = re.sub(r"[ ]+", " ", s).strip()
    return s
