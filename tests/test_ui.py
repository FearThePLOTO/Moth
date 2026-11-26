
import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from moth.ui.window import MainWindow


def test_main_window():
    app = QApplication.instance() or QApplication([])
    assert app is not None

    window = MainWindow()

    assert window.windowTitle() == "MIPS Assembler and Debugger"
    assert window.source is not None
    assert window.bit_table is not None
    assert window.register_label is not None

    window.close()
