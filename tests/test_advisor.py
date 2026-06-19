"""
tests/test_advisor.py

Automated tests for advisor.py's rule-based advice logic.

These tests exist to satisfy the "Guardrails" rubric criterion: they must
prove the *logic* is correct (e.g. "does it suggest a bus when it's
raining?"), not just that the app runs without crashing.

Since advisor.py is pure (no I/O), these tests construct forecast entries
and CalendarEvent objects directly — no mocking required.
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest

from weather_aware.advisor import (
    generate_advice,
    time_of_day_bucket,
    _is_rainy,
    _is_severe_rain,
    _is_hot,
    _is_cold,
)
from weather_aware.calendar_reader import CalendarEvent


def make_forecast_entry(
    date="2026-06-20",
    hour=14,
    temp_f=75.0,
    feels_like_f=75.0,
    condition="Clear",
    description="clear sky",
    precipitation_chance=0.0,
):
    """Helper to build a forecast entry dict matching weather.py's shape."""
    return {
        "datetime": datetime.fromisoformat(f"{date}T{hour:02d}:00:00"),
        "date": date,
        "hour": hour,
        "temp_f": temp_f,
        "feels_like_f": feels_like_f,
        "condition": condition,
        "description": description,
        "precipitation_chance": precipitation_chance,
    }


def make_event(title="Test Event", date="2026-06-20", hour=14, location="Somewhere"):
    """Helper to build a CalendarEvent for a given date/hour."""
    start = datetime.fromisoformat(f"{date}T{hour:02d}:00:00")
    end = datetime.fromisoformat(f"{date}T{hour:02d}:30:00")
    return CalendarEvent(title=title, start=start, end=end, location=location)


# ---------------------------------------------------------------------------
# Time-of-day bucketing
# ---------------------------------------------------------------------------

class TestTimeOfDayBucket:
    def test_morning_hours(self):
        for hour in (5, 8, 11):
            assert time_of_day_bucket(hour) == "morning"

    def test_afternoon_hours(self):
        for hour in (12, 14, 16):
            assert time_of_day_bucket(hour) == "afternoon"

    def test_evening_hours(self):
        for hour in (17, 19, 21):
            assert time_of_day_bucket(hour) == "evening"

    def test_night_hours(self):
        for hour in (22, 0, 3, 4):
            assert time_of_day_bucket(hour) == "night"


# ---------------------------------------------------------------------------
# Rain detection rules
# ---------------------------------------------------------------------------

class TestRainDetection:
    def test_rain_above_threshold_is_rainy(self):
        entry = make_forecast_entry(condition="Rain", precipitation_chance=0.5)
        assert _is_rainy(entry) is True

    def test_rain_below_threshold_is_not_rainy(self):
        entry = make_forecast_entry(condition="Rain", precipitation_chance=0.2)
        assert _is_rainy(entry) is False

    def test_thunderstorm_always_rainy_even_at_low_percent(self):
        entry = make_forecast_entry(condition="Thunderstorm", precipitation_chance=0.1)
        assert _is_rainy(entry) is True

    def test_clear_weather_is_not_rainy(self):
        entry = make_forecast_entry(condition="Clear", precipitation_chance=0.0)
        assert _is_rainy(entry) is False

    def test_severe_rain_requires_higher_threshold(self):
        moderate = make_forecast_entry(condition="Rain", precipitation_chance=0.5)
        severe = make_forecast_entry(condition="Rain", precipitation_chance=0.7)
        assert _is_severe_rain(moderate) is False
        assert _is_severe_rain(severe) is True

    def test_thunderstorm_is_always_severe(self):
        entry = make_forecast_entry(condition="Thunderstorm", precipitation_chance=0.1)
        assert _is_severe_rain(entry) is True


# ---------------------------------------------------------------------------
# Temperature rules
# ---------------------------------------------------------------------------

class TestTemperatureDetection:
    def test_hot_above_threshold(self):
        entry = make_forecast_entry(feels_like_f=95.0)
        assert _is_hot(entry) is True

    def test_not_hot_at_threshold_boundary(self):
        entry = make_forecast_entry(feels_like_f=90.0)
        assert _is_hot(entry) is False

    def test_cold_below_threshold(self):
        entry = make_forecast_entry(feels_like_f=35.0)
        assert _is_cold(entry) is True

    def test_not_cold_at_threshold_boundary(self):
        entry = make_forecast_entry(feels_like_f=40.0)
        assert _is_cold(entry) is False

    def test_comfortable_temp_is_neither(self):
        entry = make_forecast_entry(feels_like_f=72.0)
        assert _is_hot(entry) is False
        assert _is_cold(entry) is False


