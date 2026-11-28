"""Pass 2: expand pseudo-ops, resolve labels and fill in machine words."""

import re

from ..encode import i_type, j_type, r_type
from ..isa import BY_NAME
from ..model import Error, Program
from ..registers import REGISTER_NAME_TO_NUMBER
from .pass1 import parse_integer, split_operands
from .pseudo import _imm, expand

SHIFTS = {"sll", "srl", "sra"}
PAIR_R = {"mult", "div"}
ONE_R = {"jr"}
HILO_R = {"mfhi", "mflo"}
THREE_R = {
    "add",
    "addu",
    "sub",
    "subu",
    "and",
    "or",
    "xor",
    "nor",
    "slt",
    "sltu",
}
LOAD_STORE = {"lb", "lh", "lw", "lbu", "lhu", "sb", "sh", "sw"}
SIGNED_I = {"addi", "addiu", "slti", "sltiu", "beq", "bne"}
UNSIGNED_I = {"andi", "ori", "xori", "lui"}
MEMORY_FORM = re.compile(r"([^()]+)\(\s*([^()]+)\s*\)")


def add_error(program: Program, line: int, message: str) -> None:
    program.errors.append(Error(line=line, column=1, message=message))


def register(token: str, line: int) -> int:
    number = REGISTER_NAME_TO_NUMBER.get(token.strip().lower())
    if number is None:
        raise ValueError(f'bad register "{token.strip()}"')
    return number


def immediate(token: str, signed: bool, line: int) -> int:
    value = _imm(token)
    low, high = (-32768, 32767) if signed else (0, 65535)
    if not low <= value <= high:
        raise ValueError(f"immediate {value} does not fit in 16 bits")
    return value & 0xFFFF


def label_address(token: str, program: Program, line: int) -> int:
    address = program.symbols.get(token.strip())
    if address is None:
        raise ValueError(f'undefined label "{token.strip()}"')
    return address


def expected_operand_count(mnemonic: str) -> int:
    if mnemonic == "syscall":
        return 0
    if mnemonic in ONE_R or mnemonic in HILO_R or mnemonic in {"j", "jal"}:
        return 1
    if mnemonic in PAIR_R or mnemonic in LOAD_STORE or mnemonic == "lui":
        return 2
    return 3


def encode(mnemonic: str, operands: str, address: int, program: Program, line: int) -> int:
    """Encode one real instruction. Raises ValueError with a beginner-friendly message."""
    row = BY_NAME.get(mnemonic)
    if row is None:
        raise ValueError(f'unknown mnemonic "{mnemonic}"')

    ops = split_operands(operands)
    expected = expected_operand_count(mnemonic)
    if expected is not None and len(ops) != expected:
        raise ValueError(f"expected {expected} operands for {mnemonic}, got {len(ops)}")

    if row.fmt == "R":
        if mnemonic == "syscall":
            return r_type(row.opcode, 0, 0, 0, 0, row.funct)
        if mnemonic in ONE_R:
            return r_type(row.opcode, register(ops[0], line), 0, 0, 0, row.funct)
        if mnemonic in HILO_R:
            return r_type(row.opcode, 0, 0, register(ops[0], line), 0, row.funct)
        if mnemonic in PAIR_R:
            return r_type(
                row.opcode, register(ops[0], line), register(ops[1], line), 0, 0, row.funct
            )
        if mnemonic in SHIFTS:
            shamt = parse_integer(ops[2])
            if not 0 <= shamt <= 31:
                raise ValueError(f"shift amount {shamt} must be between 0 and 31")
            return r_type(
                row.opcode,
                0,
                register(ops[1], line),
                register(ops[0], line),
                shamt,
                row.funct,
            )
        if mnemonic in THREE_R:
            return r_type(
                row.opcode,
                register(ops[1], line),
                register(ops[2], line),
                register(ops[0], line),
                0,
                row.funct,
            )
        raise ValueError(f"cannot encode {mnemonic}")

    if row.fmt == "I":
        if mnemonic in {"beq", "bne"}:
            target = label_address(ops[2], program, line)
            distance = target - (address + 4)
            offset = distance // 4
            if not -32768 <= offset <= 32767:
                raise ValueError(
                    f"branch target is {abs(distance)} bytes away, the limit is 131068"
                )
            return i_type(row.opcode, register(ops[0], line), register(ops[1], line), offset)

        if mnemonic in LOAD_STORE:
            match = MEMORY_FORM.fullmatch(ops[1].strip())
            if match is None:
                raise ValueError(f'bad memory operand "{ops[1].strip()}"')
            offset_token, base_token = match.groups()
            offset = immediate(offset_token, signed=True, line=line)
            return i_type(row.opcode, register(base_token, line), register(ops[0], line), offset)

        if mnemonic == "lui":
            return i_type(
                row.opcode, 0, register(ops[0], line), immediate(ops[1], signed=False, line=line)
            )

        signed = mnemonic in SIGNED_I
        return i_type(
            row.opcode,
            register(ops[1], line),
            register(ops[0], line),
            immediate(ops[2], signed, line),
        )

    target = label_address(ops[0], program, line)
    next_address = address + 4
    if (target >> 28) != (next_address >> 28):
        raise ValueError(f"jump target 0x{target:08x} is out of reach from 0x{next_address:08x}")
    return j_type(row.opcode, target >> 2)


def pass2(program: Program) -> None:
    """Fill every instruction word. Errors are collected, never raised."""
    instructions = program.instructions
    index = 0

    while index < len(instructions):
        instruction = instructions[index]
        if instruction.word is not None:
            index += 1
            continue

        end = index + 1
        while (
            end < len(instructions)
            and instructions[end].line == instruction.line
            and instructions[end].mnemonic == instruction.mnemonic
            and instructions[end].operands == instruction.operands
            and instructions[end].word is None
        ):
            end += 1

        slots = instructions[index:end]
        try:
            expanded = expand(instruction.mnemonic, instruction.operands, program.symbols)
            if expanded is None:
                expanded = [(instruction.mnemonic, instruction.operands)]

            if len(expanded) != len(slots):
                raise ValueError(
                    f"pass 1 reserved {len(slots)} words for {instruction.mnemonic}, "
                    f"expansion produced {len(expanded)}"
                )

            for slot, (mnemonic, operands) in zip(slots, expanded, strict=True):
                slot.word = encode(mnemonic, operands, slot.address, program, slot.line)
                slot.text = f"{mnemonic} {operands}".strip()
                slot.mnemonic = mnemonic
                slot.operands = operands
        except (ValueError, RuntimeError) as exc:
            add_error(program, instruction.line, str(exc))
            for slot in slots:
                slot.word = 0

        index = end
