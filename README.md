Weather-Aware

1. The AI's "vibe" drift when it defaulted to bash/Unix terminal syntax (ls -a, touch, mkdir -p) without first confirming the project was on Windows/PowerShell — this caused an early command to fail and had to be corrected to PowerShell equivalents (Get-ChildItem -Force, New-Item, etc.) before work could continue.

2. The "Builder Hammer" (manual codding was use to fix a logical error when

3. The most successful "steering" prompt was specifying the exact return data shape (as a docstring with example values) before writing fetch_forecast() in weather.py — defining the dict keys, types, and a sample output up front meant the function worked correctly against the live OpenWeather API on the first run, with no debugging needed.
