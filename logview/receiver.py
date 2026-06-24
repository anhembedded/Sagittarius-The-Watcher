import asyncio
import sys
from typing import Optional

import os
import io

from logview.log_parser import LogParser


class FileTailReceiver:
    """Receives logs by tailing a file."""

    def __init__(self, filepath: str, parser: LogParser, queue: asyncio.Queue):
        self.filepath = filepath
        self.parser = parser
        self.queue = queue
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """Starts the receiver."""
        self._running = True
        self._task = asyncio.create_task(self._tail_file())

    async def stop(self):
        """Stops the receiver."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _tail_file(self):
        """Tails the file and pushes to queue."""
        loop = asyncio.get_running_loop()

        # Wait for file to exist
        while self._running and not os.path.exists(self.filepath):
            await asyncio.sleep(0.5)

        if not self._running:
            return

        with open(self.filepath, 'r', encoding='utf-8', errors='replace') as f:
            # Go to the end of the file
            f.seek(0, io.SEEK_END)

            while self._running:
                line = await loop.run_in_executor(None, f.readline)
                if not line:
                    await asyncio.sleep(0.1)
                    continue

                entry = self.parser.parse(line)
                await self.queue.put(entry)


class TCPServerReceiver:
    """Receives logs from a TCP socket or stdin and pushes parsed entries to a queue."""

    def __init__(self, host: str, port: int, parser: LogParser, queue: asyncio.Queue, listen_stdin: bool = False):
        """Initializes the receiver.

        Args:
            host (str): TCP host to bind.
            port (int): TCP port to bind.
            parser (LogParser): Parser for incoming log lines.
            queue (asyncio.Queue): The queue to push parsed LogEntry objects into.
            listen_stdin (bool): Whether to read from stdin instead of opening a TCP server.
        """
        self.host = host
        self.port = port
        self.parser = parser
        self.queue = queue
        self.listen_stdin = listen_stdin
        self.server: Optional[asyncio.AbstractServer] = None
        self._running = False

    async def start(self):
        """Starts the receiver."""
        self._running = True
        if self.listen_stdin:
            # Run stdin reader in a separate task or executor to not block
            loop = asyncio.get_running_loop()
            # Stdin might not be easily integrated with asyncio.StreamReader standard ways,
            # so using a thread to read line by line.
            asyncio.create_task(self._read_stdin())
        else:
            self.server = await asyncio.start_server(
                self.handle_client, self.host, self.port
            )
            # The server will run in the background

    async def stop(self):
        """Stops the receiver."""
        self._running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()

    async def _read_stdin(self):
        """Reads lines from stdin."""
        loop = asyncio.get_running_loop()
        while self._running:
            line = await loop.run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            entry = self.parser.parse(line)
            await self.queue.put(entry)

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handles an incoming client connection.

        Args:
            reader (asyncio.StreamReader): The stream reader.
            writer (asyncio.StreamWriter): The stream writer.
        """
        try:
            while self._running:
                line_bytes = await reader.readline()
                if not line_bytes:
                    break
                # Try to decode, ignoring errors to keep going
                line = line_bytes.decode('utf-8', errors='replace')
                entry = self.parser.parse(line)
                await self.queue.put(entry)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            # Optionally log to stderr or a special queue
            pass
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
