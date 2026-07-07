import sys
from typing import Dict, Any, List, Optional

from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget,
    QFileDialog, QMessageBox, QSplitter,
    QApplication, QDockWidget, QStyle, QSystemTrayIcon,
    QTabWidget
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QKeySequence, QShortcut, QGuiApplication, QFont

from logview.ui.log_model import LogModel
from logview.ui.log_delegate import LogDelegate
from logview.ui.find_bar import FindBar
from logview.ui.components import FilterPanel, TimeRangeWidget
from logview.ui.settings_dialog import SettingsDialog, save_config_to_toml
from logview.log_parser import LogParser
from logview.export import export_logs, save_session, load_session
from logview.models import LogEntry
from logview.config import DEFAULT_CONFIG_PATH
from logview.ui.receiver_worker import ReceiverWorker
from logview.ui.charts_panel import LiveStatsPanel
from logview.ui.window_parts.menu_builder import MenuBuilder
from logview.ui.window_parts.toolbar_builder import ToolbarBuilder
from logview.ui.window_parts.status_bar import LogStatusBar
from logview.ui.views.log_table import LogTableView
from logview.ui.components.detail_panel import DetailPanel


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

        self._table_font_size = 10          # Feature 9: current font point size
        self._connected_clients: int = 0    # Feature 1: active client count

        # Setup UI
        self.menu_builder = MenuBuilder(self)
        self._setup_ui()
        self.status_bar = LogStatusBar(self)
        self.setStatusBar(self.status_bar)

        self.is_dark_theme = QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark
        self._apply_theme()
        QGuiApplication.styleHints().colorSchemeChanged.connect(self._on_color_scheme_changed)



        # System Tray for Alerts (Feature 3)
        self.tray_icon = None
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon), self)
            self.tray_icon.show()

        # Auto-scroll state is now on tab
        self.auto_scroll = True

        # Feature 1: Rate counter timer (1s tick)
        self._rate_timer = QTimer(self)
        self._rate_timer.timeout.connect(self._update_rate_display)
        self._rate_timer.start(1000)

        # Feature 6: Level counts


        # 📊 Live Statistics & Charts Panel
        self.stats_dock = QDockWidget("Live Statistics", self)
        self.stats_panel = LiveStatsPanel(self.stats_dock)
        self.stats_dock.setWidget(self.stats_panel)
        self.stats_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.stats_dock)

        from logview.ui.components.log_tab import LogTab
        self.add_source_tab("Source 1", self.config)

        # Install event filter for Ctrl+Scroll zoom (Feature 9)

        # Ctrl+F shortcut (Feature 3)
        find_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        find_shortcut.activated.connect(self._toggle_find_bar)

        # Update initial status
        self._update_status()

    def change_theme(self, name: str):
        if "theme" not in self.config:
            self.config["theme"] = {}
        self.config["theme"]["name"] = name
        save_config_to_toml(self.config, DEFAULT_CONFIG_PATH)
        self._apply_theme()

        if hasattr(self, "menu_builder") and hasattr(self.menu_builder, "theme_group"):
            for act in self.menu_builder.theme_group.actions():
                if act.text().lower().startswith(name.lower()):
                    act.setChecked(True)
                    break

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def _setup_style(self):
        pass

    @Slot(Qt.ColorScheme)
    def _on_color_scheme_changed(self, scheme: Qt.ColorScheme):
        self.is_dark_theme = scheme == Qt.ColorScheme.Dark
        self._apply_theme()

    def _apply_theme(self):
        theme_name = self.config.get("theme", {}).get("name", "auto")
        app = QApplication.instance()
        if not app:
            return

        import qdarktheme

        app.setStyleSheet("")
        self.setStyleSheet("")

        if theme_name in ("auto", "dark", "light"):
            if theme_name == "auto":
                theme_str = "dark" if self.is_dark_theme else "light"
            else:
                theme_str = theme_name

            app.setStyleSheet(qdarktheme.load_stylesheet(theme_str))
            app.setPalette(qdarktheme.load_palette(theme_str))
        else:
            try:
                from qt_material import apply_stylesheet
                apply_stylesheet(app, theme=theme_name)
            except Exception as e:
                # Fallback to auto if qt-material fails
                print(f"Error applying qt-material theme {theme_name}: {e}")
                theme_str = "dark" if self.is_dark_theme else "light"
                app.setStyleSheet(qdarktheme.load_stylesheet(theme_str))
                app.setPalette(qdarktheme.load_palette(theme_str))

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def add_source_tab(self, name: str, config: Dict[str, Any]):
        from logview.ui.components.log_tab import LogTab
        tab = LogTab(config, self)
        self.tab_widget.addTab(tab, name)

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.toolbar_builder = ToolbarBuilder(self)

        # Feature 5: Multi-Source Tabbed Interface
        self.tab_widget = QTabWidget()
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        main_layout.addWidget(self.tab_widget)


    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------



    def toggle_pause(self, paused: bool):
        tab = self.tab_widget.currentWidget()
        if tab: tab.is_paused = paused
        if paused:
            self.toolbar_builder.action_pause.setIcon(
                self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
            )
            self.toolbar_builder.action_pause.setText("Resume")
        else:
            self.toolbar_builder.action_pause.setIcon(
                self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause)
            )
            self.toolbar_builder.action_pause.setText("Pause")
            tab = self.tab_widget.currentWidget()
            if tab and tab.pending_logs:
                tab.model.add_logs(tab.pending_logs)
                tab.pending_logs.clear()
                self._update_status()

    def clear_logs(self):
        tab = self.tab_widget.currentWidget()
        if tab:
            tab.clear_logs()

    @Slot(int)
    def _on_tab_changed(self, index: int):
        tab = self.tab_widget.widget(index)
        if tab:
            self._update_status()
            tab._on_counts_changed(tab.model.get_level_counts())

    @Slot(str)
    def on_error(self, message: str):
        self.statusBar().showMessage(f"Error: {message}", 5000)

    @Slot(str)
    def _on_client_connected(self, addr: str):
        self._connected_clients += 1
        self.status_bar.set_client_connected(addr)

    @Slot(str)
    def _on_client_disconnected(self, addr: str):
        self._connected_clients = max(0, self._connected_clients - 1)
        if self._connected_clients == 0:
            self.status_bar.set_client_disconnected()





    # Feature 2: Detail panel


    # Feature 14: Relative time
    def _on_relative_time_toggled(self, checked: bool):
        tab = self.tab_widget.currentWidget()
        if tab: tab.model.toggle_relative_time()

    # ------------------------------------------------------------------
    # Feature 1: Status bar updates
    # ------------------------------------------------------------------

    def _update_status(self):
        tab = self.tab_widget.currentWidget()
        if tab:
            total = len(tab.model.get_all_logs())
            shown = tab.model.get_filtered_count()
            pending = len(tab.pending_logs)
            self.status_bar.update_status(total, shown, pending)

    def _update_rate_display(self):
        rate = 0
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if tab:
                rate += tab._log_rate_counter
                tab._log_rate_counter = 0
        self.status_bar.update_rate_display(rate)

    @Slot(dict)
    def _update_level_counts(self, counts: dict):
        """Feature 6: Update level badges in status bar."""
        self.status_bar.update_level_counts(counts)
        self._update_status()

    # ------------------------------------------------------------------
    # Feature 3: Find bar
    # ------------------------------------------------------------------

    def _toggle_find_bar(self):
        tab = self.tab_widget.currentWidget()
        if tab:
            if tab._find_bar.isVisible():
                tab._find_bar.close_bar()
            else:
                tab._find_bar.open()

    @Slot(str, bool)
    def _on_find_term_changed(self, term: str, use_regex: bool):
        self.model.set_highlight_term(term, use_regex)
        self._delegate.set_term(term, use_regex)
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
        tab = self.tab_widget.currentWidget()
        if not tab: return
        selected = tab.table_view.selectedIndexes()
        if not selected:
            return
        # Collect unique rows
        rows = sorted(set(idx.row() for idx in selected))
        lines = []
        for row in rows:
            entry = tab.model.get_entry_at_row(row)
            if entry:
                lines.append(entry.raw)
        if lines:
            QApplication.clipboard().setText("\n".join(lines))
            self.statusBar().showMessage(f"Copied {len(lines)} row(s) to clipboard", 2000)

    def _copy_selected_messages(self):
        tab = self.tab_widget.currentWidget()
        if not tab: return
        selected = tab.table_view.selectedIndexes()
        if not selected:
            return
        rows = sorted(set(idx.row() for idx in selected))
        lines = []
        for row in rows:
            entry = tab.model.get_entry_at_row(row)
            if entry:
                lines.append(entry.message)
        if lines:
            QApplication.clipboard().setText("\n".join(lines))
            self.statusBar().showMessage(f"Copied {len(lines)} message(s) to clipboard", 2000)

    # ------------------------------------------------------------------
    # Feature 9: Font size (Ctrl + Scroll)
    # ------------------------------------------------------------------

    def _zoom_font(self, delta: int):
        self._table_font_size = max(6, min(24, self._table_font_size + delta))
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if tab:
                self._apply_table_font_to_view(tab.table_view)

    def _apply_table_font_to_view(self, table_view):
        font = QFont()
        font.setPointSize(self._table_font_size)
        table_view.setFont(font)
        table_view.verticalHeader().setDefaultSectionSize(self._table_font_size + 10)

    # ------------------------------------------------------------------
    # Export / Session (Feature 15)
    # ------------------------------------------------------------------

    def export_logs(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Logs", "", "Log Files (*.log);;JSON Files (*.json)"
        )
        if file_path:
            try:
                tab = self.tab_widget.currentWidget()
                if not tab: return
                logs_to_export = tab.model.get_all_logs()
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
                tab = self.tab_widget.currentWidget()
                if not tab: return
                save_session(tab.model.get_all_logs(), file_path)
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
                tab = self.tab_widget.currentWidget()
                if not tab: return
                tab.model.clear_logs()
                tab.model.add_logs(entries)
                self.statusBar().showMessage(
                    f"Loaded {len(entries):,} log entries from session", 3000
                )
            except Exception as e:
                QMessageBox.critical(self, "Load Failed", str(e))

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------


    def _on_new_source_tab(self):
        import copy
        new_config = copy.deepcopy(self.config)
        # We can prompt the user for a new port, but to keep it under 50 lines without creating a new dialog class,
        # we can just increment the default port and let them change it in settings.
        current_port = new_config.get("server", {}).get("port", 9999)
        new_config["server"]["port"] = current_port + self.tab_widget.count()
        name = f"Source {self.tab_widget.count() + 1} (Port {new_config['server']['port']})"
        self.add_source_tab(name, new_config)

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

        format_changed = self.config.get("log_format", {}).get("pattern") != new_config.get("log_format", {}).get("pattern")
        alerts_changed = self.config.get("alerts", {}).get("pattern") != new_config.get("alerts", {}).get("pattern")

        # Save to TOML
        try:
            save_config_to_toml(new_config, DEFAULT_CONFIG_PATH)
        except Exception as e:
            QMessageBox.warning(self, "Save Failed", f"Could not save settings:\n{e}")

        # Apply new config
        self.config = new_config

        # Live-update colors in the model
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if tab: tab.model.update_colors(new_config.get("colors", {}))

        # Restart receiver if connection settings changed
        if connection_changed or format_changed or alerts_changed:
            self.statusBar().showMessage("Restarting receiver for new settings...", 3000)
            tab = self.tab_widget.currentWidget()
            if tab:
                tab.stop()
                from logview.ui.receiver_worker import ReceiverWorker
                from logview.log_parser import LogParser
                # only apply to current tab
                tab.config = self.config
                tab.parser = LogParser(self.config.get("log_format", {}).get("pattern", ""))
                tab.receiver_thread = ReceiverWorker(tab.config, tab.parser)
                tab.receiver_thread.logs_received.connect(tab.on_logs_received)
                tab.receiver_thread.error_occurred.connect(self.on_error)
                tab.receiver_thread.client_connected.connect(self._on_client_connected)
                tab.receiver_thread.client_disconnected.connect(self._on_client_disconnected)
                tab.receiver_thread.start()

    # ------------------------------------------------------------------
    # Window close
    # ------------------------------------------------------------------

    def closeEvent(self, event):
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if tab:
                tab.stop()
        super().closeEvent(event)
