import pytest
from PySide6.QtCore import Qt
from logview.ui.main_window import MainWindow
from logview.models import LogEntry

@pytest.fixture
def app_config():
    return {
        "server": {"host": "localhost", "port": 9999},
        "display": {"max_lines": 1000},
        "log_format": {"pattern": r"^\[(?P<timestamp>.*?)\]\s*\[(?P<level>\w+)\]\s*(?P<message>.*)"}
    }

def test_main_window_init(qtbot, app_config, monkeypatch):
    # Mocking QThread start to avoid starting real receivers during UI test
    monkeypatch.setattr("logview.ui.main_window.ReceiverWorker.start", lambda self: None)

    window = MainWindow(app_config)
    qtbot.addWidget(window)

    assert window.windowTitle() == "Log Viewer"
    assert window.model.rowCount() == 0

def test_receive_logs(qtbot, app_config, monkeypatch):
    monkeypatch.setattr("logview.ui.main_window.ReceiverWorker.start", lambda self: None)

    window = MainWindow(app_config)
    qtbot.addWidget(window)

    # Simulate receiving a log
    log = LogEntry(raw="[2023] [INFO] Msg", timestamp="2023", level="INFO", message="Msg")
    window.on_logs_received([log])

    assert window.model.rowCount() == 1
    assert window.model._all_logs[0].level == "INFO"

def test_pause_resume(qtbot, app_config, monkeypatch):
    monkeypatch.setattr("logview.ui.main_window.ReceiverWorker.start", lambda self: None)

    window = MainWindow(app_config)
    qtbot.addWidget(window)

    window.action_pause.setChecked(True)
    assert window.is_paused is True

    log = LogEntry(raw="[2023] [INFO] Msg")
    window.on_logs_received([log])

    # Should not update model yet
    assert window.model.rowCount() == 0
    assert len(window.pending_logs) == 1

    # Resume
    window.action_pause.setChecked(False)
    assert window.is_paused is False
    assert window.model.rowCount() == 1
    assert len(window.pending_logs) == 0

def test_filtering(qtbot, app_config, monkeypatch):
    monkeypatch.setattr("logview.ui.main_window.ReceiverWorker.start", lambda self: None)

    window = MainWindow(app_config)
    qtbot.addWidget(window)

    logs = [
        LogEntry(raw="[2023] [INFO] Success", level="INFO", message="Success"),
        LogEntry(raw="[2023] [ERROR] Failure", level="ERROR", message="Failure")
    ]
    window.on_logs_received(logs)

    assert window.model.rowCount() == 2

    # Apply filter
    window.filter_panel.level_combo.setCurrentText("ERROR")
    assert window.model.rowCount() == 1
    assert window.model.data(window.model.index(0, 2)) == "ERROR"

def test_copy_selected_rows(qtbot, app_config, monkeypatch):
    monkeypatch.setattr("logview.ui.main_window.ReceiverWorker.start", lambda self: None)

    window = MainWindow(app_config)
    qtbot.addWidget(window)

    log = LogEntry(raw="[2023] [INFO] Msg", timestamp="2023", level="INFO", message="Msg")
    window.on_logs_received([log])

    window.table_view.selectAll()
    window._copy_selected_rows()

    from PySide6.QtWidgets import QApplication
    assert QApplication.clipboard().text() == "[2023] [INFO] Msg"

    window._copy_selected_messages()
    assert QApplication.clipboard().text() == "Msg"
