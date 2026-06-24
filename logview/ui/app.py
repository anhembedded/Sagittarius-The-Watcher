import asyncio
import os
from typing import List, Optional

from rich.text import Text
from textual.app import App, ComposeResult
from textual.widgets import RichLog, Input, Select, Label
from textual.binding import Binding
from textual.events import Key

from logview.models import LogEntry
from logview.receiver import TCPServerReceiver
from logview.log_parser import LogParser
from logview.ui.widgets import FilterBar, StatusBar, SearchBar
from logview.ui.dialogs import SaveDialog
from logview.config import get_config
from logview.export import export_logs

LEVEL_ORDER = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
}

class LogViewerApp(App):
    """The main application class for the Log Viewer TUI."""

    CSS_PATH = "style.tcss"

    BINDINGS = [
        Binding("space", "toggle_pause", "Pause/Resume"),
        Binding("ctrl+l", "clear_logs", "Clear Logs"),
        Binding("ctrl+s", "save_logs", "Save Logs"),
        Binding("slash", "toggle_search", "Search"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = get_config()
        self.all_logs: List[LogEntry] = []
        self.filtered_logs: List[LogEntry] = []
        self.queue: asyncio.Queue = asyncio.Queue()
        self.receiver: Optional[TCPServerReceiver] = None
        self.is_paused = False
        self.max_lines = self.config.get("display", {}).get("max_lines", 10000)

        # Filters
        self.current_level = "ALL"
        self.current_keyword = ""

        # Search
        self.search_term = ""
        self.search_results_indices: List[int] = []
        self.current_search_index = -1

    def compose(self) -> ComposeResult:
        """Compose the UI layout."""
        yield FilterBar()
        yield RichLog(id="log_view", auto_scroll=True, markup=True, highlight=True)
        yield SearchBar(id="search_bar")
        yield StatusBar()

    async def on_mount(self) -> None:
        """Called when app starts."""
        parser = LogParser(self.config["log_format"]["pattern"])
        self.receiver = TCPServerReceiver(
            host=self.config["server"]["host"],
            port=self.config["server"]["port"],
            parser=parser,
            queue=self.queue,
            listen_stdin=self.config.get("listen_stdin", False)
        )
        await self.receiver.start()
        # Start the background task to consume logs
        self.run_worker(self.consume_logs(), exclusive=True, thread=False)
        self.update_status_bar()

    async def on_unmount(self) -> None:
        """Called when app stops."""
        if self.receiver:
            await self.receiver.stop()

    async def consume_logs(self):
        """Consumes logs from the queue and adds them to the memory list."""
        while True:
            entry = await self.queue.get()
            # Must update memory safely
            self.call_from_thread(self.add_log, entry)

    def add_log(self, entry: LogEntry):
        """Adds log to memory list and updates UI if visible and not paused."""
        self.all_logs.append(entry)

        if len(self.all_logs) > self.max_lines * 2:
            self.all_logs = self.all_logs[-self.max_lines:]

        if not self.is_paused:
            if self.is_log_visible(entry):
                self.filtered_logs.append(entry)
                if len(self.filtered_logs) > self.max_lines:
                    self.filtered_logs.pop(0)

                self.write_to_log(entry)

        # We only want to update status bar periodically or every log? Let's just do it
        self.update_status_bar()


    def is_log_visible(self, entry: LogEntry) -> bool:
        """Checks if a log entry should be displayed based on current filters."""
        # Level filter
        if self.current_level != "ALL" and entry.level:
            entry_level_val = LEVEL_ORDER.get(entry.level, 0)
            filter_level_val = LEVEL_ORDER.get(self.current_level, 0)
            if entry_level_val < filter_level_val:
                return False

        # Keyword filter
        if self.current_keyword:
            if self.current_keyword.lower() not in entry.raw.lower():
                return False

        return True

    def write_to_log(self, entry: LogEntry):
        """Formats and writes a single log entry to the RichLog."""
        log_view = self.query_one(RichLog)

        # Formatting text based on level
        text = Text(entry.raw)

        # Basic highlight
        if entry.level == "DEBUG":
            text.stylize("bright_black")
        elif entry.level == "INFO":
            text.stylize("green")
        elif entry.level == "WARNING":
            text.stylize("yellow")
        elif entry.level == "ERROR":
            text.stylize("red")
        elif entry.level == "CRITICAL":
            text.stylize("bold white on red")

        # Highlight search term if active
        if self.search_term and self.search_term.lower() in entry.raw.lower():
            # A simple manual highlight for the search term
            term_len = len(self.search_term)
            start = 0
            raw_lower = entry.raw.lower()
            search_lower = self.search_term.lower()
            while True:
                idx = raw_lower.find(search_lower, start)
                if idx == -1:
                    break
                text.stylize("black on yellow", idx, idx + term_len)
                start = idx + term_len

        log_view.write(text)

    def refresh_log_view(self):
        """Clears and redraws the log view based on current filters and memory list."""
        log_view = self.query_one(RichLog)
        log_view.clear()

        self.filtered_logs = []
        for entry in self.all_logs:
            if self.is_log_visible(entry):
                self.filtered_logs.append(entry)

        # Enforce max lines
        self.filtered_logs = self.filtered_logs[-self.max_lines:]

        # Update search results
        self.update_search_results()

        for entry in self.filtered_logs:
            self.write_to_log(entry)

        self.update_status_bar()

    def update_status_bar(self):
        """Updates the text in the status bar."""
        try:
            status_label = self.query_one("#status_label", Label)
            count_label = self.query_one("#count_label", Label)

            status_text = "Paused" if self.is_paused else "Running"
            status_label.update(f"Status: {status_text}")

            count_label.update(f"Showing: {len(self.filtered_logs)} / {len(self.all_logs)}")
        except Exception:
            pass

    async def on_select_changed(self, event: Select.Changed) -> None:
        """Handle level filter changes."""
        if event.select.id == "level_select":
            self.current_level = str(event.value)
            self.refresh_log_view()

    async def on_input_changed(self, event: Input.Changed) -> None:
        """Handle keyword filter changes."""
        if event.input.id == "keyword_filter":
            self.current_keyword = event.value
            self.refresh_log_view()
        elif event.input.id == "search_input":
            self.search_term = event.value
            self.update_search_results()
            self.refresh_log_view()

    async def on_key(self, event: Key) -> None:
        """Handle enter / shift+enter in search box."""
        if self.query_one("#search_input", Input).has_focus:
            if event.key == "enter":
                self.next_search_result(1)
            elif event.key == "shift+enter":
                self.next_search_result(-1)

    def next_search_result(self, direction: int):
        """Cycles through search results. Positive direction for next, negative for prev."""
        if not self.search_results_indices:
            return

        self.current_search_index += direction
        if self.current_search_index >= len(self.search_results_indices):
            self.current_search_index = 0
        elif self.current_search_index < 0:
            self.current_search_index = len(self.search_results_indices) - 1

        self.update_search_label()

        # In Textual, RichLog inherits from ScrollView, so we can calculate scroll position.
        # We know each log entry is roughly 1 line, or we can use scroll_to.
        # Since text wraps, it's not exactly 1-to-1, but scrolling to the approx Y index usually helps.
        target_index = self.search_results_indices[self.current_search_index]
        log_view = self.query_one(RichLog)

        # Turn off auto_scroll so it doesn't snap to bottom while we search
        log_view.auto_scroll = False
        # Calculate Y. This assumes mostly 1 line per log.
        # A more precise way in RichLog would require measuring the lines of each entry,
        # but y=target_index is the best approximation for a fast built-in list.
        log_view.scroll_to(y=target_index)

    def update_search_results(self):
        """Finds all indices of matching logs in the current filtered view."""
        self.search_results_indices = []
        if not self.search_term:
            self.current_search_index = -1
            self.query_one("#search_results_label", Label).update("0/0")
            return

        search_lower = self.search_term.lower()
        for idx, entry in enumerate(self.filtered_logs):
            if search_lower in entry.raw.lower():
                self.search_results_indices.append(idx)

        if self.search_results_indices:
            self.current_search_index = 0
            self.update_search_label()
        else:
            self.current_search_index = -1
            self.query_one("#search_results_label", Label).update("0/0")

    def update_search_label(self):
        """Updates the search label text."""
        total = len(self.search_results_indices)
        if total > 0:
            current = self.current_search_index + 1
            self.query_one("#search_results_label", Label).update(f"{current}/{total}")
        else:
            self.query_one("#search_results_label", Label).update("0/0")

    def action_toggle_pause(self) -> None:
        """Toggles the pause state."""
        self.is_paused = not self.is_paused
        if not self.is_paused:
            # Resume: refresh the view to catch up
            self.refresh_log_view()
        self.update_status_bar()

    def action_clear_logs(self) -> None:
        """Clears all logs."""
        self.all_logs.clear()
        self.filtered_logs.clear()
        self.refresh_log_view()

    def action_save_logs(self) -> None:
        """Saves current filtered logs to a file."""
        def check_save(filename: str):
            if filename:
                try:
                    export_logs(self.filtered_logs, filename)
                    self.notify(f"Saved logs to {filename}", title="Export Success")
                except Exception as e:
                    self.notify(f"Failed to save logs: {e}", title="Export Error", severity="error")

        self.push_screen(SaveDialog(), check_save)

    def action_toggle_search(self) -> None:
        """Toggles the visibility of the search bar."""
        search_bar = self.query_one("#search_bar", SearchBar)
        if search_bar.styles.display == "none":
            search_bar.styles.display = "block"
            self.query_one("#search_input", Input).focus()
        else:
            search_bar.styles.display = "none"
            self.search_term = ""
            self.query_one("#search_input", Input).value = ""
            # Return focus to list/app
            self.query_one(RichLog).focus()
            self.refresh_log_view()
