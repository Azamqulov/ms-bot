import pytest
from bot.core.validator import (
    parse_numeric_value,
    normalize_text_answer,
    check_open_answer,
    parse_subparts_input,
)


def test_parse_numeric_value():
    assert parse_numeric_value("12") == 12.0
    assert parse_numeric_value(" 3,5 ") == 3.5
    assert parse_numeric_value("-4.25") == -4.25
    assert parse_numeric_value("1/2") == 0.5
    assert parse_numeric_value("-3/4") == -0.75
    assert parse_numeric_value("not_a_number") is None


def test_check_open_answer_numbers():
    # Ekvivalent sonlar
    assert check_open_answer("3.5", "3.5") is True
    assert check_open_answer("3,5", "3.5") is True
    assert check_open_answer("0.5", "1/2") is True
    assert check_open_answer("1/2", "0.5") is True
    assert check_open_answer("-5", "- 5") is True
    assert check_open_answer("10", "12") is False


def test_check_open_answer_multiple_options():
    # Bir nechta muqobil javoblar (masalan "3.5; 7/2")
    assert check_open_answer("3.5", "3.5; 7/2") is True
    assert check_open_answer("7/2", "3.5; 7/2") is True


def test_parse_subparts_input():
    parsed = parse_subparts_input("a) 12 b) 3.5")
    assert parsed.get("a") == "12"
    assert parsed.get("b") == "3.5"

    parsed2 = parse_subparts_input("a: -4\nb: 25")
    assert parsed2.get("a") == "-4"
    assert parsed2.get("b") == "25"
