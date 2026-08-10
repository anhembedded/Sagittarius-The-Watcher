import asyncio
import os
import tempfile

import pytest

from logview.log_parser import LogParser
from logview.receiver import FileTailReceiver, TCPServerReceiver


@pytest.mark.asyncio
async def test_file_tail_receiver():
    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        filepath = f.name

    parser = LogParser(r"^(.*)$")
    queue = asyncio.Queue()

    receiver = FileTailReceiver(filepath, parser, queue)
    await receiver.start()

    try:
        # Give tailer time to start and seek to end
        await asyncio.sleep(0.5)

        with open(filepath, "a") as f:
            f.write("Log line 1\n")
            f.flush()

        entry = await asyncio.wait_for(queue.get(), timeout=5.0)
        assert entry.message == "Log line 1"

    finally:
        await receiver.stop()
        os.unlink(filepath)


@pytest.mark.asyncio
async def test_tcp_server_receiver():
    parser = LogParser(r"^(.*)$")
    queue = asyncio.Queue()

    # Use port 0 to bind to any available port
    receiver = TCPServerReceiver("127.0.0.1", 0, parser, queue)
    await receiver.start()

    # Get the actual bound port
    addr = receiver.server.sockets[0].getsockname()
    port = addr[1]

    try:
        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        writer.write(b"TCP log line\n")
        await writer.drain()

        writer.close()
        await writer.wait_closed()

        entry = await asyncio.wait_for(queue.get(), timeout=2.0)
        assert entry.message == "TCP log line"

    finally:
        await receiver.stop()
