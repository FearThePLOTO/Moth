from pathlib import Path

import pytest

from moth.asm import pseudo
from moth.asm.pseudo import expand, word_count

SYMBOLS = {
    "main": 0x00400000,
    "msg": 0x10010000,
    "label": 0x10010000,
}


def test_nop():
    assert expand("nop", "", {}) == [("sll", "$zero, $zero, 0")]


def test_move():
    assert expand("move", "$t0, $t1", {}) == [("addu", "$t0, $0, $t1")]


@pytest.mark.parametrize(
    "value, expected, words",
    [
        ("32767", [("addiu", "$t0, $0, 32767")], 1),
        ("32768", [("ori", "$t0, $0, 32768")], 1),
        ("65535", [("ori", "$t0, $0, 65535")], 1),
        ("65536", [("lui", "$1, 1"), ("ori", "$t0, $1, 0")], 2),
        ("-32768", [("addiu", "$t0, $0, -32768")], 1),
        ("-32769", [("lui", "$1, 65535"), ("ori", "$t0, $1, 32767")], 2),
    ],
)
def test_li_boundaries(value, expected, words):
    operands = f"$t0, {value}"
    assert expand("li", operands, {}) == expected
    assert word_count("li", operands) == words


def test_li_hexadecimal():
    assert expand("li", "$t0, 0x12345678", {}) == [
        ("lui", "$1, 4660"),
        ("ori", "$t0, $1, 22136"),
    ]


def test_la_data_label():
    assert expand("la", "$t0, msg", SYMBOLS) == [
        ("lui", "$1, 4097"),
        ("ori", "$t0, $1, 0"),
    ]


def test_la_compact_label():
    symbols = {"small": 0x1000}
    assert expand("la", "$t0, small", symbols) == [("addi", "$t0, $0, 4096")]
    assert word_count("la", "$t0, small", symbols) == 1


def test_la_undefined_label():
    with pytest.raises(ValueError, match="undefined label"):
        expand("la", "$t0, end", SYMBOLS)


def test_blt_registers():
    assert expand("blt", "$t0, $t1, main", SYMBOLS) == [
        ("slt", "$1, $t0, $t1"),
        ("bne", "$1, $0, main"),
    ]


def test_blt_immediate():
    assert expand("blt", "$t0, 10, main", SYMBOLS) == [
        ("slti", "$1, $t0, 10"),
        ("bne", "$1, $0, main"),
    ]


def test_bge_large_immediate():
    operands = "$t0, 100000, main"
    result = expand("bge", operands, SYMBOLS)
    assert len(result) == 4
    assert word_count("bge", operands, SYMBOLS) == 4


def test_basic_addi_is_not_expanded():
    assert expand("addi", "$t0, $t1, 5", {}) is None
    assert word_count("addi", "$t0, $t1, 5") == 1


def test_bad_li_inputs():
    with pytest.raises(ValueError, match="expected 2 operands"):
        expand("li", "$t0", {})

    with pytest.raises(ValueError, match="is not a number"):
        expand("li", "$t0, abc", {})

    with pytest.raises(ValueError, match="does not fit in 32 bits"):
        expand("li", "$t0, 4294967296", {})


def test_word_count_matches_expand():
    examples = [
        ("nop", ""),
        ("move", "$t0, $t1"),
        ("li", "$t0, 5"),
        ("li", "$t0, 65536"),
        ("la", "$t0, msg"),
        ("blt", "$t0, $t1, main"),
        ("bge", "$t0, 100000, main"),
    ]

    for mnemonic, operands in examples:
        result = expand(mnemonic, operands, SYMBOLS)
        assert word_count(mnemonic, operands, SYMBOLS) == len(result)


def test_all_examples_from_mars_pseudo_ops():
    rules_file = Path(pseudo.__file__).with_name("PseudoOps.txt")

    for line in rules_file.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue

        source = line.split("\t", 1)[0].strip()
        if not source:
            continue

        parts = source.split(None, 1)
        mnemonic = parts[0]
        operands = parts[1] if len(parts) > 1 else ""

        result = expand(mnemonic, operands, SYMBOLS)
        if result is None:
            # MARS matches the real instruction first (e.g. lw $t1,100($t2)).
            assert pseudo._is_basic_memory_form(pseudo._tokens(source)), source
            assert word_count(mnemonic, operands, SYMBOLS) == 1, source
            continue
        assert word_count(mnemonic, operands, SYMBOLS) == len(result), source


def test_plain_memory_access_is_a_real_instruction():
    for mnemonic, operands in [
        ("sw", "$t0, 0($s0)"),
        ("lw", "$t0, -4($sp)"),
        ("lb", "$t0, 100($t1)"),
    ]:
        assert expand(mnemonic, operands, SYMBOLS) is None
        assert word_count(mnemonic, operands, SYMBOLS) == 1


def test_memory_access_on_a_label_is_still_a_pseudo():
    assert len(expand("lw", "$t0, label", SYMBOLS)) == 2


def test_two_operand_div_is_a_real_instruction():
    assert expand("div", "$t0, $t1", SYMBOLS) is None
    assert word_count("div", "$t0, $t1", SYMBOLS) == 1
