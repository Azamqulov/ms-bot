import pytest
from bot.core.latex import clean_latex


def test_clean_fractions():
    assert clean_latex(r"$\frac{5}{36}$") == "5/36"
    assert clean_latex(r"$\frac{1}{6}$") == "1/6"
    assert clean_latex(r"$\frac{7}{36}$") == "7/36"
    assert clean_latex(r"$\frac{1}{9}$") == "1/9"


def test_clean_powers_and_roots():
    assert clean_latex(r"$x^2 - 4x + 7$") == "x² - 4x + 7"
    assert clean_latex(r"$\sqrt{7 - 4\sqrt{3}} + \sqrt{3}$") == "√(7 - 4√(3)) + √(3)"
    assert clean_latex(r"$a_1 = 3$") == "a₁ = 3"


def test_clean_trig_and_symbols():
    assert clean_latex(r"$\sin 75^\circ$") == "sin 75°"
    assert clean_latex(r"$\le$") == "≤"
    assert clean_latex(r"$\ge$") == "≥"
    assert clean_latex(r"$\pi$") == "π"
