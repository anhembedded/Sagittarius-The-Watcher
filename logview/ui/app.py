import asyncio
import os
from typing import List, Optional

from rich.text import Text
from textual.app import App, ComposeResult
from textual.widgets import Input, Select, Label
from textual.binding import Binding
from textual.events import Key

from logview.models import LogEntry
from logview.receiver import TCPServerReceiver, FileTailReceiver
from logview.log_parser import LogParser
from logview.ui.widgets import FilterBar, StatusBar, SearchBar
from logview.ui.dialogs import SaveDialog
from logview.ui.custom_log_list import CustomLogList
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
        Binding("b", "toggle_bookmark", "Bookmark"),
        Binding("B", "jump_next_bookmark", "Next Bookmark"),
        Binding("t", "toggle_theme", "Toggle Theme"),
        Binding("question_mark", "show_help", "Help"),
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
        yield CustomLogList(id="log_view")
        yield SearchBar(id="search_bar")
        yield StatusBar()

    async def on_mount(self) -> None:
        """Called when app starts."""

        # Set window title
        host = self.config["server"]["host"]
        port = self.config["server"]["port"]
        self.title = f"Log Viewer - [{host}:{port}]"

        # Initialize Theme
        if self.config.get("theme", "dark") == "light":
            self.theme = "textual-light"
        else:
            self.theme = "textual-dark"

        parser = LogParser(self.config["log_format"]["pattern"])

        if "tail_file" in self.config:
            self.title = f"Log Viewer - Tail: {self.config['tail_file']}"
            self.receiver = FileTailReceiver(
                filepath=self.config["tail_file"],
                parser=parser,
                queue=self.queue
            )
        else:
            self.receiver = TCPServerReceiver(
                host=host,
                port=port,
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

        # Keyword / Regex filter
        if self.current_keyword:
            try:
                # Always attempt to use the regex approach if regex mode is on, else simple matching
                is_regex = False
                try:
                    from textual.widgets import Checkbox
                    regex_toggle = self.query_one("#regex_toggle", Checkbox)
                    is_regex = regex_toggle.value
                except Exception:
                    pass

                if is_regex:
                    import re
                    if not re.search(self.current_keyword, entry.raw):
                        return False
                else:
                    if self.current_keyword.lower() not in entry.raw.lower():
                        return False
            except Exception:
                # If regex fails, we just don't match, or fallback
                pass

        return True

    def write_to_log(self, entry: LogEntry):
        """Formats and writes a single log entry to the CustomLogList."""
        log_view = self.query_one(CustomLogList)
        is_even = len(log_view.children) % 2 == 0
        log_view.append_log(entry, search_term=self.search_term, is_even=is_even)

    def refresh_log_view(self):
        """Clears and redraws the log view based on current filters and memory list."""
        log_view = self.query_one(CustomLogList)
        log_view.clear_logs()

        self.filtered_logs = []
        for entry in self.all_logs:
            if self.is_log_visible(entry):
                self.filtered_logs.append(entry)

        # Enforce max lines
        self.filtered_logs = self.filtered_logs[-self.max_lines:]

        # Update search results
        self.update_search_results()

        for i, entry in enumerate(self.filtered_logs):
            is_even = i % 2 == 0
            # Suppress new animations on mass refresh
            was_new = entry.is_new
            entry.is_new = False
            log_view.append_log(entry, search_term=self.search_term, is_even=is_even)
            entry.is_new = was_new

        self.update_status_bar()

    def update_status_bar(self):
        """Updates the text in the status bar."""
        try:
            status_label = self.query_one("#status_label", Label)
            count_label = self.query_one("#count_label", Label)
            stats_label = self.query_one("#stats_label", Label)

            status_text = "⏸️ Paused" if self.is_paused else "▶️ Running"
            status_label.update(status_text)

            count_label.update(f"Showing: {len(self.filtered_logs)} / {len(self.all_logs)}")

            # Level stats
            counts = {"ERR": 0, "WRN": 0, "CRI": 0}
            for e in self.all_logs:
                if e.level == "ERROR": counts["ERR"] += 1
                elif e.level == "WARNING": counts["WRN"] += 1
                elif e.level == "CRITICAL": counts["CRI"] += 1

            stats_text = f"ERR:{counts['ERR']} WRN:{counts['WRN']} CRI:{counts['CRI']}"
            stats_label.update(stats_text)
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

            # Check for regex error
            is_regex = False
            try:
                from textual.widgets import Checkbox
                regex_toggle = self.query_one("#regex_toggle", Checkbox)
                is_regex = regex_toggle.value
            except Exception:
                pass

            input_widget = self.query_one("#keyword_filter", Input)
            if is_regex and self.current_keyword:
                import re
                try:
                    re.compile(self.current_keyword)
                    input_widget.remove_class("-error")
                    self.query_one("#filter_label", Label).update("Filter:")
                except re.error as e:
                    input_widget.add_class("-error")
                    self.query_one("#filter_label", Label).update(f"Regex Error: {e}")
                    return # Don't update view if regex is invalid
            else:
                input_widget.remove_class("-error")
                self.query_one("#filter_label", Label).update("Filter:")

            self.refresh_log_view()
        elif event.input.id == "search_input":
            self.search_term = event.value
            self.update_search_results()
            self.refresh_log_view()

    async def on_checkbox_changed(self, event) -> None:
        if event.checkbox.id == "regex_toggle":
            # Re-trigger input changed logic to validate
            input_widget = self.query_one("#keyword_filter", Input)
            self.current_keyword = input_widget.value

            if event.value and self.current_keyword:
                import re
                try:
                    re.compile(self.current_keyword)
                    input_widget.remove_class("-error")
                    self.query_one("#filter_label", Label).update("Regex:")
                except re.error as e:
                    input_widget.add_class("-error")
                    self.query_one("#filter_label", Label).update(f"Regex Error: {e}")
                    return
            else:
                input_widget.remove_class("-error")
                self.query_one("#filter_label", Label).update("Filter:")

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

        target_index = self.search_results_indices[self.current_search_index]
        log_view = self.query_one(CustomLogList)

        log_view.index = target_index

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
        def check_save(result: tuple):
            filename, fmt = result
            if filename:
                if not filename.endswith(f".{fmt}"):
                    filename += f".{fmt}"
                try:
                    export_logs(self.filtered_logs, filename, format=fmt)
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
            self.query_one(CustomLogList).focus()
            self.refresh_log_view()

    def action_toggle_bookmark(self) -> None:
        self.query_one(CustomLogList).toggle_bookmark()

    def action_jump_next_bookmark(self) -> None:
        self.query_one(CustomLogList).jump_next_bookmark()

    def action_toggle_theme(self) -> None:
        self.theme = "textual-light" if self.theme == "textual-dark" else "textual-dark"

    def action_show_help(self) -> None:
        from logview.ui.dialogs import HelpScreen
        self.push_screen(HelpScreen())
