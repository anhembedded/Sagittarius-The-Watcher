from typing import Dict, Any, Optional
import copy
import json

from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QTabWidget, QWidget, QFormLayout,
    QVBoxLayout, QHBoxLayout, QLineEdit, QSpinBox, QPushButton,
    QLabel, QFrame, QScrollArea, QSizePolicy, QComboBox
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QColorDialog
import re


LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class ColorButton(QPushButton):
    """A push button that shows a color swatch and opens a color picker on click."""

    def __init__(self, color: str = "", parent=None):
        super().__init__(parent)
        self.setFixedSize(80, 28)
        self._color: str = ""
        self.set_color(color)
        self.clicked.connect(self._pick_color)

    def set_color(self, hex_color: str):
        self._color = hex_color.strip() if hex_color else ""
        self._refresh_style()

    def get_color(self) -> str:
        return self._color

    def _refresh_style(self):
        if self._color:
            # Show color swatch
            c = QColor(self._color)
            if c.isValid():
                text_color = "#000000" if c.lightness() > 128 else "#ffffff"
                self.setText(self._color)
                self.setStyleSheet(
                    f"QPushButton {{ background-color: {self._color}; color: {text_color}; "
                    f"border: 1px solid #888; border-radius: 3px; font-size: 9px; }}"
                    f"QPushButton:hover {{ border: 2px solid #555; }}"
                )
                return
        # No color – show a transparent/strikethrough style
        self.setText("none")
        self.setStyleSheet(
            "QPushButton { background-color: #f0f0f0; color: #aaa; "
            "border: 1px dashed #aaa; border-radius: 3px; font-size: 9px; }"
            "QPushButton:hover { border: 1px dashed #555; }"
        )

    def _pick_color(self):
        initial = QColor(self._color) if self._color else QColor(Qt.GlobalColor.white)
        color = QColorDialog.getColor(initial, self, "Pick Color",
                                      QColorDialog.ColorDialogOption.ShowAlphaChannel)
        if color.isValid():
            self.set_color(color.name())  # #RRGGBB

    def clear_color(self):
        self.set_color("")


class LevelColorRow(QWidget):
    """One row: level label + bg picker + fg picker + reset button."""

    def __init__(self, level: str, bg: str, fg: str, parent=None):
        super().__init__(parent)
        self.level = level

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)

        lbl = QLabel(level)
        lbl.setFixedWidth(70)
        lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(lbl)

        layout.addWidget(QLabel("BG:"))
        self.bg_btn = ColorButton(bg)
        layout.addWidget(self.bg_btn)

        layout.addWidget(QLabel("FG:"))
        self.fg_btn = ColorButton(fg)
        layout.addWidget(self.fg_btn)

        reset_btn = QPushButton("✕ Reset")
        reset_btn.setFixedSize(60, 24)
        reset_btn.setStyleSheet("font-size: 9px;")
        reset_btn.clicked.connect(self._reset)
        layout.addWidget(reset_btn)

        layout.addStretch()

    def _reset(self):
        self.bg_btn.clear_color()
        self.fg_btn.clear_color()

    def get_colors(self) -> Dict[str, str]:
        return {"bg": self.bg_btn.get_color(), "fg": self.fg_btn.get_color()}


