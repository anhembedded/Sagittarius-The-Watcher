from PySide6.QtWidgets import QStatusBar, QLabel

class LogStatusBar(QStatusBar):
    """Custom Status Bar for the Log Viewer."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent

        self._status_connection = QLabel("● Listening")
        self._status_connection.setStyleSheet("color: #f39c12; padding: 0 8px;")
        self.addPermanentWidget(self._status_connection)

        self.addPermanentWidget(self._make_separator())

        self._status_total = QLabel("Total: 0")
        self.addPermanentWidget(self._status_total)

        self.addPermanentWidget(self._make_separator())

        self._status_shown = QLabel("Shown: 0")
        self.addPermanentWidget(self._status_shown)

        self.addPermanentWidget(self._make_separator())

        self._status_rate = QLabel("0 msg/s")
        self.addPermanentWidget(self._status_rate)

        self.addPermanentWidget(self._make_separator())

        self._status_levels = QLabel("")
        self.addPermanentWidget(self._status_levels)

    @staticmethod
    def _make_separator() -> QLabel:
        sep = QLabel("|")
        sep.setStyleSheet("color: #aaa; padding: 0 4px;")
        return sep

    def update_status(self, total: int, shown: int):
        self._status_total.setText(f"Total: {total:,}")
        self._status_shown.setText(f"Shown: {shown:,}")

    def update_rate_display(self, rate: int):
        self._status_rate.setText(f"{rate} msg/s")

    def update_level_counts(self, counts: dict):
        """Feature 6: Update level badges in status bar."""
        parts = []
        colors = {"ERROR": "#e74c3c", "CRITICAL": "#8e44ad", "WARNING": "#e67e22", "DEBUG": "#7f8c8d"}
        for lvl in ["ERROR", "CRITICAL", "WARNING"]:
            n = counts.get(lvl, 0)
            if n:
                c = colors.get(lvl, "#888")
                parts.append(f'<span style="color:{c};">{lvl}:{n}</span>')
        self._status_levels.setText("  ".join(parts))

    def set_client_connected(self, addr: str):
        self._status_connection.setText(f"● Connected ({addr})")
        self._status_connection.setStyleSheet("color: #27ae60; padding: 0 8px;")

    def set_client_disconnected(self):
        self._status_connection.setText("● Listening")
        self._status_connection.setStyleSheet("color: #f39c12; padding: 0 8px;")
