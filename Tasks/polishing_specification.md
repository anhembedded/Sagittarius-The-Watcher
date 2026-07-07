# Specification: Polishing Existing Features (Sagittarius Log Viewer)

This document outlines gaps in the current implementation of existing features and provides a detailed specification to complete and polish them.

---

## 1. 📊 Live Statistics Panel (QDockWidget)
### Gaps
* **No Re-open Mechanism**: Once the "Live Statistics" dock widget is closed by clicking the `X` button, there is no way for the user to open it again without restarting the application.
* **Lack of Visibility Control**: No menu action or toolbar toggle exists to explicitly show/hide the dock.

### Specification & Fix
* **View Menu**: Add a "View" menu to the main menu bar.
* **Toggle View Action**: Add the built-in `self.stats_dock.toggleViewAction()` action to this menu. This checkable action automatically syncs its check state with the visibility of the dock.
```python
# In MainWindow._setup_menu() (logview/ui/main_window.py)
view_menu = menu_bar.addMenu("View")
act_toggle_stats = self.stats_dock.toggleViewAction()
act_toggle_stats.setText("Live Statistics")
view_menu.addAction(act_toggle_stats)
```

---

## 2. 🔖 Bookmark Navigation & Filters
### Gaps
* **Bookmarks are hard to find**: While users can check the bookmark column, there is no way to filter the log list to show *only* bookmarked rows, or jump between bookmarked logs.

### Specification & Fix
* **Bookmark Filter**: Add a checkable "Show Bookmarks Only" checkbox to the `FilterPanel` (`logview/ui/components/filter_panel.py`) or a toolbar action.
* **Model Filter update**: In `LogModel.set_filter()`, if "bookmarks only" is active, filter out any log entries whose ID is not in `self._bookmarks`.
* **Shortcut Keys**: Support `F2` to toggle bookmark on the current row, and `Shift+F2` / `Ctrl+F2` to jump to the next/previous bookmarked row.

---

## 3. 🔄 Connection Live-Restart
### Gaps
* **Manual Restart Warning**: In the Settings dialog, changing the connection host/port displays a note saying *"Changes take effect after restarting the receiver"*. If the user changes settings, they have to close/re-open or perform actions manually.

### Specification & Fix
* **Automatic Thread Restart**: When settings are accepted in `MainWindow.open_settings()` and `connection_changed` is `True`, automatically stop the active `ReceiverWorker` thread, re-instantiate it with the new configuration, and start it seamlessly.
```python
# In MainWindow.open_settings()
if connection_changed:
    self.statusBar().showMessage("Restarting receiver with new settings...", 3000)
    # Safely terminate old worker
    self.receiver_thread.stop()
    self.receiver_thread.wait()
    # Start new worker
    self.receiver_thread = ReceiverWorker(self.config, self.parser)
    # Re-connect signals...
    self.receiver_thread.start()
```

---

## 📜 4. Autoscroll Sensitivity & Scroll Lock indicator
### Gaps
* **No Visual Indicator**: Users don't know if Autoscroll is currently locked or unlocked until new logs arrive.
* **Threshold Sensitivity**: The scrollbar value change detection can sometimes trigger false autoscroll disables on fast log streams.

### Specification & Fix
* **Status Bar Indicator**: Add a small lock icon or text indicator (e.g. `[Scroll Lock: ON/OFF]`) to the status bar.
* **Robust Scroll Threshold**: Only disable autoscroll if the scrollbar is moved up by more than 10 pixels from the maximum bottom position:
```python
# In LogTab._on_scroll()
scrollbar = self.table_view.verticalScrollBar()
at_bottom = (scrollbar.maximum() - scrollbar.value()) < 10
self.auto_scroll = at_bottom
self._status_scroll_lock.setText("🔒 Auto-Scroll" if self.auto_scroll else "🔓 Scroll-Free")
```

---

## 📁 5. Robust Log Parser Error Handling
### Gaps
* **Regex Crashing**: If a user saves an invalid or corrupted regex pattern in settings, the application throws `re.error` exceptions, causing the receiver worker thread to crash.

### Specification & Fix
* **Regex Compilation Check**: In `LogParser` init (`logview/log_parser.py`), wrap `re.compile()` in a `try/except` block.
* **Raw Fallback**: If compilation fails, log the warning, set `self.pattern` to a fallback regex that matches anything (e.g. `^(?P<message>.*)`), and alert the user with a dialog or status warning so the application continues to run without crashing.
