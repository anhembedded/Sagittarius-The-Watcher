# Bug Report: Missing Final Log Entry Display (LogViewer)

## 1. Code Review & Static Analysis (White-Box Approach)

During a static analysis of the log ingestion process (focusing on `logview/receiver.py` and `logview/log_parser.py`), the following 5 potential areas for hidden bugs were identified:

1. **State Mutation & Buffering in `MultiLineBuffer` (The primary suspect):**
   The `MultiLineBuffer` requires a *new* log entry to be fed via `feed()` to flush the *previous* log entry from its internal `_pending` state. If a stream is continuous and idling (e.g., waiting for new logs to be written to a file), the last logged entry remains trapped in `_pending` indefinitely until the next log line is produced.
2. **Infinite Loops without Timeout Flushing:**
   In `FileTailReceiver._tail_file` and `TCPServerReceiver.handle_client`, the reader loops indefinitely. When there is no new line (`if not line:`), they simply sleep or block. They never forcefully invoke `buf.flush()` on an inactivity timeout, exacerbating the buffering bug above.
3. **Null Handling in Parsing:**
   If a log line doesn't match the regex pattern and doesn't look like JSON, it is treated as a continuation of the previous log line. If it is the first line ever received, `MultiLineBuffer` initializes `_pending` with an unparsed standalone log entry, which is correct, but subsequent malformed lines might indefinitely bloat this single `_pending` entry without a limit, leading to an Out-Of-Memory (OOM) edge case if malformed data streams continuously.
4. **Boundary Limits on Buffered Continuation Lines:**
   `MultiLineBuffer` has no maximum limit for how large `self._pending.raw` can grow. If a giant stack trace or binary stream is read, the string allocation could crash the application.
5. **Thread/Async Queue Push Limits:**
   `self.queue.put(entry)` is used to push logs to the UI thread. In `ReceiverWorker`, if the UI thread is paused or slow, `asyncio.Queue` (which has no maxsize by default) will grow indefinitely, causing memory pressure.

## 2. Root Cause of "Tool is running but app does not display log"

The root cause of the missing logs issue lies in the interaction between the asynchronous stream readers (`FileTailReceiver`, `TCPServerReceiver`) and the `MultiLineBuffer`.

When an external process writes a single log line to the file, `FileTailReceiver` reads it and passes it to `MultiLineBuffer.feed()`. The buffer identifies it as a new log entry, sets it to `_pending`, and returns `None`. Because `feed()` returns `None`, the receiver loop continues and goes back to waiting for the *next* line. As a result, the UI queue never receives this log entry. It will only be displayed when a *second* log entry is written, which causes `feed()` to yield the first one. Consequently, the application always lags 1 full log entry behind the live stream, and if only 1 entry is ever written, it is never displayed until the stream closes (which live streams don't do).

## 3. The Failing Test Case

See the implemented test suite (`tests/unit/test_receiver_delay.py`) for the failing edge cases involving stream delays.
