import itertools
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

@dataclass
class LogEntry:
    """Represents a single log line parsed from the stream.

    Attributes:
        raw (str): The original unparsed log line.
        timestamp (Optional[str]): The extracted timestamp, if any.
        level (Optional[str]): The extracted log level, if any.
        message (str): The extracted message or the whole line if parsing failed.
        id (int): A unique identifier for the log entry, useful for bookmarking.
        is_new (bool): Indicates if the log is newly added, used for UI animation.
        parsed_dt (Optional[datetime]): Datetime parsed from timestamp, used for sorting/relative time.
    """
    raw: str
    timestamp: Optional[str] = None
    level: Optional[str] = None
    index: Optional[str] = None
    module: Optional[str] = None
    submodule: Optional[str] = None
    message: str = ""
    id: int = 0
    is_new: bool = True
    parsed_dt: Optional[datetime] = None

    _id_counter = itertools.count(1)

    def __post_init__(self):
        if self.id == 0:
            self.id = next(self._id_counter)
        if not self.index:
            self.index = str(self.id)
        self._raw_lower: Optional[str] = None

    @property
    def raw_lower(self) -> str:
        """Lazily evaluates and caches the lowercase version of the raw log string."""
        if self._raw_lower is None:
            self._raw_lower = self.raw.lower()
        return self._raw_lower
