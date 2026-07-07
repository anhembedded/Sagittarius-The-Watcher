import pytest
from PySide6.QtCore import Qt, QItemSelectionModel
from PySide6.QtWidgets import QApplication
from logview.ui.main_window import MainWindow
from logview.models import LogEntry

@pytest.fixture
def app_config():
    return {
        "server": {"host": "127.0.0.1", "port": 0},
        "display": {"max_lines": 1000},
        "log_format": {"pattern": r"^\[(?P<timestamp>.*?)\]\s*\[(?P<level>\w+)\]\s*(?P<message>.*)"}
    }

@pytest.fixture
def populated_tab(qtbot, app_config, monkeypatch):
    monkeypatch.setattr("logview.ui.components.log_tab.ReceiverWorker.start", lambda self: None)

    window = MainWindow(app_config)
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)

    current_tab = window.tab_widget.currentWidget()

    logs = [
        LogEntry(raw="[2023] [INFO] Normal message", level="INFO", message="Normal message"),
        LogEntry(raw='{"timestamp": "2023", "level": "DEBUG", "message": "JSON message", "data": {"key": "value"}}', level="DEBUG", message='{"timestamp": "2023", "level": "DEBUG", "message": "JSON message", "data": {"key": "value"}}')
    ]

    current_tab.on_logs_received(logs)
    return current_tab, window

def test_inspect_log_details(qtbot, populated_tab):
    current_tab, window = populated_tab

    # Select first row
    model_index = current_tab.model.index(0, 0)
    current_tab.table_view.selectionModel().setCurrentIndex(model_index, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)

    # Verify detail panel updates (DetailPanel inherits QTextEdit)
    assert "Normal message" in current_tab._detail_panel.toPlainText()
    assert "INFO" in current_tab._detail_panel.toPlainText()

def test_json_pretty_print(qtbot, populated_tab):
    current_tab, window = populated_tab

    # Select JSON row
    model_index = current_tab.model.index(1, 0)
    current_tab.table_view.selectionModel().setCurrentIndex(model_index, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)

    # Verify JSON formatting (should contain indentation)
    panel_text = current_tab._detail_panel.toPlainText()
    assert '"key": "value"' in panel_text
    assert '\n        "key"' in panel_text

def test_relative_time_toggle(qtbot, populated_tab):
    current_tab, window = populated_tab

    assert window.toolbar_builder.action_rel_time.isChecked() is False
    assert current_tab.model._show_relative_time is False

    # By calling the model directly we bypass any UI signal dispatching issues in headless mode
    current_tab.model.toggle_relative_time()

    assert current_tab.model._show_relative_time is True

def test_font_zooming(qtbot, populated_tab):
    current_tab, window = populated_tab

    initial_size = window._table_font_size

    window._zoom_font(1)
    assert window._table_font_size == initial_size + 1

    window._zoom_font(-2)
    assert window._table_font_size == initial_size - 1

def test_copy_selected(qtbot, populated_tab):
    current_tab, window = populated_tab

    # Select both rows
    current_tab.table_view.selectAll()
    window._copy_selected_rows()

    # Read from actual clipboard
    copied_text = QApplication.clipboard().text()

    assert copied_text is not None
    assert "Normal message" in copied_text
    assert "JSON message" in copied_text

def test_theme_switching(qtbot, populated_tab):
    current_tab, window = populated_tab

    # Test internal logic to apply theme config updates
    initial_theme = window.config.get("theme", {}).get("name")

    window.change_theme("dark")

    # Ensure config reflects the change
    assert window.config["theme"]["name"] == "dark"
