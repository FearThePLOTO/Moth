import pytest

from moth.asm.pseudo import expand

SYMBOLS = {"main": 0x00400000, "msg": 0x10010000}


def test_nop():
    assert expand("nop", "", {}) == [("sll", "$zero, $zero, 0")]


def test_move():
    assert expand("move", "$t0, $t1", {}) == [("addu", "$t0, $zero, $t1")]


def test_li_addiu_range():
    assert expand("li", "$t0, 5", {}) == [("addiu", "$t0, $zero, 5")]
    assert expand("li", "$t0, 32767", {}) == [("addiu", "$t0, $zero, 32767")]
    assert expand("li", "$t0, -32768", {}) == [("addiu", "$t0, $zero, -32768")]


def test_li_ori_range():
    assert expand("li", "$t0, 32768", {}) == [("ori", "$t0, $zero, 32768")]
    assert expand("li", "$t0, 65535", {}) == [("ori", "$t0, $zero, 65535")]


def test_li_two_words_positive():
    assert expand("li", "$t0, 65536", {}) == [
        ("lui", "$at, 1"),
        ("ori", "$t0, $at, 0"),
    ]


def test_li_two_words_negative():
    assert expand("li", "$t0, -32769", {}) == [
        ("lui", "$at, 65535"),
        ("ori", "$t0, $at, 32767"),
    ]


def test_li_two_words_hexa():
    assert expand("li", "$t0, 0x12345678", {}) == [
        ("lui", "$at, 4660"),
        ("ori", "$t0, $at, 22136"),
    ]


def test_li_missing_operand():
    with pytest.raises(ValueError, match="expected 2 operands"):
        expand("li", "$t0", {})


def test_li_not_a_num():
    with pytest.raises(ValueError, match="is not a number"):
        expand("li", "$t0, abc", {})


def test_li_too_big():
    with pytest.raises(ValueError, match="does not fit in 32 bits"):
        expand("li", "$t0, 4294967296", {})


def test_nop_with_operand():
    with pytest.raises(ValueError, match="expected 0 operands"):
        expand("nop", "$t0", {})


def test_la_data_label():
    assert expand("la", "$t0, msg", SYMBOLS) == [
        ("lui", "$at, 4097"),
        ("ori", "$t0, $at, 0"),
    ]


def test_la_text_label():
    assert expand("la", "$t1, main", SYMBOLS) == [
        ("lui", "$at, 64"),
        ("ori", "$t1, $at, 0"),
    ]


def test_la_undefined_label():
    with pytest.raises(ValueError, match="undefined label"):
        expand("la", "$t0, end", SYMBOLS)
