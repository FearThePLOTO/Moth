
from dataclasses import dataclass


@dataclass
class Line:
    line_number: int
    text: str
    label: str | None
    mnemonic: str | None
    operands: str
    comment: str | None


def remove_comment(text: str) -> tuple[str, str | None]:
    """Separate assembly code from its comment."""
    in_quotes = False
    escaped = False

    for index, char in enumerate(text):
        if escaped:
            escaped = False
            continue

        if char == "\\" and in_quotes:
            escaped = True
            continue

        if char == '"':
            in_quotes = not in_quotes

        elif char == "#" and not in_quotes:
            code = text[:index]
            comment = text[index + 1:]
            return code, comment.strip()

    return text, None


def extract_label(code: str) -> tuple[str | None, str]:
    """Extract an optional label from the beginning of a line."""
    code = code.strip()

    if ":" not in code:
        return None, code

    label, remaining = code.split(":", 1)

    return label.strip(), remaining.strip()


def extract_instruction(code: str) -> tuple[str | None, str]:
    """Extract the mnemonic and operands."""
    code = code.strip()

    if not code:
        return None, ""

    parts = code.split(maxsplit=1)

    mnemonic = parts[0]
    operands = parts[1] if len(parts) > 1 else ""

    return mnemonic, operands


def parse_line(text: str, line_number: int) -> Line:
    """Parse one assembly source line."""
    code, comment = remove_comment(text)

    label, code = extract_label(code)

    mnemonic, operands = extract_instruction(code)

    return Line(
        line_number=line_number,
        text=text,
        label=label,
        mnemonic=mnemonic,
        operands=operands,
        comment=comment,
    )


def parse_lines(source: str) -> list[Line]:
    """Parse all lines in an assembly source string."""
    lines = []

    for line_number, text in enumerate(source.splitlines(), start=1):
        line = parse_line(text, line_number)
        lines.append(line)

    return lines
