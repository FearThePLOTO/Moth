"""Encoders: turn instruction fields into a 32-bit machine word.

These functions mask and return a word. They never raise on a bad operand;
the assembler owns the errors because only it knows the line number.
"""

from moth.bits import u32


def r_type(opcode, rs, rt, rd, shamt, funct):
    """R layout: opcode[31:26] rs[25:21] rt[20:16] rd[15:11] shamt[10:6] funct[5:0]."""
    return u32((opcode << 26) | (rs << 21) | (rt << 16) | (rd << 11) | (shamt << 6) | funct)


def i_type(opcode, rs, rt, imm):
    """I layout: opcode[31:26] rs[25:21] rt[20:16] imm[15:0]."""
    return u32((opcode << 26) | (rs << 21) | (rt << 16) | (imm & 0xFFFF))


def j_type(opcode, target):
    """J layout: opcode[31:26] target[25:0]."""
    return u32((opcode << 26) | (target & 0x03FFFFFF))