# ---------------------------------------------------------------------------
# The core rubric scenario: "does it suggest a bus when it's raining?"
# ---------------------------------------------------------------------------

class TestRubricCoreScenario:
    def test_severe_rain_overlapping_event_suggests_alternate_transport(self):
        """The rubric's literal Guardrails example: when severe rain
        overlaps a scheduled event, advice must suggest leaving earlier
        or taking alternate transport (bus/rideshare).
        """
        forecast = [
            make_forecast_entry(
                date="2026-06-20",
                hour=14,
                condition="Rain",
                description="heavy rain",
                precipitation_chance=0.8,
            )
        ]
        events = [make_event(title="Client meeting", date="2026-06-20", hour=14)]

        advice = generate_advice(forecast, events)

        assert len(advice) == 1
        message = advice[0].message.lower()
        assert "bus" in message or "rideshare" in message
        assert "client meeting" in message
        assert advice[0].related_event == "Client meeting"

    def test_mild_rain_overlapping_event_suggests_umbrella_not_transport(self):
        """Below the severe threshold, advice should mention an umbrella,
        not push the user toward alternate transport.
        """
        forecast = [
            make_forecast_entry(
                date="2026-06-20",
                hour=9,
                condition="Rain",
                description="light rain",
                precipitation_chance=0.5,
            )
        ]
        events = [make_event(title="Team standup", date="2026-06-20", hour=9)]

        advice = generate_advice(forecast, events)

        assert len(advice) == 1
        message = advice[0].message.lower()
        assert "umbrella" in message
        assert "bus" not in message

    def test_rain_with_no_overlapping_event_has_no_transport_suggestion(self):
        """Per project rules: transport suggestions only fire when bad
        weather overlaps an actual calendar event.
        """
        forecast = [
            make_forecast_entry(
                date="2026-06-20",
                hour=14,
                condition="Rain",
                description="heavy rain",
                precipitation_chance=0.8,
            )
        ]
        events: list[CalendarEvent] = []  # no events at all

        advice = generate_advice(forecast, events)

        assert len(advice) == 1
        message = advice[0].message.lower()
        assert "bus" not in message
        assert advice[0].related_event is None

    def test_clear_weather_with_event_produces_no_advice(self):
        """A clear, comfortable forecast should not generate noise."""
        forecast = [
            make_forecast_entry(
                date="2026-06-20", hour=14, condition="Clear",
                description="clear sky", precipitation_chance=0.0, feels_like_f=75.0,
            )
        ]
        events = [make_event(title="Lunch", date="2026-06-20", hour=14)]

        advice = generate_advice(forecast, events)

        assert advice == []

    def test_event_on_different_date_does_not_match_forecast(self):
        """Events must match by date, not just time-of-day bucket."""
        forecast = [
            make_forecast_entry(
                date="2026-06-20", hour=14, condition="Thunderstorm",
                description="storm", precipitation_chance=0.9,
            )
        ]
        events = [make_event(title="Future meeting", date="2026-06-25", hour=14)]

        advice = generate_advice(forecast, events)

        assert len(advice) == 1
        assert advice[0].related_event is None  # no match across dates

    def test_heat_advisory_mentions_event_when_overlapping(self):
        forecast = [
            make_forecast_entry(
                date="2026-06-20", hour=14, condition="Clear",
                description="sunny", precipitation_chance=0.0, feels_like_f=98.0,
            )
        ]
        events = [make_event(title="Outdoor festival", date="2026-06-20", hour=14)]

        advice = generate_advice(forecast, events)

        assert len(advice) == 1
        message = advice[0].message.lower()
        assert "hydrated" in message
        assert "outdoor festival" in message

    def test_cold_advisory_triggers_below_threshold(self):
        forecast = [
            make_forecast_entry(
                date="2026-06-20", hour=7, condition="Clear",
                description="clear and cold", precipitation_chance=0.0, feels_like_f=28.0,
            )
        ]
        events = [make_event(title="Morning commute", date="2026-06-20", hour=7)]

        advice = generate_advice(forecast, events)

        assert len(advice) == 1
        message = advice[0].message.lower()
        assert "warmly" in message
        assert "morning commute" in message