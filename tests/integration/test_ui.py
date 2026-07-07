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
    monkeypatch.setattr("logview.ui.components.log_tab.ReceiverWorker.start", lambda self: None)

    window = MainWindow(app_config)
    qtbot.addWidget(window)

    assert window.windowTitle() == "Log Viewer"
    assert window.tab_widget.currentWidget().model.rowCount() == 0

def test_receive_logs(qtbot, app_config, monkeypatch):
    monkeypatch.setattr("logview.ui.components.log_tab.ReceiverWorker.start", lambda self: None)

    window = MainWindow(app_config)
    qtbot.addWidget(window)

    # Simulate receiving a log
    log = LogEntry(raw="[2023] [INFO] Msg", timestamp="2023", level="INFO", message="Msg")
    window.tab_widget.currentWidget().on_logs_received([log])

    assert window.tab_widget.currentWidget().model.rowCount() == 1
    assert window.tab_widget.currentWidget().model._all_logs[0].level == "INFO"

def test_pause_resume(qtbot, app_config, monkeypatch):
    monkeypatch.setattr("logview.ui.components.log_tab.ReceiverWorker.start", lambda self: None)

    window = MainWindow(app_config)
    qtbot.addWidget(window)

    window.toolbar_builder.action_pause.setChecked(True)
    assert window.tab_widget.currentWidget().is_paused is True

    log = LogEntry(raw="[2023] [INFO] Msg")
    window.tab_widget.currentWidget().on_logs_received([log])

    # Should not update model yet
    assert window.tab_widget.currentWidget().model.rowCount() == 0
    assert len(window.tab_widget.currentWidget().pending_logs) == 1

    # Resume
    window.toolbar_builder.action_pause.setChecked(False)
    assert window.tab_widget.currentWidget().is_paused is False
    assert window.tab_widget.currentWidget().model.rowCount() == 1
    assert len(window.tab_widget.currentWidget().pending_logs) == 0

def test_filtering(qtbot, app_config, monkeypatch):
    monkeypatch.setattr("logview.ui.components.log_tab.ReceiverWorker.start", lambda self: None)

    window = MainWindow(app_config)
    qtbot.addWidget(window)

    logs = [
        LogEntry(raw="[2023] [INFO] Success", level="INFO", message="Success"),
        LogEntry(raw="[2023] [ERROR] Failure", level="ERROR", message="Failure")
    ]
    window.tab_widget.currentWidget().on_logs_received(logs)

    assert window.tab_widget.currentWidget().model.rowCount() == 2

    # Apply filter by unchecking INFO
    for cb in window.tab_widget.currentWidget().filter_panel.level_checkboxes:
        if cb.text() == "INFO":
            cb.setChecked(False)
            break

    assert window.tab_widget.currentWidget().model.rowCount() == 1
    assert window.tab_widget.currentWidget().model.data(window.tab_widget.currentWidget().model.index(0, 2)) == "ERROR"

def test_view_toggles(qtbot, app_config, monkeypatch):
    monkeypatch.setattr("logview.ui.components.log_tab.ReceiverWorker.start", lambda self: None)

    window = MainWindow(app_config)
    qtbot.addWidget(window)
    window.show()

    assert window.toolbar_builder.toolbar.isVisible()
    assert window.status_bar.isVisible()
    assert window.tab_widget.currentWidget()._detail_panel.isVisible()

    window.toggle_toolbar(False)
    assert not window.toolbar_builder.toolbar.isVisible()

    window.toggle_status_bar(False)
    assert not window.status_bar.isVisible()

    window.toggle_detail_panel(False)
    assert not window.tab_widget.currentWidget()._detail_panel.isVisible()
    assert not window._show_detail_panel

def test_copy_selected_rows(qtbot, app_config, monkeypatch):
    monkeypatch.setattr("logview.ui.components.log_tab.ReceiverWorker.start", lambda self: None)

    window = MainWindow(app_config)
    qtbot.addWidget(window)

    log = LogEntry(raw="[2023] [INFO] Msg", timestamp="2023", level="INFO", message="Msg")
    window.tab_widget.currentWidget().on_logs_received([log])

    window.tab_widget.currentWidget().table_view.selectAll()
    window._copy_selected_rows()

    from PySide6.QtWidgets import QApplication
    assert QApplication.clipboard().text() == "[2023] [INFO] Msg"

    window._copy_selected_messages()
    assert QApplication.clipboard().text() == "Msg"
