"""
cli.py

The REPL (Read-Eval-Print Loop) entry point for the Weather-Aware
personal assistant.

Constraints (see .cursor/rules/architecture.mdc and docs/rules.md):
- This module owns ALL print()/input() calls.
- It contains NO business logic of its own — it only orchestrates calls
  into weather.py, calendar_reader.py, and advisor.py, and formats their
  results for display.
"""

import os
from collections import defaultdict

from dotenv import load_dotenv

from weather_aware.weather import fetch_forecast, WeatherError
from weather_aware.calendar_reader import load_calendar, CalendarLoadError
from weather_aware.advisor import generate_advice, Advice


WELCOME_MESSAGE = """
Weather-Aware: Your Personal Assistant
---------------------------------------
Commands:
  today      - advice for today
  week       - advice for the next few days
  help       - show this message
  quit       - exit
You can also just type naturally, e.g. "what's my day look like?"
"""


def run(demo: bool = False) -> None:
    """Start the REPL. Loads environment variables, prompts for a city,
    then loops accepting commands until the user quits.

    Args:
        demo: If True, skips the live OpenWeather API call and uses
            hardcoded sample forecast data instead (see sample_data.py).
            Intended for graders/reviewers who don't have their own
            OpenWeather API key. The real calendar.json is still read
            and the real advisor.py logic still runs — only the weather
            data source changes.
    """
    load_dotenv()

    print(WELCOME_MESSAGE)
    if demo:
        print("*** DEMO MODE: using sample forecast data, not a live API call. ***\n")

    city = _prompt_for_city() if not demo else "Demo City"
    if city is None:
        return  # user quit before even starting

    print(f"\nGot it — using {city} for weather. Type 'help' for commands.\n")

    while True:
        try:
            user_input = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if _is_quit_command(user_input):
            print("Goodbye!")
            break
        elif _is_help_command(user_input):
            print(WELCOME_MESSAGE)
        elif _is_week_command(user_input):
            _handle_advice_request(city, days=5, demo=demo)
        elif _is_today_command(user_input):
            _handle_advice_request(city, days=1, demo=demo)
        else:
            print(
                "Sorry, I didn't understand that. "
                "Type 'help' to see available commands."
            )


def _prompt_for_city() -> str | None:
    """Prompt the user for their city at startup.

    Returns:
        The city name as entered, or None if the user quit immediately.
    """
    while True:
        city = input("What city are you in? ").strip()
        if not city:
            print("Please enter a city name (or type 'quit' to exit).")
            continue
        if _is_quit_command(city.lower()):
            print("Goodbye!")
            return None
        return city


def _is_quit_command(text: str) -> bool:
    return any(word in text for word in ("quit", "exit", "bye"))


def _is_help_command(text: str) -> bool:
    return "help" in text


def _is_week_command(text: str) -> bool:
    return any(word in text for word in ("week", "few days", "upcoming"))


def _is_today_command(text: str) -> bool:
    return any(word in text for word in ("today", "day look like", "how's today", "now"))


def _handle_advice_request(city: str, days: int, demo: bool = False) -> None:
    """Fetch weather + calendar, generate advice, and print it.

    Args:
        city: City name to fetch weather for (ignored in demo mode).
        days: How many days ahead of forecast data to consider when
            filtering advice (1 = today only, 5 = full forecast window).
        demo: If True, uses hardcoded sample forecast data instead of
            calling the live OpenWeather API.
    """
    if demo:
        from sample_data import DEMO_FORECAST
        forecast = DEMO_FORECAST
    else:
        try:
            forecast = fetch_forecast(city)
        except WeatherError as e:
            print(f"Couldn't get the weather: {e}")
            return

    try:
        calendar_result = load_calendar("calendar.json")
    except CalendarLoadError as e:
        print(f"Couldn't read your calendar: {e}")
        return

    if calendar_result.warnings:
        print("(Note: some calendar events were skipped)")
        for warning in calendar_result.warnings:
            print(f"  - {warning}")
        print()

    if days == 1:
        today = forecast[0]["date"] if forecast else None
        forecast = [entry for entry in forecast if entry["date"] == today]

    advice_list = generate_advice(forecast, calendar_result.events)

    if not advice_list:
        print("Nothing notable in the forecast — looks like a calm stretch ahead.\n")
        return

    _print_advice(advice_list)


def _print_advice(advice_list: list[Advice]) -> None:
    """Print advice grouped by date, in a readable format."""
    grouped: dict[str, list[Advice]] = defaultdict(list)
    for advice in advice_list:
        grouped[advice.date].append(advice)

    for date in sorted(grouped.keys()):
        print(f"\n{date}")
        print("-" * len(date))
        for advice in grouped[date]:
            print(f"  [{advice.time_of_day}] {advice.message}")
    print()


if __name__ == "__main__":
    run()