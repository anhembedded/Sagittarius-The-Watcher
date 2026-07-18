# Sagittarius LogViewer - Project Knowledge Base

This document serves as the high-level entry point and single source of truth for the Sagittarius LogViewer project.

## Vision
Sagittarius LogViewer is a highly responsive, real-time log ingestion and desktop viewer application built with **PySide6 (Qt for Python)**. It is designed to aggregate, parse, filter, and inspect structured log streams (such as TCP socket streams, standard input, or active files) dynamically.

## Design Philosophy
- **Responsive Ingestion**: Log receiving and parsing are offloaded to an asynchronous background worker (`QThread` utilizing Python's `asyncio` event loop) to ensure the UI thread remains completely responsive even under heavy log ingestion rates.
- **Model-View Architecture**: Employs Qt's Model-View pattern (`QAbstractTableModel` and `QSortFilterProxyModel`) for high-performance rendering, searching, and filtering of log records.
- **Extensible & Configurable**: Every aspect of the viewer, from log parsing rules (via regex patterns with named capturing groups) to level-based styling colors and visual themes, is configurable using TOML.

## Key System Modules
- **`logview`**: Main application package.
  - **`controllers`**: Core business logic modules (e.g., filtering engine).
  - **`ui`**: UI components, views, dialogs, and main layout structure.
  - **`models.py`**: Shared log structures and models.
  - **`log_parser.py`**: Parsing engine supporting custom regex formats and JSON logs.
  - **`receiver.py`**: Abstracted ingestion streams (TCP/stdin/File).
