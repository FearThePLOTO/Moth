"""Main window for MIPS Assembler and Debugger."""

import html
from string import Template

from PySide6.QtCore import QRect, QSize, Qt, QTimer
from PySide6.QtGui import (
    QAction,
    QColor,
    QFontDatabase,
    QKeySequence,
    QPainter,
    QTextCursor,
    QTextFormat,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from moth.ui.fake import (
    LEFT_REGS,
    PROGRAM,
    RIGHT_REGS,
    SOURCE,
    TEXT_BASE,
    FakeMachine,
)

# Brown and cream color palette.
C = {
    "bg": "#F5EFE6",
    "surface": "#FFFCF7",
    "surface_alt": "#F0E6D9",
    "border": "#DCCDBB",
    "text": "#594333",
    "muted": "#927D69",
    "accent": "#9A7051",
    "accent_dark": "#745139",
    "accent_soft": "#EADCCB",
    "accent_hover": "#E1CEB9",
    "disabled_bg": "#F1EBE3",
    "disabled_fg": "#B8AA9A",
}

STYLE = Template("""
QMainWindow, QWidget#central { background: $bg; }
QWidget { color: $text; }
QLabel { background: transparent; }

QMenuBar { background: $surface; border-bottom: 1px solid $border; padding: 4px 8px; }
QMenuBar::item { padding: 4px 14px; background: transparent; border-radius: 4px; }
QMenuBar::item:selected { background: $accent_soft; }
QMenu { background: $surface; border: 1px solid $border; padding: 4px; }
QMenu::item { padding: 6px 24px; border-radius: 4px; }
QMenu::item:selected { background: $accent_soft; color: $accent_dark; }
QMenu::item:disabled { color: $disabled_fg; }
QMenu::separator { height: 1px; background: $border; margin: 4px 8px; }

QToolButton {
    background: $accent_soft; border: 1px solid $accent; border-radius: 6px;
    padding: 6px 16px; color: $accent_dark;
}
QToolButton:hover { background: $accent_hover; }
QToolButton:pressed { background: $accent; color: $surface; }
QToolButton:disabled { background: $disabled_bg; border-color: $border; color: $disabled_fg; }

QFrame#panel { background: $surface; border: 1px solid $border; border-radius: 4px; }
QFrame#panelHead { background: $surface_alt; border: none; border-bottom: 1px solid $border; }
QFrame#field { background: $surface_alt; border: 1px solid $border; border-radius: 4px; }
QLabel#fieldLabel { color: $muted; font-size: 9pt; }
QLabel#muted { color: $muted; }
QLabel#accent { color: $accent; }

QTabWidget::pane { border: 1px solid $border; background: $surface; top: -1px; }
QTabBar::tab {
    padding: 7px 20px; background: $surface_alt; color: $muted;
    border: 1px solid $border; border-bottom: none; margin-right: 2px;
}
QTabBar::tab:selected { background: $surface; color: $text; border-bottom: 2px solid $accent; }
QTabBar::tab:hover:!selected { color: $accent; }

QPlainTextEdit, QTableWidget {
    border: none; background: $surface;
    selection-background-color: $accent_soft; selection-color: $text;
}
QHeaderView::section {
    background: $surface; color: $muted; border: none;
    border-bottom: 1px solid $border; padding: 4px 6px;
}
QPushButton {
    border: 1px solid $border; border-radius: 4px; padding: 3px 12px;
    background: $surface; color: $text;
}
QPushButton:hover { border-color: $accent; color: $accent; }

QStatusBar { background: $surface; border-top: 1px solid $border; }
QStatusBar QLabel { color: $muted; }

QScrollBar:vertical { background: transparent; width: 10px; margin: 0; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 0; }
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: $border; border-radius: 5px; min-height: 24px; min-width: 24px;
}
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover { background: $muted; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
""").substitute(C)


def mono(size=10):
    font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
    font.setPointSize(size)
    return font


def panel(title, body, extra=None):
    """A bordered box with a small header row."""
    box = QFrame()
    box.setObjectName("panel")
    lay = QVBoxLayout(box)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(0)

    head = QFrame()
    head.setObjectName("panelHead")
    row = QHBoxLayout(head)
    row.setContentsMargins(12, 8, 12, 8)
    row.addWidget(QLabel(title))
    row.addStretch()

    if extra is not None:
        row.addWidget(extra)

    lay.addWidget(head)
    lay.addWidget(body, 1)
    return box


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.number_width(), 0)

    def paintEvent(self, event):
        self.editor.paint_numbers(event)


