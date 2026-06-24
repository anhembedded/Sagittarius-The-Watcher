import queue
from typing import Any

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable

from src.entities.log_entity import LogEntry

POLL_INTERVAL_SECONDS: float = 0.1

# Adapter Pattern
class TextualLogViewerApp(App):

    def __init__(self, log_queue: "queue.Queue[LogEntry]", *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.log_queue = log_queue

    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable()
        yield Footer()

    def on_mount(self) -> None:
        self.table = self.query_one(DataTable)
        self.table.add_columns("Timestamp", "Level", "Source", "Message")
        self.set_interval(POLL_INTERVAL_SECONDS, self.poll_log_queue)

    # Polling Consumer Pattern
    def poll_log_queue(self) -> None:
        while True:
            try:
                log_entry: LogEntry = self.log_queue.get_nowait()
                self.table.add_row(
                    str(log_entry.timestamp),
                    log_entry.level,
                    log_entry.source,
                    log_entry.message
                )
            except queue.Empty:
                break
