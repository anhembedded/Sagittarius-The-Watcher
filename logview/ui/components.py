from PySide6.QtWidgets import (QWidget, QHBoxLayout, QLineEdit, QComboBox,
                                 QCheckBox, QLabel, QDateTimeEdit, QFrame)
from PySide6.QtCore import Signal, QDateTime, Qt


class FilterPanel(QWidget):
    """Panel containing text/level filter controls."""

    filter_changed = Signal(str, str, bool)  # text, level, regex

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter logs...")
        self.search_input.setClearButtonEnabled(True)

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


class TimeRangeWidget(QWidget):
    """Widget for filtering logs by a datetime range (Feature 7).

    Signals:
        range_changed(from_dt, to_dt): Emitted when the range changes.
            Both values are Python datetime objects, or None if the range
            is disabled (checkbox unchecked).
    """

    range_changed = Signal(object, object)  # from_dt | None, to_dt | None

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(4)

        self._enable_cb = QCheckBox("Time range:")
        self._enable_cb.stateChanged.connect(self._on_changed)
        layout.addWidget(self._enable_cb)

        now = QDateTime.currentDateTime()

        self._from_dt = QDateTimeEdit(now.addSecs(-3600))
        self._from_dt.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self._from_dt.setEnabled(False)
        self._from_dt.setCalendarPopup(True)
        self._from_dt.dateTimeChanged.connect(self._on_changed)
        layout.addWidget(self._from_dt)

        layout.addWidget(QLabel("–"))

        self._to_dt = QDateTimeEdit(now)
        self._to_dt.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self._to_dt.setEnabled(False)
        self._to_dt.setCalendarPopup(True)
        self._to_dt.dateTimeChanged.connect(self._on_changed)
        layout.addWidget(self._to_dt)

        layout.addStretch()

    def _on_changed(self):
        enabled = self._enable_cb.isChecked()
        self._from_dt.setEnabled(enabled)
        self._to_dt.setEnabled(enabled)

        if enabled:
            from_dt = self._from_dt.dateTime().toPython()
            to_dt = self._to_dt.dateTime().toPython()
        else:
            from_dt = None
            to_dt = None

        self.range_changed.emit(from_dt, to_dt)
