import ast
import re
from pathlib import Path

from moth.isa import BY_NAME
from moth.registers import REGISTER_NAME_TO_NUMBER, REGISTER_NUMBER_TO_NAME

_RULES_FILE = Path(__file__).with_name("PseudoOps.txt")
_TOKEN_RE = re.compile(
    r"'(?:\\.|[^'\\])+'|"
    r"\$[A-Za-z0-9_]+|"
    r"[+-]?(?:0[xX][0-9A-Fa-f]+|0[bB][01]+|0[oO][0-7]+|\d[\d_]*)|"
    r"[A-Za-z_.$][A-Za-z0-9_.$]*|[()+-]"
)
_TEMPLATE_TOKEN_RE = re.compile(
    r"RG\d+|NR\d+|OP\d+|"
    r"(?:VHL|VH|VL|LL|LH)\d+(?:P[1-4])?U?|"
    r"LLP(?:U|P[1-4])?|LHPA(?:P[1-4])?|LHPN|LHL|LAB|S32|BROFF\d{2}"
)
_SYMBOL_EXPRESSION_RE = re.compile(
    r"([A-Za-z_\.][A-Za-z0-9_.$]*)(?:([+-])((?:0[xX][0-9A-Fa-f]+)|(?:\d[\d_]*)))?"
)

_MEMORY_MNEMONICS = {
    "lb",
    "lbu",
    "lh",
    "lhu",
    "lw",
    "lwl",
    "lwr",
    "sb",
    "sh",
    "sw",
    "swl",
    "swr",
    "ll",
    "sc",
    "lwc1",
    "swc1",
}


def _split(operands, expected_count):
    """split operands at commas outside parentheses and quoted literals"""
    result = []
    current = []
    depth = 0
    quote = None
    escaped = False

    for character in operands:
        if escaped:
            current.append(character)
            escaped = False
            continue

        if quote is not None:
            if character == "\\":
                current.append(character)
                escaped = True
                continue
            if character == quote:
                quote = None
            current.append(character)
            continue

        if character in "\"'":
            quote = character
            current.append(character)
            continue

        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth < 0:
                raise ValueError("unexpected closing parenthesis in operands")

        if character == "," and depth == 0:
            result.append("".join(current).strip())
            current = []
        else:
            current.append(character)

    if depth != 0:
        raise ValueError("missing closing brackets in operands")

    if operands.strip():
        result.append("".join(current).strip())

    if len(result) != expected_count or any(item == "" for item in result):
        raise ValueError(f"expected {expected_count} operands, got {len(result)}")

    return result


def _imm(text):
    """read an int treating 32 bit hex values as signed like MARS"""
    literal = text.strip()
    if len(literal) >= 3 and literal[0] == "'" and literal[-1] == "'":
        try:
            char = ast.literal_eval(literal)
        except (ValueError, SyntaxError):
            char = None
        if isinstance(char, str) and len(char) == 1:
            return ord(char)
    try:
        if re.fullmatch(r"0[0-9]+", literal):
            value = int(literal, 10)
        else:
            value = int(text, 0)
    except ValueError as error:
        raise ValueError(f'"{text}" is not a number') from error

    literal = literal.lower()
    if literal.startswith("+"):
        literal = literal[1:]
    if literal.startswith("0x") and 0 <= value <= 0xFFFFFFFF:
        if value & 0x80000000:
            value -= 0x100000000

    return value


def _tokens(statement):
    found = _TOKEN_RE.findall(statement)
    remainder = _TOKEN_RE.sub("", statement)
    if remainder.strip(" \t,\r\n"):
        raise ValueError(f"could not parse operand text near {remainder.strip()!r}")

    tokens = []
    for token in found:
        if (
            token.startswith(("+", "-"))
            and len(token) > 1
            and tokens
            and _SYMBOL_EXPRESSION_RE.fullmatch(tokens[-1])
        ):
            tokens.append(token[0])
            tokens.append(token[1:])
        else:
            tokens.append(token)
    return tokens


