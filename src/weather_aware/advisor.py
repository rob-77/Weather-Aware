"""
advisor.py

Pure rule-based logic that combines weather forecast data with calendar
events to produce actionable advice.

Constraints (see .cursor/rules/architecture.mdc, docs/rules.md, and
specs/PRD.md Section 4):
- This module contains NO I/O: no print(), no API calls, no file reads.
- Functions are pure: (weather data, calendar events) -> advice.
- Advice synthesis is rule-based by design (not LLM-powered), so that
  behavior here is deterministic and fully unit-testable.

Rules implemented (see specs/PRD.md and project discussion for rationale):
- Rain/storm advice: triggered when condition is Rain/Thunderstorm/Drizzle
  AND precipitation chance > 40%. Thunderstorm triggers regardless of %.
- Heat advisory: feels_like_f > 90.
- Cold advisory: feels_like_f < 40.
- Transport/timing suggestion: only fires when bad weather (precip > 60%,
  or any Thunderstorm) overlaps an actual calendar event.
- Time-of-day buckets: morning (5-11), afternoon (12-16), evening (17-21),
  night (22-4). Matching is done by date + time-of-day bucket, not exact hour.
"""

from typing import NamedTuple

from weather_aware.calendar_reader import CalendarEvent


RAIN_CONDITIONS = {"Rain", "Thunderstorm", "Drizzle"}
RAIN_CHANCE_THRESHOLD = 0.4
SEVERE_RAIN_CHANCE_THRESHOLD = 0.6
HOT_THRESHOLD_F = 90.0
COLD_THRESHOLD_F = 40.0


class Advice(NamedTuple):
    """A single piece of advice, tied to the date/time-of-day it concerns."""
    date: str
    time_of_day: str
    message: str
    related_event: str | None  # event title, or None for general advice


def time_of_day_bucket(hour: int) -> str:
    """Map an hour (0-23) to a time-of-day bucket.

    Args:
        hour: Hour of day, 0-23.

    Returns:
        One of "morning", "afternoon", "evening", "night".
    """
    if 5 <= hour <= 11:
        return "morning"
    if 12 <= hour <= 16:
        return "afternoon"
    if 17 <= hour <= 21:
        return "evening"
    return "night"


def _is_rainy(forecast_entry: dict) -> bool:
    """Whether a forecast entry counts as 'rainy' per project rules."""
    condition = forecast_entry["condition"]
    chance = forecast_entry["precipitation_chance"]

    if condition == "Thunderstorm":
        return True
    if condition in RAIN_CONDITIONS and chance > RAIN_CHANCE_THRESHOLD:
        return True
    return False


def _is_severe_rain(forecast_entry: dict) -> bool:
    """Whether a forecast entry is severe enough to warrant a transport
    suggestion (not just an umbrella mention).
    """
    condition = forecast_entry["condition"]
    chance = forecast_entry["precipitation_chance"]

    if condition == "Thunderstorm":
        return True
    if condition in RAIN_CONDITIONS and chance > SEVERE_RAIN_CHANCE_THRESHOLD:
        return True
    return False


def _is_hot(forecast_entry: dict) -> bool:
    return forecast_entry["feels_like_f"] is not None and forecast_entry["feels_like_f"] > HOT_THRESHOLD_F


def _is_cold(forecast_entry: dict) -> bool:
    return forecast_entry["feels_like_f"] is not None and forecast_entry["feels_like_f"] < COLD_THRESHOLD_F


