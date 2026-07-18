import asyncio
from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtCore import QThread, Signal

from logview.receiver import TCPServerReceiver, FileTailReceiver
from logview.log_parser import LogParser


class ReceiverWorker(QThread):
    """
    Worker thread to run the async log receivers.
    # Adapter/Observer Pattern: Adapts the async receivers to Qt's signal/slot mechanism.
    """
    logs_received = Signal(list)
    error_occurred = Signal(str)
    client_connected = Signal(str)       # address string
    client_disconnected = Signal(str)    # address string

    def __init__(self, config: Dict[str, Any], parser: LogParser):
        super().__init__()
        self.config = config
        self.parser = parser
        self.running = True
        self.loop = None
        self._async_queue = None
        self._receivers = []
        self._executor = ThreadPoolExecutor(max_workers=4)

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self._async_queue = asyncio.Queue()

        if "tail_file" in self.config and self.config["tail_file"]:
            self._receivers.append(
                FileTailReceiver(self.config["tail_file"], self.parser, self._async_queue)
            )
        else:
            host = self.config.get("server", {}).get("host", "localhost")
            port = self.config.get("server", {}).get("port", 9999)
            listen_stdin = self.config.get("listen_stdin", False)
            recv = TCPServerReceiver(host, port, self.parser, self._async_queue, listen_stdin)
            recv.on_client_connected = lambda addr: self.client_connected.emit(addr)
            recv.on_client_disconnected = lambda addr: self.client_disconnected.emit(addr)
            self._receivers.append(recv)

        self.loop.run_until_complete(self._run_async())
        self.loop.close()

    async def _run_async(self):
        """Starts all receivers then continuously drains the queue and emits signals."""
        for r in self._receivers:
            await r.start()

        try:
            while self.running:
                # Yield to event loop so TCP server callbacks (handle_client) can run
                await asyncio.sleep(0.05)

                logs = []
                while not self._async_queue.empty():
                    try:
                        entry = self._async_queue.get_nowait()
                        logs.append(entry)
                    except asyncio.QueueEmpty:
                        break

                if logs:
                    # Offload CPU-bound regex/JSON parsing to a ThreadPoolExecutor
                    list(self._executor.map(self.parser.parse_fields, logs))
                    self.logs_received.emit(logs)
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            for r in self._receivers:
                await r.stop()

    def stop(self):
        self.running = False
        self._executor.shutdown(wait=False)
        self.wait()
