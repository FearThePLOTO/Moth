# Lane 3 (Memory) - Test Summary

Files covered: `src/moth/registers.py`, `src/moth/memory.py` and `src/moth/state.py`.

## How to run

From the project folder:

```bash
python -m pytest tests/test_registers.py -v
python -m pytest tests/test_memory.py -v
python -m pytest tests/test_state.py -v
python -m pytest -v
```

## Result

| Test file | Tests | Result |
|---|---|---|
| `tests/test_registers.py` | 10 | 10 passed |
| `tests/test_memory.py` | 19 | 19 passed |
| `tests/test_state.py` | 22 | 22 passed |
| Lane 3 total | 51 | 51 passed |
| Whole project (`python -m pytest -v`) | 52 | 52 passed |

The whole-project run has one more test than Lane 3 because it also includes `tests/test_smoke.py`, which is not part of this lane.

## What we test

- **Registers:** names map to the right numbers (including the `$t8`/`$t9` trap), numeric names `$8` to `$31` are accepted, and the reverse dict returns canonical names.
- **Memory:** byte, half and word reads and writes, little-endian byte order, masking, unsigned reads, alignment errors that carry the address, and `load`.
- **State:** initial values, `$zero` always 0, register 31 writable, 32-bit masking, register number validation, and independence between `State` objects.

## Spec coverage

Every test listed in the Lane 3 sheet is covered:

| Required by the sheet | Covered by |
|---|---|
| `$zero` stays 0 after a write | `test_write_to_register_zero_is_ignored`, `test_register_zero_always_reads_zero` (state) |
| Register 31 is writable | `test_register_31_is_writable` (state) |
| Write `0x12345678` at `0x10010000`, read it as a word, then read the four bytes in the chosen order | `test_write_and_read_word`, `test_word_at_data_start_follows_byte_order` (memory) |
| An address nobody wrote returns 0 | `test_read_unwritten_memory_returns_zero` (memory) |
| A word read at `0x10010002` raises `AlignmentError` | `test_alignment_error_carries_address`, `test_word_alignment_error` (memory) |
| `load` puts a bytes object in, and the words read back correctly | `test_load_then_read_word` (memory) |
| A write of `-1` stores `0xFFFFFFFF` | `test_write_minus_one_stores_all_ones` (memory), `test_write_negative_value` (state) |

Extra tests beyond the sheet: half and byte reads and writes, masking, unsigned reads, register number validation, and independence between `State` objects.

---

## `tests/test_registers.py` (10 tests)

Dict names: `REGISTER_NAME_TO_NUMBER` (assembler side) and `REGISTER_NUMBER_TO_NAME` (screen side).

| # | Test | What it checks | Expected |
|---|---|---|---|
| 1 | `test_t8_t9_are_24_and_25` | `$t8` and `$t9` are not 16 and 17 | `$t8 = 24`, `$t9 = 25` |
| 2 | `test_saved_and_special_registers` | One sample from the saved, stack and return groups | `$s0 = 16`, `$sp = 29`, `$ra = 31` |
| 3 | `test_numeric_names_are_accepted` | First and last numeric name (MARS style) | `$8 = 8`, `$31 = 31` |
| 4 | `test_reverse_uses_canonical_names` | The reverse dict returns names, not `$8` | `8 -> $t0`, `24 -> $t8` |
| 5 | `test_reverse_has_32_entries` | One entry per register, no extras | 32 entries |
| 6 | `test_zero_and_at` | The two hand-written entries | `$zero = 0`, `$at = 1` |
| 7 | `test_v_and_a_registers` | First and last of the `$v` and `$a` loops | `$v0 = 2`, `$v1 = 3`, `$a0 = 4`, `$a3 = 7` |
| 8 | `test_all_numeric_names_8_to_31` | Every numeric name from `$8` to `$31` | each `$n = n` |
| 9 | `test_every_number_has_canonical_name` | Every number 0 to 31 has a name, and it is not numeric | no number missing |
| 10 | `test_round_trip` | Both dicts agree (number -> name -> number) | same number comes back |

## `tests/test_memory.py` (19 tests)

