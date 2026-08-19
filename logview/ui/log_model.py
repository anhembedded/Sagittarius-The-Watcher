import re
from datetime import datetime
from typing import Any

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QSortFilterProxyModel,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import QBrush, QColor
from PySide6.QtQml import QmlElement

QML_IMPORT_NAME = "LogView.Models"
QML_IMPORT_MAJOR_VERSION = 1

from logview.controllers.filter_engine import LogFilterEngine
from logview.models import LogEntry

# Constants for column indices
COL_BOOKMARK = 0
COL_INDEX = 1
COL_TIMESTAMP = 2
COL_LEVEL = 3
COL_MODULE = 4
COL_SUBMODULE = 5
COL_MESSAGE = 6


def _parse_color(hex_str: str) -> QColor | None:
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


@QmlElement
class LogModel(QAbstractTableModel):
    """Model for managing and storing log entries.
    # MVC Pattern: Serves as the pure source Model.
    """

    RoleBookmark = Qt.UserRole + 1
    RoleIndex = Qt.UserRole + 2
    RoleTime = Qt.UserRole + 3
    RoleLevel = Qt.UserRole + 4
    RoleModule = Qt.UserRole + 5
    RoleSubmodule = Qt.UserRole + 6
    RoleMessage = Qt.UserRole + 7
    RoleBgColor = Qt.UserRole + 8
    RoleFgColor = Qt.UserRole + 9

    # Emitted whenever level counts change (add / clear)
    counts_changed = Signal(dict)

    def __init__(self, parent=None, max_lines: int = 10000, color_config: dict = None):
        super().__init__(parent)
        self._all_logs: list[LogEntry] = []
        self._max_lines = max_lines

        # Build level -> (bg QColor | None, fg QColor | None) lookup
        self._level_colors: dict[str, tuple] = {}
        if color_config:
            for level, colors in color_config.items():
                bg = _parse_color(colors.get("bg", ""))
                fg = _parse_color(colors.get("fg", ""))
                self._level_colors[level.upper()] = (bg, fg)

        self._bookmarks: set[int] = set()
        self._level_counts: dict[str, int] = {}

        # --- Relative time (Feature 14) ---
        self._show_relative_time: bool = False
        self._relative_timer = QTimer(self)
        self._relative_timer.timeout.connect(self._refresh_timestamps)

        # Animation timer
        self._animation_timer = QTimer(self)
        self._animation_timer.timeout.connect(self._step_animations)
        self._animation_timer.start(50)

        # We'll store a "fade" value for new rows. 255 = fully highlighted, 0 = normal.
        self._new_row_fades = {}

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._all_logs)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 7  # Bookmark, Index, Timestamp, Level, Module, Submodule, Message

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()

        if row >= len(self._all_logs):
            return None

        log = self._all_logs[row]

        if role == Qt.ItemDataRole.DisplayRole:
            if col == COL_INDEX:
                return log.index or ""
            elif col == COL_TIMESTAMP:
                if self._show_relative_time and log.parsed_dt:
                    return _format_relative(log.parsed_dt)
                return log.timestamp or ""
            elif col == COL_LEVEL:
                return log.level or ""
            elif col == COL_MODULE:
                return log.module or ""
            elif col == COL_SUBMODULE:
                return log.submodule or ""
            elif col == COL_MESSAGE:
                return (log.message or log.raw).split("\n")[0]

        elif role == Qt.ItemDataRole.CheckStateRole:
            if col == COL_BOOKMARK:
                return Qt.CheckState.Checked if log.id in self._bookmarks else Qt.CheckState.Unchecked

        elif role == Qt.ItemDataRole.BackgroundRole:
            fade = self._new_row_fades.get(log.id, 0)
            if fade > 0:
                return QBrush(QColor(100, 150, 255, fade))

            if log.level:
                lvl = log.level_upper
                colors = self._level_colors.get(lvl)
                if colors and colors[0] is not None:
                    return QBrush(colors[0])

        elif role == Qt.ItemDataRole.ForegroundRole:
            if log.level:
                lvl = log.level_upper
                colors = self._level_colors.get(lvl)
                if colors and colors[1] is not None:
                    return QBrush(colors[1])

        elif role == Qt.ItemDataRole.ToolTipRole:
            if col == COL_MESSAGE:
                return log.raw

        # --- QML Custom Roles ---
        elif role == self.RoleBookmark:
            return log.id in self._bookmarks
        elif role == self.RoleIndex:
            return log.index or ""
        elif role == self.RoleTime:
            if self._show_relative_time and log.parsed_dt:
                return _format_relative(log.parsed_dt)
            return log.timestamp or ""
        elif role == self.RoleLevel:
            return log.level or ""
        elif role == self.RoleModule:
            return log.module or ""
        elif role == self.RoleSubmodule:
            return log.submodule or ""
        elif role == self.RoleMessage:
            return (log.message or log.raw).split("\n")[0]
        elif role == self.RoleBgColor:
            fade = self._new_row_fades.get(log.id, 0)
            if fade > 0:
                return QColor(100, 150, 255, fade).name()
            if log.level:
                lvl = log.level_upper
                colors = self._level_colors.get(lvl)
                if colors and colors[0] is not None:
                    return colors[0].name()
            return "transparent"
        elif role == self.RoleFgColor:
            if log.level:
                lvl = log.level_upper
                colors = self._level_colors.get(lvl)
                if colors and colors[1] is not None:
                    return colors[1].name()
            return "#ffffff"

        return None

    def roleNames(self):
        roles = super().roleNames()
        roles[self.RoleBookmark] = b"bookmark"
        roles[self.RoleIndex] = b"index"
        roles[self.RoleTime] = b"time"
        roles[self.RoleLevel] = b"level"
        roles[self.RoleModule] = b"module"
        roles[self.RoleSubmodule] = b"submodule"
        roles[self.RoleMessage] = b"message"
        roles[self.RoleBgColor] = b"bgColor"
        roles[self.RoleFgColor] = b"fgColor"
        return roles

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if section == COL_BOOKMARK:
                return "B"
            elif section == COL_INDEX:
                return "Index"
            elif section == COL_TIMESTAMP:
                return "Timestamp"
            elif section == COL_LEVEL:
                return "Level"
            elif section == COL_MODULE:
                return "Module"
            elif section == COL_SUBMODULE:
                return "Submodule"
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
            log = self._all_logs[index.row()]
            if value == Qt.CheckState.Checked.value:
                self._bookmarks.add(log.id)
            else:
                self._bookmarks.discard(log.id)
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.CheckStateRole])
            return True

        return False

    def toggle_bookmark(self, row: int):
        if 0 <= row < len(self._all_logs):
            log = self._all_logs[row]
            if log.id in self._bookmarks:
                self._bookmarks.discard(log.id)
            else:
                self._bookmarks.add(log.id)
            idx = self.index(row, COL_BOOKMARK)
            self.dataChanged.emit(idx, idx, [Qt.ItemDataRole.CheckStateRole])

    def add_logs(self, logs: list[LogEntry]):
        """Adds new logs to the model and updates counters."""
        if not logs:
            return

        first_new_row = len(self._all_logs)
        self.beginInsertRows(QModelIndex(), first_new_row, first_new_row + len(logs) - 1)
        for log in logs:
            self._all_logs.append(log)

            if log.level:
                lvl = log.level_upper
                self._level_counts[lvl] = self._level_counts.get(lvl, 0) + 1

            if log.is_new:
                self._new_row_fades[log.id] = 100
        self.endInsertRows()

        # Enforce max_lines bounded memory limit
        overflow = len(self._all_logs) - self._max_lines
        if overflow > 0:
            self.beginRemoveRows(QModelIndex(), 0, overflow - 1)
            removed_logs = self._all_logs[:overflow]
            self._all_logs = self._all_logs[overflow:]
            self.endRemoveRows()

            for log in removed_logs:
                if log.level:
                    lvl = log.level_upper
                    if lvl in self._level_counts:
                        self._level_counts[lvl] = max(0, self._level_counts[lvl] - 1)
                        if self._level_counts[lvl] == 0:
                            del self._level_counts[lvl]

            removed_ids = {log.id for log in removed_logs}
            self._bookmarks.difference_update(removed_ids)
            for rid in removed_ids:
                self._new_row_fades.pop(rid, None)

        self.counts_changed.emit(dict(self._level_counts))

    def get_level_counts(self) -> dict:
        return self._level_counts.copy()

    def clear_logs(self):
        """Clears all logs."""
        self.beginResetModel()
        self._all_logs.clear()
        self._bookmarks.clear()
        self._new_row_fades.clear()
        self._level_counts.clear()
        self.endResetModel()
        self.counts_changed.emit({})

    def toggle_relative_time(self) -> bool:
        """Toggle relative timestamp display. Returns the new state."""
        self._show_relative_time = not self._show_relative_time
        if self._show_relative_time:
            self._relative_timer.start(10_000)
        else:
            self._relative_timer.stop()
        self._refresh_timestamps()
        return self._show_relative_time

    def _refresh_timestamps(self):
        if self._all_logs:
            self.dataChanged.emit(
                self.index(0, COL_TIMESTAMP),
                self.index(len(self._all_logs) - 1, COL_TIMESTAMP),
                [Qt.ItemDataRole.DisplayRole],
            )

    def update_colors(self, color_config: dict):
        """Live-updates the level color mapping and redraws the table."""
        self._level_colors = {}
        if color_config:
            for level, colors in color_config.items():
                bg = _parse_color(colors.get("bg", ""))
                fg = _parse_color(colors.get("fg", ""))
                self._level_colors[level.upper()] = (bg, fg)

        if self._all_logs:
            self.dataChanged.emit(
                self.index(0, 0),
                self.index(len(self._all_logs) - 1, self.columnCount() - 1),
                [Qt.ItemDataRole.BackgroundRole, Qt.ItemDataRole.ForegroundRole],
            )

    def _step_animations(self):
        """Reduces the fade level of animating rows and requests redraw."""
        keys_to_remove = []

        for log_id, fade in self._new_row_fades.items():
            new_fade = fade - 10
            if new_fade <= 0:
                keys_to_remove.append(log_id)
            else:
                self._new_row_fades[log_id] = new_fade

        had_fades = bool(self._new_row_fades)
        for k in keys_to_remove:
            del self._new_row_fades[k]

        if (had_fades or self._new_row_fades) and len(self._all_logs) > 0:
            self.dataChanged.emit(
                self.index(0, 0),
                self.index(len(self._all_logs) - 1, self.columnCount() - 1),
                [Qt.ItemDataRole.BackgroundRole],
            )

    def get_all_logs(self) -> list[LogEntry]:
        return self._all_logs

    def get_entry_at_row(self, row: int) -> LogEntry | None:
        if 0 <= row < len(self._all_logs):
            return self._all_logs[row]
        return None


