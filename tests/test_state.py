# TO RUN: python -m pytest tests/test_state.py -v
# Expected: 22 passed

import pytest

from moth.memory import Memory
from moth.state import STACK_START, TEXT_START, State


def test_state_initialization():
    state = State()

    assert len(state.regs) == 32
    assert state.pc == TEXT_START
    assert state.hi == 0
    assert state.lo == 0
    assert isinstance(state.memory, Memory)


def test_stack_pointer_initialization():
    state = State()

    assert state.read_reg(29) == STACK_START


def test_register_zero_always_reads_zero():
    state = State()

    state.regs[0] = 123

    assert state.read_reg(0) == 0


def test_write_to_register_zero_is_ignored():
    state = State()

    state.write_reg(0, 123)

    assert state.regs[0] == 0
    assert state.read_reg(0) == 0


def test_write_and_read_register():
    state = State()

    state.write_reg(8, 123)

    assert state.read_reg(8) == 123


def test_register_31_is_writable():
    state = State()

    state.write_reg(31, 100)

    assert state.read_reg(31) == 100


def test_write_reg_masks_value_to_32_bits():
    state = State()

    state.write_reg(8, 0x1FFFFFFFF)

    assert state.read_reg(8) == 0xFFFFFFFF


def test_write_negative_value():
    state = State()

    state.write_reg(8, -1)

    assert state.read_reg(8) == 0xFFFFFFFF


@pytest.mark.parametrize("register_number", [-1, 32])
def test_read_reg_rejects_out_of_range_register_number(register_number):
    state = State()

    with pytest.raises(ValueError):
        state.read_reg(register_number)


@pytest.mark.parametrize("register_number", [-1, 32])
def test_write_reg_rejects_out_of_range_register_number(register_number):
    state = State()

    with pytest.raises(ValueError):
        state.write_reg(register_number, 10)


@pytest.mark.parametrize("register_number", [1.5, "8", None, True])
def test_read_reg_rejects_non_integer_register_number(register_number):
    state = State()

    with pytest.raises(TypeError):
        state.read_reg(register_number)


@pytest.mark.parametrize("register_number", [1.5, "8", None, True])
def test_write_reg_rejects_non_integer_register_number(register_number):
    state = State()

    with pytest.raises(TypeError):
        state.write_reg(register_number, 10)


def test_each_state_has_independent_registers():
    state1 = State()
    state2 = State()

    state1.write_reg(8, 100)

    assert state2.read_reg(8) == 0


def test_each_state_has_independent_memory():
    state1 = State()
    state2 = State()

    state1.memory.write_word(0x10010000, 123)

    assert state2.memory.read_word(0x10010000) == 0
