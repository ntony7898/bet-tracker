# Bet Tracker

Live: https://ntony7898.github.io/bet-tracker/ (units only; 1 unit = $20)

## Refresh (one line)

```
cd /workspace/results && python3 build_tracker.py && /workspace/bet-tracker/publish.sh
```

`publish.sh` rebuilds data.json (incl. units_by_sport) and app.js, runs the web tests, and pushes to main (Pages updates in ~1 min).


The tracker is a **private Canvas** in Tony's Grok Bot Library, titled "Bet Tracker".
- Canvas id: `823b6d30-5ba1-42d5-b3b6-00281f1c96fb`
- It has no public URL and no password. Everything is embedded in the page (no fetches, no stored state).
- The data source is `/workspace/results/Bet_tracker.xlsx` (built by Bet's `build_tracker.py`). It is units only; the only dollar figure is "1 unit = $20".
- The public GitHub Pages site is retired and `publish.sh` is disabled. Never push the tracker publicly.

## Refresh the private Canvas (Bet, after each grading)
1. `cd /workspace/results && python3 build_tracker.py && python3 /workspace/bet-tracker/refresh_canvas.py`
   - This prints either `no changes` or `N edit(s) ... -> canvas_live_edits.json`.
2. If there are edits, call **EditCanvas** (cursor namespace) with `canvas_id` `823b6d30-5ba1-42d5-b3b6-00281f1c96fb` and `edits` = the `edits` array from `/workspace/bet-tracker/canvas_live_edits.json`, verbatim. Each edit swaps one data line: a day, the `UPDATED` stamp, or a totals constant. New days are inserted after `const DAYS: any=[`.
3. Once EditCanvas succeeds, run `python3 /workspace/bet-tracker/refresh_canvas.py --applied` so `canvas.live.tsx` matches the live page.
   - If an edit fails to match, the live page drifted. ReadCanvas (write_to_file) the id, save the source as `canvas.live.tsx`, then repeat from step 1.

## Files
- `canvas.live.tsx`: exact copy of the published canvas source. The render code is JSX, because canvases reject `dangerouslySetInnerHTML`.
- `refresh_canvas.py`: xlsx -> data lines -> `canvas_live_edits.json`. It runs `build_canvas.py` and `refresh.py` for the data. It changes data lines only, never the live render code or CSS.
- `build_canvas.py` / `canvas_template.tsx` / `preview.html` / `test_canvas.py`: data generation and the local preview harness.
- The old PWA files (`index.html`, `app.js`, `app.css`, `sw.js`) are kept for reference only.

## Keep totals forever: `units_history.json` (NEVER DELETE)
Tickets older than ~2 months (cutoff = today minus 2 months, America/Phoenix; days with a pending ticket are kept) drop out of the ticket list. Before a day is pruned, `prune.py` (called by `build_canvas.py`) snapshots its units, W/L/void/pending counts, ticket count and per-sport breakdown into **`units_history.json`** (atomic write, previous copy in `units_history.json.bak`, both committed). Totals = archive + live tickets. Pruned days still show in Past as a compact row with their net units.
Publish aborts if the archive is missing after being in git, or if pruned totals differ from unpruned totals or from the xlsx Grand total. `test_canvas.py` simulates later "today" cutoffs on a temp copy and asserts identical totals. Testing overrides only: `PRUNE_DAYS=N`, `BT_TODAY=YYYY-MM-DD`.
