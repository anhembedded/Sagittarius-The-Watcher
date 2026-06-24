import re
from logview.models import LogEntry

class LogParser:
    """Parses raw log strings into LogEntry objects based on a regex pattern."""

    def __init__(self, pattern: str):
        """Initializes the parser with a specific regex pattern.

        Args:
            pattern (str): The regex pattern containing named groups
                           like 'timestamp', 'level', and 'message'.
        """
        self.pattern = re.compile(pattern)

    def parse(self, line: str) -> LogEntry:
        """Parses a single log line.

        Args:
            line (str): The raw log string.

        Returns:
            LogEntry: Parsed entry. If not matched, returns entry with raw data and no parsed fields.
        """
        # Strip trailing newline if any, but keep original for 'raw' if needed. We assume we strip it.
        clean_line = line.rstrip('\r\n')
        match = self.pattern.match(clean_line)

        if match:
            group_dict = match.groupdict()
            return LogEntry(
                raw=clean_line,
                timestamp=group_dict.get("timestamp"),
                level=group_dict.get("level", "").upper() if group_dict.get("level") else None,
                message=group_dict.get("message", clean_line)
            )

        return LogEntry(raw=clean_line, message=clean_line)
