#!/bin/bash
# GOKU Launch Script - Run this to start the rover

cd /home/sai/Desktop/goku_4

# Use the venv's Python interpreter directly (not system python3)
# This ensures all installed packages are found

sudo /home/sai/Desktop/goku_4/venv/bin/python3 main.py
