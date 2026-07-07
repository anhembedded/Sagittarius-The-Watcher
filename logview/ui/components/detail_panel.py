from PySide6.QtWidgets import QTextEdit
from PySide6.QtGui import QFont
from PySide6.QtCore import Slot

class DetailPanel(QTextEdit):
    """Panel for displaying detailed log information."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont("Courier New", 9))
        self.setPlaceholderText("Select a log row to see full details…")
        self.setMaximumHeight(180)

    @Slot(object)
    def update_details(self, entry):
        if entry:
            if not entry.level and not entry.timestamp:
                self.setPlainText(entry.raw)
                return

            # Pretty-print raw JSON if applicable
            pretty_raw = entry.raw
            if entry.raw.strip().startswith("{"):
                try:
                    import json
                    parsed_json = json.loads(entry.raw)
                    pretty_raw = json.dumps(parsed_json, indent=4)
                except Exception:
                    pass

            details = []
            if entry.timestamp:
                details.append(f"Timestamp: {entry.timestamp}")
            if entry.level:
                details.append(f"Level:     {entry.level}")
            if entry.module:
                details.append(f"Module:    {entry.module}")
            if entry.submodule:
                details.append(f"Submodule: {entry.submodule}")
            if entry.message:
                indented_msg = entry.message.replace("\n", "\n           ")
                details.append(f"Message:   {indented_msg}")

            details.append("\n" + "-" * 60 + "\nRaw Log:\n" + pretty_raw)
            self.setPlainText("\n".join(details))
        else:
            self.clear()
