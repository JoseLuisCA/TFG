import math
from pathlib import Path

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import (
    QColor,
    QIcon,
    QPainter,
    QPainterPath,
    QPainterPathStroker,
    QPalette,
    QPen,
    QPolygonF,
)
from PySide6.QtWidgets import QInputDialog, QMenu, QWidget

from widgets.movable_circle import MovableCircle


ICONS_DIR = Path(__file__).resolve().parents[1] / "icons"


class WorkspaceCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self._active_tool = "hand"
        self._pending_connection_start = None
        self._connections = []
        self._next_state_index = 0
        self._state_icon_paths = {
            "normal": str(ICONS_DIR / "state.png"),
            "initial": str(ICONS_DIR / "initial_state.png"),
            "final": str(ICONS_DIR / "final_state.png"),
        }
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

        self._overlay = _ConnectionsOverlay(self)
        self._overlay.setGeometry(self.rect())
        self._overlay.raise_()

    def refresh_view(self) -> None:
        self.update()
        if hasattr(self, "_overlay"):
            self._overlay.raise_()
            self._overlay.update()

    def set_active_tool(self, tool_name: str) -> None:
        self._active_tool = tool_name
        if tool_name != "arrow":
            self._pending_connection_start = None
        self.refresh_view()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "_overlay"):
            self._overlay.setGeometry(self.rect())
            self._overlay.raise_()

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
        circle._icon_path = self._state_icon_paths["normal"]
        circle.set_state_type("normal")
        circle.set_state_name(f"q{self._next_state_index}")
        self._next_state_index += 1
        circle_size = max(8, int(round(90 * self._zoom_factor)))
        circle.setPixmap(QIcon(circle._icon_path).pixmap(circle_size, circle_size))
        circle.setFixedSize(circle_size, circle_size)
        circle.setStyleSheet("background-color: #ffffff; border: none;")
        target_x = drop_pos.x() - circle.width() // 2
        target_y = drop_pos.y() - circle.height() // 2
        bounded_x, bounded_y = self._bounded_position(target_x, target_y, circle.width(), circle.height())
        circle.move(bounded_x, bounded_y)
        circle.show()
        self.refresh_view()
        event.acceptProposedAction()

    def mousePressEvent(self, event) -> None:
        self.setFocus()
        if self._active_tool == "arrow":
            self._pending_connection_start = None
            self.refresh_view()
        if self._active_tool == "delete" and event.button() == Qt.LeftButton:
            if self._delete_connection_at(event.position().toPoint()):
                event.accept()
                return
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

    def contextMenuEvent(self, event) -> None:
        connection_index = self._find_connection_index_at(event.pos())
        if connection_index is None:
            super().contextMenuEvent(event)
            return

        menu = QMenu(self)
        edit_action = menu.addAction("Modificar simbolos de transicion")
        selected_action = menu.exec(event.globalPos())
        if selected_action is not edit_action:
            return

        current_symbols = self._connections[connection_index].get("symbols", "")
        symbols, ok = QInputDialog.getText(
            self,
            "Modificar transicion",
            "Introduce los simbolos de la transicion separados por una coma. (a,b,c,d)",
            text=current_symbols,
        )
        if ok:
            self._connections[connection_index]["symbols"] = self._normalize_symbols(symbols)
            self.refresh_view()

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

        self.refresh_view()

    def _pan_all_circles(self, dx: int, dy: int) -> None:
        if dx == 0 and dy == 0:
            return

        for circle in self.findChildren(MovableCircle):
            new_x = circle.x() + dx
            new_y = circle.y() + dy
            bounded_x, bounded_y = self._bounded_position(new_x, new_y, circle.width(), circle.height())
            circle.move(bounded_x, bounded_y)

        self.refresh_view()

    def _bounded_position(self, x: int, y: int, w: int, h: int) -> tuple[int, int]:
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
            self.refresh_view()
            return

        if not self._has_connection(self._pending_connection_start, circle):
            symbols, ok = QInputDialog.getText(
                self,
                "Nueva transicion",
                "Introduce los simbolos de la transicion separados por una coma. (a,b,c,d)",
            )
            if ok:
                normalized_symbols = self._normalize_symbols(symbols)
                self._connections.append(
                    {
                        "start": self._pending_connection_start,
                        "end": circle,
                        "symbols": normalized_symbols,
                    }
                )
        self._pending_connection_start = None
        self.refresh_view()

    def _paint_connections(self, painter: QPainter) -> None:
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor("#1f2937"), 2)
        painter.setPen(pen)
        painter.setBrush(QColor("#1f2937"))

        for connection in self._connections:
            start_circle = connection["start"]
            end_circle = connection["end"]
            symbols = connection["symbols"]
            has_reverse = self._has_connection(end_circle, start_circle)
            curve_sign = 1.0 if has_reverse else 0.0
            self._draw_arrow(painter, start_circle, end_circle, curve_sign, symbols)

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
        symbols: str,
    ) -> None:
        if start_circle is end_circle:
            self._draw_self_loop(painter, start_circle, symbols)
            return

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

        if symbols:
            text_anchor = control_point if curve_sign != 0.0 else QPointF(
                (line_start.x() + line_end.x()) / 2.0,
                (line_start.y() + line_end.y()) / 2.0,
            )
            text_offset = 18.0 if curve_sign == 0.0 else 14.0
            text_pos = QPointF(
                text_anchor.x() + perpendicular_x * text_offset,
                text_anchor.y() + perpendicular_y * text_offset,
            )

            if curve_sign == 0.0:
                if text_pos.y() >= text_anchor.y():
                    text_pos = QPointF(
                        text_anchor.x() - perpendicular_x * text_offset,
                        text_anchor.y() - perpendicular_y * text_offset,
                    )

                if abs(perpendicular_y) < 0.2:
                    text_pos = QPointF(text_pos.x(), text_pos.y() - 10.0)

            font = painter.font()
            font.setPointSize(10)
            font.setBold(True)
            painter.setFont(font)

            metrics = painter.fontMetrics()
            text_width = metrics.horizontalAdvance(symbols)
            text_height = metrics.height()

            painter.setPen(QColor("#111827"))
            painter.drawText(
                QPointF(text_pos.x() - text_width / 2.0, text_pos.y() - text_height / 2.0),
                symbols,
            )

    def _draw_self_loop(self, painter: QPainter, circle: "MovableCircle", symbols: str) -> None:
        center = self._circle_center(circle)
        radius = min(circle.width(), circle.height()) / 2.0

        start = QPointF(center.x() + radius * 0.05, center.y() - radius * 0.95)
        end = QPointF(center.x() + radius * 1.0, center.y() - radius * 0.55)
        ctrl1 = QPointF(center.x() + radius * 0.15, center.y() - radius * 2.9)
        ctrl2 = QPointF(center.x() + radius * 2.25, center.y() - radius * 2.35)

        path = QPainterPath(start)
        path.cubicTo(ctrl1, ctrl2, end)

        painter.setPen(QPen(QColor("#1f2937"), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

        tangent_x = end.x() - ctrl2.x()
        tangent_y = end.y() - ctrl2.y()
        angle = math.atan2(tangent_y, tangent_x)
        arrow_size = 10.0
        arrow_p1 = QPointF(
            end.x() - arrow_size * math.cos(angle - math.pi / 6.0),
            end.y() - arrow_size * math.sin(angle - math.pi / 6.0),
        )
        arrow_p2 = QPointF(
            end.x() - arrow_size * math.cos(angle + math.pi / 6.0),
            end.y() - arrow_size * math.sin(angle + math.pi / 6.0),
        )
        painter.setBrush(QColor("#1f2937"))
        painter.drawPolygon(QPolygonF([end, arrow_p1, arrow_p2]))

        if symbols:
            label_x = center.x() + radius * 1.1
            label_y = center.y() - radius * 2.25

            font = painter.font()
            font.setPointSize(10)
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QColor("#111827"))

            metrics = painter.fontMetrics()
            text_width = metrics.horizontalAdvance(symbols)
            text_height = metrics.height()
            painter.drawText(
                QPointF(label_x - text_width / 2.0, label_y - text_height / 2.0),
                symbols,
            )

    def remove_circle(self, circle: "MovableCircle") -> None:
        if self._pending_connection_start is circle:
            self._pending_connection_start = None

        self._connections = [
            connection
            for connection in self._connections
            if connection["start"] is not circle and connection["end"] is not circle
        ]
        circle.deleteLater()
        self.refresh_view()

    def _delete_connection_at(self, point) -> bool:
        index = self._find_connection_index_at(point)
        if index is not None:
            self._connections.pop(index)
            self.refresh_view()
            return True

        return False

    def _find_connection_index_at(self, point):
        point_f = QPointF(point)
        for index in range(len(self._connections) - 1, -1, -1):
            connection = self._connections[index]
            path = self._connection_path(connection)
            if path is None:
                continue

            stroker = QPainterPathStroker()
            stroker.setWidth(14.0)
            hit_path = stroker.createStroke(path)
            if hit_path.contains(point_f):
                return index

        return None

    def _connection_path(self, connection):
        start_circle = connection["start"]
        end_circle = connection["end"]
        has_reverse = self._has_connection(end_circle, start_circle)
        curve_sign = 1.0 if has_reverse else 0.0

        if start_circle is end_circle:
            return self._self_loop_path(start_circle)

        start_center = self._circle_center(start_circle)
        end_center = self._circle_center(end_circle)
        dx = end_center.x() - start_center.x()
        dy = end_center.y() - start_center.y()
        distance = math.hypot(dx, dy)
        if distance == 0:
            return None

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
            lane_offset = 8.0
            line_start = QPointF(
                line_start.x() + perpendicular_x * lane_offset * curve_sign,
                line_start.y() + perpendicular_y * lane_offset * curve_sign,
            )
            line_end = QPointF(
                line_end.x() + perpendicular_x * lane_offset * curve_sign,
                line_end.y() + perpendicular_y * lane_offset * curve_sign,
            )

        path = QPainterPath(line_start)
        if curve_sign != 0.0:
            control_point = QPointF(
                (line_start.x() + line_end.x()) / 2.0,
                (line_start.y() + line_end.y()) / 2.0,
            )
            curve_offset = min(48.0, max(22.0, distance * 0.18))
            control_point = QPointF(
                control_point.x() + perpendicular_x * curve_offset * curve_sign,
                control_point.y() + perpendicular_y * curve_offset * curve_sign,
            )
            path.quadTo(control_point, line_end)
        else:
            path.lineTo(line_end)

        return path

    def _self_loop_path(self, circle: "MovableCircle"):
        center = self._circle_center(circle)
        radius = min(circle.width(), circle.height()) / 2.0

        start = QPointF(center.x() + radius * 0.05, center.y() - radius * 0.95)
        end = QPointF(center.x() + radius * 1.0, center.y() - radius * 0.55)
        ctrl1 = QPointF(center.x() + radius * 0.15, center.y() - radius * 2.9)
        ctrl2 = QPointF(center.x() + radius * 2.25, center.y() - radius * 2.35)

        path = QPainterPath(start)
        path.cubicTo(ctrl1, ctrl2, end)
        return path

    def _circle_center(self, circle: "MovableCircle") -> QPointF:
        return QPointF(circle.x() + circle.width() / 2.0, circle.y() + circle.height() / 2.0)

    def _circle_rect(self, circle: "MovableCircle"):
        return circle.geometry()

    def _has_connection(self, start_circle: "MovableCircle", end_circle: "MovableCircle") -> bool:
        for connection in self._connections:
            if connection["start"] is start_circle and connection["end"] is end_circle:
                return True
        return False

    def _normalize_symbols(self, symbols: str) -> str:
        items = [item.strip() for item in symbols.split(",") if item.strip()]
        return ",".join(items)

    def apply_circle_state_type(self, circle: "MovableCircle", state_type: str) -> None:
        icon_path = self._state_icon_paths.get(state_type)
        if not icon_path:
            return

        circle._icon_path = icon_path
        circle.set_state_type(state_type)
        circle.setPixmap(QIcon(icon_path).pixmap(circle.width(), circle.height()))
        circle.update()
        self.refresh_view()


class _ConnectionsOverlay(QWidget):
    def __init__(self, parent: WorkspaceCanvas):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

    def paintEvent(self, event) -> None:
        parent = self.parentWidget()
        if isinstance(parent, WorkspaceCanvas):
            painter = QPainter(self)
            parent._paint_connections(painter)
