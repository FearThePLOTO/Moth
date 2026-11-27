import os

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from moth.ui.fake import PROGRAM
from moth.ui.window import MothWindow


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_window_creation(app):
    window = MothWindow()

    assert window.windowTitle() == "MIPS Assembler and Debugger"
    assert window.editor is not None
    assert window.registers is not None


def test_assemble(app):
    window = MothWindow()
    window.assemble()

    assert window.machine is not None
    assert window.state == "ready"
    assert len(PROGRAM) == 4
    assert window.act_step.isEnabled()
    assert window.act_run.isEnabled()
    assert "assembled 4 instructions" in window.terminal.toPlainText()


def test_instruction_types(app):
    window = MothWindow()

    window.show_word(0x01094020, "add $t0, $t0, $t1")
    assert window.type_label.text() == "R-Type"

    window.show_word(0x2129FFFF, "addi $t1, $t1, -1")
    assert window.type_label.text() == "I-Type"

    window.show_word(0x08100006, "j end")
    assert window.type_label.text() == "J-Type"


def test_step(app):
    window = MothWindow()
    window.assemble()

    window.step()
    assert window.machine.steps == 1
    assert window.machine.regs["$t0"] == 5

    window.step()
    assert window.machine.steps == 2
    assert window.machine.regs["$t1"] == 4


def test_reset(app):
    window = MothWindow()
    window.assemble()

    window.step()
    window.step()
    window.reset()

    assert window.machine.steps == 0
    assert window.machine.regs["$t0"] == 0
    assert window.machine.regs["$t1"] == 5
    assert window.state == "ready"


def test_program_execution(app):
    window = MothWindow()
    window.assemble()

    while not window.machine.halted:
        window.step()

    assert window.machine.halted
    assert window.machine.regs["$t0"] == 15
    assert window.machine.regs["$t1"] == 0
    assert window.machine.steps == 16


def test_screenshot(app):
    window = MothWindow()
    window.show()

    assert not window.grab().isNull()