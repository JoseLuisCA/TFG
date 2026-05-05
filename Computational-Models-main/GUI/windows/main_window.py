from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLineEdit,
    QCheckBox,
    QDialogButtonBox,
    QLabel,
    QMessageBox,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from canvas.workspace_canvas import WorkspaceCanvas
from widgets.draggable_tool_button import DraggableToolButton
from tempfile import NamedTemporaryFile
import os

from library.AFND import FiniteAutomaton
from library.AFD_to_reg import dfaToRegex
from library.reg_to_AFND import regexToAutomaton
from PySide6.QtWidgets import QDialog, QGridLayout


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
        page_vlayout = QVBoxLayout(page)
        page_vlayout.setContentsMargins(0, 0, 0, 0)
        page_vlayout.setSpacing(0)

        # Top operations bar
        top_menu = QWidget()
        top_layout = QHBoxLayout(top_menu)
        top_layout.setContentsMargins(12, 8, 12, 8)
        top_layout.setSpacing(8)

        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)

        clean_btn = QPushButton("Clean")
        minimize_btn = QPushButton("Minimize")
        regex_btn = QPushButton("Regular Expression")
        regex_to_fda_btn = QPushButton("Regex to FDA")
        check_word_btn = QPushButton("Check Word")
        analyze_btn = QPushButton("Analyze")

        for b in (clean_btn, minimize_btn, regex_btn, regex_to_fda_btn, check_word_btn, analyze_btn):
            b.setMinimumHeight(36)
            b.setStyleSheet(
                "font-size:14px; font-weight:600; background-color:white; border:1px solid #d1d5db; border-radius:8px; padding:6px;"
            )

        content_layout.addWidget(clean_btn)
        content_layout.addWidget(minimize_btn)
        content_layout.addWidget(regex_btn)
        content_layout.addWidget(regex_to_fda_btn)
        content_layout.addWidget(check_word_btn)
        content_layout.addWidget(analyze_btn)

        top_layout.addWidget(content_widget, 1)

        # Left vertical tool menu
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
        open_button = QPushButton("Open")
        save_button = QPushButton("Save")
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

        open_button.setMinimumHeight(44)
        open_button.setStyleSheet(
            "font-size: 16px;"
            "font-weight: 600;"
            "background-color: white;"
            "border: 1px solid #d1d5db;"
            "border-radius: 10px;"
        )
        tool_layout.addWidget(open_button)

        save_button.setMinimumHeight(44)
        save_button.setStyleSheet(
            "font-size: 16px;"
            "font-weight: 600;"
            "background-color: white;"
            "border: 1px solid #d1d5db;"
            "border-radius: 10px;"
        )
        tool_layout.addWidget(save_button)

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
        open_button.clicked.connect(lambda: self._open_finite_automaton(workspace))
        save_button.clicked.connect(lambda: self._save_finite_automaton(workspace))

        # connect top actions to handlers
        clean_btn.clicked.connect(lambda: self._clean_automaton(workspace))
        minimize_btn.clicked.connect(lambda: self._minimize_automaton(workspace))
        regex_btn.clicked.connect(lambda: self._regular_expression_automaton(workspace))
        regex_to_fda_btn.clicked.connect(lambda: self._regex_to_fda_automaton(workspace))
        check_word_btn.clicked.connect(lambda: self._check_word_automaton(workspace))
        analyze_btn.clicked.connect(lambda: self._analyze_automaton(workspace))

        main_row = QWidget()
        main_row_layout = QHBoxLayout(main_row)
        main_row_layout.setContentsMargins(0, 0, 0, 0)
        main_row_layout.setSpacing(0)
        main_row_layout.addWidget(tool_menu)
        main_row_layout.addWidget(workspace, 1)

        page_vlayout.addWidget(top_menu)
        page_vlayout.addWidget(main_row, 1)

        page_layout = page_vlayout

        return page

    def _set_active_tool_button(self, active_button: QPushButton, inactive_buttons: list[QPushButton]) -> None:
        active_button.setStyleSheet(self._active_tool_button_style)
        for button in inactive_buttons:
            button.setStyleSheet(self._tool_button_style)

    def _save_finite_automaton(self, workspace: WorkspaceCanvas) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar automata",
            "automaton.txt",
            "Text files (*.txt);;All files (*)",
        )
        if not file_path:
            return

        saved = workspace.save_automaton_to_file(file_path)
        if not saved:
            QMessageBox.warning(
                self,
                "Guardar automata",
                "No hay estados para guardar. Crea al menos un estado antes de guardar.",
            )
            return

        QMessageBox.information(
            self,
            "Guardar automata",
            "Automata guardado correctamente.",
        )

    def _open_finite_automaton(self, workspace: WorkspaceCanvas) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Abrir automata",
            "",
            "Text files (*.txt);;All files (*)",
        )
        if not file_path:
            return

        try:
            workspace.load_automaton_from_file(file_path)
        except Exception as error:
            QMessageBox.critical(
                self,
                "Abrir automata",
                f"No se pudo abrir el automata.\n\nDetalle: {error}",
            )
            return

        QMessageBox.information(
            self,
            "Abrir automata",
            "Automata cargado correctamente.",
        )

    # --- Tool action handlers ---
    def _write_tmp_and_load(self, workspace: WorkspaceCanvas, automaton_obj) -> None:
        """Helper: convert FiniteAutomaton (object) to text and load into workspace"""
        model = automaton_obj.to_dict()
        states = model.get("states", [])
        alphabet = model.get("alphabet", [])
        finals = model.get("final", [])
        transitions = model.get("transitions", [])

        # Map original state names to compact sequential names q_0, q_1, ...
        state_map = {}
        for idx, s in enumerate(states):
            new_name = f"q_{idx}"
            # ensure uniqueness just in case
            i = 1
            candidate = new_name
            while candidate in state_map.values():
                candidate = f"{new_name}_{i}"
                i += 1
            state_map[s] = candidate

        # Ensure the initial state is first (workspace expects first state as initial)
        initial_state_orig = model.get("initial")
        sanitized_states = []
        if initial_state_orig in state_map:
            sanitized_states.append(state_map[initial_state_orig])

        for s in states:
            if s == initial_state_orig:
                continue
            sanitized_states.append(state_map[s])

        sanitized_finals = [state_map.get(f, f) for f in finals]

        lines = [
            "Q = {" + ",".join(sanitized_states) + "}",
            "A = {" + ",".join(alphabet) + "}",
            "F = {" + ",".join(sanitized_finals) + "}",
            "",
        ]

        for t in transitions:
            frm = t.get("from")
            sym = t.get("symbol")
            tos = t.get("to", [])

            frm_s = state_map.get(frm, frm)
            tos_s = [state_map.get(to, to) for to in tos]

            lines.append(f"({frm_s},{sym}) -> {{{','.join(tos_s)}}}")

        text = "\n".join(lines)
        # load into canvas
        workspace.load_automaton_text(text)

    def _clean_automaton(self, workspace: WorkspaceCanvas) -> None:
        text = workspace.build_automaton_text()
        if not text:
            QMessageBox.warning(self, "Clean", "No automaton to clean.")
            return

        with NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as tmp:
            tmp.write(text)
            tmp_path = tmp.name

        try:
            fa = FiniteAutomaton.readAutomaton(tmp_path)
            fa.deleteInaccessibleStates()
            fa.deleteErrorStates()
            self._write_tmp_and_load(workspace, fa)
            QMessageBox.information(self, "Clean", "Removed unreachable and error states.")
        except Exception as e:
            QMessageBox.critical(self, "Clean", f"Operation failed: {e}")
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    def _minimize_automaton(self, workspace: WorkspaceCanvas) -> None:
        text = workspace.build_automaton_text()
        if not text:
            QMessageBox.warning(self, "Minimize", "No automaton to minimize.")
            return

        with NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as tmp:
            tmp.write(text)
            tmp_path = tmp.name

        try:
            fa = FiniteAutomaton.readAutomaton(tmp_path)
            minimal = fa.minimalAutomaton()
            self._write_tmp_and_load(workspace, minimal)
            QMessageBox.information(self, "Minimize", "Automaton minimized.")
        except Exception as e:
            QMessageBox.critical(self, "Minimize", f"Operation failed: {e}")
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    def _determinize_automaton(self, workspace: WorkspaceCanvas) -> None:
        # determinize action removed from UI; keep method placeholder in case needed later
        QMessageBox.information(self, "Determinize", "This action has been removed from the UI.")

    def _regular_expression_automaton(self, workspace: WorkspaceCanvas) -> None:
        text = workspace.build_automaton_text()
        if not text:
            QMessageBox.warning(self, "Regular Expression", "No automaton to convert.")
            return

        with NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as tmp:
            tmp.write(text)
            tmp_path = tmp.name

        try:
            fa = FiniteAutomaton.readAutomaton(tmp_path)
            regex_source = fa.transformDeterministic()
            regular_expression = dfaToRegex(regex_source)

            dlg = QDialog(self)
            dlg.setWindowTitle("Regular Expression")
            layout = QVBoxLayout(dlg)
            label = QLabel(regular_expression)
            label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            label.setWordWrap(True)
            layout.addWidget(label)
            dlg.setLayout(layout)
            dlg.setModal(False)
            dlg.show()

        except Exception as e:
            QMessageBox.critical(self, "Regular Expression", f"Operation failed: {e}")
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    def _regex_to_fda_automaton(self, workspace: WorkspaceCanvas) -> None:
        # Ensure the canvas is cleared so the conversion is independent
        workspace.clear_canvas()

        # Custom dialog with checkbox to optionally determinize & minimize
        dlg = QDialog(self)
        dlg.setWindowTitle("Regex to FDA")
        vlayout = QVBoxLayout(dlg)
        vlayout.setContentsMargins(12, 12, 12, 12)

        label = QLabel("Enter a regular expression:")
        edit = QLineEdit()
        checkbox = QCheckBox("Determinize and minimize (may be slow for large regexes)")
        checkbox.setChecked(False)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)

        vlayout.addWidget(label)
        vlayout.addWidget(edit)
        vlayout.addWidget(checkbox)
        vlayout.addWidget(buttons)

        if dlg.exec() != QDialog.Accepted:
            return

        regex_input = edit.text().strip()
        if not regex_input:
            return

        try:
            fa = regexToAutomaton(regex_input)
            if checkbox.isChecked():
                # Determinize and minimize only if user asked for it
                fa = fa.transformDeterministic()
                fa = fa.minimalAutomaton()

            self._write_tmp_and_load(workspace, fa)
            QMessageBox.information(self, "Regex to FDA", "Automaton created from regex.")
        except Exception as e:
            QMessageBox.critical(self, "Regex to FDA", f"Operation failed: {e}")

    def _check_word_automaton(self, workspace: WorkspaceCanvas) -> None:
        text = workspace.build_automaton_text()
        if not text:
            QMessageBox.warning(self, "Check Word", "No automaton to check.")
            return

        word, ok = QInputDialog.getText(
            self,
            "Check Word",
            "Enter the string to test:",
            text="",
        )
        if not ok:
            return

        with NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as tmp:
            tmp.write(text)
            tmp_path = tmp.name

        try:
            fa = FiniteAutomaton.readAutomaton(tmp_path)
            accepted = fa.wordBelongs(word)
            message = "The automaton accepts the string." if accepted else "The automaton rejects the string."
            QMessageBox.information(self, "Check Word", message)
        except Exception as e:
            QMessageBox.critical(self, "Check Word", f"Operation failed: {e}")
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    def _analyze_automaton(self, workspace: WorkspaceCanvas) -> None:
        text = workspace.build_automaton_text()
        if not text:
            QMessageBox.warning(self, "Analyze", "No automaton to analyze.")
            return

        with NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as tmp:
            tmp.write(text)
            tmp_path = tmp.name

        try:
            fa = FiniteAutomaton.readAutomaton(tmp_path)
            fa_for_empty = FiniteAutomaton.readAutomaton(tmp_path)
            fa_for_infinite = FiniteAutomaton.readAutomaton(tmp_path)
            fa_for_deterministic = FiniteAutomaton.readAutomaton(tmp_path)

            is_empty = fa_for_empty.emptyLanguaje()
            is_infinite = fa_for_infinite.infiniteLanguaje()
            is_deterministic = fa_for_deterministic.deterministicAutomaton()

            # floating dialog with results
            dlg = QDialog(self)
            dlg.setWindowTitle("Analysis Results")
            layout = QGridLayout(dlg)
            layout.addWidget(QLabel("Is empty language:"), 0, 0)
            layout.addWidget(QLabel(str(bool(is_empty)).upper()), 0, 1)
            layout.addWidget(QLabel("Is infinite language:"), 1, 0)
            layout.addWidget(QLabel(str(bool(is_infinite)).upper()), 1, 1)
            layout.addWidget(QLabel("Is deterministic:"), 2, 0)
            layout.addWidget(QLabel(str(bool(is_deterministic)).upper()), 2, 1)
            dlg.setLayout(layout)
            dlg.setModal(False)
            dlg.show()

        except Exception as e:
            QMessageBox.critical(self, "Analyze", f"Operation failed: {e}")
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass
