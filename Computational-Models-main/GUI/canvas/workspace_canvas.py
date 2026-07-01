import math
import re
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
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QMenu,
    QVBoxLayout,
    QWidget,
)

from widgets.movable_circle import MovableCircle


ICONS_DIR = Path(__file__).resolve().parents[1] / "icons"


class WorkspaceCanvas(QWidget):
    def __init__(self, automaton_kind: str = "finite"):
        super().__init__()
        self.setAcceptDrops(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self._automaton_kind = automaton_kind
        self._initial_stack_symbol = "Z"
        self._active_tool = "hand"
        self._pending_connection_start = None
        self._connections = []
        self._next_state_index = 0
        self._state_icon_paths = {
            "normal": str(ICONS_DIR / "state.png"),
            "initial": str(ICONS_DIR / "initial_state.png"),
            "final": str(ICONS_DIR / "final_state.png"),
            "initial_final": str(ICONS_DIR / "initial_final_state.png"),
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
        if self._automaton_kind == "stack":
            edit_action = menu.addAction("Edit stack transition")
        else:
            edit_action = menu.addAction("Edit transition symbols")
        selected_action = menu.exec(event.globalPos())
        if selected_action is not edit_action:
            return

        current_symbols = self._connections[connection_index].get("symbols", "")
        if self._automaton_kind == "stack":
            symbols = self._prompt_stack_transition_dialog("Edit transition", current_symbols)
            ok = symbols is not None
        else:
            symbols, ok = QInputDialog.getText(
                self,
                "Edit transition",
                "Enter transition symbols separated by commas (a,b,c,d).",
                text=current_symbols,
            )
        if ok:
            normalized = self._normalize_symbols(symbols)
            if self._automaton_kind == "stack" and symbols.strip() and not normalized:
                QMessageBox.warning(self, "Invalid transition", "Use format a;A;B (example: a;Z;AZ).")
                return
            self._connections[connection_index]["symbols"] = normalized
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

        existing_connection = self._get_connection(self._pending_connection_start, circle)

        if self._automaton_kind == "stack":
            symbols = self._prompt_stack_transition_dialog("New transition")
            ok = symbols is not None
        elif existing_connection is None:
            symbols, ok = QInputDialog.getText(
                self,
                "New transition",
                "Enter transition symbols separated by commas (a,b,c,d).",
            )
        else:
            symbols, ok = (None, False)

        if ok:
            normalized_symbols = self._normalize_symbols(symbols)
            if self._automaton_kind == "stack" and symbols.strip() and not normalized_symbols:
                QMessageBox.warning(self, "Invalid transition", "Use format a;A;B (example: a;Z;AZ).")
                self._pending_connection_start = None
                self.refresh_view()
                return

            if existing_connection is None:
                self._connections.append(
                    {
                        "start": self._pending_connection_start,
                        "end": circle,
                        "symbols": normalized_symbols,
                    }
                )
            elif self._automaton_kind == "stack":
                current_symbols = self._normalize_symbols(existing_connection.get("symbols", ""))
                merged_symbols = [item.strip() for item in current_symbols.split(",") if item.strip()]
                if normalized_symbols not in merged_symbols:
                    merged_symbols.append(normalized_symbols)
                existing_connection["symbols"] = ",".join(merged_symbols)
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

        display_symbols = self._format_connection_symbols(symbols)
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
        text_width = metrics.horizontalAdvance(display_symbols)
        text_height = metrics.height()

        painter.setPen(QColor("#111827"))
        painter.drawText(
            QPointF(text_pos.x() - text_width / 2.0, text_pos.y() - text_height / 2.0),
            display_symbols,
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

        display_symbols = self._format_connection_symbols(symbols)
        label_x = center.x() + radius * 1.1
        label_y = center.y() - radius * 2.25

        font = painter.font()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor("#111827"))

        metrics = painter.fontMetrics()
        text_width = metrics.horizontalAdvance(display_symbols)
        text_height = metrics.height()
        painter.drawText(
            QPointF(label_x - text_width / 2.0, label_y - text_height / 2.0),
            display_symbols,
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

    def _get_connection(self, start_circle: "MovableCircle", end_circle: "MovableCircle"):
        for connection in self._connections:
            if connection["start"] is start_circle and connection["end"] is end_circle:
                return connection
        return None

    def _normalize_symbols(self, symbols: str) -> str:
        items = [item.strip() for item in symbols.split(",") if item.strip()]
        if self._automaton_kind != "stack":
            return ",".join(items)

        normalized = []
        for item in items:
            parts = [part.strip() for part in item.split(";")]
            if len(parts) != 3:
                continue
            read_symbol, pop_symbol, push_symbols = parts
            normalized.append(f"{read_symbol};{pop_symbol};{push_symbols}")
        return ",".join(normalized)

    def _format_connection_symbols(self, symbols: str) -> str:
        if self._automaton_kind != "stack":
            return symbols if symbols else "ε"

        items = [item.strip() for item in symbols.split(",") if item.strip()]
        if not items:
            return "λ"

        return " | ".join(self._stack_transition_to_display(item) for item in items)

    def _stack_symbol_to_display(self, symbol: str) -> str:
        symbol = symbol.strip()
        return symbol if symbol else "λ"

    def _stack_symbol_from_display(self, symbol: str) -> str:
        symbol = symbol.strip()
        if symbol.lower() in {"", "lambda", "λ"}:
            return ""
        return symbol

    def _stack_transition_to_display(self, symbol: str) -> str:
        parts = [part.strip() for part in symbol.split(";")]
        if len(parts) != 3:
            return symbol.strip() or "λ"

        read_symbol, pop_symbol, push_symbols = parts
        read_display = read_symbol if read_symbol else "ε"
        return (
            f"{read_display} ; "
            f"{self._stack_symbol_to_display(pop_symbol)} ; "
            f"{self._stack_symbol_to_display(push_symbols)}"
        )

    def _stack_transition_to_internal(self, read_symbol: str, pop_symbol: str, push_symbol: str) -> str:
        return (
            f"{self._stack_symbol_from_display(read_symbol)};"
            f"{self._stack_symbol_from_display(pop_symbol)};"
            f"{self._stack_symbol_from_display(push_symbol)}"
        )

    def _split_stack_transition_symbol(self, symbol: str) -> tuple[str, str, str]:
        first_symbol = symbol.split(",", 1)[0].strip()
        parts = [part.strip() for part in first_symbol.split(";")]
        while len(parts) < 3:
            parts.append("")
        return parts[0], parts[1], parts[2]

    def _prompt_stack_transition_dialog(self, title: str, current_symbols: str = "") -> str | None:
        dialog = QDialog(self)
        dialog.setWindowTitle(title)

        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Enter stack transitions separated by commas using: read;pop;push"))
        layout.addWidget(QLabel("Example: a;B;BB,b;;AB"))

        symbols_edit = QLineEdit()
        symbols_edit.setPlaceholderText("a;B;BB,b;A;AB")
        symbols_edit.setText(current_symbols)
        layout.addWidget(symbols_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.Accepted:
            return None

        return symbols_edit.text().strip()

    def apply_circle_state_type(self, circle: "MovableCircle", state_type: str) -> None:
        icon_path = self._state_icon_paths.get(state_type)
        if not icon_path:
            return

        circle._icon_path = icon_path
        circle.set_state_type(state_type)
        circle.setPixmap(QIcon(icon_path).pixmap(circle.width(), circle.height()))
        circle.update()
        self.refresh_view()

    def _ordered_state_names_for_export(self) -> list[str]:
        circles = [circle for circle in self.findChildren(MovableCircle) if getattr(circle, "_state_name", "")]
        circles.sort(key=lambda circle: circle._state_name)

        initial_circles = [circle for circle in circles if getattr(circle, "_state_type", "normal") in ("initial", "initial_final")]
        if not initial_circles:
            return [circle._state_name for circle in circles]

        initial_circles.sort(key=lambda circle: circle._state_name)
        chosen_initial = initial_circles[0]

        ordered = [chosen_initial._state_name]
        ordered.extend(circle._state_name for circle in circles if circle is not chosen_initial)
        return ordered

    def build_automaton_text(self) -> str:
        if self._automaton_kind == "stack":
            return self._build_stack_automaton_text()

        state_names = self._ordered_state_names_for_export()
        if not state_names:
            return ""

        finals = []
        for circle in self.findChildren(MovableCircle):
            if getattr(circle, "_state_name", "") and getattr(circle, "_state_type", "normal") in ("final", "initial_final"):
                if circle._state_name not in finals:
                    finals.append(circle._state_name)
        finals.sort()

        transition_map = {}
        alphabet = []
        for connection in self._connections:
            start_name = getattr(connection["start"], "_state_name", "")
            end_name = getattr(connection["end"], "_state_name", "")
            if not start_name or not end_name:
                continue

            symbols = self._normalize_symbols(connection.get("symbols", ""))

            if symbols == "":
                # empty string -> epsilon transition; represent with a single empty symbol
                symbol_items = [""]
            else:
                symbol_items = [item.strip() for item in symbols.split(",") if item.strip()]

            for symbol in symbol_items:
                if symbol and symbol not in alphabet:
                    alphabet.append(symbol)
                key = (start_name, symbol)
                if key not in transition_map:
                    transition_map[key] = []
                if end_name not in transition_map[key]:
                    transition_map[key].append(end_name)

        alphabet.sort()

        lines = [
            "Q = {" + ",".join(state_names) + "}",
            "A = {" + ",".join(alphabet) + "}",
            "F = {" + ",".join(finals) + "}",
            "",
        ]

        ordered_transitions = sorted(transition_map.items(), key=lambda item: (item[0][0], item[0][1]))
        for (start_state, symbol), targets in ordered_transitions:
            target_text = ",".join(sorted(targets))
            lines.append(f"({start_state},{symbol}) -> {{{target_text}}}")

        return "\n".join(lines)

    def _build_stack_automaton_text(self) -> str:
        state_names = self._ordered_state_names_for_export()
        if not state_names:
            return ""

        finals = []
        for circle in self.findChildren(MovableCircle):
            if getattr(circle, "_state_name", "") and getattr(circle, "_state_type", "normal") in ("final", "initial_final"):
                if circle._state_name not in finals:
                    finals.append(circle._state_name)
        finals.sort()

        transition_map = {}
        alphabet = []
        stack_symbols = []

        for connection in self._connections:
            start_name = getattr(connection["start"], "_state_name", "")
            end_name = getattr(connection["end"], "_state_name", "")
            if not start_name or not end_name:
                continue

            symbols_text = self._normalize_symbols(connection.get("symbols", ""))
            symbol_items = [item.strip() for item in symbols_text.split(",") if item.strip()]

            for item in symbol_items:
                parts = [part.strip() for part in item.split(";")]
                if len(parts) != 3:
                    continue

                read_symbol, pop_symbol, push_symbols = parts
                if read_symbol and read_symbol not in alphabet:
                    alphabet.append(read_symbol)
                if pop_symbol and pop_symbol not in stack_symbols:
                    stack_symbols.append(pop_symbol)
                for push_symbol in push_symbols:
                    if push_symbol and push_symbol not in stack_symbols:
                        stack_symbols.append(push_symbol)

                key = (start_name, read_symbol, pop_symbol)
                target = (end_name, push_symbols)
                if key not in transition_map:
                    transition_map[key] = []
                if target not in transition_map[key]:
                    transition_map[key].append(target)

        alphabet.sort()
        stack_symbols.sort()

        initial_state = state_names[0]
        initial_stack_symbol = self._initial_stack_symbol
        if not initial_stack_symbol:
            initial_stack_symbol = stack_symbols[0] if stack_symbols else "Z"
        if initial_stack_symbol and initial_stack_symbol not in stack_symbols:
            stack_symbols.insert(0, initial_stack_symbol)

        lines = [
            "Q = {" + ",".join(state_names) + "}",
            "A = {" + ",".join(alphabet) + "}",
            "B = {" + ",".join(stack_symbols) + "}",
            "q0 = {" + initial_state + "}",
            "Z0 = {" + initial_stack_symbol + "}",
            "F = {" + ",".join(finals) + "}",
            "",
        ]

        ordered_transitions = sorted(transition_map.items(), key=lambda item: (item[0][0], item[0][1], item[0][2]))
        for (start_state, read_symbol, pop_symbol), targets in ordered_transitions:
            targets_sorted = sorted(targets, key=lambda value: value[0])
            target_text = ";".join(f"({target_state},{push_symbols})" for target_state, push_symbols in targets_sorted)
            lines.append(f"({start_state},{read_symbol},{pop_symbol}) -> {{{target_text}}}")

        return "\n".join(lines)

    def save_automaton_to_file(self, file_path: str) -> bool:
        automaton_text = self.build_automaton_text()
        if not automaton_text:
            return False

        with open(file_path, "w", encoding="utf-8") as output_file:
            output_file.write(automaton_text)

        return True

    def clear_canvas(self) -> None:
        self._pending_connection_start = None
        self._connections = []
        for circle in self.findChildren(MovableCircle):
            circle.deleteLater()
        self.refresh_view()

    def load_automaton_from_file(self, file_path: str) -> None:
        with open(file_path, "r", encoding="utf-8") as input_file:
            text = input_file.read()
        self.load_automaton_text(text)

    def load_automaton_text(self, text: str) -> None:
        model = self._parse_automaton_text(text)

        states = model["states"]
        finals = set(model["finals"])
        initial_state = states[0]

        self.clear_canvas()

        circles_by_name = {}
        canvas_width = max(self.width(), 700)
        canvas_height = max(self.height(), 500)
        circle_size = max(8, int(round(90 * self._zoom_factor)))

        if len(states) == 1:
            positions = [(canvas_width // 2 - circle_size // 2, canvas_height // 2 - circle_size // 2)]
        else:
            radius = max(140.0, min(canvas_width, canvas_height) * 0.33)
            center_x = canvas_width / 2.0
            center_y = canvas_height / 2.0
            positions = []
            for index in range(len(states)):
                angle = -math.pi / 2.0 + (2.0 * math.pi * index / len(states))
                x = int(round(center_x + radius * math.cos(angle) - circle_size / 2.0))
                y = int(round(center_y + radius * math.sin(angle) - circle_size / 2.0))
                positions.append((x, y))

        for index, state_name in enumerate(states):
            if state_name == initial_state and state_name in finals:
                state_type = "initial_final"
            elif state_name == initial_state:
                state_type = "initial"
            elif state_name in finals:
                state_type = "final"
            else:
                state_type = "normal"

            circle = MovableCircle("", self)
            circle._icon_path = self._state_icon_paths[state_type]
            circle.set_state_type(state_type)
            circle.set_state_name(state_name)
            circle.setPixmap(QIcon(circle._icon_path).pixmap(circle_size, circle_size))
            circle.setFixedSize(circle_size, circle_size)
            circle.setStyleSheet("background-color: #ffffff; border: none;")

            pos_x, pos_y = positions[index]
            bounded_x, bounded_y = self._bounded_position(pos_x, pos_y, circle.width(), circle.height())
            circle.move(bounded_x, bounded_y)
            circle.show()
            circles_by_name[state_name] = circle

        for transition in model["transitions"]:
            start_circle = circles_by_name.get(transition["from"])
            end_circle = circles_by_name.get(transition["to"])
            if start_circle is None or end_circle is None:
                continue
            self._connections.append(
                {
                    "start": start_circle,
                    "end": end_circle,
                    "symbols": self._normalize_symbols(",".join(transition["symbols"])),
                }
            )

        max_state_index = -1
        for state_name in states:
            match = re.fullmatch(r"q(\d+)", state_name)
            if match is not None:
                max_state_index = max(max_state_index, int(match.group(1)))
        self._next_state_index = max_state_index + 1 if max_state_index >= 0 else len(states)
        if self._automaton_kind == "stack":
            self._initial_stack_symbol = model.get("initial_stack_symbol", self._initial_stack_symbol)

        self.refresh_view()

    def _parse_automaton_text(self, text: str) -> dict:
        if self._automaton_kind == "stack":
            return self._parse_stack_automaton_text(text)

        lines = [line.strip() for line in text.splitlines() if line.strip()]

        q_line = next((line for line in lines if line.startswith("Q")), None)
        f_line = next((line for line in lines if line.startswith("F")), None)
        if q_line is None:
            raise ValueError("States line not found: Q = {...}")
        if f_line is None:
            raise ValueError("Final states line not found: F = {...}")

        states = self._parse_braced_values(q_line)
        finals = self._parse_braced_values(f_line)
        if not states:
            raise ValueError("The automaton has no states in line Q")

        transition_map = {}
        transition_lines = [line for line in lines if line.startswith("(") and "->" in line]

        for transition_line in transition_lines:
            left_text, right_text = transition_line.split("->", 1)
            left_text = left_text.strip()
            right_text = right_text.strip()

            if not (left_text.startswith("(") and left_text.endswith(")")):
                raise ValueError(f"Invalid transition: {transition_line}")

            left_content = left_text[1:-1]
            left_parts = [item.strip() for item in left_content.split(",")]
            if len(left_parts) != 2:
                raise ValueError(f"Invalid transition: {transition_line}")

            start_state, symbol = left_parts
            target_states = self._parse_braced_values(right_text)

            for end_state in target_states:
                key = (start_state, end_state)
                if key not in transition_map:
                    transition_map[key] = []
                if symbol not in transition_map[key]:
                    transition_map[key].append(symbol)

                if start_state not in states:
                    states.append(start_state)
                if end_state not in states:
                    states.append(end_state)

        transitions = []
        for (start_state, end_state), symbols in sorted(transition_map.items(), key=lambda item: (item[0][0], item[0][1])):
            transitions.append(
                {
                    "from": start_state,
                    "to": end_state,
                    "symbols": sorted(symbols),
                }
            )

        return {"states": states, "finals": finals, "transitions": transitions}

    def _parse_stack_automaton_text(self, text: str) -> dict:
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        q_line = next((line for line in lines if line.startswith("Q")), None)
        f_line = next((line for line in lines if line.startswith("F")), None)
        z0_line = next((line for line in lines if line.startswith("Z0")), None)
        if q_line is None:
            raise ValueError("States line not found: Q = {...}")
        if f_line is None:
            raise ValueError("Final states line not found: F = {...}")

        states = self._parse_braced_values(q_line)
        finals = self._parse_braced_values(f_line)
        if not states:
            raise ValueError("The automaton has no states in line Q")

        initial_stack_symbol = "Z"
        if z0_line is not None:
            z0_values = self._parse_braced_values(z0_line)
            if z0_values:
                initial_stack_symbol = z0_values[0]

        transition_map = {}
        transition_lines = [line for line in lines if line.startswith("(") and "->" in line]

        for transition_line in transition_lines:
            left_text, right_text = transition_line.split("->", 1)
            left_text = left_text.strip()
            right_text = right_text.strip()

            if not (left_text.startswith("(") and left_text.endswith(")")):
                raise ValueError(f"Invalid transition: {transition_line}")

            left_content = left_text[1:-1]
            left_parts = self._split_stack_transition_left(left_content)
            if len(left_parts) != 3:
                raise ValueError(f"Invalid transition: {transition_line}")

            start_state, read_symbol, pop_symbol = left_parts
            target_tuples = self._parse_stack_target_tuples(right_text)

            for end_state, push_symbols in target_tuples:
                key = (start_state, end_state)
                stack_label = f"{read_symbol};{pop_symbol};{push_symbols}"
                if key not in transition_map:
                    transition_map[key] = []
                if stack_label not in transition_map[key]:
                    transition_map[key].append(stack_label)

                if start_state not in states:
                    states.append(start_state)
                if end_state not in states:
                    states.append(end_state)

        transitions = []
        for (start_state, end_state), symbols in sorted(transition_map.items(), key=lambda item: (item[0][0], item[0][1])):
            transitions.append(
                {
                    "from": start_state,
                    "to": end_state,
                    "symbols": sorted(symbols),
                }
            )

        return {
            "states": states,
            "finals": finals,
            "transitions": transitions,
            "initial_stack_symbol": initial_stack_symbol,
        }

    def _split_stack_transition_left(self, text: str) -> list[str]:
        parts = []
        current = []
        depth = 0
        for ch in text:
            if ch == "(":
                depth += 1
                current.append(ch)
            elif ch == ")":
                depth -= 1
                current.append(ch)
            elif ch == "," and depth == 0:
                parts.append("".join(current).strip())
                current = []
            else:
                current.append(ch)
        if current:
            parts.append("".join(current).strip())
        return parts

    def _parse_stack_target_tuples(self, text: str) -> list[tuple[str, str]]:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end < start:
            raise ValueError(f"Invalid stack transition format: {text}")

        content = text[start + 1 : end].strip()
        if not content:
            return []

        tuples = []
        for pair in content.split(";"):
            pair = pair.strip()
            if not pair:
                continue
            if not (pair.startswith("(") and pair.endswith(")")):
                raise ValueError(f"Invalid stack transition format: {text}")
            inner = pair[1:-1]
            parts = self._split_stack_transition_left(inner)
            if len(parts) < 1:
                continue
            state_name = parts[0].strip()
            push_symbols = parts[1].strip() if len(parts) > 1 else ""
            tuples.append((state_name, push_symbols))

        if not tuples:
            raise ValueError(f"Invalid stack transition format: {text}")

        return tuples

    def _parse_braced_values(self, text: str) -> list[str]:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end < start:
            raise ValueError(f"Invalid line format: {text}")

        content = text[start + 1 : end].strip()
        if not content:
            return []

        return [item.strip() for item in content.split(",") if item.strip()]


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
