import re
from datetime import datetime, timezone
from typing import List, Optional, Any, Dict

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QTimer, Signal
from PySide6.QtGui import QColor, QBrush

from logview.models import LogEntry
from logview.controllers.filter_engine import LogFilterEngine

# Constants for column indices
COL_BOOKMARK = 0
COL_TIMESTAMP = 1
COL_LEVEL = 2
COL_MESSAGE = 3


def _parse_color(hex_str: str) -> Optional[QColor]:
    """Returns a QColor from a hex string, or None if empty/invalid."""
    if not hex_str or not hex_str.strip():
        return None
    color = QColor(hex_str.strip())
    return color if color.isValid() else None


def _format_relative(dt: datetime) -> str:
    """Returns a human-readable relative time string like '2s ago'."""
    try:
        now = datetime.now()
        delta = now - dt.replace(tzinfo=None) if dt.tzinfo else now - dt
        secs = int(delta.total_seconds())
        if secs < 0:
            return "in the future"
        if secs < 60:
            return f"{secs}s ago"
        if secs < 3600:
            return f"{secs // 60}m ago"
        if secs < 86400:
            return f"{secs // 3600}h ago"
        return f"{secs // 86400}d ago"
    except Exception:
        return ""


class LogModel(QAbstractTableModel):
    """Model for managing and displaying log entries in a QTableView.
    # MVC Pattern: Serves as the Model providing data to the View (QTableView).
    """

    # Emitted whenever level counts change (add / clear)
    counts_changed = Signal(dict)  # Feature 6

    def __init__(self, parent=None, color_config: Dict = None):
        super().__init__(parent)
        self._all_logs: List[LogEntry] = []

        # Build level -> (bg QColor | None, fg QColor | None) lookup
        self._level_colors: Dict[str, tuple] = {}
        if color_config:
            for level, colors in color_config.items():
                bg = _parse_color(colors.get("bg", ""))
                fg = _parse_color(colors.get("fg", ""))
                self._level_colors[level.upper()] = (bg, fg)
        self._filtered_logs: List[LogEntry] = []

        self._bookmarks: set[str] = set()

        # --- Filtering state ---
        self._filter_engine = LogFilterEngine()

        # --- Sorting state (Feature 8) ---
        self._sort_column: int = -1
        self._sort_order: Qt.SortOrder = Qt.SortOrder.AscendingOrder

        # --- Level counters (Feature 6) ---
        self._level_counts: Dict[str, int] = {}

        # --- Relative time (Feature 14) ---
        self._show_relative_time: bool = False
        self._relative_timer = QTimer(self)
        self._relative_timer.timeout.connect(self._refresh_timestamps)
        # Timer is started/stopped in toggle_relative_time()

        # --- Highlight / find term (Feature 3) ---
        self._highlight_term: str = ""
        self._highlight_regex: bool = False

        # --- Find state ---
        self._find_match_rows: List[int] = []   # indices into _filtered_logs
        self._find_current_idx: int = -1

        # Animation timer
        self._animation_timer = QTimer(self)
        self._animation_timer.timeout.connect(self._step_animations)
        self._animation_timer.start(50)  # 50ms step

        # We'll store a "fade" value for new rows. 255 = fully highlighted, 0 = normal.
        self._new_row_fades = {}

    # ------------------------------------------------------------------
    # QAbstractTableModel interface
    # ------------------------------------------------------------------

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._filtered_logs)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 4  # Bookmark, Timestamp, Level, Message

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
                if self._show_relative_time and log.parsed_dt:
                    return _format_relative(log.parsed_dt)
                return log.timestamp or ""
            elif col == COL_LEVEL:
                return log.level or ""
            elif col == COL_MESSAGE:
                # Show only first line in the table cell; full raw shown in detail panel
                return (log.message or log.raw).split("\n")[0]

        elif role == Qt.ItemDataRole.CheckStateRole:
            if col == COL_BOOKMARK:
                return Qt.CheckState.Checked if log.id in self._bookmarks else Qt.CheckState.Unchecked

        elif role == Qt.ItemDataRole.BackgroundRole:
            # Animation highlight takes priority
            fade = self._new_row_fades.get(log.id, 0)
            if fade > 0:
                return QBrush(QColor(100, 150, 255, fade))

            # Configured level bg color
            if log.level:
                lvl = log.level.upper()
                colors = self._level_colors.get(lvl)
                if colors and colors[0] is not None:
                    return QBrush(colors[0])

        elif role == Qt.ItemDataRole.ForegroundRole:
            if log.level:
                lvl = log.level.upper()
                colors = self._level_colors.get(lvl)
                if colors and colors[1] is not None:
                    return QBrush(colors[1])

        elif role == Qt.ItemDataRole.ToolTipRole:
            # Show full raw text in tooltip (useful for multi-line logs)
            if col == COL_MESSAGE:
                return log.raw

        return None

    def headerData(self, section: int, orientation: Qt.Orientation,
                   role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if section == COL_BOOKMARK:
                return "B"
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

    def setData(self, index: QModelIndex, value: Any,
                role: int = Qt.ItemDataRole.EditRole) -> bool:
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

    # ------------------------------------------------------------------
    # Feature 8: Column sorting
    # ------------------------------------------------------------------

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder):
        """Sort the filtered logs by the given column."""
        self._sort_column = column
        self._sort_order = order
        self._apply_sort()

    def _apply_sort(self):
        if self._sort_column < 0:
            return

        reverse = self._sort_order == Qt.SortOrder.DescendingOrder

        def key_fn(log: LogEntry):
            if self._sort_column == COL_TIMESTAMP:
                return log.parsed_dt or datetime.min
            elif self._sort_column == COL_LEVEL:
                return log.level or ""
            elif self._sort_column == COL_MESSAGE:
                return (log.message or log.raw).lower()
            return ""

        self.layoutAboutToBeChanged.emit()
        try:
            self._filtered_logs.sort(key=key_fn, reverse=reverse)
        except Exception:
            pass
        self.layoutChanged.emit()

    # ------------------------------------------------------------------
    # Log management
    # ------------------------------------------------------------------

    def add_logs(self, logs: List[LogEntry]):
        """Adds new logs to the model, applying filters and setting up animations."""
        if not logs:
            return

        new_filtered = []
        for log in logs:
            self._all_logs.append(log)

            # Update level counters (Feature 6)
            if log.level:
                lvl = log.level.upper()
                self._level_counts[lvl] = self._level_counts.get(lvl, 0) + 1

            # Start animation
            if log.is_new:
                self._new_row_fades[log.id] = 100

            if self._filter_engine.matches(log):
                new_filtered.append(log)

        if new_filtered:
            if self._sort_column >= 0:
                # Sorted mode: full re-sort
                first_new_row = len(self._filtered_logs)
                self.beginInsertRows(QModelIndex(), first_new_row,
                                     first_new_row + len(new_filtered) - 1)
                self._filtered_logs.extend(new_filtered)
                self.endInsertRows()
                self._apply_sort()
            else:
                first_new_row = len(self._filtered_logs)
                self.beginInsertRows(QModelIndex(), first_new_row,
                                     first_new_row + len(new_filtered) - 1)
                self._filtered_logs.extend(new_filtered)
                self.endInsertRows()

        self.counts_changed.emit(dict(self._level_counts))

    def get_level_counts(self) -> dict:
        return self._level_counts.copy()

    def clear_logs(self):
        """Clears all logs."""
        self.beginResetModel()
        self._all_logs.clear()
        self._filtered_logs.clear()
        self._bookmarks.clear()
        self._new_row_fades.clear()
        self._level_counts.clear()
        self._find_match_rows.clear()
        self._find_current_idx = -1
        self.endResetModel()
        self.counts_changed.emit({})

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def set_filter(self, text: str, level: str, use_regex: bool):
        """Updates the text/level filter and re-evaluates all logs."""
        self._filter_engine.set_text_filter(text, use_regex)
        self._filter_engine.set_level_filter(level)
        self._apply_filter()

    def set_time_range(self, from_dt: Optional[datetime], to_dt: Optional[datetime]):
        """Feature 7: Set a datetime range filter."""
        self._filter_engine.set_time_range(from_dt, to_dt)
        self._apply_filter()

    def _apply_filter(self):
        self.beginResetModel()
        self._filtered_logs = [log for log in self._all_logs if self._filter_engine.matches(log)]
        self._find_match_rows.clear()
        self._find_current_idx = -1
        self.endResetModel()

        if self._sort_column >= 0:
            self._apply_sort()

        if self._highlight_term:
            self._rebuild_find_matches()

    # ------------------------------------------------------------------
    # Feature 3: Find / highlight
    # ------------------------------------------------------------------

    def set_highlight_term(self, term: str, use_regex: bool = False):
        """Set the find-bar search term. Triggers a search over filtered logs."""
        self._highlight_term = term
        self._highlight_regex = use_regex
        self._rebuild_find_matches()

        # Refresh display
        if self._filtered_logs:
            self.dataChanged.emit(
                self.index(0, COL_MESSAGE),
                self.index(len(self._filtered_logs) - 1, COL_MESSAGE),
            )

    def _rebuild_find_matches(self):
        """Rebuild the list of row indices that contain the highlight term."""
        self._find_match_rows.clear()
        self._find_current_idx = -1
        if not self._highlight_term:
            return

        if self._highlight_regex:
            try:
                pattern = re.compile(self._highlight_term, re.IGNORECASE)
                for i, log in enumerate(self._filtered_logs):
                    if pattern.search(log.raw):
                        self._find_match_rows.append(i)
            except re.error:
                # Invalid regex, ignore
                pass
        else:
            term_lower = self._highlight_term.lower()
            for i, log in enumerate(self._filtered_logs):
                if term_lower in log.raw_lower:
                    self._find_match_rows.append(i)

    def find_navigate(self, direction: int) -> int:
        """Move to the next/previous match row.

        Args:
            direction: +1 for next, -1 for previous.

        Returns:
            The row index of the new current match, or -1 if no matches.
        """
        if not self._find_match_rows:
            return -1
        n = len(self._find_match_rows)
        if self._find_current_idx < 0:
            self._find_current_idx = 0 if direction > 0 else n - 1
        else:
            self._find_current_idx = (self._find_current_idx + direction) % n
        return self._find_match_rows[self._find_current_idx]

    def find_match_count(self) -> int:
        return len(self._find_match_rows)

    def find_current_match(self) -> int:
        return self._find_current_idx + 1 if self._find_current_idx >= 0 else 0

    # ------------------------------------------------------------------
    # Feature 14: Relative timestamps
    # ------------------------------------------------------------------

    def toggle_relative_time(self) -> bool:
        """Toggle relative timestamp display. Returns the new state."""
        self._show_relative_time = not self._show_relative_time
        if self._show_relative_time:
            self._relative_timer.start(10_000)  # refresh every 10s
        else:
            self._relative_timer.stop()
        self._refresh_timestamps()
        return self._show_relative_time

    def _refresh_timestamps(self):
        if self._filtered_logs:
            self.dataChanged.emit(
                self.index(0, COL_TIMESTAMP),
                self.index(len(self._filtered_logs) - 1, COL_TIMESTAMP),
                [Qt.ItemDataRole.DisplayRole],
            )

    # ------------------------------------------------------------------
    # Feature 6: Colors (live update from settings)
    # ------------------------------------------------------------------

    def update_colors(self, color_config: Dict):
        """Live-updates the level color mapping and redraws the table."""
        self._level_colors = {}
        if color_config:
            for level, colors in color_config.items():
                bg = _parse_color(colors.get("bg", ""))
                fg = _parse_color(colors.get("fg", ""))
                self._level_colors[level.upper()] = (bg, fg)

        if self._filtered_logs:
            self.dataChanged.emit(
                self.index(0, 0),
                self.index(len(self._filtered_logs) - 1, self.columnCount() - 1),
                [Qt.ItemDataRole.BackgroundRole, Qt.ItemDataRole.ForegroundRole],
            )

    # ------------------------------------------------------------------
    # Animation
    # ------------------------------------------------------------------

    def _step_animations(self):
        """Reduces the fade level of animating rows and requests redraw."""
        keys_to_remove = []

        for log_id, fade in self._new_row_fades.items():
            new_fade = fade - 10
            if new_fade <= 0:
                keys_to_remove.append(log_id)
            else:
                self._new_row_fades[log_id] = new_fade

        if self._new_row_fades:
            for k in keys_to_remove:
                del self._new_row_fades[k]

            if len(self._filtered_logs) > 0:
                self.dataChanged.emit(
                    self.index(0, 0),
                    self.index(len(self._filtered_logs) - 1, self.columnCount() - 1),
                    [Qt.ItemDataRole.BackgroundRole]
                )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def get_all_logs(self) -> List[LogEntry]:
        return self._all_logs

    def get_filtered_count(self) -> int:
        return len(self._filtered_logs)

    def get_entry_at_row(self, row: int) -> Optional[LogEntry]:
        if 0 <= row < len(self._filtered_logs):
            return self._filtered_logs[row]
        return None
