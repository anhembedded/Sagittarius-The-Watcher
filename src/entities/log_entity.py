import dataclasses

@dataclasses.dataclass(frozen=True)
class LogEntry:
    timestamp: float
    level: str
    source: str
    message: str
