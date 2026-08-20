# PROJECT CONTEXT

**Roots:**
- `C:\Users\hoang\Documents\Sagittarius_LogViewer`

**Pattern:** `*.py, *.ps1`
**Generated:** 2026-07-18 16:15:41

## Directory Tree: C:\Users\hoang\Documents\Sagittarius_LogViewer

```
Sagittarius_LogViewer
├── logview
│   ├── __main__.py
│   ├── config.py
│   ├── controllers
│   │   ├── __init__.py
│   │   └── filter_engine.py
│   ├── core
│   │   └── __init__.py
│   ├── export.py
│   ├── log_parser.py
│   ├── models.py
│   ├── receiver.py
│   └── ui
│       ├── __init__.py
│       ├── charts_panel.py
│       ├── components
│       │   ├── __init__.py
│       │   ├── detail_panel.py
│       │   ├── heatmap_widget.py
│       │   └── log_tab.py
│       ├── dialogs
│       │   └── __init__.py
│       ├── find_bar.py
│       ├── log_delegate.py
│       ├── log_model.py
│       ├── main_window.py
│       ├── receiver_worker.py
│       ├── settings_dialog.py
│       ├── views
│       │   ├── __init__.py
│       │   └── log_table.py
│       └── window_parts
│           ├── __init__.py
│           ├── menu_builder.py
│           ├── status_bar.py
│           └── toolbar_builder.py
├── start.ps1
├── test.ps1
├── tests
│   ├── conftest.py
│   ├── integration
│   │   ├── test_receiver.py
│   │   ├── test_ui.py
│   │   └── uat
│   │       ├── test_detail_panel.py
│   │       ├── test_filtering.py
│   │       ├── test_find_navigation.py
│   │       ├── test_ingestion.py
│   │       └── test_session_management.py
│   └── unit
│       ├── test_config.py
│       ├── test_export.py
│       ├── test_filter_engine.py
│       ├── test_log_generator.py
│       ├── test_log_parser.py
│       ├── test_models.py
│       ├── test_proxy_model.py
│       ├── test_receiver_delay.py
│       └── test_settings_dialog.py
└── tools
    ├── log_generator.py
    └── run_test_env.py
```

---

# FILE: logview\__main__.py

```python
import sys
from PySide6.QtWidgets import QApplication

from logview.ui.main_window import MainWindow
from logview.config import get_config

def main():
    
    config = get_config()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

window = MainWindow(config)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
``````

# FILE: logview\config.py

```python
import argparse
import os
from typing import Any, Dict

DEFAULT_CONFIG_PATH = "logview.toml"
DEFAULT_CONFIG_CONTENT = 

def parse_args() -> argparse.Namespace:
    
    parser = argparse.ArgumentParser(description="Log Viewer TUI")
    parser.add_argument("--host", type=str, help="TCP Server Host")
    parser.add_argument("--port", type=int, help="TCP Server Port")
    parser.add_argument("--listen-stdin", action="store_true", help="Listen from stdin instead of TCP")
    parser.add_argument("--tail-file", type=str, help="Path to a file to tail instead of TCP/stdin")
    return parser.parse_args()

def load_toml(path: str) -> Dict[str, Any]:
    
    try:
        import tomllib
        with open(path, "rb") as f:
            return tomllib.load(f)
    except ImportError:
        pass

    try:
        import tomli
        with open(path, "rb") as f:
            return tomli.load(f)
    except ImportError:
        pass

