import pytest
from datetime import datetime, timezone
from logview.log_parser import LogParser, _try_parse_datetime
from logview.models import LogEntry

def test_try_parse_datetime_empty_and_none():
    assert _try_parse_datetime(None) is None
    assert _try_parse_datetime("") is None

def test_try_parse_datetime_iso_format():
    dt = _try_parse_datetime("2023-10-27T10:00:00")
    assert dt == datetime(2023, 10, 27, 10, 0, 0)

    dt = _try_parse_datetime("2023-10-27T10:00:00+00:00")
    assert dt == datetime(2023, 10, 27, 10, 0, 0, tzinfo=timezone.utc)

def test_try_parse_datetime_timestamp_formats():
    # "%Y-%m-%d %H:%M:%S.%f"
    dt = _try_parse_datetime("2023-10-27 10:00:00.123456")
    assert dt == datetime(2023, 10, 27, 10, 0, 0, 123456)

    # "%Y-%m-%d %H:%M:%S"
    dt = _try_parse_datetime("2023-10-27 10:00:00")
    assert dt == datetime(2023, 10, 27, 10, 0, 0)

    # "%Y/%m/%d %H:%M:%S"
    dt = _try_parse_datetime("2023/10/27 10:00:00")
    assert dt == datetime(2023, 10, 27, 10, 0, 0)

    # "%d/%b/%Y:%H:%M:%S"
    dt = _try_parse_datetime("27/Oct/2023:10:00:00")
    assert dt == datetime(2023, 10, 27, 10, 0, 0)

    # "%d/%b/%Y:%H:%M:%S %z"
    dt = _try_parse_datetime("27/Oct/2023:10:00:00 +0200")
    expected = datetime.strptime("27/Oct/2023:10:00:00 +0200", "%d/%b/%Y:%H:%M:%S %z")
    assert dt == expected

def test_try_parse_datetime_with_whitespace():
    dt = _try_parse_datetime("  2023-10-27 10:00:00  ")
    assert dt == datetime(2023, 10, 27, 10, 0, 0)

def test_try_parse_datetime_invalid_input():
    assert _try_parse_datetime("not a datetime string") is None
    assert _try_parse_datetime("2023-13-27 10:00:00") is None # Invalid month

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
    pattern = r"^(.*)$" # No named groups
    parser = LogParser(pattern)
    log_line = "Just some text"

    entry = parser.parse(log_line)

    assert entry.timestamp is None
    assert entry.level is None
    assert entry.message == "Just some text"
