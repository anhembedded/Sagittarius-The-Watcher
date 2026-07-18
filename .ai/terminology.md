# Terminology

This reference defines terms, widgets, and key concepts utilized in the Sagittarius LogViewer codebase.

## Core Concepts

- **LogEntry**: A standardized python data class representation of a log line. It separates raw data from structured attributes like level, timestamp, message, index, module, and submodule.
- **MultiLine Buffer / Incomplete Log**: Logging frameworks sometimes output stack traces or payloads across multiple lines. The `MultiLineBuffer` holds and reconstructs these lines into a single logical `LogEntry`.
- **Ingestion Stream**: The active connection or source providing log text. It can be a network socket, stdin pipe, or file.
- **Scroll Lock / Auto-Scroll**: When log ingestion is high, the UI normally scrolls to show the latest entry. Enabling "Scroll Lock" disables this auto-scroll behavior, allowing the user to inspect historical logs without them jumping out of view.

## Custom UI Elements

- **Heatmap Widget (`HeatmapWidget`)**: A custom drawing canvas rendered to the right of the log table. It paints color-coded rows matching the levels of visible and hidden logs in the table, acting as a density indicator for errors or warnings.
- **Bookmark**: A boolean state associated with a log entry row, toggled by double-clicking the bookmark column or pressing `B`. This allows developers to pin critical lines and filter out everything else.
- **Relative Time Mode**: Toggles timestamps from their absolute string representation to a computed relative offset (e.g., `+1.234s`) starting from the time the first log in the current session was parsed.
- **Find Bar**: An inline overlay component (similar to search bars in browsers) triggered by `Ctrl+F` allowing quick navigation, match highlights, and regex searching inside the log messages.
- **`.lvsession` File**: A JSON format serialization of the current log session including raw text, parsed timestamps, levels, messages, and state metadata.
