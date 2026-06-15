#!/usr/bin/env bash
# Curtain Call — weekly show data refresh
# Runs the scraper, rebuilds the site, and pushes to GitHub.
# Designed to be run by launchd or manually.

set -euo pipefail

REPO="/Volumes/X10 Pro/repos/curtain-call"
VENV="$REPO/scraper/.venv"
LOG="$REPO/scripts/refresh.log"

log() { echo "$(date '+%Y-%m-%d %H:%M:%S')  $*" | tee -a "$LOG"; }

log "=== Curtain Call weekly refresh starting ==="

# ── 1. Run scraper ────────────────────────────────────────────────────────────
log "Running scraper..."
source "$VENV/bin/activate"
cd "$REPO"
python3 -m scraper.scrape
deactivate

# ── 2. Build site (copies public/data/ into docs/) ───────────────────────────
log "Building site..."
npm_config_registry=https://registry.npmjs.org \
npm_config_always_auth=false \
npm_config_cache=/tmp/npm-cache \
npm run build --prefix "$REPO"

# ── 3. Commit and push ────────────────────────────────────────────────────────
log "Committing and pushing..."
cd "$REPO"
git add public/data/ docs/data/ docs/assets/
COUNT=$(python3 -c "import json; d=json.load(open('public/data/shows-dallas.json')); print(d['show_count'])" 2>/dev/null || echo "?")
git commit -m "Weekly show data refresh — $COUNT shows ($(date '+%Y-%m-%d'))" || {
  log "Nothing to commit (data unchanged)."
  exit 0
}
git push

log "=== Done. $COUNT shows published. ==="
