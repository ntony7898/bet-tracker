#!/usr/bin/env bash
# Rebuild Excel, regenerate data.json, commit and push to GitHub Pages.
set -euo pipefail
cd /workspace/results && python3 build_tracker.py >/dev/null
cd /workspace/bet-tracker && python3 refresh.py
git add -A && (git diff --cached --quiet && echo "no changes" || { git commit -qm "data: $(date +%F\ %H:%M)"; git push -q origin main; echo pushed; })
