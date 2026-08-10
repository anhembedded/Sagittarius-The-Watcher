import asyncio
import os
import tempfile

import pytest
from PySide6.QtWidgets import QApplication

from logview.models import LogEntry
from logview.ui.main_window import MainWindow


@pytest.fixture
def app_config():
    return {
        "server": {"host": "127.0.0.1", "port": 0},
        "display": {"max_lines": 1000},
        "log_format": {"pattern": r"^\[(?P<timestamp>.*?)\]\s*\[(?P<level>\w+)\]\s*(?P<message>.*)"},
    }


@pytest.mark.asyncio
async def test_tcp_connection(qtbot, app_config, monkeypatch):
    window = MainWindow(app_config)
    qtbot.addWidget(window)

    current_tab = window.tab_widget.currentWidget()

    # Wait for TCP receiver to start binding
    for _ in range(50):
        if (
            current_tab.receiver_thread._receivers
            and getattr(current_tab.receiver_thread._receivers[0], "server", None) is not None
        ):
            break
        await asyncio.sleep(0.1)

    # Get actual port
    addr = current_tab.receiver_thread._receivers[0].server.sockets[0].getsockname()
    port = addr[1]

    # Connect and send
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    writer.write(b"[2023-10-27 10:00:00] [INFO] TCP Test Line\n")
    await writer.drain()

    # Wait for UI to process log queue
    for _ in range(50):
        if current_tab.model.rowCount() == 1:
            break
        await asyncio.sleep(0.1)
        QApplication.processEvents()

    assert current_tab.model.rowCount() == 1
    assert current_tab.model._all_logs[0].message == "TCP Test Line"
    assert current_tab.model._all_logs[0].level == "INFO"

    # Status bar connected status
    assert "Connected" in window.status_bar._status_connection.text()
    assert "Total: 1" in window.status_bar._status_total.text()

    writer.close()
    await writer.wait_closed()
    window.close()


@pytest.mark.asyncio
async def test_file_tailing(qtbot, app_config):
    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        filepath = f.name

    try:
        app_config["tail_file"] = filepath
        window = MainWindow(app_config)
        qtbot.addWidget(window)

        await asyncio.sleep(0.5)

        with open(filepath, "a") as f:
            f.write("[2023-10-27 10:00:01] [ERROR] File Test Line\n")
            f.flush()

        current_tab = window.tab_widget.currentWidget()
        for _ in range(50):
            if current_tab.model.rowCount() == 1:
                break
            await asyncio.sleep(0.1)
            QApplication.processEvents()

        assert current_tab.model.rowCount() == 1
        assert current_tab.model._all_logs[0].message == "File Test Line"
        assert current_tab.model._all_logs[0].level == "ERROR"

    finally:
        if "window" in locals():
            window.close()
        try:
            os.unlink(filepath)
        except Exception:
            pass


def test_pause_resume_stream(qtbot, app_config, monkeypatch):
    monkeypatch.setattr("logview.ui.components.log_tab.ReceiverWorker.start", lambda self: None)

    window = MainWindow(app_config)
    qtbot.addWidget(window)
    current_tab = window.tab_widget.currentWidget()

    # Click pause
    window.toolbar_builder.action_pause.trigger()
    assert current_tab.is_paused is True

    # Simulate receiving logs
    log1 = LogEntry(raw="[2023] [INFO] Msg1", message="Msg1")
    log2 = LogEntry(raw="[2023] [INFO] Msg2", message="Msg2")
    current_tab.on_logs_received([log1, log2])

    # Check pending buffer in status bar and model count
    assert current_tab.model.rowCount() == 0
    assert len(current_tab.pending_logs) == 2
    assert "Pending Buffer: 2" in window.status_bar._status_pending.text()

    # Click resume
    window.toolbar_builder.action_pause.trigger()
    assert current_tab.is_paused is False
    assert current_tab.model.rowCount() == 2
    assert len(current_tab.pending_logs) == 0
    assert "Pending Buffer: 0" in window.status_bar._status_pending.text()


def test_auto_scroll_logic(qtbot, app_config, monkeypatch):
    monkeypatch.setattr("logview.ui.components.log_tab.ReceiverWorker.start", lambda self: None)

    window = MainWindow(app_config)
    qtbot.addWidget(window)
    current_tab = window.tab_widget.currentWidget()

    assert current_tab.auto_scroll is True

    # Simulate scroll break (user scrolling up)
    scrollbar = current_tab.table_view.verticalScrollBar()
    # Mocking scrollbar max to simulate scrolling up
    scrollbar.setMaximum(100)
    current_tab._on_scroll(80)  # Value less than maximum - 10 to trigger scroll break

    assert current_tab.auto_scroll is False

    # Simulate scrolling back to bottom
    current_tab._on_scroll(98)
    assert current_tab.auto_scroll is True


@pytest.mark.asyncio
async def test_new_source_tab(qtbot, app_config, monkeypatch):
    def mock_add_source_tab(*args, **kwargs):
        pass

    window = MainWindow(app_config)
    qtbot.addWidget(window)

    initial_tabs = window.tab_widget.count()
    assert initial_tabs == 1

    # Add a mock source tab directly using the actual function signature expected
    new_config = app_config.copy()
    new_config["server"]["port"] = 0
    window.add_source_tab("Source 2", new_config)

    # Wait for the new receiver to potentially start
    await asyncio.sleep(0.5)

    assert window.tab_widget.count() == 2
    new_tab = window.tab_widget.widget(1)

    assert new_tab.receiver_thread is not None
    window.close()
