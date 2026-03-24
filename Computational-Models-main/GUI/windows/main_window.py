from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from canvas.workspace_canvas import WorkspaceCanvas
from widgets.draggable_tool_button import DraggableToolButton


ICONS_DIR = Path(__file__).resolve().parents[1] / "icons"


class MainWindow(QMainWindow):
    _tool_button_style = (
        "font-size: 24px;"
        "background-color: white;"
        "border: 1px solid #d1d5db;"
        "border-radius: 10px;"
    )
    _active_tool_button_style = (
        "font-size: 24px;"
        "background-color: #e5e7eb;"
        "border: 1px solid #9ca3af;"
        "border-radius: 10px;"
    )

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AutoSandbox")
        self.setGeometry(100, 100, 800, 600)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.home_page = self._build_home_page()
        self.fa_page = self._build_fa_page()

        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.fa_page)
        self.stack.setCurrentWidget(self.home_page)

    def _build_home_page(self) -> QWidget:
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(40, 32, 40, 32)
        main_layout.setSpacing(24)

        title = QLabel("AutoSandbox", self)
        title.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(28)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #1f2937;")

        buttons = QWidget()
        buttons_layout = QVBoxLayout(buttons)
        buttons_layout.setSpacing(16)

        button1 = QPushButton("Finite Automaton")
        button2 = QPushButton("Stack Automaton")
        button3 = QPushButton("Exit")

        for button in (button1, button2, button3):
            button.setMinimumHeight(64)
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            button.setStyleSheet(
                "font-size: 18px;"
                "font-weight: 600;"
                "padding: 12px;"
            )

        buttons_layout.addWidget(button1)
        buttons_layout.addWidget(button2)
        buttons_layout.addWidget(button3)

        button1.clicked.connect(lambda: self.stack.setCurrentWidget(self.fa_page))
        button3.clicked.connect(self.close)

        main_layout.addWidget(title)
        main_layout.addWidget(buttons, 1)

        return container

    def _build_fa_page(self) -> QWidget:
        page = QWidget()
        page_layout = QHBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)

        tool_menu = QWidget()
        tool_menu.setFixedWidth(90)
        tool_menu.setStyleSheet("background-color: #f3f4f6;")
        tool_layout = QVBoxLayout(tool_menu)
        tool_layout.setContentsMargins(12, 12, 12, 12)
        tool_layout.setSpacing(12)

        mouse_button = QPushButton()
        mouse_button.setIcon(QIcon(str(ICONS_DIR / "hand.png")))
        mouse_button.setIconSize(QSize(32, 32))
        circle_button = DraggableToolButton("", "circle")
        circle_button.setIcon(QIcon(str(ICONS_DIR / "state.png")))
        circle_button.setIconSize(QSize(32, 32))
        arrow_button = QPushButton()
        arrow_button.setIcon(QIcon(str(ICONS_DIR / "curved-arrow.png")))
        arrow_button.setIconSize(QSize(32, 32))
        delete_button = QPushButton("X")
        back_button = QPushButton("Back")

        mouse_button.clicked.connect(
            lambda: self._set_active_tool_button(mouse_button, [arrow_button, delete_button])
        )
        arrow_button.clicked.connect(
            lambda: self._set_active_tool_button(arrow_button, [mouse_button, delete_button])
        )
        delete_button.clicked.connect(
            lambda: self._set_active_tool_button(delete_button, [mouse_button, arrow_button])
        )

        for tool_button in (mouse_button, circle_button, arrow_button, delete_button):
            tool_button.setMinimumHeight(56)
            tool_button.setStyleSheet(self._tool_button_style)
            tool_layout.addWidget(tool_button)

        self._set_active_tool_button(mouse_button, [arrow_button, delete_button])

        tool_layout.addStretch(1)

        back_button.setMinimumHeight(44)
        back_button.setStyleSheet(
            "font-size: 16px;"
            "font-weight: 600;"
            "background-color: white;"
            "border: 1px solid #d1d5db;"
            "border-radius: 10px;"
        )
        back_button.clicked.connect(lambda: self.stack.setCurrentWidget(self.home_page))
        tool_layout.addWidget(back_button)

        workspace = WorkspaceCanvas()
        mouse_button.clicked.connect(lambda: workspace.set_active_tool("hand"))
        arrow_button.clicked.connect(lambda: workspace.set_active_tool("arrow"))
        delete_button.clicked.connect(lambda: workspace.set_active_tool("delete"))

        page_layout.addWidget(tool_menu)
        page_layout.addWidget(workspace, 1)

        return page

    def _set_active_tool_button(self, active_button: QPushButton, inactive_buttons: list[QPushButton]) -> None:
        active_button.setStyleSheet(self._active_tool_button_style)
        for button in inactive_buttons:
            button.setStyleSheet(self._tool_button_style)
