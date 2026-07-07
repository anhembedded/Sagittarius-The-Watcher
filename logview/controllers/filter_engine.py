import re
from typing import Optional
from datetime import datetime
from logview.models import LogEntry

class LogFilterEngine:
    """Engine responsible for applying filters to log entries."""

    def __init__(self):
        self._filter_text = ""
        self._filter_level = "ALL"
        self._filter_regex = False
        self._filter_from_dt: Optional[datetime] = None
        self._filter_to_dt: Optional[datetime] = None

    def set_text_filter(self, text: str, regex: bool):
        self._filter_text = text
        self._filter_regex = regex

    def set_level_filter(self, level: str):
        self._filter_level = level

    def set_time_range(self, from_dt: Optional[datetime], to_dt: Optional[datetime]):
        self._filter_from_dt = from_dt
        self._filter_to_dt = to_dt

    def matches(self, log: LogEntry) -> bool:
        # Level filter
        if self._filter_level != "ALL":
            if log.level is None:
                return False
            if log.level.upper() != self._filter_level:
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
        if self._filter_text:
            text_to_search = log.raw
            if self._filter_regex:
                try:
                    if not re.search(self._filter_text, text_to_search):
                        return False
                except re.error:
                    return False
            else:
                if self._filter_text.lower() not in text_to_search.lower():
                    return False

        return True
