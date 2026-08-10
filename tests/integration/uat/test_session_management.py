import json
import os
import tempfile

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
        LogEntry(raw="[2023] [INFO] Msg1", level="INFO", message="Msg1"),
        LogEntry(raw="[2023] [ERROR] Msg2", level="ERROR", message="Msg2"),
    ]

    current_tab.on_logs_received(logs)
    return current_tab, window


def test_export_to_text(qtbot, populated_tab, monkeypatch):
    current_tab, window = populated_tab

    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".log") as f:
        filepath = f.name

    try:
        # Mock QFileDialog to return our temp filepath
        monkeypatch.setattr("PySide6.QtWidgets.QFileDialog.getSaveFileName", lambda *args, **kwargs: (filepath, ""))
        # Mock QMessageBox so the UI doesn't hang waiting for user
        monkeypatch.setattr("PySide6.QtWidgets.QMessageBox.information", lambda *args, **kwargs: None)

        window.export_logs()

        with open(filepath, "r") as f:
            content = f.read()

        assert "[2023] [INFO] Msg1" in content
        assert "[2023] [ERROR] Msg2" in content
    finally:
        os.unlink(filepath)


def test_save_load_session(qtbot, populated_tab, monkeypatch):
    current_tab, window = populated_tab

    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".lvsession") as f:
        filepath = f.name

    try:
        # Mock file dialogs
        monkeypatch.setattr("PySide6.QtWidgets.QFileDialog.getSaveFileName", lambda *args, **kwargs: (filepath, ""))
        monkeypatch.setattr("PySide6.QtWidgets.QFileDialog.getOpenFileName", lambda *args, **kwargs: (filepath, ""))
        # Mock QMessageBox
        monkeypatch.setattr("PySide6.QtWidgets.QMessageBox.information", lambda *args, **kwargs: None)

        window.save_session()

        # Verify file exists and has JSON
        with open(filepath, "r") as f:
            data = json.load(f)
            assert "entries" in data
            assert len(data["entries"]) == 2

        # Clear the model manually to verify load replenishes it
        current_tab.model.clear_logs()
        assert current_tab.model.rowCount() == 0

        # Load session loads into current_tab
        window.load_session()

        assert current_tab.model.rowCount() == 2
        assert current_tab.model._all_logs[0].message == "Msg1"

    finally:
        os.unlink(filepath)


def test_custom_regex(qtbot, app_config):
    # This tests the settings dialog logic directly
    from logview.ui.settings_dialog import SettingsDialog

    window = MainWindow(app_config)
    qtbot.addWidget(window)
    dialog = SettingsDialog(app_config, window)

    dialog._regex_edit.setText(r"(?P<level>INFO|ERROR)\s+(?P<message>.*)")
    dialog._sample_edit.setText("ERROR Something went wrong")

    # Click test button
    dialog._test_regex()

    assert "Match found!" in dialog._test_result_label.text()
    assert "ERROR" in dialog._test_result_label.text()
    assert "Something went wrong" in dialog._test_result_label.text()


def test_change_colors(qtbot, populated_tab):
    current_tab, window = populated_tab

    from logview.ui.settings_dialog import SettingsDialog

    dialog = SettingsDialog(window.config, window)

    # Modify config to change ERROR color
    dialog._level_rows["ERROR"].bg_btn.set_color("#ff0000")

    # Check config generation
    updated_cfg = dialog.get_updated_config()
    assert updated_cfg["colors"]["ERROR"]["bg"] == "#ff0000"
