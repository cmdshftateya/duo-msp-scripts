#!/bin/bash
# Communications Impact Report
# Double-click this file in Finder to run, or execute it from Terminal.

cd "$(dirname "$0")"

echo "============================================"
echo "  Communications Impact Report"
echo "============================================"
echo ""

# --- Find Python 3 ---
SYS_PYTHON=""
for candidate in python3 python; do
    if command -v "$candidate" &>/dev/null; then
        SYS_PYTHON="$candidate"
        break
    fi
done

if [ -z "$SYS_PYTHON" ]; then
    echo "ERROR: Python 3 not found. Install it from https://python.org"
    echo ""
    echo "Press Enter to close."
    read
    exit 1
fi

# --- Create/reuse a dedicated virtualenv ---
VENV_DIR="$(dirname "$0")/.venv"

if [ ! -f "$VENV_DIR/bin/python" ]; then
    echo "First run: creating virtual environment at .venv ..."
    "$SYS_PYTHON" -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "ERROR: Could not create virtual environment."
        echo "Press Enter to close."
        read
        exit 1
    fi
fi

PYTHON="$VENV_DIR/bin/python"

# --- Install/verify dependencies ---
echo "Checking dependencies..."
"$PYTHON" -m pip install --quiet --upgrade pip
"$PYTHON" -m pip install --quiet flask flask-cors duo_client
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies."
    echo "Press Enter to close."
    read
    exit 1
fi
echo "  OK"
echo ""

# --- Start Flask server in the background ---
echo "Starting server on http://localhost:5000 ..."
"$PYTHON" "$(dirname "$0")/server.py" &
SERVER_PID=$!

# Give the server a moment to bind
sleep 1

# Check it actually started
if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "ERROR: Server failed to start. Check server.py for errors."
    echo "Press Enter to close."
    read
    exit 1
fi

echo "  Server running (PID $SERVER_PID)"
echo ""

# --- Open the browser UI via the server ---
echo "Opening http://localhost:5000 in your default browser..."
open "http://localhost:5000"

echo ""
echo "The server is running. Press Enter here to STOP the server and close."
read

# --- Shut down the server ---
kill "$SERVER_PID" 2>/dev/null
echo "Server stopped."
