import sys
from typing import Dict, Any, List, Optional

from PySide6.QtWidgets import (
    QMainWindow, QTableView, QVBoxLayout, QWidget, QToolBar, QStyle,
    QHeaderView, QFileDialog, QMessageBox, QSplitter, QTextEdit, QLabel,
    QStatusBar, QMenuBar, QApplication, QMenu, QDockWidget,
)
from PySide6.QtCore import Qt, QThread, Signal, Slot, QTimer, QEvent
from PySide6.QtGui import QFont, QKeySequence, QShortcut, QClipboard, QAction, QColor

from logview.ui.log_model import LogModel
from logview.ui.log_delegate import HighlightDelegate
from logview.ui.find_bar import FindBar
from logview.ui.components import FilterPanel, TimeRangeWidget
from logview.ui.settings_dialog import SettingsDialog, save_config_to_toml
from logview.log_parser import LogParser
from logview.export import export_logs, save_session, load_session
from logview.models import LogEntry
from logview.config import DEFAULT_CONFIG_PATH
from logview.ui.receiver_worker import ReceiverWorker
from logview.ui.charts_panel import LiveStatsPanel


class MainWindow(QMainWindow):
    """Main Application Window."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config
        self.setWindowTitle("Log Viewer")
        self.resize(1280, 800)

        # Setup Theme/Style
        self._setup_style()

        # Initialize Core components
        self.parser = LogParser(config["log_format"]["pattern"])
        self.model = LogModel(self, color_config=config.get("colors", {}))

        # State
        self.is_paused = False
        self.pending_logs: List[LogEntry] = []
        self._log_rate_counter = 0          # Feature 1: logs received since last tick
        self._table_font_size = 10          # Feature 9: current font point size
        self._connected_clients: int = 0    # Feature 1: active client count

        # Setup UI
        self._setup_menu()
        self._setup_ui()
        self._setup_status_bar()

        self.is_dark_theme = False
        self._apply_theme()

        # Start Receiver
        self.receiver_thread = ReceiverWorker(self.config, self.parser)
        self.receiver_thread.logs_received.connect(self.on_logs_received)
        self.receiver_thread.error_occurred.connect(self.on_error)
        self.receiver_thread.client_connected.connect(self._on_client_connected)
        self.receiver_thread.client_disconnected.connect(self._on_client_disconnected)
        self.receiver_thread.start()

        # Auto-scroll timer
        self.scroll_timer = QTimer(self)
        self.scroll_timer.timeout.connect(self._check_autoscroll)
        self.scroll_timer.start(200)
        self.auto_scroll = True

        # Feature 1: Rate counter timer (1s tick)
        self._rate_timer = QTimer(self)
        self._rate_timer.timeout.connect(self._update_rate_display)
        self._rate_timer.start(1000)

        # Feature 6: Level counts
        self.model.counts_changed.connect(self._update_level_counts)

        # 📊 Live Statistics & Charts Panel
        self.stats_dock = QDockWidget("Live Statistics", self)
        self.stats_panel = LiveStatsPanel(self.stats_dock)
        self.stats_dock.setWidget(self.stats_panel)
        self.stats_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.stats_dock)
        self.model.counts_changed.connect(self.stats_panel.update_counts)

        # Install event filter for Ctrl+Scroll zoom (Feature 9)
        self.table_view.viewport().installEventFilter(self)

        # Ctrl+F shortcut (Feature 3)
        find_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        find_shortcut.activated.connect(self._toggle_find_bar)

        # Update initial status
        self._update_status()

    # ------------------------------------------------------------------
    # Menu (Feature 15: Session save/load)
    # ------------------------------------------------------------------

    def _setup_menu(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")

        act_save = QAction("Save Session…", self)
        act_save.setShortcut(QKeySequence("Ctrl+S"))
        act_save.triggered.connect(self.save_session)
        file_menu.addAction(act_save)

        act_load = QAction("Load Session…", self)
        act_load.setShortcut(QKeySequence("Ctrl+O"))
        act_load.triggered.connect(self.load_session)
        file_menu.addAction(act_load)

        file_menu.addSeparator()

        act_export = QAction("Export Logs…", self)
        act_export.triggered.connect(self.export_logs)
        file_menu.addAction(act_export)

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def _setup_style(self):
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
            QTextEdit { background-color: #2b2b2b; color: #a9b7c6; border: 1px solid #555555; }
            QStatusBar { background-color: #3c3f41; border-top: 1px solid #555555; }
            QMenuBar { background-color: #3c3f41; }
            QMenuBar::item:selected { background-color: #214283; }
            QMenu { background-color: #3c3f41; border: 1px solid #555555; }
            QMenu::item:selected { background-color: #214283; }
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
            QTextEdit { background-color: #fafafa; border: 1px solid #ccc; }
            """
        self.setStyleSheet(qss)

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Toolbar
        self.toolbar = QToolBar("Main Toolbar")
        self.addToolBar(self.toolbar)

        self.action_pause = self.toolbar.addAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause), "Pause"
        )
        self.action_pause.setCheckable(True)
        self.action_pause.toggled.connect(self.toggle_pause)

        self.action_clear = self.toolbar.addAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon), "Clear"
        )
        self.action_clear.triggered.connect(self.clear_logs)

        self.toolbar.addSeparator()

        # Feature 14: Relative timestamp toggle
        self.action_rel_time = self.toolbar.addAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogResetButton),
            "Relative Time"
        )
        self.action_rel_time.setCheckable(True)
        self.action_rel_time.setToolTip("Toggle relative timestamps (e.g. '2s ago')")
        self.action_rel_time.toggled.connect(self._on_relative_time_toggled)

        self.toolbar.addSeparator()

        self.action_theme = self.toolbar.addAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DesktopIcon), "Toggle Theme"
        )
        self.action_theme.triggered.connect(self.toggle_theme)

        self.action_settings = self.toolbar.addAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView), "Settings"
        )
        self.action_settings.triggered.connect(self.open_settings)

        # Filter Panel
        self.filter_panel = FilterPanel()
        self.filter_panel.filter_changed.connect(self.model.set_filter)
        main_layout.addWidget(self.filter_panel)

        # Feature 7: Time Range Widget
        self.time_range_widget = TimeRangeWidget()
        self.time_range_widget.range_changed.connect(self.model.set_time_range)
        main_layout.addWidget(self.time_range_widget)

        # Feature 3: Find Bar
        self._find_bar = FindBar()
        self._find_bar.term_changed.connect(self._on_find_term_changed)
        self._find_bar.navigate.connect(self._on_find_navigate)
        self._find_bar.closed.connect(self._on_find_closed)
        main_layout.addWidget(self._find_bar)

        # Feature 2: Splitter with table + detail panel
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)

        # Table View
        self.table_view = QTableView()
        self.table_view.setModel(self.model)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setSortingEnabled(True)     # Feature 8
        self.table_view.horizontalHeader().sectionClicked.connect(self._on_header_clicked)

        # Feature 3: Highlight delegate
        self._delegate = HighlightDelegate(self.table_view)
        self.table_view.setItemDelegateForColumn(3, self._delegate)  # Message column

        # Column widths
        self.table_view.setColumnWidth(0, 30)   # Bookmark
        self.table_view.setColumnWidth(1, 170)  # Timestamp
        self.table_view.setColumnWidth(2, 80)   # Level

        # Apply initial font size
        self._apply_table_font()

        splitter.addWidget(self.table_view)

        # Feature 2: Detail Panel
        self._detail_panel = QTextEdit()
        self._detail_panel.setReadOnly(True)
        self._detail_panel.setFont(QFont("Courier New", 9))
        self._detail_panel.setPlaceholderText("Select a log row to see full details…")
        self._detail_panel.setMaximumHeight(180)
        splitter.addWidget(self._detail_panel)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

        # Connect selection to detail panel
        self.table_view.selectionModel().currentRowChanged.connect(self._on_row_selected)
        # Connect scrollbar for auto-scroll
        self.table_view.verticalScrollBar().valueChanged.connect(self._on_scroll)

    def _setup_status_bar(self):
        """Feature 1: Status bar setup."""
        sb = self.statusBar()

        self._status_connection = QLabel("● Listening")
        self._status_connection.setStyleSheet("color: #f39c12; padding: 0 8px;")
        sb.addPermanentWidget(self._status_connection)

        sb.addPermanentWidget(self._make_separator())

        self._status_total = QLabel("Total: 0")
        sb.addPermanentWidget(self._status_total)

        sb.addPermanentWidget(self._make_separator())

        self._status_shown = QLabel("Shown: 0")
        sb.addPermanentWidget(self._status_shown)

        sb.addPermanentWidget(self._make_separator())

        self._status_rate = QLabel("0 msg/s")
        sb.addPermanentWidget(self._status_rate)

        sb.addPermanentWidget(self._make_separator())

        self._status_levels = QLabel("")
        sb.addPermanentWidget(self._status_levels)

    @staticmethod
    def _make_separator() -> QLabel:
        sep = QLabel("|")
        sep.setStyleSheet("color: #aaa; padding: 0 4px;")
        return sep

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    @Slot(list)
    def on_logs_received(self, logs: List[LogEntry]):
        self._log_rate_counter += len(logs)
        if self.is_paused:
            self.pending_logs.extend(logs)
        else:
            self.model.add_logs(logs)
            self._update_status()

    def toggle_pause(self, paused: bool):
        self.is_paused = paused
        if paused:
            self.action_pause.setIcon(
                self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
            )
            self.action_pause.setText("Resume")
        else:
            self.action_pause.setIcon(
                self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause)
            )
            self.action_pause.setText("Pause")
            if self.pending_logs:
                self.model.add_logs(self.pending_logs)
                self.pending_logs.clear()
                self._update_status()

    def clear_logs(self):
        self.model.clear_logs()
        self.pending_logs.clear()
        self._detail_panel.clear()
        self._update_status()

    @Slot(str)
    def on_error(self, message: str):
        self.statusBar().showMessage(f"Error: {message}", 5000)

    @Slot(str)
    def _on_client_connected(self, addr: str):
        self._connected_clients += 1
        self._status_connection.setText(f"● Connected ({addr})")
        self._status_connection.setStyleSheet("color: #27ae60; padding: 0 8px;")

    @Slot(str)
    def _on_client_disconnected(self, addr: str):
        self._connected_clients = max(0, self._connected_clients - 1)
        if self._connected_clients == 0:
            self._status_connection.setText("● Listening")
            self._status_connection.setStyleSheet("color: #f39c12; padding: 0 8px;")

    def _on_scroll(self, value: int):
        scrollbar = self.table_view.verticalScrollBar()
        self.auto_scroll = value >= scrollbar.maximum() - 5

    def _check_autoscroll(self):
        if self.auto_scroll and not self.is_paused:
            self.table_view.scrollToBottom()

    # Feature 2: Detail panel
    @Slot()
    def _on_row_selected(self, current, previous):
        row = current.row()
        entry = self.model.get_entry_at_row(row)
        if entry:
            self._detail_panel.setPlainText(entry.raw)
        else:
            self._detail_panel.clear()

    # Feature 8: Sorting
    def _on_header_clicked(self, col: int):
        # Toggle sort order if same column, else default ascending
        pass  # Handled automatically by setSortingEnabled + model.sort()

    # Feature 14: Relative time
    def _on_relative_time_toggled(self, checked: bool):
        self.model.toggle_relative_time()

    # ------------------------------------------------------------------
    # Feature 1: Status bar updates
    # ------------------------------------------------------------------

    def _update_status(self):
        total = len(self.model.get_all_logs())
        shown = self.model.get_filtered_count()
        self._status_total.setText(f"Total: {total:,}")
        self._status_shown.setText(f"Shown: {shown:,}")

    def _update_rate_display(self):
        rate = self._log_rate_counter
        self._log_rate_counter = 0
        self._status_rate.setText(f"{rate} msg/s")

    @Slot(dict)
    def _update_level_counts(self, counts: dict):
        """Feature 6: Update level badges in status bar."""
        parts = []
        colors = {"ERROR": "#e74c3c", "CRITICAL": "#8e44ad", "WARNING": "#e67e22", "DEBUG": "#7f8c8d"}
        for lvl in ["ERROR", "CRITICAL", "WARNING"]:
            n = counts.get(lvl, 0)
            if n:
                c = colors.get(lvl, "#888")
                parts.append(f'<span style="color:{c};">{lvl}:{n}</span>')
        self._status_levels.setText("  ".join(parts))
        self._update_status()

    # ------------------------------------------------------------------
    # Feature 3: Find bar
    # ------------------------------------------------------------------

    def _toggle_find_bar(self):
        if self._find_bar.isVisible():
            self._find_bar.close_bar()
        else:
            self._find_bar.open()

    @Slot(str)
    def _on_find_term_changed(self, term: str):
        self.model.set_highlight_term(term)
        self._delegate.set_term(term)
        self.table_view.viewport().update()
        total = self.model.find_match_count()
        self._find_bar.set_match_info(self.model.find_current_match(), total)

    @Slot(int)
    def _on_find_navigate(self, direction: int):
        row = self.model.find_navigate(direction)
        if row >= 0:
            idx = self.model.index(row, 3)
            self.table_view.setCurrentIndex(idx)
            self.table_view.scrollTo(idx, QTableView.ScrollHint.PositionAtCenter)
        self._find_bar.set_match_info(
            self.model.find_current_match(), self.model.find_match_count()
        )

    @Slot()
    def _on_find_closed(self):
        self._delegate.set_term("")
        self.table_view.viewport().update()

    # ------------------------------------------------------------------
    # Feature 5: Copy to clipboard
    # ------------------------------------------------------------------

    def keyPressEvent(self, event):
        if (event.key() == Qt.Key.Key_C and
                event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            self._copy_selected_rows()
        else:
            super().keyPressEvent(event)

    def _copy_selected_rows(self):
        selected = self.table_view.selectedIndexes()
        if not selected:
            return
        # Collect unique rows
        rows = sorted(set(idx.row() for idx in selected))
        lines = []
        for row in rows:
            entry = self.model.get_entry_at_row(row)
            if entry:
                lines.append(entry.raw)
        if lines:
            QApplication.clipboard().setText("\n".join(lines))
            self.statusBar().showMessage(f"Copied {len(lines)} row(s) to clipboard", 2000)

    # ------------------------------------------------------------------
    # Feature 9: Font size (Ctrl + Scroll)
    # ------------------------------------------------------------------

    def eventFilter(self, obj, event):
        if obj is self.table_view.viewport():
            if event.type() == QEvent.Type.Wheel:
                if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                    delta = event.angleDelta().y()
                    self._zoom_font(1 if delta > 0 else -1)
                    return True
        return super().eventFilter(obj, event)

    def _zoom_font(self, delta: int):
        self._table_font_size = max(6, min(24, self._table_font_size + delta))
        self._apply_table_font()

    def _apply_table_font(self):
        font = QFont()
        font.setPointSize(self._table_font_size)
        self.table_view.setFont(font)
        self.table_view.verticalHeader().setDefaultSectionSize(self._table_font_size + 10)

    # ------------------------------------------------------------------
    # Export / Session (Feature 15)
    # ------------------------------------------------------------------

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

    def save_session(self):
        """Feature 15: Save all logs to a session file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Session", "", "Log Viewer Session (*.lvsession)"
        )
        if file_path:
            try:
                save_session(self.model.get_all_logs(), file_path)
                self.statusBar().showMessage(f"Session saved to {file_path}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Save Failed", str(e))

    def load_session(self):
        """Feature 15: Load logs from a session file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Session", "", "Log Viewer Session (*.lvsession)"
        )
        if file_path:
            try:
                entries = load_session(file_path)
                self.model.clear_logs()
                self.model.add_logs(entries)
                self.statusBar().showMessage(
                    f"Loaded {len(entries):,} log entries from session", 3000
                )
            except Exception as e:
                QMessageBox.critical(self, "Load Failed", str(e))

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    def open_settings(self):
        """Opens the settings dialog and applies any changes."""
        dialog = SettingsDialog(self.config, parent=self)
        if dialog.exec() != SettingsDialog.DialogCode.Accepted:
            return

        new_config = dialog.get_updated_config()

        # Detect if connection settings changed
        old_server = self.config.get("server", {})
        new_server = new_config.get("server", {})
        connection_changed = (
            old_server.get("host") != new_server.get("host") or
            old_server.get("port") != new_server.get("port")
        )

        # Save to TOML
        try:
            save_config_to_toml(new_config, DEFAULT_CONFIG_PATH)
        except Exception as e:
            QMessageBox.warning(self, "Save Failed", f"Could not save settings:\n{e}")

        # Apply new config
        self.config = new_config

        # Live-update colors in the model
        self.model.update_colors(new_config.get("colors", {}))

        # Restart receiver if connection settings changed
        if connection_changed:
            self.statusBar().showMessage("Restarting receiver on new host/port...", 3000)
            self.receiver_thread.stop()
            self.receiver_thread = ReceiverWorker(self.config, self.parser)
            self.receiver_thread.logs_received.connect(self.on_logs_received)
            self.receiver_thread.error_occurred.connect(self.on_error)
            self.receiver_thread.client_connected.connect(self._on_client_connected)
            self.receiver_thread.client_disconnected.connect(self._on_client_disconnected)
            self.receiver_thread.start()

    # ------------------------------------------------------------------
    # Window close
    # ------------------------------------------------------------------

    def closeEvent(self, event):
        self.receiver_thread.stop()
        super().closeEvent(event)
