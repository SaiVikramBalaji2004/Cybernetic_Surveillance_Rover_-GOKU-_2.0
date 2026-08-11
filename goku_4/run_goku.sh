#!/bin/bash
# GOKU Rover Launcher - Use this script to run GOKU

cd /home/sai/Desktop/goku_4

# Preserve the venv Python and site-packages when using sudo
echo "Starting GOKU Surveillance Agent..."
echo "Using venv Python with all dependencies..."

sudo env PYTHONPATH="/home/sai/Desktop/goku_4/venv/lib/python3.13/site-packages" \
     PATH="/home/sai/Desktop/goku_4/venv/bin:$PATH" \
     /home/sai/Desktop/goku_4/venv/bin/python3 main.py
