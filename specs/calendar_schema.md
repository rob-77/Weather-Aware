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