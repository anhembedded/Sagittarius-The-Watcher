import re
from datetime import datetime

from logview.models import LogEntry


class LogFilterEngine:
    """Engine responsible for applying filters to log entries."""

    def __init__(self):
        self._filter_text = ""
        self._filter_text_lower = ""
        self._filter_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        self._filter_levels_set = set(self._filter_levels)
        self._filter_regex = False
        self._compiled_regex = None
        self._filter_from_dt: datetime | None = None
        self._filter_to_dt: datetime | None = None

    def set_text_filter(self, text: str, regex: bool):
        self._filter_text = text
        self._filter_regex = regex
        self._compiled_regex = None
        if self._filter_regex and self._filter_text:
            try:
                self._compiled_regex = re.compile(self._filter_text)
            except re.error:
                self._compiled_regex = None
        elif not self._filter_regex and self._filter_text:
            self._filter_text_lower = self._filter_text.lower()
        else:
            self._filter_text_lower = ""

    def set_level_filter(self, levels: list[str]):
        self._filter_levels = levels
        self._filter_levels_set = set(levels)

    def set_time_range(self, from_dt: datetime | None, to_dt: datetime | None):
        self._filter_from_dt = from_dt
        self._filter_to_dt = to_dt

    def matches(self, log: LogEntry) -> bool:
        # Level filter
        # Performance optimization: use O(1) set lookup instead of O(n) list lookup
        if log.level is not None:
            if log.level.upper() not in self._filter_levels_set:
                return False

        # Time range filter (Feature 7)
        if self._filter_from_dt or self._filter_to_dt:
            if log.parsed_dt is None:
                return False  # Can't filter entries without parsed datetime
            dt = log.parsed_dt.replace(tzinfo=None) if log.parsed_dt.tzinfo else log.parsed_dt
            if self._filter_from_dt and dt < self._filter_from_dt:
                return False
            if self._filter_to_dt and dt > self._filter_to_dt:
                return False

        # Text filter
        # Performance optimization: pre-calculate lowercase filter text in set_text_filter
        # and use the lazily cached log.raw_lower property to avoid repeated lower() calls
        if self._filter_text:
            if self._filter_regex:
                if self._compiled_regex is None:
                    return False
                if not self._compiled_regex.search(log.raw):
                    return False
            else:
                if self._filter_text_lower not in log.raw_lower:
                    return False

        return True
