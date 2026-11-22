# src/moth/registers.py

REGISTER_NAME_TO_NUMBER = {
    "$zero": 0,
    "$at": 1,
    "$gp": 28,
    "$sp": 29,
    "$fp": 30,
    "$ra": 31,
}

# Return value registers: $v0 - $v1
for i in range(2):
    REGISTER_NAME_TO_NUMBER[f"$v{i}"] = i + 2

# Argument registers: $a0 - $a3
for i in range(4):
    REGISTER_NAME_TO_NUMBER[f"$a{i}"] = i + 4

# Temporary registers: $t0 - $t7
for i in range(8):
    REGISTER_NAME_TO_NUMBER[f"$t{i}"] = i + 8

# Saved registers: $s0 - $s7
for i in range(8):
    REGISTER_NAME_TO_NUMBER[f"$s{i}"] = i + 16

# Temporary registers: $t8 - $t9 (numbers 24 and 25, not 16 and 17)
for i in range(2):
    REGISTER_NAME_TO_NUMBER[f"$t{i + 8}"] = i + 24

# Kernel registers: $k0 - $k1
for i in range(2):
    REGISTER_NAME_TO_NUMBER[f"$k{i}"] = i + 26

# Numeric register names: $8 - $31 (MARS accepts them)
for number in range(8, 32):
    REGISTER_NAME_TO_NUMBER[f"${number}"] = number

# Reverse mapping: register number to canonical name
REGISTER_NUMBER_TO_NAME = {}

for name, number in REGISTER_NAME_TO_NUMBER.items():
    if not name[1:].isdigit():
        REGISTER_NUMBER_TO_NAME[number] = name