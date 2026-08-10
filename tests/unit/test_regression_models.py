from logview.models import LogEntry
from logview.ui.log_model import LogFilterProxyModel, LogModel


def test_log_model_insertion():
    model = LogModel(max_lines=10)
    entries = [LogEntry(raw="msg1", level="INFO", message="msg1"), LogEntry(raw="msg2", level="ERROR", message="msg2")]
    model.add_logs(entries)

    assert model.rowCount() == 2
    logs = model.get_all_logs()
    assert len(logs) == 2
    assert logs[0].level == "INFO"
    assert logs[1].level == "ERROR"


def test_log_model_max_lines_enforcement():
    model = LogModel(max_lines=5)
    entries = [LogEntry(raw=f"msg{i}", level="INFO", message=f"msg{i}") for i in range(10)]
    model.add_logs(entries)

    assert model.rowCount() == 5
    logs = model.get_all_logs()
    # Should keep the last 5
    assert logs[0].message == "msg5"
    assert logs[-1].message == "msg9"


def test_log_filter_proxy_model():
    source = LogModel()
    proxy = LogFilterProxyModel()
    proxy.setSourceModel(source)

    entries = [
        LogEntry(raw="info msg1", level="INFO", message="info msg"),
        LogEntry(raw="error msg2", level="ERROR", message="error msg"),
        LogEntry(raw="debug msg3", level="DEBUG", message="debug msg"),
    ]
    source.add_logs(entries)

    assert proxy.rowCount() == 3

    # Filter by level
    proxy.set_filter("", ["ERROR"], False)
    assert proxy.rowCount() == 1

    # Filter by text
    proxy.set_filter("msg", ["INFO", "ERROR", "DEBUG"], False)
    assert proxy.rowCount() == 3

    proxy.set_filter("info", ["INFO", "ERROR", "DEBUG"], False)
    assert proxy.rowCount() == 1
