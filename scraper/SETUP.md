# Scraper Setup

## First-time setup

```bash
cd /Volumes/X10\ Pro/repos/curtain-call/scraper
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Ollama (local model — needed for ~30-40% of sites)

```bash
# Install Ollama if you haven't
brew install ollama

# Pull the extraction model
ollama pull qwen2.5:7b

# Ollama starts automatically on demand, but you can also run it manually:
ollama serve
```

The scraper checks if Ollama is running before attempting LLM extraction.
If it's not up, it skips the LLM step and logs a warning — it won't crash.

## Run the scraper

```bash
# From the repo root
source scraper/.venv/bin/activate

# Full run (all 25 venues)
python3 -m scraper.scrape

# Dry run (list venues, don't fetch)
python3 -m scraper.scrape --dry-run

# Single venue (useful for testing)
python3 -m scraper.scrape --venue "Kitchen Dog Theater"
```

Or use the weekly refresh script which runs, builds, and pushes:

```bash
bash scripts/weekly_refresh.sh
```

## Output

Writes to `public/data/shows-dallas.json`. After running, rebuild the site
to copy it into `docs/`:

```bash
npm run build
```

Or just run `scripts/weekly_refresh.sh` which does both.

## Scheduling (weekly, macOS)

```bash
# Copy the launchd plist
cp scripts/com.curtaincall.scraper.plist ~/Library/LaunchAgents/

# Edit it to confirm the paths are correct
nano ~/Library/LaunchAgents/com.curtaincall.scraper.plist

# Load it
launchctl load ~/Library/LaunchAgents/com.curtaincall.scraper.plist

# Verify it's loaded
launchctl list | grep curtaincall
```

To run immediately (test the schedule):
```bash
launchctl start com.curtaincall.scraper
```

To unload:
```bash
launchctl unload ~/Library/LaunchAgents/com.curtaincall.scraper.plist
```
