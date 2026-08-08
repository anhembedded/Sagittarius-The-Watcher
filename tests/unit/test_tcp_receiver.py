import asyncio
import pytest
from logview.receiver import TCPServerReceiver
from logview.log_parser import LogParser

@pytest.mark.asyncio
async def test_tcp_server_receiver():
    """Test that TCPServerReceiver can bind, accept connections, and parse logs."""
    # Setup
    parser = LogParser(r"^(?:\[(?P<timestamp>.*?)\])?\s*(?:\[(?P<level>\w+)\])?\s*(?:\[(?P<module>\w+)\])?\s*(?:\[(?P<submodule>\w+)\])?\s*(?P<message>.*)")
    queue = asyncio.Queue()
    
    # Use 127.0.0.1 for testing to ensure it binds to IPv4
    receiver = TCPServerReceiver("127.0.0.1", 9999, parser, queue)
    
    # Start receiver
    await receiver.start()
    assert receiver.server is not None
    assert receiver._running is True
    
    # Simulate a client connection
    reader, writer = await asyncio.open_connection("127.0.0.1", 9999)
    test_line = b"[2023-01-01 12:00:00] [INFO] [Auth] [Login] User logged in\n"
    writer.write(test_line)
    await writer.drain()
    
    # Close connection
    writer.close()
    await writer.wait_closed()
    
    # Wait for the entry to be parsed and put into the queue
    try:
        entry = await asyncio.wait_for(queue.get(), timeout=2.0)
        assert entry is not None
        assert entry.level == "INFO"
        assert entry.module == "Auth"
        assert entry.submodule == "Login"
        assert entry.message == "User logged in"
    except asyncio.TimeoutError:
        pytest.fail("Timeout waiting for LogEntry to be placed in queue.")
        
    # Stop receiver
    await receiver.stop()
    assert receiver._running is False
