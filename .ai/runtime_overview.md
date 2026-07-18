# Runtime Overview & Configuration

This document describes how the Sagittarius LogViewer runs, how logs are streamed, and how configuration is customized.

## 1. Execution Modes

The application runs using the `logview` module:
```pwsh
python -m logview [arguments]
```

### CLI Command Flags
- **`--host <str>`**: Set the host address for the TCP socket server (default: `localhost`).
- **`--port <int>`**: Set the port for the TCP socket server (default: `9999`).
- **`--listen-stdin`**: Tells the application to read log lines directly from Standard Input (`sys.stdin`) instead of running a TCP socket server.
- **`--tail-file <filepath>`**: Configures the app to tail an active file, reading new lines dynamically.

---

## 2. Configuration System (`logview.toml`)

All local preferences are saved to `logview.toml` in the project root. If the file is missing, it is created automatically with defaults.

### Primary Sections
- **`[server]`**: Details the network settings.
  ```toml
  host = "localhost"
  port = 9999
  ```
- **`[display]`**: Display limitations.
  ```toml
  max_lines = 10000
  ```
- **`[log_format]`**: Custom regex formatting with capture group names matching `LogEntry` fields.
  ```toml
  pattern = "^(?:\\[(?P<index>\\d+)\\])?\\s*\\[(?P<timestamp>.*?)\\]\\s*\\[(?P<level>\\w+)\\]..."
  ```
- **`[colors.<LEVEL>]`**: Level foreground (`fg`) and background (`bg`) colors.
- **`[theme]`**: Theme xml file name mapping to PySide6 styles (e.g., `dark_lightgreen.xml`).

---

## 3. UI Styling & Theme System
The UI utilizes the **Fusion** style base. In addition, it integrates:
- **`pyqtdarktheme`**: Real-time toggling between light and dark modes.
- **`qt-material`**: XML stylesheets for professional design and palettes.
- **Custom Fonts & Zoom**: Table fonts can be resized dynamically (via Ctrl + Mouse Scroll Wheel or status bar actions).
