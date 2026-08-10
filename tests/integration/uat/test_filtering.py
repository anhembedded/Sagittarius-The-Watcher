from datetime import datetime

import pytest

from logview.models import LogEntry
from logview.ui.main_window import MainWindow


@pytest.fixture
def app_config():
    return {
        "server": {"host": "127.0.0.1", "port": 0},
        "display": {"max_lines": 1000},
        "log_format": {"pattern": r"^\[(?P<timestamp>.*?)\]\s*\[(?P<level>\w+)\]\s*(?P<message>.*)"},
    }


@pytest.fixture
def populated_tab(qtbot, app_config, monkeypatch):
    monkeypatch.setattr("logview.ui.components.log_tab.ReceiverWorker.start", lambda self: None)

    window = MainWindow(app_config)
    qtbot.addWidget(window)
    current_tab = window.tab_widget.currentWidget()

    logs = [
        LogEntry(
            raw="[2023-10-01 10:00:00] [INFO] Database connection successful",
            level="INFO",
            message="Database connection successful",
            parsed_dt=datetime(2023, 10, 1, 10, 0, 0),
        ),
        LogEntry(
            raw="[2023-10-01 10:05:00] [WARNING] High memory usage detected",
            level="WARNING",
            message="High memory usage detected",
            parsed_dt=datetime(2023, 10, 1, 10, 5, 0),
        ),
        LogEntry(
            raw="[2023-10-01 10:10:00] [ERROR] Timeout connecting to host",
            level="ERROR",
            message="Timeout connecting to host",
            parsed_dt=datetime(2023, 10, 1, 10, 10, 0),
        ),
        LogEntry(
            raw="[2023-10-01 10:15:00] [ERROR] Missing configuration file",
            level="ERROR",
            message="Missing configuration file",
            parsed_dt=datetime(2023, 10, 1, 10, 15, 0),
        ),
    ]

    current_tab.on_logs_received(logs)
    return current_tab


def test_level_filtering(populated_tab):
    assert populated_tab.model.rowCount() == 4

    # Filter by ERROR
    for cb in populated_tab.filter_panel.level_checkboxes:
        cb.setChecked(cb.text() == "ERROR")
    assert populated_tab.model.rowCount() == 2
    assert populated_tab.model._filtered_logs[0].level == "ERROR"
    assert populated_tab.model._filtered_logs[1].level == "ERROR"


def test_standard_text_filter(populated_tab):
    # Filter by "timeout"
    populated_tab.filter_panel.search_input.setText("timeout")
    assert populated_tab.model.rowCount() == 1
    assert populated_tab.model._filtered_logs[0].message == "Timeout connecting to host"


def test_regex_text_filter(populated_tab):
    # Enable Regex and search
    populated_tab.filter_panel.regex_checkbox.setChecked(True)
    populated_tab.filter_panel.search_input.setText(r"memory\s+usage")

    assert populated_tab.model.rowCount() == 1
    assert populated_tab.model._filtered_logs[0].level == "WARNING"


def test_time_range_filter(populated_tab):
    # The time range widget emits range_changed(from_dt, to_dt)
    from_dt = datetime(2023, 10, 1, 10, 4, 0)
    to_dt = datetime(2023, 10, 1, 10, 12, 0)

    # Simulate time range enable
    populated_tab.time_range_widget.range_changed.emit(from_dt, to_dt)

    assert populated_tab.model.rowCount() == 2
    assert populated_tab.model._filtered_logs[0].level == "WARNING"
    assert populated_tab.model._filtered_logs[1].message == "Timeout connecting to host"


def test_combined_filters(populated_tab):
    # Level + Text
    for cb in populated_tab.filter_panel.level_checkboxes:
        cb.setChecked(cb.text() == "ERROR")
    populated_tab.filter_panel.search_input.setText("configuration")

    assert populated_tab.model.rowCount() == 1
    assert populated_tab.model._filtered_logs[0].message == "Missing configuration file"
