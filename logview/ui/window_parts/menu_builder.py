from PySide6.QtGui import QAction, QKeySequence, QActionGroup

from logview.ui.settings_dialog import save_config_to_toml
from logview.config import DEFAULT_CONFIG_PATH

class MenuBuilder:
    """Builder for the main window menu bar."""

    def __init__(self, main_window):
        self.main_window = main_window
        self.config = main_window.config
        self.theme_menu = None
        self.theme_group = None
        self._setup_menu()

    def _setup_menu(self):
        menu_bar = self.main_window.menuBar()

        file_menu = menu_bar.addMenu("File")

        act_new_tab = QAction("New Source Tab…", self.main_window)
        act_new_tab.setShortcut(QKeySequence("Ctrl+T"))
        act_new_tab.triggered.connect(self.main_window._on_new_source_tab)
        file_menu.addAction(act_new_tab)

        file_menu.addSeparator()

        act_save = QAction("Save Session…", self.main_window)
        act_save.setShortcut(QKeySequence("Ctrl+S"))
        act_save.triggered.connect(self.main_window.save_session)
        file_menu.addAction(act_save)

        act_load = QAction("Load Session…", self.main_window)
        act_load.setShortcut(QKeySequence("Ctrl+O"))
        act_load.triggered.connect(self.main_window.load_session)
        file_menu.addAction(act_load)

        file_menu.addSeparator()

        act_export = QAction("Export Logs…", self.main_window)
        act_export.triggered.connect(self.main_window.export_logs)
        file_menu.addAction(act_export)

        # View Menu
        view_menu = menu_bar.addMenu("View")

        act_toggle_toolbar = QAction("Toggle Toolbar", self.main_window)
        act_toggle_toolbar.setCheckable(True)
        act_toggle_toolbar.setChecked(True)
        act_toggle_toolbar.toggled.connect(self.main_window.toggle_toolbar)
        view_menu.addAction(act_toggle_toolbar)

        act_toggle_status_bar = QAction("Toggle Status Bar", self.main_window)
        act_toggle_status_bar.setCheckable(True)
        act_toggle_status_bar.setChecked(True)
        act_toggle_status_bar.toggled.connect(self.main_window.toggle_status_bar)
        view_menu.addAction(act_toggle_status_bar)

        act_toggle_detail_panel = QAction("Toggle Detail Panel", self.main_window)
        act_toggle_detail_panel.setCheckable(True)
        act_toggle_detail_panel.setChecked(True)
        act_toggle_detail_panel.toggled.connect(self.main_window.toggle_detail_panel)
        view_menu.addAction(act_toggle_detail_panel)

        view_menu.addSeparator()

        if hasattr(self.main_window, 'stats_dock') and self.main_window.stats_dock:
            act_toggle_stats = self.main_window.stats_dock.toggleViewAction()
            act_toggle_stats.setText("Live Statistics Panel")
            view_menu.addAction(act_toggle_stats)

        # Theme Menu
        self.theme_menu = menu_bar.addMenu("Theme")
        self.theme_group = QActionGroup(self.main_window)
        self.theme_group.setExclusive(True)

        current_theme = self.config.get("theme", {}).get("name", "auto")

        def add_theme_action(name, display_name, parent_menu):
            act = QAction(display_name, self.main_window)
            act.setCheckable(True)
            if name == current_theme:
                act.setChecked(True)
            # Use default parameter value to capture current 'name' value inside lambda
            act.triggered.connect(lambda checked=False, n=name: self.main_window.change_theme(n))
            self.theme_group.addAction(act)
            parent_menu.addAction(act)
            return act

        add_theme_action("auto", "System Default (Auto)", self.theme_menu)
        add_theme_action("dark", "PyQtDarkTheme (Dark)", self.theme_menu)
        add_theme_action("light", "PyQtDarkTheme (Light)", self.theme_menu)

        self.theme_menu.addSeparator()

        try:
            from qt_material import list_themes
            all_material = list_themes()
        except ImportError:
            all_material = []

        if all_material:
            dark_menu = self.theme_menu.addMenu("Material Dark Themes")
            light_menu = self.theme_menu.addMenu("Material Light Themes")

            for t in all_material:
                clean_name = t.replace(".xml", "").replace("_", " ").title()
                if t.startswith("dark_"):
                    add_theme_action(t, clean_name, dark_menu)
                else:
                    add_theme_action(t, clean_name, light_menu)