def _find_overlapping_events(
    forecast_entry: dict, events: list[CalendarEvent]
) -> list[CalendarEvent]:
    """Find ALL calendar events whose date and time-of-day bucket match
    this forecast entry.

    BUGFIX (manual fix, see README Vibe Report): the original version of
    this function returned only the first matching event via an early
    `return`. If two events fell in the same date + time-of-day bucket
    (e.g. a 9am standup and a 10am dentist appointment, both "morning"),
    the second event's advice was silently dropped. This version collects
    ALL matches so advice can be generated for every overlapping event.

    Args:
        forecast_entry: A single normalized forecast entry (see weather.py).
        events: List of validated calendar events.

    Returns:
        A list of all CalendarEvents that fall in this date/time-of-day
        window. Empty list if none overlap.
    """
    entry_date = forecast_entry["date"]
    entry_bucket = time_of_day_bucket(forecast_entry["hour"])

    matches = []
    for event in events:
        event_date = event.start.strftime("%Y-%m-%d")
        event_bucket = time_of_day_bucket(event.start.hour)
        if event_date == entry_date and event_bucket == entry_bucket:
            matches.append(event)
    return matches


def generate_advice(
    forecast: list[dict], events: list[CalendarEvent]
) -> list[Advice]:
    """Generate advice by combining forecast data with calendar events.

    Args:
        forecast: List of normalized forecast entries from weather.py's
            fetch_forecast().
        events: List of validated CalendarEvent objects from
            calendar_reader.py's load_calendar().

    Returns:
        A list of Advice entries. If multiple events overlap the same
        forecast window, one Advice entry is produced per event (see
        BUGFIX note on _find_overlapping_events). If no events overlap
        but the weather is still noteworthy, one general Advice entry
        is produced. Forecast entries with nothing noteworthy produce
        no advice at all.
    """
    advice_list: list[Advice] = []

    for entry in forecast:
        bucket = time_of_day_bucket(entry["hour"])
        if not (_is_rainy(entry) or _is_hot(entry) or _is_cold(entry)):
            continue

        overlapping_events = _find_overlapping_events(entry, events)

        if overlapping_events:
            for event in overlapping_events:
                advice_list.append(_build_advice_for_entry(entry, bucket, event))
        else:
            advice_list.append(_build_advice_for_entry(entry, bucket, None))

    return advice_list


def _build_advice_for_entry(
    entry: dict, bucket: str, event: CalendarEvent | None
) -> Advice:
    """Dispatch to the right advice builder based on which condition
    triggered (rain takes priority, then heat, then cold).
    """
    event_title = event.title if event else None
    if _is_rainy(entry):
        return _build_rain_advice(entry, bucket, event, event_title)
    elif _is_hot(entry):
        return _build_heat_advice(entry, bucket, event_title)
    else:
        return _build_cold_advice(entry, bucket, event_title)


def _build_rain_advice(
    entry: dict,
    bucket: str,
    overlapping_event: CalendarEvent | None,
    event_title: str | None,
) -> Advice:
    pct = round(entry["precipitation_chance"] * 100)
    base = f"{entry['description'].capitalize()} expected ({pct}% chance of rain)."

    if overlapping_event is not None:
        base += f" This overlaps your '{overlapping_event.title}'."
        if _is_severe_rain(entry):
            base += " Consider leaving earlier or taking the bus/rideshare instead of driving."
        else:
            base += " Bring an umbrella."
    else:
        base += " Bring an umbrella if you're heading out."

    return Advice(date=entry["date"], time_of_day=bucket, message=base, related_event=event_title)


def _build_heat_advice(entry: dict, bucket: str, event_title: str | None) -> Advice:
    message = (
        f"High heat expected (feels like {entry['feels_like_f']:.0f}\u00b0F). "
        f"Stay hydrated and dress lightly."
    )
    if event_title:
        message += f" Keep this in mind for your '{event_title}'."
    return Advice(date=entry["date"], time_of_day=bucket, message=message, related_event=event_title)


def _build_cold_advice(entry: dict, bucket: str, event_title: str | None) -> Advice:
    message = (
        f"Cold conditions expected (feels like {entry['feels_like_f']:.0f}\u00b0F). "
        f"Dress warmly and allow extra travel time."
    )
    if event_title:
        message += f" Keep this in mind for your '{event_title}'."
    return Advice(date=entry["date"], time_of_day=bucket, message=message, related_event=event_title)