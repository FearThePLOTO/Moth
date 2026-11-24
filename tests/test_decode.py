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
