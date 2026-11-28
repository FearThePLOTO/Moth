import ast
import re

from ..model import Error, Instruction, Program
from .line import Line
from .pseudo import word_count

TEXT_START = 0x00400000
DATA_START = 0x10010000

MAX_ALIGN = 16
MAX_SPACE = 4 * 1024 * 1024
LABEL_PATTERN = re.compile(r"[A-Za-z_.$][A-Za-z0-9_.$]*")
DATA_DIRECTIVES = {".word", ".byte", ".space", ".asciiz"}


def add_error(errors: list[Error], line: Line, message: str) -> None:
    """Add an error associated with a source line."""
    errors.append(
        Error(
            line=line.line_number,
            column=1,
            message=message,
        )
    )


def split_operands(operands: str) -> list[str]:
    """Split comma-separated operands while respecting quoted strings."""
    result = []
    current = []
    in_quotes = False
    escaped = False

    for char in operands:
        if escaped:
            current.append(char)
            escaped = False
            continue

        if char == "\\" and in_quotes:
            current.append(char)
            escaped = True
            continue

        if char == '"':
            in_quotes = not in_quotes
            current.append(char)
            continue

        if char == "," and not in_quotes:
            result.append("".join(current).strip())
            current = []
        else:
            current.append(char)

    # Keep an empty last item so that "1," is reported as an error.
    if operands.strip():
        result.append("".join(current).strip())

    return result


def parse_integer(value: str) -> int:
    """Parse a decimal, hexadecimal, or binary integer. Leading zeros mean decimal."""
    text = value.strip()
    if re.fullmatch(r"[+-]?0[0-9]+", text):
        return int(text, 10)
    return int(text, 0)


def get_instruction_size(line: Line) -> int:
    """Return the number of machine words occupied by an instruction."""
    return word_count(line.mnemonic.lower(), line.operands)


def store_bytes(
    data: dict[int, int],
    address: int,
    value: int,
    size: int,
) -> None:
    """Store an integer as bytes using little-endian byte order."""

    value &= (1 << (size * 8)) - 1

    for offset in range(size):
        data[address + offset] = (value >> (offset * 8)) & 0xFF


def process_word(
    line: Line,
    data_address: int,
    data: dict[int, int],
    errors: list[Error],
) -> int:
    """Process .word and return the updated data address."""

    values = split_operands(line.operands)

    if not values:
        add_error(errors, line, ".word requires at least one value")
        return data_address

    for value in values:
        try:
            number = parse_integer(value)
        except ValueError:
            add_error(errors, line, f"Invalid .word value: {value}")
            continue

        if not -(2**31) <= number <= (2**32 - 1):
            add_error(errors, line, f".word value out of range: {value}")
            continue

        store_bytes(data, data_address, number, 4)
        data_address += 4

    return data_address


def process_byte(
    line: Line,
    data_address: int,
    data: dict[int, int],
    errors: list[Error],
) -> int:
    """Process .byte and return the updated data address."""

    values = split_operands(line.operands)

    if not values:
        add_error(errors, line, ".byte requires at least one value")
        return data_address

    for value in values:
        try:
            number = parse_integer(value)
        except ValueError:
            add_error(errors, line, f"Invalid .byte value: {value}")
            continue

        if not -128 <= number <= 255:
            add_error(errors, line, f".byte value out of range: {value}")
            continue

        data[data_address] = number & 0xFF
        data_address += 1

    return data_address


def process_space(
    line: Line,
    data_address: int,
    data: dict[int, int],
    errors: list[Error],
) -> int:
    """Process .space and reserve zero-filled bytes."""

    try:
        size = parse_integer(line.operands)
    except ValueError:
        add_error(errors, line, "Invalid .space size")
        return data_address

    if not 0 <= size <= MAX_SPACE:
        add_error(errors, line, f".space size must be 0 to {MAX_SPACE}")
        return data_address

    for offset in range(size):
        data[data_address + offset] = 0

    return data_address + size


def process_asciiz(
    line: Line,
    data_address: int,
    data: dict[int, int],
    errors: list[Error],
) -> int:
    """Process .asciiz and append a null terminator."""

    text = line.operands.strip()

    try:
        value = ast.literal_eval(text)

        if not text.startswith('"') or not isinstance(value, str):
            raise ValueError

    except (ValueError, SyntaxError):
        add_error(errors, line, "Invalid .asciiz string")
        return data_address

    encoded = value.encode("utf-8") + b"\x00"

    for byte in encoded:
        data[data_address] = byte
        data_address += 1

    return data_address


