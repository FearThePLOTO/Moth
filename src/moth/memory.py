# src/moth/memory.py
#
# TODO (when Lane 1 pushes bits.py):
#   Replace the temporary _mask32 below with: from moth.bits import u32
#   Only the writes (write_half, write_word) use it. Nothing else changes.


BYTE_ORDER = "little"  # or "big"


def _mask32(value: int) -> int:
    # Temporary until Lane 1 provides bits.py. Replace with: from moth.bits import u32
    return value & 0xFFFFFFFF


class AlignmentError(Exception):
    def __init__(self, address: int):
        self.address = address
        super().__init__(f"Unaligned memory access at address 0x{address:08X}")


class Memory:
    def __init__(self):
        # Sparse: address -> byte. Unwritten addresses read as 0.
        self.data: dict[int, int] = {}

    def _check_alignment(self, addr: int, size: int) -> None:
        if addr % size != 0:
            raise AlignmentError(addr)

    def _read_bytes(self, addr: int, size: int) -> int:
        raw = bytes(self.read_byte(addr + i) for i in range(size))
        return int.from_bytes(raw, BYTE_ORDER)

    def _write_bytes(self, addr: int, value: int, size: int) -> None:
        raw = value.to_bytes(size, BYTE_ORDER)
        for i, byte in enumerate(raw):
            self.write_byte(addr + i, byte)

    # Reads are always unsigned; lb/lh sign-extend in the interpreter.

    def read_byte(self, addr: int) -> int:
        return self.data.get(addr, 0)

    def read_half(self, addr: int) -> int:
        self._check_alignment(addr, 2)
        return self._read_bytes(addr, 2)

    def read_word(self, addr: int) -> int:
        self._check_alignment(addr, 4)
        return self._read_bytes(addr, 4)

    # Writes mask the value to the width being written.

    def write_byte(self, addr: int, value: int) -> None:
        self.data[addr] = value & 0xFF

    def write_half(self, addr: int, value: int) -> None:
        self._check_alignment(addr, 2)
        self._write_bytes(addr, _mask32(value) & 0xFFFF, 2)

    def write_word(self, addr: int, value: int) -> None:
        self._check_alignment(addr, 4)
        self._write_bytes(addr, _mask32(value), 4)

    def load(self, addr: int, data: bytes) -> None:
        # Used by the assembler to copy raw bytes in.
        for i, byte in enumerate(data):
            self.write_byte(addr + i, byte)