"""
main.py

Entry point for running the Weather-Aware CLI.

Run with:
    python main.py            # normal mode, requires OPENWEATHER_API_KEY
    python main.py --demo     # demo mode, no API key needed (sample data)
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from weather_aware.cli import run

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Weather-Aware personal assistant")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run with sample forecast data instead of a live OpenWeather API call. "
             "No API key required. Useful for grading/review without setup.",
    )
    args = parser.parse_args()
    run(demo=args.demo)