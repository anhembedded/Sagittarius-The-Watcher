from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Input, Label, Button
from textual.containers import Vertical, Horizontal

class SaveDialog(ModalScreen[str]):
    """Dialog to ask the user for a filename."""

    def compose(self) -> ComposeResult:
        with Vertical(id="save_dialog"):
            yield Label("Enter filename to save logs:", id="save_prompt")
            yield Input(placeholder="export.log", value="export.log", id="save_input")
            with Horizontal(id="save_buttons"):
                yield Button("Save", variant="success", id="save_btn")
                yield Button("Cancel", variant="error", id="cancel_btn")

    def on_mount(self) -> None:
        self.query_one(Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save_btn":
            self.dismiss(self.query_one(Input).value)
        else:
            self.dismiss("")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value)
