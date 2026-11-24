"""Bit helpers shared by the encoder, decoder, interpreter and bit view."""


def u32(x):
    """Wrap any integer into an unsigned 32-bit value."""
    return x & 0xFFFFFFFF


def sext16(x):
    """Take the low 16 bits of x and read them as a signed number."""
    x &= 0xFFFF
    return x - 0x10000 if x & 0x8000 else x


def field(word, hi, lo):
    """Return bits hi..lo (inclusive) of word, shifted down to bit 0."""
    width = hi - lo + 1
    return (word >> lo) & ((1 << width) - 1)
