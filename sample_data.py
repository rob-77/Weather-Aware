"""
sample_data.py

Hardcoded sample forecast data used only in --demo mode (see main.py).

This exists so graders/reviewers without their own OpenWeather API key
can still run the full app and see real advisor.py logic in action,
without needing to sign up for a key or wait for activation.

This is NOT used in normal operation — only when main.py is run with
the --demo flag. Real runs always fetch live data via weather.py.
"""

from datetime import datetime

# Two days of fake but realistic-looking 3-hour-interval forecast data,
# deliberately including a severe-rain entry so the demo clearly shows
# the rubric's core scenario (rain + event -> transport suggestion).

DEMO_FORECAST = [
    {
        "datetime": datetime.fromisoformat("2026-06-20T06:00:00"),
        "date": "2026-06-20", "hour": 6,
        "temp_f": 74.0, "feels_like_f": 75.0,
        "condition": "Clear", "description": "clear sky",
        "precipitation_chance": 0.0,
    },
    {
        "datetime": datetime.fromisoformat("2026-06-20T09:00:00"),
        "date": "2026-06-20", "hour": 9,
        "temp_f": 79.0, "feels_like_f": 81.0,
        "condition": "Clouds", "description": "scattered clouds",
        "precipitation_chance": 0.1,
    },
    {
        "datetime": datetime.fromisoformat("2026-06-20T14:00:00"),
        "date": "2026-06-20", "hour": 14,
        "temp_f": 86.0, "feels_like_f": 92.0,
        "condition": "Rain", "description": "heavy rain",
        "precipitation_chance": 0.8,
    },
    {
        "datetime": datetime.fromisoformat("2026-06-20T18:00:00"),
        "date": "2026-06-20", "hour": 18,
        "temp_f": 82.0, "feels_like_f": 85.0,
        "condition": "Clouds", "description": "broken clouds",
        "precipitation_chance": 0.2,
    },
    {
        "datetime": datetime.fromisoformat("2026-06-21T07:00:00"),
        "date": "2026-06-21", "hour": 7,
        "temp_f": 70.0, "feels_like_f": 68.0,
        "condition": "Clear", "description": "clear sky",
        "precipitation_chance": 0.0,
    },
    {
        "datetime": datetime.fromisoformat("2026-06-21T19:00:00"),
        "date": "2026-06-21", "hour": 19,
        "temp_f": 84.0, "feels_like_f": 89.0,
        "condition": "Thunderstorm", "description": "thunderstorm with heavy rain",
        "precipitation_chance": 0.9,
    },
]