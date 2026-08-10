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
    # The window needs to be shown for visibility checks to work properly
    window.show()
    qtbot.waitExposed(window)

    current_tab = window.tab_widget.currentWidget()

    logs = [
        LogEntry(raw="[2023] [INFO] Request starting for user 123", message="Request starting for user 123"),
        LogEntry(raw="[2023] [DEBUG] Processing user 123 payload", message="Processing user 123 payload"),
        LogEntry(raw="[2023] [ERROR] Timeout for user 123", message="Timeout for user 123"),
    ]

    current_tab.on_logs_received(logs)
    return current_tab, window


def test_open_find_bar(qtbot, populated_tab):
    current_tab, window = populated_tab

    # Assert find bar is initially hidden
    assert current_tab._find_bar.isVisible() is False

    # Toggle find bar explicitly (Ctrl+F slot)
    window._toggle_find_bar()

    assert current_tab._find_bar.isVisible() is True
    assert current_tab._find_bar._input.hasFocus() is True


def test_highlight_text(qtbot, populated_tab):
    current_tab, window = populated_tab

    # Type in find bar
    current_tab._find_bar._input.setText("123")

    # The term should be passed to the delegate for highlighting
    assert current_tab._delegate._term == "123"


def test_next_prev_navigation(qtbot, populated_tab):
    current_tab, window = populated_tab

    # Set text and update matches
    current_tab._find_bar._input.setText("user")
    current_tab._on_find_term_changed("user", False)

    # The navigate signal should scroll the table
    # Since we can't easily access the local buttons without looping layout items, we emit the signal directly as the UI would
    current_tab._find_bar.navigate.emit(1)  # Next match
    selected_row = current_tab.table_view.selectionModel().currentIndex().row()
    assert selected_row == 0
    assert "1/3" in current_tab._find_bar._match_label.text()

    # Next match
    current_tab._find_bar.navigate.emit(1)
    selected_row = current_tab.table_view.selectionModel().currentIndex().row()
    assert selected_row == 1
    assert "2/3" in current_tab._find_bar._match_label.text()

    # Prev match
    current_tab._find_bar.navigate.emit(-1)
    selected_row = current_tab.table_view.selectionModel().currentIndex().row()
    assert selected_row == 0
    assert "1/3" in current_tab._find_bar._match_label.text()


def test_close_find_bar(qtbot, populated_tab):
    current_tab, window = populated_tab

    # Open and set term
    window._toggle_find_bar()
    current_tab._find_bar._input.setText("user")
    assert current_tab._delegate._term == "user"

    # Close find bar
    current_tab._find_bar.close_bar()

    assert current_tab._find_bar.isVisible() is False
    # Highlighting should be cleared
    assert current_tab._delegate._term == ""
