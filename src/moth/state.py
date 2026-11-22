# src/moth/state.py
#
# TODO (when Lane 1 pushes bits.py):
#   Replace the temporary _mask32 below with: from moth.bits import u32
#   Only write_reg uses it. Nothing else changes.

from dataclasses import dataclass, field

from moth.memory import Memory
from moth.registers import REGISTER_NAME_TO_NUMBER

# Memory map
TEXT_START = 0x00400000
DATA_START = 0x10010000
STACK_START = 0x7FFFFFFC
KERNEL_START = 0x80000000

INITIAL_SP = STACK_START


def _mask32(value: int) -> int:
    # Temporary until Lane 1 provides bits.py. Replace with: from moth.bits import u32
    return value & 0xFFFFFFFF


def _validate_register_number(n: int) -> None:
    # bool is a subclass of int, so it is rejected explicitly.
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError("Register number must be an integer")

    # Without this check, read_reg(-1) would silently return $ra.
    if not 0 <= n < 32:
        raise ValueError(f"Invalid register number: {n}")


def _initial_regs() -> list[int]:
    regs = [0] * 32
    regs[REGISTER_NAME_TO_NUMBER["$sp"]] = INITIAL_SP
    return regs


@dataclass
class State:
    _regs: list[int] = field(default_factory=_initial_regs)
    pc: int = TEXT_START
    hi: int = 0
    lo: int = 0
    # default_factory so each State gets its own memory.
    memory: Memory = field(default_factory=Memory)

    def read_reg(self, n: int) -> int:
        _validate_register_number(n)
        # Register 0 always reads as 0, even if _regs[0] was modified directly.
        return 0 if n == 0 else self._regs[n]

    def write_reg(self, n: int, value: int) -> None:
        _validate_register_number(n)
        # Register 0 ignores writes.
        if n != 0:
            self._regs[n] = _mask32(value)
