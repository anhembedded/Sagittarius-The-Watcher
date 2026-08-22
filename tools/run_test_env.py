import os
import subprocess
import sys
import time


def main():
    """
    Runs the Log Viewer GUI in the background, and then starts the log generator
    to pump mock data into it via TCP.
    """
    print("Starting Log Viewer GUI...")
    # Make sure we use the current python environment
    python_exe = sys.executable

    # Run GUI
    # We use subprocess.Popen to run it in the background
    # Redirecting stdout/stderr so they don't interleave with our tool output
    gui_process = subprocess.Popen([python_exe, "-m", "logview"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Wait a bit for the GUI and TCP server to initialize
    print("Waiting for GUI to initialize (2 seconds)...")
    time.sleep(2)

    print("Starting log generator...")
    # The log generator pushes to localhost:9999 by default which matches the default config
    gen_process = subprocess.Popen([python_exe, "tools/log_generator.py"])

    try:
        # Wait for user to close GUI
        gui_process.wait()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        # Cleanup
        if gui_process.poll() is None:
            gui_process.terminate()
        if gen_process.poll() is None:
            gen_process.terminate()
        print("Done.")


if __name__ == "__main__":
    main()
