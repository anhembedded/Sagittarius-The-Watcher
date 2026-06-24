import sys
from logview.ui.app import LogViewerApp

def main():
    """Entry point for the Log Viewer application."""
    app = LogViewerApp()
    app.run()

if __name__ == "__main__":
    main()
