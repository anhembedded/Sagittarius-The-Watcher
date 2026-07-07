from PySide6.QtWidgets import QTableView, QMenu, QApplication
from PySide6.QtCore import Qt, QEvent, Slot
from PySide6.QtGui import QFont, QKeySequence, QAction

class LogTableView(QTableView):
    """Custom TableView for Logs."""

    def __init__(self, log_tab, parent=None):
        super().__init__(parent)
        self.log_tab = log_tab
        self.main_window = log_tab.main_window

        self.setAlternatingRowColors(True)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

        # Feature 8
        self.setSortingEnabled(True)
        self.horizontalHeader().sectionClicked.connect(self._on_header_clicked)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        # Install event filter for Ctrl+Scroll zoom (Feature 9)
        self.viewport().installEventFilter(self)

    def _on_header_clicked(self, col: int):
        # Toggle sort order if same column, else default ascending
        pass  # Handled automatically by setSortingEnabled + model.sort()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_F2:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                # Previous bookmark
                self._navigate_bookmark(-1)
            elif event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                # Next bookmark
                self._navigate_bookmark(1)
            else:
                # Toggle bookmark on current row
                idx = self.currentIndex()
                if idx.isValid():
                    self.model().toggle_bookmark(idx.row())
        else:
            super().keyPressEvent(event)

    def _navigate_bookmark(self, direction: int):
        idx = self.currentIndex()
        current_row = idx.row() if idx.isValid() else -1
        new_row = self.model().get_bookmark_row(current_row, direction)
        if new_row >= 0:
            new_idx = self.model().index(new_row, 3) # any valid column
            self.setCurrentIndex(new_idx)
            self.scrollTo(new_idx, QTableView.ScrollHint.PositionAtCenter)

    def eventFilter(self, obj, event):
        if obj is self.viewport():
            if event.type() == QEvent.Type.Wheel:
                if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                    delta = event.angleDelta().y()
                    self.main_window._zoom_font(1 if delta > 0 else -1)
                    return True
        return super().eventFilter(obj, event)

    def _show_context_menu(self, pos):
        menu = QMenu(self)

        action_copy_raw = QAction("Copy Selected Logs", self)
        action_copy_raw.setShortcut(QKeySequence("Ctrl+C"))
        action_copy_raw.triggered.connect(self.main_window._copy_selected_rows)
        menu.addAction(action_copy_raw)

        action_copy_msg = QAction("Copy Message Only", self)
        action_copy_msg.triggered.connect(self.main_window._copy_selected_messages)
        menu.addAction(action_copy_msg)

        menu.exec(self.viewport().mapToGlobal(pos))
