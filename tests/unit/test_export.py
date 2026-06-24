import pytest
import os
import json
import tempfile
from logview.models import LogEntry
from logview.export import export_logs

@pytest.fixture
def sample_logs():
    return [
        LogEntry(raw="raw1", timestamp="t1", level="INFO", message="msg1"),
        LogEntry(raw="raw2", timestamp="t2", level="ERROR", message="msg2")
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