def _load_rules():
    if not _RULES_FILE.is_file():
        raise RuntimeError(f"MARS pseudo-op definitions not found: {_RULES_FILE}")

    rules = {}
    unsupported_rules = {}

    for line in _RULES_FILE.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue

        columns = line.split("\t")
        source = columns[0].strip()
        if not source:
            continue

        source_tokens = _tokens(source)
        if not source_tokens:
            continue

        templates = []
        for column in columns[1:]:
            item = column.strip()
            if not item or item.startswith("#"):
                continue
            if item == "COMPACT":
                # Moth is never in compact memory mode, so the default form wins.
                break
            if item == "DBNOP":
                # Delayed branching is off, so this marker emits nothing.
                continue
            templates.append(item)

        supported = True
        for template in templates:
            output_mnemonic = template.split(None, 1)[0]
            if output_mnemonic not in BY_NAME:
                supported = False
                break

        if templates and supported:
            rules.setdefault(source_tokens[0], []).append((source_tokens, templates))
        elif templates:
            unsupported_rules.setdefault(source_tokens[0], []).append(source_tokens)

    return rules, unsupported_rules


_RULES, _UNSUPPORTED_RULES = _load_rules()


def _register_number(token):
    if not token.startswith("$"):
        return None

    name = token.lower()
    if name in REGISTER_NAME_TO_NUMBER:
        return REGISTER_NAME_TO_NUMBER[name]

    if name.startswith("$f") and name[2:].isdigit():
        number = int(name[2:])
        if 0 <= number <= 31:
            return number

    return None


def _is_register(token, floating=None):
    if not token.startswith("$"):
        return False

    name = token[1:]
    is_float = name.startswith("f") and name[1:].isdigit()
    if floating is True and not is_float:
        return False
    if floating is False and is_float:
        return False
    return _register_number(token) is not None


def _parse_symbol_expression(token):
    match = _SYMBOL_EXPRESSION_RE.fullmatch(token)
    if not match:
        return None

    label = match.group(1)
    addend = 0
    if match.group(2):
        addend = _imm(match.group(3))
        if match.group(2) == "-":
            addend = -addend
    return label, addend


def _symbol_value(token, symbols):
    expression = _parse_symbol_expression(token)
    if expression is None:
        raise ValueError(f'"{token}" is not a label')

    label, addend = expression
    if label not in symbols:
        raise ValueError(f'undefined label "{label}"')
    return symbols[label] + addend


def _symbol_value_at(tokens, index, symbols):
    value = _symbol_value(tokens[index], symbols)
    if index + 2 < len(tokens) and tokens[index + 1] in ("+", "-"):
        offset = _imm(tokens[index + 2])
        if tokens[index + 1] == "-":
            offset = -offset
        value += offset
    return value


def _number_matches(sample, actual):
    try:
        number = _imm(actual)
        sample_number = _imm(sample)
    except ValueError:
        return False

    if sample_number == 10:
        return 0 <= number <= 31
    if sample_number == 100:
        return 0 <= number <= 65535
    if sample_number == -100:
        return -32768 <= number <= 32767
    if sample_number == 100000:
        return -(2**31) <= number <= (2**32) - 1
    return number == sample_number


def _token_matches(sample, actual):
    if sample in ("(", ")"):
        return sample == actual

    if sample.startswith("$"):
        floating = sample.startswith("$f")
        return _is_register(actual, floating)

    if _parse_symbol_expression(sample) is not None:
        return _parse_symbol_expression(actual) is not None

    try:
        _imm(sample)
    except ValueError:
        return sample == actual
    return _number_matches(sample, actual)


def _matches(source_pattern, source_tokens):
    if len(source_pattern) != len(source_tokens):
        return False

    for expected, actual in zip(source_pattern, source_tokens, strict=True):
        if not _token_matches(expected, actual):
            return False

    return True


def _source_operand_count(source_tokens):
    """count operands in a rule signature brackets stay in their operand"""
    count = 0
    depth = 0
    previous = ""

    for token in source_tokens[1:]:
        if token == "(":
            if depth == 0 and previous.startswith("$"):
                count += 1
            depth += 1
        elif token == ")":
            depth -= 1
        elif depth == 0 and token not in ("+", "-") and previous not in ("+", "-"):
            count += 1
        previous = token

    return count


