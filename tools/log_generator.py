import argparse
import asyncio
import json
import random
import time
from datetime import datetime

MESSAGES = [
    "User login successful",
    "Database connection timeout",
    "File not found: config.yaml",
    "Failed to authenticate token",
    "Process started successfully",
    "Out of memory error in worker thread",
    "Unexpected payload received",
    "Graceful shutdown initiated",
    "Cache miss for key: user_profile",
    "Connection reset by peer"
]

def parse_args():
    parser = argparse.ArgumentParser(description="Log Generator for Log Viewer")
    parser.add_argument("--host", type=str, default="localhost", help="Host to connect to")
    parser.add_argument("--port", type=int, default=9999, help="Port to connect to")
    parser.add_argument("--rate", type=float, default=10.0, help="Logs per second")
    parser.add_argument("--duration", type=int, default=0, help="Duration to run in seconds (0 = forever)")
    parser.add_argument("--pattern", type=str, choices=["structured", "json", "apache"], default="structured", help="Format of the logs")
    parser.add_argument("--levels", type=str, default="DEBUG:50,INFO:30,WARNING:10,ERROR:8,CRITICAL:2", help="Comma-separated LEVEL:Weight")
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
    level = random.choices(levels, weights=weights)[0]
    msg = random.choice(MESSAGES)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    if pattern == "structured":
        return f"[{ts}] [{level}] {msg}\n"
    elif pattern == "json":
        return json.dumps({"timestamp": ts, "level": level, "message": msg}) + "\n"
    elif pattern == "apache":
        return f'127.0.0.1 - - [{ts}] "{level} /api/v1/resource HTTP/1.1" 200 {random.randint(100, 5000)} "{msg}"\n'

async def main():
    args = parse_args()
    levels, weights = parse_levels(args.levels)

    print(f"Connecting to {args.host}:{args.port}...")
    try:
        reader, writer = await asyncio.open_connection(args.host, args.port)
    except Exception as e:
        print(f"Failed to connect: {e}")
        return

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

            if logs_sent % int(args.rate) == 0 or logs_sent % 100 == 0:
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
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass

if __name__ == "__main__":
    asyncio.run(main())
