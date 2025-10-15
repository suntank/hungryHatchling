#!/bin/bash
# Snake Game Launcher

# Activate virtual environment and run the game
cd "$(dirname "$0")"

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    ./venv/bin/pip install -r requirements.txt
fi

# Run the game
./venv/bin/python3 main.py
