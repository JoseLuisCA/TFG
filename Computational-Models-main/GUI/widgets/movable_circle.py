from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QLabel, QWidget


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
