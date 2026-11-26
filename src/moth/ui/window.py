from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .fake import PROGRAM, SNAPSHOTS, get_fields


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("MIPS Assembler and Debugger")
        self.resize(1100, 780)

        self.step_index = 0

        self.setStyleSheet("""
            QMainWindow, QWidget#centralWidget {
                background-color: #241817;
                color: #F2E6DC;
                font-family: Segoe UI;
            }

            QFrame#panel {
                background-color: #49302D;
                border: 1px solid #704A45;
                border-radius: 14px;
            }

            QLabel {
                color: #F2E6DC;
            }

            QLabel#panelTitle {
                color: #E5A9AE;
                font-size: 15px;
                font-weight: bold;
                padding-bottom: 5px;
            }

            QLabel#infoTitle {
                color: #D7B8AD;
                font-size: 12px;
            }

            QLabel#infoValue {
                color: #FFFFFF;
                font-size: 15px;
                font-weight: bold;
            }

            QTextEdit {
                background-color: #302220;
                color: #F2E6DC;
                border: 1px solid #704A45;
                border-radius: 8px;
                padding: 10px;
                font-family: Consolas;
                font-size: 14px;
            }

            QTableWidget {
                background-color: #302220;
                color: #F2E6DC;
                border: 1px solid #704A45;
                border-radius: 8px;
                gridline-color: #704A45;
                font-family: Consolas;
                font-size: 13px;
            }

            QHeaderView::section {
                background-color: #702D3B;
                color: #FFFFFF;
                padding: 8px;
                border: none;
                font-weight: bold;
            }

            QTableWidget::item {
                padding: 6px;
            }

            QPushButton#navigationButton {
                background-color: #702D3B;
                color: #FFF2EB;
                border: 1px solid #96505B;
                border-radius: 22px;
                padding: 9px 22px;
                font-size: 13px;
                font-weight: bold;
                min-width: 110px;
                min-height: 24px;
            }

            QPushButton#navigationButton:hover {
                background-color: #914653;
                border: 1px solid #C77B86;
            }

            QPushButton#navigationButton:pressed {
                background-color: #E5A9AE;
                color: #241817;
                border: 1px solid #E5A9AE;
            }

            QPushButton#navigationButton:disabled {
                background-color: #49302D;
                color: #907B74;
                border: 1px solid #60413C;
            }
        """)

        self.create_ui()
        self.update_ui()

    def create_panel(self, title):
        panel = QFrame()
        panel.setObjectName("panel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(10)

        title_label = QLabel(title)
        title_label.setObjectName("panelTitle")
        layout.addWidget(title_label)

        return panel, layout

    def create_info_item(self, title):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        title_label = QLabel(title)
        title_label.setObjectName("infoTitle")

        value_label = QLabel("--")
        value_label.setObjectName("infoValue")
        value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        layout.addWidget(title_label)
        layout.addWidget(value_label)

        return container, value_label

    def create_ui(self):
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(22, 18, 22, 18)
        main_layout.setSpacing(14)

        # Header
        header_layout = QHBoxLayout()

        app_title = QLabel("MIPS Studio")
        app_title.setStyleSheet("""
            font-size: 25px;
            font-weight: bold;
            color: #E5A9AE;
        """)

        subtitle = QLabel("Assembler & Debugger")
        subtitle.setStyleSheet("""
            font-size: 13px;
            color: #D7B8AD;
        """)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        title_layout.addWidget(app_title)
        title_layout.addWidget(subtitle)

        self.step_counter = QLabel("Step 1")
        self.step_counter.setStyleSheet("""
            color: #E5A9AE;
            font-size: 14px;
            font-weight: bold;
        """)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        header_layout.addWidget(self.step_counter)

        main_layout.addLayout(header_layout)

        # Upper row: Source and Register
        upper_layout = QHBoxLayout()
        upper_layout.setSpacing(14)

        # Source panel
        source_panel, source_layout = self.create_panel("Source Code")

        self.source = QTextEdit()
        self.source.setReadOnly(True)
        self.source.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.source.setPlainText("\n".join(PROGRAM))

        source_layout.addWidget(self.source)
        upper_layout.addWidget(source_panel, 55)

        # Register panel
        register_panel, register_layout = self.create_panel("Register Update")

        self.register_name = QLabel("$t0")
        self.register_label = self.register_name

        self.register_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.register_name.setStyleSheet("""
            color: #E5A9AE;
            font-size: 27px;
            font-weight: bold;
            padding: 10px;
        """)

        register_layout.addWidget(self.register_name)

        previous_container, self.previous_value = self.create_info_item("Previous Value")
        new_container, self.new_value = self.create_info_item("New Value")

        self.previous_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.new_value.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.previous_value.setStyleSheet("""
            font-size: 21px;
            color: #D7B8AD;
            padding: 8px;
        """)

        self.new_value.setStyleSheet("""
            font-size: 21px;
            color: #E5A9AE;
            padding: 8px;
        """)

        register_layout.addWidget(previous_container)
        register_layout.addWidget(new_container)
        register_layout.addStretch()

        upper_layout.addWidget(register_panel, 45)
        main_layout.addLayout(upper_layout, 3)

        # Instruction Details panel
        instruction_panel, instruction_layout = self.create_panel("Instruction Details")

        info_layout = QHBoxLayout()
        info_layout.setSpacing(30)

        address_container, self.address_label = self.create_info_item("Address")
        word_container, self.word_label = self.create_info_item("Machine Word")
        pc_container, self.pc_label = self.create_info_item("Next PC")

        info_layout.addWidget(address_container)
        info_layout.addWidget(word_container)
        info_layout.addWidget(pc_container)

        instruction_layout.addLayout(info_layout)

        self.bit_table = QTableWidget()
        self.bit_table.setColumnCount(2)
        self.bit_table.setHorizontalHeaderLabels(["Field", "Binary Value"])
        self.bit_table.setRowCount(6)
        self.bit_table.horizontalHeader().setStretchLastSection(True)
        self.bit_table.verticalHeader().setVisible(False)
        self.bit_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.bit_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)

        instruction_layout.addWidget(self.bit_table)
        main_layout.addWidget(instruction_panel, 4)

        # Navigation buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        buttons_layout.setSpacing(22)

        self.previous_button = QPushButton("Previous")
        self.previous_button.setObjectName("navigationButton")
        self.previous_button.clicked.connect(self.previous_step)

        self.next_button = QPushButton("Next")
        self.next_button.setObjectName("navigationButton")
        self.next_button.clicked.connect(self.next_step)

        buttons_layout.addWidget(self.previous_button)
        buttons_layout.addWidget(self.next_button)

        main_layout.addLayout(buttons_layout)

    def highlight_current_line(self, line_number):
        selections = []

        cursor = QTextCursor(self.source.document())
        cursor.movePosition(QTextCursor.MoveOperation.Start)

        for _ in range(line_number):
            if not cursor.movePosition(QTextCursor.MoveOperation.Down):
                break

        selection = QTextEdit.ExtraSelection()
        selection.format.setBackground(QColor("#70434A"))
        selection.format.setForeground(QColor("#FFFFFF"))
        selection.format.setProperty(QTextCharFormat.Property.FullWidthSelection, True)

        selection.cursor = cursor
        selection.cursor.select(QTextCursor.SelectionType.LineUnderCursor)

        selections.append(selection)
        self.source.setExtraSelections(selections)

    def update_ui(self):
        snapshot = SNAPSHOTS[self.step_index]

        # Step counter
        self.step_counter.setText(f"Step {self.step_index + 1} / {len(SNAPSHOTS)}")

        # Highlight current source line
        self.highlight_current_line(snapshot.line)

        # Instruction information
        self.address_label.setText(f"0x{snapshot.address:08X}")
        self.word_label.setText(f"0x{snapshot.word:08X}")
        self.pc_label.setText(f"0x{snapshot.pc:08X}")

        # Determine instruction type from opcode
        opcode = (snapshot.word >> 26) & 0x3F
        instruction_type = "R" if opcode == 0 else "I"

        fields = get_fields(snapshot.word, instruction_type)

        self.bit_table.setRowCount(len(fields))

        for row, (field_name, field_value) in enumerate(fields):
            self.bit_table.setItem(row, 0, QTableWidgetItem(str(field_name)))
            self.bit_table.setItem(row, 1, QTableWidgetItem(str(field_value)))

        self.bit_table.resizeColumnsToContents()

        # Register update
        if snapshot.reg_written is not None:
            register_names = {
                8: "$t0",
                9: "$t1",
            }

            register_name = register_names.get(snapshot.reg_written, f"$r{snapshot.reg_written}")

            self.register_name.setText(register_name)

            self.previous_value.setText(f"0x{snapshot.previous:08X}")
            self.new_value.setText(f"0x{snapshot.value:08X}")
        else:
            self.register_name.setText("No Register")
            self.previous_value.setText("--")
            self.new_value.setText("--")

        # Navigation buttons
        self.previous_button.setEnabled(self.step_index > 0)
        self.next_button.setEnabled(self.step_index < len(SNAPSHOTS) - 1)

    def next_step(self):
        if self.step_index < len(SNAPSHOTS) - 1:
            self.step_index += 1
            self.update_ui()

    def previous_step(self):
        if self.step_index > 0:
            self.step_index -= 1
            self.update_ui()
