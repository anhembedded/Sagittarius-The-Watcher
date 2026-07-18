import pytest

@pytest.fixture(autouse=True)
def isolate_config(tmp_path, monkeypatch):
    """
    Creates a temporary configuration file to ensure tests do not overwrite
    the user's local settings.toml or logview.toml.
    """
    config_file = tmp_path / "logview_test.toml"
    config_content = r"""[server]
host = "localhost"
port = 0

[display]
max_lines = 1000

[log_format]
pattern = "^(?:\\[(?P<index>\\d+)\\])?\\s*\\[(?P<timestamp>.*?)\\]\\s*\\[(?P<level>\\w+)\\](?:\\s*\\[(?P<module>\\w+)\\])?(?:\\s*\\[(?P<submodule>\\w+)\\])?\\s*(?P<message>.*)"
"""
    config_file.write_text(config_content, encoding="utf-8")
    monkeypatch.setattr("logview.config.DEFAULT_CONFIG_PATH", str(config_file))
    return config_file
