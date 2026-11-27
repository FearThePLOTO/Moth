import sys

from PySide6.QtWidgets import QApplication

from moth.ui.window import MothWindow


def main():
    app = QApplication(sys.argv)
    window = MothWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
