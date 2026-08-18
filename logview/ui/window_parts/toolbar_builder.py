from PySide6.QtWidgets import QStyle, QToolBar, QToolButton


class ToolbarBuilder:
    """Builder for the main window toolbar."""

    def __init__(self, main_window):
        self.main_window = main_window
        self.toolbar = QToolBar("Main Toolbar")

        self.action_pause = None
        self.action_clear = None
        self.action_copy = None
        self.action_rel_time = None
        self.action_theme = None
        self.action_settings = None

        self._setup_toolbar()

    def _setup_toolbar(self):
        self.main_window.addToolBar(self.toolbar)

        self.action_pause = self.toolbar.addAction(
            self.main_window.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause), "Pause"
        )
        self.action_pause.setCheckable(True)
        self.action_pause.toggled.connect(self.main_window.toggle_pause)
        pause_btn = self.toolbar.widgetForAction(self.action_pause)
        if pause_btn:
            pause_btn.setAccessibleName("Pause logging")

        self.action_clear = self.toolbar.addAction(
            self.main_window.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon), "Clear"
        )
        self.action_clear.triggered.connect(self.main_window.clear_logs)
        clear_btn = self.toolbar.widgetForAction(self.action_clear)
        if clear_btn:
            clear_btn.setAccessibleName("Clear logs")

        self.action_copy = self.toolbar.addAction(
            self.main_window.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon), "Copy"
        )
        self.action_copy.setToolTip("Copy Selected Logs (Ctrl+C)")
        self.action_copy.triggered.connect(self.main_window._copy_selected_rows)
        copy_btn = self.toolbar.widgetForAction(self.action_copy)
        if copy_btn:
            copy_btn.setAccessibleName("Copy selected logs")

        self.toolbar.addSeparator()

        # Feature 14: Relative timestamp toggle
        self.action_rel_time = self.toolbar.addAction(
            self.main_window.style().standardIcon(QStyle.StandardPixmap.SP_DialogResetButton), "Relative Time"
        )
        self.action_rel_time.setCheckable(True)
        self.action_rel_time.setToolTip("Toggle relative timestamps (e.g. '2s ago')")
        self.action_rel_time.toggled.connect(self.main_window._on_relative_time_toggled)
        rel_time_btn = self.toolbar.widgetForAction(self.action_rel_time)
        if rel_time_btn:
            rel_time_btn.setAccessibleName("Toggle relative timestamps")

        self.toolbar.addSeparator()

        self.action_theme = self.toolbar.addAction(
            self.main_window.style().standardIcon(QStyle.StandardPixmap.SP_DesktopIcon), "Theme"
        )
        theme_btn = self.toolbar.widgetForAction(self.action_theme)
        if isinstance(theme_btn, QToolButton):
            theme_btn.setAccessibleName("Theme settings")
            theme_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
            if hasattr(self.main_window, "menu_builder") and self.main_window.menu_builder:
                theme_btn.setMenu(self.main_window.menu_builder.theme_menu)

        self.action_settings = self.toolbar.addAction(
            self.main_window.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView), "Settings"
        )
        self.action_settings.triggered.connect(self.main_window.open_settings)
        settings_btn = self.toolbar.widgetForAction(self.action_settings)
        if settings_btn:
            settings_btn.setAccessibleName("Open settings")
