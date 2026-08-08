import sys
from PySide6.QtWidgets import QApplication

from sagittarius_engine.kernel.app import App
from sagittarius_engine.infrastructure.container.std_container import StdLibContainer
from sagittarius_engine.infrastructure.event_bus.memory_event_bus import MemoryEventBus
from sagittarius_engine.interfaces.i_config import IConfig
from sagittarius_engine.interfaces.i_event_bus import IEventBus
from sagittarius_engine.infrastructure.config.config_manager import ConfigManager

from logview.ui.main_window import MainWindow
from logview.log_viewer_module import LogViewerModule
import logview.config

def create_app(config_manager: ConfigManager, is_test: bool = False) -> App:
    container = StdLibContainer()
    event_bus = MemoryEventBus()
    
    container.singleton(IEventBus, event_bus)
    container.singleton(IConfig, config_manager)
    
    app = App(container, event_bus)
    app.use(LogViewerModule())
    return app

def main():
    """Entry point for the Log Viewer application."""
    qt_app = QApplication(sys.argv)
    qt_app.setStyle("Fusion")
    
    # Engine Setup
    config_manager = ConfigManager()
    # Load default configs
    config = logview.config.get_config()
    for key, val in config.items():
        config_manager.set(key, val)

    engine_app = create_app(config_manager)
    engine_app.boot()

    # Resolve main window
    window = engine_app.context.container.resolve(MainWindow)
    window.show()

    # On exit
    exit_code = qt_app.exec()
    engine_app.stop()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
