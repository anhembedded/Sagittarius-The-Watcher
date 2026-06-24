from typing import List
from logview.models import LogEntry

def export_logs(entries: List[LogEntry], filepath: str):
    """Exports a list of log entries to a file.

    Args:
        entries (List[LogEntry]): The log entries to export.
        filepath (str): The file path to save the logs to.
    """
    with open(filepath, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(entry.raw + "\n")
