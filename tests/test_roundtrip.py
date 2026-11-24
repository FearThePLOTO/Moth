import pytest

from moth.decode import decode
from moth.encode import i_type, j_type, r_type
from moth.isa import TABLE


@pytest.mark.parametrize("instruction", TABLE, ids=lambda i: i.mnemonic)
def test_roundtrip(instruction):
    if instruction.fmt == "R":
        word = r_type(instruction.opcode, 1, 2, 3, 4, instruction.funct)
        expected = {"rs": 1, "rt": 2, "rd": 3, "shamt": 4, "funct": instruction.funct}
    elif instruction.fmt == "I":
        word = i_type(instruction.opcode, 1, 2, -4)
        expected = {"rs": 1, "rt": 2, "imm": -4}
    else:
        word = j_type(instruction.opcode, 0x12345)
        expected = {"target": 0x12345}

    result = decode(word)

    assert result.mnemonic == instruction.mnemonic
    assert result.fmt == instruction.fmt
    for name, value in expected.items():
        assert result.fields[name] == value
