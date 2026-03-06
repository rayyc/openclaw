#!/bin/bash
# Backend startup script for Linux/macOS
# Runs the FastAPI server from the project root with correct Python path

echo -e "\033[36mStarting OpenClaw Backend...\033[0m"

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment if not already activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "\033[33mActivating virtual environment...\033[0m"
    source venv/bin/activate || source .venv/bin/activate
fi

# Start Uvicorn from project root (so backend.* imports work)
echo -e "\033[32mStarting Uvicorn server on http://127.0.0.1:8000\033[0m"
uvicorn backend.main:app --reload --port 8000 --host 127.0.0.1

cd - > /dev/null
