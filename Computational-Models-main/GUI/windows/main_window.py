from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont, QIcon, QAction
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLineEdit,
    QCheckBox,
    QDialogButtonBox,
    QLabel,
    QMenu,
    QMessageBox,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QApplication,
)

from canvas.workspace_canvas import WorkspaceCanvas
from widgets.draggable_tool_button import DraggableToolButton
from tempfile import NamedTemporaryFile
import os

from library.AFND import FiniteAutomaton
from library.AFND_nullable import FiniteAutomatonNullable
from library.AFD_to_reg import dfaToRegex
from library.reg_to_AFND import regexToAutomaton
from library.automatonStack import AutomatonStack
from library.AutomatonStack_ICGrammar import grammarAutomatonStack, automatonGrammar
from library.grammar import GenerativeGrammar
from library.automaton_linear_grammar import grammarLinearRight, grammarLinearLeft, computeAssociatedAFNDLinearRight, computeAssociatedAFNDLinearLeft
from PySide6.QtWidgets import QDialog, QGridLayout, QDialogButtonBox, QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView


def _compute_pda_trace(automaton_stack, word, max_configurations=200000):
    """Returns (trace, accepted). Performs an EXHAUSTIVE backtracking search of
    the PDA's computations -- the same algorithmic approach as the library's
    own (correct) AutomatonStack.checkBelonging -- instead of greedily
    following only the first matching transition at each step.

    FIX: the previous greedy, single-path version could report REJECTED for a
    word that a genuinely non-deterministic PDA actually accepts via a
    different choice of transition, because it never backtracked when a
    greedy choice ran into a dead end. This version explores every choice and
    returns an actual accepting computation whenever one exists, so the
    step-by-step trace shown to the student matches what checkBelonging would
    say. A `visited` memo (state, remaining input, stack) both prevents
    infinite loops on unproductive epsilon-cycles and avoids re-exploring a
    configuration that has already been shown not to lead to acceptance.
    `max_configurations` bounds the search as a safety net against
    pathological inputs; it is not expected to be hit by ordinary examples.
    """
    transitions = automaton_stack.getTransitions()
    final_states = automaton_stack.getFinalStates()
    initial_state = automaton_stack.getInitialState()
    initial_stack = [automaton_stack.getInitialSymbolStack()]

    visited = set()
    budget = [max_configurations]
    last_path = []

    def search(state, remaining, stack, path):
        last_path[:] = path

        if len(remaining) == 0 and (state in final_states or len(stack) == 0):
            accepting_step = {"state": state, "remaining": "", "stack": list(stack), "transition": None}
            return path + [accepting_step]

        if not stack:
            return None

        key = (state, remaining, tuple(stack))
        if key in visited:
            return None
        visited.add(key)

        budget[0] -= 1
        if budget[0] <= 0:
            return None

        top = stack[-1]

        for t in transitions:
            if t.getInitialState() != state or t.getInitialTop() != top:
                continue
            inp = t.getInputSymbol()
            if inp != "" and (len(remaining) == 0 or inp != remaining[0]):
                continue

            for target_state, push_str in t.getTransitionTuples():
                new_stack = stack[:-1]
                if push_str:
                    for ch in reversed(push_str):
                        new_stack.append(ch)
                new_remaining = remaining if inp == "" else remaining[1:]

                step = {
                    "state": state,
                    "remaining": remaining,
                    "stack": list(stack),
                    "transition": (state, inp, top, target_state, push_str),
                }

                result = search(target_state, new_remaining, new_stack, path + [step])
                if result is not None:
                    return result

        return None

    accepting_trace = search(initial_state, word, initial_stack, [])

    if accepting_trace is not None:
        return accepting_trace, True

    # Rejected: show the last computation path explored (a real, concrete
    # attempted path) ending at its stuck configuration, for display purposes.
    if last_path:
        return last_path, False

    stuck_step = {"state": initial_state, "remaining": word, "stack": list(initial_stack), "transition": None}
    return [stuck_step], False


