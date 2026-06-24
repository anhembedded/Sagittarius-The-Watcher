import sys
from typing import Dict, Any, List

from PySide6.QtWidgets import (QMainWindow, QTableView, QVBoxLayout, QWidget,
                               QToolBar, QStyle, QHeaderView, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt, QThread, Signal, Slot, QTimer

from logview.ui.log_model import LogModel
from logview.ui.components import FilterPanel
import queue
import asyncio
from logview.receiver import TCPServerReceiver, FileTailReceiver
from logview.log_parser import LogParser
from logview.export import export_logs
from logview.models import LogEntry

class ReceiverWorker(QThread):
    """
    Worker thread to run the async log receivers.
    # Adapter/Observer Pattern: Adapts the async receivers to Qt's signal/slot mechanism.
    """
    logs_received = Signal(list)
    error_occurred = Signal(str)

    def __init__(self, config: Dict[str, Any], parser: LogParser):
        super().__init__()
        self.config = config
        self.parser = parser
        self.running = True
        self.loop = None
        self._async_queue = None
        self._receivers = []

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self._async_queue = asyncio.Queue()

        if "tail_file" in self.config and self.config["tail_file"]:
            self._receivers.append(FileTailReceiver(self.config["tail_file"], self.parser, self._async_queue))
        else:
            host = self.config.get("server", {}).get("host", "localhost")
            port = self.config.get("server", {}).get("port", 9999)
            listen_stdin = self.config.get("listen_stdin", False)
            self._receivers.append(TCPServerReceiver(host, port, self.parser, self._async_queue, listen_stdin))

        for r in self._receivers:
            self.loop.run_until_complete(r.start())

        try:
            while self.running:
                logs = []
                while True:
                    try:
                        entry = self._async_queue.get_nowait()
                        logs.append(entry)
                    except asyncio.QueueEmpty:
                        break

                if logs:
                    self.logs_received.emit(logs)

                self.loop.run_until_complete(asyncio.sleep(0.1))
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            for r in self._receivers:
                self.loop.run_until_complete(r.stop())
            self.loop.close()

    def stop(self):
        self.running = False
        self.wait()

class MainWindow(QMainWindow):
    """
    Main Application Window.
    """
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config
        self.setWindowTitle("Log Viewer")
        self.resize(1200, 700)

        # Setup Theme/Style
        self._setup_style()

        # Initialize Core components
        self.parser = LogParser(config["log_format"]["pattern"])
        self.model = LogModel(self)

        # State
        self.is_paused = False
        self.pending_logs: List[LogEntry] = []

        # Setup UI
        self._setup_ui()
        self.is_dark_theme = False
        self._apply_theme()

        # Start Receiver
        self.receiver_thread = ReceiverWorker(self.config, self.parser)
        self.receiver_thread.logs_received.connect(self.on_logs_received)
        self.receiver_thread.error_occurred.connect(self.on_error)
        self.receiver_thread.start()

        # Auto-scroll timer
        self.scroll_timer = QTimer(self)
        self.scroll_timer.timeout.connect(self._check_autoscroll)
        self.scroll_timer.start(200)
        self.auto_scroll = True

    def _setup_style(self):
        # Initial style setup is handled in _apply_theme
        pass

    def toggle_theme(self):
        self.is_dark_theme = not self.is_dark_theme
        self._apply_theme()

    def _apply_theme(self):
        if self.is_dark_theme:
            qss = """
            QMainWindow, QWidget { background-color: #2b2b2b; color: #a9b7c6; }
            QTableView {
                background-color: #313335;
                alternate-background-color: #2b2b2b;
                selection-background-color: #214283;
                selection-color: #ffffff;
                border: 1px solid #555555;
            }
            QHeaderView::section {
                background-color: #3c3f41;
                padding: 4px;
                border: 1px solid #555555;
                font-weight: bold;
            }
            QToolBar { background-color: #3c3f41; border-bottom: 1px solid #555555; }
            QLineEdit, QComboBox { background-color: #45494a; color: #a9b7c6; border: 1px solid #646464; }
            """
        else:
            qss = """
            QMainWindow { background-color: #f0f0f0; color: #000000; }
            QTableView {
                background-color: #ffffff;
                alternate-background-color: #f9f9f9;
                selection-background-color: #a8d8ff;
                selection-color: #000000;
                border: 1px solid #ccc;
            }
            QHeaderView::section {
                background-color: #e0e0e0;
                padding: 4px;
                border: 1px solid #ccc;
                font-weight: bold;
            }
            QToolBar { background-color: #e0e0e0; border-bottom: 1px solid #ccc; }
            """
        self.setStyleSheet(qss)

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Toolbar
        self.toolbar = QToolBar("Main Toolbar")
        self.addToolBar(self.toolbar)

        self.action_pause = self.toolbar.addAction(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause), "Pause")
        self.action_pause.setCheckable(True)
        self.action_pause.toggled.connect(self.toggle_pause)

        self.action_clear = self.toolbar.addAction(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon), "Clear")
        self.action_clear.triggered.connect(self.clear_logs)

        self.action_export = self.toolbar.addAction(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton), "Export")
        self.action_export.triggered.connect(self.export_logs)

        self.toolbar.addSeparator()

        self.action_theme = self.toolbar.addAction(self.style().standardIcon(QStyle.StandardPixmap.SP_DesktopIcon), "Toggle Theme")
        self.action_theme.triggered.connect(self.toggle_theme)

        # Filter Panel
        self.filter_panel = FilterPanel()
        self.filter_panel.filter_changed.connect(self.model.set_filter)
        layout.addWidget(self.filter_panel)

        # Table View
        self.table_view = QTableView()
        self.table_view.setModel(self.model)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

        # Column widths
        self.table_view.setColumnWidth(0, 30)  # Bookmark
        self.table_view.setColumnWidth(1, 150) # Timestamp
        self.table_view.setColumnWidth(2, 80)  # Level

        layout.addWidget(self.table_view)

        # Connect scrollbar signal for auto-scroll logic
        self.table_view.verticalScrollBar().valueChanged.connect(self._on_scroll)

    @Slot(list)
    def on_logs_received(self, logs: List[LogEntry]):
        if self.is_paused:
            self.pending_logs.extend(logs)
        else:
            self.model.add_logs(logs)

    def toggle_pause(self, paused: bool):
        self.is_paused = paused
        if paused:
            self.action_pause.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
            self.action_pause.setText("Resume")
        else:
            self.action_pause.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
            self.action_pause.setText("Pause")
            # Flush pending logs
            if self.pending_logs:
                self.model.add_logs(self.pending_logs)
                self.pending_logs.clear()

    def clear_logs(self):
        self.model.clear_logs()
        self.pending_logs.clear()

    def export_logs(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Logs", "", "Log Files (*.log);;JSON Files (*.json)"
        )
        if file_path:
            try:
                logs_to_export = self.model.get_all_logs()
                format_type = "json" if file_path.endswith(".json") else "text"
                export_logs(logs_to_export, file_path, format_type)
                QMessageBox.information(self, "Export Successful", f"Logs exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", str(e))

    @Slot(str)
    def on_error(self, message: str):
        # Could show in status bar
        self.statusBar().showMessage(f"Error: {message}", 5000)

    def _on_scroll(self, value: int):
        # If user scrolls up, disable auto-scroll
        scrollbar = self.table_view.verticalScrollBar()
        if value < scrollbar.maximum() - 5: # Threshold
            self.auto_scroll = False
        else:
            self.auto_scroll = True

    def _check_autoscroll(self):
        if self.auto_scroll and not self.is_paused:
            self.table_view.scrollToBottom()

    def closeEvent(self, event):
        self.receiver_thread.stop()
        super().closeEvent(event)
