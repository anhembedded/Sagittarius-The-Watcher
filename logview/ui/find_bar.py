from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)


class FindBar(QWidget):
    """Collapsible in-app search bar (similar to a browser Ctrl+F bar).

    Signals:
        term_changed(str, bool): Emitted when the search text changes or regex is toggled.
        navigate(int): Emitted when user requests next (+1) or previous (-1) match.
        closed(): Emitted when the bar is dismissed.
    """

    term_changed = Signal(str, bool)
    navigate = Signal(int)
    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVisible(False)
        self.setFixedHeight(34)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(4)

        layout.addWidget(QLabel("Find:"))

        self._input = QLineEdit()
        self._input.setPlaceholderText("Search in logs…")
        self._input.setFixedWidth(240)
        self._input.textChanged.connect(self._emit_term_changed)
        self._input.returnPressed.connect(lambda: self.navigate.emit(1))
        layout.addWidget(self._input)

        self._regex_cb = QCheckBox("Regex")
        self._regex_cb.setAccessibleName("Regex Search")
        self._regex_cb.stateChanged.connect(self._emit_term_changed)
        layout.addWidget(self._regex_cb)

        self._match_label = QLabel("")
        self._match_label.setMinimumWidth(70)
        self._match_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(self._match_label)

        btn_prev = QPushButton("▲")
        btn_prev.setFixedSize(26, 24)
        btn_prev.setToolTip("Previous match (Shift+Enter)")
        btn_prev.clicked.connect(lambda: self.navigate.emit(-1))
        layout.addWidget(btn_prev)

        btn_next = QPushButton("▼")
        btn_next.setFixedSize(26, 24)
        btn_next.setToolTip("Next match (Enter)")
        btn_next.clicked.connect(lambda: self.navigate.emit(1))
        layout.addWidget(btn_next)

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(26, 24)
        btn_close.setToolTip("Close (Esc)")
        btn_close.clicked.connect(self.close_bar)
        layout.addWidget(btn_close)

        layout.addStretch()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def open(self):
        """Show the bar and focus the input."""
        self.setVisible(True)
        self._input.setFocus()
        self._input.selectAll()

    def close_bar(self):
        """Hide the bar and clear the search term."""
        self.setVisible(False)
        self._input.clear()
        self.term_changed.emit("", False)
        self.closed.emit()

    def _emit_term_changed(self, *args):
        self.term_changed.emit(self._input.text(), self._regex_cb.isChecked())

    def set_match_info(self, current: int, total: int):
        """Update the match counter label."""
        if total == 0 and self._input.text():
            self._match_label.setText("No matches")
            self._match_label.setStyleSheet("color: #c0392b; font-size: 10px;")
        elif total > 0:
            self._match_label.setText(f"{current}/{total}")
            self._match_label.setStyleSheet("color: gray; font-size: 10px;")
        else:
            self._match_label.setText("")

    def get_term(self) -> str:
        return self._input.text()

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close_bar()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.navigate.emit(-1)
            else:
                self.navigate.emit(1)
        else:
            super().keyPressEvent(event)
