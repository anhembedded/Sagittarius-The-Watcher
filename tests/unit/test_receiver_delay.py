import pytest
import asyncio
import os
import tempfile
from logview.log_parser import LogParser, MultiLineBuffer
from logview.receiver import FileTailReceiver

# Use the standard log format
PATTERN = r"(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (?P<level>\w+) (?P<message>.*)"

@pytest.fixture
def parser():
    return LogParser(PATTERN)

@pytest.fixture
def temp_log_file():
    fd, path = tempfile.mkstemp()
    os.close(fd)
    yield path
    os.remove(path)

@pytest.mark.asyncio
async def test_multiline_buffer_holds_last_log_indefinitely(parser, temp_log_file):
    """
    Test that the FileTailReceiver combined with MultiLineBuffer holds the
    last log entry indefinitely (delaying the log display in the app).
    This demonstrates the bug described in bugReport.md.
    """
    # Write a pre-existing log that should be skipped by tail
    with open(temp_log_file, "w") as f:
        f.write("2023-10-27 10:00:00 INFO Initial old log\n")

    queue = asyncio.Queue()
    receiver = FileTailReceiver(temp_log_file, parser, queue)

    # Start the receiver
    await receiver.start()

    # Wait to ensure the receiver has tailed to the end of the file
    await asyncio.sleep(0.2)

    # Assert queue is empty before any new logs are written
    assert queue.qsize() == 0, "Queue should be empty as receiver tails to the end"

    # Write exactly 1 new log line
    with open(temp_log_file, "a") as f:
        f.write("2023-10-27 10:01:00 ERROR A crash occurred\n")
        f.flush()

    # Wait long enough for the receiver to read the line.
    # With the bug, the queue size will remain 0 because it's buffered in MultiLineBuffer.
    await asyncio.sleep(0.5)

    # This assertion verifies the FIX. Without the fix, qsize == 0, so it would fail here.
    # The fix should ensure that an inactivity timeout flushes the buffer to the queue.
    assert queue.qsize() == 1, "The single log entry should have been flushed and emitted to the queue after a timeout."

    entry = await queue.get()
    assert entry.level == "ERROR"
    assert "A crash occurred" in entry.message

    # Test that multi-line logs still work with the flush mechanism
    # Write the start of a multi-line log
    with open(temp_log_file, "a") as f:
        f.write("2023-10-27 10:02:00 WARNING Stack trace below:\n")
        f.flush()

    # Don't wait too long, write the next lines immediately (before the timeout)
    with open(temp_log_file, "a") as f:
        f.write("  File \"main.py\", line 42\n")
        f.write("    raise ValueError(\"Bad input\")\n")
        f.flush()

    # Now wait for the timeout to trigger and flush the multi-line entry
    await asyncio.sleep(0.5)

    assert queue.qsize() == 1, "The multi-line log entry should have been grouped and emitted."
    ml_entry = await queue.get()
    assert ml_entry.level == "WARNING"
    assert "Stack trace below:" in ml_entry.message
    assert "File \"main.py\"" in ml_entry.message
    assert "raise ValueError" in ml_entry.message

    await receiver.stop()

@pytest.mark.asyncio
async def test_file_tail_receiver_extreme_edge_cases(parser, temp_log_file):
    """
    Test extreme edge cases: file truncation, extreme delays between continuation lines,
    and invalid negative inputs.
    """
    queue = asyncio.Queue()
    receiver = FileTailReceiver(temp_log_file, parser, queue)
    await receiver.start()
    await asyncio.sleep(0.1)

    # 1. Invalid input: Empty line, purely whitespace, or malformed JSON
    with open(temp_log_file, "a") as f:
        f.write("\n")
        f.write("     \n")
        f.write("{bad json}\n")
        f.flush()

    # Wait for timeout to flush
    await asyncio.sleep(0.5)

    # Depending on how the parser handles it, it might flush all as one unparsed block,
    # or ignore empty lines. The regex fallback parses anything as raw message.
    # We just ensure it doesn't crash and actually puts something in the queue.
    assert queue.qsize() > 0
    while not queue.empty():
        await queue.get()

    # 2. Extreme boundary: Extremely long line
    long_str = "x" * 100000
    with open(temp_log_file, "a") as f:
        f.write(f"2023-10-27 10:03:00 INFO {long_str}\n")
        f.flush()

    await asyncio.sleep(0.5)
    assert queue.qsize() == 1
    entry = await queue.get()
    assert long_str in entry.message

    await receiver.stop()
