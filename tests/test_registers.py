# TO RUN: python -m pytest tests/test_registers.py -v
# Expected: 10 passed

from moth.registers import REGISTER_NAME_TO_NUMBER as N
from moth.registers import REGISTER_NUMBER_TO_NAME as R


def test_t8_t9_are_24_and_25():
    assert N["$t8"] == 24
    assert N["$t9"] == 25


def test_saved_and_special_registers():
    assert N["$s0"] == 16
    assert N["$sp"] == 29
    assert N["$ra"] == 31


def test_numeric_names_are_accepted():
    assert N["$0"] == 0
    assert N["$31"] == 31


def test_reverse_uses_canonical_names():
    assert R[8] == "$t0"
    assert R[24] == "$t8"


def test_reverse_has_32_entries():
    assert len(R) == 32


def test_zero_and_at():
    assert N["$zero"] == 0
    assert N["$at"] == 1


def test_v_and_a_registers():
    assert N["$v0"] == 2
    assert N["$v1"] == 3
    assert N["$a0"] == 4
    assert N["$a3"] == 7


def test_all_numeric_names_0_to_31():
    for number in range(32):
        assert N[f"${number}"] == number


def test_every_number_has_canonical_name():
    for number in range(32):
        assert number in R
        assert not R[number][1:].isdigit()


def test_round_trip():
    for number, name in R.items():
        assert N[name] == number
