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
    pattern = r"^(.*)$" # No named groups
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
