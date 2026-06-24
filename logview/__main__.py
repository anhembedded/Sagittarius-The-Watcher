import sys
from PySide6.QtWidgets import QApplication

from logview.ui.main_window import MainWindow
from logview.config import get_config

def main():
    """Entry point for the Log Viewer application."""
    config = get_config()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # MVC Pattern: Set up the main window (View/Controller)
    window = MainWindow(config)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
