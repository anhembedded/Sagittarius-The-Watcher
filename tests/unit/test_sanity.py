import sys

from logview.config import get_config


def test_sanity_environment(monkeypatch):
    """Sanity check: ensure config loads and environment is correct before UI migration."""
    monkeypatch.setattr(sys, "argv", ["logviewer"])
    config = get_config()
    assert config is not None
    assert "server" in config
    assert "display" in config
    assert "colors" in config
