"""
main.py

Entry point for running the Weather-Aware CLI.
Run with: python main.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from weather_aware.cli import run

if __name__ == "__main__":
    run()