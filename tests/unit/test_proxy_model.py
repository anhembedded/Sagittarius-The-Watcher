from datetime import datetime
from PySide6.QtCore import QModelIndex
from logview.ui.log_model import LogModel, LogFilterProxyModel
from logview.models import LogEntry


def test_proxy_model_filtering_and_sorting():
    # Setup LogModel and LogFilterProxyModel
    model = LogModel(None, max_lines=100)
    proxy = LogFilterProxyModel()
    proxy.setSourceModel(model)

    # Ingest test logs
    logs = [
        LogEntry(raw="[1] [2026-07-18 12:00:00] [INFO] Msg A", timestamp="2026-07-18 12:00:00", level="INFO", message="Msg A", index="1", parsed_dt=datetime(2026, 7, 18, 12, 0, 0)),
        LogEntry(raw="[2] [2026-07-18 12:05:00] [WARNING] Msg B", timestamp="2026-07-18 12:05:00", level="WARNING", message="Msg B", index="2", parsed_dt=datetime(2026, 7, 18, 12, 5, 0)),
        LogEntry(raw="[3] [2026-07-18 12:10:00] [ERROR] Msg C", timestamp="2026-07-18 12:10:00", level="ERROR", message="Msg C", index="3", parsed_dt=datetime(2026, 7, 18, 12, 10, 0)),
    ]
    model.add_logs(logs)

    # Check that initial proxy matches source count
    assert proxy.rowCount() == 3

    # Check level filtering via proxy
    proxy.set_filter("", ["ERROR"], False, False)
    assert proxy.rowCount() == 1
    assert proxy.get_entry_at_row(0).message == "Msg C"

    # Check text filtering via proxy
    proxy.set_filter("Msg B", ["INFO", "WARNING", "ERROR"], False, False)
    assert proxy.rowCount() == 1
    assert proxy.get_entry_at_row(0).message == "Msg B"

    # Check time range filtering via proxy
    from_dt = datetime(2026, 7, 18, 12, 2, 0)
    to_dt = datetime(2026, 7, 18, 12, 7, 0)
    proxy.set_filter("", ["INFO", "WARNING", "ERROR"], False, False)
    proxy.set_time_range(from_dt, to_dt)
    assert proxy.rowCount() == 1
    assert proxy.get_entry_at_row(0).message == "Msg B"

    # Clear filters
    proxy.set_time_range(None, None)
    proxy.set_filter("", ["INFO", "WARNING", "ERROR"], False, False)
    assert proxy.rowCount() == 3

    # Verify heatmap index rebuild
    assert len(proxy._warning_rows) == 1
    assert proxy._warning_rows[0] == 1  # Msg B is at visible index 1
    assert len(proxy._error_rows) == 1
    assert proxy._error_rows[0] == 2    # Msg C is at visible index 2
