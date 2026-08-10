import json
import logging
import socket
import sys
from datetime import datetime, timezone
from typing import Any


class LoggerManager:
    """Sends structured log events to the Log Viewer over a TCP socket.

    The Log Viewer accepts newline-delimited JSON payloads. Each payload can include
    the standard fields used by the viewer: timestamp, level, message, module, and
    optionally an ``extra`` object for custom context.
    """

    def __init__(self, host: str = "localhost", port: int = 9999, module_name: str | None = None, timeout: float = 2.0):
        self.host = host
        self.port = port
        self.module_name = module_name or "app"
        self.timeout = timeout
        self._socket: socket.socket | None = None
        self._last_error: str | None = None

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _connect(self) -> socket.socket:
        if self._socket is not None:
            return self._socket

        sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
        sock.settimeout(self.timeout)
        self._socket = sock
        return sock

    def _coerce_for_json(self, value: Any) -> Any:
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, (dict, list, tuple)):
            if isinstance(value, tuple):
                value = list(value)
            if isinstance(value, dict):
                return {str(k): self._coerce_for_json(v) for k, v in value.items()}
            return [self._coerce_for_json(item) for item in value]
        if isinstance(value, Exception):
            return str(value)
        return str(value)

    def _build_payload(
        self, level: str, message: str, extra: dict[str, Any] | None = None, exc_info: bool = False
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "timestamp": self._now(),
            "level": level.upper(),
            "message": message,
            "module": self.module_name,
        }
        if extra:
            payload["extra"] = {k: self._coerce_for_json(v) for k, v in extra.items()}
        if exc_info:
            payload["exception"] = self._format_exception()
        return payload

    def _format_exception(self) -> str:
        import traceback

        return "\n".join(traceback.format_exception(*sys.exc_info()))

    def _send(self, payload: dict[str, Any]) -> None:
        try:
            sock = self._connect()
            data = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
            sock.sendall(data)
            self._last_error = None
        except OSError as exc:
            self._last_error = str(exc)
            self._close_socket()

    def _close_socket(self) -> None:
        if self._socket is not None:
            try:
                self._socket.close()
            except OSError:
                pass
            self._socket = None

    def emit(self, level: str, message: str, extra: dict[str, Any] | None = None, exc_info: bool = False) -> None:
        """Emit a log event to the receiver."""
        payload = self._build_payload(level, message, extra=extra, exc_info=exc_info)
        self._send(payload)

    def debug(self, message: str, extra: dict[str, Any] | None = None) -> None:
        self.emit("DEBUG", message, extra=extra)

    def info(self, message: str, extra: dict[str, Any] | None = None) -> None:
        self.emit("INFO", message, extra=extra)

    def warning(self, message: str, extra: dict[str, Any] | None = None) -> None:
        self.emit("WARNING", message, extra=extra)

    def error(self, message: str, extra: dict[str, Any] | None = None) -> None:
        self.emit("ERROR", message, extra=extra)

    def critical(self, message: str, extra: dict[str, Any] | None = None) -> None:
        self.emit("CRITICAL", message, extra=extra)

    def exception(self, message: str, extra: dict[str, Any] | None = None) -> None:
        self.emit("ERROR", message, extra=extra, exc_info=True)

    def close(self) -> None:
        self._close_socket()

    def __enter__(self) -> "LoggerManager":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


class LoggerManagerHandler(logging.Handler):
    """A logging.Handler that forwards records to the Log Viewer."""

    def __init__(self, host: str = "localhost", port: int = 9999, module_name: str | None = None, timeout: float = 2.0):
        super().__init__()
        self.manager = LoggerManager(host=host, port=port, module_name=module_name, timeout=timeout)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = self.format(record) if self.formatter else record.getMessage()
            extra = {
                "logger": record.name,
                "pathname": record.pathname,
                "lineno": record.lineno,
            }
            self.manager.emit(record.levelname, message, extra=extra, exc_info=record.exc_info is not None)
        except Exception:
            self.handleError(record)

    def close(self) -> None:
        self.manager.close()
        super().close()
