from PySide6.QtGui import QDrag, QFont
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import QMimeData, Qt



#Aquí se define el botón que se puede arrastrar desde el menú de herramientas y soltarlo en el espacio de trabajo para crear un nuevo círculo.
class DraggableToolButton(QPushButton):
    def __init__(self, text: str, tool_type: str):
        super().__init__(text)
        self.tool_type = tool_type
        self._drag_start = None

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_start = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if not (event.buttons() & Qt.LeftButton):
            return
        if self._drag_start is None:
            return

        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(self.tool_type)
        drag.setMimeData(mime_data)
        drag.exec(Qt.CopyAction)

#Aqui se define el lienzo donde se puede trabajar con los autómatas.
class WorkspaceCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setStyleSheet("background-color: white;")

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasText() and event.mimeData().text() == "circle":
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        if event.mimeData().text() != "circle":
            event.ignore()
            return

        drop_pos = event.position().toPoint()
        circle = MovableCircle("○", self)
        circle.setStyleSheet("font-size: 48px; color: #111827;")
        circle.adjustSize()
        circle.move(drop_pos.x() - circle.width() // 2, drop_pos.y() - circle.height() // 2)
        circle.show()
        event.acceptProposedAction()

#Aquí se define que el círculo que se ha creado en el espacio de trabajo se pueda mover arrastrándolo con el mouse, pero sin salir de los límites del espacio de trabajo.
class MovableCircle(QLabel):
    def __init__(self, text: str, parent: QWidget):
        super().__init__(text, parent)
        self._drag_offset = None

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if not (event.buttons() & Qt.LeftButton):
            return
        if self._drag_offset is None:
            return

        parent = self.parentWidget()
        target_pos = self.mapToParent(event.position().toPoint() - self._drag_offset)

        max_x = max(0, parent.width() - self.width())
        max_y = max(0, parent.height() - self.height())
        bounded_x = max(0, min(target_pos.x(), max_x))
        bounded_y = max(0, min(target_pos.y(), max_y))
        self.move(bounded_x, bounded_y)

    def mouseReleaseEvent(self, event) -> None:
        self._drag_offset = None
        super().mouseReleaseEvent(event)

#Aquí definimos la página de la aplicación.
class MainWindow(QMainWindow):

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

    #Página principal
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

        button1 = QPushButton('Finite Automaton')
        button2 = QPushButton('Stack Automaton')
        button3 = QPushButton('Exit')

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

    #Página de autómatas finitos
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

        mouse_button = QPushButton("🖱")
        circle_button = DraggableToolButton("○", "circle")
        arrow_button = QPushButton("➜")
        back_button = QPushButton("Back")

        for tool_button in (mouse_button, circle_button, arrow_button):
            tool_button.setMinimumHeight(56)
            tool_button.setStyleSheet(
                "font-size: 24px;"
                "background-color: white;"
                "border: 1px solid #d1d5db;"
                "border-radius: 10px;"
            )
            tool_layout.addWidget(tool_button)

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

        page_layout.addWidget(tool_menu)
        page_layout.addWidget(workspace, 1)

        return page


app = QApplication()
window = MainWindow()
window.show()

app.exec()