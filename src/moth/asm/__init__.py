from ..model import Program
from .line import parse_lines
from .pass1 import pass1


def assemble(source: str) -> Program:
    return pass1(parse_lines(source))
