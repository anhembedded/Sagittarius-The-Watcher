import re
from typing import Any

from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QSplitter,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from logview.log_parser import LogParser
from logview.models import LogEntry
from logview.ui.components import FilterPanel, TimeRangeWidget
from logview.ui.components.detail_panel import DetailPanel
from logview.ui.components.heatmap_widget import LogHeatmapWidget
from logview.ui.find_bar import FindBar
from logview.ui.log_delegate import LogDelegate
from logview.ui.log_model import COL_MESSAGE, LogFilterProxyModel, LogModel
from logview.ui.receiver_worker import ReceiverWorker
from logview.ui.views.log_table import LogTableView


class LogTab(QWidget):
    def __init__(self, config: dict[str, Any], main_window, parent=None):
        super().__init__(parent)
        self.config = config
        self.main_window = main_window
        self.is_paused = False
        self.pending_logs: list[LogEntry] = []
        self._log_rate_counter = 0

        self.parser = LogParser(config.get("log_format", {}).get("pattern", ""))
        self.source_model = LogModel(
            self, max_lines=config.get("display", {}).get("max_lines", 10000), color_config=config.get("colors", {})
        )
        self.model = LogFilterProxyModel(self)
        self.model.setSourceModel(self.source_model)
        self.model.counts_changed.connect(self._on_counts_changed)

        self.receiver_thread = ReceiverWorker(self.config, self.parser)
        self.receiver_thread.logs_received.connect(self.on_logs_received)
        self.receiver_thread.error_occurred.connect(main_window.on_error)
        self.receiver_thread.client_connected.connect(main_window._on_client_connected)
        self.receiver_thread.client_disconnected.connect(main_window._on_client_disconnected)
        self.receiver_thread.start()

        # UI Setup
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

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

        # Table View Container to place table side-by-side with Minimap Heatmap
        table_container = QWidget()
        table_container_layout = QHBoxLayout(table_container)
        table_container_layout.setContentsMargins(0, 0, 0, 0)
        table_container_layout.setSpacing(2)

        # Table View
        self.table_view = LogTableView(self)
        self.table_view.setModel(self.model)
        table_container_layout.addWidget(self.table_view)

        # Scrollbar minimap / heatmap widget
        self.heatmap_widget = LogHeatmapWidget(self.model, self.table_view, self)
        table_container_layout.addWidget(self.heatmap_widget)

        # Floating "Resume Tail" button
        self.resume_button = QPushButton("↓ Resume Tailing", self.table_view)
        self.resume_button.setObjectName("resume_tail_button")
        self.resume_button.setVisible(False)
        self.resume_button.clicked.connect(self._on_resume_clicked)
        self.resume_button.setStyleSheet("""
            QPushButton#resume_tail_button {
                background-color: rgba(38, 162, 105, 210); /* Sleek green matching INFO */
                color: white;
                border: none;
                border-radius: 12px;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton#resume_tail_button:hover {
                background-color: rgba(38, 162, 105, 255);
            }
        """)

        # Setup log delegate for the entire table view to handle custom row colors overriding themes
        self._delegate = LogDelegate(self.table_view)
        self.table_view.setItemDelegate(self._delegate)

        # Column widths (ensuring no truncation for ISO timestamps, module names & headers)
        self.table_view.setColumnWidth(0, 32)  # Bookmark
        self.table_view.setColumnWidth(1, 70)  # Index
        self.table_view.setColumnWidth(2, 220)  # Timestamp
        self.table_view.setColumnWidth(3, 90)  # Level
        self.table_view.setColumnWidth(4, 150)  # Module
        self.table_view.setColumnWidth(5, 150)  # Submodule

        self.main_window._apply_table_font_to_view(self.table_view)

        splitter.addWidget(table_container)

        # Feature 2: Detail Panel
        self._detail_panel = DetailPanel()
        if hasattr(self.main_window, "_show_detail_panel"):
            self._detail_panel.setVisible(self.main_window._show_detail_panel)
        splitter.addWidget(self._detail_panel)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

        # Connect selection to detail panel
        self.table_view.selectionModel().currentRowChanged.connect(self._on_row_selected)
        # Connect scrollbar for auto-scroll
        self.table_view.verticalScrollBar().valueChanged.connect(self._on_scroll)

        self.auto_scroll = True
        self.scroll_timer = QTimer(self)
        self.scroll_timer.timeout.connect(self.check_autoscroll)
        self.scroll_timer.start(200)

    def stop(self):
        self.receiver_thread.stop()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reposition_resume_button()

    def _reposition_resume_button(self):
        if hasattr(self, "resume_button") and self.resume_button.isVisible():
            btn_w = self.resume_button.width()
            btn_h = self.resume_button.height()
            view_w = self.table_view.width()
            view_h = self.table_view.height()

            # Align with bottom right corner, above scrollbars if visible
            scrollbar_h = (
                self.table_view.horizontalScrollBar().height()
                if self.table_view.horizontalScrollBar().isVisible()
                else 0
            )
            scrollbar_w = (
                self.table_view.verticalScrollBar().width() if self.table_view.verticalScrollBar().isVisible() else 0
            )

            x = view_w - btn_w - 20 - scrollbar_w
            y = view_h - btn_h - 20 - scrollbar_h
            self.resume_button.move(x, y)

    @Slot()
    def _on_resume_clicked(self):
        self.auto_scroll = True
        self.table_view.scrollToBottom()
        if hasattr(self, "resume_button"):
            self.resume_button.setVisible(False)

    @Slot(dict)
    def _on_counts_changed(self, counts: dict):
        if self.main_window.tab_widget.currentWidget() == self:
            self.main_window.stats_panel.update_counts(counts)
            self.main_window._update_level_counts(counts)

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
            idx = self.model.index(row, COL_MESSAGE)
            self.table_view.setCurrentIndex(idx)
            self.table_view.scrollTo(idx, LogTableView.ScrollHint.PositionAtCenter)
        self._find_bar.set_match_info(self.model.find_current_match(), self.model.find_match_count())

    @Slot()
    def _on_find_closed(self):
        self._delegate.set_term("")
        self.table_view.viewport().update()

    @Slot(list)
    def on_logs_received(self, logs: list[LogEntry]):
        self._log_rate_counter += len(logs)
        if self.is_paused:
            self.pending_logs.extend(logs)
        else:
            self.model.add_logs(logs)
        self.main_window._update_status()

        # Feature 3: Real-time Notification Alerts
        if self.main_window.tray_icon:
            alert_pattern = self.config.get("alerts", {}).get("pattern", "")
            if alert_pattern:
                try:
                    regex = re.compile(alert_pattern, re.IGNORECASE)
                    for log in logs:
                        if regex.search(log.raw):
                            self.main_window.tray_icon.showMessage(
                                "Log Alert",
                                f"Alert matched in log: {(log.message or log.raw)[:100]}",
                                QSystemTrayIcon.MessageIcon.Warning,
                                2000,
                            )
                except re.error:
                    pass

    @Slot()
    def _on_row_selected(self, current, previous):
        row = current.row()
        entry = self.model.get_entry_at_row(row)
        self._detail_panel.update_details(entry)

    def _on_scroll(self, value: int):
        scrollbar = self.table_view.verticalScrollBar()
        # Robust Scroll Threshold: Disable autoscroll if scrolled up more than 10 pixels
        self.auto_scroll = value >= scrollbar.maximum() - 10
        if hasattr(self.main_window, "status_bar"):
            # "Scroll Lock: ON" means auto_scroll is disabled (user is scrolling up).
            # "Scroll Lock: OFF" means auto_scroll is active.
            self.main_window.status_bar.set_scroll_lock(not self.auto_scroll)

        # Show/hide resume tail button
        if hasattr(self, "resume_button"):
            self.resume_button.setVisible(not self.auto_scroll)
            self._reposition_resume_button()

    def check_autoscroll(self):
        if self.auto_scroll and not self.is_paused:
            self.table_view.scrollToBottom()

    def clear_logs(self):
        self.model.clear_logs()
        self.pending_logs.clear()
        self._detail_panel.clear()
        self.main_window._update_status()
