# calendar.json Schema

This document defines the schema for `calendar.json`, the local file the Weather-Aware assistant reads to learn about the user's scheduled events. See `specs/PRD.md` Section 7 for a summary; this file is the full reference.

## Top-Level Structure

```json
{
  "events": [ ... ]
}
```

The file must be a single JSON object with one required key, `events`, whose value is a list of event objects. An empty list (`"events": []`) is valid and means no events are scheduled.

## Event Object

Each item in `events` must be a JSON object with these **required** fields:

| Field      | Type   | Format                          | Description                                  |
|------------|--------|----------------------------------|-----------------------------------------------|
| `title`    | string | non-empty                        | Short name of the event, e.g. "Team standup" |
| `start`    | string | ISO 8601 datetime                | When the event starts                        |
| `end`      | string | ISO 8601 datetime, after `start` | When the event ends                          |
| `location` | string | non-empty                        | Free-text location, e.g. "Office" or "Downtown Houston" |

### ISO 8601 datetime format

`start` and `end` must be strings in the form:
Example: `"2026-06-20T09:00:00"` means June 20, 2026, at 9:00 AM.

## Example

```json
{
  "events": [
    {
      "title": "Team standup",
      "start": "2026-06-20T09:00:00",
      "end": "2026-06-20T09:30:00",
      "location": "Office"
    },
    {
      "title": "Client meeting downtown",
      "start": "2026-06-20T14:00:00",
      "end": "2026-06-20T15:00:00",
      "location": "Downtown Houston"
    }
  ]
}
```

## Validation Behavior

Validation is handled by `src/weather_aware/calendar_reader.py`. Behavior:

- **File-level errors** (file missing, not valid JSON, no top-level `events` list) cause a hard failure (`CalendarLoadError`) — the app cannot proceed without a readable calendar file.
- **Event-level errors** (missing field, empty string, invalid date format, `end` not after `start`) cause that single event to be **skipped**, not a hard failure. The rest of the valid events still load, and a warning is reported back to the user listing which event(s) were skipped and why. This design choice is documented in `specs/PRD.md`.

## Out of Scope

- No field for marking an event as "outdoor" vs. "indoor" — this was deliberately descoped (see PRD Section 3).
- No recurring-event syntax — each occurrence must be its own entry in the list.
- No timezone field — all datetimes are treated as local time.