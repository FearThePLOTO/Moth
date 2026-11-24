from dataclasses import dataclass

from .bits import field, sext16
from .isa import BY_OPCODE, BY_R


@dataclass(frozen=True)
class Decoded:
    mnemonic: str
    fmt: str
    fields: dict[str, int]


def decode(word: int) -> Decoded:
    # Extract opcode
    opcode = field(word, 31, 26)

    # R-Type
    if opcode == 0:
        funct = field(word, 5, 0)
        instruction = BY_R.get((opcode, funct))

        if instruction is None:
            raise ValueError(f"Unknown R-Type funct: {funct:#x}")

        fields = {
            "opcode": opcode,
            "rs": field(word, 25, 21),
            "rt": field(word, 20, 16),
            "rd": field(word, 15, 11),
            "shamt": field(word, 10, 6),
            "funct": funct,
        }

        return Decoded(
            mnemonic=instruction.mnemonic,
            fmt="R",
            fields=fields,
        )

    # I-Type and J-Type
    instruction = BY_OPCODE.get(opcode)

    if instruction is None:
        raise ValueError(f"Unknown opcode: {opcode:#x}")

    # J-Type
    if instruction.fmt == "J":
        fields = {
            "opcode": opcode,
            "target": field(word, 25, 0),
        }

        return Decoded(
            mnemonic=instruction.mnemonic,
            fmt="J",
            fields=fields,
        )

    # I-Type
    fields = {
        "opcode": opcode,
        "rs": field(word, 25, 21),
        "rt": field(word, 20, 16),
        "imm": sext16(field(word, 15, 0)),
    }

    return Decoded(
        mnemonic=instruction.mnemonic,
        fmt="I",
        fields=fields,
    )
