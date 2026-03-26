from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QLabel, QMenu, QWidget


class MovableCircle(QLabel):
    def __init__(self, text: str, parent: QWidget):
        super().__init__(text, parent)
        self._drag_offset = None
        self._state_name = ""
        self._state_type = "normal"

    def set_state_name(self, state_name: str) -> None:
        self._state_name = state_name
        self.update()

    def set_state_type(self, state_type: str) -> None:
        self._state_type = state_type

    def mousePressEvent(self, event) -> None:
        parent = self.parentWidget()
        if event.button() == Qt.LeftButton and hasattr(parent, "_active_tool") and parent._active_tool == "delete":
            parent.remove_circle(self)
            event.accept()
            return
        if event.button() == Qt.LeftButton and hasattr(parent, "_active_tool") and parent._active_tool == "arrow":
            parent.handle_circle_click(self)
            event.accept()
            return
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        parent = self.parentWidget()
        if hasattr(parent, "_active_tool") and parent._active_tool in ("arrow", "delete"):
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
            if hasattr(parent, "refresh_view"):
                parent.refresh_view()
            else:
                parent.update()
        else:
            self.move(target_pos.x(), target_pos.y())

    def mouseReleaseEvent(self, event) -> None:
        self._drag_offset = None
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event) -> None:
        parent = self.parentWidget()
        if not hasattr(parent, "apply_circle_state_type"):
            return

        options_by_type = {
            "normal": [("Hacer inicial", "initial"), ("Hacer final", "final")],
            "initial": [("Hacer final", "final"), ("Hacer normal", "normal")],
            "final": [("Hacer inicial", "initial"), ("Hacer normal", "normal")],
        }

        options = options_by_type.get(self._state_type, options_by_type["normal"])
        menu = QMenu(self)
        action_map = {}
        for label, target_type in options:
            action = menu.addAction(label)
            action_map[action] = target_type

        selected_action = menu.exec(event.globalPos())
        if selected_action in action_map:
            parent.apply_circle_state_type(self, action_map[selected_action])
            event.accept()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        pixmap = self.pixmap()
        if pixmap is not None and not pixmap.isNull():
            scale_factor = 1.0 if self._state_type == "initial" else 0.76
            target_size = self.size() * scale_factor
            scaled_pixmap = pixmap.scaled(
                target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            x = (self.width() - scaled_pixmap.width()) // 2
            y = (self.height() - scaled_pixmap.height()) // 2
            painter.drawPixmap(x, y, scaled_pixmap)

        if self._state_name:
            font = self.font()
            font.setBold(True)
            font.setPointSize(max(8, int(self.height() * 0.22)))
            painter.setFont(font)
            painter.setPen(QColor("#111827"))
            text_rect = self.rect()
            if self._state_type == "initial":
                text_rect = text_rect.translated(12, 0)
            painter.drawText(text_rect, Qt.AlignCenter, self._state_name)
