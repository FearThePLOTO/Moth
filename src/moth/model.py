from dataclasses import dataclass


@dataclass
class Instruction:
    address: int
    line: int
    text: str
    mnemonic: str
    operands: str
    word: int | None = None


@dataclass
class Error:
    line: int
    column: int
    message: str


@dataclass
class Program:
    instructions: list[Instruction]
    symbols: dict[str, int]
    errors: list[Error]
    data: dict[int, int]
