from dataclasses import dataclass

TEXT_BASE = 0x00400000

SOURCE = """        li   $t0, 0
        li   $t1, 5
loop:   add  $t0, $t0, $t1
        addi $t1, $t1, -1
        bne  $t1, $zero, loop
        j    end
end:
"""

LEFT_REGS = [
    "$zero",
    "$at",
    "$v0",
    "$v1",
    "$a0",
    "$a1",
    "$a2",
    "$a3",
    "$t0",
    "$t1",
    "$t2",
    "$t3",
    "$t4",
    "$t5",
    "$t6",
    "$t7",
]

RIGHT_REGS = [
    "$t8",
    "$t9",
    "$s0",
    "$s1",
    "$s2",
    "$s3",
    "$s4",
    "$s5",
    "$s6",
    "$s7",
    "$k0",
    "$k1",
    "$gp",
    "$sp",
    "$fp",
    "$ra",
]

PROGRAM = [
    (3, "add  $t0, $t0, $t1", 0x01094020),
    (4, "addi $t1, $t1, -1", 0x2129FFFF),
    (5, "bne  $t1, $zero, loop", 0x1520FFFD),
    (6, "j    end", 0x08100006),
]


@dataclass(frozen=True)
class Step:
    line: int
    address: int
    word: int
    pc: int
    reg_written: int | None
    value: int
    previous: int


@dataclass
class StepResult:
    word: int
    text: str
    line: int
    reg: str | None
    old: int
    new: int
    halted: bool


class FakeMachine:
    def __init__(self):
        self.pc = TEXT_BASE + 8
        self.steps = 0
        self.halted = False
        self.regs = {name: 0 for name in LEFT_REGS + RIGHT_REGS}
        self.regs["$t0"] = 0
        self.regs["$t1"] = 5
        self.loop_count = 0

    def snapshot(self):
        return self.regs.copy()

    def step(self):
        if self.halted:
            return None

        if self.pc == TEXT_BASE + 8:
            old = self.regs["$t0"]
            new = old + self.regs["$t1"]
            self.regs["$t0"] = new
            self.pc = TEXT_BASE + 12

            result = StepResult(
                word=0x01094020,
                text="add  $t0, $t0, $t1",
                line=3,
                reg="$t0",
                old=old,
                new=new,
                halted=False,
            )

        elif self.pc == TEXT_BASE + 12:
            old = self.regs["$t1"]
            new = old - 1
            self.regs["$t1"] = new
            self.pc = TEXT_BASE + 16

            result = StepResult(
                word=0x2129FFFF,
                text="addi $t1, $t1, -1",
                line=4,
                reg="$t1",
                old=old,
                new=new,
                halted=False,
            )

        elif self.pc == TEXT_BASE + 16:
            branch_taken = self.regs["$t1"] != self.regs["$zero"]

            if branch_taken:
                self.pc = TEXT_BASE + 8
            else:
                self.pc = TEXT_BASE + 20

            self.loop_count += 1

            result = StepResult(
                word=0x1520FFFD,
                text="bne  $t1, $zero, loop",
                line=5,
                reg=None,
                old=0,
                new=0,
                halted=False,
            )

        elif self.pc == TEXT_BASE + 20:
            word = 0x08100006

            target = ((word & 0x03FFFFFF) << 2) | ((self.pc + 4) & 0xF0000000)

            self.pc = target
            self.halted = True

            result = StepResult(
                word=word,
                text="j    end",
                line=6,
                reg=None,
                old=0,
                new=0,
                halted=True,
            )

        else:
            self.halted = True
            return None

        self.steps += 1
        self.regs["$zero"] = 0

        return result