def align_address(
    address: int,
    exponent: int,
) -> int:
    """Align an address to a multiple of 2**exponent."""

    alignment = 1 << exponent

    return (address + alignment - 1) & ~(alignment - 1)


def pass1(lines: list[Line]) -> Program:
    """Perform the first pass of the assembler."""

    # Initial memory addresses
    text_address = TEXT_START
    data_address = DATA_START

    # Current section
    current_section = "text"

    # Program components
    instructions: list[Instruction] = []
    symbols: dict[str, int] = {}
    errors: list[Error] = []
    data: dict[int, int] = {}

    # Labels still waiting for an address
    pending: list[str] = []
    seen: set[str] = set()
    auto_align = True

    def place_labels() -> None:
        address = text_address if current_section == "text" else data_address

        for label in pending:
            symbols[label] = address

        pending.clear()

    # Process source lines
    for line in lines:
        mnemonic = line.mnemonic.lower() if line.mnemonic is not None else None

        # Skip empty lines and comment-only lines
        if mnemonic is None and line.label is None:
            continue

        if line.label is not None:
            if not LABEL_PATTERN.fullmatch(line.label):
                add_error(errors, line, f'Invalid label: "{line.label}"')

            elif line.label in seen:
                add_error(errors, line, f"Duplicate label: {line.label}")

            else:
                seen.add(line.label)
                pending.append(line.label)

        # A label without an instruction is valid
        if mnemonic is None:
            continue

        if mnemonic.endswith(":"):
            add_error(errors, line, "Only one label is allowed per line")
            continue

        # Handle section directives
        if mnemonic in {".text", ".data"}:
            # Labels written before the switch stay in the old section.
            place_labels()
            current_section = mnemonic[1:]
            auto_align = True
            continue

        if mnemonic == ".globl":
            continue

        # Handle alignment
        if mnemonic == ".align":
            try:
                exponent = parse_integer(line.operands)
            except ValueError:
                add_error(errors, line, "Invalid .align exponent")
                continue

            if not 0 <= exponent <= MAX_ALIGN:
                add_error(
                    errors,
                    line,
                    f".align exponent must be 0 to {MAX_ALIGN}",
                )
                continue

            # ".align 0" turns off automatic .word alignment, as in MARS.
            if exponent == 0:
                auto_align = False
                continue

            if current_section == "text":
                text_address = align_address(
                    text_address,
                    exponent,
                )
            else:
                new_address = align_address(
                    data_address,
                    exponent,
                )

                # Fill alignment padding with zeros
                for address in range(data_address, new_address):
                    data[address] = 0

                data_address = new_address

            continue

        # Handle data directives
        if mnemonic in DATA_DIRECTIVES:
            if current_section != "data":
                add_error(
                    errors,
                    line,
                    f"{mnemonic} must be used inside .data",
                )
                continue

            if mnemonic == ".word" and auto_align:
                new_address = align_address(data_address, 2)

                for address in range(data_address, new_address):
                    data[address] = 0

                data_address = new_address

            place_labels()

            if mnemonic == ".word":
                data_address = process_word(
                    line,
                    data_address,
                    data,
                    errors,
                )

            elif mnemonic == ".byte":
                data_address = process_byte(
                    line,
                    data_address,
                    data,
                    errors,
                )

            elif mnemonic == ".space":
                data_address = process_space(
                    line,
                    data_address,
                    data,
                    errors,
                )

            elif mnemonic == ".asciiz":
                data_address = process_asciiz(
                    line,
                    data_address,
                    data,
                    errors,
                )

            continue

        if mnemonic.startswith("."):
            add_error(errors, line, f'Unknown directive "{line.mnemonic}"')
            continue

        # Instructions are only valid in the text section
        if current_section != "text":
            add_error(
                errors,
                line,
                "Instructions must be inside .text",
            )
            continue

        place_labels()

        # Calculate instruction size
        size = get_instruction_size(line)

        # One record per word, so pass 2 can fill each word in place.
        for offset in range(size):
            instructions.append(
                Instruction(
                    address=text_address + offset * 4,
                    line=line.line_number,
                    text=line.text,
                    mnemonic=line.mnemonic,
                    operands=line.operands,
                    word=None,
                )
            )

        text_address += size * 4

    # Labels at the end of the file
    place_labels()

    # Return the assembled program structure
    return Program(
        instructions=instructions,
        symbols=symbols,
        errors=errors,
        data=data,
    )
