import argparse
import asyncio
import json
import random
import time
from datetime import datetime

MESSAGES = [
    ("INFO", "User login successful"),
    ("WARNING", "Database connection timeout"),
    ("ERROR", "File not found: config.yaml"),
    ("CRITICAL", "Out of memory error in worker thread"),
    ("DEBUG", "Cache miss for key: user_profile"),
    ("INFO", "Process started successfully"),
    ("WARNING", "Unexpected payload received"),
    ("INFO", "Graceful shutdown initiated"),
    ("DEBUG", "Connection reset by peer"),
    ("INFO", "Order processed successfully, ID: 98124"),
    ("WARNING", "API response latency is high (1.5s)"),
    ("ERROR", "Invalid authorization signature"),
    ("CRITICAL", "Disk space critical: 98% full on /data"),
    ("DEBUG", "Entering loop query for batch size 100"),
]

STACK_TRACES = [
    ("ERROR", "Database connection failed", "ConnectionError: Timeout while waiting for connection pool\n    at db.py:45\n    at main.py:12\n    at server.py:89"),
    ("CRITICAL", "NullPointerException in main logic", "NullPointerException: Cannot invoke 'String.hashCode()' because 'value' is null\n    at com.example.App.process(App.java:102)\n    at com.example.App.main(App.java:45)"),
    ("ERROR", "HTTP request failed", "RequestException: 504 Gateway Timeout for URL: https://api.service.internal/v1/data\n    at httpx._client.send(client.py:202)\n    at services.gateway.fetch(gateway.py:12)"),
]

def parse_args():
    parser = argparse.ArgumentParser(description="Log Generator for Log Viewer")
    parser.add_argument("--host", type=str, default="localhost", help="Host to connect to")
    parser.add_argument("--port", type=int, default=9999, help="Port to connect to")
    parser.add_argument("--rate", type=float, default=2.0, help="Logs per second")
    parser.add_argument("--duration", type=int, default=0, help="Duration to run in seconds (0 = forever)")
    parser.add_argument("--pattern", type=str, choices=["mixed", "structured", "json", "apache"], default="mixed", help="Format of the logs")
    parser.add_argument("--levels", type=str, default="DEBUG:20,INFO:50,WARNING:15,ERROR:10,CRITICAL:5", help="Comma-separated LEVEL:Weight")
    return parser.parse_args()

def parse_levels(level_str):
    levels = []
    weights = []
    for pair in level_str.split(","):
        lvl, w = pair.split(":")
        levels.append(lvl.strip())
        weights.append(float(w))
    return levels, weights

def generate_log_line(pattern, levels, weights):
    # Randomly select if we want to generate a stack trace if pattern is 'mixed'
    if pattern == "mixed" and random.random() < 0.25: # 25% chance of stack trace
        level, msg, stack = random.choice(STACK_TRACES)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        return f"[{ts}] [{level}] {msg}\n{stack}\n"

    # Otherwise choose a normal message
    level = random.choices(levels, weights=weights)[0]
    msg_choices = [m for l, m in MESSAGES if l == level]
    if msg_choices:
        msg = random.choice(msg_choices)
    else:
        msg = random.choice(MESSAGES)[1]
        
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    selected_pattern = pattern
    if pattern == "mixed":
        # Randomly choose format to test the parser's automatic fallback behavior
        selected_pattern = random.choices(["structured", "json"], weights=[0.8, 0.2])[0]

    if selected_pattern == "structured":
        return f"[{ts}] [{level}] {msg}\n"
    elif selected_pattern == "json":
        return json.dumps({"timestamp": ts, "level": level, "message": msg}) + "\n"
    elif selected_pattern == "apache":
        return f'127.0.0.1 - - [{ts}] "{level} /api/v1/resource HTTP/1.1" 200 {random.randint(100, 5000)} "{msg}"\n'
    return f"[{ts}] [{level}] {msg}\n"

async def main():
    args = parse_args()
    levels, weights = parse_levels(args.levels)

    print(f"Connecting to {args.host}:{args.port}...")
    writer = None
    while True:
        try:
            reader, writer = await asyncio.open_connection(args.host, args.port)
            break
        except Exception as e:
            print(f"Failed to connect: {e}. Retrying in 2 seconds...")
            await asyncio.sleep(2)

    print(f"Connected. Generating logs at {args.rate} msgs/sec for {'forever' if args.duration == 0 else args.duration} seconds.")

    start_time = time.time()
    sleep_interval = 1.0 / args.rate
    logs_sent = 0

    try:
        while True:
            current_time = time.time()
            if args.duration > 0 and current_time - start_time > args.duration:
                break

            line = generate_log_line(args.pattern, levels, weights)
            writer.write(line.encode('utf-8'))
            await writer.drain()
            logs_sent += 1

            if logs_sent % 10 == 0:
                elapsed = current_time - start_time
                actual_rate = logs_sent / elapsed if elapsed > 0 else 0
                print(f"Sent: {logs_sent} | Actual Rate: {actual_rate:.2f} msgs/sec")

            await asyncio.sleep(sleep_interval)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Error during sending: {e}")
    finally:
        print(f"Finished. Total sent: {logs_sent}")
        if writer:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

if __name__ == "__main__":
    asyncio.run(main())
