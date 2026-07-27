# Logger Manager Integration

This document describes how another application can send logs to this Log Viewer over TCP.

## Overview

The Log Viewer accepts newline-delimited JSON log events on a TCP socket. A simple client can use the provided LoggerManager helper or send raw JSON payloads directly.

## Default transport

- Host: localhost
- Port: 9999
- Format: newline-delimited JSON

Example payload:

```json
{
  "timestamp": "2026-07-27T10:00:00+00:00",
  "level": "INFO",
  "message": "service started",
  "module": "billing-service",
  "extra": {
    "request_id": "abc123"
  }
}
```

## Python client usage

```python
from logview.logger_manager import LoggerManager

logger = LoggerManager(host="localhost", port=9999, module_name="billing-service")
logger.info("service started", extra={"request_id": "abc123"})
logger.warning("slow response", extra={"latency_ms": 2300})
logger.close()
```

## Using with your app's own logger

If your app already uses Python's standard logging, you can route those logs to the viewer with a handler.

```python
import logging
from logview.logger_manager import LoggerManagerHandler

handler = LoggerManagerHandler(host="localhost", port=9999, module_name="billing-service")
logger = logging.getLogger("billing-service")
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.propagate = False

logger.info("hello from your app")
```

## What your app needs to provide

Your app only needs to send a log message and optionally some context.

- message: the actual log text
- level: INFO, WARNING, ERROR, etc.
- module: a name for the app or component
- extra: optional structured data such as request IDs or latency

## Notes

- Each event is sent as one JSON line over TCP.
- If the viewer is not available, the message is simply not delivered.
- You do not need to implement any viewer logic in your app.
