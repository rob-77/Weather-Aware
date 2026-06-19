"""
weather.py

Handles all communication with the OpenWeather API.

Constraints (see .cursor/rules/architecture.mdc and docs/rules.md):
- This module ONLY fetches and parses weather data.
- No print() statements, no advice/recommendation logic, no user interaction.
- Functions return plain Python data structures (dicts/lists) for other
  modules (advisor.py, cli.py) to consume.
"""

import os
from datetime import datetime
from typing import Optional

import requests

GEOCODING_URL = "https://api.openweathermap.org/geo/1.0/direct"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"


class WeatherError(Exception):
    """Raised when weather data cannot be fetched or parsed."""
    pass


def _get_api_key() -> str:
    """Read the OpenWeather API key from the environment.

    Raises:
        WeatherError: if OPENWEATHER_API_KEY is not set.
    """
    api_key = os.environ.get("OPENWEATHER_API_KEY")
    if not api_key:
        raise WeatherError(
            "OPENWEATHER_API_KEY is not set. "
            "Create a .env file (see .env.example) with your API key."
        )
    return api_key


def geocode_city(city_name: str) -> tuple[float, float]:
    """Convert a city name into (latitude, longitude).

    Args:
        city_name: Free-text city name entered by the user, e.g. "Houston".

    Returns:
        A (lat, lon) tuple.

    Raises:
        WeatherError: if the city cannot be found or the API call fails.
    """
    api_key = _get_api_key()
    params = {"q": city_name, "limit": 1, "appid": api_key}

    try:
        response = requests.get(GEOCODING_URL, params=params, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise WeatherError(f"Could not reach geocoding service: {exc}") from exc

    results = response.json()
    if not results:
        raise WeatherError(f"Could not find a city matching '{city_name}'.")

    return results[0]["lat"], results[0]["lon"]


def fetch_forecast(city_name: str) -> list[dict]:
    """Fetch a multi-day forecast for the given city.

    Uses OpenWeather's 5 day / 3-hour forecast endpoint and returns a
    normalized list of forecast entries, each broken out with enough
    detail for advisor.py to bucket by date and time-of-day.

    Args:
        city_name: Free-text city name entered by the user.

    Returns:
        A list of dicts, each shaped like:
        {
            "datetime": datetime,
            "date": "2026-06-20",
            "hour": 9,
            "temp_f": 81.0,
            "feels_like_f": 84.0,
            "condition": "Rain",
            "description": "light rain",
            "precipitation_chance": 0.6,  # 0.0-1.0, may be absent -> 0.0
        }

    Raises:
        WeatherError: if the city can't be geocoded or the forecast call fails.
    """
    api_key = _get_api_key()
    lat, lon = geocode_city(city_name)

    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": "imperial",  # Fahrenheit
    }

    try:
        response = requests.get(FORECAST_URL, params=params, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise WeatherError(f"Could not reach forecast service: {exc}") from exc

    payload = response.json()
    entries = payload.get("list", [])
    if not entries:
        raise WeatherError(f"No forecast data returned for '{city_name}'.")

    return [_parse_entry(entry) for entry in entries]


def _parse_entry(entry: dict) -> dict:
    """Normalize a single raw forecast entry from the OpenWeather API.

    Args:
        entry: One element from the OpenWeather "list" array.

    Returns:
        A normalized dict (see fetch_forecast docstring for shape).
    """
    dt = datetime.fromtimestamp(entry["dt"])
    weather_info = entry.get("weather", [{}])[0]
    main = entry.get("main", {})
    pop = entry.get("pop")  # "probability of precipitation", 0.0-1.0

    return {
        "datetime": dt,
        "date": dt.strftime("%Y-%m-%d"),
        "hour": dt.hour,
        "temp_f": main.get("temp"),
        "feels_like_f": main.get("feels_like"),
        "condition": weather_info.get("main", "Unknown"),
        "description": weather_info.get("description", ""),
        "precipitation_chance": pop if pop is not None else 0.0,
    }