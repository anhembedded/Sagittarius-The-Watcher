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
