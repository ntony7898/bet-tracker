# Bet Tracker (mobile PWA)

Static app (no build step). It reads only `data.json`, which `refresh.py` generates from `/workspace/results/Bet_tracker.xlsx`, the output of Bet's `build_tracker.py`. The Excel file is the source of truth, so the leg marks, cleaned pick text, units and banners match it exactly.

## Refresh after each grading (one command)
```
/workspace/bet-tracker/publish.sh
```
This runs `build_tracker.py` (Excel), then `refresh.py` (data.json), then commits and pushes to GitHub Pages. It is idempotent: if nothing changed, it does not commit.
To regenerate only, without publishing: `python3 /workspace/bet-tracker/refresh.py`

## Files
- `app.css`: **all** styling (CSS variables at the top). JS only emits classes and `data-result` / `data-mark` attributes.
- `app.js`: views (Days, Units, Records), filter, search, and jump-to-date.
- `sw.js`: service worker. Bump `VERSION` on every app (not data) release. data.json is network-first.
- `test_app.py`: Playwright check at 390x844 against the Excel file (`python3 test_app.py`).
