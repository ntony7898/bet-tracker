#!/usr/bin/env bash
# Rebuild the public Bet Tracker web app from Bet_tracker.xlsx + units_by_sport.json, test it, and push to GitHub Pages.
set -euo pipefail
cd "$(dirname "$0")"
[ -f /workspace/results/build_tracker.py ] && (cd /workspace/results && python3 build_tracker.py)
python3 build_canvas.py            # data.json (+units_by_sport), app.js (web app), canvas.tsx/preview.html
python3 test_canvas.py --web | tail -1 | grep -q 'ALL PASS' || { echo "web tests FAILED, not pushing" >&2; exit 1; }
git add index.html app.js app.css sw.js data.json manifest.webmanifest icon.svg units_history.json units_history.json.bak build_canvas.py prune.py test_canvas.py README.md publish.sh
git commit -qm "data: $(date '+%F %H:%M')" || { echo "no changes"; exit 0; }
git push -q origin main && echo "pushed: https://ntony7898.github.io/bet-tracker/ (live in ~1 min)"
