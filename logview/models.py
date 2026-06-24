from dataclasses import dataclass
from typing import Optional

@dataclass
class LogEntry:
    """Represents a single log line parsed from the stream.

    Attributes:
        raw (str): The original unparsed log line.
        timestamp (Optional[str]): The extracted timestamp, if any.
        level (Optional[str]): The extracted log level, if any.
        message (str): The extracted message or the whole line if parsing failed.
    """
    raw: str
    timestamp: Optional[str] = None
    level: Optional[str] = None
    message: str = ""