config = {}
    current_section = config
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("
                continue
            if line.startswith("[") and line.endswith("]"):
                section_name = line[1:-1].strip()
                config[section_name] = {}
                current_section = config[section_name]
            elif "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip()

                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                else:
                    try:
                        val = int(val)
                    except ValueError:
                        pass
                current_section[key] = val
    return config

def get_config() -> Dict[str, Any]:
    
    if not os.path.exists(DEFAULT_CONFIG_PATH):
        with open(DEFAULT_CONFIG_PATH, "w", encoding="utf-8") as f:
            f.write(DEFAULT_CONFIG_CONTENT)

    config = load_toml(DEFAULT_CONFIG_PATH)

    args = parse_args()

if "server" not in config:
        config["server"] = {"host": "localhost", "port": 9999}
    if "display" not in config:
        config["display"] = {"max_lines": 10000}
    if "log_format" not in config:
        config["log_format"] = {"pattern": r"^(?:\[(?P<timestamp>.*?)\])?\s*(?:\[(?P<level>\w+)\])?\s*(?:\[(?P<module>\w+)\])?\s*(?:\[(?P<submodule>\w+)\])?\s*(?P<message>.*)"}
    else:

pass

    if "colors" not in config:
        config["colors"] = {}

    if "theme" not in config:
        config["theme"] = {"name": "auto"}

if args.host is not None:
        config["server"]["host"] = args.host
    if args.port is not None:
        config["server"]["port"] = args.port
    config["listen_stdin"] = args.listen_stdin

    if args.tail_file is not None:
        config["tail_file"] = args.tail_file

    return config
``````

# FILE: logview\controllers\__init__.py

```python

``````

# FILE: logview\controllers\filter_engine.py

```python
import re
from typing import Optional, List
from datetime import datetime
from logview.models import LogEntry

class LogFilterEngine:

def __init__(self):
        self._filter_text = ""
        self._filter_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        self._filter_regex = False
        self._filter_from_dt: Optional[datetime] = None
        self._filter_to_dt: Optional[datetime] = None

    def set_text_filter(self, text: str, regex: bool):
        self._filter_text = text
        self._filter_regex = regex

    def set_level_filter(self, levels: List[str]):
        self._filter_levels = levels

    def set_time_range(self, from_dt: Optional[datetime], to_dt: Optional[datetime]):
        self._filter_from_dt = from_dt
        self._filter_to_dt = to_dt

    def matches(self, log: LogEntry) -> bool:

        if log.level is not None:
            if log.level.upper() not in self._filter_levels:
                return False

if self._filter_from_dt or self._filter_to_dt:
            if log.parsed_dt is None:
                return False
            dt = log.parsed_dt.replace(tzinfo=None) if log.parsed_dt.tzinfo else log.parsed_dt
            if self._filter_from_dt and dt < self._filter_from_dt:
                return False
            if self._filter_to_dt and dt > self._filter_to_dt:
                return False

if self._filter_text:
            text_to_search = log.raw
            if self._filter_regex:
                try:
                    if not re.search(self._filter_text, text_to_search):
                        return False
                except re.error:
                    return False
            else:
                if self._filter_text.lower() not in text_to_search.lower():
                    return False

        return True
``````

# FILE: logview\core\__init__.py

```python

``````

# FILE: logview\export.py

```python
from typing import List
import json
from datetime import datetime
from logview.models import LogEntry


def export_logs(entries: List[LogEntry], filepath: str, format: str = "log"):

    if format == "json":
        data = [{"timestamp": e.timestamp, "level": e.level, "message": e.message, "raw": e.raw} for e in entries]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    else:
        with open(filepath, "w", encoding="utf-8") as f:
            for entry in entries:
                f.write(entry.raw + "\n")


def save_session(entries: List[LogEntry], filepath: str):

    if not filepath.endswith(".lvsession"):
        filepath += ".lvsession"

    data = {
        "version": 1,
        "saved_at": datetime.now().isoformat(),
        "entries": [
            {
                "raw": e.raw,
                "timestamp": e.timestamp,
                "level": e.level,
                "message": e.message,
                "parsed_dt": e.parsed_dt.isoformat() if e.parsed_dt else None,
            }
            for e in entries
        ],
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_session(filepath: str) -> List[LogEntry]:

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    entries = []
    for item in data.get("entries", []):
        parsed_dt = None
        dt_str = item.get("parsed_dt")
        if dt_str:
            try:
                parsed_dt = datetime.fromisoformat(dt_str)
            except (ValueError, TypeError):
                pass
        entries.append(
            LogEntry(
                raw=item.get("raw", ""),
                timestamp=item.get("timestamp"),
                level=item.get("level"),
                message=item.get("message", ""),
                is_new=False,
                parsed_dt=parsed_dt,
            )
        )
    return entries
``````

# FILE: logview\log_parser.py

```python
import re
import json
from datetime import datetime
from typing import Optional
from logview.models import LogEntry

TIMESTAMP_FORMATS = [
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
    "%Y/%m/%d %H:%M:%S",
    "%d/%b/%Y:%H:%M:%S",
    "%d/%b/%Y:%H:%M:%S %z",
]

def _try_parse_datetime(ts_str: Optional[str]) -> Optional[datetime]:
    
    if not ts_str:
        return None
    try:
        return datetime.fromisoformat(ts_str)
    except (ValueError, TypeError):
        pass
    for fmt in TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(ts_str.strip(), fmt)
        except (ValueError, AttributeError):
            continue
    return None

class LogParser:

def __init__(self, pattern: str):
        
        try:
            self.pattern = re.compile(pattern)
        except re.error as e:
            import logging
            logging.warning(f"Invalid regex pattern '{pattern}': {e}. Falling back to raw regex.")
            from PySide6.QtWidgets import QMessageBox

from PySide6.QtWidgets import QApplication
            if QApplication.instance():
                QMessageBox.warning(
                    None,
                    "Invalid Log Format Regex",
                    f"The configured log format regex pattern is invalid:\n{e}\n\n"
                    "Falling back to a raw matching pattern to prevent application crash."
                )
            self.pattern = re.compile(r"^(?P<message>.*)")

    def parse(self, line: str) -> LogEntry:
        
        entry = LogEntry(raw=line)
        self.parse_fields(entry)
        return entry

    def parse_fields(self, entry: LogEntry):
        
        if entry.timestamp is not None or entry.level is not None:
            return

        parts = entry.raw.split("\n", 1)
        first_line = parts[0].rstrip('\r\n')
        continuation = parts[1] if len(parts) > 1 else ""

if first_line.startswith("{"):
            try:
                data = json.loads(first_line)
                ts_str = (data.get("timestamp") or data.get("time")
                          or data.get("ts") or data.get("datetime"))
                level_raw = (data.get("level") or data.get("lvl")
                             or data.get("severity") or data.get("levelname"))
                index_raw = (data.get("index") or data.get("idx"))
                module_raw = (data.get("module") or data.get("mod"))
                submodule_raw = (data.get("submodule") or data.get("submod"))
                msg = (data.get("message") or data.get("msg")
                       or data.get("text") or first_line)
                
                entry.timestamp = str(ts_str) if ts_str else None
                entry.level = str(level_raw).upper() if level_raw else None
                entry.index = str(index_raw) if index_raw is not None else None
                entry.module = str(module_raw) if module_raw else None
                entry.submodule = str(submodule_raw) if submodule_raw else None
                entry.message = str(msg)
                if continuation:
                    entry.message += "\n" + continuation
                entry.parsed_dt = _try_parse_datetime(entry.timestamp)
                return
            except (json.JSONDecodeError, AttributeError):
                pass

        match = self.pattern.match(first_line)

        if match:
            group_dict = match.groupdict()
            ts_str = group_dict.get("timestamp")
            entry.timestamp = ts_str
            entry.level = group_dict.get("level", "").upper() if group_dict.get("level") else None
            entry.index = group_dict.get("index")
            entry.module = group_dict.get("module")
            entry.submodule = group_dict.get("submodule")
            msg = group_dict.get("message", first_line)
            entry.message = msg
            if continuation:
                entry.message += "\n" + continuation
            entry.parsed_dt = _try_parse_datetime(ts_str)
            return

        entry.message = first_line
        if continuation:
            entry.message += "\n" + continuation

    def is_new_entry(self, line: str) -> bool:
        
        clean_line = line.rstrip('\r\n')
        return bool(self.pattern.match(clean_line)) or clean_line.startswith("{")

class MultiLineBuffer:

def __init__(self, parser: LogParser):
        self._parser = parser
        self._pending: Optional[LogEntry] = None

    def feed(self, line: str) -> Optional[LogEntry]:
        
        if self._parser.is_new_entry(line):
            prev = self._pending
            self._pending = LogEntry(raw=line)
            return prev
        else:
            clean = line.rstrip('\r\n')
            if self._pending is not None:
                self._pending.raw += "\n" + clean
            else:

                self._pending = LogEntry(raw=line)
            return None

    def flush(self) -> Optional[LogEntry]:
        
        prev = self._pending
        self._pending = None
        return prev
``````

# FILE: logview\models.py

```python
import itertools
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class LogEntry:
    raw: str
    timestamp: Optional[str] = None
    level: Optional[str] = None
    index: Optional[str] = None
    module: Optional[str] = None
    submodule: Optional[str] = None
    message: str = ""
    id: int = 0
    is_new: bool = True
    parsed_dt: Optional[datetime] = None

    _id_counter = itertools.count(1)

    def __post_init__(self):
        if self.id == 0:
            self.id = next(self._id_counter)
        self._raw_lower: Optional[str] = None

    @property
    def raw_lower(self) -> str:

        if self._raw_lower is None:
            self._raw_lower = self.raw.lower()
        return self._raw_lower
``````

# FILE: logview\receiver.py

```python
import asyncio
import sys
from typing import Optional

import os
import io

from logview.log_parser import LogParser, MultiLineBuffer

class FileTailReceiver:

def __init__(self, filepath: str, parser: LogParser, queue: asyncio.Queue):
        self.filepath = filepath
        self.parser = parser
        self.queue = queue
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        
        self._running = True
        self._task = asyncio.create_task(self._tail_file())

    async def stop(self):
        
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _put_entry(self, entry):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.parser.parse_fields, entry)
        await self.queue.put(entry)

    async def _tail_file(self):
        
        loop = asyncio.get_running_loop()
        buf = MultiLineBuffer(self.parser)

while self._running and not os.path.exists(self.filepath):
            await asyncio.sleep(0.5)

        if not self._running:
            return

        with open(self.filepath, 'r', encoding='utf-8', errors='replace') as f:

            f.seek(0, io.SEEK_END)

            idle_time = 0.0

            while self._running:
                line = await loop.run_in_executor(None, f.readline)
                if not line:
                    await asyncio.sleep(0.1)
                    idle_time += 0.1
                    if idle_time >= 0.2:
                        entry = buf.flush()
                        if entry:
                            await self._put_entry(entry)
                        idle_time = 0.0
                    continue

                idle_time = 0.0
                entry = buf.feed(line)
                if entry:
                    await self._put_entry(entry)

final = buf.flush()
        if final:
            await self._put_entry(final)

class TCPServerReceiver:

def __init__(self, host: str, port: int, parser: LogParser, queue: asyncio.Queue,
                 listen_stdin: bool = False):
        
        self.host = host
        self.port = port
        self.parser = parser
        self.queue = queue
        self.listen_stdin = listen_stdin
        self.server: Optional[asyncio.AbstractServer] = None
        self._running = False

self.on_client_connected = None
        self.on_client_disconnected = None

    async def start(self):
        
        self._running = True
        if self.listen_stdin:

            asyncio.create_task(self._read_stdin())
        else:
            self.server = await asyncio.start_server(
                self.handle_client, self.host, self.port,
                reuse_address=True
            )

async def stop(self):
        
        self._running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()

    async def _put_entry(self, entry):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.parser.parse_fields, entry)
        await self.queue.put(entry)

    async def _read_stdin(self):
        
        loop = asyncio.get_running_loop()
        buf = MultiLineBuffer(self.parser)

while self._running:
            line = await loop.run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            entry = buf.feed(line)
            if entry:
                await self._put_entry(entry)
        final = buf.flush()
        if final:
            await self._put_entry(final)

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        
        addr = writer.get_extra_info('peername', ('?', 0))
        addr_str = f"{addr[0]}:{addr[1]}"
        buf = MultiLineBuffer(self.parser)

        if self.on_client_connected:
            self.on_client_connected(addr_str)

        try:
            while self._running:
                try:

                    line_bytes = await asyncio.wait_for(reader.readline(), timeout=0.2)
                    if not line_bytes:
                        break
                    line = line_bytes.decode('utf-8', errors='replace')
                    entry = buf.feed(line)
                    if entry:
                        await self._put_entry(entry)
                except asyncio.TimeoutError:

                    entry = buf.flush()
                    if entry:
                        await self._put_entry(entry)
        except asyncio.CancelledError:
            pass
        except Exception:
            pass
        finally:

            final = buf.flush()
            if final:
                await self._put_entry(final)

            if self.on_client_disconnected:
                self.on_client_disconnected(addr_str)

            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
``````

# FILE: logview\ui\__init__.py

```python
from .main_window import MainWindow

__all__ = ["MainWindow"]
``````

# FILE: logview\ui\charts_panel.py

```python
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCharts import QChart, QChartView, QPieSeries
from PySide6.QtGui import QPainter
from PySide6.QtCore import Slot

class LiveStatsPanel(QWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.series = QPieSeries()
        self.series.setHoleSize(0.35)

self.slice_info = self.series.append("INFO", 0)
        self.slice_warn = self.series.append("WARNING", 0)
        self.slice_error = self.series.append("ERROR", 0)
        self.slice_debug = self.series.append("DEBUG", 0)
        self.slice_crit = self.series.append("CRITICAL", 0)

self.slice_error.setColor("
        self.slice_crit.setColor("
        self.slice_warn.setColor("
        self.slice_debug.setColor("
        self.slice_info.setColor("

        self.chart = QChart()
        self.chart.addSeries(self.series)
        self.chart.setTitle("Log Levels")
        self.chart.legend().hide()
        self.chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        layout.addWidget(self.chart_view)

    @Slot(dict)
    def update_counts(self, counts: dict):
        self.slice_info.setValue(counts.get("INFO", 0))
        self.slice_warn.setValue(counts.get("WARNING", 0))
        self.slice_error.setValue(counts.get("ERROR", 0))
        self.slice_debug.setValue(counts.get("DEBUG", 0))
        self.slice_crit.setValue(counts.get("CRITICAL", 0))

for slc in [self.slice_info, self.slice_warn, self.slice_error, self.slice_debug, self.slice_crit]:
            if slc.value() > 0:
                slc.setLabelVisible(True)
                slc.setLabel(f"{slc.label().split()[0]} ({int(slc.value())})")
            else:
                slc.setLabelVisible(False)
``````

# FILE: logview\ui\components\__init__.py

```python
from logview.ui.components.detail_panel import DetailPanel
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QLineEdit, QComboBox,
                                 QCheckBox, QLabel, QDateTimeEdit, QFrame)
from PySide6.QtCore import Signal, QDateTime, Qt

class FilterPanel(QWidget):

filter_changed = Signal(str, list, bool, bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter logs...")

        self.regex_checkbox = QCheckBox("Regex")
        self.bookmark_checkbox = QCheckBox("Show Bookmarks Only")

        layout.addWidget(QLabel("Search:"))
        layout.addWidget(self.search_input)
        layout.addWidget(QLabel("Level:"))

        self.level_checkboxes = []
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            cb = QCheckBox(level)
            cb.setChecked(True)
            cb.stateChanged.connect(self._on_filter_changed)
            self.level_checkboxes.append(cb)
            layout.addWidget(cb)

        layout.addWidget(self.regex_checkbox)
        layout.addWidget(self.bookmark_checkbox)

self.search_input.textChanged.connect(self._on_filter_changed)
        self.regex_checkbox.stateChanged.connect(self._on_filter_changed)
        self.bookmark_checkbox.stateChanged.connect(self._on_filter_changed)

    def _on_filter_changed(self):
        text = self.search_input.text()
        active_levels = [cb.text() for cb in self.level_checkboxes if cb.isChecked()]
        use_regex = self.regex_checkbox.isChecked()
        bookmarks_only = self.bookmark_checkbox.isChecked()
        self.filter_changed.emit(text, active_levels, use_regex, bookmarks_only)

class TimeRangeWidget(QWidget):

range_changed = Signal(object, object)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(4)

        self._enable_cb = QCheckBox("Time range:")
        self._enable_cb.stateChanged.connect(self._on_changed)
        layout.addWidget(self._enable_cb)

        now = QDateTime.currentDateTime()

        self._from_dt = QDateTimeEdit(now.addSecs(-3600))
        self._from_dt.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self._from_dt.setEnabled(False)
        self._from_dt.setCalendarPopup(True)
        self._from_dt.dateTimeChanged.connect(self._on_changed)
        layout.addWidget(self._from_dt)

        layout.addWidget(QLabel("–"))

        self._to_dt = QDateTimeEdit(now)
        self._to_dt.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self._to_dt.setEnabled(False)
        self._to_dt.setCalendarPopup(True)
        self._to_dt.dateTimeChanged.connect(self._on_changed)
        layout.addWidget(self._to_dt)

        layout.addStretch()

    def _on_changed(self):
        enabled = self._enable_cb.isChecked()
        self._from_dt.setEnabled(enabled)
        self._to_dt.setEnabled(enabled)

        if enabled:
            from_dt = self._from_dt.dateTime().toPython()
            to_dt = self._to_dt.dateTime().toPython()
        else:
            from_dt = None
            to_dt = None

        self.range_changed.emit(from_dt, to_dt)
``````

# FILE: logview\ui\components\detail_panel.py

```python
from PySide6.QtWidgets import QTextEdit
from PySide6.QtGui import QFont
from PySide6.QtCore import Slot

class DetailPanel(QTextEdit):

def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont("Courier New", 9))
        self.setPlaceholderText("Select a log row to see full details…")
        self.setMaximumHeight(180)

    @Slot(object)
    def update_details(self, entry):
        if entry:
            if not entry.level and not entry.timestamp:
                self.setPlainText(entry.raw)
                return

pretty_raw = entry.raw
            if entry.raw.strip().startswith("{"):
                try:
                    import json
                    parsed_json = json.loads(entry.raw)
                    pretty_raw = json.dumps(parsed_json, indent=4)
                except Exception:
                    pass

            details = []
            if entry.timestamp:
                details.append(f"Timestamp: {entry.timestamp}")
            if entry.level:
                details.append(f"Level:     {entry.level}")
            if entry.module:
                details.append(f"Module:    {entry.module}")
            if entry.submodule:
                details.append(f"Submodule: {entry.submodule}")
            if entry.message:
                indented_msg = entry.message.replace("\n", "\n           ")
                details.append(f"Message:   {indented_msg}")

            details.append("\n" + "-" * 60 + "\nRaw Log:\n" + pretty_raw)
            self.setPlainText("\n".join(details))
        else:
            self.clear()
``````

# FILE: logview\ui\components\heatmap_widget.py

```python
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import Qt, Slot

class LogHeatmapWidget(QWidget):

def __init__(self, model, table_view, parent=None):
        super().__init__(parent)
        self.model = model
        self.table_view = table_view
        self.setFixedWidth(16)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

self.table_view.verticalScrollBar().valueChanged.connect(self.update)
        self.table_view.verticalScrollBar().rangeChanged.connect(self.update)
        self.model.layoutChanged.connect(self.update)
        self.model.dataChanged.connect(self.update)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

painter.fillRect(self.rect(), QColor("

        n = self.model.rowCount()
        if n == 0:
            return

        h = self.height()

def row_to_y(r):
            return int((r / n) * h)

warning_rows = getattr(self.model, "_warning_rows", [])
        painter.setPen(QPen(QColor("
        for r in warning_rows:
            y = row_to_y(r)
            painter.drawLine(0, y, self.width(), y)

error_rows = getattr(self.model, "_error_rows", [])
        painter.setPen(QPen(QColor("
        for r in error_rows:
            y = row_to_y(r)
            painter.drawLine(0, y, self.width(), y)

find_match_rows = getattr(self.model, "_find_match_rows", [])
        painter.setPen(QPen(QColor("
        for r in find_match_rows:
            y = row_to_y(r)
            painter.drawLine(0, y, self.width(), y)

scrollbar = self.table_view.verticalScrollBar()
        val = scrollbar.value()
        page_step = scrollbar.pageStep()
        max_val = scrollbar.maximum()

first_visible = val
        last_visible = val + page_step

        y_top = row_to_y(first_visible)
        y_bottom = row_to_y(last_visible)
        y_height = max(4, y_bottom - y_top)

painter.fillRect(0, y_top, self.width(), y_height, QColor(255, 255, 255, 30))
        painter.setPen(QPen(QColor(255, 255, 255, 80), 1))
        painter.drawRect(0, y_top, self.width() - 1, y_height)

    def mousePressEvent(self, event):
        self._scroll_to_mouse(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._scroll_to_mouse(event)

    def _scroll_to_mouse(self, event):
        n = self.model.rowCount()
        if n == 0:
            return
        y = event.y()
        h = self.height()
        percentage = max(0.0, min(1.0, y / h))
        target_row = int(percentage * n)

        scrollbar = self.table_view.verticalScrollBar()
        scrollbar.setValue(target_row - (scrollbar.pageStep() // 2))
        self.update()
``````

# FILE: logview\ui\components\log_tab.py

```python
import re
from typing import List, Dict, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QPushButton
)
from PySide6.QtCore import Qt, Slot, QTimer
from PySide6.QtWidgets import QSystemTrayIcon

from logview.ui.log_model import LogModel, LogFilterProxyModel, COL_MESSAGE
from logview.ui.log_delegate import LogDelegate
from logview.ui.find_bar import FindBar
from logview.ui.components import FilterPanel, TimeRangeWidget
from logview.ui.components.detail_panel import DetailPanel
from logview.ui.views.log_table import LogTableView
from logview.log_parser import LogParser
from logview.models import LogEntry
from logview.ui.receiver_worker import ReceiverWorker
from logview.ui.components.heatmap_widget import LogHeatmapWidget

class LogTab(QWidget):
    def __init__(self, config: Dict[str, Any], main_window, parent=None):
        super().__init__(parent)
        self.config = config
        self.main_window = main_window
        self.is_paused = False
        self.pending_logs: List[LogEntry] = []
        self._log_rate_counter = 0

        self.parser = LogParser(config.get("log_format", {}).get("pattern", ""))
        self.source_model = LogModel(self, max_lines=config.get("display", {}).get("max_lines", 10000), color_config=config.get("colors", {}))
        self.model = LogFilterProxyModel(self)
        self.model.setSourceModel(self.source_model)
        self.model.counts_changed.connect(self._on_counts_changed)

        self.receiver_thread = ReceiverWorker(self.config, self.parser)
        self.receiver_thread.logs_received.connect(self.on_logs_received)
        self.receiver_thread.error_occurred.connect(main_window.on_error)
        self.receiver_thread.client_connected.connect(main_window._on_client_connected)
        self.receiver_thread.client_disconnected.connect(main_window._on_client_disconnected)
        self.receiver_thread.start()

main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

self.filter_panel = FilterPanel()
        self.filter_panel.filter_changed.connect(self.model.set_filter)
        main_layout.addWidget(self.filter_panel)

self.time_range_widget = TimeRangeWidget()
        self.time_range_widget.range_changed.connect(self.model.set_time_range)
        main_layout.addWidget(self.time_range_widget)

self._find_bar = FindBar()
        self._find_bar.term_changed.connect(self._on_find_term_changed)
        self._find_bar.navigate.connect(self._on_find_navigate)
        self._find_bar.closed.connect(self._on_find_closed)
        main_layout.addWidget(self._find_bar)

splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)

table_container = QWidget()
        table_container_layout = QHBoxLayout(table_container)
        table_container_layout.setContentsMargins(0, 0, 0, 0)
        table_container_layout.setSpacing(2)

self.table_view = LogTableView(self)
        self.table_view.setModel(self.model)
        table_container_layout.addWidget(self.table_view)

self.heatmap_widget = LogHeatmapWidget(self.model, self.table_view, self)
        table_container_layout.addWidget(self.heatmap_widget)

self.resume_button = QPushButton("↓ Resume Tailing", self.table_view)
        self.resume_button.setObjectName("resume_tail_button")
        self.resume_button.setVisible(False)
        self.resume_button.clicked.connect(self._on_resume_clicked)
        self.resume_button.setStyleSheet()

self._delegate = LogDelegate(self.table_view)
        self.table_view.setItemDelegate(self._delegate)

self.table_view.setColumnWidth(0, 30)
        self.table_view.setColumnWidth(1, 60)
        self.table_view.setColumnWidth(2, 170)
        self.table_view.setColumnWidth(3, 80)
        self.table_view.setColumnWidth(4, 100)
        self.table_view.setColumnWidth(5, 100)

        self.main_window._apply_table_font_to_view(self.table_view)

        splitter.addWidget(table_container)

self._detail_panel = DetailPanel()
        if hasattr(self.main_window, '_show_detail_panel'):
            self._detail_panel.setVisible(self.main_window._show_detail_panel)
        splitter.addWidget(self._detail_panel)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

self.table_view.selectionModel().currentRowChanged.connect(self._on_row_selected)

        self.table_view.verticalScrollBar().valueChanged.connect(self._on_scroll)

        self.auto_scroll = True
        self.scroll_timer = QTimer(self)
        self.scroll_timer.timeout.connect(self.check_autoscroll)
        self.scroll_timer.start(200)

    def stop(self):
        self.receiver_thread.stop()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reposition_resume_button()

    def _reposition_resume_button(self):
        if hasattr(self, "resume_button") and self.resume_button.isVisible():
            btn_w = self.resume_button.width()
            btn_h = self.resume_button.height()
            view_w = self.table_view.width()
            view_h = self.table_view.height()

scrollbar_h = self.table_view.horizontalScrollBar().height() if self.table_view.horizontalScrollBar().isVisible() else 0
            scrollbar_w = self.table_view.verticalScrollBar().width() if self.table_view.verticalScrollBar().isVisible() else 0

            x = view_w - btn_w - 20 - scrollbar_w
            y = view_h - btn_h - 20 - scrollbar_h
            self.resume_button.move(x, y)

    @Slot()
    def _on_resume_clicked(self):
        self.auto_scroll = True
        self.table_view.scrollToBottom()
        if hasattr(self, "resume_button"):
            self.resume_button.setVisible(False)

    @Slot(dict)
    def _on_counts_changed(self, counts: dict):
        if self.main_window.tab_widget.currentWidget() == self:
            self.main_window.stats_panel.update_counts(counts)
            self.main_window._update_level_counts(counts)

    @Slot(str, bool)
    def _on_find_term_changed(self, term: str, use_regex: bool):
        self.model.set_highlight_term(term, use_regex)
        self._delegate.set_term(term, use_regex)
        self.table_view.viewport().update()
        total = self.model.find_match_count()
        self._find_bar.set_match_info(self.model.find_current_match(), total)

    @Slot(int)
    def _on_find_navigate(self, direction: int):
        row = self.model.find_navigate(direction)
        if row >= 0:
            idx = self.model.index(row, COL_MESSAGE)
            self.table_view.setCurrentIndex(idx)
            self.table_view.scrollTo(idx, LogTableView.ScrollHint.PositionAtCenter)
        self._find_bar.set_match_info(
            self.model.find_current_match(), self.model.find_match_count()
        )

    @Slot()
    def _on_find_closed(self):
        self._delegate.set_term("")
        self.table_view.viewport().update()

    @Slot(list)
    def on_logs_received(self, logs: List[LogEntry]):
        self._log_rate_counter += len(logs)
        if self.is_paused:
            self.pending_logs.extend(logs)
        else:
            self.model.add_logs(logs)
        self.main_window._update_status()

if self.main_window.tray_icon:
            alert_pattern = self.config.get("alerts", {}).get("pattern", "")
            if alert_pattern:
                try:
                    regex = re.compile(alert_pattern, re.IGNORECASE)
                    for log in logs:
                        if regex.search(log.raw):
                            self.main_window.tray_icon.showMessage(
                                "Log Alert",
                                f"Alert matched in log: {(log.message or log.raw)[:100]}",
                                QSystemTrayIcon.MessageIcon.Warning,
                                2000
                            )
                except re.error:
                    pass

    @Slot()
    def _on_row_selected(self, current, previous):
        row = current.row()
        entry = self.model.get_entry_at_row(row)
        self._detail_panel.update_details(entry)

    def _on_scroll(self, value: int):
        scrollbar = self.table_view.verticalScrollBar()

        self.auto_scroll = value >= scrollbar.maximum() - 10
        if hasattr(self.main_window, 'status_bar'):

self.main_window.status_bar.set_scroll_lock(not self.auto_scroll)

if hasattr(self, "resume_button"):
            self.resume_button.setVisible(not self.auto_scroll)
            self._reposition_resume_button()

    def check_autoscroll(self):
        if self.auto_scroll and not self.is_paused:
            self.table_view.scrollToBottom()

    def clear_logs(self):
        self.model.clear_logs()
        self.pending_logs.clear()
        self._detail_panel.clear()
        self.main_window._update_status()
``````

# FILE: logview\ui\dialogs\__init__.py

```python

``````

# FILE: logview\ui\find_bar.py

```python
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QLabel, QCheckBox
from PySide6.QtCore import Signal, Qt

class FindBar(QWidget):

term_changed = Signal(str, bool)
    navigate = Signal(int)
    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVisible(False)
        self.setFixedHeight(34)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(4)

        layout.addWidget(QLabel("Find:"))

        self._input = QLineEdit()
        self._input.setPlaceholderText("Search in logs…")
        self._input.setFixedWidth(240)
        self._input.textChanged.connect(self._emit_term_changed)
        self._input.returnPressed.connect(lambda: self.navigate.emit(1))
        layout.addWidget(self._input)

        self._regex_cb = QCheckBox("Regex")
        self._regex_cb.setAccessibleName("Regex Search")
        self._regex_cb.stateChanged.connect(self._emit_term_changed)
        layout.addWidget(self._regex_cb)

        self._match_label = QLabel("")
        self._match_label.setMinimumWidth(70)
        self._match_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(self._match_label)

        btn_prev = QPushButton("▲")
        btn_prev.setFixedSize(26, 24)
        btn_prev.setToolTip("Previous match (Shift+Enter)")
        btn_prev.clicked.connect(lambda: self.navigate.emit(-1))
        layout.addWidget(btn_prev)

        btn_next = QPushButton("▼")
        btn_next.setFixedSize(26, 24)
        btn_next.setToolTip("Next match (Enter)")
        btn_next.clicked.connect(lambda: self.navigate.emit(1))
        layout.addWidget(btn_next)

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(26, 24)
        btn_close.setToolTip("Close (Esc)")
        btn_close.clicked.connect(self.close_bar)
        layout.addWidget(btn_close)

        layout.addStretch()

def open(self):
        
        self.setVisible(True)
        self._input.setFocus()
        self._input.selectAll()

    def close_bar(self):
        
        self.setVisible(False)
        self._input.clear()
        self.term_changed.emit("", False)
        self.closed.emit()

    def _emit_term_changed(self, *args):
        self.term_changed.emit(self._input.text(), self._regex_cb.isChecked())

    def set_match_info(self, current: int, total: int):
        
        if total == 0 and self._input.text():
            self._match_label.setText("No matches")
            self._match_label.setStyleSheet("color:
        elif total > 0:
            self._match_label.setText(f"{current}/{total}")
            self._match_label.setStyleSheet("color: gray; font-size: 10px;")
        else:
            self._match_label.setText("")

    def get_term(self) -> str:
        return self._input.text()

def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close_bar()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.navigate.emit(-1)
            else:
                self.navigate.emit(1)
        else:
            super().keyPressEvent(event)
``````

# FILE: logview\ui\log_delegate.py

```python
from PySide6.QtWidgets import (
    QStyledItemDelegate, QStyleOptionViewItem, QApplication, QStyle
)
from PySide6.QtGui import QPainter, QColor, QTextCharFormat, QTextCursor, QTextDocument
from PySide6.QtCore import Qt, QModelIndex, QRectF
import re
from logview.ui.log_model import COL_MESSAGE

class LogDelegate(QStyledItemDelegate):

def __init__(self, parent=None):
        super().__init__(parent)
        self._term: str = ""
        self._use_regex: bool = False

    def set_term(self, term: str, use_regex: bool = False):
        
        self._term = term
        self._use_regex = use_regex

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        bg_brush = index.data(Qt.ItemDataRole.BackgroundRole)
        fg_brush = index.data(Qt.ItemDataRole.ForegroundRole)

        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)

if bg_brush:
            opt.backgroundBrush = bg_brush
            if not (opt.state & QStyle.StateFlag.State_Selected):
                painter.save()
                painter.fillRect(opt.rect, bg_brush)
                painter.restore()

                opt.features &= ~QStyleOptionViewItem.ViewItemFeature.Alternate

if fg_brush:
            opt.palette.setBrush(opt.palette.ColorGroup.Active, opt.palette.ColorRole.Text, fg_brush)
            opt.palette.setBrush(opt.palette.ColorGroup.Inactive, opt.palette.ColorRole.Text, fg_brush)

if index.column() == COL_MESSAGE and self._term:
            painter.save()
            text = opt.text

style = opt.widget.style() if opt.widget else QApplication.style()
            opt.text = ""
            style.drawControl(QStyle.ControlElement.CE_ItemViewItem, opt, painter, opt.widget)

            text_rect = style.subElementRect(
                QStyle.SubElement.SE_ItemViewItemText, opt, opt.widget
            )
            painter.setClipRect(text_rect)

            doc = QTextDocument()
            doc.setDocumentMargin(0)
            doc.setDefaultFont(opt.font)
            doc.setPlainText(text)

            highlight_fmt = QTextCharFormat()
            highlight_fmt.setBackground(QColor("
            highlight_fmt.setForeground(QColor("

            if self._use_regex:
                try:
                    pattern = re.compile(self._term, re.IGNORECASE)
                    for match in pattern.finditer(text):
                        cursor = QTextCursor(doc)
                        cursor.setPosition(match.start())
                        cursor.setPosition(match.end(), QTextCursor.MoveMode.KeepAnchor)
                        cursor.mergeCharFormat(highlight_fmt)
                except re.error:
                    pass
            else:
                cursor = QTextCursor(doc)
                find_flags = QTextDocument.FindFlag(0)
                while True:
                    cursor = doc.find(self._term, cursor, find_flags)
                    if cursor.isNull():
                        break
                    cursor.mergeCharFormat(highlight_fmt)

            painter.translate(text_rect.topLeft())
            doc.setTextWidth(text_rect.width())
            ctx = doc.documentLayout().PaintContext()

if opt.state & QStyle.StateFlag.State_Selected:
                ctx.palette.setColor(
                    ctx.palette.ColorRole.Text,
                    opt.palette.color(opt.palette.ColorGroup.Active,
                                      opt.palette.ColorRole.HighlightedText)
                )
            else:
                if fg_brush:
                    ctx.palette.setBrush(ctx.palette.ColorRole.Text, fg_brush)

            doc.documentLayout().draw(painter, ctx)
            painter.restore()
        else:
            style = opt.widget.style() if opt.widget else QApplication.style()
            style.drawControl(QStyle.ControlElement.CE_ItemViewItem, opt, painter, opt.widget)
``````

# FILE: logview\ui\log_model.py

```python
import re
from datetime import datetime
from typing import List, Optional, Any, Dict

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QTimer, Signal, QSortFilterProxyModel
from PySide6.QtGui import QColor, QBrush

from logview.models import LogEntry
from logview.controllers.filter_engine import LogFilterEngine

COL_BOOKMARK = 0
COL_INDEX = 1
COL_TIMESTAMP = 2
COL_LEVEL = 3
COL_MODULE = 4
COL_SUBMODULE = 5
COL_MESSAGE = 6

def _parse_color(hex_str: str) -> Optional[QColor]:
    
    if not hex_str or not hex_str.strip():
        return None
    color = QColor(hex_str.strip())
    return color if color.isValid() else None

def _format_relative(dt: datetime) -> str:
    
    try:
        now = datetime.now()
        delta = now - dt.replace(tzinfo=None) if dt.tzinfo else now - dt
        secs = int(delta.total_seconds())
        if secs < 0:
            return "in the future"
        if secs < 60:
            return f"{secs}s ago"
        if secs < 3600:
            return f"{secs // 60}m ago"
        if secs < 86400:
            return f"{secs // 3600}h ago"
        return f"{secs // 86400}d ago"
    except Exception:
        return ""

class LogModel(QAbstractTableModel):

counts_changed = Signal(dict)

    def __init__(self, parent=None, max_lines: int = 10000, color_config: Dict = None):
        super().__init__(parent)
        self._all_logs: List[LogEntry] = []
        self._max_lines = max_lines

self._level_colors: Dict[str, tuple] = {}
        if color_config:
            for level, colors in color_config.items():
                bg = _parse_color(colors.get("bg", ""))
                fg = _parse_color(colors.get("fg", ""))
                self._level_colors[level.upper()] = (bg, fg)

        self._bookmarks: set[int] = set()
        self._level_counts: Dict[str, int] = {}

self._show_relative_time: bool = False
        self._relative_timer = QTimer(self)
        self._relative_timer.timeout.connect(self._refresh_timestamps)

self._animation_timer = QTimer(self)
        self._animation_timer.timeout.connect(self._step_animations)
        self._animation_timer.start(50)

self._new_row_fades = {}

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._all_logs)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 7

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()

        if row >= len(self._all_logs):
            return None

        log = self._all_logs[row]

        if role == Qt.ItemDataRole.DisplayRole:
            if col == COL_INDEX:
                return log.index or ""
            elif col == COL_TIMESTAMP:
                if self._show_relative_time and log.parsed_dt:
                    return _format_relative(log.parsed_dt)
                return log.timestamp or ""
            elif col == COL_LEVEL:
                return log.level or ""
            elif col == COL_MODULE:
                return log.module or ""
            elif col == COL_SUBMODULE:
                return log.submodule or ""
            elif col == COL_MESSAGE:
                return (log.message or log.raw).split("\n")[0]

        elif role == Qt.ItemDataRole.CheckStateRole:
            if col == COL_BOOKMARK:
                return Qt.CheckState.Checked if log.id in self._bookmarks else Qt.CheckState.Unchecked

        elif role == Qt.ItemDataRole.BackgroundRole:
            fade = self._new_row_fades.get(log.id, 0)
            if fade > 0:
                return QBrush(QColor(100, 150, 255, fade))

            if log.level:
                lvl = log.level.upper()
                colors = self._level_colors.get(lvl)
                if colors and colors[0] is not None:
                    return QBrush(colors[0])

        elif role == Qt.ItemDataRole.ForegroundRole:
            if log.level:
                lvl = log.level.upper()
                colors = self._level_colors.get(lvl)
                if colors and colors[1] is not None:
                    return QBrush(colors[1])

        elif role == Qt.ItemDataRole.ToolTipRole:
            if col == COL_MESSAGE:
                return log.raw

        return None

    def headerData(self, section: int, orientation: Qt.Orientation,
                   role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if section == COL_BOOKMARK:
                return "B"
            elif section == COL_INDEX:
                return "Index"
            elif section == COL_TIMESTAMP:
                return "Timestamp"
            elif section == COL_LEVEL:
                return "Level"
            elif section == COL_MODULE:
                return "Module"
            elif section == COL_SUBMODULE:
                return "Submodule"
            elif section == COL_MESSAGE:
                return "Message"
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags

        flags = super().flags(index)
        if index.column() == COL_BOOKMARK:
            flags |= Qt.ItemFlag.ItemIsUserCheckable
        return flags

    def setData(self, index: QModelIndex, value: Any,
                role: int = Qt.ItemDataRole.EditRole) -> bool:
        if not index.isValid():
            return False

        if index.column() == COL_BOOKMARK and role == Qt.ItemDataRole.CheckStateRole:
            log = self._all_logs[index.row()]
            if value == Qt.CheckState.Checked.value:
                self._bookmarks.add(log.id)
            else:
                self._bookmarks.discard(log.id)
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.CheckStateRole])
            return True

        return False

    def toggle_bookmark(self, row: int):
        if 0 <= row < len(self._all_logs):
            log = self._all_logs[row]
            if log.id in self._bookmarks:
                self._bookmarks.discard(log.id)
            else:
                self._bookmarks.add(log.id)
            idx = self.index(row, COL_BOOKMARK)
            self.dataChanged.emit(idx, idx, [Qt.ItemDataRole.CheckStateRole])

    def add_logs(self, logs: List[LogEntry]):
        
        if not logs:
            return

        first_new_row = len(self._all_logs)
        self.beginInsertRows(QModelIndex(), first_new_row, first_new_row + len(logs) - 1)
        for log in logs:
            self._all_logs.append(log)

            if log.level:
                lvl = log.level.upper()
                self._level_counts[lvl] = self._level_counts.get(lvl, 0) + 1

            if log.is_new:
                self._new_row_fades[log.id] = 100
        self.endInsertRows()

overflow = len(self._all_logs) - self._max_lines
        if overflow > 0:
            self.beginRemoveRows(QModelIndex(), 0, overflow - 1)
            removed_logs = self._all_logs[:overflow]
            self._all_logs = self._all_logs[overflow:]
            self.endRemoveRows()

            for log in removed_logs:
                if log.level:
                    lvl = log.level.upper()
                    if lvl in self._level_counts:
                        self._level_counts[lvl] = max(0, self._level_counts[lvl] - 1)
                        if self._level_counts[lvl] == 0:
                            del self._level_counts[lvl]

            removed_ids = {log.id for log in removed_logs}
            self._bookmarks.difference_update(removed_ids)
            for rid in removed_ids:
                self._new_row_fades.pop(rid, None)

        self.counts_changed.emit(dict(self._level_counts))

    def get_level_counts(self) -> dict:
        return self._level_counts.copy()

    def clear_logs(self):
        
        self.beginResetModel()
        self._all_logs.clear()
        self._bookmarks.clear()
        self._new_row_fades.clear()
        self._level_counts.clear()
        self.endResetModel()
        self.counts_changed.emit({})

    def toggle_relative_time(self) -> bool:
        
        self._show_relative_time = not self._show_relative_time
        if self._show_relative_time:
            self._relative_timer.start(10_000)
        else:
            self._relative_timer.stop()
        self._refresh_timestamps()
        return self._show_relative_time

    def _refresh_timestamps(self):
        if self._all_logs:
            self.dataChanged.emit(
                self.index(0, COL_TIMESTAMP),
                self.index(len(self._all_logs) - 1, COL_TIMESTAMP),
                [Qt.ItemDataRole.DisplayRole],
            )

    def update_colors(self, color_config: Dict):
        
        self._level_colors = {}
        if color_config:
            for level, colors in color_config.items():
                bg = _parse_color(colors.get("bg", ""))
                fg = _parse_color(colors.get("fg", ""))
                self._level_colors[level.upper()] = (bg, fg)

        if self._all_logs:
            self.dataChanged.emit(
                self.index(0, 0),
                self.index(len(self._all_logs) - 1, self.columnCount() - 1),
                [Qt.ItemDataRole.BackgroundRole, Qt.ItemDataRole.ForegroundRole],
            )

    def _step_animations(self):
        
        keys_to_remove = []

        for log_id, fade in self._new_row_fades.items():
            new_fade = fade - 10
            if new_fade <= 0:
                keys_to_remove.append(log_id)
            else:
                self._new_row_fades[log_id] = new_fade

        if self._new_row_fades:
            for k in keys_to_remove:
                del self._new_row_fades[k]

            if len(self._all_logs) > 0:
                active_ids = set(self._new_row_fades.keys())
                rows_to_update = [i for i, log in enumerate(self._all_logs) if log.id in active_ids]

                if rows_to_update:
                    min_row = rows_to_update[0]
                    max_row = rows_to_update[-1]
                    self.dataChanged.emit(
                        self.index(min_row, 0),
                        self.index(max_row, self.columnCount() - 1),
                        [Qt.ItemDataRole.BackgroundRole]
                    )

    def get_all_logs(self) -> List[LogEntry]:
        return self._all_logs

    def get_entry_at_row(self, row: int) -> Optional[LogEntry]:
        if 0 <= row < len(self._all_logs):
            return self._all_logs[row]
        return None

class LogFilterProxyModel(QSortFilterProxyModel):
    
    counts_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._filter_engine = LogFilterEngine()
        self._bookmarks_only = False

        self._highlight_term: str = ""
        self._highlight_regex: bool = False
        self._find_match_rows: List[int] = []
        self._find_current_idx: int = -1

        self._warning_rows: List[int] = []
        self._error_rows: List[int] = []

self.setDynamicSortFilter(True)

        self.layoutChanged.connect(self._rebuild_heatmap_indices)
        self.rowsInserted.connect(self._rebuild_heatmap_indices)
        self.rowsRemoved.connect(self._rebuild_heatmap_indices)
        self.modelReset.connect(self._rebuild_heatmap_indices)

    def _rebuild_heatmap_indices(self):
        self._warning_rows.clear()
        self._error_rows.clear()
        source = self.sourceModel()
        if not source:
            return
        n = self.rowCount()
        for i in range(n):
            source_idx = self.mapToSource(self.index(i, 0))
            if source_idx.row() < len(source._all_logs):
                log = source._all_logs[source_idx.row()]
                if log.level:
                    lvl = log.level.upper()
                    if lvl in ("ERROR", "CRITICAL"):
                        self._error_rows.append(i)
                    elif lvl == "WARNING":
                        self._warning_rows.append(i)

    def setSourceModel(self, model):
        super().setSourceModel(model)
        if model:
            model.counts_changed.connect(self.counts_changed.emit)
            self._rebuild_heatmap_indices()

    def add_logs(self, logs: List[LogEntry]):
        source = self.sourceModel()
        if source:
            source.add_logs(logs)

    def clear_logs(self):
        source = self.sourceModel()
        if source:
            source.clear_logs()

    def get_all_logs(self) -> List[LogEntry]:
        source = self.sourceModel()
        if source:
            return source.get_all_logs()
        return []

    @property
    def _all_logs(self) -> List[LogEntry]:
        source = self.sourceModel()
        return source._all_logs if source else []

    @property
    def _filtered_logs(self) -> List[LogEntry]:
        source = self.sourceModel()
        if not source:
            return []
        return [source._all_logs[self.mapToSource(self.index(i, 0)).row()] for i in range(self.rowCount())]

    @property
    def _show_relative_time(self) -> bool:
        source = self.sourceModel()
        return source._show_relative_time if source else False

    def toggle_relative_time(self) -> bool:
        source = self.sourceModel()
        if source:
            return source.toggle_relative_time()
        return False

    def update_colors(self, color_config: Dict):
        source = self.sourceModel()
        if source:
            source.update_colors(color_config)

    def get_level_counts(self) -> dict:
        source = self.sourceModel()
        if source:
            return source.get_level_counts()
        return {}

    def set_filter(self, text: str, levels: List[str], use_regex: bool, bookmarks_only: bool = False):
        
        self._filter_engine.set_text_filter(text, use_regex)
        self._filter_engine.set_level_filter(levels)
        self._bookmarks_only = bookmarks_only
        self.invalidateFilter()
        if self._highlight_term:
            self._rebuild_find_matches()

    def set_time_range(self, from_dt: Optional[datetime], to_dt: Optional[datetime]):
        
        self._filter_engine.set_time_range(from_dt, to_dt)
        self.invalidateFilter()
        if self._highlight_term:
            self._rebuild_find_matches()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        source = self.sourceModel()
        if not source:
            return True
        if source_row >= len(source._all_logs):
            return False
        log = source._all_logs[source_row]

        if self._bookmarks_only and log.id not in source._bookmarks:
            return False

        return self._filter_engine.matches(log)

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        source = self.sourceModel()
        if not source:
            return super().lessThan(left, right)

        if left.row() >= len(source._all_logs) or right.row() >= len(source._all_logs):
            return False
        log_left = source._all_logs[left.row()]
        log_right = source._all_logs[right.row()]

        col = left.column()
        if col == COL_TIMESTAMP:
            val_l = log_left.parsed_dt or datetime.min
            val_r = log_right.parsed_dt or datetime.min
            return val_l < val_r
        elif col == COL_LEVEL:
            val_l = log_left.level or ""
            val_r = log_right.level or ""
            return val_l < val_r
        elif col == COL_MESSAGE:
            val_l = (log_left.message or log_left.raw).lower()
            val_r = (log_right.message or log_right.raw).lower()
            return val_l < val_r
        elif col == COL_INDEX:
            try:
                val_l = int(log_left.index or 0)
                val_r = int(log_right.index or 0)
            except ValueError:
                val_l = log_left.index or ""
                val_r = log_right.index or ""
            return val_l < val_r
        elif col == COL_MODULE:
            val_l = (log_left.module or "").lower()
            val_r = (log_right.module or "").lower()
            return val_l < val_r
        elif col == COL_SUBMODULE:
            val_l = (log_left.submodule or "").lower()
            val_r = (log_right.submodule or "").lower()
            return val_l < val_r
        return super().lessThan(left, right)

    def toggle_bookmark(self, row: int):
        source = self.sourceModel()
        if not source or not (0 <= row < self.rowCount()):
            return
        source_idx = self.mapToSource(self.index(row, 0))
        source.toggle_bookmark(source_idx.row())

    def get_entry_at_row(self, row: int) -> Optional[LogEntry]:
        source = self.sourceModel()
        if not source or not (0 <= row < self.rowCount()):
            return None
        source_idx = self.mapToSource(self.index(row, 0))
        return source.get_entry_at_row(source_idx.row())

    def set_highlight_term(self, term: str, use_regex: bool = False):
        
        self._highlight_term = term
        self._highlight_regex = use_regex
        self._rebuild_find_matches()

if self.rowCount() > 0:
            self.dataChanged.emit(
                self.index(0, COL_MESSAGE),
                self.index(self.rowCount() - 1, COL_MESSAGE),
                [Qt.ItemDataRole.DisplayRole]
            )

    def _rebuild_find_matches(self):
        
        self._find_match_rows.clear()
        self._find_current_idx = -1
        if not self._highlight_term:
            return

        source = self.sourceModel()
        if not source:
            return

        n = self.rowCount()
        if self._highlight_regex:
            try:
                pattern = re.compile(self._highlight_term, re.IGNORECASE)
                for i in range(n):
                    source_idx = self.mapToSource(self.index(i, 0))
                    log = source._all_logs[source_idx.row()]
                    if pattern.search(log.raw):
                        self._find_match_rows.append(i)
            except re.error:
                pass
        else:
            term_lower = self._highlight_term.lower()
            for i in range(n):
                source_idx = self.mapToSource(self.index(i, 0))
                log = source._all_logs[source_idx.row()]
                if term_lower in log.raw_lower:
                    self._find_match_rows.append(i)

    def find_navigate(self, direction: int) -> int:
        if not self._find_match_rows:
            return -1
        n = len(self._find_match_rows)
        if self._find_current_idx < 0:
            self._find_current_idx = 0 if direction > 0 else n - 1
        else:
            self._find_current_idx = (self._find_current_idx + direction) % n
        return self._find_match_rows[self._find_current_idx]

    def find_match_count(self) -> int:
        return len(self._find_match_rows)

    def find_current_match(self) -> int:
        return self._find_current_idx + 1 if self._find_current_idx >= 0 else 0

    def get_bookmark_row(self, current_row: int, direction: int) -> int:
        source = self.sourceModel()
        if not source or not source._bookmarks:
            return -1
        n = self.rowCount()
        if n == 0:
            return -1
        row = current_row
        for _ in range(n):
            row = (row + direction) % n
            source_idx = self.mapToSource(self.index(row, 0))
            log = source._all_logs[source_idx.row()]
            if log.id in source._bookmarks:
                return row
        return -1
``````

# FILE: logview\ui\main_window.py

```python
import sys
from typing import Dict, Any, List, Optional

from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget,
    QFileDialog, QMessageBox, QSplitter,
    QApplication, QDockWidget, QStyle, QSystemTrayIcon,
    QTabWidget
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QKeySequence, QShortcut, QGuiApplication, QFont

from logview.ui.log_model import LogModel
from logview.ui.log_delegate import LogDelegate
from logview.ui.find_bar import FindBar
from logview.ui.components import FilterPanel, TimeRangeWidget
from logview.ui.settings_dialog import SettingsDialog, save_config_to_toml
from logview.log_parser import LogParser
from logview.export import export_logs, save_session, load_session
from logview.models import LogEntry
import logview.config
from logview.ui.receiver_worker import ReceiverWorker
from logview.ui.charts_panel import LiveStatsPanel
from logview.ui.window_parts.menu_builder import MenuBuilder
from logview.ui.window_parts.toolbar_builder import ToolbarBuilder
from logview.ui.window_parts.status_bar import LogStatusBar
from logview.ui.views.log_table import LogTableView
from logview.ui.components.detail_panel import DetailPanel

class MainWindow(QMainWindow):

def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config
        self.setWindowTitle("Log Viewer")
        self.resize(1280, 800)

self._setup_style()

self._show_detail_panel = True

        self._table_font_size = 10
        self._connected_clients: int = 0

self.menu_builder = MenuBuilder(self)
        self._setup_ui()
        self.status_bar = LogStatusBar(self)
        self.setStatusBar(self.status_bar)

        self.is_dark_theme = QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark
        self._apply_theme()
        QGuiApplication.styleHints().colorSchemeChanged.connect(self._on_color_scheme_changed)

self.tray_icon = None
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon), self)
            self.tray_icon.show()

self.auto_scroll = True

self._rate_timer = QTimer(self)
        self._rate_timer.timeout.connect(self._update_rate_display)
        self._rate_timer.start(1000)

self.stats_dock = QDockWidget("Live Statistics", self)
        self.stats_panel = LiveStatsPanel(self.stats_dock)
        self.stats_dock.setWidget(self.stats_panel)
        self.stats_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.stats_dock)

        from logview.ui.components.log_tab import LogTab
        self.add_source_tab("Source 1", self.config)

find_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        find_shortcut.activated.connect(self._toggle_find_bar)

self._update_status()

    def change_theme(self, name: str):
        if "theme" not in self.config:
            self.config["theme"] = {}
        self.config["theme"]["name"] = name
        save_config_to_toml(self.config, logview.config.DEFAULT_CONFIG_PATH)
        self._apply_theme()

        if hasattr(self, "menu_builder") and hasattr(self.menu_builder, "theme_group"):
            for act in self.menu_builder.theme_group.actions():
                if act.text().lower().startswith(name.lower()):
                    act.setChecked(True)
                    break

def _setup_style(self):
        pass

    @Slot(Qt.ColorScheme)
    def _on_color_scheme_changed(self, scheme: Qt.ColorScheme):
        self.is_dark_theme = scheme == Qt.ColorScheme.Dark
        self._apply_theme()

    def _apply_theme(self):
        theme_name = self.config.get("theme", {}).get("name", "auto")
        app = QApplication.instance()
        if not app:
            return

        import qdarktheme

        app.setStyleSheet("")
        self.setStyleSheet("")

        if theme_name in ("auto", "dark", "light"):
            if theme_name == "auto":
                theme_str = "dark" if self.is_dark_theme else "light"
            else:
                theme_str = theme_name

            app.setStyleSheet(qdarktheme.load_stylesheet(theme_str))
            app.setPalette(qdarktheme.load_palette(theme_str))
        else:
            try:
                from qt_material import apply_stylesheet
                apply_stylesheet(app, theme=theme_name)
            except Exception as e:

                print(f"Error applying qt-material theme {theme_name}: {e}")
                theme_str = "dark" if self.is_dark_theme else "light"
                app.setStyleSheet(qdarktheme.load_stylesheet(theme_str))
                app.setPalette(qdarktheme.load_palette(theme_str))

def add_source_tab(self, name: str, config: Dict[str, Any]):
        from logview.ui.components.log_tab import LogTab
        tab = LogTab(config, self)
        self.tab_widget.addTab(tab, name)

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.toolbar_builder = ToolbarBuilder(self)

self.tab_widget = QTabWidget()
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        main_layout.addWidget(self.tab_widget)

@Slot(bool)
    def toggle_toolbar(self, checked: bool):
        if hasattr(self, 'toolbar_builder') and hasattr(self.toolbar_builder, 'toolbar'):
            self.toolbar_builder.toolbar.setVisible(checked)

    @Slot(bool)
    def toggle_status_bar(self, checked: bool):
        if hasattr(self, 'status_bar'):
            self.status_bar.setVisible(checked)

    @Slot(bool)
    def toggle_detail_panel(self, checked: bool):
        self._show_detail_panel = checked
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if hasattr(tab, '_detail_panel'):
                tab._detail_panel.setVisible(checked)

    def toggle_pause(self, paused: bool):
        tab = self.tab_widget.currentWidget()
        if tab: tab.is_paused = paused
        if paused:
            self.toolbar_builder.action_pause.setIcon(
                self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
            )
            self.toolbar_builder.action_pause.setText("Resume")
        else:
            self.toolbar_builder.action_pause.setIcon(
                self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause)
            )
            self.toolbar_builder.action_pause.setText("Pause")
            tab = self.tab_widget.currentWidget()
            if tab and tab.pending_logs:
                tab.model.add_logs(tab.pending_logs)
                tab.pending_logs.clear()
                self._update_status()

    def clear_logs(self):
        tab = self.tab_widget.currentWidget()
        if tab:
            tab.clear_logs()

    @Slot(int)
    def _on_tab_changed(self, index: int):
        tab = self.tab_widget.widget(index)
        if tab:
            self._update_status()
            tab._on_counts_changed(tab.model.get_level_counts())

    @Slot(str)
    def on_error(self, message: str):
        self.statusBar().showMessage(f"Error: {message}", 5000)

    @Slot(str)
    def _on_client_connected(self, addr: str):
        self._connected_clients += 1
        self.status_bar.set_client_connected(addr)

    @Slot(str)
    def _on_client_disconnected(self, addr: str):
        self._connected_clients = max(0, self._connected_clients - 1)
        if self._connected_clients == 0:
            self.status_bar.set_client_disconnected()

def _on_relative_time_toggled(self, checked: bool):
        tab = self.tab_widget.currentWidget()
        if tab: tab.model.toggle_relative_time()

def _update_status(self):
        tab = self.tab_widget.currentWidget()
        if tab:
            total = len(tab.model.get_all_logs())
            shown = tab.model.rowCount()
            pending = len(tab.pending_logs)
            self.status_bar.update_status(total, shown, pending)

    def _update_rate_display(self):
        rate = 0
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if tab:
                rate += tab._log_rate_counter
                tab._log_rate_counter = 0
        self.status_bar.update_rate_display(rate)

    @Slot(dict)
    def _update_level_counts(self, counts: dict):
        
        self.status_bar.update_level_counts(counts)
        self._update_status()

def _toggle_find_bar(self):
        tab = self.tab_widget.currentWidget()
        if tab:
            if tab._find_bar.isVisible():
                tab._find_bar.close_bar()
            else:
                tab._find_bar.open()

    @Slot(str, bool)
    def _on_find_term_changed(self, term: str, use_regex: bool):
        self.model.set_highlight_term(term, use_regex)
        self._delegate.set_term(term, use_regex)
        self.table_view.viewport().update()
        total = self.model.find_match_count()
        self._find_bar.set_match_info(self.model.find_current_match(), total)

    @Slot(int)
    def _on_find_navigate(self, direction: int):
        row = self.model.find_navigate(direction)
        if row >= 0:
            idx = self.model.index(row, 3)
            self.table_view.setCurrentIndex(idx)
            self.table_view.scrollTo(idx, QTableView.ScrollHint.PositionAtCenter)
        self._find_bar.set_match_info(
            self.model.find_current_match(), self.model.find_match_count()
        )

    @Slot()
    def _on_find_closed(self):
        self._delegate.set_term("")
        self.table_view.viewport().update()

def keyPressEvent(self, event):
        if (event.key() == Qt.Key.Key_C and
                event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            self._copy_selected_rows()
        else:
            super().keyPressEvent(event)

    def _copy_selected_rows(self):
        tab = self.tab_widget.currentWidget()
        if not tab: return
        selected = tab.table_view.selectedIndexes()
        if not selected:
            return

        rows = sorted(set(idx.row() for idx in selected))
        lines = []
        for row in rows:
            entry = tab.model.get_entry_at_row(row)
            if entry:
                lines.append(entry.raw)
        if lines:
            QApplication.clipboard().setText("\n".join(lines))
            self.statusBar().showMessage(f"Copied {len(lines)} row(s) to clipboard", 2000)

    def _copy_selected_messages(self):
        tab = self.tab_widget.currentWidget()
        if not tab: return
        selected = tab.table_view.selectedIndexes()
        if not selected:
            return
        rows = sorted(set(idx.row() for idx in selected))
        lines = []
        for row in rows:
            entry = tab.model.get_entry_at_row(row)
            if entry:
                lines.append(entry.message)
        if lines:
            QApplication.clipboard().setText("\n".join(lines))
            self.statusBar().showMessage(f"Copied {len(lines)} message(s) to clipboard", 2000)

def _zoom_font(self, delta: int):
        self._table_font_size = max(6, min(24, self._table_font_size + delta))
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if tab:
                self._apply_table_font_to_view(tab.table_view)

    def _apply_table_font_to_view(self, table_view):
        font = QFont()
        font.setPointSize(self._table_font_size)
        table_view.setFont(font)
        table_view.verticalHeader().setDefaultSectionSize(self._table_font_size + 10)

def export_logs(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Logs", "", "Log Files (*.log);;JSON Files (*.json)"
        )
        if file_path:
            try:
                tab = self.tab_widget.currentWidget()
                if not tab: return
                logs_to_export = tab.model.get_all_logs()
                format_type = "json" if file_path.endswith(".json") else "text"
                export_logs(logs_to_export, file_path, format_type)
                QMessageBox.information(self, "Export Successful", f"Logs exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", str(e))

    def save_session(self):
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Session", "", "Log Viewer Session (*.lvsession)"
        )
        if file_path:
            try:
                tab = self.tab_widget.currentWidget()
                if not tab: return
                save_session(tab.model.get_all_logs(), file_path)
                self.statusBar().showMessage(f"Session saved to {file_path}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Save Failed", str(e))

    def load_session(self):
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Session", "", "Log Viewer Session (*.lvsession)"
        )
        if file_path:
            try:
                entries = load_session(file_path)
                tab = self.tab_widget.currentWidget()
                if not tab: return
                tab.model.clear_logs()
                tab.model.add_logs(entries)
                self.statusBar().showMessage(
                    f"Loaded {len(entries):,} log entries from session", 3000
                )
            except Exception as e:
                QMessageBox.critical(self, "Load Failed", str(e))

def _on_new_source_tab(self):
        import copy
        new_config = copy.deepcopy(self.config)

current_port = new_config.get("server", {}).get("port", 9999)
        new_config["server"]["port"] = current_port + self.tab_widget.count()
        name = f"Source {self.tab_widget.count() + 1} (Port {new_config['server']['port']})"
        self.add_source_tab(name, new_config)

    def open_settings(self):
        
        dialog = SettingsDialog(self.config, parent=self)
        if dialog.exec() != SettingsDialog.DialogCode.Accepted:
            return

        new_config = dialog.get_updated_config()

old_server = self.config.get("server", {})
        new_server = new_config.get("server", {})
        connection_changed = (
            old_server.get("host") != new_server.get("host") or
            old_server.get("port") != new_server.get("port")
        )

        format_changed = self.config.get("log_format", {}).get("pattern") != new_config.get("log_format", {}).get("pattern")
        alerts_changed = self.config.get("alerts", {}).get("pattern") != new_config.get("alerts", {}).get("pattern")

try:
            save_config_to_toml(new_config, logview.config.DEFAULT_CONFIG_PATH)
        except Exception as e:
            QMessageBox.warning(self, "Save Failed", f"Could not save settings:\n{e}")

self.config = new_config

for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if tab: tab.model.update_colors(new_config.get("colors", {}))

if connection_changed or format_changed or alerts_changed:
            self.statusBar().showMessage("Restarting receiver for new settings...", 3000)
            for i in range(self.tab_widget.count()):
                tab = self.tab_widget.widget(i)
                if tab:
                    tab.stop()
                    from logview.ui.receiver_worker import ReceiverWorker
                    from logview.log_parser import LogParser

                    if tab.receiver_thread:
                        tab.receiver_thread.wait()

                    tab.config = self.config
                    tab.parser = LogParser(self.config.get("log_format", {}).get("pattern", ""))
                    tab.receiver_thread = ReceiverWorker(tab.config, tab.parser)
                    tab.receiver_thread.logs_received.connect(tab.on_logs_received)
                    tab.receiver_thread.error_occurred.connect(self.on_error)
                    tab.receiver_thread.client_connected.connect(self._on_client_connected)
                    tab.receiver_thread.client_disconnected.connect(self._on_client_disconnected)
                    tab.receiver_thread.start()

def closeEvent(self, event):
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if tab:
                tab.stop()
        super().closeEvent(event)
``````

# FILE: logview\ui\receiver_worker.py

```python
import asyncio
from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtCore import QThread, Signal

from logview.receiver import TCPServerReceiver, FileTailReceiver
from logview.log_parser import LogParser


class ReceiverWorker(QThread):
    logs_received = Signal(list)
    error_occurred = Signal(str)
    client_connected = Signal(str)
    client_disconnected = Signal(str)

    def __init__(self, config: Dict[str, Any], parser: LogParser):
        super().__init__()
        self.config = config
        self.parser = parser
        self.running = True
        self.loop = None
        self._async_queue = None
        self._receivers = []
        self._executor = ThreadPoolExecutor(max_workers=4)

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self._async_queue = asyncio.Queue()

        if "tail_file" in self.config and self.config["tail_file"]:
            self._receivers.append(FileTailReceiver(self.config["tail_file"], self.parser, self._async_queue))
        else:
            host = self.config.get("server", {}).get("host", "localhost")
            port = self.config.get("server", {}).get("port", 9999)
            listen_stdin = self.config.get("listen_stdin", False)
            recv = TCPServerReceiver(host, port, self.parser, self._async_queue, listen_stdin)
            recv.on_client_connected = lambda addr: self.client_connected.emit(addr)
            recv.on_client_disconnected = lambda addr: self.client_disconnected.emit(addr)
            self._receivers.append(recv)

        self.loop.run_until_complete(self._run_async())
        self.loop.close()

    async def _run_async(self):

        for r in self._receivers:
            await r.start()

        try:
            while self.running:
                await asyncio.sleep(0.05)

                logs = []
                while not self._async_queue.empty():
                    try:
                        entry = self._async_queue.get_nowait()
                        logs.append(entry)
                    except asyncio.QueueEmpty:
                        break

                if logs:
                    list(self._executor.map(self.parser.parse_fields, logs))
                    self.logs_received.emit(logs)
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            for r in self._receivers:
                await r.stop()

    def stop(self):
        self.running = False
        self._executor.shutdown(wait=False)
        self.wait()
``````

# FILE: logview\ui\settings_dialog.py

```python
from typing import Dict, Any, Optional
import copy
import json

from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QTabWidget, QWidget, QFormLayout,
    QVBoxLayout, QHBoxLayout, QLineEdit, QSpinBox, QPushButton,
    QLabel, QFrame, QScrollArea, QSizePolicy, QComboBox
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QColorDialog
import re

LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

class ColorButton(QPushButton):

def __init__(self, color: str = "", parent=None):
        super().__init__(parent)
        self.setFixedSize(80, 28)
        self._color: str = ""
        self.set_color(color)
        self.clicked.connect(self._pick_color)

    def set_color(self, hex_color: str):
        self._color = hex_color.strip() if hex_color else ""
        self._refresh_style()

    def get_color(self) -> str:
        return self._color

    def _refresh_style(self):
        if self._color:

            c = QColor(self._color)
            if c.isValid():
                text_color = "
                self.setText(self._color)
                self.setStyleSheet(
                    f"QPushButton {{ background-color: {self._color}; color: {text_color}; "
                    f"border: 1px solid
                    f"QPushButton:hover {{ border: 2px solid
                )
                return

        self.setText("none")
        self.setStyleSheet(
            "QPushButton { background-color:
            "border: 1px dashed
            "QPushButton:hover { border: 1px dashed
        )

    def _pick_color(self):
        initial = QColor(self._color) if self._color else QColor(Qt.GlobalColor.white)
        color = QColorDialog.getColor(initial, self, "Pick Color",
                                      QColorDialog.ColorDialogOption.ShowAlphaChannel)
        if color.isValid():
            self.set_color(color.name())

    def clear_color(self):
        self.set_color("")

class LevelColorRow(QWidget):

def __init__(self, level: str, bg: str, fg: str, parent=None):
        super().__init__(parent)
        self.level = level

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)

        lbl = QLabel(level)
        lbl.setFixedWidth(70)
        lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(lbl)

        layout.addWidget(QLabel("BG:"))
        self.bg_btn = ColorButton(bg)
        layout.addWidget(self.bg_btn)

        layout.addWidget(QLabel("FG:"))
        self.fg_btn = ColorButton(fg)
        layout.addWidget(self.fg_btn)

        reset_btn = QPushButton("✕ Reset")
        reset_btn.setFixedSize(60, 24)
        reset_btn.setStyleSheet("font-size: 9px;")
        reset_btn.clicked.connect(self._reset)
        layout.addWidget(reset_btn)

        layout.addStretch()

    def _reset(self):
        self.bg_btn.clear_color()
        self.fg_btn.clear_color()

    def get_colors(self) -> Dict[str, str]:
        return {"bg": self.bg_btn.get_color(), "fg": self.fg_btn.get_color()}

class SettingsDialog(QDialog):

def __init__(self, config: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(420)
        self.setModal(True)

self._config = copy.deepcopy(config)

        root_layout = QVBoxLayout(self)

        tabs = QTabWidget()
        tabs.addTab(self._build_connection_tab(), "🔌 Connection")
        tabs.addTab(self._build_colors_tab(), "🎨 Log Colors")
        tabs.addTab(self._build_log_format_tab(), "⚙️ Log Format")
        root_layout.addWidget(tabs)

buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root_layout.addWidget(buttons)

def _build_connection_tab(self) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)
        form.setContentsMargins(12, 12, 12, 12)
        form.setVerticalSpacing(10)

        server = self._config.get("server", {})

        self._host_edit = QLineEdit(server.get("host", "localhost"))
        form.addRow("Host:", self._host_edit)

        self._port_spin = QSpinBox()
        self._port_spin.setRange(1, 65535)
        self._port_spin.setValue(int(server.get("port", 9999)))
        form.addRow("Port:", self._port_spin)

        alerts = self._config.get("alerts", {})
        self._alert_edit = QLineEdit(alerts.get("pattern", ""))
        self._alert_edit.setPlaceholderText("e.g. CRITICAL|Out of Memory")
        form.addRow("Alert Trigger (Regex):", self._alert_edit)

        note = QLabel("ℹ Changes take effect after restarting the receiver.")
        note.setStyleSheet("color: gray; font-size: 10px;")
        note.setWordWrap(True)
        form.addRow(note)

        return widget

    def _build_colors_tab(self) -> QWidget:
        widget = QWidget()
        outer = QVBoxLayout(widget)
        outer.setContentsMargins(12, 12, 12, 4)

        header = QHBoxLayout()
        for lbl_text in ["Level", "", "Background", "", "Foreground"]:
            lbl = QLabel(lbl_text)
            lbl.setStyleSheet("font-weight: bold; font-size: 10px; color:
            header.addWidget(lbl)
        header.addStretch()
        outer.addLayout(header)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        outer.addWidget(line)

        colors_cfg = self._config.get("colors", {})
        self._level_rows: Dict[str, LevelColorRow] = {}

        for level in LOG_LEVELS:
            level_colors = colors_cfg.get(level, {})
            row = LevelColorRow(
                level,
                bg=level_colors.get("bg", ""),
                fg=level_colors.get("fg", ""),
            )
            self._level_rows[level] = row
            outer.addWidget(row)

        outer.addStretch()

        note = QLabel("ℹ Leave empty for default (no color). Accepts any
        note.setStyleSheet("color: gray; font-size: 10px;")
        note.setWordWrap(True)
        outer.addWidget(note)

        return widget

    def _build_log_format_tab(self) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)
        form.setContentsMargins(12, 12, 12, 12)
        form.setVerticalSpacing(10)

        self._preset_combo = QComboBox()
        self._preset_combo.addItems(["Custom", "Apache", "Nginx", "Spring Boot", "Syslog"])
        self._preset_combo.currentTextChanged.connect(self._on_preset_changed)
        form.addRow("Preset:", self._preset_combo)

        log_format = self._config.get("log_format", {})

        self._regex_edit = QLineEdit(log_format.get("pattern", ""))
        form.addRow("Regex Pattern:", self._regex_edit)

        self._sample_edit = QLineEdit()
        self._sample_edit.setPlaceholderText("Enter a sample log line here...")
        form.addRow("Sample Log:", self._sample_edit)

        test_layout = QHBoxLayout()
        self._test_btn = QPushButton("Test Regex")
        self._test_btn.setAccessibleName("Test Regex Pattern")
        self._test_btn.clicked.connect(self._test_regex)
        test_layout.addWidget(self._test_btn)

        self._test_result_label = QLabel("")
        self._test_result_label.setWordWrap(True)
        self._test_result_label.setStyleSheet("color: gray; font-size: 10px;")
        test_layout.addWidget(self._test_result_label)

        form.addRow(test_layout)

        return widget

    def _on_preset_changed(self, text: str):
        presets = {
            "Apache": r'^(?P<host>\S+) \S+ \S+ \[(?P<timestamp>[\w:/]+\s[+\-]\d{4})\] "(?P<request>.*?)" (?P<status>\d{3}) (?P<size>\S+)',
            "Nginx": r'^(?P<host>\S+) - \S+ \[(?P<timestamp>[\w:/]+\s[+\-]\d{4})\] "(?P<request>.*?)" (?P<status>\d{3}) (?P<size>\S+)',
            "Spring Boot": r'^(?P<timestamp>\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\.\d{3})\s+(?P<level>\w+)\s+\d+\s+---\s+\[.*?\]\s+.*?\s+:\s+(?P<message>.*)',
            "Syslog": r'^(?P<timestamp>\w{3}\s+\d+\s\d{2}:\d{2}:\d{2})\s+(?P<host>\S+)\s+(?P<app>\S+):\s+(?P<message>.*)'
        }
        if text in presets:
            self._regex_edit.setText(presets[text])

    def _test_regex(self):
        pattern = self._regex_edit.text()
        sample = self._sample_edit.text()
        try:
            regex = re.compile(pattern)
            match = regex.match(sample)
            if match:
                groups = match.groupdict()
                result_text = "Match found!\n"
                for k, v in groups.items():
                    result_text += f"{k}: {v}\n"
                self._test_result_label.setStyleSheet("color: green; font-size: 10px;")
                self._test_result_label.setText(result_text)
            else:
                self._test_result_label.setStyleSheet("color: red; font-size: 10px;")
                self._test_result_label.setText("No match.")
        except re.error as e:
            self._test_result_label.setStyleSheet("color: red; font-size: 10px;")
            self._test_result_label.setText(f"Invalid regex: {e}")

def get_updated_config(self) -> Dict[str, Any]:
        
        cfg = copy.deepcopy(self._config)

if "server" not in cfg:
            cfg["server"] = {}
        cfg["server"]["host"] = self._host_edit.text().strip() or "localhost"
        cfg["server"]["port"] = self._port_spin.value()

cfg["colors"] = {}
        for level, row in self._level_rows.items():
            cfg["colors"][level] = row.get_colors()

if "log_format" not in cfg:
            cfg["log_format"] = {}
        cfg["log_format"]["pattern"] = self._regex_edit.text()

if "alerts" not in cfg:
            cfg["alerts"] = {}
        cfg["alerts"]["pattern"] = self._alert_edit.text()

        return cfg

def save_config_to_toml(config: Dict[str, Any], path: str):
    
    lines = []

    server = config.get("server", {})
    lines.append("[server]")
    lines.append(f'host = {json.dumps(server.get("host", "localhost"), ensure_ascii=False)}')
    lines.append(f'port = {server.get("port", 9999)}')
    lines.append("")

    display = config.get("display", {})
    lines.append("[display]")
    lines.append(f'max_lines = {display.get("max_lines", 10000)}')
    lines.append("")

    log_format = config.get("log_format", {})
    pattern = log_format.get("pattern", "")
    lines.append("[log_format]")
    lines.append(f'pattern = {json.dumps(pattern, ensure_ascii=False)}')
    lines.append("")

    colors = config.get("colors", {})
    for level in LOG_LEVELS:
        level_colors = colors.get(level, {})
        lines.append(f"[colors.{level}]")
        lines.append(f'bg = {json.dumps(level_colors.get("bg", ""), ensure_ascii=False)}')
        lines.append(f'fg = {json.dumps(level_colors.get("fg", ""), ensure_ascii=False)}')
        lines.append("")

    theme = config.get("theme", {})
    lines.append("[theme]")
    lines.append(f'name = {json.dumps(theme.get("name", "auto"), ensure_ascii=False)}')
    lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
``````

# FILE: logview\ui\views\__init__.py

```python

``````

# FILE: logview\ui\views\log_table.py

```python
from PySide6.QtWidgets import QTableView, QMenu, QApplication
from PySide6.QtCore import Qt, QEvent, Slot
from PySide6.QtGui import QFont, QKeySequence, QAction

class LogTableView(QTableView):

def __init__(self, log_tab, parent=None):
        super().__init__(parent)
        self.log_tab = log_tab
        self.main_window = log_tab.main_window

        self.setAlternatingRowColors(True)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

self.setSortingEnabled(True)
        self.horizontalHeader().sectionClicked.connect(self._on_header_clicked)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

self.viewport().installEventFilter(self)

    def _on_header_clicked(self, col: int):

        pass

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_F2:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:

                self._navigate_bookmark(-1)
            elif event.modifiers() & Qt.KeyboardModifier.ControlModifier:

                self._navigate_bookmark(1)
            else:

                idx = self.currentIndex()
                if idx.isValid():
                    self.model().toggle_bookmark(idx.row())
        else:
            super().keyPressEvent(event)

    def _navigate_bookmark(self, direction: int):
        idx = self.currentIndex()
        current_row = idx.row() if idx.isValid() else -1
        new_row = self.model().get_bookmark_row(current_row, direction)
        if new_row >= 0:
            new_idx = self.model().index(new_row, 3)
            self.setCurrentIndex(new_idx)
            self.scrollTo(new_idx, QTableView.ScrollHint.PositionAtCenter)

    def eventFilter(self, obj, event):
        if obj is self.viewport():
            if event.type() == QEvent.Type.Wheel:
                if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                    delta = event.angleDelta().y()
                    self.main_window._zoom_font(1 if delta > 0 else -1)
                    return True
        return super().eventFilter(obj, event)

    def _show_context_menu(self, pos):
        menu = QMenu(self)

        action_copy_raw = QAction("Copy Selected Logs", self)
        action_copy_raw.setShortcut(QKeySequence("Ctrl+C"))
        action_copy_raw.triggered.connect(self.main_window._copy_selected_rows)
        menu.addAction(action_copy_raw)

        action_copy_msg = QAction("Copy Message Only", self)
        action_copy_msg.triggered.connect(self.main_window._copy_selected_messages)
        menu.addAction(action_copy_msg)

        menu.exec(self.viewport().mapToGlobal(pos))
``````

# FILE: logview\ui\window_parts\__init__.py

```python

``````

# FILE: logview\ui\window_parts\menu_builder.py

```python
from PySide6.QtGui import QAction, QKeySequence, QActionGroup

from logview.ui.settings_dialog import save_config_to_toml

class MenuBuilder:

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

self.theme_menu = menu_bar.addMenu("Theme")
        self.theme_group = QActionGroup(self.main_window)
        self.theme_group.setExclusive(True)

        current_theme = self.config.get("theme", {}).get("name", "auto")

        def add_theme_action(name, display_name, parent_menu):
            act = QAction(display_name, self.main_window)
            act.setCheckable(True)
            if name == current_theme:
                act.setChecked(True)

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
``````

# FILE: logview\ui\window_parts\status_bar.py

```python
from PySide6.QtWidgets import QStatusBar, QLabel

class LogStatusBar(QStatusBar):

def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent

        self._status_connection = QLabel("● Listening")
        self._status_connection.setStyleSheet("color:
        self.addPermanentWidget(self._status_connection)

        self.addPermanentWidget(self._make_separator())

        self._status_total = QLabel("Total: 0")
        self.addPermanentWidget(self._status_total)

        self.addPermanentWidget(self._make_separator())

        self._status_shown = QLabel("Shown: 0")
        self.addPermanentWidget(self._status_shown)

        self.addPermanentWidget(self._make_separator())

        self._status_pending = QLabel("Pending Buffer: 0")
        self.addPermanentWidget(self._status_pending)

        self.addPermanentWidget(self._make_separator())

        self._status_rate = QLabel("0 msg/s")
        self.addPermanentWidget(self._status_rate)

        self.addPermanentWidget(self._make_separator())

        self._status_scroll = QLabel("[Scroll Lock: OFF]")
        self.addPermanentWidget(self._status_scroll)

        self.addPermanentWidget(self._make_separator())

        self._status_levels = QLabel("")
        self.addPermanentWidget(self._status_levels)

    @staticmethod
    def _make_separator() -> QLabel:
        sep = QLabel("|")
        sep.setStyleSheet("color:
        return sep

    def update_status(self, total: int, shown: int, pending: int = 0):
        self._status_total.setText(f"Total: {total:,}")
        self._status_shown.setText(f"Shown: {shown:,}")
        self._status_pending.setText(f"Pending Buffer: {pending:,}")

    def update_rate_display(self, rate: int):
        self._status_rate.setText(f"{rate} msg/s")

    def update_level_counts(self, counts: dict):
        
        parts = []
        colors = {"ERROR": "
        for lvl in ["ERROR", "CRITICAL", "WARNING"]:
            n = counts.get(lvl, 0)
            if n:
                c = colors.get(lvl, "
                parts.append(f'<span style="color:{c};">{lvl}:{n}</span>')
        self._status_levels.setText("  ".join(parts))

    def set_client_connected(self, addr: str):
        self._status_connection.setText(f"● Connected ({addr})")
        self._status_connection.setStyleSheet("color:

    def set_client_disconnected(self):
        self._status_connection.setText("● Listening")
        self._status_connection.setStyleSheet("color:

    def set_scroll_lock(self, locked: bool):
        if locked:
            self._status_scroll.setText("[Scroll Lock: ON]")
        else:
            self._status_scroll.setText("[Scroll Lock: OFF]")
``````

# FILE: logview\ui\window_parts\toolbar_builder.py

```python
from PySide6.QtWidgets import QToolBar, QStyle, QToolButton

class ToolbarBuilder:

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

        self.action_clear = self.toolbar.addAction(
            self.main_window.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon), "Clear"
        )
        self.action_clear.triggered.connect(self.main_window.clear_logs)

        self.action_copy = self.toolbar.addAction(
            self.main_window.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon), "Copy"
        )
        self.action_copy.setToolTip("Copy Selected Logs (Ctrl+C)")
        self.action_copy.triggered.connect(self.main_window._copy_selected_rows)

        self.toolbar.addSeparator()

self.action_rel_time = self.toolbar.addAction(
            self.main_window.style().standardIcon(QStyle.StandardPixmap.SP_DialogResetButton),
            "Relative Time"
        )
        self.action_rel_time.setCheckable(True)
        self.action_rel_time.setToolTip("Toggle relative timestamps (e.g. '2s ago')")
        self.action_rel_time.toggled.connect(self.main_window._on_relative_time_toggled)

        self.toolbar.addSeparator()

        self.action_theme = self.toolbar.addAction(
            self.main_window.style().standardIcon(QStyle.StandardPixmap.SP_DesktopIcon), "Theme"
        )
        theme_btn = self.toolbar.widgetForAction(self.action_theme)
        if isinstance(theme_btn, QToolButton):
            theme_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
            if hasattr(self.main_window, 'menu_builder') and self.main_window.menu_builder:
                theme_btn.setMenu(self.main_window.menu_builder.theme_menu)

        self.action_settings = self.toolbar.addAction(
            self.main_window.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView), "Settings"
        )
        self.action_settings.triggered.connect(self.main_window.open_settings)
``````

# FILE: start.ps1

```powershell
# start.ps1 - Activate virtual environment and launch Sagittarius Log Viewer

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvActivate = Join-Path $ScriptDir ".venv\Scripts\Activate.ps1"
if (-not (Test-Path $VenvActivate)) {
    $VenvActivate = Join-Path $ScriptDir ".venv\bin\Activate.ps1"
}

if (-not (Test-Path $VenvActivate)) {
    Write-Error "Virtual environment not found at: $VenvActivate"
    Write-Host "Run: python -m venv .venv  then  pip install -r requirements.txt"
    exit 1
}

Write-Host "Activating virtual environment..." -ForegroundColor Cyan
. $VenvActivate

Write-Host "Starting Sagittarius Log Viewer..." -ForegroundColor Green
Set-Location $ScriptDir
python -m logview @args
``````

# FILE: test.ps1

```powershell
# test.ps1 - Start Sagittarius Log Viewer and the Dummy Log Generator for testing

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Locate the Python executable in the virtual environment
$VenvPython = Join-Path $ScriptDir ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    $VenvPython = Join-Path $ScriptDir ".venv/bin/python"
}
if (-not (Test-Path $VenvPython)) {
    Write-Warning "Virtual environment Python not found. Falling back to system python..."
    $VenvPython = "python"
}

Write-Host "Starting Dummy Log Generator in the background..." -ForegroundColor Cyan
$GeneratorJob = Start-Job -Name "SagittariusDummyGenerator" -ScriptBlock {
    param($python, $dir)
    Set-Location $dir
    & $python tools/log_generator.py --port 9999 --rate 2.0 --pattern mixed
} -ArgumentList $VenvPython, $ScriptDir

# Give the generator a moment to boot (it will auto-retry connecting)
Start-Sleep -Seconds 1

Write-Host "Starting Sagittarius Log Viewer..." -ForegroundColor Green
Write-Host "Logs from the generator will start showing up immediately." -ForegroundColor Green
Write-Host "Closing the Log Viewer window will automatically stop the dummy generator." -ForegroundColor Yellow

# Suppress Qt Wayland textinput warning logs in console
$env:QT_LOGGING_RULES = "qt.qpa.wayland.textinput=false"

# Run the Log Viewer in the foreground
& $VenvPython -m logview --port 9999

Write-Host "Stopping Dummy Log Generator..." -ForegroundColor Cyan
Stop-Job $GeneratorJob
Remove-Job $GeneratorJob
Write-Host "Done!" -ForegroundColor Green
``````

# FILE: tests\conftest.py

```python
import pytest


@pytest.fixture(autouse=True)
def isolate_config(tmp_path, monkeypatch):

    config_file = tmp_path / "logview_test.toml"
    config_content = r
    config_file.write_text(config_content, encoding="utf-8")
    monkeypatch.setattr("logview.config.DEFAULT_CONFIG_PATH", str(config_file))
    return config_file
``````

# FILE: tests\integration\test_receiver.py

```python
import pytest
import asyncio
import tempfile
import os
from logview.receiver import TCPServerReceiver, FileTailReceiver
from logview.log_parser import LogParser

@pytest.mark.asyncio
async def test_file_tail_receiver():
    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        filepath = f.name

    parser = LogParser(r"^(.*)$")
    queue = asyncio.Queue()

    receiver = FileTailReceiver(filepath, parser, queue)
    await receiver.start()

    try:

        await asyncio.sleep(0.5)

        with open(filepath, "a") as f:
            f.write("Log line 1\n")
            f.flush()

        entry = await asyncio.wait_for(queue.get(), timeout=5.0)
        assert entry.message == "Log line 1"

    finally:
        await receiver.stop()
        os.unlink(filepath)

@pytest.mark.asyncio
async def test_tcp_server_receiver():
    parser = LogParser(r"^(.*)$")
    queue = asyncio.Queue()

receiver = TCPServerReceiver("127.0.0.1", 0, parser, queue)
    await receiver.start()

addr = receiver.server.sockets[0].getsockname()
    port = addr[1]

    try:
        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        writer.write(b"TCP log line\n")
        await writer.drain()

        writer.close()
        await writer.wait_closed()

        entry = await asyncio.wait_for(queue.get(), timeout=2.0)
        assert entry.message == "TCP log line"

    finally:
        await receiver.stop()
``````

# FILE: tests\integration\test_ui.py

```python
import pytest
from PySide6.QtCore import Qt
from logview.ui.main_window import MainWindow
from logview.models import LogEntry

@pytest.fixture
def app_config():
    return {
        "server": {"host": "localhost", "port": 9999},
        "display": {"max_lines": 1000},
        "log_format": {"pattern": r"^\[(?P<timestamp>.*?)\]\s*\[(?P<level>\w+)\]\s*(?P<message>.*)"}
    }

def test_main_window_init(qtbot, app_config, monkeypatch):

    monkeypatch.setattr("logview.ui.components.log_tab.ReceiverWorker.start", lambda self: None)

    window = MainWindow(app_config)
    qtbot.addWidget(window)

    assert window.windowTitle() == "Log Viewer"
    assert window.tab_widget.currentWidget().model.rowCount() == 0

def test_receive_logs(qtbot, app_config, monkeypatch):
    monkeypatch.setattr("logview.ui.components.log_tab.ReceiverWorker.start", lambda self: None)

    window = MainWindow(app_config)
    qtbot.addWidget(window)

log = LogEntry(raw="[2023] [INFO] Msg", timestamp="2023", level="INFO", message="Msg")
    window.tab_widget.currentWidget().on_logs_received([log])

    assert window.tab_widget.currentWidget().model.rowCount() == 1
    assert window.tab_widget.currentWidget().model._all_logs[0].level == "INFO"

def test_pause_resume(qtbot, app_config, monkeypatch):
    monkeypatch.setattr("logview.ui.components.log_tab.ReceiverWorker.start", lambda self: None)

    window = MainWindow(app_config)
    qtbot.addWidget(window)

    window.toolbar_builder.action_pause.setChecked(True)
    assert window.tab_widget.currentWidget().is_paused is True

    log = LogEntry(raw="[2023] [INFO] Msg")
    window.tab_widget.currentWidget().on_logs_received([log])

assert window.tab_widget.currentWidget().model.rowCount() == 0
    assert len(window.tab_widget.currentWidget().pending_logs) == 1

window.toolbar_builder.action_pause.setChecked(False)
    assert window.tab_widget.currentWidget().is_paused is False
    assert window.tab_widget.currentWidget().model.rowCount() == 1
    assert len(window.tab_widget.currentWidget().pending_logs) == 0

def test_filtering(qtbot, app_config, monkeypatch):
    monkeypatch.setattr("logview.ui.components.log_tab.ReceiverWorker.start", lambda self: None)

    window = MainWindow(app_config)
    qtbot.addWidget(window)

    logs = [
        LogEntry(raw="[2023] [INFO] Success", level="INFO", message="Success"),
        LogEntry(raw="[2023] [ERROR] Failure", level="ERROR", message="Failure")
    ]
    window.tab_widget.currentWidget().on_logs_received(logs)

    assert window.tab_widget.currentWidget().model.rowCount() == 2

for cb in window.tab_widget.currentWidget().filter_panel.level_checkboxes:
        if cb.text() == "INFO":
            cb.setChecked(False)
            break

    assert window.tab_widget.currentWidget().model.rowCount() == 1
    assert window.tab_widget.currentWidget().model.data(window.tab_widget.currentWidget().model.index(0, 3)) == "ERROR"

def test_view_toggles(qtbot, app_config, monkeypatch):
    monkeypatch.setattr("logview.ui.components.log_tab.ReceiverWorker.start", lambda self: None)

    window = MainWindow(app_config)
    qtbot.addWidget(window)
    window.show()

    assert window.toolbar_builder.toolbar.isVisible()
    assert window.status_bar.isVisible()
    assert window.tab_widget.currentWidget()._detail_panel.isVisible()

    window.toggle_toolbar(False)
    assert not window.toolbar_builder.toolbar.isVisible()

    window.toggle_status_bar(False)
    assert not window.status_bar.isVisible()

    window.toggle_detail_panel(False)
    assert not window.tab_widget.currentWidget()._detail_panel.isVisible()
    assert not window._show_detail_panel

def test_copy_selected_rows(qtbot, app_config, monkeypatch):
    monkeypatch.setattr("logview.ui.components.log_tab.ReceiverWorker.start", lambda self: None)

    window = MainWindow(app_config)
    qtbot.addWidget(window)

    log = LogEntry(raw="[2023] [INFO] Msg", timestamp="2023", level="INFO", message="Msg")
    window.tab_widget.currentWidget().on_logs_received([log])

    window.tab_widget.currentWidget().table_view.selectAll()
    window._copy_selected_rows()

    from PySide6.QtWidgets import QApplication
    assert QApplication.clipboard().text() == "[2023] [INFO] Msg"

    window._copy_selected_messages()
    assert QApplication.clipboard().text() == "Msg"
``````

# FILE: tests\integration\uat\test_detail_panel.py

```python
import pytest
from PySide6.QtCore import Qt, QItemSelectionModel
from PySide6.QtWidgets import QApplication
from logview.ui.main_window import MainWindow
from logview.models import LogEntry

@pytest.fixture
def app_config():
    return {
        "server": {"host": "127.0.0.1", "port": 0},
        "display": {"max_lines": 1000},
        "log_format": {"pattern": r"^\[(?P<timestamp>.*?)\]\s*\[(?P<level>\w+)\]\s*(?P<message>.*)"}
    }

@pytest.fixture
def populated_tab(qtbot, app_config, monkeypatch):
    monkeypatch.setattr("logview.ui.components.log_tab.ReceiverWorker.start", lambda self: None)

    window = MainWindow(app_config)
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)

    current_tab = window.tab_widget.currentWidget()

    logs = [
        LogEntry(raw="[2023] [INFO] Normal message", level="INFO", message="Normal message"),
        LogEntry(raw='{"timestamp": "2023", "level": "DEBUG", "message": "JSON message", "data": {"key": "value"}}', level="DEBUG", message='{"timestamp": "2023", "level": "DEBUG", "message": "JSON message", "data": {"key": "value"}}')
    ]

    current_tab.on_logs_received(logs)
    return current_tab, window

def test_inspect_log_details(qtbot, populated_tab):
    current_tab, window = populated_tab

model_index = current_tab.model.index(0, 0)
    current_tab.table_view.selectionModel().setCurrentIndex(model_index, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)

assert "Normal message" in current_tab._detail_panel.toPlainText()
    assert "INFO" in current_tab._detail_panel.toPlainText()

def test_json_pretty_print(qtbot, populated_tab):
    current_tab, window = populated_tab

model_index = current_tab.model.index(1, 0)
    current_tab.table_view.selectionModel().setCurrentIndex(model_index, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)

panel_text = current_tab._detail_panel.toPlainText()
    assert '"key": "value"' in panel_text
    assert '\n        "key"' in panel_text

def test_relative_time_toggle(qtbot, populated_tab):
    current_tab, window = populated_tab

    assert window.toolbar_builder.action_rel_time.isChecked() is False
    assert current_tab.model._show_relative_time is False

current_tab.model.toggle_relative_time()

    assert current_tab.model._show_relative_time is True

def test_font_zooming(qtbot, populated_tab):
    current_tab, window = populated_tab

    initial_size = window._table_font_size

    window._zoom_font(1)
    assert window._table_font_size == initial_size + 1

    window._zoom_font(-2)
    assert window._table_font_size == initial_size - 1

def test_copy_selected(qtbot, populated_tab):
    current_tab, window = populated_tab

current_tab.table_view.selectAll()
    window._copy_selected_rows()

copied_text = QApplication.clipboard().text()

    assert copied_text is not None
    assert "Normal message" in copied_text
    assert "JSON message" in copied_text

def test_theme_switching(qtbot, populated_tab):
    current_tab, window = populated_tab

initial_theme = window.config.get("theme", {}).get("name")

    window.change_theme("dark")

assert window.config["theme"]["name"] == "dark"
``````

# FILE: tests\integration\uat\test_filtering.py

```python
import pytest
from datetime import datetime
from PySide6.QtCore import Qt
from logview.ui.main_window import MainWindow
from logview.models import LogEntry

@pytest.fixture
def app_config():
    return {
        "server": {"host": "127.0.0.1", "port": 0},
        "display": {"max_lines": 1000},
        "log_format": {"pattern": r"^\[(?P<timestamp>.*?)\]\s*\[(?P<level>\w+)\]\s*(?P<message>.*)"}
    }

@pytest.fixture
def populated_tab(qtbot, app_config, monkeypatch):
    monkeypatch.setattr("logview.ui.components.log_tab.ReceiverWorker.start", lambda self: None)

    window = MainWindow(app_config)
    qtbot.addWidget(window)
    current_tab = window.tab_widget.currentWidget()

    logs = [
        LogEntry(raw="[2023-10-01 10:00:00] [INFO] Database connection successful", level="INFO", message="Database connection successful", parsed_dt=datetime(2023, 10, 1, 10, 0, 0)),
        LogEntry(raw="[2023-10-01 10:05:00] [WARNING] High memory usage detected", level="WARNING", message="High memory usage detected", parsed_dt=datetime(2023, 10, 1, 10, 5, 0)),
        LogEntry(raw="[2023-10-01 10:10:00] [ERROR] Timeout connecting to host", level="ERROR", message="Timeout connecting to host", parsed_dt=datetime(2023, 10, 1, 10, 10, 0)),
        LogEntry(raw="[2023-10-01 10:15:00] [ERROR] Missing configuration file", level="ERROR", message="Missing configuration file", parsed_dt=datetime(2023, 10, 1, 10, 15, 0))
    ]

    current_tab.on_logs_received(logs)
    return current_tab

def test_level_filtering(populated_tab):
    assert populated_tab.model.rowCount() == 4

for cb in populated_tab.filter_panel.level_checkboxes:
        cb.setChecked(cb.text() == "ERROR")
    assert populated_tab.model.rowCount() == 2
    assert populated_tab.model._filtered_logs[0].level == "ERROR"
    assert populated_tab.model._filtered_logs[1].level == "ERROR"

def test_standard_text_filter(populated_tab):

    populated_tab.filter_panel.search_input.setText("timeout")
    assert populated_tab.model.rowCount() == 1
    assert populated_tab.model._filtered_logs[0].message == "Timeout connecting to host"

def test_regex_text_filter(populated_tab):

    populated_tab.filter_panel.regex_checkbox.setChecked(True)
    populated_tab.filter_panel.search_input.setText(r"memory\s+usage")

    assert populated_tab.model.rowCount() == 1
    assert populated_tab.model._filtered_logs[0].level == "WARNING"

def test_time_range_filter(populated_tab):

    from_dt = datetime(2023, 10, 1, 10, 4, 0)
    to_dt = datetime(2023, 10, 1, 10, 12, 0)

populated_tab.time_range_widget.range_changed.emit(from_dt, to_dt)

    assert populated_tab.model.rowCount() == 2
    assert populated_tab.model._filtered_logs[0].level == "WARNING"
    assert populated_tab.model._filtered_logs[1].message == "Timeout connecting to host"

def test_combined_filters(populated_tab):

    for cb in populated_tab.filter_panel.level_checkboxes:
        cb.setChecked(cb.text() == "ERROR")
    populated_tab.filter_panel.search_input.setText("configuration")

    assert populated_tab.model.rowCount() == 1
    assert populated_tab.model._filtered_logs[0].message == "Missing configuration file"
``````

# FILE: tests\integration\uat\test_find_navigation.py

```python
import pytest
from PySide6.QtCore import Qt
from logview.ui.main_window import MainWindow
from logview.models import LogEntry

@pytest.fixture
def app_config():
    return {
        "server": {"host": "127.0.0.1", "port": 0},
        "display": {"max_lines": 1000},
        "log_format": {"pattern": r"^\[(?P<timestamp>.*?)\]\s*\[(?P<level>\w+)\]\s*(?P<message>.*)"}
    }

@pytest.fixture
def populated_tab(qtbot, app_config, monkeypatch):
    monkeypatch.setattr("logview.ui.components.log_tab.ReceiverWorker.start", lambda self: None)

    window = MainWindow(app_config)
    qtbot.addWidget(window)

    window.show()
    qtbot.waitExposed(window)

    current_tab = window.tab_widget.currentWidget()

    logs = [
        LogEntry(raw="[2023] [INFO] Request starting for user 123", message="Request starting for user 123"),
        LogEntry(raw="[2023] [DEBUG] Processing user 123 payload", message="Processing user 123 payload"),
        LogEntry(raw="[2023] [ERROR] Timeout for user 123", message="Timeout for user 123")
    ]

    current_tab.on_logs_received(logs)
    return current_tab, window

def test_open_find_bar(qtbot, populated_tab):
    current_tab, window = populated_tab

assert current_tab._find_bar.isVisible() is False

window._toggle_find_bar()

    assert current_tab._find_bar.isVisible() is True
    assert current_tab._find_bar._input.hasFocus() is True

def test_highlight_text(qtbot, populated_tab):
    current_tab, window = populated_tab

current_tab._find_bar._input.setText("123")

assert current_tab._delegate._term == "123"

def test_next_prev_navigation(qtbot, populated_tab):
    current_tab, window = populated_tab

current_tab._find_bar._input.setText("user")
    current_tab._on_find_term_changed("user", False)

current_tab._find_bar.navigate.emit(1)
    selected_row = current_tab.table_view.selectionModel().currentIndex().row()
    assert selected_row == 0
    assert "1/3" in current_tab._find_bar._match_label.text()

current_tab._find_bar.navigate.emit(1)
    selected_row = current_tab.table_view.selectionModel().currentIndex().row()
    assert selected_row == 1
    assert "2/3" in current_tab._find_bar._match_label.text()

current_tab._find_bar.navigate.emit(-1)
    selected_row = current_tab.table_view.selectionModel().currentIndex().row()
    assert selected_row == 0
    assert "1/3" in current_tab._find_bar._match_label.text()

def test_close_find_bar(qtbot, populated_tab):
    current_tab, window = populated_tab

window._toggle_find_bar()
    current_tab._find_bar._input.setText("user")
    assert current_tab._delegate._term == "user"

current_tab._find_bar.close_bar()

    assert current_tab._find_bar.isVisible() is False

    assert current_tab._delegate._term == ""
``````

# FILE: tests\integration\uat\test_ingestion.py

```python
import pytest
import asyncio
import tempfile
import os
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from logview.ui.main_window import MainWindow
from logview.models import LogEntry

@pytest.fixture
def app_config():
    return {
        "server": {"host": "127.0.0.1", "port": 0},
        "display": {"max_lines": 1000},
        "log_format": {"pattern": r"^\[(?P<timestamp>.*?)\]\s*\[(?P<level>\w+)\]\s*(?P<message>.*)"}
    }

@pytest.mark.asyncio
async def test_tcp_connection(qtbot, app_config, monkeypatch):
    window = MainWindow(app_config)
    qtbot.addWidget(window)

    current_tab = window.tab_widget.currentWidget()

for _ in range(50):
        if current_tab.receiver_thread._receivers and getattr(current_tab.receiver_thread._receivers[0], "server", None) is not None:
            break
        await asyncio.sleep(0.1)

addr = current_tab.receiver_thread._receivers[0].server.sockets[0].getsockname()
    port = addr[1]

reader, writer = await asyncio.open_connection("127.0.0.1", port)
    writer.write(b"[2023-10-27 10:00:00] [INFO] TCP Test Line\n")
    await writer.drain()

for _ in range(50):
        if current_tab.model.rowCount() == 1:
            break
        await asyncio.sleep(0.1)
        QApplication.processEvents()

    assert current_tab.model.rowCount() == 1
    assert current_tab.model._all_logs[0].message == "TCP Test Line"
    assert current_tab.model._all_logs[0].level == "INFO"

assert "Connected" in window.status_bar._status_connection.text()
    assert "Total: 1" in window.status_bar._status_total.text()

    writer.close()
    await writer.wait_closed()

@pytest.mark.asyncio
async def test_file_tailing(qtbot, app_config):
    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        filepath = f.name

    try:
        app_config["tail_file"] = filepath
        window = MainWindow(app_config)
        qtbot.addWidget(window)

        await asyncio.sleep(0.5)

        with open(filepath, "a") as f:
            f.write("[2023-10-27 10:00:01] [ERROR] File Test Line\n")
            f.flush()

        current_tab = window.tab_widget.currentWidget()
        for _ in range(50):
            if current_tab.model.rowCount() == 1:
                break
            await asyncio.sleep(0.1)
            QApplication.processEvents()

        assert current_tab.model.rowCount() == 1
        assert current_tab.model._all_logs[0].message == "File Test Line"
        assert current_tab.model._all_logs[0].level == "ERROR"

    finally:
        if 'window' in locals():
            window.close()
        try:
            os.unlink(filepath)
        except Exception:
            pass

def test_pause_resume_stream(qtbot, app_config, monkeypatch):
    monkeypatch.setattr("logview.ui.components.log_tab.ReceiverWorker.start", lambda self: None)

    window = MainWindow(app_config)
    qtbot.addWidget(window)
    current_tab = window.tab_widget.currentWidget()

window.toolbar_builder.action_pause.trigger()
    assert current_tab.is_paused is True

log1 = LogEntry(raw="[2023] [INFO] Msg1", message="Msg1")
    log2 = LogEntry(raw="[2023] [INFO] Msg2", message="Msg2")
    current_tab.on_logs_received([log1, log2])

assert current_tab.model.rowCount() == 0
    assert len(current_tab.pending_logs) == 2
    assert "Pending Buffer: 2" in window.status_bar._status_pending.text()

window.toolbar_builder.action_pause.trigger()
    assert current_tab.is_paused is False
    assert current_tab.model.rowCount() == 2
    assert len(current_tab.pending_logs) == 0
    assert "Pending Buffer: 0" in window.status_bar._status_pending.text()

def test_auto_scroll_logic(qtbot, app_config, monkeypatch):
    monkeypatch.setattr("logview.ui.components.log_tab.ReceiverWorker.start", lambda self: None)

    window = MainWindow(app_config)
    qtbot.addWidget(window)
    current_tab = window.tab_widget.currentWidget()

    assert current_tab.auto_scroll is True

scrollbar = current_tab.table_view.verticalScrollBar()

    scrollbar.setMaximum(100)
    current_tab._on_scroll(80)

    assert current_tab.auto_scroll is False

current_tab._on_scroll(98)
    assert current_tab.auto_scroll is True

@pytest.mark.asyncio
async def test_new_source_tab(qtbot, app_config, monkeypatch):
    def mock_add_source_tab(*args, **kwargs):
        pass

    window = MainWindow(app_config)
    qtbot.addWidget(window)

    initial_tabs = window.tab_widget.count()
    assert initial_tabs == 1

new_config = app_config.copy()
    new_config["server"]["port"] = 0
    window.add_source_tab("Source 2", new_config)

await asyncio.sleep(0.5)

    assert window.tab_widget.count() == 2
    new_tab = window.tab_widget.widget(1)

    assert new_tab.receiver_thread is not None
``````

# FILE: tests\integration\uat\test_session_management.py

```python
import pytest
import os
import tempfile
import json
from PySide6.QtCore import Qt
from logview.ui.main_window import MainWindow
from logview.models import LogEntry

@pytest.fixture
def app_config():
    return {
        "server": {"host": "127.0.0.1", "port": 0},
        "display": {"max_lines": 1000},
        "log_format": {"pattern": r"^\[(?P<timestamp>.*?)\]\s*\[(?P<level>\w+)\]\s*(?P<message>.*)"}
    }

@pytest.fixture
def populated_tab(qtbot, app_config, monkeypatch):
    monkeypatch.setattr("logview.ui.components.log_tab.ReceiverWorker.start", lambda self: None)

    window = MainWindow(app_config)
    qtbot.addWidget(window)
    current_tab = window.tab_widget.currentWidget()

    logs = [
        LogEntry(raw="[2023] [INFO] Msg1", level="INFO", message="Msg1"),
        LogEntry(raw="[2023] [ERROR] Msg2", level="ERROR", message="Msg2")
    ]

    current_tab.on_logs_received(logs)
    return current_tab, window

def test_export_to_text(qtbot, populated_tab, monkeypatch):
    current_tab, window = populated_tab

    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".log") as f:
        filepath = f.name

    try:

        monkeypatch.setattr("PySide6.QtWidgets.QFileDialog.getSaveFileName", lambda *args, **kwargs: (filepath, ""))

        monkeypatch.setattr("PySide6.QtWidgets.QMessageBox.information", lambda *args, **kwargs: None)

        window.export_logs()

        with open(filepath, "r") as f:
            content = f.read()

        assert "[2023] [INFO] Msg1" in content
        assert "[2023] [ERROR] Msg2" in content
    finally:
        os.unlink(filepath)

def test_save_load_session(qtbot, populated_tab, monkeypatch):
    current_tab, window = populated_tab

    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".lvsession") as f:
        filepath = f.name

    try:

        monkeypatch.setattr("PySide6.QtWidgets.QFileDialog.getSaveFileName", lambda *args, **kwargs: (filepath, ""))
        monkeypatch.setattr("PySide6.QtWidgets.QFileDialog.getOpenFileName", lambda *args, **kwargs: (filepath, ""))

        monkeypatch.setattr("PySide6.QtWidgets.QMessageBox.information", lambda *args, **kwargs: None)

        window.save_session()

with open(filepath, "r") as f:
            data = json.load(f)
            assert "entries" in data
            assert len(data["entries"]) == 2

current_tab.model.clear_logs()
        assert current_tab.model.rowCount() == 0

window.load_session()

        assert current_tab.model.rowCount() == 2
        assert current_tab.model._all_logs[0].message == "Msg1"

    finally:
        os.unlink(filepath)

def test_custom_regex(qtbot, app_config):

    from logview.ui.settings_dialog import SettingsDialog

    window = MainWindow(app_config)
    qtbot.addWidget(window)
    dialog = SettingsDialog(app_config, window)

    dialog._regex_edit.setText(r"(?P<level>INFO|ERROR)\s+(?P<message>.*)")
    dialog._sample_edit.setText("ERROR Something went wrong")

dialog._test_regex()

    assert "Match found!" in dialog._test_result_label.text()
    assert "ERROR" in dialog._test_result_label.text()
    assert "Something went wrong" in dialog._test_result_label.text()

def test_change_colors(qtbot, populated_tab):
    current_tab, window = populated_tab

    from logview.ui.settings_dialog import SettingsDialog
    dialog = SettingsDialog(window.config, window)

dialog._level_rows["ERROR"].bg_btn.set_color("

updated_cfg = dialog.get_updated_config()
    assert updated_cfg["colors"]["ERROR"]["bg"] == "
``````

# FILE: tests\unit\test_config.py

```python
import pytest
import os
import tempfile
import argparse
from unittest.mock import patch

from logview.config import get_config, load_toml


def test_load_toml_valid():
    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as f:
        f.write("[server]\nhost = '127.0.0.1'\nport = 8080\n")
        temp_path = f.name

    try:
        config = load_toml(temp_path)
        assert config["server"]["host"] == "127.0.0.1"
        assert config["server"]["port"] == 8080
    finally:
        os.unlink(temp_path)


@patch("logview.config.parse_args")
def test_get_config_with_cli_args(mock_parse_args):
    mock_args = argparse.Namespace(host="0.0.0.0", port=1234, listen_stdin=True, tail_file=None)
    mock_parse_args.return_value = mock_args

    config = get_config()

    assert config["server"]["host"] == "0.0.0.0"
    assert config["server"]["port"] == 1234
    assert config["listen_stdin"] is True
``````

# FILE: tests\unit\test_export.py

```python
import pytest
import os
import json
import tempfile
from datetime import datetime
from logview.models import LogEntry
from logview.export import export_logs, save_session, load_session


@pytest.fixture
def sample_logs():
    return [
        LogEntry(raw="raw1", timestamp="t1", level="INFO", message="msg1"),
        LogEntry(
            raw="raw2", timestamp="t2", level="ERROR", message="msg2", parsed_dt=datetime(2023, 10, 26, 10, 20, 30)
        ),
    ]


def test_export_logs_text(sample_logs):
    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        temp_path = f.name

    try:
        export_logs(sample_logs, temp_path, format="log")
        with open(temp_path, "r") as f:
            content = f.read()
        assert "raw1" in content
        assert "raw2" in content
    finally:
        os.unlink(temp_path)


def test_export_logs_json(sample_logs):
    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        temp_path = f.name

    try:
        export_logs(sample_logs, temp_path, format="json")
        with open(temp_path, "r") as f:
            data = json.load(f)
        assert len(data) == 2
        assert data[0]["level"] == "INFO"
        assert data[1]["message"] == "msg2"
    finally:
        os.unlink(temp_path)


def test_save_load_session(sample_logs):
    with tempfile.NamedTemporaryFile("w", suffix=".lvsession", delete=False) as f:
        temp_path = f.name

    try:
        save_session(sample_logs, temp_path)

        loaded_entries = load_session(temp_path)

        assert len(loaded_entries) == len(sample_logs)

        for orig, loaded in zip(sample_logs, loaded_entries):
            assert orig.raw == loaded.raw
            assert orig.timestamp == loaded.timestamp
            assert orig.level == loaded.level
            assert orig.message == loaded.message
            assert orig.parsed_dt == loaded.parsed_dt
            assert loaded.is_new is False
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_save_session_appends_extension(sample_logs):
    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        base_path = f.name

    try:
        save_session(sample_logs, base_path)

        expected_path = base_path + ".lvsession"
        assert os.path.exists(expected_path)

        loaded_entries = load_session(expected_path)
        assert len(loaded_entries) == len(sample_logs)

    finally:
        if os.path.exists(base_path):
            os.unlink(base_path)
        if os.path.exists(base_path + ".lvsession"):
            os.unlink(base_path + ".lvsession")


def test_load_session_handles_invalid_date():
    with tempfile.NamedTemporaryFile("w", suffix=".lvsession", delete=False) as f:
        temp_path = f.name
        data = {
            "version": 1,
            "saved_at": datetime.now().isoformat(),
            "entries": [
                {
                    "raw": "invalid date",
                    "timestamp": "bad_time",
                    "level": "INFO",
                    "message": "msg",
                    "parsed_dt": "not-a-valid-iso-date",
                }
            ],
        }
        json.dump(data, f)

    try:
        loaded_entries = load_session(temp_path)

        assert len(loaded_entries) == 1
        assert loaded_entries[0].parsed_dt is None
        assert loaded_entries[0].raw == "invalid date"
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
``````

# FILE: tests\unit\test_filter_engine.py

```python
import pytest
from logview.controllers.filter_engine import LogFilterEngine
from logview.models import LogEntry


def test_filter_engine_multi_level():
    engine = LogFilterEngine()
    engine.set_level_filter(["ERROR", "CRITICAL"])

    log_info = LogEntry(raw="info log", level="INFO")
    log_error = LogEntry(raw="error log", level="ERROR")
    log_critical = LogEntry(raw="critical log", level="CRITICAL")
    log_none = LogEntry(raw="no level log", level=None)

    assert not engine.matches(log_info)
    assert engine.matches(log_error)
    assert engine.matches(log_critical)
    assert engine.matches(log_none)
``````

# FILE: tests\unit\test_log_generator.py

```python
import json
import re
from tools.log_generator import generate_log_line, MODULE_SUBMODULES

def test_generate_log_line_structured():
    levels = ["INFO"]
    weights = [1.0]
    line = generate_log_line("structured", levels, weights, 42)

pattern = r"^\[42\] \[.*?\] \[INFO\] \[(?P<module>\w+)\] \[(?P<submodule>\w+)\] .*?\n$"
    match = re.match(pattern, line)
    assert match is not None
    
    module = match.group("module")
    submodule = match.group("submodule")
    assert (module, submodule) in MODULE_SUBMODULES

def test_generate_log_line_json():
    levels = ["ERROR"]
    weights = [1.0]
    line = generate_log_line("json", levels, weights, 42)
    
    data = json.loads(line)
    assert data["index"] == 42
    assert "timestamp" in data
    assert data["level"] == "ERROR"
    assert "module" in data
    assert "submodule" in data
    assert "message" in data
    
    assert (data["module"], data["submodule"]) in MODULE_SUBMODULES
``````

# FILE: tests\unit\test_log_parser.py

```python
import pytest
from logview.log_parser import LogParser
from logview.models import LogEntry

def test_log_parser_valid_pattern():
    pattern = r"^\[(?P<timestamp>.*?)\]\s*\[(?P<level>\w+)\]\s*(?P<message>.*)"
    parser = LogParser(pattern)
    log_line = "[2023-10-27 10:00:00] [INFO] Application started successfully."

    entry = parser.parse(log_line)

    assert isinstance(entry, LogEntry)
    assert entry.timestamp == "2023-10-27 10:00:00"
    assert entry.level == "INFO"
    assert entry.message == "Application started successfully."
    assert entry.raw == log_line

def test_log_parser_invalid_pattern():
    pattern = r"^\[(?P<timestamp>.*?)\]\s*\[(?P<level>\w+)\]\s*(?P<message>.*)"
    parser = LogParser(pattern)
    log_line = "This line does not match the pattern."

    entry = parser.parse(log_line)

    assert entry.timestamp is None
    assert entry.level is None
    assert entry.message == log_line
    assert entry.raw == log_line

def test_log_parser_missing_named_groups():
    pattern = r"^(.*)$"
    parser = LogParser(pattern)
    log_line = "Just some text"

    entry = parser.parse(log_line)

    assert entry.timestamp is None
    assert entry.level is None
    assert entry.message == "Just some text"

def test_log_parser_json_fallback_valid():
    pattern = r"^\[(?P<timestamp>.*?)\]\s*\[(?P<level>\w+)\]\s*(?P<message>.*)"
    parser = LogParser(pattern)
    log_line = '{"timestamp": "2023-10-27 10:00:00", "level": "info", "message": "JSON success"}'

    entry = parser.parse(log_line)

    assert entry.timestamp == "2023-10-27 10:00:00"
    assert entry.level == "INFO"
    assert entry.message == "JSON success"
    assert entry.raw == log_line

def test_log_parser_json_fallback_alt_fields():
    pattern = r"^\[(?P<timestamp>.*?)\]\s*\[(?P<level>\w+)\]\s*(?P<message>.*)"
    parser = LogParser(pattern)
    log_line = '{"time": "2023-10-27 10:01:00", "severity": "warn", "text": "Alt success"}'

    entry = parser.parse(log_line)

    assert entry.timestamp == "2023-10-27 10:01:00"
    assert entry.level == "WARN"
    assert entry.message == "Alt success"
    assert entry.raw == log_line

def test_log_parser_json_fallback_missing_fields():
    pattern = r"^\[(?P<timestamp>.*?)\]\s*\[(?P<level>\w+)\]\s*(?P<message>.*)"
    parser = LogParser(pattern)
    log_line = '{"other": "value"}'

    entry = parser.parse(log_line)

    assert entry.timestamp is None
    assert entry.level is None
    assert entry.message == log_line
    assert entry.raw == log_line

def test_log_parser_json_fallback_invalid_json():
    pattern = r"^\[(?P<timestamp>.*?)\]\s*\[(?P<level>\w+)\]\s*(?P<message>.*)"
    parser = LogParser(pattern)
    log_line = "{this is not valid json, but starts with a brace"

    entry = parser.parse(log_line)

    assert entry.timestamp is None
    assert entry.level is None
    assert entry.message == log_line
    assert entry.raw == log_line

def test_default_config_matches_generator_logs():
    from unittest.mock import patch
    import argparse
    from logview.config import get_config
    from logview.log_parser import LogParser
    from datetime import datetime
    
    with patch("logview.config.parse_args") as mock_parse_args:
        mock_parse_args.return_value = argparse.Namespace(host=None, port=None, listen_stdin=False, tail_file=None)
        config = get_config()
        
    pattern = config["log_format"]["pattern"]
    parser = LogParser(pattern)
    
    levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    msg = "User login successful"
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
    for lvl in levels:
        log_line = f"[{ts}] [{lvl}] {msg}\n"
        entry = parser.parse(log_line)
        
        assert entry.timestamp == ts
        assert entry.level == lvl
        assert entry.message == msg

def test_log_parser_module_submodule():
    pattern = r"^(?:\[(?P<timestamp>.*?)\])?\s*(?:\[(?P<level>\w+)\])?\s*(?:\[(?P<module>\w+)\])?\s*(?:\[(?P<submodule>\w+)\])?\s*(?P<message>.*)"
    parser = LogParser(pattern)
    log_line = "[2023-10-27 10:00:00] [INFO] [Network] [Socket] Connection established"

    entry = parser.parse(log_line)

    assert entry.timestamp == "2023-10-27 10:00:00"
    assert entry.level == "INFO"
    assert entry.module == "Network"
    assert entry.submodule == "Socket"
    assert entry.message == "Connection established"
    assert entry.raw == log_line

def test_log_parser_json_module_submodule():
    pattern = r"^(?:\[(?P<timestamp>.*?)\])?\s*(?:\[(?P<level>\w+)\])?\s*(?:\[(?P<module>\w+)\])?\s*(?:\[(?P<submodule>\w+)\])?\s*(?P<message>.*)"
    parser = LogParser(pattern)
    log_line = '{"timestamp": "2023", "level": "info", "module": "Net", "submodule": "Sock", "message": "msg"}'

    entry = parser.parse(log_line)

    assert entry.timestamp == "2023"
    assert entry.level == "INFO"
    assert entry.module == "Net"
    assert entry.submodule == "Sock"
    assert entry.message == "msg"

def test_log_parser_index():
    pattern = r"^(?:\[(?P<index>\d+)\])?\s*\[(?P<timestamp>.*?)\]\s*\[(?P<level>\w+)\](?:\s*\[(?P<module>\w+)\])?(?:\s*\[(?P<submodule>\w+)\])?\s*(?P<message>.*)"
    parser = LogParser(pattern)
    log_line = "[15] [2023-10-27 10:00:00] [INFO] [Network] [Socket] Connection established"

    entry = parser.parse(log_line)

    assert entry.index == "15"
    assert entry.timestamp == "2023-10-27 10:00:00"
    assert entry.level == "INFO"
    assert entry.module == "Network"
    assert entry.submodule == "Socket"
    assert entry.message == "Connection established"

def test_log_parser_continuation_lines():
    from logview.config import get_config
    config = get_config()
    pattern = config["log_format"]["pattern"]
    parser = LogParser(pattern)

assert parser.is_new_entry("[1] [2026-07-18 12:00:00.000] [INFO] [Auth] [Login] message") is True
    assert parser.is_new_entry("[2026-07-18 12:00:00.000] [INFO] [Auth] [Login] message") is True

assert parser.is_new_entry("at db.py:45") is False
    assert parser.is_new_entry("ConnectionError: Timeout while waiting for connection pool") is False
    assert parser.is_new_entry("    at main.py:12") is False
``````

# FILE: tests\unit\test_models.py

```python
import pytest
from logview.models import LogEntry


def test_log_entry_auto_id():
    entry1 = LogEntry(raw="test1")
    entry2 = LogEntry(raw="test2")

    assert entry1.id is not None
    assert entry2.id is not None
    assert entry1.id != entry2.id


def test_log_entry_custom_id():
    entry = LogEntry(raw="test", id="custom_id")
    assert entry.id == "custom_id"
``````

# FILE: tests\unit\test_proxy_model.py

```python
from datetime import datetime
from PySide6.QtCore import QModelIndex
from logview.ui.log_model import LogModel, LogFilterProxyModel
from logview.models import LogEntry

def test_proxy_model_filtering_and_sorting():

    model = LogModel(None, max_lines=100)
    proxy = LogFilterProxyModel()
    proxy.setSourceModel(model)

logs = [
        LogEntry(raw="[1] [2026-07-18 12:00:00] [INFO] Msg A", timestamp="2026-07-18 12:00:00", level="INFO", message="Msg A", index="1", parsed_dt=datetime(2026, 7, 18, 12, 0, 0)),
        LogEntry(raw="[2] [2026-07-18 12:05:00] [WARNING] Msg B", timestamp="2026-07-18 12:05:00", level="WARNING", message="Msg B", index="2", parsed_dt=datetime(2026, 7, 18, 12, 5, 0)),
        LogEntry(raw="[3] [2026-07-18 12:10:00] [ERROR] Msg C", timestamp="2026-07-18 12:10:00", level="ERROR", message="Msg C", index="3", parsed_dt=datetime(2026, 7, 18, 12, 10, 0)),
    ]
    model.add_logs(logs)

assert proxy.rowCount() == 3

proxy.set_filter("", ["ERROR"], False, False)
    assert proxy.rowCount() == 1
    assert proxy.get_entry_at_row(0).message == "Msg C"

proxy.set_filter("Msg B", ["INFO", "WARNING", "ERROR"], False, False)
    assert proxy.rowCount() == 1
    assert proxy.get_entry_at_row(0).message == "Msg B"

from_dt = datetime(2026, 7, 18, 12, 2, 0)
    to_dt = datetime(2026, 7, 18, 12, 7, 0)
    proxy.set_filter("", ["INFO", "WARNING", "ERROR"], False, False)
    proxy.set_time_range(from_dt, to_dt)
    assert proxy.rowCount() == 1
    assert proxy.get_entry_at_row(0).message == "Msg B"

proxy.set_time_range(None, None)
    proxy.set_filter("", ["INFO", "WARNING", "ERROR"], False, False)
    assert proxy.rowCount() == 3

assert len(proxy._warning_rows) == 1
    assert proxy._warning_rows[0] == 1
    assert len(proxy._error_rows) == 1
    assert proxy._error_rows[0] == 2
``````

# FILE: tests\unit\test_receiver_delay.py

```python
import pytest
import asyncio
import os
import tempfile
from logview.log_parser import LogParser, MultiLineBuffer
from logview.receiver import FileTailReceiver

PATTERN = r"(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (?P<level>\w+) (?P<message>.*)"

@pytest.fixture
def parser():
    return LogParser(PATTERN)

@pytest.fixture
def temp_log_file():
    fd, path = tempfile.mkstemp()
    os.close(fd)
    yield path
    os.remove(path)

@pytest.mark.asyncio
async def test_multiline_buffer_holds_last_log_indefinitely(parser, temp_log_file):

with open(temp_log_file, "w") as f:
        f.write("2023-10-27 10:00:00 INFO Initial old log\n")

    queue = asyncio.Queue()
    receiver = FileTailReceiver(temp_log_file, parser, queue)

await receiver.start()

await asyncio.sleep(0.2)

assert queue.qsize() == 0, "Queue should be empty as receiver tails to the end"

with open(temp_log_file, "a") as f:
        f.write("2023-10-27 10:01:00 ERROR A crash occurred\n")
        f.flush()

await asyncio.sleep(0.5)

assert queue.qsize() == 1, "The single log entry should have been flushed and emitted to the queue after a timeout."

    entry = await queue.get()
    assert entry.level == "ERROR"
    assert "A crash occurred" in entry.message

with open(temp_log_file, "a") as f:
        f.write("2023-10-27 10:02:00 WARNING Stack trace below:\n")
        f.flush()

with open(temp_log_file, "a") as f:
        f.write("  File \"main.py\", line 42\n")
        f.write("    raise ValueError(\"Bad input\")\n")
        f.flush()

await asyncio.sleep(0.5)

    assert queue.qsize() == 1, "The multi-line log entry should have been grouped and emitted."
    ml_entry = await queue.get()
    assert ml_entry.level == "WARNING"
    assert "Stack trace below:" in ml_entry.message
    assert "File \"main.py\"" in ml_entry.message
    assert "raise ValueError" in ml_entry.message

    await receiver.stop()

@pytest.mark.asyncio
async def test_file_tail_receiver_extreme_edge_cases(parser, temp_log_file):
    
    queue = asyncio.Queue()
    receiver = FileTailReceiver(temp_log_file, parser, queue)
    await receiver.start()
    await asyncio.sleep(0.1)

with open(temp_log_file, "a") as f:
        f.write("\n")
        f.write("     \n")
        f.write("{bad json}\n")
        f.flush()

await asyncio.sleep(0.5)

assert queue.qsize() > 0
    while not queue.empty():
        await queue.get()

long_str = "x" * 100000
    with open(temp_log_file, "a") as f:
        f.write(f"2023-10-27 10:03:00 INFO {long_str}\n")
        f.flush()

    await asyncio.sleep(0.5)
    assert queue.qsize() == 1
    entry = await queue.get()
    assert long_str in entry.message

    await receiver.stop()
``````

# FILE: tests\unit\test_settings_dialog.py

```python
import pytest
import os
import tempfile
import json
from typing import Dict, Any

from logview.ui.settings_dialog import save_config_to_toml
from logview.config import load_toml

def test_save_config_to_toml_escapes_malicious_host():
    
    malicious_host = 'localhost"\n[malicious]\nkey="value'
    config: Dict[str, Any] = {
        "server": {
            "host": malicious_host,
            "port": 9999
        }
    }

    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as f:
        temp_path = f.name

    try:
        save_config_to_toml(config, temp_path)

with open(temp_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "[malicious]" not in content.split("\n"), "Malicious section was successfully injected!"
        assert "key=\"value\"" not in content.split("\n"), "Malicious key was successfully injected!"

escaped_host = json.dumps(malicious_host)
        assert f"host = {escaped_host}" in content

parsed_config = load_toml(temp_path)
        assert parsed_config["server"]["host"] == malicious_host
        assert "malicious" not in parsed_config

    finally:
        os.unlink(temp_path)
``````

# FILE: tools\log_generator.py

```python
import argparse
import asyncio
import json
import random
import time
from datetime import datetime

MESSAGES = [
    ("INFO", "User login successful"),
    ("WARNING", "Database connection timeout"),
    ("ERROR", "File not found: config.yaml"),
    ("CRITICAL", "Out of memory error in worker thread"),
    ("DEBUG", "Cache miss for key: user_profile"),
    ("INFO", "Process started successfully"),
    ("WARNING", "Unexpected payload received"),
    ("INFO", "Graceful shutdown initiated"),
    ("DEBUG", "Connection reset by peer"),
    ("INFO", "Order processed successfully, ID: 98124"),
    ("WARNING", "API response latency is high (1.5s)"),
    ("ERROR", "Invalid authorization signature"),
    ("CRITICAL", "Disk space critical: 98% full on /data"),
    ("DEBUG", "Entering loop query for batch size 100"),
]

STACK_TRACES = [
    ("ERROR", "Database connection failed", "ConnectionError: Timeout while waiting for connection pool\n    at db.py:45\n    at main.py:12\n    at server.py:89"),
    ("CRITICAL", "NullPointerException in main logic", "NullPointerException: Cannot invoke 'String.hashCode()' because 'value' is null\n    at com.example.App.process(App.java:102)\n    at com.example.App.main(App.java:45)"),
    ("ERROR", "HTTP request failed", "RequestException: 504 Gateway Timeout for URL: https://api.service.internal/v1/data\n    at httpx._client.send(client.py:202)\n    at services.gateway.fetch(gateway.py:12)"),
]

MODULE_SUBMODULES = [
    ("Auth", "Login"),
    ("Auth", "Session"),
    ("Database", "Query"),
    ("Database", "Pool"),
    ("API", "Router"),
    ("API", "Handler"),
    ("Cache", "Redis"),
    ("Worker", "Queue"),
    ("Worker", "Scheduler"),
]

def parse_args():
    parser = argparse.ArgumentParser(description="Log Generator for Log Viewer")
    parser.add_argument("--host", type=str, default="localhost", help="Host to connect to")
    parser.add_argument("--port", type=int, default=9999, help="Port to connect to")
    parser.add_argument("--rate", type=float, default=2.0, help="Logs per second")
    parser.add_argument("--duration", type=int, default=0, help="Duration to run in seconds (0 = forever)")
    parser.add_argument("--pattern", type=str, choices=["mixed", "structured", "json", "apache"], default="mixed", help="Format of the logs")
    parser.add_argument("--levels", type=str, default="DEBUG:20,INFO:50,WARNING:15,ERROR:10,CRITICAL:5", help="Comma-separated LEVEL:Weight")
    return parser.parse_args()

def parse_levels(level_str):
    levels = []
    weights = []
    for pair in level_str.split(","):
        lvl, w = pair.split(":")
        levels.append(lvl.strip())
        weights.append(float(w))
    return levels, weights

def generate_log_line(pattern, levels, weights, index):
    module, submodule = random.choice(MODULE_SUBMODULES)

if pattern == "mixed" and random.random() < 0.25:
        level, msg, stack = random.choice(STACK_TRACES)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        return f"[{index}] [{ts}] [{level}] [{module}] [{submodule}] {msg}\n{stack}\n"

level = random.choices(levels, weights=weights)[0]
    msg_choices = [m for l, m in MESSAGES if l == level]
    if msg_choices:
        msg = random.choice(msg_choices)
    else:
        msg = random.choice(MESSAGES)[1]
        
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    selected_pattern = pattern
    if pattern == "mixed":

        selected_pattern = random.choices(["structured", "json"], weights=[0.8, 0.2])[0]

    if selected_pattern == "structured":
        return f"[{index}] [{ts}] [{level}] [{module}] [{submodule}] {msg}\n"
    elif selected_pattern == "json":
        return json.dumps({"index": index, "timestamp": ts, "level": level, "module": module, "submodule": submodule, "message": msg}) + "\n"
    elif selected_pattern == "apache":
        return f'127.0.0.1 - - [{ts}] "{level} /api/v1/resource HTTP/1.1" 200 {random.randint(100, 5000)} "{msg}"\n'
    return f"[{index}] [{ts}] [{level}] [{module}] [{submodule}] {msg}\n"

async def main():
    args = parse_args()
    levels, weights = parse_levels(args.levels)

    print(f"Connecting to {args.host}:{args.port}...")
    writer = None
    while True:
        try:
            reader, writer = await asyncio.open_connection(args.host, args.port)
            break
        except Exception as e:
            print(f"Failed to connect: {e}. Retrying in 2 seconds...")
            await asyncio.sleep(2)

    print(f"Connected. Generating logs at {args.rate} msgs/sec for {'forever' if args.duration == 0 else args.duration} seconds.")

    start_time = time.time()
    sleep_interval = 1.0 / args.rate
    logs_sent = 0

    try:
        while True:
            current_time = time.time()
            if args.duration > 0 and current_time - start_time > args.duration:
                break

            line = generate_log_line(args.pattern, levels, weights, logs_sent + 1)
            writer.write(line.encode('utf-8'))
            await writer.drain()
            logs_sent += 1

            if logs_sent % 10 == 0:
                elapsed = current_time - start_time
                actual_rate = logs_sent / elapsed if elapsed > 0 else 0
                print(f"Sent: {logs_sent} | Actual Rate: {actual_rate:.2f} msgs/sec")

            await asyncio.sleep(sleep_interval)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Error during sending: {e}")
    finally:
        print(f"Finished. Total sent: {logs_sent}")
        if writer:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

if __name__ == "__main__":
    asyncio.run(main())
``````

# FILE: tools\run_test_env.py

```python
import subprocess
import time
import sys
import os

def main():
    
    print("Starting Log Viewer GUI...")

    python_exe = sys.executable

gui_process = subprocess.Popen([python_exe, "-m", "logview"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

print("Waiting for GUI to initialize (2 seconds)...")
    time.sleep(2)

    print("Starting log generator...")

    gen_process = subprocess.Popen([python_exe, "tools/log_generator.py"])

    try:

        gui_process.wait()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:

        if gui_process.poll() is None:
            gui_process.terminate()
        if gen_process.poll() is None:
            gen_process.terminate()
        print("Done.")

if __name__ == "__main__":
    main()
``````

