import pytest
import os
import tempfile
import json
from typing import Dict, Any

from logview.ui.settings_dialog import save_config_to_toml
from logview.config import load_toml

def test_save_config_to_toml_escapes_malicious_host():
    """Test that a malicious string in host does not create new TOML sections."""
    malicious_host = 'localhost"\n[malicious]\nkey="value'
    config: Dict[str, Any] = {
        "server": {
            "host": malicious_host,
            "port": 9999
        }
    }

    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as f:
        temp_path = f.name

    try:
        save_config_to_toml(config, temp_path)

        # Read the raw contents to verify it looks right
        with open(temp_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "[malicious]" not in content.split("\n"), "Malicious section was successfully injected!"
        assert "key=\"value\"" not in content.split("\n"), "Malicious key was successfully injected!"

        # It should contain the properly escaped string using JSON dumps representation
        escaped_host = json.dumps(malicious_host)
        assert f"host = {escaped_host}" in content

        # We can also verify it's parsed back correctly using our own load_toml
        parsed_config = load_toml(temp_path)
        assert parsed_config["server"]["host"] == malicious_host
        assert "malicious" not in parsed_config

    finally:
        os.unlink(temp_path)
