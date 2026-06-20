Weather-Aware

1. The AI's "vibe" drift when it defaulted to bash/Unix terminal syntax (ls -a, touch, mkdir -p) without first confirming the project was on Windows/PowerShell — this caused an early command to fail and had to be corrected to PowerShell equivalents (Get-ChildItem -Force, New-Item, etc.) before work could continue.

2. The "Builder Hammer" (manual coding was use to fix a logical error) when a code review of advisor.py found that _find_overlapping_event() used an early `return` inside a loop, silently dropping advice for any event after the first one matching a given date/time-of-day bucket (e.g. two events both in the "morning" window). Manually rewrote it as _find_overlapping_events() (plural) to collect all matches, updated generate_advice() to produce one Advice entry per overlapping event, and added a regression test (test_multiple_events_in_same_bucket_all_get_advice) to lock the fix in.

3. The most successful "steering" prompt was specifying the exact return data shape (as a docstring with example values) before writing fetch_forecast() in weather.py — defining the dict keys, types, and a sample output up front meant the function worked correctly against the live OpenWeather API on the first run, with no debugging needed.
