import argparse
import os
import tempfile
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
