#!/bin/bash

# Build Script for Spotify Wrapped Bot on ChromeOS (Linux)

echo "--- Preparing environment ---"
sudo apt update && sudo apt install -y python3-pip python3-tk python3-venv

# Create virtual environment
python3 -m venv build_venv
source build_venv/bin/x/activate

# Install dependencies
pip install -r requirements.txt
pip install pyinstaller

# Ensure playwright drivers are present
# Note: In Linux build, we might need the driver directly in the bundle
# But for now, we assume the user will run 'playwright install chromium' inside or next to the bot

echo "--- Starting PyInstaller Build ---"
pyinstaller --clean bash_build.spec

echo "--- Build Complete ---"
echo "Binary location: dist/spotify_wrapped_bot"
echo "Run it with: ./dist/spotify_wrapped_bot"
