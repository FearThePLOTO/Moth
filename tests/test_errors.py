from pathlib import Path

import pytest

from moth.asm import assemble

FIXTURES = Path(__file__).parent / "fixtures" / "broken"


@pytest.mark.parametrize(
    ("name", "line", "message"),
    [
        ("bad_label.asm", 2, "Invalid label"),
        ("bad_register.asm", 3, 'bad register "$invalid"'),
        ("missing_operand.asm", 3, "expected 3 operands for add"),
        ("unclosed_string.asm", 2, "Invalid .asciiz string"),
        ("unknown_mnemonic.asm", 3, 'unknown mnemonic "botato"'),
        ("wrong_directive.asm", 2, "Invalid .word value"),
    ],
)
def test_broken_fixtures(name, line, message):
    program = assemble((FIXTURES / name).read_text(encoding="utf-8"))
    assert len(program.errors) == 1
    assert program.errors[0].line == line
    assert message in program.errors[0].message
