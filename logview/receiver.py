import asyncio
import sys
from typing import Optional

import os
import io

from logview.log_parser import LogParser, MultiLineBuffer


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

    async def _put_entry(self, entry):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.parser.parse_fields, entry)
        await self.queue.put(entry)

    async def _tail_file(self):
        """Tails the file and pushes to queue using MultiLineBuffer for multi-line support."""
        loop = asyncio.get_running_loop()
        buf = MultiLineBuffer(self.parser)

        # Wait for file to exist
        while self._running and not os.path.exists(self.filepath):
            await asyncio.sleep(0.5)

        if not self._running:
            return

        with open(self.filepath, 'r', encoding='utf-8', errors='replace') as f:
            # Go to the end of the file
            f.seek(0, io.SEEK_END)

            idle_time = 0.0

            while self._running:
                line = await loop.run_in_executor(None, f.readline)
                if not line:
                    await asyncio.sleep(0.1)
                    idle_time += 0.1
                    if idle_time >= 0.2:  # Flush after 200ms of inactivity
                        entry = buf.flush()
                        if entry:
                            await self._put_entry(entry)
                        idle_time = 0.0
                    continue

                idle_time = 0.0
                entry = buf.feed(line)
                if entry:
                    await self._put_entry(entry)

        # Flush remaining
        final = buf.flush()
        if final:
            await self._put_entry(final)


class TCPServerReceiver:
    """Receives logs from a TCP socket or stdin and pushes parsed entries to a queue."""

    def __init__(self, host: str, port: int, parser: LogParser, queue: asyncio.Queue,
                 listen_stdin: bool = False):
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

        # Callbacks for connection events (set by ReceiverWorker for status bar)
        self.on_client_connected = None
        self.on_client_disconnected = None

    async def start(self):
        """Starts the receiver."""
        self._running = True
        if self.listen_stdin:
            # Run stdin reader in a separate task or executor to not block
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

    async def _put_entry(self, entry):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.parser.parse_fields, entry)
        await self.queue.put(entry)

    async def _read_stdin(self):
        """Reads lines from stdin using MultiLineBuffer."""
        loop = asyncio.get_running_loop()
        buf = MultiLineBuffer(self.parser)
        # Note: sys.stdin.readline blocking makes inactivity timeout hard for stdin without select,
        # but if we can't do non-blocking, we just flush when line is received, or wait for EOF.
        # Alternatively, since we can't easily timeout a blocking readline, we leave it,
        # or we could use a separate task to timeout. For now, since stdin usually EOFs at the end
        # of the stream, it's less of an issue than a live file or TCP server.
        while self._running:
            line = await loop.run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            entry = buf.feed(line)
            if entry:
                await self._put_entry(entry)
        final = buf.flush()
        if final:
            await self._put_entry(final)

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handles an incoming client connection.
        ...
        """
        print("DEBUG: handle_client called!")
        addr = writer.get_extra_info('peername', ('?', 0))
        addr_str = f"{addr[0]}:{addr[1]}"
        buf = MultiLineBuffer(self.parser)

        if self.on_client_connected:
            self.on_client_connected(addr_str)

        try:
            while self._running:
                try:
                    # Use a timeout to detect inactivity and flush the buffer
                    line_bytes = await asyncio.wait_for(reader.readline(), timeout=0.2)
                    if not line_bytes:
                        print("DEBUG: Client disconnected (EOF)")
                        break
                    line = line_bytes.decode('utf-8', errors='replace')
                    print(f"DEBUG: Read line: {line!r}")
                    entry = buf.feed(line)
                    if entry:
                        print(f"DEBUG: Fed to buf, got entry")
                        await self._put_entry(entry)
                except asyncio.TimeoutError:
                    # Inactivity timeout reached, flush pending log
                    entry = buf.flush()
                    if entry:
                        print(f"DEBUG: Timeout flush, got entry")
                        await self._put_entry(entry)
        except asyncio.CancelledError:
            pass
        except Exception:
            pass
        finally:
            # Flush any buffered multi-line entry before disconnecting
            final = buf.flush()
            if final:
                await self._put_entry(final)

            if self.on_client_disconnected:
                self.on_client_disconnected(addr_str)

            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