class SimulationDialog(QDialog):
    def __init__(self, parent, word: str, trace: list, accepted: bool, is_dfa: bool, kind: str = "fa"):
        super().__init__(parent)
        title = "Step-by-Step Simulation — FA" if kind == "fa" else "Step-by-Step Simulation — PDA"
        self.setWindowTitle(title)
        self.setMinimumSize(600, 400)
        self._trace = trace
        self._word = word
        self._accepted = accepted
        self._is_dfa = is_dfa
        self._kind = kind
        self._current_step = 0

        layout = QVBoxLayout(self)

        self._info = QTextEdit()
        self._info.setReadOnly(True)
        self._info.setStyleSheet("font-family: monospace; font-size: 16px;")
        layout.addWidget(self._info)

        self._stack_table = None
        if kind == "pda":
            self._stack_table = QTableWidget()
            self._stack_table.setColumnCount(1)
            self._stack_table.setHorizontalHeaderLabels(["Stack (bottom → top)"])
            self._stack_table.horizontalHeader().setStretchLastSection(True)
            self._stack_table.setMaximumHeight(180)
            layout.addWidget(self._stack_table)

        btn_layout = QHBoxLayout()
        self._prev_btn = QPushButton("< Prev")
        self._next_btn = QPushButton("Next >")
        self._close_btn = QPushButton("Close")
        btn_layout.addWidget(self._prev_btn)
        btn_layout.addWidget(self._next_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self._close_btn)
        layout.addLayout(btn_layout)

        self._prev_btn.clicked.connect(self._prev_step)
        self._next_btn.clicked.connect(self._next_step)
        self._close_btn.clicked.connect(self.close)

        self._workspace = None
        self._update_view()

    def set_workspace(self, ws):
        self._workspace = ws

    def _update_view(self):
        step = self._current_step
        total = len(self._trace) - 1
        entry = self._trace[step]

        if self._kind == "fa":
            states = entry["states"]
            consumed = entry["consumed"]
            remaining = entry["remaining"]
            state_str = ", ".join(states) if isinstance(states, list) else states

            lines = [
                f"Step: {step}/{total}",
                "",
                f"Consumed: '{consumed}'" if consumed else "Consumed: (start)",
                f"Remaining: '{remaining}'" if remaining else "Remaining: (end)",
                "",
                f"Current state(s): {state_str}",
            ]
            text = "\n".join(lines)

            if self._workspace:
                self._workspace.clear_highlights()
                state_list = states if isinstance(states, list) else [states]
                for s in state_list:
                    if s:
                        self._workspace.set_state_highlight(s)
        else:
            state = entry["state"]
            remaining = entry["remaining"]
            stack = entry.get("stack", [])
            trans = entry.get("transition")

            lines = [
                f"Step: {step}/{total}",
                "",
                f"State: {state}",
                f"Remaining: '{remaining}'" if remaining else "Remaining: (end)",
                "",
            ]
            if trans:
                fs, inp, pop, ts, push = trans
                lines.append(f"Transition: ({fs}, '{inp}', {pop}) → ({ts}, '{push}')")
            lines.append("")
            lines.append(f"Stack ({len(stack)} symbols):")
            text = "\n".join(lines)

            if self._stack_table:
                self._stack_table.setRowCount(len(stack))
                for i, sym in enumerate(stack):
                    item = QTableWidgetItem(sym)
                    item.setTextAlignment(Qt.AlignCenter)
                    self._stack_table.setItem(i, 0, item)

            if self._workspace:
                self._workspace.clear_highlights()
                if state:
                    self._workspace.set_state_highlight(state)

        if step == total:
            verdict = "ACCEPTED ✓" if self._accepted else "REJECTED ✗"
            text += f"\n\nResult: {verdict}"

        self._info.setPlainText(text)
        self._prev_btn.setEnabled(step > 0)
        self._next_btn.setEnabled(step < total)

    def _prev_step(self):
        if self._current_step > 0:
            self._current_step -= 1
            self._update_view()

    def _next_step(self):
        if self._current_step < len(self._trace) - 1:
            self._current_step += 1
            self._update_view()

    def closeEvent(self, event):
        if self._workspace:
            self._workspace.clear_highlights()
        super().closeEvent(event)


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
        self.stack_page = self._build_stack_page()
        self.grammar_page = self._build_grammar_page()

        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.fa_page)
        self.stack.addWidget(self.stack_page)
        self.stack.addWidget(self.grammar_page)
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
        button3 = QPushButton("Grammar")
        button4 = QPushButton("Exit")

        for button in (button1, button2, button3, button4):
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
        buttons_layout.addWidget(button4)

        button1.clicked.connect(lambda: self.stack.setCurrentWidget(self.fa_page))
        button2.clicked.connect(lambda: self.stack.setCurrentWidget(self.stack_page))
        button3.clicked.connect(lambda: self.stack.setCurrentWidget(self.grammar_page))
        button4.clicked.connect(self.close)

        main_layout.addWidget(title)
        main_layout.addWidget(buttons, 1)

        return container

    def _make_category_button(self, label: str, actions: list[tuple[str, callable]]) -> QToolButton:
        btn = QToolButton()
        btn.setText(label)
        btn.setPopupMode(QToolButton.InstantPopup)
        btn.setMinimumHeight(36)
        btn.setStyleSheet(
            "QToolButton{font-size:14px;font-weight:600;background-color:white;"
            "border:1px solid #d1d5db;border-radius:8px;padding:6px 12px;}"
            "QToolButton::menu-indicator{image:none;}"
        )
        menu = QMenu(btn)
        for text, slot in actions:
            act = QAction(text, btn)
            act.triggered.connect(slot)
            menu.addAction(act)
        btn.setMenu(menu)
        return btn

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

        # Category dropdown buttons
        edit_btn = self._make_category_button("Edit", [
            ("Clean", lambda: self._clean_automaton(workspace)),
            ("Determinize", lambda: self._determinize_automaton(workspace)),
            ("Minimize", lambda: self._minimize_automaton(workspace)),
            ("Complement", lambda: self._complement_automaton(workspace)),
            ("Reverse", lambda: self._reverse_automaton(workspace)),
        ])
        convert_btn = self._make_category_button("Convert", [
            ("Regular Expression", lambda: self._regular_expression_automaton(workspace)),
            ("Regex to FDA", lambda: self._regex_to_fda_automaton(workspace)),
            ("To Right Grammar", lambda: self._to_grammar_right_automaton(workspace)),
            ("To Left Grammar", lambda: self._to_grammar_left_automaton(workspace)),
        ])
        combine_btn = self._make_category_button("Combine", [
            ("Union", lambda: self._union_automaton(workspace)),
            ("Intersection", lambda: self._intersection_automaton(workspace)),
            ("Equivalent?", lambda: self._equivalent_automaton(workspace)),
        ])
        test_btn = self._make_category_button("Test", [
            ("Check Word", lambda: self._check_word_automaton(workspace)),
            ("Analyze", lambda: self._analyze_automaton(workspace)),
        ])

        for b in (edit_btn, convert_btn, combine_btn, test_btn):
            top_layout.addWidget(b)
        top_layout.addStretch(1)

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

    def _build_stack_page(self) -> QWidget:
        page = QWidget()
        page_vlayout = QVBoxLayout(page)
        page_vlayout.setContentsMargins(0, 0, 0, 0)
        page_vlayout.setSpacing(0)

        # Top operations bar for stack automata
        top_menu = QWidget()
        top_layout = QHBoxLayout(top_menu)
        top_layout.setContentsMargins(12, 8, 12, 8)
        top_layout.setSpacing(8)

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

        workspace = WorkspaceCanvas("stack")
        mouse_button.clicked.connect(lambda: workspace.set_active_tool("hand"))
        arrow_button.clicked.connect(lambda: workspace.set_active_tool("arrow"))
        delete_button.clicked.connect(lambda: workspace.set_active_tool("delete"))
        open_button.clicked.connect(lambda: self._open_finite_automaton(workspace))
        save_button.clicked.connect(lambda: self._save_finite_automaton(workspace))

        # Category dropdown buttons
        edit_btn = self._make_category_button("Edit", [
            ("Simplify", lambda: self._simplify_stack_automaton(workspace)),
            ("Complement (det.)", lambda: self._complement_stack_automaton(workspace)),
        ])
        convert_btn = self._make_category_button("Convert", [
            ("To Grammar", lambda: self._to_grammar_stack_automaton(workspace)),
            ("To Final-State", lambda: self._to_final_state_stack(workspace)),
            ("To Empty-Stack", lambda: self._to_empty_stack_stack(workspace)),
        ])
        combine_btn = self._make_category_button("Combine", [
            ("Intersect with DFA", lambda: self._intersect_stack_with_dfa(workspace)),
        ])
        test_btn = self._make_category_button("Test", [
            ("Check Word", lambda: self._check_word_stack_automaton(workspace)),
            ("Analyze", lambda: self._analyze_stack_automaton(workspace)),
        ])

        for b in (edit_btn, convert_btn, combine_btn, test_btn):
            top_layout.addWidget(b)
        top_layout.addStretch(1)

        main_row = QWidget()
        main_row_layout = QHBoxLayout(main_row)
        main_row_layout.setContentsMargins(0, 0, 0, 0)
        main_row_layout.setSpacing(0)
        main_row_layout.addWidget(tool_menu)
        main_row_layout.addWidget(workspace, 1)

        page_vlayout.addWidget(top_menu)
        page_vlayout.addWidget(main_row, 1)

        return page

    def _grammar_to_text(self, grammar) -> str:
        tmp = NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8")
        grammar.writeGrammar(tmp.name)
        tmp_path = tmp.name
        tmp.close()
        with open(tmp_path, "r", encoding="utf-8") as f:
            text = f.read()
        os.remove(tmp_path)
        return text

    def _grammar_from_editor(self, editor: QPlainTextEdit) -> GenerativeGrammar | None:
        text = editor.toPlainText().strip()
        if not text:
            return None
        tmp = NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8")
        tmp.write(text)
        tmp_path = tmp.name
        tmp.close()
        try:
            g = GenerativeGrammar.readGrammar(tmp_path)
            return g
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    def _build_grammar_page(self) -> QWidget:
        page = QWidget()
        page_vlayout = QVBoxLayout(page)
        page_vlayout.setContentsMargins(0, 0, 0, 0)
        page_vlayout.setSpacing(0)

        # Top operations bar
        top_menu = QWidget()
        top_layout = QHBoxLayout(top_menu)
        top_layout.setContentsMargins(12, 8, 12, 8)
        top_layout.setSpacing(8)

        # Left toolbar
        tool_menu = QWidget()
        tool_menu.setFixedWidth(90)
        tool_menu.setStyleSheet("background-color: #f3f4f6;")
        tool_layout = QVBoxLayout(tool_menu)
        tool_layout.setContentsMargins(12, 12, 12, 12)
        tool_layout.setSpacing(12)

        open_btn = QPushButton("Open")
        open_btn.setMinimumHeight(44)
        open_btn.setStyleSheet(
            "font-size: 16px; font-weight: 600; background-color: white; border: 1px solid #d1d5db; border-radius: 10px;"
        )

        save_btn = QPushButton("Save")
        save_btn.setMinimumHeight(44)
        save_btn.setStyleSheet(
            "font-size: 16px; font-weight: 600; background-color: white; border: 1px solid #d1d5db; border-radius: 10px;"
        )

        back_btn = QPushButton("Back")
        back_btn.setMinimumHeight(44)
        back_btn.setStyleSheet(
            "font-size: 16px; font-weight: 600; background-color: white; border: 1px solid #d1d5db; border-radius: 10px;"
        )
        back_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.home_page))

        tool_layout.addWidget(open_btn)
        tool_layout.addWidget(save_btn)
        tool_layout.addStretch(1)
        tool_layout.addWidget(back_btn)

        # Grammar text editor
        editor = QPlainTextEdit()
        editor.setStyleSheet("font-family: monospace; font-size: 14px; padding: 8px;")
        editor.setPlaceholderText(
            "Enter grammar here...\n\n"
            "Format:\n"
            "V = {S,A,B}\n"
            "T = {a,b}\n"
            "\n"
            "S -> a<A>|b<B>\n"
            "A -> a|a<A>\n"
            "B -> b|b<B>"
        )

        open_btn.clicked.connect(lambda: self._grammar_open(editor))
        save_btn.clicked.connect(lambda: self._grammar_save(editor))

        # Category dropdown buttons
        edit_btn = self._make_category_button("Edit", [
            ("Simplify", lambda: self._grammar_simplify(editor)),
            ("Chomsky", lambda: self._grammar_chomsky(editor)),
            ("Greibach", lambda: self._grammar_greibach(editor)),
        ])
        check_btn = self._make_category_button("Check", [
            ("CYK", lambda: self._grammar_cyk(editor)),
            ("Earley", lambda: self._grammar_earley(editor)),
        ])
        combine_btn = self._make_category_button("Combine", [
            ("Union", lambda: self._grammar_union(editor)),
            ("Concatenation", lambda: self._grammar_concat(editor)),
            ("Closure", lambda: self._grammar_closure(editor)),
        ])
        convert_btn = self._make_category_button("Convert", [
            ("To AFND Right", lambda: self._grammar_to_afnd_right(editor)),
            ("To AFND Left", lambda: self._grammar_to_afnd_left(editor)),
            ("To PDA", lambda: self._grammar_to_pda(editor)),
        ])

        for b in (edit_btn, check_btn, combine_btn, convert_btn):
            top_layout.addWidget(b)
        top_layout.addStretch(1)

        main_row = QWidget()
        main_row_layout = QHBoxLayout(main_row)
        main_row_layout.setContentsMargins(0, 0, 0, 0)
        main_row_layout.setSpacing(0)
        main_row_layout.addWidget(tool_menu)
        main_row_layout.addWidget(editor, 1)

        page_vlayout.addWidget(top_menu)
        page_vlayout.addWidget(main_row, 1)

        return page

    def _set_active_tool_button(self, active_button: QPushButton, inactive_buttons: list[QPushButton]) -> None:
        active_button.setStyleSheet(self._active_tool_button_style)
        for button in inactive_buttons:
            button.setStyleSheet(self._tool_button_style)

    def _save_finite_automaton(self, workspace: WorkspaceCanvas) -> None:
        if not workspace.has_initial_state():
            QMessageBox.warning(
                self,
                "Guardar automata",
                "No hay ningun estado marcado como inicial. "
                "Marca un estado como inicial antes de guardar: "
                "el fichero no indica cual es el estado inicial y, "
                "al volver a abrirlo, se tomaria uno cualquiera por defecto.",
            )
            return

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
            fa = FiniteAutomatonNullable.readAutomaton(tmp_path)
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

    def _determinize_automaton(self, workspace: WorkspaceCanvas) -> None:
        fa, tmp_path = self._read_fa_from_workspace(workspace)
        if fa is None:
            QMessageBox.warning(self, "Determinize", "No automaton to determinize.")
            return
        if fa.deterministicAutomaton():
            QMessageBox.information(self, "Determinize", "Already deterministic.")
            return
        try:
            result = fa.transformDeterministic()
            result.deleteInaccessibleStates()
            result.deleteErrorStates()
            self._write_tmp_and_load(workspace, result)
            QMessageBox.information(self, "Determinize", "Determinized (NFA → DFA).")
        except Exception as e:
            QMessageBox.critical(self, "Determinize", f"Operation failed: {e}")
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
            fa = FiniteAutomatonNullable.readAutomaton(tmp_path)
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

    def _regular_expression_automaton(self, workspace: WorkspaceCanvas) -> None:
        text = workspace.build_automaton_text()
        if not text:
            QMessageBox.warning(self, "Regular Expression", "No automaton to convert.")
            return

        with NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as tmp:
            tmp.write(text)
            tmp_path = tmp.name

        try:
            fa = FiniteAutomatonNullable.readAutomaton(tmp_path)
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
        checkbox.setChecked(True)  # FIX: default to the safer, immediately-usable DFA output

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
            fa = FiniteAutomatonNullable.readAutomaton(tmp_path)
            is_dfa = fa.deterministicAutomaton()
            initial = fa.getInitialState()
            alphabet = fa.getAlphabetSymbols()

            # FIX: step through the word using the epsilon-aware public
            # delta* (fa.deltaStarSymbol), not the raw base-class
            # fa._delta_star_symbol, which ignores null transitions entirely.
            # The very first displayed state set is also the epsilon-closure
            # of the initial state, matching delta*({q0}, epsilon) = Cl({q0}).
            current_states = fa.clousureStatesSet([initial])
            trace = [{"states": current_states, "consumed": "", "remaining": word}]

            for i, ch in enumerate(word):
                current_states = fa.deltaStarSymbol(current_states, ch)
                trace.append({
                    "states": current_states,
                    "consumed": word[:i+1],
                    "remaining": word[i+1:],
                })

            accepted = fa.wordBelongs(word)

            dlg = SimulationDialog(self, word, trace, accepted, is_dfa, kind="fa")
            dlg.set_workspace(workspace)
            dlg.exec()
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
            fa = FiniteAutomatonNullable.readAutomaton(tmp_path)
            fa_for_empty = FiniteAutomatonNullable.readAutomaton(tmp_path)
            fa_for_infinite = FiniteAutomatonNullable.readAutomaton(tmp_path)
            fa_for_deterministic = FiniteAutomatonNullable.readAutomaton(tmp_path)

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

    def _read_fa_from_workspace(self, workspace: WorkspaceCanvas):
        """Helper: build text from canvas, write to temp file, return (FiniteAutomaton, tmp_path) or (None, None)."""
        text = workspace.build_automaton_text()
        if not text:
            return None, None
        tmp = NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8")
        tmp.write(text)
        tmp_path = tmp.name
        tmp.close()
        try:
            fa = FiniteAutomatonNullable.readAutomaton(tmp_path)
            return fa, tmp_path
        except Exception:
            try:
                os.remove(tmp_path)
            except Exception:
                pass
            raise

    def _load_second_automaton_dialog(self) -> FiniteAutomaton | None:
        """Open a file dialog to load a second finite automaton. Returns FiniteAutomaton or None."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Select second automaton", "",
            "Text files (*.txt);;All files (*.*)"
        )
        if not path:
            return None
        try:
            return FiniteAutomatonNullable.readAutomaton(path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load second automaton: {e}")
            return None

    def _show_grammar_dialog(self, title: str, grammar: GenerativeGrammar) -> None:
        """Show a GenerativeGrammar in a read-only dialog."""
        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        layout = QVBoxLayout(dlg)
        label = QLabel()
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        label.setWordWrap(True)
        label.setStyleSheet("font-family: monospace; white-space: pre; background: #f9f9f9; padding: 8px;")
        layout.addWidget(label, 1)
        tmp_g = NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8")
        grammar.writeGrammar(tmp_g.name)
        tmp_g.close()
        with open(tmp_g.name, "r", encoding="utf-8") as f:
            label.setText(f.read())
        os.remove(tmp_g.name)
        dlg.setLayout(layout)
        dlg.setModal(False)
        dlg.resize(700, 500)
        dlg.show()

    def _complement_automaton(self, workspace: WorkspaceCanvas) -> None:
        fa, tmp_path = self._read_fa_from_workspace(workspace)
        if fa is None:
            QMessageBox.warning(self, "Complement", "No automaton to complement.")
            return
        try:
            result = fa.complementaryAutomaton()
            self._write_tmp_and_load(workspace, result)
            QMessageBox.information(self, "Complement", "Complement computed.")
        except Exception as e:
            QMessageBox.critical(self, "Complement", f"Operation failed: {e}")
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    def _reverse_automaton(self, workspace: WorkspaceCanvas) -> None:
        fa, tmp_path = self._read_fa_from_workspace(workspace)
        if fa is None:
            QMessageBox.warning(self, "Reverse", "No automaton to reverse.")
            return
        try:
            result = fa.computeReverseAutomaton()
            if result is None:
                QMessageBox.warning(self, "Reverse", "Reverse requires exactly one final state.")
                return
            self._write_tmp_and_load(workspace, result)
            QMessageBox.information(self, "Reverse", "Reverse computed.")
        except Exception as e:
            QMessageBox.critical(self, "Reverse", f"Operation failed: {e}")
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    def _union_automaton(self, workspace: WorkspaceCanvas) -> None:
        fa_a, tmp_path = self._read_fa_from_workspace(workspace)
        if fa_a is None:
            QMessageBox.warning(self, "Union", "No automaton A on the canvas.")
            return
        fa_b = self._load_second_automaton_dialog()
        if fa_b is None:
            return
        try:
            result = fa_a.unionAutomaton(fa_b)
            if result is None:
                QMessageBox.warning(self, "Union", "Both automata must have the same input alphabet.")
                return
            self._write_tmp_and_load(workspace, result)
            QMessageBox.information(self, "Union", "Union computed.")
        except Exception as e:
            QMessageBox.critical(self, "Union", f"Operation failed: {e}")
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    def _intersection_automaton(self, workspace: WorkspaceCanvas) -> None:
        fa_a, tmp_path = self._read_fa_from_workspace(workspace)
        if fa_a is None:
            QMessageBox.warning(self, "Intersection", "No automaton A on the canvas.")
            return
        fa_b = self._load_second_automaton_dialog()
        if fa_b is None:
            return
        try:
            result = fa_a.intersectionAutomaton(fa_b)
            if result is None:
                QMessageBox.warning(self, "Intersection", "Both automata must have the same input alphabet.")
                return
            self._write_tmp_and_load(workspace, result)
            QMessageBox.information(self, "Intersection", "Intersection computed.")
        except Exception as e:
            QMessageBox.critical(self, "Intersection", f"Operation failed: {e}")
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    def _equivalent_automaton(self, workspace: WorkspaceCanvas) -> None:
        fa_a, tmp_path = self._read_fa_from_workspace(workspace)
        if fa_a is None:
            QMessageBox.warning(self, "Equivalent?", "No automaton A on the canvas.")
            return
        fa_b = self._load_second_automaton_dialog()
        if fa_b is None:
            return
        try:
            equivalent = fa_a.sameLanguaje(fa_b)
            msg = "The automata recognise the SAME language." if equivalent else "The automata recognise DIFFERENT languages."
            QMessageBox.information(self, "Equivalent?", msg)
        except Exception as e:
            QMessageBox.critical(self, "Equivalent?", f"Operation failed: {e}")
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    def _to_grammar_right_automaton(self, workspace: WorkspaceCanvas) -> None:
        fa, tmp_path = self._read_fa_from_workspace(workspace)
        if fa is None:
            QMessageBox.warning(self, "To Right Grammar", "No automaton to convert.")
            return
        try:
            grammar = grammarLinearRight(fa)
            self._show_grammar_dialog("Right-Linear Grammar", grammar)
        except Exception as e:
            QMessageBox.critical(self, "To Right Grammar", f"Operation failed: {e}")
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    def _to_grammar_left_automaton(self, workspace: WorkspaceCanvas) -> None:
        fa, tmp_path = self._read_fa_from_workspace(workspace)
        if fa is None:
            QMessageBox.warning(self, "To Left Grammar", "No automaton to convert.")
            return
        try:
            grammar = grammarLinearLeft(fa)
            if grammar is None:
                QMessageBox.warning(self, "To Left Grammar", "The automaton must have exactly one final state.")
                return
            self._show_grammar_dialog("Left-Linear Grammar", grammar)
        except Exception as e:
            QMessageBox.critical(self, "To Left Grammar", f"Operation failed: {e}")
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    def _simplify_stack_automaton(self, workspace: WorkspaceCanvas) -> None:
        text = workspace.build_automaton_text()
        if not text:
            QMessageBox.warning(self, "Simplify", "No stack automaton to simplify.")
            return

        with NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as tmp:
            tmp.write(text)
            tmp_path = tmp.name

        try:
            automaton_stack = AutomatonStack.readAutomaton(tmp_path)
            automaton_stack.simplify()

            tmp2 = NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8")
            automaton_stack.writeAutomaton(tmp2.name)
            tmp2_path = tmp2.name
            tmp2.close()

            workspace.load_automaton_from_file(tmp2_path)
            QMessageBox.information(self, "Simplify", "Removed inaccessible and dead states.")
            os.remove(tmp2_path)
        except Exception as e:
            QMessageBox.critical(self, "Simplify", f"Operation failed: {e}")
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    def _to_grammar_stack_automaton(self, workspace: WorkspaceCanvas) -> None:
        text = workspace.build_automaton_text()
        if not text:
            QMessageBox.warning(self, "To Grammar", "No stack automaton to convert.")
            return

        with NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as tmp:
            tmp.write(text)
            tmp_path = tmp.name

        try:
            automaton_stack = AutomatonStack.readAutomaton(tmp_path)
            grammar = grammarAutomatonStack(automaton_stack)

            dlg = QDialog(self)
            dlg.setWindowTitle("Generated Grammar")
            layout = QVBoxLayout(dlg)

            text_edit = QLabel()
            text_edit.setTextInteractionFlags(Qt.TextSelectableByMouse)
            text_edit.setWordWrap(True)
            text_edit.setStyleSheet("font-family: monospace; white-space: pre; background: #f9f9f9; padding: 8px;")
            layout.addWidget(text_edit, 1)

            tmp_g = NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8")
            grammar.writeGrammar(tmp_g.name)
            tmp_g.close()
            with open(tmp_g.name, "r", encoding="utf-8") as f:
                text_edit.setText(f.read())
            os.remove(tmp_g.name)

            dlg.setLayout(layout)
            dlg.setModal(False)
            dlg.resize(700, 500)
            dlg.show()
        except Exception as e:
            QMessageBox.critical(self, "To Grammar", f"Operation failed: {e}")
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    def _to_final_state_stack(self, workspace: WorkspaceCanvas) -> None:
        """Convert PDA from empty-stack to final-state acceptance."""
        text = workspace.build_automaton_text()
        if not text:
            QMessageBox.warning(self, "To Final-State", "No stack automaton to convert.")
            return

        with NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as tmp:
            tmp.write(text)
            tmp_path = tmp.name

        try:
            pda = AutomatonStack.readAutomaton(tmp_path)
            result = pda.equivalentAutomatonFinalStates()

            tmp2 = NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8")
            result.writeAutomaton(tmp2.name)
            tmp2_path = tmp2.name
            tmp2.close()

            workspace.load_automaton_from_file(tmp2_path)
            QMessageBox.information(self, "To Final-State", "Converted to final-state acceptance.")
            os.remove(tmp2_path)
        except Exception as e:
            QMessageBox.critical(self, "To Final-State", f"Operation failed: {e}")
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    def _to_empty_stack_stack(self, workspace: WorkspaceCanvas) -> None:
        """Convert PDA from final-state to empty-stack acceptance."""
        text = workspace.build_automaton_text()
        if not text:
            QMessageBox.warning(self, "To Empty-Stack", "No stack automaton to convert.")
            return

        with NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as tmp:
            tmp.write(text)
            tmp_path = tmp.name

        try:
            pda = AutomatonStack.readAutomaton(tmp_path)
            result = pda.equivalentAutomatonEmptyStack()

            tmp2 = NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8")
            result.writeAutomaton(tmp2.name)
            tmp2_path = tmp2.name
            tmp2.close()

            workspace.load_automaton_from_file(tmp2_path)
            QMessageBox.information(self, "To Empty-Stack", "Converted to empty-stack acceptance.")
            os.remove(tmp2_path)
        except Exception as e:
            QMessageBox.critical(self, "To Empty-Stack", f"Operation failed: {e}")
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    def _complement_stack_automaton(self, workspace: WorkspaceCanvas) -> None:
        """Complement of a deterministic PDA."""
        text = workspace.build_automaton_text()
        if not text:
            QMessageBox.warning(self, "Complement", "No stack automaton to complement.")
            return

        with NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as tmp:
            tmp.write(text)
            tmp_path = tmp.name

        try:
            pda = AutomatonStack.readAutomaton(tmp_path)
            result = pda.complementaryDeterministic()
            if result is None:
                QMessageBox.warning(self, "Complement", "The PDA is not deterministic. Complement requires a deterministic PDA.")
                return

            tmp2 = NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8")
            result.writeAutomaton(tmp2.name)
            tmp2_path = tmp2.name
            tmp2.close()

            workspace.load_automaton_from_file(tmp2_path)
            QMessageBox.information(self, "Complement", "Complement computed.")
            os.remove(tmp2_path)
        except Exception as e:
            QMessageBox.critical(self, "Complement", f"Operation failed: {e}")
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    def _intersect_stack_with_dfa(self, workspace: WorkspaceCanvas) -> None:
        """Intersect PDA with a DFA loaded from file."""
        text = workspace.build_automaton_text()
        if not text:
            QMessageBox.warning(self, "Intersect with DFA", "No stack automaton on the canvas.")
            return

        dfa_path, _ = QFileDialog.getOpenFileName(
            self, "Select DFA file", "",
            "Text files (*.txt);;All files (*.*)"
        )
        if not dfa_path:
            return

        with NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as tmp:
            tmp.write(text)
            tmp_path = tmp.name

        try:
            pda = AutomatonStack.readAutomaton(tmp_path)
            dfa = FiniteAutomatonNullable.readAutomaton(dfa_path)
            result = pda.intersectionFiniteAutomaton(dfa)
            if result is None:
                QMessageBox.warning(self, "Intersect with DFA", "Intersection failed. Check alphabet compatibility.")
                return

            tmp2 = NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8")
            result.writeAutomaton(tmp2.name)
            tmp2_path = tmp2.name
            tmp2.close()

            workspace.load_automaton_from_file(tmp2_path)
            QMessageBox.information(self, "Intersect with DFA", "Intersection computed.")
            os.remove(tmp2_path)
        except Exception as e:
            QMessageBox.critical(self, "Intersect with DFA", f"Operation failed: {e}")
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    def _check_word_stack_automaton(self, workspace: WorkspaceCanvas) -> None:
        text = workspace.build_automaton_text()
        if not text:
            QMessageBox.warning(self, "Check Word", "No stack automaton to check.")
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
            automaton_stack = AutomatonStack.readAutomaton(tmp_path)
            trace, accepted = _compute_pda_trace(automaton_stack, word)
            dlg = SimulationDialog(self, word, trace, accepted, True, kind="pda")
            dlg.set_workspace(workspace)
            dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Check Word", f"Operation failed: {e}")
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    def _analyze_stack_automaton(self, workspace: WorkspaceCanvas) -> None:
        text = workspace.build_automaton_text()
        if not text:
            QMessageBox.warning(self, "Analyze", "No stack automaton to analyze.")
            return

        with NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as tmp:
            tmp.write(text)
            tmp_path = tmp.name

        try:
            automaton_stack = AutomatonStack.readAutomaton(tmp_path)
            is_deterministic = automaton_stack.isDeterministic()
            uses_final_states = len(automaton_stack.getFinalStates()) > 0
            acceptance_criterion = "Final states" if uses_final_states else "Empty stack"

            dlg = QDialog(self)
            dlg.setWindowTitle("Stack Analysis Results")
            layout = QGridLayout(dlg)
            layout.addWidget(QLabel("Is deterministic:"), 0, 0)
            layout.addWidget(QLabel(str(bool(is_deterministic)).upper()), 0, 1)
            layout.addWidget(QLabel("Acceptance criterion:"), 1, 0)
            layout.addWidget(QLabel(acceptance_criterion), 1, 1)
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

    # ── Grammar page handlers ──────────────────────────────────────────────

    def _grammar_open(self, editor: QPlainTextEdit) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open grammar", "",
            "Text files (*.txt);;All files (*.*)"
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                editor.setPlainText(f.read())
        except Exception as e:
            QMessageBox.critical(self, "Open", f"Failed to open file: {e}")

    def _grammar_save(self, editor: QPlainTextEdit) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save grammar", "",
            "Text files (*.txt);;All files (*.*)"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(editor.toPlainText())
        except Exception as e:
            QMessageBox.critical(self, "Save", f"Failed to save file: {e}")

    def _grammar_simplify(self, editor: QPlainTextEdit) -> None:
        g = self._grammar_from_editor(editor)
        if g is None:
            QMessageBox.warning(self, "Simplify", "No grammar to simplify.")
            return
        try:
            g.deleteNullProductions()
            g.deleteUnitaryProductions()
            g.deleteUselessSymbolsProductions()
            editor.setPlainText(self._grammar_to_text(g))
            QMessageBox.information(self, "Simplify", "Removed null/unit/useless productions.")
        except Exception as e:
            QMessageBox.critical(self, "Simplify", f"Operation failed: {e}")

    def _grammar_chomsky(self, editor: QPlainTextEdit) -> None:
        g = self._grammar_from_editor(editor)
        if g is None:
            QMessageBox.warning(self, "Chomsky", "No grammar to transform.")
            return
        try:
            g.transformChomsky()
            editor.setPlainText(self._grammar_to_text(g))
            QMessageBox.information(self, "Chomsky", "Converted to Chomsky Normal Form.")
        except Exception as e:
            QMessageBox.critical(self, "Chomsky", f"Operation failed: {e}")

    def _grammar_greibach(self, editor: QPlainTextEdit) -> None:
        g = self._grammar_from_editor(editor)
        if g is None:
            QMessageBox.warning(self, "Greibach", "No grammar to transform.")
            return
        try:
            g.transformGreibach()
            editor.setPlainText(self._grammar_to_text(g))
            QMessageBox.information(self, "Greibach", "Converted to Greibach Normal Form.")
        except Exception as e:
            QMessageBox.critical(self, "Greibach", f"Operation failed: {e}")

    def _grammar_cyk(self, editor: QPlainTextEdit) -> None:
        g = self._grammar_from_editor(editor)
        if g is None:
            QMessageBox.warning(self, "CYK", "No grammar.")
            return
        word, ok = QInputDialog.getText(self, "CYK", "Enter word to check:")
        if not ok:
            return
        try:
            g.transformChomsky()
            accepted = g.checkBelongingCYK(word)
            msg = "The word IS generated by the grammar." if accepted else "The word IS NOT generated by the grammar."
            QMessageBox.information(self, "CYK", msg)
        except Exception as e:
            QMessageBox.critical(self, "CYK", f"Operation failed: {e}")

    def _grammar_earley(self, editor: QPlainTextEdit) -> None:
        g = self._grammar_from_editor(editor)
        if g is None:
            QMessageBox.warning(self, "Earley", "No grammar.")
            return
        word, ok = QInputDialog.getText(self, "Earley", "Enter word to check:")
        if not ok:
            return
        try:
            accepted = g.checkBelongingEarly(word)
            msg = "The word IS generated by the grammar." if accepted else "The word IS NOT generated by the grammar."
            QMessageBox.information(self, "Earley", msg)
        except Exception as e:
            QMessageBox.critical(self, "Earley", f"Operation failed: {e}")

    def _grammar_union(self, editor: QPlainTextEdit) -> None:
        g = self._grammar_from_editor(editor)
        if g is None:
            QMessageBox.warning(self, "Union", "No grammar A in the editor.")
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Select second grammar", "",
            "Text files (*.txt);;All files (*.*)"
        )
        if not path:
            return
        try:
            g2 = GenerativeGrammar.readGrammar(path)
            result = g.unionGrammar(g2)
            if result is None:
                QMessageBox.warning(self, "Union", "Both grammars must have the same terminal symbols.")
                return
            editor.setPlainText(self._grammar_to_text(result))
            QMessageBox.information(self, "Union", "Union computed.")
        except Exception as e:
            QMessageBox.critical(self, "Union", f"Operation failed: {e}")

    def _grammar_concat(self, editor: QPlainTextEdit) -> None:
        g = self._grammar_from_editor(editor)
        if g is None:
            QMessageBox.warning(self, "Concatenation", "No grammar A in the editor.")
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Select second grammar", "",
            "Text files (*.txt);;All files (*.*)"
        )
        if not path:
            return
        try:
            g2 = GenerativeGrammar.readGrammar(path)
            result = g.concatenationGrammar(g2)
            if result is None:
                QMessageBox.warning(self, "Concatenation", "Both grammars must have the same terminal symbols.")
                return
            editor.setPlainText(self._grammar_to_text(result))
            QMessageBox.information(self, "Concatenation", "Concatenation computed.")
        except Exception as e:
            QMessageBox.critical(self, "Concatenation", f"Operation failed: {e}")

    def _grammar_closure(self, editor: QPlainTextEdit) -> None:
        g = self._grammar_from_editor(editor)
        if g is None:
            QMessageBox.warning(self, "Closure", "No grammar.")
            return
        try:
            result = g.clausureGrammar()
            editor.setPlainText(self._grammar_to_text(result))
            QMessageBox.information(self, "Closure", "Kleene closure computed.")
        except Exception as e:
            QMessageBox.critical(self, "Closure", f"Operation failed: {e}")

    def _grammar_to_afnd_right(self, editor: QPlainTextEdit) -> None:
        g = self._grammar_from_editor(editor)
        if g is None:
            QMessageBox.warning(self, "To AFND Right", "No grammar.")
            return
        try:
            fa = computeAssociatedAFNDLinearRight(g)
            if fa is None:
                QMessageBox.warning(self, "To AFND Right", "The grammar must be linear by the right.")
                return
            ws = self.fa_page.findChild(WorkspaceCanvas)
            if ws:
                self._write_tmp_and_load(ws, fa)
            self.stack.setCurrentWidget(self.fa_page)
            QMessageBox.information(self, "To AFND Right", "AFND created and loaded into FA page.")
        except Exception as e:
            QMessageBox.critical(self, "To AFND Right", f"Operation failed: {e}")

    def _grammar_to_afnd_left(self, editor: QPlainTextEdit) -> None:
        g = self._grammar_from_editor(editor)
        if g is None:
            QMessageBox.warning(self, "To AFND Left", "No grammar.")
            return
        try:
            fa = computeAssociatedAFNDLinearLeft(g)
            if fa is None:
                QMessageBox.warning(self, "To AFND Left", "The grammar must be linear by the left.")
                return
            ws = self.fa_page.findChild(WorkspaceCanvas)
            if ws:
                self._write_tmp_and_load(ws, fa)
            self.stack.setCurrentWidget(self.fa_page)
            QMessageBox.information(self, "To AFND Left", "AFND created and loaded into FA page.")
        except Exception as e:
            QMessageBox.critical(self, "To AFND Left", f"Operation failed: {e}")

    def _grammar_to_pda(self, editor: QPlainTextEdit) -> None:
        g = self._grammar_from_editor(editor)
        if g is None:
            QMessageBox.warning(self, "To PDA", "No grammar.")
            return
        try:
            pda = automatonGrammar(g)
            tmp = NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8")
            pda.writeAutomaton(tmp.name)
            tmp_path = tmp.name
            tmp.close()
            with open(tmp_path, "r", encoding="utf-8") as f:
                text = f.read()
            ws = self.stack_page.findChild(WorkspaceCanvas)
            if ws:
                ws.load_automaton_text(text)
            self.stack.setCurrentWidget(self.stack_page)
            QMessageBox.information(self, "To PDA", "PDA created and loaded into Stack page.")
        except Exception as e:
            QMessageBox.critical(self, "To PDA", f"Operation failed: {e}")
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass
