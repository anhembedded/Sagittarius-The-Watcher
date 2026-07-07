Mapping out user journeys before writing a single line of Pytest code is the exact right move. When architecting UI automation tools or writing software requirement specs, establishing these behavioral baselines ensures your Unit and Integration tests actually validate what the user experiences, rather than just testing implementation details.

Here is a comprehensive matrix of User Acceptance Testing (UAT) scenarios for the Log Viewer, categorized by feature. You can use these exact scenarios to script your `pytest-qt` (for UI) and `pytest-asyncio` (for backend) integration tests.

### 1. Data Ingestion & Tab Management

This covers how the user interacts with incoming log streams and manages multiple sources.

| Scenario | User Action | Expected Result |
| --- | --- | --- |
| **TCP Connection** | Launch app with TCP port configured. Send log line via TCP client. | Log line appears in the table immediately. Status bar shows "Connected" and increments "Total" count. |
| **File Tailing** | Launch app targeting a file. Append text to the file. | Log line appears in the table. |
| **Pause Stream** | Click the "Pause" button on the toolbar while logs are streaming in. | Table stops updating. "Pending Buffer" count in the status bar increases. |
| **Resume Stream** | Click the "Resume" button. | All pending logs flush into the table at once. "Pending Buffer" drops to 0. |
| **Auto-Scroll** | Receive continuous logs without touching the scrollbar. | Table automatically scrolls to keep the newest log visible at the bottom. |
| **Manual Scroll Break** | Scroll up slightly while logs are streaming in. | Auto-scroll stops, allowing the user to read older logs while new ones append silently. |
| **New Source Tab** | Go to File > New Source Tab. | A new tab opens with an incremented port number, ready to listen for a separate stream. |

### 2. Filtering Engine (The Core Logic)

This verifies that the user can isolate the exact logs they need.

| Scenario | User Action | Expected Result |
| --- | --- | --- |
| **Level Filtering** | Select "ERROR" from the Level dropdown. | Only logs with the ERROR level (or logs completely missing a level) are displayed. Status bar "Shown" updates. |
| **Standard Text Filter** | Type "timeout" in the Search input. | Table updates to show only rows containing the word "timeout" (case-insensitive). |
| **Regex Text Filter** | Check "Regex" and type `error\s+\d+` in the Search input. | Table updates to show only rows matching the regular expression. |
| **Time Range Enable** | Check the "Time range" box and set a Start/End time. | Table filters to show only logs parsed within that specific time window. |
| **Combined Filters** | Set Level to "WARNING" AND type "memory" in Search. | Table shows only WARNING logs that also contain the word "memory". |

### 3. Find, Navigate & Highlight

This covers the Ctrl+F functionality and inline highlighting.

| Scenario | User Action | Expected Result |
| --- | --- | --- |
| **Open Find Bar** | Press `Ctrl+F`. | Find bar appears at the top of the log table. Focus is immediately on the text input. |
| **Highlight Text** | Type a keyword in the Find bar. | All occurrences of that keyword in the "Message" column are highlighted with a colored background. |
| **Next/Prev Navigation** | Click the Up/Down arrows (or press Enter / Shift+Enter). | The table scrolls to center the next/previous matched row. The match counter updates (e.g., "2/5"). |
| **Close Find Bar** | Press `Esc` or click the "X" button. | Find bar hides, and all background highlighting is removed from the table. |

### 4. Detail Panel & UI Interactivity

This ensures the user can inspect logs comfortably and customize their view.

| Scenario | User Action | Expected Result |
| --- | --- | --- |
| **Inspect Log Details** | Click a row in the log table. | The Detail Panel at the bottom populates with formatted Timestamp, Level, and Message. |
| **JSON Pretty Print** | Click a row where the raw log is a JSON string. | The Detail Panel automatically parses and formats the JSON with indentation for readability. |
| **Relative Time Toggle** | Click the "Relative Time" toolbar button. | Timestamps change from absolute (e.g., `2023-10-27 10:00:00`) to relative (e.g., `5s ago`). |
| **Font Zooming** | Hold `Ctrl` and scroll the mouse wheel over the table. | The font size of the table and the row heights scale up or down accordingly. |
| **Copy Selected** | Select multiple rows and press `Ctrl+C`. | The raw log strings for all selected rows are copied to the system clipboard. |
| **Theme Switching** | Go to Theme menu and select a different theme (e.g., Dark to Light). | The entire application UI updates to the new color scheme without requiring a restart. |

### 5. Session Management, Export & Settings

This tests data persistence and application configuration.

| Scenario | User Action | Expected Result |
| --- | --- | --- |
| **Export to Text** | Go to File > Export Logs and save as `.log`. | A plain text file is created containing the raw strings of all currently held logs. |
| **Save Session** | Go to File > Save Session and save as `.lvsession`. | A JSON-structured session file is saved to disk containing parsed log states. |
| **Load Session** | Go to File > Load Session and open a `.lvsession` file. | The current table clears and populates with the logs from the saved session file. |
| **Test Custom Regex** | Open Settings > Log Format, type a custom regex, input a sample log, and click "Test". | The UI displays "Match found!" in green, listing the extracted capture groups. |
| **Change Colors** | Open Settings > Colors, change the background color for "ERROR", and save. | The table immediately repaints existing ERROR logs with the newly selected background color. |

---

These user journeys provide a solid blueprint for your testing strategy. Which area would you like to tackle first: setting up the `pytest-qt` fixtures to simulate UI clicks, or writing the integration tests for the asynchronous backend receiver?