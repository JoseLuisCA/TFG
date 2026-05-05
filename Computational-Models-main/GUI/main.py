from pathlib import Path
import sys

from PySide6.QtWidgets import QApplication

# Ensure repository root is on sys.path so imports like `library.AFND` work
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "library"))

from windows.main_window import MainWindow


def main() -> int:
    app = QApplication()
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
