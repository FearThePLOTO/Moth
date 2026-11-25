# src/moth/isa.py
#
# The instruction table. One row per instruction.

from dataclasses import dataclass


@dataclass(frozen=True)
class Instr:
    mnemonic: str
    fmt: str  # "R", "I" or "J"
    opcode: int  # top 6 bits
    funct: int | None = None  # bottom 6 bits, R-type only
    unsigned_imm: bool = False  # andi/ori/xori/lui: no sign extension


TABLE = [
    # R-type: opcode is always 0, funct tells them apart
    Instr("sll", "R", 0x00, 0x00),
    Instr("srl", "R", 0x00, 0x02),
    Instr("sra", "R", 0x00, 0x03),
    Instr("jr", "R", 0x00, 0x08),
    Instr("syscall", "R", 0x00, 0x0C),
    Instr("mfhi", "R", 0x00, 0x10),
    Instr("mflo", "R", 0x00, 0x12),
    Instr("mult", "R", 0x00, 0x18),
    Instr("div", "R", 0x00, 0x1A),
    Instr("add", "R", 0x00, 0x20),
    Instr("addu", "R", 0x00, 0x21),
    Instr("sub", "R", 0x00, 0x22),
    Instr("subu", "R", 0x00, 0x23),
    Instr("and", "R", 0x00, 0x24),
    Instr("or", "R", 0x00, 0x25),
    Instr("xor", "R", 0x00, 0x26),
    Instr("nor", "R", 0x00, 0x27),
    Instr("slt", "R", 0x00, 0x2A),
    Instr("sltu", "R", 0x00, 0x2B),
    # I-type: no funct
    Instr("beq", "I", 0x04),
    Instr("bne", "I", 0x05),
    Instr("addi", "I", 0x08),
    Instr("addiu", "I", 0x09),
    Instr("slti", "I", 0x0A),
    Instr("sltiu", "I", 0x0B),
    Instr("andi", "I", 0x0C, unsigned_imm=True),
    Instr("ori", "I", 0x0D, unsigned_imm=True),
    Instr("xori", "I", 0x0E, unsigned_imm=True),
    Instr("lui", "I", 0x0F, unsigned_imm=True),
    Instr("lb", "I", 0x20),
    Instr("lh", "I", 0x21),
    Instr("lw", "I", 0x23),
    Instr("lbu", "I", 0x24),
    Instr("lhu", "I", 0x25),
    Instr("sb", "I", 0x28),
    Instr("sh", "I", 0x29),
    Instr("sw", "I", 0x2B),
    # J-type: no funct
    Instr("j", "J", 0x02),
    Instr("jal", "J", 0x03),
]
# Lookup by name (used by the assembler)
BY_NAME = {i.mnemonic: i for i in TABLE}

# R-type lookup by (opcode, funct)
BY_R = {(i.opcode, i.funct): i for i in TABLE if i.fmt == "R"}

# I and J lookup by opcode
BY_OPCODE = {i.opcode: i for i in TABLE if i.fmt in ("I", "J")}
