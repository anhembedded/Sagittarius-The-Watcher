from typing import List
import json
from datetime import datetime
from logview.models import LogEntry


def export_logs(entries: List[LogEntry], filepath: str, format: str = "log"):
    """Exports a list of log entries to a file.

    Args:
        entries (List[LogEntry]): The log entries to export.
        filepath (str): The file path to save the logs to.
        format (str): The format to save ("log" or "json").
    """
    if format == "json":
        data = [
            {
                "timestamp": e.timestamp,
                "level": e.level,
                "message": e.message,
                "raw": e.raw
            }
            for e in entries
        ]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    else:
        with open(filepath, "w", encoding="utf-8") as f:
            for entry in entries:
                f.write(entry.raw + "\n")


def save_session(entries: List[LogEntry], filepath: str):
    """Saves all log entries as a session file (JSON) that can be reloaded later.

    Args:
        entries (List[LogEntry]): All log entries to persist.
        filepath (str): Output file path (conventionally *.lvsession).
    """
    data = {
        "version": 1,
        "saved_at": datetime.now().isoformat(),
        "entries": [
            {
                "raw": e.raw,
                "timestamp": e.timestamp,
                "level": e.level,
                "message": e.message,
                "parsed_dt": e.parsed_dt.isoformat() if e.parsed_dt else None,
            }
            for e in entries
        ]
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_session(filepath: str) -> List[LogEntry]:
    """Loads a previously saved session file.

    Args:
        filepath (str): Path to a *.lvsession JSON file.

    Returns:
        List[LogEntry]: The restored log entries (is_new=False so no animation).
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    entries = []
    for item in data.get("entries", []):
        parsed_dt = None
        dt_str = item.get("parsed_dt")
        if dt_str:
            try:
                parsed_dt = datetime.fromisoformat(dt_str)
            except (ValueError, TypeError):
                pass
        entries.append(LogEntry(
            raw=item.get("raw", ""),
            timestamp=item.get("timestamp"),
            level=item.get("level"),
            message=item.get("message", ""),
            is_new=False,
            parsed_dt=parsed_dt,
        ))
    return entries
