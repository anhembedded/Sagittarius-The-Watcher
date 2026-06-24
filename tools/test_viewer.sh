#!/bin/bash
# Test script to run Log Viewer and Generator

echo "Starting Log Viewer in a new terminal..."

# Try to detect terminal emulator
if command -v gnome-terminal &> /dev/null; then
    gnome-terminal -- bash -c "python -m logview --port 9999; exec bash"
elif command -v xterm &> /dev/null; then
    xterm -e "python -m logview --port 9999; exec bash" &
elif command -v konsole &> /dev/null; then
    konsole -e bash -c "python -m logview --port 9999; exec bash" &
elif [[ "$OSTYPE" == "darwin"* ]]; then
    osascript -e 'tell app "Terminal" to do script "cd \"'$(pwd)'\" && python -m logview --port 9999"'
else
    echo "Could not auto-detect terminal. Please open a new terminal and run: python -m logview --port 9999"
    echo "Waiting 5 seconds before starting generator..."
    sleep 5
fi

# Give the server a moment to start
sleep 2

echo "Starting Log Generator..."
python tools/log_generator.py --port 9999 --duration 30
