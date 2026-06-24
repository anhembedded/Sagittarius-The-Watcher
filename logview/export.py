from typing import List
import json
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
