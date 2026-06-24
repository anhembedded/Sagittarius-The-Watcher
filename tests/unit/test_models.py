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
