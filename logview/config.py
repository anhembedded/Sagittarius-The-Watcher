import argparse
import os
from typing import Any, Dict

DEFAULT_CONFIG_PATH = "logview.toml"
DEFAULT_CONFIG_CONTENT = """[server]
host = "0.0.0.0"
port = 9999

[display]
max_lines = 10000

[log_format]
pattern = "^(?:\\\\[(?P<timestamp>.*?)\\\\])?\\\\s*(?:\\\\[(?P<level>\\\\w+)\\\\])?\\\\s*(?:\\\\[(?P<module>\\\\w+)\\\\])?\\\\s*(?:\\\\[(?P<submodule>\\\\w+)\\\\])?\\\\s*(?P<message>.*)"
"""

def parse_args() -> argparse.Namespace:
    """Parses command line arguments."""
    parser = argparse.ArgumentParser(description="Log Viewer TUI")
    parser.add_argument("--host", type=str, help="TCP Server Host")
    parser.add_argument("--port", type=int, help="TCP Server Port")
    parser.add_argument("--listen-stdin", action="store_true", help="Listen from stdin instead of TCP")
    parser.add_argument("--tail-file", type=str, help="Path to a file to tail instead of TCP/stdin")
    return parser.parse_args()


def load_toml(path: str) -> Dict[str, Any]:
    """Loads a TOML configuration file with fallbacks.

    Args:
        path (str): The path to the toml file.

    Returns:
        Dict[str, Any]: The parsed configuration dictionary.
    """
    try:
        import tomllib
        with open(path, "rb") as f:
            return tomllib.load(f)
    except ImportError:
        pass

    try:
        import tomli
        with open(path, "rb") as f:
            return tomli.load(f)
    except ImportError:
        pass

    # Simple fallback parser for minimal config
    config = {}
    current_section = config
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("[") and line.endswith("]"):
                section_name = line[1:-1].strip()
                config[section_name] = {}
                current_section = config[section_name]
            elif "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip()
                # Remove quotes if they exist
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                else:
                    try:
                        val = int(val)
                    except ValueError:
                        pass
                current_section[key] = val
    return config


def get_config() -> Dict[str, Any]:
    """Retrieves the configuration, merging TOML and command line arguments.

    Returns:
        Dict[str, Any]: The final configuration dictionary.
    """
    if not os.path.exists(DEFAULT_CONFIG_PATH):
        with open(DEFAULT_CONFIG_PATH, "w", encoding="utf-8") as f:
            f.write(DEFAULT_CONFIG_CONTENT)

    config = load_toml(DEFAULT_CONFIG_PATH)

    args = parse_args()

    # Ensure sections exist
    if "server" not in config:
        config["server"] = {"host": "0.0.0.0", "port": 9999}
    if "display" not in config:
        config["display"] = {"max_lines": 10000}
    if "log_format" not in config:
        config["log_format"] = {"pattern": r"^(?:\[(?P<timestamp>.*?)\])?\s*(?:\[(?P<level>\w+)\])?\s*(?:\[(?P<module>\w+)\])?\s*(?:\[(?P<submodule>\w+)\])?\s*(?P<message>.*)"}
    else:
        # If read from TOML string, it should already be parsed correctly.
        # Ensure we have a string.
        pass

    if "colors" not in config:
        config["colors"] = {}

    if "theme" not in config:
        config["theme"] = {"name": "auto"}

    # Override with CLI args
    if args.host is not None:
        config["server"]["host"] = args.host
    if args.port is not None:
        config["server"]["port"] = args.port
    config["listen_stdin"] = args.listen_stdin

    if args.tail_file is not None:
        config["tail_file"] = args.tail_file

    return config
