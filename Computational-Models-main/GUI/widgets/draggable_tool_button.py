from PySide6.QtCore import QMimeData, Qt
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import QPushButton


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
