# Product Requirements Document (PRD)
## Weather-Aware: A CLI Personal Assistant

**Status:** Draft v1
**Owner:** Roberto
**Last updated:** 2026-06-19

---

## 1. Problem Statement

People plan their day around two largely disconnected sources of information: their calendar (what they're doing and when) and the weather (what conditions they'll face). Checking both manually and mentally cross-referencing them — "I have a 9am that's a 20-minute walk away, is it going to rain at 9am?" — is a small but real daily friction point.

This project builds a command-line personal assistant that closes that gap automatically: it reads the user's schedule, fetches a weather forecast, and synthesizes time-aware, weather-aware advice for the day(s) ahead.

## 2. Goals

- Provide a REPL-style CLI where a user can ask about their day and get weather-aware advice tied to their actual calendar events.
- Fetch live weather data (current + multi-day forecast) for a city the user specifies each session.
- Read events from a local `calendar.json` file (title, start, end, location).
- Match weather conditions to events by **date and time-of-day** (morning / afternoon / evening), and produce relevant, specific advice (e.g., "Bring an umbrella to your 2pm meeting — afternoon rain expected").
- Keep the system cleanly modular: API access, calendar parsing, advice logic, and CLI/UI are fully separated.
- Cover the core advice logic with automated tests that prove the *logic* is correct, not just that the app runs.

## 3. Non-Goals (explicitly out of scope for v1)

- **Outdoor vs. indoor event detection.** Classifying whether an event is outdoors (and therefore more weather-sensitive) based on free-text `location` strings was considered and deliberately descoped. Reliable classification from arbitrary text ("Discovery Green" vs. "123 Main St" vs. "The Yard") isn't achievable with simple rule-based keyword matching without a high false-positive/false-negative rate — and incorrect classification here would undermine the reliability of the advice itself. This is noted as a strong candidate for a future LLM-assisted enhancement (see Section 8).
- Persisting state between sessions (e.g., remembering the last city used) — each session starts fresh.
- Calendar write access (the assistant reads `calendar.json`, it does not create or modify events).
- Multi-user support or authentication.
- A graphical interface — this is CLI/REPL only.

## 4. Why Rule-Based Advice Synthesis (and not LLM-powered)

This project deliberately uses **rule-based logic** for the advice synthesis step, not an LLM call. Reasoning:

1. **Determinism and testability.** The rubric's "Guardrails" criterion explicitly tests whether the app's logic is correct (e.g., "does it suggest a bus when it's raining?"). Rule-based logic produces the same output for the same input every time, which makes it possible to write precise, repeatable unit tests. An LLM-generated suggestion is non-deterministic and much harder to assert against in an automated test.
2. **No added cost or external dependency.** The app already depends on one external API (weather). Adding an LLM API call for advice would introduce a second network dependency, a second API key to manage, and a second point of failure for a feature whose underlying logic (temperature/precipitation thresholds → advice) doesn't actually require natural language reasoning to get right.
3. **Transparency.** Rule-based advice is fully explainable — every suggestion traces back to a specific, readable condition in `advisor.py` (e.g., `if precipitation_chance > 50: suggest umbrella`). This is easier to debug, easier to extend, and easier to defend in the "Integrity of Intent" writeup than "the model decided to say this."
4. **Scope fit.** The advice needed here is narrow and well-defined (weather conditions × time-of-day × event presence → a small set of actionable suggestions). This is a good fit for rules; it doesn't need the open-ended reasoning an LLM is suited for.

**Future consideration:** an LLM-powered mode is a natural v2 extension — e.g., to generate more natural-sounding phrasing of the same rule-based conclusions, or to attempt the outdoor/indoor classification descoped above. This is noted as a possible enhancement, not built in v1.

## 5. User Stories

- As a user, I want to start the app and enter my city, so the assistant knows where to fetch weather for.
- As a user, I want to ask "what's my day look like" and get a synthesis of my events plus relevant weather advice for each.
- As a user, I want to be warned about weather that could affect a specific event (e.g., rain during an afternoon event, cold mornings for an early commute).
- As a user, I want clear, plain-language advice (not raw weather data dumps).
- As a user, I want the app to handle a missing or malformed `calendar.json` gracefully, without crashing.

## 6. System Design Overview

```
src/weather_aware/
├── weather.py            # OpenWeather API calls only. No print(), no advice logic.
├── calendar_reader.py    # Reads + validates calendar.json. No print().
├── advisor.py            # Pure functions: (weather data, calendar events) -> advice. No I/O.
├── cli.py                # REPL loop. Calls the above modules, handles all print()/input().
```

**Data flow:**
1. `cli.py` prompts the user for a city.
2. `weather.py` calls the OpenWeather API, returns structured forecast data (current + multi-day, broken out by time-of-day where available).
3. `calendar_reader.py` loads and validates `calendar.json`, returns a list of event objects.
4. `advisor.py` takes both data sets, matches events to forecast windows by date + time-of-day, and returns a list of advice strings.
5. `cli.py` prints the results.

This separation is the basis for the "System Orchestration" criterion: `cli.py` never reaches into the weather API or writes advice logic directly, it only orchestrates calls to the other three modules.

## 7. calendar.json Schema

Minimum schema (see `specs/calendar_schema.md` for full detail):

```json
{
  "events": [
    {
      "title": "Team standup",
      "start": "2026-06-20T09:00:00",
      "end": "2026-06-20T09:30:00",
      "location": "Office"
    }
  ]
}
```

## 8. Future Enhancements (out of scope, noted for completeness)

- Outdoor/indoor event classification (likely LLM-assisted)
- Optional LLM-powered advice phrasing mode
- Persisting last-used city between sessions
- Multi-day "week ahead" summary view

## 9. Success Criteria

- App runs as a REPL: user can issue multiple queries in one session without restarting.
- Weather is fetched live from OpenWeather for a user-specified city.
- Calendar events are correctly loaded from `calendar.json` and matched to the right forecast day/time-of-day window.
- Advice is specific and correct for known test scenarios (e.g., rain + morning commute event → umbrella/early-departure suggestion).
- Core logic in `advisor.py` is covered by automated tests in `tests/`.
- Code is organized per Section 6 with no business logic inside `cli.py`.
