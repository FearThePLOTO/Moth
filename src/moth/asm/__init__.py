from ..model import Program
from .line import parse_lines
from .pass1 import pass1
from .pass2 import pass2


def assemble(source: str) -> Program:
    """Assemble source into a Program with encoded words and collected errors."""
    program = pass1(parse_lines(source))
    pass2(program)
    return program
