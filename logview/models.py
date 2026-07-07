from dataclasses import dataclass
from typing import Optional
from datetime import datetime

import uuid

@dataclass
class LogEntry:
    """Represents a single log line parsed from the stream.

    Attributes:
        raw (str): The original unparsed log line.
        timestamp (Optional[str]): The extracted timestamp, if any.
        level (Optional[str]): The extracted log level, if any.
        message (str): The extracted message or the whole line if parsing failed.
        id (str): A unique identifier for the log entry, useful for bookmarking.
        is_new (bool): Indicates if the log is newly added, used for UI animation.
        parsed_dt (Optional[datetime]): Datetime parsed from timestamp, used for sorting/relative time.
    """
    raw: str
    timestamp: Optional[str] = None
    level: Optional[str] = None
    message: str = ""
    id: str = ""
    is_new: bool = True
    parsed_dt: Optional[datetime] = None

    def __post_init__(self):
        if not self.id:
            self.id = uuid.uuid4().hex
        self._raw_lower: Optional[str] = None

    @property
    def raw_lower(self) -> str:
        """Lazily evaluates and caches the lowercase version of the raw log string."""
        if self._raw_lower is None:
            self._raw_lower = self.raw.lower()
        return self._raw_lower
