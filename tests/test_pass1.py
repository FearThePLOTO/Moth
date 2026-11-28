import pytest

from moth.asm.line import parse_line, parse_lines
from moth.asm.pass1 import get_instruction_size, pass1
from moth.asm.pseudo import word_count
from moth.model import Program


def test_addresses_and_symbols():
    source = (
        ".text\nstart: add $t0, $t1, $t2\n"
        + "".join(f"    addi $t0, $t0, {i}\n" for i in range(28))
        + "end: j start\n"
    )
    program = pass1(parse_lines(source))

    assert isinstance(program, Program)
    assert program.errors == []
    assert program.symbols == {"start": 0x00400000, "end": 0x00400074}
    assert len(program.instructions) == 30
    assert program.instructions[-1].address == 0x00400074
    assert [i.line for i in program.instructions] == list(range(2, 32))


@pytest.mark.parametrize(
    ("source", "address", "byte"),
    [
        (".data\nv: .word 0x01020304\n", 0x10010000, 0x04),
        (".data\nv: .byte 7\n", 0x10010000, 7),
        (".data\nv: .space 3\n", 0x10010002, 0),
        ('.data\nv: .asciiz "hi"\n', 0x10010002, 0),
        (".data\n.align 2\nv: .byte 1\n", 0x10010000, 1),
    ],
)
def test_directives(source, address, byte):
    program = pass1(parse_lines(source))
    assert program.errors == []
    assert program.data[address] == byte


def test_word_count_matches_pseudo_table():
    cases = [
        ("li $t0, 5", None),
        ("li $t0, 0xFFFFFFFF", None),
        ("bge $t0, 100000, main", {"main": 0x00400000}),
        ("blt $t0, 100000, main", {"main": 0x00400000}),
        ("abs $t0, $t1", None),
        ("seq $t0, $t1, $t2", None),
        ("ld $t0, 0($s0)", None),
    ]
    for operands, symbols in cases:
        mnemonic, rest = operands.split(" ", 1)
        line = parse_line("    " + operands, 1)
        assert get_instruction_size(line) == word_count(mnemonic, rest, symbols)


def test_leading_zeros_are_decimal():
    program = pass1(parse_lines(".data\nv: .word 08, 010\n"))
    assert program.errors == []
    assert program.data[0x10010000] == 8
    assert program.data[0x10010004] == 10


def test_signed_leading_zero_is_an_error():
    program = pass1(parse_lines(".data\n.word -08\n"))
    assert len(program.errors) == 1


def test_word_accepts_labels():
    program = pass1(parse_lines(".data\n.word later\nlater: .word 1\n"))
    assert program.errors == []
    assert program.data[0x10010000] == 0x04
    assert program.data[0x10010001] == 0x00
    assert program.data[0x10010002] == 0x01
    assert program.data[0x10010003] == 0x10


def test_word_undefined_label_is_an_error():
    program = pass1(parse_lines(".data\n.word missing\n"))
    assert len(program.errors) == 1
    assert "undefined label" in program.errors[0].message


def test_character_literals_in_data():
    program = pass1(parse_lines(".data\n.byte 'a', ','\n.word 'A'\n"))
    assert program.errors == []
    assert program.data[0x10010000] == 0x61
    assert program.data[0x10010001] == 0x2C
    assert program.data[0x10010004] == 0x41


def test_align_in_text_is_an_error():
    program = pass1(parse_lines(".text\n.align 2\nnop\n"))
    assert len(program.errors) == 1
    assert ".align" in program.errors[0].message


def test_asciiz_stores_one_byte_per_character():
    program = pass1(parse_lines('.data\n.asciiz "é"\n'))
    assert program.errors == []
    assert program.data[0x10010000] == 0xE9
    assert program.data[0x10010001] == 0
