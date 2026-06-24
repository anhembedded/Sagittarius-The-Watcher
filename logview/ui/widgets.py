from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Select, Input, Static, Label
from textual.events import InputEvent


from textual.widgets import Checkbox

class FilterBar(Horizontal):
    """Bar containing filter controls (level and keyword)."""

    def compose(self) -> ComposeResult:
        levels = [
            ("ALL", "ALL"),
            ("DEBUG", "DEBUG"),
            ("INFO", "INFO"),
            ("WARNING", "WARNING"),
            ("ERROR", "ERROR"),
            ("CRITICAL", "CRITICAL"),
        ]
        yield Label("Level:")
        yield Select(levels, value="ALL", id="level_select")
        yield Checkbox("Regex", id="regex_toggle", value=False)
        yield Label("Filter:", id="filter_label")
        yield Input(placeholder="Keyword...", id="keyword_filter")


class StatusBar(Horizontal):
    """Bar displaying current app status."""

    def compose(self) -> ComposeResult:
        yield Label("▶️ Running", id="status_label")
        yield Label(" | ", classes="separator")
        yield Label("Showing: 0 / 0", id="count_label")
        yield Label(" | ", classes="separator")
        yield Label("", id="stats_label")
        yield Label(" | ", classes="separator")
        yield Label("Keys: [?] Help", id="keys_label")


class SearchBar(Horizontal):
    """Hidden bar for finding text."""

    def compose(self) -> ComposeResult:
        yield Label("Search:")
        yield Input(placeholder="Search... (Enter for next, Shift+Enter for prev)", id="search_input")
        yield Label("0/0", id="search_results_label")
