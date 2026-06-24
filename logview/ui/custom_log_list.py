from typing import List, Optional, Set
from rich.text import Text
from rich.style import Style
from textual.app import ComposeResult
from textual.widgets import ListItem, ListView, Label
from textual.containers import ScrollableContainer
from textual.reactive import reactive
from textual import events
from logview.models import LogEntry

LEVEL_ORDER = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
}

class LogItem(ListItem):
    """A single log item in the list view."""

    def __init__(self, entry: LogEntry, search_term: str = "", is_even: bool = False, is_bookmarked: bool = False):
        super().__init__()
        self.entry = entry
        self.search_term = search_term
        self.is_even = is_even
        self.is_bookmarked = is_bookmarked

    def compose(self) -> ComposeResult:
        yield Label(self._format_text())

    def _format_text(self) -> Text:
        prefix = "* " if self.is_bookmarked else "  "
        text = Text(prefix + self.entry.raw)

        # Zebra striping
        if self.is_even:
            text.stylize("on #222222") # A slight background for even rows

        if self.entry.is_new:
            # Highlight fade for new entries
            text.stylize("black on white")
        else:
            # Basic highlight
            if self.entry.level == "DEBUG":
                text.stylize("bright_black")
            elif self.entry.level == "INFO":
                text.stylize("green")
            elif self.entry.level == "WARNING":
                text.stylize("yellow")
            elif self.entry.level == "ERROR":
                text.stylize("red")
            elif self.entry.level == "CRITICAL":
                text.stylize("bold white on red")

        # Highlight search term if active
        if self.search_term and self.search_term.lower() in self.entry.raw.lower():
            term_len = len(self.search_term)
            start = len(prefix)
            raw_lower = self.entry.raw.lower()
            search_lower = self.search_term.lower()
            while True:
                idx = raw_lower.find(search_lower, start - len(prefix))
                if idx == -1:
                    break
                # adjust index due to prefix
                text.stylize("black on yellow", idx + len(prefix), idx + len(prefix) + term_len)
                start = idx + len(prefix) + term_len

        return text

    def update_view(self):
        label = self.query_one(Label)
        label.update(self._format_text())

    def set_not_new(self):
        if self.entry.is_new:
            self.entry.is_new = False
            self.update_view()

class CustomLogList(ListView):
    """A custom log list that supports bookmarking and animation."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bookmarks: Set[str] = set()
        self.search_term = ""

    def append_log(self, entry: LogEntry, search_term: str = "", is_even: bool = False):
        is_bookmarked = entry.id in self.bookmarks
        item = LogItem(entry, search_term=search_term, is_even=is_even, is_bookmarked=is_bookmarked)
        self.append(item)
        if entry.is_new:
            # Set a timer to turn off the highlight
            self.set_timer(0.5, item.set_not_new)

    def clear_logs(self):
        self.clear()

    def toggle_bookmark(self):
        """Toggles bookmark on the currently selected item."""
        if self.index is not None and 0 <= self.index < len(self.children):
            item: LogItem = self.children[self.index]
            if item.entry.id in self.bookmarks:
                self.bookmarks.remove(item.entry.id)
                item.is_bookmarked = False
            else:
                self.bookmarks.add(item.entry.id)
                item.is_bookmarked = True
            item.update_view()

    def jump_next_bookmark(self):
        """Jumps to the next bookmarked item."""
        if not self.children:
            return

        start_idx = 0 if self.index is None else self.index + 1

        # Search forward
        for i in range(start_idx, len(self.children)):
            item: LogItem = self.children[i]
            if item.entry.id in self.bookmarks:
                self.index = i
                return

        # Wrap around
        for i in range(0, start_idx):
            item: LogItem = self.children[i]
            if item.entry.id in self.bookmarks:
                self.index = i
                return
