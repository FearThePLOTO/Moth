import pytest

from moth.encode import i_type, j_type, r_type

# (MARS line, r_type args, expected word)
R_CASES = [
    ("add $t0, $t1, $t2", (0, 9, 10, 8, 0, 0x20), 0x012A4020),
    ("sub $s0, $s1, $s2", (0, 17, 18, 16, 0, 0x22), 0x02328022),
    ("and $t0, $t1, $t2", (0, 9, 10, 8, 0, 0x24), 0x012A4024),
    ("or $t0, $t1, $t2", (0, 9, 10, 8, 0, 0x25), 0x012A4025),
    ("slt $t0, $t1, $t2", (0, 9, 10, 8, 0, 0x2A), 0x012A402A),
    ("sll $t0, $t1, 4", (0, 0, 9, 8, 4, 0x00), 0x00094100),
    ("sll $t0, $t1, 31", (0, 0, 9, 8, 31, 0x00), 0x000947C0),
    ("srl $t0, $t1, 2", (0, 0, 9, 8, 2, 0x02), 0x00094082),
    ("sra $t0, $t1, 1", (0, 0, 9, 8, 1, 0x03), 0x00094043),
    ("jr $ra", (0, 31, 0, 0, 0, 0x08), 0x03E00008),
    ("syscall", (0, 0, 0, 0, 0, 0x0C), 0x0000000C),
    ("add $zero, $zero, $zero", (0, 0, 0, 0, 0, 0x20), 0x00000020),
]

# (MARS line, i_type args, expected word)
I_CASES = [
    ("addi $t0, $t1, 4", (0x08, 9, 8, 4), 0x21280004),
    ("addi $t0, $t1, -4", (0x08, 9, 8, -4), 0x2128FFFC),
    ("addi $t0, $zero, 32767", (0x08, 0, 8, 32767), 0x20087FFF),
    ("andi $t0, $t1, 255", (0x0C, 9, 8, 255), 0x312800FF),
    ("ori $t0, $t1, 255", (0x0D, 9, 8, 255), 0x352800FF),
    ("lui $t0, 0x1001", (0x0F, 0, 8, 0x1001), 0x3C081001),
    ("lw $t0, 4($s0)", (0x23, 16, 8, 4), 0x8E080004),
    ("sw $t0, -4($sp)", (0x2B, 29, 8, -4), 0xAFA8FFFC),
    ("beq $t0, $t1, next", (0x04, 8, 9, 2), 0x11090002),
    ("bne $t0, $t1, start", (0x05, 8, 9, -2), 0x1509FFFE),
]

# (MARS line, j_type args, expected word)
J_CASES = [
    ("j target1", (0x02, 0x0010001F), 0x0810001F),
    ("jal target1", (0x03, 0x0010001F), 0x0C10001F),
    ("j (target near top)", (0x02, 0x03FFFFFF), 0x0BFFFFFF),
]


@pytest.mark.parametrize(("line", "args", "expected"), R_CASES, ids=[c[0] for c in R_CASES])
def test_r_type(line, args, expected):
    assert r_type(*args) == expected


@pytest.mark.parametrize(("line", "args", "expected"), I_CASES, ids=[c[0] for c in I_CASES])
def test_i_type(line, args, expected):
    assert i_type(*args) == expected


@pytest.mark.parametrize(("line", "args", "expected"), J_CASES, ids=[c[0] for c in J_CASES])
def test_j_type(line, args, expected):
    assert j_type(*args) == expected


def test_negative_imm_does_not_touch_upper_fields():
    # -1 must only fill the low 16 bits, leaving opcode/rs/rt intact.
    assert i_type(0x08, 9, 8, -1) == 0x2128FFFF


def test_oversized_imm_is_masked_not_raised():
    assert i_type(0x08, 9, 8, 70000) == 0x21281170


def test_jump_target_is_masked_to_26_bits():
    assert j_type(0x02, 0xFFFFFFFF) == 0x0BFFFFFF