def _expected_operand_counts(mnemonic):
    counts = set()
    for source_pattern, _templates in _RULES.get(mnemonic, []):
        counts.add(_source_operand_count(source_pattern))
    return counts


def _signed_low(value):
    value &= 0xFFFF
    if value >= 0x8000:
        value -= 0x10000
    return value


def _substitute(token, source_tokens, symbols):
    if token.startswith("RG"):
        index = int(token[2:])
        return source_tokens[index]

    if token.startswith("NR"):
        index = int(token[2:])
        source_register = source_tokens[index]
        number = _register_number(source_register)
        if number is None or number >= 31:
            raise ValueError(f'cannot use next register after "{source_register}"')
        if source_register.startswith("$f"):
            return f"$f{number + 1}"
        return REGISTER_NUMBER_TO_NAME[number + 1]

    if token.startswith("OP"):
        index = int(token[2:])
        return source_tokens[index]

    if token == "LAB":
        return source_tokens[-1]

    if token == "S32":
        return str(32 - _imm(source_tokens[-1]))

    if token.startswith("BROFF"):
        return token[5]

    match = re.fullmatch(r"(VHL|VH|VL|LL|LH)(\d+)(?:P([1-4]))?(U)?", token)
    if match:
        kind, index_text, plus_text, unsigned = match.groups()
        index = int(index_text)
        adjustment = int(plus_text) if plus_text else 0
        source = source_tokens[index]

        if kind in ("VL", "VH", "VHL"):
            value = _imm(source) + adjustment
        else:
            value = _symbol_value_at(source_tokens, index, symbols) + adjustment

        value &= 0xFFFFFFFF
        if kind in ("VH", "LH"):
            high = value >> 16
            if value & 0x8000:
                high += 1
            return str(high & 0xFFFF)
        if kind in ("VHL",):
            return str((value >> 16) & 0xFFFF)
        if kind in ("VL",):
            low = value & 0xFFFF
            if unsigned:
                return str(low)
            return str(_signed_low(low))
        if kind == "LL":
            low = value & 0xFFFF
            if unsigned:
                return str(low)
            return str(_signed_low(low))

    if token == "LHL":
        value = _symbol_value_at(source_tokens, 2, symbols) & 0xFFFFFFFF
        return str((value >> 16) & 0xFFFF)

    if token in ("LLP", "LLPU", "LHPA", "LHPN") or token.startswith(("LLPP", "LHPAP")):
        value = _symbol_value_at(source_tokens, 2, symbols) & 0xFFFFFFFF
        if token.startswith("LLPP"):
            value += int(token[-1])
        if token.startswith("LHPAP"):
            value += int(token[-1])
        value &= 0xFFFFFFFF

        if token.startswith("LHPA") or token == "LHPN":
            high = value >> 16
            if token != "LHPN" and value & 0x8000:
                high += 1
            return str(high & 0xFFFF)

        low = value & 0xFFFF
        if token == "LLPU":
            return str(low)
        return str(_signed_low(low))

    raise ValueError(f"unsupported MARS template token {token}")


def _format_instruction(template):
    template = template.strip()
    first_space = template.find(" ")
    if first_space < 0:
        return (template, "")

    mnemonic = template[:first_space]
    operands = template[first_space + 1 :].strip()
    operands = re.sub(r"\s*,\s*", ", ", operands)
    operands = re.sub(r"\s*\(\s*", "(", operands)
    operands = re.sub(r"\s*\)", ")", operands)
    return (mnemonic, operands)


def _expand_templates(templates, source_tokens, symbols):
    instructions = []
    for template in templates:
        substituted = _TEMPLATE_TOKEN_RE.sub(
            lambda match: _substitute(match.group(0), source_tokens, symbols),
            template,
        )
        instruction = _format_instruction(substituted)
        if instruction is not None:
            instructions.append(instruction)

    return instructions


def _choose_rule(mnemonic, source_tokens):
    for source_pattern, templates in _RULES.get(mnemonic, []):
        if _matches(source_pattern, source_tokens):
            return templates
    return None


