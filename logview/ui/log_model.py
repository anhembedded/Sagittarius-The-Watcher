import re
from typing import List, Optional, Any

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QTimer, Signal
from PySide6.QtGui import QColor, QBrush

from logview.models import LogEntry

# Constants for column indices
COL_BOOKMARK = 0
COL_TIMESTAMP = 1
COL_LEVEL = 2
COL_MESSAGE = 3

class LogModel(QAbstractTableModel):
    """
    Model for managing and displaying log entries in a QTableView.
    # MVC Pattern: Serves as the Model providing data to the View (QTableView).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_logs: List[LogEntry] = []
        self._filtered_logs: List[LogEntry] = []

        self._bookmarks: set[str] = set()

        # Filtering state
        self._filter_text = ""
        self._filter_level = "ALL"
        self._filter_regex = False

        # Animation timer
        self._animation_timer = QTimer(self)
        self._animation_timer.timeout.connect(self._step_animations)
        self._animation_timer.start(50) # 50ms step

        # We'll store a "fade" value for new rows. 255 = fully highlighted, 0 = normal.
        # Dictionary mapping log ID to fade level
        self._new_row_fades = {}

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._filtered_logs)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 4 # Bookmark, Timestamp, Level, Message

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()

        if row >= len(self._filtered_logs):
            return None

        log = self._filtered_logs[row]

        if role == Qt.ItemDataRole.DisplayRole:
            if col == COL_TIMESTAMP:
                return log.timestamp or ""
            elif col == COL_LEVEL:
                return log.level or ""
            elif col == COL_MESSAGE:
                return log.message or log.raw

        elif role == Qt.ItemDataRole.CheckStateRole:
            if col == COL_BOOKMARK:
                return Qt.CheckState.Checked if log.id in self._bookmarks else Qt.CheckState.Unchecked

        elif role == Qt.ItemDataRole.BackgroundRole:
            # Handle animation highlight
            fade = self._new_row_fades.get(log.id, 0)
            if fade > 0:
                # Highlight color: slightly yellow/blue fading out
                return QBrush(QColor(100, 150, 255, fade))

            # Default level colors if not animating
            if log.level:
                lvl = log.level.upper()
                if lvl in ("ERROR", "CRITICAL", "FATAL"):
                    return QBrush(QColor(255, 200, 200))
                elif lvl == "WARNING":
                    return QBrush(QColor(255, 255, 200))

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if section == COL_BOOKMARK:
                return "B" # Bookmark column
            elif section == COL_TIMESTAMP:
                return "Timestamp"
            elif section == COL_LEVEL:
                return "Level"
            elif section == COL_MESSAGE:
                return "Message"
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags

        flags = super().flags(index)
        if index.column() == COL_BOOKMARK:
            flags |= Qt.ItemFlag.ItemIsUserCheckable
        return flags

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole) -> bool:
        if not index.isValid():
            return False

        if index.column() == COL_BOOKMARK and role == Qt.ItemDataRole.CheckStateRole:
            log = self._filtered_logs[index.row()]
            if value == Qt.CheckState.Checked.value:
                self._bookmarks.add(log.id)
            else:
                self._bookmarks.discard(log.id)
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.CheckStateRole])
            return True

        return False

    def add_logs(self, logs: List[LogEntry]):
        """Adds new logs to the model, applying filters and setting up animations."""
        if not logs:
            return

        new_filtered = []
        for log in logs:
            self._all_logs.append(log)
            # Start animation
            if log.is_new:
                self._new_row_fades[log.id] = 100 # start alpha

            if self._matches_filter(log):
                new_filtered.append(log)

        if new_filtered:
            first_new_row = len(self._filtered_logs)
            self.beginInsertRows(QModelIndex(), first_new_row, first_new_row + len(new_filtered) - 1)
            self._filtered_logs.extend(new_filtered)
            self.endInsertRows()

    def clear_logs(self):
        """Clears all logs."""
        self.beginResetModel()
        self._all_logs.clear()
        self._filtered_logs.clear()
        self._bookmarks.clear()
        self._new_row_fades.clear()
        self.endResetModel()

    def set_filter(self, text: str, level: str, use_regex: bool):
        """Updates the filter and re-evaluates all logs."""
        self._filter_text = text
        self._filter_level = level
        self._filter_regex = use_regex

        self._apply_filter()

    def _apply_filter(self):
        self.beginResetModel()
        self._filtered_logs = [log for log in self._all_logs if self._matches_filter(log)]
        self.endResetModel()

    def _matches_filter(self, log: LogEntry) -> bool:
        if self._filter_level != "ALL" and log.level:
            if log.level.upper() != self._filter_level:
                return False

        if self._filter_text:
            text_to_search = log.raw
            if self._filter_regex:
                try:
                    if not re.search(self._filter_text, text_to_search):
                        return False
                except re.error:
                    # Invalid regex, ignore filter or treat as false
                    return False
            else:
                if self._filter_text.lower() not in text_to_search.lower():
                    return False

        return True

    def _step_animations(self):
        """Reduces the fade level of animating rows and requests redraw."""
        keys_to_remove = []
        updated_rows = []

        for log_id, fade in self._new_row_fades.items():
            new_fade = fade - 10
            if new_fade <= 0:
                keys_to_remove.append(log_id)
            else:
                self._new_row_fades[log_id] = new_fade

            # Find the row in filtered_logs to emit dataChanged
            # (In a highly optimized scenario, we might keep an index map, but for 10k logs, a simple scan or updating visible rows only might be better. We'll emit dataChanged for the whole column if we have animations to avoid slow lookups).

        if self._new_row_fades:
            for k in keys_to_remove:
                del self._new_row_fades[k]

            # Emit dataChanged for all visible to avoid O(N) lookup.
            # A more optimal way is to track visible rows, or map log_id -> row.
            # Since animation is short, we just trigger redraw for all.
            # In a real app, mapping log_id -> index in _filtered_logs is faster.
            if len(self._filtered_logs) > 0:
                self.dataChanged.emit(
                    self.index(0, 0),
                    self.index(len(self._filtered_logs) - 1, self.columnCount() - 1),
                    [Qt.ItemDataRole.BackgroundRole]
                )

    def get_all_logs(self) -> List[LogEntry]:
        return self._all_logs
