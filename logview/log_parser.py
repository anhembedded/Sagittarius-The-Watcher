import re
import json
from datetime import datetime
from typing import Optional
from logview.models import LogEntry

TIMESTAMP_FORMATS = [
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
    "%Y/%m/%d %H:%M:%S",
    "%d/%b/%Y:%H:%M:%S",
    "%d/%b/%Y:%H:%M:%S %z",
]


def _try_parse_datetime(ts_str: Optional[str]) -> Optional[datetime]:
    """Attempt to parse a timestamp string into a datetime object."""
    if not ts_str:
        return None
    try:
        return datetime.fromisoformat(ts_str)
    except (ValueError, TypeError):
        pass
    for fmt in TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(ts_str.strip(), fmt)
        except (ValueError, AttributeError):
            continue
    return None


class LogParser:
    """Parses raw log strings into LogEntry objects based on a regex pattern.
    Also handles JSON-formatted lines as a fallback."""

    def __init__(self, pattern: str):
        """Initializes the parser with a specific regex pattern.

        Args:
            pattern (str): The regex pattern containing named groups
                           like 'timestamp', 'level', and 'message'.
        """
        try:
            self.pattern = re.compile(pattern)
        except re.error as e:
            import logging
            logging.warning(f"Invalid regex pattern '{pattern}': {e}. Falling back to raw regex.")
            from PySide6.QtWidgets import QMessageBox
            # To avoid crashing or showing dialogs in non-GUI thread testing contexts,
            # we can attempt to show a message box if a QApplication exists.
            from PySide6.QtWidgets import QApplication
            if QApplication.instance():
                QMessageBox.warning(
                    None,
                    "Invalid Log Format Regex",
                    f"The configured log format regex pattern is invalid:\n{e}\n\n"
                    "Falling back to a raw matching pattern to prevent application crash."
                )
            self.pattern = re.compile(r"^(?P<message>.*)")

    def parse(self, line: str) -> LogEntry:
        """Parses a single log line.

        Args:
            line (str): The raw log string.

        Returns:
            LogEntry: Parsed entry. If not matched, returns entry with raw data and no parsed fields.
        """
        clean_line = line.rstrip('\r\n')
        match = self.pattern.match(clean_line)

        if match:
            group_dict = match.groupdict()
            ts_str = group_dict.get("timestamp")
            return LogEntry(
                raw=clean_line,
                timestamp=ts_str,
                level=group_dict.get("level", "").upper() if group_dict.get("level") else None,
                message=group_dict.get("message", clean_line),
                parsed_dt=_try_parse_datetime(ts_str),
            )

        # JSON fallback (Feature 13 lite: parse common JSON log formats)
        if clean_line.startswith("{"):
            try:
                data = json.loads(clean_line)
                ts_str = (data.get("timestamp") or data.get("time")
                          or data.get("ts") or data.get("datetime"))
                level_raw = (data.get("level") or data.get("lvl")
                             or data.get("severity") or data.get("levelname"))
                msg = (data.get("message") or data.get("msg")
                       or data.get("text") or clean_line)
                return LogEntry(
                    raw=clean_line,
                    timestamp=str(ts_str) if ts_str else None,
                    level=str(level_raw).upper() if level_raw else None,
                    message=str(msg),
                    parsed_dt=_try_parse_datetime(str(ts_str) if ts_str else None),
                )
            except (json.JSONDecodeError, AttributeError):
                pass

        return LogEntry(raw=clean_line, message=clean_line)

    def is_new_entry(self, line: str) -> bool:
        """Returns True if this line begins a new log entry (matches pattern or looks like JSON)."""
        clean_line = line.rstrip('\r\n')
        return bool(self.pattern.match(clean_line)) or clean_line.startswith("{")


class MultiLineBuffer:
    """Wraps a LogParser and groups continuation lines (e.g. stack traces) into
    a single LogEntry.  Any line that does not match the parser's main pattern
    is appended to the previous entry's raw/message fields.
    """

    def __init__(self, parser: LogParser):
        self._parser = parser
        self._pending: Optional[LogEntry] = None

    def feed(self, line: str) -> Optional[LogEntry]:
        """Process one raw line.

        Returns a completed LogEntry when a new entry starts (flushing the
        previous one), or None if the line was appended as a continuation.
        """
        if self._parser.is_new_entry(line):
            prev = self._pending
            self._pending = self._parser.parse(line)
            return prev
        else:
            clean = line.rstrip('\r\n')
            if self._pending is not None:
                self._pending.raw += "\n" + clean
                self._pending.message += "\n" + clean
            else:
                # No pending entry yet — treat as standalone
                self._pending = self._parser.parse(line)
            return None

    def flush(self) -> Optional[LogEntry]:
        """Flush and return any remaining buffered entry."""
        prev = self._pending
        self._pending = None
        return prev
