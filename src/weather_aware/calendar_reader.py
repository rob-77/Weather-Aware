"""
calendar_reader.py

Reads and validates the local calendar.json file.

Constraints (see .cursor/rules/architecture.mdc and docs/rules.md):
- This module ONLY reads and validates calendar.json.
- No print() statements, no advice logic, no weather/API calls.
- Malformed individual events are skipped (not fatal) so one bad event
  doesn't prevent the rest of the schedule from loading. Skipped events
  are reported back to the caller, not silently dropped.
"""

import json
import os
from datetime import datetime
from typing import NamedTuple


REQUIRED_FIELDS = ("title", "start", "end", "location")


class CalendarLoadError(Exception):
    """Raised when calendar.json itself cannot be read or parsed at all
    (e.g. file missing, not valid JSON, wrong top-level shape).

    This is distinct from a single malformed event, which is skipped
    rather than raised — see load_calendar()'s return value.
    """
    pass


class CalendarEvent(NamedTuple):
    """A single validated calendar event."""
    title: str
    start: datetime
    end: datetime
    location: str


class CalendarLoadResult(NamedTuple):
    """Result of loading calendar.json: valid events plus any warnings
    about events that were skipped due to validation errors.
    """
    events: list[CalendarEvent]
    warnings: list[str]


def load_calendar(path: str = "calendar.json") -> CalendarLoadResult:
    """Load and validate events from a calendar.json file.

    Args:
        path: Path to the calendar JSON file. Defaults to "calendar.json"
            in the current working directory.

    Returns:
        A CalendarLoadResult containing the list of successfully validated
        CalendarEvent objects, and a list of human-readable warning strings
        for any events that were skipped.

    Raises:
        CalendarLoadError: if the file is missing, not valid JSON, or does
            not have the expected top-level {"events": [...]} shape. This
            is a hard failure (no usable data at all), unlike a single
            malformed event, which is skipped instead.
    """
    if not os.path.exists(path):
        raise CalendarLoadError(
            f"Calendar file not found at '{path}'. "
            f"Create one with a top-level 'events' list."
        )

    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as exc:
            raise CalendarLoadError(f"'{path}' is not valid JSON: {exc}") from exc

    if not isinstance(data, dict) or "events" not in data:
        raise CalendarLoadError(
            f"'{path}' must be a JSON object with a top-level 'events' list."
        )

    raw_events = data["events"]
    if not isinstance(raw_events, list):
        raise CalendarLoadError(f"'events' in '{path}' must be a list.")

    valid_events: list[CalendarEvent] = []
    warnings: list[str] = []

    for index, raw_event in enumerate(raw_events):
        try:
            event = _validate_event(raw_event)
            valid_events.append(event)
        except ValueError as exc:
            warnings.append(f"Skipped event at index {index}: {exc}")

    return CalendarLoadResult(events=valid_events, warnings=warnings)


def _validate_event(raw_event: dict) -> CalendarEvent:
    """Validate and parse a single raw event dict into a CalendarEvent.

    Args:
        raw_event: One element from the "events" list in calendar.json.

    Returns:
        A validated CalendarEvent.

    Raises:
        ValueError: if a required field is missing, empty, or a date
            string can't be parsed. The message is meant to be readable
            directly in a warning to the user.
    """
    if not isinstance(raw_event, dict):
        raise ValueError("event is not a JSON object")

    missing = [field for field in REQUIRED_FIELDS if field not in raw_event]
    if missing:
        raise ValueError(f"missing required field(s): {', '.join(missing)}")

    title = raw_event["title"]
    location = raw_event["location"]
    if not isinstance(title, str) or not title.strip():
        raise ValueError("'title' must be a non-empty string")
    if not isinstance(location, str) or not location.strip():
        raise ValueError("'location' must be a non-empty string")

    start = _parse_datetime(raw_event["start"], "start")
    end = _parse_datetime(raw_event["end"], "end")

    if end <= start:
        raise ValueError("'end' must be after 'start'")

    return CalendarEvent(title=title, start=start, end=end, location=location)


def _parse_datetime(value: object, field_name: str) -> datetime:
    """Parse an ISO 8601 datetime string from calendar.json.

    Args:
        value: The raw value from the JSON (expected to be a string).
        field_name: Name of the field, used in error messages.

    Returns:
        A parsed datetime object.

    Raises:
        ValueError: if value is not a string or not a valid ISO 8601
            datetime (e.g. "2026-06-20T09:00:00").
    """
    if not isinstance(value, str):
        raise ValueError(f"'{field_name}' must be a string")
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"'{field_name}' is not a valid ISO 8601 datetime: '{value}'"
        ) from exc