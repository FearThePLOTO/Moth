from pathlib import Path

import pytest

from moth.asm import assemble

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize("name", ["bom.asm", "crlf.asm", "utf8.asm", "tabs.asm"])
def test_encoding_fixtures_assemble(name):
    program = assemble((FIXTURES / name).read_bytes().decode("utf-8-sig"))
    assert program.errors == []
    assert program.symbols["main"] == 0x00400000
    assert [instruction.word for instruction in program.instructions] == [
        0x012A4020,
        0x2402000A,
        0x0000000C,
    ]
