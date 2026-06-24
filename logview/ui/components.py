from PySide6.QtWidgets import (QWidget, QHBoxLayout, QLineEdit, QComboBox,
                                 QCheckBox, QLabel)
from PySide6.QtCore import Signal

class FilterPanel(QWidget):
    """
    Panel containing filter controls.
    """
    filter_changed = Signal(str, str, bool) # text, level, regex

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter logs...")

        self.level_combo = QComboBox()
        self.level_combo.addItems(["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])

        self.regex_checkbox = QCheckBox("Regex")

        layout.addWidget(QLabel("Search:"))
        layout.addWidget(self.search_input)
        layout.addWidget(QLabel("Level:"))
        layout.addWidget(self.level_combo)
        layout.addWidget(self.regex_checkbox)

        # Connect signals
        self.search_input.textChanged.connect(self._on_filter_changed)
        self.level_combo.currentTextChanged.connect(self._on_filter_changed)
        self.regex_checkbox.stateChanged.connect(self._on_filter_changed)

    def _on_filter_changed(self):
        text = self.search_input.text()
        level = self.level_combo.currentText()
        use_regex = self.regex_checkbox.isChecked()
        self.filter_changed.emit(text, level, use_regex)