class CodeEditor(QPlainTextEdit):
    """Plain text editor with line numbers and current-line highlight."""

    def __init__(self):
        super().__init__()
        self.setFont(mono(11))
        self.area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_margin)
        self.updateRequest.connect(self.update_area)
        self.cursorPositionChanged.connect(self.highlight_line)
        self.update_margin()
        self.highlight_line()

    def number_width(self):
        digits = max(2, len(str(max(1, self.blockCount()))))
        return 24 + self.fontMetrics().horizontalAdvance("9") * digits

    def update_margin(self):
        self.setViewportMargins(self.number_width(), 0, 0, 0)

    def update_area(self, rect, dy):
        if dy:
            self.area.scroll(0, dy)
        else:
            self.area.update(0, rect.y(), self.area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_margin()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.area.setGeometry(QRect(cr.left(), cr.top(), self.number_width(), cr.height()))

    def paint_numbers(self, event):
        painter = QPainter(self.area)
        painter.fillRect(event.rect(), QColor(C["surface_alt"]))

        block = self.firstVisibleBlock()
        number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        current = self.textCursor().blockNumber()
        height = self.fontMetrics().height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.setPen(QColor(C["accent_dark"] if number == current else C["muted"]))
                painter.drawText(
                    0,
                    top,
                    self.area.width() - 8,
                    height,
                    Qt.AlignmentFlag.AlignRight,
                    str(number + 1),
                )

            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            number += 1

    def highlight_line(self):
        selection = QTextEdit.ExtraSelection()
        selection.format.setBackground(QColor("#EADCCB"))
        selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()
        self.setExtraSelections([selection])

    def goto_line(self, line):
        block = self.document().findBlockByNumber(line - 1)
        if block.isValid():
            self.setTextCursor(QTextCursor(block))
            self.centerCursor()


class Field(QFrame):
    """One labelled box of the instruction word."""

    def __init__(self, label):
        super().__init__()
        self.setObjectName("field")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 6, 10, 8)
        lay.setSpacing(2)

        self.label = QLabel(label)
        self.label.setObjectName("fieldLabel")
        self.label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.value = QLabel("-")
        self.value.setFont(mono(12))
        self.value.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        lay.addWidget(self.label)
        lay.addWidget(self.value)

    def set(self, label, value):
        self.label.setText(label)
        self.value.setText(value)


class RegisterTable(QTableWidget):
    """32 registers displayed vertically in one name/hex pair."""

    def __init__(self):
        all_regs = LEFT_REGS + RIGHT_REGS
        super().__init__(len(all_regs), 2)

        self.setHorizontalHeaderLabels(["Register", "Hex"])
        self.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(24)

        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.setShowGrid(False)
        self.setFont(mono(10))

        self._cells = {}

        for row, name in enumerate(all_regs):
            self._cells[name] = row

            for col, value in enumerate((name, "0x00000000")):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
                self.setItem(row, col, item)

    def update_values(self, snapshot, changed=None):
        for name, row in self._cells.items():
            self.item(row, 1).setText(f"0x{snapshot[name]:08x}")

            color = QColor(C["accent_soft"]) if name == changed else QColor(C["surface"])

            self.item(row, 0).setBackground(color)
            self.item(row, 1).setBackground(color)


class MothWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("MIPS Assembler and Debugger")
        self.resize(1280, 860)

        self.machine = None
        self.state = "idle"

        # Timer makes Run visibly move through instructions.
        self.run_timer = QTimer(self)
        self.run_timer.setInterval(350)
        self.run_timer.timeout.connect(self._run_tick)

        self._build_actions()
        self._build_ui()
        self._build_menu()
        self.setStyleSheet(STYLE)

        self.registers.update_values(FakeMachine().snapshot())
        self.refresh_status()

    # ---------------------------------------------------------------- build

    def _action(self, text, slot, shortcut=None, enabled=True):
        action = QAction(text, self)
        action.triggered.connect(lambda _checked=False: slot())

        if shortcut:
            action.setShortcut(QKeySequence(shortcut))

        action.setEnabled(enabled)
        return action

    def _build_actions(self):
        self.act_open = self._action("Open", self.open_file, "Ctrl+O")
        self.act_assemble = self._action("Assemble", self.assemble, "F7")
        self.act_run = self._action("Run", self.run, "F5", enabled=False)
        self.act_step = self._action("Step", self.step, "F10", enabled=False)
        self.act_reset = self._action("Reset", self.reset, "Shift+F5", enabled=False)

    def _build_menu(self):
        bar = self.menuBar()

        file_menu = bar.addMenu("&File")
        file_menu.addAction(self.act_open)
        file_menu.addSeparator()
        file_menu.addAction(self._action("Exit", self.close))

        edit_menu = bar.addMenu("&Edit")
        edit_menu.addAction(self._action("Undo", self.editor.undo))
        edit_menu.addAction(self._action("Redo", self.editor.redo))
        edit_menu.addSeparator()
        edit_menu.addAction(self._action("Cut", self.editor.cut))
        edit_menu.addAction(self._action("Copy", self.editor.copy))
        edit_menu.addAction(self._action("Paste", self.editor.paste))

        view_menu = bar.addMenu("&View")
        view_menu.addAction(self._action("Clear terminal", self.terminal.clear))

        sim_menu = bar.addMenu("&Simulator")
        for act in (
            self.act_assemble,
            self.act_run,
            self.act_step,
            self.act_reset,
        ):
            sim_menu.addAction(act)

        help_menu = bar.addMenu("&Help")
        help_menu.addAction(self._action("About", self.about))

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(12, 8, 12, 8)
        root.setSpacing(10)

        # Toolbar.
        toolbar = QHBoxLayout()

        for act in (
            self.act_open,
            self.act_assemble,
            self.act_run,
            self.act_step,
            self.act_reset,
        ):
            button = QToolButton()
            button.setDefaultAction(act)
            button.setMinimumSize(64, 34)
            toolbar.addWidget(button)

        toolbar.addStretch()
        root.addLayout(toolbar)

        # Editor and Execute tabs.
        self.editor = CodeEditor()
        self.editor.setPlainText(SOURCE)

        self.execute_view = QPlainTextEdit()
        self.execute_view.setReadOnly(True)
        self.execute_view.setFont(mono(10))

        self.tabs = QTabWidget()
        self.tabs.addTab(self.editor, "Edit")
        self.tabs.addTab(self.execute_view, "Execute")

        left = QVBoxLayout()
        left.addWidget(self.tabs, 1)
        left.addWidget(self._build_word_panel())

        # Registers only; Current Instruction panel removed.
        self.registers = RegisterTable()

        right = QVBoxLayout()
        right.addWidget(panel("Registers", self.registers), 1)

        columns = QHBoxLayout()
        columns.setSpacing(16)
        columns.addLayout(left, 3)
        columns.addLayout(right, 2)

        root.addLayout(columns, 1)
        root.addWidget(self._build_terminal_panel())

        self.status = QLabel()
        self.status.setFont(mono(9))
        self.statusBar().addWidget(self.status)

    def _build_word_panel(self):
        body = QWidget()
        lay = QVBoxLayout(body)
        lay.setContentsMargins(12, 12, 12, 12)

        row = QHBoxLayout()
        self.fields = [Field(n) for n in ("opcode", "rs", "rt", "rd", "shamt", "funct")]

        for field in self.fields:
            row.addWidget(field)

        lay.addLayout(row)

        info = QHBoxLayout()

        self.word_hex = QLabel("0x00000000")
        self.word_hex.setFont(mono(12))

        self.type_label = QLabel("R-Type")
        self.type_label.setObjectName("accent")
        self.type_label.setFont(mono(10))

        self.word_text = QLabel("")
        self.word_text.setObjectName("accent")
        self.word_text.setFont(mono(10))

        info.addWidget(self.word_hex)
        info.addWidget(self.type_label)
        info.addSpacing(20)
        info.addWidget(self.word_text)
        info.addStretch()

        lay.addLayout(info)

        bits = QLabel("32 bits")
        bits.setObjectName("muted")

        return panel("Instruction word", body, bits)

    def _build_terminal_panel(self):
        self.terminal = QPlainTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setFont(mono(10))
        self.terminal.setMinimumHeight(100)

        clear = QPushButton("Clear")
        clear.clicked.connect(self.terminal.clear)

        box = panel("Messages / Terminal", self.terminal, clear)
        box.setMaximumHeight(200)

        return box

    # ------------------------------------------------------------- helpers

    def log(self, text, accent=False):
        if accent:
            self.terminal.appendHtml(
                f'<span style="color:{C["accent"]}">{html.escape(text)}</span>'
            )
        else:
            self.terminal.appendPlainText(text)

    def refresh_status(self):
        pc = self.machine.pc if self.machine else TEXT_BASE
        steps = self.machine.steps if self.machine else 0

        self.status.setText(
            f"PC 0x{pc:08x}      instruction {steps}      errors 0      {self.state}"
        )

    def show_word(self, word, text):
        opcode = (word >> 26) & 0x3F
        rs = (word >> 21) & 0x1F
        rt = (word >> 16) & 0x1F

        if opcode == 0:
            # R-Type
            instruction_type = "R-Type"

            parts = [
                ("opcode", opcode, 6),
                ("rs", rs, 5),
                ("rt", rt, 5),
                ("rd", (word >> 11) & 0x1F, 5),
                ("shamt", (word >> 6) & 0x1F, 5),
                ("funct", word & 0x3F, 6),
            ]

        elif opcode in (2, 3):
            # J-Type
            instruction_type = "J-Type"

            parts = [
                ("opcode", opcode, 6),
                ("address", word & 0x03FFFFFF, 26),
            ]

        else:
            # I-Type
            instruction_type = "I-Type"

            parts = [
                ("opcode", opcode, 6),
                ("rs", rs, 5),
                ("rt", rt, 5),
                ("immediate", word & 0xFFFF, 16),
            ]

        self.type_label.setText(instruction_type)

        for i, field in enumerate(self.fields):
            if i < len(parts):
                name, value, width = parts[i]
                field.set(name, format(value, f"0{width}b"))
                field.setVisible(True)
            else:
                field.setVisible(False)

        self.word_hex.setText(f"0x{word:08x}")
        self.word_text.setText(text)

    def show_result(self, res):
        self.show_word(res.word, res.text)
        self.registers.update_values(self.machine.snapshot(), res.reg)

        self.editor.goto_line(res.line)

    def show_next_instruction(self):
        """Highlight the next instruction based on the machine PC."""
        if self.machine is None or self.machine.halted:
            return

        index = (self.machine.pc - (TEXT_BASE + 8)) // 4

        if 0 <= index < len(PROGRAM):
            line, text, word = PROGRAM[index]
            self.editor.goto_line(line)
            self.show_word(word, text)

    # --------------------------------------------------------------- slots

    def open_file(self):
        self.stop_run()

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open assembly",
            "",
            "Assembly (*.asm *.s);;All files (*)",
        )

        if path:
            with open(path, encoding="utf-8") as fh:
                self.editor.setPlainText(fh.read())

            self.log(f"opened {path}")

    def assemble(self):
        self.stop_run()

        # TODO: replace with the real assembler once it exists.
        self.machine = FakeMachine()

        self.execute_view.setPlainText(
            "\n".join(
                f"0x{TEXT_BASE + 8 + 4 * i:08x}  0x{word:08x}  {text}"
                for i, (_line, text, word) in enumerate(PROGRAM)
            )
        )

        for act in (
            self.act_run,
            self.act_step,
            self.act_reset,
        ):
            act.setEnabled(True)

        self.registers.update_values(self.machine.snapshot())

        first_line, first_text, first_word = PROGRAM[0]
        self.editor.goto_line(first_line)
        self.show_word(first_word, first_text)

        self.state = "ready"
        self.log(f"assembled {len(PROGRAM)} instructions, 0 errors")
        self.refresh_status()

    def step(self):
        if self.machine is None or self.machine.halted:
            return

        self.stop_run()
        self._execute_one_step()

    def _execute_one_step(self):
        if self.machine is None or self.machine.halted:
            self.stop_run()
            return

        res = self.machine.step()

        if res is None:
            self.stop_run()
            return

        self.show_result(res)

        if res.halted:
            self.stop_run()
            self.log("done", accent=True)
            self.act_run.setEnabled(False)
            self.act_step.setEnabled(False)
            self.state = "halted"
        else:
            self.show_next_instruction()
            self.state = "running" if self.run_timer.isActive() else "paused"

        self.refresh_status()

    def run(self):
        if self.machine is None or self.machine.halted:
            return

        if not self.run_timer.isActive():
            self.state = "running"
            self.run_timer.start()
            self.refresh_status()

    def _run_tick(self):
        """Execute one instruction each timer interval."""
        if self.machine is None or self.machine.halted:
            self.stop_run()
            return

        self._execute_one_step()

    def stop_run(self):
        if self.run_timer.isActive():
            self.run_timer.stop()

    def reset(self):
        self.stop_run()

        self.machine = FakeMachine()

        self.act_run.setEnabled(True)
        self.act_step.setEnabled(True)

        self.registers.update_values(self.machine.snapshot())

        first_line, first_text, first_word = PROGRAM[0]
        self.editor.goto_line(first_line)
        self.show_word(first_word, first_text)

        self.state = "ready"
        self.log("reset")
        self.refresh_status()

    def about(self):
        QMessageBox.about(
            self,
            "About",
            "MIPS Assembler and Debugger",
        )