def _is_basic_memory_form(source_tokens):
    """true for ``lw $t0, 4($s0)``: a signed 16-bit offset plus a base register"""
    if len(source_tokens) != 6 or source_tokens[3] != "(" or source_tokens[5] != ")":
        return False
    if not _is_register(source_tokens[4], floating=False):
        return False
    try:
        return -32768 <= _imm(source_tokens[2]) <= 32767
    except ValueError:
        return False


def _uses_basic_immediate_form(mnemonic, source_tokens):
    """leave immediates to a real instruction when its field can hold them"""
    if mnemonic in _MEMORY_MNEMONICS:
        return _is_basic_memory_form(source_tokens)
    if mnemonic not in ("addi", "addiu", "andi", "ori", "xori"):
        return False
    if len(source_tokens) != 4:
        return False

    try:
        immediate = _imm(source_tokens[3])
    except ValueError:
        return False

    if mnemonic in ("addi", "addiu"):
        return -32768 <= immediate <= 32767
    return 0 <= immediate <= 65535


def _template_word_count(templates):
    return len(templates)


def expand(mnemonic, operands, symbols=None):
    """expand a MARS pseudo-op, or return None for an instruction the ISA encodes directly"""
    if symbols is None:
        symbols = {}

    if mnemonic == "nop":
        _split(operands, 0)
        return [("sll", "$zero, $zero, 0")]

    if mnemonic == "li":
        li_operands = _split(operands, 2)
        immediate = _imm(li_operands[1])
        if immediate < -(2**31) or immediate > (2**32) - 1:
            raise ValueError(f"immediate {immediate} does not fit in 32 bits")

    actual_count = _operand_count_hint(operands)
    operands_list = _split(operands, actual_count)
    expected_counts = _expected_operand_counts(mnemonic)

    if expected_counts and actual_count not in expected_counts:
        if mnemonic in BY_NAME:
            return None
        if len(expected_counts) == 1:
            expected_text = str(next(iter(expected_counts)))
        else:
            expected_text = " or ".join(str(value) for value in sorted(expected_counts))
        raise ValueError(f"expected {expected_text} operands, got {actual_count}")

    source_tokens = _tokens(mnemonic + " " + ", ".join(operands_list))

    if _uses_basic_immediate_form(mnemonic, source_tokens):
        return None

    templates = _choose_rule(mnemonic, source_tokens)
    if templates is None:
        unsupported_patterns = _UNSUPPORTED_RULES.get(mnemonic, [])
        if any(_matches(pattern, source_tokens) for pattern in unsupported_patterns):
            raise ValueError(f"{mnemonic} form needs an instruction the ISA does not have yet")

        if mnemonic in _RULES and mnemonic not in BY_NAME:
            raise ValueError(f"operands do not match a MARS {mnemonic} form")
        return None

    return _expand_templates(templates, source_tokens, symbols)


def _operand_count_hint(operands):
    """use the source rule samples to split ordinary comma separated inputs"""
    # A top-level split is enough to count operands; commas inside memory
    # addressing parentheses or quoted literals are ignored by _split.
    count = 0
    depth = 0
    has_text = False
    quote = None
    escaped = False
    for character in operands:
        if escaped:
            escaped = False
            has_text = True
            continue
        if quote is not None:
            if character == "\\":
                escaped = True
            elif character == quote:
                quote = None
            has_text = True
            continue
        if character in "\"'":
            quote = character
            has_text = True
            continue
        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
        elif character == "," and depth == 0:
            count += 1
            has_text = False
            continue
        if not character.isspace():
            has_text = True
    if has_text:
        count += 1
    return count


def word_count(mnemonic, operands, symbols=None):
    """return the pseudo expansion word count invalid lines reserve one"""
    try:
        if mnemonic == "nop":
            _split(operands, 0)
            return 1

        actual_count = _operand_count_hint(operands)
        operand_list = _split(operands, actual_count)
        expected_counts = _expected_operand_counts(mnemonic)
        if expected_counts and actual_count not in expected_counts:
            return 1

        source_tokens = _tokens(mnemonic + " " + ", ".join(operand_list))
        if _uses_basic_immediate_form(mnemonic, source_tokens):
            return 1

        templates = _choose_rule(mnemonic, source_tokens)
        if templates is None:
            return 1

        return _template_word_count(templates)
    except (ValueError, RuntimeError):
        return 1