| # | Test | What it checks | Expected |
|---|---|---|---|
| 1 | `test_read_unwritten_memory_returns_zero` | Reading an address nobody wrote | byte, half and word all return 0 |
| 2 | `test_write_and_read_byte` | Byte round trip | write `0xAB`, read `0xAB` |
| 3 | `test_write_and_read_half` | Halfword round trip | write `0x1234`, read `0x1234` |
| 4 | `test_write_and_read_word` | Word round trip | write `0x12345678`, read `0x12345678` |
| 5 | `test_little_endian_byte_order` | Bytes of `0x12345678` at address 0 | `78 56 34 12` in addresses 0 to 3 |
| 6 | `test_half_byte_order` | Bytes of a halfword follow `BYTE_ORDER` | matches `(0x1234).to_bytes(2, BYTE_ORDER)` |
| 7 | `test_write_byte_masks_value` | Byte write keeps the low 8 bits | `0x1AB` stored as `0xAB` |
| 8 | `test_write_half_masks_value` | Half write keeps the low 16 bits | `0x12345678` stored as `0x5678` |
| 9 | `test_write_word_masks_value` | Word write keeps the low 32 bits | `0x123456789` stored as `0x23456789` |
| 10 | `test_write_minus_one_stores_all_ones` | Writing -1 | word `0xFFFFFFFF`, half `0xFFFF`, byte `0xFF` |
| 11 | `test_reads_are_unsigned` | Reads never return negative values | `0xFF` reads as 255, `0xFFFF` reads as 65535 |
| 12 | `test_half_alignment_error` | `read_half` at an odd address | raises `AlignmentError` |
| 13 | `test_word_alignment_error` | `read_word` at an address not divisible by 4 | raises `AlignmentError` |
| 14 | `test_write_half_alignment_error` | `write_half` at an odd address | raises `AlignmentError` |
| 15 | `test_write_word_alignment_error` | `write_word` at an address not divisible by 4 | raises `AlignmentError` |
| 16 | `test_alignment_error_carries_address` | The exception holds the bad address | `error.address == 0x10010002` |
| 17 | `test_load_bytes` | Bytes copied in land at consecutive addresses | `12 34 56 78` at addresses 0 to 3 |
| 18 | `test_load_then_read_word` | A word read after `load` is correct | equals `int.from_bytes(data, BYTE_ORDER)` |
| 19 | `test_word_at_data_start_follows_byte_order` | The sheet's case: `0x12345678` at `0x10010000` | four bytes match `to_bytes(4, BYTE_ORDER)` |

## `tests/test_state.py` (22 tests)

Parametrized tests count once per value, so 14 test functions produce 22 tests.

| # | Test | What it checks | Expected |
|---|---|---|---|
| 1 | `test_state_initialization` | A new `State` | 32 registers, `pc = TEXT_START`, `hi = 0`, `lo = 0`, `memory` is a `Memory` |
| 2 | `test_stack_pointer_initialization` | `$sp` (register 29) starts at the top of the stack | `read_reg(29) == STACK_START` |
| 3 | `test_register_zero_always_reads_zero` | Reading register 0 even if `_regs[0]` was changed directly | 0 |
| 4 | `test_write_to_register_zero_is_ignored` | Writing to register 0 | `_regs[0]` stays 0 |
| 5 | `test_write_and_read_register` | Normal register round trip | write 123 to `$8`, read 123 |
| 6 | `test_register_31_is_writable` | Register 31 accepts writes | write 100, read 100 |
| 7 | `test_write_reg_masks_value_to_32_bits` | Value wider than 32 bits | `0x1FFFFFFFF` stored as `0xFFFFFFFF` |
| 8 | `test_write_negative_value` | Writing -1 | `0xFFFFFFFF` |
| 9-10 | `test_read_reg_rejects_out_of_range_register_number` (-1, 32) | `read_reg` with a number outside 0 to 31 | raises `ValueError` |
| 11-12 | `test_write_reg_rejects_out_of_range_register_number` (-1, 32) | `write_reg` with a number outside 0 to 31 | raises `ValueError` |
| 13-16 | `test_read_reg_rejects_non_integer_register_number` (1.5, "8", None, True) | `read_reg` with a non-integer number | raises `TypeError` |
| 17-20 | `test_write_reg_rejects_non_integer_register_number` (1.5, "8", None, True) | `write_reg` with a non-integer number | raises `TypeError` |
| 21 | `test_each_state_has_independent_registers` | Two `State` objects do not share registers | write in one, the other still reads 0 |
| 22 | `test_each_state_has_independent_memory` | Two `State` objects do not share memory | write in one, the other still reads 0 |

---

## Notes

- `test_little_endian_byte_order` assumes `BYTE_ORDER = "little"` (confirmed with QtSPIM). Checked by switching the constant to `"big"`: only this test fails and the rest pass. The constant was then set back to `"little"`.
- Reads are unsigned. `lb` and `lh` sign-extend in the interpreter, not in `memory.py`.
- `_mask32` is temporary and appears in both `memory.py` and `state.py`. When Lane 1 pushes `bits.py`, both are replaced by `from moth.bits import u32`, and the tests are run again.
- `state.py` validates the register number (`ValueError` outside 0 to 31, `TypeError` for non-integers). This is an addition beyond the spec, so that `read_reg(-1)` cannot silently return `$ra`.
- Initial values in `State` (all registers 0, `pc = 0x00400000`, `$sp = 0x7FFFFFFC`) are our choices. The spec does not state them explicitly.
- Register names `$8` to `$31` are accepted as the sheet says. `$0` to `$7` are not added, because the sheet does not ask for them.
