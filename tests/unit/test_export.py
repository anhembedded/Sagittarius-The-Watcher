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
        LogEntry(raw="raw2", timestamp="t2", level="ERROR", message="msg2", parsed_dt=datetime(2023, 10, 26, 10, 20, 30))
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
            ]
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
