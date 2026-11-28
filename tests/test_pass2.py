from pathlib import Path

import pytest

from moth.asm import assemble
from moth.asm.pass2 import encode
from moth.asm.pseudo import expand, word_count
from moth.model import Program


def test_small_program_words():
    program = assemble(
        "        .text\n"
        "        li   $t0, 5\n"
        "        sw   $t0, 0($s0)\n"
        "        bne  $t0, $zero, done\n"
        "        j    done\n"
        "done:\n"
        "        syscall\n"
    )

    assert program.errors == []
    assert [instruction.word for instruction in program.instructions] == [
        0x24080005,
        0xAE080000,
        0x15000001,
        0x08100004,
        0x0000000C,
    ]
    assert program.instructions[0].text == "addiu $t0, $0, 5"


def test_forward_label_and_branch_offset():
    program = assemble(".text\nloop: addi $t1, $t1, -1\n      bne  $t1, $zero, loop\n")

    assert program.errors == []
    assert program.symbols["loop"] == 0x00400000
    assert program.instructions[1].word == 0x1520FFFE


def test_branch_out_of_range_reports_byte_distance():
    program = Program([], {"far": 0x00400000 + 32768 * 4 + 8}, [], {})
    with pytest.raises(ValueError, match="131068"):
        encode("bne", "$t0, $zero, far", 0x00400000, program, 1)


def test_jump_out_of_region_reports_error():
    program = Program([], {"far": 0x10000000}, [], {})
    with pytest.raises(ValueError, match="out of reach"):
        encode("j", "far", 0x00400000, program, 1)


def test_mnemonics_and_registers_are_case_insensitive():
    program = assemble(".text\nADD $t0, $T1, $t2\nLI $t0, 5\nNOP\n")
    assert program.errors == []
    assert [instruction.word for instruction in program.instructions] == [
        0x012A4020,
        0x24080005,
        0x00000000,
    ]


def test_shift_amount_out_of_range_is_an_error():
    program = assemble(".text\nsll $t0, $t1, 32\n")
    assert len(program.errors) == 1
    assert "shift amount 32" in program.errors[0].message


def test_every_supported_mars_rule_has_matching_word_count():
    rules = Path(__file__).parents[1] / "src" / "moth" / "asm" / "PseudoOps.txt"
    checked = 0

    for line in rules.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        source = line.split("\t")[0].strip()
        if not source:
            continue
        mnemonic, _, operands = source.partition(" ")
        try:
            expanded = expand(mnemonic, operands)
        except ValueError:
            continue
        checked += 1
        actual = 1 if expanded is None else len(expanded)
        assert word_count(mnemonic, operands) == actual, source

    assert checked > 100


def test_pseudo_expansion_word_count_agrees():
    program = assemble(
        ".text\n"
        "      li   $t0, 0xFFFFFFFF\n"
        "      la   $t0, msg\n"
        "      bge  $t0, 100000, done\n"
        "      abs  $t1, $t0\n"
        "done: nop\n"
        ".data\n"
        'msg: .asciiz "hi"\n'
    )

    assert program.errors == []
    assert all(instruction.word is not None for instruction in program.instructions)
    assert program.instructions[0].address == 0x00400000
    assert program.instructions[1].address == 0x00400004
