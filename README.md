# Curtain Call

Find the show. Remember the night.

A concept pitch for a theater discovery and personal show-log app.

**Pitch deck → https://michaelnotbolton.github.io/curtain-call**

---

## What this is

This repo contains a concept pitch for Curtain Call — an app for theater audiences that:

1. **Finds shows** — search by title or playwright (actor on roadmap), with US-wide results, distance/date filters, and a map view
2. **Surfaces local productions** — automatically indexes community theater, school shows, and small venues without requiring anyone to submit them
3. **Logs your theater life** — a personal record of every production you've seen: venue, dates, your notes

The pitch deck site compares the feature set against GoSeeAShow, Showify, and StagePass.

---

## Pitch docs (`/pitch`)

Technical and strategic reference material not included in the public pitch page:

- [`DISCOVERY_ENGINE.md`](pitch/DISCOVERY_ENGINE.md) — how automated local show indexing would work, including venue seeding strategies, crawl/extraction pipeline, LLM cost trade-offs, and open risks
- [`FEATURE_SPEC.md`](pitch/FEATURE_SPEC.md) — full v1 scope, v2 roadmap, and explicitly out-of-scope decisions
- [`COMPETITOR_ANALYSIS.md`](pitch/COMPETITOR_ANALYSIS.md) — detailed breakdown of GoSeeAShow, Showify, StagePass, and other notable apps

---

## Tech stack (pitch site only)

- Vite + React
- Tailwind CSS v4
- Built to `docs/` — served via GitHub Pages