@QmlElement
class LogFilterProxyModel(QSortFilterProxyModel):
    """Proxy model for high-performance sorting and filtering on the C++ native side.
    # MVC Pattern: Serves as the Controller/Proxy between Model and View.
    """

    counts_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._filter_engine = LogFilterEngine()
        self._bookmarks_only = False

        self._highlight_term: str = ""
        self._highlight_regex: bool = False
        self._find_match_rows: list[int] = []
        self._find_current_idx: int = -1

        self._warning_rows: list[int] = []
        self._error_rows: list[int] = []

        # Enable dynamic filtering update as the source model changes
        self.setDynamicSortFilter(True)

        self.layoutChanged.connect(self._rebuild_heatmap_indices)
        self.rowsInserted.connect(self._rebuild_heatmap_indices)
        self.rowsRemoved.connect(self._rebuild_heatmap_indices)
        self.modelReset.connect(self._rebuild_heatmap_indices)

    def _rebuild_heatmap_indices(self):
        self._warning_rows.clear()
        self._error_rows.clear()
        source = self.sourceModel()
        if not source:
            return
        n = self.rowCount()
        for i in range(n):
            source_idx = self.mapToSource(self.index(i, 0))
            if source_idx.row() < len(source._all_logs):
                log = source._all_logs[source_idx.row()]
                if log.level:
                    lvl = log.level_upper
                    if lvl in ("ERROR", "CRITICAL"):
                        self._error_rows.append(i)
                    elif lvl == "WARNING":
                        self._warning_rows.append(i)

    def setSourceModel(self, model):
        super().setSourceModel(model)
        if model:
            model.counts_changed.connect(self.counts_changed.emit)
            self._rebuild_heatmap_indices()

    def add_logs(self, logs: list[LogEntry]):
        source = self.sourceModel()
        if source:
            source.add_logs(logs)

    def clear_logs(self):
        source = self.sourceModel()
        if source:
            source.clear_logs()

    def get_all_logs(self) -> list[LogEntry]:
        source = self.sourceModel()
        if source:
            return source.get_all_logs()
        return []

    @property
    def _all_logs(self) -> list[LogEntry]:
        source = self.sourceModel()
        return source._all_logs if source else []

    @property
    def _filtered_logs(self) -> list[LogEntry]:
        source = self.sourceModel()
        if not source:
            return []
        return [source._all_logs[self.mapToSource(self.index(i, 0)).row()] for i in range(self.rowCount())]

    @property
    def _show_relative_time(self) -> bool:
        source = self.sourceModel()
        return source._show_relative_time if source else False

    def toggle_relative_time(self) -> bool:
        source = self.sourceModel()
        if source:
            return source.toggle_relative_time()
        return False

    def update_colors(self, color_config: dict):
        source = self.sourceModel()
        if source:
            source.update_colors(color_config)

    def get_level_counts(self) -> dict:
        source = self.sourceModel()
        if source:
            return source.get_level_counts()
        return {}

    def set_filter(self, text: str, levels: list[str], use_regex: bool, bookmarks_only: bool = False):
        """Updates filters and invalidates to trigger refiltering."""
        self._filter_engine.set_text_filter(text, use_regex)
        self._filter_engine.set_level_filter(levels)
        self._bookmarks_only = bookmarks_only
        self.invalidateFilter()
        if self._highlight_term:
            self._rebuild_find_matches()

    def set_time_range(self, from_dt: datetime | None, to_dt: datetime | None):
        """Sets a datetime range filter and invalidates filter."""
        self._filter_engine.set_time_range(from_dt, to_dt)
        self.invalidateFilter()
        if self._highlight_term:
            self._rebuild_find_matches()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        source = self.sourceModel()
        if not source:
            return True
        if source_row >= len(source._all_logs):
            return False
        log = source._all_logs[source_row]

        if self._bookmarks_only and log.id not in source._bookmarks:
            return False

        return self._filter_engine.matches(log)

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        source = self.sourceModel()
        if not source:
            return super().lessThan(left, right)

        if left.row() >= len(source._all_logs) or right.row() >= len(source._all_logs):
            return False
        log_left = source._all_logs[left.row()]
        log_right = source._all_logs[right.row()]

        col = left.column()
        if col == COL_TIMESTAMP:
            val_l = log_left.parsed_dt or datetime.min
            val_r = log_right.parsed_dt or datetime.min
            return val_l < val_r
        elif col == COL_LEVEL:
            val_l = log_left.level or ""
            val_r = log_right.level or ""
            return val_l < val_r
        elif col == COL_MESSAGE:
            val_l = log_left.message_lower
            val_r = log_right.message_lower
            return val_l < val_r
        elif col == COL_INDEX:
            try:
                val_l = int(log_left.index or 0)
                val_r = int(log_right.index or 0)
            except ValueError:
                val_l = log_left.index or ""
                val_r = log_right.index or ""
            return val_l < val_r
        elif col == COL_MODULE:
            val_l = log_left.module_lower
            val_r = log_right.module_lower
            return val_l < val_r
        elif col == COL_SUBMODULE:
            val_l = log_left.submodule_lower
            val_r = log_right.submodule_lower
            return val_l < val_r
        return super().lessThan(left, right)

    def toggle_bookmark(self, row: int):
        source = self.sourceModel()
        if not source or not (0 <= row < self.rowCount()):
            return
        source_idx = self.mapToSource(self.index(row, 0))
        source.toggle_bookmark(source_idx.row())

    def get_entry_at_row(self, row: int) -> LogEntry | None:
        source = self.sourceModel()
        if not source or not (0 <= row < self.rowCount()):
            return None
        source_idx = self.mapToSource(self.index(row, 0))
        return source.get_entry_at_row(source_idx.row())

    def set_highlight_term(self, term: str, use_regex: bool = False):
        """Set search term to highlight."""
        self._highlight_term = term
        self._highlight_regex = use_regex
        self._rebuild_find_matches()

        # Trigger message column display refresh
        if self.rowCount() > 0:
            self.dataChanged.emit(
                self.index(0, COL_MESSAGE), self.index(self.rowCount() - 1, COL_MESSAGE), [Qt.ItemDataRole.DisplayRole]
            )

    def _rebuild_find_matches(self):
        """Rebuild rows matching search highlights among visible filtered rows."""
        self._find_match_rows.clear()
        self._find_current_idx = -1
        if not self._highlight_term:
            return

        source = self.sourceModel()
        if not source:
            return

        n = self.rowCount()
        if self._highlight_regex:
            try:
                pattern = re.compile(self._highlight_term, re.IGNORECASE)
                for i in range(n):
                    source_idx = self.mapToSource(self.index(i, 0))
                    log = source._all_logs[source_idx.row()]
                    if pattern.search(log.raw):
                        self._find_match_rows.append(i)
            except re.error:
                pass
        else:
            term_lower = self._highlight_term.lower()
            for i in range(n):
                source_idx = self.mapToSource(self.index(i, 0))
                log = source._all_logs[source_idx.row()]
                if term_lower in log.raw_lower:
                    self._find_match_rows.append(i)

    def find_navigate(self, direction: int) -> int:
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

    def get_bookmark_row(self, current_row: int, direction: int) -> int:
        source = self.sourceModel()
        if not source or not source._bookmarks:
            return -1
        n = self.rowCount()
        if n == 0:
            return -1
        row = current_row
        for _ in range(n):
            row = (row + direction) % n
            source_idx = self.mapToSource(self.index(row, 0))
            log = source._all_logs[source_idx.row()]
            if log.id in source._bookmarks:
                return row
        return -1
