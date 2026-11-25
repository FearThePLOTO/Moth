import pytest

from moth.decode import decode


def test_decode_lw():
    result = decode(0x8E080004)

    assert result.mnemonic == "lw"
    assert result.fmt == "I"

    assert result.fields == {
        "opcode": 0x23,
        "rs": 16,
        "rt": 8,
        "imm": 4,
    }


def test_decode_add():
    result = decode(0x012A4020)

    assert result.mnemonic == "add"
    assert result.fmt == "R"

    assert result.fields == {
        "opcode": 0,
        "rs": 9,
        "rt": 10,
        "rd": 8,
        "shamt": 0,
        "funct": 0x20,
    }


def test_decode_jump():
    result = decode(0x08012345)

    assert result.mnemonic == "j"
    assert result.fmt == "J"

    assert result.fields == {
        "opcode": 0x02,
        "target": 0x12345,
    }


def test_decode_negative_immediate():
    result = decode(0x2128FFFC)

    assert result.mnemonic == "addi"
    assert result.fields["imm"] == -4


def test_decode_max_positive_immediate():
    result = decode(0x21287FFF)

    assert result.mnemonic == "addi"
    assert result.fields["imm"] == 32767


@pytest.mark.parametrize(
    ("word", "imm"),
    [
        (0x3408FFFF, 0xFFFF),  # ori  $t0, $zero, 0xFFFF
        (0x31288000, 0x8000),  # andi $t0, $t1, 0x8000
        (0x3C08FFFF, 0xFFFF),  # lui  $t0, 0xFFFF
        (0x3928FFFF, 0xFFFF),  # xori $t0, $t1, 0xFFFF
    ],
)
def test_decode_logical_immediate_is_unsigned(word, imm):
    assert decode(word).fields["imm"] == imm


def test_decode_max_shamt():
    word = 0x00000FC0

    result = decode(word)

    assert result.mnemonic == "sll"
    assert result.fields["shamt"] == 31


def test_decode_zero_register():
    word = 0x00000020

    result = decode(word)

    assert result.mnemonic == "add"
    assert result.fields["rs"] == 0
    assert result.fields["rt"] == 0
    assert result.fields["rd"] == 0


def test_decode_unknown_opcode():
    with pytest.raises(ValueError):
        decode(0xFC000000)


def test_decode_unknown_funct():
    word = 0x0000003F

    with pytest.raises(ValueError):
        decode(word)


def test_decode_jump_target_near_top():
    result = decode(0x0BFFFFFF)

    assert result.mnemonic == "j"
    assert result.fields["target"] == 0x3FFFFFF


def test_decode_syscall():
    result = decode(0x0000000C)

    assert result.mnemonic == "syscall"
    assert result.fmt == "R"
    assert result.fields == {
        "opcode": 0,
        "rs": 0,
        "rt": 0,
        "rd": 0,
        "shamt": 0,
        "funct": 0x0C,
    }


@pytest.mark.parametrize(
    ("word", "mnemonic"),
    [
        (0x012A4020, "add"),
        (0x02328022, "sub"),
        (0x018D5824, "and"),
        (0x00A62025, "or"),
        (0x0085102A, "slt"),
        (0x00094100, "sll"),
        (0x000947C2, "srl"),
        (0x03E00008, "jr"),
        (0x01090018, "mult"),
        (0x00005012, "mflo"),
        (0x2008FFFC, "addi"),
        (0x21497FFF, "addi"),
        (0x312800FF, "andi"),
        (0x3C081001, "lui"),
        (0x8E080004, "lw"),
        (0xAFA8FFF8, "sw"),
        (0x80880000, "lb"),
        (0x11090003, "beq"),
        (0x15090002, "bne"),
        (0x08100015, "j"),
        (0x0C100015, "jal"),
        (0x0000000C, "syscall"),
    ],
)
def test_decode_matches_mars(word, mnemonic):
    assert decode(word).mnemonic == mnemonic