class SettingsDialog(QDialog):
    """Settings dialog with Connection and Log Colors tabs."""

    def __init__(self, config: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(420)
        self.setModal(True)

        # Deep copy so changes don't affect live config until accepted
        self._config = copy.deepcopy(config)

        root_layout = QVBoxLayout(self)

        tabs = QTabWidget()
        tabs.addTab(self._build_connection_tab(), "🔌 Connection")
        tabs.addTab(self._build_colors_tab(), "🎨 Log Colors")
        tabs.addTab(self._build_log_format_tab(), "⚙️ Log Format")
        root_layout.addWidget(tabs)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root_layout.addWidget(buttons)

    # ------------------------------------------------------------------
    # Tab builders
    # ------------------------------------------------------------------

    def _build_connection_tab(self) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)
        form.setContentsMargins(12, 12, 12, 12)
        form.setVerticalSpacing(10)

        server = self._config.get("server", {})

        self._host_edit = QLineEdit(server.get("host", "localhost"))
        form.addRow("Host:", self._host_edit)

        self._port_spin = QSpinBox()
        self._port_spin.setRange(1, 65535)
        self._port_spin.setValue(int(server.get("port", 9999)))
        form.addRow("Port:", self._port_spin)

        alerts = self._config.get("alerts", {})
        self._alert_edit = QLineEdit(alerts.get("pattern", ""))
        self._alert_edit.setPlaceholderText("e.g. CRITICAL|Out of Memory")
        form.addRow("Alert Trigger (Regex):", self._alert_edit)

        note = QLabel("ℹ Changes take effect after restarting the receiver.")
        note.setStyleSheet("color: gray; font-size: 10px;")
        note.setWordWrap(True)
        form.addRow(note)

        return widget

    def _build_colors_tab(self) -> QWidget:
        widget = QWidget()
        outer = QVBoxLayout(widget)
        outer.setContentsMargins(12, 12, 12, 4)

        header = QHBoxLayout()
        for lbl_text in ["Level", "", "Background", "", "Foreground"]:
            lbl = QLabel(lbl_text)
            lbl.setStyleSheet("font-weight: bold; font-size: 10px; color: #555;")
            header.addWidget(lbl)
        header.addStretch()
        outer.addLayout(header)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        outer.addWidget(line)

        colors_cfg = self._config.get("colors", {})
        self._level_rows: Dict[str, LevelColorRow] = {}

        for level in LOG_LEVELS:
            level_colors = colors_cfg.get(level, {})
            row = LevelColorRow(
                level,
                bg=level_colors.get("bg", ""),
                fg=level_colors.get("fg", ""),
            )
            self._level_rows[level] = row
            outer.addWidget(row)

        outer.addStretch()

        note = QLabel("ℹ Leave empty for default (no color). Accepts any #RRGGBB hex color.")
        note.setStyleSheet("color: gray; font-size: 10px;")
        note.setWordWrap(True)
        outer.addWidget(note)

        return widget

    def _build_log_format_tab(self) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)
        form.setContentsMargins(12, 12, 12, 12)
        form.setVerticalSpacing(10)

        self._preset_combo = QComboBox()
        self._preset_combo.addItems(["Custom", "Apache", "Nginx", "Spring Boot", "Syslog"])
        self._preset_combo.currentTextChanged.connect(self._on_preset_changed)
        form.addRow("Preset:", self._preset_combo)

        log_format = self._config.get("log_format", {})

        self._regex_edit = QLineEdit(log_format.get("pattern", ""))
        form.addRow("Regex Pattern:", self._regex_edit)

        self._sample_edit = QLineEdit()
        self._sample_edit.setPlaceholderText("Enter a sample log line here...")
        form.addRow("Sample Log:", self._sample_edit)

        test_layout = QHBoxLayout()
        self._test_btn = QPushButton("Test Regex")
        self._test_btn.setAccessibleName("Test Regex Pattern")
        self._test_btn.clicked.connect(self._test_regex)
        test_layout.addWidget(self._test_btn)

        self._test_result_label = QLabel("")
        self._test_result_label.setWordWrap(True)
        self._test_result_label.setStyleSheet("color: gray; font-size: 10px;")
        test_layout.addWidget(self._test_result_label)

        form.addRow(test_layout)

        return widget

    def _on_preset_changed(self, text: str):
        presets = {
            "Apache": r'^(?P<host>\S+) \S+ \S+ \[(?P<timestamp>[\w:/]+\s[+\-]\d{4})\] "(?P<request>.*?)" (?P<status>\d{3}) (?P<size>\S+)',
            "Nginx": r'^(?P<host>\S+) - \S+ \[(?P<timestamp>[\w:/]+\s[+\-]\d{4})\] "(?P<request>.*?)" (?P<status>\d{3}) (?P<size>\S+)',
            "Spring Boot": r'^(?P<timestamp>\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\.\d{3})\s+(?P<level>\w+)\s+\d+\s+---\s+\[.*?\]\s+.*?\s+:\s+(?P<message>.*)',
            "Syslog": r'^(?P<timestamp>\w{3}\s+\d+\s\d{2}:\d{2}:\d{2})\s+(?P<host>\S+)\s+(?P<app>\S+):\s+(?P<message>.*)'
        }
        if text in presets:
            self._regex_edit.setText(presets[text])

    def _test_regex(self):
        pattern = self._regex_edit.text()
        sample = self._sample_edit.text()
        try:
            regex = re.compile(pattern)
            match = regex.match(sample)
            if match:
                groups = match.groupdict()
                result_text = "Match found!\n"
                for k, v in groups.items():
                    result_text += f"{k}: {v}\n"
                self._test_result_label.setStyleSheet("color: green; font-size: 10px;")
                self._test_result_label.setText(result_text)
            else:
                self._test_result_label.setStyleSheet("color: red; font-size: 10px;")
                self._test_result_label.setText("No match.")
        except re.error as e:
            self._test_result_label.setStyleSheet("color: red; font-size: 10px;")
            self._test_result_label.setText(f"Invalid regex: {e}")

    # ------------------------------------------------------------------
    # Result extraction
    # ------------------------------------------------------------------

    def get_updated_config(self) -> Dict[str, Any]:
        """Returns the config dict updated with values from the dialog."""
        cfg = copy.deepcopy(self._config)

        # Connection
        if "server" not in cfg:
            cfg["server"] = {}
        cfg["server"]["host"] = self._host_edit.text().strip() or "localhost"
        cfg["server"]["port"] = self._port_spin.value()

        # Colors
        cfg["colors"] = {}
        for level, row in self._level_rows.items():
            cfg["colors"][level] = row.get_colors()

        # Log Format
        if "log_format" not in cfg:
            cfg["log_format"] = {}
        cfg["log_format"]["pattern"] = self._regex_edit.text()

        # Alerts
        if "alerts" not in cfg:
            cfg["alerts"] = {}
        cfg["alerts"]["pattern"] = self._alert_edit.text()

        return cfg


def save_config_to_toml(config: Dict[str, Any], path: str):
    """Writes the relevant config sections back to logview.toml."""
    lines = []

    server = config.get("server", {})
    lines.append("[server]")
    lines.append(f'host = {json.dumps(server.get("host", "localhost"), ensure_ascii=False)}')
    lines.append(f'port = {server.get("port", 9999)}')
    lines.append("")

    display = config.get("display", {})
    lines.append("[display]")
    lines.append(f'max_lines = {display.get("max_lines", 10000)}')
    lines.append("")

    log_format = config.get("log_format", {})
    pattern = log_format.get("pattern", "")
    lines.append("[log_format]")
    lines.append(f'pattern = {json.dumps(pattern, ensure_ascii=False)}')
    lines.append("")

    colors = config.get("colors", {})
    for level in LOG_LEVELS:
        level_colors = colors.get(level, {})
        lines.append(f"[colors.{level}]")
        lines.append(f'bg = {json.dumps(level_colors.get("bg", ""), ensure_ascii=False)}')
        lines.append(f'fg = {json.dumps(level_colors.get("fg", ""), ensure_ascii=False)}')
        lines.append("")

    theme = config.get("theme", {})
    lines.append("[theme]")
    lines.append(f'name = {json.dumps(theme.get("name", "auto"), ensure_ascii=False)}')
    lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
