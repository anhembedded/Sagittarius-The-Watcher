import json
import re
from tools.log_generator import generate_log_line, MODULE_SUBMODULES

def test_generate_log_line_structured():
    levels = ["INFO"]
    weights = [1.0]
    line = generate_log_line("structured", levels, weights, 42)
    
    # Expected format: [index] [timestamp] [level] [module] [submodule] message
    pattern = r"^\[42\] \[.*?\] \[INFO\] \[(?P<module>\w+)\] \[(?P<submodule>\w+)\] .*?\n$"
    match = re.match(pattern, line)
    assert match is not None
    
    module = match.group("module")
    submodule = match.group("submodule")
    assert (module, submodule) in MODULE_SUBMODULES

def test_generate_log_line_json():
    levels = ["ERROR"]
    weights = [1.0]
    line = generate_log_line("json", levels, weights, 42)
    
    data = json.loads(line)
    assert data["index"] == 42
    assert "timestamp" in data
    assert data["level"] == "ERROR"
    assert "module" in data
    assert "submodule" in data
    assert "message" in data
    
    assert (data["module"], data["submodule"]) in MODULE_SUBMODULES
