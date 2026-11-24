from moth.bits import field, sext16, u32


def test_u32_negative_one():
    assert u32(-1) == 0xFFFFFFFF


def test_u32_keeps_small_values():
    assert u32(5) == 5


def test_u32_wraps_overflow():
    assert u32(0x1_0000_0001) == 1


def test_sext16_negative():
    assert sext16(0xFFFF) == -1


def test_sext16_max_positive():
    assert sext16(0x7FFF) == 32767


def test_sext16_min_negative():
    assert sext16(0x8000) == -32768


def test_sext16_ignores_upper_bits():
    assert sext16(0x8E08FFFC) == -4


def test_field_rs():
    assert field(0x8E080004, 25, 21) == 16


def test_field_opcode():
    assert field(0x8E080004, 31, 26) == 0x23


def test_field_funct():
    assert field(0x00000020, 5, 0) == 0x20
