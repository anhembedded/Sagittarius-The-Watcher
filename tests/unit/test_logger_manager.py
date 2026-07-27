import json
import logging
import socketserver
import threading

from logview.logger_manager import LoggerManager, LoggerManagerHandler


class CaptureHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request.recv(4096)
        self.server.received_payloads.append(data.decode("utf-8").strip())


class CaptureServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.received_payloads = []


def test_emit_sends_json_payload_to_tcp_listener():
    server = CaptureServer(("127.0.0.1", 0), CaptureHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        manager = LoggerManager(host="127.0.0.1", port=server.server_address[1], module_name="tests")
        manager.info("hello from test", extra={"request_id": "abc123"})
        manager.close()

        for _ in range(20):
            if server.received_payloads:
                break
            threading.Event().wait(0.05)

        assert len(server.received_payloads) == 1
        payload = json.loads(server.received_payloads[0])
        assert payload["level"] == "INFO"
        assert payload["message"] == "hello from test"
        assert payload["module"] == "tests"
        assert payload["extra"]["request_id"] == "abc123"
    finally:
        server.shutdown()
        server.server_close()


def test_logger_manager_handler_for_python_logging():
    server = CaptureServer(("127.0.0.1", 0), CaptureHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        handler = LoggerManagerHandler(host="127.0.0.1", port=server.server_address[1], module_name="logging-tests")
        logger = logging.getLogger("test.logger.manager")
        logger.handlers = [handler]
        logger.setLevel(logging.INFO)
        logger.propagate = False

        logger.warning("hello via handler")
        handler.close()

        for _ in range(20):
            if server.received_payloads:
                break
            threading.Event().wait(0.05)

        assert len(server.received_payloads) == 1
        payload = json.loads(server.received_payloads[0])
        assert payload["level"] == "WARNING"
        assert payload["message"] == "hello via handler"
    finally:
        server.shutdown()
        server.server_close()
