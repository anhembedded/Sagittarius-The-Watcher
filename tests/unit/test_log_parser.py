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
    from unittest.mock import patch
    import argparse
    from logview.config import get_config
    with patch("logview.config.parse_args") as mock_parse_args:
        mock_parse_args.return_value = argparse.Namespace(host=None, port=None, listen_stdin=False, tail_file=None)
        config = get_config()
    pattern = config["log_format"]["pattern"]
    parser = LogParser(pattern)

    # Valid new entries
    assert parser.is_new_entry("[1] [2026-07-18 12:00:00.000] [INFO] [Auth] [Login] message") is True
    assert parser.is_new_entry("[2026-07-18 12:00:00.000] [INFO] [Auth] [Login] message") is True

    # Continuation lines must not be classified as a new entry
    assert parser.is_new_entry("at db.py:45") is False
    assert parser.is_new_entry("ConnectionError: Timeout while waiting for connection pool") is False
    assert parser.is_new_entry("    at main.py:12") is False
