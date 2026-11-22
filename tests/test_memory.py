# TO RUN: python -m pytest tests/test_memory.py -v
# Expected: 19 passed
#
# Note: test_little_endian_byte_order assumes BYTE_ORDER = "little".
# If BYTE_ORDER is changed to "big", only that test is expected to fail.

import pytest

from moth.memory import BYTE_ORDER, AlignmentError, Memory


def test_read_unwritten_memory_returns_zero():
    memory = Memory()

    assert memory.read_byte(0) == 0
    assert memory.read_half(0) == 0
    assert memory.read_word(0) == 0


def test_write_and_read_byte():
    memory = Memory()

    memory.write_byte(0, 0xAB)

    assert memory.read_byte(0) == 0xAB


def test_write_and_read_half():
    memory = Memory()

    memory.write_half(0, 0x1234)

    assert memory.read_half(0) == 0x1234


def test_write_and_read_word():
    memory = Memory()

    memory.write_word(0, 0x12345678)

    assert memory.read_word(0) == 0x12345678


def test_little_endian_byte_order():
    memory = Memory()

    memory.write_word(0, 0x12345678)

    assert memory.read_byte(0) == 0x78
    assert memory.read_byte(1) == 0x56
    assert memory.read_byte(2) == 0x34
    assert memory.read_byte(3) == 0x12


def test_half_byte_order():
    memory = Memory()

    memory.write_half(0, 0x1234)

    expected = (0x1234).to_bytes(2, BYTE_ORDER)

    assert bytes([memory.read_byte(0), memory.read_byte(1)]) == expected


def test_write_byte_masks_value():
    memory = Memory()

    memory.write_byte(0, 0x1AB)

    assert memory.read_byte(0) == 0xAB


def test_write_half_masks_value():
    memory = Memory()

    memory.write_half(0, 0x12345678)

    assert memory.read_half(0) == 0x5678


def test_write_word_masks_value():
    memory = Memory()

    memory.write_word(0, 0x123456789)

    assert memory.read_word(0) == 0x23456789


def test_write_minus_one_stores_all_ones():
    memory = Memory()

    memory.write_word(0, -1)
    memory.write_half(8, -1)
    memory.write_byte(12, -1)

    assert memory.read_word(0) == 0xFFFFFFFF
    assert memory.read_half(8) == 0xFFFF
    assert memory.read_byte(12) == 0xFF


def test_reads_are_unsigned():
    memory = Memory()

    memory.write_byte(0, 0xFF)
    memory.write_half(2, 0xFFFF)

    assert memory.read_byte(0) == 255
    assert memory.read_half(2) == 65535


def test_half_alignment_error():
    memory = Memory()

    with pytest.raises(AlignmentError):
        memory.read_half(1)


def test_word_alignment_error():
    memory = Memory()

    with pytest.raises(AlignmentError):
        memory.read_word(2)


def test_write_half_alignment_error():
    memory = Memory()

    with pytest.raises(AlignmentError):
        memory.write_half(1, 0x1234)


def test_write_word_alignment_error():
    memory = Memory()

    with pytest.raises(AlignmentError):
        memory.write_word(2, 0x12345678)


def test_alignment_error_carries_address():
    memory = Memory()

    with pytest.raises(AlignmentError) as error:
        memory.read_word(0x10010002)

    assert error.value.address == 0x10010002


def test_load_bytes():
    memory = Memory()

    memory.load(0, bytes([0x12, 0x34, 0x56, 0x78]))

    assert memory.read_byte(0) == 0x12
    assert memory.read_byte(1) == 0x34
    assert memory.read_byte(2) == 0x56
    assert memory.read_byte(3) == 0x78


def test_load_then_read_word():
    memory = Memory()
    data = bytes([0x12, 0x34, 0x56, 0x78])

    memory.load(0x10010000, data)

    assert memory.read_word(0x10010000) == int.from_bytes(data, BYTE_ORDER)


def test_word_at_data_start_follows_byte_order():
    memory = Memory()

    memory.write_word(0x10010000, 0x12345678)

    expected = (0x12345678).to_bytes(4, BYTE_ORDER)
    actual = bytes(memory.read_byte(0x10010000 + i) for i in range(4))
    assert actual == expected
