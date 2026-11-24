# src/moth/decode.py
#
# Turns a 32-bit word into an instruction name and its fields.

from dataclasses import dataclass

from moth.bits import field, sext16
from moth.isa import BY_OPCODE, BY_R


@dataclass(frozen=True)
class Decoded:
    mnemonic: str
    fmt: str
    fields: dict[str, int]


def decode(word: int) -> Decoded:
    opcode = field(word, 31, 26)

    # R-type: opcode is 0, so look up the row by funct
    if opcode == 0:
        funct = field(word, 5, 0)
        instruction = BY_R.get((opcode, funct))

        if instruction is None:
            raise ValueError(f"Unknown R-type funct: {funct:#x}")

        fields = {
            "opcode": opcode,
            "rs": field(word, 25, 21),
            "rt": field(word, 20, 16),
            "rd": field(word, 15, 11),
            "shamt": field(word, 10, 6),
            "funct": funct,
        }

        return Decoded(instruction.mnemonic, "R", fields)

    instruction = BY_OPCODE.get(opcode)

    if instruction is None:
        raise ValueError(f"Unknown opcode: {opcode:#x}")

    # J-type
    if instruction.fmt == "J":
        fields = {
            "opcode": opcode,
            "target": field(word, 25, 0),
        }

        return Decoded(instruction.mnemonic, "J", fields)

    # I-type: imm is sign-extended
    fields = {
        "opcode": opcode,
        "rs": field(word, 25, 21),
        "rt": field(word, 20, 16),
        "imm": sext16(field(word, 15, 0)),
    }

    return Decoded(instruction.mnemonic, "I", fields)
