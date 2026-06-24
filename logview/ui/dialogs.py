from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Input, Label, Button
from textual.containers import Vertical, Horizontal

from textual.widgets import Select

class SaveDialog(ModalScreen[tuple]):
    """Dialog to ask the user for a filename and format."""

    def compose(self) -> ComposeResult:
        with Vertical(id="save_dialog"):
            yield Label("Enter filename to save logs:", id="save_prompt")
            yield Input(placeholder="export", value="export", id="save_input")
            yield Select([("Text (.log)", "log"), ("JSON (.json)", "json")], value="log", id="save_format")
            with Horizontal(id="save_buttons"):
                yield Button("Save", variant="success", id="save_btn")
                yield Button("Cancel", variant="error", id="cancel_btn")

    def on_mount(self) -> None:
        self.query_one(Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save_btn":
            filename = self.query_one(Input).value
            fmt = self.query_one(Select).value
            self.dismiss((filename, fmt))
        else:
            self.dismiss((None, None))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        filename = event.value
        fmt = self.query_one(Select).value
        self.dismiss((filename, fmt))

class HelpScreen(ModalScreen):
    """Screen that displays help and keybindings."""

    def compose(self) -> ComposeResult:
        with Vertical(id="help_dialog"):
            yield Label("Keyboard Shortcuts", id="help_title")
            yield Label("[Space]    : Pause / Resume")
            yield Label("[Ctrl+L]   : Clear Logs")
            yield Label("[Ctrl+S]   : Save Logs")
            yield Label("[/]        : Toggle Search")
            yield Label("[b]        : Toggle Bookmark on selected line")
            yield Label("[B]        : Jump to next Bookmark")
            yield Label("[t]        : Toggle Dark/Light Theme")
            yield Label("[?]        : Show this Help Screen")
            yield Label("[q]        : Quit application")
            with Horizontal(id="save_buttons"):
                yield Button("Close", variant="primary", id="close_btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close_btn":
            self.dismiss()

    def on_key(self, event) -> None:
        if event.key == "escape" or event.key == "question_mark":
            self.dismiss()
