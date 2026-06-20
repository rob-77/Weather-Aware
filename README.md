# Weather-Aware

A CLI-based (REPL) personal assistant that fetches live weather data, reads your local schedule, and synthesizes weather-aware advice for your day.

## What it does

- Asks for your city, then fetches a live 5-day forecast from the OpenWeather API.
- Reads your schedule from a local `calendar.json` file.
- Combines the two using rule-based logic to produce specific, actionable advice — e.g. warning you about rain overlapping a meeting, or suggesting alternate transport during severe weather.
- Runs as an interactive REPL: ask "today", "week", or just talk naturally ("what's my day look like?").

See `specs/PRD.md` for the full product requirements and design rationale, including why advice synthesis is rule-based rather than LLM-powered.

## Getting Started

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Get an OpenWeather API key
Sign up for a free key at [openweathermap.org/api](https://openweathermap.org/api). New keys can take up to ~2 hours to activate.

### 3. Set up your `.env` file
Copy `.env.example` to `.env` and add your real key:
```
OPENWEATHER_API_KEY=your_actual_key_here
```
`.env` is gitignored and will never be committed — keep your real key there only.

### 4. Add your schedule
Edit `calendar.json` at the repo root with your own events. See `specs/calendar_schema.md` for the full schema.

### 5. Run it
```bash
python main.py
```

You'll be prompted for a city, then can use commands like `today`, `week`, `help`, and `quit` — or just type naturally.

## Project Structure

```
src/weather_aware/
├── weather.py            # OpenWeather API integration
├── calendar_reader.py    # Reads + validates calendar.json
├── advisor.py            # Rule-based advice logic (pure, no I/O)
└── cli.py                # REPL loop and orchestration
```

## Running Tests

```bash
pytest tests/ -v
```

23 tests cover the advisor logic, including the core scenario: does it suggest alternate transport when severe rain overlaps a scheduled event?

---

## Vibe Report

1. The AI's "vibe" drift when it defaulted to bash/Unix terminal syntax (ls -a, touch, mkdir -p) without first confirming the project was on Windows/PowerShell — this caused an early command to fail and had to be corrected to PowerShell equivalents (Get-ChildItem -Force, New-Item, etc.) before work could continue.

2. The "Builder Hammer" (manual coding was use to fix a logical error) when a code review of advisor.py found that _find_overlapping_event() used an early `return` inside a loop, silently dropping advice for any event after the first one matching a given date/time-of-day bucket (e.g. two events both in the "morning" window). Manually rewrote it as _find_overlapping_events() (plural) to collect all matches, updated generate_advice() to produce one Advice entry per overlapping event, and added a regression test (test_multiple_events_in_same_bucket_all_get_advice) to lock the fix in.

3. The most successful "steering" prompt was specifying the exact return data shape (as a docstring with example values) before writing fetch_forecast() in weather.py — defining the dict keys, types, and a sample output up front meant the function worked correctly against the live OpenWeather API on the first run, with no debugging needed.
