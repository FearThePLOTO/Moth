 
from dataclasses import dataclass


@dataclass(frozen=True)
class Step:
    line: int
    address: int
    word: int
    pc: int
    reg_written: int | None
    value: int
    previous: int


PROGRAM = [
    "li     $t0, 0",
    "li     $t1, 5",
    "loop:  add    $t0, $t0, $t1",
    "       addi   $t1, $t1, -1",
    "       bne    $t1, $zero, loop"
]


SNAPSHOTS = [
    # Loop iteration 1
    Step(2, 0x00400008, 0x01094020, 0x0040000C, 8, 5, 0),
    Step(3, 0x0040000C, 0x2129FFFF, 0x00400010, 9, 4, 5),
    Step(4, 0x00400010, 0x1520FFFD, 0x00400008, None, 0, 0),

    # Loop iteration 2
    Step(2, 0x00400008, 0x01094020, 0x0040000C, 8, 9, 5),
    Step(3, 0x0040000C, 0x2129FFFF, 0x00400010, 9, 3, 4),
    Step(4, 0x00400010, 0x1520FFFD, 0x00400008, None, 0, 0),

    # Loop iteration 3
    Step(2, 0x00400008, 0x01094020, 0x0040000C, 8, 12, 9),
    Step(3, 0x0040000C, 0x2129FFFF, 0x00400010, 9, 2, 3),
    Step(4, 0x00400010, 0x1520FFFD, 0x00400008, None, 0, 0),

    # Loop iteration 4
    Step(2, 0x00400008, 0x01094020, 0x0040000C, 8, 14, 12),
    Step(3, 0x0040000C, 0x2129FFFF, 0x00400010, 9, 1, 2),
    Step(4, 0x00400010, 0x1520FFFD, 0x00400008, None, 0, 0),

    # Loop iteration 5
    Step(2, 0x00400008, 0x01094020, 0x0040000C, 8, 15, 14),
    Step(3, 0x0040000C, 0x2129FFFF, 0x00400010, 9, 0, 1),
    Step(4, 0x00400010, 0x1520FFFD, 0x00400014, None, 0, 0),
]


def get_fields(word, instruction_type):
    opcode = (word >> 26) & 0x3F
    rs = (word >> 21) & 0x1F
    rt = (word >> 16) & 0x1F

    if instruction_type == "R":
        rd = (word >> 11) & 0x1F
        shamt = (word >> 6) & 0x1F
        funct = word & 0x3F

        return [
            ("Opcode", format(opcode, "06b")),
            ("RS", format(rs, "05b")),
            ("RT", format(rt, "05b")),
            ("RD", format(rd, "05b")),
            ("Shamt", format(shamt, "05b")),
            ("Funct", format(funct, "06b"))
        ]

    immediate = word & 0xFFFF

    return [
        ("Opcode", format(opcode, "06b")),
        ("RS", format(rs, "05b")),
        ("RT", format(rt, "05b")),
        ("Immediate", format(immediate, "016b"))
    ]
