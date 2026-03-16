import math

from PySide6.QtGui import (
    QColor,
    QDrag,
    QFont,
    QIcon,
    QPainter,
    QPainterPath,
    QPalette,
    QPen,
    QPolygonF,
)
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
from PySide6.QtCore import QMimeData, QPointF, QSize, Qt



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
        self.setFocusPolicy(Qt.StrongFocus)
        self._active_tool = "hand"
        self._pending_connection_start = None
        self._connections = []
        self._next_state_index = 0
        self._zoom_factor = 1.0
        self._zoom_step = 1.15
        self._min_zoom = 0.4
        self._max_zoom = 3.0
        self._is_panning = False
        self._pan_last_pos = None
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("#ffffff"))
        self.setPalette(palette)

    def set_active_tool(self, tool_name: str) -> None:
        self._active_tool = tool_name
        if tool_name != "arrow":
            self._pending_connection_start = None
        self.update()

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasText() and event.mimeData().text() == "circle":
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        if event.mimeData().text() != "circle":
            event.ignore()
            return

        self.setFocus()
        drop_pos = event.position().toPoint()
        circle = MovableCircle("", self)
        circle._icon_path = "icons/circlev2.png"
        circle.set_state_name(f"q{self._next_state_index}")
        self._next_state_index += 1
        circle_size = max(8, int(round(48 * self._zoom_factor)))
        circle.setPixmap(QIcon(circle._icon_path).pixmap(circle_size, circle_size))
        circle.setFixedSize(circle_size, circle_size)
        circle.setStyleSheet("background-color: #ffffff; border: none;")
        target_x = drop_pos.x() - circle.width() // 2
        target_y = drop_pos.y() - circle.height() // 2
        bounded_x, bounded_y = self._bounded_position(target_x, target_y, circle.width(), circle.height())
        circle.move(bounded_x, bounded_y)
        circle.show()
        self.update()
        event.acceptProposedAction()

    def mousePressEvent(self, event) -> None:
        self.setFocus()
        if self._active_tool == "arrow":
            self._pending_connection_start = None
            self.update()
        if event.button() == Qt.LeftButton and self.childAt(event.position().toPoint()) is None:
            self._is_panning = True
            self._pan_last_pos = event.position().toPoint()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._is_panning and (event.buttons() & Qt.LeftButton) and self._pan_last_pos is not None:
            current_pos = event.position().toPoint()
            delta = current_pos - self._pan_last_pos
            self._pan_last_pos = current_pos
            self._pan_all_circles(delta.x(), delta.y())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton and self._is_panning:
            self._is_panning = False
            self._pan_last_pos = None
            self.unsetCursor()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event) -> None:
        if event.modifiers() & Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self._apply_zoom(self._zoom_factor * self._zoom_step)
            elif event.angleDelta().y() < 0:
                self._apply_zoom(self._zoom_factor / self._zoom_step)
            event.accept()
            return
        super().wheelEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.modifiers() & Qt.ControlModifier:
            key_text = event.text()
            if key_text == "+" or event.key() in (Qt.Key_Plus, Qt.Key_Equal):
                self._apply_zoom(self._zoom_factor * self._zoom_step)
                event.accept()
                return
            if key_text == "-" or event.key() in (Qt.Key_Minus, Qt.Key_Underscore):
                self._apply_zoom(self._zoom_factor / self._zoom_step)
                event.accept()
                return
        super().keyPressEvent(event)

    def _apply_zoom(self, new_zoom: float) -> None:
        clamped_zoom = max(self._min_zoom, min(new_zoom, self._max_zoom))
        if abs(clamped_zoom - self._zoom_factor) < 1e-9:
            return

        ratio = clamped_zoom / self._zoom_factor
        self._zoom_factor = clamped_zoom

        for circle in self.findChildren(MovableCircle):
            new_x = int(round(circle.x() * ratio))
            new_y = int(round(circle.y() * ratio))
            new_w = max(8, int(round(circle.width() * ratio)))
            new_h = max(8, int(round(circle.height() * ratio)))

            circle.setFixedSize(new_w, new_h)
            icon_path = getattr(circle, "_icon_path", "")
            if icon_path:
                circle.setPixmap(QIcon(icon_path).pixmap(new_w, new_h))

            bounded_x, bounded_y = self._bounded_position(new_x, new_y, new_w, new_h)
            circle.move(bounded_x, bounded_y)

        self.update()

    def _pan_all_circles(self, dx: int, dy: int) -> None:
        if dx == 0 and dy == 0:
            return

        for circle in self.findChildren(MovableCircle):
            new_x = circle.x() + dx
            new_y = circle.y() + dy
            bounded_x, bounded_y = self._bounded_position(new_x, new_y, circle.width(), circle.height())
            circle.move(bounded_x, bounded_y)

        self.update()

    def _bounded_position(self, x: int, y: int, w: int, h: int) -> tuple[int, int]:
        # Mantener siempre los límites equivalentes al zoom mínimo,
        # independientemente del zoom actual.
        extra_x = int(round((self.width() * (1.0 - self._min_zoom)) / 2.0))
        extra_y = int(round((self.height() * (1.0 - self._min_zoom)) / 2.0))

        min_x = -extra_x
        min_y = -extra_y
        max_x = self.width() + extra_x - w
        max_y = self.height() + extra_y - h

        bounded_x = max(min_x, min(x, max_x))
        bounded_y = max(min_y, min(y, max_y))
        return bounded_x, bounded_y

    def handle_circle_click(self, circle: "MovableCircle") -> None:
        if self._active_tool != "arrow":
            return

        if self._pending_connection_start is None:
            self._pending_connection_start = circle
            self.update()
            return

        if self._pending_connection_start is circle:
            self._pending_connection_start = None
            self.update()
            return

        if not self._has_connection(self._pending_connection_start, circle):
            self._connections.append((self._pending_connection_start, circle))
        self._pending_connection_start = None
        self.update()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor("#1f2937"), 2)
        painter.setPen(pen)
        painter.setBrush(QColor("#1f2937"))

        for start_circle, end_circle in self._connections:
            has_reverse = self._has_connection(end_circle, start_circle)
            curve_sign = 1.0 if has_reverse else 0.0
            self._draw_arrow(painter, start_circle, end_circle, curve_sign)

        if self._active_tool == "arrow" and self._pending_connection_start is not None:
            highlight_pen = QPen(QColor("#2563eb"), 2)
            painter.setPen(highlight_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(self._circle_rect(self._pending_connection_start))

    def _draw_arrow(
        self,
        painter: QPainter,
        start_circle: "MovableCircle",
        end_circle: "MovableCircle",
        curve_sign: float,
    ) -> None:
        start_center = self._circle_center(start_circle)
        end_center = self._circle_center(end_circle)

        dx = end_center.x() - start_center.x()
        dy = end_center.y() - start_center.y()
        distance = math.hypot(dx, dy)
        if distance == 0:
            return

        start_radius = min(start_circle.width(), start_circle.height()) / 2.0
        end_radius = min(end_circle.width(), end_circle.height()) / 2.0

        unit_x = dx / distance
        unit_y = dy / distance

        line_start = QPointF(
            start_center.x() + unit_x * start_radius,
            start_center.y() + unit_y * start_radius,
        )
        line_end = QPointF(
            end_center.x() - unit_x * end_radius,
            end_center.y() - unit_y * end_radius,
        )

        perpendicular_x = -unit_y
        perpendicular_y = unit_x

        if curve_sign != 0.0:
            # Separa carriles de ida/vuelta para que no se superpongan.
            lane_offset = 8.0
            line_start = QPointF(
                line_start.x() + perpendicular_x * lane_offset * curve_sign,
                line_start.y() + perpendicular_y * lane_offset * curve_sign,
            )
            line_end = QPointF(
                line_end.x() + perpendicular_x * lane_offset * curve_sign,
                line_end.y() + perpendicular_y * lane_offset * curve_sign,
            )

        painter.setPen(QPen(QColor("#1f2937"), 2))

        control_point = QPointF(
            (line_start.x() + line_end.x()) / 2.0,
            (line_start.y() + line_end.y()) / 2.0,
        )

        painter.setBrush(Qt.NoBrush)
        if curve_sign != 0.0:
            curve_offset = min(48.0, max(22.0, distance * 0.18))
            control_point = QPointF(
                control_point.x() + perpendicular_x * curve_offset * curve_sign,
                control_point.y() + perpendicular_y * curve_offset * curve_sign,
            )
            path = QPainterPath(line_start)
            path.quadTo(control_point, line_end)
            painter.drawPath(path)
            arrow_dx = line_end.x() - control_point.x()
            arrow_dy = line_end.y() - control_point.y()
        else:
            painter.drawLine(line_start, line_end)
            arrow_dx = line_end.x() - line_start.x()
            arrow_dy = line_end.y() - line_start.y()

        arrow_size = 10.0
        angle = math.atan2(arrow_dy, arrow_dx)
        arrow_p1 = QPointF(
            line_end.x() - arrow_size * math.cos(angle - math.pi / 6.0),
            line_end.y() - arrow_size * math.sin(angle - math.pi / 6.0),
        )
        arrow_p2 = QPointF(
            line_end.x() - arrow_size * math.cos(angle + math.pi / 6.0),
            line_end.y() - arrow_size * math.sin(angle + math.pi / 6.0),
        )
        painter.setBrush(QColor("#1f2937"))
        painter.drawPolygon(QPolygonF([line_end, arrow_p1, arrow_p2]))

    def _circle_center(self, circle: "MovableCircle") -> QPointF:
        return QPointF(circle.x() + circle.width() / 2.0, circle.y() + circle.height() / 2.0)

    def _circle_rect(self, circle: "MovableCircle"):
        return circle.geometry()

    def _has_connection(self, start_circle: "MovableCircle", end_circle: "MovableCircle") -> bool:
        for existing_start, existing_end in self._connections:
            if existing_start is start_circle and existing_end is end_circle:
                return True
        return False

#Aquí se define que el círculo que se ha creado en el espacio de trabajo se pueda mover arrastrándolo con el mouse, pero sin salir de los límites del espacio de trabajo.
class MovableCircle(QLabel):
    def __init__(self, text: str, parent: QWidget):
        super().__init__(text, parent)
        self._drag_offset = None
        self._state_name = ""

    def set_state_name(self, state_name: str) -> None:
        self._state_name = state_name
        self.update()

    def mousePressEvent(self, event) -> None:
        parent = self.parentWidget()
        if event.button() == Qt.LeftButton and hasattr(parent, "_active_tool") and parent._active_tool == "arrow":
            parent.handle_circle_click(self)
            event.accept()
            return
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        parent = self.parentWidget()
        if hasattr(parent, "_active_tool") and parent._active_tool == "arrow":
            return
        if not (event.buttons() & Qt.LeftButton):
            return
        if self._drag_offset is None:
            return

        target_pos = self.mapToParent(event.position().toPoint() - self._drag_offset)
        if hasattr(parent, "_bounded_position"):
            bounded_x, bounded_y = parent._bounded_position(
                target_pos.x(), target_pos.y(), self.width(), self.height()
            )
            self.move(bounded_x, bounded_y)
            parent.update()
        else:
            self.move(target_pos.x(), target_pos.y())

    def mouseReleaseEvent(self, event) -> None:
        self._drag_offset = None
        super().mouseReleaseEvent(event)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        pixmap = self.pixmap()
        if pixmap is not None and not pixmap.isNull():
            painter.drawPixmap(self.rect(), pixmap)

        if self._state_name:
            font = self.font()
            font.setBold(True)
            font.setPointSize(max(8, int(self.height() * 0.22)))
            painter.setFont(font)
            painter.setPen(QColor("#111827"))
            painter.drawText(self.rect(), Qt.AlignCenter, self._state_name)

#Aquí definimos la página de la aplicación.
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

        mouse_button = QPushButton()
        mouse_button.setIcon(QIcon("icons/hand.png"))
        mouse_button.setIconSize(QSize(32, 32))
        circle_button = DraggableToolButton("", "circle")
        circle_button.setIcon(QIcon("icons/circlev2.png"))
        circle_button.setIconSize(QSize(32, 32))
        arrow_button = QPushButton()
        arrow_button.setIcon(QIcon("icons/curved-arrow.png"))
        arrow_button.setIconSize(QSize(32, 32))
        back_button = QPushButton("Back")

        mouse_button.clicked.connect(
            lambda: self._set_active_tool_button(mouse_button, arrow_button)
        )
        arrow_button.clicked.connect(
            lambda: self._set_active_tool_button(arrow_button, mouse_button)
        )

        for tool_button in (mouse_button, circle_button, arrow_button):
            tool_button.setMinimumHeight(56)
            tool_button.setStyleSheet(self._tool_button_style)
            tool_layout.addWidget(tool_button)

        self._set_active_tool_button(mouse_button, arrow_button)

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

        page_layout.addWidget(tool_menu)
        page_layout.addWidget(workspace, 1)

        return page

    def _set_active_tool_button(self, active_button: QPushButton, inactive_button: QPushButton) -> None:
        active_button.setStyleSheet(self._active_tool_button_style)
        inactive_button.setStyleSheet(self._tool_button_style)


app = QApplication()
window = MainWindow()
window.show()

app.exec()